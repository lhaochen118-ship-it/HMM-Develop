"""Entry 29a board: final rule (un2_t67Q2.json, unchanged) vs external baselines at @pub / @seg / @orc on the same runs (seeds 67-72)."""
import json, sys, numpy as np
A = 0.05; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
U = json.load(open(sys.argv[1])); B = {}
for f in sys.argv[2:]: B.update(json.load(open(f)))
keys = sorted(k for k in U if k in B and 67 <= int(U[k]["seed"]) <= 72)
vs = sorted({v for k in keys for v in B[k]["variants"]})
M = {k: dict(ds=U[k]["ds"], ours=U[k]["variants"][inc], **{v: B[k]["variants"][v] for v in vs if v in B[k]["variants"]}) for k in keys}
dss = sorted({M[k]["ds"] for k in keys}); rng = np.random.default_rng(0)
print(f"{len(keys)} common runs (seeds 67-72)")
print("| rule | recall | mean segFAR | worst-dataset mean segFAR | runs > a | nav (m) | valid | recall diff ours - rule [95% CI] |")
print("|---|---|---|---|---|---|---|---|")
for v in ["ours"] + vs:
    kk = [k for k in keys if v in M[k]]
    r = np.array([M[k][v]["recall"] for k in kk]); sf = np.array([M[k][v]["seg_FAR"] for k in kk]); nv = np.nanmean([M[k][v]["err_mean"] for k in kk])
    worst = max(np.mean([M[k][v]["seg_FAR"] for k in kk if M[k]["ds"] == d]) for d in dss)
    valid = worst <= A and (sf > A).sum() <= 2
    if v == "ours": dtxt = "–"
    else:
        d = np.array([M[k]["ours"]["recall"] - M[k][v]["recall"] for k in kk]); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
        dtxt = f"{d.mean():+.3f} [{np.percentile(bs, 2.5):+.3f}, {np.percentile(bs, 97.5):+.3f}]"
    print(f"| {v} | {r.mean():.3f} | {sf.mean():.4f} | {worst:.4f} | {(sf > A).sum()} / {len(kk)} | {nv:.1f} | {'yes' if valid else 'no'} | {dtxt} |")
print("\nper dataset recall (ours / Claxton24@orc / Xu21@orc / TAO26@orc):")
for d in dss:
    kk = [k for k in keys if M[k]["ds"] == d]
    print(f"  {d:16s} " + " / ".join(f"{np.mean([M[k][v]['recall'] for k in kk if v in M[k]]):.3f}" if any(v in M[k] for k in kk) else "–" for v in ("ours", "Claxton24@orc", "Xu21@orc", "TAO26@orc")))
