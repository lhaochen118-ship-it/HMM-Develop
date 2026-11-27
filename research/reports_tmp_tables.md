
### R@1 (test sequences; ↑ better for R@1, ↓ for NLL)

| Dataset | Descriptor | Single | SeqSLAM† | HMM (fixed kernel, β*) | +latent vel. | +change emission | +IA weighting | **IA-HMM (dev-selected)** | oracle motion (diag.) | run |
|---|---|---|---|---|---|---|---|---|---|---|
| nord | netvlad | 0.364 | 0.889 | 0.970 | 0.838 | 0.839 | 0.872 | 0.970 (hmm_fixed) | – | 20261127-040_E18_nord_netvlad_s0 |
| nord | cosplace | 0.652 | 0.966 | 0.987 | 0.969 | 0.970 | 0.982 | 0.982 (LV+ME+IA) | – | 20261127-041_E18_nord_cosplace_s0 |
| nord | salad | 0.811 | 0.970 | 0.986 | 0.987 | 0.986 | 0.991 | 0.991 (LV+ME+IA) | – | 20261127-039_E18_nord_salad_s0 |
| nord | megaloc | 0.821 | 0.960 | 0.985 | 0.962 | 0.977 | 0.989 | 0.985 (hmm_fixed) | – | 20261127-042_E18_nord_megaloc_s0 |
| nord-tw s1 | netvlad | 0.430 | 0.580 | 0.563 | 0.712 | 0.805 | 0.827 | 0.827 (LV+ME+IA) | 0.896 | 20261127-036_E18_nord-tw_netvlad_s1 |
| nord-tw s1 | cosplace | 0.695 | 0.658 | 0.826 | 0.890 | 0.904 | 0.915 | 0.915 (LV+ME+IA) | 0.968 | 20261127-037_E18_nord-tw_cosplace_s1 |
| nord-tw s1 | salad | 0.808 | 0.671 | 0.869 | 0.912 | 0.901 | 0.915 | 0.901 (LV+ME) | 0.961 | 20261127-035_E18_nord-tw_salad_s1 |
| nord-tw s1 | megaloc | 0.832 | 0.669 | 0.882 | 0.914 | 0.917 | 0.914 | 0.917 (LV+ME) | 0.953 | 20261127-038_E18_nord-tw_megaloc_s1 |
| nord-tw s2 | netvlad | 0.363 | – | 0.531 | 0.599 | 0.747 | 0.822 | – | 0.809 | 20261127-027_E18_nord-tw_netvlad_s2 |
| nord-tw s2 | salad | 0.819 | – | 0.878 | 0.919 | 0.909 | 0.904 | – | 0.953 | 20261127-028_E18_nord-tw_salad_s2 |
| cmu | netvlad | 0.701 | 0.770 | 0.820 | 0.719 | 0.734 | 0.733 | 0.820 (hmm_fixed) | – | 20261127-024_E18_cmu_netvlad_s0 |
| cmu | cosplace | 0.908 | 0.921 | 0.931 | 0.905 | 0.904 | 0.902 | 0.931 (hmm_fixed) | – | 20261127-026_E18_cmu_cosplace_s0 |
| cmu | salad | 0.943 | 0.954 | 0.955 | 0.946 | 0.946 | 0.946 | 0.955 (hmm_fixed) | – | 20261127-025_E18_cmu_salad_s0 |
| cmu | megaloc | 0.932 | 0.947 | 0.941 | 0.930 | 0.933 | 0.937 | 0.941 (hmm_fixed) | – | 20261127-029_E18_cmu_megaloc_s0 |
| rc | netvlad | 0.708 | 0.777 | 0.772 | 0.760 | 0.775 | 0.779 | 0.779 (LV+ME+IA) | – | 20261127-032_E18_rc_netvlad_s0 |
| rc | cosplace | 0.834 | 0.858 | 0.860 | 0.855 | 0.859 | 0.857 | 0.857 (LV+ME+IA) | – | 20261127-033_E18_rc_cosplace_s0 |
| rc | salad | 0.987 | 0.989 | 0.992 | 0.991 | 0.991 | 0.991 | 0.991 (LV+ME) | – | 20261127-030_E18_rc_salad_s0 |
| rc | megaloc | 0.974 | 0.984 | 0.984 | 0.978 | 0.980 | 0.980 | 0.980 (LV+ME+IA) | – | 20261127-034_E18_rc_megaloc_s0 |

### NLL (test sequences; ↑ better for R@1, ↓ for NLL)

| Dataset | Descriptor | Single | SeqSLAM† | HMM (fixed kernel, β*) | +latent vel. | +change emission | +IA weighting | **IA-HMM (dev-selected)** | oracle motion (diag.) | run |
|---|---|---|---|---|---|---|---|---|---|---|
| nord | netvlad | 3.593 | 6.640 | 0.203 | 1.348 | 1.417 | 1.090 | 0.203 | – | 20261127-040_E18_nord_netvlad_s0 |
| nord | cosplace | 1.550 | 5.629 | 0.089 | 0.160 | 0.129 | 0.065 | 0.065 | – | 20261127-041_E18_nord_cosplace_s0 |
| nord | salad | 0.942 | 5.720 | 0.087 | 0.085 | 0.063 | 0.055 | 0.055 | – | 20261127-039_E18_nord_salad_s0 |
| nord | megaloc | 0.989 | 6.274 | 0.086 | 0.239 | 0.140 | 0.116 | 0.086 | – | 20261127-042_E18_nord_megaloc_s0 |
| nord-tw s1 | netvlad | 3.128 | 6.790 | 2.816 | 2.047 | 1.225 | 0.936 | 0.936 | 0.786 | 20261127-036_E18_nord-tw_netvlad_s1 |
| nord-tw s1 | cosplace | 1.359 | 6.012 | 0.739 | 0.492 | 0.483 | 0.445 | 0.445 | 0.231 | 20261127-037_E18_nord-tw_cosplace_s1 |
| nord-tw s1 | salad | 0.838 | 6.051 | 0.548 | 0.437 | 0.448 | 0.360 | 0.448 | 0.280 | 20261127-035_E18_nord-tw_salad_s1 |
| nord-tw s1 | megaloc | 0.845 | 6.523 | 0.520 | 0.464 | 0.399 | 0.546 | 0.399 | 0.399 | 20261127-038_E18_nord-tw_megaloc_s1 |
| nord-tw s2 | netvlad | 3.776 | – | 3.614 | 3.430 | 2.065 | 0.985 | – | 1.824 | 20261127-027_E18_nord-tw_netvlad_s2 |
| nord-tw s2 | salad | 0.918 | – | 0.517 | 0.469 | 0.446 | 0.556 | – | 0.439 | 20261127-028_E18_nord-tw_salad_s2 |
| cmu | netvlad | 1.117 | 2.707 | 0.867 | 1.484 | 1.285 | 1.221 | 0.867 | – | 20261127-024_E18_cmu_netvlad_s0 |
| cmu | cosplace | 0.286 | 1.673 | 0.333 | 0.422 | 0.425 | 0.434 | 0.333 | – | 20261127-026_E18_cmu_cosplace_s0 |
| cmu | salad | 0.158 | 1.812 | 0.142 | 0.182 | 0.178 | 0.195 | 0.142 | – | 20261127-025_E18_cmu_salad_s0 |
| cmu | megaloc | 0.177 | 1.939 | 0.155 | 0.197 | 0.197 | 0.186 | 0.155 | – | 20261127-029_E18_cmu_megaloc_s0 |
| rc | netvlad | 1.458 | 5.731 | 1.415 | 1.454 | 1.410 | 1.302 | 1.302 | – | 20261127-032_E18_rc_netvlad_s0 |
| rc | cosplace | 0.801 | 4.358 | 0.921 | 0.947 | 0.917 | 0.796 | 0.796 | – | 20261127-033_E18_rc_cosplace_s0 |
| rc | salad | 0.032 | 4.159 | 0.023 | 0.027 | 0.025 | 0.025 | 0.025 | – | 20261127-030_E18_rc_salad_s0 |
| rc | megaloc | 0.058 | 4.646 | 0.035 | 0.057 | 0.057 | 0.057 | 0.057 | – | 20261127-034_E18_rc_megaloc_s0 |
