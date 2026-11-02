"""SafeVPR'26 (Sier et al., arXiv 2605.28048) reproduced from the paper text for a DIRECT comparison on St Lucia (Entry 36).

Stage A (this script, CPU or GPU), per query frame t of every query traversal:
  matcher   T = 10 frame windows; every map window of T consecutive map frames is scored by the diagonal-mean cosine of the global
            descriptor (Sec. III-A); the top-5 windows are re-ranked by DTW on the cosine distance (band 2); winner c*_t (the map
            frame aligned with t);
  verifier  frozen DINOv2 patch tokens (final layer, no CLS; the paper uses ViT-L/14 at 224 x 224; offline weights available here:
            ViT-B/14 -> the backbone of this repo's earlier SafeVPR baseline, analysis/safevpr_mnn.py), for each of the T diagonal pairs
            (q_{t-k}, c*_{t-k}) the fraction of query patches that are mutual nearest neighbours AND pass Lowe's ratio test 0.9
            (ties rejected); score s_t = mean over the T pairs (Eq. 2).
Output: results/safevpr26_<ds>_<desc>.npz: per query frame cand (map row, -1 if no window), s, d (cosine score), q_rec.
Stage B (calibration with labels: Mondrian Learn-Then-Test, B = 5 quantile bins of s, delta = 0.05, Bonferroni per bin, Clopper-Pearson;
metrics FDR of accepted / TPR / validity) and our rules on the same frames: safevpr26_eval.py.
Usage: safevpr26.py <dump> <img_root> <ds> <desc> <bundle_root> [--T 10]"""
import sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def match(qd, md, T=10, top=5, band=2):
    """diagonal-mean cosine over T-frame windows + DTW re-rank -> map row aligned with every query frame (t >= T-1), and score"""
    S = qd @ md.T                                                      # (L, Nm)
    L, Nm = S.shape; cand = np.full(L, -1); score = np.full(L, np.nan)
    if L < T or Nm < T: return cand, score
    # diagonal means: D[t, j] = mean_k S[t - k, j - k], k = 0..T-1 (window ending at query t and map j)
    D = np.zeros((L - T + 1, Nm - T + 1))
    for k in range(T): D += S[k:L - T + 1 + k, k:Nm - T + 1 + k]
    D /= T
    for i in range(D.shape[0]):
        t = i + T - 1; js = np.argsort(-D[i])[:top]; best = (np.inf, -1)
        for j0 in js:                                                  # window map j0..j0+T-1 vs query t-T+1..t, DTW in a band
            Q = qd[t - T + 1:t + 1]; lo, hi = max(0, j0 - band), min(Nm, j0 + T + band); C = 1 - Q @ md[lo:hi].T
            n, m = C.shape; A = np.full((n + 1, m + 1), np.inf); A[0, 0] = 0.0
            for a in range(1, n + 1):
                for c in range(1, m + 1): A[a, c] = C[a - 1, c - 1] + min(A[a - 1, c], A[a, c - 1], A[a - 1, c - 1])
            cost = A[n, 1:].min() / n
            if cost < best[0]: best = (cost, lo + int(np.argmin(A[n, 1:])))
        cand[t], score[t] = best[1], float(D[i].max())
    return cand, score


def mnn_ratio(Fq, Fc, r=0.9):
    """fraction of query patches that are mutual nearest neighbours of the candidate patches and pass Lowe's ratio test"""
    S = Fq.astype(np.float32) @ Fc.astype(np.float32).T                 # (P, P)
    j1 = S.argmax(1); i1 = S.argmax(0)
    mutual = i1[j1] == np.arange(len(S))
    s2 = np.partition(S, -2, axis=1)[:, -2:]; first, second = s2[:, 1], s2[:, 0]
    ratio_ok = (second / np.maximum(first, 1e-9)) < r                  # cosine similarities: ratio of the 2nd to the 1st
    return float((mutual & ratio_ok).mean())


def main():
    dump, img_root, ds, desc, broot = sys.argv[1:6]; T = int(sys.argv[sys.argv.index("--T") + 1]) if "--T" in sys.argv else 10
    import torch, vprlib as V, topk_dump as TKD
    from PIL import Image
    import torchvision.transforms as TT
    sys.path.insert(0, os.path.join(broot, "sources", "dinov2"))
    from dinov2.models.vision_transformer import vit_base
    vit = vit_base(patch_size=14, img_size=518, init_values=1.0, block_chunks=0)
    sd = torch.load(os.path.join(broot, "checkpoints", "dinov2_vitb14_pretrain.pth"), map_location="cpu"); vit.load_state_dict(sd.get("state_dict", sd), strict=False); vit.eval()
    tx = TT.Compose([TT.Resize((224, 224), antialias=True), TT.ToTensor(), TT.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))])
    @torch.no_grad()
    def patches(paths, bs=16):
        out = []
        for a in range(0, len(paths), bs):
            x = torch.stack([tx(Image.open(p).convert("RGB")) for p in paths[a:a + bs]])
            f = torch.nn.functional.normalize(vit.forward_features(x)["x_norm_patchtokens"], dim=-1); out.append(f.numpy().astype(np.float16))
        return np.concatenate(out)
    ep = TKD.load(dump, ds, desc); meta = lambda r: np.load(os.path.join(dump, "meta", f"{ds}_{r}.npz"), allow_pickle=True)
    t0 = time.time(); ref = ep.ref; mnames = meta(ref)["names"]
    pf = os.path.join("results", f"patch_{ds}_{ref}.npy"); os.makedirs("results", exist_ok=True)
    if os.path.exists(pf): MPt = np.load(pf)
    else: MPt = patches([os.path.join(img_root, ref, f"{n}.jpg") for n in mnames]); np.save(pf, MPt)
    print(f"map patches {MPt.shape} {time.time() - t0:.0f}s", flush=True)
    md = ep.m.astype(np.float32); recs = np.asarray(ep.q_rec).astype(str)
    cand = np.full(len(recs), -1); s = np.full(len(recs), np.nan); dsc = np.full(len(recs), np.nan)
    for r in dict.fromkeys(recs):
        rows = np.flatnonzero(recs == r); qd = ep.q[rows].astype(np.float32)
        c, d = match(qd, md, T); cand[rows], dsc[rows] = c, d
        qn = meta(r)["names"]; assert len(qn) == len(rows)
        qf = os.path.join("results", f"patch_{ds}_{r}.npy")
        if os.path.exists(qf): QP = np.load(qf)
        else:
            QP = patches([os.path.join(img_root, r, f"{n}.jpg") for n in qn])
            if "--save-qpatch" in sys.argv: np.save(qf, QP)
        if "--patch-only" in sys.argv: print(f"{r}: patches {QP.shape}", flush=True); continue
        rho = np.full(len(rows), np.nan); memo = {}
        def pair(a, m):
            if (a, m) not in memo: memo[(a, m)] = mnn_ratio(QP[a], MPt[m])
            return memo[(a, m)]
        for i in range(T - 1, len(rows)):
            if c[i] < 0: continue
            vals = [pair(i - k, c[i] - k) for k in range(T) if c[i] - k >= 0]
            rho[i] = float(np.mean(vals)) if vals else np.nan
        s[rows] = rho; print(f"{r}: {len(rows)} queries, {time.time() - t0:.0f}s", flush=True)
    if "--patch-only" in sys.argv: return
    np.savez(os.path.join("results", f"safevpr26_{ds}_{desc}.npz"), cand=cand, s=s, d=dsc, q_rec=recs)


def holes():
    """map-hole protocol (Entry 36): for every seed's reduced map (navcache kidx) the matcher runs on the reduced map and the MNN
    verifier on the saved patch tokens -> results/safevpr26_<ds>_<desc>_s<seed>.npz (cand = FULL-map row)"""
    dump, ds, desc, navdir = sys.argv[2:6]; T = 10
    import glob, topk_dump as TKD
    ep = TKD.load(dump, ds, desc); recs = np.asarray(ep.q_rec).astype(str)
    MPt = np.load(os.path.join("results", f"patch_{ds}_{ep.ref}.npy"))
    QPs = {r: np.load(os.path.join("results", f"patch_{ds}_{r}.npy")) for r in dict.fromkeys(recs)}
    for nf in sorted(glob.glob(os.path.join(navdir, f"navcache_{ds}_{desc}_s*.npz"))):
        seed = int(nf.rsplit("_s", 1)[1][:-4]); z = np.load(nf, allow_pickle=True); kidx = z["kidx"]
        md = ep.m.astype(np.float32)[kidx]; cand = np.full(len(recs), -1); s = np.full(len(recs), np.nan)
        for r in dict.fromkeys(recs):
            rows = np.flatnonzero(recs == r); c, _ = match(ep.q[rows].astype(np.float32), md, T); QP = QPs[r]; memo = {}
            for i in range(T - 1, len(rows)):
                if c[i] < 0: continue
                vals = []
                for k in range(T):
                    if c[i] - k < 0: continue
                    key = (i - k, c[i] - k)
                    if key not in memo: memo[key] = mnn_ratio(QP[i - k], MPt[kidx[c[i] - k]])
                    vals.append(memo[key])
                s[rows[i]] = float(np.mean(vals)) if vals else np.nan
            cand[rows] = np.where(c >= 0, kidx[np.maximum(c, 0)], -1)
        np.savez(os.path.join("results", f"safevpr26_{ds}_{desc}_s{seed}.npz"), cand=cand, s=s, q_rec=recs); print(f"seed {seed} done", flush=True)


if __name__ == "__main__":
    holes() if sys.argv[1] == "--holes" else main()
