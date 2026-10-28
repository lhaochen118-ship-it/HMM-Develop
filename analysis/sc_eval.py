"""Evaluate map-self-calibrated acceptance tests on one dataset. Usage: sc_eval.py <dump> <rc|cmu|nord> [desc]"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC

CFG = {"rc": dict(cell=10.0, excl=25.0, k=10, block=300.0, off_d=40.0, in_d=5.0, tol=(5.0, 10.0), calib=["overcast-summer", "overcast-winter"]),
       "cmu": dict(cell=10.0, excl=25.0, k=10, block=300.0, off_d=40.0, in_d=5.0, tol=(5.0, 10.0), calib=None),
       "msls": dict(cell=10.0, excl=25.0, k=10, block=300.0, off_d=40.0, in_d=10.0, tol=(25.0, None), calib=None),
       "nordw": dict(cell=3.0, excl=5.0, k=10, block=200.0, off_d=10.0, in_d=0.5, tol=(2.0, None), calib=["spring"]),
       "nord": dict(cell=3.0, excl=5.0, k=10, block=200.0, off_d=10.0, in_d=0.5, tol=(2.0, None), calib=["fall"])}
STATS = ["T_spacing", "T_level", "z_far", "z_all"]


def evaluate(ep, c, variant="centered", alphas=(0.01, 0.05, 0.1), verbose=True):
    q, m = SC.center(ep.q, ep.m) if variant == "centered" else (ep.q.astype(np.float32), ep.m.astype(np.float32))
    nul = SC.map_null(m, ep.m_pos, c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
    off = SC.lobo_stats(m, ep.m_pos, c["block"], c["off_d"], q, ep.q_pos, c["cell"], c["excl"], c["k"])
    full = SC.query_stats(q @ m.T, ep.m_pos, c["cell"], c["excl"], c["k"])
    e2 = V.Episode(ep.name, q, m, ep.q_pos, ep.m_pos, ep.q_cond, ep.q_R, ep.m_R)
    inm = V.nearest_map_dist(e2) <= c["in_d"]; corr = V.correct(e2, *c["tol"]) & inm
    offm = np.isfinite(off["z_all"]); conds = sorted(set(ep.q_cond))
    # label-calibrated baseline: raw max-similarity threshold fit on calibration conditions' off-map queries
    S_raw = ep.q.astype(np.float32) @ ep.m.astype(np.float32).T; ms_in = S_raw.max(1)
    off_raw = SC.lobo_stats(ep.m.astype(np.float32), ep.m_pos, c["block"], c["off_d"], ep.q.astype(np.float32), ep.q_pos, c["cell"], c["excl"], c["k"])
    calib = c["calib"] or sorted(conds, key=lambda x: -corr[ep.q_cond == x].mean())[:2]
    res = {"n_null": int(np.isfinite(nul["z_all"]).sum()), "n_off": int(offm.sum()), "n_corr": int(corr.sum()), "calib": calib, "rows": []}
    if verbose: print(f"[{ep.name} | {variant}] map-null n={res['n_null']} off-map n={res['n_off']} correct in-map n={res['n_corr']} | R@1(in-map)={corr[inm].mean():.3f}")
    # raw max-sim of off-map queries = s1 recovered from z-statistics is not stored; recompute via z_all: use T? -> store separately
    for st in STATS:
        po, pi = SC.conformal_p(nul[st], off[st]), SC.conformal_p(nul[st], full[st])
        au = V.auroc(np.r_[full[st][corr], off[st][offm]], np.r_[np.ones(corr.sum()), np.zeros(offm.sum())])
        for a in alphas:
            fc = {cc: float(np.mean(po[offm & (ep.q_cond == cc)] <= a)) for cc in conds if (offm & (ep.q_cond == cc)).sum() >= 20}
            res["rows"].append(dict(stat=st, alpha=a, FAR=float(np.mean(po[offm] <= a)), worstFAR=max(fc.values()), worst=max(fc, key=fc.get),
                                    TPR=float(np.mean(pi[corr] <= a)), AUROC=au, per_cond=fc))
    return res, dict(nul=nul, off=off, full=full, corr=corr, offm=offm, inm=inm)


def label_baseline(ep, c, sig, alphas=(0.01, 0.05, 0.1)):
    """Label-calibrated thresholds (split conformal on calibration conditions' OFF-MAP queries) on raw max-sim."""
    pass


if __name__ == "__main__":
    dump, ds = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
    ep = V.LOADERS[ds](dump, desc)
    out = {}
    for variant in ["raw", "centered"]:
        r, _ = evaluate(ep, CFG[ds], variant); out[variant] = r
        for row in r["rows"]:
            print(f"  {row['stat']:10s} a={row['alpha']:.2f} AUROC {row['AUROC']:.3f} FAR {row['FAR']:.3f} worst {row['worstFAR']:.3f} ({row['worst'][:10]}) TPR {row['TPR']:.3f}")
    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "results", f"sc_{ds}_{desc}.json"), "w"), default=float, indent=1)
