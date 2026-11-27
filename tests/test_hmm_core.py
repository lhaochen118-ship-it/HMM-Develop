"""G0 correctness tests: probability conservation, brute-force equivalence, boundaries, all-null."""
import itertools, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hmmloc import hmm
import scipy.sparse as sp


def dense_T(cfg):
    """Explicit (MK+1)x(MK+1) transition matrix implied by the filter equations."""
    M, K = cfg.M, cfg.K; e, rho, eta = cfg.exit_prob, cfg.null_stay, cfg.leak
    N = M * K + 1; Tm = np.zeros((N, N))
    A = [k.toarray() for k in cfg.kernels]
    for i in range(M):
        for k in range(K):
            for j in range(M):
                for k2 in range(K):
                    Tm[i * K + k, j * K + k2] = (1 - e) * ((1 - eta) * cfg.Pv[k, k2] * A[k2][i, j] + eta / M * cfg.P0v[k2])
            Tm[i * K + k, N - 1] = e
    for j in range(M):
        for k2 in range(K):
            Tm[N - 1, j * K + k2] = (1 - rho) * ((1 - eta) * cfg.reentry[j] + eta / M) * cfg.P0v[k2]
    Tm[N - 1, N - 1] = rho
    return Tm


def make_cfg(M=4, K=2, rng=None):
    rng = rng or np.random.default_rng(0)
    ks = []
    for _ in range(K):
        A = rng.random((M, M)) * (rng.random((M, M)) < 0.6) + np.eye(M) * 0.1
        A /= A.sum(1, keepdims=True); ks.append(sp.csr_matrix(A))
    return hmm.HMMConfig(ks, Pv=hmm.sticky_velocity(K, 0.8), P0v=np.array([0.3, 0.7])[:K] / np.array([0.3, 0.7])[:K].sum(),
                         exit_prob=0.05, null_stay=0.7, null_prior=0.1, leak=0.02, use_null=True,
                         reentry=rng.random(M) + 0.1)


def test_conservation_and_bruteforce():
    rng = np.random.default_rng(1)
    for trial in range(5):
        M, K, T = 3, 2, 4
        cfg = make_cfg(M, K, rng)
        L = rng.normal(size=(T, M)); Ln = rng.normal(size=T); beta = rng.uniform(0.3, 1.2, size=T)
        V = rng.normal(size=(T, K))
        out = hmm.forward(L, cfg, beta=beta, loglik_null=Ln, vel_loglik=V)
        tot = out["post"].sum(1) + out["null"]
        assert np.allclose(tot, 1, atol=1e-6), tot
        # brute force over all paths
        Tm = dense_T(cfg); N = M * K + 1
        init = np.zeros(N); init[:-1] = np.repeat(np.full(M, (1 - cfg.null_prior) / M), K) * np.tile(cfg.P0v, M)
        init[-1] = cfg.null_prior
        def emis(t, s):
            if s == N - 1: return np.exp(beta[t] * Ln[t]) * (cfg.P0v * np.exp(V[t])).sum()
            return np.exp(beta[t] * L[t, s // K] + V[t, s % K])
        for tt in range(T):
            marg = np.zeros(N)
            for path in itertools.product(range(N), repeat=tt + 1):
                p = init[path[0]] * emis(0, path[0])
                for u in range(1, tt + 1): p *= Tm[path[u - 1], path[u]] * emis(u, path[u])
                marg[path[-1]] += p
            marg /= marg.sum()
            onmap = marg[:-1].reshape(M, K).sum(1)
            assert np.allclose(onmap, out["post"][tt], atol=1e-5), (tt, onmap, out["post"][tt])
            assert np.isclose(marg[-1], out["null"][tt], atol=1e-6)


def test_dense_rows_stochastic():
    cfg = make_cfg(5, 2)
    Tm = dense_T(cfg); assert np.allclose(Tm.sum(1), 1)


def test_edge_cases():
    M = 6; s = np.arange(M, dtype=float)
    A = hmm.chain_kernel(s, mean=1.0, std=0.7)
    assert np.allclose(np.asarray(A.sum(1)).ravel(), 1)              # boundary rows renormalised
    for use_null, leak in [(True, 0.0), (False, 0.0), (True, 1.0), (False, 1e-3)]:
        cfg = hmm.HMMConfig([A], exit_prob=0.0 if not use_null else 0.1, leak=leak, use_null=use_null)
        L = np.full((5, M), -50.0)                                      # everything looks like a non-match
        o = hmm.forward(L, cfg)
        assert np.allclose(o["post"].sum(1) + o["null"], 1, atol=1e-6)
        if use_null: assert o["null"][-1] > 0.99                        # all-null evidence -> off-map
    L = np.zeros((4, 1)); cfg = hmm.HMMConfig([sp.csr_matrix(np.ones((1, 1)))], use_null=False)
    assert np.allclose(hmm.forward(L, cfg)["post"], 1)                  # K=1, M=1


def test_reset_and_lag():
    rng = np.random.default_rng(3); M = 8
    A = hmm.chain_kernel(np.arange(M, dtype=float), mean=1.0, std=0.8)
    cfg = hmm.HMMConfig([A], use_null=False, leak=1e-3)
    L = rng.normal(size=(10, M)); rm = np.zeros(10, bool); rm[5] = True
    o1 = hmm.forward(L, cfg, reset_mask=rm)["post"]; o2 = hmm.forward(L[5:], cfg)["post"]
    assert np.allclose(o1[5:], o2, atol=1e-6)
    sm = hmm.forward_backward_lag(L, cfg, lag=0)
    assert np.allclose(sm, hmm.forward(L, cfg)["post"], atol=1e-5)


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("PASS", n)
