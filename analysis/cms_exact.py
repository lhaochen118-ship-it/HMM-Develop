"""EXACT counterfactual statistics for CMS (Entry 29 audit fix).

cms.cms_stats builds the counterfactual from the stored top-100 list by deleting the entries inside the corridor B_t, so
the counterfactual route test sees only 100 - n_mask hypotheses (n_mask median 39-62) and anchor look-ups fall back to the
100th similarity of the UNmasked map. On the surgically altered map M \\ B_t the same statistic would use the top-100 of
M \\ B_t, i.e. the first 100 unmasked entries of the full ranking: the truncated counterfactual is biased towards higher
cost (the counterfactual winner sits at rank 58-72 of the 100, 7-21 % in the last 10 ranks, so ranks > 100 would often win)
-> anti-conservative. Here every frame keeps a LONG list (top-KL, KL = 300, GPU) and the counterfactual uses exactly the
first K = 100 unmasked entries for hypotheses, look-ups and the K-th-similarity fallback; the real statistic is unchanged
(top-100: identical to TAO'26 and to cms.cms_stats).
Usage: cms_exact.py <dump_dir> <cache_dir> <ds> <desc> --seeds s [--KL 300] [--rho-add 0] -> results/cms_<ds>_<desc>_s<seed>.npz"""
import sys, os, glob, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tao as TAO
import cms

KL = int(sys.argv[sys.argv.index("--KL") + 1]) if "--KL" in sys.argv else 300
SEEDS = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")] if "--seeds" in sys.argv else None
RHO_ADD = float(sys.argv[sys.argv.index("--rho-add") + 1]) if "--rho-add" in sys.argv else 0.0


def topk_long(q, Mk, K):
    """top-K of every query against the reduced map (GPU if available); returns idx, sim (sorted desc), row std"""
    n = len(q); I = np.zeros((n, K), np.int32); Sv = np.zeros((n, K), np.float32); sd = np.zeros(n, np.float32)
    try:
        import torch
        dev = "cuda" if torch.cuda.is_available() else None
    except Exception:
        torch, dev = None, None
    if dev:
        Mt = torch.from_numpy(Mk).to(dev)
        for a in range(0, n, 4096):
            S = torch.from_numpy(q[a:a + 4096]).to(dev) @ Mt.T; v, i = torch.topk(S, min(K, S.shape[1]), dim=1)
            I[a:a + 4096, :i.shape[1]], Sv[a:a + 4096, :i.shape[1]], sd[a:a + 4096] = i.cpu().numpy(), v.cpu().numpy(), S.std(1).cpu().numpy()
    else:
        for a in range(0, n, 2048):
            S = q[a:a + 2048] @ Mk.T; i = np.argpartition(-S, K - 1, axis=1)[:, :K]; v = np.take_along_axis(S, i, 1)
            o = np.argsort(-v, 1); I[a:a + 2048], Sv[a:a + 2048] = np.take_along_axis(i, o, 1), np.take_along_axis(v, o, 1)
            sd[a:a + 2048] = S.std(1, ddof=1)                          # unbiased, as torch.std on the GPU path (Entry 36 fix)
    return I, Sv, sd


def _costs(j, a0, c, dl, o_w, P, lo_arc, hi_arc, key_all, BIG, look, trim, delta, wapp, corridor=None):
    """route cost of hypotheses j (both directions) given per-window-frame look-up tables look[l] = (keys, sims, fallback).
    corridor (n_w, d) or None: anchor traces entering the corridor leave the route chunk from there on."""
    best = (np.inf, -1, None)
    for sgn in (1.0, -1.0):
        aa = a0[:, None] - sgn * dl[None, :]
        inside = (aa >= lo_arc[j][:, None]) & (aa <= hi_arc[j][:, None])
        q = np.empty(aa.shape + (P.shape[1],))
        for d in range(P.shape[1]): q[..., d] = np.interp((c[:, None] * BIG + aa).ravel(), key_all, P[:, d]).reshape(aa.shape)
        pc = o_w - o_w.mean(0); qc = q - q.mean(1, keepdims=True)
        if P.shape[1] == 1:
            res = np.abs(qc[..., 0] - pc[None, :, 0])
        else:
            a_ = (pc[None, :, 0] * qc[..., 0] + pc[None, :, 1] * qc[..., 1]).sum(1)
            b_ = (pc[None, :, 0] * qc[..., 1] - pc[None, :, 1] * qc[..., 0]).sum(1)
            th = np.arctan2(b_, a_); cs, sn = np.cos(th)[:, None], np.sin(th)[:, None]
            rx = cs * pc[None, :, 0] - sn * pc[None, :, 1]; ry = sn * pc[None, :, 0] + cs * pc[None, :, 1]
            res = np.sqrt((qc[..., 0] - rx) ** 2 + (qc[..., 1] - ry) ** 2)
        hub = np.where(res <= delta, 0.5 * res ** 2, delta * (res - 0.5 * delta)) / delta ** 2
        if corridor is not None:
            am = np.sqrt(((q[..., None, :] - corridor) ** 2).sum(-1)).min(-1) <= corridor_rho[0]
            inside = inside & ~np.maximum.accumulate(am, axis=1)
        m = max(1, int(np.ceil(trim * len(dl)))); geo = np.sort(np.where(inside, hub, 10.0), 1)[:, :m].mean(1)
        keys = c[:, None] * BIG + aa; app = np.empty(aa.shape)
        for l, (ks, ss, fb) in enumerate(look):
            p = np.searchsorted(ks, keys[:, l]); bs = np.full(len(j), fb); K = len(ks)
            for off in (-2, -1, 0, 1):
                pp = np.clip(p + off, 0, K - 1); okk = np.abs(ks[pp] - keys[:, l]) <= 4.0
                bs = np.where(okk, np.maximum(bs, ss[pp]), bs)
            app[:, l] = bs
        C = geo + wapp * (1.0 - app).mean(1); k = int(np.argmin(C))
        if C[k] < best[0]: best = (float(C[k]), int(j[k]), q[k])
    return best


corridor_rho = [40.0]


def cms_stats_exact(z, tkL, K=100, rho=None, ds=None, N=20, delta=8.0, trim=0.75, wapp=2.0):
    MP = z["MP"]; one_d = MP.ndim == 1 or MP.shape[1] == 1; hz = list(z["hz"]); excl = float(z["excl"])
    if rho is None: rho = cms.OFF_D.get((ds or "cmu").split(":")[0].split("_")[0], 40.0)
    corridor_rho[0] = rho
    P, cid, arc = TAO.route(MP[:, hz] if (not one_d and MP.shape[1] > 2) else MP)
    o_all = z["o_q"]; o_all = (o_all[:, hz] if (not one_d and o_all.shape[1] > 2) else o_all).astype(float)
    if one_d: o_all = o_all.reshape(-1, 1)
    IL, SL, sd = tkL["idx"].astype(np.int64), tkL["sim"].astype(np.float32), np.maximum(tkL["std"].astype(np.float32), 1e-6)
    BIG = 1e7; key_all = cid * BIG + arc
    starts = {c: arc[cid == c].min() for c in np.unique(cid)}; ends = {c: arc[cid == c].max() for c in np.unique(cid)}
    lo_arc = np.array([starts[c] for c in cid]); hi_arc = np.array([ends[c] for c in cid])
    n = len(IL); EPL = P[IL]                                                         # (n, KL, d)
    out = dict(cost=np.full(n, np.inf), cost_cf=np.full(n, np.inf), j=np.full(n, -1), j_cf=np.full(n, -1),
               z=np.full(n, -np.inf), z_cf=np.full(n, -np.inf), n_mask=np.zeros(n, np.int32), short=np.zeros(n, bool))
    I, Sm = IL[:, :K], SL[:, :K]
    d01 = np.linalg.norm(EPL[:, :K] - EPL[:, :1], axis=2); far = d01 > excl
    out["z"] = (Sm[:, 0] - np.where(far.any(1), np.where(far, Sm, -np.inf).max(1), Sm[:, -1])) / sd
    keyL = key_all[IL]
    def table(f, valid=None):
        """look-up table of frame f: its top-K (of the unmasked entries if valid is given): sorted keys, sims, fallback"""
        sel = np.arange(K) if valid is None else np.flatnonzero(valid)[:K]
        ks, ss = keyL[f, sel], SL[f, sel]; o = np.argsort(ks)
        return ks[o], ss[o], (float(SL[f, sel].min()) if len(sel) else -1.0), sel
    sid, kk = z["q_sid"], z["q_k"]
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(kk[idx])]; o = o_all[idx]
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        for i in range(len(idx)):
            t = idx[i]; w = np.arange(max(0, i - N + 1), i + 1)[::-1]
            if len(w) < 3: continue
            dl = cum[i] - cum[w]; fw = idx[w]
            look = [table(f)[:3] for f in fw]; j = I[t]
            cr, jr, A = _costs(j, arc[j], cid[j], dl, o[w], P, lo_arc, hi_arc, key_all, BIG, look, trim, delta, wapp)
            out["cost"][t], out["j"][t] = cr, jr
            # ---- exact surgery: every frame's list restricted to entries outside the corridor, then its first K
            inB = lambda X: np.sqrt(((X[..., None, :] - A) ** 2).sum(-1)).min(-1) <= rho
            val = [~inB(EPL[f]) for f in fw]
            out["n_mask"][t] = int((~val[0][:K]).sum())
            lt = [table(f, v) for f, v in zip(fw, val)]
            selt = lt[0][3]
            if len(selt) < K: out["short"][t] = True
            if len(selt) == 0: continue
            v0 = selt; s1c = SL[t, v0[0]]; farc = np.linalg.norm(EPL[t, v0] - EPL[t, v0[0]], axis=1) > excl
            sfc = SL[t, v0[farc]].max() if farc.any() else SL[t, v0[-1]]
            out["z_cf"][t] = (s1c - sfc) / sd[t]
            jc = IL[t, selt]
            cc, jcc, _ = _costs(jc, arc[jc], cid[jc], dl, o[w], P, lo_arc, hi_arc, key_all, BIG, [x[:3] for x in lt], trim, delta, wapp, corridor=A)
            out["cost_cf"][t], out["j_cf"][t] = cc, jcc
    out["rho"] = rho; out["KL"] = IL.shape[1]
    return out


def stats(z, tkL, **kw):
    """the exact counterfactual statistics: vectorised implementation (cms_vec.py, Entry 36; identical outputs, verified against
    the published cache) unless CMS_LOOP=1 (this module's per-frame loop)"""
    if os.environ.get("CMS_LOOP") == "1": return cms_stats_exact(z, tkL, **kw)
    import cms_vec
    return cms_vec.cms_stats_vec(z, tkL, **kw)


def main():
    import topk_dump as TKD
    dump, cdir, ds, desc = sys.argv[1:5]; tag = ds.replace(":", "_")
    files = sorted(glob.glob(os.path.join(cdir, f"navcache_{tag}_{desc}_s*.npz")))
    if SEEDS is not None: files = [f for f in files if int(f.rsplit("_s", 1)[1][:-4]) in SEEDS]
    os.makedirs("results", exist_ok=True); t0 = time.time()
    ep = TKD.load(dump, ds, desc); q, M = ep.q.astype(np.float32), ep.m.astype(np.float32)
    for f in files:
        out = f"results/cms_{os.path.basename(f)[9:]}"
        if os.path.exists(out): continue
        z = np.load(f, allow_pickle=True); kidx = z["kidx"]; assert len(z["top"]) == len(q)
        I, Sv, sd = topk_long(q, M[kidx], KL)
        agree = float((I[:, 0] == z["top"]).mean())
        rho = cms.OFF_D.get(ds.split(":")[0], 40.0) + RHO_ADD * float(z["excl"])
        st = stats(z, dict(idx=I, sim=Sv, std=sd), rho=rho, ds=ds)
        np.savez_compressed(out, **{k: (v.astype(np.float32) if isinstance(v, np.ndarray) and v.dtype == np.float64 else v) for k, v in st.items()})
        print(f"{out}: top-1 agreement {agree:.4f}, short lists {st['short'].mean():.4f}, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
