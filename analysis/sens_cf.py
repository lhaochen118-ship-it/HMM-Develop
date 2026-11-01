"""Sensitivity of the counterfactual construction + per-stage running time (RESEARCH_LOG Entry 32).
One job = one run x one variant of the surgery: N (belief window of the route hypothesis, default 20 frames) and rho (corridor
radius, default off_d). Recomputes the exact top-300 list on the GPU, the exact counterfactual statistics (cms_exact) with the
variant, then the decision rules (oc_curves, @E32S, +NGRr). Records the wall time of every stage.
Usage: sens_cf.py <dump> <cache dir> <ds> <desc> <seed> <variant: base|N10|N40|rho075|rho125>
Output: results/oc_<ds>_<desc>_cf<variant>_s<seed>.json, results/time_<ds>_<desc>_cf<variant>_s<seed>.json"""
import sys, os, json, time, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cms
import cms_exact as CE
import topk_dump as TKD

HERE = os.path.dirname(os.path.abspath(__file__))
VAR = {"base": (20, 1.0), "N10": (10, 1.0), "N40": (40, 1.0), "rho075": (20, 0.75), "rho125": (20, 1.25)}


def main():
    dump, cdir, ds, desc, seed, var = sys.argv[1:7]; tag = ds.replace(":", "_"); N, rm = VAR[var]
    W = os.path.abspath(f"_cf_{tag}_{desc}_{seed}_{var}"); os.makedirs(W, exist_ok=True); os.makedirs("results", exist_ok=True)
    tm = {}; t = time.time()
    z = np.load(os.path.join(cdir, f"navcache_{tag}_{desc}_s{seed}.npz"), allow_pickle=True)
    ep = TKD.load(dump, ds, desc); q, M = ep.q.astype(np.float32), ep.m.astype(np.float32); Mk = M[z["kidx"]]; tm["load_s"] = time.time() - t
    t = time.time(); IL, SL, sdL = CE.topk_long(q, Mk, 300); tm["topk300_s"] = time.time() - t
    rho = cms.OFF_D.get(ds.split(":")[0].split("_")[0], 40.0) * rm
    t = time.time(); st = CE.cms_stats_exact(z, dict(idx=IL, sim=SL, std=sdL), rho=rho, ds=ds, N=N); tm["cms_stats_s"] = time.time() - t
    np.savez_compressed(os.path.join(W, f"cms_{tag}_{desc}_s{seed}.npz"), **st)
    np.savez_compressed(os.path.join(W, f"tao_{tag}_{desc}_s{seed}.npz"), cost=st["cost"].astype(np.float32), j=st["j"].astype(np.int32))
    np.savez(os.path.join(W, f"topk_{tag}_{desc}_s{seed}.npz"), idx=IL[:, :100], sim=SL[:, :100].astype(np.float16), std=sdL)
    t = time.time()
    cmd = [sys.executable, os.path.join(HERE, "oc_curves.py"), cdir, ds, desc, "--seeds", seed, "--jobs", "1", "--defaults-only",
           "--out-suffix", f"_cf{var}_s{seed}", "--topk", W, "--taocache", W, "--cms", W, "--tw", "0.5", "--variants", "--light",
           "--cms-alpha", "0.05,0.01", "--cms-groups", "cond", "--navgate", "--gate-rate", "--fams", "@E32S"]
    r = subprocess.run(cmd, capture_output=True, text=True); tm["rules_s"] = time.time() - t
    try:
        import torch; gpu = bool(torch.cuda.is_available())
    except Exception:
        gpu = False
    tm.update(n_frames=int(len(q)), n_map=int(len(Mk)), dim=int(q.shape[1]), N=N, rho=float(rho), rc=r.returncode, gpu=gpu)
    json.dump(tm, open(f"results/time_{tag}_{desc}_cf{var}_s{seed}.json", "w"), indent=1)
    print(ds, desc, seed, var, {k: (round(v, 1) if isinstance(v, float) else v) for k, v in tm.items()}, r.stderr[-600:] if r.returncode else "", flush=True)


if __name__ == "__main__":
    main()
