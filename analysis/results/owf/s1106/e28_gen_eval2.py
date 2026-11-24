"""Second audit (Entry 28): generality sets and development set A with the causal hindsight branch in every column:
final rule (hsq2 + HSI-VNc), old rule S5 (+ HSI-VNc), standalone HSI-VNc. Cell = pooled recall / worst-dataset mean segFAR / runs > alpha."""
import json, glob, os, sys
import numpy as np
SP = sys.argv[1]; A = 0.05; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
L = lambda f: json.load(open(f)) if os.path.exists(f) else {}
def cell(rows):
    if not rows: return "—", None
    r = np.mean([x[1] for x in rows]); dss = sorted({x[0] for x in rows})
    w = max(np.mean([x[2] for x in rows if x[0] == d]) for d in dss); n = sum(x[2] > A for x in rows)
    nav = np.nanmean([x[3] for x in rows]); return f"{r:.3f} / {w:.3f} / {n}", (r, w, n, nav, np.mean([x[2] for x in rows]))
def from_union(f):
    J = L(f); return {k: (v["ds"], v["variants"][inc]["recall"], v["variants"][inc]["seg_FAR"], v["variants"][inc]["err_mean"]) for k, v in J.items()}
def from_hsi(d, tag):
    out = {}
    for f in glob.glob(f"{SP}/a2/{d}/results/hsi_*_{tag}.json"):
        j = json.load(open(f)); v = j["variants"].get("HSI-VNc")
        if v: out[f"{j['ds'].replace(':', '_')}_{j['desc']}_s{int(j['seed'])}"] = (j["ds"], v["recall"], v["seg_FAR"], v["err_mean"])
    return out
print("| Set | Ours (hsq2 + HSI-VNc) | OWF-HWA-S5 (+ HSI-VNc) | HSI-VNc |")
print("|---|---|---|---|")
for nm, st, b in (("holes 10 %", "d10", "bd10"), ("holes 50 %", "d50", "bd50"), ("natural off-map", "x", "bx"), ("NCLT", "n", None)):
    Q, S = from_union(f"{SP}/a2/un2_{st}Q2.json"), from_union(f"{SP}/a2/un2_{st}S5.json")
    H = from_hsi(b, f"{b}c") if b else {}
    ks = sorted(set(Q) & set(S)); hk = sorted(set(Q) & set(H))
    print(f"| {nm} ({len(ks)}) | {cell([Q[k] for k in ks])[0]} | {cell([S[k] for k in ks])[0]} | {cell([H[k] for k in hk])[0] + (f' ({len(hk)})' if hk and len(hk) != len(ks) else '')} |")
Q, S = from_union(f"{SP}/a2/un2_aQ2.json"), from_union(f"{SP}/a2/un2_aS5.json"); ks = sorted(set(Q) & set(S))
if ks:
    a, b = cell([Q[k] for k in ks])[1], cell([S[k] for k in ks])[1]
    d = np.array([Q[k][1] - S[k][1] for k in ks]); rng = np.random.default_rng(0); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    print(f"\ndev set A ({len(ks)}): final {a[0]:.4f} / worst {a[1]:.4f} / mean {a[4]:.4f} / runs>a {a[2]} / nav {a[3]:.2f} | S5 {b[0]:.4f} / {b[1]:.4f} / {b[4]:.4f} / {b[2]} / {b[3]:.2f} | delta recall {d.mean():+.4f} [{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]")
    for ds in sorted({Q[k][0] for k in ks}):
        kk = [k for k in ks if Q[k][0] == ds]; x, y = cell([Q[k] for k in kk])[1], cell([S[k] for k in kk])[1]
        print(f"   {ds:16s} final {x[0]:.3f}/{x[4]:.4f}/{x[2]}/{x[3]:.1f}  S5 {y[0]:.3f}/{y[4]:.4f}/{y[2]}/{y[3]:.1f}")
