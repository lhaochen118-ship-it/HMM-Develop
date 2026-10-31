"""SafeVPR baseline, stage A (GPU): mutual-nearest-neighbour patch-matching score (Sier et al. 2026) between every query
frame and its top-K map candidates of every global descriptor, on frozen DINOv2 ViT-B/14 patch tokens.

Boreas: map = reference sequence, queries = V.BOREAS_Q (as V.load_boreas). Images come from the public datasets
nhatlong1103/boreas-vpr-images-{1..4} (img/<seq>/<timestamp_us>.jpg), DINOv2 weights from nhatlong1103/bundle.
All GPUs of the session are used: map patch tokens are replicated on every GPU, query batches are spread round-robin.
Output results/safevpr_<ds>_p<i>.npz: for each descriptor d, cand_<d> (n_rows, K) full-map indices of the top-K by global
cosine similarity, mnn_<d> (n_q, K) number of mutual-NN patch pairs (the SafeVPR score); q_rows = query rows covered (frames whose image is missing are skipped).
Stage B (calibration with labels, Mondrian Learn-Then-Test, navigation) is in nav_demo.py (--safevpr).
Usage: safevpr_mnn.py <dump> <ds: boreas|nclt|4s:<scene>> [K=20] [--part i/n]   (images: vpr_images.py)"""
import sys, os, time, threading, queue
import numpy as np, torch
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V

PART = (0, 1)
if "--part" in sys.argv:
    i = sys.argv.index("--part"); a, b = sys.argv[i + 1].split("/"); PART = (int(a), int(b)); del sys.argv[i:i + 2]
DESCS = ["megaloc", "salad", "mixvpr", "cosplace", "netvlad", "dinov2"]
SHORT = 224                                                   # short side (pixels) -> 16 x ~19 patches of 14 px


def find(root, name):
    for d, ds, fs in os.walk(root):
        if name in ds or name in fs: return os.path.join(d, name)
    return None


def main():
    dump, ds = sys.argv[1], sys.argv[2]; K = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    t0 = time.time(); ngpu = max(1, torch.cuda.device_count())
    import topk_dump as TKD, vpr_images as VI
    eps = {d: TKD.load(dump, ds, d) for d in DESCS}; ep = eps["megaloc"]
    qpaths, mpaths = VI.image_paths(ds, dump, ep)
    print("images: missing map", sum(p is None for p in mpaths), "missing query", sum(p is None for p in qpaths), f"{time.time()-t0:.0f}s", flush=True)
    mpaths = [p if p is not None else next(x for x in mpaths if x is not None) for p in mpaths]   # missing map image: any placeholder (never a candidate in practice)
    have = np.array([p is not None for p in qpaths]); rows = np.flatnonzero(have); rows = rows[PART[0]::PART[1]]
    # ---- candidates: top-K over the FULL map per descriptor (global cosine; descriptors are L2-normalised)
    cand = {}
    for d in DESCS:
        e = eps[d]; M = torch.from_numpy(e.m.astype(np.float32)).cuda(0); out = np.empty((len(rows), K), np.int32)
        for s in range(0, len(rows), 4096):
            Q = torch.from_numpy(e.q[rows[s:s + 4096]].astype(np.float32)).cuda(0)
            out[s:s + 4096] = torch.topk(Q @ M.T, K, dim=1).indices.cpu().numpy()
        cand[d] = out; del M
    print("candidates", f"{time.time()-t0:.0f}s", flush=True)
    # ---- DINOv2 ViT-B/14 from the offline bundle
    bundle = find("/kaggle/input", "checkpoints"); bundle = os.path.dirname(bundle)
    sys.path.insert(0, os.path.join(bundle, "sources", "dinov2")); sys.path.insert(0, os.path.join(bundle, "sources"))
    from dinov2.models.vision_transformer import vit_base
    sd = torch.load(os.path.join(bundle, "checkpoints", "dinov2_vitb14_pretrain.pth"), map_location="cpu")
    mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1); std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)

    def load(p):
        im = Image.open(p).convert("RGB"); w, h = im.size; s = SHORT / min(w, h)
        im = im.resize((int(round(w * s / 14)) * 14, int(round(h * s / 14)) * 14), Image.BILINEAR)
        return torch.from_numpy(np.asarray(im, np.float32) / 255.).permute(2, 0, 1)

    models = []
    for g in range(ngpu):
        m = vit_base(patch_size=14, img_size=518, init_values=1.0, block_chunks=0); m.load_state_dict(sd.get("state_dict", sd), strict=False)
        models.append(m.eval().half().cuda(g))

    from concurrent.futures import ThreadPoolExecutor
    pool = ThreadPoolExecutor(min(48, (os.cpu_count() or 8)))                                     # JPEG decode + resize in parallel (CPU bound)

    @torch.no_grad()
    def feats(g, paths):
        x = torch.stack(list(pool.map(load, paths))); x = ((x - mean) / std).half().cuda(g)
        f = models[g].forward_features(x)["x_norm_patchtokens"]; return torch.nn.functional.normalize(f, dim=-1)

    # map patch tokens, replicated on every GPU
    chunks_ = list(range(0, len(mpaths), 128)); mfp = [None] * len(chunks_)

    def mworker(g):
        for ci in range(g, len(chunks_), ngpu): mfp[ci] = feats(g, mpaths[chunks_[ci]:chunks_[ci] + 128]).cpu()
    ths = [threading.Thread(target=mworker, args=(g,)) for g in range(ngpu)]; [t.start() for t in ths]; [t.join() for t in ths]
    mf = torch.cat(mfp); mfg = [mf.cuda(g) for g in range(ngpu)]
    print("map tokens", tuple(mf.shape), f"{time.time()-t0:.0f}s", flush=True)
    allc = np.stack([cand[d] for d in DESCS], 1)                          # (n, n_desc, K)
    mnn = np.zeros(allc.shape, np.float32); B = 64; jobs = queue.Queue()
    for s in range(0, len(rows), B): jobs.put(s)

    def worker(g):
        while True:
            try: s = jobs.get_nowait()
            except queue.Empty: return
            qf = feats(g, [qpaths[r] for r in rows[s:s + B]])
            for b in range(qf.shape[0]):
                cu, inv = np.unique(allc[s + b].ravel(), return_inverse=True)
                S = torch.einsum("pd,cqd->cpq", qf[b], mfg[g][torch.from_numpy(cu).long().cuda(g)])
                a1 = S.argmax(2); a2 = S.argmax(1)                         # q-patch -> m-patch, m-patch -> q-patch
                mutual = (torch.gather(a2, 1, a1) == torch.arange(S.shape[1], device=S.device)[None]).sum(1).float().cpu().numpy()
                mnn[s + b] = mutual[inv].reshape(allc.shape[1:])
            if s % (B * 100) == 0: print(f"  gpu{g} {s}/{len(rows)} {time.time()-t0:.0f}s", flush=True)

    th = [threading.Thread(target=worker, args=(g,)) for g in range(ngpu)]
    [t.start() for t in th]; [t.join() for t in th]
    os.makedirs("results", exist_ok=True)
    np.savez_compressed(f"results/safevpr_{ds.replace(':', '_')}_p{PART[0]}.npz", q_rows=rows, **{f"cand_{d}": cand[d] for d in DESCS},
                        **{f"mnn_{d}": mnn[:, i] for i, d in enumerate(DESCS)})
    print("DONE", len(rows), "queries", f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
