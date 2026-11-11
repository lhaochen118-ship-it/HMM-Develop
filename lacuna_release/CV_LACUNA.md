# LACUNA: CV entry

## Main version (4 lines, for the "Research Experience" or "Projects" section)

**LACUNA: Open-World Sequential Visual Localization on Maps with Holes** · *paper in preparation* · [[GitHub]](https://github.com/nhatlong113/LACUNA---Localization-Aware-of-Coverage-and-UNmapped-Areas)

- Proposed **LACUNA**, an open-world Bayes filter that models unmapped space as part of a metric state. A robot localizing on an incomplete image map therefore *predicts* when it leaves the map by dead reckoning, instead of committing to look-alike places and reporting false position fixes. Added label-free evidence, calibrated causally within each session, that suppresses odometry-unobservable aliasing.
- On 432 pre-registered runs (8 environments from 6 datasets incl. Oxford RobotCar, Nordland, CMU Seasons, 4Seasons; 6 VPR descriptors), achieved **93% recall** while exceeding the 5% false-report budget on only **0.7%** of runs. Outperformed SOTA (TAO'26, Claxton RA-L'24, Xu RA-L'21) by **+26–28 pp** recall with **2–3× lower** navigation error, even when their thresholds were tuned on test labels.

## Short version (3 lines, when space is tight)

**LACUNA: Open-World Visual Localization on Maps with Holes** · *paper in preparation* · [[GitHub]](https://github.com/nhatlong113/LACUNA---Localization-Aware-of-Coverage-and-UNmapped-Areas)

- Proposed an open-world Bayes filter that models unmapped areas in the state, so a robot predicts leaving an incomplete map instead of reporting false position fixes. No labels are needed at deployment.
- 93% recall on 8 environments (6 datasets) × 6 descriptors, with the false-report budget exceeded on only 0.7% of runs. +26–28 pp recall over SOTA (TAO'26, Claxton RA-L'24, Xu RA-L'21), even with their thresholds tuned on test labels.

## Where each number comes from

| Claim | Value | Source |
|---|---|---|
| Recall | 0.926–0.933 on three fresh hole-layout groups (seeds 64–72, 144 runs each) | `analysis/results/owf/s1106/e28_rerun.md` |
| False-report budget | 3 of 432 runs above α = 0.05 (0.7%); 0 of 432 at the safe operating point | `e28_rerun.md` |
| vs SOTA, fair comparison | 0.927 vs 0.670 / 0.651 / 0.651 (Claxton / Xu / TAO at per-run oracle threshold, 288 runs) → +0.257 … +0.276, CI lower bound > 0 | `analysis/results/owf/s1111/e29a_board_s67_72.md` (Entry 29a) |
| Navigation error | 13.3 m vs 28.1 / 44.5 / 37.1 m at the same oracle thresholds → 2.1–3.3× | same file |
| vs closed-world baseline | +0.133 [0.115, 0.151] and +0.117 [0.100, 0.133] (95% CI) | `e28_rerun.md`, Entries 24 / 26 |

## Claims dropped after audit 3 (2026-11-11, `handoff/09_KIEM_TOAN_2026-11-11.md`), do not use

- "SOTA exceeds the target on 56–90% of runs": this measured the baselines' published operating points, which do not target segFAR. A
  reviewer would call it a strawman. Use the oracle-threshold comparison above. The published-point numbers (57–89%) can only appear
  alongside it.
- "Above the single-frame oracle": that oracle is per-frame top-1 accuracy, which any sequence filter is expected to beat, and on CMU
  LACUNA is below it.

## Caveats to have ready for interviews

- "Fresh" means fresh hole layouts on the same images, sequences and descriptors. The holes are simulated (30% of 300 m map cells removed)
  except on NCLT, 4Seasons cross-scene and VPR-Space.
- On CMU, Oxford and St Lucia the simulated odometry keeps the true heading. With heading drift of 0.13°/√m, recall drops by 4.8 points
  (St Lucia: 14.5), and validity is unchanged (Entry 29b).
- The external baselines were re-implemented from the papers' text (no original code). The TAO re-implementation still has recall below
  top-1 on 5 of 8 datasets.
