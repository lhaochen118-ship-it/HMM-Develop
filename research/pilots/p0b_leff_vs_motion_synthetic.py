#!/usr/bin/env python3
"""Pilot P0b (SYNTHETIC ONLY) — does the effective memory L_eff behave like a property of the FILTER?
Prediction (H6b mechanism): a wider motion kernel (more diffusion) and a larger leak make the filter forget
faster -> smaller L_eff -> NLL-optimal beta closer to 1 at the same rho. If L_eff did not move with the
motion kernel, the 'filter memory' interpretation would be wrong.
Reuses the P0 generator/filter; only the motion std and leak change. Usage: python p0b_leff_vs_motion_synthetic.py --out x.json"""
import json, argparse
import numpy as np
import p0_dependence_tempering_synthetic as p0

def run_filter_std(S, inv_tau, beta, std, leak):
    T, M = S.shape
    half = int(np.ceil(4 * std)) + 1
    offs = np.arange(1 - half, 1 + half + 1); w = np.exp(-0.5 * ((offs - 1) / std) ** 2); w /= w.sum()
    b = np.full(M, 1.0 / M); post = np.empty((T, M))
    for t in range(T):
        b = p0.motion(b, offs, w, leak)
        lb = np.log(b + 1e-300) + beta * S[t] * inv_tau
        lb -= p0.lse(lb); b = np.exp(lb); post[t] = b
    return post

def evaluate(eps, inv_tau, beta, std, leak, burn=10):
    nll = []
    for S, tr in eps:
        P = run_filter_std(S, inv_tau, beta, std, leak)[burn:]; tt = tr[burn:]
        nll.append(-np.log(P[np.arange(len(tt)), tt] + 1e-300))
    return float(np.concatenate(nll).mean())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out"); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(); rng = np.random.default_rng(a.seed)
    M, T, mu, sigma = 400, 60, 1.6, 1.0
    Ls = [1, 2, 3, 4, 6, 8, 12, 20, 40]
    rows = []
    for rho in [0.5, 0.7]:
        cal = [p0.episode(T, M, mu, sigma, rho, rng) for _ in range(25)]
        inv_tau = 1.0 / p0.fit_tau(cal)
        rho_hat = float(np.mean([p0.label_free_rho(S) for S, _ in cal]))
        for std, leak in [(0.5, 1e-3), (1.0, 1e-3), (2.0, 1e-3), (1.0, 3e-2)]:
            nlls = [evaluate(cal, inv_tau, 1.0 / p0.vif(rho_hat, L), std, leak) for L in Ls]
            k = int(np.argmin(nlls))
            r = dict(rho=rho, rho_hat=round(rho_hat, 3), motion_std=std, leak=leak, L_eff=Ls[k],
                     beta=round(1.0 / p0.vif(rho_hat, Ls[k]), 3), nll_best=round(nlls[k], 3),
                     nll_beta1=round(evaluate(cal, inv_tau, 1.0, std, leak), 3))
            rows.append(r); print(r, flush=True)
    if a.out: json.dump(dict(config=dict(M=M, T=T, mu=mu, sigma=sigma, seed=a.seed, Ls=Ls), rows=rows), open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
