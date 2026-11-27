# ISSUES — audit of the legacy pipeline (IDs from Master Plan v2.0 §3.3)

Status: FIXED (in `hmmloc`, tested) · OPEN · N/A · MITIGATED

| ID | Issue | Status | Where / evidence |
|---|---|---|---|
| A01 | `predict_place` renormalised on-map mass to 1 → null mass not conserved | FIXED | `hmmloc/hmm.py::forward` implements Master Plan §3.4 equations; `tests/test_hmm_core.py` brute-force path enumeration (M=3,K=2,T=4, random emissions/β/null) matches to 1e-5; mass sums to 1 every step |
| A02 | v=1 on synchronised Nordland frames = oracle-like motion prior | MITIGATED | kernel mean/std selected on calibration only; latent-velocity HMM (no speed knowledge) reported separately; time-warp experiments E08 on video-rate Nordland (`nordseg`) |
| A03 | stride ≈45 destroys video-rate correlation | MITIGATED | new GPU kernel `kaggle/k01_nordseg` dumps contiguous stride-1 blocks (2×2500 frames × 4 seasons) for stride sweeps |
| A04 | τ per season fitted on mismatched map pairs | FIXED | single calibration on the *same* map as test, on disjoint calibration sequences |
| A05 | condition centroids fitted on test | N/A (CCBF parked) | — |
| A06 | odd/even split of the same traversal (leakage) | FIXED | splits by whole sequences / route blocks (`Episode.calib_seq`) |
| A07 | ±2 sampled frames at stride 45 ≈ ±90 raw frames | FIXED | Nordland tol = ±1 sampled frame at stride ≈7.9 (≈±8 raw ≤ Nordland** ±10); nordseg tol = ±10 raw |
| A08 | null likelihood = heuristic quantile 0.98/τ | FIXED | emission is a calibrated LLR vs the all-non-match baseline ⇒ l(null)=0 exactly (`hmmloc/emission.py`) |
| A09 | similarity/τ is a potential, not a likelihood | FIXED | logistic LLR with case-control prior correction (`LogisticLLR`, `fit_llr_multi`) |
| A10 | condition mixture with different temperatures not on a common scale | N/A (CCBF parked) | — |
| A11 | confidence = max posterior vs event correctness | FIXED | confidence = posterior mass in the tolerance neighbourhood of the prediction; event NLL = −log mass on positive set (`hmmloc/metrics.py`) |
| A12 | RobotCar translation parsing / CMU pose convention | FIXED (upstream) | nb15 dumps: RobotCar 4×4 [3,7,11], CMU last-3 = centre; sanity median q→nearest-ref 0.54 m |
| A13–A15 | CCBF theorem claims | OPEN (theory) | not used for any claim; see THEORY.md |
| A16 | P(on-map) ≠ top-1 correct | FIXED | off-map, ambiguity and confidence are evaluated separately |
| A17 | only R@1/ECE, frame-iid CI | FIXED | NLL/Brier/ECE/CW@0.9/AUROC/AURC + block bootstrap over sequences |
| A18 | Windows paths, no registry | FIXED | portable package + `research/registry/runs.jsonl` |
| A19 | state lacks orientation/scale/gaps | PARTIAL | map positions = arc length from map poses (metres); gaps capped; orientation enters GT only |
| A20 | geometry/retrieval double counting | OPEN | relevant only if M5 (6DoF verification) is pursued |
| A21 (new) | SeqSLAM local contrast enhancement collapses dense maps (L=1 → R@1 0.11 on CMU s7) | FIXED | SeqSLAM L/enhancement tuned on calibration like all methods |
| A22 (new, own code) | `fit_llr_multi` v0 mixed top-scoring negatives with random ones **without inclusion weights** → case-control correction invalid, LLR slope biased low (e.g. CMU/SALAD w=20 vs 1/τ=69) | FIXED | Horvitz–Thompson weights (hard negatives weight 1, random negatives weight n_rest/n_rand); runs 20261127-001…-005 and the first Nordland E01 runs: H2/H3/H4 rows INVALID (B01/B04/H0/H1 unaffected) |
| A23 (new, own code) | `load_nordseg(stride>1)` kept map positions in raw-frame units while kernels assume sampled-frame units → motion prior wrong by ×stride | FIXED | positions divided by stride, GT tolerance kept at ±10 raw frames; runs `E15_nordseg5_*` (first pass) INVALID, rerun |
| A24 (new, own code) | `ORACLE_motion` diagnostic in `e07_motionev` returns NaN NLL / implausible R@1 on `nordseg1-tw` (multi-block positions; no zero-mass guard in `forward_kernel_seq`) | OPEN | rows `ORACLE_motion` of runs E18_nordseg1-tw_* INVALID; not used in any finding |
