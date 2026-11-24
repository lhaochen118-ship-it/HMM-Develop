"""Geometric (shape) consistency of the reported place track with the odometry over a long path (Entry 26).

For frame t, take the frames of the same sequence whose odometry path to t is <= D metres, sub-sample them every `step`
metres of odometry path, and fit the 2-D rigid motion (rotation + translation; Procrustes, no reflection) that maps the
odometry points onto the reported places m_s (place-chain MAP). Outputs per frame:
  resid   RMS residual after the fit (metres)              small  <=> the track moves with the odometry, turns included
  shape   sqrt(lambda_min / lambda_max) of the centred odometry points (0 = straight path: shape carries no information
          beyond distance; larger = the path turns, the fit also tests the turns)
  span    odometry path length actually covered by the window (< D at the start of a sequence)
  rot     fitted rotation (radians)
1-D datasets (Nordland, frames): translation only.
Magnitude-only CS (cpc_sc.consistency_ok) is the special case of a straight path."""
import numpy as np


def window_points(o, cum, t, D, step):
    """indices of frames s <= t with cum[t] - cum[s] <= D, sub-sampled every `step` metres of path (always keeps t)"""
    lo = np.searchsorted(cum, cum[t] - D, side="left")
    if lo >= t: return np.array([t])
    targets = np.arange(cum[t], cum[lo] - 1e-9, -step)
    j = np.searchsorted(cum[lo:t + 1], targets, side="left") + lo
    return np.unique(np.clip(j, lo, t))


def procrustes2(m, o):
    """rigid 2-D fit o -> m; returns (rms residual, rotation, shape index of o)"""
    mc, oc = m - m.mean(0), o - o.mean(0)
    Hm = oc.T @ mc; th = np.arctan2(Hm[0, 1] - Hm[1, 0], Hm[0, 0] + Hm[1, 1])
    c, s = np.cos(th), np.sin(th); ro = np.stack([c * oc[:, 0] - s * oc[:, 1], s * oc[:, 0] + c * oc[:, 1]], 1)
    r = float(np.sqrt(((mc - ro) ** 2).sum(1).mean()))
    ev = np.linalg.eigvalsh(oc.T @ oc / len(oc)) if len(oc) > 1 else np.array([0.0, 0.0])
    shp = float(np.sqrt(max(ev[0], 0) / ev[1])) if ev[1] > 1e-9 else 0.0
    return r, float(th), shp


def track_consistency(x_m, o_q, seqs, D, step=5.0, hz=None, min_pts=3):
    """per-frame (resid, shape, span, rot) of the reported track x_m vs the odometry o_q (see module doc)"""
    n = len(x_m); resid, shape, span, rot = (np.full(n, np.nan) for _ in range(4))
    one_d = x_m.ndim == 1 or x_m.shape[1] == 1
    if not one_d and hz is not None and x_m.shape[1] > 2: x_m, o_q = x_m[:, hz], o_q[:, hz]
    for idx in seqs:
        m, o = x_m[idx].astype(float), o_q[idx].astype(float)
        if one_d: m, o = m.reshape(-1, 1), o.reshape(-1, 1)
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        for i in range(len(idx)):
            w = window_points(o, cum, i, D, step); span[idx[i]] = cum[i] - cum[w[0]]
            if len(w) < min_pts: continue
            if one_d:
                d = (m[w, 0] - m[w, 0].mean()) - (o[w, 0] - o[w, 0].mean()); resid[idx[i]] = float(np.sqrt((d ** 2).mean())); shape[idx[i]] = 0.0
            else:
                resid[idx[i]], rot[idx[i]], shape[idx[i]] = procrustes2(m[w], o[w])
    return resid, shape, span, rot
