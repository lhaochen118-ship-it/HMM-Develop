#!/bin/bash
# Entry 27: generality sets re-run with the audited HQ code (hsq2, tag Q2) vs the tested code (hsq, tag HQ) and the old rule (S5), same runs.
SP=${SP:?set SP to the working directory}
for st in d10 d50 x n; do mkdir -p $SP/w/${st}Q2/fr $SP/w/${st}Q2/h; done
for d in $SP/runs/gq2/genq2-*_out/results; do for st in d10 d50 x n; do
  find $d -maxdepth 1 -name "fr_*_${st}Q2_b1.npz" -exec cp {} $SP/w/${st}Q2/fr/ \; ; find $d -maxdepth 1 -name "hsifr_*_${st}Q2xms09_16.npz" -exec cp {} $SP/w/${st}Q2/h/ \; ;
done; done
cd /home/user/HMM-Develop/analysis; V="H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5);H"
declare -A NC=( [d10]=$SP/nc/holes/d10 [d50]=$SP/nc/holes/d50 [x]=$SP/nc/nat [n]=$SP/nc/v2 )
for st in d10 d50 x n; do python3 owf_union.py $SP/w/${st}Q2/fr $SP/w/${st}Q2/h ${NC[$st]} $SP/w/ung_${st}Q2.json --tag ${st}Q2xms09_16 --ftag _${st}Q2 --jobs 4 --variants "$V" 2>/dev/null | tail -1; done
python3 - <<'PY'
import json, numpy as np
import os; SP = os.environ["SP"]; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
nm = dict(d10="holes 10 %", d50="holes 50 %", x="natural off-map", n="NCLT")
for st in ("d10", "d50", "x", "n"):
    J = {t: json.load(open(f"{SP}/w/ung_{st}{t}.json")) for t in ("Q2", "HQ", "S5")}
    ks = sorted(set(J["Q2"]) & set(J["HQ"]) & set(J["S5"])); row = []
    for t in ("Q2", "HQ", "S5"):
        r = np.mean([J[t][k]["variants"][inc]["recall"] for k in ks]); sf = np.array([J[t][k]["variants"][inc]["seg_FAR"] for k in ks])
        w = max(np.mean([J[t][k]["variants"][inc]["seg_FAR"] for k in ks if J[t][k]["ds"] == d]) for d in {J[t][k]["ds"] for k in ks})
        row.append(f"{r:.3f} / {w:.3f} / {int((sf > 0.05).sum())}")
    same = sum(abs(J["Q2"][k]["variants"][inc]["recall"] - J["HQ"][k]["variants"][inc]["recall"]) < 1e-12 for k in ks)
    print(f"| {nm[st]} ({len(ks)}) | " + " | ".join(row) + f" | {same}/{len(ks)} |")
PY
