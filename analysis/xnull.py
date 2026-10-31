"""Cross-traversal (condition-matched) null for Boreas (Entry 27).

The map self-replay null uses the map's own images (one condition) and is stochastically STRONGER than off-map queries of
other conditions (Entry 26: the default point is conservative because of this), and it has ~10 short chunks. Boreas has
17 traversals that are neither the map nor a query (other dates / weather / light). Used as MAP-SIDE calibration data
(their poses belong to the mapping run's data, never to a deployment condition), each of their frames becomes a
leave-block-out pseudo-query exactly like the map null: its nearest map block is masked and it is kept only when it is
farther than off_d from the remaining (reduced) map. For every seed's reduced map (kidx of the nav_demo cache):
  p_x     SelfCal-AA p-value with the SAME half-map test as the queries' p_q (SelfCalTest on even blocks)
  pR_x    p-value of the anchored R statistic (cert_seq.running, ANCH) against the same map-null R distribution as pR
  top_x   top-1 (reduced-map row) with the frame's own block masked
  tk_idx / tk_sim   top-100 with the own block masked (for the TAO route cost of the pseudo-queries, CPC-SC-T)
  chunks  maximal runs of valid frames inside one masked block, per traversal (time order) = pseudo off-map excursions
  odometry: the traversal's REAL wheel + gyro odometry (cert_seq.odometry_wheel), as the queries
Heavy statistics run on the GPU (selfcal.qm_stats torch backend, SELFCAL_DEVICE=cuda). One job = one descriptor and a
list of seeds: the 17 traversals are loaded once and reused for every seed.
Usage: xnull.py <dump> <desc> <cache_dir> [--seeds 0,1,2] -> results/xnull_boreas_<desc>_s<seed>.npz"""
import sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V, selfcal as SC
from sc_eval import CFG
from cert_seq import running, chunks, odometry_wheel

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
H, A = 10, 0.05


class _Ep:                                        # minimal episode for odometry_wheel
    def __init__(s, pos, dmi, gyro): s.q_pos, s.q_dmi, s.q_gyro = pos, dmi, gyro


def calib_traversals(dump, desc, ref="boreas-2020-11-26-13-58"):
    seqs = sorted(f[7:-4] for f in os.listdir(os.path.join(dump, "meta")) if f.startswith("boreas_")
                  and os.path.isfile(os.path.join(dump, desc, f[:-4] + ".npy")))
    cal = [s for s in seqs if s != ref and s not in V.BOREAS_Q]
    from concurrent.futures import ThreadPoolExecutor                  # /kaggle/input is a slow network FS: read all files concurrently
    rd = lambda s: (dict(np.load(os.path.join(dump, "meta", f"boreas_{s}.npz"), allow_pickle=True)), np.load(os.path.join(dump, desc, f"boreas_{s}.npy")))
    with ThreadPoolExecutor(16) as ex: loaded = list(ex.map(rd, cal))
    X, P, sid, k, dmi, gy = [], [], [], [], [], []
    for i, (m, x) in enumerate(loaded):
        X.append(x); P.append(m["C"][:, :2]); sid.append(np.full(len(x), i)); k.append(np.arange(len(x))); dmi.append(m["dmi"]); gy.append(m["gyro_yaw"])
    cat = np.concatenate; X, P, sid, k = cat(X).astype(np.float32), cat(P), cat(sid), cat(k)
    o = odometry_wheel(_Ep(P, cat(dmi), cat(gy)), sid, k)
    return cal, X, P, sid, k, o


def main():
    dump, desc, cdir = sys.argv[1], sys.argv[2], sys.argv[3]
    seeds = [int(x) for x in arg("--seeds", "0,1,2").split(",")]; c = CFG["cmu"]; K = 100; t0 = time.time()
    ep = V.load_boreas(dump, desc); cal, X, PX, sid, kk, OX = calib_traversals(dump, desc)
    print(f"boreas/{desc}: {len(cal)} calibration traversals, {len(X)} frames ({time.time() - t0:.0f}s)", flush=True)
    nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
    import torch
    dev = "cuda" if torch.cuda.is_available() else None
    for seed in seeds:
        z = np.load(os.path.join(cdir, f"navcache_boreas_{desc}_s{seed}.npz"), allow_pickle=True)
        kidx = z["kidx"]; M, MP = ep.m[kidx].astype(np.float32), ep.m_pos[kidx]; assert np.allclose(MP, z["MP"])
        mu = M.mean(0, keepdims=True); Mc = nrm(M - mu); Xc = nrm(X - mu)
        args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
        Nr, Nc = SC.map_null(M, MP, *args, stride=1), SC.map_null(Mc, MP, *args, stride=1)
        bidM, _ = V.map_cells(MP, c["block"]); half = bidM % 2 == 0
        sub = lambda d, m: {kk_: np.where(m, v, np.nan) for kk_, v in d.items()}
        th = SC.SelfCalTest(SC.pack(sub(Nr, half), sub(Nc, half))); p_n = th.pvalue(**SC.pack(Nr, Nc))
        fl0 = z["nchunk_flat"]; print(f"  seed {seed}: map-null p_n reproduces the cache: max |diff| {np.nanmax(np.abs(np.nan_to_num(p_n[fl0], nan=1) - np.nan_to_num(z['p_n'][fl0], nan=1))):.2e}", flush=True)
        # map-null R distribution (exactly as nav_demo: noise-free map odometry, held-out half, chunks inside one block)
        null_ok = np.isfinite(Nr["maxsim"]) & np.isfinite(Nc["z_far"]) & ~half
        Rn0 = np.full(len(MP), np.nan)
        for ch in chunks(np.arange(len(MP)), null_ok, bidM): Rn0[ch] = running(p_n, Nr["top"], np.array(ch), MP.astype(float), MP, "ANCH", c["excl"], 5.0, H)
        rn = np.sort(Rn0[np.isfinite(Rn0)])
        # calibration pseudo-queries (leave-block-out, off_d from the remaining map)
        Fr = SC.lobo_stats(M, MP, c["block"], c["off_d"], X, PX, c["cell"], c["excl"], c["k"])
        Fc = SC.lobo_stats(Mc, MP, c["block"], c["off_d"], Xc, PX, c["cell"], c["excl"], c["k"])
        p_x = th.pvalue(**SC.pack(Fr, Fc)); ok = np.isfinite(p_x) & np.isfinite(Fr["maxsim"]) & np.isfinite(Fc["z_far"])
        from scipy.spatial import cKDTree
        bx = bidM[cKDTree(MP).query(PX)[1]]                                     # the masked block of every pseudo-query
        top_x = np.where(ok, np.nan_to_num(Fr["top"], nan=-1), -1).astype(int)
        flat, lens, R_x = [], [], np.full(len(X), np.nan)
        for s in np.unique(sid):
            order = np.where(sid == s)[0]; order = order[np.argsort(kk[order])]
            for ch in chunks(order, ok, bx):
                ch = np.array(ch)
                if len(ch) < 2: continue
                R_x[ch] = running(p_x, top_x, ch, OX, MP, "ANCH", c["excl"], 5.0, H); flat.append(ch); lens.append(len(ch))
        flat = np.concatenate(flat) if flat else np.zeros(0, int)
        pR_x = (1 + len(rn) - np.searchsorted(rn, R_x, side="left")) / (1 + len(rn))
        # top-100 with the own block masked (route cost of the pseudo-queries)
        tki = np.zeros((len(flat), K), np.int16); tks = np.zeros((len(flat), K), np.float16)
        if dev:
            Mt = torch.from_numpy(M).to(dev); bM = torch.from_numpy(bidM).to(dev)
        for a in range(0, len(flat), 4096):
            r = flat[a:a + 4096]
            if dev:
                S = torch.from_numpy(X[r]).to(dev) @ Mt.T; S[torch.from_numpy(bx[r]).to(dev)[:, None] == bM[None]] = -1e4
                v, i = torch.topk(S, K, dim=1); tki[a:a + len(r)] = i.cpu().numpy(); tks[a:a + len(r)] = v.cpu().numpy()
            else:
                S = X[r] @ M.T; S[bx[r][:, None] == bidM[None]] = -1e4; i = np.argsort(-S, 1)[:, :K]
                tki[a:a + len(r)] = i; tks[a:a + len(r)] = np.take_along_axis(S, i, 1)
        os.makedirs("results", exist_ok=True)
        np.savez_compressed(f"results/xnull_boreas_{desc}_s{seed}.npz", flat=flat, lens=np.array(lens), p_x=p_x[flat], pR_x=pR_x[flat],
                            top_x=top_x[flat], R_x=R_x[flat], o_x=OX[flat].astype(np.float32), pos_x=PX[flat].astype(np.float32),
                            trav=sid[flat], tk_idx=tki, tk_sim=tks, n_valid=int(ok.sum()), cal=np.array(cal))
        print(f"  seed {seed}: {int(ok.sum())} pseudo off-map frames, {len(lens)} chunks (mean {np.mean(lens) if lens else 0:.0f}), "
              f"P(p_x<=.05) {np.mean(p_x[flat] <= .05):.3f} vs map null {np.mean(p_n[z['nchunk_flat']] <= .05):.3f} ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
