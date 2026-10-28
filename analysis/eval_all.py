"""Unified comparison: label-free self-calibrated tests vs label-calibrated / oracle / theory-only baselines.
Usage: eval_all.py <dump> <rc|cmu|nord> [desc]   -> prints a table, writes results/eval_<ds>_<desc>.json"""
import sys, os, json
import numpy as np
from scipy.stats import norm, binom
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC
from sc_eval import CFG

ALPHAS = (0.01, 0.05, 0.1)


def signals(ep, c, centered):
    q, m = SC.center(ep.q, ep.m) if centered else (ep.q.astype(np.float32), ep.m.astype(np.float32))
    args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
    nul = SC.map_null(m, ep.m_pos, *args)
    off = SC.lobo_stats(m, ep.m_pos, c["block"], c["off_d"], q, ep.q_pos, c["cell"], c["excl"], c["k"])
    full = SC.query_stats(q @ m.T, ep.m_pos, c["cell"], c["excl"], c["k"])
    return nul, off, full, m.shape[0]


def violations(acc_off, cond, offm, a):
    """#conditions whose FAR is significantly above alpha (one-sided binomial, Bonferroni over conditions)."""
    cs = [c for c in sorted(set(cond)) if (offm & (cond == c)).sum() >= 20]; nv = 0; fars = {}
    for c in cs:
        m = offm & (cond == c); k, n = int(acc_off[m].sum()), int(m.sum()); fars[c] = k / n
        if binom.sf(k - 1, n, a) < 0.05 / len(cs): nv += 1
    return nv, fars


def evaluate(ep, c, desc):
    raw = signals(ep, c, False); cen = signals(ep, c, True)
    e_raw = V.Episode(ep.name, ep.q, ep.m, ep.q_pos, ep.m_pos, ep.q_cond, ep.q_R, ep.m_R)
    inm = V.nearest_map_dist(e_raw) <= c["in_d"]; corr = V.correct(e_raw, *c["tol"]) & inm
    offm = np.isfinite(raw[1]["maxsim"]) & np.isfinite(cen[1]["z_far"]); cond = ep.q_cond
    conds = sorted(set(cond)); calib = c["calib"] or sorted(conds, key=lambda x: -corr[cond == x].mean())[:2]
    cal = np.isin(cond, calib)
    methods = {}   # name -> (accept_off(alpha), accept_in(alpha)) as callables
    def conformal(nullv, off_v, in_v):
        return lambda a: (SC.conformal_p(nullv, off_v) <= a, SC.conformal_p(nullv, in_v) <= a)
    # --- ours: map self-calibrated, affine-invariant statistics (no labels)
    for st in ["z_far", "z_all", "T_spacing"]:
        for tag, (nul, off, full, _) in [("", raw), ("+center", cen)]:
            methods[f"SelfCal[{st}{tag}]"] = conformal(nul[st], off[st], full[st])
    # --- ablation: self-calibration of a NON-invariant score
    methods["SelfCal[maxsim] (non-invariant)"] = conformal(raw[0]["maxsim"], raw[1]["maxsim"], raw[2]["maxsim"])
    # --- theory-only p-values (no calibration at all)
    k = c["k"]
    methods["Theory F-test[T_spacing]"] = lambda a: ((1 + raw[1]["T_spacing"] / k) ** (-k) <= a, (1 + raw[2]["T_spacing"] / k) ** (-k) <= a)
    methods["Theory Gauss[z_all]"] = lambda a: (np.clip(raw[3] * norm.sf(raw[1]["z_all"]), 0, 1) <= a, np.clip(raw[3] * norm.sf(raw[2]["z_all"]), 0, 1) <= a)
    # --- label-calibrated on calibration conditions (split conformal on their OFF-MAP queries), transferred
    for st in ["maxsim", "margin", "PA", "z_far"]:
        methods[f"LabelCal[{st}] (day->all)"] = conformal(raw[1][st][cal & offm], raw[1][st], raw[2][st])
    # CRSG: logistic on [margin, maxsim, neg_entropy]; positives correct in-map, negatives off-map, calib conds only
    F = lambda d: np.column_stack([d["margin"], d["maxsim"], d["neg_entropy"]])
    tr_p, tr_n = cal & corr, cal & offm
    f = V.logistic_model(np.vstack([F(raw[2])[tr_p], F(raw[1])[tr_n]]), np.r_[np.ones(tr_p.sum()), np.zeros(tr_n.sum())])
    crsg_off, crsg_in = f(np.nan_to_num(F(raw[1]))), f(F(raw[2]))
    methods["LabelCal[CRSG] (day->all)"] = conformal(crsg_off[cal & offm], crsg_off, crsg_in)
    rows = []
    for name, fn in methods.items():
        for a in ALPHAS:
            ao, ai = fn(a)
            nv, fars = violations(ao, cond, offm, a)
            rows.append(dict(method=name, alpha=a, FAR=float(ao[offm].mean()), worstFAR=max(fars.values()), n_viol=nv, n_cond=len(fars),
                             TPR=float(ai[corr].mean()), per_cond=fars))
    # oracle: per-condition label-calibrated max-sim (needs labels of every deployment condition) = power ceiling
    for a in ALPHAS:
        tp = []; fars = {}
        for cc in conds:
            mc = cond == cc
            if (mc & offm).sum() < 20: continue
            ao, ai = conformal(raw[1]["maxsim"][mc & offm], raw[1]["maxsim"], raw[2]["maxsim"])(a)
            fars[cc] = float(ao[mc & offm].mean()); tp.append(ai[mc & corr])
        rows.append(dict(method="Oracle[maxsim] (labels per cond.)", alpha=a, FAR=float(np.mean(list(fars.values()))), worstFAR=max(fars.values()),
                         n_viol=0, n_cond=len(fars), TPR=float(np.concatenate(tp).mean()), per_cond=fars))
    return rows, dict(n_off=int(offm.sum()), n_corr=int(corr.sum()), n_null=int(np.isfinite(cen[0]["z_far"]).sum()), calib=list(calib))


if __name__ == "__main__":
    dump, ds = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
    ep = {"rc": V.load_robotcar, "cmu": V.load_cmu_merged, "nord": V.load_nordland}[ds](dump, desc)
    rows, meta = evaluate(ep, CFG[ds], desc)
    print(f"\n### {ds} / {desc}: off-map n={meta['n_off']}, correct in-map n={meta['n_corr']}, map-null n={meta['n_null']}, label-cal conds={meta['calib']}")
    for a in ALPHAS:
        print(f"\nalpha={a}:  {'method':38s} {'FAR':>6s} {'worst':>6s} {'#viol':>6s} {'TPR':>6s}")
        for r in [r for r in rows if r["alpha"] == a]:
            print(f"            {r['method']:38s} {r['FAR']:6.3f} {r['worstFAR']:6.3f} {r['n_viol']:3d}/{r['n_cond']:<2d} {r['TPR']:6.3f}")
    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
    json.dump({"rows": rows, "meta": meta}, open(os.path.join(os.path.dirname(__file__), "results", f"eval_{ds}_{desc}.json"), "w"), default=float, indent=1)
