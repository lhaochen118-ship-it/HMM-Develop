"""Compute the CMS statistics (real + counterfactual route cost and distinctiveness, cms.cms_stats) of every run.
Usage: cms_dump.py <cache_dir> <topk_dir> <ds> <desc> [--seeds 0,1,2] [--jobs 3] [--rho-add 1]  -> results/cms_<ds>_<desc>_s<seed>.npz
(ds with ':' written with '_', e.g. 4s_old_town). Published as nhatlong1103/hmm-cms-cache; read by oc_curves.py --cms."""
import sys, os, glob, time
import numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cms

SEEDS = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")] if "--seeds" in sys.argv else None
JOBS = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 3
RHO_ADD = float(sys.argv[sys.argv.index("--rho-add") + 1]) if "--rho-add" in sys.argv else 1.0   # rho = off_d + RHO_ADD * excl (sensitivity)


def one(a):
    cf, tkd, ds = a
    tag = os.path.basename(cf)[len("navcache_"):-4]; out = f"results/cms_{tag}.npz"
    if os.path.exists(out): return out, 0.0
    tf = os.path.join(tkd, f"topk_{tag}.npz")
    if not os.path.exists(tf): return out + " (no topk)", 0.0
    t0 = time.time(); z = np.load(cf, allow_pickle=True); rho = cms.OFF_D.get(ds.split(":")[0].split("_")[0], 40.0) + RHO_ADD * float(z["excl"])
    st = cms.cms_stats(z, np.load(tf), rho=rho, ds=ds)
    np.savez_compressed(out, **{k: (v.astype(np.float32) if isinstance(v, np.ndarray) and v.dtype == np.float64 else v) for k, v in st.items()})
    return out, time.time() - t0


def main():
    cdir, tkd, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    files = sorted(glob.glob(os.path.join(cdir, f"navcache_{ds.replace(':', '_')}_{desc}_s*.npz")))
    if SEEDS is not None: files = [f for f in files if int(f.rsplit("_s", 1)[1][:-4]) in SEEDS]
    os.makedirs("results", exist_ok=True)
    with Pool(max(1, min(JOBS, len(files)))) as p:
        for out, dt in p.imap_unordered(one, [(f, tkd, ds) for f in files]): print(out, f"{dt:.0f}s", flush=True)


if __name__ == "__main__":
    main()
