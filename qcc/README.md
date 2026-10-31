# QCC — Google "Verifiable quantum circuit compilation", Benchmark I (invsqrt)

Tools for problem 1 of https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation.
**New chat: start with `handoff/03_HANDOFF.md`** (goal, decisions, locations, next steps); the task, cost
model, findings and evidence are in `handoff/01_SCIENTIFIC_FINDINGS.md`, operations in
`handoff/02_ENGINEERING_OPS_NOTES.md` (PDFs alongside). Competition data is not committed (rules).

| file | what |
|---|---|
| `ksim.py` | bit-sliced simulator of .kmx: all 3.1M inputs in ~15 s; per-rotation control bits, exact Clifford/T phase, executed Toffolis, qubit lifetimes, `probe` / `snap_at` hooks. Matches the official verifier exactly |
| `refit_angles.py` | LP refit of rotation angles maximizing the margin (cutting planes, HiGHS); `--drop` tries removing rotations |
| `peephole.py` | Toffolis replaceable by CNOTs (affine in live wires) or deletable |
| `redundancy.py` | is a wire affine/quadratic in the live wires; smallest support |
| `probes/` | `block.py` (is an instruction block a clean phase oracle), `ccz_fast.py` (Clifford-replaceable CCZ), `xbits_run.py` (x-bit parking) |
| `make_submission.py` | builds `submission.zip` (the only accepted file name) |
| `kaggle_verify.py` | self-contained Kaggle CPU kernel running the official verifier (kickmix from PyPI, circuits embedded), launched through `automation/run_kernel.py` |
| `wait_scores.sh` | waits until no submission is pending, prints the latest scores |

Local official verification: `PYTHONPATH=<kickmix dir> python3 verify_submission_invsqrt.py c.kmb`
(4 cores: ~10 min for 200M shots; 1M shots ~3 s).
