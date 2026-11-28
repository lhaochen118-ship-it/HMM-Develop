"""Shared experiment utilities: method zoo, calibration-on-dev, evaluation, registry logging."""
from __future__ import annotations
import os, json, time, hashlib, subprocess
import numpy as np
from .. import hmm, emission, metrics, baselines

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG = os.path.join(ROOT, "research", "registry", "runs.jsonl")


def git_commit():
    try: return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception: return "nogit"


def new_run_id(task):
    os.makedirs(os.path.dirname(REG), exist_ok=True)
    n = sum(1 for _ in open(REG)) if os.path.exists(REG) else 0
    return f"{time.strftime('%Y%m%d', time.gmtime())}-{n+1:03d}_{task}"


def log_run(row):
    row = dict(row); row.setdefault("date_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    row.setdefault("git_commit", git_commit())
    with open(REG, "a") as f: f.write(json.dumps(row, default=float) + "\n")


def cfg_hash(cfg):
    return hashlib.sha1(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:10]


# ------------------------------------------------------------------------------------- sub-episode
def subset(ep, rows):
    """Restrict an episode's query side to `rows` (keeps map)."""
    S = ep.sim()[rows]; pos = ep.pos[rows]; seq = ep.seq[rows]
    rm = np.zeros(len(rows), bool); rm[0] = True; rm[1:] = seq[1:] != seq[:-1]
    return S, pos, seq, rm


def unit_scale(ep):
    return 1.0                         # positions already in metres (rc/cmu) or frames (nord)


def make_kernels(ep, mean, std, vels=None, vstd=None, back=None):
    if getattr(ep, "graph", None) == "spatial":
        if vels is None: return [hmm.spatial_kernel(ep.C, ep.heading, mean, std)]
        return [hmm.spatial_kernel(ep.C, ep.heading, v, vstd) for v in vels]
    if vels is None:
        return [hmm.chain_kernel(ep.s, mean=mean, std=std, back=back)]
    return [hmm.chain_kernel(ep.s, mean=v, std=vstd, back=back) for v in vels]


def run_hmm(ep, rows, L, kernels, beta=1.0, use_null=False, exit_prob=0.0, leak=1e-3, vel_stay=0.9,
            null_stay=0.9, loglik_null=None, P0v=None):
    K = len(kernels)
    cfg = hmm.HMMConfig(kernels, Pv=hmm.sticky_velocity(K, vel_stay) if K > 1 else None, P0v=P0v,
                        exit_prob=exit_prob, null_stay=null_stay, null_prior=0.0, leak=leak, use_null=use_null)
    S, pos, seq, rm = subset(ep, rows)
    out = hmm.forward(L, cfg, beta=beta, reset_mask=rm, loglik_null=loglik_null)
    return out


def evaluate(ep, rows, post, extra=None):
    pos = ep.pos[rows]; has = pos.any(1)
    near_fn = lambda j: ep.near[j]
    summ, pred, corr, conf, nll = metrics.summarize(post[has], pos[has], near_fn)
    blocks_idx = [np.where(ep.seq[rows][has] == q)[0] for q in np.unique(ep.seq[rows][has])]
    summ["R@1_CI"] = metrics.block_bootstrap([corr[b] for b in blocks_idx], n=1000)
    summ["n"] = int(has.sum()); summ["n_seq"] = len(blocks_idx)
    if extra: summ.update(extra)
    per = {"corr": corr, "nll": nll, "conf": conf, "pred": pred, "blocks": blocks_idx}
    return summ, per


def fmt(s):
    return (f"R@1 {s['R@1']:.3f} [{s['R@1_CI'][0]:.3f},{s['R@1_CI'][1]:.3f}] NLL {s['NLL']:.3f} "
            f"ECE {s['ECE']:.3f} CW {s['CW@0.9']:.3f} AUROC {s['AUROC_conf']:.3f}")
