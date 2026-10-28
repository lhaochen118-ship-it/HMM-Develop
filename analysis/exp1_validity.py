"""E1 — Is the false-accept rate controlled under appearance shift, without labels?

Protocol (per dataset, several random map-hole draws):
  * remove ~30% of the map (random 50 m cells); queries whose nearest remaining map item is > OFF_D away are
    OFF-MAP (any accept is a false accept); queries within IN_D are IN-MAP (correct if top-1 within tolerance).
  * label-free p-value methods (EVS, no-spatial EVS, per-query Gaussian z-norm) accept iff p <= alpha.
  * score methods (margin, PA, L2, SU, true SUE, CRSG logistic) need a threshold: split-conformal on the OFF-MAP
    scores of a labelled CALIBRATION condition set (benign/day), then transferred to every condition.
Reported per condition: realised false-accept rate on off-map queries (target alpha) and TPR on correct in-map.
"""
import sys, json, argparse
import numpy as np
from scipy.stats import norm
sys.path.insert(0, __import__("os").path.dirname(__file__))
import vprlib as V


def make_holes(ep, cell=50.0, frac=0.3, seed=0, off_d=40.0, in_d=5.0):
    rng = np.random.default_rng(seed)
    cid, _ = V.map_cells(ep.m_pos, cell); nc = cid.max() + 1
    drop = rng.random(nc) < frac
    keep = ~drop[cid]
    eh = ep.subset_map(keep)
    d = V.nearest_map_dist(eh)
    return eh, d > off_d, d <= in_d


def pvalue_methods(ep, cfg):
    out = {}
    out["EVS"] = V.evs_test(ep, cell=cfg["cell"], excl=cfg["excl"], k=cfg["k"])
    # ablation: same spacing test but competitors = raw top-(k+1) scores (no map geometry) ~ meta-recognition
    S = ep.S; part = -np.sort(-S, 1)[:, :cfg["k"] + 2]
    D = part[:, 0] - part[:, 1]; j = np.arange(2, cfg["k"] + 2)[None, :]
    beta = (j * (part[:, 1:-1] - part[:, 2:])).mean(1); T = D / np.maximum(beta, 1e-9)
    out["EVS-nomap"] = (1 + T / cfg["k"]) ** (-cfg["k"])
    # per-query Gaussian null (z-norm) with Bonferroni over the map size
    mu, sd = S.mean(1), S.std(1) + 1e-9; z = (part[:, 0] - mu) / sd
    out["Znorm"] = np.clip(S.shape[1] * norm.sf(z), 0, 1)
    return out


def score_methods(ep):
    b = V.baseline_scores(ep)
    sc = {k: b[k] for k in ["margin", "PA", "neg_L2", "neg_SU", "maxsim"]}
    sc["SUE"] = V.sue_score(ep)
    return sc, b


def conformal_threshold(null_scores, alpha):
    """Smallest tau with P(score >= tau | null) <= alpha (split conformal, finite-sample valid if exchangeable)."""
    s = np.sort(np.asarray(null_scores))[::-1]; n = len(s)
    r = int(np.floor(alpha * (n + 1)))          # number of null calibration points allowed above tau
    return np.inf if r < 1 else s[r - 1] + 1e-12


DEFAULT_CFG = {"cell": 10.0, "excl": 25.0, "k": 10, "block": 300.0, "off_d": 40.0, "in_d": 5.0}
NORD_CFG = {"cell": 3.0, "excl": 5.0, "k": 10, "block": 200.0, "off_d": 10.0, "in_d": 0.5}


def all_methods(ep, cfg):
    """Every reliability signal for the queries of `ep` (dict name -> array; p-values marked by key prefix 'p:')."""
    out = {"p:" + k: v for k, v in pvalue_methods(ep, cfg).items()}
    sc, b = score_methods(ep)
    out.update({"s:" + k: v for k, v in sc.items()})
    out["f:margin"], out["f:neg_L2"], out["f:neg_entropy"] = b["margin"], b["neg_L2"], b["neg_entropy"]
    return out


def lobo_offmap(ep, cfg):
    """Leave-one-block-out: remove each spatial block of the map in turn; queries of that block that end up
    farther than off_d from the remaining map are OFF-MAP for that fold. Returns (signals, off_mask)."""
    bid, _ = V.map_cells(ep.m_pos, cfg["block"])
    nn = np.empty(len(ep.q_pos), int)
    for i in range(0, len(ep.q_pos), 1024):
        d = ((ep.q_pos[i:i + 1024, None, :] - ep.m_pos[None, :, :]) ** 2).sum(-1); nn[i:i + 1024] = d.argmin(1)
    qb = bid[nn]; sig = None; off = np.zeros(len(ep.q_pos), bool)
    for b in range(bid.max() + 1):
        qsel = np.where(qb == b)[0]
        if len(qsel) == 0: continue
        e2 = ep.subset_map(bid != b).subset_q(qsel)
        far = V.nearest_map_dist(e2) > cfg["off_d"]
        if not far.any(): continue
        e3 = e2.subset_q(np.where(far)[0]); m = all_methods(e3, cfg)
        if sig is None: sig = {k: np.full(len(ep.q_pos), np.nan) for k in m}
        for k, v in m.items(): sig[k][qsel[far]] = v
        off[qsel[far]] = True
    return sig, off


def run(ep, tol, calib_conds, alphas=(0.01, 0.05, 0.1), cfg=None):
    cfg = {**DEFAULT_CFG, **(cfg or {})}
    sig_off, off = lobo_offmap(ep, cfg)
    sig_in = all_methods(ep, cfg); inm = V.nearest_map_dist(ep) <= cfg["in_d"]
    corr = V.correct(ep, *tol) & inm
    cal = np.isin(ep.q_cond, calib_conds)
    # CRSG: logistic on [margin, -L2, -entropy]; positives = correct in-map, negatives = off-map (calib conds only)
    Xin = np.column_stack([sig_in["f:margin"], sig_in["f:neg_L2"], sig_in["f:neg_entropy"]])
    Xoff = np.column_stack([sig_off["f:margin"], sig_off["f:neg_L2"], sig_off["f:neg_entropy"]])
    tr_pos, tr_neg = cal & corr, cal & off
    f = V.logistic_model(np.vstack([Xin[tr_pos], Xoff[tr_neg]]), np.r_[np.ones(tr_pos.sum()), np.zeros(tr_neg.sum())])
    sig_in["s:CRSG"], sig_off["s:CRSG"] = f(Xin), np.where(off, f(np.nan_to_num(Xoff)), np.nan)
    rows = []
    names = [k for k in sig_in if k[:2] in ("p:", "s:")]
    for cond in sorted(set(ep.q_cond)):
        m = ep.q_cond == cond
        for a in alphas:
            for k in names:
                if k.startswith("p:"):
                    acc_off, acc_in = sig_off[k] <= a, sig_in[k] <= a; variants = [(k[2:], acc_off, acc_in)]
                else:
                    tau = conformal_threshold(sig_off[k][cal & off], a)
                    tau_o = conformal_threshold(sig_off[k][m & off], a)
                    variants = [(k[2:] + "+conf(day)", sig_off[k] >= tau, sig_in[k] >= tau),
                                (k[2:] + "+oracle", sig_off[k] >= tau_o, sig_in[k] >= tau_o)]
                for name, ao, ai in variants:
                    rows.append(dict(cond=str(cond), alpha=a, method=name, n_off=int((m & off).sum()), n_corr=int((m & corr).sum()),
                                     FAR=float(ao[m & off].mean()) if (m & off).any() else np.nan,
                                     TPR=float(ai[m & corr].mean()) if (m & corr).any() else np.nan,
                                     acc_wrong_inmap=float(ai[m & inm & ~corr].mean()) if (m & inm & ~corr).any() else np.nan))
    return rows, dict(sig_in=sig_in, sig_off=sig_off, off=off, inm=inm, corr=corr)


def summarise(rows, alpha=0.05, methods=None):
    import collections
    agg = collections.defaultdict(list)
    for r in rows:
        if r["alpha"] != alpha: continue
        agg[(r["method"], r["cond"])].append(r)
    meths = methods or sorted({k[0] for k in agg})
    conds = sorted({k[1] for k in agg})
    print(f"\nalpha={alpha}: realised FAR on OFF-MAP queries (target <= {alpha})  |  TPR on correct in-map")
    print(f"{'method':22s}" + "".join(f"{c[:10]:>11s}" for c in conds) + f"{'maxFAR':>9s}{'meanTPR':>9s}")
    r0 = agg[(meths[0], conds[0])][0]
    print(f"{'(n_off)':22s}" + "".join(f"{agg[(meths[0], c)][0]['n_off']:11d}" for c in conds))
    for mt in meths:
        far = [np.nanmean([r['FAR'] for r in agg[(mt, c)]]) for c in conds]
        noff = [agg[(mt, c)][0]['n_off'] for c in conds]
        tpr = [np.nanmean([r['TPR'] for r in agg[(mt, c)]]) for c in conds]
        print(f"{mt:22s}" + "".join(f"{x:11.3f}" for x in far) + f"{np.nanmax(far):9.3f}{np.nanmean(tpr):9.3f}")
