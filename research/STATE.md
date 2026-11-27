# STATE (update at every session end) — last update 2026-11-27 ~21:00 UTC

**Branch:** `claude/nice-fermi-l7bzd6` · **Phase:** 6–7 (33-cell fair-protocol evaluation incl. 2 real 4Seasons routes done at [S]; report/handoff PDFs in research/reports/)
**Gates:** G0 ✅ · G1 ✅ · G2 ✅ ([S], H1 on 3 datasets) · G3 parked (CCBF) · G4 ✅ ([S]: dependence/overconfidence and
oracle-motion inflation supported by interventions on ≥2 datasets — F02, F04, E15 nordseg) · G5 partial (no learned-sequence
baseline, no held-out 4th dataset) · G6 not requested

## Feature bank (all reproducible from Kaggle kernels of owner nhatlong1103)
nb15a/b/c/d dumps (Nordland stride≈8, RobotCar v2, CMU 11 slices; 6 descriptors) + `hmm-k01-nordseg` (Nordland stride-1,
2×2500 frames × 4 seasons × SALAD/MegaLoc/NetVLAD/CosPlace; ~1 T4-hour). Local path `hmmloc/data.py::FB` (env HMMLOC_FB).

## Next 3 tasks
1. Learned-sequence baseline (JIST/SeqVLAD weights needed — check Kaggle datasets/licences) or document as blocker.
2. Held-out real stop-and-go dataset (4Seasons cross-traversal: extract a second traversal of `office_loop`/`old_town`
   on Kaggle T4, ~10 min each) to test LV+ME+IA without synthetic time-warp (H17 on real data).
3. M5: posterior-guided LightGlue+PnP on RobotCar/CMU (bundle has SuperPoint/LightGlue/pycolmap) under a fixed
   matching budget; plus multi-seed time-warp for all descriptors and Holm correction.

## Known open issues
A20 (geometry double counting, only if M5), A24 (oracle-motion diagnostic NaN on nordseg time-warp).
## Notes
- Kaggle tokens live only in the session scratchpad (never in repo). Only account `nhatlong1103` was used (owner of the
  private datasets); ~1 T4 GPU-hour consumed this session.
