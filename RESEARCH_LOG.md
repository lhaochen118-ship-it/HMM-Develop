# DIVE-HMM / CCBF — Autonomous Research Log

Running log of the autonomous Generate→Run→Critique→Iterate loop (cloud session, Kaggle T4/RTX).
Each entry: hypothesis, experiment, honest verdict. Newest at top.

Kaggle user `nhatlong1103`. Default tier **T4** (instant); **RTX PRO 6000** for large-scale only.
Stall rule: RUNNING with 0 stdout for >10 min → auto re-push fresh version (`automation/run_stall.py`).

---

## Entry 0 — Starting state (inherited from HANDOFF_CCBF.md)

**CCBF** (Calibrated Condition-Belief Filtering): factored Bayes filter over (place p_t, condition c_t);
inferred condition selects a per-condition temperature τ_c for the observation likelihood.

Honest state at handoff:
- NB2 (Nordland 4-season, SALAD): fixed_filter R@1 0.889 / ECE 0.028; **ccbf 0.884 / 0.030 ≈ fixed**.
- Root cause: fitted τ nearly identical across seasons (spring/summer/fall 0.0309, winter 0.0253; **spread ≈ 1.22×**).
  SALAD is so condition-robust on Nordland there is almost no condition-dependent miscalibration to exploit.
- Two components DID work: label-free condition tracking **0.974**; calibrated off-map AUROC **0.992** (> SUE 0.935).
- Verdict: CCBF not yet A*-worthy on Nordland. **Decisive next test:** do per-condition τ differ *substantially*
  on RobotCar day↔night/rain? If τ_night ≫ τ_day → CCBF has a home; else pivot.

---

## Entry 14 — SUE baseline, natural off-map stress test (a validity gap), MSLS + 4Seasons data (2026-10-28)

**SUE baseline** (Zaffar CVPR'24, published K=10, λ=350; label-calibrated benign→all) on SALAD, α=0.05:
- RobotCar: 1/9 violations (worst 0.102), TPR 0.934.
- CMU: 0/11, TPR 0.516.
- Nordland: 0/3, TPR 0.865, which is higher than SelfCal-AA's 0.754.

SUE is more shift-robust than a max-sim threshold, but it still needs labels and still violates on RobotCar.
SelfCal-calibrated SUE alone is not invariant (CMU 1/11 violations). Putting SUE inside the AA combination
(SelfCal-AA+SUE) stays valid and lifts Nordland TPR 0.754→0.806 (winter map 0.593→0.663). Added to eval_all.

**Natural off-map stress test (exp9_natural.py).** Every query of *another* dataset/city is scored against a map,
so all such queries are truly unmapped with no leave-block-out simulation. At α=0.05 most cells have FAR ≤ 0.035.
**One violation:** CosPlace with the CMU map and RobotCar queries gives FAR 0.134 (dawn 0.27).
- **Diagnosis:** raw max-sim is strongly dominated (FAR 0.000), but z_far (0.200), z_gap (0.218) and T_spacing
  (0.12) are inflated. For foreign-domain queries the far-region scores are compressed into a light-tailed bulk,
  so the top-1 stands out in spread-normalised units. The T2 dominance assumption ("shift only makes off-map
  queries less map-like") holds for raw similarity but **not** for scale-normalised statistics under *domain*
  (not appearance) shift.
- **Tried:**
  - (a) Location-only statistics (s1−μ_far, s1−best far): valid but Nordland TPR collapses (0.35→0.10).
  - (b) AND-gate with max-sim: valid but Nordland TPR is about 0.06 (CosPlace).
  - (c) Dual null (map null AND background-image null, intersection-union): fixes the violation only if the
    background resembles the foreign domain (bg=RobotCar fixes it, bg=Nordland does not), and costs CMU TPR
    0.81→0.48.
- **Status: open.** Must be fixed or stated as a scoped limitation (guarantee covers off-map places of the same
  environment/domain as the map).

**MSLS-val** added as the 4th benchmark (CPH 12.5k map / 6.6k queries, SF 6.3k / 4.5k; conditions = city ×
season + night). NB15 loader added. Two T4 kernels `dive-vpr-nb16{a,b}-msls` dump 6 descriptors.

**4Seasons poses** (user request): all 30 `reference_poses` archives + calibration downloaded from TUM and
uploaded as Kaggle dataset `nhatlong1103/4seasons-poses` (layout scene/date like `nhatlong1103/4seasons`).

**Literature:** `literature/VISUAL_LOCALIZATION_REVIEW.md` §6 (HMM/sequence VPR, anti-overlap checklist) and
LITERATURE_GATE Gate 3. Newly found related papers are Trinh & Lyons'25 (negative-stat thresholds), TAO'26
(map-out protocol) and Vysotska ICRA'25. SelfCal is still novel, but these must be cited.

## Entry 13 — SelfCal-AA validated on 6 descriptors × 3 datasets (138 deployment conditions)

**Aliasing guard.** The union rule controls *off-map* false accepts but accepts many in-map aliasing errors on
repetitive Nordland (52%). AND-rule with the gap to the best far region (`z_gap`, map-self-calibrated):
SelfCal-AA = accept iff max(p_comb, p_gap) ≤ α. SALAD α=0.05: aliasing accept 0.000 / 0.015 / 0.057 (RobotCar / CMU /
Nordland) vs 0.33–0.80 for every label-calibrated baseline; BH on AA p-values controls gross FDR on Nordland too
(≤ 0.030 at q=0.1).

**All descriptors (NetVLAD, CosPlace, MixVPR, DINOv2 CLS+mean, SALAD, MegaLoc), α=0.05:**

| method | violating cells (of 138) | settings with ≥1 violation (of 18) | mean TPR | median aliasing-accept |
|---|---|---|---|---|
| SelfCal-AA (no labels) | **0** | **0** | 0.676 | **0.008** |
| SelfCal (no labels) | **0** | **0** | **0.718** | 0.060 |
| Oracle (labels of every condition) | 0 | 0 | 0.721 | — |
| Conformal LOCO (SAFEVPR protocol) | 38 | **18** | 0.716 | 0.231 |
| Quantile Transfer | 64 | 18 | 0.799 | 0.440 |
| Threshold benign→all / CRSG | 25 / 25 | 10 / 10 | 0.664 / 0.785 | 0.218 / 0.173 |
| Gaussian z-norm null | 112 | 16 | 0.740 | 0.451 |

- Honest weak spot: **DINOv2 CLS+mean** (generic, not VPR-trained) — valid but very conservative (TPR 0.06–0.33 vs
  oracle 0.39–0.70): its global feature encodes the capture condition, so same-condition map pseudo-queries are far more
  map-like than deployment queries. Dual (session-mean) centring recovers only 0.33→0.41 → reported as a limitation.
- Robustness: winter-as-map Nordland 0/3; 25% of RobotCar map (650 pseudo-queries) FAR 0, TPR 0.994; ablations
  insensitive; centring essential on Nordland (0.754 vs 0.329).
- Mechanism: one-sided KS excess-risk bound Δ⁺ ≤ 0.052 with the map null vs up to 0.255 with a labelled benign null.
- Cost: offline 24 s (7k-image map, CPU); online ≈10 ms/query incl. similarity products (`selfcal.SelfCalAA`).
- 4Seasons on Kaggle has no pose files → not usable for evaluation.
- Paper: `paper/SelfCal_paper_full.pdf` (built by `paper/build_paper.py` from `paper/selfcal_paper.md` + results).

---

## Entry 12 — New direction: self-calibrating maps (label-free, shift-robust acceptance for VPR)

**Gap.** Every guarantee-giving VPR acceptance method needs labelled calibration data (integrity MLPs, Quantile
Transfer, SAFEVPR LTT/Mondrian, our CRSG+conformal) and breaks under unseen appearance shift. No method controls the
false-accept (wrong loop-closure / off-map) rate without labels.

**Idea.** (1) In VPR the map is a free source of *off-map* calibration queries: each map image with its own spatial
block removed from the map is off-map by construction (leave-one-block-out) — labelled nulls at zero cost.
(2) Use per-query statistics invariant to affine score changes (z-norm of the top-1 vs the far-region maxima, EVT
spacing), so that appearance shift (night compresses scores) does not move their null distribution. (3) Split-conformal
p-values of a deployment query against the map pseudo-queries → FAR control with no labels. (4) Centering descriptors on
the map mean (hubness reduction, map-only).

**Infra.** NB15 dumps fp16 descriptors once (T4): RobotCar-Seasons overcast-reference **rear map with NVM poses** (6954)
+ 1906 train queries (poses cam→world, verified); Extended-CMU **official databases of 11 slices merged into one city
map** (2418 db, 21.4k queries, 11 dates; slices share one world frame); Nordland 4×4500. All analysis local (CPU).
Off-map protocol = leave-one-300m-block-out (RobotCar 1386, CMU 14117, Nordland 12180 off-map queries).

**Results (SALAD, α=0.05; FAR on off-map, #conditions significantly violating, TPR on correct in-map):**

| | RobotCar (9 cond.) | CMU (11 dates) | Nordland (3 seasons) |
|---|---|---|---|
| SelfCal[z_all] (ours, no labels) | 0.009, 0/9, **0.987** | 0.034, 1/11, 0.848 | 0.046, 0/3, 0.304 |
| SelfCal[z_far+center] (ours) | 0.012, 0/9, 0.995 | 0.019, **0/11**, 0.864 | 0.048, **0/3**, **0.840** |
| SelfCal[maxsim] (non-invariant) | 0.001, 0/9, 0.979 | 0.010, 0/11, 0.949 | 0.022, 0/3, 0.411 |
| LabelCal[maxsim] day→all | 0.109, **5/9**, 0.997 | 0.052, **4/11**, 0.985 | 0.037, 0/3, 0.630 |
| LabelCal[CRSG] day→all | 0.099, **4/9**, 0.996 | 0.054, **4/11**, 0.982 | 0.041, 0/3, 0.814 |
| Oracle[maxsim] (labels of every cond.) | 0.040, 0/9, 0.995 | 0.049, 0/11, 0.992 | 0.050, 0/3, 0.780 |
| Theory-only Gaussian z-norm | 0.350, 9/9 | 0.250, 11/11 | 0.125, 3/3 |

- Label-calibrated thresholds transferred from benign conditions **violate the target in 4–5 conditions** on the two
  realistic datasets; map self-calibration is valid everywhere tested (0 significant violations for z_far+center).
- Pure EVT spacing test (closed-form F(2,2k)) is close to valid but mildly anti-conservative (night-rain 0.109@0.05);
  cause = **hubness** (5% of map cells win 59% of null competitions). Map self-calibration + centering fix it.
- No single statistic has the best power everywhere (maxsim strong on CMU, z_far+center on Nordland) → next: self-
  calibrate a *combination* (min of conformal p-values, re-calibrated on the map null).
- Honest caveats: worst-condition FAR at α=0.1 reaches ~0.11–0.13 on RobotCar (within binomial noise, n≈150/cond);
  RobotCar GT only exists for the public train split (test GT withheld), official thresholds applied to top-1 poses.

**Ops lesson (2026-10-28 05:05):** a "RUNNING but silent for 60 min → cancel+restart" rule in `run_kernel.py`
killed two *healthy* multi-descriptor dump kernels (Kaggle's output API hides logs until a run ends). Silent-restart is
now OFF by default; only QUEUED > 10 min triggers cancel (`kaggle kernels delete -y`) + re-push. `--attach` waits for
an already-running kernel after a local container restart without re-pushing.

**Ablation (Nordland, SALAD, α=0.05):** SelfCal-AA is insensitive to cell / exclusion / block / δ / calibration-set
size (TPR 0.72–0.76, FAR ≤ 0.011, aliasing ≤ 0.058, even with 497 null items); **without map-centring TPR drops to
0.33** (hubness), so centring is essential on Nordland. RobotCar: TPR 0.94–0.99 across all variants.

---

## Entry 11 — Literature gate (Bước 0)  →  VERDICT: OVERLAP on method + conformal; reality-check still novel

Full report: `LITERATURE_GATE.md`. Read 9 closest papers in full (paper text only, no code).

- **CRSG-as-a-method is pre-empted.** Its features are standard retrieval-based uncertainty: margin ≈ PA-score d1/d2
  (Hausler'21; baseline in Zaffar CVPR'24), NN-distance = L2-distance RUE (Zaffar'24), score-distribution shape ≈
  RS/SD/SU (Miller et al., RA-L'26, 9 descriptors incl. SALAD/MixVPR). A supervised classifier on distance-vector
  statistics predicting in-tolerance correctness already exists (Carson RA-L'22 SVM; Claxton RA-L'24 MLP with 192
  features, incl. SALAD). CRSG is a 3-feature logistic special case; only the calibrated (ECE/AURC) framing differs.
- **Conformal C2/C3 is pre-empted** by SAFEVPR (2026-05): LTT on cosine breaks under cross-condition shift on Oxford
  RobotCar/NCLT/St Lucia; Mondrian (score-bin) conformal restores FDR validity. Our C3 additionally uses condition
  labels at test time — a real weakness.
- **Naming bug (must fix in any direction):** our "SUE" baseline is `sqrt(2-2*max cos)`, i.e. Zaffar's *L2-distance*
  RUE baseline, NOT SUE (spatial spread of the top-K reference poses). True SUE was never compared.
- **Still novel:** reliability (ECE/AURC/off-map) of sequential filtering is regime-dependent — near-oracle on dense
  Nordland, failing on RobotCar/CMU (off-map 0.23), with the NB8 mechanism; condition-temperature inert. SMR
  (Hussaini'25) only shows sequence matching can hurt *accuracy*.

**Decision:** per the handoff gate rule, do NOT proceed to the official benchmark / BoQ-MixVPR / full paper under the
current "CRSG is a new method" framing. Options (A) reframe as a cross-regime reliability analysis with correct
baselines + label-free Mondrian conformal, or (B) return to Phase 2 — put to the user.

---

## Entry 10 — RTX full-scale validation + Kaggle ops learnings

**Ops / environment findings (verified live):**
- Kaggle token API has **no cancel/stop** method; **pushing a new version does NOT free a queued GPU session**
  (confirmed). The only programmatic cancel is **`kaggle kernels delete -y <id>`** (deletes the kernel → ends its
  run → frees the GPU slot; a later push recreates it). `run_rtx2.py` now cancels this way.
- GPU concurrency cap is **2 batch GPU sessions** (the "Maximum batch GPU session count of 2 reached" error proves
  >1 is allowed). **Two T4 kernels DO run concurrently** — verified: NB13 and NB14 both executed 13:51–14:05
  (Kaggle's output API only exposes a RUNNING kernel's log near completion, so early "0 output" was API lag, not a
  hang). Accumulating sessions without deleting the old one is what triggers the cap error.
- **RTX PRO 6000 was genuinely busy**: NB13 on RTX sat queued 21 min with zero output even on a free slot →
  re-queuing wouldn't help. Moved full-scale to **T4** (instant, reliable). T4 SALAD throughput measured ~16 img/s
  here (NB13 12k imgs extracted in ~12 min), so T4 full-scale is only ~10–15 min/run — RTX's edge is marginal and
  the sequential filter is CPU-bound regardless.

**NB13 — Nordland large-scale (3000/season, N=9000 pooled), T4:**

| tol | method | ECE | AURC ↓ | conf-AUROC ↑ |
|---|---|---|---|---|
| 2 fr (acc 0.804) | softmax | 0.432 | 0.061 | 0.822 |
| | temperature | 0.086 | 0.035 | 0.932 |
| | **CRSG** | 0.047 | 0.029 | **0.957** |
| | fixed_filter / ccbf | 0.063 | **0.011** | 0.933 |
| | off-map | filter 0.981 > SUE 0.922 > CRSG 0.799 | | |

Scale-up (vs 800/season) is **consistent**: CRSG beats softmax & temperature on all metrics and has best
conf-AUROC; the sequential filter keeps its AURC + off-map edge on dense Nordland. The regime story holds at scale.

**NB14 — CMU multi-slice large-scale (4 routes: slice6–9, N=7395 pooled), T4:**

| tol | method | ECE | AURC ↓ | conf-AUROC ↑ |
|---|---|---|---|---|
| 2 m (acc 0.707) | maxsim-cal (baseline) | 0.019 | 0.159 | 0.732 |
| | **CRSG** | 0.025 | **0.143** | **0.759** |
| | fixed_filter | **0.321** | **0.196** | **0.647** |
| 5 m (acc 0.972) | CRSG | 0.010 | **0.006** | **0.854** |
| | maxsim-cal | 0.005 | 0.009 | 0.788 |

Confirms the realistic-data story at scale across **4 distinct routes**: CRSG beats the calibrated-max-sim baseline
on discrimination (AURC, conf-AUROC), and the **sequential filter fails badly** (ECE 0.32, conf-AUROC 0.65). Fixed
two loader bugs first (3-tuple unpack; nested `sliceN/sliceN` duplicate slices).

**Full-scale validation (task) complete:** both Nordland (N=9000) and CMU (N=7395, 4 routes) scale-ups confirm the
contribution — CRSG dominant/robust on realistic data, filter regime-specific — matching the subsampled results.

---

## Entry 9 — NB12 conformal risk control (RobotCar)  →  distribution-free guarantees, all 3 claims hold

Selective predictor on the CRSG reliability score with an RCPS/Hoeffding upper bound so realized selective-risk ≤
target α (finite-sample, δ=0.1). Pose tol 2 m.

- **C1 risk control + coverage.** At α=0.10, **CRSG certifies 61.5% coverage** (realized risk 0.11) while
  **softmax certifies 0%** (must abstain entirely) — CRSG is a far better conformity score. At α=0.20 both ~control
  (CRSG 0.22/0.98 cov, softmax 0.21/0.97).
- **C2 shift breaks the marginal guarantee.** Calibrate on benign, deploy on night/night-rain: realized hard-risk
  exceeds target (α=0.20 → 0.304; α=0.10 → 0.115), a cautionary result for reliability calibrated on easy data.
- **C3 Mondrian restores per-group control.** Marginal per-condition risk varies 0.05–0.22 (worst 0.221 ≫ target
  0.10); **Mondrian per-condition thresholds drive every condition's risk to ≤ target (worst 0.221 → 0.000)**.

**Core A* package complete:** reality-check (3 datasets) + CRSG method (realistic-dominant, descriptor-agnostic) +
conformal guarantees (better score, shift-aware via Mondrian).

---

## Entry 8 — NB11 third dataset: Extended-CMU-Seasons  →  reinforces regime-dependence + CRSG dominance

CMU slice as a single route, 10 date-conditions (camera c0), pose-GT, same CRSG protocol (N=1335). Headline
tol=2m (acc 0.876):

| method | ECE | AURC ↓ | conf-AUROC ↑ | off-map AUROC |
|---|---|---|---|---|
| softmax | 0.651 | 0.085 | 0.640 | — |
| temperature | 0.435 | 0.084 | 0.633 | — |
| fixed_filter | 0.416 | 0.080 | 0.603 | **0.228 (collapse)** |
| ccbf | 0.359 | 0.081 | 0.601 | — |
| **CRSG (ours)** | **0.055** | **0.048** | **0.769** | 0.861 |
| SUE / oracle AURC | — | 0.008 | — | SUE 0.895 |

- **CRSG dominates on CMU exactly as on RobotCar** (best ECE/AURC/conf-AUROC at every tolerance).
- **The sequential filter's off-map COLLAPSES on CMU (AUROC 0.228 — worse than random)**, a 2nd realistic dataset
  confirming the filter is regime-specific; SUE (0.895) and CRSG (0.861) are the robust off-map signals.
- Filter/CCBF again give no discrimination gain over softmax.

**Status: the contribution is now robustly supported on 3 datasets + 2 descriptors.** CRSG dominant on BOTH realistic
benchmarks (RobotCar, CMU), competitive on idealized Nordland; sequential filtering regime-specific (great on dense
Nordland, fails on sparse RobotCar+CMU); condition-temperature inert everywhere.

**Entry 9 (next):** conformal risk control (NB12) — distribution-free selective-prediction guarantees on the CRSG
score; show the marginal guarantee breaks under appearance shift and Mondrian restores it (the A*-depth lever).

---

## Entry 7 — NB9 descriptor-agnostic (DINOv2 instead of SALAD)  →  honest nuance

DINOv2 CLS+mean (dim 1536), much weaker than SALAD: R@1 0.10/0.28/0.50/0.76 at tol 0.5/1/2/5 m. RobotCar, same
protocol. Headline tol=2m (acc 0.50):

| method | ECE | AURC ↓ | conf-AUROC ↑ | off-map |
|---|---|---|---|---|
| softmax | 0.438 | 0.319 | 0.729 | — |
| temperature | 0.309 | 0.326 | 0.738 | — |
| **CRSG** | **0.058** | 0.331 | 0.702 | **0.861** (SUE 0.746, filter 0.802) |

- **CRSG fixes calibration descriptor-agnostically** (ECE 0.03–0.06 across tolerances for BOTH SALAD and DINOv2,
  vs softmax/temperature 0.2–0.7) and **wins off-map with both descriptors** (here 0.861 ≫ SUE 0.746, since a weak
  descriptor degrades the raw NN-distance SUE while multi-feature CRSG is robust).
- **But CRSG's discrimination EDGE is descriptor-dependent:** with strong SALAD it clearly beats softmax on AURC /
  conf-AUROC; with weak DINOv2 it is ~parity (softmax-max already ranks reasonably; the calibrator optimizes
  log-loss, not ranking). Honest: the *calibration* and *open-set* wins are descriptor-agnostic; the *discrimination
  dominance* is larger for stronger descriptors.

**Net:** the descriptor-agnostic claim holds for calibration + open-set (the core reliability deliverables); the
discrimination-dominance claim should be stated for strong descriptors specifically.

---

## Entry 6 — NB8 unified "calibrate the belief"  →  sharper finding: calibration can't rescue the filter

Tested CRSG-filter = calibrate the *filter posterior* geometry (max/margin/entropy/null), vs CRSG-single
(calibrate single-image retrieval geometry), on RobotCar. Headline tol=2m (acc ~0.77):

| method | ECE | AURC ↓ | conf-AUROC ↑ |
|---|---|---|---|
| softmax | 0.303 | 0.135 | 0.736 |
| raw filter | 0.285 | 0.138 | 0.700 |
| **CRSG-single (ours)** | 0.071 | **0.090** | **0.801** |
| CRSG-filter | 0.054 | 0.137 | 0.678 |

- **CRSG-filter does NOT recover** on sparse RobotCar: it fixes ECE (0.054) but NOT discrimination
  (AURC 0.137 ≈ raw filter; conf-AUROC 0.678 < CRSG-single 0.801). CRSG-single is best at every tolerance.
- **Mechanistic insight:** the discriminative reliability signal lives in the **single-image retrieval-score
  geometry (the top-1/top-2 margin)**. On sparse realistic data the sequential filter **destroys** this signal
  (its motion prior is uninformative), and no calibration of the filter posterior can regenerate it. "Calibrate
  the belief" is not a free lunch — you must calibrate the belief that *carries discrimination*, which on realistic
  data is the single-image geometry, not the filter. (On dense Nordland the filter posterior IS informative, so
  there the filter wins — Entry 5.)

**This completes a clean, honest story:** reliability is regime-dependent; the single-image retrieval margin is the
robust discriminative signal; CRSG-single is the stream-free default that dominates realistic data and is
competitive on idealized data; sequential filtering and condition-temperature are regime-specific / inert.

---

## Entry 5 — NB7 cross-dataset on Nordland  →  the honest, richer finding: reliability is REGIME-DEPENDENT

Nordland 4 seasons (ref=summer), pooled cross-fit, frame-GT. R@tol: 0.815@0, 0.854@1, 0.879@2, 0.914@5
(meaningful errors — a fair regime). Headline tol=0 (acc 0.815):

| method | ECE | AURC ↓ | conf-AUROC ↑ | off-map AUROC |
|---|---|---|---|---|
| softmax (uncal) | 0.254 | 0.063 | 0.813 | — |
| temperature | 0.039 | 0.041 | 0.920 | — |
| **CRSG (ours)** | 0.040 | 0.0365 | **0.941** | 0.804 |
| **fixed_filter** | **0.017** | **0.019** | 0.940 | **0.992** |
| ccbf | 0.017 | 0.019 | 0.941 | — |
| oracle AURC / SUE | — | 0.018 | — | SUE 0.935 |

**This refutes the naïve "CRSG dominates everywhere" reading and gives the real contribution:**
- On **dense idealized Nordland**, the **sequential filter is excellent** (AURC 0.019 ≈ oracle 0.018; off-map
  0.992 ≫ SUE). CRSG is only *competitive* (AURC 0.037), and CRSG's off-map (0.804) is *weak* here.
- On **sparse realistic RobotCar**, the filter **collapses** and **CRSG dominates** (Entry 4).
- CRSG beats softmax AND temperature on **both** datasets, and is the best **stream-free** method + the most
  **regime-robust** one; the filter is regime-specific (needs dense temporal structure).

**Honest contribution (revised).** (1) A reliability protocol + the finding that VPR reliability is
**regime-dependent** and that Nordland-only evaluation masks it (sequential filtering looks great on Nordland,
fails on realistic RobotCar; condition-temperature is inert on both). (2) **CRSG**, a trivial stream-free
per-frame geometry calibrator that is regime-robust and dominant on realistic data. This is honest and genuinely
useful, but as a *single-method-wins* claim it does NOT hold — the filter wins on Nordland.

**Entry 6 (next, unifying).** Apply the CRSG geometry-calibration to the **filter's posterior** (not just the
single-image similarity): "calibrate whatever belief you have." Hypothesis: this is regime-adaptive best-of-both —
matches the filter on dense Nordland and keeps CRSG's win on sparse RobotCar — turning a nuanced result into a
clean unified method. (NB8)

---

## Entry 4 — NB6 CRSG validation on RobotCar (tolerance sweep)  →  POSITIVE: CRSG dominates (on realistic data)

Calibrated Retrieval-Score Geometry (**CRSG**) = a per-frame logistic on retrieval-score geometry
[top1−top2 margin, NN-distance, score entropy] → one calibrated reliability score. Pooled cross-fit (fit 50% /
eval 50%), ref map = overcast-summer, 8 query conditions, pose tolerance swept (R@1: 0.21@0.5m, 0.51@1m,
0.79@2m, 0.94@5m — tight tol = meaningful errors; the 5m regime used earlier was too easy).

**Headline tol = 2.0m (acc 0.765):**

| method | ECE | AURC ↓ | conf-AUROC ↑ |
|---|---|---|---|
| softmax (uncal) | 0.485 | 0.133 | 0.749 |
| temperature scaling | 0.303 | 0.135 | 0.736 |
| sequential fixed_filter | 0.301 | 0.132 | 0.677 |
| CCBF | 0.269 | 0.130 | 0.671 |
| **CRSG (ours)** | **0.069** | **0.090** | **0.801** |
| oracle AURC | — | 0.030 | — |

- **CRSG gives the best discrimination (AURC, conf-AUROC) at EVERY tolerance** {0.5,1,2,5}m, and near-best ECE.
  It beats softmax, temperature, the sequential filter AND CCBF. The sequential/condition methods give **no**
  reliability benefit over softmax here (AURC ~0.13 ≈ softmax; ECE ~0.27–0.30).
- Single-feature platt(margin) calibrates ECE well but discriminates poorly (conf-AUROC ~0.61–0.74); the
  **multi-feature CRSG** is what delivers discrimination — a clean ablation.
- **Off-map:** CRSG 0.949 ≈ SUE 0.948 > filter_null 0.898. CRSG is a *unified* reliability score (in-map
  calibration + open-set), matching the best instantaneous OOD and beating the filter.
- (Notebook prints "PARTIAL" only because a hard gate ECE≤0.06 vs CRSG 0.069; the discrimination wins are the
  real, consistent result.)

**Verdict: the contribution holds.** On realistic RobotCar hard conditions, reliable VPR needs **calibrated
retrieval-score geometry**, not sequential filtering or condition modeling. Simple per-frame calibration dominates.

**Entry 5 (next):** cross-dataset — the SAME CRSG protocol on Nordland (4 seasons, frame-GT). Nordland is dense
(the filter's natural home), so it tests whether CRSG matches/beats the filter even where the filter is strongest.

---

## Entry 3 — NB5 diagnosis + instantaneous-calibration probe  →  BREAKTHROUGH (positive direction)

- **G1 velocity:** sorted-GT traversal is clean ~1:1 (median Δ=1, 97–99% of steps in [0,3], <2% jumps) for all
  conditions. The motion model is **not** mismatched.
- **G2 matched filter:** filter_matched ECE = filter_default = 0.439 (single 0.472). → **The filter's RobotCar
  failure is REAL, not a setup artifact.** Temporal filtering genuinely barely helps calibration here.
- **G3 instantaneous calibration (cross-fit, fit evens / eval odds):**
  - softmax-max (uncalibrated) ECE = **0.470**
  - **Platt(top1−top2 gap) ECE = 0.0056**  ← ~80× better, 2 parameters
  - Platt(sue)=0.029, Platt(entropy)=0.024, Platt(maxsim)=0.024 — all crush softmax.
  - off-map AUROC: SUE / maxsim = **0.950** > filter_null 0.888 > gap12 0.668.

**Insight.** VPR reliability does NOT need sequential filtering or condition modeling. The failure mode is that
**softmax-max over ~180 near-tie candidates is not a correctness signal**; the **top1−top2 retrieval margin** is,
and a trivial 2-parameter calibrator on it fixes ECE. Instantaneous **NN-distance** is the best off-map detector.
A per-frame "calibrated retrieval-score geometry" beats the whole sequential/condition line (filter, CCBF).

**Caveat to resolve in Entry 4.** Acc is ~0.94–0.98 across all conditions, so a low ECE could partly reflect a
stable base rate. Must report **discrimination** (risk–coverage / AURC, confidence-vs-correct AUROC), not just ECE,
and test **cross-condition transfer** (fit calibrator on benign/day conditions, evaluate on night/rain) — that
transfer under appearance shift is the real novelty claim, not in-condition fitting.

**Direction (candidate A* contribution).** *Calibrated retrieval-score geometry for reliable VPR*: a descriptor-
agnostic, per-frame calibration (margin→confidence, NN-distance→abstention/OOD) that dominates sequential Bayesian
filtering and condition-aware temperature across datasets, with selective-prediction (risk–coverage) and possibly
conformal coverage guarantees. Honest negatives on filter/CCBF become the motivation.

---

## Entry 2 — RobotCar reliability gating (NB4)  →  VERDICT: RECONSIDER

Both Nordland "wins" FAILED to generalize to RobotCar (ref=overcast-summer, 6 hard query conds, pose-GT 5m):

| method | pooled ECE | pooled acc |   | off-map | AUROC |
|---|---|---|---|---|---|
| single_image | 0.472 | 0.943 |   | **SUE** | **0.950** |
| fixed_filter | 0.439 | 0.950 |   | fixed_null | 0.888 |
| ccbf | 0.398 | 0.950 |   | ccbf_null | 0.891 |

- **Filter does NOT fix calibration** (0.472→0.439; on Nordland it was 0.076→0.028). ECE-vs-T stays flat ~0.44–0.49.
- **SUE (trivial L2-to-NN) BEATS the filter on off-map** (0.950 vs 0.888) — the *opposite* of Nordland (0.99 vs 0.94).
- All methods badly UNDER-confident (acc 0.94 but conf ~0.47): softmax-max over ~180 near-tie candidates ≠ P(correct).

**Interpretation (tentative):** the Nordland advantages are artifacts of its dense, 1:1-aligned, smooth trajectories.
RobotCar train = ~180 *sparse* samples per condition → the motion model (velocity≈1) is likely mismatched, which
would handicap the filter. **Must rule out this setup artifact before concluding the filter "fails"** (honesty).

**Entry 3 (next):** NB5 diagnoses traversal spacing + retests the filter with a *matched* motion model; and probes
a new direction — **instantaneous calibrated uncertainty** (Platt-scaled SUE / top1–top2 gap / score-entropy) to
see if a simple per-frame signal fixes calibration + beats raw SUE on off-map (works on sparse data, no dense video).

---

## Entry 1 — RobotCar per-condition τ diagnostic  →  VERDICT: PIVOT

**Hypothesis.** RobotCar's huge day↔night/rain/snow appearance gaps make SALAD's match/non-match score
distributions differ drastically by condition ⇒ τ_c spread ≫ Nordland's 1.22× ⇒ condition-conditional
calibration (CCBF) has real value.

**Experiment (`DIVE_HMM_CCBF_NB3.ipynb`, built from `nb3_src/`, T4).**
- Parse `robotcar_v2_train.txt` with the **corrected** pose format (translation = flat idx [3,7,11]; NB2's
  `nums[4:7]` was wrong).
- SALAD descriptors per condition; benign reference condition B = sun/overcast.
- For every query condition: pose-NN GT at an adaptive tolerance; fit τ_c by NLL; report match/non-match gap.
- Compare pooled single-image ECE under one global τ vs per-condition τ_c.
- Decision keyed on **τ spread** and **gap variation across conditions** (single-image ECE gain is reported
  but NOT gated on — a dry run confirmed per-condition τ barely moves single-image ECE even when τ varies 6×;
  CCBF's real edge, if any, is *sequential*: Theorem 1 / ECE-vs-T).

**Result (T4, SALAD dim 8448, 9 RobotCar conditions ~200 imgs each, ref=sun, tol=5m).**

| query cond | n | τ | R@1 | match | nonmatch | gap |
|---|---|---|---|---|---|---|
| night | 175 | 0.0208 | 0.977 | 0.384 | 0.295 | 0.089 |
| night-rain | 203 | 0.0253 | 0.966 | 0.395 | 0.308 | 0.087 |
| rain | 170 | 0.0253 | 1.000 | 0.553 | 0.384 | 0.170 |
| dawn | 210 | 0.0253 | 0.986 | 0.529 | 0.380 | 0.149 |
| snow | 215 | 0.0253 | 0.991 | 0.549 | 0.392 | 0.158 |
| dusk | 167 | 0.0253 | 1.000 | 0.580 | 0.414 | 0.166 |
| overcast-winter | 181 | 0.0253 | 0.994 | 0.564 | 0.397 | 0.167 |
| overcast-summer | 201 | 0.0309 | 0.995 | 0.565 | 0.394 | 0.171 |

- **τ spread = 1.49×** (Nordland 1.22×). per-condition-τ pooled ECE improvement vs global-τ = **−0.1%** (nil).
- Appearance gap is **real**: night/night-rain match–nonmatch gap (~0.088) is **half** the day gap (~0.17); night
  match scores are much lower (0.38 vs 0.58). But R@1 stays ~0.98 everywhere — **SALAD is recall-robust**.
- Single-image pooled ECE ≈ **0.55** (softmax over ~200 candidates is wildly miscalibrated to top-1 correctness).

**Verdict: PIVOT (CCBF's temperature mechanism is inert on a 2nd dataset).** A scalar per-condition temperature
does not convert the real appearance gap into a calibration gain — on both Nordland and RobotCar. Condition-
conditional *temperature* is the wrong knob. **Stop polishing CCBF-as-temperature.**

**What IS worth keeping (verified or strongly indicated):**
1. The sequential Bayes filter sharply improves calibration (Nordland single→filter ECE 0.076→0.028).
2. Filter-null off-map detection beats SUE (Nordland AUROC 0.99 vs 0.94).
3. Single-image VPR confidence is badly miscalibrated even when recall is ~saturated — an under-studied problem.

**Research gap / new direction.** VPR is benchmarked on recall, which is saturating for SOTA descriptors even in
hard conditions. The deployment-critical axis is **reliability**: calibrated confidence + knowing when you are
off-map/lost. Standard fixes (temperature scaling, SUE) are weak. → **Contribution candidate:** a descriptor-
agnostic sequential probabilistic layer giving calibrated place posteriors + reliable open-set abstention,
beating temperature/SUE across datasets; condition-modeling demoted to an honest ablation ("when does it help?").

**Gating experiment (Entry 2):** confirm (1) filter fixes calibration and (2) filter-null beats SUE off-map — on
**RobotCar hard conditions** (night/rain), with route-indexed maps + pose-GT. If both hold → solid cross-dataset
reliability contribution. If the filter does NOT help on RobotCar → rethink (open-set-only, or tournament idea B).

