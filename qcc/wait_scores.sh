#!/bin/bash
# Poll the competition submissions until none is pending; print the latest rows. Exits when done.
export KAGGLE_API_TOKEN=$(cat ~/.kaggle/tok_nhatlong1103)
C=google-verifiable-quantum-circuit-compilation
while true; do
  out=$(kaggle competitions submissions $C 2>&1 | head -8)
  if ! echo "$out" | grep -qi "pending"; then echo "$out"; exit 0; fi
  sleep 120
done
