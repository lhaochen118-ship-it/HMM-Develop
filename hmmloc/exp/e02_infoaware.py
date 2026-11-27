"""E15/E24-real — Information-aware HMM (H20) vs fixed β vs keyframing vs β=1, same kernel/emission budget.
Usage: python -m hmmloc.exp.e02_infoaware <dataset> <descriptor> <emission kind: tau|llrz>"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run
from .. import infoaware, metrics

DS, DESC, KIND = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "tau")
t00 = time.time(); B = Bench(DS, DESC); NULL = KIND != "tau"
BETAS = [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]
# 1) kernel chosen once with fixed beta grid (shared by all variants -> only the evidence weighting differs)
best = None
for (m, s), b in itertools.product(B.kernel_grid(), BETAS):
    v = B.nll("calib", B.run("calib", KIND, m, s, b, null=NULL))
    if best is None or v < best[0]: best = (v, m, s, b)
_, M0, S0, BFIX = best
print(f"[{DS}/{DESC}/{KIND}] kernel mean={M0} std={S0}; fixed-beta*={BFIX} (calib NLL {best[0]:.4f}); kappa grid {np.round(B.kappa_grid,3)}", flush=True)
VAR = {"beta1": dict(beta=1.0), "fixed_beta": dict(beta=BFIX)}
# 2) IA-HMM: (beta0, kappa) on calib
bi = None
for b0, k in itertools.product([0.35, 0.5, 0.75, 1.0, 1.5, 2.0], B.kappa_grid):
    fn = (lambda ch, b0=b0, k=k: infoaware.beta_schedule(ch, b0, k))
    v = B.nll("calib", B.run("calib", KIND, M0, S0, None, null=NULL, beta_fn=fn))
    if bi is None or v < bi[0]: bi = (v, b0, k)
print(f"  IA-HMM beta0={bi[1]} kappa={bi[2]:.3f} (calib NLL {bi[0]:.4f})", flush=True)
VAR["infoaware"] = dict(beta_fn=lambda ch, b0=bi[1], k=bi[2]: infoaware.beta_schedule(ch, b0, k))
# 3) keyframing control: skip updates (beta=0) when change < thr, else fixed beta (thr on calib)
bk = None
for thr in B.kappa_grid / 2.0:
    for b in BETAS:
        fn = (lambda ch, thr=thr, b=b: np.where(ch < thr, 0.0, b))
        v = B.nll("calib", B.run("calib", KIND, M0, S0, None, null=NULL, beta_fn=fn))
        if bk is None or v < bk[0]: bk = (v, thr, b)
print(f"  keyframe thr={bk[1]:.3f} beta={bk[2]} (calib NLL {bk[0]:.4f})", flush=True)
VAR["keyframe"] = dict(beta_fn=lambda ch, thr=bk[1], b=bk[2]: np.where(ch < thr, 0.0, b))

RES, PER = {}, {}
for name, kw in VAR.items():
    posts = B.run("test", KIND, M0, S0, kw.get("beta"), null=NULL, beta_fn=kw.get("beta_fn"))
    RES[name], PER[name] = B.evaluate(posts)
ref = PER["fixed_beta"]
for name in RES:
    RES[name]["dNLL_vs_fixed_CI"] = metrics.paired_block_bootstrap([PER[name]["nll"][b] for b in ref["blocks"]],
                                                                   [ref["nll"][b] for b in ref["blocks"]], n=1000)
    RES[name]["dR1_vs_fixed_CI"] = metrics.paired_block_bootstrap([PER[name]["corr"][b] for b in ref["blocks"]],
                                                                  [ref["corr"][b] for b in ref["blocks"]], n=1000)
    r = RES[name]
    print(f"  {name:11s} R@1 {r['R@1']:.4f} NLL {r['NLL']:.4f} ECE {r['ECE']:.3f} CW {r['CW@0.9']:.4f} AURC {r['AURC']:.4f} "
          f"| dNLL CI {np.round(r['dNLL_vs_fixed_CI'],4)} dR1 CI {np.round(r['dR1_vs_fixed_CI'],4)}", flush=True)
rid = new_run_id(f"E15_{DS}_{DESC}_{KIND}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RES, "kernel": [M0, S0], "fixed_beta": BFIX, "ia": bi[1:], "keyframe": bk[1:]}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T5.2", "experiment_id": "E15", "hypothesis_ids": ["H20", "H6b"], "dataset": DS,
         "descriptor": DESC, "method": f"IA-HMM vs fixed-beta ({KIND})", "status": "ok", "evidence_level": "S",
         "metrics": {k: {m: v[m] for m in ("R@1", "NLL", "ECE", "CW@0.9")} for k, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid, f"{time.time()-t00:.0f}s")
