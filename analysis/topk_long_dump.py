"""Exact long candidate lists (top-KL, default 300) of every query frame against the reduced map of each cached run (CPU or GPU):
the input of cms_vec / cms_exact / cms_fwd. Usage: topk_long_dump.py <dump> <navcache_dir> <ds> <desc> <out_dir> [--seeds 0,1] [--KL 300]
-> <out_dir>/tkl_<ds>_<desc>_s<seed>.npz (idx int32, sim float16 -> float32 on load, std)"""
import sys, os, glob, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cms_exact as CE
import topk_dump as TKD


def main():
    dump, cdir, ds, desc, out = sys.argv[1:6]; tag = ds.replace(":", "_")
    KL = int(sys.argv[sys.argv.index("--KL") + 1]) if "--KL" in sys.argv else 300
    seeds = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")] if "--seeds" in sys.argv else None
    files = sorted(glob.glob(os.path.join(cdir, f"navcache_{tag}_{desc}_s*.npz")))
    if seeds is not None: files = [f for f in files if int(f.rsplit("_s", 1)[1][:-4]) in seeds]
    os.makedirs(out, exist_ok=True); t0 = time.time()
    ep = TKD.load(dump, ds, desc); q, M = ep.q.astype(np.float32), ep.m.astype(np.float32)
    for f in files:
        sd_ = int(f.rsplit("_s", 1)[1][:-4]); of = os.path.join(out, f"tkl_{tag}_{desc}_s{sd_}.npz")
        if os.path.exists(of): continue
        z = np.load(f, allow_pickle=True); assert len(z["top"]) == len(q)
        I, Sv, sd = CE.topk_long(q, M[z["kidx"]], KL)
        np.savez(of, idx=I.astype(np.int32), sim=Sv.astype(np.float32), std=sd.astype(np.float32))
        print(f"{of}: top-1 agreement {float((I[:, 0] == z['top']).mean()):.4f}, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
