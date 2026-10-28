# Master results — Self-calibrating maps (SelfCal / SelfCal-AA)

Current direction (Entries 12–13). The previous CRSG tables are superseded (see `LITERATURE_GATE.md`); they remain in
git history (commit `96ced6c`). All numbers are reproducible from the NB15 descriptor dumps with `analysis/`:
`eval_all.py` (main comparison), `exp3_fdr.py` (BH / label-free confidence), `exp5_ablation.py`, `exp6_dominance.py`,
`exp7_mapsize.py`, `exp8_dualcenter.py`, `summarize.py`; paper tables via `paper/build_tables.py`.

Protocol: off-map queries by leave-one-300 m-block-out of the map (RobotCar 1,386 / CMU 14,117 / Nordland 12,180);
correct = top-1 within (5 m, 10°) (RobotCar official coarse threshold; CMU) or 2 places (Nordland); aliasing =
in-map query whose top-1 is > 25 m (5 places) away. #viol = conditions whose FAR is significantly above α
(one-sided binomial, Bonferroni).

## Aggregate over 6 descriptors × 3 datasets (138 deployment conditions), α = 0.05
See `paper/tables.md` (Table 2a) — SelfCal-AA 0/138 violating, mean TPR 0.676, median aliasing 0.008;
SelfCal 0/138, mean TPR 0.718 (oracle 0.721); LOCO (SAFEVPR protocol) 38/138 with a violation in all 18 settings;
Quantile Transfer 64/138; benign threshold 25/138; CRSG 25/138; Gaussian z-norm 112/138.

## SALAD, α = 0.05 (FAR / #viol / TPR / aliasing-accept)
| method | RobotCar (9) | CMU (11) | Nordland (3) |
|---|---|---|---|
| SelfCal-AA (ours) | 0.004 / 0/9 / 0.988 / 0.00 | 0.002 / 0/11 / 0.853 / 0.01 | 0.008 / 0/3 / 0.754 / 0.06 |
| SelfCal (ours) | 0.004 / 0/9 / 0.994 / 0.01 | 0.009 / 0/11 / 0.956 / 0.26 | 0.031 / 0/3 / 0.788 / 0.52 |
| Threshold benign→all | 0.109 / 5/9 / 0.997 / 0.50 | 0.052 / 4/11 / 0.985 / 0.78 | 0.037 / 0/3 / 0.630 / 0.49 |
| Conformal LOCO | 0.052 / 1/9 / 0.997 / 0.34 | 0.051 / 4/11 / 0.984 / 0.77 | 0.070 / 2/3 / 0.666 / 0.51 |
| Quantile Transfer | 0.097 / 4/9 / 0.998 / 0.47 | 0.054 / 2/11 / 0.993 / 0.80 | 0.109 / 2/3 / 0.901 / 0.72 |
| CRSG benign→all | 0.099 / 4/9 / 0.996 / 0.33 | 0.054 / 4/11 / 0.982 / 0.68 | 0.041 / 0/3 / 0.814 / 0.45 |
| Oracle (labels, all cond.) | 0.040 / 0/9 / 0.995 / — | 0.049 / 0/11 / 0.992 / — | 0.050 / 0/3 / 0.780 / — |

Full per-descriptor tables: `analysis/results/summary_a0.05.md`, `summary_a0.1.md`, `paper/tables.md`.
