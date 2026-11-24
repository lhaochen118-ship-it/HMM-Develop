---
title: "Your Map Is Its Own Calibration Set: Label-Free, Shift-Robust Rejection of False Matches in Visual Place Recognition"
author: "Anonymous submission"
---

# Abstract

Visual place recognition (VPR) returns a best match for every query, yet a robot must decide whether to *trust* it:
accepting a match for a place that is not in the map — or one that merely looks like it — corrupts pose graphs and
relocalisation. Existing acceptance rules (similarity thresholds, spatial-uncertainty scores, learned integrity
monitors, conformal calibration) need labelled query–map pairs, and we show that their false-accept guarantees break as
soon as the appearance condition (night, rain, snow, season) differs between calibration and deployment. We observe
that VPR offers labelled negatives for free: **the map itself**. Holding out each spatial block of the map turns every
map image into a query that is off-map *by construction*, and calibrating against these map pseudo-queries yields
split-conformal p-values without any human or deployment labels. To make this calibration transfer across conditions we
use statistics that are invariant to per-query affine changes of the similarity scores, computed against spatially
distant map regions on map-centred descriptors; we combine them with a self-calibrated minimum-p rule, an aliasing
guard, Mondrian strata on the spread of the distant regions, and a lenient raw-similarity gate that keeps the test valid
for queries from foreign cities or datasets. We prove validity under exchangeability, conservativeness whenever
appearance change makes unrelated queries less map-like, an intersection–union bound under domain shift, and FDR
control. On RobotCar-Seasons, Extended-CMU-Seasons, Nordland and MSLS with six descriptors from NetVLAD to MegaLoc
(24 settings, 192 deployment conditions), the method has no condition whose off-map false-accept rate exceeds the
target (worst condition 0.048 at α = 0.05) and accepts a median 1.1% of perceptual-aliasing errors, while
label-calibrated baselines exceed the target in 16–79 conditions — leave-one-condition-out conformal calibration in
every one of the 24 settings — and accept 7–41% of aliasing errors. Queries from other cities and datasets are rejected
(false-accept rate ≤ 0.007 in all 120 map × source pairs). Its average power is 0.646, against 0.706 for an oracle
that holds labels for every deployment condition. A higher-power operating point that tests only the gap statistic
(SelfCal-Gap) reaches 0.746 — above the oracle — still without any significant violation (worst condition 0.073). In a
localisation experiment on a map with holes, SelfCal lowers the mean position error of an odometry + VPR filter
1.3–12.6× relative to a label-calibrated threshold.

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

**Contributions.** (i) We show on four benchmarks that label-calibrated acceptance (threshold, spatial uncertainty,
learned and conformal) loses its false-accept guarantee under appearance shift, and that the classical parametric nulls
(Gaussian z-norm, EVT spacing tests) are invalid or degraded by hubness. (ii) We propose SelfCal: map pseudo-queries via
spatial hold-out as a conformal null sample, affine-invariant far-region statistics on map-centred descriptors, a
self-calibrated combination, an aliasing guard, Mondrian strata and a domain gate. (iii) We give validity,
dominance-based robustness, excess-risk, domain-shift and FDR results. (iv) We evaluate on RobotCar-Seasons,
Extended-CMU-Seasons, Nordland and MSLS with six descriptors and 32 deployment conditions, plus queries from foreign
cities and datasets, with full ablations; code and the descriptor dumps are public.

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

**Mondrian strata.** How informative a given $z_{far}$ or $z_{gap}$ is depends on how spread out the distant
regions are: the same standardised score is common when $\sigma_{far}$ is small and rare when it is large, and
$\sigma_{far}$ varies widely across one map (open roads vs. repetitive façades). Pooling all null items into one
reference distribution therefore forces a single threshold on very different queries. We split the null into $B$
quantile bins of $\sigma_{far}$ and compute all p-values of a query against the null items of its own bin only
(Mondrian conformal prediction [Vovk'05]). $\sigma_{far}$ is computed from the query's own similarities, so no labels
enter. With $n_b$ null items per bin the smallest attainable p-value is $1/(n_b+1)$; we use $B=10$ and reduce $B$
automatically so that every bin keeps at least 50 items (enough for $\alpha\ge0.02$).

**Domain gate.** The scale-normalised statistics can be inflated for queries from a *foreign* domain (another city or
dataset): their similarity profile against the map is flat, so $\sigma_{far}$ shrinks and $z_{far},z_{gap}$ grow
even though $s_{j^*}$ is low. We therefore also require that the raw similarity is not unusually low for the map:
accept iff $\max\{p_{comb},p_{z_{gap}}\}\le\alpha$ **and** $p_{\max s}(q)\le\gamma$, with a lenient
$\gamma=0.8$ (the raw max-similarity must exceed the 20 % quantile of the map null). The gate is inactive for
almost every true match (mean TPR 0.648 → 0.646 over 24 settings) but removes the foreign-domain false accepts (§6.7).

**Two operating points.** SelfCal-AA requires both the combination and the gap to be significant, so it stays valid
when *either* branch is dominated by the map null (intersection–union, as for the gate). Where the far-region level
$z_{far}$ is not dominated (we observe this on MSLS) its branch is still harmless for validity but costs power.
**SelfCal-Gap** uses the gap alone, $p=p_{z_{gap}}$ within the same Mondrian strata and behind the same gate: it is
valid whenever $z_{gap}$ is dominated and has markedly more power (§6.4). We report both and recommend SelfCal-AA when
validity must hold under the weakest assumptions.

**Batches.** With p-values of a deployment batch, Benjamini–Hochberg controls the false-discovery rate, and the
two-groups model (Storey's $\hat\pi_0$, Grenander density estimate) turns $p$ into a calibrated probability of a true
match, $1-\widehat{\mathrm{lfdr}}(p)$ — again without labels.

**Cost.** Offline: one self-retrieval pass over the map with block hold-out — 18 s on 4 CPU cores for the
6,954-image RobotCar map (8,448-d SALAD). Online: the similarity vector (needed for retrieval anyway), its centred
counterpart, cell maxima (one `reduceat`), a bin look-up and four binary searches — about 1 ms per query on CPU in
NumPy when queries are processed in batches, both similarity products included.

# 5. Guarantees

**T1 (validity).** If, for an off-map query, $T(q)$ and the null statistics $\{T^0_i\}$ are exchangeable, then
$P(p_T(q)\le\alpha)\le\alpha$. *Standard split-conformal argument.* With Mondrian strata the same holds
conditionally on the stratum (exchangeability is only needed among queries and null items with similar
$\sigma_{far}$), and hence marginally; T2–T4 below apply within each stratum.

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

**T6 (domain gate: valid if either assumption holds).** For the gated test,
$\mathrm{FAR}_c(\alpha)\le\min\{\alpha+\Delta_c^+,\ \varepsilon_c\}$ with
$\varepsilon_c:=P\big(s^c_{j^*}\ge\hat q_{1-\gamma}(s^0)\big)$, the probability that an off-map query of condition
$c$ reaches the lower $(1-\gamma)$ quantile of the map's own raw max-similarity null. *Proof:* the accept event is the
intersection of the two tests' accept events, so its probability is at most that of either. The first term is
small under **appearance** shift (the invariant statistics are dominated, T2/T3); the second is small under
**domain** shift, where foreign images are visibly less similar to the map than its own unrelated places are. The
test is thus conservative whenever *either* kind of shift explains the change, the intersection–union principle
[Berger'82]. Neither assumption needs labels; $\varepsilon_c$ can be audited with any unlabelled foreign image set.

# 6. Experiments

## 6.1 Setup

**Datasets.** *RobotCar-Seasons v2* [Sattler'18]: the map is the official `overcast-reference` rear-camera traversal
(6,954 images, ~1.3 × 1.1 km) with poses from the official reconstruction (`all.nvm`); queries are the 1,906 rear
images of the public training split in nine conditions (dawn, dusk, night, night-rain, overcast-summer/winter, rain,
snow, sun), whose 6-DoF poses are released (test poses are withheld by the benchmark). A query is correct if the top-1
reference is within the coarsest official threshold (5 m, 10°). *Extended-CMU-Seasons* [Toft'20]: the eleven slices
with released query poses (6–8, 10–13, 21–24) share one world frame and are consecutive segments, so we merge their
official databases into one 2,418-image city map; queries are the 21,407 camera-0 images of 11 dates (Sep 2010 – Jul
2011), correct at (5 m, 10°). *Nordland* [Sünderhauf'13]: 4,500 frame-aligned places per season (uniform subsample of
the 35,768-frame route); summer is the map (winter in §6.6), spring/fall/winter are queries, correct within 2 places.
*MSLS* [Warburg'20], validation cities Copenhagen and San Francisco (panoramas excluded): the two city databases
(12,556 and 6,315 images) form one map and the 11,084 queries are grouped into nine conditions (city × season, plus
Copenhagen night), correct within the standard 25 m.

**Off-map protocol.** We cannot rely on a few hand-picked unmapped streets, so we hold out the map in turn: the map is
partitioned into 300 m blocks (200 places on Nordland); for each block, the block is removed and its queries farther
than 40 m (10 places) from the remaining map are evaluated as *off-map*. This gives 1,386 (RobotCar), 14,117 (CMU),
12,180 (Nordland) and 8,491 (MSLS) off-map query instances spread over all conditions. In-map queries (within 5 m of a
map image; 10 m on MSLS) are evaluated against the full map; in-map queries whose top-1 is farther than 25 m (5 places)
are *aliasing* errors. The method's own null construction uses only the map and never sees queries. We also score
*natural* off-map queries: the queries of every other dataset and city against each map (§6.7).

**Descriptors.** Frozen, off-the-shelf: NetVLAD (VGG16, Pitts30k, 4,096-d) [Arandjelović'16], CosPlace (ResNet-50,
2,048-d) [Berton'22], MixVPR (ResNet-50, 4,096-d) [Ali-bey'23], DINOv2 ViT-B/14 CLS+mean (1,536-d) [Oquab'24], SALAD
(8,448-d) [Izquierdo'24] and MegaLoc (8,448-d) [Berton'25]. All descriptors are extracted once at 322 × 322.

**Baselines.** (a) *Threshold, benign→all*: split-conformal threshold on the max-similarity of off-map queries of the
two most benign conditions (the two with the highest recall; Nordland: fall), applied to all conditions; (b) the same
with aliasing errors added to the negatives; (c) *conformal LOCO*, the SAFEVPR protocol: calibrate on the labelled
off-map queries of all *other* conditions and test on the held-out one; (d) *Quantile Transfer* [Rajani'26]: the benign
threshold mapped through the quantile function of each deployment batch; (e) a learned logistic calibrator on margin,
max-similarity and entropy (CRSG) trained on benign conditions; (f) *SUE* [Zaffar'24], the spatial spread of the
top-10 reference poses (λ = 350), and (g) the PA ratio [Hausler'21], both calibrated benign→all; (h) parametric nulls:
Gaussian z-norm with Bonferroni and the closed-form EVT spacing test; (i) an *oracle* that calibrates max-similarity with
the labels of every deployment condition.

**Metrics.** FAR on off-map queries per condition (target α), the number of conditions whose FAR is significantly above
α (one-sided binomial test, Bonferroni over conditions), the worst-condition FAR, TPR on correct in-map queries, and the
acceptance rate of aliasing errors.

## 6.2 Main result

Table 1 reports α = 0.05 for SALAD. Every label-calibrated method exceeds the target on at least one dataset — the
benign→all threshold in 5/9 RobotCar conditions (worst FAR 0.21 at night-rain) and 4/11 CMU dates; calibrating on all
other labelled conditions (SAFEVPR protocol) still fails in 1/9, 4/11, 2/3 and 2/9 conditions; SUE in 1/9 RobotCar and
2/9 MSLS conditions — and the score-threshold methods accept a third to four fifths of the aliasing errors.
Parametric nulls are either invalid (Gaussian z-norm: FAR 0.13–0.90) or anti-conservative under hubness (EVT spacing:
5/9 MSLS conditions). SelfCal-AA, which uses no labels, has **no significant violation in any of the 32 conditions**,
a worst-condition FAR of 0.048, accepts 3%, 1%, 6% and 12% of aliasing errors, and its TPR (0.978 / 0.865 / 0.742 /
0.528) is close to the oracle that holds labels for every condition on RobotCar, CMU and Nordland (0.995 / 0.992 /
0.780) but not on MSLS (0.820; §7). Fig. 2 shows the same picture for α ∈ [0.005, 0.2].

## 6.3 Why it works

Fig. 1 plots the survival function of the off-map statistic for every RobotCar condition against the map null.
All conditions lie below the null for both max-similarity and z_far: appearance change makes unrelated queries
*less* map-like than the map's own held-out blocks (T2). Table 3 quantifies the excess-risk bound Δ⁺ of T3: with the
map null it is at most 0.052 (max-similarity) and 0.047 (z_far, centred) over the RobotCar, CMU and Nordland
conditions, whereas with a labelled benign null it reaches 0.255 (max-similarity, night-rain) — exactly the violations
of Table 1. The invariant statistic matters for power: calibrating raw max-similarity on the map is valid but loses
power on Nordland (0.41 vs 0.74), where seasonal change lowers all similarities.

## 6.4 Descriptors and datasets

Table 2a aggregates all six descriptors and four datasets (24 settings, 192 deployment conditions) and Table 2 details
each setting. SelfCal-AA has **no significant violation in any of the 192 conditions** and a worst-condition FAR of at
most 0.048 at α = 0.05. The benign threshold violates in 36 conditions (15 of 24 settings), the learned calibrator in
32, SUE in 16 (10 settings), leave-one-condition-out conformal calibration in 51 — at least once in *every* setting —
and Quantile Transfer in 79. Averaged over all settings SelfCal-AA has TPR 0.646 against the oracle's 0.706, with a
median aliasing acceptance of 0.011 (benign threshold 0.218, SUE 0.070). On RobotCar, CMU and Nordland alone the gap to
the oracle is 0.013 (0.708 vs 0.721). For older descriptors (NetVLAD, CosPlace, MixVPR) SelfCal-AA often exceeds the
oracle's TPR on CMU and Nordland, because the oracle thresholds raw max-similarity while SelfCal also exploits the
far-region statistic.

Two cases are conservative. *DINOv2 CLS+mean*, a generic descriptor not trained for VPR, encodes the capture condition
so strongly that map pseudo-queries (which share the map's condition) are much more map-like than any deployment
query: SelfCal stays valid (FAR ≤ 0.001) but its TPR is 0.04–0.38 against the oracle's 0.32–0.70. *MSLS* combines two
cities, many capture dates and front/side views in one map; SelfCal-AA keeps 0/54 violations but reaches TPR 0.460
against the oracle's 0.661 (MegaLoc 0.879 vs 0.965). The label-calibrated baselines obtain their higher MSLS power by
violating 6–15 of the 54 conditions.

**SelfCal-Gap.** Testing the gap alone (§4) keeps 0/192 significant violations and raises the mean TPR from 0.646 to
0.746, above the oracle's 0.706: on MSLS from 0.460 to 0.603 (oracle 0.661) and on RobotCar, CMU and Nordland from
0.708 to 0.793. The price is a thinner margin: the worst single-condition FAR is 0.073 (none significant) instead of
0.048, and the median aliasing acceptance is 0.021 instead of 0.011. Without the gate its TPR is 0.758, but the
foreign-domain leaks return. The far-region level $z_{far}$ is the statistic whose dominance fails on MSLS: alone it
reaches a worst-condition FAR of 0.40–0.88 there. It is therefore not needed for validity where $z_{gap}$ is dominated,
but it protects SelfCal-AA where $z_{gap}$ might not be.

**Components (Table 2a).** Removing the Mondrian strata lowers the mean TPR from 0.646 to 0.612 and raises the
worst-condition FAR from 0.048 to 0.140 (one RobotCar condition; not significant after Bonferroni); removing the domain
gate changes the TPR by +0.002 but re-opens the foreign-domain leaks of §6.7; removing the aliasing guard raises the TPR
to 0.667 but accepts a median 7.2% of aliasing errors and produces 5 significant violations on MSLS, where aliasing
errors and off-map queries share the similarity range.

## 6.5 Batches: FDR and label-free confidence

With an off-map share of 10–50%, Benjamini–Hochberg on SelfCal-AA p-values (q = 0.1) keeps the false-discovery rate of
gross errors at 0.005–0.012 on RobotCar, 0.002–0.006 on CMU and 0.019–0.022 on Nordland (max over conditions 0.040 /
0.016 / 0.028) with power 0.97–0.99, 0.87–0.89 and 0.68–0.74 (Table 5). The two-groups confidence has ECE 0.018–0.023
on RobotCar without labels, but it is poorly calibrated on CMU (≈ 0.09) and Nordland (≈ 0.13): many correct matches
on repetitive scenery have non-significant gaps, which inflates π̂₀ (Nordland 0.47–0.90 vs. 0.27–0.57). We therefore
recommend the p-values, not the two-groups confidence, on aliasing-prone maps.

## 6.6 Robustness and ablations

*Map in a hard condition.* Using Nordland **winter** as the map (queries summer/spring/fall) — so that map
pseudo-queries are the degraded ones — SelfCal-AA keeps 0/3 violations (FAR 0.009, aliasing 0.011, TPR 0.623).
*Map size.* Keeping 25% or 50% of the RobotCar map (1,739 / 3,477 images, 650 / 1,147 pseudo-queries) keeps 0/9
violations (FAR 0.017 / 0.026) with TPR 0.964 / 0.843. *Hyper-parameters.* Cell size (×0.5–2), exclusion radius
(×0.4–2), block size (×0.5–2), δ (×0.6–2) and calibration-set size (497–4,747 pseudo-queries) change TPR by at most 0.06
and keep the worst-condition FAR at or below 0.073 at α = 0.05 (Table 4). *Centring* is essential on Nordland (TPR 0.742
→ 0.568 without it) and neutral elsewhere.

## 6.7 Foreign cities and datasets

A deployed robot may also see places of a different kind than the map — another city, a rural railway instead of
streets. We score 2,000 queries of every other dataset and city against each map with the deployable SelfCal-AA, fitted
on the map alone (6 descriptors × 5 maps × 4 foreign sources = 120 cells). Without the domain gate, the scale-normalised
statistics are inflated for some foreign queries: with CosPlace, 13% of RobotCar and MSLS-Copenhagen queries are
accepted against the CMU map (3 of 120 cells above α, worst 0.143). With the gate, **no cell exceeds α; the largest
false-accept rate is 0.007** (Table 6). The gate costs 0.002 TPR on average, and T6 explains why both kinds of shift
are covered: the invariant statistics are dominated under appearance shift, and foreign images fall below the map's
own raw-similarity quantile under domain shift.

## 6.8 Sequences: more power, but a caveat

Robots observe sequences, so evidence can be pooled over the last $L$ frames. We calibrate a window statistic the
SelfCal way: runs of $L$ consecutive *map* images inside a held-out block are off-map pseudo-sequences. To make the
window p-value exact, the per-frame test is fitted on the map items of even blocks and the pseudo-windows are drawn
from odd blocks (cross-fitting). As statistic we sum $-\log p$ over the trailing run of frames whose consecutive top-1
positions agree within $\rho$. A last frame whose match jumps away keeps only its own evidence, so earlier frames never
vouch for a match they disagree with (a whole-window average does, and fails on Nordland). Table 7 shows large power
gains where single frames are weak: Nordland TPR rises from 0.26 to 0.62 (DINOv2), 0.44 to 0.71 (NetVLAD) and 0.59 to
0.88 (MixVPR) with $L=5$. Validity, however, does **not** carry over everywhere. With MegaLoc on Nordland, 2–3 of the 3
seasons are significantly above α for $L\ge3$ (worst 0.081). The per-frame statistics remain dominated, but the
*temporal dependence* of off-map retrievals depends on the condition: snowy frames keep retrieving the same wrong
place, giving longer consistent runs than the map's own pseudo-sequences. Exchangeability of windows is therefore a
stronger assumption than exchangeability of frames. Averaging e-values would be valid under any dependence but is far
weaker than the per-frame test. We leave dependence-robust sequential calibration to future work and do not include
the window test in our claims.

## 6.9 Downstream: localisation on a map with holes

Finally we measure what false-accept control buys a robot. We remove a random 30% of the 300 m map blocks, so that the
robot regularly drives through unmapped areas, and fit SelfCal on the remaining map only. Every query traversal (CMU:
130 sequences at about 1 m steps; Nordland: 3 seasons) is tracked by a position Kalman filter driven by simulated
odometry with scale bias, heading random walk and noise. Every accepted VPR match becomes a 5 m position fix (Table 8,
mean of 10 seeds). Accepting every top-1 match gives mean errors of 78–114 m on CMU. The label-calibrated threshold
still accepts 370–1,150 wrong fixes per run on CMU and leaves up to 16% of its frames more than 25 m off. SelfCal-AA
accepts 1.5–27× fewer wrong fixes and lowers the mean error in **every** descriptor–dataset pair: by 1.3–2.7× on CMU
(3.6–9.3 m against an oracle at 2.8–3.2 m) and by 3.9–12.6× on Nordland. The window test of §6.8 is on average *worse*
than per-frame SelfCal-AA in this deployment (it accepts more consistent aliasing and map-edge matches), which confirms
that its extra power on held-out windows does not translate into safer localisation.

# 7. Limitations

The aliasing guard is supported empirically, not by a theorem. The guarantees concern the *off-map* null and assume
deployment off-map queries are no more map-like than the map's own held-out blocks (or, for the gate, less similar
than the map's unrelated places); a deployment area that is a near-duplicate of a mapped area (e.g. two identical
stations) is aliasing in disguise. The map must be large enough to hold out blocks and to fill the Mondrian strata: with
$n_b$ pseudo-queries per stratum no p-value is below $1/(n_b+1)$, so strict levels (α ≤ 0.01) need about 100 per
stratum (CMU has 75). Power is the price of label-free validity on heterogeneous maps (MSLS) and for condition-sensitive
descriptors (DINOv2). RobotCar ground truth exists only for the public training queries (test poses are withheld by
the benchmark), so we apply the official thresholds to the top-1 reference pose of the 1,906 training queries.

# 8. Conclusion

A VPR map is more than a retrieval database: with its poses, it is a free, unlimited source of labelled off-map
queries in its own environment. Calibrating affine-invariant, geometry-aware statistics against these pseudo-queries
gives acceptance decisions whose false-accept rate is controlled without labels and survives both the appearance
changes that break label-based calibration and queries from foreign cities and datasets, together with an aliasing
guard, FDR control and calibrated confidence. Natural next steps are dependence-robust sequential evidence (§6.8), maps that change over time, and combining SelfCal with geometric verification scores, which it can calibrate without modification.

# References

- [Ali-bey'23] A. Ali-bey, B. Chaib-draa, P. Giguère. MixVPR: Feature mixing for visual place recognition. WACV 2023.
- [Angelopoulos'21] A. N. Angelopoulos, S. Bates. A gentle introduction to conformal prediction and distribution-free uncertainty quantification. arXiv:2107.07511.
- [Arandjelović'16] R. Arandjelović, P. Gronat, A. Torii, T. Pajdla, J. Sivic. NetVLAD: CNN architecture for weakly supervised place recognition. CVPR 2016.
- [Barber'23] R. F. Barber, E. J. Candès, A. Ramdas, R. J. Tibshirani. Conformal prediction beyond exchangeability. Annals of Statistics 2023.
- [Bates'23] S. Bates, E. Candès, L. Lei, Y. Romano, M. Sesia. Testing for outliers with conformal p-values. Annals of Statistics 2023.
- [Benjamini'95] Y. Benjamini, Y. Hochberg. Controlling the false discovery rate. JRSS-B 1995.
- [Berger'82] R. L. Berger. Multiparameter hypothesis testing and acceptance sampling. *Technometrics* 24(4), 1982.
- [Berton'22] G. Berton, C. Masone, B. Caputo. Rethinking visual geo-localization for large-scale applications (CosPlace). CVPR 2022.
- [Berton'25] G. Berton, C. Masone. MegaLoc: One retrieval to place them all. CVPR Workshops 2025.
- [Cai'22] K. Cai, C. X. Lu, X. Huang. STUN: Self-teaching uncertainty estimation for place recognition. IROS 2022.
- [Carson'22] H. Carson, J. J. Ford, M. Milford. Predicting to improve: Integrity measures for assessing visual localization performance. RA-L 2022.
- [Claxton'24] O. Claxton, C. Malone, H. Carson, J. J. Ford, G. Bolton, I. Shames, M. Milford. Improving visual place recognition based robot navigation by verifying localization estimates. RA-L 2024.
- [Conneau'18] A. Conneau, G. Lample, M. Ranzato, L. Denoyer, H. Jégou. Word translation without parallel data (CSLS). ICLR 2018.
- [Efron'01] B. Efron, R. Tibshirani, J. D. Storey, V. Tusher. Empirical Bayes analysis of a microarray experiment (local fdr). JASA 2001.
- [Hausler'21] S. Hausler, T. Fischer, M. Milford. Unsupervised complementary-aware multi-process fusion for visual place recognition. arXiv:2112.04701.
- [Hussaini'25] S. Hussaini, T. Fischer, M. Milford. Improving visual place recognition with sequence-matching receptiveness prediction. arXiv:2503.06840.
- [Hussaini'26] S. Hussaini, T. Fischer, M. Milford. Automatic map density selection for locally-performant visual place recognition. arXiv:2602.21473.
- [Izquierdo'24] S. Izquierdo, J. Civera. Optimal transport aggregation for visual place recognition (SALAD). CVPR 2024.
- [KappaPlace'26] M. Yanko, Y. Shavit. KappaPlace: Learning hyperspherical uncertainty for visual place recognition via prototype-anchored supervision. arXiv:2605.19435.
- [Lowe'04] D. G. Lowe. Distinctive image features from scale-invariant keypoints. IJCV 2004.
- [Miller'26] E. Miller, M. Milford, M. B. Hafez, S. D. Ramchurn, S. Ehsan. Through the lens of doubt: Robust and efficient uncertainty estimation for visual place recognition. RA-L 2026 (arXiv:2510.13464).
- [Oquab'24] M. Oquab et al. DINOv2: Learning robust visual features without supervision. TMLR 2024.
- [Radovanović'10] M. Radovanović, A. Nanopoulos, M. Ivanović. Hubs in space: Popular nearest neighbors in high-dimensional data. JMLR 2010.
- [Rajani'26] D. M. Rajani, M. Milford, T. Fischer. Quantile transfer for reliable operating point selection in visual place recognition. IROS 2026 (arXiv:2602.04401).
- [RouteMHT'26] Z. Lu, K. Tanaka. Route-MHT: Multimodal transformer guardrails for thermal visual place recognition. arXiv:2607.04745.
- [Sattler'18] T. Sattler et al. Benchmarking 6DOF outdoor visual localization in changing conditions. CVPR 2018.
- [Scheirer'11] W. J. Scheirer, A. Rocha, R. J. Micheals, T. E. Boult. Meta-recognition: The theory and practice of recognition score analysis. TPAMI 2011.
- [Schubert'21] S. Schubert, P. Neubert, P. Protzel. Beyond ANN: Exploiting structural knowledge for efficient place recognition. ICRA 2021.
- [Sier'26] H. Sier, J. Zhang, Z. Zou, X. Yu, T. Westerlund. SAFEVPR: Patch-based conformal verification for safe cross-condition sequence visual place recognition. arXiv:2605.28048.
- [Storey'02] J. D. Storey. A direct approach to false discovery rates. JRSS-B 2002.
- [Sünderhauf'13] N. Sünderhauf, P. Neubert, P. Protzel. Are we there yet? Challenging SeqSLAM on a 3000 km journey across all four seasons. ICRA Workshops 2013.
- [Suzuki'13] I. Suzuki, K. Hara, M. Shimbo, M. Saerens, K. Fukumizu. Centering similarity measures to reduce hubs. EMNLP 2013.
- [Toft'20] C. Toft et al. Long-term visual localization revisited. TPAMI 2020.
- [Trinh'25] N. Trinh, D. Lyons. Adaptive thresholding for visual place recognition using negative Gaussian mixture statistics. arXiv:2512.09071.
- [Vovk'05] V. Vovk, A. Gammerman, G. Shafer. Algorithmic Learning in a Random World. Springer 2005.
- [Vysotska'25] O. Vysotska, I. Bogoslavskyi, M. Hutter, C. Stachniss. Adaptive thresholding for sequence-based place recognition. ICRA 2025.
- [Warburg'20] F. Warburg, S. Hauberg, M. López-Antequera, P. Gargallo, Y. Kuang, J. Civera. Mapillary Street-Level Sequences: A dataset for lifelong place recognition. CVPR 2020.
- [Warburg'21] F. Warburg, M. Jørgensen, J. Civera, S. Hauberg. Bayesian triplet loss: Uncertainty quantification in image retrieval. ICCV 2021.
- [Zaffar'24] M. Zaffar, L. Nan, J. F. P. Kooij. On the estimation of image-matching uncertainty in visual place recognition. CVPR 2024.
- [Zaffar'25] M. Zaffar, L. Nan, S. Scherer, J. F. P. Kooij. The overlooked value of test-time reference sets in visual place recognition. arXiv:2510.03751.
