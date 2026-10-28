# DIVE-VPR — reliability of visual place recognition (research repo)

**Start here:** `handoff/00_READ_ME_FIRST.md` (reading order + next task). Stable branch: `claude/selfcal-aa`;
experimental extensions (sequence SelfCal, localisation demo): `claude/selfcal-seq`.

| Path | What |
|---|---|
| `handoff/` | `00_READ_ME_FIRST.md`; PDFs `01_SCIENTIFIC_FINDINGS`, `02_ENGINEERING_OPS_NOTES`, `03_HANDOFF_NEW_CHAT`, `04_RESEARCH_WORKFLOW`, `ENVIRONMENT_SUMMARY` (md sources alongside). |
| `RESEARCH_LOG.md` | Experiment log, newest first (Entries 11–17; 0–10 condensed). |
| `LITERATURE_GATE.md` | Novelty gates 1–4 (Gate 5 = next task). |
| `literature/` | Paper-only review of visual localization (`VISUAL_LOCALIZATION_REVIEW.md/.pdf`). |
| `paper/` | `selfcal_paper.md` (source), `build_tables.py` → `tables.md`, `build_paper.py` → `SelfCal_paper_full.pdf`; `SelfCal_paper_AA_only.pdf` = AA-only version. |
| `analysis/` | Method `selfcal.py` (`SelfCalTest` modes aa/gap, online `SelfCalAA`), loaders `vprlib.py`, configs `sc_eval.py`, main comparison `eval_all.py`, studies `exp3`/`exp5`–`exp7`/`exp9`/`exp10`, figures `figures2.py`; results in `results/` (Gap rows in `results/gap/`). |
| `automation/` | Kaggle: `fanout.py` (all accounts' GPU slots), `make_eval_kernel.py`, `run_kernel.py`; dump notebooks: `build_nb.py`, `make_meta.py`, `vpr_extra.py`; `md2pdf.py`. |
| `nb15_src/` | Descriptor-dump notebook sources (data now public: Kaggle `nhatlong1103/vpr-descriptor-dumps`). |

Legacy CCBF/CRSG notebooks (NB1–NB14), old drafts, old handoffs and exploratory scripts were removed from the working tree to keep
it small; they are preserved in git history at commit `96ced6c` (`git checkout 96ced6c -- <path>`).
