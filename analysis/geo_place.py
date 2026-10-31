"""Geometric placements of the robot's odometry window on the map (Entry 26).

A PLACEMENT of the odometry window O_t (the last D metres of odometry path, sampled every `step` metres of path) is a
stretch of the map's own traversal (either direction) of the same path length whose rigid 2-D fit to O_t (rotation +
translation, Procrustes) has RMS residual <= eps. Placements whose end points lie within `merge` metres are one
hypothesis (the best residual is kept). N_t = number of distinct placements depends on the map geometry and the
odometry ONLY (no image): it is the multiplicity an appearance test has to pay for after the geometry has been used.
Straight paths have many placements (N_t ~ straight map length / merge), turning paths few.
1-D maps (Nordland, positions in frames): a placement is any stretch of the right length (no shape information)."""
import numpy as np


def map_chunks(MP, step, gap=None):
    """traversal polylines of the (reduced) map, split where consecutive map rows jump by more than `gap`, resampled
    every `step` metres of path. Returns list of (K_c, d) arrays."""
    P = MP.astype(float) if MP.ndim > 1 else MP.astype(float)[:, None]
    d = np.linalg.norm(np.diff(P, axis=0), axis=1)
    gap = gap if gap is not None else max(5 * np.median(d[d > 0]) if (d > 0).any() else 1.0, 2 * step)
    cuts = np.flatnonzero(d > gap) + 1; out = []
    for seg in np.split(np.arange(len(P)), cuts):
        if len(seg) < 2: continue
        q = P[seg]; cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
        if cum[-1] < step: continue
        s = np.arange(0, cum[-1] + 1e-9, step); out.append(np.stack([np.interp(s, cum, q[:, k]) for k in range(q.shape[1])], 1))
    return out


def resample_back(o, cum, i, D, step):
    """odometry points at path offsets 0, step, ..., <= D back from frame i (index into o), newest first"""
    s = cum[i] - np.arange(0, D + 1e-9, step); s = s[s >= cum[0] - 1e-9]
    return np.stack([np.interp(s, cum, o[:, k]) for k in range(o.shape[1])], 1)


class Placer:
    """enumerate placements of odometry windows of K points on the map chunks (vectorised over all candidates)"""

    def __init__(self, MP, step, K):
        self.step, self.K = step, K; ch = map_chunks(MP, step); self.dim = ch[0].shape[1] if ch else 2
        cand, ends = [], []
        for c in ch:
            if len(c) < K: continue
            idx = np.arange(K - 1, len(c))
            fw = np.stack([c[idx - i] for i in range(K)], 1)          # end at idx, going backwards in map order
            idx2 = np.arange(0, len(c) - K + 1)
            bw = np.stack([c[idx2 + i] for i in range(K)], 1)         # end at idx2, robot drives against map order
            cand += [fw, bw]
        self.C = np.concatenate(cand) if cand else np.zeros((0, K, self.dim))   # (n_cand, K, dim): point i = i*step back from the end
        self.Cc = self.C - self.C.mean(1, keepdims=True)

    def fit(self, O):
        """residual (n_cand,) and fitted end point (n_cand, dim) of every candidate for odometry points O (K, dim), newest first"""
        Oc = O - O.mean(0)
        if self.dim == 1:
            r = np.sqrt(((self.Cc[..., 0] - Oc[None, :, 0]) ** 2).mean(1)); return r, self.C[:, 0]
        H00 = (Oc[None, :, 0] * self.Cc[..., 0]).sum(1); H01 = (Oc[None, :, 0] * self.Cc[..., 1]).sum(1)
        H10 = (Oc[None, :, 1] * self.Cc[..., 0]).sum(1); H11 = (Oc[None, :, 1] * self.Cc[..., 1]).sum(1)
        th = np.arctan2(H01 - H10, H00 + H11); c, s = np.cos(th), np.sin(th)
        rx = c[:, None] * Oc[None, :, 0] - s[:, None] * Oc[None, :, 1]; ry = s[:, None] * Oc[None, :, 0] + c[:, None] * Oc[None, :, 1]
        r = np.sqrt(((self.Cc[..., 0] - rx) ** 2 + (self.Cc[..., 1] - ry) ** 2).mean(1))
        return r, self.C[:, 0]


def distinct(ends, resid, merge):
    """greedy de-duplication by end point (best residual first): indices of distinct placements"""
    order = np.argsort(resid); keep = []
    for i in order:
        if all(np.linalg.norm(ends[i] - ends[j]) > merge for j in keep): keep.append(i)
    return np.array(keep, int)


def placements(placer, o_seq, cum, i, D, eps, merge):
    """distinct placements of the odometry window ending at frame i: (end points (n, dim), residuals (n,)); None if the
    window is shorter than D"""
    if cum[i] - cum[0] < D - 1e-6: return None
    O = resample_back(o_seq, cum, i, D, placer.step)[: placer.K]
    if len(O) < placer.K: return None
    r, e = placer.fit(O); ok = np.flatnonzero(r <= eps)
    if not len(ok): return np.zeros((0, placer.dim)), np.zeros(0)
    k = distinct(e[ok], r[ok], merge)
    return e[ok][k], r[ok][k]
