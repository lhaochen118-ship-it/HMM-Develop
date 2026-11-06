"""Temporal self-audit of open-world reports (Entry 19 development, 2026-11-06).

A report (x_hat_t, disc mass D_t) is AUDITED at the first later frame t' of the same sequence such that the odometry path from t to t' is at
least L_A excl and the filter is confident there (D_t' >= 1 - EPS_REF): the report is RETRACTED if x_hat_t moved by the odometry displacement
u(t -> t') lands farther than TOL excl from x_hat_t'. No labels are used; the audit becomes available at frame t' (causal). Off-map aliasing
reports are retracted when the robot re-enters the map elsewhere; wrong on-map reports when the track is re-acquired.
This module computes the audits (audit_run) and, with labels for diagnosis only, the sensitivity / specificity of the audit (main).
Usage: owf_audit.py <frames_dir> <navcache_dir>[,dir2] [--ftag _aS5] [--la 1] [--epsref 1e-3] [--tol 2]"""
import sys, os, glob
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)


def audit_run(mass, xh, MP, O, seqs, excl, la=1.0, epsref=1e-3, tol=2.0):
    """returns (at, retr): at[t] = frame index at which the report at t is audited (-1: never), retr[t] = retracted (bool).
    O = integrated odometry positions (cache o_q, per-sequence frame), MP map positions; positions compared in the map frame by moving the
    reported map image by the odometry displacement (heading assumed consistent between odometry and map, as in the protocol)."""
    n = len(mass); at = np.full(n, -1, np.int64); retr = np.zeros(n, bool)
    conf = (mass >= 1 - epsref) & (xh >= 0)
    for idx in seqs:
        path = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(O[idx], axis=0), axis=1))]
        cidx = np.flatnonzero(conf[idx])                                   # confident frames of the sequence (positions in idx)
        for j in range(len(idx)):
            t = idx[j]
            if xh[t] < 0: continue
            k = np.searchsorted(path, path[j] + la * excl, side="left")   # first position with path >= la excl ahead
            c = cidx[np.searchsorted(cidx, max(k, j + 1)):] if len(cidx) else cidx
            if not len(c): continue
            jj = c[0]; t2 = idx[jj]
            pred = MP[xh[t]] + (O[t2] - O[t]); at[t] = t2
            retr[t] = np.linalg.norm(pred - MP[xh[t2]]) > tol * excl
    return at, retr


def main():
    fdir, cdirs = sys.argv[1], sys.argv[2].split(",")
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    ftag = opt("--ftag", ""); la, epsref, tol = float(opt("--la", "1")), float(opt("--epsref", "1e-3")), float(opt("--tol", "2"))
    agg = {}
    for ff in sorted(glob.glob(os.path.join(fdir, f"fr_*{ftag}_b1.npz"))):
        t = os.path.basename(ff)[3:].rsplit("_b1.npz", 1)[0]
        if ftag: t = t[: -len(ftag)]
        cf = next((os.path.join(d, f"navcache_{t}.npz") for d in cdirs if os.path.exists(os.path.join(d, f"navcache_{t}.npz"))), None)
        if cf is None: continue
        z = np.load(cf, allow_pickle=True); fr = np.load(ff)
        excl = float(z["excl"]); MP = z["MP"].astype(float); MP = MP if MP.ndim > 1 else MP[:, None]
        O = z["o_q"].astype(float); O = O if O.ndim > 1 else O[:, None]
        sid, k = z["q_sid"], z["q_k"]; seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
        mass, xh = fr["mass"], fr["xhat"].astype(int)
        at, retr = audit_run(mass, xh, MP, O, seqs, excl, la, epsref, tol)
        wrong = z["offm"] | (z["inm"] & (fr["err"] > excl)); ok = z["inm"] & (fr["err"] <= excl)
        ds = t.split("_")[0] if not t.startswith("4s") else "_".join(t.split("_")[:3])
        if t.startswith("vs_"): ds = "vs"
        a = agg.setdefault(ds, {})
        for e in (1e-1, 1e-2, 1e-3, 1e-5):
            rep = (mass >= 1 - e) & (xh >= 0); aud = rep & (at >= 0)
            v = a.setdefault(e, np.zeros(6))
            v += [rep.sum(), aud.sum(), (aud & wrong).sum(), (aud & wrong & retr).sum(), (aud & ok).sum(), (aud & ok & retr).sum()]
    print("dataset            eps     reports  audited  wrong(aud)  sensitivity  correct(aud)  false-retraction")
    for ds, a in sorted(agg.items()):
        for e, v in sorted(a.items(), reverse=True):
            print(f"{ds:18s} {e:7g} {int(v[0]):9d} {v[1] / max(v[0], 1):8.2f} {int(v[2]):10d} {v[3] / max(v[2], 1):12.3f} {int(v[4]):12d} {v[5] / max(v[4], 1):16.4f}")


if __name__ == "__main__":
    main()
