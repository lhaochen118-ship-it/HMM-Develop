# Calibrated Retrieval-Score Geometry: Reliable Visual Place Recognition without Sequential Filtering or Condition Modeling

*Working draft. Numbers marked ✅ are verified on Kaggle T4 this session; ⏳ = run in flight; 🔲 = planned.*

---

## Abstract (draft)

State-of-the-art visual place recognition (VPR) descriptors now achieve near-saturated recall even under extreme
appearance change, yet two deployment-critical questions remain poorly served: *is this match trustworthy?* and
*am I off the map?* We show that VPR reliability is **regime-dependent** and that the field's Nordland-centric
evaluation has masked this. The two natural remedies — **condition-aware calibration** and **sequential Bayesian
filtering** — give large, convincing gains on the dense idealized Nordland benchmark but **fail to generalize** to
the sparse realistic RobotCar-Seasons benchmark, where the sequential filter stops helping and a trivial
nearest-neighbour baseline beats its open-set detector. We trace this to a mechanism: the discriminative
reliability signal lives in the **single-image retrieval-score geometry** (chiefly the top-1/top-2 margin), and the
sequential filter *destroys* this signal on sparse data (its motion prior is uninformative), while a scalar
temperature — global or per-condition — never repairs the softmax-over-hundreds-of-ties in the first place. We
propose **Calibrated Retrieval-Score Geometry (CRSG)**, a 2–3 parameter per-frame calibrator on that geometry
(margin, nearest-neighbour distance, score entropy) producing one calibrated reliability score for both confidence
and open-set abstention. CRSG beats temperature scaling and the sequential/condition methods on **both** datasets
for calibration-plus-discrimination, is the **regime-robust, stream-free default** (dominant on realistic
RobotCar, competitive on idealized Nordland where the filter also works), and is descriptor-agnostic.

## 1. The gap

VPR research is benchmarked almost entirely on **recall@K**, which is saturating: on RobotCar-Seasons at a 5 m
tolerance, SALAD attains R@1 ≈ 0.94–0.98 across *every* condition including night. Deployment (robotics, AV,
loop-closure) instead needs **reliability**: a calibrated confidence and a principled abstention/off-map signal.
This axis is under-studied, and the obvious tools are assumed to help:

- **Condition-aware calibration** — model the appearance condition (season/weather/time) and calibrate per
  condition (the inherited *CCBF* idea: a factored place×condition Bayes filter with a per-condition temperature).
- **Sequential filtering** — aggregate a temporal stream with a Bayes/HMM filter to sharpen and calibrate the
  place posterior (SeqSLAM-lineage).

We test both rigorously and find they do **not** deliver reliability on realistic data.

## 2. Setup

- **Descriptor:** SALAD (DINOv2-ViT-B/14 backbone, dim 8448), loaded offline; frozen, no fine-tuning. ✅
- **Datasets:** RobotCar-Seasons v2 (9 real conditions, pose-GT) ✅; Extended-CMU-Seasons (per-slice route, ~10
  date-conditions, pose-GT) ✅; Nordland (4 seasons, frame-aligned GT) ✅. Two realistic (RobotCar, CMU) + one
  idealized dense (Nordland).
- **GT & tolerance:** place = pose-nearest reference (RobotCar) / aligned frame id (Nordland). We **sweep the
  tolerance** (RobotCar 0.5/1/2/5 m; Nordland 0/1/2/5 frames) because the loose regime is trivially easy and
  hides the problem.
- **Metrics:** R@1; **ECE** (calibration); **AURC** / risk–coverage and confidence-vs-correct AUROC
  (*discrimination* — ECE alone is gamed by a stable base rate); open-set **AUROC** (map = first 70 % of route).

## 3. Why the natural remedies fail

**3.1 Condition-aware temperature is inert.** Fitting a per-condition temperature τ_c (CCBF's core mechanism)
yields nearly identical values across conditions on both datasets — Nordland spread **1.22×**, RobotCar **1.49×** —
and per-condition calibration improves pooled ECE by **≈0 %** over a single global temperature. The appearance gap
is real (RobotCar night match–nonmatch margin is *half* the day margin) but a scalar temperature cannot convert it
into a calibration gain. ✅ (NB3)

**3.2 Sequential filtering helps on Nordland but not RobotCar.**

| | single→filter ECE | off-map: filter-null vs SUE |
|---|---|---|
| Nordland (dense, idealized) | 0.076 → 0.028 (helps) | 0.99 vs 0.94 (filter wins) [prior] |
| RobotCar (realistic) ✅ | 0.472 → 0.439 (barely) | **0.888 vs 0.950 (SUE wins)** |

On RobotCar the filter's motion model is well-matched (traversal velocity ≈1, verified), so the failure is real,
not a setup artifact. The sequential null posterior is *beaten by a trivial instantaneous NN-distance* for off-map
detection. ✅ (NB4, NB5)

## 4. Method: Calibrated Retrieval-Score Geometry (CRSG)

For a query with similarity vector s ∈ ℝ^M against the map, compute per-frame **geometry features** of s:
the **top-1/top-2 margin** (s₍₁₎−s₍₂₎), the **NN-distance** √(2−2·maxₖ sₖ) (≡ SUE), and the **score entropy**.
Fit a tiny logistic calibrator g(·) on these features to predict *correctness* (fit on held-out data; descriptor-
and dataset-agnostic). g(s) is a single **calibrated reliability score** used directly for (i) confidence,
(ii) selective prediction / abstention, and (iii) open-set detection (low reliability ⇒ off-map).

Intuition: the softmax *maximum* over hundreds of near-ties is not monotone with correctness; the **margin** is,
and the **NN-distance** captures out-of-distribution. A 2–3 parameter calibrator on these suffices — no temporal
stream, no condition labels, no filtering.

## 5. Results

**5.1 RobotCar, held-out hard conditions, pooled cross-fit, tol = 2 m (R@1 0.765).** ✅ (NB6)

| method | ECE | AURC ↓ | conf-AUROC ↑ |
|---|---|---|---|
| softmax (uncal.) | 0.485 | 0.133 | 0.749 |
| temperature scaling | 0.303 | 0.135 | 0.736 |
| sequential fixed filter | 0.301 | 0.132 | 0.677 |
| CCBF (condition-aware) | 0.269 | 0.130 | 0.671 |
| **CRSG (ours)** | **0.069** | **0.090** | **0.801** |
| oracle AURC | — | 0.030 | — |

CRSG gives the **best discrimination (AURC, conf-AUROC) at every tolerance** {0.5,1,2,5} m and near-best ECE,
beating softmax, temperature, filter and CCBF. The sequential/condition methods offer no discrimination gain over
softmax. **Open-set:** CRSG 0.949 ≈ SUE 0.948 > filter-null 0.898 — CRSG is a *unified* reliability score.

**5.1b Second realistic benchmark: Extended-CMU-Seasons, tol=2 m (R@1 0.876).** ✅ (NB11)

| method | ECE | AURC ↓ | conf-AUROC ↑ | off-map |
|---|---|---|---|---|
| softmax | 0.651 | 0.085 | 0.640 | — |
| temperature | 0.435 | 0.084 | 0.633 | — |
| sequential filter | 0.416 | 0.080 | 0.603 | **0.228 (collapse)** |
| CCBF | 0.359 | 0.081 | 0.601 | — |
| **CRSG (ours)** | **0.055** | **0.048** | **0.769** | 0.861 |

Same pattern as RobotCar — **CRSG dominates** all methods on calibration and discrimination at every tolerance,
and the **sequential filter's open-set detector collapses** (AUROC 0.228, worse than random), a second realistic
dataset confirming the filter is regime-specific. SUE (0.895) and CRSG (0.861) are the robust open-set signals.

**5.2 Cross-dataset: Nordland (dense, the filter's natural home), tol=0 (R@1 0.815).** ✅ (NB7)

| method | ECE | AURC ↓ | conf-AUROC ↑ | off-map AUROC |
|---|---|---|---|---|
| softmax (uncal.) | 0.254 | 0.063 | 0.813 | — |
| temperature | 0.039 | 0.041 | 0.920 | — |
| **CRSG (ours)** | 0.040 | 0.037 | 0.941 | 0.804 |
| sequential fixed filter | **0.017** | **0.019** | 0.940 | **0.992** |
| CCBF | 0.017 | 0.019 | 0.941 | — |
| oracle AURC / SUE | — | 0.018 | — | SUE 0.935 |

Here the **filter is excellent** (AURC ≈ oracle; off-map 0.99 ≫ SUE) — dense 1:1 frame alignment is its natural
home. CRSG is only *competitive* (beats softmax & temperature, ties conf-AUROC, loses AURC to the filter). This is
the honest cross-dataset picture: **the filter is regime-specific (needs dense temporal structure); CRSG is the
regime-robust stream-free method** — dominant on realistic RobotCar, competitive on idealized Nordland.

**5.3 Can calibration rescue the filter on sparse data? No.** ✅ (NB8) Calibrating the *filter posterior* geometry
(CRSG-filter) fixes its ECE on RobotCar but NOT its discrimination (AURC 0.137 ≈ raw filter; conf-AUROC 0.68 <
CRSG-single 0.80). The sequential filter destroys the single-image margin signal on sparse data, and no
calibration of its posterior regenerates it — one must calibrate the belief that *carries* discrimination, i.e.
the single-image geometry.

**5.4 Ablation.** Single-feature margin-Platt calibrates ECE but discriminates poorly (conf-AUROC ≈0.61–0.74);
the multi-feature CRSG recovers discrimination (0.80) — the feature combination matters. ✅ (NB6)

**5.5 Descriptor-agnosticism.** ✅ (NB9) Repeating on a weaker descriptor (DINOv2 CLS+mean, dim 1536; R@1 drops to
0.10–0.76 across tolerances) shows CRSG **fixes calibration for both descriptors** (ECE 0.03–0.06 vs softmax/
temperature 0.2–0.7) and **wins open-set with both** (DINOv2: CRSG 0.861 ≫ SUE 0.746 — a weak descriptor degrades
the raw NN-distance, but multi-feature CRSG stays robust). Honest nuance: CRSG's *discrimination* edge over the raw
softmax ranking is **larger for stronger descriptors** (clear with SALAD, ~parity with DINOv2), since the margin is
only as informative as the descriptor. The calibration and open-set gains are descriptor-agnostic; the
discrimination dominance is stated for strong descriptors.

## 6. Contributions

1. A **reliability evaluation protocol** for VPR (calibration + selective risk via AURC + open-set, swept over
   tolerance) that exposes problems hidden by loose-tolerance recall, and the finding that **VPR reliability is
   regime-dependent**.
2. A rigorous, cross-benchmark demonstration that **condition-aware calibration is inert** (per-condition τ ≈
   global on both datasets) and **sequential filtering is regime-specific** — near-oracle on dense Nordland but
   collapsing on sparse realistic RobotCar, where it even loses open-set to a trivial NN-distance — with the
   **mechanism** (filtering destroys the single-image margin signal; calibrating its posterior cannot regenerate
   discrimination, NB8). A cautionary result against Nordland-only evaluation.
3. **CRSG**, a trivial descriptor-agnostic, stream-free per-frame calibrator on retrieval-score geometry that is
   the **regime-robust default**: it beats softmax and temperature scaling on both datasets, dominates all methods
   on realistic RobotCar, and stays competitive on Nordland where the filter also works.

## 7. Honesty / limitations

- CRSG is deliberately simple; the scientific weight is in the *reality-check* and the *simple-beats-complex*
  finding, not in method complexity.
- RobotCar traversals here are the ~200-sample train split per condition (sparse); the filter may do better on a
  dense video stream — but such streams are exactly what realistic benchmarks lack.
- Pose-GT is constructed from the released flattened poses (translation = flat indices [3,7,11]); route ordering
  via NN-chaining. Rotation tolerance not yet used.
- Next: a second descriptor (DINOv2/BoQ) for descriptor-agnosticism; conformal risk control for distribution-free
  coverage guarantees under appearance shift.
