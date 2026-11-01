"""NATURAL off-map benchmark of the CMS rules (RESEARCH_LOG Entry 30): 4Seasons cross-scene runs "4sx:A+B" (vprlib.load_4s_cross):
map = reference recording of scene A (no synthetic hole), queries = the other recordings of A (on-map) followed by every
recording of scene B (a different part of the city: every B frame is off the map, real images, real VIO).
Pipeline per (pair, descriptor), one seed (no hole layout to randomise; real odometry):
  nav_demo.py --cache-only -> navcache;  exact top-300 against the map (cms_exact.topk_long, GPU if present) -> top-100 cache +
  exact counterfactual statistics (cms_exact.cms_stats_exact);  route cache (TAO cost = real part of the CMS statistics);
  oc_curves.py --cms ... --cms-groups cond,loco,online --navgate --fams @E30 for the default navigation init and, with
  --init-top1, a second pass with --nav-init top1 (label-free global initialisation; error of scene B is not reported).
Entry 33: also the standard protocol on a new dataset (e.g. "oxford": 30 % map holes, one layout per seed) with
--seeds K [--seed0 S] (one navcache / top-300 / CMS file and one oc_curves pass per seed) and --oc <extra oc_curves flags, comma-separated>.
Usage: natural_eval.py <dump_dir> <A+B | ds> <desc> [--init-top1] [--fams @E30] [--seeds 1] [--seed0 0] [--oc --newbase,--shcf]
Output: results/oc_4sx_<A+B>_<desc>_s<seed>.json (+ _top1_s<seed>.json), results/cms_*_s<seed>.npz, results/navcache_*.npz"""
import sys, os, subprocess, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cms_exact as CE
import topk_dump as TKD

HERE = os.path.dirname(os.path.abspath(__file__))
FAMS = sys.argv[sys.argv.index("--fams") + 1] if "--fams" in sys.argv else "@E30"
TOP1 = "--init-top1" in sys.argv
opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SEEDS, SEED0 = int(opt("--seeds", "1")), int(opt("--seed0", "0"))
OC = [a for a in opt("--oc", "").split(",") if a]                  # extra oc_curves flags, comma-separated: --oc --newbase,--shcf


def run(cmd):
    t = time.time(); r = subprocess.run(cmd, capture_output=True, text=True)
    print(" ".join(os.path.basename(c) if i < 2 else c for i, c in enumerate(cmd))[:200], f"rc={r.returncode} {time.time() - t:.0f}s", flush=True)
    print(r.stdout[-600:], r.stderr[-1500:] if r.returncode else "", flush=True)
    return r.returncode


def main():
    dump, pair, desc = sys.argv[1], sys.argv[2], sys.argv[3]; ds = pair if (":" in pair or "+" not in pair) else "4sx:" + pair; tag = ds.replace(":", "_")   # Entry 32: any ds (nclt:<ref>)
    W = os.path.abspath(f"_nat_{tag}_{desc}"); ncd, tkd, cmd_, tcd = (os.path.join(W, x) for x in ("nav", "topk", "cms", "taoc"))
    for d in (ncd, tkd, cmd_, tcd, "results"): os.makedirs(d, exist_ok=True)
    t0 = time.time(); seeds = list(range(SEED0, SEED0 + SEEDS))
    if not all(os.path.exists(f"results/navcache_{tag}_{desc}_s{sd}.npz") for sd in seeds) and \
            run([sys.executable, os.path.join(HERE, "nav_demo.py"), dump, ds, desc, str(SEEDS), "--cache", "--cache-only", "--seed0", str(SEED0)]): return
    ep = TKD.load(dump, ds, desc); q, M = ep.q.astype(np.float32), ep.m.astype(np.float32)
    for sd in seeds:
        nf = f"results/navcache_{tag}_{desc}_s{sd}.npz"; os.replace(nf, os.path.join(ncd, os.path.basename(nf))); nf = os.path.join(ncd, os.path.basename(nf))
        z = np.load(nf, allow_pickle=True); t1 = time.time()
        IL, SL, sdL = CE.topk_long(q, M[z["kidx"]], 300)
        np.savez(os.path.join(tkd, f"topk_{tag}_{desc}_s{sd}.npz"), idx=IL[:, :100], sim=SL[:, :100].astype(np.float16), std=sdL)
        st = CE.cms_stats_exact(z, dict(idx=IL, sim=SL, std=sdL), ds=ds)
        np.savez_compressed(os.path.join(cmd_, f"cms_{tag}_{desc}_s{sd}.npz"), **st)
        np.savez_compressed(f"results/cms_{tag}_{desc}_s{sd}.npz", **{k: (v.astype(np.float32) if isinstance(v, np.ndarray) and v.dtype == np.float64 else v) for k, v in st.items()})
        np.savez_compressed(os.path.join(tcd, f"tao_{tag}_{desc}_s{sd}.npz"), cost=st["cost"].astype(np.float32), j=st["j"].astype(np.int32))
        import shutil; shutil.copy(nf, "results/")                  # navcache kept for later re-analysis (Kaggle dataset)
        print(f"{ds}/{desc}/s{sd}: top-300 + cms {time.time() - t1:.0f}s, q {q.shape}, map {M[z['kidx']].shape}", flush=True)
        base = [sys.executable, os.path.join(HERE, "oc_curves.py"), ncd, ds, desc, "--seeds", str(sd), "--jobs", "1", "--topk", tkd, "--taocache", tcd,
                "--cms", cmd_, "--mapdump", dump, "--tw", "0.5", "--variants", "--light", "--cms-alpha", "0.05,0.01", "--cms-groups", "cond,loco,online",
                "--navgate", "--nav-pts", "3", "--fams", FAMS] + (["--gate-rate"] if "--gate-rate" in sys.argv else []) + OC
        run(base + ["--out-suffix", f"_s{sd}"])
        if TOP1: run(base + ["--out-suffix", f"_top1_s{sd}", "--defaults-only", "--nav-init", "top1"])
    print(f"done {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
