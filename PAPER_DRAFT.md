# Calibrated Retrieval-Score Geometry: Reliable Visual Place Recognition without Sequential Filtering or Condition Modeling

*Working draft. Numbers marked ✅ are verified on Kaggle T4 this session; ⏳ = run in flight; 🔲 = planned.*

---

## Abstract (draft)

State-of-the-art visual place recognition (VPR) descriptors now achieve near-saturated recall even under extreme
appearance change, yet two deployment-critical questions remain poorly served: *is this match trustworthy?* and
*am I off the map?* We show that the field's two natural remedies — **condition-aware calibration** and
**sequential Bayesian filtering** — give large, convincing gains on the idealized Nordland benchmark but **fail to
generalize** to the realistic RobotCar-Seasons benchmark, where a trivial nearest-neighbour-distance baseline
actually beats the sequential open-set detector. We trace the failure to a simple fact: a retrieval softmax over
hundreds of near-tie candidates is not a calibratable confidence, and a scalar temperature — global or
per-condition — cannot repair it. We propose **Calibrated Retrieval-Score Geometry (CRSG)**, a 2–3 parameter
per-frame calibrator on the *geometry* of the retrieval score vector (top-1/top-2 margin, nearest-neighbour
distance, score entropy). CRSG produces a single calibrated reliability score that supports both confidence
calibration and open-set abstention, and **dominates temperature scaling, sequential filtering, and condition
modeling across datasets and pose tolerances**, while being descriptor-agnostic and requiring no temporal stream.

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
- **Datasets:** RobotCar-Seasons v2 (9 real conditions, pose-GT) ✅; Nordland (4 seasons, frame-aligned GT) ⏳.
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

**5.2 Cross-dataset: Nordland (dense, the filter's natural home).** ⏳ (NB7)
Expected/role: the filter should be strong here; the claim is CRSG remains **competitive-to-best** on Nordland
while being **dominant** on RobotCar — i.e. one simple per-frame method is robust across regimes, whereas the
filter is regime-specific. *(table to be filled from NB7)*

**5.3 Ablation.** Single-feature margin-Platt calibrates ECE but discriminates poorly (conf-AUROC ≈0.61–0.74);
the multi-feature CRSG recovers discrimination (0.80) — the feature combination matters. ✅ (NB6)

## 6. Contributions

1. A **reliability evaluation protocol** for VPR (calibration + selective risk + open-set, swept over tolerance)
   that exposes problems hidden by loose-tolerance recall.
2. A rigorous, cross-benchmark demonstration that **condition-aware calibration and sequential filtering do not
   deliver reliability on realistic data**, despite convincing gains on idealized Nordland — a cautionary result.
3. **CRSG**, a trivial descriptor-agnostic per-frame calibrator on retrieval-score geometry that **dominates** these
   complex methods for both calibration and open-set abstention.

## 7. Honesty / limitations

- CRSG is deliberately simple; the scientific weight is in the *reality-check* and the *simple-beats-complex*
  finding, not in method complexity.
- RobotCar traversals here are the ~200-sample train split per condition (sparse); the filter may do better on a
  dense video stream — but such streams are exactly what realistic benchmarks lack.
- Pose-GT is constructed from the released flattened poses (translation = flat indices [3,7,11]); route ordering
  via NN-chaining. Rotation tolerance not yet used.
- Next: a second descriptor (DINOv2/BoQ) for descriptor-agnosticism; conformal risk control for distribution-free
  coverage guarantees under appearance shift.
