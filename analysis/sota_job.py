"""External baselines on one run of a fresh test group (same navcache, same protocol as the OWF rules; 2026-11-05):
  TAO26     Lu & Tanaka arXiv 2607.04745 (trajectory-anchor optimisation over the top-100 retrievals, analysis/tao.py), map-out threshold
            tau_OOD = mean + 3 std of the winner cost on correctly localised frames of the two easiest conditions (LABELS, as in the paper);
  Xu21      Xu et al. RA-L'21 topometric HMM with an off-map state (cache fields acc_h / x_hmm; T, k tuned WITH labels in nav_demo);
  Claxton24 Claxton et al. RA-L'24-style MLP integrity monitor trained WITH labels on the two easiest conditions;
  top1      accept every top-1 retrieval; oracle: accept exactly the correct top-1 (upper reference).
The top-100 list is computed here (GPU matmul when available, analysis/topk_dump.py logic) from the descriptor dumps.
Usage (kernel runner): sota_job.py <cache_dir> <dump_dir> <ds> <desc> <seed> [--tag t55] -> results/sota_<ds>_<desc>_s<seed>_<tag>.json"""
import sys, os, json, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)


def topk(Q, M, K=100):
    try:
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        Mt = torch.tensor(M, dtype=torch.float32, device=dev).T; I, S = [], []
        for a in range(0, len(Q), 4096):
            s = torch.tensor(Q[a:a + 4096], dtype=torch.float32, device=dev) @ Mt
            v, i = torch.topk(s, min(K, s.shape[1]), dim=1); I.append(i.cpu().numpy()); S.append(v.cpu().numpy())
        return np.concatenate(I).astype(np.int32), np.concatenate(S).astype(np.float16)
    except ImportError:
        S = Q.astype(np.float32) @ M.T.astype(np.float32); i = np.argpartition(-S, K - 1, axis=1)[:, :K]
        v = np.take_along_axis(S, i, 1); o = np.argsort(-v, 1)
        return np.take_along_axis(i, o, 1).astype(np.int32), np.take_along_axis(v, o, 1).astype(np.float16)


def main():
    cdir, dump, ds, desc, seed = sys.argv[1:6]; seed = int(seed)
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "sota"
    sys.argv = sys.argv[:1]
    import owf, nav_demo as N, tao as TAO, position_audit as PA
    t0 = time.time()
    z, Q, M = owf.load_run(cdir, dump, ds, desc, seed)
    z = dict(z); idx, sim = topk(np.asarray(Q), np.asarray(M)); tk = dict(idx=idx, sim=sim)
    excl = float(z["excl"]); MP = z["MP"]; qp = z["q_pos"]; H = int(z["H"])
    sid, k = z["q_sid"], z["q_k"]; seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    hz = list(z["hz"]); dsn = ds.split(":")[0]; segs = PA.seg_classes(z, PA.OFF_D[dsn])
    out = {"ds": ds, "desc": desc, "seed": seed, "variants": {}}
    r = TAO.tao(z, tk); tau = TAO.tao_threshold(r["cost"], z["good"], z["bsel"])
    xt = np.asarray(r["x_fix"], float)
    if MP.ndim > 1 and xt.ndim > 1 and xt.shape[1] < MP.shape[1]:     # TAO works in the horizontal plane: embed (vertical from the map row)
        x3 = MP[np.maximum(r["j"], 0)].astype(float).copy(); x3[:, hz] = xt; xt = x3
    rules = {"TAO26": (np.isfinite(r["cost"]) & (r["cost"] <= tau) & (r["j"] >= 0), xt)}
    bad_top = z["offm"] | (z["err_top"] > excl)
    rules["Claxton24"] = (N.claxton_rule(z["srt10"], z["Smean"], z["Sstd"], z["bsel"], z["good"], bad_top, int(z["seed"])), MP[z["top"]])
    rules["Xu21"] = (z["acc_h"].astype(bool), z["x_hmm"])
    rules["top1"] = (np.ones(len(qp), bool), MP[z["top"]]); rules["oracle"] = (z["good"].astype(bool), MP[z["top"]])
    q2 = qp if qp.ndim > 1 else qp[:, None]
    for name, (acc, xf) in rules.items():
        xf = np.asarray(xf, float); xf2 = xf if xf.ndim > 1 else xf[:, None]
        gd = z["inm"] & (np.linalg.norm(np.nan_to_num(xf2, nan=1e9) - q2, axis=1) <= excl)
        m = N.rule_metrics(acc, gd, z["inm"], z["offm"], seqs, H)
        e = N.track(acc, np.nan_to_num(xf, nan=0.0), qp, z["o_q"], bool(z["real"]), seqs, hz, seed, dsn == "nclt")
        pos = {c: [int(sum(bool(acc[g].any()) for g, cc in segs if cc == c)), int(sum(1 for _, cc in segs if cc == c))] for c in PA.CLASSES}
        out["variants"][name] = dict(recall=m["recall"], FL=m["FL"], seg_FAR=m["seg_FAR"], err_mean=float(np.nanmean(e)), pos=pos)
        print(f"{ds}/{desc} s{seed} {name:10s} recall {m['recall']:.3f} segFAR {m['seg_FAR']:.4f} err {np.nanmean(e):.1f}", flush=True)
    out["secs"] = time.time() - t0; os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/sota_{ds.replace(':', '_')}_{desc}_s{seed}_{tag}.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
