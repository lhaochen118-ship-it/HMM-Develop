# DECISIONS

| ID | Date | Decision | Evidence / reason |
|---|---|---|---|
| D01 | 2026-11-27 | Reuse the existing 6-descriptor feature bank (nb15a–d) instead of re-extracting; GPU only for missing video-rate Nordland (k01) | saves ~6–8 T4-hours; dumps pass G1 sanity |
| D02 | 2026-11-27 | All HMM inference on CPU from cached similarities | 4500–6954-node maps run in seconds per sequence set |
| D03 | 2026-11-27 | CCBF (M4) parked; HMM-centred method = IA-HMM (M1+M2+M3) | legacy τ per condition nearly identical [R]; user constraint "HMM is the centre" |
| D04 | 2026-11-27 | SeqSLAM tuned on calibration (L, enhancement) — enhancement off on dense maps | A21 |
| D05 | 2026-11-27 | Positives for RobotCar/CMU = 5 m & 30°; fine 6DoF thresholds reported separately (M5 later) | standard coarse threshold; HMM operates at place level |
