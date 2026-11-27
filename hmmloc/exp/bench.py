"""Reusable benchmark harness: episodes + dev calibration + HMM runs with per-frame β schedules."""
import itertools, time
import numpy as np
from .. import data, hmm, emission, metrics, baselines, infoaware
from .common import subset, make_kernels, run_hmm


def load(ds, desc):
    if ds == "nord": return [data.load_nordland(desc)]
    if ds == "rc": return [data.load_robotcar(desc)]
    if ds == "cmu": return data.load_cmu(desc)
    if ds.startswith("nordseg"): return [data.load_nordseg(desc, stride=int(ds[7:] or 1))]
    raise ValueError(ds)


class Bench:
    def __init__(self, ds, desc, eps=None):
        self.ds, self.desc = ds, desc
        self.eps = eps if eps is not None else load(ds, desc)
        self.unit = self.eps[0].unit
        self.split = {s: [(ep, ep.rows(s)) for ep in self.eps] for s in ("calib", "test")}
        parts = [(ep.sim()[r], ep.pos[r]) for ep, r in self.split["calib"]]
        self.tau, _ = emission.fit_temperature_multi(parts)
        self.llr = {"llr": emission.fit_llr_multi(parts, kind="raw"), "llrz": emission.fit_llr_multi(parts, kind="raw+z")}
        self.change = {s: [infoaware.frame_change(ep.Q[r], ep.seq[r]) for ep, r in self.split[s]] for s in ("calib", "test")}
        ch = np.concatenate([c[np.isfinite(c)] for c in self.change["calib"]])
        self.kappa_grid = np.percentile(ch, [50, 75, 90, 97]) if len(ch) else np.array([1.0])

    def emit(self, ep, rows, kind):
        S = ep.sim()[rows]
        if kind == "tau": return S / self.tau, None
        return self.llr[kind].loglik(S), np.zeros(len(rows))

    def run(self, split, kind, mean, std, beta, vel=None, vstd=0.5, null=False, beta_fn=None, lag=0):
        posts = []
        for i, (ep, rows) in enumerate(self.split[split]):
            L, Ln = self.emit(ep, rows, kind)
            ks = make_kernels(ep, mean, std) if vel is None else make_kernels(ep, None, None, vels=vel, vstd=vstd)
            b = beta if beta_fn is None else beta_fn(self.change[split][i])
            if lag > 0:
                cfg = hmm.HMMConfig(ks, use_null=False, leak=1e-3)
                S, pos, seq, rm = subset(ep, rows)
                posts.append(hmm.forward_backward_lag(L, cfg, lag=lag, beta=b, reset_mask=rm).astype(np.float32))
            else:
                posts.append(run_hmm(ep, rows, L, ks, beta=b, use_null=null, exit_prob=0.01 if null else 0.0,
                                     loglik_null=Ln if null else None)["post"])
        return posts

    def nll(self, split, posts):
        tot, n = 0.0, 0
        for (ep, rows), p in zip(self.split[split], posts):
            P = ep.pos[rows]; k = P.any(1); tot += metrics.event_nll(p[k], P[k]).sum(); n += k.sum()
        return tot / n

    def evaluate(self, posts, split="test"):
        allc, alln, allconf, blocks = [], [], [], []
        for (ep, rows), p in zip(self.split[split], posts):
            P = ep.pos[rows]; has = P.any(1)
            pr = p[has].argmax(1); c = P[has][np.arange(has.sum()), pr].astype(float)
            cf = np.array([p[has][t, ep.near[pr[t]]].sum() for t in range(len(pr))])
            nl = metrics.event_nll(p[has], P[has]); off = sum(len(x) for x in allc)
            sq = ep.seq[rows][has]
            blocks += [np.where(sq == q)[0] + off for q in np.unique(sq)]
            allc.append(c); alln.append(nl); allconf.append(cf)
        c = np.concatenate(allc); nl = np.concatenate(alln); cf = np.concatenate(allconf)
        s = {"R@1": float(c.mean()), "NLL": float(nl.mean()), "ECE": metrics.ece(cf, c), "Brier": metrics.brier(cf, c),
             "CW@0.9": float(np.mean((cf > 0.9) & (c == 0))), "AUROC_conf": metrics.auroc(cf, c), "AURC": metrics.aurc(cf, c),
             "n": int(len(c)), "n_seq": len(blocks)}
        return s, {"corr": c, "nll": nl, "conf": cf, "blocks": blocks}

    def kernel_grid(self):
        if self.unit == "frame": return [(1.0, s) for s in (0.5, 1.0, 2.0)]
        return [(m, s) for m in (1.0, 1.5, 2.5) for s in (1.5, 3.0)]
