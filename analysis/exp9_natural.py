"""E9 — natural off-map queries: every query of ANOTHER dataset / city is scored against a map (truly unmapped places,
no leave-block-out simulation). Deployable SelfCal-AA (selfcal.SelfCalAA, fitted on the map alone) vs a max-sim
threshold label-calibrated on the map dataset's own benign off-map queries (LOBO), at alpha in {0.01, 0.05, 0.1}.
Usage: exp9_natural.py <desc> <dump_rc_nord> <dump_cmu> [dump_msls]"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC
from sc_eval import CFG

desc, d_rn, d_cmu = sys.argv[1], sys.argv[2], sys.argv[3]; d_ms = sys.argv[4] if len(sys.argv) > 4 else None
ALPHAS, NQ = (0.01, 0.05, 0.1), 3000
SRC = {"rc": (lambda: V.load_robotcar(d_rn, desc), "rc"), "cmu": (lambda: V.load_cmu_merged(d_cmu, desc), "cmu"),
       "nord": (lambda: V.load_nordland(d_rn, desc), "nord")}
if d_ms:
    for c in ("cph", "sf"):
        if os.path.isfile(os.path.join(d_ms, "meta", f"msls_{c}.npz")):
            SRC[f"msls-{c}"] = ((lambda c=c: V.load_msls(d_ms, desc, (c,))), "msls")
EP = {k: f() for k, (f, _) in SRC.items()}
rng = np.random.default_rng(0)
QS = {k: e.q[np.sort(rng.choice(len(e.q), min(NQ, len(e.q)), replace=False))].astype(np.float32) for k, e in EP.items()}


def pvals(sc, q, chunk=1000):
    return np.concatenate([sc.pvalue(q[i:i + chunk])[0] for i in range(0, len(q), chunk)])


res = {}
for mk, ep in EP.items():
    c = CFG[SRC[mk][1]]
    sc = SC.SelfCalAA(ep.m, ep.m_pos, c["cell"], c["excl"], c["k"], c["block"], c["off_d"])
    p_own = pvals(sc, ep.q)
    inm = V.nearest_map_dist(ep) <= c["in_d"]; corr = V.correct(ep, *c["tol"]) & inm
    # label-calibrated baseline: split-conformal max-sim threshold on the map dataset's own off-map (LOBO) queries
    # from its two most benign conditions (as LabelCal "benign->all" in eval_all)
    off = SC.lobo_stats(ep.m.astype(np.float32), ep.m_pos, c["block"], c["off_d"], ep.q.astype(np.float32), ep.q_pos, c["cell"], c["excl"], c["k"])["maxsim"]
    conds = sorted(set(ep.q_cond)); calib = c["calib"] or sorted(conds, key=lambda x: -corr[ep.q_cond == x].mean())[:2]
    cal = np.sort(off[np.isfinite(off) & np.isin(ep.q_cond, calib)]); n = len(cal)
    thr = {a: cal[min(n - 1, int(np.ceil((n + 1) * (1 - a))) - 1)] for a in ALPHAS}
    ms_own = (ep.q.astype(np.float32) @ ep.m.astype(np.float32).T).max(1)
    r = {"n_map": int(len(ep.m)), "n_null": int(sc.test.n), "own": {}}
    for a in ALPHAS:
        r["own"][str(a)] = dict(TPR_selfcal=float(np.mean(p_own[corr] <= a)), TPR_thr=float(np.mean(ms_own[corr] > thr[a])))
    for sk, q in QS.items():
        if sk == mk: continue
        p = pvals(sc, q); ms = (q @ ep.m.astype(np.float32).T).max(1)
        r[sk] = {str(a): dict(FAR_selfcal=float(np.mean(p <= a)), FAR_thr=float(np.mean(ms > thr[a])), n=int(len(q))) for a in ALPHAS}
    res[mk] = r
    line = " | ".join(f"{sk}: {r[sk]['0.05']['FAR_selfcal']:.3f}/{r[sk]['0.05']['FAR_thr']:.3f}" for sk in QS if sk != mk)
    print(f"{desc} map={mk:8s} TPR@.05 selfcal {r['own']['0.05']['TPR_selfcal']:.3f} thr {r['own']['0.05']['TPR_thr']:.3f} || natural off-map FAR@.05 (SelfCal-AA/thr): {line}", flush=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
json.dump(res, open(os.path.join(os.path.dirname(__file__), "results", f"natural_{desc}.json"), "w"), indent=1)
