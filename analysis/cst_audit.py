"""Audit of (S3-T), the assumption behind Proposition 14 (CST), with labels used ONLY to evaluate (Entry 36, step 1).

Proposition 14 bounds, for a real off-map H-frame segment G0 lying deep in an excursion, the probability that the reported HMM
track passes the counterfactual shape test at least once in G0: P(min_{t in G0} r_t <= eps) <= a (n+1)/(pi n+1). This script
measures that probability directly on the real off-map segments of a run (segmentation as nav_demo.rule_metrics), split by the
segment's position in its excursion (index 0 = the first H off-map frames, the boundary), and compares the CST threshold eps
(from the counterfactual track) with the ORACLE threshold (the a-quantile of the segment minima of the real off-map track).
Optional extra null tracks (npz with key 'r_null' per frame, or computed here: 'anchor' = residual of the counterfactual
winner's own route hypothesis) are audited the same way.
Usage: cst_audit.py <navcache_dir> <cms_dir> <out.json> [--runs regex] [--jobs 4]"""
import sys, os, json, glob, re
import numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nav_rules as NR
import cms as CMS
import cpc_geo as CG

A = 0.05


def offmap_segments(seqs, offm, H, full=None):
    """[(frames, index in excursion)] of disjoint H-frame segments of consecutive off-map frames (as rule_metrics); with
    full (bool per frame: shape window not truncated by the sequence start) also a flag per segment"""
    out = []
    for idx in seqs:
        of = offm[idx]; i = 0
        while i < len(idx):
            if of[i]:
                j = i
                while j < len(idx) and of[j]: j += 1
                for n_, k in enumerate(range(i, j - H + 1, H)):
                    out.append((idx[k:k + H], n_) if full is None else (idx[k:k + H], n_, bool(full[idx[k:k + H]].all())))
                i = j
            else: i += 1
    return out


def full_window(seqs, o, excl, D_x=3.0):
    """frames whose odometry path since the start of their sequence is >= D_x excl (shape window not truncated)"""
    f = np.zeros(len(o), bool)
    for idx in seqs:
        oo = o[idx]; oo = oo if oo.ndim > 1 else oo[:, None]
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(oo, axis=0), axis=1))]; f[idx] = cum >= D_x * excl
    return f


def eps_from(rnull, z, b, a=A):
    """CST threshold per frame from a per-frame null residual (floor(a (n+1))-th smallest segment minimum per group)"""
    eps = np.full(len(rnull), -np.inf); CMS.GROUP = "cond"; CMS.ALPHA_MIN[0] = 0.05
    for sqs, cqs in CMS.cal_groups(z, b["seqs"]):
        m = np.concatenate(sqs); mins = []
        for sg in CMS._segments(cqs, b["H"]):
            v = rnull[sg]; v = v[np.isfinite(v)]
            if len(v): mins.append(v.min())
        mins = np.sort(mins); k = int(np.floor(a * (len(mins) + 1))); eps[m] = mins[k - 1] if k >= 1 else -np.inf
    return eps


def audit_one(args):
    zf, cdir = args
    tag = os.path.basename(zf)[len("navcache_"):]
    cf = os.path.join(cdir, "cms_" + tag)
    if not os.path.exists(cf): return tag, None
    z = np.load(zf, allow_pickle=True); st = dict(np.load(cf)); b = NR.base_parts(z)
    seqs, excl, MP, H = b["seqs"], b["excl"], b["MP"], b["H"]; hz = list(z["hz"])
    xc = MP[b["est_c"]]; jj = np.maximum(st["j"], 0)
    r = CG.shape_resid(xc, z["o_q"], seqs, excl, hz=hz)
    jc = np.where(st["j_cf"] >= 0, st["j_cf"], jj); rcf = CG.shape_resid(MP[jc], z["o_q"], seqs, excl, hz=hz)
    nulls = {"cf": rcf}
    for k in [k for k in st if k.startswith("rnull_")]: nulls[k[6:]] = st[k]
    oq = z["o_q"]; oq = (oq[:, hz] if oq.ndim > 1 and oq.shape[1] > 2 else oq).astype(float)
    fw = full_window(seqs, oq, excl); segs3 = offmap_segments(seqs, z["offm"], H, fw); segs = [(g, p) for g, p, _ in segs3]
    fullseg = np.array([f_ for _, _, f_ in segs3], bool)
    res = {"n_seg": len(segs), "excl": excl, "frac_trunc": float(1 - fullseg.mean()) if len(fullseg) else None}
    smin = np.array([np.nanmin(np.where(np.isfinite(r[g]), r[g], np.inf)) for g, _ in segs]) if segs else np.array([])
    pos = np.array([p for _, p in segs])
    epsd = {nm: eps_from(rn, z, b) for nm, rn in nulls.items()}
    fd = os.environ.get("FWD_DIR")
    if fd and os.path.exists(os.path.join(fd, "fwd_" + tag)):
        import cms_fwd as CF
        recs, _ = CF.load_recs(os.path.join(fd, "fwd_" + tag)); fs = CF.fwd_segments(recs, H, 0); fs1 = CF.fwd_segments(recs, H, 1)
        es = CF.eps_fwd(z, b, fs1, A, "pooled") if fs1 else np.full(len(z["cond"]), -np.inf)
        for mode in ("pooled", "minbin", "bins3"):
            ex_ = CF.eps_fwd(z, b, fs, A, mode); epsd["F" + mode[:3]] = np.where(fw, ex_, np.minimum(es, ex_))
        res["n_fseg"] = len(fs); res["n_fseg_start"] = len(fs1)
    for nm, eps in epsd.items():
        e_seg = np.array([eps[g[0]] for g, _ in segs])
        pas = smin <= e_seg
        res[nm] = dict(eps_med=float(np.median(eps[np.isfinite(eps)])) if np.isfinite(eps).any() else None,
                       pass_all=float(pas.mean()) if len(pas) else None,
                       pass_b0=float(pas[pos == 0].mean()) if (pos == 0).any() else None,
                       pass_b1_2=float(pas[(pos >= 1) & (pos <= 2)].mean()) if ((pos >= 1) & (pos <= 2)).any() else None,
                       pass_deep=float(pas[pos >= 3].mean()) if (pos >= 3).any() else None,
                       pass_full=float(pas[fullseg].mean()) if fullseg.any() else None,
                       pass_trunc=float(pas[~fullseg].mean()) if (~fullseg).any() else None,
                       pass_full_b0=float(pas[fullseg & (pos == 0)].mean()) if (fullseg & (pos == 0)).any() else None,
                       pass_full_deep=float(pas[fullseg & (pos >= 3)].mean()) if (fullseg & (pos >= 3)).any() else None)
    k = int(np.floor(A * (len(smin) + 1)))
    res["eps_oracle"] = float(np.sort(smin)[k - 1]) if k >= 1 else None
    res["eps_oracle_deep"] = (lambda s: float(np.sort(s)[int(np.floor(A * (len(s) + 1))) - 1]) if int(np.floor(A * (len(s) + 1))) >= 1 else None)(smin[pos >= 3])
    good = z["inm"] & (np.linalg.norm(xc - z["q_pos"], axis=1) <= excl)
    res["r_good_q"] = [float(np.nanpercentile(r[good], q)) for q in (50, 80, 90)]
    return tag, res


def main():
    nd, cd, out = sys.argv[1:4]
    rx = sys.argv[sys.argv.index("--runs") + 1] if "--runs" in sys.argv else "."
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4
    fs = [f for f in sorted(glob.glob(os.path.join(nd, "navcache_*.npz"))) if re.search(rx, os.path.basename(f))]
    with Pool(jobs) as p: R = dict(p.map(audit_one, [(f, cd) for f in fs], chunksize=1))
    json.dump(R, open(out, "w"), indent=1)
    agg = {}
    for tag, r in R.items():
        if r is None: continue
        ds = tag.split("_")[0] if not tag.startswith("4s_") else "4s_" + ("countryside" if "countryside" in tag else ("old_town" if "old_town" in tag else "office_loop"))
        for nm in [k for k in r if isinstance(r[k], dict)]:
            agg.setdefault((ds, nm), []).append([r[nm].get(k) if r[nm].get(k) is not None else np.nan for k in ("pass_all", "pass_b0", "pass_deep", "pass_full", "pass_trunc", "pass_full_b0", "pass_full_deep", "eps_med")] + [r["eps_oracle"] or np.nan, r.get("frac_trunc") or 0.0])
    print(f"{'dataset':16s} {'null':8s} {'runs':>4s} {'pass':>6s} {'b0':>6s} {'deep':>6s} {'full':>6s} {'trunc':>6s} {'f.b0':>6s} {'f.deep':>6s} {'eps':>6s} {'oracle':>6s} {'%trunc':>6s}")
    for (ds, nm), v in sorted(agg.items()):
        v = np.array(v, float); m = np.nanmean(v, 0)
        print(f"{ds:16s} {nm:8s} {len(v):4d} " + " ".join(f"{x:6.3f}" for x in m[:7]) + f" {m[7]:6.1f} {m[8]:6.1f} {m[9]:6.3f}")


if __name__ == "__main__":
    main()
