"""Self-calibrating maps: label-free, shift-robust acceptance tests for VPR.

Idea: every query statistic below is invariant to per-query affine score changes (s -> a*s + b, a > 0), which is how
global appearance change (night, rain) mostly acts on retrieval scores. Its null distribution ("query is off-map")
is then estimated from the MAP ITSELF: each map image, with its own spatial block removed from the map, is a
pseudo-query that is off-map by construction. No human labels, no deployment labels. p-values are split-conformal
w.r.t. these map pseudo-queries.
"""
import numpy as np
import vprlib as V


def center(q, m):
    """Hubness reduction: subtract the map mean descriptor, re-normalise (uses the map only)."""
    mu = m.astype(np.float32).mean(0, keepdims=True)
    n = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
    return n(q.astype(np.float32) - mu), n(m.astype(np.float32) - mu)


def query_stats(S, m_pos, cell, excl, k):
    """Affine-invariant per-query statistics (higher = more evidence the top-1 is a real match)."""
    cid, cent = V.map_cells(m_pos, cell); nc = cid.max() + 1
    Z = np.empty((S.shape[0], nc), np.float32)
    for c in range(nc): Z[:, c] = S[:, cid == c].max(1)
    top = S.argmax(1); s1 = S[np.arange(len(top)), top]
    dc = np.sqrt(((m_pos[top][:, None, :] - cent[None]) ** 2).sum(-1))
    Zf = np.where(dc > excl, Z, -np.inf); Zs = -np.sort(-Zf, 1)
    ok = np.isfinite(Zs[:, :k + 1]).all(1)
    top_k = Zs[:, :k + 1]; j = np.arange(2, k + 2)[None, :]
    beta = np.maximum((j * (top_k[:, :-1] - top_k[:, 1:])).mean(1), 1e-9)
    far_vals = np.where(np.isfinite(Zs), Zs, np.nan)
    mu_f, sd_f = np.nanmean(far_vals, 1), np.nanstd(far_vals, 1) + 1e-9
    mu, sd = S.mean(1), S.std(1) + 1e-9
    s2 = -np.partition(-S, 1, axis=1)[:, 1]
    d1, d2 = np.sqrt(np.maximum(2 - 2 * s1, 0)), np.sqrt(np.maximum(2 - 2 * s2, 0))
    z = S / 0.05; z = z - z.max(1, keepdims=True); pr = np.exp(z); pr /= pr.sum(1, keepdims=True)
    raw = {"maxsim": s1, "margin": s1 - s2, "PA": -d1 / np.maximum(d2, 1e-9), "neg_entropy": (pr * np.log(pr + 1e-12)).sum(1)}
    out = {"T_spacing": (s1 - top_k[:, 0]) / beta,                 # EVS spacing statistic (F(2,2k) under ideal null)
           "T_level": (s1 - top_k[:, :k].mean(1)) / beta,         # level above the top-k far maxima, in tail units
           "z_far": (s1 - mu_f) / sd_f,                            # standardised vs far region maxima
           "z_all": (s1 - mu) / sd,                                # classic per-query z-norm
           "z_gap": (s1 - top_k[:, 0]) / sd_f}                     # gap to the best FAR region, in far-sd units
    for kk in out: out[kk] = np.where(ok, out[kk], -np.inf)
    out.update(raw)   # NOT affine-invariant: literature baselines
    return out


def lobo_stats(m_desc, m_pos, block, off_d, q_desc, q_pos, cell, excl, k, chunk=1024):
    """Statistics of queries that are OFF-MAP under leave-one-block-out (NaN for queries never off-map)."""
    bid, _ = V.map_cells(m_pos, block)
    nn = np.empty(len(q_pos), int)
    for i in range(0, len(q_pos), chunk):
        nn[i:i + chunk] = (((q_pos[i:i + chunk, None] - m_pos[None]) ** 2).sum(-1)).argmin(1)
    qb = bid[nn]; out = None
    for b in range(bid.max() + 1):
        qs = np.where(qb == b)[0]
        if not len(qs): continue
        keep = bid != b
        d = np.empty(len(qs))
        for i in range(0, len(qs), chunk):
            d[i:i + chunk] = np.sqrt((((q_pos[qs[i:i + chunk], None] - m_pos[keep][None]) ** 2).sum(-1)).min(1))
        far = qs[d > off_d]
        if not len(far): continue
        st = query_stats(q_desc[far].astype(np.float32) @ m_desc[keep].astype(np.float32).T, m_pos[keep], cell, excl, k)
        if out is None: out = {kk: np.full(len(q_pos), np.nan) for kk in st}
        for kk, v in st.items(): out[kk][far] = v
    return out


def conformal_p(null_stat, stat):
    """Split-conformal p-value of `stat` w.r.t. null calibration statistics (higher stat = less null-like)."""
    ns = np.sort(null_stat[np.isfinite(null_stat)])
    ge = len(ns) - np.searchsorted(ns, stat, side="left")
    return (1 + ge) / (1 + len(ns))


def map_null(m_desc, m_pos, block, off_d, cell, excl, k, stride=2):
    sub = np.arange(0, len(m_desc), stride)
    return lobo_stats(m_desc, m_pos, block, off_d, m_desc[sub], m_pos[sub], cell, excl, k)


def combined_p(null_list, stat_list):
    """Self-calibrated combination of several statistics: c = min_k conformal p_k, re-calibrated on the map null
    with leave-one-out p-values of the null items themselves (valid under exchangeability, power ~ best statistic).
    null_list: [ (n,) null statistics per k ] aligned over the same null items; stat_list: [ (m,) query statistics ]."""
    N = np.column_stack(null_list); ok = np.isfinite(N).all(1); N = N[ok]; n = len(N)
    ranks = np.empty_like(N)
    for k in range(N.shape[1]):
        srt = np.sort(N[:, k]); ge = n - np.searchsorted(srt, N[:, k], side="left")    # includes itself
        ranks[:, k] = ge / n                                                                # LOO: (1 + (ge-1)) / n
    c_null = np.sort(ranks.min(1))
    P = np.column_stack([conformal_p(N[:, k], st) for k, st in enumerate(stat_list)])
    c = P.min(1)
    le = np.searchsorted(c_null, c, side="right")
    return (1 + le) / (1 + n)
