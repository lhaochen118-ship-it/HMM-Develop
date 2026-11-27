"""E18b — Latent-velocity HMM with a data-driven velocity prior P0(v) (calibration speed histogram) vs uniform P0.
Same emission/ME/IA machinery as e07; selection on calibration NLL. Usage: e13_vprior <dataset> <desc> [seed]"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench, load
from .common import ROOT, new_run_id, log_run
from .. import data, infoaware

DS, DESC = sys.argv[1], sys.argv[2]; SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 1
t00 = time.time()
eps = [data.timewarp(e, seed=SEED) for e in load(DS[:-3], DESC)] if DS.endswith("-tw") else load(DS, DESC)
B = Bench(DS, DESC, eps=eps)
sp = np.concatenate([data.true_speed(ep)[r] for ep, r in B.split["calib"]]); sp = sp[np.isfinite(sp)]
VELS = sorted(set([0.0] + [round(float(q), 2) for q in np.percentile(sp, [10, 30, 50, 70, 90, 99])]))
B.fit_motion(VELS); P0 = B.speed_prior(VELS)
print(f"[{DS}/{DESC}] bins {VELS} prior {np.round(P0, 3)}", flush=True)
RES = {}
fk = None
for (m, s), b in itertools.product(B.kernel_grid(), [0.2, 0.35, 0.5, 0.75, 1.0]):
    v = B.nll("calib", B.run("calib", "tau", m, s, b))
    if fk is None or v < fk[0]: fk = (v, m, s, b)
RES["hmm_fixed"] = B.evaluate(B.run("test", "tau", fk[1], fk[2], fk[3]))[0]; RES["hmm_fixed"]["calib_nll"] = fk[0]
for tag, p0 in (("uniformP0", None), ("speedP0", P0)):
    best = None
    for vs, b, g, st, b0k in itertools.product([0.3, 0.6, 1.0], [0.35, 0.5, 1.0], [0.25, 0.5], [0.98, 0.995], [None, "ia"]):
        kw = dict(vel=VELS, vstd=vs, me_gamma=g, vel_stay=st, p0v=p0)
        for kap in (B.kappa_grid if b0k else [None]):
            fn = (lambda ch, b0=b, k=kap: infoaware.beta_schedule(ch, b0, k)) if b0k else None
            v = B.nll("calib", B.run("calib", "tau", None, None, None if fn else b, beta_fn=fn, **kw))
            if best is None or v < best[0]: best = (v, kw, b, kap, b0k)
    v, kw, b, kap, b0k = best
    fn = (lambda ch, b0=b, k=kap: infoaware.beta_schedule(ch, b0, k)) if b0k else None
    RES[tag] = B.evaluate(B.run("test", "tau", None, None, None if fn else b, beta_fn=fn, **kw))[0]; RES[tag]["calib_nll"] = v
    RES[tag]["sel"] = {"vstd": kw["vstd"], "beta": b, "gamma": kw["me_gamma"], "stay": kw["vel_stay"], "ia_kappa": kap}
pick = min(RES, key=lambda k: RES[k]["calib_nll"]); RES["devselected"] = dict(RES[pick]); RES["devselected"]["picked"] = pick
for k, r in RES.items(): print(f"  {k:12s} R@1 {r['R@1']:.4f} NLL {r['NLL']:.4f} calibNLL {r['calib_nll']:.4f} {r.get('picked','')}", flush=True)
rid = new_run_id(f"E18b_{DS}_{DESC}_s{SEED}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RES, "bins": VELS, "prior": P0.tolist()}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=str)
log_run({"run_id": rid, "task_id": "T5.3", "experiment_id": "E18b", "hypothesis_ids": ["H17"], "dataset": DS, "descriptor": DESC, "seed": SEED,
         "status": "ok", "evidence_level": "S", "metrics": {k: {m: v[m] for m in ("R@1", "NLL")} for k, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid, f"{time.time()-t00:.0f}s")
