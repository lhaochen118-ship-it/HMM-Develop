"""SafeVPR'26 stage B (calibration with labels) and the direct comparison on St Lucia (Entry 36).

SafeVPR protocol (Sier et al. 2026, Sec. III-IV, read in full): one held-out condition at a time; the thresholds are calibrated on
the LABELLED queries of the other conditions; Mondrian Learn-Then-Test: calibration queries binned into B = 5 quantile bins of the
verifier score s; per bin a grid of M = 5 thresholds (quantiles of s in the bin), each tested with the Clopper-Pearson upper bound of
its accepted-set FDR at confidence 1 - delta / (B M) (Bonferroni over bins and grid), delta = 0.05; the most permissive valid
threshold per bin is kept (none valid: the bin abstains). Test query accepted iff s >= threshold of its bin. A query is correct iff the
matched map frame is within `tol` m (25 m, the usual St Lucia VPR tolerance; the paper states none). Metrics per held-out condition:
accepted-set FDR, TPR (accepted correct / correct candidates), valid iff FDR <= alpha (empty accepted set: vacuously valid).
Our rules on the SAME query frames (no map hole, oc_curves frames dump of the no-hole St Lucia runs): a frame is "accepted" iff the
rule reports it; FDR = wrong reports / reports; TPR = correct reports / frames whose reported place is correct; no label is used.
Usage: safevpr26_eval.py <safevpr26_npz> <dump> <frames_npz (oc_curves --dump-frames, no-hole run)> <navcache_npz> [--alpha 0.05,0.10]
       [--tol 25] [--rules a,b] -> results/safevpr26_eval_<desc>.json"""
import sys, os, json
import numpy as np
from scipy.stats import beta as Beta


def cp_upper(f, n, conf):
    return 1.0 if n == 0 else float(Beta.ppf(conf, f + 1, n - f)) if f < n else 1.0


def ltt_mondrian(s_cal, y_cal, alpha, delta=0.05, B=5, M=5):
    """per-bin thresholds (bin edges from calibration quantiles of s)"""
    ok = np.isfinite(s_cal); s_cal, y_cal = s_cal[ok], y_cal[ok]
    edges = np.quantile(s_cal, np.linspace(0, 1, B + 1)); edges[0], edges[-1] = -np.inf, np.inf
    thr = np.full(B, np.inf); conf = 1 - delta / (B * M)
    for b in range(B):
        m = (s_cal >= edges[b]) & (s_cal < edges[b + 1]); sb, yb = s_cal[m], y_cal[m]
        if not len(sb): continue
        for lam in sorted(np.quantile(sb, np.linspace(0, 0.8, M))):     # most permissive first
            acc = sb >= lam; n = int(acc.sum()); f = int((acc & ~yb).sum())
            if cp_upper(f, n, conf) <= alpha: thr[b] = lam; break
    return edges, thr


def apply(s, edges, thr):
    b = np.clip(np.searchsorted(edges, s, side="right") - 1, 0, len(thr) - 1)
    return np.isfinite(s) & (s >= thr[b])


def main():
    sv, dump, frf, nvf = sys.argv[1:5]
    alphas = [float(x) for x in (sys.argv[sys.argv.index("--alpha") + 1] if "--alpha" in sys.argv else "0.05,0.10").split(",")]
    tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 25.0
    S = np.load(sv, allow_pickle=True); z = np.load(nvf, allow_pickle=True); fr = np.load(frf, allow_pickle=True)
    MP, q_pos = np.asarray(z["MP"], float), np.asarray(z["q_pos"], float); kidx = z["kidx"]
    recs = np.asarray(S["q_rec"]).astype(str); cand = S["cand"]; s = S["s"].astype(float)
    # SafeVPR's candidate is a FULL-map row; positions from the full map (no hole: kidx = all rows)
    full_pos = np.zeros((int(kidx.max()) + 1, MP.shape[1])); full_pos[kidx] = MP
    y = (cand >= 0) & (np.linalg.norm(full_pos[np.maximum(cand, 0)] - q_pos, axis=1) <= tol)
    rows = []
    for a in alphas:
        res = []
        for h in dict.fromkeys(recs):
            te, ca = recs == h, recs != h
            e, t = ltt_mondrian(s[ca], y[ca], a); acc = apply(s[te], e, t); yt = y[te]
            n = int(acc.sum()); fdr = float((acc & ~yt).sum() / n) if n else 0.0; tpr = float((acc & yt).sum() / max(yt.sum(), 1))
            res.append((h, fdr, tpr, n, float((acc & yt).sum() / te.sum())))
        r = np.array([x[1:] for x in res], float)
        rows.append(dict(method=f"SafeVPR'26 (MNN DINOv2-B/14, Mondrian LTT, labels)", alpha=a, valid=f"{int((r[:, 0] <= a).sum())}/{len(r)}",
                         fdr=float(r[r[:, 2] > 0, 0].mean()) if (r[:, 2] > 0).any() else 0.0, tpr=float(r[:, 1].mean()), recall=float(r[:, 3].mean()),
                         labels="calibration conditions", per=[(x[0], x[1], x[2], x[3]) for x in res]))
    names = list(fr["names"]); accs = dict(zip(names, fr["acc"])); xfs = dict(zip(names, fr["xf"]))
    for rule in (sys.argv[sys.argv.index("--rules") + 1].split(",") if "--rules" in sys.argv else [n for n in names if "CST" in n or "SH+G+NGRr" in n]):
        if rule not in accs: continue
        acc, xf = accs[rule].astype(bool), np.asarray(xfs[rule], float)
        ok = np.linalg.norm(xf[:, :q_pos.shape[1]] - q_pos, axis=1) <= tol; res = []
        for h in dict.fromkeys(recs):
            te = recs == h; a_, o_ = acc[te], ok[te]; n = int(a_.sum())
            res.append((h, float((a_ & ~o_).sum() / n) if n else 0.0, float((a_ & o_).sum() / max(o_.sum(), 1)), n, float((a_ & o_).sum() / te.sum())))
        r = np.array([x[1:] for x in res], float)
        for a in alphas:
            rows.append(dict(method=rule, alpha=a, valid=f"{int((r[:, 0] <= a).sum())}/{len(r)}", fdr=float(r[r[:, 2] > 0, 0].mean()) if (r[:, 2] > 0).any() else 0.0,
                             tpr=float(r[:, 1].mean()), recall=float(r[:, 3].mean()), labels="none", per=[(x[0], x[1], x[2], x[3]) for x in res]))
    os.makedirs("results", exist_ok=True); desc = os.path.basename(sv).rsplit("_", 1)[1][:-4]
    json.dump(dict(rows=rows, tol=tol), open(f"results/safevpr26_eval_{desc}.json", "w"), indent=1)
    for r in rows: print(f"{r['method'][:40]:40s} a={r['alpha']:.2f} valid {r['valid']} FDR {r['fdr']:.4f} TPR {r['tpr']:.3f} recall {r['recall']:.3f}")


if __name__ == "__main__":
    main()
