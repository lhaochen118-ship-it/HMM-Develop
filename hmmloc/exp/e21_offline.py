"""E37 — OFFLINE comparison (A34): centred sequence baselines vs HMM smoothing with the SAME look-ahead.
Official SeqSLAM (OpenSeqSLAM), SeqMatch (SeqNet code), JIST and SeqVLAD use centred windows (h = L//2 future frames).
  seqslam_centred : centred SeqSLAM/SeqMatch, velocity search on the same calibration-derived velocities as E18,
                    no contrast enhancement (A21), L in {5, 10, 20, 40} chosen on calibration R@1
  hmm_lag_h       : fixed-kernel HMM (E18 calibration selection, unchanged) + fixed-lag smoothing with lag = h of the
                    selected SeqSLAM L (identical future context) — no new hyper-parameters
  hmm_lag_20      : the same with lag 20 (more context, still finite)
plus the causal E18 numbers for reference (single, seqslam causal, hmm_fixed filter).
Usage: python -m hmmloc.exp.e21_offline <dataset> <desc>"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run, subset
from .. import baselines, data

DS, DESC = sys.argv[1], sys.argv[2]; t00 = time.time(); B = Bench(DS, DESC)
_sp = np.concatenate([data.true_speed(ep)[r] for ep, r in B.split["calib"]]); _sp = _sp[np.isfinite(_sp)]
VELS = sorted(set([round(float(q), 2) for q in np.percentile(_sp, [10, 30, 50, 70, 90, 99])] if len(_sp) else [1.0]))
SV = tuple(v for v in VELS if v > 0) or (1.0,)


def seq_posts(split, L, centred):
    out = []
    for ep, r in B.split[split]:
        S, pos, seq, rm = subset(ep, r)
        sp = (np.median(np.diff(ep.s)) if ep.s is not None else float(np.median(np.linalg.norm(np.diff(ep.C, axis=0), axis=1)))) if ep.unit != "frame" else 1.0
        v = tuple(sorted(set(round(x / sp, 2) for x in SV)))
        f = baselines.seqslam_centred if centred else baselines.seqslam_causal
        sc = f(S, L=L, vels=v, enhance=0, reset_mask=rm)
        z = sc * 5.0; z -= z.max(1, keepdims=True); p = np.exp(z); out.append(p / p.sum(1, keepdims=True))
    return out


def r1(split, posts):
    acc = []
    for (ep, r), p in zip(B.split[split], posts):
        P = ep.pos[r]; k = P.any(1); acc.append(P[np.arange(len(p)), p.argmax(1)][k])
    return float(np.concatenate(acc).mean())


RES = {}
RES["single"] = B.evaluate([baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split["test"]])[0]["R@1"]
for centred, name in ((False, "seqslam_causal"), (True, "seqslam_centred")):
    bl = max(((r1("calib", seq_posts("calib", L, centred)), L) for L in (5, 10, 20, 40)))
    RES[name] = r1("test", seq_posts("test", bl[1], centred)); RES[name + "_L"] = bl[1]
best = None
for (m, s), b in itertools.product(B.kernel_grid(), [0.2, 0.35, 0.5, 0.75, 1.0]):
    v = B.nll("calib", B.run("calib", "tau", m, s, b))
    if best is None or v < best[0]: best = (v, m, s, b)
RES["hmm_filter"] = B.evaluate(B.run("test", "tau", best[1], best[2], best[3]))[0]["R@1"]
h = RES["seqslam_centred_L"] // 2
RES["hmm_lag_h"] = B.evaluate(B.run("test", "tau", best[1], best[2], best[3], lag=h))[0]["R@1"]; RES["lag_h"] = h
RES["hmm_lag_20"] = B.evaluate(B.run("test", "tau", best[1], best[2], best[3], lag=20))[0]["R@1"]
print("  " + " | ".join(f"{k} {v:.3f}" if isinstance(v, float) else f"{k} {v}" for k, v in RES.items()), flush=True)
rid = new_run_id(f"E37_{DS}_{DESC}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump(RES, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T5.8", "experiment_id": "E37", "hypothesis_ids": ["A34"], "dataset": DS, "descriptor": DESC,
         "status": "ok", "evidence_level": "S", "metrics": RES,
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
