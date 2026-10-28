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


def query_stats(S, m_pos, cell, excl, k, chunk=2048, sue_k=10, sue_lam=350.0):
    """Affine-invariant per-query statistics (higher = more evidence the top-1 is a real match). Row-chunked."""
    cid, cent = V.map_cells(m_pos, cell); order = np.argsort(cid, kind="stable")
    starts = np.r_[0, np.flatnonzero(np.diff(cid[order])) + 1]
    parts = [_query_stats(S[i:i + chunk], m_pos, cent, order, starts, excl, k, sue_k, sue_lam) for i in range(0, S.shape[0], chunk)]
    return {kk: np.concatenate([p[kk] for p in parts]) for kk in parts[0]}


def _query_stats(S, m_pos, cent, order, starts, excl, k, sue_k, sue_lam):
    S = np.asarray(S, np.float32)
    Z = np.maximum.reduceat(S[:, order], starts, axis=1)                # max similarity per map cell
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
    # SUE (Zaffar CVPR'24): weighted spatial variance of the top-K reference positions (returned negated)
    K = min(sue_k, S.shape[1]); idx = np.argpartition(-S, K - 1, axis=1)[:, :K]
    dk = np.sqrt(np.maximum(2 - 2 * np.take_along_axis(S, idx, 1), 0)); w = np.exp(-sue_lam * (dk - dk.min(1, keepdims=True)))
    w /= w.sum(1, keepdims=True); P = m_pos[idx]; mp = (w[..., None] * P).sum(1, keepdims=True)
    raw = {"maxsim": s1, "margin": s1 - s2, "PA": -d1 / np.maximum(d2, 1e-9), "neg_entropy": (pr * np.log(pr + 1e-12)).sum(1),
           "SUE": -(w[..., None] * (P - mp) ** 2).sum((1, 2))}
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


class SelfCalAA:
    """Deployment-time SelfCal-AA: everything query-independent is precomputed once from the map.
    p(q) = max( recalibrated min(p_maxsim, p_zfar), p_zgap ); accept iff p <= alpha."""

    def __init__(self, m_desc, m_pos, cell=10.0, excl=25.0, k=10, block=300.0, off_d=40.0, stride=2):
        self.m_raw = m_desc.astype(np.float32); self.mu = self.m_raw.mean(0, keepdims=True)
        n = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
        self.m_c = n(self.m_raw - self.mu); self.k, self.excl = k, excl
        cid, self.cent = V.map_cells(m_pos, cell); self.order = np.argsort(cid, kind="stable")
        self.starts = np.r_[0, np.flatnonzero(np.diff(cid[self.order])) + 1]; self.top_cell_dist = None
        self.m_pos = np.asarray(m_pos, float)
        nr = map_null(self.m_raw, m_pos, block, off_d, cell, excl, k, stride)
        nc = map_null(self.m_c, m_pos, block, off_d, cell, excl, k, stride)
        N = np.column_stack([nr["maxsim"], nc["z_far"]]); ok = np.isfinite(N).all(1) & np.isfinite(nc["z_gap"])
        self.null_ms, self.null_zf, self.null_zg = np.sort(N[ok, 0]), np.sort(N[ok, 1]), np.sort(nc["z_gap"][ok])
        nn = ok.sum(); r = np.column_stack([(nn - np.searchsorted(np.sort(N[ok, j]), N[ok, j], "left")) / nn for j in range(2)])
        self.c_null = np.sort(r.min(1)); self.n = nn

    @staticmethod
    def _p(srt, x):
        return (1 + len(srt) - np.searchsorted(srt, x, side="left")) / (1 + len(srt))

    def pvalue(self, q_desc):
        q = np.atleast_2d(q_desc).astype(np.float32)
        s_raw = q @ self.m_raw.T; qc = q - self.mu; qc /= np.linalg.norm(qc, axis=1, keepdims=True); s_c = qc @ self.m_c.T
        top = s_c.argmax(1)  # same retrieval as raw up to centring; use the raw top-1 for the reported match
        top_raw = s_raw.argmax(1); s1_raw = s_raw[np.arange(len(q)), top_raw]
        Z = np.maximum.reduceat(s_c[:, self.order], self.starts, axis=1)
        far = np.sqrt(((self.m_pos[top_raw][:, None, :] - self.cent[None]) ** 2).sum(-1)) > self.excl
        Zf = np.where(far, Z, np.nan); mu_f, sd_f = np.nanmean(Zf, 1), np.nanstd(Zf, 1) + 1e-9
        s1_c = s_c[np.arange(len(q)), top_raw]; best_far = np.nanmax(Zf, 1)
        z_far, z_gap = (s1_c - mu_f) / sd_f, (s1_c - best_far) / sd_f
        m = np.minimum(self._p(self.null_ms, s1_raw), self._p(self.null_zf, z_far))
        p_comb = (1 + np.searchsorted(self.c_null, m, side="right")) / (1 + self.n)
        return np.maximum(p_comb, self._p(self.null_zg, z_gap)), top_raw
