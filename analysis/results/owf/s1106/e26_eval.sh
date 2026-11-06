#!/bin/bash
SP=/tmp/claude-0/-home-user-HMM-Develop/1345ea5d-f2ee-5042-813e-a6294e540411/scratchpad
cd $SP/runs/t70b; for tg in S5 HQ; do mkdir -p $SP/w/t70$tg/fr $SP/w/t70$tg/h; done; mkdir -p $SP/w/t70sota
for d in test70b-*_out/results; do for tg in S5 HQ; do
  find $d -maxdepth 1 -name "fr_*_t70${tg}_b1.npz" -exec cp {} $SP/w/t70$tg/fr/ \; ; find $d -maxdepth 1 -name "hsifr_*_t70${tg}xms09_16.npz" -exec cp {} $SP/w/t70$tg/h/ \; ;
done; find $d -maxdepth 1 -name "sota_*.json" -exec cp {} $SP/w/t70sota/ \; ; done
for tg in S5 HQ; do echo $tg fr $(ls $SP/w/t70$tg/fr | wc -l) h $(ls $SP/w/t70$tg/h | wc -l); done; echo sota $(ls $SP/w/t70sota | wc -l)
cd /home/user/HMM-Develop/analysis
V="H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5);H"
[ "$(ls $SP/w/t70S5/fr | wc -l)" -ge 144 ] && python3 owf_union.py $SP/w/t70S5/fr $SP/w/t70S5/h $SP/r67 $SP/w/un_t70S5.json --tag t70S5xms09_16 --ftag _t70S5 --jobs 4 --variants "$V" 2>/dev/null | tail -1
python3 owf_union.py $SP/w/t70HQ/fr $SP/w/t70HQ/h $SP/r67 $SP/w/un_t70HQ.json --tag t70HQxms09_16 --ftag _t70HQ --jobs 4 --variants "$V" 2>/dev/null | tail -1
OWF_VETO=0.5 python3 owf_union.py $SP/w/t70HQ/fr $SP/w/t70HQ/h $SP/r67 $SP/w/un_t70HQV.json --tag t70HQxms09_16 --ftag _t70HQ --jobs 4 --variants "$V" 2>/dev/null | tail -1
python3 - <<'PY'
import json, glob, numpy as np
SP = "/tmp/claude-0/-home-user-HMM-Develop/1345ea5d-f2ee-5042-813e-a6294e540411/scratchpad"; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"; A = 0.05
import os; O = json.load(open(SP + "/w/un_t70S5.json")) if os.path.exists(SP + "/w/un_t70S5.json") else None; N = json.load(open(SP + "/w/un_t70HQ.json")); C = json.load(open(SP + "/w/un_t70HQV.json"))
key = lambda ds, desc, seed: f"{ds.replace(':', '_')}_{desc}_s{int(seed)}"
M = {t: dict(ds=N[t]["ds"], seed=N[t]["seed"], variants=dict({"R_new": N[t]["variants"][inc], "C10": C[t]["variants"][inc], "H(R_new)": N[t]["variants"]["H"]}, **({"R_old": O[t]["variants"][inc]} if O and t in O else {}))) for t in set(N) & set(C)}
for f in glob.glob(SP + "/hsi67/hsi_*_r67.json"):
    j = json.load(open(f)); t = key(j["ds"], j["desc"], j["seed"])
    if t in M and "HSI-VN" in j["variants"]: M[t]["variants"]["HSI-VN"] = {k: j["variants"]["HSI-VN"][k] for k in ("recall", "seg_FAR", "err_mean", "FL")}
for f in glob.glob(SP + "/w/t70sota/sota_*.json"):
    j = json.load(open(f)); t = key(j["ds"], j["desc"], j["seed"])
    if t in M: M[t]["variants"].update(j["variants"])
vs = ["R_new"] + (["R_old"] if O else []) + ["C10", "H(R_new)", "HSI-VN", "TAO26", "Xu21", "Claxton24", "top1", "oracle"]
keys = sorted(k for k, r in M.items() if all(v in r["variants"] for v in vs)); json.dump({k: M[k] for k in keys}, open(SP + "/w/e26_merged.json", "w"))
print(len(keys), "runs with every variant; seeds", sorted({M[k]["seed"] for k in keys}))
dss = sorted({M[k]["ds"] for k in keys}); g = lambda v, f: np.array([M[k]["variants"][v][f] for k in keys])
nab = lambda v: int((g(v, "seg_FAR") > A).sum()); wst = lambda v: max(np.mean([M[k]["variants"][v]["seg_FAR"] for k in keys if M[k]["ds"] == d]) for d in dss)
nav = lambda v: float(np.nanmean(g(v, "err_mean"))); msf = lambda v: float(g(v, "seg_FAR").mean())
def diff(a, b):
    d = g(a, "recall") - g(b, "recall"); rng = np.random.default_rng(0); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
valid = lambda v: wst(v) <= A and nab(v) <= 2
c1 = valid("R_new"); print(f"C1 validity R_new: worst dataset mean segFAR {wst('R_new'):.4f}, runs > alpha {nab('R_new')} -> {'MET' if c1 else 'NOT MET'}")
m, lo, hi = diff("R_new", "HSI-VN"); c2 = m >= 0.08 and lo > 0; print(f"C2 R_new - HSI-VN {m:+.4f} [{lo:+.4f}, {hi:+.4f}] -> {'MET' if c2 else 'NOT MET'}")
c3 = True
for v in ("TAO26", "Xu21", "Claxton24"):
    vv = valid(v); m, lo, hi = diff("R_new", v); o = (not vv) or lo > 0; c3 &= o
    print(f"C3 {v}: valid {vv} (worst {wst(v):.4f}, runs > alpha {nab(v)}); R_new - {v} {m:+.4f} [{lo:+.4f}, {hi:+.4f}] -> {'MET' if o else 'NOT MET'}")
c4 = nav("R_new") <= nav("HSI-VN"); print(f"C4 navigation R_new {nav('R_new'):.2f} vs HSI-VN {nav('HSI-VN'):.2f} -> {'MET' if c4 else 'NOT MET'}")
print("DECISION Entry 26:", "R_new CONFIRMED (C1-C4)" if c1 and c2 and c3 and c4 else "NOT CONFIRMED")
if O:
  m, lo, hi = diff("R_new", "R_old")
  print(f"Replication of Entry 23 (V1-V3, R_new vs R_old): runs>a {nab('R_new')} vs {nab('R_old')}, mean segFAR {msf('R_new'):.4f} vs {msf('R_old'):.4f}; recall {m:+.4f} [{lo:+.4f}, {hi:+.4f}]; nav {nav('R_new'):.2f} vs {nav('R_old'):.2f}")
s1 = valid("C10"); m, lo, hi = diff("C10", "R_new"); s2 = m >= -0.015
print(f"Safe point C10: S1 {'MET' if s1 else 'NOT MET'} (worst {wst('C10'):.4f}, runs>a {nab('C10')}); S2 {'MET' if s2 else 'NOT MET'} (C10 - R_new {m:+.4f} [{lo:+.4f}, {hi:+.4f}]); nav {nav('C10'):.2f} -> {'SAFE POINT CONFIRMED' if s1 and s2 else 'not confirmed'}")
PY
python3 hcal_board.py $SP/w/e26_merged.json --ref R_new --variants "R_new,C10,HSI-VN,TAO26,Xu21,Claxton24,top1,oracle" --md $SP/w/e26_board.md > /dev/null; head -n 14 $SP/w/e26_board.md
