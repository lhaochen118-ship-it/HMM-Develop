"""Mass-conserving HMM forward filter for sequence-based visual localization.

State space: z_t in {(j, k) : j map node, k velocity bin} U {null (off-map)}.
Prediction (per step, all mass conserved, see Master Plan §3.4 / issue A01):
    on-map  : b~(j,k') = (1-eta) * [ sum_i sum_k (1-e) P(k'|k) A_{k'}(i,j) b(i,k) + (1-rho) r_j P0(k') b(null) ]
                         + eta * u(j) P0(k') * (1 - b(null))         (global recovery leak; u uniform)
    null    : b~(null) = e * sum_{i,k} b(i,k) + rho * b(null)
Update:  b(j,k) ∝ b~(j,k) * exp(beta_t * l_t(j)),  b(null) ∝ b~(null) * exp(beta_t * l_t(null)).
A_k rows are normalised over on-map successors (boundary handled by row renormalisation, never by
renormalising the whole vector, which would hide leaks). Sum of all mass is exactly 1 after every step.

The emission l_t is a *log-likelihood ratio* against an "everything is a non-match" baseline, so the
null state has l_t(null)=0 exactly (all reference images are non-matches when off-map).
"""
from __future__ import annotations
import numpy as np
import scipy.sparse as sp


# ----------------------------------------------------------------------------------- map / kernels
def arc_length(C: np.ndarray) -> np.ndarray:
    """Cumulative path length of an ordered sequence of camera centres (M,3) -> (M,)."""
    d = np.linalg.norm(np.diff(C, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(d)])


def chain_kernel(s: np.ndarray, mean: float, std: float, back: float = None, width_sd: float = 4.0,
                 floor: float = 0.0) -> sp.csr_matrix:
    """Row-stochastic transition over an ordered map with node positions s (arc-length or index).
    Displacement d = s_j - s_i ~ N(mean, std^2), truncated to [mean - width_sd*std, mean + width_sd*std]
    (and >= -back if back is given). `floor` adds a small uniform mass inside the window (robustness)."""
    s = np.asarray(s, float); M = len(s)
    lo_d, hi_d = mean - width_sd * std, mean + width_sd * std
    if back is not None: lo_d = max(lo_d, -back)
    rows, cols, vals = [], [], []
    lo_idx = np.searchsorted(s, s + lo_d, side="left")
    hi_idx = np.searchsorted(s, s + hi_d, side="right")
    for i in range(M):
        a, b = lo_idx[i], max(hi_idx[i], lo_idx[i] + 1)
        b = min(b, M); a = min(a, M - 1)
        js = np.arange(a, b)
        if len(js) == 0: js = np.array([min(i, M - 1)])
        d = s[js] - s[i]
        w = np.exp(-0.5 * ((d - mean) / max(std, 1e-9)) ** 2) + floor
        w = w / w.sum()
        rows.append(np.full(len(js), i)); cols.append(js); vals.append(w)
    A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(M, M))
    return A


def add_junctions(A: sp.csr_matrix, C: np.ndarray, radius: float, weight: float) -> sp.csr_matrix:
    """Mix a kernel with 'junction' edges to map nodes whose camera centres are within `radius` of the
    kernel's successors but far in chain order (loops / revisits). Uses only map poses (allowed input)."""
    from scipy.spatial import cKDTree
    tree = cKDTree(C); M = A.shape[0]
    near = tree.query_ball_point(C, r=radius)
    J = sp.lil_matrix((M, M))
    for i, nb in enumerate(near):
        nb = [j for j in nb if abs(j - i) > 5]
        if nb:
            for j in nb: J[i, j] = 1.0 / len(nb)
    J = J.tocsr()
    has = np.asarray(J.sum(1)).ravel() > 0
    # successor-preserving: go via junction then apply the chain kernel
    JA = J @ A
    W = sp.diags(np.where(has, weight, 0.0)) @ JA + sp.diags(np.where(has, 1 - weight, 1.0)) @ A
    W = sp.csr_matrix(W); rs = np.asarray(W.sum(1)).ravel(); W = sp.diags(1 / rs) @ W
    return sp.csr_matrix(W)


# ----------------------------------------------------------------------------------- filter config
class HMMConfig:
    def __init__(self, kernels, Pv=None, P0v=None, exit_prob=0.0, null_stay=0.9, null_prior=0.0,
                 leak=1e-3, use_null=True, reentry=None):
        self.kernels = list(kernels)                 # list of K csr (M x M) row-stochastic
        K = len(self.kernels)
        self.K = K
        self.Pv = np.eye(K) if Pv is None else np.asarray(Pv, float)          # P(k'|k)  rows sum to 1
        self.P0v = np.full(K, 1.0 / K) if P0v is None else np.asarray(P0v, float)
        self.exit_prob = exit_prob; self.null_stay = null_stay; self.null_prior = null_prior
        self.leak = leak; self.use_null = use_null
        self.M = self.kernels[0].shape[0]
        self.reentry = np.full(self.M, 1.0 / self.M) if reentry is None else reentry / reentry.sum()
        self.kernelsT = [k.T.tocsr() for k in self.kernels]
        assert np.allclose(self.Pv.sum(1), 1) and np.isclose(self.P0v.sum(), 1)


def sticky_velocity(K: int, stay: float) -> np.ndarray:
    """Velocity-bin transition: stay with prob `stay`, else move to an adjacent bin (reflecting)."""
    P = np.zeros((K, K))
    for k in range(K):
        nb = [j for j in (k - 1, k + 1) if 0 <= j < K]
        P[k, k] = stay if nb else 1.0
        for j in nb: P[k, j] = (1 - stay) / len(nb)
    return P


# ----------------------------------------------------------------------------------- forward filter
def forward(loglik: np.ndarray, cfg: HMMConfig, beta=1.0, loglik_null=None, init=None,
            return_full=False, reset_mask=None, vel_loglik=None):
    """Causal filtering.  loglik: (T, M) log-likelihood ratios l_t(j). beta: scalar or (T,) tempering.
    loglik_null: (T,) or None (=0, the LLR null).  reset_mask: (T,) bool, start a new sequence there.
    vel_loglik: (T,K) optional log p(m_t | v_t=k) — a second emission stream observed by the velocity state
    (e.g. the appearance change between consecutive frames). The null state uses the P0v-marginal of it.
    Returns dict with 'post' (T,M) on-map marginal posterior, 'null' (T,), 'vel' (T,K)."""
    T, M = loglik.shape; K = cfg.K
    beta = np.broadcast_to(np.asarray(beta, float), (T,))
    lnull = np.zeros(T) if loglik_null is None else np.asarray(loglik_null, float)
    post = np.empty((T, M), np.float32); nullp = np.empty(T); vel = np.empty((T, K))
    def fresh():
        b = np.outer(np.full(M, (1 - cfg.null_prior) / M), cfg.P0v) if init is None else np.outer(init * (1 - cfg.null_prior), cfg.P0v)
        return b, (cfg.null_prior if cfg.use_null else 0.0)
    b, bn = fresh()
    for t in range(T):
        if t > 0 and reset_mask is not None and reset_mask[t]:
            b, bn = fresh()
            pred, pn = b, bn
        elif t == 0:
            pred, pn = b, bn
        else:
            e = cfg.exit_prob if cfg.use_null else 0.0
            mix = b @ cfg.Pv                                   # (M,K): sum_k b(i,k) P(k'|k)
            pred = np.empty_like(b)
            for k in range(K):
                pred[:, k] = cfg.kernelsT[k] @ mix[:, k]
            onmass = b.sum()
            pred *= (1 - e)
            if cfg.use_null:
                pred += np.outer((1 - cfg.null_stay) * bn * cfg.reentry, cfg.P0v)
                pn = e * onmass + cfg.null_stay * bn
            else:
                pn = 0.0
            if cfg.leak > 0:
                tot_on = pred.sum()
                pred = (1 - cfg.leak) * pred + cfg.leak * tot_on * np.outer(np.full(M, 1.0 / M), cfg.P0v)
        # update
        l = beta[t] * loglik[t].astype(np.float64)
        ln = beta[t] * lnull[t] if cfg.use_null else -np.inf
        if vel_loglik is not None:
            mv = vel_loglik[t].astype(np.float64); mvm = mv.max()
            wk = np.exp(mv - mvm)
            ln = ln + (np.log((cfg.P0v * wk).sum()) + mvm) if cfg.use_null else ln
            lk_off = mvm
        else:
            wk = np.ones(K); lk_off = 0.0
        m = max(l.max() + lk_off, ln if cfg.use_null else -np.inf)
        w = np.exp(l + lk_off - m)
        b = pred * w[:, None] * wk[None, :]
        bn = pn * np.exp(ln - m) if cfg.use_null else 0.0
        Z = b.sum() + bn
        if not np.isfinite(Z) or Z <= 0:
            b, bn = fresh(); Z = 1.0
        b /= Z; bn = bn / Z
        post[t] = b.sum(1); nullp[t] = bn; vel[t] = b.sum(0) / max(b.sum(), 1e-300)
    out = {"post": post, "null": nullp, "vel": vel}
    return out


def forward_backward_lag(loglik, cfg: HMMConfig, lag: int, beta=1.0, reset_mask=None):
    """Fixed-lag smoothing (velocity-marginal, null disabled): posterior of z_{t} given o_{1:t+lag}.
    Implemented by re-running a backward pass over a sliding window (O(T*lag) matvecs). K must be 1."""
    assert cfg.K == 1, "fixed-lag implemented for K=1"
    T, M = loglik.shape
    filt = forward(loglik, cfg, beta=beta, reset_mask=reset_mask)["post"].astype(np.float64)
    A = cfg.kernels[0]; beta = np.broadcast_to(np.asarray(beta, float), (T,))
    seg_end = np.full(T, T)
    if reset_mask is not None:
        starts = list(np.where(reset_mask)[0]) + [T]
        for a, bnd in zip([0] + starts[:-1], starts): seg_end[a:bnd] = bnd
    out = np.empty_like(filt)
    for t in range(T):
        end = min(t + lag, seg_end[t] - 1)
        beta_msg = np.ones(M)
        for u in range(end, t, -1):
            l = beta[u] * loglik[u]; w = np.exp(l - l.max())
            beta_msg = A @ (w * beta_msg); beta_msg /= beta_msg.sum()
        p = filt[t] * beta_msg; out[t] = p / p.sum()
    return out


def viterbi(loglik, A: sp.csr_matrix, beta=1.0):
    """Max-product decoding over a single kernel (no null), log-space. Returns path (T,)."""
    T, M = loglik.shape
    logA = A.copy(); logA.data = np.log(logA.data + 1e-300)
    logA = logA.tocsc()
    delta = beta * loglik[0] - np.log(M); bp = np.zeros((T, M), np.int32)
    for t in range(1, T):
        best = np.full(M, -np.inf); arg = np.zeros(M, np.int32)
        for j in range(M):
            s, e = logA.indptr[j], logA.indptr[j + 1]
            if s == e: continue
            cand = delta[logA.indices[s:e]] + logA.data[s:e]
            k = np.argmax(cand); best[j] = cand[k]; arg[j] = logA.indices[s + k]
        delta = best + beta * loglik[t]; bp[t] = arg
    path = np.zeros(T, np.int64); path[-1] = int(np.argmax(delta))
    for t in range(T - 1, 0, -1): path[t - 1] = bp[t, path[t]]
    return path


def forward_kernel_seq(loglik, kernels, kidx, beta=1.0, leak=1e-3, reset_mask=None):
    """Diagnostic (ORACLE motion): K=1 filter whose transition at step t is kernels[kidx[t]]."""
    T, M = loglik.shape; beta = np.broadcast_to(np.asarray(beta, float), (T,))
    KT = [k.T.tocsr() for k in kernels]
    post = np.empty((T, M), np.float32); b = np.full(M, 1.0 / M)
    for t in range(T):
        if t == 0 or (reset_mask is not None and reset_mask[t]):
            pred = np.full(M, 1.0 / M)
        else:
            pred = KT[kidx[t]] @ b; pred = (1 - leak) * pred + leak * pred.sum() / M
        l = beta[t] * loglik[t]; w = np.exp(l - l.max()); b = pred * w; b /= b.sum(); post[t] = b
    return post
