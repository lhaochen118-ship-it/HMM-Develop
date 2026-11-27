"""E21 — Cross-dataset transfer (H13): select (tau, kernel, beta) on SOURCE calibration, evaluate on TARGET test,
vs in-domain selection. Metric-unit datasets only (cmu <-> rc). Usage: e10_transfer <src> <tgt> <desc>"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run
from .. import baselines

SRC, TGT, DESC = sys.argv[1], sys.argv[2], sys.argv[3]; t00 = time.time()
Bs, Bt = Bench(SRC, DESC), Bench(TGT, DESC)
GRID = list(itertools.product(Bs.kernel_grid(), [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]))
def select(B):
    best = None
    for (m, s), b in GRID:
        v = B.nll("calib", B.run("calib", "tau", m, s, b))
        if best is None or v < best[0]: best = (v, m, s, b)
    return best
ss, st = select(Bs), select(Bt)
RES = {}
RES["single_tgt_tau"] = Bt.evaluate([baselines.single_image_post(ep.sim()[r], Bt.tau) for ep, r in Bt.split["test"]])[0]
RES["hmm_in_domain"] = Bt.evaluate(Bt.run("test", "tau", st[1], st[2], st[3]))[0]
tau_t = Bt.tau; Bt.tau = Bs.tau                               # transfer the emission temperature too
RES["single_src_tau"] = Bt.evaluate([baselines.single_image_post(ep.sim()[r], Bt.tau) for ep, r in Bt.split["test"]])[0]
RES["hmm_transfer"] = Bt.evaluate(Bt.run("test", "tau", ss[1], ss[2], ss[3]))[0]
Bt.tau = tau_t
for k, r in RES.items(): print(f"  {k:15s} R@1 {r['R@1']:.4f} NLL {r['NLL']:.4f} ECE {r['ECE']:.3f}", flush=True)
g_in = RES["hmm_in_domain"]["R@1"] - RES["single_tgt_tau"]["R@1"]; g_tr = RES["hmm_transfer"]["R@1"] - RES["single_tgt_tau"]["R@1"]
print(f"  gain retained {g_tr:.4f}/{g_in:.4f} = {g_tr / g_in if g_in else float('nan'):.2f}  (src sel {ss[1:]}, tgt sel {st[1:]}, tau src {Bs.tau:.4f} tgt {tau_t:.4f})")
rid = new_run_id(f"E21_{SRC}to{TGT}_{DESC}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RES, "src_sel": ss, "tgt_sel": st, "tau": [Bs.tau, tau_t]}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T6.6", "experiment_id": "E21", "hypothesis_ids": ["H13"], "dataset": f"{SRC}->{TGT}", "descriptor": DESC,
         "status": "ok", "evidence_level": "S", "metrics": {k: {m: v[m] for m in ("R@1", "NLL", "ECE")} for k, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
