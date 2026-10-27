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

**Result.** _(pending T4 run — see below)_

**Verdict.** _(pending)_
