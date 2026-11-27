# AGENTS.md — read me first (AI research/coding agents)

1. Read `research/STATE.md` (phase, gate, next 3 tasks, blockers), then `research/MASTER_PLAN.md` (v3, the
   operative plan; it extends the user's *Master Research Plan v2.0* and *Operations Plan v1.3* PDFs).
2. Evidence policy: every number in a report must come from `research/registry/runs.jsonl` (run_id) or a cited
   source. Levels: [V] verified, [S] supported (dev/limited), [P] pilot/synthetic, [R] reported legacy,
   [H] hypothesis, [L] literature.  Never tune on test sequences; hyper-parameters are chosen on calibration
   sequences only (see `research/PROTOCOL.md`).
3. Code: `hmmloc/` is the source of truth (legacy notebooks `nb_src/`, `nb2_src/`, `diag_src/` are kept
   unchanged for audit). Run `python3 tests/test_hmm_core.py` before any experiment (Gate G0).
4. GPU only for descriptor extraction (Kaggle T4, kernels in `kaggle/`). All HMM work runs on CPU from the
   cached feature bank. Secrets (Kaggle tokens) are never written to the repo.
5. At the end of a work session: update STATE.md, FINDINGS.md, DECISIONS.md, ISSUES.md; commit + push.
