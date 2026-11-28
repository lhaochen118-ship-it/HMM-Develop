"""E30b — 6DoF (M5) on CMU and 4Seasons from Kaggle k11 outputs (triangulation from known reference poses +
SuperPoint/LightGlue + PnP; candidates = top-3 NetVLAD single-image vs top-3 of the HMM posterior, same budget).
Accuracy at (0.25m,2°)/(0.5m,5°)/(5m,10°); paired difference HMM-single with a sequence-block bootstrap CI (2000 draws).
Usage: python3 -m hmmloc.exp.e16_pose6dof <dataset cmu|4s|4s2|4s3> <k11_out.json> [<k11_out.json> ...]"""
import sys, os, json, time
import numpy as np
from .common import ROOT, new_run_id, log_run

THR = [(0.25, 2.0), (0.5, 5.0), (5.0, 10.0)]


def succ(rec, a, b):
    return float(rec.get("ok", False) and rec.get("dt", 1e9) <= a and rec.get("dr", 1e9) <= b)


def main(ds, files):
    t0 = time.time(); per = {"single": {}, "hmm": {}}; conv = []
    for f in files:
        d = json.load(open(f)); conv.append(d.get("convention"))
        for m in ("single", "hmm"):
            for r in d["results"][m]:
                per[m][(os.path.abspath(f), r["q"])] = r
    keys = sorted(set(per["single"]) & set(per["hmm"]))
    seq = np.array([f"{k[0]}:{per['single'][k]['seq']}" for k in keys]); useq = np.unique(seq)
    rng = np.random.default_rng(0); res = {"n_queries": len(keys), "n_seq": int(len(useq)), "conventions": conv}
    for a, b in THR:
        s = np.array([succ(per["single"][k], a, b) for k in keys]); h = np.array([succ(per["hmm"][k], a, b) for k in keys])
        diffs = []
        groups = [np.where(seq == u)[0] for u in useq]
        for _ in range(2000):
            idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
            diffs.append(h[idx].mean() - s[idx].mean())
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        res[f"{a}m_{b}deg"] = {"single": float(s.mean()), "hmm": float(h.mean()), "diff": float(h.mean() - s.mean()),
                              "diff_CI": [float(lo), float(hi)]}
        print(f"  {ds} ({a}m,{b}deg): single {s.mean():.3f} hmm {h.mean():.3f} diff {h.mean()-s.mean():+.3f} "
              f"CI [{lo:+.3f}, {hi:+.3f}]", flush=True)
    for m in ("single", "hmm"):
        dt = np.array([per[m][k].get("retr_dt", np.nan) for k in keys])
        res[f"retrieval_top1_median_m_{m}"] = float(np.nanmedian(dt))
    rid = new_run_id(f"E30b_{ds}_pnp")
    od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True)
    json.dump(res, open(os.path.join(od, "metrics.json"), "w"), indent=1)
    log_run({"run_id": rid, "task_id": "T5.5", "experiment_id": "E30", "hypothesis_ids": ["H11"], "dataset": ds,
             "descriptor": "netvlad", "method": "k=3 candidates single vs HMM; triangulated refs (known poses) + SP/LG + PnP (k11)",
             "status": "ok", "evidence_level": "S", "metrics": res,
             "compute": {"platform": "kaggle-gpu(k11)+local-cpu", "minutes": (time.time() - t0) / 60},
             "artifacts": f"research/runs/{rid}", "inputs": [os.path.basename(f) for f in files]})
    print("RUN", rid)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
