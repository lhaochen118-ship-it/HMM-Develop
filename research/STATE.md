# STATE (update at every session end) — last update 2026-11-27 ~19:00 UTC

**Branch:** `claude/nice-fermi-l7bzd6` · **Phase:** 3–5 (feasibility done on 2 datasets, method IA-HMM in test)
**Gates:** G0 ✅ (tests/test_hmm_core.py) · G1 ✅ (single-image R@1 reproduces dump sanity logs) ·
G2 ✅ provisional (H1 supported on Nordland + CMU, CI excl. 0) · G3 parked (CCBF) · G4 in progress · G5/G6 open

## Running / pending compute
- Kaggle `nhatlong1103/hmm-k01-nordseg` (T4, Nordland stride-1 blocks, 4 descriptors) — RUNNING since ~17:12 UTC.
  When COMPLETE: `kaggle kernels output nhatlong1103/hmm-k01-nordseg -p $FB/hmm-k01-nordseg` (FB = feature-bank dir,
  see `hmmloc/data.py::FB`), then run E15/E33 on `nordseg1/2/5`.
- Local CPU: E01 RobotCar ×4 descriptors; E08 time-warp Nordland SALAD.

## Next 3 tasks
1. E08 time-warp (H3/H17/H20) on SALAD + NetVLAD; E15 IA-HMM on CMU (14 Hz) and nordseg.
2. Rerun E01 CMU H2–H4 rows with fixed LLR (A22); E12 off-map holes (H7/H19); fixed-lag (H21).
3. Phase 4 failure taxonomy + oracle swap; consolidate FINDINGS → final report; update Master Plan §1 with evidence.

## Blockers / notes
- Kaggle tokens live only in the session scratchpad (never in repo). Feature bank is re-downloadable from kernels
  `dive-vpr-nb15a..d-dump` (owner nhatlong1103) in ~4 min.
- Multi-account use: only `nhatlong1103` (owner of the private datasets) is used so far; other accounts must only
  be used if Kaggle's terms and the account owners permit it (Ops Plan v1.3 §2).
