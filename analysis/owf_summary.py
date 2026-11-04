"""Idea 2 (Entry 1): paired comparison of the open-world filter (owf.py results) with the idea-1 baselines on the SAME runs
(dataset, descriptor, seed = same holes, odometry, queries), and the pre-registered hypothesis checks.

Baselines (label-free, default points as published): SH = CMS-CPC/H+SH+G+NGRr, CST-JS = CMS-CPC/H+CSTJS+G+NGRr, CST-F =
CMS-CPC/H+CSTF+G+NGRr, from the idea-1 oc JSONs (Entry 38 files for seeds 0-9 of every dataset; Entry 37 files for St Lucia).
OWF: the default point (eps0, recorded in each owf_*.json) and its curve over eps; position classes (start / edge / deep) of
the real off-map segments (position_audit.seg_classes).
HSI-VN (idea 2a, branch head before Entry 10): per-run JSONs of analysis/results/hsi/hsi_results_json.tgz (--hsi <dir>, variants
HSI-VN / HSI-VMN); on the reserve seeds 25-27 the HSI-VN runs of the same wave (--hsi <dir of hsi_*.json>).
Usage: owf_summary.py <owf_results_dir> <e38_oc_dir> <e37_oc_dir> [--hsi dir] [--seeds 1-9] [--tag ""] [--md out.md] [--json out.json]"""
import sys, os, json, glob, re
import numpy as np

BASE = {"SH": "CMS-CPC/H+SH+G+NGRr", "CST-JS": "CMS-CPC/H+CSTJS+G+NGRr", "CST-F": "CMS-CPC/H+CSTF+G+NGRr"}
ORDER = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside", "oxford", "stlucia"]
SHORT = {"boreas": "Boreas", "nclt": "NCLT", "cmu": "CMU", "nord": "Nordland", "4s:office_loop": "office", "4s:old_town": "old town",
         "4s:countryside": "countryside", "oxford": "Oxford", "stlucia": "St Lucia"}
ALPHA = 0.05


def opt(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def seeds_of(s):
    if "-" in s: a, b = s.split("-"); return set(range(int(a), int(b) + 1))
    return {int(x) for x in s.split(",")}


def load_base(d38, d37):
    """(ds, desc, seed) -> {name: default dict}; Entry 38 files first, Entry 37 files fill the runs E38 lacks (St Lucia)"""
    out = {}
    for d, lab in ((d38, "e38"), (d37, "e37")):
        for f in glob.glob(os.path.join(d, f"oc_*_{lab}_s*.json")):
            j = json.load(open(f))
            for run in j["runs"].values():
                key = (j["ds"], j["desc"], int(run["seed"]))
                if key in out: continue
                out[key] = {b: run["families"][n]["default"] for b, n in BASE.items() if n in run["families"] and run["families"][n].get("default")}
    return out


def load_hsi(d):
    """(ds, desc, seed) -> {'HSI-VN': default dict, 'HSI-VMN': ...} from hsi_<ds>_<desc>_s<seed>.json files (any sub-directory)"""
    out = {}
    if not d: return out
    for f in glob.glob(os.path.join(d, "**", "hsi_*.json"), recursive=True):
        j = json.load(open(f)); v = j.get("variants", {})
        out[(j["ds"], j["desc"], int(j["seed"]))] = {k: v[k] for k in ("HSI-VN", "HSI-VMN") if k in v}
    return out


def recall_at_seg(curve, x):
    ok = [c["recall"] for c in curve if c["seg_FAR"] <= x + 1e-12]
    return max(ok) if ok else 0.0


def main():
    rdir, d38, d37 = sys.argv[1:4]; seeds = seeds_of(opt("--seeds", "1-9")); tag = opt("--tag", "")
    base = load_base(d38, d37); hsi = load_hsi(opt("--hsi", None)); rows = {}
    pat = re.compile(r"owf_(.+)_([a-z0-9]+)_s(\d+)" + (f"_{tag}" if tag else "") + r"\.json$")
    for f in sorted(glob.glob(os.path.join(rdir, "owf_*.json"))):
        m = pat.search(os.path.basename(f))
        if not m: continue
        j = json.load(open(f)); ds, desc, seed = j["ds"], j["desc"], int(j["seed"])
        if not tag and os.path.basename(f) != f"owf_{ds.replace(':', '_')}_{desc}_s{seed}.json": continue
        if ds not in ("nclt", "oxford", "stlucia") and seed not in seeds: continue
        r = j["runs"]["1.0"]; b = base.get((ds, desc, seed), {})
        d = r.get("default") or dict(next(c for c in r["curve"] if abs(c["eps"] - 1e-3) < 1e-12), err_mean=float("nan"))   # design runs before the default field
        b = dict(b, **hsi.get((ds, desc, seed), {}))
        rows.setdefault(ds, []).append(dict(desc=desc, seed=seed, owf=d, curve=r["curve"], ms=r["ms_per_frame"], base=b,
                                            ceil=r["map_correct_on"]))
    res = {}; md = []
    hdr = "| Dataset | runs | OWF recall | OWF segFAR | SH recall | SH segFAR | CST-JS recall | CST-JS segFAR | Δrecall vs SH (wins) | OWF err (m) | SH err (m) | OWF@SH-segFAR | start / edge / deep (OWF) | ms/frame | HSI-VN recall / segFAR | Δrecall vs HSI-VN (wins) | HSI-VN err (m) |"
    md += [hdr, "|" + "---|" * (hdr.count("|") - 1)]
    for ds in ORDER:
        if ds not in rows: continue
        R = rows[ds]; P = [x for x in R if "SH" in x["base"]]
        mean = lambda f, L: float(np.mean([f(x) for x in L])) if L else float("nan")
        o_rec, o_seg = mean(lambda x: x["owf"]["recall"], R), mean(lambda x: x["owf"]["seg_FAR"], R)
        s_rec, s_seg = mean(lambda x: x["base"]["SH"]["recall"], P), mean(lambda x: x["base"]["SH"]["seg_FAR"], P)
        hv = [x for x in R if "HSI-VN" in x["base"]]
        h_rec, h_seg = mean(lambda x: x["base"]["HSI-VN"]["recall"], hv), mean(lambda x: x["base"]["HSI-VN"]["seg_FAR"], hv)
        h_err = mean(lambda x: x["base"]["HSI-VN"]["err_mean"], hv); o_err_h = mean(lambda x: x["owf"]["err_mean"], hv)
        dh = [x["owf"]["recall"] - x["base"]["HSI-VN"]["recall"] for x in hv]; wins_h = int(sum(v > 0 for v in dh))
        cj = [x for x in R if "CST-JS" in x["base"]]
        c_rec, c_seg = mean(lambda x: x["base"]["CST-JS"]["recall"], cj), mean(lambda x: x["base"]["CST-JS"]["seg_FAR"], cj)
        dlt = [x["owf"]["recall"] - x["base"]["SH"]["recall"] for x in P]; wins = int(sum(v > 0 for v in dlt))
        o_err, s_err = mean(lambda x: x["owf"]["err_mean"], P), mean(lambda x: x["base"]["SH"]["err_mean"], P)
        o_at = mean(lambda x: recall_at_seg(x["curve"], x["base"]["SH"]["seg_FAR"]), P)       # OWF curve at SH's segFAR (same run)
        pos = {c: [sum(x["owf"]["pos"][c][0] for x in R), sum(x["owf"]["pos"][c][1] for x in R)] for c in ("start", "edge", "deep")}
        prate = {c: (pos[c][0] / pos[c][1] if pos[c][1] else None) for c in pos}
        worst = max((x["owf"]["seg_FAR"] for x in R), default=float("nan")); n_bad = int(sum(x["owf"]["seg_FAR"] > ALPHA for x in R))
        by_desc = {}
        for x in R: by_desc.setdefault(x["desc"], []).append(x["owf"]["seg_FAR"])
        res[ds] = dict(runs=len(R), paired=len(P), owf_recall=o_rec, owf_segFAR=o_seg, SH_recall=s_rec, SH_segFAR=s_seg, CSTJS_recall=c_rec,
                       CSTJS_segFAR=c_seg, d_recall_SH=float(np.mean(dlt)) if dlt else float("nan"), wins_SH=wins, owf_err=o_err, SH_err=s_err,
                       owf_at_SH_segFAR=o_at, pos=pos, pos_rate=prate, worst_run_segFAR=worst, runs_above_alpha=n_bad,
                       segFAR_by_desc={k: float(np.mean(v)) for k, v in by_desc.items()}, ms_per_frame=mean(lambda x: x["ms"], R),
                       paired_hsi=len(hv), HSIVN_recall=h_rec, HSIVN_segFAR=h_seg, HSIVN_err=h_err, owf_err_on_hsi=o_err_h,
                       d_recall_HSIVN=float(np.mean(dh)) if dh else float("nan"), wins_HSIVN=wins_h,
                       ceiling=mean(lambda x: x["ceil"], R))
        f3 = lambda v: "–" if v is None or v != v else f"{v:.3f}"
        md.append(f"| {SHORT[ds]} | {len(R)} | {o_rec:.3f} | {o_seg:.4f} | {f3(s_rec)} | {f3(s_seg)} | {f3(c_rec)} | {f3(c_seg)} | "
                  f"{np.mean(dlt) if dlt else float('nan'):+.3f} ({wins}/{len(P)}) | {o_err:.1f} | {f3(s_err) if s_err != s_err else f'{s_err:.1f}'} | {f3(o_at)} | "
                  + " / ".join(f3(prate[c]) for c in ("start", "edge", "deep")) + f" | {res[ds]['ms_per_frame']:.1f} | "
                  + (f"{h_rec:.3f} / {h_seg:.4f} | {np.mean(dh):+.3f} ({wins_h}/{len(hv)}) | {h_err:.1f} |" if hv else "– | – | – |"))
    # pre-registered hypotheses (Entry 1 section 4)
    D = [d for d in ORDER if d in res]
    H = {}
    H["H1 validity: mean segFAR <= 0.05 on every dataset"] = all(res[d]["owf_segFAR"] <= ALPHA for d in D)
    H["H2 recall > SH (paired mean) on >= 7/9 datasets"] = sum(res[d]["d_recall_SH"] > 0 for d in D if res[d]["paired"]) >= 7
    H["H2b recall > CST-JS on >= 7/9 datasets"] = sum(res[d]["owf_recall"] > res[d]["CSTJS_recall"] for d in D if res[d]["paired"]) >= 7
    H["H3 position: every class rate <= 0.07 on every dataset"] = all((res[d]["pos_rate"][c] or 0) <= 0.07 for d in D for c in ("start", "edge", "deep"))
    H["H4 navigation error <= SH on >= 6 of the 7 main datasets"] = sum(res[d]["owf_err"] <= res[d]["SH_err"] for d in D[:7] if d in res) >= 6
    H["H5 cost <= 15 ms/frame (3 filters, one core) on every dataset"] = all(res[d]["ms_per_frame"] <= 15 for d in D)
    H["H6 OWF recall at the run's SH segFAR >= SH recall on >= 8/9"] = sum(res[d]["owf_at_SH_segFAR"] >= res[d]["SH_recall"] for d in D if res[d]["paired"]) >= 8
    DH = [d for d in D if res[d]["paired_hsi"]]
    H["H8 recall > HSI-VN (paired mean) on >= 7 datasets (of those with HSI-VN)"] = sum(res[d]["d_recall_HSIVN"] > 0 for d in DH) >= min(7, len(DH))
    H["H9 navigation error <= HSI-VN on >= 5 of the main datasets with HSI-VN"] = sum(res[d]["owf_err_on_hsi"] <= res[d]["HSIVN_err"] for d in DH) >= min(5, len(DH))
    md += ["", "| Hypothesis | Passed |", "|---|---|"] + [f"| {k} | {'yes' if v else '**no**'} |" for k, v in H.items()]
    counts = {"H2": f"{sum(res[d]['d_recall_SH'] > 0 for d in D if res[d]['paired'])}/{sum(1 for d in D if res[d]['paired'])}",
              "H8": f"{sum(res[d]['d_recall_HSIVN'] > 0 for d in D if res[d]['paired_hsi'])}/{sum(1 for d in D if res[d]['paired_hsi'])}",
              "H4": f"{sum(res[d]['owf_err'] <= res[d]['SH_err'] for d in D[:7] if d in res)}/{min(7, len(D))}"}
    if "--decide" in sys.argv:            # Entry 10 Set B (reserve seeds 25-27): D1-D3 against HSI-VN on the same runs
        allr = [x for d in D for x in rows[d] if "HSI-VN" in x["base"]]
        dd = np.array([x["owf"]["recall"] - x["base"]["HSI-VN"]["recall"] for x in allr])
        rng = np.random.default_rng(0); bs = [rng.choice(dd, len(dd)).mean() for _ in range(5000)] if len(dd) else [np.nan]
        n_above = sum(x["owf"]["seg_FAR"] > ALPHA for d in D for x in rows[d]); n_all = sum(len(rows[d]) for d in D)
        dec = {"D1 validity: mean segFAR <= 0.05 on every dataset and <= 5 % runs above alpha":
                   all(res[d]["owf_segFAR"] <= ALPHA for d in D) and n_above <= 0.05 * n_all,
               "D2 pooled recall OWF - HSI-VN > 0, 95 % CI lower end > 0": bool(len(dd) and dd.mean() > 0 and np.percentile(bs, 2.5) > 0),
               "D3 navigation error <= HSI-VN + 1 m on >= 4/6 datasets": sum(res[d]["owf_err_on_hsi"] <= res[d]["HSIVN_err"] + 1.0 for d in D) >= 4}
        md += ["", f"Set B: {n_all} runs, {n_above} above alpha; pooled recall OWF - HSI-VN = {dd.mean() if len(dd) else float('nan'):+.4f} "
               f"(95 % CI [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}], n = {len(dd)})", "", "| Decision criterion | Passed |", "|---|---|"]
        md += [f"| {k} | {'yes' if v else '**no**'} |" for k, v in dec.items()]
        H.update(dec)
    out = "\n".join(md); print(out); print(counts)
    if opt("--md", None): open(opt("--md", None), "w").write(out + "\n")
    if opt("--json", None): json.dump(dict(per_dataset=res, hypotheses=H, counts=counts), open(opt("--json", None), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
