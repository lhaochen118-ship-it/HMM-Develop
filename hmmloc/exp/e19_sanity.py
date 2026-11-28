"""E35 — Sanity / leakage controls for the HMM scores (user audit request, 28/11). Same protocol as E18's fixed-kernel
HMM (kernel grid x beta chosen on CALIBRATION NLL), applied to deliberately broken inputs:
  real      : unchanged episode
  random    : map and query descriptors replaced by random unit vectors -> no appearance information. Any method must fall
              to chance (= mean fraction of map nodes that are positives). Above-chance HMM = leakage of GT into the filter.
  shuffled  : query frames permuted WITHIN each sequence (per-frame evidence and labels kept, temporal order destroyed)
              -> the HMM's advantage over single image must (largely) vanish.
  reversed  : map node order reversed (the forward-motion chain prior is now wrong) -> the HMM must degrade.
Usage: python -m hmmloc.exp.e19_sanity <dataset> <desc>"""
import sys, os, json, time, itertools, dataclasses
import numpy as np
from .bench import Bench, load
from .common import ROOT, new_run_id, log_run
from .. import baselines

DS, DESC = sys.argv[1], sys.argv[2]; t00 = time.time(); rng = np.random.default_rng(0)


def fixed_hmm(B):
    best = None
    for (m, s), b in itertools.product(B.kernel_grid(), [0.2, 0.35, 0.5, 0.75, 1.0]):
        v = B.nll("calib", B.run("calib", "tau", m, s, b))
        if best is None or v < best[0]: best = (v, m, s, b)
    return B.evaluate(B.run("test", "tau", best[1], best[2], best[3]))[0]["R@1"], best[1:]


def variant(ep, kind):
    if kind == "real": return ep
    if kind == "random":
        R = rng.standard_normal(ep.R.shape).astype(np.float32); R /= np.linalg.norm(R, axis=1, keepdims=True)
        Q = rng.standard_normal(ep.Q.shape).astype(np.float32); Q /= np.linalg.norm(Q, axis=1, keepdims=True)
        return dataclasses.replace(ep, R=R, Q=Q)
    if kind == "shuffled":
        perm = np.arange(ep.T)
        for q in np.unique(ep.seq):
            ix = np.where(ep.seq == q)[0]; perm[ix] = rng.permutation(ix)
        return dataclasses.replace(ep, Q=ep.Q[perm], pos=ep.pos[perm], cond=ep.cond[perm],
                                   qC=None if ep.qC is None else ep.qC[perm], qt=None if ep.qt is None else ep.qt[perm])
    if kind == "reversed":
        o = np.arange(ep.M)[::-1]
        return dataclasses.replace(ep, R=ep.R[o], s=(ep.s[-1] - ep.s[o]) if ep.s is not None else None, pos=ep.pos[:, o],
                                   near=ep.near[np.ix_(o, o)], C=None if ep.C is None else ep.C[o],
                                   Rrot=None if ep.Rrot is None else ep.Rrot[o])
    raise ValueError(kind)


RES = {}
base = load(DS, DESC)
for kind in ("real", "random", "shuffled", "reversed"):
    eps = [variant(e, kind) for e in base]
    B = Bench(DS, DESC, eps=eps)
    single = B.evaluate([baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split["test"]])[0]["R@1"]
    hmm_r1, sel = fixed_hmm(B)
    chance = float(np.mean(np.concatenate([ep.pos[r][ep.pos[r].any(1)].sum(1) / ep.M for ep, r in B.split["test"]])))
    RES[kind] = {"single": single, "hmm": hmm_r1, "chance": chance, "sel": sel}
    print(f"  {kind:9s} single {single:.3f}  HMM {hmm_r1:.3f}  chance {chance:.4f}  sel {sel}", flush=True)
rid = new_run_id(f"E35_{DS}_{DESC}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump(RES, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T6.0", "experiment_id": "E35", "hypothesis_ids": ["sanity"], "dataset": DS, "descriptor": DESC,
         "status": "ok", "evidence_level": "S", "metrics": {k: {"single": v["single"], "hmm": v["hmm"], "chance": v["chance"]} for k, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
