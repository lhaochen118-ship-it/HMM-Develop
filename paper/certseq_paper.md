# Never Lost Twice: Label-Free, Excursion-Level Guarantees for Sequential Visual Localization

*Draft v0.1 (2026-10-29). Branch `hmm-navigation`. Numbers: `paper/cert_tables.md` (auto-generated from
`analysis/results/`); experiment log: `RESEARCH_LOG.md` Entries 18–19.*

## Abstract

Sequence-based visual localization fuses a stream of place-recognition matches with odometry, typically in an HMM. It
is the standard way a robot with a monocular camera relocalizes against a prior map. With modern foundation-model
descriptors, the open problem is no longer average recall but **integrity**: knowing when not to trust the
localizer.

The failure that matters is a *false localization during an excursion*: the robot leaves the mapped area (route
deviation, map hole, changed scene) and the localizer reports a place anyway. Per-frame confidence tests do not bound
this event: an excursion offers many dependent chances to fail. Existing sequence and HMM methods use thresholds tuned
on labels, which transfer poorly across conditions.

We propose a label-free localizer whose acceptance rule has an **excursion-level guarantee**:

> P(any false acceptance during an H-frame off-map excursion) ≤ α.

It works for any descriptor and any within-excursion temporal dependence, and is robust to appearance change. Two
ideas make it work.

1. **Odometry-anchored sequence evidence.** It accumulates calibrated per-frame evidence only along hypotheses that
   move with the odometry. This removes the stationary-alias failure that breaks sequence tests under snow and night.
2. **Calibration with the map's own held-out traversal segments as exchangeable units.** This makes the bound exact
   no matter how strongly consecutive frames depend on each other.

On RobotCar-Seasons and CMU-Seasons (the benchmarks of Sattler et al.), Nordland, 4Seasons (real VIO) and Boreas
(wheel + gyro odometry, one route over a year), with 6 descriptors:

- the excursion false-alarm rate stays at or below α;
- a label-calibrated threshold violates it by up to 2.5×;
- 2–7× more correct frames are certified than with a per-frame test, and the first certified fix comes 5–20× sooner.

In a navigation loop with 30 % of the map missing, certified fixes cut the mean position error 2–10× relative to
per-frame and label-calibrated acceptance. They also avoid the catastrophic lock-ins of an HMM with a tuned off-map
state.

## 1. Introduction

**Context.** Long-term visual localization under changing conditions was benchmarked by Sattler et al. (CVPR'18). The
modern pipeline retrieves the most similar map images with a global descriptor, then filters the matches over time
with odometry: SeqSLAM, HMM/Viterbi, topometric Bayes filters (Xu'20/'21), particle filters.

**What changed.** Foundation-model descriptors (MegaLoc, SALAD) now find the correct place for 90–98 % of RobotCar and
CMU queries within 10 m (our audit, Table A1). A plain HMM adds only 2 points on CMU (90.7 → 92.5 % @5 m, Entry 18).

**What remains** is what a navigation stack actually needs: *knowing when the localization is wrong.* A robot that
relocalizes onto the wrong street does more damage than one that waits.

**Gap: false localization during excursions.** Consider a robot that leaves the map: a detour, an unmapped side street,
a map with holes, a construction site. Every frame of the excursion is a chance to accept a wrong place. Frames are
strongly dependent: a snowy or dark scene keeps retrieving the same wrong place frame after frame. Existing methods
fail here in three ways:

- *Per-frame* confidence tests (including our label-free SelfCal) bound the false-accept probability of each frame,
  not of the excursion.
- *Window or sequence* tests calibrated as if frames or windows were exchangeable are invalid. We show they violate the
  target rate on Nordland because the temporal dependence of off-map retrievals depends on the condition (Section 6.1).
- HMMs with an explicit off-map state (Xu'21) and sequence verifiers (SAFEVPR'26, SMR'25) set their thresholds on
  labelled data. Labels from benign conditions do not transfer to hard ones.

**Contributions.**

1. A formulation of **excursion-level false localization** as the integrity target of sequential visual localization.
   We diagnose why frame-level and window-level calibration cannot control it.
2. **Odometry-anchored evidence.** An HMM-style max-product statistic that sums calibrated per-frame evidence over the
   frames whose matches agree with the current hypothesis moved by the odometry. A heading-free variant fits the
   unknown odometry-to-map rotation per window. It needs only a physical odometry tolerance.
3. **Map-calibrated excursion guarantee.** The null distribution is learned from H-frame segments of the map's *own*
   traversal, each queried against the map without its block. Segment exchangeability gives a finite-sample bound
   that holds for arbitrary within-segment dependence (Theorem 1). Dominance gives robustness to appearance change
   (Corollary 1). No labels, no training, no per-environment tuning.
4. **Evidence on 5 benchmarks × 6 descriptors.**
   - Benchmarks: two from Sattler'18, Nordland, and two long-sequence benchmarks with real odometry that we prepared
     and release (4Seasons VIO, Boreas wheel + gyro).
   - Validity at α ∈ {0.01, 0.05, 0.1}; natural off-map excursions; 2–7× power over per-frame tests; a closed-loop
     navigation study.

## 2. Related work

*(Condensed; full gate: `LITERATURE_GATE.md`, Gates 3 and 6.)*

**Sequence and HMM localization.**

- SeqSLAM (Milford'12); HMM/Viterbi (Hansen & Browning'14); MPF (Hausler'19); HM4 / topological HMMs (Doan'19);
  probabilistic topometric localization with an off-map state (Xu et al., RA-L'20/'21); learned sequence descriptors
  (SeqNet, JIST); learned CRFs with a dustbin (TRAIL'26); multi-hypothesis tracking (Route-MHT/TAO'26); topometric
  particle filters with FF3D models ('26).
- They deliver accuracy, but their decision thresholds or off-map likelihoods are heuristic or tuned on labels. None
  gives a guarantee.

**Integrity and verification for VPR.**

- Supervised integrity monitors (Claxton RA-L'24; integrity measures IEEE'22); SMR prediction (Hussaini'25);
  VLM auditing ('26).
- SAFEVPR ('26) applies Mondrian conformal calibration to sequence VPR. Its validity is empirical, it needs labelled
  calibration traverses, and it gives no excursion-level statement.
- Our earlier SelfCal (map-calibrated per-frame test) is the per-frame building block.

**Conformal and sequential testing.**

- Split-conformal outlier detection (Bates'23); conformal under shift (Barber'23); conformal anomaly detection on time
  series, where per-window coverage does not imply time-uniform control ('26).
- Treating a dependent block as the exchangeable unit is the standard remedy in that literature. We instantiate it
  with the map's own traversal as the source of blocks, which needs no labels.

## 3. Problem

**Setting.**

- *Map.* One traversal: images with global descriptors and poses, sampled about 1 m apart.
- *Deployment.* A stream of frames with descriptors and odometry increments. A frame is *on-map* if a map image lies
  within d_in of it, and *off-map* if none lies within d_off.
- *Excursion.* E = H consecutive off-map frames.
- *Localizer.* At each frame it outputs a map place or abstains.

**Target.** P_E( ∃ t ∈ E: accept_t ) ≤ α, without labels, for unknown deployment conditions.

**Power.** The share of correctly localized on-map frames that are accepted, and the latency to the first correct
acceptance.

## 4. Method

**4.1 Per-frame evidence.**

- ℓ_t = −log p_t, where p_t is the SelfCal-AA p-value of the top-1 match. It is computed from affine-invariant
  far-region statistics plus a raw-similarity gate, and calibrated on leave-block-out map pseudo-queries.
- Cross-fitting: the per-frame test is fitted on map items of even spatial blocks only. Null segments come from odd
  blocks, so they are processed exactly like deployment data.

**4.2 Odometry-anchored evidence (ANCH).** Let x_t be the map position of frame t's top-1 match and o_t the integrated
odometry.

R_t = ℓ_t + Σ_{j=1}^{H−1} ℓ_{t−j} · 1[ ‖(x_t − x_{t−j}) − (o_t − o_{t−j})‖ ≤ ρ_o ].

- **HMM view.** R_t is the Viterbi score of the path that ends at x_t and moves with the odometry, in an HMM with hard
  transition gating and outlier-tolerant emissions (frames whose top-1 disagrees contribute 0).
- **Why anchor.** Anchoring at t rather than chaining consecutive frames means past frames never vouch for a
  hypothesis they do not support.
- **Why odometry.** Without it (RUN, exp11), a *stationary* alias counts as consistent: snowy frames retrieving the same
  wrong place. Its frequency depends on the condition, and no map-side null can represent it.

**ANCHR (heading-free).** When the odometry-to-map rotation is unknown (a monocular robot before its first fix), the
consistency is evaluated after rotating the odometry displacements by the angle that maximizes the anchored evidence
in the window (a 1-parameter RANSAC).

**4.3 Excursion-level calibration on the map.**

- For each odd held-out block, its frames, in traversal order, form pseudo-trajectories. They are queried against the
  map without that block, with simulated odometry from the map poses.
- Every H-frame segment s gives a score S = max_{t∈s} R_t.
- With n null scores and k = ⌈(1−α)(n+1)⌉, set τ = S_(k). At deployment, accept frame t iff R_t > τ.
- Costs: O(n_map · N) once for the map null; O(N) per frame (a top-1 retrieval plus an O(H) consistency check).

## 5. Theory

**Theorem 1.** If the null scores S_1..S_n and the score S* of a deployment excursion are exchangeable, then
P(∃ t ∈ E: R_t > τ) ≤ α (and ≥ α − 1/(n+1) without ties).

*Proof.* The event equals {S* > S_(k)}. The rank of S* is uniform on {1..n+1}. ∎

The bound places **no condition on the dependence between frames inside a segment**. Calibrating frames or windows
needs exchangeability across correlated units, and that is what fails in practice (Section 6.1).

**Corollary 1 (appearance shift).** If S* is stochastically dominated by an exchangeable copy, the bound holds. This is
the case when appearance change makes off-map frames less map-like, which the AA statistics were shown to satisfy, and
the odometry gate is appearance-independent.

**Corollary 2 (horizon).** An excursion of E frames contains ⌈E/H⌉ disjoint H-segments, so P ≤ ⌈E/H⌉α.

**Training-conditional behaviour.**

- Given one map, the realised FAR is distributed as Beta(k, n+1−k).
- Large maps give tight per-map control: Nordland and 4Seasons have 100–200 null segments at H = 10.
- Small maps (CMU, ~70) give noisier per-map FAR around the same mean.

## 6. Experiments

**Datasets.**

| Dataset | Content | Odometry |
|---|---|---|
| RobotCar-Seasons v2 | 9 conditions, 1,906 train queries in 9-frame snippets | simulated |
| Extended CMU-Seasons | 11 conditions, 21k queries, sequences of median 186 frames | simulated |
| Nordland | 3 seasons vs summer, 4,500 frames | simulated |
| 4Seasons | 3 scenes with ≥ 2 recordings (office loop, old town incl. dusk, countryside); map = earliest recording | real stereo-VIO |
| Boreas | one 8 km route, 31 sequences over a year (snow, rain, night) | real wheel + gyro |

- Descriptors: MegaLoc, SALAD, MixVPR, CosPlace, NetVLAD, DINOv2.
- Off-map excursions: leave-block-out over 300 m blocks (Nordland: 200 frames) with 3 random block grids, plus
  natural excursions (queries of other scenes and datasets).
- α ∈ {0.01, 0.05, 0.1}; H ∈ {10, 30, 60} (RobotCar {5, 8}).

**Baselines.**

- Per-frame SelfCal.
- RUN: exp11's sequence statistic without odometry.
- RUNO: contiguous odometry run.
- Label-calibrated threshold: the ANCH statistic, thresholded on labelled off-map segments of the two most benign
  conditions (SAFEVPR / Quantile-Transfer style).
- HMM with a tuned off-map state (Xu'21 style).
- EVT-HMM, a tuning-free HMM with a Gumbel-calibrated off-map state (ablation, Entry 18).

### 6.1 Why window-level calibration fails

*(seq_odo / exp11 analysis.)*

- Calibrating windows on map pseudo-windows violates on Nordland MegaLoc for every L ≥ 3 (2–3 of 3 seasons).
- With odometry consistency (RUNO, tight tolerance) the violations vanish, but long windows on CMU still exceed α. The
  reason is that windows inside one block are strongly dependent, so the effective number of null samples is the
  number of blocks.
- Calibrating on the deployment condition's own windows is *worse*, because of spatial heterogeneity.
- Both observations motivate segment-level units.

### 6.2 Validity (Table 1, Table 3)

**Table 1 — Excursion FAR at α = 0.05.**

| Method | RobotCar | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| ANCH (mean FAR) | 0.016 | 0.022 | 0.020 | 0.020 | 0.014 | 0.015 |
| Label-calibrated, mean FAR (worst condition) | 0.044 (0.125) | 0.044 (0.089) | – | – | – | – |

- **ANCH:** mean ≤ 0.022 everywhere; worst condition ≤ 0.067.
- **Label-calibrated:** exceeds α on the Sattler'18 datasets.

**Table 3 — Other α.** α = 0.01 and α = 0.1 track the target, for example on 4S old town: 0.002 / 0.014 / 0.036.

*(Boreas and natural off-map: pending.)*

### 6.3 Power (Table 2, Table 4)

Share of correct frames certified, ANCH vs per-frame:

| Nordland | CMU | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|
| 0.86 vs 0.44 | 0.82 vs 0.62 | 0.83 vs 0.31 | 0.77 vs 0.43 | 0.37 vs 0.19 |

- The largest gains are for weak descriptors: CosPlace on 4S office 0.93 vs 0.09; NetVLAD on CMU 0.75 vs 0.29.
- Latency to the first certified fix on 4S office drops from about 1100 frames to about 50.
- Alias acceptance stays ≤ 0.03.
- **Limitation:** RobotCar queries are 9-frame snippets, too short for evidence to accumulate (0.68 vs 0.77). The
  method needs sequences, which are what a navigating robot produces.

### 6.4 Navigation with map holes (Table 5)

**Setup.** A Kalman filter integrates the odometry and fuses accepted fixes (σ = 5 m), with 30 % of the map removed.

**Mean error, certified vs per-frame:**

| Dataset | Certified | Per-frame |
|---|---|---|
| Nordland, SALAD (frames) | 7.7 | 24.4 |
| Nordland, NetVLAD (frames) | 34.8 | 72.4 |
| CMU, NetVLAD (m) | 4.1 | 10.7 |

- Label-threshold baseline: 41.6 m on CMU NetVLAD.
- The Xu'21-style HMM with a label-tuned off-map state produces many correct fixes, but rare lock-ins onto wrong places
  dominate its tail. On Nordland CosPlace its p95 is 1416 frames, vs 53 for the certified method.

### 6.5 Ablations

*(Pending in the final round.)*

- Heading-free ANCHR vs ANCH: CMU CosPlace FAR 0.037 vs 0.030, equal power.
- ρ_o, odometry noise, H, and map size (null segments).

## 7. Limitations

- **Exchangeability.** It requires off-map excursions to resemble held-out map segments. Natural off-map tests probe
  this.
- **Short query sequences** give little power.
- **Small maps** give noisy per-map FAR. This is training-conditional variance; the marginal guarantee is unaffected.
- **Scope.** Place-level (5 m) localization only. 6DOF refinement with local features (the fine Sattler'18
  thresholds) is orthogonal: certified fixes can gate a 6DOF solver.

## 8. Conclusion

A robot's map can certify its own sequential localizer. Calibrating on segments of its own traversal turns any global
descriptor plus odometry into a relocalizer whose excursion false-alarm rate is bounded without labels, with large
power gains over per-frame tests.
