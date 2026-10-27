# CRSG — Master Results Table

All numbers verified on Kaggle T4 this session (SALAD descriptor unless noted). Lower ECE/AURC better; higher
conf-AUROC / off-map AUROC better. "CRSG" = per-frame logistic on retrieval-score geometry (margin, NN-dist,
entropy). Full method/context in `PAPER_DRAFT.md`; honest narrative in `RESEARCH_LOG.md`.

## Reliability: calibration + discrimination (pooled cross-fit)

Headline tolerance chosen where errors are non-trivial (acc≈0.8). **Bold** = best in column per dataset.

| dataset (regime) | tol | method | ECE ↓ | AURC ↓ | conf-AUROC ↑ |
|---|---|---|---|---|---|
| **RobotCar** (sparse, realistic) | 2 m | softmax | 0.485 | 0.133 | 0.749 |
| | | temperature | 0.303 | 0.135 | 0.736 |
| | | sequential filter | 0.301 | 0.132 | 0.677 |
| | | CCBF | 0.269 | 0.130 | 0.671 |
| | | **CRSG (ours)** | **0.069** | **0.090** | **0.801** |
| | | *oracle AURC* | — | 0.030 | — |
| **CMU** (sparse, realistic) | 2 m | softmax | 0.651 | 0.085 | 0.640 |
| | | temperature | 0.435 | 0.084 | 0.633 |
| | | sequential filter | 0.416 | 0.080 | 0.603 |
| | | CCBF | 0.359 | 0.081 | 0.601 |
| | | **CRSG (ours)** | **0.055** | **0.048** | **0.769** |
| | | *oracle AURC* | — | 0.008 | — |
| **Nordland** (dense, idealized) | 0 fr | softmax | 0.254 | 0.063 | 0.813 |
| | | temperature | 0.039 | 0.041 | 0.920 |
| | | CRSG (ours) | 0.040 | 0.037 | 0.941 |
| | | **sequential filter** | **0.017** | **0.019** | 0.940 |
| | | CCBF | 0.017 | 0.019 | 0.941 |
| | | *oracle AURC* | — | 0.018 | — |
| **Nordland @ scale** (3000/season, N=9000) | 2 fr | softmax | 0.432 | 0.061 | 0.822 |
| | | temperature | 0.086 | 0.035 | 0.932 |
| | | CRSG (ours) | 0.047 | 0.029 | **0.957** |
| | | **sequential filter** | 0.063 | **0.011** | 0.933 |

*Scale-up (NB13, T4) is consistent with the 800/season result: CRSG beats softmax & temperature and has the best
conf-AUROC; the sequential filter keeps its AURC + off-map edge on dense Nordland.*

**Reading:** CRSG dominates all methods on both **realistic** datasets (RobotCar, CMU). On **idealized dense**
Nordland the sequential filter is best (near-oracle) and CRSG is competitive (beats softmax & temperature). The
sequential/condition methods never beat softmax on the realistic data.

## Open-set / off-map detection (AUROC)

| dataset | CRSG | SUE | filter-null |
|---|---|---|---|
| RobotCar | 0.949 | 0.948 | 0.898 |
| CMU | 0.861 | **0.895** | **0.228 (collapse)** |
| Nordland | 0.804 | 0.935 | **0.992** |

**Reading:** the sequential filter-null is the best OOD detector on dense Nordland (0.99) but **collapses on sparse
realistic data** (CMU 0.23 ≪ random-ish). SUE and CRSG are the robust instantaneous OOD signals on realistic data.

## Why the inherited methods fail

| finding | evidence |
|---|---|
| Condition-aware temperature (CCBF) is **inert** | per-condition τ spread: Nordland 1.22×, RobotCar 1.49×; per-cond ECE gain ≈0% |
| Sequential filtering is **regime-specific** | fixes calibration on Nordland (ECE 0.076→0.028) but not RobotCar (0.47→0.44); off-map collapses on CMU (0.23) |
| Calibration can't **rescue** the filter on sparse data | CRSG-filter AURC 0.137 ≈ raw filter ≫ CRSG-single 0.090 (NB8) — the margin signal is destroyed, not recoverable |

## Descriptor-agnosticism (RobotCar, DINOv2 vs SALAD)

CRSG fixes calibration for both (ECE 0.03–0.06 vs softmax/temperature 0.2–0.7) and wins open-set for both. Its
*discrimination* edge over raw softmax ranking is larger for the stronger descriptor (clear SALAD, ~parity DINOv2).

## Conformal risk control (RobotCar, tol 2 m, δ=0.1)  ✅ NB12

**C1 — selective risk control (exchangeable): CRSG is a far better conformity score.**

| target α | softmax risk / cov | CRSG risk / cov |
|---|---|---|
| 0.10 | — / **0.00** (abstains all) | 0.11 / **0.615** |
| 0.20 | 0.21 / 0.97 | 0.22 / 0.98 |

**C2 — marginal guarantee breaks under appearance shift** (calibrate benign → deploy hard): realized hard-risk
0.115 (α=0.10), 0.304 (α=0.20) — exceeds target.

**C3 — Mondrian per-condition conformal restores control** (α=0.10): worst-condition risk marginal **0.221** →
Mondrian **0.000** (every condition ≤ target).
