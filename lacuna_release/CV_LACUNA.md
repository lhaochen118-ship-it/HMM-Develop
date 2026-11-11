# LACUNA: CV entry

## Main version (4 lines, for the "Research Experience" or "Projects" section)

**LACUNA: Open-World Sequential Visual Localization on Maps with Holes** · *paper in preparation* · [[GitHub]](https://github.com/nhatlong113/LACUNA---Localization-Aware-of-Coverage-and-UNmapped-Areas)

- Proposed **LACUNA**, an open-world Bayes filter that models unmapped space as part of a metric state. A robot localizing against an incomplete image map therefore *predicts* leaving the map by dead reckoning instead of committing to look-alike places and reporting false position fixes. Added label-free, causally calibrated evidence that rejects odometry-unobservable aliasing.
- On 432 pre-registered runs (8 datasets incl. Oxford RobotCar, Nordland, CMU Seasons, 4Seasons; 6 VPR descriptors), achieved **93% recall** (**+12–13 pp** over a closed-world baseline, **+8 pp** over a single-frame oracle). It violates the 5% false-report budget on only **0.7%** of runs, versus **56–90%** for SOTA methods (TAO'26, Claxton RA-L'24, Xu RA-L'21), with **3.5–8.7× lower** navigation error.

## Short version (3 lines, when space is tight)

**LACUNA: Open-World Visual Localization on Maps with Holes** · *paper in preparation* · [[GitHub]](https://github.com/nhatlong113/LACUNA---Localization-Aware-of-Coverage-and-UNmapped-Areas)

- Proposed an open-world Bayes filter that models unmapped areas in the state, so a robot predicts leaving an incomplete map instead of reporting false position fixes. No labels are needed at deployment.
- 93% recall on 432 runs (8 datasets, 6 descriptors). It violates the 5% false-report budget on 0.7% of runs, versus 56–90% for SOTA (TAO'26, Claxton RA-L'24, Xu RA-L'21).

## Where each number comes from (audited re-run, Entries 27–28 of `RESEARCH_LOG.md`)

| Claim | Value | Source |
|---|---|---|
| Recall | 0.926–0.933 on three fresh groups (seeds 64–72, 144 runs each) | `analysis/results/owf/s1106/e28_rerun.md` |
| vs closed-world baseline (HSI-VNc) | +0.133 [0.115, 0.151] and +0.117 [0.100, 0.133] (95% CI) | same file, Entries 24 / 26 |
| vs single-frame oracle | 0.928 vs 0.847, 0.926 vs 0.848 | `paper/OWF_paper_draft.md` §6.1c, `e26_board_s70_72.md` |
| Runs above α = 0.05 | 3 of 432 (0.7%); 0 of 432 at the safe operating point | `e28_rerun.md` |
| SOTA runs above α | TAO'26 130 / 126, Claxton'24 104 / 101, Xu'21 81 / 83 (of 144) → 56–90% | `e28_rerun.md`, criterion C3 |
| Navigation error | ours 12.6 / 14.0 m; Claxton 44.3 / 48.9 m; TAO 109.5 / 114.9 m → 3.5–8.7× | §6.1c, `e26_board_s70_72.md` |

Caveat to keep in mind for interviews: the holes are simulated (30% of 300 m map cells removed), except on NCLT, 4Seasons cross-scene and
VPR-Space. The external baselines were re-implemented from their papers, with thresholds tuned on labels as in the original works.
