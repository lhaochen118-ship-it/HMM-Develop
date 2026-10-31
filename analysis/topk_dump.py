"""Top-K retrieval candidates of every query frame against the REDUCED map of every nav_demo seed (Entry 26).

Inputs of the TAO'26 / TRAIL'26 baselines (and of any rule that needs more than the top-1): for each seed's cache
(navcache_<ds>_<desc>_s<seed>.npz, which stores the kept map rows `kidx`), the K most similar kept map rows of every query
frame, in the query order of the cache. One similarity matmul per query chunk against the FULL map, then a masked top-K
per seed (all seeds share the matmul). GPU (torch, fp32) when available, else numpy.
Usage: topk_dump.py <dump_dir> <ds> <desc> <cache_dir> [--K 100] [--seeds 0,1,...]
Output: results/topk_<ds>_<desc>_s<seed>.npz  idx (n_q, K) int32 = rows of the REDUCED map (MP / est_c index space),
        sim (n_q, K) float16, plus row statistics mean / std of the similarity to the reduced map (float32)."""
import sys, os, glob, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V

K = int(sys.argv[sys.argv.index("--K") + 1]) if "--K" in sys.argv else 100
SEEDS = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")] if "--seeds" in sys.argv else None


def load(dump, ds, desc):
    if ds.startswith("4s:"): return V.load_4seasons(dump, desc, ds[3:])
    if ds == "boreas": return V.load_boreas(dump, desc)
    return V.LOADERS[ds](dump, desc)


def main():
    dump, ds, desc, cdir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    tag = ds.replace(":", "_")
    files = sorted(glob.glob(os.path.join(cdir, f"navcache_{tag}_{desc}_s*.npz")), key=lambda f: int(f.rsplit("_s", 1)[1][:-4]))
    if SEEDS is not None: files = [f for f in files if int(f.rsplit("_s", 1)[1][:-4]) in SEEDS]
    if not files: print("no caches"); return
    t0 = time.time(); ep = load(dump, ds, desc); q, M = ep.q.astype(np.float32), ep.m.astype(np.float32)
    keeps = []
    for f in files:
        z = np.load(f, allow_pickle=True); kidx = z["kidx"]; assert len(z["top"]) == len(q), (len(z["top"]), len(q))
        keeps.append((int(z["seed"]), kidx, z["top"]))
    print(f"{ds}/{desc}: q {q.shape} map {M.shape} seeds {[s for s, _, _ in keeps]} load {time.time() - t0:.0f}s", flush=True)
    try:
        import torch
        dev = "cuda" if torch.cuda.is_available() else None
    except Exception:
        dev = None
    n = len(q); out = {s: (np.zeros((n, K), np.int32), np.zeros((n, K), np.float16), np.zeros(n, np.float32), np.zeros(n, np.float32)) for s, _, _ in keeps}
    ch = 8192 if dev else 2048
    if dev:
        Mt = torch.from_numpy(M).to(dev); kt = {s: torch.from_numpy(kidx).to(dev) for s, kidx, _ in keeps}
    for a in range(0, n, ch):
        if dev:
            S = torch.from_numpy(q[a:a + ch]).to(dev) @ Mt.T
            for s, kidx, _ in keeps:
                Sk = S[:, kt[s]]; v, i = torch.topk(Sk, min(K, Sk.shape[1]), dim=1)
                o = out[s]; o[0][a:a + ch] = i.cpu().numpy(); o[1][a:a + ch] = v.cpu().numpy().astype(np.float16)
                o[2][a:a + ch] = Sk.mean(1).cpu().numpy(); o[3][a:a + ch] = Sk.std(1).cpu().numpy()
        else:
            S = q[a:a + ch] @ M.T
            for s, kidx, _ in keeps:
                Sk = S[:, kidx]; i = np.argpartition(-Sk, K - 1, axis=1)[:, :K]; v = np.take_along_axis(Sk, i, 1)
                o_ = np.argsort(-v, 1); i, v = np.take_along_axis(i, o_, 1), np.take_along_axis(v, o_, 1)
                o = out[s]; o[0][a:a + ch] = i; o[1][a:a + ch] = v.astype(np.float16); o[2][a:a + ch] = Sk.mean(1); o[3][a:a + ch] = Sk.std(1)
    os.makedirs("results", exist_ok=True)
    for s, kidx, top in keeps:
        i, v, mu, sd = out[s]; agree = float((i[:, 0] == top).mean())
        np.savez_compressed(f"results/topk_{tag}_{desc}_s{s}.npz", idx=i, sim=v, mean=mu, std=sd, K=K)
        print(f"  seed {s}: top-1 agreement with cache {agree:.4f}", flush=True)
    print(f"done {time.time() - t0:.0f}s on {dev or 'cpu'}", flush=True)


if __name__ == "__main__":
    main()
