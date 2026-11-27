# PROTOCOL (v1, locked 2026-11-27 before any HMM test-set result was inspected for method selection)

## Inputs allowed at query time
One monocular camera stream (query descriptors, timestamps/order). Map: reference images, their descriptors and
their poses (for graph construction). **No** query GT pose, GPS, IMU, LiDAR, second camera. Oracle variants
(GT motion, GT condition, GT emission) are diagnostics only and are labelled `oracle`.

## Datasets / episodes (feature bank = Kaggle dumps nb15a–d, k01; fp16 L2-normalised descriptors)
| Episode | Map | Queries | Positives (GT) | Sequences | Calibration split |
|---|---|---|---|---|---|
| Nordland (`nord`) | summer, 4500 frames uniformly sub-sampled from 35,768 common frames (stride≈7.9) | spring, fall, winter (same 4500 frame ids) | |Δidx|≤1 sampled frame (≈±8 raw frames) | each season cut in 10 route blocks of 450 frames (30 sequences) | blocks b with b mod 3 = 0 (12 seq.) |
| Nordland video-rate (`nordseg`) | summer, 2 contiguous blocks × 2500 frames (common idx 10000–12499, 25000–27499) | spring/fall/winter | |Δraw frame|≤10 | sub-sequences of 500 frames | sub-seq id mod 3 = 0 |
| RobotCar Seasons v2 (`rc`) | overcast-reference rear, 6954 imgs, ordered by timestamp, NVM poses | 1906 rear train queries (9 conditions) | ‖ΔC‖≤5 m and Δθ≤30° | split at condition change or gap>2 s (225 seq.) | seq id mod 3 = 0 |
| Extended CMU Seasons (`cmu`) | per slice (6,7,8,10,11,12,13,21,22,23,24) database c0 | dated query c0 with GT | ‖ΔC‖≤5 m and Δθ≤30° | (slice, date), split at gap>2 s | (date index + slice) mod 3 = 0 |

Frames with no positive are excluded from R@1/NLL (reported as `n`); they are used only for off-map analyses.

## Selection rule
Every tunable (τ, LLR weights, kernel mean/std, β, velocity bins, IA (β₀,κ), SeqSLAM L/enhancement,
keyframe threshold) is selected on calibration sequences by event NLL (SeqSLAM: by R@1, since it has no
probabilistic output). Test sequences are evaluated once per (method, config).

## Metrics
R@1 (top-1 on-map node in positive set), event NLL = −log Σ_{j∈pos} b(j) (clip 1e-6; null mass counts as
error), confidence q = posterior mass within the map-only tolerance neighbourhood of the prediction,
ECE (15 bins), Brier, CW@0.9 = P(q>0.9 ∧ wrong), AUROC(q→correct), AURC. CIs: bootstrap over whole test
sequences (1000 resamples); paired differences use the same resampled sequences.

## Causal modes
`online` = filtering (o_{1:t}); `fixed-lag ℓ` = o_{1:t+ℓ} (reported separately with latency ℓ frames).
