# HSI wave summary

runs: 441 (held-out 413, with idea-1 SH on the same run 413)

## Held-out runs: mean recall / segFAR / navigation error per dataset

| dataset | n | HSI rec / seg / err | geo rec / seg / err | SH rec / seg / err | CST-JS rec / seg / err | oracle rec / seg / err | HSI−SH rec (wins) | HSI−SH err (better) |
|---|---|---|---|---|---|---|---|---|
| boreas | 56 | 0.889 / 0.001 / 4.4 | 0.832 / 0.001 / 5.9 | 0.777 / 0.002 / 4.5 | 0.781 / 0.011 / 8.5 | 0.882 / 0.000 / 2.1 | +0.113 (56/56) | -0.1 (41/56) |
| nclt | 2 | 0.577 / 0.000 / 5.1 | 0.565 / 0.000 / 3.9 | 0.690 / 0.000 / 3.2 | 0.711 / 0.002 / 3.4 | 0.784 / 0.000 / 2.2 | -0.113 (0/2) | +1.9 (0/2) |
| cmu | 56 | 0.692 / 0.011 / 4.3 | 0.450 / 0.005 / 3.6 | 0.835 / 0.009 / 3.9 | 0.816 / 0.019 / 3.8 | 0.945 / 0.000 / 2.9 | -0.142 (0/56) | +0.4 (34/56) |
| nord | 56 | 0.769 / 0.000 / 5.1 | 0.679 / 0.000 / 5.9 | 0.770 / 0.000 / 6.0 | 0.783 / 0.001 / 6.1 | 0.676 / 0.000 / 5.1 | -0.000 (22/56) | -0.9 (21/56) |
| 4s_office_loop | 56 | 0.867 / 0.000 / 8.9 | 0.697 / 0.001 / 11.6 | 0.803 / 0.000 / 9.7 | 0.815 / 0.008 / 9.7 | 0.914 / 0.000 / 8.3 | +0.064 (54/56) | -0.7 (48/56) |
| 4s_old_town | 56 | 0.710 / 0.000 / 30.5 | 0.594 / 0.003 / 47.2 | 0.708 / 0.006 / 25.9 | 0.715 / 0.012 / 39.6 | 0.844 / 0.000 / 19.3 | +0.003 (29/56) | +4.6 (19/56) |
| 4s_countryside | 56 | 0.638 / 0.005 / 27.4 | 0.595 / 0.011 / 27.8 | 0.492 / 0.001 / 33.5 | 0.503 / 0.005 / 32.9 | 0.739 / 0.000 / 16.0 | +0.145 (56/56) | -6.1 (52/56) |
| oxford | 45 | 0.758 / 0.005 / 21.5 | 0.338 / 0.002 / 35.3 | 0.719 / 0.004 / 21.9 | 0.729 / 0.021 / 22.0 | 0.899 / 0.000 / 15.9 | +0.039 (33/45) | -0.4 (35/45) |
| stlucia | 30 | 0.904 / 0.002 / 18.8 | 0.332 / 0.000 / 44.9 | 0.761 / 0.001 / 25.5 | 0.763 / 0.021 / 25.6 | 0.896 / 0.000 / 17.3 | +0.143 (30/30) | -6.7 (30/30) |

## Pre-registered hypotheses (Entry 1) on the held-out runs

- **H1 (validity):** mean segFAR <= 0.05 on 9/9 datasets; runs > 0.05: 0/413 (0.0%) -> **supported**
- **H2 (recall):** HSI >= SH on 6/9 datasets; pooled mean difference +0.0388 -> **supported**
- **H3 (weak descriptors):** DINOv2 + NetVLAD held-out runs: mean HSI − SH = +0.0888 over 133 runs -> **supported**
- **H4 (navigation):** mean error within +1 m of SH on 7/9 datasets -> **supported**
- **H5 (position audit):** every class <= 0.07 (classes with >= 50 segments) on 9/9 datasets -> **supported**
  - boreas: start 0.011 (n=4632), edge 0.001 (n=3954), deep 0.000 (n=86096)
  - nclt: start 0.000 (n=186), edge 0.000 (n=52), deep 0.000 (n=374)
  - cmu: start 0.013 (n=24472), edge 0.000 (n=0), deep 0.000 (n=0)
  - nord: start 0.000 (n=496), edge 0.000 (n=798), deep 0.000 (n=20102)
  - 4s_office_loop: start 0.000 (n=504), edge 0.000 (n=806), deep 0.000 (n=14580)
  - 4s_old_town: start 0.000 (n=1756), edge 0.002 (n=612), deep 0.000 (n=10238)
  - 4s_countryside: start 0.023 (n=1152), edge 0.007 (n=684), deep 0.004 (n=13560)
  - oxford: start 0.021 (n=2634), edge 0.007 (n=8799), deep 0.004 (n=34788)
  - stlucia: start 0.058 (n=120), edge 0.000 (n=1794), deep 0.000 (n=2556)

## Held-out, per descriptor (mean over datasets and seeds)

| descriptor | n | HSI rec | SH rec | HSI−SH | wins | HSI seg | HSI err | SH err |
|---|---|---|---|---|---|---|---|---|
| cosplace | 64 | 0.798 | 0.775 | +0.023 | 39 | 0.003 | 13.8 | 14.1 |
| netvlad | 64 | 0.608 | 0.548 | +0.059 | 52 | 0.002 | 20.8 | 21.6 |
| megaloc | 64 | 0.878 | 0.884 | -0.007 | 38 | 0.002 | 11.3 | 11.0 |
| dinov2 | 69 | 0.610 | 0.494 | +0.116 | 55 | 0.005 | 18.7 | 23.1 |
| salad | 76 | 0.860 | 0.845 | +0.015 | 43 | 0.003 | 11.8 | 12.0 |
| mixvpr | 76 | 0.849 | 0.822 | +0.027 | 53 | 0.003 | 12.3 | 12.3 |

## Ablations (held-out runs; mean over datasets of the per-dataset means)

| variant | recall | segFAR | runs seg>0.05 | nav err | worst-class rate |
|---|---|---|---|---|---|
| HSI | 0.756 | 0.0027 | 0 | 14.0 | 0.058 |
| HSI-adapt | 0.651 | 0.0043 | 7 | 18.8 | 0.045 |
| HSI-e1 | 0.626 | 0.0016 | 1 | 20.1 | 0.012 |
| HSI-m | 0.746 | 0.0027 | 1 | 14.6 | 0.067 |
| HSI-nofloor | 0.630 | 0.0032 | 1 | 20.1 | 0.023 |
| HSI-nogate | 0.631 | 0.0031 | 1 | 19.9 | 0.012 |
| HSI-nosc | 0.640 | 0.0042 | 13 | 20.9 | 0.127 |
| HSI-nounl | 0.630 | 0.0025 | 7 | 19.9 | 0.018 |
| HSI-regime | 0.534 | 0.0002 | 0 | 23.6 | 0.002 |
| HSI-rigid | 0.635 | 0.0018 | 0 | 19.6 | 0.018 |
| HSI-rot | 0.632 | 0.0017 | 1 | 19.7 | 0.013 |
| HSI-rot-m-c | 0.761 | 0.0028 | 0 | 13.7 | 0.058 |
| HSI-rot-m-s | 0.753 | 0.0022 | 0 | 14.5 | 0.058 |
| HSI-rot-m-sc | 0.758 | 0.0023 | 0 | 14.3 | 0.058 |
| HSI-sess | 0.582 | 0.0007 | 0 | 21.7 | 0.006 |
| Xu21 | 0.689 | 0.1903 | 202 | 47.5 | 0.710 |
| anc | 0.547 | 0.0147 | 40 | 22.2 | 0.175 |
| geo | 0.564 | 0.0026 | 6 | 20.7 | 0.039 |
| oracle | 0.842 | 0.0000 | 0 | 9.9 | 0.000 |
| top1 | 0.842 | 1.0000 | 413 | 162.0 | 1.000 |
| (idea 1) SH | 0.728 | 0.0025 | 2 | 14.9 | – |
