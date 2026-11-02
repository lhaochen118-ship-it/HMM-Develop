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


def chain_tau(M, MP, c):
    """emission scale of the place chain exactly as nav_demo: std of the map-null z_far of centred descriptors * sqrt(6) / pi"""
    import selfcal as SC
    nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True); mu = M.mean(0, keepdims=True); Mc = nrm(M - mu)
    Nc = SC.map_null(Mc, MP, c["block"], c["off_d"], c["cell"], c["excl"], c["k"], stride=1)
    zf = Nc["z_far"][np.isfinite(Nc["z_far"])]
    return float(zf.std() * np.sqrt(6) / np.pi)


def fwd_null(z, b, q, M, c, stride=None, horizon=6.0, rho=None, verbose=False, tau=None, starts=True):
    """forward counterfactual ghost tracks of every virtual exit (one per `stride` frames) and their shape residuals.
    q (n_q, d) query descriptors, M (n_map, d) reduced-map descriptors, c = sc_eval.CFG entry. Returns dict(recs, agree, tau)."""
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
    for si, idx in enumerate(b["seqs"]):
        L = len(idx); o = o_all[idx]; cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        Sq = q[idx].astype(np.float32) @ M.T                            # (L, n_map) similarities (q may be kept in fp16: memory)
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
                hole = (dpost <= rho) & (dpost < dpre)
                if hole.all() or not hole.any(): continue
                Bv = np.where(hole, 0.0, exits[ie]); s_ = Bv.sum()
                if s_ > 0: act.append(dict(ie=ie, keep=~hole, B=Bv / s_, last=post[-1], g={}, mode=0))
                if starts:
                    # VIRTUAL START (truncated shape windows): the sequence starts at tau inside a hole -> the chain restarts from the
                    # uniform belief on the map with the corridor of radius rho around the believed path of the next 3 excl removed
                    # (no Voronoi cut: nothing before the start), residual windows truncated at tau (as at a real sequence start)
                    ps_ = post[cum[post] <= cum[ie] + 3.0 * excl]
                    if len(ps_) >= 3:
                        dps, _ = cKDTree(xc[idx[np.r_[ie, ps_]]]).query(Pl); hs = dps <= rho
                        if not hs.all():
                            Bs = np.where(hs, 0.0, 1.0); act.append(dict(ie=ie, keep=~hs, B=Bs / Bs.sum(), last=ps_[-1], g={ie: None}, mode=1))
            live = [a for a in act if a["ie"] < i <= a["last"] or (a["mode"] == 1 and a["ie"] == i)]
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
                    if a["mode"] == 1: w = w[w >= a["ie"]]                   # window truncated at the virtual start
                    if len(w) < 3 or cum[k] - cum[w[0]] < excl: continue
                    if Pl.shape[1] == 1:
                        d = (track[w, 0] - track[w, 0].mean()) - (o[w, 0] - o[w, 0].mean()); rr[q_] = float(np.sqrt((d ** 2).mean()))
                    else:
                        rr[q_] = procrustes2(track[w], o[w])[0]
                rem = a["keep"]; nb_ = tree.query_ball_point(xc[idx[lags]], rho)
                voff = np.array([not rem[np.asarray(l_, int)].any() for l_ in nb_])
                gerr = np.linalg.norm(track[lags] - xc[idx[lags]], axis=1)   # ghost displacement from the belief
                recs.append((idx[a["ie"]], idx[lags], rr, voff, gerr, a["mode"], np.array([a["g"][k] for k in lags], np.int32)))
        if verbose: print(f"  seq {si} {L} frames, {len(exits)} exits, {time.time() - t0:.0f}s", flush=True)
    return dict(recs=recs, agree=n_ag[0] / max(n_ag[1], 1), tau=tau, rho=float(rho), stride=float(stride_path / excl) if stride_path else int(stride), horizon=horizon)


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
        ex, fr, rr, voff, _, _, gi = rc
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
                        horizon=R["horizon"], **(extra or {}))


def load_recs(f):
    q = np.load(f); cut = np.cumsum(q["lens"])[:-1]
    sp_ = lambda k: np.split(q[k], cut)
    md = q["mode"] if "mode" in q.files else np.zeros(len(q["lens"]), np.int8)
    gi = sp_("gidx") if "gidx" in q.files else [np.full(len(x), -1, np.int32) for x in sp_("fr")]
    return [(int(e[0]), f_, r_, v_, g_, int(m_), gg) for e, f_, r_, v_, g_, m_, gg in zip(sp_("ex"), sp_("fr"), sp_("rr"), sp_("voff"), sp_("gerr"), md, gi) if len(e)], q


def main():
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
    R = fwd_null(zz, b, q, M, c, stride=stride, horizon=hor, verbose="--verbose" in sys.argv)
    save(of, R)
    print(f"{of}: {len(R['recs'])} exits, replica agreement {R['agree']:.4f}, tau {R['tau']:.4f}, {time.time() - t0:.0f}s "
          f"({1e3 * (time.time() - t0) / len(q):.1f} ms/frame)", flush=True)


if __name__ == "__main__":
    main()
