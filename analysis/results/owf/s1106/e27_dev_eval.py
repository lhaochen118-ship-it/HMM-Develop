"""Entry 27: development set A re-run with the causal HQ code (hsq2) vs the leaky tested code (hsq) and the old rule (S5), same runs."""
import json, sys, numpy as np
SP = sys.argv[1]; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"; A = 0.05
L = lambda f: json.load(open(f"{SP}/w/{f}"))
N, H, S = L("un_aq2.json"), L("un_hq.json"), L("un_dev_a.json")
keys = sorted(k for k in N if k in H and k in S)
def st(M, ks):
    g = lambda f: np.array([M[k]["variants"][inc][f] for k in ks])
    return g("recall").mean(), g("seg_FAR").mean(), int((g("seg_FAR") > A).sum()), float(np.nanmean(g("err_mean")))
print(f"dev set A: {len(keys)} runs in common (hsq2 {len(N)}, hsq {len(H)}, S5 {len(S)})")
for nm, M in (("hsq2 (audited)", N), ("hsq (tested)", H), ("S5 (old rule)", S)):
    r = st(M, keys); print(f"  {nm:15s} recall {r[0]:.4f}  mean segFAR {r[1]:.4f}  runs>a {r[2]}  nav {r[3]:.2f}")
same = sum(abs(N[k]["variants"][inc]["recall"] - H[k]["variants"][inc]["recall"]) < 1e-12 and abs(N[k]["variants"][inc]["seg_FAR"] - H[k]["variants"][inc]["seg_FAR"]) < 1e-12 for k in keys)
d = np.array([N[k]["variants"][inc]["recall"] - H[k]["variants"][inc]["recall"] for k in keys]); rng = np.random.default_rng(0)
bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
print(f"  hsq2 vs hsq: identical runs {same}/{len(keys)}, delta recall {d.mean():+.4f} [{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}], max |delta| {np.abs(d).max():.4f}")
for ds in sorted({N[k]["ds"] for k in keys}):
    ks = [k for k in keys if N[k]["ds"] == ds]; a, b, c = st(N, ks), st(H, ks), st(S, ks)
    print(f"  {ds:16s} n={len(ks):3d}  hsq2 {a[0]:.3f}/{a[1]:.4f}/{a[2]}  hsq {b[0]:.3f}/{b[1]:.4f}/{b[2]}  S5 {c[0]:.3f}/{c[1]:.4f}/{c[2]}")
