"""E08b/E18 — Latent-velocity HMM with appearance-change velocity emission (ME) and information-aware weighting (IA).
Variants (all dev-selected): LV (latent velocity), LV+ME, LV+ME+IA, plus single image and ORACLE motion.
Usage: e07_motionev <dataset|nord-tw> <desc> [seed]"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench, load
from .common import ROOT, new_run_id, log_run, subset
from .. import data, hmm, infoaware, metrics, baselines

DS, DESC = sys.argv[1], sys.argv[2]; SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 1
t00 = time.time()
if DS.endswith("-tw"):
    eps = [data.timewarp(e, seed=SEED) for e in load(DS[:-3], DESC)]
elif "-q" in DS:                               # e.g. cmu-q3: every 3rd query frame
    base_ds, k = DS.split("-q"); eps = [data.subsample_queries(e, int(k)) for e in load(base_ds, DESC)]
else:
    eps = load(DS, DESC)
B = Bench(DS, DESC, eps=eps); KIND = "tau"
UNIT = B.unit
# velocity bins: data-driven from CALIBRATION GT speed quantiles (+ a stop bin) — no test information
_sp = np.concatenate([data.true_speed(ep)[r] for ep, r in B.split["calib"]]); _sp = _sp[np.isfinite(_sp)]
VELS = sorted(set([0.0] + [round(float(q), 2) for q in np.percentile(_sp, [10, 30, 50, 70, 90, 99])]))
print("velocity bins from calibration quantiles:", VELS, flush=True)
BETAS = [0.2, 0.35, 0.5, 0.75, 1.0]
me = B.fit_motion(VELS); print(f"[{DS}/{DESC}] motion emission {me.describe()}", flush=True)
RES, PER = {}, {}
def ev(name, posts):
    RES[name], PER[name] = B.evaluate(posts); r = RES[name]
    print(f"  {name:14s} R@1 {r['R@1']:.4f} NLL {r['NLL']:.4f} ECE {r['ECE']:.3f} CW {r['CW@0.9']:.4f}", flush=True)
ev("single", [baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split["test"]])
SV = tuple(v for v in VELS if v > 0) if len(VELS) > 1 else (1.0,)
def _seq(split, L):
    out = []
    for ep, r in B.split[split]:
        S, pos, seq, rm = subset(ep, r)
        # velocities in map NODES per frame: divide metric speeds by the median node spacing
        sp = (np.median(np.diff(ep.s)) if ep.s is not None else float(np.median(np.linalg.norm(np.diff(ep.C, axis=0), axis=1)))) if ep.unit != "frame" else 1.0
        sc = baselines.seqslam_causal(S, L=L, vels=tuple(sorted(set(round(v / sp, 2) for v in SV))), enhance=0, reset_mask=rm)
        z = sc * 5.0; z -= z.max(1, keepdims=True); p_ = np.exp(z); out.append(p_ / p_.sum(1, keepdims=True))
    return out
_bs = None
for L in (5, 10, 20):
    acc = []
    for (ep, r), p_ in zip(B.split["calib"], _seq("calib", L)):
        P = ep.pos[r]; k = P.any(1); acc.append(P[np.arange(len(p_)), p_.argmax(1)][k])
    a = np.concatenate(acc).mean()
    if _bs is None or a > _bs[0]: _bs = (a, L)
ev(f"seqslam", _seq("test", _bs[1])); RES["seqslam"]["L"] = _bs[1]

def sel(grid, fn):
    best = None
    for g in grid:
        v = B.nll("calib", fn("calib", *g))
        if best is None or v < best[0]: best = (v,) + tuple(g)
    return best
VSTDS = [0.3, 0.6, 1.0] if UNIT == "frame" else [0.3, 0.6, 1.0]
fk = sel(itertools.product([(m, s) for m, s in B.kernel_grid()], BETAS), lambda sp, ms, b: B.run(sp, KIND, ms[0], ms[1], b))
print("  sel fixed", fk, flush=True); ev("hmm_fixed", B.run("test", KIND, fk[1][0], fk[1][1], fk[2]))
lv = sel(itertools.product(VSTDS, BETAS, [0.9, 0.98]), lambda sp, vs, b, st: B.run(sp, KIND, None, None, b, vel=VELS, vstd=vs, vel_stay=st))
print("  sel LV", lv, flush=True); ev("LV", B.run("test", KIND, None, None, lv[2], vel=VELS, vstd=lv[1], vel_stay=lv[3]))
lvme = sel(itertools.product(VSTDS, BETAS, [0.25, 0.5, 1.0], [0.9, 0.98]),
           lambda sp, vs, b, g, st: B.run(sp, KIND, None, None, b, vel=VELS, vstd=vs, me_gamma=g, vel_stay=st))
print("  sel LV+ME", lvme, flush=True)
ev("LV+ME", B.run("test", KIND, None, None, lvme[2], vel=VELS, vstd=lvme[1], me_gamma=lvme[3], vel_stay=lvme[4]))
vs, g, st = lvme[1], lvme[3], lvme[4]
ia = sel(itertools.product([0.35, 0.5, 0.75, 1.0, 1.5], list(B.kappa_grid) + [float(np.percentile(np.concatenate([c[np.isfinite(c)] for c in B.change['calib']]), 10))]),
         lambda sp, b0, k: B.run(sp, KIND, None, None, None, vel=VELS, vstd=vs, me_gamma=g, vel_stay=st,
                                 beta_fn=lambda ch, b0=b0, k=k: infoaware.beta_schedule(ch, b0, k)))
print("  sel LV+ME+IA", ia, flush=True)
ev("LV+ME+IA", B.run("test", KIND, None, None, None, vel=VELS, vstd=vs, me_gamma=g, vel_stay=st,
                     beta_fn=lambda ch, b0=ia[1], k=ia[2]: infoaware.beta_schedule(ch, b0, k)))
_cands = {"hmm_fixed": fk[0], "LV": lv[0], "LV+ME": lvme[0], "LV+ME+IA": ia[0]}
_pick = min(_cands, key=_cands.get)
RES["OURS_devselected"] = dict(RES[_pick]); PER["OURS_devselected"] = PER[_pick]; RES["OURS_devselected"]["picked"] = _pick
print(f"  OURS_devselected -> {_pick} (calib NLL {_cands})", flush=True)
# A32: calibration-selected leak (uniform re-localisation mass) for the picked variant; leak=1 ~ tempered single image,
# so the HMM can fall back gracefully when appearance evidence is too weak for the motion model (MSLS-sf + DINOv2).
_RUN = {"hmm_fixed": lambda sp, lk: B.run(sp, KIND, fk[1][0], fk[1][1], fk[2], leak=lk),
        "LV": lambda sp, lk: B.run(sp, KIND, None, None, lv[2], vel=VELS, vstd=lv[1], vel_stay=lv[3], leak=lk),
        "LV+ME": lambda sp, lk: B.run(sp, KIND, None, None, lvme[2], vel=VELS, vstd=lvme[1], me_gamma=lvme[3], vel_stay=lvme[4], leak=lk),
        "LV+ME+IA": lambda sp, lk: B.run(sp, KIND, None, None, None, vel=VELS, vstd=vs, me_gamma=g, vel_stay=st, leak=lk,
                                         beta_fn=lambda ch, b0=ia[1], k=ia[2]: infoaware.beta_schedule(ch, b0, k))}
LEAKS = [1e-3, 0.03, 0.1, 0.3, 1.0]
# leak = 1 is the DEGENERATE HMM: uniform transitions -> evidence alone; with beta = 1 it is exactly the calibrated
# single-image posterior (A32: tempering by the HMM's beta made it over-flat, so selection never fell back).
_RUN_DEG = lambda sp: [baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split[sp]]
_lk = {lk: (_cands[_pick] if lk == 1e-3 else B.nll("calib", _RUN_DEG("calib") if lk == 1.0 else _RUN[_pick]("calib", lk))) for lk in LEAKS}
_best_lk = min(_lk, key=_lk.get)
if _best_lk == 1e-3:
    RES["OURS_leak"] = dict(RES[_pick]); PER["OURS_leak"] = PER[_pick]
else:
    ev("OURS_leak", _RUN_DEG("test") if _best_lk == 1.0 else _RUN[_pick]("test", _best_lk))
RES["OURS_leak"].update(picked=_pick, leak=_best_lk, leak_calib_nll={str(k): float(v) for k, v in _lk.items()})
print(f"  OURS_leak -> {_pick} leak={_best_lk} (calib NLL {_lk})", flush=True)
if "speed" in B.eps[0].meta:
    ep, rows = B.split["test"][0]; spd = B.eps[0].meta["speed"][rows]
    ks = [hmm.chain_kernel(ep.s, mean=v, std=0.5) for v in sorted(set(spd))]; vals = sorted(set(spd))
    kid = np.r_[0, [vals.index(v) for v in spd[:-1]]]
    S, pos, seq, rm = subset(ep, rows)
    ev("ORACLE_motion", [hmm.forward_kernel_seq(ep.sim()[rows] / B.tau, ks, kid, beta=fk[2], reset_mask=rm)])
ref = PER["hmm_fixed"]
for k in RES:
    RES[k]["dR1_vs_fixed_CI"] = metrics.paired_block_bootstrap([PER[k]["corr"][b] for b in ref["blocks"]], [ref["corr"][b] for b in ref["blocks"]], n=1000)
    RES[k]["dNLL_vs_fixed_CI"] = metrics.paired_block_bootstrap([PER[k]["nll"][b] for b in ref["blocks"]], [ref["nll"][b] for b in ref["blocks"]], n=1000)
print({k: (round(v["R@1"], 4), np.round(v["dR1_vs_fixed_CI"], 4).tolist()) for k, v in RES.items()})
rid = new_run_id(f"E18_{DS}_{DESC}_s{SEED}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RES, "sel": {"fixed": fk, "LV": lv, "LVME": lvme, "IA": ia}, "motion_emission": me.describe()},
          open(os.path.join(od, "metrics.json"), "w"), indent=1, default=str)
log_run({"run_id": rid, "task_id": "T5.3", "experiment_id": "E18", "hypothesis_ids": ["H17", "H18", "H20"], "dataset": DS,
         "descriptor": DESC, "seed": SEED, "status": "ok", "evidence_level": "S",
         "metrics": {k: {m: v[m] for m in ("R@1", "NLL", "ECE", "CW@0.9")} for k, v in RES.items()},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid, f"{time.time()-t00:.0f}s")
