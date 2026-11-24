# history/ — earlier research directions kept on `main`

Since 2026-11-24 the repo has one working branch, `main` (it holds all of `hmm-2nd-idea`). The old branches were
deleted; every commit stays reachable through the archive tags below, so any old file can still be restored with
`git checkout <tag> -- <path>` (or read with `git show <tag>:<path>`).

| Old branch | Archive tag | What it was |
|---|---|---|
| `claude/elegant-brown-xvnecd` | `archive/elegant-brown` | CCBF/CRSG start, exp10 (contained in every later branch) |
| `claude/selfcal-aa` | `archive/selfcal-aa` | SelfCal-AA, stable label-free VPR reliability test + paper |
| `claude/selfcal-seq` | `archive/selfcal-seq` | SelfCal experimental extensions (Gap v3, localisation demo); **8 commits only here** |
| `hmm-navigation` | `archive/hmm-navigation` | start of HMM sequence-based localization (idea 1) |
| `hmm-navigation-2` | `archive/qcc` | idea 1 + the unrelated Kaggle QCC project (`qcc/`, last state) |
| `hmm-navigation-3`, `-4` | `archive/hmm-navigation-3`, `archive/hmm-navigation-4` | idea 1, intermediate |
| `hmm-navigation-5` | `archive/idea1-final` | idea 1 final state (Entries 18–39, CST-JS / SH); **4 commits only here** |
| `hmm-2nd-idea` | `archive/hmm-2nd-idea` | idea 2 (OWF, LACUNA); merged into `main` |

Removed idea-1 code and reports: `git checkout archive/idea1-final -- <path>`.
Removed SelfCal code, results and paper: `git checkout archive/selfcal-aa -- <path>` (stable) or `archive/selfcal-seq`.

## Files here

| Path | What |
|---|---|
| `RESEARCH_LOG_idea1.md` | full log of idea 1 (Entries 18–39 + the SelfCal-era Entries before it), verbatim from `hmm-navigation-5` incl. the Entry 39 execution / results / D39 diagnostics |
| `01_SCIENTIFIC_FINDINGS_idea1_and_idea2-early.md` | findings document of idea 1 and early idea 2 |
| `RESEARCH_LOG_idea2_entries01-22.md` | idea 2 Entries 1–22 (the current log keeps 23+) |
| `idea1_entry39/` | the Entry 39 pieces that were only on `hmm-navigation-5`: `e39_tables.md`, `diag39.log`, `e39_diag.py`. The raw e39 results (`audit39.json`, `diag39*.json`, `oc_e39.tgz`) are byte-identical in `analysis/results/baselines_idea1/e39/` (where the log says `analysis/results/e39/`, read `analysis/results/baselines_idea1/e39/`) |
| `selfcal_seq/` | the SelfCal results that were only on `claude/selfcal-seq` |
| `selfcal_seq/results/deploy_{cmu,nord}_<descriptor>_s<seed>.json` | localisation demo on a map with holes (exp12), 6 descriptors x 2 datasets x 10 seeds = 120 runs (paper §6.9) |
| `selfcal_seq/results/eval_msls_<descriptor>.json` | v3 eval_all rerun on MSLS with SelfCal-AA + SelfCal-Gap rows |
| `selfcal_seq/paper/selfcal_paper.md` | the most complete SelfCal paper text (abstract with Gap, §6.4 Gap paragraph, §6.9 over 10 seeds) |
| `selfcal_seq/RESEARCH_LOG_selfcal.md` | SelfCal research log (Entries 11–17 with the v3 result; Entries 0–10 condensed) |
| `selfcal_seq/exp12_deploy.py` | script of the localisation demo (needs the SelfCal modules: restore them from `archive/selfcal-seq`) |
