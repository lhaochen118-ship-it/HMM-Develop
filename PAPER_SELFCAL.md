# Your Map Is Its Own Calibration Set: Label-Free, Shift-Robust Rejection of False Matches in Visual Place Recognition

*Working draft (supersedes the CRSG framing of `PAPER_DRAFT.md`, see `LITERATURE_GATE.md`). Numbers are filled from
`analysis/results/*.json`; ⏳ = pending run.*

## Abstract (draft)

Visual place recognition (VPR) returns a best match for every query, but a robot must decide whether to *trust*
it: accepting a match for a place that is not in the map — or that only looks like one — corrupts SLAM graphs and
relocalisation. Existing acceptance rules (thresholds, learned integrity monitors, conformal calibration) all need
labelled query–map pairs from the deployment conditions, and we show that their false-accept guarantees break as soon
as appearance changes (night, rain, snow, seasons) between calibration and deployment. We observe that VPR offers a
source of labelled negatives for free: **the map itself**. Holding out each spatial block of the map turns every map
image into a query that is off-map *by construction*. Calibrating an acceptance statistic against these map
pseudo-queries yields split-conformal p-values with no human or deployment labels. To make this calibration transfer
across appearance conditions we use statistics that are invariant to per-query affine changes of the similarity
scores (the dominant effect of illumination and weather on modern descriptors), computed against spatially distant map
regions, on hubness-reduced (map-centred) descriptors, and combined by a self-calibrated minimum-p rule. Across
RobotCar-Seasons, Extended-CMU-Seasons (a 2,418-image city map, 21k queries, 11 dates) and Nordland, and ⏳ six
descriptors, the resulting test controls the off-map false-accept rate in every one of the 23 deployment conditions,
whereas thresholds calibrated with labels on benign conditions, leave-one-condition-out conformal calibration, quantile
transfer and learned calibrators violate the target in up to 5 of 9 conditions. Its power approaches an oracle that
has labels for every condition, and it provides label-free FDR control (Benjamini–Hochberg) and calibrated confidence.

## 1. Problem

Map M = {(f_j, x_j)}: descriptors and positions. Query q, similarities s_j = ⟨f_q, f_j⟩, retrieval j* = argmax s_j.
Decision: accept (localise at x_{j*}) or reject. **Null hypothesis H0(q): q is off-map** (no map position within δ).
Goal: P(accept | H0) ≤ α in *every* deployment condition c, **without labelled data**.

## 2. Method — self-calibrating maps (SelfCal)

1. **Map pseudo-queries.** Partition map positions into blocks B_1..B_L (300 m; 200 frames on Nordland). For map item i
   in block b with d(x_i, M∖B_b) > δ, compute T_i^0 = T(f_i; M∖B_b). These are off-map by construction (free labels).
2. **Shift-robust statistic.** z_far(q) = (s_{j*} − μ_far)/σ_far where μ_far, σ_far are the mean/std of the
   region maxima (10 m cells) farther than ρ = 25 m from x_{j*}. Invariant to s → a·s + b (a>0).
   Descriptors are centred on the map mean (hubness reduction).
3. **Conformal p-value.** p(q) = (1 + #{i : T_i^0 ≥ T(q)}) / (1 + n).
4. **Self-calibrated combination.** c(q) = min_k p_k(q) over {max-similarity, z_far}; re-calibrated against the
   leave-one-out c-values of the null items.
5. **Batch use.** Benjamini–Hochberg on p-values of a deployment batch; label-free confidence from the two-groups
   model (Storey π0, Grenander density).

## 3. Guarantees

- **T1 (validity).** If, under H0, T(q) is exchangeable with {T_i^0}, then P(p(q) ≤ α) ≤ α (split conformal).
- **T2 (dominance ⇒ conservative).** If the deployment off-map statistic is stochastically dominated by the map null,
  P(T^c ≥ t) ≤ P(T^0 ≥ t) ∀t, then FAR_c(α) ≤ α. Map pseudo-queries share the map's own appearance condition, so any
  appearance change can only make an unrelated query *less* map-like — calibrating on the clean map is safe.
- **T3 (excess risk).** In general FAR_c(α) − α ≤ Δ_c⁺ := sup_t [P(T^c ≥ t) − P(T^0 ≥ t)]₊ (one-sided KS). Affine
  invariance drives Δ_c⁺ → 0 without sacrificing tightness (power).
- **T4 (combination).** The min-p rule re-calibrated with leave-one-out null p-values is a valid conformal p-value under
  exchangeability of the statistic vector.
- **T5 (FDR).** Conformal p-values sharing one calibration set are PRDS (Bates et al., 2023), so BH at level q controls
  FDR ≤ π0·q over a deployment batch.

## 4. Results (SALAD, α = 0.05; FAR on off-map queries / #conditions significantly violating / TPR on correct in-map)

| method | labels | RobotCar (9) | CMU (11) | Nordland (3) |
|---|---|---|---|---|
| **SelfCal[min(maxsim, z_far+c)]** | none | 0.004 / 0/9 / 0.994 | 0.009 / 0/11 / 0.956 | 0.031 / 0/3 / 0.788 |
| SelfCal[z_far+c] | none | 0.012 / 0/9 / 0.995 | 0.019 / 0/11 / 0.864 | 0.048 / 0/3 / 0.840 |
| LabelCal[maxsim] benign→all | benign | 0.109 / **5/9** / 0.997 | 0.052 / **4/11** / 0.985 | 0.037 / 0/3 / 0.630 |
| LabelCal LOCO (SAFEVPR-style) | all other cond. | 0.052 / **1/9** / 0.997 | 0.051 / **4/11** / 0.984 | 0.070 / **2/3** / 0.666 |
| Quantile Transfer | benign | 0.097 / **4/9** / 0.998 | 0.054 / **2/11** / 0.993 | 0.109 / **2/3** / 0.901 |
| CRSG (learned) benign→all | benign | 0.099 / **4/9** / 0.996 | 0.054 / **4/11** / 0.982 | 0.041 / 0/3 / 0.814 |
| Oracle (labels of every cond.) | all | 0.040 / 0/9 / 0.995 | 0.049 / 0/11 / 0.992 | 0.050 / 0/3 / 0.780 |
| Gaussian z-norm (theory only) | none | 0.350 / 9/9 | 0.250 / 11/11 | 0.125 / 3/3 |

⏳ descriptors: NetVLAD, CosPlace, MixVPR, DINOv2, MegaLoc. ⏳ ablations, BH/FDR, figures.
