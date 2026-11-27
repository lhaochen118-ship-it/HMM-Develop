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

## F08 [S] Cross-dataset main table (E18, registry-generated: reports/RESULTS_TABLES.md, figures/fig1)
IA-HMM (dev-selected by calibration NLL among {fixed kernel, LV, LV+ME, LV+ME+IA}) ≥ single image in all 16
dataset×descriptor cells; vs tuned SeqSLAM: better in 12/16, within 0.6 pt in the other 4 (CMU MegaLoc 0.941 vs 0.947,
RobotCar MegaLoc 0.980 vs 0.984, RobotCar CosPlace 0.857 vs 0.858, Nordland-sync ties at ~0.98).
Under variable speed (time-warp seed 1) SeqSLAM drops below single image for 3/4 descriptors while IA-HMM gains
+0.08…+0.40 R@1 (NetVLAD 0.430→0.827, CosPlace 0.695→0.915, SALAD 0.808→0.901, MegaLoc 0.832→0.917).
Dev selection behaves sensibly: fixed kernel on constant-speed CMU, LV(+ME/IA) under time-warp.

## F09 [S] Gains concentrate where single-image evidence is weak (H2/H23)
Per condition (runs PC_*): Nordland winter NetVLAD 0.120→0.954, spring 0.372→0.977; SALAD winter 0.755→0.986.
RobotCar NetVLAD night 0.153→0.229, night-rain 0.071→0.121 (short ~8-frame sequences cap the gain); SALAD night-rain
0.964→0.993. Fine 6DoF thresholds (0.25 m/0.5 m) do not change with retrieval-only poses (needs M5 geometry).

## F10 [S] Fixed-lag smoothing (H21) — partially supported
R@1 gain over causal filtering at lag 10: CMU NetVLAD +0.043 [CI +0.033,+0.054]; Nordland NetVLAD +0.016
[+0.012,+0.020]; RobotCar +0.009 (n.s., short sequences). Threshold ≥2 pt on ≥2 datasets → met on 1 ⇒ partial.

## F11 [S] Information-aware weighting ALONE does not beat a dev-tuned fixed β on constant-speed data (H20 standalone refuted)
CMU (14 Hz, no stops) with a fixed kernel: NetVLAD IA 0.810 vs fixed-β 0.820 (dR1 CI [−0.020,−0.003]); SALAD
0.952 vs 0.955. Keyframing also no better. Together with F04: IA is useful only when the HMM can also represent
speed changes (LV+ME): time-warp NetVLAD LV+ME 0.805 → LV+ME+IA 0.827 (s1), 0.747 → 0.822 (s2).

## F12 [S] Off-map (map holes, Nordland SALAD, 21% of query frames unmapped; run 20261127-031)
AUROC of off-map detection: single-image SUE 0.880, single-frame LLR null 0.643, HMM + legacy quantile null 0.988
(FPR@95TPR 0.029), HMM + calibrated-LLR null 0.979 (FPR 0.055). Temporal filtering is what makes off-map
detection work (+0.10 AUROC over SUE); the calibrated LLR null (M1) did NOT beat the tuned quantile null
(H7 not supported on this test).

## F13 [S] Dose-response on REAL video-rate Nordland (k01; strides 1/2/5 of the 1-fps stream) — H5 [S+], H20 [S+ at high rate]
| stride | descriptor | β* (dev) | R@1 β=1 | R@1 fixed β* | R@1 IA | NLL fixed β* → IA (paired CI of ΔNLL) |
|---|---|---|---|---|---|---|
| 1 | NetVLAD | 0.1 | 0.683 | 0.972 | 0.976 | 0.130 → 0.108 ([−0.045, −0.001]) |
| 2 | NetVLAD | 0.35 | 0.738 | 0.932 | **0.971** (ΔR@1 CI [+0.011,+0.073]) | 0.311 → 0.124 ([−0.451, −0.030]) |
| 5 | NetVLAD | 0.35 | 0.830 | 0.947 | 0.948 | 0.212 → 0.258 (n.s.) |
| 1 | SALAD | 0.1 | 0.879 | 0.982 | 0.986 | 0.064 → 0.042 ([−0.057, +0.001]) |
| 2 | SALAD | 0.2 | 0.902 | 0.988 | 0.987 | 0.056 → 0.044 ([−0.025, +0.001]) |
| 5 | SALAD | 0.35 | 0.938 | 0.984 | 0.987 | 0.064 → 0.062 (n.s.) |
The cost of ignoring dependence (β=1) grows monotonically with frame rate; the information-aware weight helps only
where consecutive frames are redundant (high rate, tunnels/stations) and reduces to fixed β at low rate — exactly
predictions P2/P3 of THEORY.md T1. Stride-5/2 runs are the A23-fixed reruns (queue 4).

## F14 [S] Place-level gains transfer to coarse 6DoF; fine pose needs geometry (E30-lite)
(5 m,10°) with top-1 reference pose: CMU NetVLAD 0.690 → 0.808 (HMM), SALAD 0.934 → 0.946; RobotCar NetVLAD
0.643 → 0.699 (all test frames). Posterior-weighted position interpolation adds ≤ +0.04 at (0.5 m,5°)
(CMU SALAD 0.214 → 0.254) — fine-pose gains require M5 (local features + PnP).

## F15 [S] Final fair-protocol summary (A25 grid; 33 E18 cells incl. seeds, video-rate and real 4Seasons)
IA-HMM (dev-selected) ≥ single image in 33/33 cells; vs tuned SeqSLAM 27 W / 5 T (±0.5 pt) / 1 L (CMU MegaLoc −0.6);
vs fixed-kernel HMM under the same protocol 18 W / 13 T / 2 L. Real variable-speed data (4Seasons, kernels k02/k03):
office_loop NetVLAD 0.512 → 0.836 (SeqSLAM 0.702, fixed HMM 0.792), CosPlace 0.814 → 0.924 (fixed 0.853, CI vs fixed
[+0.023,+0.117]), SALAD 0.932 → 0.980; countryside SALAD 0.659 → 0.851, MegaLoc 0.724 → 0.888 (fixed 0.824, CI
[+0.034,+0.082]). Earlier 4Seasons fixed-kernel numbers (0.582 NetVLAD) were handicapped by the grid (A25) and are superseded.

## F16 [S] When does the latent-velocity state help? A displacement/spacing regime (root cause of F07)
CMU NetVLAD, R@1 LV+ME vs fixed kernel as query frames are sub-sampled (per-frame displacement / map node spacing
≈ 1, 3, 6): 0.734 vs 0.820 (−0.086) → 0.771 vs 0.807 (−0.036) → 0.819 vs 0.813 (+0.006; NLL LV+ME+IA 0.677 vs 0.723,
dev-selection switches to LV+ME+IA). At ~1 node/frame the per-frame map displacement is quantised and jittery, not a
persistent regime, so a memoryless broad kernel is the better HMM transition; persistence (vel_stay 0→0.95) worsens calib
NLL monotonically (1.06→1.51). Refuted alternatives: metric-vs-arc-length speed units (A26: negligible change), node-density
bias of the kernel (cell-length correction: 1.265→1.260 NLL), velocity prior (calibration histogram: 0.733→0.735).
Runs: E18_cmu-q3_*, E18_cmu-q6_*, plus inline diagnostics recorded in this entry.
