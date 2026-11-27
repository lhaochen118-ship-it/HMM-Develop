"""E32 — Fixed-lag smoothing (H21): same HMM (tau emission, dev-selected kernel and beta), lag in {0,2,5,10} frames.
Usage: e06_lag <dataset> <desc>"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run
from .. import metrics

DS, DESC = sys.argv[1], sys.argv[2]; t00 = time.time(); B = Bench(DS, DESC)
best = None
for (m, s), b in itertools.product(B.kernel_grid(), [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]):
    v = B.nll("calib", B.run("calib", "tau", m, s, b))
    if best is None or v < best[0]: best = (v, m, s, b)
print(f"[{DS}/{DESC}] kernel/beta {best}", flush=True)
RES, PER = {}, {}
for lag in (0, 2, 5, 10):
    posts = B.run("test", "tau", best[1], best[2], best[3], lag=lag)
    RES[f"lag{lag}"], PER[f"lag{lag}"] = B.evaluate(posts)
ref = PER["lag0"]
for k, r in RES.items():
    r["dR1_vs_lag0_CI"] = metrics.paired_block_bootstrap([PER[k]["corr"][b] for b in ref["blocks"]], [ref["corr"][b] for b in ref["blocks"]], n=1000)
    print(f"  {k:6s} R@1 {r['R@1']:.4f} NLL {r['NLL']:.4f} ECE {r['ECE']:.3f} CW {r['CW@0.9']:.4f} dR1 CI {np.round(r['dR1_vs_lag0_CI'],4)}", flush=True)
rid = new_run_id(f"E32_{DS}_{DESC}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RES, "sel": best}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T5.x", "experiment_id": "E32", "hypothesis_ids": ["H21"], "dataset": DS, "descriptor": DESC,
         "status": "ok", "evidence_level": "S", "metrics": {k: {m: v[m] for m in ("R@1", "NLL", "ECE", "CW@0.9")} for k, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid, f"{time.time()-t00:.0f}s")
