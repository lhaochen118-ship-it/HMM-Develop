"""AUTOLOOP iteration 4 (offline): union of OWF-H with very confident, settled OWF reports.
OWF-H (Entry 11) reports where HSI-VN reports on the hybrid chain; on Nordland / old town the open-world filter alone reports more correct
fixes. Union rule U(e2, D2): report at t iff OWF-H reports, OR (OWF disc mass >= 1 - e2 AND odometry path since the sequence start >= D2 excl);
W(e2, D2, e3, D3): two tiers (a very strict one early, e.g. 1e-8 after 2 excl, and a strict one later, e.g. 1e-5 after 16 excl).
Fix position: OWF-H's position where it reports (hybrid chain = OWF image where mass >= 0.9 and path >= 16 excl, the topological chain
elsewhere), the OWF image otherwise. Inputs: OWF frames (fr_*_b1.npz: mass, xhat), OWF-H masks (hsifr_*_<tag>.npz from hsi_eval --frames
via owf_hybrid --hsiframes), navcaches. Usage:
  owf_union.py <owf_frames_dir> <hsifr_dir> <navcache_dir>[,dir2] <out.json> [--tag hfr0916] [--variants "U(1e-4,16);U(1e-5,32)"] [--ftag ""]
Output in the owf_decide.py JSON format (variant names prefixed OWF: by owf_score.py --decide)."""
import sys, os, glob, json
import numpy as np
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = "H;U(1e-3,16);U(1e-4,16);U(1e-5,16);U(1e-4,32);U(1e-5,32)"


def one(args):
    ff, hdir, cdirs, variants, tag, ftag = args
    sys.argv = sys.argv[:1]; sys.path.insert(0, HERE)
    import nav_demo as N, position_audit as PA, owf_decide as OD
    t = os.path.basename(ff)[3:].rsplit("_b1.npz", 1)[0]
    if ftag: t = t[: -len(ftag)]
    base, _, rest = t.rpartition("_s"); seed = int(rest)
    cf = next((os.path.join(d, f"navcache_{base}_s{seed}.npz") for d in cdirs if os.path.exists(os.path.join(d, f"navcache_{base}_s{seed}.npz"))), None)
    hf = os.path.join(hdir, f"hsifr_{base}_s{seed}_{tag}.npz")
    if cf is None or not os.path.exists(hf): return t, None
    z = np.load(cf, allow_pickle=True); fr = np.load(ff, allow_pickle=True); hm = np.load(hf)
    n = int(hm["n"]); accH = np.unpackbits(hm["HSI-VN"])[:n].astype(bool)
    excl = float(z["excl"]); MP = z["MP"]; qp = z["q_pos"]; sid, k = z["q_sid"], z["q_k"]
    seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    hz = list(z["hz"]); U = z["U"].astype(float); U = U if U.ndim > 1 else U[:, None]
    mass, xh = np.asarray(fr["mass"], float), np.asarray(fr["xhat"]).astype(int)
    pst = OD.path_from_start(U, seqs, hz)
    est_h = z["est_c"].astype(int).copy(); rep = (xh >= 0) & (mass >= 0.9) & (pst >= 16 * excl); est_h[rep] = xh[rep]   # OWF-H chain
    ds = OD._dsname(base); segs = PA.seg_classes(z, PA.OFF_D[ds.split(":")[0]])
    q2 = qp if qp.ndim > 1 else qp[:, None]; out = {}
    for v in variants:
        if v == "H": acc = accH; est = est_h
        else:
            a = [float(x) for x in v[2:-1].split(",")]                        # U(e2,D2) or W(e2,D2,e3,D3): two tiers
            ok = (mass >= 1 - a[0]) & (pst >= a[1] * excl)
            if v.startswith("W"): ok |= (mass >= 1 - a[2]) & (pst >= a[3] * excl)
            extra = (xh >= 0) & ok & ~accH
            acc = accH | extra; est = np.where(extra, np.maximum(xh, 0), est_h)
        xf = MP[est].astype(float); xf = xf if xf.ndim > 1 else xf[:, None]
        err = np.linalg.norm(xf - q2, axis=1); gd = z["inm"] & (err <= excl)
        m = N.rule_metrics(acc, gd, z["inm"], z["offm"], seqs, int(z["H"]))
        e = N.track(acc, MP[est], qp, z["o_q"], bool(z["real"]), seqs, hz, seed, ds == "nclt")
        pos = {c: [int(sum(bool(acc[g].any()) for g, c_ in segs if c_ == c)), int(sum(1 for _, c_ in segs if c_ == c))] for c in PA.CLASSES}
        out[v] = dict(recall=m["recall"], FL=m["FL"], seg_FAR=m["seg_FAR"], err_mean=float(np.nanmean(e)), pos=pos)
    return t, dict(ds=ds, seed=seed, variants=out)


def main():
    fdir, hdir, cdirs, outf = sys.argv[1], sys.argv[2], sys.argv[3].split(","), sys.argv[4]
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    variants = opt("--variants", DEFAULT).split(";"); tag = opt("--tag", "hfr0916"); ftag = opt("--ftag", ""); jobs = int(opt("--jobs", "4"))
    fs = sorted(glob.glob(os.path.join(fdir, f"fr_*{ftag}_b1.npz")))
    with Pool(jobs) as p: R = {k: v for k, v in p.imap_unordered(one, [(f, hdir, cdirs, variants, tag, ftag) for f in fs], chunksize=1) if v is not None}
    json.dump(R, open(outf, "w"), indent=0); print(f"{len(R)} runs -> {outf}")


if __name__ == "__main__":
    main()
