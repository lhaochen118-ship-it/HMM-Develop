# QCC invsqrt — experiment log

## 2026-10-30

1. Read paper (arXiv:2610.23832), verifier, evaluation page; pulled the public frontier and the
   mrmeows write-up. Reference design: normalize (leading zero pairs) → QROM cubic seed → one NR step
   → shift → phase → uncompute (Q=260, C=7988). Public best: Q=62, C=1628 (ratio 20.57).
2. Built `ksim` (bit-sliced simulator); reproduces the official numbers exactly.
3. Qubit lifetimes: peak 62 nonzero for 15.7k instructions → no free qubit by relabelling.
4. Peephole (affine-replaceable Toffolis, 3 HMR seeds): 42 never-firing CCZ in rare measurement
   branches; −0.125 Toffoli/shot. Not worth a submission alone.
5. Rotation LP refit: running.
