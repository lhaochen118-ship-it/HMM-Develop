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


def run(ep, tol, calib_conds, alphas=(0.01, 0.05, 0.1), seeds=(0, 1, 2, 3, 4), cfg=None, extra_off=None):
    cfg = cfg or {"cell": 10.0, "excl": 25.0, "k": 10}
    rows = []
    for seed in seeds:
        eh, off, inm = make_holes(ep, seed=seed)
        if extra_off is not None: off = off | extra_off
        corr = V.correct(eh, *tol) & inm
        pv = pvalue_methods(eh, cfg); sc, b = score_methods(eh)
        cal = np.isin(eh.q_cond, calib_conds)
        # CRSG: logistic on [margin, -L2, -entropy] fit on calibration condition, target = correct in-map vs rest
        X = np.column_stack([b["margin"], b["neg_L2"], b["neg_entropy"]]); lab = cal & (inm | off)
        f = V.logistic_model(X[lab], corr[lab].astype(float)); sc["CRSG"] = f(X)
        for cond in sorted(set(eh.q_cond)):
            m = eh.q_cond == cond
            for a in alphas:
                for name, p in pv.items():
                    acc = p <= a
                    rows.append(dict(seed=seed, cond=str(cond), alpha=a, method=name, n_off=int((m & off).sum()),
                                     FAR=float(acc[m & off].mean()) if (m & off).any() else np.nan,
                                     TPR=float(acc[m & corr].mean()) if (m & corr).any() else np.nan,
                                     acc_wrong_inmap=float(acc[m & inm & ~corr].mean()) if (m & inm & ~corr).any() else np.nan))
                for name, s in sc.items():
                    tau = conformal_threshold(s[cal & off], a); acc = s >= tau
                    rows.append(dict(seed=seed, cond=str(cond), alpha=a, method=name + "+conf(day)", n_off=int((m & off).sum()),
                                     FAR=float(acc[m & off].mean()) if (m & off).any() else np.nan,
                                     TPR=float(acc[m & corr].mean()) if (m & corr).any() else np.nan,
                                     acc_wrong_inmap=float(acc[m & inm & ~corr].mean()) if (m & inm & ~corr).any() else np.nan))
                    # oracle: per-condition conformal threshold (needs labels of THIS condition) - power upper bound
                    tau_o = conformal_threshold(s[m & off], a); acc_o = s >= tau_o
                    rows.append(dict(seed=seed, cond=str(cond), alpha=a, method=name + "+oracle", n_off=int((m & off).sum()),
                                     FAR=float(acc_o[m & off].mean()) if (m & off).any() else np.nan,
                                     TPR=float(acc_o[m & corr].mean()) if (m & corr).any() else np.nan, acc_wrong_inmap=np.nan))
    return rows


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
    for mt in meths:
        far = [np.nanmean([r['FAR'] for r in agg[(mt, c)]]) for c in conds]
        tpr = [np.nanmean([r['TPR'] for r in agg[(mt, c)]]) for c in conds]
        print(f"{mt:22s}" + "".join(f"{x:11.3f}" for x in far) + f"{np.nanmax(far):9.3f}{np.nanmean(tpr):9.3f}")
