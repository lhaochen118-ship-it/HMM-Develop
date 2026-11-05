"""Diagnostic (labels used, development data only): how do confident-but-wrong OWF hypotheses ("alias episodes") look?
An alias episode = a maximal run of frames of one sequence in which the OWF report position (xhat) is farther than excl from the true
position while the disc mass is >= 0.5. For each episode: path since the sequence start at its first frame (excl units), its length
(path, excl units), the peak disc mass (as -log10(1 - mass)), whether the robot was off the map during it. Also the false-report
counts at fixed eps by path-since-start bin. Usage: owf_alias_diag.py <frames_dir> <navcache_dir>[,dir2] [--ftag _t] [--out f.json]"""
import sys, os, glob, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)


def episodes(bad, pst, mass, offm, idx):
    out = []; i = 0; b = bad[idx]
    while i < len(idx):
        if not b[i]: i += 1; continue
        j = i
        while j + 1 < len(idx) and b[j + 1]: j += 1
        sl = idx[i:j + 1]
        out.append(dict(start=float(pst[sl[0]]), length=float(pst[sl[-1]] - pst[sl[0]]), nfr=len(sl),
                        peak=float(-np.log10(max(1 - mass[sl].max(), 1e-300))), off=float(offm[sl].mean())))
        i = j + 1
    return out


def main():
    fdir, cdirs = sys.argv[1], sys.argv[2].split(",")
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    ftag = opt("--ftag", ""); outf = opt("--out", None)
    sys.argv = sys.argv[:1]
    import owf_decide as OD
    R = {}
    for ff in sorted(glob.glob(os.path.join(fdir, f"fr*{ftag}_b1.npz"))):
        t = os.path.basename(ff).split("_", 1)[1].rsplit("_b1.npz", 1)[0]
        if ftag: t = t[: -len(ftag)]
        base, _, sd = t.rpartition("_s"); seed = int(sd)
        cf = next((os.path.join(d, f"navcache_{base}_s{seed}.npz") for d in cdirs if os.path.exists(os.path.join(d, f"navcache_{base}_s{seed}.npz"))), None)
        if cf is None: continue
        z = np.load(cf, allow_pickle=True); fr = np.load(ff)
        excl = float(z["excl"]); sid, k = z["q_sid"], z["q_k"]
        seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
        U = z["U"].astype(float); U = U if U.ndim > 1 else U[:, None]; hz = list(z["hz"])
        pst = OD.path_from_start(U, seqs, hz) / excl
        mass = fr["mass"]; err = fr["err"]; inm, offm = z["inm"], z["offm"]
        bad = (mass >= 0.5) & ((err > excl) | offm)
        eps = []
        for idx in seqs: eps += episodes(bad, pst, mass, offm, idx)
        bins = [0, 0.5, 2, 4, 8, 16, 32, 1e9]
        fr_rep = {}
        for e in (1e-3, 1e-4, 1e-5, 1e-6, 1e-8):
            rep = mass >= 1 - e; wrong = rep & ((err > excl) | offm)
            fr_rep[str(e)] = dict(wrong=[int(((pst >= a) & (pst < b) & wrong).sum()) for a, b in zip(bins[:-1], bins[1:])],
                                  right=[int(((pst >= a) & (pst < b) & rep & ~wrong & inm).sum()) for a, b in zip(bins[:-1], bins[1:])])
        R[t] = dict(n=len(mass), nseq=len(seqs), episodes=eps, by_eps=fr_rep, bins=bins)
        ep = np.array([[x["start"], x["length"], x["peak"], x["off"]] for x in eps]) if eps else np.zeros((0, 4))
        print(f"{t}: {len(seqs)} seqs, {len(eps)} alias episodes; start<2excl: {int((ep[:, 0] < 2).sum()) if len(ep) else 0}; "
              f"peak>=3 (1e-3): {int((ep[:, 2] >= 3).sum()) if len(ep) else 0}, >=5: {int((ep[:, 2] >= 5).sum()) if len(ep) else 0}, >=8: {int((ep[:, 2] >= 8).sum()) if len(ep) else 0}")
        for e, v in fr_rep.items(): print(f"   eps {e}: wrong by path-from-start bin {v['wrong']}  right {v['right']}")
        if len(ep):
            for lo, hi in ((0, 2), (2, 16), (16, 1e9)):
                s_ = ep[(ep[:, 0] >= lo) & (ep[:, 0] < hi)]
                if len(s_): print(f"   episodes starting at path {lo}-{hi} excl: n {len(s_)}, length median {np.median(s_[:, 1]):.2f} p90 {np.percentile(s_[:, 1], 90):.2f} excl, "
                                  f"peak median {np.median(s_[:, 2]):.1f} max {s_[:, 2].max():.1f}, off-map share {s_[:, 3].mean():.2f}")
    if outf: json.dump(R, open(outf, "w"))


if __name__ == "__main__":
    main()
