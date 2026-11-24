#!/bin/bash
SP=/tmp/claude-0/-home-user-HMM-Develop/1345ea5d-f2ee-5042-813e-a6294e540411/scratchpad
cd $SP/runs/hsq; mkdir -p $SP/w/aHQ/fr $SP/w/aHQ/h $SP/w/aHQ/j
for d in devhq-*_out/results; do
  find $d -maxdepth 1 -name "fr_*HQ_b1.npz" -exec cp {} $SP/w/aHQ/fr/ \; ; find $d -maxdepth 1 -name "hsifr_*HQxms09_16.npz" -exec cp {} $SP/w/aHQ/h/ \; ; find $d -maxdepth 1 -name "owf_*HQ.json" -exec cp {} $SP/w/aHQ/j/ \; ;
done
echo fr $(ls $SP/w/aHQ/fr | wc -l) h $(ls $SP/w/aHQ/h | wc -l) json-with-lu $(grep -l '"lu"' $SP/w/aHQ/j/*.json | wc -l) of $(ls $SP/w/aHQ/j | wc -l)
cd /home/user/HMM-Develop/analysis
V="H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5);H"
python3 owf_union.py $SP/w/aHQ/fr $SP/w/aHQ/h $SP/nc/v2,$SP/nc/e37 $SP/w/un_hq.json --tag aHQxms09_16 --ftag _aHQ --jobs 4 --variants "$V" 2>/dev/null | tail -1
OWF_VETO=0.5 python3 owf_union.py $SP/w/aHQ/fr $SP/w/aHQ/h $SP/nc/v2,$SP/nc/e37 $SP/w/un_hq_v05.json --tag aHQxms09_16 --ftag _aHQ --jobs 4 --variants "$V" 2>/dev/null | tail -1
python3 - <<'PY'
import json, glob
SP = "/tmp/claude-0/-home-user-HMM-Develop/1345ea5d-f2ee-5042-813e-a6294e540411/scratchpad"; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
A = json.load(open(SP + "/w/un_dev_a.json")); B = json.load(open(SP + "/w/un_p0full.json")); C = json.load(open(SP + "/w/un_hq.json")); D = json.load(open(SP + "/w/un_hq_v05.json"))
O = {}
for f in glob.glob(SP + "/w/aHQ/j/owf_*_aHQ.json"):
    j = json.load(open(f)); t = f"{j['ds'].replace(':', '_')}_{j['desc']}_s{j['seed']}"; c = {str(r['eps']): r for r in j["runs"]["1.0"]["curve"]}
    O[t] = c
M = {}
for t in set(A) & set(B) & set(C) & set(D):
    if inc not in A[t]["variants"]: continue
    v = {"R*(S5)": A[t]["variants"][inc], "C1(NT)": B[t]["variants"][inc], "C9(NT+HQ)": C[t]["variants"][inc], "C10(NT+HQ+V)": D[t]["variants"][inc],
         "H(NT+HQ)": C[t]["variants"]["H"], "H(NT+HQ+V)": D[t]["variants"]["H"]}
    if t in O:
        for e in ("0.001", "1e-05"): v[f"OWF-HQ@{e}"] = dict(recall=O[t][e]["recall"], seg_FAR=O[t][e]["seg_FAR"], err_mean=float("nan"))
    M[t] = dict(ds=B[t]["ds"], seed=B[t]["seed"], variants=v)
json.dump(M, open(SP + "/w/cmp_hq.json", "w")); print(len(M), "common runs")
PY
python3 hcal_board.py $SP/w/cmp_hq.json --ref "R*(S5)" --variants "R*(S5),C1(NT),C9(NT+HQ),C10(NT+HQ+V),H(NT+HQ),H(NT+HQ+V)" --md $SP/w/cmp_hq.md > /dev/null; cat $SP/w/cmp_hq.md
