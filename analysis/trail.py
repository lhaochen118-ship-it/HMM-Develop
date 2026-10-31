"""TRAIL'26 baseline (Kloepfer & Wenzel, arXiv 2609.07373), reproduced from the paper text (d_g transition variant of
Table 2 / Eq. 51, reported on par with the local-feature CNN). Specs and choices: literature/BASELINES_2026.md.

Linear-chain CRF over the top-K (K = 10) MegaLoc candidates of every frame, no odometry:
  emission    phi_e(r, q)          = MLP_e(D * d(r) . d(q))                  8448 -> 64 -> 1   (LeakyReLU, dropout 0.1)
  transition  phi_tr(r_i, r_j, q_t, q_t-1) = MLP_tr(D d(r_i).d(r_j) . D d(q_t).d(q_t-1))   8448 -> 512 -> 512 -> 1,
              -inf if |x_i - x_j| > Delta = 3 excl (75 m for excl = 25 m)
  dustbin     state K: emission = learnable bias, phi_tr(i <- dust) = phi_e(r_i, q_t) (paper), phi_tr(dust <- .) = 0
  filter      log alpha_t(i) = phi_e(i) + logsumexp_j [phi_tr(i, j) + log alpha_t-1(j)], normalised (causal)
  location    P(s_i) = sum_j kappa(|x_i - x_j|) P(c_j), kappa(x) = exp(-(x / 0.8 excl)^4) 1(x <= excl) (Eq. 50, beta = 4)
  output      place = argmax_i P(s_i) over the candidates, confidence P(s_i*)
Training: leave-one-dataset-out (the held-out dataset never seen), stage A (emission, softmax over the K candidates,
positive = closest candidate if within excl) then stage C (end to end on sequences of 10 frames, loss of Eq. 9-10 on
the candidate set). Labels (query poses) are used for TRAINING only, on the other datasets.
Usage: trail.py <dump> <cache_dir> <topk_dir> --heldout <ds> [--seeds 0,1,2] [--stepsA 3000] [--stepsC 3000]
Output: results/trail_<ds>_megaloc_s<seed>.npz  place (n_q,) reduced-map row, conf (n_q,)."""
import sys, os, time, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
DSS = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
KC = 10


def load_ep(dump, ds):
    if ds.startswith("4s:"): return V.load_4seasons(dump, "megaloc", ds[3:])
    if ds == "boreas": return V.load_boreas(dump, "megaloc")
    return V.LOADERS[ds](dump, "megaloc")


def prep(dump, cdir, tkdir, ds, seed):
    """per-dataset arrays: query / map descriptors (fp16), candidates (n, K) reduced-map rows, sequences, positions, labels"""
    tag = ds.replace(":", "_"); z = np.load(os.path.join(cdir, f"navcache_{tag}_megaloc_s{seed}.npz"), allow_pickle=True)
    tk = np.load(os.path.join(tkdir, f"topk_{tag}_megaloc_s{seed}.npz")); ep = load_ep(dump, ds)
    hz = list(z["hz"]); MP = z["MP"]; one_d = MP.ndim == 1 or MP.shape[1] == 1
    pos = (MP[:, hz] if (not one_d and MP.shape[1] > 2) else MP).astype(np.float32).reshape(len(MP), -1)
    qp = z["q_pos"]; qp = (qp[:, hz] if (not one_d and qp.shape[1] > 2) else qp).astype(np.float32).reshape(len(qp), -1)
    sid, kk = z["q_sid"], z["q_k"]; seqs = [np.where(sid == s)[0][np.argsort(kk[sid == s])] for s in np.unique(sid)]
    return dict(q=ep.q.astype(np.float16), m=ep.m[z["kidx"]].astype(np.float16), cand=tk["idx"][:, :KC].astype(np.int64),
                seqs=seqs, pos=pos, qpos=qp, excl=float(z["excl"]), seed=seed, ds=ds)


def main():
    import torch, torch.nn as nn
    dump, cdir, tkdir = sys.argv[1], sys.argv[2], sys.argv[3]; held = arg("--heldout", "cmu")
    seeds = [int(x) for x in arg("--seeds", "0,1,2").split(",")]; stepsA, stepsC = arg("--stepsA", 3000), arg("--stepsC", 3000)
    dev = "cuda" if torch.cuda.is_available() else "cpu"; torch.manual_seed(0); rng = np.random.default_rng(0); t0 = time.time()
    tr_ds = arg("--train", ",".join(d for d in DSS if d != held)).split(",")
    train = [prep(dump, cdir, tkdir, d, 0) for d in tr_ds if d != held]
    print(f"held-out {held}: train on {[d['ds'] for d in train]} ({time.time() - t0:.0f}s)", flush=True)
    Dm = train[0]["q"].shape[1]

    class TRAIL(nn.Module):
        def __init__(s):
            super().__init__()
            s.e = nn.Sequential(nn.Linear(Dm, 64), nn.LeakyReLU(), nn.Dropout(0.1), nn.Linear(64, 1))
            s.tr = nn.Sequential(nn.Linear(Dm, 512), nn.LeakyReLU(), nn.Dropout(0.1), nn.Linear(512, 512), nn.LeakyReLU(), nn.Dropout(0.1), nn.Linear(512, 1))
            s.dust = nn.Parameter(torch.zeros(()))

        def emis(s, q, r):                      # q (B, D), r (B, K, D) -> (B, K)
            return s.e(Dm * q[:, None] * r).squeeze(-1)

        def trans(s, qa, qb, ra, rb):           # frame t (qa, ra (B,K,D)) <- frame t-1 (qb, rb) -> (B, K, K)
            x = (Dm * ra[:, :, None] * rb[:, None]) * (Dm * qa * qb)[:, None, None]
            return s.tr(x).squeeze(-1)

    net = TRAIL().to(dev)

    def gather(d, rows):
        q = torch.from_numpy(d["q"][rows].astype(np.float32)).to(dev)
        r = torch.from_numpy(d["m"][d["cand"][rows]].astype(np.float32)).to(dev)
        x = torch.from_numpy(d["pos"][d["cand"][rows]]).to(dev); y = torch.from_numpy(d["qpos"][rows]).to(dev)
        return q, r, x, y

    # ---- stage A: emission, softmax over the K candidates, positive = closest candidate within excl
    opt = torch.optim.AdamW([p for n, p in net.named_parameters() if n.startswith("e.") or n == "dust"], lr=1e-3, weight_decay=1e-3)
    for it in range(stepsA):
        d = train[it % len(train)]; rows = rng.integers(0, len(d["q"]), 56)
        q, r, x, y = gather(d, rows); dist = (x - y[:, None]).norm(dim=-1); pos_ = dist.argmin(1); okp = dist.min(1).values <= d["excl"]
        if not okp.any(): continue
        with torch.autocast(dev, dtype=torch.bfloat16, enabled=dev == "cuda"):
            lg = net.emis(q, r).float()
        loss = nn.functional.cross_entropy(lg[okp], pos_[okp]); opt.zero_grad(); loss.backward(); opt.step()
        if it % 500 == 0: print(f"  A {it} loss {loss.item():.3f}", flush=True)

    # ---- stage C: end to end on sequences of 10 frames
    def filt(q, r, x, excl, lo_prev=None, keep_graph=True):
        """one sequence chunk: q (T, D), r (T, K, D), x (T, K, d) -> list of log P(c_t) over K + dustbin"""
        T = len(q); out = []; Delta = 3 * excl
        with torch.autocast(dev, dtype=torch.bfloat16, enabled=dev == "cuda"):
            pe = net.emis(q, r).float()                                              # (T, K)
            ptr = net.trans(q[1:], q[:-1], r[1:], r[:-1]).float() if T > 1 else None   # (T-1, K, K)
        la = torch.cat([pe[0], net.dust.view(1)]) if lo_prev is None else lo_prev
        if lo_prev is None: la = la - torch.logsumexp(la, 0); out.append(la)
        for t in range(1 if lo_prev is None else 0, T):
            if t == 0: continue
            far = (x[t][:, None] - x[t - 1][None]).norm(dim=-1) > Delta
            M = torch.where(far, torch.full_like(ptr[t - 1], -1e4), ptr[t - 1])        # (K, K): i at t <- j at t-1
            M = torch.cat([M, pe[t][:, None]], 1)                                      # i <- dustbin: phi_e(r_i, q_t)
            M = torch.cat([M, torch.zeros(1, M.shape[1], device=dev)], 0)              # dustbin <- anything: 0
            em = torch.cat([pe[t], net.dust.view(1)])
            la = em + torch.logsumexp(M + la[None], 1); la = la - torch.logsumexp(la, 0); out.append(la)
        return out

    def kappa(dmat, excl):
        return torch.exp(-(dmat / (0.8 * excl)) ** 4) * (dmat <= excl)

    opt = torch.optim.AdamW(net.parameters(), lr=1e-4, weight_decay=1e-3)
    for it in range(stepsC):
        loss = 0.0
        for b in range(6):
            d = train[(it * 6 + b) % len(train)]; sq = d["seqs"][rng.integers(len(d["seqs"]))]
            if len(sq) < 10: continue
            a = rng.integers(0, len(sq) - 9); rows = sq[a:a + 10]; q, r, x, y = gather(d, rows)
            lps = filt(q, r, x, d["excl"])
            for t, lp in enumerate(lps):
                P = lp[:KC].exp(); kp = kappa((x[t][:, None] - x[t][None]).norm(dim=-1), d["excl"])
                Ps = (kp * P[None]).sum(1).clamp(1e-6, 1 - 1e-6); good = (x[t] - y[t]).norm(dim=-1) <= d["excl"]
                loss = loss - (torch.log(Ps) * good).sum() - (torch.log(1 - Ps) * ~good).sum()
        if not torch.is_tensor(loss): continue
        opt.zero_grad(); loss.backward(); opt.step()
        if it % 500 == 0: print(f"  C {it} loss {loss.item():.2f}", flush=True)
    print(f"trained ({time.time() - t0:.0f}s)", flush=True)

    # ---- inference on the held-out dataset (causal filter at every frame)
    net.eval(); os.makedirs("results", exist_ok=True)
    for seed in seeds:
        d = prep(dump, cdir, tkdir, held, seed); n = len(d["q"]); place = np.zeros(n, np.int64); conf = np.zeros(n, np.float32)
        with torch.no_grad():
            for sq in d["seqs"]:
                lo = None
                for a in range(0, len(sq), 512):
                    rows = sq[max(0, a - 1):a + 512] if a else sq[:512]
                    q, r, x, _ = gather(d, rows); lps = filt(q, r, x, d["excl"], lo_prev=lo)
                    if a: lps = lps                                                   # first returned = frame rows[1]
                    tgt = rows[1:] if a else rows
                    for t, lp in zip(range(len(tgt)), lps):
                        ti = t + (1 if a else 0); P = lp[:KC].exp()
                        kp = kappa((x[ti][:, None] - x[ti][None]).norm(dim=-1), d["excl"]); Ps = (kp * P[None]).sum(1)
                        k = int(Ps.argmax()); place[tgt[t]] = d["cand"][tgt[t], k]; conf[tgt[t]] = float(Ps[k])
                    lo = lps[-1]
        np.savez_compressed(f"results/trail_{held.replace(':', '_')}_megaloc_s{seed}.npz", place=place, conf=conf)
        err = np.linalg.norm(d["pos"][place] - d["qpos"], axis=1)
        print(f"  {held} s{seed}: TRAIL place correct (all frames) {(err <= d['excl']).mean():.3f}, top-1 {(np.linalg.norm(d['pos'][d['cand'][:, 0]] - d['qpos'], axis=1) <= d['excl']).mean():.3f} ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
