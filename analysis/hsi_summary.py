"""Summarise an HSI evaluation wave against the idea-1 baselines (same dataset, descriptor, seed) and test the Entry-1
pre-registered hypotheses on the held-out runs.

Usage: hsi_summary.py <results_dir_with_hsi_json> <idea1_oc_dir> [<idea1_oc_dir> ...] [--md out.md] [--json out.json]
Idea-1 rules read from oc_*.json: SH = CMS-CPC/H+SH+G+NGRr, CST-JS = CMS-CPC/H+CSTJS+G+NGRr (default points), oracle.
Design set (seen while designing, Entry 1): seed 0 of the 7 holed/natural datasets x {cosplace, netvlad, megaloc, dinov2}.
Everything else is held out."""
import sys, os, glob, json, warnings
import numpy as np
warnings.filterwarnings("ignore")

DS_ORDER = ["boreas", "nclt", "cmu", "nord", "4s_office_loop", "4s_old_town", "4s_countryside", "oxford", "stlucia"]
DESIGN_DESC = {"cosplace", "netvlad", "megaloc", "dinov2"}
FAM = {"SH": "CMS-CPC/H+SH+G+NGRr", "CST-JS": "CMS-CPC/H+CSTJS+G+NGRr"}


def load_base(dirs):
    base = {}
    for d in dirs:
        for f in glob.glob(os.path.join(d, "**", "oc_*.json"), recursive=True):
            try: j = json.load(open(f))
            except Exception: continue
            ds = j["ds"].replace(":", "_")
            for run in j["runs"].values():
                F = run["families"]; k = (ds, j["desc"], int(run["seed"]))
                for tag, fam in FAM.items():
                    if fam in F and "default" in F[fam]: base.setdefault(k, {})[tag] = F[fam]["default"]
                base.setdefault(k, {})["oracle"] = run["oracle"]
    return base


def load_hsi(rdir):
    out = {}
    for f in glob.glob(os.path.join(rdir, "**", "hsi_*.json"), recursive=True):
        j = json.load(open(f)); out[(j["ds"].replace(":", "_"), j["desc"], int(j["seed"]))] = j["variants"]
    return out


def main():
    a = sys.argv[1:]; md = a[a.index("--md") + 1] if "--md" in a else None; js = a[a.index("--json") + 1] if "--json" in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--md", "--json"))]
    H, B = load_hsi(pos[0]), load_base(pos[1:])
    variants = sorted({v for r in H.values() for v in r}, key=lambda v: (v != "HSI", v))
    L = []; P = lambda s="": L.append(s)
    keys = sorted(H, key=lambda k: (DS_ORDER.index(k[0]) if k[0] in DS_ORDER else 99, k[1], k[2]))
    held = [k for k in keys if not (k[2] == 0 and k[1] in DESIGN_DESC and k[0] not in ("oxford", "stlucia"))]
    paired = [k for k in held if k in B and "SH" in B[k]]
    P(f"# HSI wave summary\n\nruns: {len(keys)} (held-out {len(held)}, with idea-1 SH on the same run {len(paired)})\n")
    # ---- per dataset, held-out, main comparison
    P("## Held-out runs: mean recall / segFAR / navigation error per dataset\n")
    cols = ["HSI", "geo", "SH", "CST-JS", "oracle"]
    P("| dataset | n | " + " | ".join(f"{c} rec / seg / err" for c in cols) + " | HSI−SH rec (wins) | HSI−SH err (better) |")
    P("|---|---|" + "---|" * (len(cols) + 2))
    res = {}
    for ds in DS_ORDER:
        ks = [k for k in paired if k[0] == ds]
        if not ks: continue
        row = {}
        for c in cols:
            vals = [(H[k][c] if c in H[k] else B[k].get(c)) for k in ks]
            vals = [v for v in vals if v]
            if not vals: row[c] = None; continue
            row[c] = (np.mean([v["recall"] for v in vals]), np.mean([v.get("seg_FAR", 0) for v in vals]), np.mean([v["err_mean"] for v in vals]), len(vals))
        dr = np.array([H[k]["HSI"]["recall"] - B[k]["SH"]["recall"] for k in ks]); de = np.array([H[k]["HSI"]["err_mean"] - B[k]["SH"]["err_mean"] for k in ks])
        res[ds] = dict(n=len(ks), **{c: row[c] for c in cols}, d_rec=float(dr.mean()), wins=int((dr > 0).sum()), d_err=float(de.mean()), better=int((de < 0).sum()),
                       seg_runs_over=int(sum(H[k]["HSI"]["seg_FAR"] > 0.05 for k in ks)))
        f = lambda r: f"{r[0]:.3f} / {r[1]:.3f} / {r[2]:.1f}" if r else "–"
        P(f"| {ds} | {len(ks)} | " + " | ".join(f(row[c]) for c in cols) + f" | {dr.mean():+.3f} ({(dr > 0).sum()}/{len(ks)}) | {de.mean():+.1f} ({(de < 0).sum()}/{len(ks)}) |")
    # ---- hypotheses
    P("\n## Pre-registered hypotheses (Entry 1) on the held-out runs\n")
    ndat = len(res)
    if not res: print("no held-out run with a baseline"); return
    h1a = sum(r["HSI"][1] <= 0.05 for r in res.values()); over = sum(H[k]["HSI"]["seg_FAR"] > 0.05 for k in held); h1 = h1a == ndat and over <= 0.1 * len(held)
    P(f"- **H1 (validity):** mean segFAR <= 0.05 on {h1a}/{ndat} datasets; runs > 0.05: {over}/{len(held)} ({over / max(len(held), 1):.1%}) -> **{'supported' if h1 else 'NOT supported'}**")
    h2a = sum(r["d_rec"] >= 0 for r in res.values()); dall = np.mean([H[k]["HSI"]["recall"] - B[k]["SH"]["recall"] for k in paired]); h2 = h2a >= 5 and dall >= 0
    P(f"- **H2 (recall):** HSI >= SH on {h2a}/{ndat} datasets; pooled mean difference {dall:+.4f} -> **{'supported' if h2 else 'NOT supported'}**")
    wk = [k for k in paired if k[1] in ("dinov2", "netvlad")]; dw = np.mean([H[k]["HSI"]["recall"] - B[k]["SH"]["recall"] for k in wk]) if wk else float("nan")
    P(f"- **H3 (weak descriptors):** DINOv2 + NetVLAD held-out runs: mean HSI − SH = {dw:+.4f} over {len(wk)} runs -> **{'supported' if dw >= 0.05 else 'NOT supported'}**")
    h4a = sum(r["d_err"] <= 1.0 for r in res.values())
    P(f"- **H4 (navigation):** mean error within +1 m of SH on {h4a}/{ndat} datasets -> **{'supported' if h4a >= 5 else 'NOT supported'}**")
    # H5: pooled position classes per dataset
    h5 = 0; lines = []
    for ds in res:
        ks = [k for k in held if k[0] == ds]; cl = {}
        for k in ks:
            for c, (nseg, rate) in H[k]["HSI"]["classes"].items():
                cl.setdefault(c, [0, 0.0]); cl[c][0] += nseg; cl[c][1] += rate * nseg
        okd = all(v[1] / v[0] <= 0.07 for c, v in cl.items() if v[0] >= 50)
        h5 += okd; lines.append(f"{ds}: " + ", ".join(f"{c} {v[1] / max(v[0], 1):.3f} (n={v[0]})" for c, v in cl.items()))
    P(f"- **H5 (position audit):** every class <= 0.07 (classes with >= 50 segments) on {h5}/{ndat} datasets -> **{'supported' if h5 >= 7 else 'NOT supported'}**")
    for l in lines: P(f"  - {l}")
    # ---- per descriptor (held-out, pooled over datasets)
    P("\n## Held-out, per descriptor (mean over datasets and seeds)\n")
    P("| descriptor | n | HSI rec | SH rec | HSI−SH | wins | HSI seg | HSI err | SH err |"); P("|---|---|---|---|---|---|---|---|---|")
    for d in ["cosplace", "netvlad", "megaloc", "dinov2", "salad", "mixvpr"]:
        ks = [k for k in paired if k[1] == d]
        if not ks: continue
        hr = np.mean([H[k]["HSI"]["recall"] for k in ks]); sr = np.mean([B[k]["SH"]["recall"] for k in ks])
        P(f"| {d} | {len(ks)} | {hr:.3f} | {sr:.3f} | {hr - sr:+.3f} | {sum(H[k]['HSI']['recall'] > B[k]['SH']['recall'] for k in ks)} | "
          f"{np.mean([H[k]['HSI']['seg_FAR'] for k in ks]):.3f} | {np.mean([H[k]['HSI']['err_mean'] for k in ks]):.1f} | {np.mean([B[k]['SH']['err_mean'] for k in ks]):.1f} |")
    # ---- ablations (held-out, all variants)
    P("\n## Ablations (held-out runs; mean over datasets of the per-dataset means)\n")
    P("| variant | recall | segFAR | runs seg>0.05 | nav err | worst-class rate |"); P("|---|---|---|---|---|---|")
    for v in variants:
        rr, ss, ee, ov, wc = [], [], [], 0, []
        for ds in res:
            ks = [k for k in held if k[0] == ds and v in H[k]]
            if not ks: continue
            rr.append(np.mean([H[k][v]["recall"] for k in ks])); ss.append(np.mean([H[k][v]["seg_FAR"] for k in ks])); ee.append(np.mean([H[k][v]["err_mean"] for k in ks]))
            ov += sum(H[k][v]["seg_FAR"] > 0.05 for k in ks)
            cl = {}
            for k in ks:
                for c, (nseg, rate) in H[k][v]["classes"].items(): cl.setdefault(c, [0, 0.0]); cl[c][0] += nseg; cl[c][1] += rate * nseg
            wc.append(max([x[1] / x[0] for x in cl.values() if x[0] >= 50] or [0]))
        if rr: P(f"| {v} | {np.mean(rr):.3f} | {np.mean(ss):.4f} | {ov} | {np.mean(ee):.1f} | {max(wc):.3f} |")
    sh = [np.mean([B[k]["SH"]["recall"] for k in paired if k[0] == ds]) for ds in res]
    if sh: P(f"| (idea 1) SH | {np.mean(sh):.3f} | {np.mean([np.mean([B[k]['SH']['seg_FAR'] for k in paired if k[0] == ds]) for ds in res]):.4f} | "
      f"{sum(B[k]['SH']['seg_FAR'] > 0.05 for k in paired)} | {np.mean([np.mean([B[k]['SH']['err_mean'] for k in paired if k[0] == ds]) for ds in res]):.1f} | – |")
    txt = "\n".join(L); print(txt)
    if md: open(md, "w").write(txt + "\n")
    if js: json.dump(dict(per_dataset=res, n_runs=len(keys), n_held=len(held), n_paired=len(paired)), open(js, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
