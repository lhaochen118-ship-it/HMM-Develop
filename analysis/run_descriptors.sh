#!/bin/bash
# Usage: run_descriptors.sh <dump_rc_nord> <dump_cmu> <desc1,desc2,...>   (runs eval_all for every descriptor x dataset, 3 in parallel)
D1=$1; D2=$2; IFS=',' read -ra DS <<< "$3"; cd "$(dirname "$0")"; mkdir -p logs
jobs_run() { while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 5; done; }
for d in "${DS[@]}"; do
  for ds in rc nord cmu; do
    dump=$D1; [ "$ds" = cmu ] && dump=$D2
    [ -f "$dump/$d/$( [ $ds = rc ] && echo rc_q || ([ $ds = nord ] && echo nord_summer || echo cmu_s7_q)).npy" ] || { echo "skip $d/$ds (no dump)"; continue; }
    jobs_run; (python3 eval_all.py "$dump" "$ds" "$d" > "logs/eval_${ds}_${d}.log" 2>&1; echo "done $d/$ds") &
  done
done
wait; python3 summarize.py 0.05 > /dev/null; python3 summarize.py 0.1 > /dev/null; echo ALL_DONE
