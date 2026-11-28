# New datasets — R@1 on test sequences (PROTOCOL v1, hyper-parameters on calibration only)

| Dataset | Descriptor | Single | SeqSLAM (causal) | HMM fixed kernel | **HMM (ours, calib-selected + fallback)** | Δ vs SeqSLAM | Δ vs single | Note | run_id |
|---|---|---|---|---|---|---|---|---|---|
| Oxford RobotCar (7 conditions vs overcast map) | netvlad | 0.547 | 0.689 | 0.793 | **0.793** | +0.105 | +0.246 |  | 20261128-268_E18_oxford_netvlad_s0 |
| Oxford RobotCar (7 conditions vs overcast map) | cosplace | 0.643 | 0.704 | 0.791 | **0.791** | +0.087 | +0.148 |  | 20261128-269_E18_oxford_cosplace_s0 |
| Oxford RobotCar (7 conditions vs overcast map) | dinov2 | 0.633 | 0.639 | 0.827 | **0.827** | +0.188 | +0.195 |  | 20261128-272_E18_oxford_dinov2_s0 |
| Oxford RobotCar (7 conditions vs overcast map) | salad | 0.953 | 0.966 | 0.978 | **0.977** | +0.011 | +0.024 |  | 20261128-270_E18_oxford_salad_s0 |
| Oxford RobotCar (7 conditions vs overcast map) | megaloc | 0.943 | 0.965 | 0.979 | **0.980** | +0.015 | +0.037 |  | 20261128-271_E18_oxford_megaloc_s0 |
| Boreas (8 seasonal traversals) | netvlad | 0.793 | 0.965 | 0.983 | **0.968** | +0.003 | +0.174 |  | 20261128-372_E18_boreas:8_netvlad_s0 |
| Boreas (8 seasonal traversals) | cosplace | 0.990 | 0.993 | 0.995 | **0.990** | -0.003 | +0.000 |  | 20261128-368_E18_boreas:8_cosplace_s0 |
| Boreas (8 seasonal traversals) | dinov2 | 0.638 | 0.779 | 0.828 | **0.826** | +0.047 | +0.188 |  | 20261128-369_E18_boreas:8_dinov2_s0 |
| Boreas (8 seasonal traversals) | salad | 0.998 | 0.998 | 0.998 | **0.998** | +0.000 | -0.000 | saturated | 20261128-373_E18_boreas:8_salad_s0 |
| Boreas (8 seasonal traversals) | megaloc | 0.999 | 0.998 | 0.998 | **0.998** | +0.001 | -0.000 | saturated | 20261128-370_E18_boreas:8_megaloc_s0 |
| NCLT (8 campus sessions, off-map parts) | netvlad | 0.628 | 0.763 | 0.835 | **0.819** | +0.056 | +0.191 |  | 20261128-359_E18_nclt_netvlad_s0 |
| NCLT (8 campus sessions, off-map parts) | cosplace | 0.893 | 0.888 | 0.918 | **0.916** | +0.028 | +0.023 |  | 20261128-362_E18_nclt_cosplace_s0 |
| NCLT (8 campus sessions, off-map parts) | dinov2 | 0.711 | 0.762 | 0.806 | **0.807** | +0.045 | +0.096 |  | 20261128-314_E18_nclt_dinov2_s0 |
| NCLT (8 campus sessions, off-map parts) | salad | 0.939 | 0.926 | 0.943 | **0.946** | +0.020 | +0.007 |  | 20261128-363_E18_nclt_salad_s0 |
| NCLT (8 campus sessions, off-map parts) | megaloc | 0.950 | 0.936 | 0.955 | **0.956** | +0.020 | +0.006 |  | 20261128-358_E18_nclt_megaloc_s0 |
| St Lucia (5 times of day) | netvlad | 0.606 | 0.944 | 0.972 | **0.972** | +0.028 | +0.366 |  | 20261128-294_E18_stlucia_netvlad_s0 |
| St Lucia (5 times of day) | cosplace | 0.995 | 1.000 | 1.000 | **1.000** | +0.000 | +0.005 | saturated | 20261128-295_E18_stlucia_cosplace_s0 |
| St Lucia (5 times of day) | dinov2 | 0.682 | 0.934 | 0.967 | **0.995** | +0.061 | +0.313 |  | 20261128-298_E18_stlucia_dinov2_s0 |
| St Lucia (5 times of day) | salad | 0.999 | 1.000 | 1.000 | **1.000** | +0.000 | +0.001 | saturated | 20261128-296_E18_stlucia_salad_s0 |
| St Lucia (5 times of day) | megaloc | 1.000 | 1.000 | 1.000 | **1.000** | +0.000 | +0.000 | saturated | 20261128-297_E18_stlucia_megaloc_s0 |
| Brisbane-Event-VPR (5 times of day) | netvlad | 0.267 | 0.464 | 0.557 | **0.557** | +0.093 | +0.290 |  | 20261128-247_E18_brisbane_netvlad_s0 |
| Brisbane-Event-VPR (5 times of day) | cosplace | 0.623 | 0.652 | 0.680 | **0.680** | +0.028 | +0.056 |  | 20261128-249_E18_brisbane_cosplace_s0 |
| Brisbane-Event-VPR (5 times of day) | salad | 0.785 | 0.837 | 0.925 | **0.925** | +0.088 | +0.140 |  | 20261128-250_E18_brisbane_salad_s0 |
| Brisbane-Event-VPR (5 times of day) | megaloc | 0.746 | 0.796 | 0.878 | **0.878** | +0.082 | +0.132 |  | 20261128-252_E18_brisbane_megaloc_s0 |
| QUT Gardens Point (day/night, lateral) | netvlad | 0.890 | 0.995 | 0.995 | **0.995** | +0.000 | +0.105 |  | 20261128-325_E18_qut-gp_netvlad_s0 |
| QUT Gardens Point (day/night, lateral) | cosplace | 0.940 | 1.000 | 1.000 | **1.000** | +0.000 | +0.060 |  | 20261128-260_E18_qut-gp_cosplace_s0 |
| QUT Gardens Point (day/night, lateral) | salad | 0.955 | 1.000 | 0.995 | **0.995** | -0.005 | +0.040 |  | 20261128-261_E18_qut-gp_salad_s0 |
| QUT Gardens Point (day/night, lateral) | megaloc | 0.925 | 0.975 | 0.965 | **0.965** | -0.010 | +0.040 |  | 20261128-262_E18_qut-gp_megaloc_s0 |
| QUT SouthBank bicycle | netvlad | 0.225 | 0.690 | 0.825 | **0.825** | +0.135 | +0.600 |  | 20261128-256_E18_qut-sb_netvlad_s0 |
| QUT SouthBank bicycle | cosplace | 0.405 | 0.900 | 0.905 | **0.905** | +0.005 | +0.500 |  | 20261128-257_E18_qut-sb_cosplace_s0 |
| QUT SouthBank bicycle | salad | 0.785 | 0.955 | 0.960 | **0.960** | +0.005 | +0.175 |  | 20261128-258_E18_qut-sb_salad_s0 |
| QUT SouthBank bicycle | megaloc | 0.845 | 0.990 | 0.995 | **0.995** | +0.005 | +0.150 |  | 20261128-259_E18_qut-sb_megaloc_s0 |
| KITTI Odometry loops (revisit) | netvlad | 0.841 | 0.865 | 0.832 | **0.850** | -0.014 | +0.009 |  | 20261128-364_E18_kitti_netvlad_s0 |
| KITTI Odometry loops (revisit) | cosplace | 0.829 | 0.831 | 0.805 | **0.811** | -0.020 | -0.018 |  | 20261128-365_E18_kitti_cosplace_s0 |
| KITTI Odometry loops (revisit) | salad | 0.845 | 0.856 | 0.823 | **0.841** | -0.014 | -0.004 |  | 20261128-366_E18_kitti_salad_s0 |
| KITTI Odometry loops (revisit) | megaloc | 0.856 | 0.852 | 0.845 | **0.845** | -0.007 | -0.011 |  | 20261128-367_E18_kitti_megaloc_s0 |

Non-saturated cells: 31; vs tuned causal SeqSLAM: 21 wins / 4 ties (±0.005) / 6 losses; vs single image: 27 / 2 / 2.
