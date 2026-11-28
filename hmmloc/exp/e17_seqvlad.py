"""B11 — Learned sequence baseline SeqVLAD (Mereu et al., RA-L 2022; CCT384+SeqVLAD, MSLS-trained) under PROTOCOL v1.
SeqVLAD sequence descriptor computed EXACTLY offline from the k12 per-frame unnormalised VLAD residual sums V_f:
    d_seq = L2( intra-norm( sum_{f in window} V_f ) )   (one VLAD over all tokens of all frames of the window).
Per-frame descriptor (single image / HMM emission) = the same with a window of one frame.
Query sequences are CAUSAL (last L frames of the same sequence); database sequences end at map node j with stride k
(nodes j-(L-1)k .. j). L ∈ {3,5,10} and k ∈ {1,2,3,5} selected on CALIBRATION R@1 (fair budget, like SeqSLAM).
Usage: e17_seqvlad <dataset>"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run
from .. import baselines, metrics

DS = sys.argv[1]; P = None
t00 = time.time(); B = Bench(DS, "seqvlad")
from .bench import load as _load
RAW = {}
for ep, epr in zip(B.eps, _load(DS, "seqvlad_raw")):      # raw residual sums, same loader -> same row order (no Bench/sim)
    assert len(epr.R) == ep.M and len(epr.Q) == ep.T, (ep.name, epr.R.shape, epr.Q.shape)
    RAW[id(ep)] = epr
KC, DC = 64, 384

def _vlad(X):
    X = X.reshape(len(X), KC, DC); X /= np.linalg.norm(X, axis=2, keepdims=True) + 1e-12
    X = X.reshape(len(X), KC * DC); return (X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)).astype(np.float32)

def seqvlad(F, idx_lists):
    L = max(len(ix) for ix in idx_lists); out = np.empty((len(idx_lists), F.shape[1]), np.float32)
    for s in range(0, len(idx_lists), 1024):
        blk = idx_lists[s:s + 1024]; acc = np.zeros((len(blk), F.shape[1]), np.float32)
        for o in range(L):
            sel = np.array([ix[o] if o < len(ix) else -1 for ix in blk]); ok = sel >= 0
            acc[ok] += F[sel[ok]].astype(np.float32)
        out[s:s + 1024] = _vlad(acc)
    return out

def jist_scores(ep, rows, L, k):
    er = RAW[id(ep)]
    M = ep.M; db_idx = [np.clip(np.arange(j - (L - 1) * k, j + 1, k), 0, M - 1) for j in range(M)]
    Dseq = seqvlad(er.R, db_idx)
    seq = ep.seq[rows]; q_idx = []
    for i in range(len(rows)):
        lo = i
        while lo > 0 and i - lo < L - 1 and seq[lo - 1] == seq[i]: lo -= 1
        q_idx.append(rows[lo:i + 1])
    Qseq = seqvlad(er.Q, q_idx)
    return Qseq @ Dseq.T

def r1(split, L, k):
    acc = []
    for ep, rows in B.split[split]:
        S = jist_scores(ep, rows, L, k); P_ = ep.pos[rows]; h = P_.any(1)
        acc.append(P_[np.arange(len(rows)), S.argmax(1)][h])
    return float(np.concatenate(acc).mean())

best = max(((r1("calib", L, k), L, k) for L, k in itertools.product((3, 5, 10), (1, 2, 3, 5))), key=lambda x: x[0])
print(f"[{DS}/seqvlad] selected L={best[1]} k={best[2]} (calib R@1 {best[0]:.3f})", flush=True)
RES, PER = {}, {}
RES["single_seqvlad"], PER["single_seqvlad"] = B.evaluate([baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split["test"]])
from .. import emission as _em
SC = {sp: [jist_scores(ep, rows, best[1], best[2]) for ep, rows in B.split[sp]] for sp in ("calib", "test")}
tau_s, _ = _em.fit_temperature_multi([(S, ep.pos[rows]) for S, (ep, rows) in zip(SC["calib"], B.split["calib"])])
posts = []                                              # sequence posterior with ITS OWN calibrated temperature
for S in SC["test"]:
    z = S / tau_s; z -= z.max(1, keepdims=True); p_ = np.exp(z); posts.append(p_ / p_.sum(1, keepdims=True))
RES["SeqVLAD_seq"], PER["SeqVLAD_seq"] = B.evaluate(posts)
RES["SeqVLAD_seq"]["L"], RES["SeqVLAD_seq"]["k"] = best[1], best[2]
# JIST sequence similarity used as the HMM emission (learned sequence descriptor + HMM inference), dev-tuned
from .. import hmm, emission
from .common import subset
def run_seqhmm(sp, m, sd, b):
    out = []
    for S, (ep, rows) in zip(SC[sp], B.split[sp]):
        _, _, _, rm = subset(ep, rows)
        cfg = hmm.HMMConfig([hmm.chain_kernel(ep.s, mean=m, std=sd)], use_null=False, leak=1e-3)
        out.append(hmm.forward(S / tau_s, cfg, beta=b, reset_mask=rm)["post"])
    return out
bh = None
for (m, sd), b in itertools.product(B.kernel_grid(), [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]):
    v = B.nll("calib", run_seqhmm("calib", m, sd, b))
    if bh is None or v < bh[0]: bh = (v, m, sd, b)
RES["SeqVLAD_seq+HMM"], PER["SeqVLAD_seq+HMM"] = B.evaluate(run_seqhmm("test", bh[1], bh[2], bh[3])); RES["SeqVLAD_seq+HMM"]["sel"] = bh[1:]
for k_, r in RES.items(): print(f"  {k_:12s} R@1 {r['R@1']:.4f} NLL {r['NLL']:.4f}", flush=True)
rid = new_run_id(f"B11_{DS}_seqvlad")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RES, "sel": best, "p": P}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T3.5", "experiment_id": "B11", "hypothesis_ids": ["H22"], "dataset": DS, "descriptor": "seqvlad",
         "status": "ok", "evidence_level": "S", "metrics": {k_: {m: v[m] for m in ("R@1", "NLL")} for k_, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
