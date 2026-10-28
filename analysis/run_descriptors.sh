#!/bin/bash
# Usage: run_descriptors.sh <dump_rc_nord> <dump_cmu> <dump_msls|-> <desc1,desc2,...>
# Runs eval_all for every descriptor x dataset (3 in parallel); a dataset is skipped when its dump is missing.
D1=$1; D2=$2; D3=$3; IFS=',' read -ra DS <<< "$4"; cd "$(dirname "$0")"; mkdir -p logs
jobs_run() { while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 5; done; }
probe() { case $1 in rc) echo "$D1/$2/rc_q.npy";; nord) echo "$D1/$2/nord_summer.npy";; cmu) echo "$D2/$2/cmu_s7_q.npy";; msls) echo "$D3/$2/msls_cph_q.npy";; esac; }
dump_of() { case $1 in cmu) echo "$D2";; msls) echo "$D3";; *) echo "$D1";; esac; }
for d in "${DS[@]}"; do
  for ds in msls cmu rc nord; do
    [ -f "$(probe $ds $d)" ] || { echo "skip $d/$ds (no dump)"; continue; }
    jobs_run; (python3 eval_all.py "$(dump_of $ds)" "$ds" "$d" > "logs/eval_${ds}_${d}.log" 2>&1; echo "done $d/$ds $?") &
  done
done
wait; python3 summarize.py 0.05 > /dev/null; python3 summarize.py 0.1 > /dev/null; echo ALL_DONE
