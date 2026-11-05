# Open-World Filtering for Sequence-Based Visual Localization on Maps with Holes

*Working draft (branch `hmm-2nd-idea`, started 2026-11-05). Sections 1–5 describe the method and theory that are fixed; Sections 6–7 are
filled only from pre-registered experiments (`RESEARCH_LOG.md`). Nothing here claims A\*-level novelty or state-of-the-art performance
beyond what the cited experiments show.*

## Abstract (placeholder — to be written from the final results)

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
3. A hindsight-calibrated decision rule: the filter's own posterior confidence is thresholded per evidence stratum by split-conformal
   calibration on the deployment's own hindsight-labelled excursions, giving a finite-sample false-report guarantee that does not require
   the emission model to be correct under perceptual aliasing (Section 4, Proposition 4) — *pending Entry 16*.
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

## 4. Theory

Propositions 1–3 and their proofs: `paper/owf_theory.md` §2–4 (no net pull of a diffuse belief; a Ville bound on false reports within an
off-map stretch under the e-value assumption (E1), with no separate edge term; leaving the map is decided by dead reckoning).
Proposition 4 (hindsight-calibrated decision, finite-sample, no (E1)): `paper/owf_theory.md` §6. Why (E1) fails in practice — coherent
perceptual aliasing — is measured in Section 6 (alias episodes).

## 5. Protocol

Holes: 30 % of 300 m map cells removed (Nordland: 200 frames), fresh hole layouts per test group; 10 % / 50 % hole ratios and natural
off-map (4Seasons cross-scene, NCLT) as generality checks. Metrics: recall (on-map frames with a reported fix within excl), segFAR (share
of H = 10-frame off-map segments with at least one report; target ≤ α = 0.05 per dataset and per run), navigation error of a Kalman
filter fed with the reported fixes, position audit (start / edge / deep). Datasets: Boreas, Extended CMU Seasons, Nordland, 4Seasons
(office loop, old town, countryside), Oxford RobotCar, St Lucia, NCLT; descriptors: CosPlace, NetVLAD, MegaLoc, SALAD, MixVPR, DINOv2.
One configuration for every dataset; no per-dataset tuning.

## 6. Experiments (filled only from pre-registered entries or from sets never used for tuning)

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

A threshold fixed across environments cannot fit both regimes. This is the main limitation and motivates bounding K per map before
deployment.

**6.3 Why fixed extreme thresholds (Proposition 2′).** The measured inflation of the e-value assumption, K̂(ε) = segFAR(ε)/(2ε), is ≤ 1 on
4Seasons and St Lucia, i.e. Proposition 2 holds as stated. On CMU and Nordland it grows from about 10 at ε = 1e-3 to about 10⁴ at ε = 1e-8,
because coherent aliasing is heavy-tailed (`owf_theory.md` §7).

**6.4 Negative results (development set, 399 runs; each dropped before any fresh test).**
- Hindsight-calibrated thresholds (Proposition 4): recall −0.017 … −0.027, 23–46 runs > α vs 1.
- Wider odometry-scale bank (±15 %, 22 filters): −0.0037.
- Emission temperature selected by evidence: log-evidence +3300 but segFAR ×1.7 and navigation error ×3 on Nordland.
- Simplified tiers: recall ±0.005, with more runs above α.
- Continuous (posterior-mean) fixes: no navigation gain; fix errors are already 2.3–2.5 m.

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
- Global descriptors only (no 6-DoF refinement).
