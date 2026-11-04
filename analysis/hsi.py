"""HSI — Hindsight Self-supervised Integrity (idea 2, branch hmm-2nd-idea).

The localiser is the shared place chain (HMM over the places of the map, odometry transitions; `est_c` of the
nav_demo cache). Whether its fix is REPORTED to the navigation filter is decided by a score that is LEARNED ONLINE from
labels the robot generates itself, in hindsight, from geometry only (no ground truth, no labelled calibration data,
no intervention on the map):

  1. verification   the chain's track agrees with the odometry at several lags over a window (two-sided in hindsight:
                    `verified`; causal online: `anchor`). Displacement agreement between the camera-driven belief and
                    proprioception does not involve any similarity value, so it means the same thing in every
                    condition (night, snow, season);
  2. bridges        between verified runs the odometry, rigidly aligned (Kabsch) on the verified frames on both sides,
                    gives the hindsight position x~_t of every frame, with an uncertainty sd_t = s0 + kappa * (path to
                    the nearest verified frame); s0 and kappa are estimated from the deployment itself (fit residual
                    of verified frames; one-sided prediction error of two-sided bridges);
  3. labels         y_t = 1 if the chain's fix MP[est_t] lies within excl of x~_t, y_t = 0 if it does not or if x~_t is
                    farther than off_d from every map place (off-map is a property of the map's known coverage),
                    with margins z * sd_t; frames whose x~_t may be off-map (> off_d - z sd_t) form the hindsight NULL;
  4. learning       a gradient-boosted classifier of y_t on causal features (appearance statistics, chain-odometry
                    residuals at several lags, dead reckoning from the last anchor) is refitted as labels arrive, in
                    deployment order (sessions sorted by date, then sequences);
  5. calibration    report iff score > the conformal (1 - alpha) quantile of the score maxima of H-frame segments of the
                    hindsight null of REAL excursions (edges and starts included) held out from training; Mondrian per
                    session (condition). Until a session has enough held-out null segments, a fallback decides.

Every label becomes usable only when it is final (`avail`: the deployment rank at which the bridge that labels it has
closed), so nothing in the online loop looks ahead. Ground truth (q_pos, inm, offm) is used ONLY by `evaluate`.
Usage (from cache): hsi.py <navcache.npz> [...]  (prints protocol metrics; --json out.json)"""
import os, sys, json, time
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BIG = np.iinfo(np.int64).max


# ----------------------------------------------------------------------------------------------------------- basics
def deployment_seqs(z):
    """query sequences (index arrays in time order), sorted in deployment order: condition (session date), then start"""
    sid, k, cond = z["q_sid"], z["q_k"], np.asarray(z["cond"]).astype(str)
    s = [np.where(sid == x)[0][np.argsort(k[sid == x], kind="stable")] for x in np.unique(sid)]
    return sorted(s, key=lambda idx: (cond[idx[0]], int(idx[0])))


def horiz(P):
    """horizontal axes of the positions (1-D: Nordland frame index; 2-D; 3-D: the two axes of largest variance, as
    nav_demo's navigation filter)"""
    return np.arange(P.shape[1]) if P.shape[1] <= 2 else np.sort(np.argsort(P.var(0))[1:])


def lag_res(X, O, idx, k):
    """|(X_{i+k} - X_i) - (O_{i+k} - O_i)| for consecutive frames of one sequence, indexed by i (length L - k)"""
    if len(idx) <= k: return np.zeros(0)
    return np.linalg.norm((X[idx[k:]] - X[idx[:-k]]) - (O[idx[k:]] - O[idx[:-k]]), axis=1)


def kabsch(A, B):
    """rigid (R, t) minimising sum |R a + t - b|^2 (rows are points; 1-D: translation only)"""
    ca, cb = A.mean(0), B.mean(0)
    if A.shape[1] == 1: return np.eye(1), cb - ca
    U, _, Vt = np.linalg.svd((A - ca).T @ (B - cb)); D = np.eye(A.shape[1]); D[-1, -1] = np.sign(np.linalg.det(U @ Vt))
    R = (U @ D @ Vt).T
    return R, cb - R @ ca


def kabsch_batch(A, B):
    """batched 2-D Kabsch: A, B (m, w, 2) -> R (m, 2, 2), t (m, 2)"""
    ca, cb = A.mean(1, keepdims=True), B.mean(1, keepdims=True)
    C = np.einsum("mwi,mwj->mij", A - ca, B - cb); U, _, Vt = np.linalg.svd(C)
    d = np.sign(np.linalg.det(U @ Vt)); D = np.zeros_like(C); D[:, 0, 0] = 1; D[:, 1, 1] = d
    R = np.transpose(U @ D @ Vt, (0, 2, 1))
    return R, cb[:, 0] - np.einsum("mij,mj->mi", R, ca[:, 0])


class Cfg:
    """all constants in the units of the protocol (excl, off_d) or in frames; one setting for every dataset"""
    def __init__(self, z, name, **kw):
        self.excl = float(z["excl"]); self.H = int(z["H"])
        nord = name.startswith("nord")
        self.off_d = 10.0 if nord else (20.0 if name.startswith("nclt") else 40.0)   # sc_eval.CFG off_d (protocol)
        self.tau = 0.4 * self.excl                    # displacement tolerance of a consistent lag pair (grows with the lag)
        self.lags_c = (10, 20, 40, 80)                # causal anchor: consistent at every lag over the last 80 frames
        self.span = 20; self.lags_h = (5, 10, 20, 40)  # hindsight verification: every lag pair inside t +- 20 frames
        self.W = 40                                   # verified frames used on each side to align a bridge
        self.zm = 2.0                                 # label margin in hindsight standard deviations
        self.alpha = 0.05; self.chunk = 200; self.unit = 300; self.cal_mod = 2
        self.P_over = 80                              # frames of continuous anchoring that override a conflicting reference
        self.null_kind = "wrong"                      # calibration null: possibly wrong fixes ('wrong') or possibly off-map ('off')
        self.scope = "session"                        # threshold from this session's held-out null ('session'), every session's ('pooled')
        self.min_seg = int(np.ceil(1 / self.alpha)) - 1
        for k, v in kw.items(): setattr(self, k, v)
        if getattr(self, "metric_windows", False):   # windows in metres of path (the frame values above assume ~1 m per frame)
            O = z["o_q"]; st = float(np.median(np.linalg.norm(np.diff(O, axis=0), axis=1)))
            st = st if np.isfinite(st) and st > 0 else 1.0; f = lambda m: max(1, int(round(m / max(st, 1.0))))   # never finer than 1 m
            self.step = st; self.lags_c = tuple(sorted({f(k) for k in self.lags_c})); self.lags_h = tuple(sorted({f(k) for k in self.lags_h}))
            self.span = max(2, f(self.span)); self.W = max(4, f(self.W)); self.P_over = max(4, f(self.P_over)); self.unit = max(30, f(self.unit))
            self.sc_scale = f

    def tol(self, k):
        return self.tau * (1 + k / 40.0)

    def tolv(self, k, frames):
        """tolerance of the lag-k pairs ending at `frames`: self-calibrated array if set (adaptive_tolerance), else scalar"""
        T = getattr(self, "tolarr", None)
        return T[k][frames] if T is not None and k in T else self.tol(k)


def adaptive_tolerance(z, seqs, cfg, lags=(5, 10, 20, 40, 80), c=3.0, every=2000, min_n=500, mode="free"):
    """label-free, causal consistency tolerances: tol_k(t) = c x running median (deployment order, frames before t) of the
    lag-k residual |(MP[est_t] - MP[est_{t-k}]) - (o_t - o_{t-k})| of the place chain, clipped to [0.15 excl, 0.8 excl (1 + k/40)
    x 1.5]; the scalar default tau (1 + k/40) is used until min_n residuals exist. The median is dominated by frames where the
    chain tracks, so it measures the odometry + chain noise of this robot and this map (NCLT, VIO drift vs Boreas wheels)."""
    MP, est, O = z["MP"], z["est_c"], z["o_q"]; n = len(est); order = np.concatenate(seqs)
    rank = np.empty(n, np.int64); rank[order] = np.arange(n); out = {}
    for k in lags:
        r = np.full(n, np.nan)
        for idx in seqs:
            if len(idx) > k: r[idx[k:]] = lag_res(MP[est], O, idx, k)
        ro = r[order]; tl = np.full(n, cfg.tol(k)); lo, hi = 0.15 * cfg.excl, 0.8 * cfg.excl * (1 + k / 40.0) * 1.5
        for c0 in range(every, n + every, every):
            pre = ro[:min(c0, n)]; pre = pre[np.isfinite(pre)]
            if len(pre) >= min_n:
                v = np.clip(c * np.median(pre), lo, hi)
                tl[c0:c0 + every] = max(v, cfg.tol(k)) if mode == "max" else v          # 'max': only loosen the default
        out[k] = tl[rank]                                                   # back to frame index
    return out


def window_rotation(F, O, idx, W, hz):
    """per frame i of one sequence: angle of the 2-D rotation that best maps the odometry of frames [i-W, i] onto the chain
    positions F (Kabsch). nan for i < W or for 1-D positions."""
    L = len(idx); ang = np.full(L, np.nan)
    if len(hz) != 2 or L <= W: return ang
    t = np.arange(W, L); ii = t[:, None] - np.arange(W + 1)[None, ::-1]
    R, _ = kabsch_batch(O[idx[ii]][..., hz], F[idx[ii]][..., hz]); ang[W:] = np.arctan2(R[:, 1, 0], R[:, 0, 0])
    return ang


def lag_res_rot(F, O, idx, k, ang, hz):
    """|(F_{i+k} - F_i) - R(ang_{i+k}) (O_{i+k} - O_i)| for pairs ending at i+k (rotation of the window ending there)"""
    if len(idx) <= k: return np.zeros(0)
    dF = F[idx[k:]] - F[idx[:-k]]; dO = (O[idx[k:]] - O[idx[:-k]]).astype(float).copy(); a = np.nan_to_num(ang[k:])
    if len(hz) == 2:
        c, s_ = np.cos(a), np.sin(a); x, y = dO[:, hz[0]].copy(), dO[:, hz[1]].copy()
        dO[:, hz[0]] = c * x - s_ * y; dO[:, hz[1]] = s_ * x + c * y
    return np.linalg.norm(dF - dO, axis=1)


# ------------------------------------------------------------------------------------------------- verification
def causal_anchor(MP, est, O, seqs, cfg, n):
    """anchor_t: the chain's displacement over the last k frames matches the odometry for every k in lags_c (rot_max: after
    the best rotation of the last max(lags_c) frames, which must stay within +-rot_max: a bounded heading offset of the
    odometry is tolerated, a track that needs a large rotation is not)"""
    out = np.zeros(n, bool); hz = horiz(MP); rm = getattr(cfg, "rot_max", None)
    for idx in seqs:
        L = len(idx); g = np.ones(L, bool); g[:max(cfg.lags_c)] = False
        if rm is not None:
            ang = window_rotation(MP[est], O, idx, max(cfg.lags_c), hz)
            if len(hz) == 2: g &= np.abs(np.nan_to_num(ang, nan=np.inf)) <= rm
        for k in cfg.lags_c:
            r = lag_res(MP[est], O, idx, k) if rm is None else lag_res_rot(MP[est], O, idx, k, ang, hz)
            ok = np.zeros(L, bool); ok[k:] = r <= cfg.tolv(k, idx[k:]); g &= ok
        out[idx] = g
    return out


def hindsight_verified(MP, est, O, seqs, cfg, n):
    """verified_t (two-sided, hindsight): every lag pair (i, i+k), k in lags_h, inside [t - span, t + span] is consistent.
    Vectorised with prefix sums of inconsistent pairs. Returns the mask and, per frame, the deployment-time index (within
    the sequence) at which its verification is complete (t + span)."""
    out = np.zeros(n, bool); S = cfg.span
    for idx in seqs:
        L = len(idx)
        if L < 2 * S + 1: continue
        good = np.ones(L, bool); good[:S] = False; good[L - S:] = False
        t = np.arange(S, L - S)
        for k in cfg.lags_h:
            if k > 2 * S: continue
            r = lag_res(MP[est], O, idx, k); bad = (r > cfg.tolv(k, idx[k:])).astype(np.int64)     # pair (i, i+k), i in [0, L-k)
            c = np.r_[0, np.cumsum(bad)]
            lo, hi = t - S, t + S - k                                                  # pairs with i in [lo, hi]
            nb = c[np.minimum(hi + 1, len(bad))] - c[np.clip(lo, 0, len(bad))]
            g = np.ones(L, bool); g[t] = nb == 0; good &= g
        out[idx] = good
    return out


# ------------------------------------------------------------------------------------------------------- features
def features(z, seqs, cfg, anc):
    """causal per-frame features (each uses frames <= t of its own sequence only)"""
    MP, est, top, O = z["MP"], z["est_c"], z["top"], z["o_q"]; n = len(est); hz = horiz(MP); tree = cKDTree(MP)
    srt = z["srt10"].astype(float); s1m = srt[:, 0] - z["Smean"]
    F = {"s1": srt[:, 0], "s1m": s1m, "zs": s1m / np.maximum(z["Sstd"], 1e-6), "m12": srt[:, 0] - srt[:, 1],
         "m15": srt[:, 0] - srt[:, 4], "m110": srt[:, 0] - srt[:, 9], "lp": np.log(np.clip(z["p_frame"], 1e-9, 1)),
         "lpR": np.log(np.clip(z["pR"], 1e-9, 1)), "lo": z["lo_c"], "conf": z["conf_c"],
         "agree": (np.linalg.norm(MP[top] - MP[est], axis=1) <= cfg.excl).astype(float)}
    lags = (3, 5, 10, 20, 40, 80); R = {k: np.full(n, np.nan) for k in lags}
    m5, m20, ag10 = np.zeros(n), np.zeros(n), np.zeros(n)
    dDR, eDR, since = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    for idx in seqs:
        L = len(idx); i1 = np.arange(1, L + 1)
        for k in lags:
            if L > k: R[k][idx[k:]] = lag_res(MP[est], O, idx, k)
        c = np.cumsum(np.r_[0, s1m[idx]])
        for w, arr in ((5, m5), (20, m20)): ww = np.minimum(i1, w); arr[idx] = (c[i1] - c[i1 - ww]) / ww
        ca = np.cumsum(np.r_[0, F["agree"][idx]]); ww = np.minimum(i1, 10); ag10[idx] = (ca[i1] - ca[i1 - ww]) / ww
        # dead reckoning from the last causal anchor, rigidly aligned on the anchor's last W frames (vectorised)
        a = np.flatnonzero(anc[idx])
        if not len(a): continue
        if len(hz) == 2:
            w0 = np.maximum(a - cfg.W, 0); wl = cfg.W + 1
            ii = np.clip(w0[:, None] + np.arange(wl)[None], None, a[:, None])            # (m, wl) frames of each window
            Rm, tv = kabsch_batch(O[idx[ii]][..., hz], MP[est[idx[ii]]][..., hz])
        last = np.maximum.accumulate(np.where(anc[idx], np.arange(L), -1)); has = last >= 0
        j = np.searchsorted(a, last[has])                                                # which anchor
        x = MP[est[idx[has]]].astype(float).copy()
        if len(hz) == 2: x[:, hz] = np.einsum("mij,mj->mi", Rm[j], O[idx[has]][:, hz]) + tv[j]
        else: x[:, hz] = MP[est[idx[a[j]]]][:, hz] + O[idx[has]][:, hz] - O[idx[a[j]]][:, hz]
        path = np.r_[0, np.cumsum(np.linalg.norm(np.diff(O[idx], axis=0), axis=1))]
        hi = idx[has]; dDR[hi] = tree.query(x)[0]; eDR[hi] = np.linalg.norm(x - MP[est[hi]], axis=1); since[hi] = path[has] - path[a[j]]
    for k in lags: F[f"r{k}"] = np.log1p(R[k])
    F.update(m5=m5, m20=m20, ag10=ag10, anc=anc.astype(float), dDR=dDR / cfg.off_d, eDR=np.log1p(eDR), since=np.log1p(since))
    names = list(F)
    return np.stack([F[k] for k in names], 1).astype(np.float32), names


# ------------------------------------------------------------------------------------------------------ hindsight
def hindsight(z, seqs, cfg, ver):
    """hindsight positions from verified runs and rigid bridges. Returns x~ (nan where none), sd, avail (deployment rank at
    which the frame's label is final), drift kappa and s0 (both estimated label-free) and the number of closures used"""
    MP, est, O = z["MP"], z["est_c"], z["o_q"]; n = len(est); hz = horiz(MP); W = cfg.W
    order = np.concatenate(seqs); rank = np.empty(n, np.int64); rank[order] = np.arange(n)
    xt = np.full((n, MP.shape[1]), np.nan); dist = np.full(n, np.inf); two = np.zeros(n, bool); avail = np.full(n, BIG)
    clos, fitres = [], []
    for idx in seqs:
        L = len(idx); vi = np.flatnonzero(ver[idx])
        if not len(vi): continue
        path = np.r_[0, np.cumsum(np.linalg.norm(np.diff(O[idx], axis=0), axis=1))]
        av = np.full(L, -1, np.int64)
        xt[idx[vi]] = MP[est[idx[vi]]]; dist[idx[vi]] = 0.0; two[idx[vi]] = True
        av[vi] = np.minimum(vi + cfg.span, L - 1)                                  # verification needs t + span
        runs = np.split(vi, np.flatnonzero(np.diff(vi) > 1) + 1)
        for r0, r1 in zip([None] + runs, runs + [None]):
            if r0 is None and r1 is None: continue
            lo = 0 if r0 is None else r0[-1] + 1; hi = L if r1 is None else r1[0]
            if hi <= lo: continue
            gi = np.arange(lo, hi); fi = np.concatenate([x for x in (None if r0 is None else r0[-W:], None if r1 is None else r1[:W]) if x is not None])
            Rm, tv = kabsch(O[idx[fi]][:, hz], MP[est[idx[fi]]][:, hz])
            fitres.append(np.median(np.linalg.norm((Rm @ O[idx[fi]][:, hz].T).T + tv - MP[est[idx[fi]]][:, hz], axis=1)))
            x = MP[est[idx[gi]]].astype(float).copy(); x[:, hz] = (Rm @ O[idx[gi]][:, hz].T).T + tv; xt[idx[gi]] = x
            dl = np.full(len(gi), np.inf)
            if r0 is not None: dl = np.minimum(dl, path[gi] - path[r0[-1]])
            if r1 is not None: dl = np.minimum(dl, path[r1[0]] - path[gi])
            dist[idx[gi]] = dl; two[idx[gi]] = r0 is not None and r1 is not None
            av[gi] = min(r1[0] + cfg.span, L - 1) if r1 is not None else L - 1            # final when the next run is verified
            if r0 is not None and r1 is not None:                                       # label-free drift: predict r1 from r0
                R0, t0 = kabsch(O[idx[r0[-W:]]][:, hz], MP[est[idx[r0[-W:]]]][:, hz])
                pr = (R0 @ O[idx[r1[:W]]][:, hz].T).T + t0
                clos.append((path[r1[0]] - path[r0[-1]], float(np.median(np.linalg.norm(pr - MP[est[idx[r1[:W]]]][:, hz], axis=1)))))
        avail[idx] = rank[idx[np.clip(av, 0, L - 1)]]
    clos = np.array(clos) if clos else np.zeros((0, 2))
    kappa = float(np.median(clos[:, 1] / np.maximum(clos[:, 0], 1.0))) if len(clos) >= 5 else 0.05
    kappa = float(np.clip(kappa, 0.005, 0.2))
    s0 = float(np.clip(np.median(fitres) if fitres else cfg.tau / 2, 0.05 * cfg.excl, cfg.tau))
    sd = s0 + np.where(two, 0.5, 1.0) * kappa * dist
    return xt, sd, avail, kappa, s0, len(clos)


def hindsight_labels(z, cfg, xt, sd):
    """y = 1 (fix correct), 0 (fix wrong or off-map), -1 (no label); null = possibly off-map (calibration null)"""
    MP, est = z["MP"], z["est_c"]; n = len(est); have = np.isfinite(sd) & np.isfinite(xt).all(1)
    dmap = np.full(n, np.nan); dmap[have] = cKDTree(MP).query(xt[have])[0]
    e = np.full(n, np.nan); e[have] = np.linalg.norm(MP[est[have]] - xt[have], axis=1); mg = cfg.zm * sd
    y = np.full(n, -1, np.int8)
    y[have & (e <= cfg.excl - mg) & (dmap <= cfg.off_d - mg)] = 1
    y[have & ((e > cfg.excl + mg) | (dmap > cfg.off_d + mg))] = 0
    null_off = have & (dmap > cfg.off_d - mg)
    null = null_off | (have & (e > cfg.excl - mg)) if cfg.null_kind == "wrong" else null_off
    return y, null, dmap


def null_segments(seqs, null, mask, unit, H, klass=None):
    """disjoint H-frame segments of runs of null frames (within one calibration unit and, if given, one regime class), from
    the start of each run"""
    segs = []; kl = np.zeros(len(unit), np.int64) if klass is None else klass
    for idx in seqs:
        mm = null[idx] & mask[idx]; i = 0; L = len(idx)
        while i < L:
            if mm[i]:
                j = i
                while j < L and mm[j] and unit[idx[j]] == unit[idx[i]] and kl[idx[j]] == kl[idx[i]]: j += 1
                for kk in range(i, j - H + 1, H): segs.append(idx[kk:kk + H])
                i = j
            else: i += 1
    return segs



def calib_units(unit, mod, seed=17):
    """held-out calibration units: each unit independently with probability 1/mod (deterministic, label-free)"""
    u = np.unique(unit); flag = np.random.default_rng(seed).random(len(u)) < 1.0 / mod
    return flag[np.searchsorted(u, unit)]

# ---------------------------------------------------------------------------------------------------- online rule
class Model:
    """gradient-boosted classifier of the hindsight label; columns that are entirely missing in the training rows are
    dropped (sklearn's binning fails on them), the same columns are used at prediction"""
    def __init__(self, X, y, seed=0):
        from sklearn.ensemble import HistGradientBoostingClassifier
        self.cols = np.flatnonzero(np.isfinite(X).any(0))
        self.clf = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.1, max_leaf_nodes=15, random_state=seed).fit(X[:, self.cols], y)

    def predict_proba(self, X):
        return self.clf.predict_proba(X[:, self.cols])


def fit_model(X, y, seed=0):
    return Model(X, y, seed)


def conformal_thr(segmax, alpha):
    s = np.sort(segmax); k = int(np.ceil((1 - alpha) * (len(s) + 1)))
    return s[k - 1] if k <= len(s) else np.inf


def online(z, name, mode="session", verbose=False, **kw):
    """the deployment-order online loop. mode: 'session' (Mondrian per session; fallback = causal anchors),
    'session+geo' (fallback = a geometry-only model calibrated on pooled held-out null segments of every session).
    Returns dict with acc (report mask), score, thr, and diagnostics."""
    cfg = Cfg(z, name, **kw); t0 = time.time()
    MP, est, O = z["MP"], z["est_c"], z["o_q"]; n = len(est); cond = np.asarray(z["cond"]).astype(str); H = cfg.H
    seqs = deployment_seqs(z); order = np.concatenate(seqs)
    anc = causal_anchor(MP, est, O, seqs, cfg, n); ver = hindsight_verified(MP, est, O, seqs, cfg, n)
    X, names = features(z, seqs, cfg, anc)
    xt, sd, avail, kappa, s0, ncl = hindsight(z, seqs, cfg, ver)
    y, null, dmap = hindsight_labels(z, cfg, xt, sd)
    unit = np.zeros(n, np.int64)
    for si, idx in enumerate(seqs): unit[idx] = si * 100000 + np.arange(len(idx)) // cfg.unit
    cal = calib_units(unit, cfg.cal_mod)                                          # held-out calibration units
    segs = null_segments(seqs, null, cal, unit, H)
    seg_av = np.array([avail[s].max() for s in segs], np.int64) if segs else np.zeros(0, np.int64)
    seg_c = np.array([cond[s[0]] for s in segs]) if segs else np.zeros(0, str)
    seg_cert = np.array([cert[s_].all() for s_ in segs], bool) if segs else np.zeros(0, bool)
    seg_geo = np.array([geo[s_].any() for s_ in segs], bool) if segs else np.zeros(0, bool)
    geo = [i for i, nm in enumerate(names) if nm in ("r3", "r5", "r10", "r20", "r40", "r80", "anc", "dDR", "eDR", "since")]
    score = np.full(n, -np.inf); thr_at = np.full(n, np.inf); gscore = np.full(n, -np.inf); gthr_at = np.full(n, np.inf)
    clf = gclf = None; last_n = 0; thr = gthr = np.inf
    for c0 in range(0, n, cfg.chunk):
        T = c0; cur = order[c0:c0 + cfg.chunk]; cc = cond[cur[0]]
        m = (y >= 0) & (avail < T) & (~cal if cfg.scope == "pooled" else ((cond != cc) | ~cal))
        n1, n0 = int((y[m] == 1).sum()), int((y[m] == 0).sum())
        if n1 >= 50 and n0 >= 50 and (clf is None or m.sum() > 1.1 * last_n):
            clf = fit_model(X[m], y[m]); last_n = int(m.sum())
            if mode == "session+geo": gclf = fit_model(X[m][:, geo], y[m])
        if clf is None: continue
        ready = (seg_av < T)
        rs = [s for s, r, c in zip(segs, ready, seg_c) if r and (c == cc or cfg.scope == "pooled")]
        thr = conformal_thr(clf.predict_proba(X[np.concatenate(rs)])[:, 1].reshape(len(rs), H).max(1), cfg.alpha) if len(rs) >= cfg.min_seg else np.inf
        score[cur] = clf.predict_proba(X[cur])[:, 1]; thr_at[cur] = thr
        if gclf is not None:
            rg = [s for s, r in zip(segs, ready) if r]
            gthr = conformal_thr(gclf.predict_proba(X[np.concatenate(rg)][:, geo])[:, 1].reshape(len(rg), H).max(1), cfg.alpha) if len(rg) >= cfg.min_seg else np.inf
            gscore[cur] = gclf.predict_proba(X[cur][:, geo])[:, 1]; gthr_at[cur] = gthr
    session_ready = np.isfinite(thr_at)
    acc = np.where(session_ready, score > thr_at, (gscore > gthr_at) if mode == "session+geo" else anc)
    out = dict(acc=acc, score=score, thr=thr_at, anc=anc, ver=ver, y=y, null=null, xt=xt, sd=sd, avail=avail, kappa=kappa, s0=s0,
               n_closures=ncl, n_cal_seg=len(segs), seqs=seqs, names=names, cfg=cfg, secs=time.time() - t0, session_ready=session_ready)
    return out


# ------------------------------------------------------------------------------------------------------ evaluation
def evaluate(z, name, out, nav=True):
    """protocol metrics (nav_demo.rule_metrics) + position classes of real off-map segments + navigation error.
    Ground truth is used here only."""
    import nav_demo as N
    MP, est, q, inm, offm = z["MP"], z["est_c"], z["q_pos"], z["inm"], z["offm"]; cfg = out["cfg"]; H = cfg.H
    seqs = out["seqs"]; acc = out["acc"]; ok = np.linalg.norm(out.get("xf", MP[est]) - q, axis=1) <= cfg.excl
    r = N.rule_metrics(acc, ok & inm, inm, offm, seqs, H)
    O = z["o_q"]; start_h = cfg.off_d + 20 * cfg.excl                          # as position_audit.py: path from the start
    cls = {"start": [0, 0], "edge": [0, 0], "deep": [0, 0]}
    for idx in seqs:
        of = offm[idx]; L = len(idx); i = 0
        path = np.r_[0, np.cumsum(np.linalg.norm(np.diff(O[idx], axis=0), axis=1))]
        while i < L:
            if of[i]:
                j = i
                while j < L and of[j]: j += 1
                for kk in range(i, j - H + 1, H):
                    c = "start" if path[kk] <= start_h else ("edge" if kk == i else "deep")
                    cls[c][0] += 1; cls[c][1] += int(acc[idx[kk:kk + H]].any())
                i = j
            else: i += 1
    r["classes"] = {k: (v[0], v[1] / max(v[0], 1)) for k, v in cls.items()}
    r["chain_ok"] = float(ok[inm].mean())
    if nav:
        cx = dict(q_pos=q, o_q=O, real=bool(z["real"]), q_seqs=seqs, hz=list(z["hz"]), seed=int(z["seed"]), excl=cfg.excl,
                  head=name.startswith("nclt"))
        xf = out.get("xf", MP[est])                                             # fix positions (default: the place chain's MAP)
        e = N.track(acc, xf, cx["q_pos"], cx["o_q"], cx["real"], cx["q_seqs"], cx["hz"], cx["seed"], cx["head"])
        r["err_mean"] = float(np.nanmean(e)); r["err_p95"] = float(np.nanpercentile(e, 95))
    return r


def main():
    js = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    mode = sys.argv[sys.argv.index("--mode") + 1] if "--mode" in sys.argv else "session"
    kw = {}
    for a in sys.argv:
        if a.startswith("--set:"): k, v = a[6:].split("="); kw[k] = type(getattr(Cfg.__init__, "__defaults__", None) or "")(v) if False else (float(v) if v.replace(".", "", 1).isdigit() else v)
    files = [a for a in sys.argv[1:] if a.endswith(".npz")]; res = {}
    for f in files:
        z = np.load(f, allow_pickle=True); name = os.path.basename(f)[9:-4]
        out = online(z, name, mode=mode, **kw); r = evaluate(z, name, out)
        cl = r["classes"]; res[name] = {k: v for k, v in r.items()}
        print(f"{name:30s} chain_ok {r['chain_ok']:.3f} | rec {r['recall']:.3f} seg {r['seg_FAR']:.3f} FL {r['FL']:.4f} err {r['err_mean']:.1f} | "
              + " ".join(f"{k} {v[0]}:{v[1]:.3f}" for k, v in cl.items())
              + f" | kappa {out['kappa']:.3f} s0 {out['s0']:.1f} closures {out['n_closures']} calseg {out['n_cal_seg']} ready {out['session_ready'].mean():.2f} | {out['secs']:.0f}s", flush=True)
    if js: json.dump(res, open(js, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()


# ================================================================================ v2: trusted references + DR agreement
def trusted_geometry(z, seqs, cfg, anc, kappa0=0.05, P_over=None, zz=2.0, seq_kappa=True):
    """Causal geometric self-verification (no appearance threshold, no labels).
    Per sequence, a TRUSTED REFERENCE = rigid map<-odometry transform fitted (Kabsch) on the last W frames of a causal
    anchor. A new anchor refreshes the reference iff its fix agrees with the dead reckoning of the current reference
    (|MP[est] - x_DR| <= tau + zz * kappa * path since the reference), or, when it conflicts, after P_over frames of
    continuous anchoring (the old reference was wrong). The drift rate kappa is updated label-free from the agreements
    (prediction error of the dead reckoning at refreshed anchors / path), starting at kappa0.
    Reports:  (a) trusted anchors;  (b) DR agreement: |MP[est_t] - x_DR(t)| + zz sd <= excl and dmap(x_DR) + zz sd <= off_d,
    sd = s0 + kappa * path since the reference (the fix is correct and on-map under the drift model).
    Returns rep_a, rep_b, has_ref, x_dr, sd (nan without reference), kappa trace."""
    MP, est, O = z["MP"], z["est_c"], z["o_q"]; n = len(est); hz = horiz(MP); tree = cKDTree(MP); W = cfg.W
    P_over = cfg.P_over if P_over is None else P_over
    rep_a = np.zeros(n, bool); rep_b = np.zeros(n, bool); has_ref = np.zeros(n, bool)
    xdr = np.full((n, MP.shape[1]), np.nan); sdv = np.full(n, np.nan); errs = []          # (path, DR error) pairs
    kap = kappa0
    for idx in seqs:
        L = len(idx); path = np.r_[0, np.cumsum(np.linalg.norm(np.diff(O[idx], axis=0), axis=1))]
        ref = None; conflict = 0; s0 = cfg.tau / 2
        F = MP[est[idx]].astype(float)
        for i in range(L):
            t = idx[i]
            if ref is not None:
                Rm, tv, pref, s0 = ref; x = F[i].copy(); x[hz] = Rm @ O[t][hz] + tv; ell = path[i] - pref
                sd = s0 + kap * ell; xdr[t] = x; sdv[t] = sd; has_ref[t] = True
                dmap = tree.query(x)[0]; e = np.linalg.norm(F[i] - x)
                rep_b[t] = (e + zz * sd <= cfg.excl) and (dmap + zz * sd <= cfg.off_d)
            if anc[t]:
                w0 = max(0, i - W); Rn, tn = kabsch(O[idx[w0:i + 1]][:, hz], F[w0:i + 1][:, hz])
                res = float(np.median(np.linalg.norm((Rn @ O[idx[w0:i + 1]][:, hz].T).T + tn - F[w0:i + 1][:, hz], axis=1)))
                if ref is None: ok = True
                else:
                    ok = np.linalg.norm(F[i] - xdr[t]) <= cfg.tolv(10, t) / 1.25 + zz * kap * (path[i] - ref[2])
                    conflict = 0 if ok else conflict + 1
                    if ok and path[i] - ref[2] > 2 * cfg.excl: errs.append((path[i] - ref[2], np.linalg.norm(F[i] - xdr[t])))
                    if not ok and conflict >= P_over: ok = True; conflict = 0
                if ok:
                    ref = (Rn, tn, path[i], max(res, 0.05 * cfg.excl)); rep_a[t] = True
                    if seq_kappa and len(errs) >= 5:
                        ee = np.array(errs[-200:]); kap = float(np.clip(np.median(ee[:, 1] / ee[:, 0]), 0.005, 0.2))
            else:
                conflict = 0 if ref is None else conflict
    return rep_a, rep_b, has_ref, xdr, sdv, kap


def evaluate_mask(z, name, acc, seqs, cfg, nav=True):
    """evaluate() for an arbitrary report mask"""
    return evaluate(z, name, dict(acc=acc, seqs=seqs, cfg=cfg), nav=nav)


def online_v2(z, name, scope="pooled", null_kind="offwrong", gate_kind="strict", bridge="rigid", sc_lags=(), train_all=False,
              calib="regime", adaptive=False, floor=-np.inf, start_relax=False, null_cap=None, mondrian=None, verbose=False,
              null_oracle=None, geo_budget=None, anchors="ver", sc_mode="window", place_feats=False, train_null=False, **kw):
    """HSI v2 = geometric self-verification (a: trusted anchors, b: dead-reckoning agreement; trusted_geometry) OR
    (c) a hindsight-learned score above a conformal threshold calibrated on hindsight-null segments of the SAME regime
    (frames where a|b do not fire), held out from training. scope: 'pooled' (every session's held-out units) or 'session'.
    null_kind: 'off' (possibly off-map) or 'offwrong' (possibly off-map OR clearly wrong fix: e > excl + z sd)."""
    cfg = Cfg(z, name, **kw); t0 = time.time()
    MP, est, O = z["MP"], z["est_c"], z["o_q"]; n = len(est); cond = np.asarray(z["cond"]).astype(str); H = cfg.H
    seqs = deployment_seqs(z); order = np.concatenate(seqs)
    if adaptive: cfg.tolarr = adaptive_tolerance(z, seqs, cfg, mode="max" if adaptive == "max" else "free")
    anc = causal_anchor(MP, est, O, seqs, cfg, n)
    ra, rb, hr, xdr, sdr, kap = trusted_geometry(z, seqs, cfg, anc)
    geo = ra | rb
    X, names = features(z, seqs, cfg, anc)
    tree = cKDTree(MP); dm = np.full(n, np.nan); edr = np.full(n, np.nan)
    h = np.isfinite(xdr).all(1); dm[h] = tree.query(xdr[h])[0]; edr[h] = np.linalg.norm(MP[est[h]] - xdr[h], axis=1)
    X = np.c_[X, hr.astype(np.float32), np.log1p(edr), dm / cfg.off_d, np.log1p(sdr), geo.astype(np.float32)].astype(np.float32)
    names = names + ["has_ref", "e_ref", "dmap_ref", "sd_ref", "geo"]
    if adaptive == "max":                                       # hindsight labels keep the strict default tolerance
        T_ = cfg.tolarr; cfg.tolarr = None; ver = hindsight_verified(MP, est, O, seqs, cfg, n); cfg.tolarr = T_
    else: ver = hindsight_verified(MP, est, O, seqs, cfg, n)
    def labels_null(ver_):
        xt, sd, avail, kappa, s0, ncl = (hindsight_bridge if bridge == "blend" else hindsight)(z, seqs, cfg, ver_)
        return (xt, sd, avail, kappa, s0, ncl) + null_from(xt, sd)
    def null_from(xt, sd):
        y, null_off, dmap = hindsight_labels(z, Cfg(z, name, null_kind="off", **kw), xt, sd)
        if null_cap is not None:                                # cap the margin of the possibly-off-map null (NCLT: off_d 20 m)
            null_off = np.isfinite(sd) & (np.nan_to_num(dmap, nan=-np.inf) > cfg.off_d - np.minimum(cfg.zm * sd, null_cap * cfg.off_d))
        if null_kind in ("offwrong", "offwrong+unl"):
            e = np.linalg.norm(MP[est] - np.nan_to_num(xt), axis=1); null = null_off | (np.isfinite(sd) & (e > cfg.excl + cfg.zm * sd))
            if null_kind == "offwrong+unl":                   # never verified: a report there cannot be shown correct -> null
                null = null | ~np.isfinite(sd)
        else: null = null_off
        return y, dmap, null
    if anchors == "ver":
        xt, sd, avail, kappa, s0, ncl, y, dmap, null = labels_null(ver)
    else:                                                       # trusted causal geometry also anchors the hindsight bridges
        xt, sd, avail, kappa, s0, ncl, y, dmap, null = labels_null(ver | geo)
        if anchors == "ver+geo/charged":                        # ...but a geometric report is judged by the bridges WITHOUT the
            _, sdA, avA, _, _, _, _, _, nullA = labels_null(ver)  # geometry (it cannot certify itself): charged as before
            null = np.where(geo, nullA, null); avail = np.where(geo, avA, avail); sd = np.where(geo & ~np.isfinite(sdA), sdA, sd)
        elif anchors in ("ver+geo/loo", "ver+geo/loo-e"):       # ...and each anchor run is cross-examined by its neighbours only
            xl_, sl_, al_ = loo_bridge(z, seqs, cfg, ver | geo, kappa, s0)
            _, _, nullL = null_from(xl_, sl_)
            if anchors == "ver+geo/loo-e": nullL = nullL & np.isfinite(sl_)   # only EVIDENCE against a geometric report charges it
            null = np.where(geo, nullL, null); avail = np.where(geo, np.where(np.isfinite(sl_), al_, avail), avail)
            sd = np.where(geo & ~np.isfinite(sl_), np.inf, sd)
    # hindsight-CONFIDENT null frames (bridge certain even at zm sd): certainly off-map, or (certwrong) certainly a wrong fix
    e_b = np.linalg.norm(MP[est] - np.nan_to_num(xt), axis=1); dmap_ = np.nan_to_num(dmap, nan=-np.inf)
    cert = np.isfinite(sd) & (dmap_ - cfg.zm * sd > cfg.off_d)
    if geo_budget == "split-w": cert = cert | (np.isfinite(sd) & (e_b - cfg.zm * sd > cfg.excl))
    if null_oracle == "off": null = z["offm"].copy()           # DIAGNOSTIC ONLY (uses ground truth): calibrate on the true off-map frames
    elif null_oracle == "lab_or_off": null = (null & np.isfinite(sd)) | (~np.isfinite(sd) & z["offm"])   # truth only where unlabelled
    unit = np.zeros(n, np.int64); rank = np.empty(n, np.int64); rank[order] = np.arange(n)
    for si, idx in enumerate(seqs):
        unit[idx] = si * 100000 + np.arange(len(idx)) // cfg.unit
        nv = ~np.isfinite(sd[idx]); avail[idx[nv]] = rank[idx[-1]]                 # unlabelled frames: known at sequence end
    cal = calib_units(unit, cfg.cal_mod)
    zz = 2.0                                                                    # (c) may not contradict a trusted reference:
    if gate_kind == "strict":
        gate = ~hr | ((np.nan_to_num(edr, nan=np.inf) <= cfg.excl + zz * np.nan_to_num(sdr, nan=0)) &
                      (np.nan_to_num(dm, nan=np.inf) + zz * np.nan_to_num(sdr, nan=0) <= cfg.off_d))
    elif gate_kind == "loose":                                 # block only far contradictions of a trusted reference
        gate = ~hr | (np.nan_to_num(edr, nan=np.inf) - zz * np.nan_to_num(sdr, nan=0) <= cfg.off_d)
    else: gate = np.ones(n, bool)
    # (c) needs short-track support: the chain consistent with the odometry at every lag in sc_lags (causal)
    if sc_lags and hasattr(cfg, "sc_scale"): sc_lags = tuple(sorted({cfg.sc_scale(k) for k in sc_lags}))
    def sc_jump():
        sc = np.ones(n, bool)
        hz_ = horiz(MP); rm = getattr(cfg, "rot_max", None); K = tuple(sorted(sc_lags))   # support measured only SINCE the last jump of
        for idx in seqs:                                       # the chain (re-acquisition): the longest lag inside the current stretch
            L = len(idx); g = np.zeros(L, bool); ar = np.arange(L)   # decides (with its own window rotation); >= the shortest lag
            jmp = np.zeros(L, bool); jmp[1:] = lag_res(MP[est], O, idx, 1) > cfg.excl
            since = ar - np.maximum.accumulate(np.where(jmp, ar, 0))
            kmax = np.full(L, -1)
            for k in K: kmax[since >= k] = k
            for Kx in K:
                sel = kmax == Kx
                if not sel.any(): continue
                ang = window_rotation(MP[est], O, idx, Kx, hz_) if rm is not None else None
                gg = np.ones(L, bool)
                if rm is not None and len(hz_) == 2: gg &= np.abs(np.nan_to_num(ang, nan=np.inf)) <= rm
                for k in K:
                    if k > Kx: break
                    r = lag_res(MP[est], O, idx, k) if rm is None else lag_res_rot(MP[est], O, idx, k, ang, hz_)
                    okk = np.zeros(L, bool); okk[k:] = r <= cfg.tolv(k, idx[k:]); gg &= okk
                g[sel] = gg[sel]
            sc[idx] = g
        return sc
    def sc_window():
        sc = np.ones(n, bool)
        for idx in seqs:
            L = len(idx); g = np.ones(L, bool); g[:max(sc_lags)] = False; hz_ = horiz(MP); rm = getattr(cfg, "rot_max", None)
            if rm is not None:
                ang = window_rotation(MP[est], O, idx, max(sc_lags), hz_)
                if len(hz_) == 2: g &= np.abs(np.nan_to_num(ang, nan=np.inf)) <= rm
            for k in sc_lags:
                r = lag_res(MP[est], O, idx, k) if rm is None else lag_res_rot(MP[est], O, idx, k, ang, hz_)
                okk = np.zeros(L, bool); okk[k:] = r <= cfg.tolv(k, idx[k:]); g &= okk
            sc[idx] = g
        return sc
    if not sc_lags: sc = np.ones(n, bool)
    elif sc_mode == "jump": sc = sc_jump()
    elif sc_mode == "jump-dr":                                 # after a jump, the shorter support counts only if the new fix agrees
        e_ = np.nan_to_num(edr, nan=np.inf); s_ = np.nan_to_num(sdr, nan=np.inf)   # with dead reckoning from a trusted reference
        sc = sc_window() | (sc_jump() & hr & (e_ <= cfg.excl + zz * s_) & (s_ <= cfg.excl))
    else: sc = sc_window()
    st = np.zeros(n, bool)                                      # frames whose (c) eligibility rests on the start relaxation
    if start_relax and sc_lags:                                 # sequence starts: short-track support is undefined there
        for idx in seqs: st[idx[:max(sc_lags)]] = True
        st &= ~sc; sc = sc | st
    regime = ~geo & gate & sc
    # calibration units: JOINT (default) = every held-out null segment, scored by the whole rule (+inf where the geometry
    # reports, the learned score where (c) may report, -inf elsewhere) -> P(any report in a new null segment) <= alpha for
    # the union; 'regime' = only segments inside the (c) regime (conditional, more conservative)
    klass = (~hr).astype(np.int64) if mondrian == "ref" else np.zeros(n, np.int64)   # 1 = no trusted reference yet (start / lost)
    if mondrian == "start": klass = st.astype(np.int64)        # Mondrian by EVIDENCE STATE: frames relying on the start relaxation
    elif mondrian == "ref+start": klass = (~hr).astype(np.int64) + 2 * st   # are calibrated apart, so their risk cannot drain the rest
    segs = null_segments(seqs, null if calib == "joint" else null & regime, cal, unit, H, klass)
    seg_k = np.array([klass[s_[0]] for s_ in segs], np.int64) if segs else np.zeros(0, np.int64)
    seg_av = np.array([avail[s].max() for s in segs], np.int64) if segs else np.zeros(0, np.int64)
    seg_c = np.array([cond[s[0]] for s in segs]) if segs else np.zeros(0, str)
    seg_cert = np.array([cert[s_].all() for s_ in segs], bool) if segs else np.zeros(0, bool)
    seg_geo = np.array([geo[s_].any() for s_ in segs], bool) if segs else np.zeros(0, bool)
    if place_feats:                                             # the map learns its own blind spots (hubness of the place chain):
        from scipy import sparse                                # per map place, causal counts of hindsight-null vs verified fixes
        M = len(MP); nbl = cKDTree(MP).query_ball_point(MP, r=cfg.excl)   # and their similarity, pooled over places within excl
        A_ = sparse.csr_matrix((np.ones(sum(len(a) for a in nbl)), (np.repeat(np.arange(M), [len(a) for a in nbl]), np.concatenate(nbl))), shape=(M, M))
        neg = null | (y == 0); pos = (y == 1) & ~neg; ms = np.asarray(z["maxsim"], float)
        lab = np.flatnonzero((neg | pos) & (avail < BIG)); lab = lab[np.argsort(avail[lab], kind="stable")]; lab_av = avail[lab]; lp = 0
        acc_ = {k: np.zeros(M) for k in ("c0", "s0", "q0", "c1", "s1", "q1")}; sm_ = None
        X = np.c_[X, np.full((n, 5), np.nan, np.float32)]; names = names + ["pl_haz", "pl_sup", "pl_z0", "pl_z1", "pl_n0"]
    # training targets: hindsight labels (default), or (train_null) positives vs the CALIBRATION NULL itself (incl. never-verified
    # frames): the score then estimates the likelihood ratio against the very distribution the conformal threshold is set on
    # (Neyman-Pearson), so frames the model never saw as negatives cannot lock the threshold; training units only (split conformal)
    yt = np.where(null, 0, y).astype(np.int8) if train_null else y
    score = np.full(n, -np.inf); thr_at = np.full(n, np.inf); clf = None; last_n = 0
    for c0 in range(0, n, cfg.chunk):
        T = c0; cur = order[c0:c0 + cfg.chunk]; cc = cond[cur[0]]
        if place_feats:
            up = int(np.searchsorted(lab_av, T, side="left"))
            if up > lp or sm_ is None:
                new_ = lab[lp:up]; lp = up
                for g_, k_ in ((neg, "0"), (pos, "1")):
                    w_ = new_[g_[new_]]
                    np.add.at(acc_["c" + k_], est[w_], 1.0); np.add.at(acc_["s" + k_], est[w_], ms[w_]); np.add.at(acc_["q" + k_], est[w_], ms[w_] ** 2)
                sm_ = {k: A_ @ v for k, v in acc_.items()}
            pc = est[cur]; n0_, n1_ = sm_["c0"][pc], sm_["c1"][pc]
            mu0 = sm_["s0"][pc] / np.maximum(n0_, 1); sd0 = np.sqrt(np.maximum(sm_["q0"][pc] / np.maximum(n0_, 1) - mu0 ** 2, 1e-6))
            mu1 = sm_["s1"][pc] / np.maximum(n1_, 1); sd1 = np.sqrt(np.maximum(sm_["q1"][pc] / np.maximum(n1_, 1) - mu1 ** 2, 1e-6))
            X[cur, -5] = np.log((n0_ + 1) / (n1_ + 1)); X[cur, -4] = np.log1p(n0_ + n1_)
            X[cur, -3] = np.where(n0_ >= 3, (ms[cur] - mu0) / sd0, np.nan); X[cur, -2] = np.where(n1_ >= 3, (ms[cur] - mu1) / sd1, np.nan)
            X[cur, -1] = np.log1p(n0_)
        m = (yt >= 0) & (avail < T) & ~cal if train_all else (yt >= 0) & (avail < T) & ~cal & regime
        n1, n0 = int((yt[m] == 1).sum()), int((yt[m] == 0).sum())
        if n1 >= 50 and n0 >= 50 and (clf is None or m.sum() > 1.1 * last_n):
            clf = fit_model(X[m], yt[m]); last_n = int(m.sum())
        if clf is None: continue
        thr_k = {}
        for kk in np.unique(klass[cur]):
            sel = [i_ for i_, (a, c, sk) in enumerate(zip(seg_av, seg_c, seg_k)) if a < T and (scope == "pooled" or c == cc) and sk == kk]
            rs = [segs[i_] for i_ in sel]
            if len(rs) >= cfg.min_seg:
                ii = np.concatenate(rs); pp = clf.predict_proba(X[ii])[:, 1]
                f = np.where(regime[ii] & (pp > floor), pp, -np.inf); a_c = cfg.alpha
                if geo_budget is None: f[geo[ii]] = np.inf                # joint: a geometric report in a null segment is a violation
                else:                                                      # split: geometry charged its own (upper) rate, measured on
                    f[geo[ii]] = -np.inf                                   # the hindsight-confident null segments; (c) gets the rest
                    if geo_budget != "drop":
                        cs = np.array(sel)[seg_cert[sel]]; m_ = len(cs); k_ = int(seg_geo[cs].sum()) if m_ else 0
                        a_c = cfg.alpha - (k_ + 1) / (m_ + 1)
                thr_k[kk] = conformal_thr(f.reshape(len(rs), H).max(1), a_c) if a_c > 0 else np.inf
            else: thr_k[kk] = np.inf
        score[cur] = clf.predict_proba(X[cur])[:, 1]; thr_at[cur] = np.array([thr_k[k_] for k_ in klass[cur]])
    rc = (score > np.maximum(thr_at, floor)) & regime          # MAP floor: never report a fix the model thinks is more likely wrong
    acc = geo | rc
    return dict(acc=acc, ra=ra, rb=rb, rc=rc, score=score, thr=thr_at, anc=anc, y=y, null=null, seqs=seqs, cfg=cfg, kappa=kap, sc=sc, gate=gate,
                hr=hr, edr=edr, sdr=sdr, dm=dm, st=st,
                n_cal_seg=len(segs), names=names, secs=time.time() - t0)


def loo_bridge(z, seqs, cfg, ver, kappa, s0, zz=2.0):
    """leave-one-run-out cross-examination: hindsight positions of the frames of each anchor run predicted ONLY from its
    neighbouring anchor runs (blended dead reckoning as in hindsight_bridge, with the same closure test, kappa and s0), so
    an anchor never certifies itself. Frames of a run with no usable neighbour stay unlabelled (sd = inf)."""
    MP, est, O = z["MP"], z["est_c"], z["o_q"]; n = len(est); hz = horiz(MP); W = cfg.W
    order = np.concatenate(seqs); rank = np.empty(n, np.int64); rank[order] = np.arange(n)
    fit = lambda ii, idx: kabsch(O[idx[ii]][:, hz], MP[est[idx[ii]]][:, hz])
    xt = np.full((n, MP.shape[1]), np.nan); sd = np.full(n, np.inf); avail = np.full(n, BIG)
    for idx in seqs:
        L = len(idx); vi = np.flatnonzero(ver[idx])
        if not len(vi): continue
        path = np.r_[0, np.cumsum(np.linalg.norm(np.diff(O[idx], axis=0), axis=1))]
        runs = np.split(vi, np.flatnonzero(np.diff(vi) > 1) + 1)
        for j, r in enumerate(runs):
            r0 = runs[j - 1] if j > 0 else None; r1 = runs[j + 1] if j + 1 < len(runs) else None
            if r0 is None and r1 is None: continue
            gi = r; base = MP[est[idx[gi]]].astype(float)
            if r0 is not None: R0, t0 = fit(r0[-W:], idx); xl = base.copy(); xl[:, hz] = (R0 @ O[idx[gi]][:, hz].T).T + t0; dl = path[gi] - path[r0[-1]]
            if r1 is not None: R1, t1 = fit(r1[:W], idx); xr = base.copy(); xr[:, hz] = (R1 @ O[idx[gi]][:, hz].T).T + t1; dr = path[r1[0]] - path[gi]
            if r0 is not None and r1 is not None:
                g = path[r1[0]] - path[r0[-1]]; prl = (R0 @ O[idx[r1[0]]][hz]) + t0
                if np.linalg.norm(prl - MP[est[idx[r1[0]]]][hz]) > cfg.tau + zz * kappa * g: continue      # closure failed
                w = (dl / np.maximum(dl + dr, 1e-9))[:, None]; x = (1 - w) * xl + w * xr
                s_ = s0 + kappa * dl * dr / np.maximum(dl + dr, 1e-9); a = min(r1[0] + cfg.span, L - 1)
            elif r0 is not None: x, s_, a = xl, s0 + kappa * dl, L - 1
            else: x, s_, a = xr, s0 + kappa * dr, min(r1[0] + cfg.span, L - 1)
            xt[idx[gi]] = x; sd[idx[gi]] = s_; avail[idx[gi]] = rank[idx[a]]
    return xt, sd, avail


def hindsight_bridge(z, seqs, cfg, ver, zz=2.0):
    """hindsight positions v2: between two verified runs, forward dead reckoning from the left run (rigid fit on its last W
    frames) and backward from the right run are BLENDED by path distance (linear drift cancels at both ends); the
    uncertainty follows a Brownian bridge, sd = s0 + kappa * dl dr / (dl + dr); one-sided gaps: s0 + kappa * d. Gaps whose
    closure fails (left prediction of the right run off by more than tau + zz kappa gap) stay unlabelled (one of the runs
    is wrong). kappa: median one-sided prediction error / path over closed gaps (label-free); s0: median fit residual."""
    MP, est, O = z["MP"], z["est_c"], z["o_q"]; n = len(est); hz = horiz(MP); W = cfg.W
    order = np.concatenate(seqs); rank = np.empty(n, np.int64); rank[order] = np.arange(n)
    gaps, fitres, clos = [], [], []
    fit = lambda ii, idx: kabsch(O[idx[ii]][:, hz], MP[est[idx[ii]]][:, hz])
    for si, idx in enumerate(seqs):
        L = len(idx); vi = np.flatnonzero(ver[idx])
        if not len(vi): continue
        path = np.r_[0, np.cumsum(np.linalg.norm(np.diff(O[idx], axis=0), axis=1))]
        runs = np.split(vi, np.flatnonzero(np.diff(vi) > 1) + 1)
        for r in runs:
            Rm, tv = fit(r[-W:], idx); fitres.append(np.median(np.linalg.norm((Rm @ O[idx[r[-W:]]][:, hz].T).T + tv - MP[est[idx[r[-W:]]]][:, hz], axis=1)))
        for r0, r1 in zip(runs[:-1], runs[1:]):
            R0, t0 = fit(r0[-W:], idx); pr = (R0 @ O[idx[r1[:W]]][:, hz].T).T + t0
            clos.append((path[r1[0]] - path[r0[-1]], float(np.median(np.linalg.norm(pr - MP[est[idx[r1[:W]]]][:, hz], axis=1)))))
        gaps.append((si, idx, L, vi, runs, path))
    s0 = float(np.clip(np.median(fitres) if fitres else cfg.tau / 2, 0.05 * cfg.excl, cfg.tau))
    cl = np.array(clos) if clos else np.zeros((0, 2))
    kappa = float(np.clip(np.median(cl[:, 1] / np.maximum(cl[:, 0], 1.0)), 0.005, 0.2)) if len(cl) >= 5 else 0.05
    xt = np.full((n, MP.shape[1]), np.nan); sd = np.full(n, np.inf); avail = np.full(n, BIG)
    for si, idx, L, vi, runs, path in gaps:
        av = np.full(L, -1, np.int64)
        xt[idx[vi]] = MP[est[idx[vi]]]; sd[idx[vi]] = s0; av[vi] = np.minimum(vi + cfg.span, L - 1)
        for r0, r1 in zip([None] + runs, runs + [None]):
            if r0 is None and r1 is None: continue
            lo = 0 if r0 is None else r0[-1] + 1; hi = L if r1 is None else r1[0]
            if hi <= lo: continue
            gi = np.arange(lo, hi); base = MP[est[idx[gi]]].astype(float)
            if r0 is not None: R0, t0 = fit(r0[-W:], idx); xl = base.copy(); xl[:, hz] = (R0 @ O[idx[gi]][:, hz].T).T + t0; dl = path[gi] - path[r0[-1]]
            if r1 is not None: R1, t1 = fit(r1[:W], idx); xr = base.copy(); xr[:, hz] = (R1 @ O[idx[gi]][:, hz].T).T + t1; dr = path[r1[0]] - path[gi]
            if r0 is not None and r1 is not None:
                g = path[r1[0]] - path[r0[-1]]
                prl = (R0 @ O[idx[r1[0]]][hz]) + t0
                if np.linalg.norm(prl - MP[est[idx[r1[0]]]][hz]) > cfg.tau + zz * kappa * g: continue      # closure failed
                w = (dl / np.maximum(dl + dr, 1e-9))[:, None]; x = (1 - w) * xl + w * xr
                s = s0 + kappa * dl * dr / np.maximum(dl + dr, 1e-9); a = min(r1[0] + cfg.span, L - 1)
            elif r0 is not None: x, s, a = xl, s0 + kappa * dl, L - 1
            else: x, s, a = xr, s0 + kappa * dr, min(r1[0] + cfg.span, L - 1)
            xt[idx[gi]] = x; sd[idx[gi]] = s; av[gi] = a
        lab = av >= 0; avail[idx[lab]] = rank[idx[av[lab]]]
    return xt, sd, avail, kappa, s0, len(cl)
