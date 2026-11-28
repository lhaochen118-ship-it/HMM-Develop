"""Kaggle-CPU entry for research/apply_degenerate_fallback.py step 1 (single-image calibration NLL per E18 cell).
Usage: python -m hmmloc.exp.fallback_nll <dataset> <desc> <seed> [...]   -> research/fallback/*.json"""
import sys, os, runpy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = r'''#!/usr/bin/env python3
"""A32b post-hoc: the degenerate HMM (uniform transitions, beta=1 = calibrated single-image posterior) is a candidate of
the calibration leak selection. Runs made before that candidate existed get it here, using CALIBRATION data only:
  step 1 (needs the data; local or Kaggle CPU):  apply_degenerate_fallback.py nll <dataset> <desc> <seed> [...]
          -> research/fallback/<dataset>_<desc>_s<seed>.json  {"single_calib_nll": ...}  (episodes built exactly as e07)
  step 2 (local):                                 apply_degenerate_fallback.py apply
          -> research/fallback/final.json: per E18 cell, OURS_final = single if single_calib_nll < min(leak_calib_nll)
             else OURS_leak (or OURS_devselected for runs without leak selection)."""
import sys, os, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "research", "fallback"); os.makedirs(OUT, exist_ok=True)


def _name(ds, desc, seed):
    return os.path.join(OUT, f"{ds.replace(':', 'q')}_{desc}_s{seed}.json")


def nll(triples):
    sys.path.insert(0, ROOT)
    from hmmloc.exp.bench import Bench, load
    from hmmloc import baselines, data
    for ds, desc, seed in triples:
        f = _name(ds, desc, seed); seed = int(seed)
        if os.path.exists(f):
            continue
        if ds.endswith("-tw"):
            eps = [data.timewarp(e, seed=seed) for e in load(ds[:-3], desc)]
        elif "-q" in ds:
            b, k = ds.split("-q"); eps = [data.subsample_queries(e, int(k)) for e in load(b, desc)]
        else:
            eps = load(ds, desc)
        B = Bench(ds, desc, eps=eps)
        v = B.nll("calib", [baselines.single_image_post(ep.sim()[r], B.tau) for ep, r in B.split["calib"]])
        json.dump({"dataset": ds, "descriptor": desc, "seed": seed, "single_calib_nll": float(v)}, open(f, "w"))
        print(ds, desc, round(float(v), 4), flush=True)


def apply():
    reg = [json.loads(l) for l in open(os.path.join(ROOT, "research", "registry", "runs.jsonl"))]
    latest = {}
    for r in reg:
        if r.get("experiment_id") == "E18" and r["run_id"].split("_")[1] == "E18" and r.get("status") == "ok":
            latest[(r["dataset"], r["descriptor"], r.get("seed", 1))] = r
    final = {}
    for (ds, desc, seed), r in latest.items():
        mj = os.path.join(ROOT, r["artifacts"], "metrics.json")
        res = json.load(open(mj))["results"] if os.path.exists(mj) else {}
        fb = _name(ds, desc, seed)
        key = "OURS_leak" if "OURS_leak" in res else "OURS_devselected"
        rec = {"run_id": r["run_id"], "base": key, "R@1": r["metrics"].get(key, r["metrics"].get("OURS_devselected", {})).get("R@1")}
        if os.path.exists(fb) and "OURS_leak" in res:
            s = json.load(open(fb))["single_calib_nll"]; best = min(res["OURS_leak"]["leak_calib_nll"].values())
            rec.update(single_calib_nll=s, hmm_calib_nll=best)
            if s < best:
                rec.update(base="degenerate(single)", **{"R@1": r["metrics"]["single"]["R@1"]})
        rec["fallback_checked"] = os.path.exists(fb)
        final[f"{ds}|{desc}|{seed}"] = rec
    json.dump(final, open(os.path.join(OUT, "final.json"), "w"), indent=1)
    n = sum(v["base"].startswith("degenerate") for v in final.values())
    print(f"{len(final)} cells, fallback chosen in {n}, unchecked {sum(not v['fallback_checked'] for v in final.values())}")


if __name__ == "__main__":
    if sys.argv[1] == "nll":
        a = sys.argv[2:]; nll(list(zip(a[::3], a[1::3], a[2::3])))
    else:
        apply()
'''
if __name__ == "__main__":
    p = os.path.join(ROOT, "research", "apply_degenerate_fallback.py"); os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p): open(p, "w").write(SRC)
    sys.argv = [p, "nll"] + sys.argv[1:]; runpy.run_path(p, run_name="__main__")
