# FINDINGS (evidence-levelled; every number cites a run in registry/runs.jsonl)

## F01 [S] HMM sequence filtering beats single-image retrieval on CMU and Nordland for all 4 descriptors
Protocol: PROTOCOL v1 (calibration-selected hyper-parameters, test = disjoint sequences, CI = sequence bootstrap).
R@1 single → HMM-τ-β (H1, β selected on calibration):
| Dataset (test frames / seqs) | NetVLAD | CosPlace | SALAD | MegaLoc | runs |
|---|---|---|---|---|---|
| Nordland (8100 / 18) | 0.364 → **0.970** (+0.605, CI [+0.506,+0.708]) | 0.652 → **0.987** | 0.811 → **0.986** | 0.821 → **0.985** | 20261127-006…009 |
| CMU 11 slices (14199 / 86) | 0.701 → **0.820** (+0.119 [+0.097,+0.141]) | 0.908 → **0.931** | 0.943 → **0.956** (+0.013 [+0.007,+0.020]) | 0.932 → **0.941** | 20261127-002…005 |
Caveat (A02): Nordland queries are frame-synchronised with the map, so the selected kernel mean (1 frame/step) is
oracle-like; see F04 (time-warp) before interpreting Nordland gains as motion-agnostic.

## F02 [S] The single-image-calibrated emission is far too confident inside the HMM (β* ≪ 1)
β selected on calibration for the τ-emission (τ fitted for single-image NLL): Nordland β*=0.2 for all four
descriptors; CMU β*∈{0.2 (NetVLAD), 0.35, 0.75, 0.75}. With β=1 (naive HMM, H0) NetVLAD/Nordland R@1 is 0.846 and
NLL 1.130 vs 0.970 / 0.203 with β*=0.2; CW@0.9 0.046 → 0.000. Interpretation [H]: consecutive (and spatially
adjacent) evidence is strongly dependent; under an AR(1) model β=0.2 ⇔ ρ≈0.67. Tested further in E15/H20.

## F03 [S] HMM vs tuned SeqSLAM (H22)
Both tuned on calibration (SeqSLAM: L∈{3,5,10,20}, enhancement∈{0,25}, velocity search). R@1 HMM-τ-β vs SeqSLAM:
Nordland NetVLAD 0.970 vs 0.855, CosPlace 0.987 vs 0.958, SALAD 0.986 vs 0.966, MegaLoc 0.985 vs 0.957;
CMU NetVLAD 0.820 vs 0.773, CosPlace 0.931 vs 0.924, SALAD 0.956 vs 0.955, MegaLoc 0.941 vs 0.945 (tie).
The HMM additionally gives calibrated beliefs (Nordland NLL 0.09 vs 5.7; SeqSLAM's scores are not probabilities).
SeqSLAM's local contrast enhancement had to be disabled on these dense maps (A21).

## F05 [S] Latent velocity (K=6 bins) did not beat a dev-tuned fixed kernel on synchronised/regular-speed data
Nordland SALAD 0.981 vs 0.986; CMU all descriptors worse (e.g. NetVLAD 0.632 vs 0.815 with old LLR — row
invalid for LLR, see A22, rerun pending). Expected if speed is nearly constant: extra states only dilute.
Decisive test is time-warp (E08).

## F06 [P] Synthetic AR(1) stop-and-go pilot (tests/synth_ar1_ia.py, 4 seeds, in-sample selection)
NLL: β=1 0.469, best fixed β 0.288, IA-HMM 0.222, oracle (1−ρ)/(1+ρ) 0.276; CW@0.9 0.0067 / 0.0023 / 0.0005 / 0.
Supports the derivation in THEORY.md T1 under its assumptions only.

## F04 [S] Time-warp exposes the oracle-motion inflation (H3) and a large, motion-agnostic HMM gain (H17)
Nordland, queries re-timed with random piecewise-constant speed ∈ {0 (stop), 0.5, 1, 2, 3} frames/step (seed 1).
| R@1 (NLL) | single | SeqSLAM | HMM fixed kernel | +latent velocity (LV) | +change emission (ME) | +info-aware β_t (IA) | ORACLE motion |
|---|---|---|---|---|---|---|---|
| SALAD | 0.809 (0.84) | 0.671 | 0.870 (0.55) | 0.897 (0.46) | 0.892 (0.50) | **0.902 (0.40)** | 0.961 (0.28) |
| NetVLAD | 0.430 (3.13) | — | 0.563 (2.82) | 0.697 (2.16) | 0.788 (1.35) | **0.820 (1.10)** | 0.896 (0.79) |
Runs 20261127-017 (SeqSLAM, SALAD), -020, -021. All paired CIs of LV, LV+ME, LV+ME+IA vs fixed exclude 0.
- H3 supported: synchronised HMM gain over single (SALAD +0.175, F01) drops to +0.061 for a fixed kernel (−65%).
- SeqSLAM (constant-velocity assumption) falls *below* single image (0.671 vs 0.809).
- H17 supported on NetVLAD: full model recovers (0.820−0.430)/(0.896−0.430)=84% of the oracle-motion gain;
  SALAD 61% (below the 70% threshold → partial).
- IA alone on a fixed kernel HURTS (SALAD 0.783 vs 0.871, run -017): removing duplicate evidence while the motion
  prior keeps moving lets belief drift. IA is only beneficial once the velocity state can represent the stop
  (M2×M3 interaction, H18 supported qualitatively).

## F07 [S] Latent velocity with hand-picked bins hurts on CMU (regular speed)
CMU NetVLAD: fixed 0.820 vs LV 0.713 (run -018). Root cause check: no reverse traversals (0% backward steps);
but per-sequence speed in map arc-length spans 0.7–4.9 m/frame, beyond the hand-picked bins (≤2.4). Fix:
bins from calibration-speed quantiles (E18v2, running).
