"""Local analysis library for the VPR reliability study (runs on CPU from NB15 dumps).

Core object: an Episode = (query descriptors, map descriptors, map/query poses, condition labels).
Reliability scores are computed from the query->map similarity vector (+ map poses where a method needs them).
"""
import os, json
import numpy as np

# --------------------------------------------------------------------------- data
class Episode:
    """q: (Nq,D) map: (Nm,D) descriptors (L2-normalised). Positions in metres (or frames for Nordland, 1-D)."""
    def __init__(self, name, q, m, q_pos, m_pos, q_cond, q_R=None, m_R=None, unit="m"):
        self.name, self.q, self.m = name, q, m
        self.q_pos, self.m_pos = np.asarray(q_pos, float), np.asarray(m_pos, float)
        if self.q_pos.ndim == 1: self.q_pos, self.m_pos = self.q_pos[:, None], self.m_pos[:, None]
        self.q_cond = np.asarray(q_cond); self.q_R, self.m_R = q_R, m_R; self.unit = unit
        self._S = None

    @property
    def S(self):
        if self._S is None:
            self._S = (self.q.astype(np.float32) @ self.m.astype(np.float32).T)
        return self._S

    def subset_map(self, keep):
        e = Episode(self.name, self.q, self.m[keep], self.q_pos, self.m_pos[keep], self.q_cond,
                    self.q_R, None if self.m_R is None else self.m_R[keep], self.unit)
        if self._S is not None: e._S = self._S[:, keep]
        return e

    def subset_q(self, sel):
        e = Episode(self.name, self.q[sel], self.m, self.q_pos[sel], self.m_pos, self.q_cond[sel],
                    None if self.q_R is None else self.q_R[sel], self.m_R, self.unit)
        if self._S is not None: e._S = self._S[sel]
        return e


def rot_angle_deg(Ra, Rb):
    """Angle of Ra^T Rb, vectorised over leading dims."""
    tr = np.einsum("...ij,...ij->...", Ra, Rb)  # trace(Ra^T Rb)
    return np.degrees(np.arccos(np.clip((tr - 1) / 2, -1, 1)))


def top1_errors(ep):
    top = ep.S.argmax(1)
    dt = np.linalg.norm(ep.q_pos - ep.m_pos[top], axis=1)
    da = rot_angle_deg(ep.q_R, ep.m_R[top]) if (ep.q_R is not None and ep.m_R is not None) else np.zeros(len(top))
    return top, dt, da


def correct(ep, tol_m, tol_deg=None):
    _, dt, da = top1_errors(ep)
    ok = dt <= tol_m
    if tol_deg is not None: ok &= da <= tol_deg
    return ok


def nearest_map_dist(ep):
    d = np.sqrt(((ep.q_pos[:, None, :] - ep.m_pos[None, :, :]) ** 2).sum(-1))
    return d.min(1)


# --------------------------------------------------------------------------- loaders
def load_robotcar(dump, desc="salad"):
    m = np.load(os.path.join(dump, "meta", "rc.npz"), allow_pickle=True)
    q = np.load(os.path.join(dump, desc, "rc_q.npy")); r = np.load(os.path.join(dump, desc, "rc_ref.npy"))
    return Episode("robotcar", q, r, m["q_C"], m["ref_C"], m["q_cond"], m["q_R"], m["ref_R"])


def load_cmu(dump, desc="salad"):
    eps = []
    for f in sorted(os.listdir(os.path.join(dump, "meta"))):
        if not f.startswith("cmu_s"): continue
        s = f[4:-4]; m = np.load(os.path.join(dump, "meta", f), allow_pickle=True)
        qp = os.path.join(dump, desc, f"cmu_{s}_q.npy")
        if not os.path.isfile(qp): continue
        eps.append(Episode(f"cmu_{s}", np.load(qp), np.load(os.path.join(dump, desc, f"cmu_{s}_db.npy")),
                           m["q_C"], m["db_C"], m["q_cond"], m["q_R"], m["db_R"]))
    return eps


def load_nordland(dump, desc="salad", ref="summer"):
    m = np.load(os.path.join(dump, "meta", "nord.npz"), allow_pickle=True)
    seasons = [str(s) for s in m["seasons"]]; R = np.load(os.path.join(dump, desc, f"nord_{ref}.npy"))
    n = len(R); qs, cs = [], []
    for s in seasons:
        if s == ref: continue
        qs.append(np.load(os.path.join(dump, desc, f"nord_{s}.npy"))); cs += [s] * n
    pos = np.arange(n, dtype=float)
    return Episode("nordland", np.concatenate(qs), R, np.tile(pos, len(qs)), pos, np.array(cs), unit="frame")


# --------------------------------------------------------------------------- score-based baselines
def _softmax_max(S, T=0.05):
    z = S / T; z = z - z.max(1, keepdims=True); p = np.exp(z); p /= p.sum(1, keepdims=True)
    return p.max(1), -(p * np.log(p + 1e-12)).sum(1)


def baseline_scores(ep, k=10):
    """Higher = more confident. All label-free, training-free score functions from the literature."""
    S = ep.S; part = -np.sort(-S, axis=1)[:, :max(k, 2)]
    s1, s2 = part[:, 0], part[:, 1]
    d1, d2 = np.sqrt(np.maximum(2 - 2 * s1, 0)), np.sqrt(np.maximum(2 - 2 * s2, 0))
    sm, ent = _softmax_max(S)
    rs = (part[:, 1:k] / part[:, :1]).mean(1)                      # Ratio Spread (Miller'26) - uncertainty
    sd = np.median(part[:, :k], 1) / part[:, 0]                       # Similarity Distribution - uncertainty
    mu, sdv = S.mean(1), S.std(1) + 1e-9
    return {"maxsim": s1, "neg_L2": -d1, "PA": -(d1 / np.maximum(d2, 1e-9)), "margin": s1 - s2,
            "softmax": sm, "neg_entropy": -ent, "neg_RS": -rs, "neg_SD": -sd, "neg_SU": -(0.5 * rs + 0.5 * sd),
            "znorm": (s1 - mu) / sdv}


def sue_score(ep, K=10, lam=350.0):
    """True SUE (Zaffar CVPR'24): weighted spatial variance of the top-K reference positions. Returns -trace."""
    S = ep.S; idx = np.argsort(-S, 1)[:, :K]
    d = np.sqrt(np.maximum(2 - 2 * np.take_along_axis(S, idx, 1), 0))
    w = np.exp(-lam * d); w /= w.sum(1, keepdims=True) + 1e-12
    P = ep.m_pos[idx]                                   # (Nq,K,dim)
    mu = (w[..., None] * P).sum(1, keepdims=True)
    var = (w[..., None] * (P - mu) ** 2).sum((1, 2))
    return -var


# --------------------------------------------------------------------------- EVS: extreme-value spacing test
def map_cells(m_pos, cell):
    """Hash map positions into spatial cells of size `cell`. Returns (cell_id per map item, cell centres)."""
    P = np.asarray(m_pos, float)
    if P.shape[1] >= 3:   # project onto the 2 dominant (ground-plane) axes
        c = P - P.mean(0); _, _, Vt = np.linalg.svd(c, full_matrices=False); P = c @ Vt[:2].T
    key = np.floor(P / cell).astype(np.int64)
    _, cid = np.unique(key, axis=0, return_inverse=True); cid = cid.ravel()
    cent = np.stack([np.asarray(m_pos, float)[cid == c].mean(0) for c in range(cid.max() + 1)])
    return cid, cent


def evs_test(ep, cell=10.0, excl=25.0, k=10, return_parts=False):
    """Label-free per-query p-value that the top-1 is NOT a null (off-map / random) region maximum.

    Region maxima Z_c = max_{j in cell c} s_j over cells farther than `excl` from the top-1 reference.
    With X_(1)=s1 and X_(j+1)=Z_(j) the descending competitors, Renyi's representation for Gumbel-domain
    maxima gives j*(X_(j)-X_(j+1)) ~ iid Exp(beta) under H0, so
        T = (X_(1)-X_(2)) / ( (1/k) sum_{j=2}^{k+1} j (X_(j)-X_(j+1)) ) ~ F(2, 2k),
        p = (1 + T/k)^(-k)   (closed form).
    """
    S = ep.S; cid, cent = map_cells(ep.m_pos, cell); nc = cid.max() + 1
    Z = np.full((S.shape[0], nc), -np.inf, np.float32)
    for c in range(nc):
        Z[:, c] = S[:, cid == c].max(1)
    top = S.argmax(1); s1 = S[np.arange(len(top)), top]
    dc = np.sqrt(((ep.m_pos[top][:, None, :] - cent[None, :, :]) ** 2).sum(-1))   # (Nq, nc)
    Z = np.where(dc > excl, Z, -np.inf)
    Zs = -np.sort(-Z, 1)[:, :k + 1]
    ok = np.isfinite(Zs).all(1)
    D = s1 - Zs[:, 0]
    j = np.arange(2, k + 2)[None, :]
    beta = (j * (Zs[:, :-1] - Zs[:, 1:])).mean(1)
    T = D / np.maximum(beta, 1e-9)
    p = np.where(ok, (1 + T / k) ** (-k), 1.0)
    if return_parts: return p, {"D": D, "beta": beta, "T": T, "valid": ok, "ncells": nc}
    return p


# --------------------------------------------------------------------------- metrics
def auroc(score, label):
    """AUROC of `score` for predicting label==1 (ties averaged)."""
    score = np.asarray(score, float); label = np.asarray(label).astype(bool)
    n1, n0 = label.sum(), (~label).sum()
    if n1 == 0 or n0 == 0: return float("nan")
    order = np.argsort(score, kind="mergesort"); r = np.empty(len(score)); r[order] = np.arange(1, len(score) + 1)
    _, inv, cnt = np.unique(score, return_inverse=True, return_counts=True)
    sums = np.bincount(inv, weights=r); r = (sums / cnt)[inv]
    return float((r[label].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def aurc(conf, correct_):
    o = np.argsort(-np.asarray(conf, float), kind="mergesort"); err = 1 - np.asarray(correct_, float)[o]
    return float((np.cumsum(err) / np.arange(1, len(err) + 1)).mean())


def ece(prob, correct_, bins=15):
    prob = np.clip(np.asarray(prob, float), 0, 1); c = np.asarray(correct_, float)
    edges = np.linspace(0, 1, bins + 1); idx = np.clip(np.digitize(prob, edges[1:-1]), 0, bins - 1); e = 0.0
    for b in range(bins):
        m = idx == b
        if m.any(): e += m.mean() * abs(prob[m].mean() - c[m].mean())
    return float(e)


def bh(p, alpha):
    """Benjamini-Hochberg: boolean reject (=accept the match) mask."""
    p = np.asarray(p, float); n = len(p); o = np.argsort(p)
    thr = alpha * np.arange(1, n + 1) / n; ok = p[o] <= thr
    kmax = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
    acc = np.zeros(n, bool); acc[o[:kmax]] = True
    return acc


def fit_logistic(X, y, l2=1e-3, iters=200):
    X = np.column_stack([np.ones(len(X)), (X - X.mean(0)) / (X.std(0) + 1e-9)]); w = np.zeros(X.shape[1])
    mu0, sd0 = None, None
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ w)); g = X.T @ (p - y) / len(y) + l2 * w
        H = (X * (p * (1 - p))[:, None]).T @ X / len(y) + l2 * np.eye(len(w)); w -= np.linalg.solve(H, g)
    return w


def logistic_model(Xtr, ytr, l2=1e-3):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    w = fit_logistic(Xtr, ytr, l2)
    def f(X):
        Z = np.column_stack([np.ones(len(X)), (X - mu) / sd]); return 1 / (1 + np.exp(-Z @ w))
    return f
