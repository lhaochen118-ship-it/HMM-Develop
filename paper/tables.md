
### Table 1 (α = 0.05). SALAD. Cell: off-map FAR / #conditions significantly above α (binomial, Bonferroni) / TPR / aliasing-accept rate

| method | labels | RobotCar-Seasons (9 cond.) | Extended-CMU (11 dates) | Nordland (3 seasons) |
|---|---|---|---|---|
| **SelfCal-AA (ours)** | none | 0.004 / 0/9 / 0.988 / 0.00 | 0.002 / 0/11 / 0.853 / 0.01 | 0.008 / 0/3 / 0.754 / 0.06 |
| SelfCal (ours, no alias guard) | none | 0.004 / 0/9 / 0.994 / 0.01 | 0.009 / 0/11 / 0.956 / 0.26 | 0.031 / 0/3 / 0.788 / 0.52 |
| Threshold, benign→all | benign | 0.109 / 5/9 / 0.997 / 0.50 | 0.052 / 4/11 / 0.985 / 0.78 | 0.037 / 0/3 / 0.630 / 0.49 |
| Threshold, benign, neg. incl. aliasing | benign | 0.075 / 2/9 / 0.997 / 0.43 | 0.047 / 4/11 / 0.984 / 0.75 | 0.010 / 0/3 / 0.043 / 0.10 |
| Conformal LOCO (SAFEVPR protocol) | other cond. | 0.052 / 1/9 / 0.997 / 0.34 | 0.051 / 4/11 / 0.984 / 0.77 | 0.070 / 2/3 / 0.666 / 0.51 |
| Quantile Transfer | benign | 0.097 / 4/9 / 0.998 / 0.47 | 0.054 / 2/11 / 0.993 / 0.80 | 0.109 / 2/3 / 0.901 / 0.72 |
| Learned calibrator (CRSG), benign→all | benign | 0.099 / 4/9 / 0.996 / 0.33 | 0.054 / 4/11 / 0.982 / 0.68 | 0.041 / 0/3 / 0.814 / 0.45 |
| PA ratio, benign→all | benign | 0.078 / 2/9 / 0.596 / 0.09 | 0.046 / 2/11 / 0.449 / 0.19 | 0.040 / 0/3 / 0.846 / 0.18 |
| Gaussian z-norm null | none | 0.350 / 9/9 / 0.999 / 0.72 | 0.250 / 11/11 / 0.994 / 0.73 | 0.125 / 3/3 / 0.752 / 0.79 |
| EVT spacing test (F(2,2k)) | none | 0.058 / 1/9 / 0.888 / 0.17 | 0.050 / 1/11 / 0.700 / 0.01 | 0.036 / 0/3 / 0.743 / 0.07 |
| SelfCal on raw max-sim (ablation) | none | 0.001 / 0/9 / 0.979 / 0.00 | 0.010 / 0/11 / 0.949 / 0.46 | 0.022 / 0/3 / 0.411 / 0.39 |
| Oracle (labels of every condition) | all | 0.040 / 0/9 / 0.995 / — | 0.049 / 0/11 / 0.992 / — | 0.050 / 0/3 / 0.780 / — |

### Table 1 (α = 0.1). SALAD. Cell: off-map FAR / #conditions significantly above α (binomial, Bonferroni) / TPR / aliasing-accept rate

| method | labels | RobotCar-Seasons (9 cond.) | Extended-CMU (11 dates) | Nordland (3 seasons) |
|---|---|---|---|---|
| **SelfCal-AA (ours)** | none | 0.017 / 0/9 / 0.995 / 0.04 | 0.010 / 0/11 / 0.910 / 0.01 | 0.023 / 0/3 / 0.829 / 0.08 |
| SelfCal (ours, no alias guard) | none | 0.025 / 0/9 / 0.998 / 0.05 | 0.038 / 0/11 / 0.984 / 0.65 | 0.068 / 0/3 / 0.863 / 0.65 |
| Threshold, benign→all | benign | 0.177 / 4/9 / 0.998 / 0.62 | 0.108 / 5/11 / 0.994 / 0.84 | 0.061 / 0/3 / 0.699 / 0.55 |
| Threshold, benign, neg. incl. aliasing | benign | 0.151 / 3/9 / 0.998 / 0.58 | 0.101 / 4/11 / 0.994 / 0.84 | 0.019 / 0/3 / 0.246 / 0.29 |
| Conformal LOCO (SAFEVPR protocol) | other cond. | 0.102 / 1/9 / 0.997 / 0.47 | 0.101 / 5/11 / 0.993 / 0.83 | 0.134 / 1/3 / 0.731 / 0.60 |
| Quantile Transfer | benign | 0.143 / 2/9 / 0.998 / 0.54 | 0.111 / 4/11 / 0.996 / 0.91 | 0.154 / 2/3 / 0.925 / 0.76 |
| Learned calibrator (CRSG), benign→all | benign | 0.163 / 4/9 / 0.997 / 0.47 | 0.112 / 6/11 / 0.993 / 0.84 | 0.071 / 0/3 / 0.865 / 0.53 |
| PA ratio, benign→all | benign | 0.151 / 3/9 / 0.697 / 0.21 | 0.098 / 1/11 / 0.566 / 0.32 | 0.080 / 0/3 / 0.876 / 0.22 |
| Gaussian z-norm null | none | 0.425 / 9/9 / 0.999 / 0.79 | 0.308 / 11/11 / 0.998 / 0.83 | 0.162 / 3/3 / 0.789 / 0.80 |
| EVT spacing test (F(2,2k)) | none | 0.113 / 1/9 / 0.937 / 0.29 | 0.098 / 0/11 / 0.810 / 0.01 | 0.078 / 0/3 / 0.811 / 0.10 |
| SelfCal on raw max-sim (ablation) | none | 0.011 / 0/9 / 0.994 / 0.07 | 0.076 / 0/11 / 0.990 / 0.82 | 0.041 / 0/3 / 0.646 / 0.50 |
| Oracle (labels of every condition) | all | 0.092 / 0/9 / 0.998 / — | 0.099 / 0/11 / 0.996 / — | 0.100 / 0/3 / 0.880 / — |

### Table 2 (α = 0.05). Descriptors. Cell: FAR / #viol / TPR / aliasing for SelfCal-AA | #viol for benign threshold, LOCO, CRSG | oracle TPR

| descriptor | dataset | R@1 (5 m,10° / 2 fr) | SelfCal-AA | benign thr. #viol (alias) | LOCO #viol | CRSG #viol | oracle TPR |
|---|---|---|---|---|---|---|---|
| NetVLAD | RobotCar-Seasons | 0.666 | 0.006 / 0/9 / 0.746 / 0.00 | 4/9 (0.07) | 2/9 | 4/9 | 0.715 |
| NetVLAD | Extended-CMU | 0.640 | 0.006 / 0/11 / 0.594 / 0.01 | 4/11 (0.20) | 4/11 | 5/11 | 0.367 |
| NetVLAD | Nordland | 0.366 | 0.009 / 0/3 / 0.413 / 0.02 | 0/3 (0.07) | 1/3 | 0/3 | 0.179 |
| CosPlace | RobotCar-Seasons | 0.767 | 0.004 / 0/9 / 0.842 / 0.01 | 0/9 (0.07) | 1/9 | 0/9 | 0.869 |
| CosPlace | Extended-CMU | 0.903 | 0.012 / 0/11 / 0.813 / 0.01 | 1/11 (0.24) | 3/11 | 1/11 | 0.962 |
| CosPlace | Nordland | 0.640 | 0.006 / 0/3 / 0.351 / 0.01 | 0/3 (0.16) | 1/3 | 0/3 | 0.393 |
| MixVPR | RobotCar-Seasons | 0.850 | 0.004 / 0/9 / 0.912 / 0.00 | 1/9 (0.04) | 1/9 | 1/9 | 0.915 |
| MixVPR | Extended-CMU | 0.937 | 0.012 / 0/11 / 0.884 / 0.00 | 1/11 (0.34) | 5/11 | 1/11 | 0.940 |
| MixVPR | Nordland | 0.748 | 0.007 / 0/3 / 0.638 / 0.05 | 0/3 (0.33) | 1/3 | 0/3 | 0.552 |
| DINOv2 (CLS+mean) | RobotCar-Seasons | 0.536 | 0.001 / 0/9 / 0.326 / 0.00 | 0/9 (0.11) | 2/9 | 0/9 | 0.642 |
| DINOv2 (CLS+mean) | Extended-CMU | 0.637 | 0.001 / 0/11 / 0.062 / 0.00 | 2/11 (0.12) | 4/11 | 2/11 | 0.696 |
| DINOv2 (CLS+mean) | Nordland | 0.459 | 0.007 / 0/3 / 0.183 / 0.01 | 0/3 (0.06) | 1/3 | 0/3 | 0.388 |
| SALAD | RobotCar-Seasons | 0.911 | 0.004 / 0/9 / 0.988 / 0.00 | 5/9 (0.50) | 1/9 | 4/9 | 0.995 |
| SALAD | Extended-CMU | 0.936 | 0.002 / 0/11 / 0.853 / 0.01 | 4/11 (0.78) | 4/11 | 4/11 | 0.992 |
| SALAD | Nordland | 0.791 | 0.008 / 0/3 / 0.754 / 0.06 | 0/3 (0.49) | 2/3 | 0/3 | 0.780 |
| MegaLoc | RobotCar-Seasons | 0.905 | 0.002 / 0/9 / 0.994 / 0.10 | 1/9 (0.29) | 1/9 | 1/9 | 0.993 |
| MegaLoc | Extended-CMU | 0.927 | 0.012 / 0/11 / 0.950 / 0.00 | 2/11 (0.68) | 2/11 | 2/11 | 0.996 |
| MegaLoc | Nordland | 0.799 | 0.007 / 0/3 / 0.861 / 0.08 | 0/3 (0.59) | 2/3 | 0/3 | 0.615 |

### Table 2a (α = 0.05). All 6 descriptors × 3 datasets (18 settings, 138 deployment conditions)

| method | labels | violating conditions | settings with ≥1 violation | mean TPR | median aliasing-accept | max worst-cond. FAR |
|---|---|---|---|---|---|---|
| SelfCal-AA (ours) | none | 0/138 | 0/18 | 0.676 | 0.008 | 0.040 |
| SelfCal (ours) | none | 0/138 | 0/18 | 0.718 | 0.060 | 0.051 |
| Threshold, benign→all | benign | 25/138 | 10/18 | 0.664 | 0.218 | 0.281 |
| Threshold, benign, neg. incl. aliasing | benign | 15/138 | 7/18 | 0.541 | 0.087 | 0.209 |
| Conformal LOCO (SAFEVPR protocol) | other cond. | 38/138 | 18/18 | 0.716 | 0.231 | 0.418 |
| Quantile Transfer | benign | 64/138 | 18/18 | 0.799 | 0.440 | 0.483 |
| Learned calibrator (CRSG) | benign | 25/138 | 10/18 | 0.785 | 0.173 | 0.187 |
| PA ratio | benign | 11/138 | 5/18 | 0.526 | 0.083 | 0.122 |
| Gaussian z-norm null | none | 112/138 | 16/18 | 0.740 | 0.451 | 0.525 |
| EVT spacing test | none | 4/138 | 4/18 | 0.670 | 0.039 | 0.109 |
| Oracle (labels of every condition) | all | 0/138 | 0/18 | 0.721 | — | 0.050 |

### Table 2a (α = 0.1). All 6 descriptors × 3 datasets (18 settings, 138 deployment conditions)

| method | labels | violating conditions | settings with ≥1 violation | mean TPR | median aliasing-accept | max worst-cond. FAR |
|---|---|---|---|---|---|---|
| SelfCal-AA (ours) | none | 0/138 | 0/18 | 0.762 | 0.020 | 0.079 |
| SelfCal (ours) | none | 0/138 | 0/18 | 0.802 | 0.133 | 0.103 |
| Threshold, benign→all | benign | 25/138 | 9/18 | 0.742 | 0.344 | 0.583 |
| Threshold, benign, neg. incl. aliasing | benign | 18/138 | 8/18 | 0.617 | 0.175 | 0.568 |
| Conformal LOCO (SAFEVPR protocol) | other cond. | 42/138 | 17/18 | 0.783 | 0.341 | 0.559 |
| Quantile Transfer | benign | 58/138 | 17/18 | 0.857 | 0.529 | 0.523 |
| Learned calibrator (CRSG) | benign | 27/138 | 10/18 | 0.831 | 0.318 | 0.525 |
| PA ratio | benign | 10/138 | 4/18 | 0.608 | 0.134 | 0.203 |
| Gaussian z-norm null | none | 106/138 | 15/18 | 0.755 | 0.554 | 0.622 |
| EVT spacing test | none | 2/138 | 2/18 | 0.757 | 0.082 | 0.182 |
| Oracle (labels of every condition) | all | 0/138 | 0/18 | 0.811 | — | 0.100 |

### Table 3. Excess-FAR bound Δ⁺_c (one-sided KS) — labelled benign null vs map null

- RobotCar-Seasons (9 cond.): max over conditions — max-sim | benign null 0.255, max-sim | map null 0.017, z_far | benign null 0.146, z_far+centring | map null 0.047
- Extended-CMU (11 dates): max over conditions — max-sim | benign null 0.101, max-sim | map null 0.052, z_far | benign null 0.067, z_far+centring | map null 0.028
- Nordland (3 seasons): max over conditions — max-sim | benign null 0.018, max-sim | map null 0.006, z_far | benign null 0.093, z_far+centring | map null 0.024

### Table 4. Ablations of SelfCal-AA (SALAD, α = 0.05): FAR / worst / TPR / aliasing


**RobotCar-Seasons (9 cond.)**

| variant | FAR | worst | TPR | aliasing | null n |
|---|---|---|---|---|---|
| default | 0.004 | 0.030 | 0.988 | 0.000 | 2391 |
| cell x0.5 | 0.004 | 0.030 | 0.987 | 0.000 | 2391 |
| cell x2.0 | 0.005 | 0.036 | 0.988 | 0.000 | 2391 |
| excl x0.4 | 0.003 | 0.012 | 0.941 | 0.000 | 2391 |
| excl x2.0 | 0.004 | 0.030 | 0.990 | 0.000 | 2391 |
| block_m x0.5 | 0.001 | 0.006 | 0.970 | 0.000 | 1384 |
| block_m x2.0 | 0.004 | 0.030 | 0.991 | 0.000 | 2951 |
| off_d_m x0.6 | 0.001 | 0.006 | 0.964 | 0.000 | 2851 |
| off_d_m x2.0 | 0.012 | 0.073 | 0.993 | 0.026 | 1572 |
| stride 1 | 0.004 | 0.030 | 0.987 | 0.000 | 4747 |
| stride 4 | 0.004 | 0.030 | 0.988 | 0.000 | 1194 |
| stride 8 | 0.003 | 0.024 | 0.986 | 0.000 | 597 |
| no centering | 0.002 | 0.007 | 0.980 | 0.000 | 2391 |

**Nordland (3 seasons)**

| variant | FAR | worst | TPR | aliasing | null n |
|---|---|---|---|---|---|
| default | 0.008 | 0.010 | 0.754 | 0.057 | 2030 |
| cell x0.5 | 0.005 | 0.006 | 0.719 | 0.049 | 2030 |
| cell x2.0 | 0.010 | 0.011 | 0.761 | 0.057 | 2030 |
| excl x0.4 | 0.008 | 0.009 | 0.748 | 0.047 | 2030 |
| excl x2.0 | 0.008 | 0.009 | 0.759 | 0.076 | 2030 |
| block_m x0.5 | 0.001 | 0.001 | 0.566 | 0.044 | 1810 |
| block_m x2.0 | 0.011 | 0.012 | 0.774 | 0.060 | 2140 |
| off_d_m x0.6 | 0.008 | 0.009 | 0.752 | 0.057 | 2118 |
| off_d_m x2.0 | 0.008 | 0.010 | 0.758 | 0.057 | 1810 |
| stride 1 | 0.008 | 0.009 | 0.753 | 0.058 | 4060 |
| stride 4 | 0.007 | 0.008 | 0.750 | 0.055 | 1015 |
| stride 8 | 0.006 | 0.007 | 0.747 | 0.053 | 497 |
| no centering | 0.005 | 0.006 | 0.329 | 0.086 | 2030 |

### Table 5. Deployment batches: BH on SelfCal p-values (SALAD), label-free confidence

- RobotCar-Seasons (9 cond.), off-map share 0.1: π̂0 0.15 (true 0.14); ECE label-free 0.044; BH q=0.1: gross FDR mean 0.004 (max 0.014), power 0.998
- RobotCar-Seasons (9 cond.), off-map share 0.3: π̂0 0.41 (true 0.33); ECE label-free 0.018; BH q=0.1: gross FDR mean 0.009 (max 0.046), power 0.998
- RobotCar-Seasons (9 cond.), off-map share 0.5: π̂0 0.56 (true 0.44); ECE label-free 0.013; BH q=0.1: gross FDR mean 0.004 (max 0.024), power 0.993
- Extended-CMU (11 dates), off-map share 0.1: π̂0 0.11 (true 0.11); ECE label-free 0.050; BH q=0.1: gross FDR mean 0.008 (max 0.018), power 0.972
- Extended-CMU (11 dates), off-map share 0.3: π̂0 0.34 (true 0.31); ECE label-free 0.036; BH q=0.1: gross FDR mean 0.011 (max 0.023), power 0.964
- Extended-CMU (11 dates), off-map share 0.5: π̂0 0.45 (true 0.40); ECE label-free 0.034; BH q=0.1: gross FDR mean 0.011 (max 0.023), power 0.958
- Nordland (3 seasons), off-map share 0.1: π̂0 0.22 (true 0.27); ECE label-free 0.166; BH q=0.1: gross FDR mean 0.144 (max 0.166), power 0.807
- Nordland (3 seasons), off-map share 0.3: π̂0 0.46 (true 0.43); ECE label-free 0.138; BH q=0.1: gross FDR mean 0.146 (max 0.169), power 0.780
- Nordland (3 seasons), off-map share 0.5: π̂0 0.67 (true 0.57); ECE label-free 0.104; BH q=0.1: gross FDR mean 0.147 (max 0.176), power 0.733
