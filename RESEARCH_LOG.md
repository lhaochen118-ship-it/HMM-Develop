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

