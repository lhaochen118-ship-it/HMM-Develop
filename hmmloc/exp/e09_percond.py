"""Per-condition breakdown (RobotCar conditions, Nordland seasons, CMU dates) for single vs dev-tuned HMM.
Also reports the coarse 6DoF thresholds (0.25m,2°)/(0.5m,5°)/(5m,10°) of the top-1 reference pose (rc/cmu).
Usage: e09_percond <dataset> <desc>"""
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
acc = {}
for (ep, r), ph, ps in zip(B.split["test"], hp, sp):
    P = ep.pos[r]; has = P.any(1); cond = ep.cond[r]
    for name, post in (("single", ps), ("hmm", ph)):
        pr = post.argmax(1); ok = P[np.arange(len(r)), pr]
        for c in np.unique(cond):
            sel = (cond == c) & has
            d = acc.setdefault(c, {}).setdefault(name, {"n": 0, "R@1": 0.0, "pose": [0, 0, 0]})
            d["n"] += int(sel.sum()); d["R@1"] += float(ok[sel].sum())
            if ep.qC is not None:
                dt = np.linalg.norm(ep.qC[r] - ep.C[pr], axis=1)
                da = data._rot_deg(ep.qR[r], ep.Rrot[pr])
                for i, (t, a) in enumerate(THR): d["pose"][i] += int(((dt <= t) & (da <= a))[sel].sum())
out = {}
for c, dd in sorted(acc.items()):
    out[c] = {k: {"n": v["n"], "R@1": v["R@1"] / max(v["n"], 1), "pose": [x / max(v["n"], 1) for x in v["pose"]]} for k, v in dd.items()}
    s_, h_ = out[c]["single"], out[c]["hmm"]
    print(f"  {c:16s} n={s_['n']:5d} R@1 single {s_['R@1']:.3f} -> HMM {h_['R@1']:.3f} | pose(.25/.5/5) single "
          f"{'/'.join(f'{x:.3f}' for x in s_['pose'])} -> HMM {'/'.join(f'{x:.3f}' for x in h_['pose'])}", flush=True)
rid = new_run_id(f"PC_{DS}_{DESC}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"per_condition": out, "sel": best}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T6.5", "experiment_id": "PC", "hypothesis_ids": ["H1", "H23"], "dataset": DS, "descriptor": DESC,
         "status": "ok", "evidence_level": "S", "metrics": out, "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60},
         "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
