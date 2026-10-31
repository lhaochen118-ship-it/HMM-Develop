# HMM-navigation — sequence-based visual localization with a monocular camera (research repo)

**Start here:** `handoff/05_NEW_CHAT_GUIDE.md` (reading order, code map, next steps; index in `handoff/00_READ_ME_FIRST.md`). Latest branch: `hmm-navigation-3`. Current method: CPC-SC+CS (`analysis/cpc_sc.py`); report `paper/BAO_CAO_PhanBien.pdf`.

| Path | What |
|---|---|
| `handoff/` | `00_READ_ME_FIRST.md` (guide + next tasks), `02_ENGINEERING_OPS_NOTES` (Kaggle ops), `04_RESEARCH_WORKFLOW` (process; original prompt in `RESEARCH_WORKFLOW_original.pdf`), `ENVIRONMENT_SUMMARY` (datasets, dumps, accounts). md sources with PDFs alongside. |
| `analysis/` | `vprlib.py` (dump loaders, metrics, `frame_order` for sequences), `selfcal.py` + `sc_eval.py` (label-free map-calibrated off-map test and per-dataset config, reusable as an HMM component). `results/` is empty for the new direction. |
| `automation/` | Kaggle: `fanout.py` (all accounts' GPU slots), `make_eval_kernel.py`, `run_kernel.py`; dump notebooks: `build_nb.py`, `make_meta.py`, `vpr_extra.py`; `md2pdf.py`. |
| `nb15_src/` | Descriptor-dump notebook sources (data public: Kaggle `nhatlong1103/vpr-descriptor-dumps`). |
| `literature/` | Paper-only review of visual localization (`VISUAL_LOCALIZATION_REVIEW.md/.pdf`). |
| `LITERATURE_GATE.md`, `RESEARCH_LOG.md` | Novelty gates 1–5 and experiment log of the earlier directions (history and lessons). |

Earlier work is kept on other branches: SelfCal paper, results and experiments on `claude/selfcal-aa`; sequence SelfCal
and the Kalman localisation demo (`exp11`, `exp12`) on `claude/selfcal-seq`; the first HMM/CCBF notebooks and docs on
`main`. Restore any file with `git checkout <branch> -- <path>`.
