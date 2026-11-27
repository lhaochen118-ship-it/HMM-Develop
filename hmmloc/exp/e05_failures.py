"""T4.1 — Failure taxonomy of the dev-selected HMM (tau-beta) vs single image, per dataset/descriptor.
Categories for HMM-wrong frames (multi-label resolved by priority): cold_start (first 5 frames of a sequence),
outage (true place not in single-image top-10), near_miss (prediction within 3x tolerance of truth: motion lag),
lock_in (wrong and the previous 5 frames also wrong), other.  Also counts HMM-induced errors (single right,
HMM wrong) vs HMM-fixed errors.  Usage: e05_failures <dataset> <desc>"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run
from .. import baselines

DS, DESC = sys.argv[1], sys.argv[2]; t00 = time.time(); B = Bench(DS, DESC)
best = None
for (m, s), b in itertools.product(B.kernel_grid(), [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]):
    v = B.nll("calib", B.run("calib", "tau", m, s, b))
    if best is None or v < best[0]: best = (v, m, s, b)
posts = B.run("test", "tau", best[1], best[2], best[3])
cnt = {"frames": 0, "hmm_wrong": 0, "single_wrong": 0, "hmm_induced": 0, "hmm_fixed": 0,
       "cold_start": 0, "outage": 0, "near_miss": 0, "lock_in": 0, "other": 0}
for (ep, rows), p in zip(B.split["test"], posts):
    S = ep.sim()[rows]; P = ep.pos[rows]; has = P.any(1); seq = ep.seq[rows]
    pred = p.argmax(1); sp = S.argmax(1)
    ok = P[np.arange(len(rows)), pred]; sok = P[np.arange(len(rows)), sp]
    rank_true = np.array([(S[t] > S[t][P[t]].max()).sum() if has[t] else 10 ** 9 for t in range(len(rows))])
    first = np.zeros(len(rows), int)
    for t in range(1, len(rows)): first[t] = 0 if seq[t] != seq[t - 1] else first[t - 1] + 1
    near3 = np.zeros(len(rows), bool)
    for t in range(len(rows)):
        if has[t]:
            tj = np.where(P[t])[0]; near3[t] = np.abs(ep.s[pred[t]] - ep.s[tj]).min() <= 3 * (1 if ep.unit == "frame" else 5.0)
    for t in np.where(has)[0]:
        cnt["frames"] += 1; cnt["hmm_wrong"] += int(~ok[t]); cnt["single_wrong"] += int(~sok[t])
        cnt["hmm_induced"] += int(sok[t] and not ok[t]); cnt["hmm_fixed"] += int(ok[t] and not sok[t])
        if ok[t]: continue
        if first[t] < 5: cnt["cold_start"] += 1
        elif rank_true[t] >= 10: cnt["outage"] += 1
        elif near3[t]: cnt["near_miss"] += 1
        elif t >= 5 and (~ok[t - 5:t]).all() and first[t] >= 5: cnt["lock_in"] += 1
        else: cnt["other"] += 1
print(f"[{DS}/{DESC}] sel {best[1:]} | " + " ".join(f"{k}={v}" for k, v in cnt.items()), flush=True)
rid = new_run_id(f"T41_{DS}_{DESC}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"counts": cnt, "sel": best}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T4.1", "experiment_id": "T4.1", "hypothesis_ids": ["H4"], "dataset": DS, "descriptor": DESC,
         "status": "ok", "evidence_level": "S", "metrics": cnt, "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60},
         "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
