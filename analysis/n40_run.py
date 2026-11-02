"""Entry 36 item 2: belief window N = 40 vs 20 on held-out seeds. For each (ds, desc, seed): exact top-300 from the dump, counterfactual
statistics with N = 40 (cms_vec), then oc_curves (@E32S, group cond, alpha 0.05, +NGRr) with the N = 40 statistics and with the published
N = 20 statistics -> results/oc_<tag>_<desc>_n40_s<seed>.json and ..._n20_s<seed>.json.
Usage: n40_run.py <dump> <navcache_dir> <cms20_dir> <cms40_dir> <topk_dir> <tao_dir> --jobs jobs.txt --workers 3"""
import sys, os, time, subprocess
import numpy as np
from multiprocessing.pool import ThreadPool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)


def one(args):
    dump, nd, c20, c40, kd, td, ds, desc, seed = args; tag = ds.replace(":", "_"); t0 = time.time(); msg = []
    f40 = os.path.join(c40, f"cms_{tag}_{desc}_s{seed}.npz")
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    if not os.path.exists(f40):
        code = ("import sys, numpy as np; sys.path.insert(0, %r); import cms_exact as CE, cms_vec as CV, topk_dump as TKD;"
                "z = np.load(%r, allow_pickle=True); ep = TKD.load(%r, %r, %r); q, M = ep.q.astype(np.float32), ep.m.astype(np.float32);"
                "IL, SL, sd = CE.topk_long(q, M[z['kidx']], 300);"
                "st = CV.cms_stats_vec({k: z[k] for k in z.files}, dict(idx=IL, sim=SL, std=sd), ds=%r, N=40);"
                "np.savez_compressed(%r, **{k: (v.astype(np.float32) if isinstance(v, np.ndarray) and v.dtype == np.float64 else v) for k, v in st.items()})"
                ) % (HERE, os.path.join(nd, f"navcache_{tag}_{desc}_s{seed}.npz"), dump, ds, desc, ds, f40)
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
        if r.returncode: return f"{ds} {desc} {seed}: cms40 FAILED {r.stderr[-800:]}"
        msg.append(f"cms40 {time.time() - t0:.0f}s")
    for lab, cd in (("n40", c40), ("n20", c20)):
        if os.path.exists(f"results/oc_{tag}_{desc}_{lab}_s{seed}.json"): continue
        t = time.time()
        cmd = [sys.executable, os.path.join(HERE, "oc_curves.py"), nd, ds, desc, "--seeds", str(seed), "--jobs", "1", "--defaults-only",
               "--topk", kd, "--taocache", td, "--cms", cd, "--tw", "0.5", "--variants", "--light", "--cms-alpha", "0.05", "--cms-groups", "cond",
               "--navgate", "--gate-rate", "--fams", "@E32S", "--out-suffix", f"_{lab}_s{seed}"]
        r = subprocess.run(cmd, capture_output=True, text=True, env=env); msg.append(f"{lab} rc {r.returncode} {time.time() - t:.0f}s")
        if r.returncode: msg.append(r.stderr[-500:])
    return f"{ds} {desc} {seed}: " + ", ".join(msg)


def main():
    fixed = sys.argv[1:7]; jf = sys.argv[sys.argv.index("--jobs") + 1]; nw = int(sys.argv[sys.argv.index("--workers") + 1])
    os.makedirs(fixed[3], exist_ok=True); os.makedirs("results", exist_ok=True)
    jobs = [tuple(fixed) + tuple(l.split()) for l in open(jf) if l.strip()]
    with ThreadPool(nw) as p:
        for m in p.imap_unordered(one, jobs): print(m, flush=True)


if __name__ == "__main__":
    main()
