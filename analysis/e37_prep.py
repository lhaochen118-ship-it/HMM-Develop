"""Entry 37 kernel job for a run whose inputs are NOT in the public caches (Oxford RobotCar, St Lucia): the whole chain in one job.
  1. nav_demo.py --cache --cache-only (30 % holes, seed s)                 -> results/navcache_<tag>_<desc>_s<seed>.npz
  2. exact counterfactual statistics (top-300 on the GPU if visible, cms_vec) -> results/cms/cms_..., results/topk/topk_... (top-100),
     results/tao/tao_... (route cost = real part of the statistics), as e36_run.py step 1
  3. forward counterfactual null with the system's presence statistics (e37_fwd.py config, whole run) -> results/fwdp_..._s<seed>.p0of1.npz
Usage: e37_prep.py <dump_dir> <ds> <desc> <seed> [--no-fwd]"""
import sys, os, time, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)


def main():
    dump, ds, desc, seed = sys.argv[1:5]; tag = ds.replace(":", "_"); t0 = time.time(); tm = {}
    for d in ("results", "results/cms", "results/topk", "results/tao"): os.makedirs(d, exist_ok=True)
    nf = os.path.join("results", f"navcache_{tag}_{desc}_s{seed}.npz")
    if not os.path.exists(nf):
        t = time.time()
        r = subprocess.run([sys.executable, os.path.join(HERE, "nav_demo.py"), dump, ds, desc, "1", "--cache", "--cache-only", "--seed0", seed],
                           capture_output=True, text=True)
        tm["navcache"] = time.time() - t
        if r.returncode or not os.path.exists(nf): print(r.stdout[-1500:], r.stderr[-3000:], flush=True); sys.exit(1)
    open(nf + ".done", "w").write("ok")                                 # complete file marker for the parts waiting on it (e37_fwd --wait)
    cf = os.path.join("results", "cms", f"cms_{tag}_{desc}_s{seed}.npz")
    if not os.path.exists(cf):
        import cms_exact as CE, topk_dump as TKD
        z = np.load(nf, allow_pickle=True); ep = TKD.load(dump, ds, desc); q, M = ep.q.astype(np.float32), ep.m.astype(np.float32)
        t = time.time(); IL, SL, sdL = CE.topk_long(q, M[z["kidx"]], 300); tm["topk"] = time.time() - t
        t = time.time(); st = CE.stats({k: z[k] for k in z.files}, dict(idx=IL, sim=SL, std=sdL), ds=ds); tm["cms"] = time.time() - t
        np.savez_compressed(cf, **{k: (v.astype(np.float32) if isinstance(v, np.ndarray) and v.dtype == np.float64 else v) for k, v in st.items()})
        np.savez_compressed(os.path.join("results", "tao", f"tao_{tag}_{desc}_s{seed}.npz"), cost=st["cost"].astype(np.float32), j=st["j"].astype(np.int32))
        np.savez(os.path.join("results", "topk", f"topk_{tag}_{desc}_s{seed}.npz"), idx=IL[:, :100], sim=SL[:, :100].astype(np.float16), std=sdL)
        del q, M, ep
    if "--no-fwd" not in sys.argv:
        t = time.time()
        r = subprocess.run([sys.executable, os.path.join(HERE, "e37_fwd.py"), dump, "results", ds, desc, seed, "0/1"], capture_output=True, text=True)
        tm["fwd"] = time.time() - t
        if r.returncode: print(r.stdout[-1500:], r.stderr[-3000:], flush=True); sys.exit(1)
        print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "", flush=True)
    print(f"{tag}/{desc}/s{seed}: " + ", ".join(f"{k} {v:.0f}s" for k, v in tm.items()) + f", total {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
