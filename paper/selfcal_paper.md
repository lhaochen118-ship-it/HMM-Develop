---
title: "Your Map Is Its Own Calibration Set: Label-Free, Shift-Robust Rejection of False Matches in Visual Place Recognition"
author: "Anonymous submission"
---

# Abstract

Visual place recognition (VPR) returns a best match for every query, yet a robot must decide whether to *trust* it:
accepting a match for a place that is not in the map — or one that merely looks like it — corrupts pose graphs and
relocalisation. Existing acceptance rules (similarity thresholds, learned integrity monitors, conformal calibration) all
need labelled query–map pairs, and we show that their false-accept guarantees break as soon as the appearance
condition (night, rain, snow, season) differs between calibration and deployment. We observe that VPR offers labelled
negatives for free: **the map itself**. Holding out each spatial block of the map turns every map image into a query
that is off-map *by construction*. Calibrating an acceptance statistic against these map pseudo-queries yields
split-conformal p-values without any human or deployment labels. To make this calibration transfer across appearance
conditions we use statistics that are invariant to per-query affine changes of the similarity scores, computed against
spatially distant map regions on hubness-reduced (map-centred) descriptors, combine them with a self-calibrated
minimum-p rule, and add an aliasing guard based on the gap to the best distant region. We prove validity under
exchangeability, conservativeness whenever appearance change only makes unrelated queries less map-like, and FDR
control with Benjamini–Hochberg. On RobotCar-Seasons (official reference map and thresholds), Extended-CMU-Seasons
(eleven official slices merged into one 2,418-image city map, 21k queries, 11 dates) and Nordland, with six descriptors
from NetVLAD to MegaLoc, the method keeps the off-map false-accept rate at or below the target in every deployment
condition and rejects nearly all perceptual-aliasing errors, while label-calibrated baselines — including
leave-one-condition-out conformal calibration and quantile transfer — exceed the target in up to five of nine conditions
and accept 33–80% of aliasing errors. Its power approaches an oracle that has labels for every condition.

# 1. Introduction

Modern VPR descriptors are remarkably robust: on RobotCar-Seasons a frozen SALAD descriptor retrieves a reference image
within 5 m and 10° for about 90% of queries even at night. Recall, however, is not what breaks a deployed system. A
VPR module always returns a top-1 match, and the downstream consumer — loop closure in SLAM, relocalisation, map
merging — needs to know *whether to accept it*. Two failure modes dominate. First, the query may come from a place
that is **not in the map** (an unmapped street, a detour, a changed environment). Second, the query may be in the map
but be matched to a **perceptual alias**, a different place that looks the same. A single accepted false match can
corrupt a pose graph irreversibly; a rejected true match merely delays localisation. The decision therefore calls for
an explicit, controllable false-accept rate.

The standard recipe is to calibrate a threshold — on raw similarity, on a hand-crafted score such as the top-1/top-2
ratio, or on the output of a learned integrity monitor — using queries whose correctness is known, possibly with a
conformal procedure that turns the calibration set into a finite-sample guarantee [SAFEVPR, Quantile Transfer]. These
guarantees rest on exchangeability between calibration and deployment queries. VPR is the textbook case in which this
assumption fails: the whole point of the task is that deployment happens under different illumination, weather and
season than any data one could label in advance. We confirm this empirically (§6): thresholds calibrated with labels on
benign conditions exceed a 5% false-accept target by up to 4× at night, and even calibrating on all *other* labelled
conditions (the protocol of SAFEVPR) leaves violations in a third of the deployment conditions on Extended-CMU.

We make three observations that, together, remove the need for labels.

1. **The map provides labelled negatives for free.** A VPR map is a set of images with known positions. Removing a
   spatial block from the map and querying it with one of its own images produces a query that is off-map *by
   construction*. Repeating this for all blocks yields thousands of null examples in the map's own environment —
   exactly the distribution a deployment-time off-map query is drawn from, up to the appearance condition.
2. **Appearance change acts mostly as an affine distortion of similarity scores**, and appearance change can only make
   an unrelated query *less* similar to the map than the map is to itself. Statistics that are invariant to per-query
   affine changes therefore transfer from the map's condition to any deployment condition, and the residual shift is in
   the safe (conservative) direction.
3. **Map geometry separates the two failure modes.** Scoring the top-1 against the best matches of *spatially distant*
   map regions (rather than its own neighbours, which are visually redundant) gives a statistic for off-map detection;
   the gap to the single best distant region exposes aliasing, where the true place is a strong distant competitor.

We call the result **self-calibrating maps (SelfCal)**. It is training-free, label-free, descriptor-agnostic, costs one
offline pass of self-retrieval over the map and a sort per query, and provides a p-value per query that can be used
with a fixed level, with Benjamini–Hochberg for batches, or turned into a calibrated confidence via the two-groups
model — all without labels.

**Contributions.** (i) We show on three benchmarks that label-calibrated acceptance (threshold, learned and conformal)
loses its false-accept guarantee under appearance shift, and that the classical parametric nulls (Gaussian z-norm, EVT
spacing tests) are invalid or degraded by hubness. (ii) We propose SelfCal: map pseudo-queries via spatial hold-out as
a conformal null sample, affine-invariant far-region statistics on map-centred descriptors, a self-calibrated
combination, and an aliasing guard. (iii) We give validity, dominance-based robustness, excess-risk and FDR results.
(iv) We evaluate on RobotCar-Seasons, Extended-CMU-Seasons and Nordland with six descriptors and 23 deployment
conditions, with full ablations; code and descriptor dumps are released.

# 2. Related work

**Uncertainty and introspection for VPR.** Retrieval-based scores — the L2 distance to the nearest reference and the
perceptual-aliasing (PA) ratio of the first two distances [Hausler'21] — remain strong baselines [Zaffar'24]. Zaffar
et al. [CVPR'24] compare them with learned aleatoric uncertainty (BTL [Warburg'21], STUN [Cai'22]) and geometric
verification, and propose SUE, the spatial spread of the top-K reference poses. Miller et al. [RA-L'26] introduce
training-free score-distribution metrics (ratio spread, similarity distribution). KappaPlace [2026] learns a von
Mises–Fisher concentration and reports calibration error. Integrity monitors learn to predict whether a match is within
tolerance from statistics of the distance vector, with SVMs [Carson'22] or MLPs [Claxton'24]; Hussaini et al. predict
when sequence matching helps [2025]. All of these produce *scores*; turning a score into an accept/reject decision with
a known error rate requires labelled calibration data from the deployment conditions. SelfCal is complementary: it can
calibrate any score, and it shows which scores transfer across conditions.

**Thresholds and operating points.** Schubert et al. [ICRA'21] model the similarity distribution as a robust normal and
threshold a high quantile; Vysotska et al. [ICRA'25] adapt thresholds for sequences; Trinh & Lyons [2025] derive
per-place thresholds from negative statistics of the database; Quantile Transfer [IROS'26] transfers a threshold
calibrated on a labelled traversal through quantiles of the deployment similarity distribution. None provides a
guarantee under appearance shift; parametric nulls are invalid in our experiments and raw-score database negatives are
conservative but lose power under shift (§6.4).

**Conformal prediction for robotics and VPR.** Split conformal prediction and its risk-control extensions provide
finite-sample guarantees under exchangeability [Vovk'05, Angelopoulos'21, Bates'23]; Barber et al. [2023] bound the
coverage gap under distribution shift. SAFEVPR [Sier'26] combines a DINOv2 patch-matching verifier with Mondrian
Learn-then-Test and reports empirical FDR validity across conditions when calibrating on labelled data of the other
conditions; Route-MHT [2026] learns a map-out guardrail for thermal VPR. Our null sample comes from the map rather than
from labelled queries, and our robustness argument is a stochastic-dominance property of the map's own condition.

**Using the map at test time.** The reference map with its poses is available before deployment in most VPR
applications; it has been used to fine-tune descriptors (RSF [Zaffar'25]), to choose map density from two reference
traversals [Hussaini'26], and to estimate spatial uncertainty (SUE). We use it as a *calibration set*.

**Hubness.** High-dimensional nearest-neighbour retrieval produces hubs, points that are close to many queries
[Radovanović'10]; centring [Suzuki'13] and local scaling (CSLS [Conneau'18]) reduce it. We find that hubness is what
breaks extreme-value nulls in VPR and that map centring improves the power of the invariant statistic.

# 3. Problem

A map $\mathcal{M}=\{(f_j,x_j)\}_{j=1}^N$ holds L2-normalised global descriptors $f_j$ and positions $x_j$ (metres;
frame index on Nordland). A query $q$ with descriptor $f_q$ yields similarities $s_j=\langle f_q,f_j\rangle$ and the
retrieval $j^*=\arg\max_j s_j$. An *acceptance test* maps the similarity vector (and map positions) to accept/reject.
We distinguish:

* **Off-map false accept:** $q$ has no map position within $\delta$ (40 m) and is accepted. The false-accept rate in
  deployment condition $c$ is $\mathrm{FAR}_c(\alpha)=P(\text{accept}\mid q\text{ off-map}, c)$.
* **Aliasing accept:** $q$ is in the map, but $x_{j^*}$ is farther than $\rho$ (25 m) from its true position.
* **True accept (power):** $q$ is in the map and the top-1 satisfies the localisation tolerance (5 m and 10° on
  RobotCar/CMU; 2 frames on Nordland).

The goal is $\mathrm{FAR}_c(\alpha)\le\alpha$ for every condition $c$, few aliasing accepts and high power, **without
labelled queries**.

# 4. Method: self-calibrating maps

**Map pseudo-queries.** Partition map positions into square blocks of side $L$ (300 m; 200 frames on Nordland). For a
map item $i$ in block $b$ whose distance to $\mathcal{M}\setminus B_b$ exceeds $\delta$, compute the acceptance
statistic of $f_i$ against the reduced map, $T^0_i=T(f_i;\mathcal{M}\setminus B_b)$. Item $i$ is an off-map query
by construction. Using every second map image gives 757 (CMU) to 2,391 (RobotCar) null statistics.

**Far-region statistic.** Hash map positions into cells of side 10 m, take the region maxima $Z_c=\max_{j\in c}s_j$,
and keep the cells farther than $\rho$ from $x_{j^*}$. With mean $\mu_{far}$ and standard deviation $\sigma_{far}$ of
these far-region maxima,
$$z_{far}(q)=\frac{s_{j^*}-\mu_{far}}{\sigma_{far}},\qquad z_{gap}(q)=\frac{s_{j^*}-\max_{c\,\text{far}}Z_c}{\sigma_{far}}.$$
Both are invariant to $s\mapsto as+b$ ($a>0$). Excluding the neighbourhood of $j^*$ prevents the visually redundant
neighbours of a true match from being counted as competitors; using region maxima makes the competitors comparable.

**Hubness reduction.** Descriptors are centred on the map mean and re-normalised (map only, no labels).

**Conformal p-value.** $p_T(q)=\big(1+\#\{i: T^0_i\ge T(q)\}\big)/(1+n)$.

**Self-calibrated combination.** No single statistic is best everywhere (raw max-similarity is strongest on CMU, the
invariant $z_{far}$ on Nordland). We take $m(q)=\min\{p_{\max s}(q),p_{z_{far}}(q)\}$ and re-calibrate it against
the leave-one-out values $m(i)$ of the null items: $p_{comb}(q)=(1+\#\{i:m(i)\le m(q)\})/(1+n)$.

**Aliasing guard (SelfCal-AA).** Accept iff $\max\{p_{comb}(q),\,p_{z_{gap}}(q)\}\le\alpha$. In an aliasing failure
the true place is a strong far competitor, so $z_{gap}$ is small.

**Batches.** With p-values of a deployment batch, Benjamini–Hochberg controls the false-discovery rate, and the
two-groups model (Storey's $\hat\pi_0$, Grenander density estimate) turns $p$ into a calibrated probability of a true
match, $1-\widehat{\mathrm{lfdr}}(p)$ — again without labels.

**Cost.** Offline: one self-retrieval pass over the map ($O(N^2d)$; seconds for $N\approx7{,}000$). Online: the
similarity vector (needed for retrieval anyway), cell maxima and a binary search.

# 5. Guarantees

**T1 (validity).** If, for an off-map query, $T(q)$ and the null statistics $\{T^0_i\}$ are exchangeable, then
$P(p_T(q)\le\alpha)\le\alpha$. *Standard split-conformal argument.*

**T2 (dominance ⇒ conservative).** If in condition $c$ the off-map statistic is stochastically dominated by the map
null, $P(T^c\ge t)\le P(T^0\ge t)\ \forall t$, then $\mathrm{FAR}_c(\alpha)\le\alpha$. Map pseudo-queries are images of
the map's own traversal: appearance change can only make an unrelated query *less* map-like, so calibrating on the clean
map errs on the safe side. Fig. 1 verifies dominance for all nine RobotCar conditions.

**T3 (excess risk).** In general $\mathrm{FAR}_c(\alpha)-\alpha\le\Delta_c^+:=\sup_t[P(T^c\ge t)-P(T^0\ge t)]_+$,
the one-sided Kolmogorov distance. Affine invariance removes the dominant per-query distortion, keeping $\Delta_c^+$
near zero while keeping the null tight (power).

**T4 (combination).** If the vector of statistics is exchangeable with the null vectors, the re-calibrated minimum is a
valid conformal p-value (the leave-one-out ranks are computed exactly as for the query).

**T5 (FDR).** Conformal p-values that share one calibration set are PRDS [Bates'23]; hence Benjamini–Hochberg at level
$q$ controls the off-map FDR at $\pi_0 q$. Aliasing control is empirical: an in-map aliasing failure differs from its
off-map counterpart by an extra strong far competitor, which can only decrease $z_{far}$ and $z_{gap}$.

# 6. Experiments

## 6.1 Setup

**Datasets.** *RobotCar-Seasons v2* [Sattler'18]: the map is the official `overcast-reference` rear-camera traversal
(6,954 images, ~1.3 × 1.1 km) with poses from the official reconstruction (`all.nvm`); queries are the 1,906 rear
images of the public training split in nine conditions (dawn, dusk, night, night-rain, overcast-summer/winter, rain,
snow, sun), whose 6-DoF poses are released (test poses are withheld by the benchmark). A query is correct if the top-1
reference is within the coarsest official threshold (5 m, 10°); we also report the finer official thresholds.
*Extended-CMU-Seasons* [Toft'20]: the eleven slices with released query poses (6–8, 10–13, 21–24) share one world frame
and are consecutive segments, so we merge their official databases into one 2,418-image city map; queries are the
21,407 camera-0 images of 11 dates (Sep 2010 – Jul 2011), correct at (5 m, 10°). *Nordland* [Sünderhauf'13]: 4,500
frame-aligned places per season (uniform subsample of the 35,768-frame route); summer is the map (winter in §6.6),
spring/fall/winter are queries, correct within 2 places.

**Off-map protocol.** We cannot rely on a few hand-picked unmapped streets, so we hold out the map in turn: the map is
partitioned into 300 m blocks (200 places on Nordland); for each block, the block is removed and its queries farther
than 40 m (10 places) from the remaining map are evaluated as *off-map*. This gives 1,386 (RobotCar), 14,117 (CMU) and
12,180 (Nordland) off-map query instances spread over all conditions. In-map queries (within 5 m of a map image) are
evaluated against the full map; in-map queries whose top-1 is farther than 25 m (5 places) are *aliasing* errors.
The method's own null construction (map blocks, pseudo-queries) uses only the map and never sees queries.

**Descriptors.** Frozen, off-the-shelf: NetVLAD (VGG16, Pitts30k, 4,096-d) [Arandjelović'16], CosPlace (ResNet-50,
2,048-d) [Berton'22], MixVPR (ResNet-50, 4,096-d) [Ali-bey'23], DINOv2 ViT-B/14 CLS+mean (1,536-d) [Oquab'24], SALAD
(8,448-d) [Izquierdo'24] and MegaLoc (8,448-d) [Berton'25]. All descriptors are extracted once at 322 × 322.

**Baselines.** (a) *Threshold, benign→all*: split-conformal threshold on the max-similarity of off-map queries of the
two most benign conditions (RobotCar: overcast-summer/winter; CMU: the two dates with the highest recall; Nordland:
fall), applied to all conditions; (b) the same with aliasing errors added to the negatives; (c) *conformal LOCO*,
the SAFEVPR protocol: calibrate on the labelled off-map queries of all *other* conditions and test on the held-out
one; (d) *Quantile Transfer* [Rajani'26]: the benign threshold mapped through the quantile function of each deployment
batch; (e) a learned logistic calibrator on margin, max-similarity and entropy (CRSG) trained on benign conditions;
(f) the PA ratio [Hausler'21]; (g) parametric nulls: Gaussian z-norm with Bonferroni and the closed-form EVT spacing
test; (h) an *oracle* that calibrates max-similarity with the labels of every deployment condition.

**Metrics.** FAR on off-map queries per condition (target α), the number of conditions whose FAR is significantly above
α (one-sided binomial test, Bonferroni over conditions), TPR on correct in-map queries, and the acceptance rate of
aliasing errors.

## 6.2 Main result

Table 1 reports α = 0.05 for SALAD. Every label-calibrated method exceeds the target in at least one realistic dataset —
the benign→all threshold in 5/9 RobotCar conditions (worst FAR 0.21 at night-rain) and 4/11 CMU dates; calibrating on
all other labelled conditions (SAFEVPR protocol) still fails in 1/9, 4/11 and 2/3 conditions — and all of them accept a
third to four fifths of the aliasing errors. Parametric nulls are either invalid (Gaussian z-norm: FAR 0.13–0.35) or
anti-conservative under hubness (EVT spacing: night-rain 0.109). SelfCal-AA, which uses no labels, has **no
significant violation in any of the 23 conditions**, accepts 0.0%, 1.5% and 5.7% of aliasing errors, and its TPR
(0.988 / 0.853 / 0.754) is close to the oracle that holds labels for every condition (0.995 / 0.992 / 0.780).
Without the aliasing guard, SelfCal reaches oracle power on RobotCar and CMU (0.994 / 0.956) while still controlling
the off-map FAR. Fig. 2 shows the same picture for α ∈ [0.005, 0.2].

## 6.3 Why it works

Fig. 1 plots the survival function of the off-map statistic for every RobotCar condition against the map null.
All conditions lie below the null for both max-similarity and z_far: appearance change makes unrelated queries
*less* map-like than the map's own held-out blocks (T2). Table 3 quantifies the excess-risk bound Δ⁺ of T3: with the
map null it is at most 0.052 (max-similarity) and 0.047 (z_far, centred) over all 23 conditions, whereas with a
labelled benign null it reaches 0.255 (max-similarity, night-rain) — exactly the violations of Table 1. The
invariant statistic matters for power: calibrating raw max-similarity on the map is valid but loses most of its
power on Nordland (0.41 vs 0.84), where seasonal change lowers all similarities.

## 6.4 Descriptors

Table 2 repeats the comparison for six descriptors spanning a decade of VPR. ⏳

## 6.5 Batches: FDR and label-free confidence

With an off-map share of 10–50%, Benjamini–Hochberg on SelfCal p-values (q = 0.1) keeps the false-discovery rate of
gross errors at 0.004–0.009 on RobotCar and 0.008–0.011 on CMU (max over conditions 0.046 / 0.023) with power 0.96–0.998,
and the two-groups confidence has ECE 0.013–0.050 without labels (π̂₀ within 0.03–0.08 of the true off-map share).
On Nordland, where 18.5% of in-map queries are gross aliasing errors that the union rule does not target, BH on the
union p-values exceeds q (gross FDR 0.15); with the aliasing-aware p-values, max(p_comb, p_gap), BH keeps the gross FDR
at 0.017–0.021 (max 0.030) with power 0.53–0.75. The label-free confidence is, however, poorly calibrated on Nordland
(ECE ≈ 0.14): many correct matches on its repetitive scenery have non-significant gaps, which inflates π̂₀
(0.47–0.91 vs. 0.27–0.57). We therefore recommend the p-values, not the two-groups confidence, on aliasing-prone maps.

## 6.6 Robustness and ablations

*Map in a hard condition.* Using Nordland **winter** as the map (queries summer/spring/fall) — so that map
pseudo-queries are the degraded ones — SelfCal-AA keeps 0/3 violations (FAR 0.010, aliasing 0.022, TPR 0.593).
*Map size.* Keeping 25% of the RobotCar map (635 × 592 m, 1,739 images, 650 pseudo-queries) gives FAR 0.000 and
TPR 0.994; 50% gives 0.037 and 0.916. *Hyper-parameters.* Cell size (×0.5–2), exclusion radius (×0.4–2), block size
(×0.5–2), δ (×0.6–2) and calibration-set size (497–4,747 pseudo-queries) change TPR by at most 0.05 and keep the worst-condition FAR at or below 0.073 at α = 0.05 (Table 4). *Centring* is essential on Nordland (TPR 0.754 → 0.329 without it) and neutral elsewhere.

# 7. Limitations

The aliasing guard is supported empirically, not by a theorem. The guarantees concern the *off-map* null and assume
deployment off-map queries are no more map-like than the map's own held-out blocks; a deployment area that is a
near-duplicate of a mapped area (e.g. two identical stations) is aliasing in disguise. The map must be large enough to
hold out blocks (we merged the CMU slices into one city map). RobotCar ground truth exists only for the public training
queries (test poses are withheld by the benchmark), so we apply the official thresholds to the top-1 reference pose of
the 1,906 training queries. Strict levels (α ≤ 0.01) cost power on Extended-CMU.
