"""E12/E13 — Open-world: map holes (queries traverse unmapped route segments) on Nordland (H7, H19, M1, M6).
Off-map detectors: single-image SUE (L2 to nearest ref), single-frame Bayes null with LLR, legacy HMM null
(quantile 0.98 / tau, A08), IA/HMM with calibrated-LLR null (l(null)=0).  Usage: e04_offmap <desc> [seed]"""
import sys, os, json, time, itertools
import numpy as np
from .. import data, hmm, emission, metrics, baselines
from .common import ROOT, new_run_id, log_run

DESC = sys.argv[1]; SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 0
t00 = time.time(); rng = np.random.default_rng(SEED)
ep = data.load_nordland(DESC); M = ep.M
# holes: 8 segments of 120 sampled frames (~21% of route), never at block boundaries
hole = np.zeros(M, bool); starts = rng.choice(np.arange(200, M - 300, 500), size=8, replace=False)
for s0 in starts: hole[s0 + rng.integers(0, 150): s0 + rng.integers(0, 150) + 120] = True
keep = ~hole; kidx = np.where(keep)[0]
R = ep.R[keep]; s = ep.s[keep]; S_full = ep.sim()[:, keep]; pos = ep.pos[:, keep]; near = ep.near[np.ix_(keep, keep)]
qidx = np.tile(np.arange(M), 3); offmap = hole[qidx]                      # query frames whose place is unmapped
seq = ep.seq; rm = np.zeros(ep.T, bool); rm[0] = True; rm[1:] = seq[1:] != seq[:-1]
cal = np.array([q in ep.calib_seq for q in seq]); tst = ~cal
print(f"[{DESC}] map {M}->{keep.sum()} | off-map query frac {offmap.mean():.3f}", flush=True)

def rows_of(mask): return np.where(mask)[0]
calr, tstr = rows_of(cal), rows_of(tst)
tau, _ = emission.fit_temperature_multi([(S_full[calr], pos[calr])])
llr = emission.fit_llr_multi([(S_full[calr], pos[calr])], kind="raw+z")
A = hmm.chain_kernel(s, mean=1.0, std=0.5)

def run(rows, kind, beta, exit_p, nstay):
    S = S_full[rows]; r = rm[rows].copy(); r[0] = True
    if kind == "llr": L, Ln = llr.loglik(S), np.zeros(len(rows))
    else: L, Ln = S / tau, np.quantile(S, 0.98, axis=1) / tau
    cfg = hmm.HMMConfig([A], exit_prob=exit_p, null_stay=nstay, null_prior=0.05, leak=1e-3, use_null=True)
    o = hmm.forward(L, cfg, beta=beta, loglik_null=Ln, reset_mask=r)
    return o["post"], o["null"]

def score(rows, post, null):
    y = offmap[rows].astype(int)
    inm = ~offmap[rows] & pos[rows].any(1)
    pred = post[inm].argmax(1); corr = pos[rows][inm][np.arange(inm.sum()), pred]
    # event NLL over ALL frames: on-map frames -> mass on positives; off-map frames -> null mass
    p_evt = np.where(offmap[rows], null, (post * pos[rows]).sum(1))
    nll = -np.log(np.clip(p_evt, 1e-6, 1)).mean()
    sc = null
    au = metrics.auroc(sc, y)
    thr = np.percentile(sc[y == 1], 5); fpr95 = float(np.mean(sc[y == 0] >= thr))
    return {"AUROC_off": au, "FPR@95TPR": fpr95, "R@1_inmap": float(corr.mean()), "NLL_all": float(nll)}

RES = {}
# single-image detectors
S = S_full[tstr]
RES["single_SUE"] = {"AUROC_off": metrics.auroc(np.sqrt(np.maximum(2 - 2 * S.max(1), 0)), offmap[tstr].astype(int))}
Lt = llr.loglik(S); pi0 = 0.2
pn = pi0 / (pi0 + (1 - pi0) * np.exp(Lt - Lt.max(1, keepdims=True)).mean(1) * np.exp(Lt.max(1)))
RES["single_LLR_null"] = {"AUROC_off": metrics.auroc(pn, offmap[tstr].astype(int))}
# HMM variants: (beta, exit, null_stay) selected on calibration by all-frame event NLL
for kind in ("tau_legacyQ", "llr"):
    k = "llr" if kind == "llr" else "tau"
    best = None
    for b, e, ns in itertools.product([0.2, 0.35, 0.5, 1.0] if k == "tau" else [0.5, 1.0, 2.0, 3.0], [0.005, 0.02, 0.05], [0.9, 0.97]):
        p, n = run(calr, k, b, e, ns); v = score(calr, p, n)["NLL_all"]
        if best is None or v < best[0]: best = (v, b, e, ns)
    p, n = run(tstr, k, best[1], best[2], best[3]); RES[f"hmm_{kind}"] = score(tstr, p, n); RES[f"hmm_{kind}"]["sel"] = best[1:]
for k, v in RES.items(): print(f"  {k:16s} " + " ".join(f"{a} {b:.4f}" if isinstance(b, float) else f"{a} {b}" for a, b in v.items()), flush=True)
rid = new_run_id(f"E12_nord_{DESC}_holes{SEED}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump(RES, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T3.6", "experiment_id": "E12", "hypothesis_ids": ["H7", "H19"], "dataset": "nord-holes",
         "descriptor": DESC, "seed": SEED, "status": "ok", "evidence_level": "S", "metrics": RES,
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid, f"{time.time()-t00:.0f}s")
