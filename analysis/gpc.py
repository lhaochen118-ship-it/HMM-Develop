"""GPC -- Geometric Placement Certificate for sequential localization (Entry 26).

A per-frame false-fix guarantee that holds under ARBITRARY temporal dependence of the image evidence.

Ingredients at frame t (constants in problem units: excl = localisation tolerance):
  window      the last D metres of odometry path, sampled every `step` metres: K points O_t (newest first) and the
              query frames f_k nearest to each sample
  placements  P_t = stretches of the map's own traversal (either direction; end points on a grid of spacing g along the
              traversal) whose rigid 2-D Procrustes fit to O_t has RMS residual <= eps. P_t depends on the odometry and the
              map geometry ONLY, never on an image.
  hit         h_k(P) = 1[ ||m_top(f_k) - p_k(P)|| <= excl ]  (the top-1 map image of frame f_k lies at the placement's k-th point)
  strength    the per-frame map-calibrated SelfCal p-value p_k of the top-1 (super-uniform for off-map frames, Assumption D)
  q(p)        share of map images within excl of p (the chance that a placement point hits the top-1 if placements carry
              no information about the image: Assumption GAI, geometry-appearance independence)
Rule: certify frame t (report the end point of the best placement, or the place-chain MAP when it lies there) iff for some
P in P_t at least phi*K window frames have h_k(P) = 1 and p_k <= u*,   u* = alpha * phi / min(1, Q_t),
Q_t = (1/K) sum_k q(U_k), U_k = union over P in P_t of the excl-balls around p_k(P)  (the geometric coverage: the share of
the map that some placement could explain at window offset k; ~ the straight share of the map for straight paths, << 1 for
turning ones; always <= 1).

Theorem (dependence-free). Let t be a frame such that the robot is not within excl of p_k(P) at f_k for any P, k (e.g. t is
off-map and its window lies off the map). Under D (P(p_k <= u) <= u) and GAI (P(h_k(P) = 1 | images) <= q(p_k(P))), for ANY
joint law of the images over time:  P(t certified) <= alpha.
Proof: N_P := #{k : h_k(P) = 1, p_k <= u*}.  Each frame adds at most 1 to any N_P, so max_P N_P <= sum_k 1[top1(f_k) in U_k]
1[p_k <= u*], and E max_P N_P <= sum_k q(U_k) u* (GAI then D).  Markov: P(max_P N_P >= phi K) <= Q_t u* / phi.  Without GAI: N_P <= #{k : p_k <= u*} for every P, so
P <= K u* / (phi K) = u* / phi.  Hence P <= min(1, Q_t) u* / phi = alpha.  Linearity of expectation then gives E[FL] <= alpha
for the off-map false-report rate, with no assumption on the dependence between frames.            []
Without GAI the bound degrades gracefully to alpha / min(1, Q_t) (D only).

Per-frame certificate level (for operating curves):  a_t = min(1, Q_t) / phi * min_P u_P,  u_P = the ceil(phi K)-th
smallest p_k among the hit frames of P (inf if fewer hits): t is certified at level alpha iff a_t <= alpha."""
import numpy as np
from geo_place import map_chunks, resample_back


class PlacementBank:
    """all candidate placements (map traversal stretches of K points, both directions, end points every `grid` metres)"""

    def __init__(self, MP, step, K, grid, excl):
        self.step, self.K = step, K
        ch = map_chunks(MP, step); self.dim = ch[0].shape[1]
        g = max(1, int(round(grid / step))); C = []
        for c in ch:
            if len(c) < K: continue
            e1 = np.arange(K - 1, len(c), g); C.append(np.stack([c[e1 - i] for i in range(K)], 1))     # robot drives in map order
            e2 = np.arange(0, len(c) - K + 1, g); C.append(np.stack([c[e2 + i] for i in range(K)], 1))   # against map order
        self.C = np.concatenate(C) if C else np.zeros((0, K, self.dim))
        self.Cc = self.C - self.C.mean(1, keepdims=True)
        # q(p): share of map images within excl of every candidate point (GAI chance of a hit)
        from scipy.spatial import cKDTree
        from scipy import sparse
        P = MP.astype(float) if MP.ndim > 1 else MP.astype(float)[:, None]
        tr = cKDTree(P); pts = self.C.reshape(-1, self.dim); self.n_map = len(P)
        lists = tr.query_ball_point(pts, excl) if len(pts) else []
        cnt = np.array([len(x) for x in lists]) if len(pts) else np.zeros(0)
        self.q = (cnt / len(P)).reshape(self.C.shape[:2])
        # ball membership (candidate point -> map images within excl), for the coverage of a union of placements
        rows = np.repeat(np.arange(len(lists)), cnt) if len(pts) else np.zeros(0, int)
        cols = np.concatenate([np.asarray(x, int) for x in lists]) if len(pts) else np.zeros(0, int)
        self.B = sparse.csr_matrix((np.ones(len(rows), bool), (rows, cols)), shape=(len(pts), len(P)))

    def coverage(self, ok):
        """Q'_t = mean over window offsets k of the share of map images within excl of ANY placement point p_k(P), P in ok"""
        K = self.K; tot = 0.0
        for k in range(K):
            r = self.B[ok * K + k]; tot += np.unique(r.indices).size / self.n_map
        return tot / K

    def fit(self, O):
        """RMS residual of the rigid fit O -> every candidate"""
        Oc = O - O.mean(0)
        if self.dim == 1: return np.sqrt(((self.Cc[..., 0] - Oc[None, :, 0]) ** 2).mean(1))
        a = (Oc[None, :, 0] * self.Cc[..., 0]).sum(1) + (Oc[None, :, 1] * self.Cc[..., 1]).sum(1)
        b = (Oc[None, :, 0] * self.Cc[..., 1]).sum(1) - (Oc[None, :, 1] * self.Cc[..., 0]).sum(1)
        th = np.arctan2(b, a); c, s = np.cos(th), np.sin(th)
        rx = c[:, None] * Oc[None, :, 0] - s[:, None] * Oc[None, :, 1]; ry = s[:, None] * Oc[None, :, 0] + c[:, None] * Oc[None, :, 1]
        return np.sqrt(((self.Cc[..., 0] - rx) ** 2 + (self.Cc[..., 1] - ry) ** 2).mean(1))


def gpc(z, D_x=6.0, step_x=0.2, eps_x=0.25, grid_x=0.4, phi=0.5, pkey="p_frame", est=None, every=1):
    """GPC per frame from a nav_demo cache `z` (dict-like). Lengths in units of excl: D = D_x excl, step = step_x excl,
    eps = eps_x excl, grid = grid_x excl. Returns dict of per-frame arrays:
      a      certificate level a_t (inf where no window / no placement)      -> certified at alpha iff a <= alpha
      x_fix  reported position (end point of the best placement)
      Q      geometric multiplicity mass, npl = #placements, map_ok = place-chain MAP within excl of a certified end
      a_map  certificate level restricted to placements whose end point is within excl of the place-chain MAP"""
    excl = float(z["excl"]); MP = z["MP"]; top = z["top"]; est = z["est_c"] if est is None else est
    hz = list(z["hz"]); one_d = MP.ndim == 1 or MP.shape[1] == 1
    P2 = (MP[:, hz] if (not one_d and MP.shape[1] > 2) else MP).astype(float)
    if one_d: P2 = P2.reshape(-1, 1)
    o_all = z["o_q"]; o_all = (o_all[:, hz] if (not one_d and o_all.shape[1] > 2) else o_all).astype(float)
    if one_d: o_all = o_all.reshape(-1, 1)
    D, step, eps, grid = D_x * excl, step_x * excl, eps_x * excl, grid_x * excl
    K = int(round(D / step)) + 1; bank = PlacementBank(P2, step, K, grid, excl); need = int(np.ceil(phi * K))
    pv = np.clip(np.nan_to_num(z[pkey], nan=1.0), 1e-12, 1); xt = P2[top]; xe = P2[est]
    n = len(top); a = np.full(n, np.inf); a_map = np.full(n, np.inf); Q = np.full(n, np.nan); npl = np.zeros(n, int)
    x_fix = np.full((n, P2.shape[1]), np.nan)
    sid, kk = z["q_sid"], z["q_k"]
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(kk[idx])]; o = o_all[idx]
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        for i in range(0, len(idx), every):
            if cum[i] - cum[0] < D - 1e-6 or not len(bank.C): continue
            O = resample_back(o, cum, i, D, step)[:K]
            if len(O) < K: continue
            r = bank.fit(O); ok = np.flatnonzero(r <= eps); t = idx[i]; npl[t] = len(ok)
            if not len(ok): Q[t] = 0.0; continue
            f = idx[np.clip(np.searchsorted(cum, cum[i] - np.arange(K) * step, side="left"), 0, i)]   # frame at each sample
            Cp = bank.C[ok]; Qt = bank.coverage(ok); Q[t] = Qt
            hit = np.linalg.norm(Cp - xt[f][None], axis=2) <= excl                                  # (n_ok, K)
            pk = np.where(hit, pv[f][None], np.inf); uP = np.sort(pk, 1)[:, need - 1]                # need-th smallest p among hits
            sc = min(1.0, Qt) / phi * uP; j = int(np.argmin(sc)); a[t] = sc[j]; x_fix[t] = Cp[j, 0]
            near = np.linalg.norm(Cp[:, 0] - xe[t], axis=1) <= excl
            if near.any(): a_map[t] = sc[near].min()
    return dict(a=a, a_map=a_map, x_fix=x_fix, Q=Q, npl=npl)
