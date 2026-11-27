"""E30-lite — Posterior-weighted pose (M5-lite, no local features): position = posterior-weighted mean of reference
centres within the tolerance neighbourhood of the MAP node; orientation = MAP node's. Same procedure for the
single-image softmax posterior and the HMM posterior. Thresholds (0.25m,2°)/(0.5m,5°)/(5m,10°) + median error.
Usage: e12_pose <rc|cmu> <desc>"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run
from .. import baselines, data

DS, DESC = sys.argv[1], sys.argv[2]; t00 = time.time(); B = Bench(DS, DESC)
best = None
for (m, s), b in itertools.product(B.kernel_grid(), [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]):
    v = B.nll("calib", B.run("calib", "tau", m, s, b))
    if best is None or v < best[0]: best = (v, m, s, b)
hp = B.run("test", "tau", best[1], best[2], best[3])
sp = [baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split["test"]]
THR = [(0.25, 2.0), (0.5, 5.0), (5.0, 10.0)]
res = {}
for name, posts in (("single", sp), ("hmm", hp)):
    for mode in ("top1", "interp"):
        dts, das = [], []
        for (ep, r), p in zip(B.split["test"], posts):
            pr = p.argmax(1)
            if mode == "top1": C = ep.C[pr]
            else:
                C = np.empty((len(r), 3))
                for t in range(len(r)):
                    nb = np.where(ep.near[pr[t]])[0]; w = p[t, nb].astype(np.float64); w /= w.sum()
                    C[t] = w @ ep.C[nb]
            dts.append(np.linalg.norm(ep.qC[r] - C, axis=1)); das.append(data._rot_deg(ep.qR[r], ep.Rrot[pr]))
        dt, da = np.concatenate(dts), np.concatenate(das)
        res[f"{name}_{mode}"] = {"acc": [float(np.mean((dt <= a) & (da <= b))) for a, b in THR], "median_m": float(np.median(dt))}
        print(f"  {name}_{mode:6s} (.25m,2)/(.5m,5)/(5m,10) = {'/'.join(f'{x:.3f}' for x in res[f'{name}_{mode}']['acc'])} median {np.median(dt):.2f} m", flush=True)
rid = new_run_id(f"E30_{DS}_{DESC}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump(res, open(os.path.join(od, "metrics.json"), "w"), indent=1)
log_run({"run_id": rid, "task_id": "T5.5", "experiment_id": "E30", "hypothesis_ids": ["H11"], "dataset": DS, "descriptor": DESC,
         "status": "ok", "evidence_level": "S", "metrics": res, "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60},
         "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
