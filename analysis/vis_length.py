"""Visual decorrelation length of a map (label-free, before deployment; Entry 20 development, 2026-11-06).
L_vis = the distance at which the EXCESS similarity of two map images over the background (pairs far apart) has decayed to 1/e of its value
at the shortest distances: views closer than L_vis carry largely the same appearance evidence. Uses only the map's descriptors and positions.
vis_length(M, MP, excl) -> (L_vis, curve); a random subsample of at most n_max images, distance bins of excl/10 up to 4 excl."""
import numpy as np


def vis_length(M, MP, excl, n_max=3000, seed=0):
    rng = np.random.default_rng(seed); n = len(M); idx = rng.choice(n, min(n, n_max), replace=False)
    X = M[idx].astype(np.float32); P = np.asarray(MP, float)[idx]; P = P if P.ndim > 1 else P[:, None]
    S = X @ X.T; D = np.sqrt(((P[:, None] - P[None]) ** 2).sum(-1)); iu = np.triu_indices(len(idx), 1); s, d = S[iu], D[iu]
    bg = np.median(s[d > 8 * excl]) if (d > 8 * excl).sum() > 100 else np.median(s)
    edges = np.arange(0, 4 * excl + 1e-9, excl / 10); cen = 0.5 * (edges[1:] + edges[:-1])
    med = np.array([np.median(s[(d >= a) & (d < b)]) if ((d >= a) & (d < b)).sum() >= 20 else np.nan for a, b in zip(edges[:-1], edges[1:])])
    ex = med - bg; ok = np.isfinite(ex)
    if not ok.any() or ex[ok][0] <= 0: return float(excl), (cen, ex)
    e0 = ex[ok][0]; below = np.flatnonzero(ok & (ex <= e0 / np.e))
    return (float(cen[below[0]]) if len(below) else float(4 * excl)), (cen, ex)
