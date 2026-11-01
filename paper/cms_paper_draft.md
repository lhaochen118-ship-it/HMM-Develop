# Counterfactual Map Surgery: Label-Free, Segment-Level Integrity for HMM Visual Localization

*Draft v0.1 (2026-11-01), branch `hmm-navigation-5`. Every number comes from `RESEARCH_LOG.md` Entries 28–34 and the tables
in `paper/e30_tables.md`, `paper/e32_tables.md`, `paper/e33_tables.md`, `paper/e34_tables.md`. Theory: `paper/cms_theory.md`.
No claim beyond those results; open items are listed in Section 7.*

## Abstract

A robot that localizes against a prior map with visual place recognition (VPR) and odometry must know when it has left the
map: a route deviation, a closed street, a map hole. Off-map, the localizer still finds a "best" place and, if it reports
it, corrupts navigation. Existing integrity tests either need labelled calibration traversals (and break when conditions
shift) or give no guarantee. We show that a localizer can **generate its own null** from the deployment stream.
*Counterfactual map surgery* (CMS) removes a corridor around the system's own belief from the map and recomputes the evidence
exactly as before. On the surgically altered map the current window is off-map by construction, under the same images,
conditions, odometry noise and temporal dependence as the real stream. Ranking the real evidence against hundreds of such
counterfactual segments per session gives (i) a bound on the false-onset rate of reports per off-map segment,
α(n+1)/(πn+1), under any within-segment dependence, with the self-contamination of the null quantified by π. It also
gives (ii) a causal (online) version and (iii) an HMM whose off-map state is calibrated by the counterfactual null. The same
surgery also yields the null of the *track*, which calibrates the exit of a report chain (Entry 34). Across 7 datasets
(Boreas, NCLT, CMU-Seasons, Nordland, three 4Seasons scenes) × 6 descriptors (366 runs), two natural off-map benchmarks
(4Seasons cross-scene; NCLT with each of 9 sessions as the map) and Oxford RobotCar, the rule is valid wherever we
tested. Its recall is higher than every valid label-free baseline on 7/7 datasets and 9/9 NCLT maps. Every label-calibrated
baseline we tried (Xu'21, Claxton'24, TAO'26, SU'25, SUE'24, Carson'23) violates the target rate or loses 40–70 % of the
recall.

## 1. Problem

Map M (places m_j with descriptors and positions), a query stream (image I_t, odometry o_t), a localizer that reports a fix
x̂_t or abstains. A frame is *off-map* if its true position is farther than off_d from every map place. Integrity target:
**segFAR** = fraction of H-frame off-map segments that contain at least one reported fix, required ≤ α (H = 10). The cost is
**recall** (share of on-map frames with a correct fix). No labels at deployment; no calibration traversal.

## 2. Counterfactual map surgery

The system holds a belief: the anchors a_{t,1..N} of its winning route hypothesis over the last N = 20 frames. Surgery removes
B_t = ∪_k B(a_{t,k}, ρ), ρ = off_d. The counterfactual statistic T^cf_t = τ(W_t; M \ B_t) is computed with the exact top-K of the
altered map (top-300 kept per frame, GPU). If the belief is right, every frame of the window is ≈ off_d from the remaining
map. That is an off-map window at the *boundary* of the off-map definition, the hardest case. Statistics: route cost C_t
(TAO'26) and distinctiveness z_t (spatial ratio). Each counterfactual segment is one exchangeable null unit, and a session
gives 190–580 of them.

## 3. Guarantees (assumptions S1 surgery invariance, S2 monotonicity, S3 within-stream segment exchangeability)

- **Theorem 6 (validity under self-contamination).** With κ the conformal (1−α) quantile of segment maxima of T^cf over n
  segments of which a share π are "good" (correct belief): P(∃ t ∈ G₀: T_t > κ) ≤ α(n+1)/(πn+1) for every off-map segment G₀
  deep in an excursion, under any dependence within and between segments. Contamination by wrong beliefs is conservative
  (Proposition 8).
- **Theorem 6′ (finite-memory onset)** and **Theorem 6″ (causal sequential calibration)**: the same bound for the windowed
  presence chain and for thresholds learned online from past counterfactual segments of the session.
- **Proposition 13 (HMM view).** With OFF emission set by the calibrated presence log-LR, the OFF marginal of the joint
  place–presence HMM *is* the calibrated presence chain, so the guarantees are statements about one HMM.
- **Proposition 14 / Corollary 15 (exit, Entry 34).** The counterfactual route MP[j_cf] is false by construction: it is the
  ghost track that a report chain follows after a real exit. A lower conformal quantile of per-segment minimum shape residuals
  of these ghost tracks gives a stop that a real off-map segment passes with probability ≤ a_sh(n+1)/(πn+1), whatever the
  chain state. Every report must pass, so the segment false-fix rate is ≤ a_sh/π with no tolerance constant in the validity
  condition (approximation: the tested track is the HMM MAP track, the null track is the route winner).

## 4. Decision rule

Presence chain over calibrated e-values (Beta-EM transform of counterfactual ranks of C and z), place HMM for the reported
position, shape stop on the MAP track, agreement gate (MAP place within excl of the route winner) and a counterfactual
innovation gate in the navigation filter (+NGRr). Names: CMS-CPC/H+SH+G+NGRr (main), CMS-CPCW/H+SH+NGRr (finite-memory onset),
[online] / [both] (causal calibration).

## 5. Experiments

**Protocol.** 7 datasets × 6 descriptors (MegaLoc, SALAD, MixVPR, CosPlace, NetVLAD, DINOv2), 30 % of map blocks removed, 10
seeds (NCLT: natural off-map, no holes) = 366 runs; Kalman navigation error with each rule's fixes; α = 0.05 (and 0.01).

**Main result (366 runs, default operating points).** Recall / mean segFAR:

| Rule | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| CMS-CPC/H+SH+G+NGRr | 0.775 / 0.003 | 0.612 / 0.002 | 0.822 / 0.009 | 0.765 / 0.000 | 0.800 / 0.000 | 0.703 / 0.006 | 0.491 / 0.001 |
| CPC-SC-T½+SH (best previous label-free) | 0.666 / 0.002 | 0.588 / 0.001 | 0.789 / 0.018 | 0.713 / 0.001 | 0.738 / 0.000 | 0.640 / 0.007 | 0.334 / 0.000 |
| SUE'24, labelled segments (best valid competitor) | 0.248 / 0.041 | 0.208 / 0.036 | 0.268 / 0.044 | 0.391 / 0.037 | 0.281 / 0.039 | 0.221 / 0.040 | 0.086 / 0.039 |
| Xu'21 (HMM off-map state, labels) | 0.684 / 0.043 | 0.526 / 0.021 | 0.686 / 0.227 | 0.740 / 0.038 | 0.724 / 0.215 | 0.625 / 0.101 | 0.254 / 0.088 |
| TAO'26 (labels) | 0.801 / 0.240 | 0.756 / 0.707 | 0.930 / 0.370 | 0.805 / 0.579 | 0.935 / 0.740 | 0.839 / 0.557 | 0.769 / 0.732 |
| Oracle recall | 0.88 | 0.72 | 0.94 | 0.67 | 0.91 | 0.84 | 0.73 |

Navigation error of the main rule is lower than CPC-SC-T½+SH on 7/7 (Entry 30).

**Natural off-map.** (a) 4Seasons cross-scene (map of scene A, queries from scene B; 36 runs): 0/36 runs above α, recall
0.70–0.72 vs 0.59 on 6/6 pairs; label baselines exceed α in 11–28 % of runs. (b) NCLT with each of 9 sessions as the map
(near off-map: neighbouring paths; 48 runs): pooled segFAR 0.007, 0 % of runs above α, recall above CPC-SC-T½+SH on 9/9 maps.

**Robustness.** 12 of 14 decision constants ×0.5–×2 and both surgery parameters (N ∈ {10, 20, 40}, ρ ∈ {0.75, 1, 1.25} off_d)
keep validity on 7/7 and the recall advantage on 7/7. The exception is the shape-stop tolerance, which motivates Proposition
14. Filters F1–F3 (process noise ×4, fix σ 10 m, label-free global init) leave the conclusions unchanged (Entry 30).
Cost: ~20 ms per frame on one CPU core (top-300 on GPU).

**Counterfactual exit calibration (Entry 34).** {{E34PAPER}}

**Oxford RobotCar** (PointNetVLAD split, 43 traversals, reference 2014-12-09). {{OXPAPER}}

## 6. Related work (positioning; `literature/RELATED_WORK_E32.md`)

Integrity VPR (Carson et al. RA-L'22/ICRA'23, Claxton'24, SMR'25, SafeVPR'26) uses labelled calibration or no guarantee.
Off-map states in topometric filters (Xu'21) are hand- or label-tuned. Label-free thresholds (Lee–Pollefeys'14) have no null.
Sequential change detection with e-values (Shin–Ramdas–Rinaldo; Vovk) needs a pre-specified pre/post class or an exchangeable
null from the data; conformal under dependence (Zheng–Proutière'24) needs mixing. Knockoffs build null copies of variables.
CMS instead builds null copies of the *evidence* by an intervention on the map at the system's own belief, and inherits the
stream's dependence exactly.

## 7. Limitations and open items

- S1–S3 are assumptions about how the stream sees the map; they are supported empirically (validity on all tested runs, two
  natural benchmarks), not proved. π is not observable; the bound degrades as 1/π.
- Segments at excursion boundaries (depth < N) are outside the theorems; forward surgery (remove only anchors after a virtual
  exit) is the planned fix.
- Off-map regions are synthetic holes on 5 of 7 datasets (natural on NCLT and the cross-scene benchmark); odometry is
  simulated where the dataset has none (CMU, Nordland, Oxford).
- The counterfactual statistics are a Python loop (10–17 ms per frame); vectorisation is straightforward but not done.
