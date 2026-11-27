"""Observation models.  Every model returns l_t(j) = log p(o_t | z_t=j) - log p(o_t | z_t=null)
(a log-likelihood ratio against the all-non-match baseline), so that the off-map state has l=0.

  * SoftmaxTemp  : l = s / tau  (classic; only defined up to a constant -> needs a null offset c)
  * LogisticLLR  : l = logit p(match | features) - log(pi/(1-pi))   (calibrated LLR, prior-corrected)
Features (per query frame t, map node j): raw cosine s, per-frame z-score  (s - mu_t)/sd_t, and
map-node distinctiveness  s - mu_j  (CSLS-like hubness correction, mu_j = mean top-k sim of node j to
other map nodes, computed from the map only).
"""
from __future__ import annotations
import numpy as np


def frame_zscore(S: np.ndarray) -> np.ndarray:
    mu = S.mean(1, keepdims=True); sd = S.std(1, keepdims=True) + 1e-6
    return (S - mu) / sd


def map_hubness(Rdesc: np.ndarray, k: int = 10, exclude: int = 5) -> np.ndarray:
    """mu_j = mean of the top-k cosine similarities of map node j to map nodes at least `exclude` indices away."""
    R = Rdesc.astype(np.float32)
    G = R @ R.T
    M = len(R); idx = np.arange(M)
    G[np.abs(idx[:, None] - idx[None, :]) < exclude] = -np.inf
    part = -np.partition(-G, kth=min(k, M - 1), axis=1)[:, :k]
    return part.mean(1)


def features(S, hub=None, kind="raw"):
    if kind == "raw": return [S]
    if kind == "z": return [frame_zscore(S)]
    if kind == "raw+z": return [S, frame_zscore(S)]
    if kind == "csls": return [S - 0.5 * hub[None, :]]
    if kind == "z+csls":
        return [frame_zscore(S - 0.5 * hub[None, :])]
    raise ValueError(kind)


class LogisticLLR:
    """Fit logit p(match|x) = w.x + b on (match, non-match) pairs sampled from calibration frames,
    then l = w.x + b - log(pi/(1-pi)) with pi the sampled match fraction (case-control correction).
    Optional `temper` multiplies the LLR (fit separately; 1.0 = pure LLR)."""
    def __init__(self, kind="raw", n_neg=200, seed=0, C=1.0):
        self.kind, self.n_neg, self.seed, self.C = kind, n_neg, seed, C

    def _X(self, S, hub):
        return np.stack([f for f in features(S, hub, self.kind)], -1)  # (T,M,F)

    def fit(self, S, pos_mask, hub=None, rows=None):
        """S (T,M) sims; pos_mask (T,M) bool positives; rows: calibration row indices."""
        rng = np.random.default_rng(self.seed)
        rows = np.arange(S.shape[0]) if rows is None else np.asarray(rows)
        rows = rows[pos_mask[rows].any(1)]
        X = self._X(S[rows], hub); P = pos_mask[rows]
        xs, ys = [], []
        for r in range(len(rows)):
            pj = np.where(P[r])[0]; nj = np.where(~P[r])[0]
            # hard + random negatives (top-scoring negatives matter most for localization)
            top = nj[np.argsort(-X[r, nj, 0])[: self.n_neg // 2]]
            rnd = rng.choice(nj, size=min(self.n_neg // 2, len(nj)), replace=False)
            nn = np.unique(np.concatenate([top, rnd]))
            xs.append(X[r, pj]); ys.append(np.ones(len(pj)))
            xs.append(X[r, nn]); ys.append(np.zeros(len(nn)))
        x = np.concatenate(xs); y = np.concatenate(ys)
        self.mu = x.mean(0); self.sd = x.std(0) + 1e-9
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression(C=self.C, max_iter=2000).fit((x - self.mu) / self.sd, y)
        self.w = lr.coef_[0] / self.sd; self.b = lr.intercept_[0] - (self.mu * self.w).sum()
        # Correction to the population prior of a match among ALL map nodes for a frame (not the sampled one)
        pi_s = y.mean()
        pi_pop = P.sum() / P.size
        self.offset = -np.log(pi_s / (1 - pi_s)) + np.log(pi_pop / (1 - pi_pop))
        self.pi_pop = pi_pop
        return self

    def loglik(self, S, hub=None):
        """LLR log h1/h0 = logit_sampled - log(pi_s/(1-pi_s))."""
        X = self._X(S, hub)
        logit = X @ self.w + self.b
        # population log-odds -> LLR:  log h1/h0 = logit_pop - log(pi_pop/(1-pi_pop));
        # (legacy unweighted fit stored offset = logit_pop - logit_sampled correction)
        return logit + self.offset - np.log(self.pi_pop / (1 - self.pi_pop))

    def describe(self):
        return {"kind": self.kind, "w": np.round(self.w, 3).tolist(), "b": float(self.b)}


def fit_temperature(S, pos_mask, rows=None, grid=None):
    """tau minimising event NLL  -log sum_{j in pos} softmax(s/tau)_j  on calibration rows."""
    grid = np.logspace(-2.7, -0.3, 40) if grid is None else grid
    rows = np.arange(S.shape[0]) if rows is None else np.asarray(rows)
    rows = rows[pos_mask[rows].any(1)]
    Sr, P = S[rows].astype(np.float64), pos_mask[rows]
    best, bn = None, np.inf
    for tau in grid:
        z = Sr / tau; z -= z.max(1, keepdims=True); p = np.exp(z); p /= p.sum(1, keepdims=True)
        nll = -np.log(np.maximum((p * P).sum(1), 1e-12)).mean()
        if nll < bn: bn, best = nll, tau
    return float(best), float(bn)


# ------------------------------------------------------------------ multi-episode calibration helpers
def fit_temperature_multi(parts, grid=None):
    """parts: list of (S_rows, pos_rows). Pools per-row event NLL across episodes (different map sizes)."""
    grid = np.logspace(-2.7, -0.3, 40) if grid is None else grid
    best, bn = None, np.inf
    for tau in grid:
        tot, n = 0.0, 0
        for S, P in parts:
            k = P.any(1)
            if not k.any(): continue
            z = S[k].astype(np.float64) / tau; z -= z.max(1, keepdims=True); p = np.exp(z); p /= p.sum(1, keepdims=True)
            tot += -np.log(np.maximum((p * P[k]).sum(1), 1e-12)).sum(); n += k.sum()
        if tot / n < bn: bn, best = tot / n, tau
    return float(best), float(bn)


def fit_llr_multi(parts, kind="raw", hubs=None, n_hard=50, n_rand=150, seed=0):
    """Fit one LogisticLLR on pooled calibration rows from several episodes.
    Sampling design per calibration frame: all positives (weight 1), the n_hard top-scoring negatives
    (inclusion prob 1, weight 1) and n_rand uniformly random negatives from the remaining ones
    (weight = n_remaining / n_rand, Horvitz-Thompson).  The weighted sample reproduces the population of
    (frame, node) pairs, so  LLR = logit - log(pi/(1-pi))  with pi the population match rate.  (Fixes A22:
    hard negatives without inclusion weights bias the slope.)"""
    m = LogisticLLR(kind=kind)
    rng = np.random.default_rng(seed); xs, ys, ws = [], [], []
    for i, (S, P) in enumerate(parts):
        hub = None if hubs is None else hubs[i]
        k = P.any(1); S, P = S[k], P[k]
        X = m._X(S, hub)
        for r in range(len(S)):
            pj = np.where(P[r])[0]; nj = np.where(~P[r])[0]
            order = nj[np.argsort(-X[r, nj, 0])]
            hard = order[:n_hard]; rest = order[n_hard:]
            nr = min(n_rand, len(rest)); rnd = rng.choice(rest, size=nr, replace=False) if nr else rest[:0]
            xs += [X[r, pj], X[r, hard], X[r, rnd]]
            ys += [np.ones(len(pj)), np.zeros(len(hard)), np.zeros(nr)]
            ws += [np.ones(len(pj)), np.ones(len(hard)), np.full(nr, len(rest) / max(nr, 1))]
    x = np.concatenate(xs); y = np.concatenate(ys); w = np.concatenate(ws)
    from sklearn.linear_model import LogisticRegression
    mu, sd = x.mean(0), x.std(0) + 1e-9
    lr = LogisticRegression(C=10.0, max_iter=5000).fit((x - mu) / sd, y, sample_weight=w / w.mean())
    m.w = lr.coef_[0] / sd; m.b = lr.intercept_[0] - (mu * m.w).sum()
    m.pi_pop = float((w * y).sum() / w.sum())
    # weighted sample == population -> logit is already the population posterior log-odds
    m.offset = 0.0
    return m
