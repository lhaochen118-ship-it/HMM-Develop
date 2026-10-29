"""HMM sequence localization with an off-map state, evaluated on maps with holes (navigation protocol).

Protocol: the map loses a random 30 % of its spatial blocks (seeded); query frames farther than off_d from the
remaining map are OFF-MAP, frames within in_d are ON-MAP (frames in between are ignored in the metrics). Every query
sequence is filtered online. Per frame a method outputs a map index or "unknown".
Metrics: on-map recall (output within tol), on-map false (output beyond tol), off-map false-localisation rate,
availability. Odometry = integrated GT displacement with scale error and noise (as seq_odo.py).

Methods:
  single      top-1 always
  hmm         forward filter, emission exp(s/T) (T tuned on a held-out condition; Doan'19 / Xu'20 style), no off-map
  hmm_kth     + off-map state with emission exp(s_(k)/T), s_(k) = k-th best similarity (Xu'21 style), T, k tuned
  evt         EVT-HMM (ours, tuning-free): per-query affine-invariant z-scores of cell maxima; the map's own
              leave-block-out pseudo-queries give the Gumbel law (mu, beta) of the best NON-matching z; emission of
              place j = exp((z_j - mu) / beta) (Gumbel-tail likelihood ratio), off-map state = phantom place at mu.
The filter outputs argmax state; "unknown" when the argmax is the off-map state.
Usage: hmm_eval.py <dump> <rc|cmu|nord> <desc> [seeds=3] -> results/hmmeval_<ds>_<desc>.json"""
import sys, os, json, time
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V
from sc_eval import CFG

try:
    import torch
    DEV = "cuda" if torch.cuda.is_available() else None
except ImportError:
    torch, DEV = None, None


def sims(q, m):
    if DEV:
        Q, M = torch.from_numpy(q.astype(np.float32)).to(DEV), torch.from_numpy(m.astype(np.float32)).to(DEV)
        return torch.cat([(Q[i:i + 4096] @ M.T).cpu() for i in range(0, len(Q), 4096)]).numpy()
    return q.astype(np.float32) @ m.astype(np.float32).T


def zscores(S, cid, nc):
    """per-query affine-invariant z of every map item w.r.t. the query's cell-maximum distribution (median / MAD)"""
    Z = np.empty_like(S)
    order = np.argsort(cid, kind="stable"); starts = np.r_[0, np.flatnonzero(np.diff(cid[order])) + 1]
    for i in range(0, len(S), 2048):
        s = S[i:i + 2048]; cm = np.maximum.reduceat(s[:, order], starts, axis=1)
        med = np.median(cm, 1, keepdims=True); mad = np.median(np.abs(cm - med), 1, keepdims=True) * 1.4826 + 1e-6
        Z[i:i + 2048] = (s - med) / mad
    return Z


class Filter:
    """forward filter over N map states (+ optional off-map state) with odometry transitions on sparse neighbour pairs"""

    def __init__(self, m_pos, sigma, radius, m_R=None, p_out=0.01, p_in=0.05, eps=1e-4, conf_r=5.0):
        """m_R (N,3,3) camera->world rotation of every map image: odometry increments are then given in the BODY
        (camera) frame and rotated into the world by the orientation of the source state i (as real odometry)."""
        self.n = len(m_pos); tr = cKDTree(m_pos); pr = tr.query_pairs(radius, output_type="ndarray")
        self.ii = np.r_[pr[:, 0], pr[:, 1], np.arange(self.n)]; self.jj = np.r_[pr[:, 1], pr[:, 0], np.arange(self.n)]
        self.D = m_pos[self.jj] - m_pos[self.ii]; self.sigma, self.p_out, self.p_in, self.eps = sigma, p_out, p_in, eps
        self.Ri = None if m_R is None else np.asarray(m_R, float)[self.ii]
        self.nbr = tr.query_ball_point(m_pos, conf_r)                   # confidence = posterior mass within conf_r of the MAP state

    def run(self, E, U, off=None):
        """E (L,N) emission (unnormalised, linear), U (L,dim) odometry increments, off (L,) off-map emission or None.
        returns est (L,) map index or -1 (off-map), conf (L,) posterior mass within conf_r of the best place"""
        L = len(E); b = np.full(self.n, 1.0 / self.n); bo = 0.5 if off is not None else 0.0; b *= (1 - bo); est = np.empty(L, int); conf = np.empty(L)
        for t in range(L):
            if t > 0:
                u = U[t][None] if self.Ri is None else np.einsum("pij,j->pi", self.Ri, U[t])
                w = np.exp(-0.5 * ((self.D - u) ** 2).sum(1) / self.sigma ** 2)
                z = np.bincount(self.ii, w, self.n); z[z == 0] = 1
                nb = np.bincount(self.jj, b[self.ii] * w / z[self.ii], self.n)
                if off is not None:
                    stay = nb.sum(); nb = (1 - self.p_out) * nb + self.p_in * bo / self.n; bo = (1 - self.p_in) * bo + self.p_out * stay
                b = (1 - self.eps) * nb + self.eps * (nb.sum() + bo) / self.n
            b = b * E[t]
            if off is not None: bo = bo * off[t]
            s = b.sum() + bo; b /= s; bo /= s
            j = int(b.argmax()); est[t] = -1 if (off is not None and bo > b[j]) else j; conf[t] = b[self.nbr[j]].sum()
            if est[t] < 0: est[t] = -1 - j                                   # keep the best place, encoded (-1-j)
        return est, conf


def odometry(pos, sid, k, seed, R=None, scale_sd=0.03, step_sd=0.05):
    """simulated odometry increments from GT: per-sequence scale error + per-step noise; in the body frame of the
    previous frame (R = camera->world GT rotations) when R is given, else in the world frame"""
    rng = np.random.default_rng(seed); U = np.zeros_like(pos)
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(k[idx])]; dx = np.diff(pos[idx], axis=0)
        if R is not None: dx = np.einsum("nji,nj->ni", R[idx[:-1]], dx)
        U[idx[1:]] = (1 + rng.normal(0, scale_sd)) * dx + rng.normal(0, 1, dx.shape) * step_sd * np.linalg.norm(dx, axis=1, keepdims=True)
    return U


def vio_odometry(ep, sid, k):
    """real odometry: VIO increments in the body frame of the previous frame, mapped into the GNSS camera frame by the
    fixed rotation X (VIO body -> camera) fitted once by Procrustes on the map-free query data (extrinsic calibration)"""
    U = np.zeros_like(ep.q_pos); G = np.zeros_like(ep.q_pos)
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(k[idx])]
        U[idx[1:]] = np.einsum("nji,nj->ni", ep.q_vioR[idx[:-1]], np.diff(ep.q_vio[idx], axis=0))
        G[idx[1:]] = np.einsum("nji,nj->ni", ep.q_R[idx[:-1]], np.diff(ep.q_pos[idx], axis=0))
    Uu, _, Vt = np.linalg.svd(G.T @ U); X = Uu @ np.diag([1, 1, np.linalg.det(Uu @ Vt)]) @ Vt
    out = U @ X.T
    print("VIO->camera rotation fitted; residual median %.3f m, step median %.3f m" % (np.median(np.linalg.norm(out - G, axis=1)), np.median(np.linalg.norm(G, axis=1))), flush=True)
    return out


def gumbel_null(m, m_pos, bid, keep, cid_full, off_d, n_max=3000, seed=0):
    """map pseudo-queries: kept map items of block b queried against kept map items of other blocks (> off_d away);
    returns the best z per pseudo-query (Gumbel moment fit)."""
    rng = np.random.default_rng(seed); kept = np.flatnonzero(keep); best = []
    for b in np.unique(bid[kept]):
        qi = kept[bid[kept] == b]; mi = kept[bid[kept] != b]
        if len(mi) < 50: continue
        d, _ = cKDTree(m_pos[mi]).query(m_pos[qi]); qi = qi[d > off_d]
        if not len(qi): continue
        qi = qi[rng.permutation(len(qi))[:max(1, n_max // 20)]]
        S = sims(m[qi], m[mi]); _, cc = np.unique(cid_full[mi], return_inverse=True)
        best.append(zscores(S, cc.ravel(), cc.max() + 1).max(1))
    x = np.concatenate(best); beta = x.std() * np.sqrt(6) / np.pi; mu = x.mean() - 0.5772 * beta
    return mu, beta, len(x)


def main():
    dump, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3]; seeds = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    if ds.startswith("4s:"):
        ep = V.load_4seasons(dump, desc, ds[3:]); c = CFG["cmu"]
    else:
        ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
    q_sid, q_k, _, _ = V.frame_order(dump, ds, ep, desc)
    unit_tol = c["tol"][0]; nord = ds in ("nord", "nordw")
    sigma, radius = (1.0, 6.0) if nord else (2.0, 15.0)
    cid_full, _ = V.map_cells(ep.m_pos, c["cell"]); bid, _ = V.map_cells(ep.m_pos, c["block"])
    S_all = sims(ep.q, ep.m); cond = np.asarray(ep.q_cond).astype(str); conds = sorted(set(cond))
    seqs = [np.where(q_sid == s)[0][np.argsort(q_k[q_sid == s])] for s in np.unique(q_sid)]
    out = {"ds": ds, "desc": desc, "runs": []}; tag = ds.replace(":", "_")
    for seed in range(seeds):
        t0 = time.time(); rng = np.random.default_rng(seed); blocks = np.unique(bid)
        keep = ~np.isin(bid, rng.choice(blocks, int(round(0.3 * len(blocks))), replace=False))
        mp = ep.m_pos[keep]; S = S_all[:, keep]; _, cc = np.unique(cid_full[keep], return_inverse=True); cc = cc.ravel()
        dmap, _ = cKDTree(mp).query(ep.q_pos); onm = dmap <= c["in_d"]; offm = dmap > c["off_d"]
        Z = zscores(S, cc, cc.max() + 1)
        mu, beta, nnull = gumbel_null(ep.m, ep.m_pos, bid, keep, cid_full, c["off_d"], seed=seed)
        body = ep.q_R is not None and ep.m_R is not None
        if hasattr(ep, "q_vio"): U = vio_odometry(ep, q_sid, q_k)       # 4Seasons: real VIO
        else: U = odometry(ep.q_pos, q_sid, q_k, 1000 + seed, R=ep.q_R if body else None)
        F = Filter(mp, sigma, radius, m_R=ep.m_R[keep] if body else None, conf_r=unit_tol)
        tune_c = conds[0]                                      # T / k tuned on one condition (labels), applied to all
        srt = -np.sort(-S, 1)

        def evaluate(est, conf=None):
            best = np.where(est >= 0, est, -1 - est); err_b = np.linalg.norm(ep.q_pos - mp[best], axis=1)
            est = np.where(est >= 0, est, -1)
            err = np.where(est >= 0, err_b, np.inf)
            r = {}
            if conf is not None:                                         # threshold-free: accept best place iff conf >= tau
                on_ok = (err_b <= unit_tol)[onm]; c_on, c_off = conf[onm], conf[offm]
                taus = np.unique(np.r_[c_off, np.inf]); fl = np.array([(c_off >= t).mean() for t in taus])
                rec = np.array([((c_on >= t) & on_ok).mean() for t in taus])
                r["curve"] = {f"R@FL{a}": float(rec[fl <= a].max()) for a in (0.01, 0.05, 0.1)}
                r["curve"]["AUC"] = float(np.trapezoid(rec[np.argsort(fl)], np.sort(fl))) if len(taus) > 1 else 0.0
            for cn in conds + ["ALL"]:
                if cn == "curve": continue
                sel = (cond == cn) if cn != "ALL" else np.ones(len(cond), bool)
                r[cn] = dict(recall=float((err[sel & onm] <= unit_tol).mean()), wrong=float(((est >= 0) & (err > unit_tol))[sel & onm].mean()),
                             offmap_false=float((est >= 0)[sel & offm].mean()) if (sel & offm).any() else None,
                             avail=float((est >= 0)[sel & onm].mean()))
            return r

        def run_all(E, off=None, subset=None):
            est = np.full(len(cond), -1, int); conf = np.zeros(len(cond))
            for idx in seqs:
                if subset is not None and not subset[idx[0]]: continue
                est[idx], conf[idx] = F.run(E[idx], U[idx], None if off is None else off[idx])
            return est, conf

        res = {"seed": seed, "mu": float(mu), "beta": float(beta), "n_null": nnull, "n_on": int(onm.sum()), "n_off": int(offm.sum()), "methods": {}}
        res["methods"]["single"] = evaluate(S.argmax(1), S.max(1))
        res["methods"]["single_z"] = evaluate(Z.argmax(1), Z.max(1))
        # tuned baselines: grid on condition tune_c (labels), objective recall - offmap_false
        sub = cond == tune_c
        def score(r): return r[tune_c]["recall"] - (r[tune_c]["offmap_false"] or 0) - r[tune_c]["wrong"]
        best = None
        for T in (0.005, 0.01, 0.02, 0.05):
            E = np.exp((S - S.max(1, keepdims=True)) / T); r = evaluate(run_all(E, subset=sub)[0])
            if best is None or score(r) > best[0]: best = (score(r), T)
        T = best[1]; E = np.exp((S - S.max(1, keepdims=True)) / T)
        res["methods"]["hmm"] = evaluate(*run_all(E)); res["methods"]["hmm"]["T"] = T
        best = None
        for T in (0.005, 0.01, 0.02, 0.05):
            for k in (2, 5, 10, 20):
                E = np.exp((S - S.max(1, keepdims=True)) / T); off = np.exp((srt[:, k - 1] - S.max(1)) / T)
                r = evaluate(run_all(E, off, subset=sub)[0])
                if best is None or score(r) > best[0]: best = (score(r), T, k)
        _, T, k = best; E = np.exp((S - S.max(1, keepdims=True)) / T); off = np.exp((srt[:, k - 1] - S.max(1)) / T)
        res["methods"]["hmm_kth"] = evaluate(*run_all(E, off)); res["methods"]["hmm_kth"].update(T=T, k=k)
        zmax = Z.max(1, keepdims=True)
        E = np.exp((Z - zmax) / beta); off = np.exp((mu - zmax[:, 0]) / beta)
        res["methods"]["evt"] = evaluate(*run_all(E, off))
        E2 = np.exp((Z - zmax) / beta); res["methods"]["evt_nooff"] = evaluate(*run_all(E2))
        out["runs"].append(res)
        print(f"[{ds}/{desc} seed {seed}] mu {mu:.2f} beta {beta:.2f} null {nnull} on {onm.sum()} off {offm.sum()} ({time.time()-t0:.0f}s)", flush=True)
        for nm, r in res["methods"].items():
            a = r["ALL"]; w = min((r[cn]["recall"] for cn in conds))
            print(f"   {nm:10s} recall {a['recall']:.3f} (worst {w:.3f}) wrong {a['wrong']:.3f} offmap-false {a['offmap_false']:.3f} avail {a['avail']:.3f} curve {r.get('curve')}"
                  + (f"  T={r.get('T')} k={r.get('k')}" if "T" in r else ""), flush=True)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/hmmeval_{tag}_{desc}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
