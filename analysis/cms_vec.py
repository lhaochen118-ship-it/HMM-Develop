"""VECTORISED exact counterfactual statistics of CMS (RESEARCH_LOG Entry 36; drop-in replacement of cms_exact.cms_stats_exact).

cms_exact.cms_stats_exact loops over frames in Python (Entry 32: 10.3-17.5 ms per frame on one core, the pre-registered budget
was < 10 ms). Here every frame of a batch is processed at once with array operations; the arithmetic is the same, step by step:
  real route test   K = 100 hypotheses x 2 directions x N window frames: anchors by interpolation along the map route,
                    batched 2-D Procrustes, Huber, trimmed mean, anchor appearance look-up (the searchsorted p-2..p+1 rule of
                    tao.py, evaluated by counting instead of a per-row searchsorted);
  exact surgery     corridor of radius rho around the winner's anchors; every window frame's long list (KL = 300) restricted to
                    the unmasked entries, first K of them (hypotheses, look-ups, K-th-similarity fallback);
  counterfactual    the same route test on the unmasked hypotheses, anchor traces leaving the chunk at the corridor;
                    distinctiveness z_cf on the unmasked entries.
Frames are grouped by window length (n_w = N except the first N - 1 frames of a sequence) and processed in batches of B frames.
Forward surgery (Entry 36, `fwd`): see cms_fwd.py; this module exposes the per-anchor distance tensor needed for it.
Usage (library): cms_stats_vec(z, dict(idx, sim, std), K=100, rho=None, ds=None, N=20) -> same dict as cms_stats_exact.
Check: python3 cms_vec.py --check <navcache.npz> <topk.npz>  (equality with cms_exact on a subset of frames)."""
import sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tao as TAO

BIG = 1e7


def setup(z, tkL, ds=None, rho=None):
    """route coordinates, odometry, long lists, per-frame real look-up tables"""
    import cms
    MP = z["MP"]; one_d = MP.ndim == 1 or MP.shape[1] == 1; hz = list(z["hz"])
    if rho is None: rho = cms.OFF_D.get((ds or "cmu").split(":")[0].split("_")[0], 40.0)
    P, cid, arc = TAO.route(MP[:, hz] if (not one_d and MP.shape[1] > 2) else MP)
    o_all = z["o_q"]; o_all = (o_all[:, hz] if (not one_d and o_all.shape[1] > 2) else o_all).astype(float)
    if one_d: o_all = o_all.reshape(-1, 1)
    IL = tkL["idx"].astype(np.int64); SL = tkL["sim"].astype(np.float32); sd = np.maximum(tkL["std"].astype(np.float32), 1e-6)
    key_all = cid * BIG + arc
    starts = {c: arc[cid == c].min() for c in np.unique(cid)}; ends = {c: arc[cid == c].max() for c in np.unique(cid)}
    lo_arc = np.array([starts[c] for c in cid]); hi_arc = np.array([ends[c] for c in cid])
    return dict(P=P, cid=cid, arc=arc, o=o_all, IL=IL, SL=SL, sd=sd, key_all=key_all, lo_arc=lo_arc, hi_arc=hi_arc,
                keyL=key_all[IL], EPL=P[IL], rho=float(rho), excl=float(z["excl"]))


def sequences(z):
    """query frame indices of every sequence, in recording order"""
    sid, kk = z["q_sid"], z["q_k"]; out = []
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; out.append(idx[np.argsort(kk[idx])])
    return out


def _searchsorted_rows(TK, keys):
    """p[b, k, l] = #{i : TK[b, l, i] < keys[b, k, l]} for row-sorted tables TK (B, n_w, Kt) (+inf padded): one np.searchsorted on
    the rows laid end to end with offsets, then an exact one-step correction (the offsets cost ~1e-3 of precision)"""
    B, n_w, Kt = TK.shape; Kh = keys.shape[1]
    fin = np.isfinite(TK); lo = min(TK[fin].min() if fin.any() else 0.0, keys.min()); hi = max(TK[fin].max() if fin.any() else 0.0, keys.max())
    span = hi - lo + 10.0; off = (np.arange(B * n_w, dtype=np.float64) * span).reshape(B, n_w)
    T = np.where(fin, TK - lo, span - 5.0) + off[..., None]             # padding sits between the row's keys and the next row
    Q = (keys - lo) + off[:, None, :]                                   # (B, Kh, n_w)
    flat = T.reshape(-1); q = np.transpose(Q, (0, 2, 1)).reshape(-1)     # queries grouped by (b, l)
    p = np.searchsorted(flat, q, side="left").reshape(B, n_w, Kh) - (np.arange(B * n_w) * Kt).reshape(B, n_w, 1)
    p = np.clip(p, 0, Kt)
    kq = np.transpose(keys, (0, 2, 1))                                  # (B, n_w, Kh) exact keys
    bi = np.arange(B)[:, None, None]; li = np.arange(n_w)[None, :, None]
    dn = (p > 0) & (TK[bi, li, np.maximum(p - 1, 0)] >= kq)             # counted an entry that is not < key
    p = p - dn
    up = (p < Kt) & (TK[bi, li, np.minimum(p, Kt - 1)] < kq)            # missed an entry that is < key
    p = p + up
    return np.transpose(p, (0, 2, 1))


def _interp_pos(S, c, aa):
    """anchor positions (..., d) by interpolation along the map route (as tao.py)"""
    x = (c * BIG + aa).ravel(); P = S["P"]
    return np.stack([np.interp(x, S["key_all"], P[:, d]).reshape(aa.shape) for d in range(P.shape[1])], -1)


def _lookup(TK, TS, FB, CNT, keys, tol=4.0):
    """appearance look-up of tao.py for a batch: TK, TS (B, n_w, Kt) sorted keys / sims of each window frame's table (+inf
    padded), FB (B, n_w) fallback, CNT (B, n_w) table length; keys (B, Kh, n_w). Returns (B, Kh, n_w) float64.
    Rule: p = searchsorted(ks, key) (left); best = max(fallback, ss[pp] for pp in clip(p + {-2,-1,0,1}, 0, len-1) with
    |ks[pp] - key| <= tol)."""
    B, Kh, n_w = keys.shape; Kt = TK.shape[-1]
    p = _searchsorted_rows(TK, keys)                                    # (B, Kh, n_w) = searchsorted left, per (b, l) table
    best = np.broadcast_to(FB[:, None, :].astype(np.float64), keys.shape).copy()
    bi = np.arange(B)[:, None, None]; li = np.arange(n_w)[None, None, :]
    hi = np.maximum(CNT - 1, 0)[:, None, :]
    for off in (-2, -1, 0, 1):
        pp = np.clip(p + off, 0, hi)
        ks = TK[bi, li, pp]; ss = TS[bi, li, pp].astype(np.float64)
        ok = np.abs(ks - keys) <= tol
        best = np.where(ok, np.maximum(best, ss), best)
    return best


def _route_cost(S, J, hv, dl, ow, look, trim=0.75, delta=8.0, wapp=2.0, cmask=None):
    """route cost of hypotheses J (B, Kh) [valid mask hv] for both directions; returns cost (B,), winner (B,) map row,
    winner anchors (B, n_w, d). cmask(q) -> bool (removed region): anchor traces entering it leave the chunk."""
    P = S["P"]; cid, arc = S["cid"], S["arc"]; Bn, Kh = J.shape; n_w = dl.shape[1]; dd = P.shape[1]
    c, a0 = cid[J], arc[J]; lo, hi = S["lo_arc"][J], S["hi_arc"][J]
    pc = ow - ow.mean(1, keepdims=True)                                 # (B, n_w, d)
    m = max(1, int(np.ceil(trim * n_w)))
    best_C = np.full(Bn, np.inf); best_k = np.zeros(Bn, int); best_q = None
    for sgn in (1.0, -1.0):
        aa = a0[:, :, None] - sgn * dl[:, None, :]                      # (B, Kh, n_w)
        inside = (aa >= lo[..., None]) & (aa <= hi[..., None])
        q = _interp_pos(S, np.broadcast_to(c[..., None], aa.shape), aa)
        qc = q - q.mean(2, keepdims=True)
        if dd == 1:
            res = np.abs(qc[..., 0] - pc[:, None, :, 0])
        else:
            a_ = (pc[:, None, :, 0] * qc[..., 0] + pc[:, None, :, 1] * qc[..., 1]).sum(2)
            b_ = (pc[:, None, :, 0] * qc[..., 1] - pc[:, None, :, 1] * qc[..., 0]).sum(2)
            th = np.arctan2(b_, a_); cs, sn = np.cos(th)[..., None], np.sin(th)[..., None]
            rx = cs * pc[:, None, :, 0] - sn * pc[:, None, :, 1]; ry = sn * pc[:, None, :, 0] + cs * pc[:, None, :, 1]
            res = np.sqrt((qc[..., 0] - rx) ** 2 + (qc[..., 1] - ry) ** 2)
        hub = np.where(res <= delta, 0.5 * res ** 2, delta * (res - 0.5 * delta)) / delta ** 2
        if cmask is not None:
            inside = inside & ~np.maximum.accumulate(cmask(q), axis=2)
        geo = np.sort(np.where(inside, hub, 10.0), 2)[..., :m].mean(2)
        keys = c[..., None] * BIG + aa
        app = _lookup(*look, keys)
        C = geo + wapp * (1.0 - app).mean(2)
        C = np.where(hv, C, np.inf)
        k = np.argmin(C, 1); Ck = C[np.arange(Bn), k]
        upd = Ck < best_C
        best_C = np.where(upd, Ck, best_C); best_k = np.where(upd, k, best_k)
        qk = q[np.arange(Bn), k]
        best_q = qk if best_q is None else np.where(upd[:, None, None], qk, best_q)
    return best_C, J[np.arange(Bn), best_k], best_q


def real_tables(S, K):
    """per-frame look-up table of the unmasked map: first K entries sorted by route key"""
    ks = S["keyL"][:, :K]; o = np.argsort(ks, 1, kind="stable")
    return np.take_along_axis(ks, o, 1), np.take_along_axis(S["SL"][:, :K], o, 1), S["SL"][:, :K].min(1)


def masked_tables(S, W, val, K):
    """tables of the window frames W (B, n_w) restricted to unmasked entries val (B, n_w, KL): first K unmasked, sorted by key.
    Returns TK, TS (B, n_w, K) (+inf / -inf padded), FB (B, n_w), CNT (B, n_w), SEL (B, n_w, K) list positions (-1 padded)"""
    sel = np.argsort(~val, axis=-1, kind="stable")[..., :K]             # first K unmasked positions (in list order)
    cnt = np.minimum(val.sum(-1), K)
    okp = np.arange(K)[None, None, :] < cnt[..., None]
    ks = np.where(okp, np.take_along_axis(S["keyL"][W], sel, -1), np.inf)
    ss = np.where(okp, np.take_along_axis(S["SL"][W], sel, -1), -np.inf)
    fb = np.where(cnt > 0, np.where(okp, ss, np.inf).min(-1), -1.0)
    o = np.argsort(ks, -1, kind="stable")
    return np.take_along_axis(ks, o, -1), np.take_along_axis(ss, o, -1), fb, cnt, np.where(okp, sel, -1)


def _min_d2(q, A):
    """min over anchors A (B, n_a, d) of the squared distance of points q (B, ..., d): (B, ...)"""
    Bn = q.shape[0]; qf = q.reshape(Bn, -1, q.shape[-1]); D = 0.0
    for d in range(q.shape[-1]): D = D + (qf[:, :, None, d] - A[:, None, :, d]) ** 2
    return D.min(-1).reshape(q.shape[:-1])


def in_corridor(X, A, rho, step=4):
    """bool (B, ...): point X[b, ...] within rho of some anchor A[b, k] (exactly the test sqrt(min_k |X - A_k|^2) <= rho of
    cms_exact). Two-stage: a cover of every `step`-th anchor decides the sure cases (inside if within rho of a cover anchor;
    outside if farther than rho + delta, delta = cover radius of the row), the band in between is computed with every anchor."""
    Bn, na, dd = A.shape; shp = X.shape[:-1]; Xf = X.reshape(Bn, -1, dd)
    ci = np.unique(np.r_[np.arange(0, na, step), na - 1]); C = A[:, ci]
    dAC = np.zeros((Bn, na, len(ci)))
    for d in range(dd): dAC = dAC + (A[:, :, None, d] - C[:, None, :, d]) ** 2
    delta = np.sqrt(dAC.min(2).max(1))                                  # (B,) every anchor is within delta of the cover
    D = 0.0
    for d in range(dd): D = D + (Xf[:, :, None, d] - C[:, None, :, d]) ** 2
    dC = np.sqrt(D.min(2))                                              # (B, M)
    inside = dC <= rho
    amb = ~inside & (dC - delta[:, None] <= rho + 1e-6)
    if amb.any():
        bi, mi = np.nonzero(amb); Xa = Xf[bi, mi]; Aa = A[bi]          # (n_amb, d), (n_amb, na, d)
        Da = 0.0
        for d in range(dd): Da = Da + (Xa[:, None, d] - Aa[:, :, d]) ** 2
        inside[bi, mi] = np.sqrt(Da.min(1)) <= rho
    return inside.reshape(shp)


def anchor_dist2(S, W, A):
    """squared distance of every long-list entry of every window frame to every anchor: (B, n_w frames, KL, n_w anchors)"""
    E = S["EPL"][W]                                                     # (B, n_w, KL, d)
    D2 = 0.0
    for d in range(E.shape[-1]): D2 = D2 + (E[:, :, :, None, d] - A[:, None, None, :, d]) ** 2
    return D2


def cf_from_mask(S, t, W, dl, ow, val, removed, K, out, col=None, trim=0.75, delta=8.0, wapp=2.0):
    """counterfactual statistics of frames t given the unmasked-entry mask val (B, n_w, KL) of their window frames and the
    removed-region test removed(q) -> bool for anchor traces. Writes cost_cf, j_cf, z_cf, n_mask, short (column col if given)."""
    TK, TS, FB, CNT, SEL = masked_tables(S, W, val, K)
    IL, SL, EPL, sd, excl = S["IL"], S["SL"], S["EPL"], S["sd"], S["excl"]
    put = (lambda k, v, m=slice(None): out[k].__setitem__(t[m], v)) if col is None else (lambda k, v, m=slice(None): out[k].__setitem__((t[m], col), v))
    put("n_mask", (~val[:, 0, :K]).sum(-1))
    put("short", CNT[:, 0] < K)
    has = CNT[:, 0] > 0
    if not has.any(): return
    sel0 = SEL[:, 0, :]; c0 = CNT[:, 0]; B = len(t); bi = np.arange(B)
    i1 = np.where(has, sel0[:, 0], 0); s1 = SL[t, i1]
    Ev = EPL[t[:, None], np.maximum(sel0, 0)]                           # (B, K, d)
    farc = (np.linalg.norm(Ev - EPL[t, i1][:, None, :], axis=-1) > excl) & (sel0 >= 0)
    sv = SL[t[:, None], np.maximum(sel0, 0)]
    sfar = np.where(farc.any(1), np.where(farc, sv, -np.inf).max(1), SL[t, sel0[bi, np.maximum(c0 - 1, 0)]])
    zc = (s1 - sfar) / sd[t]
    put("z_cf", zc[has], has)
    J = IL[t[:, None], np.maximum(sel0, 0)]; hv = sel0 >= 0
    C, jw, _ = _route_cost(S, J, hv, dl, ow, (TK, TS, FB, CNT), trim, delta, wapp, cmask=removed)
    put("cost_cf", C[has], has); put("j_cf", jw[has], has)


def cms_stats_vec(z, tkL, K=100, rho=None, ds=None, N=20, delta=8.0, trim=0.75, wapp=2.0, B=128, frames=None, hook=None):
    """vectorised cms_exact.cms_stats_exact (same outputs). frames: optional subset of frame indices (checks). hook(S, t, W, dl,
    ow, A, D2, out): called per batch after the real route test with the winner anchors A and the anchor distances D2 (used by
    the forward surgery)."""
    S = setup(z, tkL, ds, rho); IL, SL, sd = S["IL"], S["SL"], S["sd"]; excl = S["excl"]; rho = S["rho"]
    n = len(IL); EPL = S["EPL"]
    out = dict(cost=np.full(n, np.inf), cost_cf=np.full(n, np.inf), j=np.full(n, -1), j_cf=np.full(n, -1),
               z=np.full(n, -np.inf), z_cf=np.full(n, -np.inf), n_mask=np.zeros(n, np.int32), short=np.zeros(n, bool))
    Sm = SL[:, :K]; d01 = np.linalg.norm(EPL[:, :K] - EPL[:, :1], axis=2); far = d01 > excl
    out["z"] = (Sm[:, 0] - np.where(far.any(1), np.where(far, Sm, -np.inf).max(1), Sm[:, -1])) / sd
    RT = real_tables(S, K)
    # window groups
    jobs = {}
    sub = None if frames is None else set(int(f) for f in frames)
    for idx in sequences(z):
        o = S["o"][idx]; cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        for i in range(2, len(idx)):
            if sub is not None and int(idx[i]) not in sub: continue
            w = np.arange(max(0, i - N + 1), i + 1)[::-1]
            jobs.setdefault(len(w), []).append((idx[i], idx[w], cum[i] - cum[w]))
    for n_w, lst in jobs.items():
        for a in range(0, len(lst), B):
            ch = lst[a:a + B]
            t = np.array([c[0] for c in ch]); W = np.stack([c[1] for c in ch]); dl = np.stack([c[2] for c in ch])
            ow = S["o"][W]
            look = (RT[0][W], RT[1][W], RT[2][W], np.full(W.shape, K))
            C, jr, A = _route_cost(S, IL[t, :K], np.ones((len(t), K), bool), dl, ow, look, trim, delta, wapp)
            out["cost"][t], out["j"][t] = C, jr
            val = ~in_corridor(S["EPL"][W], A, rho)                    # unmasked long-list entries of the window frames
            removed = lambda q, A=A: in_corridor(q, A, rho)
            cf_from_mask(S, t, W, dl, ow, val, removed, K, out, None, trim, delta, wapp)
            if hook is not None: hook(S, t, W, dl, ow, A, anchor_dist2(S, W, A), out)
    out["rho"] = rho; out["KL"] = IL.shape[1]
    return out


def _check():
    import cms_exact as CE
    zf, tf = sys.argv[sys.argv.index("--check") + 1], sys.argv[sys.argv.index("--check") + 2]
    z = np.load(zf, allow_pickle=True); tk = dict(np.load(tf)); KL = tk["idx"].shape[1]; K = int(os.environ.get("CHK_K", 60))
    ds = os.path.basename(zf)[len("navcache_"):].split("_")[0]
    n = len(z["cond"]); rng = np.random.default_rng(0); sub = np.sort(rng.choice(n, min(n, int(os.environ.get("CHK_N", 400))), replace=False))
    t0 = time.time(); v = cms_stats_vec(z, tk, K=K, ds=ds); tv = time.time() - t0
    # reference on the subset: run the loop version restricted to the frames of the subset (same windows)
    zz = {k: z[k] for k in z.files}
    t0 = time.time(); r = CE.cms_stats_exact(zz, tk, K=K, ds=ds); tr = time.time() - t0
    for k in ("cost", "cost_cf", "j", "j_cf", "z", "z_cf", "n_mask", "short"):
        a, b = np.asarray(v[k], float), np.asarray(r[k], float)
        same = np.isclose(a, b, rtol=1e-9, atol=1e-9) | (np.isinf(a) & np.isinf(b) & (np.sign(a) == np.sign(b)))
        print(f"{k:8s} equal {same.mean():.6f}  max|diff| {np.nanmax(np.abs(np.where(same, 0, a - b))) if (~same).any() else 0:.3g}")
    print(f"vectorised {tv:.1f}s ({1e3 * tv / n:.2f} ms/frame), loop {tr:.1f}s ({1e3 * tr / n:.2f} ms/frame), n {n}, KL {KL}, K {K}")


if __name__ == "__main__":
    if "--check" in sys.argv: _check()
