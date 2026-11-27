"""[P] Synthetic check of T1: stop-and-go chain, AR(1)-dependent LLR whose correlation is high when stopped.
Compares beta=1, best fixed beta, IA beta_t from a noisy change proxy, and oracle beta_t=(1-rho)/(1+rho)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from hmmloc import hmm, infoaware, metrics

def simulate(seed, M=300, T=1500, delta=1.5, rho_stop=0.95, rho_move=0.2, p_stop=0.03, p_go=0.1):
    rng = np.random.default_rng(seed)
    z = np.zeros(T, int); stop = np.zeros(T, bool); z[0] = rng.integers(0, M // 3)
    for t in range(1, T):
        stop[t] = (rng.random() < (1 - p_go)) if stop[t - 1] else (rng.random() < p_stop)
        z[t] = min(M - 1, z[t - 1] + (0 if stop[t] else 1))
    rho = np.where(stop, rho_stop, rho_move)
    e = np.zeros((T, M)); e[0] = rng.normal(size=M)
    for t in range(1, T): e[t] = rho[t] * e[t - 1] + np.sqrt(1 - rho[t] ** 2) * rng.normal(size=M)
    L = e.copy(); L[np.arange(T), z] += delta
    change = (1 - rho) + 0.05 * rng.normal(size=T); change = np.clip(change, 1e-4, None); change[0] = np.inf
    return L, z, rho, change

def run(L, z, beta, M):
    A = hmm.chain_kernel(np.arange(M, dtype=float), mean=0.7, std=0.8)
    cfg = hmm.HMMConfig([A], use_null=False, leak=1e-3)
    post = hmm.forward(L, cfg, beta=beta)["post"]
    pos = np.abs(np.arange(M)[None] - z[:, None]) <= 1
    pred = post.argmax(1); corr = pos[np.arange(len(z)), pred]
    conf = np.array([post[t, max(0, pred[t]-1):pred[t]+2].sum() for t in range(len(z))])
    return metrics.event_nll(post, pos).mean(), corr.mean(), np.mean((conf > 0.9) & ~corr)

if __name__ == "__main__":
    M = 300; res = {k: [] for k in ["beta1", "fixed*", "IA", "oracle"]}
    for seed in range(4):
        L, z, rho, ch = simulate(seed, M=M)
        fixed = min([(run(L, z, b, M)[0], b) for b in (0.1, 0.2, 0.35, 0.5, 0.75, 1.0)])[1]
        ia = min([(run(L, z, infoaware.beta_schedule(ch, b0, k), M)[0], b0, k) for b0 in (0.5, 1.0, 1.5) for k in (0.4, 0.6, 0.8, 1.0)])
        res["beta1"].append(run(L, z, 1.0, M)); res["fixed*"].append(run(L, z, fixed, M))
        res["IA"].append(run(L, z, infoaware.beta_schedule(ch, ia[1], ia[2]), M))
        res["oracle"].append(run(L, z, (1 - rho) / (1 + rho), M))
    for k, v in res.items():
        v = np.array(v); print(f"{k:7s} NLL {v[:,0].mean():.3f}±{v[:,0].std():.3f}  R@1 {v[:,1].mean():.3f}  CW@0.9 {v[:,2].mean():.4f}")
