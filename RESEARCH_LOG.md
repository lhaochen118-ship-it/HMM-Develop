# Research Log

*Branch `hmm-navigation` (2026-10-29): hướng mới là HMM sequence-based visual localization. Các entry dưới đây thuộc
hướng cũ (CCBF/HMM filter → SelfCal), giữ lại làm lịch sử và bài học. Entry mới bắt đầu từ 18, đặt ở trên cùng. Kết quả
và script SelfCal được nhắc tới nằm ở branch `claude/selfcal-aa` / `claude/selfcal-seq`.*

Newest entry at the top. Each entry: hypothesis, experiment, honest verdict. Compute runs on Kaggle (see
`handoff/02_ENGINEERING_OPS_NOTES.md`).

## Entry 18 — HMM direction, first round: data audit, sequence validity root cause, EVT-HMM (2026-10-29)

**Data (Step 1):** see `DATA_AUDIT.md`. The dumps are correct. RobotCar train queries are only 9-frame snippets.
CMU (median 186 frames) and Nordland have long sequences. No dataset has odometry except 4Seasons (real VIO). On
RobotCar/CMU, MegaLoc/SALAD place recall is at 92–98 % @10 m.

**HMM headroom check (CMU, CosPlace, local):**

| method | R@5 m |
|---|---|
| single frame | 90.7 |
| HMM random walk | 91.0 |
| HMM + simulated odometry | 92.5 |

The worst condition stays at 84.5 → 84.8. Average place recall is not where an HMM paper can win on these
benchmarks.

**H1: odometry-consistent sequence evidence (`analysis/seq_odo.py`, 18 settings, 6 T4 accounts).**
- exp11's run statistic counts a *stationary* alias as consistent. Requiring the matches to move with the odometry,
  anchored at the last frame with a tight tolerance (`RUNO`, 1 frame on Nordland), removes the Nordland MegaLoc
  violations at every L (0/18 conditions, worst 0.050). It also lifts power: DINOv2 0.44 → 0.63, NetVLAD
  0.57 → 0.70, CosPlace 0.67 → 0.81, MixVPR 0.73 → 0.88. The alias acceptance drops below the RUN statistic's.
- On CMU, long windows (L = 20) still "violate" (DINOv2 3/11, worst 0.14).
- **Root cause:** windows inside one 300 m block are strongly dependent. The map null of CMU has only ~500
  pseudo-windows ≈ 10–20 independent blocks, so the realised FAR of all 11 conditions (same calibration set) moves
  together. The per-window binomial violation test is itself anti-conservative for clustered windows.
- A deployment-condition null (calibrating on the same condition's own LOBO query windows, cross-fit by block parity)
  is *worse* (`proto/dcn.py`): violations already at L = 1–5. Spatial heterogeneity between blocks dominates.
- An excursion-level guarantee (null unit = whole held-out segment, scan max) would be exact under within-segment
  dependence. But CMU gives only 61 ten-frame null segments, too few.
- **Verdict:** the sequence guarantee is limited by the effective sample size of the spatial null. Not pursued as the
  main claim. The odometry-consistency fix is kept.

**EVT-HMM (new idea, `analysis/hmm_eval.py`).** Turn the map's leave-block-out null into the *HMM itself*. With
per-query affine-invariant z-scores of the cell maxima:

- the best non-matching z follows a Gumbel law (μ, β), estimated from map pseudo-queries;
- emission of place j = exp((z_j − μ)/β), the Gumbel-tail likelihood ratio;
- the off-map state is a "phantom place" at μ.

No temperature or threshold is tuned, and the HMM prior gives the multiplicity correction (z_1 > μ + β ln n is
needed to leave the off-map state when not localised).

Navigation protocol: 30 % of the map blocks removed, simulated odometry. First local run, CMU CosPlace, seed 0:

| method | recall | wrong | off-map false loc. | tuned |
|---|---|---|---|---|
| single | 0.878 | 0.122 | 1.000 | – |
| HMM exp(s/T) | 0.918 | 0.082 | 1.000 | T on 1 condition |
| HMM + k-th-best off-map (Xu'21) | 0.867 | 0.060 | 0.108 | T, k |
| **EVT-HMM** | 0.868 | 0.060 | **0.048** | none |
| EVT emission, no off-map | **0.927** | 0.073 | 1.000 | none |

Full run (6 descriptors × 3 datasets × 3 seeds) on Kaggle CPU: pending. The 4Seasons dump (21 of 30 recordings have
images on Kaggle, about 65 k frames, 6 descriptors, 7 T4) is running.

## History before SelfCal (Entries 0–10, condensed; full text in git history before branch `claude/selfcal-aa`)

- **CCBF / HMM sequence filter (Entries 0–3, 5–8).** A Bayes filter over (place, condition) with per-condition
  temperatures. The filter fixes single-image calibration on dense Nordland (ECE 0.076 → 0.028) and its off-map
  detection beats SUE there (AUROC 0.99 vs 0.94). But the condition temperatures barely differ (spread ≈ 1.2×), and
  on RobotCar/CMU the filter's reliability fails (off-map 0.23). Verdict: reliability is regime-dependent; the CCBF
  method was dropped.
- **CRSG (Entries 4, 8, 9).** A label-calibrated logistic gate on [margin, max-sim, entropy] with conformal risk
  control. It looked strong, but Entry 11's literature gate found it pre-empted (PA ratio, RS/SD/SU, integrity MLPs,
  SAFEVPR's Mondrian conformal). It survives only as a baseline.
- **Ops (Entry 10).** RTX full-scale runs and the Kaggle stall/re-push rules, now in the ops notes.
- **Lesson carried forward.** Labels from benign conditions do not transfer to hard ones. This motivates a label-free
  null drawn from the map itself, which is SelfCal (Entry 12).


## Entry 17 — SelfCal-Gap, sequence-level SelfCal, localisation demo (summary; full entry on branch `claude/selfcal-seq`)

- **SelfCal-Gap** (z_gap only + strata + gate): 0/192 violations, TPR **0.746** (oracle 0.706, AA 0.646), MSLS 0.603,
  worst point FAR 0.073.
  - Reason it helps: z_far's dominance fails on MSLS (alone it reaches FAR 0.40–0.88 there).
  - Ported here additively: `SelfCalTest(mode="gap")`, rows in `analysis/results/gap/`. The 1,275 AA rows of the
    rerun equal this branch's results exactly.
- **Sequence SelfCal** (window, map pseudo-sequences): large power gains, but window validity fails (Nordland MegaLoc
  2–3/3 seasons). Not a claim.
- **Localisation demo** (map with 30 % holes, 10 seeds): per-frame SelfCal-AA beats the label-calibrated threshold in
  all 12 descriptor × dataset pairs (mean error 1.3–12.6× lower). Details in `handoff/01_SCIENTIFIC_FINDINGS.pdf`.

## Entry 16 — Full rerun with the adopted SelfCal-AA (Mondrian strata by sd_far + domain gate), 6 T4 on 3 accounts (2026-10-28)

Branch `claude/selfcal-aa`. Rule = `selfcal.SelfCalTest` (B=10 strata of the null's sd_far, gate p_maxsim ≤ 0.8).
6 descriptors × 4 datasets = 24 settings, 192 deployment conditions, α = 0.05 (`paper/tables.md`, Table 2a):

| method | labels | viol. cond. | settings ≥1 viol. | mean TPR | median alias-accept | max worst FAR |
|---|---|---|---|---|---|---|
| **SelfCal-AA** | none | **0/192** | **0/24** | **0.646** | 0.011 | **0.048** |
| − strata | none | 0/192 | 0/24 | 0.612 | 0.008 | 0.140 |
| − gate | none | 0/192 | 0/24 | 0.648 | 0.012 | 0.048 |
| − both (original AA) | none | 0/192 | 0/24 | 0.617 | 0.011 | 0.140 |
| − alias guard | none | 5/192 | 3/24 | 0.667 | 0.072 | 0.721 |
| SUE [Zaffar'24] | benign | 16/192 | 10/24 | 0.661 | 0.070 | 0.163 |
| Threshold benign→all | benign | 36/192 | 15/24 | 0.652 | 0.218 | 0.281 |
| CRSG | benign | 32/192 | 14/24 | 0.757 | 0.169 | 0.356 |
| Conformal LOCO (SAFEVPR) | other cond. | 51/192 | 24/24 | 0.699 | 0.217 | 0.419 |
| Quantile Transfer | benign | 79/192 | 23/24 | 0.769 | 0.405 | 0.483 |
| Oracle | all | 0/192 | 0/24 | 0.706 | — | 0.050 |

- **Validity:**
  - No violating condition anywhere. The worst single-condition FAR is now ≤ α (0.048).
  - The original rule reached 0.140 in one condition. That is not significant after Bonferroni, but the point
    estimate is above α. Strata fix it.
- **Natural off-map (exp9):** deployable `SelfCalAA` on queries from the other datasets/cities. 0/120 cells > α, max
  FAR 0.007. The original rule leaked 0.134 (CosPlace, CMU map).
- **Power:** on RobotCar, CMU and Nordland the TPR is 0.708 vs oracle 0.721 (original rule 0.676).
- **MSLS is still the weak spot:** TPR 0.460 vs oracle 0.661 (original 0.439).

  | descriptor | v2 | v1 | oracle |
  |---|---|---|---|
  | MegaLoc | 0.879 | 0.878 | 0.965 |
  | CosPlace | 0.578 | 0.535 | 0.736 |
  | SALAD | 0.528 | 0.549 | 0.820 |
  | MixVPR | 0.517 | 0.480 | 0.747 |
  | NetVLAD | 0.218 | 0.135 | 0.377 |
  | DINOv2 | 0.040 | 0.060 | 0.320 |

  Label-based baselines get their extra MSLS power by violating 6–15 of the 54 conditions.
- **Ablations (SALAD):** centring still matters on Nordland (TPR 0.742 vs 0.568 without).
- **Map size (RobotCar, SALAD):** 0/9 violations at 25 %, 50 % and 100 % of the map. TPR 0.964 / 0.843 / 0.978.
  The 50 % dip has 115 null items per stratum; to look at.
- **Ops:**
  - The GPU backend makes `eval_all` take 0.5–1 min per setting (RobotCar/CMU/Nordland) and about 40–50 min for MSLS.
  - Natural off-map on CPU takes 17–40 min per descriptor.
  - Dumps are now a public dataset, `nhatlong1103/vpr-descriptor-dumps`.
- **Next for A\*:**
  1. Power on MSLS (large, heterogeneous maps): a better nuisance variable for the strata, or per-city/per-view nulls.
  2. Sequence-level anytime-valid acceptance.
  3. A SLAM/loop-closure demo.

## Entry 15 — MSLS (4th dataset) and the domain-shift fix: a lenient raw-similarity gate (2026-10-28)

**MSLS-val, both cities (CPH+SF, 9 conditions, 6 descriptors, Kaggle CPU):** SelfCal-AA has **0/54** significant
violations at α=0.05. The label-based methods all violate somewhere: SUE 5, CRSG 7, benign threshold 11, LOCO
(SAFEVPR) 13, Quantile Transfer 15. SelfCal without the AA guard has 5. Power is conservative on MSLS: MegaLoc 0.878
vs oracle 0.965, SALAD/CosPlace/MixVPR 0.48–0.55 vs 0.74–0.82. Natural off-map (exp9, now with MSLS): CPH↔SF cross-city
FAR ≤ 0.005 for all descriptors. The only failure is CosPlace with the CMU map (rc 0.134, msls-cph 0.135, msls-sf 0.089).

**exp10 (account yuan1103, 2×T4 + CPU): 8 variants × 6 descriptors × 5 maps.** 192 LOBO conditions, 120 natural
map/source cells.

| variant | LOBO viol. | worst LOBO | natural cells > α | natural max | mean TPR |
|---|---|---|---|---|---|
| AA (current) | 0/192 | 0.047 | 3/120 | 0.143 | 0.587 |
| **AA & p_maxsim ≤ 0.8** | **0/192** | 0.040 | **0/120** | **0.008** | **0.583** |
| AA & p_maxsim ≤ 0.5 | 0/192 | 0.040 | 0/120 | 0.004 | 0.567 |
| AND-ms (gate at α) | 0/192 | 0.029 | 0/120 | 0.000 | 0.432 |
| Mondrian by sd_far (5 strata) | 0/192 | 0.061 | 2/120 | 0.061 | 0.621 |
| Mondrian by maxsim | 0/192 | 0.074–0.094 | 15–20/120 | 0.179 | 0.46–0.49 |

**Decision:** adopt **SelfCal-AA with a lenient raw-similarity gate** (accept only if the raw max-sim is above the
20 % quantile of the map null, p_ms ≤ 0.8). It removes every domain-shift failure for a TPR cost of 0.004 on average
(Nordland 0.533 → 0.524).
- **Theory (to write):** the acceptance set is an intersection, so FAR ≤ min(P(p_AA ≤ α), P(p_ms ≤ 0.8)). The test
  is valid if **either** (A) the invariant statistics are dominated (appearance shift) **or** (B) foreign-domain
  queries fall below the null's 20 % max-sim quantile with probability ≥ 1−α (domain shift). This is a
  "union of assumptions" robustness result.
- **Next:**
  - Mondrian-by-sd_far gains power (0.621) but leaks under domain shift. Test it **with** the gate for more power.
  - Power on MSLS is still the main weakness.
- **Follow-up (Mondrian-by-sd_far + gate; kernels dive-vpr-shiftfix2-*, 6 descriptors × 5 maps):**

  | variant | LOBO viol. | max worst FAR | natural cells > α | natural max | mean TPR |
  |---|---|---|---|---|---|
  | AA&ms<=0.8 | 0/192 | 0.040 | 0/120 | 0.008 | 0.583 |
  | **Mondrian-sdf-10&ms<=0.8** | **0/192** | **0.048** | **0/120** | **0.006** | **0.612** |
  | Mondrian-sdf-5&ms<=0.8 | 0/192 | 0.061 (SALAD rc, n.s.) | 0/120 | 0.006 | 0.618 |

  The gate also fixes Mondrian's domain-shift leaks (2/120 → 0/120). The gain is largest where SelfCal was weakest:
  DINOv2 TPR 0.124 → 0.218 (B=10), CosPlace 0.624 → 0.677, NetVLAD 0.410 → 0.447, CMU map 0.692 → 0.749,
  Nordland 0.524 → 0.567. MegaLoc, MixVPR and SALAD are unchanged (±0.01). MSLS improves only slightly
  (0.45 → 0.46–0.48).
  **Candidate main method:** Mondrian-sdf-10 + gate, because its worst condition stays ≤ α everywhere. Caveat: B
  and γ were chosen after seeing these results. Either fix them a priori in the paper and report B ∈ {5,10} as a
  sensitivity check, or select them on the map null only. Mondrian conformal is valid per stratum under
  exchangeability, so T1–T6 carry over conditionally on the sd_far stratum.

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
