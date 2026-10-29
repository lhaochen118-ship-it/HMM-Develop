# Certified sequential localization — tables (auto-generated)

Excursion FAR = share of H-frame off-map excursions (leave-block-out) with any accepted frame; mean over 6 descriptors x 3 block grids, (max over runs), [worst condition, mean over runs]. alpha = 0.05; H = 10 frames (RobotCar: 5, its queries are 9-frame snippets). Power = share of correctly matched on-map frames accepted; latency = median frames to the first correct acceptance.


## Table 1: validity

| method | RobotCar-Seasons | CMU-Seasons | Nordland | 4Seasons office | 4Seasons old town | 4Seasons countryside | Boreas |
|---|---|---|---|---|---|---|---|
| per-frame (SelfCal) | 0.019 (0.089) [0.069] | 0.027 (0.072) [0.054] | 0.019 (0.039) [0.033] | 0.013 (0.058) [0.034] | 0.015 (0.044) [0.021] | 0.018 (0.068) [0.030] | 0.004 (0.012) [0.009] |
| run, no odometry (exp11) | 0.016 (0.089) [0.072] | 0.027 (0.066) [0.058] | 0.033 (0.076) [0.053] | 0.019 (0.042) [0.051] | 0.016 (0.046) [0.024] | 0.015 (0.058) [0.025] | 0.006 (0.017) [0.016] |
| odometry run | 0.017 (0.109) [0.064] | 0.027 (0.078) [0.056] | 0.019 (0.048) [0.032] | 0.021 (0.042) [0.047] | 0.013 (0.038) [0.020] | 0.015 (0.055) [0.024] | 0.007 (0.017) [0.016] |
| ours: anchored | 0.016 (0.094) [0.067] | 0.022 (0.051) [0.052] | 0.020 (0.039) [0.033] | 0.020 (0.039) [0.049] | 0.014 (0.037) [0.022] | 0.015 (0.068) [0.025] | 0.006 (0.016) [0.017] |
| ours: anchored, heading-free | 0.017 (0.094) [0.068] | 0.023 (0.058) [0.052] | 0.020 (0.039) [0.033] | 0.020 (0.053) [0.048] | 0.014 (0.046) [0.023] | 0.015 (0.055) [0.024] | 0.006 (0.013) [0.017] |
| label-calibrated (ANCH stat., labels of 2 benign conditions) | 0.044 (0.122) [0.125] | 0.044 (0.090) [0.089] | 0.016 (0.030) [0.024] | 0.022 (0.044) [0.038] | 0.010 (0.040) [0.010] | 0.025 (0.066) [0.025] | 0.026 (0.039) [0.063] |

## Table 2: power

| method | RobotCar-Seasons | CMU-Seasons | Nordland | 4Seasons office | 4Seasons old town | 4Seasons countryside | Boreas |
|---|---|---|---|---|---|---|---|
| per-frame (SelfCal) | 0.77 / 0 | 0.62 / 0 | 0.44 / 27 | 0.31 / 33 | 0.43 / 28 | 0.19 / 4 | 0.35 / 24 |
| run, no odometry (exp11) | 0.67 / 2 | 0.78 / 6 | 0.73 / 23 | 0.76 / 8 | 0.70 / 28 | 0.29 / 8 | 0.67 / 7 |
| odometry run | 0.67 / 2 | 0.77 / 4 | 0.73 / 24 | 0.76 / 4 | 0.64 / 30 | 0.31 / 6 | 0.67 / 5 |
| ours: anchored | 0.68 / 2 | 0.82 / 4 | 0.86 / 24 | 0.83 / 4 | 0.77 / 28 | 0.37 / 6 | 0.71 / 5 |
| ours: anchored, heading-free | 0.65 / 2 | 0.80 / 5 | 0.86 / 24 | 0.81 / 5 | 0.75 / 28 | 0.35 / 6 | 0.69 / 6 |
| label-calibrated (ANCH stat., labels of 2 benign conditions) | 0.77 | 0.87 | 0.87 | 0.85 | 0.86 | 0.49 | 0.79 |

## Table 3: validity across alpha and horizon (ours: ANCH; mean excursion FAR over descriptors and grids)

| dataset | H | alpha=0.01 | alpha=0.05 | alpha=0.1 | null segments |
|---|---|---|---|---|---|
| RobotCar-Seasons | 5 | 0.002 | 0.016 | 0.033 | 466 |
| RobotCar-Seasons | 8 | 0.000 | 0.015 | 0.031 | 288 |
| CMU-Seasons | 10 | – | 0.022 | 0.059 | 70 |
| CMU-Seasons | 30 | – | 0.035 | 0.031 | 22 |
| CMU-Seasons | 60 | – | – | 0.072 | 13 |
| Nordland | 10 | 0.001 | 0.020 | 0.042 | 198 |
| Nordland | 30 | – | 0.023 | 0.044 | 66 |
| Nordland | 60 | – | 0.005 | 0.040 | 33 |
| 4Seasons office | 10 | 0.002 | 0.020 | 0.047 | 108 |
| 4Seasons office | 30 | – | 0.013 | 0.041 | 31 |
| 4Seasons office | 60 | – | 0.010 | 0.033 | 18 |
| 4Seasons old town | 10 | 0.002 | 0.014 | 0.036 | 148 |
| 4Seasons old town | 30 | – | 0.010 | 0.026 | 45 |
| 4Seasons old town | 60 | – | 0.013 | 0.017 | 20 |
| 4Seasons countryside | 10 | 0.001 | 0.015 | 0.032 | 173 |
| 4Seasons countryside | 30 | – | 0.008 | 0.026 | 54 |
| 4Seasons countryside | 60 | – | 0.005 | 0.021 | 26 |
| Boreas | 10 | 0.001 | 0.006 | 0.017 | 138 |
| Boreas | 30 | – | 0.005 | 0.014 | 42 |
| Boreas | 60 | – | – | 0.010 | 17 |

## Table 4: power per descriptor (ANCH vs per-frame), H = 10 (RobotCar 5), alpha = 0.05

| dataset | megaloc | salad | mixvpr | cosplace | netvlad | dinov2 |
|---|---|---|---|---|---|---|
| RobotCar-Seasons | 0.76 vs 0.99 | 0.75 vs 0.95 | 0.70 vs 0.60 | 0.71 vs 0.86 | 0.71 vs 0.73 | 0.45 vs 0.45 |
| CMU-Seasons | 0.94 vs 0.62 | 0.91 vs 0.86 | 0.86 vs 0.81 | 0.87 vs 0.77 | 0.75 vs 0.29 | 0.58 vs 0.38 |
| Nordland | 0.97 vs 0.73 | 0.96 vs 0.61 | 0.88 vs 0.45 | 0.86 vs 0.40 | 0.77 vs 0.25 | 0.71 vs 0.20 |
| 4Seasons office | 0.98 vs 0.42 | 0.97 vs 0.61 | 0.93 vs 0.43 | 0.93 vs 0.09 | 0.67 vs 0.06 | 0.54 vs 0.23 |
| 4Seasons old town | 0.94 vs 0.69 | 0.92 vs 0.54 | 0.80 vs 0.41 | 0.85 vs 0.47 | 0.69 vs 0.32 | 0.41 vs 0.15 |
| 4Seasons countryside | 0.61 vs 0.33 | 0.42 vs 0.21 | 0.40 vs 0.21 | 0.47 vs 0.26 | 0.26 vs 0.13 | 0.06 vs 0.02 |
| Boreas | 0.97 vs 0.47 | 0.92 vs 0.33 | 0.95 vs 0.80 | 0.86 vs 0.33 | 0.45 vs 0.12 | 0.09 vs 0.01 |

## Table 5: navigation with 30 % map holes — mean position error (share of frames with error > rho), mean over descriptors and seeds

| dataset | accept all | label threshold | SelfCal frame | HMM off-map (labels) | CPC-HMM (ours) | certified (ours) | oracle |
|---|---|---|---|---|---|---|---|
| CMU-Seasons | 92.6 (0.41) | 15.5 (0.11) | 5.2 (0.03) | 13.0 (0.06) | 5.7 (0.03) | 3.8 (0.01) | 2.9 (0.00) |
| Nordland | 438.5 (0.98) | 211.1 (0.89) | 36.1 (0.69) | 68.0 (0.55) | 20.0 (0.50) | 17.2 (0.49) | 5.4 (0.40) |
| 4Seasons office | 57.5 (0.45) | 16.9 (0.20) | 11.6 (0.09) | 22.7 (0.18) | 12.8 (0.11) | 11.3 (0.11) | 8.4 (0.05) |
| 4Seasons old town | 277.0 (0.80) | 68.0 (0.53) | 50.4 (0.46) | 76.9 (0.45) | 46.4 (0.44) | 37.0 (0.45) | 21.1 (0.29) |
| 4Seasons countryside | 110.0 (0.52) | 54.3 (0.49) | 66.2 (0.64) | 76.0 (0.52) | 52.3 (0.49) | 51.5 (0.54) | 17.8 (0.20) |
| Boreas | 165.5 (0.54) | 208.1 (0.19) | 118.4 (0.12) | 74.4 (0.13) | 354.4 (0.18) | 168.1 (0.11) | 17.9 (0.01) |

Nordland errors are in frames; all others in metres. 4Seasons uses real VIO odometry.


## Table 6: natural off-map excursions (queries of other scenes/datasets driven against the map), excursion FAR at alpha = 0.05

| map | source | H | FRAME | ANCH | ANCHR |
|---|---|---|---|---|---|
| 4Seasons countryside | 4Seasons office | 10 | 0.001 (0.002) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons countryside | 4Seasons office | 30 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons countryside | 4Seasons old town | 10 | 0.000 (0.001) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons countryside | 4Seasons old town | 30 | 0.001 (0.003) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons countryside | CMU-Seasons | 10 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons countryside | CMU-Seasons | 30 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons countryside | RobotCar-Seasons | 10 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons countryside | RobotCar-Seasons | 30 | nan (nan) | nan (nan) | nan (nan) |
| 4Seasons office | 4Seasons countryside | 10 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.001) |
| 4Seasons office | 4Seasons countryside | 30 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons office | 4Seasons old town | 10 | 0.001 (0.001) | 0.000 (0.001) | 0.004 (0.016) |
| 4Seasons office | 4Seasons old town | 30 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons office | CMU-Seasons | 10 | 0.000 (0.000) | 0.001 (0.005) | 0.001 (0.006) |
| 4Seasons office | CMU-Seasons | 30 | 0.000 (0.000) | 0.001 (0.003) | 0.003 (0.012) |
| 4Seasons office | RobotCar-Seasons | 10 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons office | RobotCar-Seasons | 30 | nan (nan) | nan (nan) | nan (nan) |
| 4Seasons old town | 4Seasons countryside | 10 | 0.007 (0.021) | 0.007 (0.027) | 0.005 (0.020) |
| 4Seasons old town | 4Seasons countryside | 30 | 0.004 (0.011) | 0.005 (0.021) | 0.007 (0.027) |
| 4Seasons old town | 4Seasons office | 10 | 0.010 (0.024) | 0.003 (0.008) | 0.003 (0.007) |
| 4Seasons old town | 4Seasons office | 30 | 0.016 (0.060) | 0.000 (0.000) | 0.002 (0.009) |
| 4Seasons old town | CMU-Seasons | 10 | 0.001 (0.002) | 0.000 (0.001) | 0.000 (0.000) |
| 4Seasons old town | CMU-Seasons | 30 | 0.000 (0.002) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons old town | RobotCar-Seasons | 10 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| 4Seasons old town | RobotCar-Seasons | 30 | nan (nan) | nan (nan) | nan (nan) |
| CMU-Seasons | 4Seasons countryside | 10 | 0.000 (0.001) | 0.000 (0.000) | 0.000 (0.000) |
| CMU-Seasons | 4Seasons countryside | 30 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| CMU-Seasons | 4Seasons office | 10 | 0.001 (0.002) | 0.000 (0.000) | 0.000 (0.000) |
| CMU-Seasons | 4Seasons office | 30 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| CMU-Seasons | 4Seasons old town | 10 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| CMU-Seasons | 4Seasons old town | 30 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| CMU-Seasons | RobotCar-Seasons | 10 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) |
| CMU-Seasons | RobotCar-Seasons | 30 | nan (nan) | nan (nan) | nan (nan) |
