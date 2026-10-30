# QCC invsqrt — experiment log

## 2026-10-30

1. Read paper (arXiv:2610.23832), verifier, evaluation page; pulled the public frontier and the
   mrmeows write-up. Reference design: normalize (leading zero pairs) → QROM cubic seed → one NR step
   → shift → phase → uncompute (Q=260, C=7988). Public best: Q=62, C=1628 (ratio 20.57).
2. Built `ksim` (bit-sliced simulator); reproduces the official numbers exactly.
3. Qubit lifetimes: peak 62 nonzero for 15.7k instructions → no free qubit by relabelling.
4. Peephole (affine-replaceable Toffolis, 3 HMR seeds): 42 never-firing CCZ in rare measurement
   branches; −0.125 Toffoli/shot. Not worth a submission alone.
5. Rotation LP refit (exact, cutting planes in units of 2^-40 turns): margin 3.17654e-12 → 3.17655e-12.
   The 41 angles are already LP-optimal; the margin is pinned by ~52 inputs spread over every
   shift s (619 within 2x of the minimum), so no cheap local fix raises it.
6. Rotation anatomy: two phase streams. A (15 rotations on q28, weights 2^-18..2^-4 turns) and B
   (26 rotations, 2^-36..2^-11). 8 weights are duplicated (2^-18..2^-11) and 14 rotations fire
   only for small x (x <= 2^20 ... x <= 252) because each stream must cover the s-shift range.
   One merged stream would need 33 rotations (−55 Toffoli-eq, −3.4%), but stream A's seed bits are
   not reconstructible at stream-B time (also found by mrmeows), so merging needs a second lookup.
7. Qubit 62→61 search: a greedy cover of all 15,720 peak instructions needs 5 freed idle
   intervals (q23 x3, q43, q32). None of those values is affine/quadratic in the live wires, nor a
   function of <= 3 live wires at the recompute points → no cheap erase/recompute. Dead end.
8. Kaggle verification kernel (yuan1103, kickmix from PyPI) reproduces the official cost exactly:
   100,940.5617, 800 s for 200M shots.
9. Baseline submission (best public circuits for all three tasks) from nhatlong1103:
   **public LB 23.13505** (= GM of 20.57, 60.6, 9.93; the pipeline reproduces the official score).
10b. CCZ whose full product a·b·c never fires (the first peephole only tested a·b): 48 stable over
    4 HMR seeds, all inside rarely executed measurement branches → −0.63 Toffoli/shot (−0.04%).
    Not worth a submission.
10. Idle x-register bits (q0–q13 idle across most of the peak) and q23 at the ends of their idle
    intervals: none is a quadratic function of the live wires → cannot be parked/recomputed cheaply.

### Assessment (night of 2026-10-30)

The public invsqrt circuit sits at a tight local optimum: rotation angles are LP-optimal, no
cheap peephole, no qubit can be freed (relabelling or quadratic recompute), and the only visible
structural slack — the 8 duplicated rotation weights of the two phase streams (−3.4%) — needs the
seed bits again at stream-B time, which costs a second lookup (~186 Toffolis). A from-scratch
"normalize → 256-entry seed → cubic correction → single stream" design estimates at ~1,700
Toffoli-eq at 62–70 qubits, i.e. not better than 1,628 @ 62. Big gains on this task need a new
idea that removes most of the floating-point overhead (input normalization ~230 Toffolis, shift
routing, 14 rarely-firing high-weight rotations ~100 Toffoli-eq), which none of the variants
studied here achieves.

### Toffoli budget of the public best (executed mean per shot, by instruction window)

| instructions | Toffolis | what |
|---|---:|---|
| 0–1k | 92 | normalization forward (prefix-zero AND chain, binary s by XOR, CSWAP shifts) |
| 1k–15k | ~160 | seed/coefficient lookup as a shared-monomial ANF (≈38 monomial wires live → the Q=62 peak) |
| 15k–16k | 72 | phase stream A (seed taps, 15 rotations, 2 routing CSWAPs per bit) |
| 16k–21k | ~51 | |
| 21k–26k | ~436 | main arithmetic and phase stream B (26 rotations) |
| 28k–37k | ~446 | uncomputation of the arithmetic |
| 44k–48k | ~74 | normalization reverse |

Uncompute ≈ compute for the in-place adders; a measurement-only erasure would need the XAG wires
kept alive (hundreds of qubits), so at Q·C the low-Q recompute point is the right one.

### Most promising lever found (not yet exploited)

Occupancy over the arithmetic and uncompute region (19k–31k instructions) averages ~56 of 62
qubits; the 62 peaks there are short spikes (transient adder ANDs), except 33k–34k and 17k–18k.
An arithmetic block rebuilt to (a) flatten those spikes and (b) keep adder carries in the 4–8 spare
qubits would let the in-place adders be undone by measurement + Clifford repair instead of
subtraction, attacking the ~446-Toffoli uncompute (27% of C) without raising Q. This needs a
re-implementation of the arithmetic (seed → cubic correction → stream B) with our own generator;
the recovered gate list cannot be patched that deeply.
