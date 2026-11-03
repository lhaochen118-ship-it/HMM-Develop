"""FORWARD counterfactual map surgery (RESEARCH_LOG Entry 36): the null of the system's OWN ghost track after an exit.

Diagnosis (cst_audit.py, Entry 36 step 1; labels only to evaluate). Proposition 14 assumes (S3-T): the reported track of a real
off-map segment is exchangeable with the counterfactual ghost track. The CST null track is MP[j_cf], the sequence of PER-FRAME
counterfactual route winners, each from its own surgery and its own estimator (TAO route test): consecutive winners are
unrelated places, so this null track is less coherent than the ghost the system's place chain really follows after an exit
(it moves with the odometry, sticks to the hole edge, locks onto a parallel street). On seeds 0-1, real off-map segments pass
CST in 7-29 % of the deep segments and 14-46 % of the first ones, where Prop. 14 claims <= a/pi (a = 0.05); the CST threshold
is 1.2-2.3 x the oracle one. The CST rules stay valid only because the presence onset must also fire.

Forward surgery. A VIRTUAL EXIT at frame tau of the stream. The map region the robot visits AFTER tau is removed,
    hole(tau) = { m : d(m, X+) <= rho  and  d(m, X+) < d(m, X-) },
X+ = believed positions (system MAP) of the frames after tau up to off_d + h excl of odometry path, X- = those before tau over
the same path (Voronoi cut: the map before the exit point stays, as at a real hole entered at tau), rho = off_d. The system's
OWN place chain is then run FORWARD from its belief at tau on M \\ hole(tau) with the real frames (same emissions, recomputed on
the altered map, same odometry kernel). Its MAP track after tau is the ghost the system would follow if the map ended at tau,
with the stream's images, condition, odometry, temporal dependence and the system's own dynamics.
The place chain is replicated exactly (hmm_diag.DiagFilter with the emission of nav_demo: (s - s_max) / (tau sd_far), tau from
the map null of centred descriptors, sd_far the spread of the far-cell maxima): 99.97 % identical MAP on CMU CosPlace s0.
Null of the shape test (CST-F). For every virtual exit, the frames whose believed position has no remaining map place within rho
are the virtual off-map frames; the spliced track (system MAP up to tau, ghost after) gives their shape residual (the SH / CST
statistic, cpc_geo.shape_resid); the virtual excursion is cut into H-frame segments exactly as a real one
(nav_demo.rule_metrics); eps_F = floor(a (n+1))-th smallest segment minimum per calibration group. A frame passes iff its own
residual <= eps_F. Proposition 16 (cms_theory.md section 4f): under (S3-F) a real off-map segment (any position in its
excursion, boundary included) passes with probability <= a (n+1)/(pi n+1).
CLI: cms_fwd.py <dump> <navcache.npz> <out.npz> [--stride H] [--horizon 6] [--ds name] -> per-exit ghost residuals"""
import sys, os, time
import numpy as np
from scipy.spatial import cKDTree
import scipy.sparse as sp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpc_geo as CG
from geo_cons import window_points, procrustes2

OFF_D = {"boreas": 40.0, "cmu": 40.0, "4s": 40.0, "4sx": 40.0, "oxford": 40.0, "nclt": 20.0, "nord": 10.0, "rc": 40.0, "stlucia": 40.0}


class Chain:
    """hmm_diag.DiagFilter (odometry kernel: Gaussian sigma on the displacement between places within `radius`, normalised over
    the existing neighbours; epsilon mixing) for E beliefs at once, each on its own altered map (keep mask)"""

    def __init__(self, MP, sigma, radius, eps=1e-4):
        MP = np.asarray(MP, float); MP = MP if MP.ndim > 1 else MP[:, None]
        tr = cKDTree(MP); pr = tr.query_pairs(radius, output_type="ndarray"); n = len(MP)
        ii = np.r_[pr[:, 0], pr[:, 1], np.arange(n)]; jj = np.r_[pr[:, 1], pr[:, 0], np.arange(n)]
        o = np.lexsort((jj, ii)); self.ii, self.jj = ii[o], jj[o]
        self.D = MP[self.jj] - MP[self.ii]; self.n, self.sigma, self.eps = n, sigma, eps
        self.W = sp.csr_matrix((np.ones(len(self.ii)), (self.ii, self.jj)), shape=(n, n)); self.W.sort_indices()
        assert np.array_equal(self.W.indices, self.jj)

    def predict(self, B, keep, u, keepf=None, nr=None):
        """B (n, E) beliefs (0 on removed places), keep (n, E) bool, u odometry increment (keepf / nr: cached float mask and
        number of remaining places per column; the arithmetic is the same as computing them here)"""
        d2 = 0.0
        for k in range(self.D.shape[1]): d2 = d2 + (self.D[:, k] - u[k]) ** 2
        self.W.data = np.exp(-0.5 * d2 / self.sigma ** 2)
        keepf = keep.astype(float) if keepf is None else keepf
        z = self.W @ keepf; z[z == 0] = 1.0
        nb = (self.W.T @ (B / z)) * keepf
        nr = np.maximum(keep.sum(0, keepdims=True), 1) if nr is None else nr
        return ((1 - self.eps) * nb + self.eps * nb.sum(0, keepdims=True) / nr) * keepf


class Emission:
    """nav_demo emission of the place chain on an altered map: rel_j = (s_j - max_remaining s) / (tau sd_far), sd_far = population
    std of the maxima of the map cells (selfcal.query_stats: cells of `cell` m) whose centre is farther than excl from the top-1"""

    def __init__(self, MP, cell, excl, tau):
        import vprlib as V
        P = np.asarray(MP, float); P = P if P.ndim > 1 else P[:, None]
        cid, cent = V.map_cells(P, cell); self.cid, self.cent, self.P, self.excl, self.tau = cid, cent, P, excl, tau
        self.nc = int(cid.max()) + 1; self.order = np.argsort(cid, kind="stable"); cs = cid[self.order]
        self.starts = np.r_[0, np.flatnonzero(np.diff(cs)) + 1]

    def __call__(self, s, keep):
        """s (n,) similarities of one frame to the map, keep (n, E) -> log-emission (n, E) (-inf on removed places)"""
        X = np.where(keep, s[:, None].astype(np.float64), -np.inf)       # (n, E)
        smax = X.max(0); top = X.argmax(0)
        Z = np.maximum.reduceat(X[self.order], self.starts, axis=0)    # (n_cells, E) cell maxima over remaining places
        dc = np.linalg.norm(self.cent[:, None, :] - self.P[top][None, :, :], axis=2)   # (n_cells, E)
        F = np.where((dc > self.excl) & np.isfinite(Z), Z, np.nan)
        sd = np.sqrt(np.nanmean((F - np.nanmean(F, 0)) ** 2, 0)) + 1e-9
        sd = np.maximum(np.nan_to_num(sd, nan=1e-4), 1e-4)
        return (X - smax[None, :]) / (self.tau * sd[None, :])


class FwdStats:
    """Entry 37: the system's PRESENCE statistics on an altered map -- route cost C and winner j of the TAO route test over the last
    N frames and the distinctiveness z = (s1 - s_far) / std of cms_exact / cms_vec -- with the hypotheses (top-K of the frame) and the
    look-up tables of every window frame taken on the SAME altered map (first K remaining places of the full ranking, computed from
    the full similarity row), and anchor traces leaving the route chunk where they enter the removed region (the convention of the
    exact full surgery). With nothing removed it reproduces the real statistics (check: cms_fwd.py --check-presence)."""

    def __init__(self, z, ds, K=100, N=20, trim=0.75, delta=8.0, wapp=2.0):
        import cms_vec as CV
        self.CV = CV
        dummy = dict(idx=np.zeros((1, 1), np.int64), sim=np.zeros((1, 1), np.float32), std=np.ones(1, np.float32))
        self.S = CV.setup(z, dummy, ds=ds); self.K, self.N, self.kw = K, N, (trim, delta, wapp)

    def tables(self, X):
        """X (E, n) similarities with -inf on removed places -> top-K idx (E, K), sims (E, K) sorted descending (-inf padded)"""
        K = min(self.K, X.shape[1])
        I = np.argpartition(-X, K - 1, axis=1)[:, :K]; V = np.take_along_axis(X, I, 1)
        o = np.argsort(-V, 1, kind="stable")
        return np.take_along_axis(I, o, 1).astype(np.int32), np.take_along_axis(V, o, 1).astype(np.float32)

    def stats(self, J, V, TI, TV, dl, ow, sd, removed=None):
        """J, V (B, K) top-K of the current frame on each run's map; TI, TV (B, n_w, K) tables of the window frames (current first)
        on the same maps; dl (B, n_w) path lags; ow (B, n_w, d) odometry; sd (B,) row std of the full map row; removed(q) -> bool
        (B, ...) (None: nothing removed). Returns cost (B,), winner j (B,) (-1 if no hypothesis), z (B,)"""
        S, CV = self.S, self.CV; P = S["P"]; excl = S["excl"]; B = len(J); bi = np.arange(B)
        hv = np.isfinite(V); Jc = np.where(hv, J, 0); cnt = hv.sum(1)
        far = (np.linalg.norm(P[Jc] - P[Jc[:, :1]], axis=-1) > excl) & hv
        sfar = np.where(far.any(1), np.where(far, V, -np.inf).max(1), V[bi, np.maximum(cnt - 1, 0)])
        zz = np.where(cnt > 0, (V[:, 0].astype(np.float64) - sfar) / sd, -np.inf)
        cost, jw = np.full(B, np.inf), np.full(B, -1)
        if dl.shape[1] >= 3:
            okp = np.isfinite(TV)
            ks = np.where(okp, S["key_all"][np.where(okp, TI, 0)], np.inf); o = np.argsort(ks, -1, kind="stable")
            TK = np.take_along_axis(ks, o, -1); TS = np.take_along_axis(np.where(okp, TV, -np.inf), o, -1)
            CNT = okp.sum(-1); FB = np.where(CNT > 0, np.where(okp, TV, np.inf).min(-1), -1.0)
            C, j_, _ = CV._route_cost(S, Jc, hv, dl, ow, (TK, TS, FB, CNT), *self.kw, cmask=removed)
            cost = np.where(cnt > 0, C, np.inf); jw = np.where((cnt > 0) & np.isfinite(C), j_, -1)
        return cost, jw, zz

    def run_stats(self, Sq, sd, cum, o, keep, lo, lags, rem, B=None):
        """presence statistics of every lag frame of ONE virtual run (local frame indices of its sequence): tables of the frames
        max(lo, first lag - N + 1) .. last lag on the run's altered map (keep), windows truncated at lo (exits: 0, starts: the
        start frame), anchor traces tested against the run's removed region rem. Returns cost, j, z per lag."""
        import cms_torch as CT
        B = B or (512 if CT.device() == "cuda" else 128)                 # GPU: larger batches
        N = self.N; f0 = max(lo, int(lags.min()) - N + 1); f1 = int(lags.max())
        TI, TV = self.tables(np.where(keep[None, :], Sq[f0:f1 + 1], -np.inf))
        n = len(lags); C = np.full(n, np.inf); J = np.full(n, -1); Z = np.full(n, -np.inf)
        nw = np.array([i - max(lo, i - N + 1) + 1 for i in lags])
        for n_w in np.unique(nw):
            sel = np.flatnonzero(nw == n_w)
            for a in range(0, len(sel), B):
                ss = sel[a:a + B]; ii = lags[ss]; W_ = ii[:, None] - np.arange(n_w)[None, :]
                C[ss], J[ss], Z[ss] = self.stats(TI[ii - f0], TV[ii - f0], TI[W_ - f0], TV[W_ - f0], cum[ii][:, None] - cum[W_], o[W_],
                                                 sd[ii], removed=rem)
        return C, J, Z


class HoleMask:
    """removed region of a virtual run for anchor-trace points q (..., d): within rho of the believed path after the exit and closer
    to it than to the path before (exits, Voronoi cut as for the map places), or within rho of the believed path (starts, Xm None).
    __call__: numpy (KD-trees); torch(q): the same distance tests on the device (brute force over the path points, chunked)."""

    def __init__(self, Xp, Xm, rho):
        self.Xp = np.asarray(Xp, float); self.Xm = None if Xm is None or not len(Xm) else np.asarray(Xm, float); self.rho = float(rho)
        self.tp = cKDTree(self.Xp); self.tm = cKDTree(self.Xm) if self.Xm is not None else None
        self.blo, self.bhi = self.Xp.min(0) - rho - 1e-6, self.Xp.max(0) + rho + 1e-6   # bounding box: most points are far from the hole
        self._t = None

    def __call__(self, q):
        pts = q.reshape(-1, q.shape[-1]); out = np.zeros(len(pts), bool)
        cand = np.flatnonzero(((pts >= self.blo) & (pts <= self.bhi)).all(1))
        if len(cand):
            dp, _ = self.tp.query(pts[cand], distance_upper_bound=self.rho + 1e-9); ins = dp <= self.rho
            if self.tm is not None and ins.any():
                dm, _ = self.tm.query(pts[cand[ins]]); ins[ins] = dp[ins] < dm
            out[cand] = ins
        return out.reshape(q.shape[:-1])

    def torch(self, q):
        import torch
        dev = q.device
        if self._t is None or self._t[0].device != dev:
            f = lambda x: None if x is None else torch.as_tensor(x, dtype=torch.float64, device=dev)
            self._t = (f(self.Xp), f(self.Xm), f(self.blo), f(self.bhi))
        Xp, Xm, blo, bhi = self._t
        pts = q.reshape(-1, q.shape[-1]); out = torch.zeros(pts.shape[0], dtype=torch.bool, device=dev)
        cand = torch.nonzero(((pts >= blo) & (pts <= bhi)).all(1)).flatten()
        mind = lambda P, X: torch.cat([torch.sqrt(sum((P[a:a + 8192, None, d] - X[None, :, d]) ** 2 for d in range(P.shape[1])).min(1).values)
                                       for a in range(0, P.shape[0], 8192)]) if P.shape[0] else P.new_zeros(0)
        if cand.numel():
            P = pts[cand]; dp = mind(P, Xp); ins = dp <= self.rho
            if Xm is not None and bool(ins.any()):
                ii = torch.nonzero(ins).flatten(); dm = mind(P[ii], Xm); ins[ii] = dp[ii] < dm
            out[cand] = ins
        return out.reshape(q.shape[:-1])


def _hole_test(Xp, Xm, rho):
    return HoleMask(Xp, Xm, rho)


BLOCK_SCALES = (0.5, 1.0, 2.0)                                          # Entry 38: block side = scale x the map-null block of the config


class BlockGrid:
    """Entry 38: a square grid of side `size`, rotated by th and shifted by off (in cells), over the planar map coordinates (d = 2;
    d = 1: intervals). keys(X) -> int64 cell key per point, numpy and torch with the same float64 operations in the same order."""

    def __init__(self, size, th, off, d):
        self.size, self.c, self.s, self.off, self.d = float(size), float(np.cos(th)), float(np.sin(th)), [float(o) for o in off], int(d)

    def keys(self, X):
        X = np.asarray(X, float)
        if self.d == 1: return np.floor(X[..., 0] / self.size + self.off[0]).astype(np.int64)
        u0 = (X[..., 0] * self.c + X[..., 1] * self.s) / self.size + self.off[0]
        u1 = (X[..., 1] * self.c - X[..., 0] * self.s) / self.size + self.off[1]
        return np.floor(u0).astype(np.int64) * (1 << 31) + np.floor(u1).astype(np.int64)

    def keys_t(self, X):
        import torch
        if self.d == 1: return torch.floor(X[..., 0] / self.size + self.off[0]).to(torch.int64)
        u0 = (X[..., 0] * self.c + X[..., 1] * self.s) / self.size + self.off[0]
        u1 = (X[..., 1] * self.c - X[..., 0] * self.s) / self.size + self.off[1]
        return torch.floor(u0).to(torch.int64) * (1 << 31) + torch.floor(u1).to(torch.int64)


def block_grid(key, B, d):
    """the random grid of one virtual run (deterministic in key = (global frame index of the exit / start, family)): side B x a scale
    of BLOCK_SCALES, rotation U[0, pi/2), offset U[0, 1) cells -- a prior over block-shaped holes, NOT the benchmark's hole grid"""
    rng = np.random.default_rng([int(k) for k in key] + [38])
    sc = BLOCK_SCALES[int(rng.integers(len(BLOCK_SCALES)))]; th = float(rng.uniform(0.0, np.pi / 2)); off = rng.uniform(0.0, 1.0, 2)
    return BlockGrid(B * sc, th if d == 2 else 0.0, off[:d], d)


class BlockHoleMask:
    """Entry 38: removed region of a BLOCK-shaped virtual run for anchor-trace points q (..., d): inside one of the removed cells of the
    run's grid AND (exits) closer to the believed path after the exit than to the path before (the same Voronoi cut as the map places;
    starts: Xm None). The map places removed by the run are exactly {m : key(m) in removed and d(m, X+) < d(m, X-)}."""

    def __init__(self, grid, removed, Xp, Xm, P_removed):
        self.g, self.rem = grid, np.unique(np.asarray(removed, np.int64))
        self.Xp = np.asarray(Xp, float); self.Xm = None if Xm is None or not len(Xm) else np.asarray(Xm, float)
        self.tp = cKDTree(self.Xp); self.tm = cKDTree(self.Xm) if self.Xm is not None else None
        P_removed = np.asarray(P_removed, float); pad = grid.size * 1.5 + 1e-6      # cells reach <= sqrt(2) side beyond their places
        self.blo, self.bhi = P_removed.min(0) - pad, P_removed.max(0) + pad
        self._t = None

    def __call__(self, q):
        pts = q.reshape(-1, q.shape[-1]); out = np.zeros(len(pts), bool)
        cand = np.flatnonzero(((pts >= self.blo) & (pts <= self.bhi)).all(1)) if len(self.rem) else np.zeros(0, int)
        if len(cand):
            k = self.g.keys(pts[cand]); pos = np.clip(np.searchsorted(self.rem, k), 0, len(self.rem) - 1); ins = self.rem[pos] == k
            if self.tm is not None and ins.any():
                P = pts[cand[ins]]; dp, _ = self.tp.query(P); dm, _ = self.tm.query(P); ins[ins] = dp < dm
            out[cand] = ins
        return out.reshape(q.shape[:-1])

    def torch(self, q):
        import torch
        dev = q.device
        if self._t is None or self._t[0].device != dev:
            f = lambda x, dt=torch.float64: None if x is None else torch.as_tensor(x, dtype=dt, device=dev)
            self._t = (f(self.Xp), f(self.Xm), f(self.blo), f(self.bhi), f(self.rem, torch.int64))
        Xp, Xm, blo, bhi, rem = self._t
        pts = q.reshape(-1, q.shape[-1]); out = torch.zeros(pts.shape[0], dtype=torch.bool, device=dev)
        if not len(self.rem): return out.reshape(q.shape[:-1])
        cand = torch.nonzero(((pts >= blo) & (pts <= bhi)).all(1)).flatten()
        mind = lambda P, X: torch.cat([torch.sqrt(sum((P[a:a + 8192, None, d] - X[None, :, d]) ** 2 for d in range(P.shape[1])).min(1).values)
                                       for a in range(0, P.shape[0], 8192)]) if P.shape[0] else P.new_zeros(0)
        if cand.numel():
            P = pts[cand]; k = self.g.keys_t(P); pos = torch.searchsorted(rem, k).clamp(max=rem.shape[0] - 1); ins = rem[pos] == k
            if Xm is not None and bool(ins.any()):
                ii = torch.nonzero(ins).flatten(); ins[ii] = mind(P[ii], Xp) < mind(P[ii], Xm)
            out[cand] = ins
        return out.reshape(q.shape[:-1])


def chain_tau(M, MP, c):
    """emission scale of the place chain exactly as nav_demo: std of the map-null z_far of centred descriptors * sqrt(6) / pi"""
    import selfcal as SC
    nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True); mu = M.mean(0, keepdims=True); Mc = nrm(M - mu)
    Nc = SC.map_null(Mc, MP, c["block"], c["off_d"], c["cell"], c["excl"], c["k"], stride=1)
    zf = Nc["z_far"][np.isfinite(Nc["z_far"])]
    return float(zf.std() * np.sqrt(6) / np.pi)


def fwd_null(z, b, q, M, c, stride=None, horizon=6.0, rho=None, verbose=False, tau=None, starts=True, presence=False, start_h=None,
             ds=None, N=20, K=100, shape="corridor"):
    """forward counterfactual ghost tracks of every virtual exit (one per `stride` frames) and their shape residuals.
    q (n_q, d) query descriptors, M (n_map, d) reduced-map descriptors, c = sc_eval.CFG entry. Returns dict(recs, agree, tau).
    Entry 37: presence=True also runs the system's PRESENCE statistics forward on each run's altered map (FwdStats: route cost,
    winner, distinctiveness of every frame of the run, windows on the altered map; virtual starts: windows truncated at the start);
    start_h = horizon of the virtual starts in excl of path (None: 3 excl as Entry 36; "full": the exits' horizon off_d + h excl,
    hole = corridor rho around the whole believed path of the run).
    Entry 38: shape="block" -- every virtual run removes whole CELLS of its own random grid (block_grid: side c["block"] x {0.5, 1, 2},
    random rotation and offset): the cells holding a map place within rho of the run's believed path (exits: then the Voronoi cut
    against the path before the exit, so the map before the exit point stays), i.e. holes with the lateral extent of a missing map
    area (parallel and crossing streets of those cells removed too) instead of a tube of radius rho along the path."""
    MP = np.asarray(z["MP"], float); MP2 = MP if MP.ndim > 1 else MP[:, None]; hz = list(z["hz"])
    Pl = MP2[:, hz] if MP2.shape[1] > 2 else MP2                        # planar positions (residuals, hole geometry)
    excl = float(z["excl"]); H = int(z["H"]); rho = c["off_d"] if rho is None else rho
    stride_path = None
    if isinstance(stride, str) and stride.endswith("x"): stride_path, stride = float(stride[:-1]) * excl, None   # exits every k excl of path
    stride = stride or H
    nord = MP2.shape[1] == 1; ch = Chain(MP2, 1.0 if nord else 2.0, 6.0 if nord else 15.0)
    tau = chain_tau(M, MP, c) if tau is None else tau; em = Emission(MP2, c["cell"], c["excl"], tau)
    U = np.asarray(z["U"], float); U = U if U.ndim > 1 else U[:, None]
    o_all = z["o_q"]; o_all = (o_all[:, hz] if o_all.ndim > 1 and o_all.shape[1] > 2 else o_all).astype(float); o_all = o_all if o_all.ndim > 1 else o_all[:, None]
    est_c = np.asarray(z["est_c"]); xc = Pl[est_c]; Dpath = rho + horizon * excl
    tree = cKDTree(Pl); recs = []; n_ag = [0, 0]; t0 = time.time()
    fs = FwdStats(z, ds, K=K, N=N) if presence else None
    shs = list(start_h) if isinstance(start_h, (tuple, list)) else [start_h]   # one virtual-start family per horizon: modes 1, 2, ...
    Dss = [3.0 * excl if h_ is None else (Dpath if h_ == "full" else float(h_) * excl) for h_ in shs]
    for si, idx in enumerate(b["seqs"]):
        L = len(idx); o = o_all[idx]; cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        Sq = q[idx].astype(np.float32) @ M.T                            # (L, n_map) similarities (q may be kept in fp16: memory)
        sdq = np.maximum(Sq.std(1, ddof=1), 1e-6) if presence else None  # row std of the full map row (as cms_exact.topk_long)
        # exact replica of the system's place chain on the unaltered map (beliefs at the exit frames)
        keep1 = np.ones((ch.n, 1), bool); bel = np.full((ch.n, 1), 1.0 / ch.n); exits = {}; rep = np.empty(L, int); last_ex = 0.0
        for i in range(L):
            if i > 0: bel = ch.predict(bel, keep1, U[idx[i]])
            E = em(Sq[i], keep1); bel = bel * np.exp(E - E.max(0, keepdims=True)); bel /= bel.sum(0, keepdims=True)
            rep[i] = int(bel[:, 0].argmax())
            if i > 0 and ((stride_path is None and i % stride == 0) or (stride_path is not None and cum[i] >= last_ex + stride_path)):
                exits[i] = bel[:, 0].copy(); last_ex = cum[i]
        n_ag[0] += int((rep == est_c[idx]).sum()); n_ag[1] += L
        act, ex_list, ptr = [], sorted(exits), 0; cache_ = [None, None, None, None]
        for i in range(L):
            while ptr < len(ex_list) and ex_list[ptr] == i:
                ie = ex_list[ptr]; ptr += 1
                post = np.flatnonzero((cum > cum[ie]) & (cum <= cum[ie] + Dpath)); post = post[post > ie]
                pre = np.flatnonzero((cum <= cum[ie]) & (cum >= cum[ie] - Dpath))
                if len(post) < H: continue
                dpost, _ = cKDTree(xc[idx[post]]).query(Pl); dpre, _ = cKDTree(xc[idx[pre]]).query(Pl)
                if shape == "block":                                    # Entry 38: whole cells of the run's own random grid
                    G = block_grid((idx[ie], 0), c["block"], Pl.shape[1]); cid = G.keys(Pl); rc = np.unique(cid[dpost <= rho])
                    hole = np.isin(cid, rc) & (dpost < dpre)
                else:
                    hole = (dpost <= rho) & (dpost < dpre)
                if hole.all() or not hole.any(): continue
                Bv = np.where(hole, 0.0, exits[ie]); s_ = Bv.sum()
                if s_ > 0:
                    a0 = dict(ie=ie, keep=~hole, B=Bv / s_, last=post[-1], g={}, mode=0)
                    if presence:
                        a0.update(lo=0, rem=(BlockHoleMask(G, rc, xc[idx[post]], xc[idx[pre]], Pl[hole]) if shape == "block"
                                             else _hole_test(xc[idx[post]], xc[idx[pre]], rho)))
                    act.append(a0)
                if starts:
                    # VIRTUAL START (truncated shape windows): the sequence starts at tau inside a hole -> the chain restarts from the
                    # uniform belief on the map with the corridor of radius rho around the believed path of the next Ds removed
                    # (Entry 36: Ds = 3 excl; Entry 37 "full": the exits' horizon), no Voronoi cut (nothing before the start), residual
                    # windows truncated at tau (as at a real sequence start); Entry 37: presence windows truncated at tau too
                    for md_, Ds in enumerate(Dss, 1):
                        ps_ = post[cum[post] <= cum[ie] + Ds]
                        if len(ps_) < 3: continue
                        Xs_ = xc[idx[np.r_[ie, ps_]]]; dps, _ = cKDTree(Xs_).query(Pl); hs = dps <= rho
                        if shape == "block":
                            Gs = block_grid((idx[ie], md_), c["block"], Pl.shape[1]); cs_ = Gs.keys(Pl); rcs = np.unique(cs_[hs]); hs = np.isin(cs_, rcs)
                        if not hs.all():
                            Bs = np.where(hs, 0.0, 1.0); a1 = dict(ie=ie, keep=~hs, B=Bs / Bs.sum(), last=ps_[-1], g={ie: None}, mode=md_)
                            if presence: a1.update(lo=ie, rem=(BlockHoleMask(Gs, rcs, Xs_, None, Pl[hs] if hs.any() else Xs_) if shape == "block"
                                                               else _hole_test(Xs_, None, rho)))
                            act.append(a1)
            live = [a for a in act if a["ie"] < i <= a["last"] or (a["mode"] >= 1 and a["ie"] == i)]
            if live:
                key_ = tuple(id(a) for a in live)
                if key_ != cache_[0]:
                    KP = np.stack([a["keep"] for a in live], 1); cache_[:] = [key_, KP, KP.astype(float), np.maximum(KP.sum(0, keepdims=True), 1)]
                KP, KPf, NR_ = cache_[1:]
                BB = np.stack([a["B"] for a in live], 1)
                mv = np.array([a["ie"] < i for a in live])               # a virtual start's first frame has no motion step
                if mv.all(): BB = ch.predict(BB, KP, U[idx[i]], KPf, NR_)
                elif mv.any(): BB[:, mv] = ch.predict(BB[:, mv], KP[:, mv], U[idx[i]])
                E = em(Sq[i], KP)
                BB = BB * np.exp(E - E.max(0, keepdims=True)); BB = BB / np.maximum(BB.sum(0, keepdims=True), 1e-300)
                g = BB.argmax(0)
                for e_, a in enumerate(live): a["B"] = BB[:, e_]; a["g"][i] = int(g[e_])
            done_ = [a for a in act if i >= a["last"]]; act = [a for a in act if i < a["last"]]
            for a in done_:
                lags = np.array(sorted(a["g"]))
                if not len(lags): continue
                track = xc[idx].copy(); track[lags] = Pl[[a["g"][k] for k in lags]]
                rr = np.full(len(lags), np.nan)
                for q_, k in enumerate(lags):
                    w = window_points(o, cum, k, 3.0 * excl, 0.2 * excl)
                    if a["mode"] >= 1: w = w[w >= a["ie"]]                   # window truncated at the virtual start
                    if len(w) < 3 or cum[k] - cum[w[0]] < excl: continue
                    if Pl.shape[1] == 1:
                        d = (track[w, 0] - track[w, 0].mean()) - (o[w, 0] - o[w, 0].mean()); rr[q_] = float(np.sqrt((d ** 2).mean()))
                    else:
                        rr[q_] = procrustes2(track[w], o[w])[0]
                rem = a["keep"]; nb_ = tree.query_ball_point(xc[idx[lags]], rho)
                voff = np.array([not rem[np.asarray(l_, int)].any() for l_ in nb_])
                gerr = np.linalg.norm(track[lags] - xc[idx[lags]], axis=1)   # ghost displacement from the belief
                rec = (idx[a["ie"]], idx[lags], rr, voff, gerr, a["mode"], np.array([a["g"][k] for k in lags], np.int32))
                if presence:                                            # the system's presence statistics on this run's altered map
                    C_, j_, z_ = fs.run_stats(Sq, sdq, cum, o, a["keep"], a["lo"], lags, a["rem"])
                    rec = rec + (C_.astype(np.float32), z_.astype(np.float32), j_.astype(np.int32))
                recs.append(rec)
        if verbose: print(f"  seq {si} {L} frames, {len(exits)} exits, {time.time() - t0:.0f}s", flush=True)
    return dict(recs=recs, agree=n_ag[0] / max(n_ag[1], 1), tau=tau, rho=float(rho), stride=float(stride_path / excl) if stride_path else int(stride), horizon=horizon,
                start_h=np.array([D_ / excl for D_ in Dss]), presence=bool(presence), n_frames=int(n_ag[1]))


def fwd_segments(recs, H, mode=0):
    """[(exit frame, frames, position in the virtual excursion, segment-min residual)] of the virtual off-map segments of the
    virtual exits (mode 0) or virtual starts (mode 1); segments start at the first virtual off-map frame, every H frames, as
    nav_demo.rule_metrics; NaN residuals (windows shorter than 1 excl) never pass"""
    out = []
    for rc in recs:
        if (rc[5] if len(rc) > 5 else 0) != mode: continue
        ex, fr, rr, voff = rc[:4]; i = 0
        while i < len(fr) and not voff[i]: i += 1
        j = i
        while j < len(fr) and voff[j]: j += 1
        for p_, k in enumerate(range(i, j - H + 1, H)):
            v = rr[k:k + H]; v = v[np.isfinite(v)]
            out.append((ex, fr[k:k + H], p_, float(v.min()) if len(v) else np.inf))
    return out


def joint_segments(recs, H, lo, kap, llc, Hreal, jref, P, excl, p_tr=0.01, g_rad=1.0, mode=0, nan_pass=False):
    """JOINT forward simulation of the whole decision (Entry 36, CST-J). Along every virtual run the presence chain is continued from
    the REAL state at the exit (log-odds lo and hysteresis state Hreal of the exit frame; a virtual start begins at odds 1, off) with
    the counterfactual log-LR llc of the frames after the exit (the off-map null of the presence evidence, as in Theorems 6-6'),
    onset when log-odds > kappa, persistence while > 0; the agreement gate compares the ghost place with the counterfactual route
    winner jref (|.| <= g excl). A virtual frame is a REPORT CANDIDATE iff the virtual chain is on, the gate agrees and its shape
    residual is finite. Returns [(exit, frames, position, critical residual)] per virtual off-map segment: the smallest residual among
    its report candidates (inf if none) = the largest tolerance at which the system would NOT report in that segment."""
    g = lambda l: np.log((1 / (1 + np.exp(-l)) * (1 - p_tr) + (1 - 1 / (1 + np.exp(-l))) * p_tr) /
                         (1 - (1 / (1 + np.exp(-l)) * (1 - p_tr) + (1 - 1 / (1 + np.exp(-l))) * p_tr)))
    out = []
    for rc in recs:
        if rc[5] != mode: continue
        ex, fr, rr, voff, _, _, gi = rc[:7]
        l, h = (float(lo[ex]), bool(Hreal[ex])) if mode == 0 else (None, False)
        cand = np.zeros(len(fr), bool)
        for q_, s_ in enumerate(fr):
            l = float(np.clip((g(l) if l is not None else 0.0) + llc[s_], -50, 50))
            h = (l > 0) if h else (l > kap[s_])
            ag = gi[q_] >= 0 and np.linalg.norm(P[gi[q_]] - P[jref[s_]]) <= excl * g_rad
            cand[q_] = h and ag and (np.isfinite(rr[q_]) or nan_pass)
        i = 0
        while i < len(fr) and not voff[i]: i += 1
        j = i
        while j < len(fr) and voff[j]: j += 1
        for p_, k in enumerate(range(i, j - H + 1, H)):
            c = cand[k:k + H]; v = np.where(np.isfinite(rr[k:k + H]), rr[k:k + H], -np.inf)   # NaN window (< 1 excl): passes if nan_pass
            out.append((ex, fr[k:k + H], p_, float(v[c].min()) if c.any() else np.inf))
    return out


def _pad(lst, fill, dt):
    L = max(len(x) for x in lst); out = np.full((len(lst), L), fill, dt)
    for i, x in enumerate(lst): out[i, :len(x)] = x
    return out


def joint_crit(recs, H, lo, kap, Hreal, P, excl, llv, jrv, p_tr=0.01, g_rad=1.0, mode=0, nan_pass=False):
    """Entry 37: joint_segments vectorised over the virtual runs of one mode, with the presence log-LR llv[i] and the route winner
    jrv[i] of record i given per lag (Entry 37 forward presence: the system's statistics re-run on the run's altered map, mapped to
    log-LR by the system's own transform; or llc / j_cf of the full surgery at those frames, which reproduces joint_segments).
    Same recursion: exits continue the REAL chain state at the exit (log-odds lo, hysteresis Hreal), starts begin at odds 1 (off);
    onset when log-odds > kappa, persistence while > 0; report candidate iff chain on, gate |P[ghost] - P[winner]| <= g excl and a
    finite residual (or any residual if nan_pass). Returns [(exit, frames, position, critical residual)] per virtual off-map segment."""
    sel = [i for i, r in enumerate(recs) if r[5] == mode]
    if not sel: return []
    g = lambda l: np.log((1 / (1 + np.exp(-l)) * (1 - p_tr) + (1 - 1 / (1 + np.exp(-l))) * p_tr) /
                         (1 - (1 / (1 + np.exp(-l)) * (1 - p_tr) + (1 - 1 / (1 + np.exp(-l))) * p_tr)))
    FR = _pad([recs[i][1] for i in sel], -1, np.int64); valid = FR >= 0; FR0 = np.where(valid, FR, 0)
    LL = _pad([np.asarray(llv[i], float) for i in sel], 0.0, float); RR = _pad([recs[i][2] for i in sel], np.nan, float)
    GI = _pad([recs[i][6] for i in sel], -1, np.int64); JR = _pad([np.asarray(jrv[i]) for i in sel], -1, np.int64)
    ex = np.array([recs[i][0] for i in sel]); KAP = np.asarray(kap, float)[FR0]
    if mode == 0: l = np.asarray(lo, float)[ex].copy(); h = np.asarray(Hreal, bool)[ex].copy()
    else: l = np.zeros(len(sel)); h = np.zeros(len(sel), bool)
    cand = np.zeros(FR.shape, bool); candn = np.zeros(FR.shape, bool); LO = np.zeros(FR.shape)
    for k in range(FR.shape[1]):
        l = np.clip((0.0 if (k == 0 and mode != 0) else g(l)) + LL[:, k], -50, 50)   # a virtual start begins at odds 1
        h = np.where(h, l > 0, l > KAP[:, k]); LO[:, k] = l
        okg = (GI[:, k] >= 0) & (JR[:, k] >= 0)
        ag = okg & (np.linalg.norm(P[np.where(okg, GI[:, k], 0)] - P[np.where(okg, JR[:, k], 0)], axis=1) <= excl * g_rad)
        cand[:, k] = valid[:, k] & h & ag & (np.isfinite(RR[:, k]) | nan_pass)
        candn[:, k] = valid[:, k] & h & ag & np.isnan(RR[:, k])
    out = []
    for r_, i in enumerate(sel):
        fr, rr, voff = recs[i][1], recs[i][2], recs[i][3]; n_ = len(fr); a = 0
        while a < n_ and not voff[a]: a += 1
        e = a
        while e < n_ and voff[e]: e += 1
        for p_, k in enumerate(range(a, e - H + 1, H)):
            c = cand[r_, k:k + H]; v = np.where(np.isfinite(rr[k:k + H]), rr[k:k + H], -np.inf); cn = candn[r_, k:k + H]
            # (exit, frames, position, critical residual, Entry 37: max log-odds of the short-window report candidates, short-window flag)
            out.append((recs[i][0], fr[k:k + H], p_, float(v[c].min()) if c.any() else np.inf,
                        float(LO[r_, k:k + H][cn].max()) if cn.any() else -np.inf, bool(np.isnan(rr[k:k + H]).any())))
    return out


def eps_start_pos(z, b, segs, a, groups, pos_frame):
    """Entry 37: thresholds of the VIRTUAL-START null per position since the sequence start (known without labels: frame index // H).
    Per calibration group, positions are merged in order into bins of >= 2 / (a/2) segments; in a bin whose virtual segments contain
    short-window frames (shape window < 1 excl) the budget is split: tolerance eps = floor(a/2 (n+1))-th smallest critical residual,
    onset kappa' = ceil((1 - a/2)(n+1))-th smallest max log-odds of the short-window report candidates (report on a short window iff
    log-odds > kappa'); other bins: eps at level a, no short-window frames. P(report in a virtual-start segment of the bin) <= a (union).
    Frames beyond the last bin use the last (deepest) bin. Returns eps (n,), kappa' (n,) per frame."""
    import cms as CMS
    n = len(z["cond"]); eps = np.full(n, -np.inf); kap = np.full(n, np.inf)
    if not segs: return eps, kap
    ex = np.array([s_[0] for s_ in segs]); pos = np.array([s_[2] for s_ in segs]); cf = np.array([s_[3] for s_ in segs], float)
    cn = np.array([s_[4] for s_ in segs], float); hn = np.array([s_[5] for s_ in segs], bool)
    lo_q = lambda v, a_: (np.sort(v)[int(np.floor(a_ * (len(v) + 1))) - 1] if int(np.floor(a_ * (len(v) + 1))) >= 1 else -np.inf)
    def hi_q(v, a_):
        k = int(np.ceil((1 - a_) * (len(v) + 1))); return np.sort(v)[k - 1] if k <= len(v) else np.inf
    nmin = int(np.ceil(2.0 / (a / 2)))
    for sqs, cqs in (groups or CMS.cal_groups(z, b["seqs"])):
        m = np.concatenate(sqs); s_ = np.isin(ex, np.concatenate(cqs)); P_, C_, N_, Hn = pos[s_], cf[s_], cn[s_], hn[s_]
        if not len(P_): continue
        bins, cur = [], []
        for p_ in np.unique(P_):
            cur.append(p_)
            if (np.isin(P_, cur)).sum() >= nmin: bins.append(cur); cur = []
        if cur:
            if bins: bins[-1] = bins[-1] + cur
            else: bins.append(cur)
        th = []
        for bp in bins:
            sel = np.isin(P_, bp)
            if Hn[sel].any(): th.append((max(bp), lo_q(C_[sel], a / 2), hi_q(N_[sel], a / 2)))
            else: th.append((max(bp), lo_q(C_[sel], a), np.inf))
        hi_p = np.array([t[0] for t in th]); bi = np.minimum(np.searchsorted(hi_p, pos_frame[m], side="left"), len(th) - 1)
        eps[m] = np.array([t[1] for t in th])[bi]; kap[m] = np.array([t[2] for t in th])[bi]
    return eps, kap


def eps_fwd(z, b, segs, a, mode="pooled", groups=None):
    """CST-F / CST-J threshold per frame: floor(a (n+1))-th smallest virtual-segment value per calibration group (cms.cal_groups; a
    virtual segment belongs to the group of its exit frame). mode "pooled", "minbin" (positions merged in order until a bin has
    >= 2/a segments, eps = min over bins), "bins3" (edge / early / deep) or "minpos" (min of the per-position thresholds).
    Vectorised (same result as the per-segment loops of the first version)."""
    import cms as CMS
    eps = np.full(len(z["cond"]), -np.inf)
    if not segs: return eps
    ex = np.array([s_[0] for s_ in segs]); pos = np.array([s_[2] for s_ in segs]); val = np.array([s_[3] for s_ in segs], float)
    def q(v):
        v = np.sort(v); k = int(np.floor(a * (len(v) + 1))); return v[k - 1] if k >= 1 else -np.inf
    nmin = int(np.ceil(2.0 / a))
    for sqs, cqs in (groups or CMS.cal_groups(z, b["seqs"])):
        m = np.concatenate(sqs); sel = np.isin(ex, np.concatenate(cqs)); P_, V_ = pos[sel], val[sel]
        if not len(V_): eps[m] = -np.inf; continue
        if mode == "pooled": e = q(V_)
        elif mode in ("minbin", "bins3"):
            if mode == "minbin": edges = [(p_, p_) for p_ in np.unique(P_)]
            else: edges = [(0, 0), (1, 2), (3, 10 ** 9)]
            bins, cur = [], []
            for lo_, hi_ in edges:
                cur.append(V_[(P_ >= lo_) & (P_ <= hi_)])
                if sum(len(c) for c in cur) >= nmin: bins.append(np.concatenate(cur)); cur = []
            if cur:
                rest = np.concatenate(cur)
                if bins: bins[-1] = np.concatenate([bins[-1], rest])
                else: bins.append(rest)
            e = min([q(v) for v in bins] or [-np.inf])
        else:
            e = min([q(V_[P_ == p_]) for p_ in np.unique(P_)] or [-np.inf])
        eps[m] = e
    return eps


def save(of, R, extra=None):
    recs = R["recs"]; cat = lambda k: np.concatenate([r[k] for r in recs]) if recs else np.zeros(0)
    np.savez_compressed(of, ex=np.concatenate([np.full(len(r[1]), r[0]) for r in recs]).astype(np.int32) if recs else np.zeros(0, np.int32),
                        fr=cat(1).astype(np.int32), rr=cat(2).astype(np.float32), voff=cat(3).astype(bool), gerr=cat(4).astype(np.float32),
                        mode=np.array([r[5] for r in recs], np.int8), gidx=cat(6).astype(np.int32),
                        lens=np.array([len(r[1]) for r in recs], np.int32), agree=R["agree"], tau=R["tau"], rho=R["rho"], stride=R["stride"],
                        horizon=R["horizon"], start_h=np.atleast_1d(R.get("start_h", 3.0)), n_frames=R.get("n_frames", 0),
                        **(dict(costf=cat(7).astype(np.float32), zf=cat(8).astype(np.float32), jf=cat(9).astype(np.int32))
                           if recs and len(recs[0]) > 7 else {}), **(extra or {}))


def load_recs(f):
    q = np.load(f); cut = np.cumsum(q["lens"])[:-1]
    sp_ = lambda k: np.split(q[k], cut)
    md = q["mode"] if "mode" in q.files else np.zeros(len(q["lens"]), np.int8)
    gi = sp_("gidx") if "gidx" in q.files else [np.full(len(x), -1, np.int32) for x in sp_("fr")]
    base = [(int(e[0]), f_, r_, v_, g_, int(m_), gg) for e, f_, r_, v_, g_, m_, gg in zip(sp_("ex"), sp_("fr"), sp_("rr"), sp_("voff"), sp_("gerr"), md, gi)]
    if "costf" in q.files:                                              # Entry 37: forward presence statistics per lag
        base = [r + (c_, zz_, jj_) for r, c_, zz_, jj_ in zip(base, sp_("costf"), sp_("zf"), sp_("jf"))]
    return [r for r in base if len(r[1])], q


def merge(of, parts):
    """merge the part files of one run (cms_fwd.py --part k/n): records concatenated, replica agreement weighted by frames"""
    recs, agr, nf, R0 = [], 0.0, 0, None
    for f in parts:
        rc, q = load_recs(f); recs += rc; n_ = int(q["n_frames"]); agr += float(q["agree"]) * n_; nf += n_
        R0 = R0 or {k: q[k] for k in ("tau", "rho", "stride", "horizon", "start_h")}
    R = dict(recs=sorted(recs, key=lambda r: (r[5], r[0])), agree=agr / max(nf, 1), n_frames=nf, presence=len(recs[0]) > 7 if recs else False, **R0)
    save(of, R); return R


def part_seqs(seqs, k, n):
    """sequences of part k of n: longest-first greedy balance of the frame counts (deterministic)"""
    load = [0] * n; own = [[] for _ in range(n)]
    for i in sorted(range(len(seqs)), key=lambda i: (-len(seqs[i]), i)):
        j = int(np.argmin(load)); own[j].append(i); load[j] += len(seqs[i])
    return [seqs[i] for i in sorted(own[k])]


def check_presence(z, b, q, M, st, ds, nseq=None, N=20):
    """FwdStats with nothing removed must reproduce the real cost / winner / z of the published exact cache (cms_exact)"""
    fs = FwdStats(z, ds, N=N); o_all = fs.S["o"]; seqs = b["seqs"] if nseq is None else b["seqs"][:nseq]; t0 = time.time()
    got = {k: [] for k in ("cost", "j", "z")}; ref = {k: [] for k in ("cost", "j", "z")}; nf = 0
    for idx in seqs:
        L = len(idx); o = o_all[idx]; cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        Sq = q[idx].astype(np.float32) @ M.T; sd = np.maximum(Sq.std(1, ddof=1), 1e-6); TI, TV = fs.tables(Sq)
        for n_w in range(1, N + 1):
            ii = [i for i in range(L) if len(range(max(0, i - N + 1), i + 1)) == n_w]
            if not ii: continue
            W_ = np.stack([np.arange(max(0, i - N + 1), i + 1)[::-1] for i in ii]); ii = np.array(ii)
            C_, j_, z_ = fs.stats(TI[ii], TV[ii], TI[W_], TV[W_], cum[ii][:, None] - cum[W_], o[W_], sd[ii])
            if n_w < 3: C_[:] = np.inf; j_[:] = -1                       # cms_vec: no route test on windows < 3 frames
            for k, v in (("cost", C_), ("j", j_), ("z", z_)): got[k].append(v); ref[k].append(np.asarray(st[k])[idx[ii]])
        nf += L
    for k in got:
        a, r_ = np.concatenate(got[k]).astype(float), np.concatenate(ref[k]).astype(float)
        same = np.isclose(a, r_, rtol=1e-4, atol=1e-4) | (np.isinf(a) & np.isinf(r_))
        print(f"{k:5s} equal {same.mean():.5f}  max|diff| {np.nanmax(np.abs(np.where(same, 0, a - r_))) if (~same).any() else 0:.3g}")
    print(f"{nf} frames, {1e3 * (time.time() - t0) / max(nf, 1):.2f} ms/frame")


def main():
    if sys.argv[1] == "--merge":                                        # cms_fwd.py --merge <out.npz> <part files...>
        R = merge(sys.argv[2], sys.argv[3:]); print(f"{sys.argv[2]}: {len(R['recs'])} runs from {len(sys.argv) - 3} parts"); return
    dump, zf, of = sys.argv[1:4]
    import nav_rules as NR, topk_dump as TKD
    from sc_eval import CFG
    z = np.load(zf, allow_pickle=True); zz = {k: z[k] for k in z.files}; b = NR.base_parts(z)
    tag = os.path.basename(zf)[len("navcache_"):].rsplit("_", 2)[0]; desc = os.path.basename(zf).rsplit("_", 2)[1]
    ds = sys.argv[sys.argv.index("--ds") + 1] if "--ds" in sys.argv else (("4s:" + tag[3:]) if tag.startswith("4s_") else (("nclt:" + tag[5:]) if tag.startswith("nclt_") else tag))
    base = ds.split(":")[0]; c = CFG["cmu"] if base in ("4s", "4sx", "boreas") else CFG[base]   # as nav_demo.main
    stride = sys.argv[sys.argv.index("--stride") + 1] if "--stride" in sys.argv else None
    stride = None if stride is None else (stride if stride.endswith("x") else int(stride))
    hor = float(sys.argv[sys.argv.index("--horizon") + 1]) if "--horizon" in sys.argv else 6.0
    t0 = time.time(); ep = TKD.load(dump, ds, desc); q = ep.q; M = ep.m.astype(np.float32)[z["kidx"]]   # q stays fp16 (cast per sequence)
    assert len(q) == len(z["top"])
    if "--check-presence" in sys.argv:                                  # Entry 37: FwdStats on the unaltered map == the real statistics
        st = dict(np.load(sys.argv[sys.argv.index("--check-presence") + 1])); check_presence(zz, b, q, M, st, ds); return
    sh = sys.argv[sys.argv.index("--start-h") + 1] if "--start-h" in sys.argv else None   # e.g. "3,full": modes 1 (Entry 36) and 2
    sh = None if sh is None else [None if h_ in ("3", "none") else (h_ if h_ == "full" else float(h_)) for h_ in sh.split(",")]
    if "--part" in sys.argv:                                            # --part k/n: a balanced subset of the sequences (merge later)
        k_, n_ = map(int, sys.argv[sys.argv.index("--part") + 1].split("/")); b = dict(b, seqs=part_seqs(b["seqs"], k_, n_))
    R = fwd_null(zz, b, q, M, c, stride=stride, horizon=hor, verbose="--verbose" in sys.argv, presence="--presence" in sys.argv,
                 start_h=sh, ds=ds)
    save(of, R)
    print(f"{of}: {len(R['recs'])} exits, replica agreement {R['agree']:.4f}, tau {R['tau']:.4f}, {time.time() - t0:.0f}s "
          f"({1e3 * (time.time() - t0) / len(q):.1f} ms/frame)", flush=True)


if __name__ == "__main__":
    main()
