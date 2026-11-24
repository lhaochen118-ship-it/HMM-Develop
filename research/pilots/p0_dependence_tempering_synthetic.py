#!/usr/bin/env python3
"""Pilot P0 (SYNTHETIC ONLY) — does temporally-correlated observation noise make a place-HMM
over-confident, and does variance-matching tempering beta=(1-rho)/(1+rho) restore calibration?

Model (deliberately minimal, NOT a claim about real data):
  * M places on a 1-D route; true trajectory p_t = p0 + t (velocity 1).
  * Similarity field S[t,j] = mu*1[j==p_t] + sigma*N[t,j], where the noise is AR(1) along the
    diagonals (the direction a v=1 HMM integrates): N[t,j] = rho*N[t-1,j-1] + sqrt(1-rho^2)*xi.
  * Emission log-potential = beta * S/tau, tau fit by single-frame NLL (temperature scaling, as in the repo).
  * Banded motion kernel (v=1, std=1) + small uniform leak.
Prediction (Prop. "variance-matching tempering"): ECE(beta=1) grows with rho; beta_theory=(1-rho)/(1+rho)
keeps ECE low; the NLL-optimal beta fitted on calibration sequences is close to beta_theory.
Usage: python p0_dependence_tempering_synthetic.py [--out results.json]
"""
import json, sys, argparse
import numpy as np

def lse(x, axis=None):
    m = np.max(x, axis=axis, keepdims=True)
    return np.squeeze(m + np.log(np.exp(x - m).sum(axis=axis, keepdims=True)), axis=axis)

def make_field(T, M, rho, rng):
    N = np.empty((T, M))
    N[0] = rng.standard_normal(M)
    a = np.sqrt(1 - rho ** 2)
    for t in range(1, T):
        xi = rng.standard_normal(M)
        N[t, 0] = xi[0]
        N[t, 1:] = rho * N[t - 1, :-1] + a * xi[1:]
    return N

def episode(T, M, mu, sigma, rho, rng):
    p0 = rng.integers(0, M - T - 1)
    truth = p0 + np.arange(T)
    S = sigma * make_field(T, M, rho, rng)
    S[np.arange(T), truth] += mu
    return S, truth

def motion(b, offs, w, leak):
    M = b.shape[0]; out = np.zeros_like(b)
    for o, wt in zip(offs, w):
        if o == 0: out += wt * b
        elif o > 0: out[o:] += wt * b[:M - o]
        else: out[:M + o] += wt * b[-o:]
    out /= out.sum()
    return (1 - leak) * out + leak / M

def run_filter(S, inv_tau, beta, leak=1e-3):
    T, M = S.shape
    offs = np.arange(-3, 6); w = np.exp(-0.5 * ((offs - 1) / 1.0) ** 2); w /= w.sum()
    b = np.full(M, 1.0 / M); post = np.empty((T, M))
    for t in range(T):
        b = motion(b, offs, w, leak)
        lb = np.log(b + 1e-300) + beta * S[t] * inv_tau
        lb -= lse(lb); b = np.exp(lb); post[t] = b
    return post

def whiten_diag(S, rho):
    """Innovation field along the v=1 diagonal: U[t,j] = S[t,j] - rho*S[t-1,j-1] (AR(1) whitening).
    This is the emission an AR-HMM would use for the transition j-1 -> j (approximation: it ignores
    the motion-kernel spread, i.e. it whitens only along the nominal-velocity diagonal)."""
    U = S.copy()
    U[1:, 1:] = S[1:, 1:] - rho * S[:-1, :-1]
    U[1:, 0] = S[1:, 0] * np.sqrt(1 - rho ** 2)
    return U

def vif(rho, L):
    """Variance-inflation factor of a sum of L AR(1) terms: 1 + 2*sum_k (1-k/L) rho^k."""
    k = np.arange(1, int(L))
    return float(1 + 2 * np.sum((1 - k / L) * rho ** k)) if L > 1 else 1.0

def ece(conf, corr, n_bins=15):
    # equal-mass bins (more stable than equal-width at high confidence)
    order = np.argsort(conf); conf, corr = conf[order], corr[order]
    e = 0.0
    for idx in np.array_split(np.arange(len(conf)), n_bins):
        if len(idx): e += len(idx) / len(conf) * abs(conf[idx].mean() - corr[idx].mean())
    return float(e)

def fit_tau(eps):
    best = (None, np.inf)
    for tau in np.logspace(-2, 1, 60):
        nll = 0.0; n = 0
        for S, tr in eps:
            lp = S / tau; lp = lp - lse(lp, axis=1)[:, None]
            nll -= lp[np.arange(len(tr)), tr].sum(); n += len(tr)
        if nll / n < best[1]: best = (tau, nll / n)
    return best[0]

def evaluate(eps, inv_tau, beta, burn=10):
    conf, corr, nll = [], [], []
    for S, tr in eps:
        P = run_filter(S, inv_tau, beta)[burn:]; t_true = tr[burn:]
        pred = P.argmax(1)
        conf.append(P.max(1)); corr.append((np.abs(pred - t_true) <= 1).astype(float))
        nll.append(-np.log(P[np.arange(len(t_true)), t_true] + 1e-300))
    conf, corr, nll = map(np.concatenate, (conf, corr, nll))
    over = float(((conf > 0.9) & (corr == 0)).mean())
    return dict(ECE=ece(conf, corr), acc=float(corr.mean()), NLL=float(nll.mean()),
                mean_conf=float(conf.mean()), confident_wrong=over)

def label_free_rho(S, top_exclude=3):
    """Estimate the diagonal lag-1 autocorrelation of the similarity field WITHOUT labels:
    mask each row's top-k entries (likely true matches) and correlate R[t,j] with R[t-1,j-1]."""
    R = S - S.mean(1, keepdims=True)
    mask = np.ones_like(S, bool)
    top = np.argsort(-S, axis=1)[:, :top_exclude]
    for t in range(S.shape[0]):
        lo = np.clip(top[t][:, None] + np.arange(-2, 3)[None, :], 0, S.shape[1] - 1)
        mask[t, lo.ravel()] = False
    a = R[1:, 1:]; b = R[:-1, :-1]; m = mask[1:, 1:] & mask[:-1, :-1]
    return float(np.corrcoef(a[m], b[m])[0, 1])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=None)
    ap.add_argument("--seed", type=int, default=0); args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    M, T, mu, sigma = 400, 60, 1.6, 1.0
    n_cal, n_test = 25, 60
    rows = []
    for rho in [0.0, 0.3, 0.5, 0.7, 0.85]:
        cal = [episode(T, M, mu, sigma, rho, rng) for _ in range(n_cal)]
        test = [episode(T, M, mu, sigma, rho, rng) for _ in range(n_test)]
        inv_tau = 1.0 / fit_tau(cal)                       # single-frame temperature scaling
        b_theory = (1 - rho) / (1 + rho)
        grid = np.linspace(0.05, 1.2, 24)                  # NLL-optimal beta on calibration seqs
        b_fit = grid[int(np.argmin([evaluate(cal, inv_tau, b)["NLL"] for b in grid]))]
        rho_hat = float(np.mean([label_free_rho(S) for S, _ in cal]))
        b_hat = (1 - rho_hat) / (1 + rho_hat)
        r = dict(rho=rho, rho_hat_label_free=round(rho_hat, 3), beta_theory=round(b_theory, 3),
                 beta_from_rho_hat=round(b_hat, 3), beta_nll_fit=round(float(b_fit), 3),
                 naive=evaluate(test, inv_tau, 1.0), theory=evaluate(test, inv_tau, b_theory),
                 label_free=evaluate(test, inv_tau, b_hat), fitted=evaluate(test, inv_tau, b_fit))
        # (b) AR-HMM-style whitened emission: temperature re-fit on the innovation field
        cal_w = [(whiten_diag(S, rho_hat), tr) for S, tr in cal]
        test_w = [(whiten_diag(S, rho_hat), tr) for S, tr in test]
        inv_tau_w = 1.0 / fit_tau(cal_w)
        r["whitened"] = evaluate(test_w, inv_tau_w, 1.0)
        # (c) finite-window variance-matching: pick L by NLL on calibration, beta = 1/VIF(rho_hat, L)
        Ls = [1, 2, 3, 4, 6, 8, 12, 20]
        nlls = [evaluate(cal, inv_tau, 1.0 / vif(rho_hat, L))["NLL"] for L in Ls]
        L_best = Ls[int(np.argmin(nlls))]
        r["L_eff"] = L_best; r["beta_vif"] = round(1.0 / vif(rho_hat, L_best), 3)
        r["vif_window"] = evaluate(test, inv_tau, 1.0 / vif(rho_hat, L_best))
        rows.append(r)
        print(f"rho={rho:.2f} rho_hat={rho_hat:.3f} | beta theory={b_theory:.3f} from_rho_hat={b_hat:.3f} "
              f"nll_fit={b_fit:.3f}")
        print(f"    L_eff={r['L_eff']} beta_vif={r['beta_vif']}")
        for k in ["naive", "theory", "label_free", "fitted", "vif_window", "whitened"]:
            m = r[k]
            print(f"    {k:<10} ECE={m['ECE']:.3f} acc={m['acc']:.3f} NLL={m['NLL']:.3f} "
                  f"mean_conf={m['mean_conf']:.3f} conf>0.9&wrong={m['confident_wrong']:.3f}")
        sys.stdout.flush()
    if args.out:
        json.dump(dict(config=dict(M=M, T=T, mu=mu, sigma=sigma, n_cal=n_cal, n_test=n_test, seed=args.seed),
                       rows=rows), open(args.out, "w"), indent=1)

if __name__ == "__main__":
    main()
