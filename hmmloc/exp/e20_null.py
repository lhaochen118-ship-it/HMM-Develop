"""E36 — HMM with its OFF-MAP (null) state on revisit / partial-overlap data (KITTI, NCLT, Oxford; F25).
Emission = calibrated LLR (Horvitz-Thompson logistic, l(null)=0); null state with exit probability e, null self-transition
ns and uniform re-entry (hmm.HMMConfig). Hyper-parameters (beta, e, ns; kernel = the fixed-kernel HMM's calibration choice)
are selected on CALIBRATION by the ALL-FRAME event NLL (on-map frames: mass on positives; off-map frames: null mass), so
the selection can neither ignore nor over-use the null. Compared on TEST with single image and the no-null HMM (E18).
Reported: R@1 on on-map frames (same rows as E18) and off-map AUROC of the null posterior.
Usage: python -m hmmloc.exp.e20_null <dataset> <desc>"""
import sys, os, json, time, itertools
import numpy as np
from .bench import Bench
from .common import ROOT, new_run_id, log_run, subset, make_kernels
from .. import hmm, metrics, baselines

DS, DESC = sys.argv[1], sys.argv[2]; t00 = time.time(); B = Bench(DS, DESC)
LLR = B.llr["llrz"]


def run_null(split, mean, std, beta, e, ns):
    posts, nulls = [], []
    for ep, rows in B.split[split]:
        S, pos, seq, rm = subset(ep, rows)
        cfg = hmm.HMMConfig(make_kernels(ep, mean, std), exit_prob=e, null_stay=ns, null_prior=0.05, leak=1e-3, use_null=True)
        o = hmm.forward(LLR.loglik(S), cfg, beta=beta, loglik_null=np.zeros(len(rows)), reset_mask=rm)
        posts.append(o["post"]); nulls.append(o["null"])
    return posts, nulls


def nll_all(split, posts, nulls):
    tot = n = 0
    for (ep, rows), p, nu in zip(B.split[split], posts, nulls):
        P = ep.pos[rows]; on = P.any(1)
        pe = np.where(on, (p * P).sum(1), nu)
        tot += -np.log(np.clip(pe, 1e-6, 1)).sum(); n += len(rows)
    return tot / n


# no-null fixed-kernel HMM (exactly E18's hmm_fixed selection)
best = None
for (m, s), b in itertools.product(B.kernel_grid(), [0.2, 0.35, 0.5, 0.75, 1.0]):
    v = B.nll("calib", B.run("calib", "tau", m, s, b))
    if best is None or v < best[0]: best = (v, m, s, b)
RES = {}
RES["single"] = B.evaluate([baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split["test"]])[0]
RES["hmm_fixed"] = B.evaluate(B.run("test", "tau", best[1], best[2], best[3]))[0]
bn = None
for b, e, ns in itertools.product([0.2, 0.35, 0.5, 1.0, 2.0, 3.0], [0.005, 0.02, 0.05, 0.1, 0.2, 0.3], [0.8, 0.9, 0.97]):
    v = nll_all("calib", *run_null("calib", best[1], best[2], b, e, ns))
    if bn is None or v < bn[0]: bn = (v, b, e, ns)
pt, nt = run_null("test", best[1], best[2], bn[1], bn[2], bn[3])
RES["hmm_null"] = B.evaluate(pt)[0]
off = np.concatenate([~ep.pos[r].any(1) for ep, r in B.split["test"]]).astype(int); nu = np.concatenate(nt)
RES["hmm_null"]["AUROC_offmap"] = float(metrics.auroc(nu, off)) if 0 < off.sum() < len(off) else None
RES["hmm_null"]["offmap_frac_test"] = float(off.mean())
RES["sel"] = {"fixed": best[1:], "null": bn[1:], "null_calib_nll_all": bn[0]}
for k in ("single", "hmm_fixed", "hmm_null"):
    print(f"  {k:10s} R@1 {RES[k]['R@1']:.4f} NLL {RES[k]['NLL']:.4f}", flush=True)
print("  null sel (beta, exit, null_stay):", bn[1:], "| AUROC off-map", RES["hmm_null"]["AUROC_offmap"], flush=True)
rid = new_run_id(f"E36_{DS}_{DESC}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump(RES, open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T5.7", "experiment_id": "E36", "hypothesis_ids": ["H7", "H19"], "dataset": DS, "descriptor": DESC,
         "status": "ok", "evidence_level": "S", "metrics": {k: {m: RES[k][m] for m in ("R@1", "NLL")} for k in ("single", "hmm_fixed", "hmm_null")},
         "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60}, "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
