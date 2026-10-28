# DIVE-VPR — reliability of visual place recognition (research repo)

| Path | What |
|---|---|
| `RESEARCH_LOG.md` | Honest experiment log (newest entry first). |
| `LITERATURE_GATE.md` | Novelty gate (Entry 11): why CRSG was dropped, what is still novel. |
| `PAPER_DRAFT.md`, `RESULTS.md` | Previous (CRSG) draft + tables — superseded framing, kept for numbers. |
| `handoff/` | Handoff notes (science / Kaggle ops / environment). |
| `nb15_src/` | NB15 descriptor-dump notebook (build: `python automation/build_nb.py out.ipynb ../nb15_src`). |
| `analysis/` | All experiments run locally on CPU from the dumps (`vprlib.py`, `exp*.py`, `run_all.py`, `figures.py`). |
| `automation/` | `build_nb.py`, `make_meta.py` (T4/RTX metadata), `run_kernel.py` (queue-aware runner), `vpr_extra.py` (MixVPR/CosPlace/NetVLAD/MegaLoc loaders), `md2pdf.py`. |

Legacy CCBF/CRSG notebooks (NB1–NB14), their sources and the old PDFs were removed from the working tree to keep
it small; they are preserved in git history at commit `96ced6c` (`git checkout 96ced6c -- <path>`).
