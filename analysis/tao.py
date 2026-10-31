"""TAO'26 baseline (Lu & Tanaka, arXiv 2607.04745 v1, Trajectory-Anchor Optimization), reproduced from the paper text.
Specs and our choices: literature/BASELINES_2026.md.

Per frame t, every one of the K = 100 retrieval hypotheses j (topk_dump.py) is solved independently (no state across
frames): anchors are traced backward along the map route from j by the odometry path length of each of the last N = 20
frames (both traversal directions), the 2-D rigid motion odometry -> anchors is fitted (batched Procrustes), and
  C(j) = trimmed-75% mean of Huber_8m(residual) / 8^2  +  2 * mean_i (1 - s_i(j)),
s_i(j) = largest similarity among frame i's top-K entries within 4 m (route length) of the anchor, else frame i's K-th.
Winner j* = argmin C; reported place = map position of j*; the map-out score is C(j*).
Usage (library): tao(z, tk) -> dict(x_fix, cost, j); z = nav_demo cache, tk = topk_dump npz."""
import numpy as np


def route(MP, gap_x=5.0):
    """route coordinate of every reduced-map row: chunk id and arc length (rows in map order, chunks split at jumps)"""
    P = MP.astype(float) if MP.ndim > 1 else MP.astype(float)[:, None]
    d = np.linalg.norm(np.diff(P, axis=0), axis=1); gap = max(gap_x * np.median(d[d > 0]) if (d > 0).any() else 1.0, 1e-6)
    cid = np.r_[0, np.cumsum(d > gap)]; arc = np.r_[0, np.cumsum(np.where(d > gap, 0.0, d))]
    return P, cid, arc


def tao(z, tk, N=20, delta=8.0, trim=0.75, wapp=2.0, tol=4.0, hz=None):
    MP = z["MP"]; one_d = MP.ndim == 1 or MP.shape[1] == 1
    hz = list(z["hz"]) if hz is None else hz
    P, cid, arc = route(MP[:, hz] if (not one_d and MP.shape[1] > 2) else MP)
    o_all = z["o_q"]; o_all = (o_all[:, hz] if (not one_d and o_all.shape[1] > 2) else o_all).astype(float)
    if one_d: o_all = o_all.reshape(-1, 1)
    I, Sm = tk["idx"], tk["sim"].astype(np.float32); K = I.shape[1]
    # global route key: chunk id * BIG + arc length, so that "within tol along the same chunk" is a 1-D interval test
    BIG = 1e7; key_all = cid * BIG + arc
    starts = {c: arc[cid == c].min() for c in np.unique(cid)}; ends = {c: arc[cid == c].max() for c in np.unique(cid)}
    lo_arc = np.array([starts[c] for c in cid]); hi_arc = np.array([ends[c] for c in cid])
    n = len(I); x_fix = np.full((n, P.shape[1]), np.nan); cost = np.full(n, np.inf); jbest = np.full(n, -1)
    sid, kk = z["q_sid"], z["q_k"]
    # per frame: top-K entries sorted by route key (for the anchor appearance look-up)
    order = np.argsort(key_all[I], axis=1); Ks = np.take_along_axis(key_all[I], order, 1); Ss = np.take_along_axis(Sm, order, 1)
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(kk[idx])]; o = o_all[idx]
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        for i in range(len(idx)):
            t = idx[i]; w = np.arange(max(0, i - N + 1), i + 1)[::-1]            # newest first
            if len(w) < 3: continue
            dl = cum[i] - cum[w]                                                 # odometry path back to each window frame
            j = I[t]; c, a0 = cid[j], arc[j]
            best = (np.inf, None, None)
            for sgn in (1.0, -1.0):                                              # +1: robot drives in map order
                aa = a0[:, None] - sgn * dl[None, :]                             # anchor arc length (K, n_w)
                inside = (aa >= lo_arc[j][:, None]) & (aa <= hi_arc[j][:, None])
                # anchor positions: interpolate along the chunk (rows of one chunk are contiguous in map order)
                q = np.empty(aa.shape + (P.shape[1],))
                for d in range(P.shape[1]): q[..., d] = np.interp((c[:, None] * BIG + aa).ravel(), key_all, P[:, d]).reshape(aa.shape)
                pw = o[w]; pc = pw - pw.mean(0); qc = q - q.mean(1, keepdims=True)
                if P.shape[1] == 1:
                    res = np.abs(qc[..., 0] - pc[None, :, 0])
                else:
                    a_ = (pc[None, :, 0] * qc[..., 0] + pc[None, :, 1] * qc[..., 1]).sum(1)
                    b_ = (pc[None, :, 0] * qc[..., 1] - pc[None, :, 1] * qc[..., 0]).sum(1)
                    th = np.arctan2(b_, a_); cs, sn = np.cos(th)[:, None], np.sin(th)[:, None]
                    rx = cs * pc[None, :, 0] - sn * pc[None, :, 1]; ry = sn * pc[None, :, 0] + cs * pc[None, :, 1]
                    res = np.sqrt((qc[..., 0] - rx) ** 2 + (qc[..., 1] - ry) ** 2)
                hub = np.where(res <= delta, 0.5 * res ** 2, delta * (res - 0.5 * delta)) / delta ** 2
                hub = np.where(inside, hub, 10.0)                                # anchor off the route chunk: large residual
                m = max(1, int(np.ceil(trim * len(w)))); geo = np.sort(hub, 1)[:, :m].mean(1)
                # appearance of each anchor in its window frame
                app = np.empty(aa.shape)
                for l, f in enumerate(idx[w]):
                    key = c * BIG + aa[:, l]; ks, ss = Ks[f], Ss[f]
                    p = np.searchsorted(ks, key); best_s = np.full(len(key), ss.min())
                    for off in (-2, -1, 0, 1):
                        pp = np.clip(p + off, 0, K - 1); okk = np.abs(ks[pp] - key) <= tol
                        best_s = np.where(okk, np.maximum(best_s, ss[pp]), best_s)
                    app[:, l] = best_s
                C = geo + wapp * (1.0 - app).mean(1)
                k = int(np.argmin(C))
                if C[k] < best[0]: best = (float(C[k]), k, sgn)
            cost[t], jbest[t] = best[0], j[best[1]]; x_fix[t] = P[j[best[1]]]
    return dict(x_fix=x_fix, cost=cost, j=jbest)


def tao_threshold(cost, good, bsel):
    """tau_OOD = mean + 3 std of the winner cost over correctly localised on-map frames of the two easiest conditions
    (labels; the paper's '3-sigma residual bounds of the calibration split')"""
    c = cost[good & bsel & np.isfinite(cost)]
    return float(c.mean() + 3 * c.std()) if len(c) else np.inf
