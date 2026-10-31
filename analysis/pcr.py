"""Predictive cell-rank (PCR) e-values for the CPC-HMM presence chain, from nav_demo --cache --pred files.

Root cause addressed (hmm_diag / RESEARCH_LOG Entry 25): the presence chain only sees the top-1 SelfCal p-value, a MAX
over all N map places, so it pays an N-fold multiplicity. With weak descriptors the place chain tracks the robot (its MAP
is correct on 70-86 % of on-map frames) and the top-1 often sits at the tracked place, yet the top-1 similarity is not
extreme against null maxima: the presence chain never switches on and whole traversals go unreported.
PCR tests ONE location fixed before frame t is seen: the place chain's predicted place j_t (F_{t-1}-measurable).
  statistic   r_t = (1 + #other cells whose max similarity >= best similarity within excl of j_t) / (1 + #other cells)
  null        the same place chain run on the map's own held-out traversal (block masked, exact map odometry)
  p-values    u_t = conformal rank of r_t among null values (marginal), and TCE: Mondrian cell = bin of r_{t-1}
              (null transition pairs inside null chunks), as nav_demo.tce
  e-values    b u^(b-1), b = Beta-EM per query condition; TCEmin = min(marginal, TCE) (valid if EITHER holds)
Frames without a prediction (first frame of a run) get e = 1."""
import numpy as np
from hmm_fix import beta_em


def _conf_p(null_sorted, x):
    return (1 + np.searchsorted(null_sorted, x, side="right")) / (1 + len(null_sorted))


def pcr_pvalues(z, seqs, nb=6, min_n=30):
    """marginal and transition-calibrated conformal p-values of the query PCR statistic (small = evidence for on-map)"""
    pq, pn = z["pcr_q"].astype(float), z["pcr_n"].astype(float)
    fl, ln = z["nchunk_flat"], z["nchunk_len"]; bounds = np.r_[0, np.cumsum(ln)]
    nul = pn[np.isfinite(pn)]; ns = np.sort(nul)
    u_m = np.where(np.isfinite(pq), _conf_p(ns, np.nan_to_num(pq, nan=1.0)), 1.0)
    lp = lambda x: np.log(np.clip(x, 1e-9, 1))
    edges = np.quantile(lp(nul), np.linspace(0, 1, nb + 1)[1:-1]) if len(nul) else np.zeros(0)
    cell = lambda x: -1 if not np.isfinite(x) else int(np.searchsorted(edges, lp(x)))
    pool = {}
    for a, b in zip(bounds[:-1], bounds[1:]):
        v = pn[a:b]
        for i in range(len(v)):
            if not np.isfinite(v[i]): continue
            key = cell(v[i - 1]) if i > 0 else -1
            pool.setdefault(key, []).append(v[i]); pool.setdefault("all", []).append(v[i])
    pool = {k: np.sort(x) for k, x in pool.items()}
    u_t = np.ones(len(pq))
    for idx in seqs:
        for i, t in enumerate(idx):
            if not np.isfinite(pq[t]): continue
            key = cell(pq[idx[i - 1]]) if i > 0 else -1
            ref = pool[key] if key in pool and len(pool[key]) >= min_n else pool.get("all", ns)
            u_t[t] = _conf_p(ref, pq[t])
    return u_m, u_t


def pcr_evalues(z, seqs):
    """(e_marginal, e_TCE, e_TCEmin) per frame; 1 where there is no prediction"""
    u_m, u_t = pcr_pvalues(z, seqs); has = np.isfinite(z["pcr_q"]); cond = z["cond"]
    em, et = np.ones(len(u_m)), np.ones(len(u_m))
    for cn in sorted(set(cond)):
        m = (cond == cn) & has
        if not m.any(): continue
        b1, _ = beta_em(u_m[m]); b2, _ = beta_em(u_t[m])
        em[m] = b1 * np.clip(u_m[m], 1e-6, 1) ** (b1 - 1); et[m] = b2 * np.clip(u_t[m], 1e-6, 1) ** (b2 - 1)
    return em, et, np.minimum(em, et)
