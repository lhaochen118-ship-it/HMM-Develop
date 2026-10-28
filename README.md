# DIVE-VPR — reliability of visual place recognition (research repo)

| Path | What |
|---|---|
| `RESEARCH_LOG.md` | Honest experiment log (newest entry first). |
| `LITERATURE_GATE.md` | Novelty gates 1–4: why CRSG was dropped, why SelfCal is still novel. |
| `literature/` | Paper-only review of visual localization (`VISUAL_LOCALIZATION_REVIEW.md/.pdf`, HMM/sequence VPR in §6). |
| `handoff/` | Handoff notes; start with `03_HANDOFF_NEW_CHAT.md` (current SelfCal state). |
| `nb15_src/` | NB15 descriptor-dump notebook (build: `python automation/build_nb.py out.ipynb ../nb15_src`). |
| `paper/` | SelfCal paper: `selfcal_paper.md` (source), `build_tables.py` → `tables.md`, `build_paper.py` → `SelfCal_paper_full.pdf`. |
| `analysis/` | Method (`selfcal.py`: `SelfCalTest`, online `SelfCalAA`), loaders (`vprlib.py`), main comparison (`eval_all.py`), studies `exp3`/`exp5`–`exp7`/`exp9`/`exp10`, `figures2.py`. All heavy runs go to Kaggle via `automation/make_eval_kernel.py`. |
| `automation/` | `build_nb.py`, `make_meta.py` (T4/RTX metadata), `run_kernel.py` (queue-aware runner), `make_eval_kernel.py` (Kaggle CPU/GPU evaluation kernels, 3 accounts), `vpr_extra.py` (MixVPR/CosPlace/NetVLAD/MegaLoc loaders), `md2pdf.py`. |

Legacy CCBF/CRSG notebooks (NB1–NB14), old drafts, old handoffs and exploratory scripts were removed from the working tree to keep
it small; they are preserved in git history at commit `96ced6c` (`git checkout 96ced6c -- <path>`).
