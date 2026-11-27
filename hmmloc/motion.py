"""Appearance-change emission for the latent velocity state (M3+, 'motion evidence without VO').

Observation m_t = log(1 - q_t·q_{t-1} + eps): how much the monocular view changed since the previous frame.
Model p(m_t | v_t = v_k) = N(mu_k, sigma_k^2). Fitted on CALIBRATION sequences using their GT per-frame
displacement (map units / frame) assigned to the nearest velocity bin; bins with few samples use a pooled linear
fit mu(v) = a + b log(v + v0). This makes the velocity state observable (a stop produces m_t ≈ log eps), so the
HMM can stop its motion prior exactly when the evidence stream becomes redundant.
"""
import numpy as np
EPS = 1e-4


def obs(change):
    c = np.where(np.isfinite(change), change, np.nan)
    return np.log(np.maximum(c, 0) + EPS)


class ChangeEmission:
    def __init__(self, vels, v0=0.1, min_n=30, sigma_floor=0.15):
        self.vels = np.asarray(vels, float); self.v0 = v0; self.min_n = min_n; self.sf = sigma_floor

    def fit(self, m, speed):
        ok = np.isfinite(m) & np.isfinite(speed)
        m, speed = m[ok], speed[ok]
        k = np.abs(speed[:, None] - self.vels[None, :]).argmin(1)
        X = np.log(speed + self.v0); A = np.vstack([np.ones_like(X), X]).T
        coef, *_ = np.linalg.lstsq(A, m, rcond=None); res = m - A @ coef
        pooled = max(res.std(), self.sf)
        self.mu = coef[0] + coef[1] * np.log(self.vels + self.v0); self.sig = np.full(len(self.vels), pooled)
        for j in range(len(self.vels)):
            sel = k == j
            if sel.sum() >= self.min_n:
                self.mu[j] = m[sel].mean(); self.sig[j] = max(m[sel].std(), self.sf)
        self.counts = np.bincount(k, minlength=len(self.vels))
        return self

    def loglik(self, m, gamma=1.0):
        """(T,K) log N(m_t; mu_k, sig_k); undefined m (sequence start) -> 0 for all bins."""
        L = -0.5 * ((m[:, None] - self.mu[None]) / self.sig[None]) ** 2 - np.log(self.sig)[None]
        L[~np.isfinite(m)] = 0.0
        return gamma * L

    def describe(self):
        return {"vels": self.vels.tolist(), "mu": np.round(self.mu, 3).tolist(), "sig": np.round(self.sig, 3).tolist(),
                "counts": self.counts.tolist()}
