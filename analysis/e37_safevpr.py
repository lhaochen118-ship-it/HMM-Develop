"""Entry 37: direct comparison with SafeVPR'26 on St Lucia for every descriptor (map-hole protocol of Entry 36: 5 query traversals x
5 hole layouts = 25 held-out conditions per descriptor), with the paper's verifier backbone (DINOv2 ViT-L/14, 224 x 224; patch tokens
from automation/make_stlucia_kernel.py, stage A safevpr26.py --holes --tag vitl).
SafeVPR'26 (labels): for each held-out condition (query traversal h of seed s) Mondrian Learn-Then-Test calibrated on the LABELLED
queries of the other 4 traversals of the same seed (safevpr26_eval.ltt_mondrian: B = 5 bins, M = 5 thresholds, delta = 0.05,
Clopper-Pearson, Bonferroni). Ours (no label): a frame is accepted iff the rule reports it (oc_curves --dump-frames of the same run).
Metrics (SafeVPR's): accepted-set FDR (tolerance 25 m), TPR = correct accepted / correct candidates, recall = correct accepted / frames;
a condition is valid iff FDR <= alpha.
Usage: e37_safevpr.py <results_dir> <out.json> [--descs a,b] [--seeds 0,1,2,3,4] [--tag vitl] [--alpha 0.05,0.10] [--tol 25]
  results_dir holds safevpr26_stlucia_<desc>_<tag>_s<seed>.npz, frames_stlucia_<desc>_e37_s<seed>.npz, navcache_stlucia_<desc>_s<seed>.npz"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safevpr26_eval import ltt_mondrian, apply

RULES = ["CMS-CPC/H+SH+G+NGRr", "CMS-CPC/H+CSTJS+G+NGRr", "CMS-CPC/H+SH+CSTJS+G+NGRr", "CMS-CPC/H+CSTF+G+NGRr", "CMS-CPC/H+CSTJs+G+NGRr",
         "CMS-CPC/H+SH+CSTJs+G+NGRr", "CPC-SC-T0.5+SH", "CMS-CPCW/H+SH+NGRr"]


def opt(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def conds_of_run(rd, desc, seed, tag, alphas, tol):
    """per held-out condition of one run: {method: {alpha: (fdr, tpr, n_acc, recall)}}"""
    sv = np.load(os.path.join(rd, f"safevpr26_stlucia_{desc}_{tag}_s{seed}.npz"), allow_pickle=True)
    z = np.load(os.path.join(rd, f"navcache_stlucia_{desc}_s{seed}.npz"), allow_pickle=True)
    fr = np.load(os.path.join(rd, f"frames_stlucia_{desc}_e37_s{seed}.npz"), allow_pickle=True)
    MP, q_pos, kidx = np.asarray(z["MP"], float), np.asarray(z["q_pos"], float), z["kidx"]
    recs = np.asarray(sv["q_rec"]).astype(str); cand = sv["cand"]; s = sv["s"].astype(float)
    full = np.zeros((int(max(kidx.max(), cand.max())) + 1, MP.shape[1])); full[kidx] = MP     # cand = FULL-map row, always inside kidx
    assert np.all(np.isin(cand[cand >= 0], kidx))
    y = (cand >= 0) & (np.linalg.norm(full[np.maximum(cand, 0)] - q_pos, axis=1) <= tol)
    out = {}
    for h in dict.fromkeys(recs):
        te, ca = recs == h, recs != h; r = {}
        for a in alphas:
            e, t = ltt_mondrian(s[ca], y[ca], a); acc = apply(s[te], e, t); yt = y[te]; n = int(acc.sum())
            r.setdefault("SafeVPR'26", {})[a] = (float((acc & ~yt).sum() / n) if n else 0.0, float((acc & yt).sum() / max(yt.sum(), 1)), n,
                                                float((acc & yt).sum() / te.sum()))
        names = list(fr["names"])
        for rule in RULES:
            if rule not in names: continue
            i = names.index(rule); acc = fr["acc"][i].astype(bool)[te]; xf = np.asarray(fr["xf"][i], float)[te]
            ok = np.linalg.norm(xf[:, :q_pos.shape[1]] - q_pos[te], axis=1) <= tol; n = int(acc.sum())
            r[rule] = {"-": (float((acc & ~ok).sum() / n) if n else 0.0, float((acc & ok).sum() / max(ok.sum(), 1)), n, float((acc & ok).sum() / te.sum()))}
        out[f"s{seed}:{h}"] = r
    return out


def main():
    rd, of = sys.argv[1], sys.argv[2]
    descs = opt("--descs", "cosplace,netvlad,megaloc,salad,mixvpr,dinov2").split(","); seeds = [int(x) for x in opt("--seeds", "0,1,2,3,4").split(",")]
    tag = opt("--tag", "vitl"); alphas = [float(x) for x in opt("--alpha", "0.05,0.10").split(",")]; tol = float(opt("--tol", "25"))
    rows = []
    for desc in descs:
        C = {}
        for s in seeds:
            if os.path.exists(os.path.join(rd, f"safevpr26_stlucia_{desc}_{tag}_s{s}.npz")) and os.path.exists(os.path.join(rd, f"frames_stlucia_{desc}_e37_s{s}.npz")):
                C.update(conds_of_run(rd, desc, s, tag, alphas, tol))
        if not C: continue
        meths = {m_: list(v) for c in C.values() for m_, v in c.items()}
        for m_, als in meths.items():
            for a in (alphas if m_ == "SafeVPR'26" else ["-"]):
                r = np.array([C[c][m_][a] for c in C if m_ in C[c]], float)
                for a_ in ([a] if m_ == "SafeVPR'26" else [alphas[0]]):
                    rows.append(dict(desc=desc, method=("SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels)" if m_ == "SafeVPR'26" else m_), alpha=a_,
                                     valid=f"{int((r[:, 0] <= a_).sum())}/{len(r)}", fdr=float(r[r[:, 2] > 0, 0].mean()) if (r[:, 2] > 0).any() else 0.0,
                                     tpr=float(r[:, 1].mean()), recall=float(r[:, 3].mean()), labels=("calibration traversals" if m_ == "SafeVPR'26" else "none"),
                                     n_cond=len(r)))
    note = (f"St Lucia, 10 m frames, map 100909_0845, 5 query traversals x {len(seeds)} hole layouts (30 % map blocks removed) per descriptor; SafeVPR'26 "
            f"calibrated with labels on the other 4 traversals of the same layout; verifier DINOv2 ViT-L/14 (224 x 224, as the paper); our rules "
            f"label-free (validity of our rules is checked at alpha = {alphas[0]}); FDR = wrong accepted / accepted (tolerance {tol:g} m)")
    json.dump(dict(rows=rows, note=note), open(of, "w"), indent=1)
    for r in rows: print(f"{r['desc']:9s} {r['method'][:44]:44s} a={r['alpha']:.2f} valid {r['valid']:6s} FDR {r['fdr']:.4f} TPR {r['tpr']:.3f} recall {r['recall']:.3f}")


if __name__ == "__main__":
    main()
