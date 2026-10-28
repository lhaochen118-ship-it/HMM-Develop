# Handoff — SelfCal (for a FRESH chat window)

*Updated 2026-10-28 after Entry 13. Supersedes the earlier CCBF/CRSG version of this file (git history). Read this,
then `RESEARCH_LOG.md` Entries 11–14, `LITERATURE_GATE.md` and `RESULTS.md`. The paper is `paper/selfcal_paper.md`.*

Repo `lhaochen118-ship-it/hmm-develop`, branch **`claude/elegant-brown-xvnecd`** (all work lives here; no PRs).
Kaggle user **`nhatlong1103`**, token in `~/.kaggle/access_token` (re-create it from the user's message if the
container is new; do not write it into shell rc files).

## 1. Where the project is

- **CRSG is dropped.** Gate 1 (`LITERATURE_GATE.md`) found it pre-empted (PA ratio, L2/RS-SD-SU, integrity MLPs,
  SAFEVPR). It is not enough for A/A*.
- **New contribution: SelfCal, "your map is its own calibration set".** It controls the off-map false-accept rate
  (FAR) of VPR without labels and under appearance shift. It has four parts:
  1. **Map pseudo-queries.** Each map image is queried against the map with its own 300 m block removed
     (leave-one-block-out), so it is off-map by construction. This gives a free labelled null.
  2. **Affine-invariant statistic** `z_far = (s1 − μ_far)/σ_far` over the maxima of 10 m cells farther than 25 m
     from the top-1, computed after **centring the descriptors on the map mean** (reduces hubness).
  3. **Combined split-conformal p-value**: `combined_p` (min of conformal p's of max-sim and z_far, re-calibrated by
     leave-one-out null ranks).
  4. **SelfCal-AA** (aliasing-aware): accept iff `max(p_comb, p_zgap) ≤ α`, where
     `z_gap = (s1 − best far region)/σ_far`.
- **Theory (paper §5):** T1 validity under exchangeability, T2 stochastic dominance ⇒ conservative, T3 FAR − α ≤ Δ⁺
  (one-sided KS), T4 combination validity, T5 BH FDR (PRDS).
- **Gate 2 (`LITERATURE_GATE.md`): novel.** Checked against RSF (Zaffar'25), map-density (Hussaini'26),
  Trinh & Lyons, Schubert, meta-recognition, SAFEVPR and Quantile Transfer.

## 2. Headline results (α = 0.05; 6 descriptors × 3 datasets = 18 settings, 138 deployment conditions)

| method | labels | violating cond. | settings ≥1 viol. | mean TPR |
|---|---|---|---|---|
| **SelfCal-AA** | none | **0/138** | **0/18** | 0.676 (median aliasing-accept 0.008, max worst FAR 0.040) |
| SelfCal | none | 0/138 | 0/18 | 0.718 (Oracle 0.721) |
| Conformal LOCO (SAFEVPR protocol) | other cond. | 38/138 | 18/18 | — |
| Quantile Transfer | benign | 64/138 | — | — |
| Threshold benign→all / CRSG | benign | 25/138 each | — | — |

Robustness: Nordland with winter as the map passes 0/3. A 25 % RobotCar map gives FAR 0 and TPR 0.994. Ablations
barely move the result, but centring is essential on Nordland (TPR 0.754 vs 0.329). Δ⁺ for the map null is at most
0.052, against up to 0.255 for a labelled benign null. BH on the AA p-values keeps Nordland gross FDR at or below
0.030.

**Known weaknesses (stated in the paper's Limitations):**
- DINOv2 CLS+mean stays valid but is conservative (TPR 0.06–0.33 vs oracle 0.39–0.70). Dual centring only lifts
  this from 0.33 to 0.41, so it was not adopted.
- Label-free confidence has poor ECE on Nordland (~0.14).
- RobotCar test GT is withheld, so the evaluation uses the official map, official thresholds and the public train
  split.
- BoQ was not available: GitHub is blocked and there is no mirror. MixVPR, CosPlace, NetVLAD, MegaLoc and DINOv2 were
  added instead.

## 3. Code map

| path | role |
|---|---|
| `nb15_src/` | Kaggle descriptor-dump notebook. `40_run.src` runs every descriptor in one image pass and writes fp16 `.npy` plus meta npz. The kernel dir needs a generated `15_sel.src` with `DUMP = [...]` and `DESCRIPTORS = [...]`. Build with `python automation/build_nb.py out.ipynb ../nb15_src`. |
| `automation/run_kernel.py` | `run_kernel.py <kernel_dir> <out_dir> [stall=600] [max_restarts=4] [hard=10800] [silent_max=0] [--attach]`. Only a kernel QUEUED for more than 10 min is cancelled (`kaggle kernels delete -y`) and re-pushed. Silent-restart is OFF because Kaggle hides RUNNING logs. |
| `automation/make_meta.py` | `kernel-metadata.json` (tier `t4` default, `rtx` for RTX PRO 6000). |
| `automation/vpr_extra.py` | Offline builders for MixVPR, CosPlace, NetVLAD and MegaLoc (weights in dataset `nhatlong1103/vpr-descriptor-weights`). |
| `analysis/vprlib.py` | Episode loaders (RobotCar, CMU merged, Nordland with `ref=`), metrics, BH, nearest-map distance. |
| `analysis/selfcal.py` | Core method: `query_stats`, `lobo_stats`, `map_null`, `conformal_p`, `combined_p`, `SelfCalTest` = the adopted decision rule (Mondrian strata by sd_far, B=10, raw-similarity gate 0.8; `strata=1, gate=1` = original AA), plus the online class `SelfCalAA` (18 s offline for the 6954-image RobotCar map, ~1 ms/query batched; matches the batch statistics to 4e-6). |
| `analysis/sc_eval.py` | `CFG` per dataset (cell, excl, k, block, off_d, in_d, tol). |
| `analysis/eval_all.py` | Main comparison (all baselines). Writes `analysis/results/eval_<ds>_<desc>.json` and caches in `analysis/cache/` (git-ignored). |
| `analysis/exp3..exp8` | FDR/confidence, aliasing, ablation, dominance Δ⁺, map size, dual centring. |
| `analysis/summarize.py`, `figures2.py` | Summary tables, paper figures. |
| `paper/` | `selfcal_paper.md` (source text). `build_tables.py` produces `tables.md`. `build_paper.py` produces `SelfCal_paper_full.md` and `.pdf`. |

**Reproduce:** evaluations run on Kaggle: `automation/make_eval_kernel.py <dir> <slug> "eval_all.py <ds> <desc>;..." [--gpu] [--acc2]`,
then `automation/run_kernel.py <dir> <out>`. Copy `<out>/results/*.json` to `analysis/results/` and run `python3 paper/build_paper.py`.

## 4. Data (descriptor dumps, ~2.9 GB, NOT in git)

The dumps are outputs of four Kaggle kernels. They were run on T4 and their datasets are `nhatlong1103/bundle`,
`robotcar-seasons-v2`, `nordland-full-47-6gb`, `vpr-descriptor-weights` and the CMU dataset.

| kernel | content | local path used last session (scratchpad, ephemeral) |
|---|---|---|
| `nhatlong1103/dive-vpr-nb15a-dump` | SALAD for RobotCar and Nordland | `out15a/dump` |
| `nhatlong1103/dive-vpr-nb15b-dump` | SALAD for CMU | `out15b/dump` |
| `nhatlong1103/dive-vpr-nb15c-dump` | DINOv2, NetVLAD, CosPlace, MixVPR and MegaLoc for RobotCar and Nordland | `out15c/dump` |
| `nhatlong1103/dive-vpr-nb15d-dump` | the same five descriptors for CMU | `out15d/dump` |

Fetch a dump in a new container with `kaggle kernels output nhatlong1103/dive-vpr-nb15a-dump -p <dir>`. Do not push a
new version under these slugs, because that replaces their outputs.

## 5. Next steps (if continuing toward A*)

1. **Power for weak descriptors.** DINOv2 is the one setting where SelfCal is conservative. Candidates are a
   per-descriptor statistic choice selected on the map null only, or sequential evidence (combining p-values over
   consecutive frames, which stays valid by the T4 logic).
2. **More datasets.** A fourth geo-tagged benchmark with GPS (MSLS val, Pitts30k or SF-XL) needs only the
   leave-block-out protocol, no new labels. 4Seasons poses are now on Kaggle (`nhatlong1103/4seasons-poses`, pairs with `nhatlong1103/4seasons`).
3. **Paper polish.** Turn the markdown into a LaTeX venue template and add a qualitative figure (accepted vs rejected
   aliasing examples).

## 6. Ops reminders (details in `handoff/02_ENGINEERING_OPS_NOTES.md`)

- A T4 kernel starts at once and two can run concurrently. Use RTX only for large runs.
- Datasets mount at `/kaggle/input/datasets/<owner>/<slug>`.
- Do not run downloaded third-party code locally, because the sandbox classifier blocks it. Run it inside Kaggle
  instead.
- Restarting the container loses background waits. Re-attach with `run_kernel.py ... --attach`.
