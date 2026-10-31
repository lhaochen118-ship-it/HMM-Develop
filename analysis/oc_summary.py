"""Matched-operating-point comparison from oc_curves.py outputs (results/oc_<ds>_<desc>.json).

For every run (dataset, descriptor, seed) and rule family, the curve is interpolated at
  * MATCHED RECALL r_ref = the recall of a reference rule at its default point (Xu'21 by default): FL, segment FAR,
    precision and navigation error of every other rule when it is operated at the same recall;
  * MATCHED FALSE REPORTS: recall (and error) at FL = 0.005 / 0.01 / 0.02 and at segment FAR = 0.01 / 0.025 / 0.05;
  * pAUC: mean recall over FL in [0, 0.05] (area under the recall-FL curve, normalised).
A rule that is only more conservative has the same curve as the others with a different default point; a better rule
has a curve above them (more recall at every false-report level, fewer false reports at every recall).
Usage: oc_summary.py <results_dir> [--ref Xu21] [--md out.md]  -> prints per-dataset means; JSON next to --md"""
import sys, os, json, glob
import numpy as np

REF = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "Xu21"
RULES = sys.argv[sys.argv.index("--rules") + 1].split(",") if "--rules" in sys.argv else None     # rows to print
OURS = sys.argv[sys.argv.index("--ours") + 1].split(",") if "--ours" in sys.argv else ["CPC-HMM+CS", "TCEmin"]
MD = sys.argv[sys.argv.index("--md") + 1] if "--md" in sys.argv else None
FLS, SEGS = (0.005, 0.01, 0.02), (0.01, 0.025, 0.05)


def interp_at(curve, xkey, x, ykey, nav_only=False):
    """y at x along the curve (thresholds give nested report sets, so recall / FL / segFAR are monotone in the threshold)"""
    pts = [(c[xkey], c[ykey]) for c in curve if ykey in c and (not nav_only or "err_mean" in c)]
    if not pts: return float("nan")
    xs, ys = np.array([p[0] for p in pts]), np.array([p[1] for p in pts]); o = np.argsort(xs, kind="stable"); xs, ys = xs[o], ys[o]
    if x <= xs[0]: return float(ys[0])
    if x >= xs[-1]: return float(ys[-1]) if x - xs[-1] < 1e-9 else float("nan")   # beyond the most liberal point: unreachable
    return float(np.interp(x, xs, ys))


def recall_at(curve, key, x):
    """largest recall with key <= x (step curve; no extrapolation)"""
    ok = [c["recall"] for c in curve if c[key] <= x + 1e-12]
    return float(max(ok)) if ok else 0.0


def pauc(curve, fmax=0.05):
    g = np.linspace(0, fmax, 26); return float(np.mean([recall_at(curve, "FL", f) for f in g]))


def summarize(rdir):
    rows = {}
    for f in sorted(glob.glob(os.path.join(rdir, "oc_*.json"))):
        d = json.load(open(f)); ds = d["ds"]
        for rk, run in d["runs"].items():
            fams = run["families"]
            ref = fams.get(REF, {}).get("default")
            for name, fam in fams.items():
                cv, df = fam["curve"], fam.get("default")
                r = {"pAUC_FL0.05": pauc(cv)} if cv else {}
                if df: r.update({f"def_{k}": df[k] for k in ("recall", "FL", "seg_FAR", "precision", "err_mean")})
                for x in FLS:
                    if cv: r[f"recall@FL{x}"] = recall_at(cv, "FL", x)
                for x in SEGS:
                    if cv: r[f"recall@segFAR{x}"] = recall_at(cv, "seg_FAR", x)
                if ref and cv:
                    rr = ref["recall"]; r["ref_recall"] = rr
                    for k in ("FL", "seg_FAR", "precision"): r[f"{k}@refrecall"] = interp_at(cv, "recall", rr, k)
                    r["err@refrecall"] = interp_at(cv, "recall", rr, "err_mean", nav_only=True)
                rows.setdefault(ds, {}).setdefault(name, []).append(r)
            o = run["oracle"]; rows.setdefault(ds, {}).setdefault("oracle", []).append({"def_recall": o["recall"], "def_err_mean": o["err_mean"]})
    return rows


def pairwise(rdir, ours, base):
    """per run: does `ours` beat `base` when operated at base's default recall (lower FL / segFAR / error), and at
    matched FL (higher recall)? returns per-dataset means of the paired differences"""
    out = {}
    for f in sorted(glob.glob(os.path.join(rdir, "oc_*.json"))):
        d = json.load(open(f))
        for run in d["runs"].values():
            F = run["families"]
            if ours not in F or base not in F or "default" not in F[base] or not F[ours]["curve"]: continue
            bd, cv = F[base]["default"], F[ours]["curve"]
            r = {"d_FL@base_recall": interp_at(cv, "recall", bd["recall"], "FL") - bd["FL"],
                 "d_segFAR@base_recall": interp_at(cv, "recall", bd["recall"], "seg_FAR") - bd["seg_FAR"],
                 "d_err@base_recall": interp_at(cv, "recall", bd["recall"], "err_mean", nav_only=True) - bd["err_mean"],
                 "d_recall@base_FL": recall_at(cv, "FL", bd["FL"]) - bd["recall"]}
            out.setdefault(d["ds"], []).append(r)
    return {ds: {k: (float(np.nanmean([r[k] for r in rs])), int(np.sum([r[k] < 0 if "recall" not in k else r[k] > 0 for r in rs])), len(rs))
                 for k in rs[0]} for ds, rs in out.items()}


def main():
    rows = summarize(sys.argv[1]); lines = []
    keys = ["def_recall", "def_FL", "def_seg_FAR", "def_err_mean", "FL@refrecall", "seg_FAR@refrecall", "precision@refrecall", "err@refrecall",
            "recall@FL0.01", "recall@segFAR0.025", "pAUC_FL0.05"]
    agg = {}
    for ds, fams in rows.items():
        lines.append(f"\n### {ds}  (reference recall = {REF} default)\n")
        lines.append("| rule | " + " | ".join(keys) + " |"); lines.append("|---" * (len(keys) + 1) + "|")
        for name, rs in fams.items():
            if RULES and name not in RULES and name != "oracle": continue
            m = {k: float(np.nanmean([r[k] for r in rs if k in r])) if any(k in r for r in rs) else float("nan") for k in keys}
            agg.setdefault(ds, {})[name] = dict(m, n=len(rs))
            lines.append(f"| {name} | " + " | ".join("" if np.isnan(m[k]) else (f"{m[k]:.1f}" if "err" in k else f"{m[k]:.3f}") for k in keys) + " |")
    bases = sorted({n for fams in rows.values() for n in fams} - set(OURS) - {"oracle"})
    for o in OURS:
        lines.append(f"\n### Paired: {o} operated at each baseline's default point (mean difference; wins / runs)\n")
        lines.append("| dataset | baseline | dFL @ base recall | dsegFAR @ base recall | derr @ base recall | drecall @ base FL |")
        lines.append("|---|---|---|---|---|---|")
        for bname in bases:
            if RULES and bname not in RULES: continue
            for ds, m in pairwise(sys.argv[1], o, bname).items():
                cell = lambda k: f"{m[k][0]:+.3f} ({m[k][1]}/{m[k][2]})" if "err" not in k else f"{m[k][0]:+.1f} ({m[k][1]}/{m[k][2]})"
                lines.append(f"| {ds} | {bname} | " + " | ".join(cell(k) for k in ("d_FL@base_recall", "d_segFAR@base_recall", "d_err@base_recall", "d_recall@base_FL")) + " |")
    txt = "\n".join(lines); print(txt)
    if MD:
        open(MD, "w").write(txt + "\n"); json.dump(agg, open(MD.rsplit(".", 1)[0] + ".json", "w"), indent=1)


if __name__ == "__main__":
    main()
