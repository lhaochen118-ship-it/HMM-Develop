"""E08/E11 — Time-warp (stop-and-go / variable speed) on Nordland: does the HMM need the oracle v=1 prior?
Methods (all dev-tuned): single, SeqSLAM (velocity search), HMM fixed kernel, HMM latent velocity,
IA-HMM (+latent velocity), ORACLE per-step kernel (diagnostic).  Usage: e03_timewarp <dataset> <desc> [seed]"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench, load
from .common import ROOT, new_run_id, log_run, subset
from .. import data, hmm, infoaware, metrics, baselines

DS, DESC = sys.argv[1], sys.argv[2]; SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 1
t00 = time.time()
base = load(DS, DESC)[0]
SPEEDS = (0.0, 0.5, 1.0, 2.0, 3.0)
tw = data.timewarp(base, speeds=SPEEDS, seed=SEED)
B = Bench(DS, DESC, eps=[tw]); KIND = "tau"
BETAS = [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]
VELS = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
RES, PER = {}, {}
def ev(name, posts):
    RES[name], PER[name] = B.evaluate(posts); r = RES[name]
    print(f"  {name:16s} R@1 {r['R@1']:.4f} NLL {r['NLL']:.4f} ECE {r['ECE']:.3f} CW {r['CW@0.9']:.4f}", flush=True)

ep, rows = B.split["test"][0]
ev("single", [baselines.single_image_post(ep.sim()[rows], B.tau)])
# SeqSLAM with velocity search including slow/fast
best = None
for L in (5, 10, 20):
    ece, r_ = None, []
    for (e_, r) in B.split["calib"]:
        S, pos, seq, rm = subset(e_, r)
        sc = baselines.seqslam_causal(S, L=L, vels=(0.5, 1.0, 1.5, 2.0, 3.0), enhance=0, reset_mask=rm)
        P = e_.pos[r]; k = P.any(1); r_.append(P[np.arange(len(sc)), sc.argmax(1)][k])
    v = np.concatenate(r_).mean()
    if best is None or v > best[0]: best = (v, L)
S, pos, seq, rm = subset(ep, rows)
sc = baselines.seqslam_causal(S, L=best[1], vels=(0.5, 1.0, 1.5, 2.0, 3.0), enhance=0, reset_mask=rm)
z = sc * 5.0; z -= z.max(1, keepdims=True); p = np.exp(z); ev(f"seqslam_L{best[1]}", [p / p.sum(1, keepdims=True)])

# HMM fixed kernel: mean/std/beta on calib (wider mean grid since speed unknown)
best = None
for m, s, b in itertools.product([0.5, 1.0, 1.5, 2.0], [0.5, 1.0, 2.0, 3.0], BETAS):
    v = B.nll("calib", B.run("calib", KIND, m, s, b))
    if best is None or v < best[0]: best = (v, m, s, b)
print("  fixed kernel sel", best, flush=True); FK = best
ev("hmm_fixed", B.run("test", KIND, FK[1], FK[2], FK[3]))

# HMM latent velocity: vstd, beta on calib
best = None
for vs, b in itertools.product([0.3, 0.6, 1.0], BETAS):
    v = B.nll("calib", B.run("calib", KIND, None, None, b, vel=VELS, vstd=vs))
    if best is None or v < best[0]: best = (v, vs, b)
print("  latent-velocity sel", best, flush=True); LV = best
ev("hmm_latentvel", B.run("test", KIND, None, None, LV[2], vel=VELS, vstd=LV[1]))

# IA-HMM on fixed kernel and on latent velocity
for tag, kw in [("ia_fixed", dict(mean=FK[1], std=FK[2])), ("ia_latentvel", dict(mean=None, std=None, vel=VELS, vstd=LV[1]))]:
    bi = None
    for b0, k in itertools.product([0.35, 0.5, 0.75, 1.0, 1.5], B.kappa_grid):
        fn = (lambda ch, b0=b0, k=k: infoaware.beta_schedule(ch, b0, k))
        v = B.nll("calib", B.run("calib", KIND, kw["mean"], kw["std"], None, vel=kw.get("vel"), vstd=kw.get("vstd", 0.5), beta_fn=fn))
        if bi is None or v < bi[0]: bi = (v, b0, k)
    print(f"  {tag} sel", bi, flush=True)
    fn = (lambda ch, b0=bi[1], k=bi[2]: infoaware.beta_schedule(ch, b0, k))
    ev(tag, B.run("test", KIND, kw["mean"], kw["std"], None, vel=kw.get("vel"), vstd=kw.get("vstd", 0.5), beta_fn=fn))

# ORACLE motion (diagnostic): per-step kernel with the true speed, std small
spd = tw.meta["speed"][rows]
ks = [hmm.chain_kernel(ep.s, mean=v, std=0.5) for v in SPEEDS]
kid = np.array([SPEEDS.index(v) for v in spd]); kid = np.r_[kid[1:], kid[-1]]  # speed applied between t-1 and t
kid = np.r_[0, kid[:-1]]
L = ep.sim()[rows] / B.tau
ev("ORACLE_motion", [hmm.forward_kernel_seq(L, ks, kid, beta=FK[3], reset_mask=rm)])

ref = PER["single"]
for k in RES:
    RES[k]["dR1_vs_single_CI"] = metrics.paired_block_bootstrap([PER[k]["corr"][b] for b in ref["blocks"]], [ref["corr"][b] for b in ref["blocks"]], n=1000)
rid = new_run_id(f"E08_{DS}_{DESC}_tw{SEED}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RES, "fixed": FK, "latentvel": LV}, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T3.1", "experiment_id": "E08", "hypothesis_ids": ["H3", "H17", "H20"], "dataset": DS + "-timewarp",
         "descriptor": DESC, "seed": SEED, "status": "ok", "evidence_level": "S",
         "metrics": {k: {m: v[m] for m in ("R@1", "NLL", "ECE", "CW@0.9")} for k, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid, f"{time.time()-t00:.0f}s")
