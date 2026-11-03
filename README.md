# HMM sequence-based visual localization — idea 2 (branch `hmm-2nd-idea`)

**Start here:** `handoff/05_NEW_CHAT_GUIDE.md`. This branch searches for a NEW A\*-level solution to sequence-based visual localization
with an HMM on monocular image sequences (foundation: Sattler et al., CVPR 2018). Idea 1 (counterfactual map surgery, branch
`hmm-navigation-5`) is the baseline to beat: `handoff/07_IDEA1_SUMMARY.md`, numbers in `analysis/results/baselines_idea1/`.

| Path | What |
|---|---|
| `handoff/` | 00 index, 01 scientific findings, 02 engineering / Kaggle ops (§00 resource-optimisation rules), 03 status, 04 research workflow, 05 new-chat guide, 07 idea-1 summary, ENVIRONMENT_SUMMARY (md + pdf) |
| `analysis/` | shared platform: loaders (`vprlib.py`), holes + odometry + HMM + metrics (`nav_demo.py`), evaluation (`nav_rules.py`, `oc_summary.py`, `e26_summary.py`, `position_audit.py`), 2026 baselines (`tao.py`, `trail.py`, `safevpr26*.py`, `vlm_*.py`) |
| `automation/` | Kaggle: `make_eval_kernel.py`, `fanout.py`, `central_monitor.py`, `e37_collect.py`, `publish_dataset.py`, dump builders, `md2pdf.py` |
| `nb15_src/` | descriptor-extraction notebook sources |
| `literature/`, `LITERATURE_GATE.md` | related work and novelty gates (new gates from Gate 17) |
| `RESEARCH_LOG.md` | log of idea 2 (idea 1: `history/RESEARCH_LOG_idea1.md`) |

Removed idea-1 code and reports can be restored with `git checkout hmm-navigation-5 -- <path>`.
