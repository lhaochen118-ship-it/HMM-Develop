"""E18c / task 8 — Velocity-state models for the HMM: adjacent-sticky (LV, current), IMM mixing to the calibration speed
distribution (nests the fixed mixture kernel at stay=0), stop-aware semi-Markov approximation; each with the change
emission (ME). Selection on calibration NLL. Usage: e15_vmodels <dataset> <desc> [seed]"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench, load
from .common import ROOT, new_run_id, log_run
from .. import data, metrics

DS, DESC = sys.argv[1], sys.argv[2]; SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 0; t00 = time.time()
eps = [data.timewarp(e, seed=SEED) for e in load(DS[:-3], DESC)] if DS.endswith("-tw") else load(DS, DESC)
B = Bench(DS, DESC, eps=eps)
sp = np.concatenate([data.true_speed(ep)[r] for ep, r in B.split["calib"]]); sp = sp[np.isfinite(sp)]
V = sorted(set([0.0] + [round(float(q), 2) for q in np.percentile(sp, [10, 30, 50, 70, 90, 99])])); P0 = B.speed_prior(V); B.fit_motion(V)
print(f"[{DS}/{DESC}] bins {V} P0 {np.round(P0, 3)}", flush=True)
def search(name, grid, fn):
    best = None
    for g in grid:
        v = B.nll("calib", fn("calib", *g))
        if best is None or v < best[0]: best = (v,) + tuple(g)
    print(f"  {name:10s} sel {best}", flush=True); return best
RES, PER = {}, {}
def ev(name, posts, sel):
    RES[name], PER[name] = B.evaluate(posts); RES[name]["calib_nll"] = sel[0]; RES[name]["sel"] = sel[1:]
    print(f"  {name:10s} R@1 {RES[name]['R@1']:.4f} NLL {RES[name]['NLL']:.4f}", flush=True)
BET = [0.2, 0.35, 0.5, 1.0]
f = search("fixed", itertools.product(B.kernel_grid(), BET), lambda s_, ms, b: B.run(s_, "tau", ms[0], ms[1], b))
ev("fixed", B.run("test", "tau", f[1][0], f[1][1], f[2]), f)
g = search("LV+ME", itertools.product([0.6, 1.0, 1.5], BET, [0.25, 0.5], [0.9, 0.98]),
           lambda s_, vs, b, gm, st: B.run(s_, "tau", None, None, b, vel=V, vstd=vs, me_gamma=gm, vel_stay=st))
ev("LV+ME", B.run("test", "tau", None, None, g[2], vel=V, vstd=g[1], me_gamma=g[3], vel_stay=g[4]), g)
g = search("IMM+ME", itertools.product([0.6, 1.0, 1.5], BET, [0.25, 0.5], [0.0, 0.5, 0.9]),
           lambda s_, vs, b, gm, st: B.run(s_, "tau", None, None, b, vel=V, vstd=vs, me_gamma=gm, vel_stay=st, p0v=P0, vel_mix="prior"))
ev("IMM+ME", B.run("test", "tau", None, None, g[2], vel=V, vstd=g[1], me_gamma=g[3], vel_stay=g[4], p0v=P0, vel_mix="prior"), g)
g = search("STOP+ME", itertools.product([0.6, 1.0, 1.5], BET, [0.25, 0.5], [0.0, 0.5], [0.8, 0.95]),
           lambda s_, vs, b, gm, st, ss: B.run(s_, "tau", None, None, b, vel=V, vstd=vs, me_gamma=gm, vel_stay=st, p0v=P0, vel_mix="stop", stop_stay=ss))
ev("STOP+ME", B.run("test", "tau", None, None, g[2], vel=V, vstd=g[1], me_gamma=g[3], vel_stay=g[4], p0v=P0, vel_mix="stop", stop_stay=g[5]), g)
pick = min(RES, key=lambda k: RES[k]["calib_nll"]); RES["devselected"] = dict(RES[pick]); RES["devselected"]["picked"] = pick; PER["devselected"] = PER[pick]
ref = PER["fixed"]
for k in RES:
    RES[k]["dR1_vs_fixed_CI"] = metrics.paired_block_bootstrap([PER[k]["corr"][b] for b in ref["blocks"]], [ref["corr"][b] for b in ref["blocks"]], n=1000)
print({k: (round(v["R@1"], 4), np.round(v["dR1_vs_fixed_CI"], 3).tolist(), v.get("picked", "")) for k, v in RES.items()}, flush=True)
rid = new_run_id(f"E18c_{DS}_{DESC}_s{SEED}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RES, "bins": V, "P0": P0.tolist()}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=str)
log_run({"run_id": rid, "task_id": "T5.3", "experiment_id": "E18c", "hypothesis_ids": ["H17"], "dataset": DS, "descriptor": DESC, "seed": SEED,
         "status": "ok", "evidence_level": "S", "metrics": {k: {m: v[m] for m in ("R@1", "NLL")} for k, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
