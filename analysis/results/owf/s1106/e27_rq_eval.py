"""Audit re-evaluation (Entry 27): the pre-registered criteria of Entries 23, 24 and 26 on runs recomputed with the causal code (hsq2) and
the strictly online variant (hsq2s). Inputs are union JSONs (owf_union.py) and the HSI-VN / SOTA results of the same runs."""
import json, glob, os, sys
import numpy as np
SP = sys.argv[1]; A = 0.05; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
L = lambda f: json.load(open(f)) if os.path.exists(f) else {}
key = lambda ds, desc, seed: f"{ds.replace(':', '_')}_{desc}_s{int(seed)}"
HSI = {}
for f in glob.glob(SP + "/hsi67/hsi_*_r67.json"):
    j = json.load(open(f))
    if "HSI-VN" in j["variants"]: HSI[key(j["ds"], j["desc"], j["seed"])] = {k: j["variants"]["HSI-VN"][k] for k in ("recall", "seg_FAR", "err_mean", "FL")}
SOTA = {}
for d in ("t67sota", "t70sota"):
    for f in glob.glob(f"{SP}/w/{d}/sota_*.json"):
        j = json.load(open(f)); SOTA[key(j["ds"], j["desc"], j["seed"])] = j["variants"]
def stats(M, keys, v):
    g = lambda f: np.array([M[k][v][f] for k in keys]); dss = sorted({M[k]["ds"] for k in keys})
    wst = max(np.mean([M[k][v]["seg_FAR"] for k in keys if M[k]["ds"] == d]) for d in dss)
    return dict(recall=g("recall").mean(), msf=g("seg_FAR").mean(), nab=int((g("seg_FAR") > A).sum()), worst=wst, nav=float(np.nanmean(g("err_mean"))))
def diff(M, keys, a, b):
    d = np.array([M[k][a]["recall"] - M[k][b]["recall"] for k in keys]); rng = np.random.default_rng(0)
    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]; return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
out = []
groups = [("64-66", "t64", "r61"), ("67-69", "t67", "r67"), ("70-72", "t67", "r67")]
tot = {}
for gname, tg, _ in groups:
    s0, s1 = [int(x) for x in gname.split("-")]
    old = L(f"{SP}/w/un_{tg}S5.json") if gname != "70-72" else L(f"{SP}/w/un_t70S5.json")
    hq_old = L(f"{SP}/w/un_{'t64' if gname=='64-66' else ('t67' if gname=='67-69' else 't70')}HQ.json")
    for var in ("Q2", "QS"):
        N = L(f"{SP}/w/un_{tg}{var}.json"); V = L(f"{SP}/w/un_{tg}{var}V.json")
        keys = sorted(k for k in N if s0 <= int(N[k]["seed"]) <= s1 and k in V)
        if not keys: out.append(f"{gname} {var}: no runs yet"); continue
        M = {k: dict(ds=N[k]["ds"], R_new=N[k]["variants"][inc], C10=V[k]["variants"][inc]) for k in keys}
        for k in keys:
            if k in old: M[k]["R_old"] = old[k]["variants"][inc]
            if k in hq_old: M[k]["R_hsq"] = hq_old[k]["variants"][inc]
            if k in HSI: M[k]["HSI-VN"] = HSI[k]
            if k in SOTA:
                for s in ("TAO26", "Xu21", "Claxton24", "oracle"): M[k][s] = SOTA[k][s]
        r = stats(M, keys, "R_new"); c = stats(M, keys, "C10")
        tot.setdefault(var, [0, 0, 0]); tot[var][0] += len(keys); tot[var][1] += r["nab"]; tot[var][2] += c["nab"]
        out.append(f"== seeds {gname}, {var} ({'causal hsq2' if var == 'Q2' else 'strict hsq2s'}), {len(keys)} runs")
        out.append(f"   R_new: recall {r['recall']:.4f}, mean segFAR {r['msf']:.4f}, runs>a {r['nab']}, worst {r['worst']:.4f}, nav {r['nav']:.2f}")
        out.append(f"   C10  : recall {c['recall']:.4f}, mean segFAR {c['msf']:.4f}, runs>a {c['nab']}, worst {c['worst']:.4f}, nav {c['nav']:.2f}")
        hk = [k for k in keys if "R_hsq" in M[k]]
        if hk:
            same = sum(abs(M[k]["R_new"]["recall"] - M[k]["R_hsq"]["recall"]) < 1e-12 and abs(M[k]["R_new"]["seg_FAR"] - M[k]["R_hsq"]["seg_FAR"]) < 1e-12 for k in hk)
            h = stats(M, hk, "R_hsq"); dd = diff(M, hk, "R_new", "R_hsq")
            out.append(f"   vs tested hsq: identical runs {same}/{len(hk)}; hsq recall {h['recall']:.4f} msf {h['msf']:.4f} runs>a {h['nab']}; delta recall {dd[0]:+.4f} [{dd[1]:+.4f}, {dd[2]:+.4f}]")
        ok = [k for k in keys if "R_old" in M[k]]
        if ok:
            o = stats(M, ok, "R_old"); r2 = stats(M, ok, "R_new"); d, lo, hi = diff(M, ok, "R_new", "R_old")
            v1 = r2["nab"] <= o["nab"] and r2["msf"] <= o["msf"]; v2 = d >= -0.006 and lo >= -0.010; v3 = r2["nav"] <= o["nav"] + 0.5
            out.append(f"   Entry 23 rule vs R_old ({len(ok)} runs): V1 {'MET' if v1 else 'NOT'} ({r2['nab']} vs {o['nab']}, {r2['msf']:.4f} vs {o['msf']:.4f}); V2 {'MET' if v2 else 'NOT'} ({d:+.4f} [{lo:+.4f}, {hi:+.4f}]); V3 {'MET' if v3 else 'NOT'} ({r2['nav']:.2f} vs {o['nav']:.2f})")
        sk = [k for k in keys if "HSI-VN" in M[k] and "TAO26" in M[k]]
        if sk:
            rr = stats(M, sk, "R_new"); c1 = rr["worst"] <= A and rr["nab"] <= 2
            d, lo, hi = diff(M, sk, "R_new", "HSI-VN"); c2 = d >= 0.08 and lo > 0
            c3 = True; line3 = []
            for s in ("TAO26", "Xu21", "Claxton24"):
                ss = stats(M, sk, s); val = ss["worst"] <= A and ss["nab"] <= 2; dd = diff(M, sk, "R_new", s); o3 = (not val) or dd[1] > 0; c3 &= o3
                line3.append(f"{s} valid={val} runs>a {ss['nab']} diff {dd[0]:+.3f}")
            c4 = rr["nav"] <= stats(M, sk, "HSI-VN")["nav"]
            cc = stats(M, sk, "C10"); dc = diff(M, sk, "C10", "R_new"); s1_ = cc["worst"] <= A and cc["nab"] <= 2; s2_ = dc[0] >= -0.015
            out.append(f"   Entry 24/26 rule ({len(sk)} runs): C1 {'MET' if c1 else 'NOT'}; C2 {'MET' if c2 else 'NOT'} ({d:+.4f} [{lo:+.4f}, {hi:+.4f}]); C3 {'MET' if c3 else 'NOT'} ({'; '.join(line3)}); C4 {'MET' if c4 else 'NOT'} ({rr['nav']:.2f} vs {stats(M, sk, 'HSI-VN')['nav']:.2f}) -> {'CONFIRMED' if c1 and c2 and c3 and c4 else 'NOT CONFIRMED'}")
            out.append(f"   safe point C10: S1 {'MET' if s1_ else 'NOT'} ({cc['nab']} runs>a, worst {cc['worst']:.4f}); S2 {'MET' if s2_ else 'NOT'} ({dc[0]:+.4f}) -> {'CONFIRMED' if s1_ and s2_ else 'not confirmed'}")
for var, (n, a, c) in tot.items(): out.append(f"TOTAL {var}: {n} runs; R_new runs>a {a}; C10 runs>a {c}")
print("\n".join(out))
