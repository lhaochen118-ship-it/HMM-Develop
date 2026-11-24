# HSI wave summary

runs: 108 (held-out 84, with idea-1 SH on the same run 84)

## Held-out runs: mean recall / segFAR / navigation error per dataset

| dataset | n | HSI rec / seg / err | geo rec / seg / err | SH rec / seg / err | CST-JS rec / seg / err | oracle rec / seg / err | HSI−SH rec (wins) | HSI−SH err (better) |
|---|---|---|---|---|---|---|---|---|
| boreas | 14 | 0.910 / 0.001 / 5.6 | 0.877 / 0.000 / 2.8 | 0.832 / 0.000 / 3.0 | 0.833 / 0.002 / 6.8 | 0.890 / 0.000 / 1.7 | +0.078 (14/14) | +2.6 (6/14) |
| cmu | 14 | 0.539 / 0.001 / 2.9 | 0.466 / 0.000 / 2.9 | 0.845 / 0.013 / 3.7 | 0.839 / 0.019 / 3.4 | 0.943 / 0.000 / 2.7 | -0.306 (0/14) | -0.8 (12/14) |
| nord | 14 | 0.838 / 0.000 / 4.8 | 0.745 / 0.000 / 5.8 | 0.790 / 0.000 / 6.9 | 0.802 / 0.001 / 6.8 | 0.682 / 0.000 / 5.4 | +0.048 (6/14) | -2.1 (9/14) |
| 4s_office_loop | 14 | 0.873 / 0.000 / 6.7 | 0.724 / 0.000 / 9.4 | 0.827 / 0.001 / 7.3 | 0.839 / 0.008 / 7.3 | 0.913 / 0.000 / 6.3 | +0.046 (9/14) | -0.6 (13/14) |
| 4s_old_town | 14 | 0.764 / 0.001 / 25.8 | 0.591 / 0.001 / 54.3 | 0.760 / 0.004 / 20.0 | 0.765 / 0.011 / 26.0 | 0.855 / 0.000 / 15.4 | +0.004 (8/14) | +5.8 (4/14) |
| 4s_countryside | 14 | 0.703 / 0.002 / 19.9 | 0.665 / 0.008 / 24.0 | 0.546 / 0.000 / 30.5 | 0.553 / 0.002 / 30.0 | 0.759 / 0.000 / 14.3 | +0.156 (14/14) | -10.6 (14/14) |

## Pre-registered hypotheses (Entry 1) on the held-out runs

- **H1 (validity):** mean segFAR <= 0.05 on 6/6 datasets; runs > 0.05: 0/84 (0.0%) -> **supported**
- **H2 (recall):** HSI >= SH on 5/6 datasets; pooled mean difference +0.0046 -> **supported**
- **H3 (weak descriptors):** DINOv2 + NetVLAD held-out runs: mean HSI − SH = +0.1041 over 24 runs -> **supported**
- **H4 (navigation):** mean error within +1 m of SH on 4/6 datasets -> **supported**
- **H5 (position audit):** every class <= 0.07 (classes with >= 50 segments) on 6/6 datasets -> **supported**
  - boreas: start 0.000 (n=18), edge 0.000 (n=284), deep 0.001 (n=7484)
  - cmu: start 0.001 (n=2820), edge 0.000 (n=0), deep 0.000 (n=0)
  - nord: start 0.000 (n=0), edge 0.000 (n=66), deep 0.000 (n=1482)
  - 4s_office_loop: start 0.000 (n=42), edge 0.000 (n=158), deep 0.000 (n=1554)
  - 4s_old_town: start 0.002 (n=552), edge 0.000 (n=48), deep 0.000 (n=956)
  - 4s_countryside: start 0.000 (n=108), edge 0.000 (n=114), deep 0.002 (n=2532)

## Held-out, per descriptor (mean over datasets and seeds)

| descriptor | n | HSI rec | SH rec | HSI−SH | wins | HSI seg | HSI err | SH err |
|---|---|---|---|---|---|---|---|---|
| cosplace | 12 | 0.799 | 0.806 | -0.007 | 9 | 0.001 | 10.0 | 10.3 |
| netvlad | 12 | 0.595 | 0.524 | +0.070 | 10 | 0.000 | 19.6 | 20.2 |
| megaloc | 12 | 0.868 | 0.931 | -0.062 | 6 | 0.000 | 7.6 | 7.6 |
| dinov2 | 12 | 0.606 | 0.468 | +0.138 | 10 | 0.003 | 14.0 | 21.1 |
| salad | 18 | 0.853 | 0.894 | -0.041 | 7 | 0.000 | 8.9 | 7.9 |
| mixvpr | 18 | 0.835 | 0.866 | -0.031 | 9 | 0.000 | 8.0 | 8.2 |

## Ablations (held-out runs; mean over datasets of the per-dataset means)

| variant | recall | segFAR | runs seg>0.05 | nav err | worst-class rate |
|---|---|---|---|---|---|
| HSI | 0.771 | 0.0007 | 0 | 10.9 | 0.002 |
| HSI-rot-m | 0.790 | 0.0024 | 0 | 10.7 | 0.011 |
| geo | 0.678 | 0.0015 | 2 | 16.5 | 0.026 |
| (idea 1) SH | 0.767 | 0.0031 | 1 | 11.9 | – |
