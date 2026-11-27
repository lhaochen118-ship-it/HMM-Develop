"""Information-aware evidence weighting for HMM localization (IA-HMM, hypothesis H20).

Motivation (Master Plan §4.5).  Consecutive monocular frames are not conditionally independent given the
place: at high frame rate / standstill, o_t ≈ o_{t-1} and multiplying both likelihoods double-counts
evidence (over-confident lock-in).  Under a Gaussian AR(1) residual model for the per-node LLR stream,
  l_t = δ·1[z_t=j] + e_t,   e_t = ρ e_{t-1} + sqrt(1-ρ²) ξ_t,
the conditional likelihood of o_t given o_{t-1} carries Fisher information δ²/σ² · (1-ρ)/(1+ρ) instead of
δ²/σ².  A power-likelihood (generalised Bayes) update with weight
        β_t = β₀ · (1-ρ_t)/(1+ρ_t)
matches the information of the conditional (AR) emission while keeping the HMM forward recursion and its
state space unchanged — the model remains an HMM whose emission is the tempered conditional likelihood.

Label-free ρ_t.  ρ_t is predicted from the query stream only: u_t = min(1, (1 - q_t·q_{t-1}) / κ) is the
fraction of "fresh" appearance change relative to a scale κ (the typical squared-chord change between two
decorrelated frames), and ρ_t = 1 - u_t.  Hence β_t = β₀ · u_t / (2 - u_t).   (β₀, κ) are fit on calibration
sequences; κ's grid is defined by quantiles of the calibration change distribution (no labels needed for κ).
"""
import numpy as np


def frame_change(Q, seq=None):
    """1 - cos(q_t, q_{t-1}); first frame of each sequence gets +inf (fully fresh)."""
    Qn = Q.astype(np.float32); Qn = Qn / (np.linalg.norm(Qn, axis=1, keepdims=True) + 1e-12)
    c = np.ones(len(Q)) * np.inf
    c[1:] = 1.0 - (Qn[1:] * Qn[:-1]).sum(1)
    if seq is not None:
        c[1:][seq[1:] != seq[:-1]] = np.inf
    return c


def beta_schedule(change, beta0, kappa, floor=0.02):
    u = np.minimum(1.0, change / kappa)
    b = beta0 * u / (2.0 - u)
    return np.maximum(b, floor * beta0)
