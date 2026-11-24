"""Second audit (Entry 28): the pre-registered criteria of Entries 23, 24, 26 on the final rule with the causal HSI branch (HSI-VNc),
the old-rule reference with the same branch, and the standalone HSI-VNc baseline (C2). Also compares with the first-audit numbers
(HSI-VN branch) to show the effect of the HSI fix."""
import json, glob, os, sys
import numpy as np
SP = sys.argv[1]; A = 0.05; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
L = lambda f: json.load(open(f)) if os.path.exists(f) else {}
key = lambda ds, desc, seed: f"{ds.replace(':', '_')}_{desc}_s{int(seed)}"
HSI = {}
for f in glob.glob(SP + "/a2/b67/results/hsi_*_r67c.json"):
    j = json.load(open(f))
    if "HSI-VNc" in j["variants"]: HSI[key(j["ds"], j["desc"], j["seed"])] = {k: j["variants"]["HSI-VNc"][k] for k in ("recall", "seg_FAR", "err_mean", "FL")}
HSI_OLD = {}
for f in glob.glob(SP + "/hsi67/hsi_*_r67.json"):
    j = json.load(open(f))
    if "HSI-VN" in j["variants"]: HSI_OLD[key(j["ds"], j["desc"], j["seed"])] = {k: j["variants"]["HSI-VN"][k] for k in ("recall", "seg_FAR", "err_mean", "FL")}
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
out = []; tot = {}
for gname, tg in (("64-66", "t64"), ("67-69", "t67"), ("70-72", "t67")):
    s0, s1 = [int(x) for x in gname.split("-")]
    old = L(f"{SP}/a2/un2_{'t70' if gname == '70-72' else tg}S5.json")
    for var in ("Q2", "QS"):
        N = L(f"{SP}/a2/un2_{tg}{var}.json"); V = L(f"{SP}/a2/un2_{tg}{var}V.json"); P = L(f"{SP}/w/un_{tg}{var}.json")   # P: first-audit (HSI-VN)
        keys = sorted(k for k in N if s0 <= int(N[k]["seed"]) <= s1 and k in V)
        if not keys: out.append(f"{gname} {var}: no runs yet"); continue
        M = {k: dict(ds=N[k]["ds"], R_new=N[k]["variants"][inc], C10=V[k]["variants"][inc]) for k in keys}
        for k in keys:
            if k in old: M[k]["R_old"] = old[k]["variants"][inc]
            if k in P: M[k]["R_vn"] = P[k]["variants"][inc]
            if k in HSI: M[k]["HSI-VNc"] = HSI[k]
            if k in HSI_OLD: M[k]["HSI-VN"] = HSI_OLD[k]
            if k in SOTA:
                for s in ("TAO26", "Xu21", "Claxton24", "oracle"): M[k][s] = SOTA[k][s]
        r = stats(M, keys, "R_new"); c = stats(M, keys, "C10")
        tot.setdefault(var, [0, 0, 0]); tot[var][0] += len(keys); tot[var][1] += r["nab"]; tot[var][2] += c["nab"]
        out.append(f"== seeds {gname}, {var} ({'causal hsq2' if var == 'Q2' else 'strict hsq2s'}) + HSI-VNc, {len(keys)} runs")
        out.append(f"   R_new: recall {r['recall']:.4f}, mean segFAR {r['msf']:.4f}, runs>a {r['nab']}, worst {r['worst']:.4f}, nav {r['nav']:.2f}")
        out.append(f"   C10  : recall {c['recall']:.4f}, mean segFAR {c['msf']:.4f}, runs>a {c['nab']}, worst {c['worst']:.4f}, nav {c['nav']:.2f}")
        pk = [k for k in keys if "R_vn" in M[k]]
        if pk:
            h = stats(M, pk, "R_vn"); dd = diff(M, pk, "R_new", "R_vn")
            out.append(f"   vs same rule with HSI-VN (first audit): recall {h['recall']:.4f} msf {h['msf']:.4f} runs>a {h['nab']} nav {h['nav']:.2f}; delta recall {dd[0]:+.4f} [{dd[1]:+.4f}, {dd[2]:+.4f}]")
        ok = [k for k in keys if "R_old" in M[k]]
        if ok:
            o = stats(M, ok, "R_old"); r2 = stats(M, ok, "R_new"); d, lo, hi = diff(M, ok, "R_new", "R_old")
            v1 = r2["nab"] <= o["nab"] and r2["msf"] <= o["msf"]; v2 = d >= -0.006 and lo >= -0.010; v3 = r2["nav"] <= o["nav"] + 0.5
            out.append(f"   Entry 23 rule vs R_old+HSI-VNc ({len(ok)} runs; R_old {o['recall']:.4f}/{o['msf']:.4f}/{o['nab']}/{o['nav']:.2f}): V1 {'MET' if v1 else 'NOT'} ({r2['nab']} vs {o['nab']}, {r2['msf']:.4f} vs {o['msf']:.4f}); V2 {'MET' if v2 else 'NOT'} ({d:+.4f} [{lo:+.4f}, {hi:+.4f}]); V3 {'MET' if v3 else 'NOT'} ({r2['nav']:.2f} vs {o['nav']:.2f})")
        sk = [k for k in keys if "HSI-VNc" in M[k] and "TAO26" in M[k]]
        if sk:
            rr = stats(M, sk, "R_new"); c1 = rr["worst"] <= A and rr["nab"] <= 2
            d, lo, hi = diff(M, sk, "R_new", "HSI-VNc"); c2 = d >= 0.08 and lo > 0
            c3 = True; line3 = []
            for s in ("TAO26", "Xu21", "Claxton24"):
                ss = stats(M, sk, s); val = ss["worst"] <= A and ss["nab"] <= 2; dd = diff(M, sk, "R_new", s); o3 = (not val) or dd[1] > 0; c3 &= o3
                line3.append(f"{s} valid={val} runs>a {ss['nab']} diff {dd[0]:+.3f}")
            hb = stats(M, sk, "HSI-VNc"); c4 = rr["nav"] <= hb["nav"]
            cc = stats(M, sk, "C10"); dc = diff(M, sk, "C10", "R_new"); s1_ = cc["worst"] <= A and cc["nab"] <= 2; s2_ = dc[0] >= -0.015
            out.append(f"   HSI-VNc baseline: recall {hb['recall']:.4f} msf {hb['msf']:.4f} runs>a {hb['nab']} nav {hb['nav']:.2f}" +
                       (f" (HSI-VN first audit: {stats(M, sk, 'HSI-VN')['recall']:.4f} / {stats(M, sk, 'HSI-VN')['nab']} / {stats(M, sk, 'HSI-VN')['nav']:.2f})" if all('HSI-VN' in M[k] for k in sk) else ""))
            out.append(f"   Entry 24/26 rule ({len(sk)} runs): C1 {'MET' if c1 else 'NOT'}; C2 {'MET' if c2 else 'NOT'} ({d:+.4f} [{lo:+.4f}, {hi:+.4f}]); C3 {'MET' if c3 else 'NOT'} ({'; '.join(line3)}); C4 {'MET' if c4 else 'NOT'} ({rr['nav']:.2f} vs {hb['nav']:.2f}) -> {'CONFIRMED' if c1 and c2 and c3 and c4 else 'NOT CONFIRMED'}")
            out.append(f"   safe point C10: S1 {'MET' if s1_ else 'NOT'} ({cc['nab']} runs>a, worst {cc['worst']:.4f}); S2 {'MET' if s2_ else 'NOT'} ({dc[0]:+.4f}) -> {'CONFIRMED' if s1_ and s2_ else 'not confirmed'}")
for var, (n, a, c) in tot.items(): out.append(f"TOTAL {var}: {n} runs; R_new runs>a {a}; C10 runs>a {c}")
# development set and generality sets: final rule with HSI-VNc vs the same rule with HSI-VN (first audit)
for nm, f2, f1 in (("dev set A", "un2_aQ2", "un_aq2"), ("holes 10 %", "un2_d10Q2", "ung_d10Q2"), ("holes 50 %", "un2_d50Q2", "ung_d50Q2"),
                   ("natural off-map", "un2_xQ2", "ung_xQ2"), ("NCLT", "un2_nQ2", "ung_nQ2")):
    N2, N1 = L(f"{SP}/a2/{f2}.json"), L(f"{SP}/w/{f1}.json"); ks = sorted(set(N2) & set(N1))
    if not ks: out.append(f"{nm}: no runs yet"); continue
    M = {k: dict(ds=N2[k]["ds"], c=N2[k]["variants"][inc], v=N1[k]["variants"][inc]) for k in ks}
    a, b = stats(M, ks, "c"), stats(M, ks, "v"); d = diff(M, ks, "c", "v")
    out.append(f"{nm} ({len(ks)}): HSI-VNc {a['recall']:.4f} / worst {a['worst']:.4f} / mean {a['msf']:.4f} / runs>a {a['nab']} / nav {a['nav']:.2f}"
               f" | HSI-VN {b['recall']:.4f} / {b['worst']:.4f} / {b['msf']:.4f} / {b['nab']} / {b['nav']:.2f} | delta recall {d[0]:+.4f} [{d[1]:+.4f}, {d[2]:+.4f}]")
    if nm == "dev set A":
        for ds in sorted({M[k]["ds"] for k in ks}):
            kk = [k for k in ks if M[k]["ds"] == ds]; x, y = stats(M, kk, "c"), stats(M, kk, "v")
            out.append(f"   {ds:16s} HSI-VNc {x['recall']:.3f}/{x['msf']:.4f}/{x['nab']}  HSI-VN {y['recall']:.3f}/{y['msf']:.4f}/{y['nab']}")
print("\n".join(out))
