"""Dependence diagnosis (Entry 26): WHY does the map self-replay null fail for long off-map excursions?

For every nav_demo cache, compare the map self-replay null (held-out map traversal, own block masked) with the query's
off-map frames (labels used only for this diagnosis):
  marg     P(p <= u) of the top-1 half-map SelfCal p-value (p_q vs p_n) and of the anchored-R p-value (pR vs pRn)
  acf      lag-k autocorrelation of log p inside off-map runs (query) and inside null chunks
  runlen   mean length of runs with p <= 0.1
  fresh    share of disjoint H-frame segments whose max CPC log-odds (chain restarted at odds 1 at the segment start, the
           SC statistic) exceeds kappa: query off-map segments vs the null's own segments (the SC onset theorem says the
           query share is <= alpha if query segments are exchangeable with null segments)
  depth    share of off-map segments with a fresh-start exceedance, by depth (frames since the excursion started)
Usage: dep_diag.py <cache_dir> <ds> <desc,...> [--seeds 0,1,2] -> results/depdiag_<ds>.json"""
import sys, os, json, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hmm_fix import beta_em

U_GRID = (0.01, 0.05, 0.1, 0.2)
LAGS = (1, 5, 10, 25, 50)


def runs_of(mask, idx):
    """maximal runs (as index arrays into idx order) where mask[idx] is True"""
    m = mask[idx].astype(int); d = np.diff(np.r_[0, m, 0]); st, en = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    return [idx[a:b] for a, b in zip(st, en)]


def acf(series_list, lag):
    """pooled autocorrelation at `lag`, mean removed per series"""
    num = den = 0.0
    for x in series_list:
        if len(x) <= lag: continue
        x = x - x.mean(); num += float((x[lag:] * x[:-lag]).sum()); den += float((x * x).sum() * (len(x) - lag) / len(x))
    return num / den if den > 0 else float("nan")


def seg_max_fresh(ll, segs, p_in=0.01, p_out=0.01):
    out = []
    for sg in segs:
        pon, best = 0.5, -np.inf
        for i, t in enumerate(sg):
            pr = pon * (1 - p_out) + (1 - pon) * p_in if i > 0 else 0.5
            l = float(np.clip(np.log(pr / (1 - pr)) + ll[t], -50, 50)); pon = 1 / (1 + np.exp(-l)); best = max(best, l)
        out.append(best)
    return np.array(out)


def one(f, alpha=0.05):
    z = np.load(f, allow_pickle=True); H = int(z["H"]); excl = float(z["excl"])
    sid, k = z["q_sid"], z["q_k"]; seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    fl, ln = z["nchunk_flat"], z["nchunk_len"]; nch = np.split(fl, np.cumsum(ln)[:-1]) if len(ln) else []
    cl = lambda x: np.clip(np.nan_to_num(x, nan=1.0), 1e-6, 1)
    pn, prn, pq, pr = cl(z["p_n"]), cl(z["pRn"]), cl(z["p_q"]), cl(z["pR"])
    offm, cond = z["offm"], z["cond"]; MP, est, top = z["MP"], z["est_c"], z["top"]
    agree = np.linalg.norm(MP[top] - MP[est], axis=1) <= excl
    res = {"n_null": int(len(fl)), "n_off": int(offm.sum()), "n_null_seg": 0, "conds": {}}
    offruns = [r for idx in seqs for r in runs_of(offm, idx)]
    nseg = [ch[i:i + H] for ch in nch for i in range(0, len(ch) - H + 1, H)]; res["n_null_seg"] = len(nseg)
    # marginal tails
    res["marg_q"] = {str(u): float((pq[offm] <= u).mean()) for u in U_GRID}
    res["marg_n"] = {str(u): float((pn[fl] <= u).mean()) for u in U_GRID}
    res["margR_q"] = {str(u): float((pr[offm] <= u).mean()) for u in U_GRID}
    res["margR_n"] = {str(u): float((prn[fl] <= u).mean()) for u in U_GRID}
    lq = [np.log(pq[r]) for r in offruns]; lnl = [np.log(pn[c]) for c in nch]
    res["acf_q"] = {str(l): acf(lq, l) for l in LAGS}; res["acf_n"] = {str(l): acf(lnl, l) for l in LAGS}
    rl = lambda xs: float(np.mean([len(r) for x in xs for r in runs_of(x <= 0.1, np.arange(len(x)))] or [0]))
    res["runlen_q"], res["runlen_n"] = rl([pq[r] for r in offruns]), rl([pn[c] for c in nch])
    res["len_offrun_mean"] = float(np.mean([len(r) for r in offruns])) if offruns else 0.0
    res["len_nchunk_mean"] = float(np.mean([len(c) for c in nch])) if nch else 0.0
    # fresh-start segment statistic (SC) per condition
    ex_q, ex_n, depth = [], [], {}
    for cn in sorted(set(cond)):
        m = cond == cn; a1, _ = beta_em(pq[m]); a2, _ = beta_em(pr[m])
        llq = np.log(0.5 * (np.where(agree, a1 * pq ** (a1 - 1), a1) + (a2 * pr ** (a2 - 1)) ** (1.0 / H)))
        lln = np.log(0.5 * (np.maximum(a1 * pn ** (a1 - 1), a1) + (a2 * prn ** (a2 - 1)) ** (1.0 / H)))
        mxn = np.sort(seg_max_fresh(lln, nseg)); kk = int(np.ceil((1 - alpha) * (len(mxn) + 1)))
        kap = max(mxn[kk - 1] if kk <= len(mxn) else np.inf, 0.0)
        qsegs, dep = [], []
        for r in offruns:
            if not m[r[0]]: continue
            for i in range(0, len(r) - H + 1, H): qsegs.append(r[i:i + H]); dep.append(i)
        mxq = seg_max_fresh(llq, qsegs)
        e_q = mxq > kap; e_n = mxn > kap
        ex_q += e_q.tolist(); ex_n += e_n.tolist()
        for d, e in zip(dep, e_q):
            b = "0-9" if d < 10 else "10-49" if d < 50 else "50-199" if d < 200 else "200+"
            depth.setdefault(b, []).append(bool(e))
        res["conds"][cn] = {"kappa": float(kap), "fresh_q": float(e_q.mean()) if len(e_q) else float("nan"), "n_qseg": len(qsegs),
                            "a1": float(a1), "a2": float(a2), "marg_q01": float((pq[m & offm] <= 0.1).mean()) if (m & offm).any() else float("nan")}
    res["fresh_q"] = float(np.mean(ex_q)) if ex_q else float("nan"); res["fresh_n"] = float(np.mean(ex_n)) if ex_n else float("nan")
    res["depth"] = {b: [float(np.mean(v)), len(v)] for b, v in depth.items()}
    return res


def main():
    cdir, ds, descs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    seeds = [int(s) for s in sys.argv[sys.argv.index("--seeds") + 1].split(",")] if "--seeds" in sys.argv else [0, 1, 2]
    out = {}
    for desc in descs:
        for s in seeds:
            f = os.path.join(cdir, f"navcache_{ds.replace(':', '_')}_{desc}_s{s}.npz")
            if not os.path.exists(f): continue
            out[f"{desc}_s{s}"] = r = one(f)
            print(f"{ds}/{desc} s{s}: margq<=.1 {r['marg_q']['0.1']:.3f} (null {r['marg_n']['0.1']:.3f}) margR<=.1 {r['margR_q']['0.1']:.3f} "
                  f"(null {r['margR_n']['0.1']:.3f}) acf1/10/50 q {r['acf_q']['1']:.2f}/{r['acf_q']['10']:.2f}/{r['acf_q']['50']:.2f} "
                  f"n {r['acf_n']['1']:.2f}/{r['acf_n']['10']:.2f}/{r['acf_n']['50']:.2f} runlen q {r['runlen_q']:.1f} n {r['runlen_n']:.1f} "
                  f"| fresh q {r['fresh_q']:.3f} n {r['fresh_n']:.3f} depth {r['depth']}", flush=True)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/depdiag_{ds.replace(':', '_')}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
