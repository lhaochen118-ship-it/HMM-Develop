# Reproducing the HMM / IA-HMM results

## 0. Environment
Python ≥3.10 with `numpy scipy scikit-learn matplotlib` (CPU only). Kaggle CLI ≥2.2 only to (re)download the
feature bank. GPU is needed only to regenerate descriptors (Kaggle T4 kernels in `kaggle/`).

## 1. Feature bank (cached descriptors, fp16, L2-normalised)
```bash
export HMMLOC_FB=/path/to/feature_bank          # default: session scratchpad path in hmmloc/data.py
for k in dive-vpr-nb15a-dump dive-vpr-nb15b-dump dive-vpr-nb15c-dump dive-vpr-nb15d-dump hmm-k01-nordseg hmm-k02-4s-stopgo; do
  kaggle kernels output nhatlong1103/$k -p $HMMLOC_FB/$k
done
```
(The kernels are private to the owner account; to regenerate: `kaggle/build_k01.py` + `kaggle/k01_nordseg`,
`kaggle/k02_4s_stopgo`; the nb15 dump notebooks are the owner's earlier kernels.)

## 2. Correctness gate (G0)
```bash
python3 tests/test_hmm_core.py        # brute-force path enumeration vs filter, mass conservation, edge cases
python3 tests/synth_ar1_ia.py         # [P] synthetic AR(1) pilot for the information-aware weight
```

## 3. Main experiments (each appends a row to research/registry/runs.jsonl and writes research/runs/<run_id>/)
| What | Command |
|---|---|
| HMM ladder (single, SeqSLAM, HMM τ/β/LLR) | `python3 -m hmmloc.exp.e01_ladder <nord|cmu|rc|nordseg1> <desc>` |
| IA-HMM full comparison (main table) | `python3 -m hmmloc.exp.e07_motionev <nord|nord-tw|cmu|rc|4s|nordseg1|nordseg1-tw> <desc> <seed>` |
| Information-aware β vs fixed β vs keyframes | `python3 -m hmmloc.exp.e02_infoaware <dataset> <desc> tau` |
| Off-map holes | `python3 -m hmmloc.exp.e04_offmap <desc> <seed>` |
| Failure taxonomy | `python3 -m hmmloc.exp.e05_failures <dataset> <desc>` |
| Fixed-lag smoothing | `python3 -m hmmloc.exp.e06_lag <dataset> <desc>` |
| Per-condition + coarse 6DoF | `python3 -m hmmloc.exp.e09_percond <rc|nord> <desc>` |
| Cross-dataset transfer | `python3 -m hmmloc.exp.e10_transfer <src> <tgt> <desc>` |
| Runtime | `python3 -m hmmloc.exp.e11_runtime` |
| Posterior-weighted pose | `python3 -m hmmloc.exp.e12_pose <rc|cmu> <desc>` |
Batch: `research/run_queue.sh <parallel> research/jobs_final7.txt`.
Descriptors: `netvlad cosplace salad megaloc` (+ `mixvpr dinov2` for nord/rc/cmu).

## 4. Tables and figures (generated, never hand-typed)
```bash
python3 research/make_tables.py > research/reports/RESULTS_TABLES.md
python3 research/make_figure.py
```
