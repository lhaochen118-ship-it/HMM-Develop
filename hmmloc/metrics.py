"""Evaluation metrics (Master Plan §7.5). Unit of inference for CIs = contiguous blocks / sequences."""
from __future__ import annotations
import numpy as np


def top1(post):
    return np.asarray(post).argmax(1)


def recall1(pred, pos_mask):
    return pos_mask[np.arange(len(pred)), pred].astype(float)


def event_nll(post, pos_mask, eps=1e-6):
    """-log P(true event): posterior mass on the positive set (null mass counts as wrong)."""
    m = (np.asarray(post, np.float64) * pos_mask).sum(1)
    return -np.log(np.clip(m, eps, 1.0))


def local_confidence(post, pred, near_mask_fn):
    """q_t = posterior mass within the tolerance neighbourhood of the prediction."""
    return np.array([post[t, near_mask_fn(pred[t])].sum() for t in range(len(pred))])


def ece(conf, correct, n_bins=15):
    conf = np.asarray(conf, float); correct = np.asarray(correct, float)
    bins = np.linspace(0, 1, n_bins + 1); e = 0.0
    for i in range(n_bins):
        m = (conf > bins[i]) & (conf <= bins[i + 1]) if i else (conf >= 0) & (conf <= bins[1])
        if m.any(): e += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(e)


def brier(conf, correct):
    return float(np.mean((np.asarray(conf) - np.asarray(correct)) ** 2))


def auroc(score, label):
    score = np.asarray(score, float); label = np.asarray(label, int)
    P, N = label.sum(), (label == 0).sum()
    if P == 0 or N == 0: return float("nan")
    from scipy.stats import rankdata
    r = rankdata(score)
    return float((r[label == 1].sum() - P * (P + 1) / 2) / (P * N))


def aurc(conf, correct):
    """Area under risk-coverage curve (lower is better)."""
    o = np.argsort(-np.asarray(conf)); err = 1 - np.asarray(correct, float)[o]
    risk = np.cumsum(err) / (np.arange(len(err)) + 1)
    return float(risk.mean())


def block_bootstrap(values_by_block, n=2000, seed=0, stat=np.mean):
    """values_by_block: list of 1-D arrays (one per block). Resample blocks with replacement."""
    rng = np.random.default_rng(seed)
    vals = [np.asarray(v, float) for v in values_by_block if len(v)]
    B = len(vals); out = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, B, B)
        out[i] = stat(np.concatenate([vals[j] for j in idx]))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def paired_block_bootstrap(a_by_block, b_by_block, n=2000, seed=0):
    """CI of mean(a)-mean(b) where a,b are paired per-frame metrics grouped by the same blocks."""
    rng = np.random.default_rng(seed)
    A = [np.asarray(x, float) for x in a_by_block]; Bv = [np.asarray(x, float) for x in b_by_block]
    nb = len(A); out = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, nb, nb)
        out[i] = np.concatenate([A[j] for j in idx]).mean() - np.concatenate([Bv[j] for j in idx]).mean()
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def summarize(post, pos_mask, near_fn, null=None):
    pred = top1(post); corr = recall1(pred, pos_mask)
    conf = local_confidence(post, pred, near_fn)
    nll = event_nll(post, pos_mask)
    return {"R@1": float(corr.mean()), "NLL": float(nll.mean()), "ECE": ece(conf, corr),
            "Brier": brier(conf, corr), "CW@0.9": float(np.mean((conf > 0.9) & (corr == 0))),
            "AUROC_conf": auroc(conf, corr), "AURC": aurc(conf, corr)}, pred, corr, conf, nll
