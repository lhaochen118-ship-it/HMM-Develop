"""EXACT matched-operating-point comparison (replaces the interpolated navigation error of oc_summary).

For every run (cache file), every label-free rule O of ours and every baseline B with a default point:
  recall-matched   O at the largest threshold whose recall >= recall(B): FL, segment FAR, precision and the navigation
                   error from a Kalman run AT that threshold (the error is not monotone along a curve, so interpolating
                   between sparse points is not reliable)
  FL-matched       O at the smallest threshold whose FL <= FL(B): recall and navigation error
Thresholds: 200 quantiles of O's score. If O cannot reach recall(B) (its curve stops below), the comparison is recorded
as unreachable (NaN). Labels are used only to evaluate.
Usage: oc_matched.py <cache_dir> <ds> <desc,...> [--jobs 4] -> results/matched_<ds>_<desc>.json
       oc_matched.py --summary <results_dir> [--ours CPC-SC+CS]"""
import sys, os, json, glob, io, contextlib
import numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nav_rules as NR
import oc_curves as OC

OC.VARIANTS = True
JOBS = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4
OURS = ["CPC-SC+CS", "CPC-HMM+CS", "TCEmin", "CPC-HMM"]
BASES = ["Xu21", "Claxton24", "certified", "SelfCal frame", "max-sim", "TCEmin", "CPC-HMM", "CPC-SC+CS"]


def one(args):
    f, ds = args
    z = np.load(f, allow_pickle=True); b = NR.base_parts(z); b["ds"] = ds.split(":")[0]
    cx = dict(q_pos=z["q_pos"], o_q=z["o_q"], real=bool(z["real"]), q_seqs=b["seqs"], hz=list(z["hz"]), seed=int(z["seed"]), head=ds == "nclt")
    with contextlib.redirect_stdout(io.StringIO()): F = OC.families(z, b)
    base = {n: OC.point(F[n][3], F[n][1], z, b, cx, True) for n in BASES if n in F and F[n][3] is not None}
    out = {"defaults": base, "matched": {}}
    for o in OURS:
        sc, xf, _, _ = F[o]; sc = np.nan_to_num(sc, nan=-np.inf); fin = sc[np.isfinite(sc)]
        th = np.unique(np.quantile(fin, np.linspace(0, 1, 200)))
        pts = [(t, OC.point(sc >= t, xf, z, b, cx, False)) for t in th]           # nested report sets, ascending threshold
        res = {}
        for bn, bp in base.items():
            if bn == o: continue
            ok = [(t, p) for t, p in pts if p["recall"] >= bp["recall"] - 1e-12]
            r = {}
            if ok:
                t, _ = ok[-1]; p = OC.point(sc >= t, xf, z, b, cx, True)
                r.update({f"{k}@recall": p[k] for k in ("recall", "FL", "seg_FAR", "precision", "err_mean", "err_p95")})
            fl = [(t, p) for t, p in pts if p["FL"] <= bp["FL"] + 1e-12]
            if fl:
                t, _ = fl[0]; p = OC.point(sc >= t, xf, z, b, cx, True)
                r.update({f"{k}@FL": p[k] for k in ("recall", "FL", "seg_FAR", "err_mean")})
            res[bn] = r
        out["matched"][o] = res
    return os.path.basename(f), out


def main():
    cdir, ds, descs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    for desc in descs:
        files = sorted(glob.glob(os.path.join(cdir, f"navcache_{ds.replace(':', '_')}_{desc}_s*.npz")))
        if not files: continue
        with Pool(min(JOBS, len(files))) as p: res = dict(p.map(one, [(f, ds) for f in files]))
        os.makedirs("results", exist_ok=True)
        json.dump({"ds": ds, "desc": desc, "runs": res}, open(f"results/matched_{ds.replace(':', '_')}_{desc}.json", "w"), default=float)
        print(f"{ds}/{desc}: {len(res)} runs", flush=True)


if __name__ == "__main__" and "--summary" not in sys.argv:
    main()


def summary(rdir, ours="CPC-SC+CS"):
    """per dataset and baseline: median paired difference (ours - baseline) and wins / defined runs; 'unreach' = runs
    where ours cannot reach the baseline's recall at all"""
    rows = {}
    for f in sorted(glob.glob(os.path.join(rdir, "matched_*.json"))):
        d = json.load(open(f))
        for run in d["runs"].values():
            for bn, r in run["matched"].get(ours, {}).items():
                bp = run["defaults"][bn]; x = rows.setdefault((d["ds"], bn), {k: [] for k in ("FL@recall", "seg_FAR@recall", "err_mean@recall", "recall@FL", "err_mean@FL")})
                for k in x: x[k].append(r[k] - bp[k.split("@")[0]] if k in r else np.nan)
    print(f"\n### {ours} operated at each baseline's default point (exact; median paired difference, wins / defined runs)\n")
    print("| dataset | baseline | dFL @ base recall | dsegFAR @ base recall | derr @ base recall | drecall @ base FL | derr @ base FL |")
    print("|---|---|---|---|---|---|---|")
    for (ds, bn), x in sorted(rows.items()):
        cells = []
        for k, v in x.items():
            v = np.array(v, float); ok = np.isfinite(v)
            if not ok.any(): cells.append(f"unreach ({len(v)})"); continue
            w = int((v[ok] > 0).sum() if k == "recall@FL" else (v[ok] < 0).sum())
            cells.append((f"{np.median(v[ok]):+.1f}" if "err" in k else f"{np.median(v[ok]):+.3f}") + f" ({w}/{ok.sum()})")
        print(f"| {ds} | {bn} | " + " | ".join(cells) + " |")


if __name__ == "__main__" and "--summary" in sys.argv:
    summary(sys.argv[sys.argv.index("--summary") + 1], sys.argv[sys.argv.index("--ours") + 1] if "--ours" in sys.argv else "CPC-SC+CS")
