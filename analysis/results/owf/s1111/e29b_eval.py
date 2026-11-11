"""Entry 29b: heading-drift ablation (ODO_YAWRW 0 / 0.13 / 0.3 deg / sqrt(m)) on the set-A subset CMU / Oxford / St Lucia x CosPlace /
MegaLoc x seeds 1-3 (18 runs per level). Inputs: owf_union JSON per level (final rule; + OWF_VETO=0.5), standalone HSI-VNc JSONs
(hsi_eval.py with the same drift), sota_job JSONs (TAO26 drifts with the odometry; Claxton24 / Xu21 come from the cache and do not).
Also checks that level 0 reproduces the Entry 28 numbers (un2_aQ2.json) on the same runs.
Usage: e29b_eval.py <work dir with un_aY*.json, hsi/results, sota/> <un2_aQ2.json>"""
import json, glob, os, sys
import numpy as np
W, REF = sys.argv[1], sys.argv[2]; A = 0.05; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
LV = [("0", "aY0", "hY0"), ("0.13", "aY13", "hY013"), ("0.3", "aY30", "hY03")]
key = lambda ds, desc, seed: f"{ds.replace(':', '_')}_{desc}_s{int(seed)}"


def cell(rs):
    r = np.array([x["recall"] for x in rs]); s = np.array([x["seg_FAR"] for x in rs]); n = np.nanmean([x["err_mean"] for x in rs])
    return f"{r.mean():.3f} / {s.mean():.4f} / {(s > A).sum()} / {n:.1f}", r


rows, base = [], {}
for lv, tg, hg in LV:
    U = json.load(open(os.path.join(W, f"un_{tg}.json"))); V = json.load(open(os.path.join(W, f"un_{tg}V.json")))
    H = {}
    for f in glob.glob(os.path.join(W, "hsi", "results", f"hsi_*_{hg}.json")):
        j = json.load(open(f)); H[key(j["ds"], j["desc"], j["seed"])] = j["variants"]["HSI-VNc"]
    S = {}
    for f in glob.glob(os.path.join(W, "sota", f"sota_*_{tg}.json")):
        j = json.load(open(f)); S[key(j["ds"], j["desc"], j["seed"])] = j["variants"]
    ks = sorted(U)
    out = {"ours": [U[k]["variants"][inc] for k in ks], "ours+veto": [V[k]["variants"][inc] for k in ks if k in V],
           "HSI-VNc": [H[k] for k in ks if k in H]}
    for b in ("TAO26", "TAO26@seg", "TAO26@orc", "Claxton24@orc", "Xu21@orc"):
        out[b] = [S[k][b] for k in ks if k in S and b in S[k]]
    rows.append((lv, len(ks), {b: cell(v) for b, v in out.items() if v}))
    base[lv] = {k: U[k]["variants"][inc]["recall"] for k in ks}
    if lv == "0":                                            # reproduction check against Entry 28 (same code, same runs)
        R = json.load(open(REF)); kk = [k for k in ks if k in R]
        d = [U[k]["variants"][inc]["recall"] - R[k]["variants"][inc]["recall"] for k in kk]
        ds_ = [U[k]["variants"][inc]["seg_FAR"] - R[k]["variants"][inc]["seg_FAR"] for k in kk]
        print(f"level 0 vs Entry 28 (un2_aQ2.json), {len(kk)} runs: max |d recall| {np.max(np.abs(d)):.4f}, max |d segFAR| {np.max(np.abs(ds_)):.4f}")
names = ["ours", "ours+veto", "HSI-VNc", "TAO26", "TAO26@seg", "TAO26@orc", "Claxton24@orc", "Xu21@orc"]
print("\ncell = recall / mean segFAR / runs > alpha / navigation error (m); 18 runs per level")
print("| drift (deg/sqrt m) | runs | " + " | ".join(names) + " |"); print("|---|---|" + "---|" * len(names))
for lv, n, c in rows: print(f"| {lv} | {n} | " + " | ".join(c[b][0] if b in c else "–" for b in names) + " |")
rng = np.random.default_rng(0)
for lv in ("0.13", "0.3"):
    kk = sorted(set(base["0"]) & set(base[lv])); d = np.array([base[lv][k] - base["0"][k] for k in kk])
    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    print(f"final rule recall change at {lv}: {d.mean():+.4f} [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}] (paired, {len(kk)} runs)")
    for ds in ("cmu", "oxford", "stlucia"):
        dd = [base[lv][k] - base["0"][k] for k in kk if k.startswith(ds)]
        print(f"   {ds:8s} {np.mean(dd):+.4f}")
