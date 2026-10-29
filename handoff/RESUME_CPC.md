# Resume note: CPC-HMM work (2026-10-29)

How to continue if the session or container was restarted.

## State

- **Main method:** certified sequential localization (`analysis/cert_seq.py`). Report: `paper/BAO_CAO_CertSeq.*`.
- **HMM-fix module CPC-HMM:**
  - code: `analysis/hmm_fix.py` (`fac_anchT_mix` = CPC-HMM; `cpc_p*`, `cpc_pout*`, `cpc_pred` = theory checks);
  - navigation rule: `analysis/nav_demo.py`;
  - theory: `paper/cpc_theory.md`;
  - novelty: `LITERATURE_GATE.md`, Gate 7.
- **Boreas findings:**
  1. A wheel-pulse counter discontinuity (one 8.7 km step in 4 sequences) broke the place chain. Fixed in
     `cert_seq.odometry_wheel`.
  2. Off-map fixes come mainly from the EXIT LAG of the presence chain, ≈ log((1−p_out)/p_out)/|E0 log LR|, not from false
     onsets. Remedy: asymmetric switching with p_in = 0.01 (keeps ARL0 ≥ 99) and a larger p_out; being evaluated.
  3. The ANCH e-value e_R is sub-uniform off-map on Boreas and 4S countryside. A noise-free odometry null did NOT fix it,
     so the cause is coherent aliasing; still open.

## Runs on Kaggle (work dirs in the session scratchpad `runs/`)

- **Active runs:** listed in `runs/active_runs.txt`.
- **After a container restart:**

  ```bash
  python3 automation/resume.py <scratchpad>/runs
  ```

  It re-attaches every unfinished kernel and copies its results into `analysis/results`.
- **If the scratchpad itself is lost:** kernels are named `<account>/hmm-<run>-<k>`. Pull an output with
  `kaggle kernels output <id> -p <dir>`, using the token in `~/.kaggle/tok_<account>`.

## Next

1. Aggregate `nav_*` with the `CPC-HMM p_out=*` rules (runs `navF`, `navFc`) and `hmmfix_*` (`fix7`).
2. Choose ONE p_out for all datasets, from the exit-lag formula, and compare with Xu'21 on all 6 navigation datasets.
3. Report ARL0 vs (1−p_in)/p_in and the re-entry delay vs log((1−p)/p)/KL1 (`KL` in `hmmfix_*` runs).
