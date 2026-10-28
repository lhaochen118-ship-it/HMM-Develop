"""E2/E3 — label-free calibrated confidence and FDR control from EVS p-values.

Two-groups model on one deployment batch (all queries of a session/condition): p ~ pi0*U(0,1) + (1-pi0)*f1.
  pi0  : Storey's estimator  #{p > lam} / ((1-lam) n)
  f(p) : decreasing (Grenander) density = slopes of the least concave majorant of the empirical CDF
  P(correct | p) ~= 1 - lfdr(p) = 1 - min(1, pi0 / f(p))
No labels are used anywhere. Compared against label-trained calibrators transferred from benign conditions.
"""
import numpy as np


def storey_pi0(p, lam=0.5):
    p = np.asarray(p, float)
    return float(min(1.0, max(1e-3, (p > lam).mean() / (1 - lam))))


def grenander_density(p):
    """Decreasing density estimate on [0,1] at each p (least concave majorant of the ECDF)."""
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); x = np.concatenate([[0.0], p[o], [1.0]])
    y = np.concatenate([[0.0], np.arange(1, n + 1) / n, [1.0]])
    # upper concave hull (monotone chain)
    hull = [0]
    for i in range(1, len(x)):
        while len(hull) >= 2:
            a, b = hull[-2], hull[-1]
            if (y[b] - y[a]) * (x[i] - x[a]) <= (y[i] - y[a]) * (x[b] - x[a]): hull.pop()
            else: break
        hull.append(i)
    hx, hy = x[hull], y[hull]; slopes = np.diff(hy) / np.maximum(np.diff(hx), 1e-12)
    seg = np.clip(np.searchsorted(hx, p, side="left") - 1, 0, len(slopes) - 1)
    return np.maximum(slopes[seg], 1e-9)


def labelfree_confidence(p, lam=0.5):
    pi0 = storey_pi0(p, lam); f = grenander_density(p)
    return np.clip(1 - pi0 / f, 0, 1), pi0


def bh_accept(p, alpha):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p)
    ok = p[o] <= alpha * np.arange(1, n + 1) / n
    k = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
    acc = np.zeros(n, bool); acc[o[:k]] = True
    return acc
