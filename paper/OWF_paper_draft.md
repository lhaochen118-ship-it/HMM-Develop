# Open-World Filtering for Sequence-Based Visual Localization on Maps with Holes

*Working draft (branch `hmm-2nd-idea`, started 2026-11-05). Sections 1–5 describe the method and theory that are fixed; Sections 6–7 are
filled only from pre-registered experiments (`RESEARCH_LOG.md`). Nothing here claims A\*-level novelty or state-of-the-art performance
beyond what the cited experiments show.*

## Abstract (draft, 2026-11-07, from pre-registered results only; numbers from the twice-audited re-run, Entries 27–28)

A robot localizing against an image map with holes must decide, frame by frame, whether to report a position fix. A false fix while it
is off the map corrupts navigation. We propose an open-world filter: a mass-conserving Bayes filter on a metric grid that covers mapped and
unmapped space, so that leaving the map is predicted by dead reckoning instead of being detected by a test.

We identify the failure that remains in every sequential filter that normalises appearance evidence per frame: a weak look-alike shifted
along a straight road. The odometry cannot see the shift, so the look-alike accumulates evidence without bound. We correct it by giving the
unmapped cells calibrated absolute evidence: the density of the frame's best match when on the map versus the best look-alike when the true
place is absent. Both densities are estimated without labels from the filter's own confident fixes, causally within each session (until a session has its own
samples, from the run's other sessions).

On three groups of fresh hole layouts (8 datasets, 6 global descriptors, 432 runs; decisions pre-registered before each test), the final
system:
- reports correct fixes on 0.93 of on-map frames, above a single-frame oracle (0.85 on the group where it was measured);
- exceeds the false-report target on 3 of 432 runs (0.7 %), and on none with an open-world veto of its learned branch;
- achieves navigation errors 9–13 % lower than our closed-world, hindsight-calibrated baseline (HSI-VNc; 12.6 vs 14.5 m and 14.0 vs 15.4 m).

Three published integrity / off-map methods, tuned with labels, exceed the target on 56–90 % of the same runs (two groups, 288 runs).


## 1. Introduction

A robot with a monocular camera and odometry localizes itself against a geo-referenced image map by sequence matching (HMM filtering over
map places; Sattler et al. 2018 for the evaluation tradition, Hansen & Browning 2014, Xu et al. 2021). Real maps have **holes**: streets that
were never mapped, construction, seasonal occlusion. Each frame the system must decide whether to *report* a position fix to the
navigation filter. A false fix while the robot is off the map corrupts navigation; a missed fix wastes information. No labels are
available at deployment.

Topological HMMs place all probability on map nodes: a robot that drives into a hole has nowhere to go but the remaining nodes, so
"off the map" must be detected by a separate statistical test (off-map states, Xu et al. 2021; calibrated presence tests in our earlier
work). We take the opposite route: **the hole is part of the state space**. The belief lives on a metric grid that covers mapped and
unmapped space; presence on the map is a deterministic function of position; the odometry carries probability mass into, through and out
of holes. Leaving the map is then predicted by dead reckoning against the map's known coverage instead of being detected.

Contributions (each tied to a measured claim in Section 6):
1. The open-world filter (OWF): a mass-conserving metric Bayes filter over mapped and unmapped space with likelihood-ratio emissions whose
   unmapped cells are the natural null (Section 3; Propositions 1–3).
2. Odometry self-calibration as online Bayesian model selection over a bank of (process noise × scale) hypotheses, which handles the
   3–7 % scale error of real visual-inertial odometry without labels (Section 3.4).
3. A diagnosis and a fix for odometry-unobservable aliasing.
   - Diagnosis (Proposition 6): the per-frame normalised emission has a crossover near 0.5 robust SD, so a motion-consistent shifted copy
     of the track accumulates evidence without bound.
   - Fix (Proposition 7, Section 3.3c): label-free, causal, per-session hindsight calibration of absolute evidence for the unmapped
     cells. Confirmed on two fresh groups (Entries 23–24).
   - A hindsight-calibrated conformal decision rule (Proposition 4) was tested and is negative (Entry 16, Section 6.4).
4. An evaluation protocol with pre-registered decisions on fresh hole layouts (8 datasets × 6 descriptors per test group), a
   position audit (sequence starts, hole edges, deep holes), external baselines on the same runs, and a GPU implementation that runs the
   whole bank of filters of a run in one tensor.

## 2. Related work (from `LITERATURE_GATE.md` Gates 17–18; to be completed by a systematic sweep before submission)

*Sequence-based VPR / topological HMMs*: SeqSLAM, Hansen & Browning 2014, Multi-Process Fusion (Hausler et al. 2019), HM4, Guo et al.
2022, Xu et al. RA-L 2021 (one off-map node, no metric position while off the map). *Metric / topometric filters*: Markov and Monte Carlo
localization (Fox, Burgard, Thrun) on complete maps; topometric localization (Badino et al. 2011/2012); sequential Monte Carlo in
topometric appearance maps with loss-of-tracking detection (Jaenal et al. IJRR 2023); CAT-SLAM's new-place hypothesis (Maddern et al.
2012) has no metric position relative to the map. *Integrity monitoring of VPR*: Claxton et al. RA-L 2024, Carson et al. ICRA 2023,
SafeVPR'26, TAO'26 (Lu & Tanaka), VLM auditing (Waheed et al. 2026). *Conformal prediction*: split conformal (Vovk; Lei et al. 2018),
Mondrian conformal, online conformal with delayed feedback. *Self-supervision from geometry*: Lajoie & Beltrame RA-L 2023, TF-VPR.
Differences: (i) the unmapped space is part of the metric state, (ii) presence is a function of position, (iii) decisions are calibrated
on the robot's own hindsight-labelled real excursions rather than on labelled calibration traversals.

## 3. The open-world filter

**3.1 State.** Grid G with cell size g = excl/5 over the map's bounding box grown by a band B (cells farther than B from every map image
removed) plus a position-less far state Ω. A cell is *mapped* when it contains a map image.

**3.2 Motion.** The odometry increment u_t shifts the belief by whole cells (the sub-cell remainder is kept as a phase, so deterministic
motion adds no numerical diffusion); process noise q|u_t| per axis accumulates and is applied as an exact Gaussian blur when it exceeds
(g/2)²; mass that leaves the band moves to Ω; a negligible kidnap rate and an Ω re-entry rate redistribute mass over the prior. Every step
maps a probability vector to a probability vector; **nothing is renormalised over the mapped cells**.

**3.2b No teleport (Proposition 5, Entry 19).** Mass that leaves the band goes to the far state Ω and comes back only through the band edge
(or never). The historical design (Entry 10) returned Ω-mass over the start prior, i.e. onto every map image each frame. Coherent aliasing
then amplifies those seeds: on the Nordland design run, the reports wrong at 1 − 1e-8 drop from 22 to 0 when the channel is removed.
Fresh-seed tests (Entries 19 and 21, seeds 58–63, 288 runs): no change in recall (−0.001) and lower mean segFAR (0.0101 → 0.0091 on 58–60).
Navigation error is lower on 58–60 (16.3 → 15.6 m) but +0.07 m on 61–63. Under the pre-registered rules it did not replace the incumbent:
on 58–60 the absolute run-count target failed for both rules, and on 61–63 the navigation criterion failed by 0.07 m.

**3.3 Emission.** For frame z_t with similarities to the n map images, robust z-scores z_{t,i} within the frame's own profile give
L_{t,i} = exp(β z_{t,i}) / mean_j exp(β z_{t,j}) (mean exactly 1 over the map); a mapped cell gets the mean L of its images, an unmapped
cell and Ω get 1. Evidence is weighted by the distance travelled, w_t = min(1, |u_t| / 0.4 excl), so a stopped robot does not count the
same view repeatedly. Ablation (Entry 10, 26 runs each): without the unmapped cells (closed world, same emission and motion) every run
exceeds the false-report target (segFAR 0.297); without distance weighting every run exceeds it (0.606).

**3.4 Odometry self-calibration.** The filter runs as a bank over q ∈ {0.005, 0.02} excl and odometry scale s ∈ {0.94, 0.97, 1, 1.03, 1.06};
at each frame the member with the largest cumulative log predictive likelihood Σ log p(z_s | z_<s) is followed (causal Bayesian model
selection). Measured scale error of the 4Seasons VIO against GNSS: countryside 1.04, office 1.04, old town 0.94.

**3.5 Decision statistic.** D_t = the largest posterior mass in a disc of radius excl around one of the 12 heaviest mapped cells; the
reported fix is the map image nearest to the posterior mean of that disc.

**3.6 Implementation.** All bank members of a run advance as one float64 tensor on one GPU (whole-cell shifts as gathers, the blur as two
zero-padded 1-D convolutions, emission updates as scatter-adds); odometry-only bookkeeping is precomputed on the CPU. On an NVIDIA L4 the
10-member bank runs at 2.7–3.4 ms/frame (numpy reference on the same machine: 29 ms/frame) with identical decisions at every threshold
(`analysis/owf_torch.py`).

**3.3b What the emission cannot reject (Proposition 6, Entries 21–22).** Relative to the unmapped cells, an image gains mass when its
z-score exceeds A_t/β ≈ 0.5 robust SD. Consider a copy of the true track shifted along a straight road: the odometry cannot see the shift,
so the copy and the true (unmapped) track have equal motion likelihood, and the copy wins whenever its mean z exceeds the crossover. CMU
contains two such copies, found by tracing the runs above α:
- seed 60: 204 m back along slices 11–12;
- seed 61: 673 m away, slice 22 vs slice 24.

Both have a constant offset over 10–17 traversals, and two independent descriptors agree on the copy. Both match weakly (cosine 0.34–0.45
vs 0.69–0.77 at the true place). A Gaussian-shift crossover μ₁/2 removes these false fixes (OWF alone: CMU false segments ÷ 4.6). But
with one crossover per run it costs 3 pp recall and makes Nordland worse, so it was dropped at development (Section 6.4).

**3.3c Hindsight-calibrated absolute evidence for the unmapped cells (Proposition 7, Entry 23).** The observation that separates a true
match from an alias is the frame's best similarity above its own profile level, x_t = max_i s_ti − median_i s_ti:
- on the map, x_t is the maximum over the true place and the best look-alike (density f_on);
- off the map, x_t is the best look-alike with the true place absent (density f_off).

The unmapped cells and Ω receive the log-LR log f_off(x_t) − log f_on(x_t) instead of 0. Both densities are estimated without labels from the
confident fixes of a first, historical pass:
- f_on: the frame's maximum;
- f_off: the best image farther than 1.6 excl from the fix, a look-alike of the same condition, descriptor and map.

Densities are KDEs with 1 % uniform contamination (its support taken from the samples only). Causality within a session is kept because the
first pass does not depend on the second: frame t uses its own session's samples from frames < t once there are 100 of each, otherwise the
run's other sessions; a unit test (`analysis/tests/test_hq_causality.py`) checks that changing a session's future leaves its past log-LR
unchanged. The fallback to other sessions is transductive across the sessions of one deployment (a fleet that has driven the map); a strictly
online variant that uses only earlier sessions (`--lu hsq2s`) is reported in Section 6.1d. Where the true place does not stand out
(night, repetitive stretches), f_on ≈ f_off and the filter reduces to the historical one. Off the map, the on-map hypothesis loses evidence
at rate KL(f_off ‖ f_on).

Fresh pre-registered test (Entry 23, seeds 64–66, 144 runs): it replaced OWF-HWA-S5 by the rule (validity not worse, recall cost ≤ 0.006,
navigation not worse by > 0.5 m):
- mean segFAR 0.0076 → 0.0058, recall −0.0035, navigation 15.15 → 14.88 m (re-run with the twice-audited code, Entries 27–28);
- CMU recall +0.009 with segFAR −30 % and navigation 8.5 → 7.1 m; Nordland navigation 7.5 → 4.1 m;
- with a veto of the hindsight branch where the near-map mass is < ½: 0/144 runs above α.
- on the sets never used for tuning (holes 10/50 %, natural off-map, NCLT), it is more valid everywhere (runs above α 7 → 4, all CMU at
  50 % holes; natural off-map mean segFAR 0.0104 → 0.0025), with recall −0.001 … −0.021 (largest at 50 % holes).

Development set (399 runs, same runs as the incumbent):
- pooled mean segFAR 0.0045 → 0.0034, runs above α 1 → 0, recall −0.004;
- CMU recall +0.011 with segFAR 0.0095 → 0.0066; Nordland segFAR 0.0069 → 0.0026;
- the cost is at the start of sessions whose condition differs from every other session (night), before 100 own samples.

**3.7 The final system (OWF-HWA-S5-NT-HQ) and its constants.** Per deployment (a run of sessions on one map):

1. First pass: the OWF bank (q ∈ {0.005, 0.02} excl × scale ∈ {0.94, …, 1.06}) with the far state absorbing (no teleport) and the
   historical emission.
2. Hindsight samples at its confident fixes (mass ≥ 1 − 10⁻³):
   - frame maximum minus profile median (f_on);
   - best image beyond 1.6 excl (f_off).
3. Second pass: the same bank with unmapped / Ω log-LR log f_off(x_t) − log f_on(x_t).
   - Densities come from the session's own earlier samples (≥ 100), else from the run's other sessions.
   - KDE with 1 % uniform contamination, evaluated in blocks of 50 frames.
4. Decision: the hindsight branch (HSI-VNc, the causal form of HSI-VN, Entry 28) on the OWF-handed chain (mass ≥ 0.9 after 16 excl), OR the OWF reports at:
   - 1 − 10⁻⁵ after 16 excl;
   - 1 − 10⁻⁸ after 2 excl;
   - 1 − 3·10⁻⁴ with three-way agreement after 0.5 excl.
5. Optional safe operating point: the hindsight branch reports only where the OWF near-map mass is ≥ ½.

Every constant is shared by all datasets and descriptors. The tiers come from Entries 12–15; 1.6 excl, 1 %, 100 and 50 from Entry 23. One
command per run: `owf_hsi_job.py <cache> <dump> <ds> <desc> <seed> --modes xms0.9_16:HSI-VNc --hsiframes --qx 0.005,0.02 --scales
0.94,0.97,1.0,1.03,1.06 --engine torch --pin 0 --lu hsq2`, then `owf_union.py ... --hvar HSI-VNc --variants "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"`
(with `OWF_VETO=0.5` for the safe point). Cost: two passes of the 10-member bank, about 6 ms/frame on one L4.

## 4. Theory

Propositions 1–3 and their proofs: `paper/owf_theory.md` §2–4 (no net pull of a diffuse belief; a Ville bound on false reports within an
off-map stretch under the e-value assumption (E1), with no separate edge term; leaving the map is decided by dead reckoning).
Proposition 4 (hindsight-calibrated decision, finite-sample, no (E1)): `paper/owf_theory.md` §6. Why (E1) fails in practice — coherent
perceptual aliasing — is measured in Section 6 (alias episodes).
Proposition 2′ (Ville bound with an inflation budget K, measured): §7. Proposition 5 (no teleport: re-entry seeds are amplified by
coherent aliasing): §8. Proposition 6 (the crossover of the per-frame normalised emission; aliases that the odometry cannot see grow
without bound above it; the Gaussian-shift crossover μ₁/2, with predictions written before its development wave and the measured
outcome): §9. Proposition 7 (hindsight-calibrated absolute evidence for the unmapped cells; drift −KL(f_off ‖ f_on) off the map;
neutral where the condition hides the true place): §10.

## 5. Protocol

Holes: 30 % of 300 m map cells removed (Nordland: 200 frames), fresh hole layouts per test group; 10 % / 50 % hole ratios and natural
off-map (4Seasons cross-scene, NCLT) as generality checks. Metrics: recall (on-map frames with a reported fix within excl), segFAR (share
of H = 10-frame off-map segments with at least one report; target ≤ α = 0.05 per dataset and per run), navigation error of a Kalman
filter fed with the reported fixes, position audit (start / edge / deep). Datasets: Boreas, Extended CMU Seasons, Nordland, 4Seasons
(office loop, old town, countryside), Oxford RobotCar, St Lucia, NCLT; descriptors: CosPlace, NetVLAD, MegaLoc, SALAD, MixVPR, DINOv2.
One configuration for every dataset; no per-dataset tuning.

## 6. Experiments (filled only from pre-registered entries or from sets never used for tuning)

*Rows before seeds 64 (Entries 11–21) used the historical hindsight branch HSI-VN, whose labels looked ahead (Entry 28); they document the
development path and are not re-run.*

**6.1 Pre-registered fresh-seed tests of the full system** (`RESEARCH_LOG.md` Entries 11–15; 144 runs per group, 8 datasets × 6 descriptors,
paired against the previous rule on the same runs). Pooled recall / runs above α / navigation error:

| Group | Rule | Recall | Paired gain | Runs > α | Nav (m) |
|---|---|---|---|---|---|
| 40–42 | OWF-H | 0.885 | +0.074 vs HSI-VN | 1 | 14.46 |
| 43–45 | OWF-HU | 0.896 | +0.018 | 1 | 14.94 |
| 46–48 | OWF-HW-S | 0.902 | +0.024 | 1 | 12.75 |
| 49–51 | OWF-HWA-S | 0.933 | +0.012 | 0 | 13.64 |
| 52–54 | OWF-HWA-S5 | 0.941 | +0.0045 | 1 | 12.67 |
| 55–57 | OWF-HWA-S5 (confirmation, Entry 17) | 0.937 | +0.131 vs HSI-VN | 1 | 12.48 |
| 58–60 | OWF-HWA-S5 (reference of Entry 19) | 0.934 | — | 6 | 16.29 |
| 61–63 | OWF-HWA-S5 (reference of Entry 21) | 0.927 | — | 2 | 12.91 |
| 64–66 | **OWF-HWA-S5-NT-HQ (Entry 23, final rule)** | 0.933 | −0.0035 vs OWF-HWA-S5 (mean segFAR 0.0076 → 0.0058) | 3 | 14.88 (vs 15.15) |
| 64–66 | OWF-HWA-S5-NT-HQ + veto ½ (reported) | 0.924 | −0.0090 vs final rule (mean segFAR 0.0026) | **0** | 15.34 |
| 67–69 | **OWF-HWA-S5-NT-HQ (confirmation, Entry 24)** | 0.928 | +0.133 vs HSI-VNc | **0** | 12.58 |
| 67–69 | OWF-HWA-S5-NT-HQ + veto ½ (safe point, Entry 24) | 0.920 | −0.0071 vs final rule (mean segFAR 0.0007) | **0** | 12.93 |
| 70–72 | **OWF-HWA-S5-NT-HQ (third confirmation, Entry 26)** | 0.926 | +0.117 vs HSI-VNc | **0** | 14.01 |
| 70–72 | OWF-HWA-S5-NT-HQ + veto ½ (safe point) | 0.919 | −0.0075 vs final rule (mean segFAR 0.0013) | **0** | 14.62 |

Over the three fresh groups that confirm the final rule (55–63, 432 runs), it reached pooled recall 0.927–0.937 with pooled mean segFAR
0.0063. 9/432 runs (2.1 %) exceed α; 7 of the 9 are CMU, from two hole layouts (seed 60, seed 61) that each cover an odometry-unobservable
alias (Section 3.3b). The project target "≤ 2 % of runs above α" holds on 2 of the 3 groups.

Rows 64–72 are the re-run with the twice-audited implementation (`--lu hsq2`, Entry 27; causal hindsight branch HSI-VNc, Entry 28), and
the comparisons use the old rule and the standalone hindsight branch with the same causal branch. Every pre-registered decision is
unchanged. Over the three groups: 3/432 runs above α, all CMU seed 64–66; 0/432 with the veto.

**6.1d Strictly online calibration** (Entries 27–28, same 432 runs, causal hindsight branch). The fallback before a session has 100 own samples uses the run's other
sessions (a fleet that has driven the map). With the fallback restricted to earlier sessions (`--lu hsq2s`):

| Group | Final rule (hsq2): recall / worst-dataset mean segFAR / runs > α | Strict (hsq2s) | Strict + veto ½ |
|---|---|---|---|
| 64–66 | 0.933 / 0.026 / 3 | 0.932 / 0.036 / 5 | 0.923 / 0.028 / 4 |
| 67–69 | 0.928 / 0.010 / 0 | 0.927 / 0.010 / 0 | 0.920 / 0.003 / 0 |
| 70–72 | 0.926 / 0.009 / 0 | 0.926 / 0.012 / 0 | 0.919 / 0.007 / 0 |

The strict variant matches on 67–72 but loses the CMU validity gain on 64–66 (CMU mean segFAR 0.036, as the old rule's 0.036; final rule 0.026): part of HQ's benefit
on CMU comes from calibrating on the same environment's other sessions. We report this as a deployment assumption.

**6.1c External baselines on the fresh group 67–69 for the final rule** (Entry 24, pre-registered, 144 runs, same runs for every rule).
Cell = pooled recall / worst-dataset mean segFAR / runs above α / navigation error (m):

| Ours (OWF-HWA-S5-NT-HQ) | + veto (safe point) | HSI-VNc | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|---|
| **0.928** / 0.010 / **0** / 12.6 | 0.920 / 0.003 / **0** / 12.9 | 0.795 (HSI-VNc) / – / 0 / 14.5 | 0.834 / 0.992 / 130 / 109.5 | 0.692 / 0.584 / 81 / 51.0 | 0.738 / 0.283 / 104 / 44.3 | 0.847 / 0 / 0 / 10.6 |

**6.1b External baselines on the fresh group 55–57** (Entry 17, pre-registered, 144 runs, the same runs for every rule). Cell = pooled
recall / worst-dataset mean segFAR / runs above α / navigation error (m):

| Ours | HSI-VN | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|
| **0.937** / 0.013 / 1 / 12.5 | 0.806 / 0.008 / 0 / 15.0 | 0.846 / 0.996 / 129 / 123.5 | 0.691 / 0.600 / 75 / 57.5 | 0.732 / 0.268 / 99 / 48.4 | 0.847 / 0 / 0 / 10.9 |

**6.2 Generality and external baselines on sets never used for tuning** (`analysis/results/owf/s1105/sota_*.md`; same runs for every rule).
Cell = pooled recall / mean segFAR / runs above α. TAO'26, Xu'21 and Claxton'24 use thresholds tuned WITH labels on the two easiest
conditions, as in their papers; oracle = report exactly the correct top-1 retrievals.

| Set | Ours (OWF-HWA-S5) | HSI-VN | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|---|
| holes 10 % (108) | **0.933** / 0.002 / 1 | 0.772 / 0.000 / 0 | 0.843 / 0.554 / 92 | 0.646 / 0.077 / 35 | 0.737 / 0.288 / 86 | 0.827 |
| holes 50 % (108) | **0.894** / 0.009 / 4 | 0.754 / 0.006 / 4 | 0.842 / 0.535 / 93 | 0.609 / 0.129 / 30 | 0.678 / 0.090 / 60 | 0.829 |
| natural off-map, 4Seasons cross-scene (36) | **0.952** / 0.010 / 2 | 0.742 / 0.004 / 0 | 0.578 / 0.075 / 4 | 0.581 / 0.037 / 10 | 0.678 / 0.020 / 5 | 0.822 |
| NCLT (6) | **0.781** / 0.005 / 0 | — | 0.756 / 0.713 / 6 | 0.526 / 0.021 / 1 | 0.663 / 0.213 / 5 | 0.724 |

Ours is the only rule that is valid and has high recall. It exceeds the single-frame oracle by 0.06–0.13 because sequence evidence recovers
frames whose top-1 retrieval is wrong. Its runs above α (CMU at 50 % holes, two natural runs) coincide with its HSI branch.

**6.2a The final rule on the same generality sets** (Entry 23 generality wave, re-run with the twice-audited code in Entries 27–28, every rule with the causal hindsight branch; external baselines from 6.2 on the same runs). Cell = pooled
recall / worst-dataset mean segFAR / runs above α:

| Set | Ours (OWF-HWA-S5-NT-HQ) | OWF-HWA-S5 | HSI-VNc | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|---|---|
| holes 10 % (108) | **0.932 / 0.004 / 0** | 0.933 / 0.008 / 1 | 0.777 / 0.003 / 0 | 0.843 / 0.775 / 92 | 0.646 / 0.145 / 35 | 0.737 / 0.517 / 86 | 0.827 |
| holes 50 % (108) | **0.872 / 0.028 / 4** | 0.894 / 0.030 / 4 | 0.751 / 0.027 / 4 | 0.842 / 0.754 / 93 | 0.609 / 0.381 / 30 | 0.678 / 0.133 / 60 | 0.829 |
| natural off-map (36) | **0.945 / 0.004 / 0** | 0.954 / 0.012 / 1 | 0.756 / 0.011 / 0 | 0.578 / 0.075 / 4 | 0.581 / 0.037 / 10 | 0.678 / 0.020 / 5 | 0.822 |
| NCLT (6) | **0.769 / 0.001 / 0** | 0.780 / 0.003 / 0 | — | 0.756 / 0.713 / 6 | 0.526 / 0.021 / 1 | 0.663 / 0.213 / 5 | 0.724 |

cell = pooled recall / worst-dataset mean segFAR / runs > alpha

The final rule is valid on average everywhere and is the most valid rule on every set except the standalone hindsight branch at 10 % holes
(0.003 vs 0.004, at recall 0.777 vs 0.932). Its runs above α fall from 6 to 4, all of them CMU at 50 % holes, where every label-free rule has
4. Recall is −0.001 … −0.022 below the previous rule; the largest drop is at 50 % holes.

**6.2b VPR-Space (planetary / lunar / volcanic; descriptive, Entry 18).** 16 db → query setups × 6 descriptors, natural off-map, the
protocol scaled by each setup's own ground-truth tolerance τ:
- ours 0.292 (0 runs > α), single-frame oracle 0.562, TAO'26 0.629 (24 runs > α);
- label-tuned Xu'21 / Claxton'24: 0.498 / 0.441.

The OWF estimator transfers: its map estimate is right on 0.70–1.00 of on-map frames, far above single-frame retrieval. The decision layer
does not:
- the hindsight branch never warms up on 54–1683-frame deployments;
- the tiers need 2–16 excl of path;
- OWF alone makes no false report at any ε on these scenes (pooled recall 0.733 at ε = 0.2), i.e. K ≈ 0 here versus 10³–10⁴ on CMU and
  Nordland.

With the final rule (absolute evidence, Section 3.3c) VPR-Space is unchanged: 0.281, 0 runs above α. Each setup has a single short
query session, so there is nothing to calibrate from, and the absolute evidence falls back to neutral by design.

A threshold fixed across environments cannot fit both regimes. This is the main limitation and motivates bounding K per map before
deployment.

**6.2c Ablation of the final rule** (development set A, 399 runs, the same runs). Cell = recall / mean segFAR / runs above α / navigation
error (m):

| | S5 (previous rule) | + no teleport | + absolute evidence (HQ) | + both (final) |
|---|---|---|---|---|
| pooled | 0.933 / 0.0045 / 1 / 12.7 | 0.932 / 0.0040 / 2 / 12.4 | 0.930 / 0.0034 / 0 / 12.9 | 0.929 / 0.0034 / 0 / 13.0 |
| CMU | 0.852 / 0.0095 / 1 / 4.4 | 0.852 / 0.0096 / 2 / 4.4 | 0.862 / 0.0066 / 0 / 3.8 | 0.863 / 0.0066 / 0 / 3.8 |
| Nordland | 0.968 / 0.0069 / 0 / 6.2 | 0.967 / 0.0053 / 0 / 5.0 | 0.972 / 0.0028 / 0 / 4.9 | 0.970 / 0.0026 / 0 / 4.7 |

The calibrated absolute evidence carries almost all of the validity gain. No teleport adds little once it is present.

**6.3 Why fixed extreme thresholds (Proposition 2′).** The measured inflation of the e-value assumption, K̂(ε) = segFAR(ε)/(2ε), is ≤ 1 on
4Seasons and St Lucia, i.e. Proposition 2 holds as stated. On CMU and Nordland it grows from about 10 at ε = 1e-3 to about 10⁴ at ε = 1e-8,
because coherent aliasing is heavy-tailed (`owf_theory.md` §7).

**6.4 Negative results (development set, 399 runs; each dropped before any fresh test).**
- Hindsight-calibrated thresholds (Proposition 4): recall −0.017 … −0.027, 23–46 runs > α vs 1.
- Wider odometry-scale bank (±15 %, 22 filters): −0.0037.
- Emission temperature selected by evidence: log-evidence +3300 but segFAR ×1.7 and navigation error ×3 on Nordland.
- Simplified tiers: recall ±0.005, with more runs above α.
- Continuous (posterior-mean) fixes: no navigation gain; fix errors are already 2.3–2.5 m.
- Evidence length from the map's visual decorrelation length L_vis (Entry 20): recall −0.029, 13 runs > α. Map–map correlation (same
  condition) does not measure query–map evidence correlation.
- The open-world filter vetoes the hindsight branch where its near-map mass is < ½ (Entry 21, pre-registered, seeds 61–63):
  - mean segFAR 0.0043 → 0.0033, recall −0.005;
  - navigation +0.9 m (countryside, where odometry drift spreads the belief and the veto removes correct fixes). Not adopted.
- Gaussian-shift crossover μ₁/2 for the unmapped cells (Entry 22): CMU false fixes ÷ 4.6, but recall −0.030 and Nordland worse. A veto by
  that filter only (robust decision over the two emission models) is the most valid rule measured on the development set (mean segFAR
  0.0012–0.0018), but recall is −0.026 … −0.045.

**6.5 Compute.** The 10-member OWF bank runs at 2.7–3.4 ms/frame on one NVIDIA L4 (numpy: 29 ms/frame). A full evaluation of the system on
657 runs takes 35 min on six 4×L4 sessions.

## 7. Limitations

- The decision layer of the full system is a union of a hindsight-calibrated learned branch and fixed extreme-confidence tiers. Its
  validity is established empirically across fresh hole layouts, hole ratios 10–50 % and natural off-map, not by a per-run theorem;
  Proposition 2′ explains it, but the inflation budget K is measured, not bounded a priori.
- CMU (short sequences) keeps a recall gap of about 0.12 at sequence starts, although the OWF estimate is already right on 0.95–0.99 of
  those frames.
- The holes are simulated (except NCLT, 4Seasons cross-scene and VPR-Space). On short planetary deployments (VPR-Space) the fixed decision
  layer is far too conservative (0.29 vs single-frame oracle 0.56) although the estimator is right on ≥ 0.93 of frames in most setups.
- Odometry-unobservable aliases (a weak look-alike shifted along a straight road) defeat every sequential filter that normalises
  similarities per frame (Proposition 6). They are the source of 7 of the 9 runs above α over the 432 fresh runs. Rejecting them needs an
  emission calibrated in absolute similarity per condition, which is open.
- Global descriptors only (no 6-DoF refinement).
