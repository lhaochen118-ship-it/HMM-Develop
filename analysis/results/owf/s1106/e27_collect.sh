#!/bin/bash
SP=${SP:?set SP to the working directory}
for tg in t64Q2 t64QS t67Q2 t67QS aQ2; do mkdir -p $SP/w/$tg/fr $SP/w/$tg/h; done
for d in $R/b64/rq64-*_out/results $R/b67/rq67-*_out/results $R/bdev/rqdev-*_out/results; do [ -d $d ] || continue
  for tg in t64Q2 t64QS t67Q2 t67QS aQ2; do find $d -maxdepth 1 -name "fr_*_${tg}_b1.npz" -exec cp {} $SP/w/$tg/fr/ \; ; find $d -maxdepth 1 -name "hsifr_*_${tg}xms09_16.npz" -exec cp {} $SP/w/$tg/h/ \; ; done; done
mkdir -p $SP/w/t70S5/fr $SP/w/t70S5/h
for d in $SP/runs/t70b/test70b-*_out/results $SP/runs/t70s5/t70ref-*_out/results; do [ -d $d ] || continue; find $d -maxdepth 1 -name "fr_*_t70S5_b1.npz" -exec cp {} $SP/w/t70S5/fr/ \; ; find $d -maxdepth 1 -name "hsifr_*_t70S5xms09_16.npz" -exec cp {} $SP/w/t70S5/h/ \; ; done
for tg in t64Q2 t64QS t67Q2 t67QS aQ2 t70S5; do echo $tg fr $(ls $SP/w/$tg/fr | wc -l) h $(ls $SP/w/$tg/h | wc -l); done
cd $A; V="H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5);H"
for tg in t64Q2 t64QS; do python3 owf_union.py $SP/w/$tg/fr $SP/w/$tg/h $SP/r61 $SP/w/un_$tg.json --tag ${tg}xms09_16 --ftag _$tg --jobs 4 --variants "$V" 2>/dev/null | tail -1; OWF_VETO=0.5 python3 owf_union.py $SP/w/$tg/fr $SP/w/$tg/h $SP/r61 $SP/w/un_${tg}V.json --tag ${tg}xms09_16 --ftag _$tg --jobs 4 --variants "$V" 2>/dev/null | tail -1; done
for tg in t67Q2 t67QS; do python3 owf_union.py $SP/w/$tg/fr $SP/w/$tg/h $SP/r67 $SP/w/un_$tg.json --tag ${tg}xms09_16 --ftag _$tg --jobs 4 --variants "$V" 2>/dev/null | tail -1; OWF_VETO=0.5 python3 owf_union.py $SP/w/$tg/fr $SP/w/$tg/h $SP/r67 $SP/w/un_${tg}V.json --tag ${tg}xms09_16 --ftag _$tg --jobs 4 --variants "$V" 2>/dev/null | tail -1; done
[ $(ls $SP/w/t70S5/fr | wc -l) -ge 144 ] && python3 owf_union.py $SP/w/t70S5/fr $SP/w/t70S5/h $SP/r67 $SP/w/un_t70S5.json --tag t70S5xms09_16 --ftag _t70S5 --jobs 4 --variants "$V" 2>/dev/null | tail -1
python3 owf_union.py $SP/w/aQ2/fr $SP/w/aQ2/h $SP/nc/v2,$SP/nc/e37 $SP/w/un_aq2.json --tag aQ2xms09_16 --ftag _aQ2 --jobs 4 --variants "$V" 2>/dev/null | tail -1
python3 $SP/rq_eval.py $SP
