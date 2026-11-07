#!/bin/bash
# Second audit (Entry 28): union of the existing OWF frames with the causal HSI branch (HSI-VNc), every set.
SP=${SP:?set SP to the working directory}; A=/home/user/HMM-Develop/analysis; V="H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5);H"; cd $A
declare -A NC=( [t64Q2]=$SP/r61 [t64QS]=$SP/r61 [t64S5]=$SP/r61 [t67Q2]=$SP/r67 [t67QS]=$SP/r67 [t67S5]=$SP/r67 [t70S5]=$SP/r67
                [aQ2]=$SP/nc/v2,$SP/nc/e37 [d10Q2]=$SP/nc/holes/d10 [d50Q2]=$SP/nc/holes/d50 [xQ2]=$SP/nc/nat [nQ2]=$SP/nc/v2
                [aS5]=$SP/nc/v2,$SP/nc/e37 [d10S5]=$SP/nc/holes/d10 [d50S5]=$SP/nc/holes/d50 [xS5]=$SP/nc/nat [nS5]=$SP/nc/v2 )
for T in "$@"; do
  [ -d $SP/a2/$T/results ] || continue
  python3 owf_union.py $SP/w/$T/fr $SP/a2/$T/results ${NC[$T]} $SP/a2/un2_$T.json --tag ${T}xms09_16 --ftag _$T --hvar HSI-VNc --jobs 4 --variants "$V" 2>/dev/null | tail -1
  case $T in t64Q2|t64QS|t67Q2|t67QS) OWF_VETO=0.5 python3 owf_union.py $SP/w/$T/fr $SP/a2/$T/results ${NC[$T]} $SP/a2/un2_${T}V.json --tag ${T}xms09_16 --ftag _$T --hvar HSI-VNc --jobs 4 --variants "$V" 2>/dev/null | tail -1;; esac
done
