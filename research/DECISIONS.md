# DECISIONS

| ID | Date | Decision | Evidence / reason |
|---|---|---|---|
| D01 | 2026-11-27 | Reuse the existing 6-descriptor feature bank (nb15a–d) instead of re-extracting; GPU only for missing video-rate Nordland (k01) | saves ~6–8 T4-hours; dumps pass G1 sanity |
| D02 | 2026-11-27 | All HMM inference on CPU from cached similarities | 4500–6954-node maps run in seconds per sequence set |
| D03 | 2026-11-27 | CCBF (M4) parked; HMM-centred method = IA-HMM (M1+M2+M3) | legacy τ per condition nearly identical [R]; user constraint "HMM is the centre" |
| D04 | 2026-11-27 | SeqSLAM tuned on calibration (L, enhancement) — enhancement off on dense maps | A21 |
| D05 | 2026-11-27 | Positives for RobotCar/CMU = 5 m & 30°; fine 6DoF thresholds reported separately (M5 later) | standard coarse threshold; HMM operates at place level |
| D06 | 2026-11-27 | Real stop-and-go/variable-speed evidence from 4Seasons (k02–k04) instead of only synthetic time-warp | user goal "high results on real data"; GNSS keyframes limit true stops except old_town |
| D07 | 2026-11-27 | Model selection among {fixed kernel, LV, LV+ME, LV+ME+IA} by calibration NLL is part of the method (no test info) | F07/F16: latent velocity is regime-dependent |
| D08 | 2026-11-27 | M5 test (k05): RobotCar, k=3 candidates single vs HMM, SuperPoint+LightGlue+PnP on the dataset SfM model, same budget | STATE next task 1; isolates candidate quality from matcher |
| D09 | 2026-11-27 | Only Kaggle account nhatlong1103 used; other accounts not touched | Kaggle ToS (one account per person) and Ops Plan §2 |
| D10 | 2026-11-28 | Use the other lab Kaggle accounts for parallel GPU jobs when needed | user confirmed (28/11) they belong to lab members who allow it; tokens stay in scratchpad only |
| D11 | 2026-11-28 | JIST downloaded with internet-enabled kernel (user-approved); evaluated at its default 480×640 | 384×384 first pass superseded (A28) |
| D12 | 2026-11-28 | L4x4 policy: 4 independent per-GPU workers + dynamic chunk queue (no DDP for inference); batch = smallest reaching 97% of peak throughput under 90% VRAM; HMM stays on CPU sessions; competition grant only after user confirms its terms allow the job | research/reports/HUONG_DAN_L4x4.md; Ops Plan v1.3 §3; hmm-2nd-idea ops notes |
| D13 | 2026-11-28 | User confirmed the gemma-4-developer-agent grant is allowed for our jobs; only 5 accounts used: nhatlong1103, quynhtran35, yuan1103, phatle1578, huyenco | user message 28/11; all 19 lab accounts have entered the competition (checked read-only) |
| D14 | 2026-11-28 | GPU work packed per guide D12: one L4x4 session for k11 (4 scenes), one for k09 (7 chunks), 3 workers/GPU (RANSAC/PnP is CPU-bound), dynamic unit queue; k12 SeqVLAD-cmu (single process) on T4; smoke on T4 first | research/reports/HUONG_DAN_L4x4.md §3, §9 |
