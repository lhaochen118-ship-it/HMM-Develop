#!/bin/bash
# usage: research/run_queue.sh <parallel> <jobfile>   (each line: module args...; log -> research/logs/<tag>.log)
P=$1; F=$2
cat "$F" | xargs -P "$P" -L 1 bash -c 'tag=$(echo "$@" | tr " /" "__"); timeout 7200 python3 -m "$@" > research/logs/Q_${tag}.log 2>&1; echo "done $tag"' _
