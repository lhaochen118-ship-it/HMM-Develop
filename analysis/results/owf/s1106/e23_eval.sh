#!/bin/bash
set -e
SP=/tmp/claude-0/-home-user-HMM-Develop/1345ea5d-f2ee-5042-813e-a6294e540411/scratchpad
cd $SP/runs/t64q; for tg in S5 HQ; do mkdir -p $SP/w/t64$tg/fr $SP/w/t64$tg/h $SP/w/t64$tg/j; done
for d in test64-*_out/results; do for tg in S5 HQ; do
  find $d -maxdepth 1 -name "fr_*_t64${tg}_b1.npz" -exec cp {} $SP/w/t64$tg/fr/ \; ; find $d -maxdepth 1 -name "hsifr_*_t64${tg}xms09_16.npz" -exec cp {} $SP/w/t64$tg/h/ \; ; find $d -maxdepth 1 -name "*_t64${tg}*.json" -exec cp {} $SP/w/t64$tg/j/ \; ;
done; done
for tg in S5 HQ; do echo $tg fr $(ls $SP/w/t64$tg/fr | wc -l) h $(ls $SP/w/t64$tg/h | wc -l); done
cd /home/user/HMM-Develop/analysis
V="H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5);H"
python3 owf_union.py $SP/w/t64S5/fr $SP/w/t64S5/h $SP/r61 $SP/w/un_t64S5.json --tag t64S5xms09_16 --ftag _t64S5 --jobs 4 --variants "$V" 2>/dev/null | tail -1
python3 owf_union.py $SP/w/t64HQ/fr $SP/w/t64HQ/h $SP/r61 $SP/w/un_t64HQ.json --tag t64HQxms09_16 --ftag _t64HQ --jobs 4 --variants "$V" 2>/dev/null | tail -1
OWF_VETO=0.5 python3 owf_union.py $SP/w/t64HQ/fr $SP/w/t64HQ/h $SP/r61 $SP/w/un_t64HQV.json --tag t64HQxms09_16 --ftag _t64HQ --jobs 4 --variants "$V" 2>/dev/null | tail -1
python3 - <<'PY'
import json, numpy as np
SP = "/tmp/claude-0/-home-user-HMM-Develop/1345ea5d-f2ee-5042-813e-a6294e540411/scratchpad"; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
A = json.load(open(SP + "/w/un_t64S5.json")); B = json.load(open(SP + "/w/un_t64HQ.json")); C = json.load(open(SP + "/w/un_t64HQV.json"))
M = {t: dict(ds=A[t]["ds"], seed=A[t]["seed"], variants={"R*": A[t]["variants"][inc], "C1": B[t]["variants"][inc], "C2": C[t]["variants"][inc],
         "H(R*)": A[t]["variants"]["H"], "H(C1)": B[t]["variants"]["H"], "H(C2)": C[t]["variants"]["H"]}) for t in set(A) & set(B) & set(C)}
json.dump(M, open(SP + "/w/e23_merged.json", "w")); keys = sorted(M); print(len(keys), "common runs (seeds", sorted({M[k]['seed'] for k in keys}), ")")
dss = sorted({M[k]["ds"] for k in keys}); g = lambda v, f: np.array([M[k]["variants"][v][f] for k in keys])
wst = lambda v: max(np.mean([M[k]["variants"][v]["seg_FAR"] for k in keys if M[k]["ds"] == d]) for d in dss)
nab = lambda v: int((g(v, "seg_FAR") > 0.05).sum()); msf = lambda v: float(g(v, "seg_FAR").mean()); nav = lambda v: float(np.nanmean(g(v, "err_mean")))
def ci(v):
    d = g(v, "recall") - g("R*", "recall"); rng = np.random.default_rng(0); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    return d, *np.percentile(bs, [2.5, 97.5])
for v in ("R*", "C1", "C2"): print(f"{v}: runs>alpha {nab(v)}, pooled mean segFAR {msf(v):.4f}, worst dataset {wst(v):.4f}, nav {nav(v):.2f} m, recall {g(v, 'recall').mean():.4f}")
d2, lo2, hi2 = ci("C2")
v1 = nab("C2") <= nab("R*") and msf("C2") <= msf("R*"); v2 = d2.mean() >= -0.006 and lo2 >= -0.010; v3 = nav("C2") <= nav("R*") + 0.5
v4 = all(np.mean([M[k]["variants"]["C2"]["seg_FAR"] for k in keys if M[k]["ds"] == d]) <= 0.05 for d in dss) and nab("C2") <= 2
print(f"V1 relative validity: C2 runs>alpha {nab('C2')} vs R* {nab('R*')}, mean segFAR {msf('C2'):.4f} vs {msf('R*'):.4f} -> {'MET' if v1 else 'NOT MET'}{' (SAFER: strictly fewer runs > alpha)' if nab('C2') < nab('R*') else ''}")
print(f"V2 recall cost C2 - R* {d2.mean():+.4f} [{lo2:+.4f}, {hi2:+.4f}] (wins {int((d2 > 1e-9).sum())} / ties {int((abs(d2) <= 1e-9).sum())} / losses {int((d2 < -1e-9).sum())}) -> {'MET' if v2 else 'NOT MET'}")
print(f"V3 navigation C2 {nav('C2'):.2f} vs R* {nav('R*'):.2f} + 0.5 -> {'MET' if v3 else 'NOT MET'}")
print(f"V4 absolute (reported): dataset means <= alpha and <= 2/144 runs > alpha -> {'MET' if v4 else 'NOT MET'}")
d1, lo1, hi1 = ci("C1")
n1 = nab("C1") <= nab("R*") and wst("C1") <= max(0.05, wst("R*")); n2 = d1.mean() >= -0.003 and lo1 >= -0.006; import os; n3 = nav("C1") <= nav("R*") + float(os.environ.get("N3TOL", "0"))
print(f"C1: N1' {'MET' if n1 else 'NOT MET'} (runs>alpha {nab('C1')} vs {nab('R*')}, worst {wst('C1'):.4f} vs max(0.05, {wst('R*'):.4f})); N2 {d1.mean():+.4f} [{lo1:+.4f}, {hi1:+.4f}] {'MET' if n2 else 'NOT MET'}; N3 {nav('C1'):.2f} vs {nav('R*'):.2f} {'MET' if n3 else 'NOT MET'}")
print("DECISION (Entry 23 rule: N1prime and N2 and N3 on C1 = NT+HQ; C2 = NT+HQ+veto reported only):", "C1 = OWF-HWA-S5-NT-HQ REPLACES R*" if n1 and n2 and n3 else "R* KEPT")
PY
python3 hcal_board.py $SP/w/e23_merged.json --ref R* --variants "R*,C1,C2,H(R*),H(C1),H(C2)" --md $SP/w/e23_board.md | head -14
