#!/usr/bin/env python3
"""Turn the k12 SeqVLAD dumps (per-frame UNNORMALISED VLAD residual sums V_f, 64x384, fp16) into the feature bank:
  hmm-k12-seqvlad/dump/seqvlad_raw/<name>.npy  = V_f (unchanged, for exact sequence descriptors L2(intra(sum_f V_f)))
  hmm-k12-seqvlad/dump/seqvlad/<name>.npy      = L2(intra-norm(V_f)) per frame (= SeqVLAD with L=1), fp16
  hmm-k12-seqvlad/dump/meta/*                  = metadata copied from the kernels
Usage: prep_seqvlad.py <k12 output dir> [...]    (dirs contain dump/seqvlad/*.npy and dump/meta/*)"""
import sys, os, glob, shutil
import numpy as np

FB = os.environ.get("HMMLOC_FB", "/tmp/claude-0/-home-user-HMM-Develop/865660f3-ecf6-5c6c-b462-db1884ef1e8f/scratchpad/fb")
OUT = os.path.join(FB, "hmm-k12-seqvlad", "dump")
K, D = 64, 384


def intra_l2(V):
    V = V.astype(np.float32).reshape(len(V), K, D)
    V /= np.linalg.norm(V, axis=2, keepdims=True) + 1e-12
    V = V.reshape(len(V), K * D)
    return V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-12)


for src in sys.argv[1:]:
    for sub in ("seqvlad", "seqvlad_raw", "meta"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    for m in glob.glob(os.path.join(src, "dump", "meta", "*")):
        shutil.copy(m, os.path.join(OUT, "meta"))
    for f in sorted(glob.glob(os.path.join(src, "dump", "seqvlad", "*.npy"))):
        name = os.path.basename(f); raw = os.path.join(OUT, "seqvlad_raw", name)
        shutil.move(f, raw)
        A = np.load(raw, mmap_mode="r"); out = np.empty(A.shape, np.float16)
        for s in range(0, len(A), 2000):
            out[s:s + 2000] = intra_l2(np.asarray(A[s:s + 2000])).astype(np.float16)
        assert np.isfinite(out.astype(np.float32)).all(), name
        np.save(os.path.join(OUT, "seqvlad", name), out)
        print(f"{name}: {A.shape} -> normalised", flush=True)
