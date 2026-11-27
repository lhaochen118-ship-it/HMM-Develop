"""E01/E02 — HMM feasibility ladder (Master Plan T3.3, H1): single-image vs SeqSLAM vs HMM variants.
All hyper-parameters (tau, LLR, kernel std/mean, beta, velocity) are selected on CALIBRATION sequences only;
metrics are on disjoint TEST sequences.  Usage: python -m hmmloc.exp.e01_ladder <dataset> <descriptor> [tag]
"""
import sys, os, json, time, itertools
import numpy as np
from .. import data, hmm, emission, metrics, baselines
from .common import *

DS, DESC = sys.argv[1], sys.argv[2]
TAG = sys.argv[3] if len(sys.argv) > 3 else ""
t00 = time.time()
if DS == "nord": EPS = [data.load_nordland(DESC)]
elif DS == "rc": EPS = [data.load_robotcar(DESC)]
elif DS == "cmu": EPS = data.load_cmu(DESC)
elif DS.startswith("nordseg"): EPS = [data.load_nordseg(DESC, stride=int(DS[7:] or 1))]
else: raise SystemExit("unknown dataset")
UNIT = EPS[0].unit
cal = [(ep, ep.rows("calib")) for ep in EPS]; tst = [(ep, ep.rows("test")) for ep in EPS]
parts_cal = [(ep.sim()[r], ep.pos[r]) for ep, r in cal]

# ---------------- calibration (dev only)
tau, tau_nll = emission.fit_temperature_multi(parts_cal)
llr_raw = emission.fit_llr_multi(parts_cal, kind="raw")
llr_z = emission.fit_llr_multi(parts_cal, kind="raw+z")
print(f"[{DS}/{DESC}] tau={tau:.4f} (calib single NLL {tau_nll:.3f}) | LLR raw w={llr_raw.w} b={llr_raw.b:.2f} | "
      f"LLR raw+z w={llr_z.w} b={llr_z.b:.2f}", flush=True)

if UNIT == "frame":
    MEANS = [1.0]; STDS = [0.5, 1.0, 2.0]; VELS = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]; VSTD = 0.4
else:
    MEANS = [0.75, 1.5, 2.5]; STDS = [0.75, 1.5, 3.0]; VELS = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]; VSTD = 1.0
BETAS = [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]


def emit(ep, rows, kind):
    S = ep.sim()[rows]
    if kind == "tau": return S / tau, None
    if kind == "llr": return llr_raw.loglik(S), np.zeros(len(rows))
    if kind == "llrz": return llr_z.loglik(S), np.zeros(len(rows))


def run_all(split, kind, mean=None, std=None, beta=1.0, vel=False, use_null=False):
    posts = []
    for ep, rows in (cal if split == "calib" else tst):
        L, Ln = emit(ep, rows, kind)
        ks = make_kernels(ep, mean, std) if not vel else make_kernels(ep, None, None, vels=VELS, vstd=VSTD)
        out = run_hmm(ep, rows, L, ks, beta=beta, use_null=use_null, exit_prob=0.01 if use_null else 0.0,
                      loglik_null=Ln if use_null else None)
        posts.append(out["post"])
    return posts


def calib_nll(posts):
    tot, n = 0.0, 0
    for (ep, rows), p in zip(cal, posts):
        P = ep.pos[rows]; k = P.any(1)
        tot += metrics.event_nll(p[k], P[k]).sum(); n += k.sum()
    return tot / n


def select(kind, vel=False, use_null=False):
    best = None
    bet = BETAS if kind == "tau" else BETAS + [1.5, 2.0, 3.0, 4.0]
    grid = itertools.product(MEANS if not vel else [None], STDS if not vel else [None], bet)
    for mean, std, beta in grid:
        nll = calib_nll(run_all("calib", kind, mean, std, beta, vel, use_null))
        if best is None or nll < best[0]: best = (nll, mean, std, beta)
    return best


def eval_posts(posts):
    """Pool test frames across episodes."""
    summs, pers = [], []
    allc, alln, allconf, blocks = [], [], [], []
    for (ep, rows), p in zip(tst, posts):
        s, per = evaluate(ep, rows, p); pers.append(per)
        off = sum(len(x) for x in allc)
        allc.append(per["corr"]); alln.append(per["nll"]); allconf.append(per["conf"])
        blocks += [b + off for b in per["blocks"]]
    c = np.concatenate(allc); nl = np.concatenate(alln); cf = np.concatenate(allconf)
    summ = {"R@1": float(c.mean()), "NLL": float(nl.mean()), "ECE": metrics.ece(cf, c), "Brier": metrics.brier(cf, c),
            "CW@0.9": float(np.mean((cf > 0.9) & (c == 0))), "AUROC_conf": metrics.auroc(cf, c),
            "AURC": metrics.aurc(cf, c), "R@1_CI": metrics.block_bootstrap([c[b] for b in blocks], n=1000),
            "n": int(len(c)), "n_seq": len(blocks)}
    return summ, {"corr": c, "nll": nl, "conf": cf, "blocks": blocks}


RESULTS = {}; PER = {}
# B01 single image (calibrated softmax)
posts = [baselines.single_image_post(ep.sim()[rows], tau) for ep, rows in tst]
RESULTS["B01_single"], PER["B01_single"] = eval_posts(posts)
# B04 SeqSLAM (causal): L and contrast enhancement selected on calibration R@1 (fair tuning budget)
SVELS = (0.5, 0.75, 1.0, 1.25, 1.5) if UNIT == "frame" else (0.6, 0.8, 1.0, 1.2, 1.5)
def seqslam_posts(split, L, enh):
    out = []
    for ep, rows in (cal if split == "calib" else tst):
        S, pos, seq, rm = subset(ep, rows)
        sc = baselines.seqslam_causal(S, L=L, vels=SVELS, enhance=enh, reset_mask=rm)
        z = sc * 5.0; z -= z.max(1, keepdims=True); p = np.exp(z); out.append(p / p.sum(1, keepdims=True))
    return out
best = None
for L in (3, 5, 10, 20):
    for enh in (0, 25):
        r = []
        for (ep, rows), p in zip(cal, seqslam_posts("calib", L, enh)):
            P = ep.pos[rows]; k = P.any(1); r.append(P[np.arange(len(p)), p.argmax(1)][k])
        r = np.concatenate(r).mean()
        if best is None or r > best[0]: best = (r, L, enh)
print(f"  SeqSLAM selected L={best[1]} enhance={best[2]} (calib R@1 {best[0]:.3f})", flush=True)
RESULTS["B04_seqslam"], PER["B04_seqslam"] = eval_posts(seqslam_posts("test", best[1], best[2]))
RESULTS["B04_seqslam"]["sel"] = [best[1], best[2]]

CHOSEN = {}
for name, kind, vel, null, fixed_beta in [("H0_hmm_tau_b1", "tau", False, False, 1.0),
                                          ("H1_hmm_tau_beta", "tau", False, False, None),
                                          ("H2_hmm_llr", "llr", False, True, None),
                                          ("H3_hmm_llrz", "llrz", False, True, None),
                                          ("H4_hmm_llrz_vel", "llrz", True, True, None)]:
    t0 = time.time()
    if fixed_beta is not None:
        global BETAS_SAVE
        BETAS_SAVE = BETAS; BETAS = [fixed_beta]
        sel = select(kind, vel, null); BETAS = BETAS_SAVE
    else:
        sel = select(kind, vel, null)
    CHOSEN[name] = {"calib_nll": sel[0], "mean": sel[1], "std": sel[2], "beta": sel[3]}
    posts = run_all("test", kind, sel[1], sel[2], sel[3], vel, null)
    RESULTS[name], PER[name] = eval_posts(posts)
    print(f"  {name:18s} sel(mean={sel[1]},std={sel[2]},beta={sel[3]}) {fmt(RESULTS[name])} [{time.time()-t0:.0f}s]", flush=True)

# paired deltas vs single-image
base = PER["B01_single"]
for k in RESULTS:
    if k == "B01_single": continue
    d = metrics.paired_block_bootstrap([PER[k]["corr"][b] for b in base["blocks"]], [base["corr"][b] for b in base["blocks"]], n=1000)
    RESULTS[k]["dR@1_vs_single"] = float(PER[k]["corr"].mean() - base["corr"].mean()); RESULTS[k]["dR@1_CI"] = d

print(f"\n=== {DS}/{DESC}  (test frames {RESULTS['B01_single']['n']}, seqs {RESULTS['B01_single']['n_seq']}) ===")
for k, v in RESULTS.items():
    extra = f" | dR@1 {v.get('dR@1_vs_single', 0):+.3f} CI[{v.get('dR@1_CI',(0,0))[0]:+.3f},{v.get('dR@1_CI',(0,0))[1]:+.3f}]" if k != "B01_single" else ""
    print(f"{k:18s} {fmt(v)}{extra}")

rid = new_run_id(f"E01_{DS}_{DESC}{TAG}")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
json.dump({"results": RESULTS, "chosen": CHOSEN, "tau": tau, "llr_raw": llr_raw.describe(), "llr_z": llr_z.describe()},
          open(os.path.join(od, "metrics.json"), "w"), indent=1, default=float)
log_run({"run_id": rid, "task_id": "T3.3", "experiment_id": "E01", "hypothesis_ids": ["H1"], "dataset": DS,
         "descriptor": DESC, "split": "calib-select/test-eval by sequence", "status": "ok",
         "metrics": {k: {m: v[m] for m in ("R@1", "NLL", "ECE", "CW@0.9")} for k, v in RESULTS.items()},
         "evidence_level": "S", "compute": {"platform": "local-cpu", "minutes": (time.time() - t00) / 60},
         "artifacts": f"research/runs/{rid}"})
print("RUN", rid, f"{time.time()-t00:.0f}s")
