#!/bin/bash
SP=/tmp/claude-0/-home-user-HMM-Develop/1345ea5d-f2ee-5042-813e-a6294e540411/scratchpad
cd $SP/runs/ghq
for st in d10 d50 x n; do mkdir -p $SP/w/${st}HQ/fr $SP/w/${st}HQ/h; done
for d in genhq-*_out/results; do for st in d10 d50 x n; do
  find $d -maxdepth 1 -name "fr_*_${st}HQ_b1.npz" -exec cp {} $SP/w/${st}HQ/fr/ \; ; find $d -maxdepth 1 -name "hsifr_*_${st}HQxms09_16.npz" -exec cp {} $SP/w/${st}HQ/h/ \; ;
done; done
cd /home/user/HMM-Develop/analysis
V="H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5);H"
declare -A NC=( [d10]=$SP/nc/holes/d10 [d50]=$SP/nc/holes/d50 [x]=$SP/nc/nat [n]=$SP/nc/v2 )
for st in d10 d50 x n; do
  for tg in S5 HQ; do python3 owf_union.py $SP/w/${st}${tg}/fr $SP/w/${st}${tg}/h ${NC[$st]} $SP/w/ung_${st}${tg}.json --tag ${st}${tg}xms09_16 --ftag _${st}${tg} --jobs 4 --variants "$V" 2>/dev/null | tail -1; done
  python3 - $st <<'PY'
import json, sys
SP = "/tmp/claude-0/-home-user-HMM-Develop/1345ea5d-f2ee-5042-813e-a6294e540411/scratchpad"; st = sys.argv[1]; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
A = json.load(open(f"{SP}/w/ung_{st}S5.json")); B = json.load(open(f"{SP}/w/ung_{st}HQ.json"))
M = {t: dict(ds=A[t]["ds"], seed=A[t]["seed"], variants={"R*": A[t]["variants"][inc], "C9": B[t]["variants"][inc]}) for t in set(A) & set(B)}
json.dump(M, open(f"{SP}/w/cmpg_{st}.json", "w")); print(st, len(M), "common runs")
PY
  python3 hcal_board.py $SP/w/cmpg_${st}.json --ref R* --variants "R*,C9" --md $SP/w/cmpg_${st}.md > /dev/null; echo "== $st"; grep -E "pooled|cmu|nord|^\| C9" $SP/w/cmpg_${st}.md
done
