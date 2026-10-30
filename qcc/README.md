# QCC — Google "Verifiable quantum circuit compilation", Benchmark I (invsqrt)

Work log, tools and findings for problem 1 of
https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation (deadline 2027-01-20).
Competition data (kickmix.so, verifiers, paper) is **not** committed (rules); download it with
`kaggle competitions download google-verifiable-quantum-circuit-compilation -f <path>`.

## The task

Circuit on a 22-qubit register `x` mapping `|x>|0> -> exp(2 pi i / sqrt(x)) |x>|0>` for every
`x in [1, 3133452]`, phase error `<= 2^-24 / sqrt(x)` turns, scratch back to |0>, every input tested
64 times (200,540,928 shots; HMR outcomes seeded from SHA-256(circuit) + secret salt).

Cost `Q x C`: `Q` = qubit count, `C` = mean executed Toffolis per shot + T/4. Fine `Z_POW`
rotations cost `0.56 log2(1/eps) + 5.3` T each with `eps = pi * margin / n_rot`,
`margin = min_x (tol(x) - |error(x)|)` (turns). Reference cost 2,076,774.23.

Leaderboard score = geometric mean over the 3 tasks of `ref_cost / cost`. A submission is a zip
with `invsqrt.kmb`, `dqi.kmb`, `dfthcsos/` (angle_k_*.kmb + submission.npz). 5 submissions/day;
**submit only from one account (`nhatlong1103`)** — multiple accounts are against the rules.

## Public frontier (2026-10-30)

| task | best public | cost | ratio |
|---|---|---:|---:|
| invsqrt | `6dbb98b34c3b` (Ozer; mrmeows/busyaprime lineage), Q=62 | 100,940.6 | 20.57 |
| dqi | `2ed7ccf189f1` (manwithacat) | 4.033e11 | 60.6 |
| dfthcsos | `0d46767d0211` (manwithacat) | 3.378e8 | 9.93 |

All public circuits + manifest: Kaggle dataset `manwithacat/vqcc-apache-public-circuits`.
Write-up of the invsqrt lineage (what worked / failed): dataset `mrmeows/qcc-1375-open-circuits`.

Best invsqrt anatomy (from `ksim`): Q=62, 1331.48 mean Toffolis (1501 static), 7 T, 41 fine
rotations (~295 Toffoli-eq, 18% of C), margin 3.18e-12 turns, worst err/tol 0.99932 at x=161.
Only ~126 Toffolis execute after the last rotation: uncomputation is mostly measurement-based (HMR
+ Clifford phase repair). 62 qubits are simultaneously nonzero for ~15.7k instructions, so no qubit
can be saved by relabelling. Simple peephole (Toffolis acting as an affine function of live wires)
finds only 0.125 Toffoli/shot.

## Tools (`qcc/`)

| file | what |
|---|---|
| `ksim.py` | bit-sliced simulator of .kmx: all 3.1M inputs in ~15 s; per-rotation control bits, exact Clifford/T phase, executed Toffolis, qubit lifetimes, probe hook. Matches the official verifier exactly. |
| `refit_angles.py` | LP refit of rotation angles maximizing the margin (cutting planes, HiGHS); `--drop` tries removing rotations |
| `peephole.py` | finds Toffolis replaceable by CNOTs / deletable |
| `make_submission.py` | builds submission.zip |
| `kaggle_verify.py` | self-contained Kaggle CPU kernel running the official verifier (kickmix from PyPI, circuits embedded), launched through `automation/run_kernel.py` (restarts queue-stuck sessions) |

Local official verification: `PYTHONPATH=<kickmix dir> python3 verify_submission_invsqrt.py c.kmb`
(4 cores: ~10 min for the full 200M shots; 1M shots ~3 s).

## Log

See `LOG.md`.
