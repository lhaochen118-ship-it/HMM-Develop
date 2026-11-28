"""E10/B10 — Learned sequence baseline JIST (Berton et al., RA-L 2024) under PROTOCOL v1, vs single image and IA-HMM.
JIST sequence descriptor = SeqGeM(p) over per-frame JIST descriptors (exact, computed offline from the k07/k08 dumps):
    d_seq = ( mean_k clamp(f_k, 1e-6)^p )^(1/p), then L2-normalised.
Query sequences are CAUSAL (last L frames of the same sequence); database sequences end at map node j with stride k
(nodes j-(L-1)k .. j). L ∈ {3,5,10} and k ∈ {1,2,3,5} selected on CALIBRATION R@1 (fair budget, like SeqSLAM).
Usage: e14_jist <dataset> [p]   (p = learned SeqGeM exponent printed by the extraction kernel; default 3.0)"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run
from .. import baselines, metrics

DS = sys.argv[1]; P = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
CENTRED = os.environ.get("HMMLOC_CENTRED") == "1"
t00 = time.time(); B = Bench(DS, "jist")

def seqgem(F, idx_lists):
    X = np.clip(F.astype(np.float64), 1e-6, None) ** P
    out = np.stack([X[ix].mean(0) for ix in idx_lists]) ** (1.0 / P)
    return (out / np.linalg.norm(out, axis=1, keepdims=True)).astype(np.float32)

SEQAGG = lambda F, ix: seqgem(F, ix); DB_SRC = lambda ep: ep.R
def jist_scores(ep, rows, L, k):
    M = ep.M; db_idx = [np.clip(np.arange(j - (L - 1) * k, j + 1, k), 0, M - 1) for j in range(M)]
    Dseq = seqgem(ep.R, db_idx)
    seq = ep.seq[rows]; q_idx = []
    if CENTRED:   # A34: official JIST/SeqVLAD protocol = centred windows (h future frames), same for the database
        h = L // 2; db_idx = [np.clip(np.arange(j - h * k, j + (L - 1 - h) * k + 1, k), 0, M - 1) for j in range(M)]
        Dseq = SEQAGG(DB_SRC(ep), db_idx)
        for i in range(len(rows)):
            lo, hi = i, i
            while lo > 0 and i - lo < h and seq[lo - 1] == seq[i]: lo -= 1
            while hi < len(rows) - 1 and hi - i < L - 1 - h and seq[hi + 1] == seq[i]: hi += 1
            q_idx.append(rows[lo:hi + 1])
    else:
      for i in range(len(rows)):
        lo = i
        while lo > 0 and i - lo < L - 1 and seq[lo - 1] == seq[i]: lo -= 1
        q_idx.append(rows[lo:i + 1])
    Qseq = seqgem(ep.Q, q_idx)
    return Qseq @ Dseq.T

def r1(split, L, k):
    acc = []
    for ep, rows in B.split[split]:
        S = jist_scores(ep, rows, L, k); P_ = ep.pos[rows]; h = P_.any(1)
        acc.append(P_[np.arange(len(rows)), S.argmax(1)][h])
    return float(np.concatenate(acc).mean())

best = max(((r1("calib", L, k), L, k) for L, k in itertools.product((3, 5, 10), (1, 2, 3, 5))), key=lambda x: x[0])
print(f"[{DS}/jist] p={P} selected L={best[1]} k={best[2]} (calib R@1 {best[0]:.3f})", flush=True)
RES, PER = {}, {}
RES["single_jist"], PER["single_jist"] = B.evaluate([baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split["test"]])
posts = []
for ep, rows in B.split["test"]:
    S = jist_scores(ep, rows, best[1], best[2]); z = S / B.tau; z -= z.max(1, keepdims=True); p_ = np.exp(z); posts.append(p_ / p_.sum(1, keepdims=True))
RES["JIST_seq"], PER["JIST_seq"] = B.evaluate(posts)
RES["JIST_seq"]["L"], RES["JIST_seq"]["k"] = best[1], best[2]
# JIST sequence similarity used as the HMM emission (learned sequence descriptor + HMM inference), dev-tuned
from .. import hmm, emission
from .common import subset
SC = {sp: [jist_scores(ep, rows, best[1], best[2]) for ep, rows in B.split[sp]] for sp in ("calib", "test")}
tau_s, _ = emission.fit_temperature_multi([(S, ep.pos[rows]) for S, (ep, rows) in zip(SC["calib"], B.split["calib"])])
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
RES["JIST_seq+HMM"], PER["JIST_seq+HMM"] = B.evaluate(run_seqhmm("test", bh[1], bh[2], bh[3])); RES["JIST_seq+HMM"]["sel"] = bh[1:]
for k_, r in RES.items(): print(f"  {k_:12s} R@1 {r['R@1']:.4f} NLL {r['NLL']:.4f}", flush=True)
rid = new_run_id(f"B10{'c' if CENTRED else ''}_{DS}_jist")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RES, "sel": best, "p": P}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T3.5", "experiment_id": "B10", "hypothesis_ids": ["H22"], "dataset": DS, "descriptor": "jist",
         "status": "ok", "evidence_level": "S", "metrics": {k_: {m: v[m] for m in ("R@1", "NLL")} for k_, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
