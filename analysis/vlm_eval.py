"""Evaluate the VPR-auditing baseline (vlm_audit.py) against every other rule ON THE SAME AUDITED FRAMES (every 5th query
frame): the paper's precision / coverage / FAR / S (positive = top-1 within excl of the true position), and the sequence
metrics of this project (recall, FL, segment FAR) plus the Kalman navigation error with fixes allowed only at audited
frames (so that every rule gets the same sparse fix opportunities). Labels only evaluate.
Usage: vlm_eval.py <cache_dir> <vlm_results_dir> <ds> <desc> [--seed 0]  -> results/vlmeval_<ds>_<desc>_s<seed>.json"""
import sys, os, glob, json, io, contextlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nav_rules as NR, nav_demo as N, cpc_geo as CG

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d


def main():
    cdir, vdir, ds, desc = sys.argv[1:5]; seed = arg("--seed", 0); tag = ds.replace(":", "_")
    z = np.load(os.path.join(cdir, f"navcache_{tag}_{desc}_s{seed}.npz"), allow_pickle=True); b = NR.base_parts(z)
    parts = [np.load(f) for f in sorted(glob.glob(os.path.join(vdir, f"vlm_{tag}_{desc}_s{seed}_p*.npz")))]
    rows = np.concatenate([p["rows"] for p in parts]); lo = np.concatenate([p["logodds"] for p in parts])
    o = np.argsort(rows); rows, lo = rows[o], lo[o]; n = len(z["top"])
    sub = np.zeros(n, bool); sub[rows] = True
    vacc = np.zeros(n, bool); vacc[rows] = np.where(np.isfinite(lo), lo > 0, True); vlo = np.full(n, -np.inf); vlo[rows] = np.nan_to_num(lo, nan=np.inf)
    with contextlib.redirect_stdout(io.StringIO()):
        R, X, _ = NR.base_rules(z, b)
        G, xg = CG.rules(z, b)
    for k, (_, a) in G.items(): R[k], X[k] = a, xg
    R["VPR-auditing (Qwen2.5-VL-7B)"] = vacc; X["VPR-auditing (Qwen2.5-VL-7B)"] = z["MP"][z["top"]]
    inm, offm, excl = z["inm"], z["offm"], b["excl"]
    cx = dict(q_pos=z["q_pos"], o_q=z["o_q"], real=bool(z["real"]), q_seqs=b["seqs"], hz=list(z["hz"]), seed=int(z["seed"]), head=ds == "nclt")
    out = {"ds": ds, "desc": desc, "seed": seed, "n_audited": int(sub.sum()), "rules": {}}
    for name, acc in R.items():
        a = acc & sub; xf = X[name]; err = np.linalg.norm(xf - z["q_pos"], axis=1)
        pos = inm & (err <= excl)                                       # a correct fix of this rule's reported place
        TP, FP = int((a & pos).sum()), int((a & ~pos).sum()); neg = sub & ~pos; TN = int((neg & ~a).sum())
        P = TP / max(TP + FP, 1); C = (TP + FP) / max(sub.sum(), 1); FAR = FP / max(FP + TN, 1)
        S = 3 / (1 / max(P, 1e-9) + 1 / max(C, 1e-9) + 1 / max(1 - FAR, 1e-9))
        m = N.rule_metrics(a, pos, inm & sub, offm & sub, b["seqs"], 1)
        e = N.track(a, xf, cx["q_pos"], cx["o_q"], cx["real"], cx["q_seqs"], cx["hz"], cx["seed"], cx["head"])
        out["rules"][name] = dict(P=P, C=C, FAR=FAR, S=S, recall=m["recall"], FL=m["FL"], err_mean=float(np.nanmean(e)))
    # VLM operating curve (label-free score: log p(true) - log p(false))
    th = np.unique(np.quantile(vlo[sub & np.isfinite(vlo)], np.linspace(0, 1, 40)))
    out["vlm_curve"] = [dict(thr=float(t), recall=float(((vlo > t) & sub & inm & (z["err_top"] <= excl)).sum() / max((sub & inm).sum(), 1)),
                             FL=float(((vlo > t) & sub & offm).sum() / max((sub & offm).sum(), 1))) for t in th]
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/vlmeval_{tag}_{desc}_s{seed}.json", "w"), indent=1)
    for k in ("VPR-auditing (Qwen2.5-VL-7B)", "CPC-SC+CS", "CPC-SC+SH", "Claxton24 MLP (labels)", "HMM off-map (labels)", "label threshold", "SelfCal frame", "accept all"):
        if k in out["rules"]:
            r = out["rules"][k]; print(f"{k:30s} P {r['P']:.3f} C {r['C']:.3f} FAR {r['FAR']:.3f} S {r['S']:.3f} | recall {r['recall']:.3f} FL {r['FL']:.4f} err {r['err_mean']:.1f}")


if __name__ == "__main__":
    main()
