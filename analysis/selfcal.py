"""Self-calibrating maps: label-free, shift-robust acceptance tests for VPR.

Idea: every query statistic below is invariant to per-query affine score changes (s -> a*s + b, a > 0), which is how
global appearance change (night, rain) mostly acts on retrieval scores. Its null distribution ("query is off-map")
is then estimated from the MAP ITSELF: each map image, with its own spatial block removed from the map, is a
pseudo-query that is off-map by construction. No human labels, no deployment labels. p-values are split-conformal
w.r.t. these map pseudo-queries.
"""
import os
import numpy as np
import vprlib as V

# Compute backend for the heavy part (query x map similarities + per-cell statistics). SELFCAL_DEVICE=auto (default:
# CUDA if available, else numpy), cuda, torchcpu (PyTorch on CPU, for testing) or numpy.
try:
    import torch
    torch.backends.cuda.matmul.allow_tf32 = False
except Exception:   # pragma: no cover
    torch = None


def _device():
    want = os.environ.get("SELFCAL_DEVICE", "auto")
    if torch is None or want == "numpy": return None
    if want == "torchcpu": return "cpu"
    if want in ("auto", "cuda") and torch.cuda.is_available(): return "cuda"
    return None


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
           "SUE": -(w[..., None] * (P - mp) ** 2).sum((1, 2)), "mu_far": mu_f, "sd_far": sd_f, "top": top.astype(float)}
    out = {"T_spacing": (s1 - top_k[:, 0]) / beta,                 # EVS spacing statistic (F(2,2k) under ideal null)
           "T_level": (s1 - top_k[:, :k].mean(1)) / beta,         # level above the top-k far maxima, in tail units
           "z_far": (s1 - mu_f) / sd_f,                            # standardised vs far region maxima
           "z_all": (s1 - mu) / sd,                                # classic per-query z-norm
           "z_gap": (s1 - top_k[:, 0]) / sd_f,                     # gap to the best FAR region, in far-sd units
           "d_far": s1 - mu_f,                                     # shift-invariant only (not scale-normalised)
           "d_gap": s1 - top_k[:, 0]}                              # shift-invariant gap to the best far region
    for kk in out: out[kk] = np.where(ok, out[kk], -np.inf)
    out.update(raw)   # NOT affine-invariant: literature baselines
    return out


def qm_stats(q, m, m_pos, cell, excl, k, chunk=2048, sue_k=10, sue_lam=350.0):
    """query_stats(q @ m.T, ...) computed on the GPU when available (identical statistics, float32 similarities)."""
    dev = _device()
    if dev is None:
        return query_stats(np.asarray(q, np.float32) @ np.asarray(m, np.float32).T, m_pos, cell, excl, k, chunk, sue_k, sue_lam)
    cid, cent = V.map_cells(m_pos, cell); nc = int(cid.max()) + 1
    M = torch.as_tensor(np.asarray(m, np.float32), device=dev)
    CID = torch.as_tensor(cid, device=dev, dtype=torch.long)
    CENT = torch.as_tensor(np.asarray(cent, np.float64), device=dev); POS = torch.as_tensor(np.asarray(m_pos, np.float64), device=dev)
    parts = []
    for i in range(0, len(q), chunk):
        Q = torch.as_tensor(np.asarray(q[i:i + chunk], np.float32), device=dev)
        parts.append(_query_stats_torch(Q @ M.T, POS, CENT, CID, nc, excl, k, sue_k, sue_lam))
    return {kk: np.concatenate([p[kk] for p in parts]) for kk in parts[0]}


def _query_stats_torch(S, POS, CENT, CID, nc, excl, k, sue_k, sue_lam):
    n = S.shape[0]; ninf = float("-inf")
    Z = torch.full((n, nc), ninf, device=S.device, dtype=S.dtype).scatter_reduce(1, CID.expand(n, -1), S, reduce="amax", include_self=True)
    s1, top = S.max(1)
    dc = torch.cdist(POS[top], CENT)
    Zf = torch.where(dc > excl, Z, torch.full_like(Z, ninf))
    kk1 = min(k + 1, nc); top_k = torch.topk(Zf, kk1, dim=1).values
    ok = torch.isfinite(top_k).all(1) & (kk1 == k + 1)
    j = torch.arange(2, kk1 + 1, device=S.device, dtype=S.dtype)[None, :]
    beta = torch.clamp((j * (top_k[:, :-1] - top_k[:, 1:])).mean(1), min=1e-9)
    fin = torch.isfinite(Zf); cnt = fin.sum(1).clamp(min=1).double()
    Zd = torch.where(fin, Zf, torch.zeros_like(Zf)).double(); mu_f = Zd.sum(1) / cnt
    sd_f = torch.sqrt((torch.where(fin, Zf.double() - mu_f[:, None], torch.zeros_like(Zd)) ** 2).sum(1) / cnt) + 1e-9
    mu, sd = S.mean(1), S.std(1, unbiased=False) + 1e-9
    s2 = torch.topk(S, 2, dim=1).values[:, 1]
    d1, d2 = torch.sqrt(torch.clamp(2 - 2 * s1, min=0)), torch.sqrt(torch.clamp(2 - 2 * s2, min=0))
    pr = torch.softmax(S / 0.05, dim=1)
    K = min(sue_k, S.shape[1]); sv, idx = torch.topk(S, K, dim=1)
    dk = torch.sqrt(torch.clamp(2 - 2 * sv, min=0)); w = torch.exp(-sue_lam * (dk - dk.min(1, keepdim=True).values))   # float32 as numpy
    w = w / w.sum(1, keepdim=True); P = POS[idx]; mp = (w[..., None] * P).sum(1, keepdim=True)
    s1d, tk0 = s1.double(), top_k[:, 0].double()
    raw = {"maxsim": s1, "margin": s1 - s2, "PA": -d1 / torch.clamp(d2, min=1e-9), "neg_entropy": (pr * torch.log(pr + 1e-12)).sum(1),
           "SUE": -(w[..., None] * (P - mp) ** 2).sum((1, 2)), "mu_far": mu_f, "sd_far": sd_f, "top": top}
    out = {"T_spacing": (s1 - top_k[:, 0]) / beta, "T_level": (s1 - top_k[:, :k].mean(1)) / beta,
           "z_far": (s1d - mu_f) / sd_f, "z_all": (s1 - mu) / sd, "z_gap": (s1d - tk0) / sd_f,
           "d_far": s1d - mu_f, "d_gap": s1 - top_k[:, 0]}
    res = {kk: torch.where(ok, v.double(), torch.full_like(v.double(), ninf)).cpu().numpy() for kk, v in out.items()}
    res.update({kk: v.double().cpu().numpy() for kk, v in raw.items()})
    return res


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
        st = qm_stats(q_desc[far], m_desc[keep], m_pos[keep], cell, excl, k)
        st["top"] = np.flatnonzero(keep)[st["top"].astype(int)].astype(float)   # top-1 index in the FULL map
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


class _AACal:
    """SelfCal-AA p-value against one (sub)set of map-null statistics: max(recalibrated min(p_ms, p_zf), p_zg)."""

    def __init__(self, ms, zf, zg):
        self.ms, self.zf, self.zg, n = np.sort(ms), np.sort(zf), np.sort(zg), len(ms)
        r = np.column_stack([(n - np.searchsorted(srt, x, "left")) / n for srt, x in ((self.ms, ms), (self.zf, zf))])
        self.c_null, self.n = np.sort(r.min(1)), n

    @staticmethod
    def _p(srt, x):
        return (1 + len(srt) - np.searchsorted(srt, x, side="left")) / (1 + len(srt))

    def p(self, ms, zf, zg):
        m = np.minimum(self._p(self.ms, ms), self._p(self.zf, zf))
        p_comb = (1 + np.searchsorted(self.c_null, m, side="right")) / (1 + self.n)
        return np.maximum(p_comb, self._p(self.zg, zg))


class SelfCalTest:
    """The SelfCal-AA decision rule given the map-null statistics N = {ms, zf, zg, sdf} (raw max-sim; centred z_far,
    z_gap, sd_far of the map pseudo-queries):
      1. Mondrian strata: B quantile bins of the null's far-region spread sd_far (B reduced so that every bin keeps
         >= min_per null items; with n_b items the smallest p-value is 1/(n_b+1), so choose min_per >= 1/alpha - 1);
         the AA p-value of a query is computed against the null items of its own bin only.
      2. Domain gate: the query's raw max-sim p-value w.r.t. the whole null must be <= gate (0.8: above the null's
         20 % quantile), otherwise p = 1.
    strata=1, gate=1 recovers the original SelfCal-AA."""

    def __init__(self, N, strata=10, gate=0.8, min_per=50):
        N = {k: np.asarray(N[k], float) for k in ("ms", "zf", "zg", "sdf")}
        ok = np.isfinite(N["ms"]) & np.isfinite(N["zf"]) & np.isfinite(N["zg"]) & np.isfinite(N["sdf"])
        self.B = max(1, min(strata, int(ok.sum()) // min_per)); self.gate = gate
        self.edges = np.quantile(N["sdf"][ok], np.linspace(0, 1, self.B + 1)[1:-1])
        bn = np.digitize(N["sdf"], self.edges)
        self.cal = [_AACal(N["ms"][ok & (bn == b)], N["zf"][ok & (bn == b)], N["zg"][ok & (bn == b)]) for b in range(self.B)]
        self.ms_all, self.n = np.sort(N["ms"][ok]), int(ok.sum())

    def pvalue(self, ms, zf, zg, sdf):
        ms, zf, zg = np.asarray(ms, float), np.asarray(zf, float), np.asarray(zg, float)
        bx = np.digitize(np.nan_to_num(np.asarray(sdf, float), nan=-1e9), self.edges); p = np.ones(len(ms))
        for b in range(self.B):
            mx = bx == b
            if mx.any(): p[mx] = self.cal[b].p(ms[mx], zf[mx], zg[mx])
        return np.where(_AACal._p(self.ms_all, ms) <= self.gate, p, 1.0)


def pack(raw, cen):
    """SelfCalTest inputs from query_stats/lobo_stats dicts of raw (maxsim) and map-centred (z_far, z_gap, sd_far) runs"""
    return dict(ms=raw["maxsim"], zf=cen["z_far"], zg=cen["z_gap"], sdf=cen["sd_far"])


def selfcal_p(raw_null, cen_null, raw_x, cen_x, **kw):
    """SelfCal-AA p-values of queries (raw_x, cen_x) against the map null (raw_null, cen_null); kw -> SelfCalTest"""
    return SelfCalTest(pack(raw_null, cen_null), **kw).pvalue(**pack(raw_x, cen_x))


def run_evidence(p, xpos, W, rho):
    """Sequence evidence for the match of the LAST frame of each window W (rows = L frame indices, oldest first):
    sum of -log p over the trailing run of frames whose consecutive top-1 positions xpos stay within rho of each other.
    A last frame whose match jumps away from its predecessor keeps only its own evidence, so past frames never vouch
    for a match they do not agree with (entering unmapped areas, aliasing)."""
    lp = -np.log(np.clip(p[W], 1e-12, 1)); X = xpos[W]
    if W.shape[1] == 1: return lp[:, 0]
    cons = np.linalg.norm(X[:, 1:] - X[:, :-1], axis=-1) <= rho                  # (n, L-1), pair j = frames j, j+1
    run = np.cumprod(cons[:, ::-1], axis=1).sum(1)                               # consistent pairs ending at the last frame
    take = np.arange(W.shape[1])[None, ::-1] <= run[:, None]                     # last run+1 frames
    return (lp * take).sum(1)


class SelfCalAA:
    """Deployment-time SelfCal-AA: everything query-independent is precomputed once from the map; accept iff p <= alpha.
    Defaults = the adopted rule (Mondrian by sd_far, B=10, raw-similarity gate 0.8); strata=1, gate=1 = original rule."""

    def __init__(self, m_desc, m_pos, cell=10.0, excl=25.0, k=10, block=300.0, off_d=40.0, stride=2,
                 strata=10, gate=0.8, min_per=50):
        self.m_raw = m_desc.astype(np.float32); self.mu = self.m_raw.mean(0, keepdims=True)
        n = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
        self.m_c = n(self.m_raw - self.mu); self.k, self.excl = k, excl
        cid, self.cent = V.map_cells(m_pos, cell); self.order = np.argsort(cid, kind="stable")
        self.starts = np.r_[0, np.flatnonzero(np.diff(cid[self.order])) + 1]
        self.m_pos = np.asarray(m_pos, float)
        nr = map_null(self.m_raw, m_pos, block, off_d, cell, excl, k, stride)
        nc = map_null(self.m_c, m_pos, block, off_d, cell, excl, k, stride)
        self.test = SelfCalTest(dict(ms=nr["maxsim"], zf=nc["z_far"], zg=nc["z_gap"], sdf=nc["sd_far"]), strata, gate, min_per)

    def stats(self, q_desc):
        """per-query statistics (same definitions as query_stats on raw / centred similarities) + raw top-1 index"""
        q = np.atleast_2d(q_desc).astype(np.float32)
        s_raw = q @ self.m_raw.T; qc = q - self.mu; qc /= np.linalg.norm(qc, axis=1, keepdims=True); s_c = qc @ self.m_c.T
        top_raw = s_raw.argmax(1); top_c = s_c.argmax(1); r = np.arange(len(q))
        Z = np.maximum.reduceat(s_c[:, self.order], self.starts, axis=1)
        far = np.sqrt(((self.m_pos[top_c][:, None, :] - self.cent[None]) ** 2).sum(-1)) > self.excl
        Zf = np.where(far, Z, np.nan); mu_f, sd_f = np.nanmean(Zf, 1), np.nanstd(Zf, 1) + 1e-9
        s1_c = s_c[r, top_c]
        return dict(ms=s_raw[r, top_raw], zf=(s1_c - mu_f) / sd_f, zg=(s1_c - np.nanmax(Zf, 1)) / sd_f, sdf=sd_f), top_raw

    def pvalue(self, q_desc):
        X, top_raw = self.stats(q_desc)
        return self.test.pvalue(**X), top_raw
