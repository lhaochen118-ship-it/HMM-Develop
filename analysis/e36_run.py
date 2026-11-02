"""Entry 36 driver: one run (ds, desc, seed) end to end on CPU, reusing every cached input.
  1. counterfactual statistics (cms_vec, exact top-300 from the dump) unless <cms_dir>/cms_<tag>_s<seed>.npz exists; the route cache
     tao_<tag>_s<seed>.npz (TAO cost = real part of the statistics) and the top-100 list are written next to it when missing;
  2. forward counterfactual null (cms_fwd, exits + starts, horizon 20 excl, exits every 1 excl) unless it exists;
  3. oc_curves defaults (--cst --fwd --navgate --gate-rate, preset @E36 unless --fams) -> results/oc_<tag>_<desc>_e36_s<seed>.json.
Usage: e36_run.py <dump> <navcache_dir> <cms_dir> <topk_dir> <tao_dir> <fwd_dir> <ds> <desc> <seed> [--fams @E36] [--groups cond,loco]
       [--horizon 20] [--stride 1x] [--sfx _e36] [--extra "--sens N=40"]"""
import sys, os, time, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)


def main():
    dump, nd, cd, kd, td, fd, ds, desc, seed = sys.argv[1:10]; tag = ds.replace(":", "_"); seed = int(seed)
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    fams, groups, hor, stride, sfx = opt("--fams", "@E36"), opt("--groups", "cond,loco"), opt("--horizon", "20"), opt("--stride", "1x"), opt("--sfx", "_e36")
    for d in (cd, kd, td, fd, "results"): os.makedirs(d, exist_ok=True)
    nf = os.path.join(nd, f"navcache_{tag}_{desc}_s{seed}.npz"); cf = os.path.join(cd, f"cms_{tag}_{desc}_s{seed}.npz")
    ff = os.path.join(fd, f"fwd_{tag}_{desc}_s{seed}.npz"); t0 = time.time(); tm = {}
    if not os.path.exists(cf):
        import cms_exact as CE, topk_dump as TKD
        z = np.load(nf, allow_pickle=True); ep = TKD.load(dump, ds, desc); q, M = ep.q.astype(np.float32), ep.m.astype(np.float32)
        t = time.time(); IL, SL, sdL = CE.topk_long(q, M[z["kidx"]], 300); tm["topk"] = time.time() - t
        t = time.time(); st = CE.stats({k: z[k] for k in z.files}, dict(idx=IL, sim=SL, std=sdL), ds=ds); tm["cms"] = time.time() - t
        np.savez_compressed(cf, **{k: (v.astype(np.float32) if isinstance(v, np.ndarray) and v.dtype == np.float64 else v) for k, v in st.items()})
        tf = os.path.join(td, f"tao_{tag}_{desc}_s{seed}.npz")
        if not os.path.exists(tf): np.savez_compressed(tf, cost=st["cost"].astype(np.float32), j=st["j"].astype(np.int32))
        kf = os.path.join(kd, f"topk_{tag}_{desc}_s{seed}.npz")
        if not os.path.exists(kf): np.savez(kf, idx=IL[:, :100], sim=SL[:, :100].astype(np.float16), std=sdL)
    if not os.path.exists(ff):
        t = time.time()
        r = subprocess.run([sys.executable, os.path.join(HERE, "cms_fwd.py"), dump, nf, ff, "--stride", stride, "--horizon", hor] +
                           (["--ds", ds] if ":" in ds or ds in ("oxford", "stlucia") else []), capture_output=True, text=True)
        tm["fwd"] = time.time() - t
        if r.returncode: print(r.stderr[-2000:], flush=True); return
    t = time.time()
    cmd = [sys.executable, os.path.join(HERE, "oc_curves.py"), nd, ds, desc, "--seeds", str(seed), "--jobs", "1", "--defaults-only",
           "--topk", kd, "--taocache", td, "--cms", cd, "--fwd", fd, "--tw", "0.5", "--variants", "--light", "--cms-alpha", "0.05",
           "--cms-groups", groups, "--navgate", "--gate-rate", "--cst", "--fams", fams, "--out-suffix", f"{sfx}_s{seed}"]
    if "--mapdump" in sys.argv or ds in ("oxford", "stlucia"): cmd += ["--mapdump", dump]
    if "--extra" in sys.argv: cmd += opt("--extra", "").split()
    r = subprocess.run(cmd, capture_output=True, text=True); tm["rules"] = time.time() - t
    print(f"{tag}/{desc}/s{seed}: rc {r.returncode}, " + ", ".join(f"{k} {v:.0f}s" for k, v in tm.items()) + f", total {time.time() - t0:.0f}s",
          r.stderr[-1500:] if r.returncode else "", flush=True)


if __name__ == "__main__":
    main()
