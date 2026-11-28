"""E34 / I30 — Geometric verification as an HMM emission term (HMM stays the inference engine).
For frames with geometry (RobotCar: every query; CMU: every 3rd), the candidate set is top-5 of the single-image
posterior U top-5 of the HMM posterior (NetVLAD; kaggle/k09_geo/candidates_local.json). Kernel k09 gives, per
(query, candidate), LightGlue matches n_m and fundamental-matrix MAGSAC inliers n_i.
Geometric log-likelihood ratio (fitted on CALIBRATION candidates only):
    g(x) = logit P(correct | x) - logit P(correct),   x = [log1p n_i, log1p n_m, n_i/(n_m+1)]   (logistic regression)
    = log p(x | correct) / p(x | wrong) under the candidate population; nodes without a measurement get 0 (l(∅)=0).
HMM emission: L_t(j) = appearance(t, j) + (w/β) * g_t(j)  (β = the HMM's evidence tempering, so g enters UNtempered with
weight w; w = 1 = the calibrated LLR at face value).  w ∈ {0.25, ..., 16} (x2 grid) chosen on calibration NLL with the HMM
hyper-parameters fixed to the appearance-only dev selection (no test information).
Compared on TEST: single, single+geo (re-rank by the same g), HMM, HMM+geo; paired sequence-block bootstrap CIs.
Usage: python3 -m hmmloc.exp.e18_geofusion <rc|cmu> <geo_*.json files...>"""
import sys, os, re, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run
from .. import baselines, data, metrics

DS = sys.argv[1]; FILES = sys.argv[2:]; t00 = time.time()
GEO = {}
for f in FILES:
    for q, r, nm, ni in json.load(open(f)):
        GEO[(q, r)] = (nm, ni)
CAND = json.load(open(os.path.join(ROOT, "kaggle", "k09_geo", "candidates_local.json")))[DS]
B = Bench(DS, "netvlad")


def names(ep):
    if DS == "rc":
        z = np.load(f"{data.FB}/dive-vpr-nb15a-dump/dump/meta/rc.npz")
        rts = np.array([int(re.findall(r"(\d+)\.\w+$", n)[0]) for n in z["ref_names"]]); rn = [str(t) for t in np.sort(rts)]
        qts = np.array([int(re.findall(r"(\d+)\.\w+$", n)[0]) for n in z["q_names"]]); o = np.lexsort((qts, z["q_cond"]))
        return [str(t) for t in qts[o]], rn
    sl = int(ep.name.split("/")[1][1:]); z = np.load(f"{data.FB}/dive-vpr-nb15b-dump/dump/meta/cmu_s{sl}.npz")
    qts = np.array([int(re.findall(r"_(\d+)us", n)[0]) for n in z["q_names"]]); o = np.lexsort((qts, z["q_cond"]))
    return [os.path.splitext(str(n))[0] for n in z["q_names"][o]], [os.path.splitext(str(n))[0] for n in z["db_names"]]


def feats(nm, ni):
    return [np.log1p(ni), np.log1p(nm), ni / (nm + 1.0)]


# ---- collect (row, node, x, label) per split
ENT = {"calib": [], "test": []}; miss = 0; tot = 0
NM = {}
for sp in ("calib", "test"):
    for k, (ep, rows) in enumerate(B.split[sp]):
        if ep.name not in NM: NM[ep.name] = names(ep)
        qn, rn = NM[ep.name]
        for i, r in enumerate(rows):
            c = CAND.get(f"{ep.name}|{int(r)}")
            if not c: continue
            for j in c:
                tot += 1; g = GEO.get((qn[r], rn[j]))
                if g is None or g[0] < 0: miss += 1; continue
                ENT[sp].append((k, i, j, feats(*g), bool(ep.pos[r, j])))
print(f"[{DS}] geometry entries calib {len(ENT['calib'])} test {len(ENT['test'])} | missing {miss}/{tot}", flush=True)
from sklearn.linear_model import LogisticRegression
Xc = np.array([e[3] for e in ENT["calib"]]); yc = np.array([e[4] for e in ENT["calib"]])
lr = LogisticRegression(C=1.0, max_iter=1000).fit(Xc, yc)
prior = np.log(yc.mean() / (1 - yc.mean()))
print(f"  logistic coef {lr.coef_.round(3).tolist()} b {lr.intercept_.round(3).tolist()} | calib positive rate {yc.mean():.3f}", flush=True)


def gmat(sp):
    G = [np.zeros((len(rows), ep.M), np.float32) for ep, rows in B.split[sp]]; has = [np.zeros(len(rows), bool) for ep, rows in B.split[sp]]
    if not ENT[sp]: return G, has
    X = np.array([e[3] for e in ENT[sp]])
    if sp == "calib":   # cross-fitted (2 folds by sequence): w is chosen with OUT-OF-FOLD g, not with in-sample g
        fold = np.array([int(B.split["calib"][e[0]][0].seq[B.split["calib"][e[0]][1][e[1]]]) % 2 for e in ENT[sp]])
        z = np.zeros(len(X))
        for f_ in (0, 1):
            tr = fold != f_; m_ = LogisticRegression(C=1.0, max_iter=1000).fit(X[tr], yc[tr])
            pr = np.log(yc[tr].mean() / (1 - yc[tr].mean())); z[~tr] = m_.decision_function(X[~tr]) - pr
    else:               # test: g fitted on ALL calibration candidates
        z = lr.decision_function(X) - prior
    for (k, i, j, _, _), v in zip(ENT[sp], z):
        G[k][i, j] = v; has[k][i] = True
    return G, has


GM = {sp: gmat(sp) for sp in ("calib", "test")}
# ---- appearance-only dev selection (same as main pipeline: tau emission, kernel grid x beta by calib NLL)
best = None
for (m, s), b in itertools.product(B.kernel_grid(), [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]):
    v = B.nll("calib", B.run("calib", "tau", m, s, b))
    if best is None or v < best[0]: best = (v, m, s, b)
_emit = B.emit
W = {"w": 0.0, "sp": "calib"}


def emit_geo(ep, rows, kind):
    L, Ln = _emit(ep, rows, kind)
    k = [i for i, (e, r) in enumerate(B.split[W["sp"]]) if e is ep and len(r) == len(rows) and (r == rows).all()][0]
    return L + (W["w"] / best[3]) * GM[W["sp"]][0][k], Ln     # forward() tempers ALL evidence by beta: undo it for g


B.emit = emit_geo
selw = None
for w in (0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0):
    W.update(w=w, sp="calib"); v = B.nll("calib", B.run("calib", "tau", best[1], best[2], best[3]))
    print(f"  calib NLL w={w}: {v:.4f}", flush=True)
    if selw is None or v < selw[0]: selw = (v, w)
RES, PER = {}, {}
W.update(w=0.0, sp="test"); RES["hmm"], PER["hmm"] = B.evaluate(B.run("test", "tau", best[1], best[2], best[3]))
W.update(w=selw[1], sp="test"); RES["hmm+geo"], PER["hmm+geo"] = B.evaluate(B.run("test", "tau", best[1], best[2], best[3]))
sp_ = [baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split["test"]]
RES["single"], PER["single"] = B.evaluate(sp_)
spg = []
for p, G in zip(sp_, GM["test"][0]):
    lp = np.log(np.clip(p, 1e-30, None)) + selw[1] * G; lp -= lp.max(1, keepdims=True); q = np.exp(lp); spg.append(q / q.sum(1, keepdims=True))
RES["single+geo"], PER["single+geo"] = B.evaluate(spg)
# rows that carry geometry (subset analysis)
hasT = np.concatenate([h[ep.pos[r].any(1)] for h, (ep, r) in zip(GM["test"][1], B.split["test"])])
for k_ in RES:
    RES[k_]["R@1_geo_rows"] = float(PER[k_]["corr"][hasT].mean()) if hasT.any() else None
for a, b_ in (("hmm+geo", "hmm"), ("single+geo", "single"), ("hmm+geo", "single+geo")):
    blk = PER[a]["blocks"]
    lo, hi = metrics.paired_block_bootstrap([PER[a]["corr"][x] for x in blk], [PER[b_]["corr"][x] for x in blk])
    RES[f"diff_{a}_vs_{b_}"] = {"R@1": RES[a]["R@1"] - RES[b_]["R@1"], "CI": [lo, hi]}
for k_, r in RES.items():
    if "R@1" in r and "NLL" in r:
        print(f"  {k_:11s} R@1 {r['R@1']:.4f} (geo rows {r['R@1_geo_rows']}) NLL {r['NLL']:.4f} CW {r['CW@0.9']:.4f}", flush=True)
    else:
        print(f"  {k_}: {r}", flush=True)
RES["sel"] = {"hmm": best[1:], "w": selw[1], "coef": lr.coef_.tolist(), "intercept": lr.intercept_.tolist()}
if os.environ.get("HMMLOC_DRY"):
    print("DRY run: not logged"); sys.exit(0)
rid = new_run_id(f"E34_{DS}_geofusion")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump(RES, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T5.6", "experiment_id": "E34", "hypothesis_ids": ["H11"], "dataset": DS, "descriptor": "netvlad",
         "method": "I30 geometric LLR (LightGlue+MAGSAC inliers, logistic on calib) added to the HMM emission",
         "status": "ok", "evidence_level": "S", "metrics": {k_: ({m: v[m] for m in ("R@1", "NLL", "R@1_geo_rows")} if "NLL" in v else v) for k_, v in RES.items() if k_ != "sel"},
         "compute": {"platform": "kaggle-gpu(k09)+local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}",
         "inputs": [os.path.basename(f) for f in FILES]})
print("RUN", rid)
