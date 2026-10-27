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

## Entry 1 — RobotCar per-condition τ diagnostic  [IN PROGRESS]

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

