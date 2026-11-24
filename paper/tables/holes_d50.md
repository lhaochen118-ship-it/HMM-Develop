# HSI wave summary

runs: 108 (held-out 84, with idea-1 SH on the same run 84)

## Held-out runs: mean recall / segFAR / navigation error per dataset

| dataset | n | HSI rec / seg / err | geo rec / seg / err | SH rec / seg / err | CST-JS rec / seg / err | oracle rec / seg / err | HSI−SH rec (wins) | HSI−SH err (better) |
|---|---|---|---|---|---|---|---|---|
| boreas | 14 | 0.893 / 0.000 / 5.9 | 0.788 / 0.009 / 13.0 | 0.738 / 0.001 / 4.2 | 0.738 / 0.003 / 8.7 | 0.901 / 0.000 / 2.4 | +0.155 (14/14) | +1.6 (8/14) |
| cmu | 14 | 0.766 / 0.036 / 12.7 | 0.398 / 0.059 / 18.0 | 0.774 / 0.032 / 10.6 | 0.770 / 0.028 / 7.1 | 0.921 / 0.000 / 3.3 | -0.008 (8/14) | +2.1 (8/14) |
| nord | 14 | 0.670 / 0.000 / 10.9 | 0.561 / 0.000 / 12.2 | 0.771 / 0.000 / 11.6 | 0.784 / 0.002 / 11.4 | 0.708 / 0.000 / 10.0 | -0.102 (2/14) | -0.6 (2/14) |
| 4s_office_loop | 14 | 0.875 / 0.001 / 13.0 | 0.727 / 0.005 / 14.0 | 0.806 / 0.001 / 12.8 | 0.828 / 0.014 / 14.2 | 0.927 / 0.000 / 11.6 | +0.069 (14/14) | +0.2 (10/14) |
| 4s_old_town | 14 | 0.730 / 0.001 / 54.8 | 0.598 / 0.008 / 57.5 | 0.706 / 0.003 / 34.2 | 0.711 / 0.014 / 73.8 | 0.860 / 0.000 / 29.5 | +0.023 (8/14) | +20.6 (4/14) |
| 4s_countryside | 14 | 0.615 / 0.005 / 39.7 | 0.535 / 0.026 / 60.8 | 0.466 / 0.003 / 40.9 | 0.487 / 0.009 / 38.7 | 0.749 / 0.000 / 24.2 | +0.149 (14/14) | -1.1 (12/14) |

## Pre-registered hypotheses (Entry 1) on the held-out runs

- **H1 (validity):** mean segFAR <= 0.05 on 6/6 datasets; runs > 0.05: 4/84 (4.8%) -> **supported**
- **H2 (recall):** HSI >= SH on 4/6 datasets; pooled mean difference +0.0479 -> **supported**
- **H3 (weak descriptors):** DINOv2 + NetVLAD held-out runs: mean HSI − SH = +0.0971 over 24 runs -> **supported**
- **H4 (navigation):** mean error within +1 m of SH on 3/6 datasets -> **NOT supported**
- **H5 (position audit):** every class <= 0.07 (classes with >= 50 segments) on 6/6 datasets -> **supported**
  - boreas: start 0.004 (n=488), edge 0.000 (n=1294), deep 0.000 (n=37044)
  - cmu: start 0.037 (n=13772), edge 0.000 (n=0), deep 0.000 (n=0)
  - nord: start 0.000 (n=266), edge 0.000 (n=252), deep 0.000 (n=9034)
  - 4s_office_loop: start 0.003 (n=1208), edge 0.000 (n=190), deep 0.000 (n=6080)
  - 4s_old_town: start 0.010 (n=96), edge 0.006 (n=180), deep 0.001 (n=5500)
  - 4s_countryside: start 0.013 (n=948), edge 0.000 (n=270), deep 0.004 (n=7390)

## Held-out, per descriptor (mean over datasets and seeds)

| descriptor | n | HSI rec | SH rec | HSI−SH | wins | HSI seg | HSI err | SH err |
|---|---|---|---|---|---|---|---|---|
| cosplace | 12 | 0.769 | 0.732 | +0.037 | 8 | 0.006 | 23.1 | 17.3 |
| netvlad | 12 | 0.549 | 0.482 | +0.068 | 9 | 0.001 | 45.7 | 25.2 |
| megaloc | 12 | 0.866 | 0.855 | +0.011 | 8 | 0.011 | 16.6 | 15.8 |
| dinov2 | 12 | 0.565 | 0.438 | +0.127 | 11 | 0.006 | 24.7 | 27.6 |
| salad | 18 | 0.861 | 0.832 | +0.029 | 10 | 0.011 | 15.9 | 15.9 |
| mixvpr | 18 | 0.844 | 0.811 | +0.033 | 14 | 0.006 | 17.3 | 15.8 |

## Ablations (held-out runs; mean over datasets of the per-dataset means)

| variant | recall | segFAR | runs seg>0.05 | nav err | worst-class rate |
|---|---|---|---|---|---|
| HSI | 0.758 | 0.0070 | 4 | 22.8 | 0.037 |
| HSI-rot-m | 0.742 | 0.0066 | 4 | 21.7 | 0.035 |
| geo | 0.601 | 0.0178 | 10 | 29.2 | 0.150 |
| (idea 1) SH | 0.710 | 0.0067 | 3 | 19.0 | – |
