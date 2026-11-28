#!/usr/bin/env python3
"""Reproduce SeqVLAD's published MSLS number with the OFFICIAL protocol (vandal-vpr/vg-transformers build_sequences):
centred windows of L consecutive frames (stride 1) built identically for queries and database, inside each Mapillary
sequence (rows stored in sequence order; a sequence = same date, consecutive rows < 40 m apart), descriptor =
L2(intra-norm(sum of per-frame VLAD residuals)) (exact for SeqVLAD), positives = any query frame within 25 m of any
database frame of the window, queries without positives excluded. Cities cph + sf (the papers' MSLS test).
Published (SeqVLAD RA-L 2022 Tab. II / JIST Tab. I): SeqVLAD CCT384 24576-D, MSLS->MSLS R@1 = 89.4 (L = 5).
Usage: repro_seqvlad_msls.py [L ...]"""
import sys, os
import numpy as np
from scipy.spatial import cKDTree

FB = os.environ.get("HMMLOC_FB", "/tmp/claude-0/-home-user-HMM-Develop/865660f3-ecf6-5c6c-b462-db1884ef1e8f/scratchpad/fb")
D = os.path.join(FB, "hmm-k12-seqvlad", "dump")


def vlad(X):
    X = X.reshape(len(X), 64, 384).astype(np.float32); X /= np.linalg.norm(X, axis=2, keepdims=True) + 1e-12
    X = X.reshape(len(X), -1); return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)


def groups(C, date, gap=40.0):
    g = np.zeros(len(C), int)
    for t in range(1, len(C)):
        g[t] = g[t - 1] + int(date[t] != date[t - 1] or np.linalg.norm(C[t] - C[t - 1]) > gap)
    return g


def windows(g, L):
    out = []
    for gid in np.unique(g):
        ix = np.where(g == gid)[0]
        for c in range(len(ix) - L + 1):               # every full window of L consecutive frames (stride 1)
            out.append(ix[c:c + L])
    return np.array(out)


def run(L):
    hit = n = 0
    for city in ("cph", "sf"):
        z = np.load(os.path.join(D, "meta", f"msls_{city}.npz"), allow_pickle=True)
        Vd = np.load(os.path.join(D, "seqvlad_raw", f"msls_{city}_db.npy"), mmap_mode="r")
        Vq = np.load(os.path.join(D, "seqvlad_raw", f"msls_{city}_q.npy"), mmap_mode="r")
        wd = windows(groups(z["db_C"], z["db_date"]), L); wq = windows(groups(z["q_C"], z["q_date"]), L)
        Dd = np.concatenate([vlad(np.add.reduce([np.asarray(Vd[w[:, k]], np.float32) for k in range(L)])) for w in np.array_split(wd, max(1, len(wd) // 2000))])
        tree = cKDTree(z["db_C"]); frame_pos = tree.query_ball_point(z["q_C"], r=25.0)
        db_win_of_frame = {}
        for wi, w in enumerate(wd):
            for f in w: db_win_of_frame.setdefault(int(f), set()).add(wi)
        for blk in np.array_split(np.arange(len(wq)), max(1, len(wq) // 2000)):
            Q = vlad(np.add.reduce([np.asarray(Vq[wq[blk, k]], np.float32) for k in range(L)]))
            top = (Q @ Dd.T).argmax(1)
            for i, qi in enumerate(blk):
                pos = set()
                for f in wq[qi]:
                    for j in frame_pos[f]: pos |= db_win_of_frame.get(int(j), set())
                if pos:
                    n += 1; hit += int(top[i] in pos)
        print(f"  {city}: db windows {len(wd)}, query windows {len(wq)}", flush=True)
    print(f"SeqVLAD L={L}: R@1 = {hit / n:.4f} over {n} query sequences with a positive", flush=True)


for L in [int(a) for a in sys.argv[1:]] or [5, 1]:
    run(L)
