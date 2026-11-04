"""Offline decision variants on top of the open-world filter (AUTOLOOP iteration 1). The filter is NOT re-run: every variant reads the
per-frame outputs saved by owf.py --frames (largest excl-disc mass, reported image xhat) and the run's navcache (odometry, sequences, labels
for evaluation only), so a variant costs seconds per run.

Variants (name -> rule; eps0 = 1e-3 is the Entry-10 default):
  base            report iff mass >= 1 - eps0                                                       (Entry 10 OWF)
  start(Ls,es)    1 - es instead of 1 - eps0 while the odometry path since the sequence start < Ls * excl   (Proposition 2: O0 ~ 1 at a start)
  age(D)          report only when the current TRACK is >= D * excl old: a track starts when the disc mass first reaches 0.5 and breaks
                  when the mass drops below 0.5 or xhat jumps (|xhat_t - xhat_{t-1} - u_t| > excl); covers starts, re-localisations after
                  holes / Omega and posterior jumps to look-alikes (the far wrong fixes behind Entry 10's navigation failures)
  agestart(D,Ls,es)  both
  jump(D)         suppress reports for D * excl of odometry after a JUMP of the confident posterior (consecutive confident frames whose
                  images disagree with the odometry by > excl); starts untouched
  jumpstart(D,Ls,es) jump(D) + start(Ls,es)
Usage: owf_decide.py <frames_dir> <navcache_dir>[,<dir2>...] <out.json> [--variants a;b;...] [--glob pattern] [--jobs 4] [--tag ""]
Writes per run and variant: recall, FL, segFAR, err_mean (nav_demo.track), position classes."""
import sys, os, glob, json
import numpy as np
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = ("base;start(8,1e-4);start(20,1e-4);start(20,2e-4);start(8,1e-5);age(0.5);age(1);jump(2);jump(4);jump(8);"
           "jumpstart(4,20,1e-4);jumpstart(8,20,1e-4);jumpstart(4,8,1e-4)")


def parse(v):
    name, _, args = v.partition("(")
    return name, [float(a) for a in args.rstrip(")").split(",")] if args else []


def track_age(mass, xf, U, seqs, excl, hz):
    """odometry path length of the current confident, jump-free track at every frame (0 when not in a track)"""
    age = np.zeros(len(mass))
    for idx in seqs:
        a, prev = None, None
        for t in idx:
            step = float(np.linalg.norm(U[t][hz]))
            if mass[t] < 0.5: a, prev = None, None; continue
            if a is None or prev is None or np.linalg.norm((xf[t] - xf[prev] - U[t])[hz]) > excl: a = 0.0
            else: a += step
            age[t] = a; prev = t
    return age


def since_jump(mass, xf, U, seqs, excl, hz):
    """odometry path since the last JUMP (two consecutive confident frames, mass >= 0.5, whose reported images disagree with the odometry
    by more than excl); inf before the first jump of a sequence"""
    out = np.full(len(mass), np.inf)
    for idx in seqs:
        s_, prev = np.inf, None
        for t in idx:
            s_ += float(np.linalg.norm(U[t][hz]))
            if mass[t] >= 0.5 and prev is not None and mass[prev] >= 0.5 and np.linalg.norm((xf[t] - xf[prev] - U[t])[hz]) > excl: s_ = 0.0
            out[t] = s_; prev = t
    return out


def path_from_start(U, seqs, hz):
    p = np.zeros(len(U))
    for idx in seqs: p[idx] = np.r_[0.0, np.cumsum(np.linalg.norm(U[idx[1:]][:, hz], axis=1))]
    return p


def one(args):
    ff, cdirs, variants, eps0 = args
    sys.argv = sys.argv[:1]; sys.path.insert(0, HERE)
    import nav_demo as N, position_audit as PA
    tag = os.path.basename(ff)[3:].rsplit("_b1.npz", 1)[0]
    base, _, rest = tag.rpartition("_s"); seed = int(rest.split("_")[0])
    cf = next((os.path.join(d, f"navcache_{base}_s{seed}.npz") for d in cdirs if os.path.exists(os.path.join(d, f"navcache_{base}_s{seed}.npz"))), None)
    if cf is None: return tag, None
    z = np.load(cf, allow_pickle=True); fr = np.load(ff, allow_pickle=True)
    excl = float(z["excl"]); MP = z["MP"]; qp = z["q_pos"]; sid, k = z["q_sid"], z["q_k"]
    seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    hz = list(z["hz"]); U = z["U"].astype(float); U = U if U.ndim > 1 else U[:, None]
    mass, xh = fr["mass"], fr["xhat"]; xf = MP[np.maximum(xh, 0)].astype(float); xf = xf if xf.ndim > 1 else xf[:, None]
    err = np.linalg.norm(xf - (qp if qp.ndim > 1 else qp[:, None]), axis=1); gd = z["inm"] & (err <= excl) & (xh >= 0)
    ds = base.split("_")[0]; segs = PA.seg_classes(z, PA.OFF_D[ds])
    age = track_age(mass, xf, U, seqs, excl, hz); pst = path_from_start(U, seqs, hz); sj = since_jump(mass, xf, U, seqs, excl, hz)
    out = {}
    for v in variants:
        name, a = parse(v); thr = np.full(len(mass), 1 - eps0); ok = np.ones(len(mass), bool)
        if name in ("start", "agestart"):
            Ls, es = (a[1], a[2]) if name == "agestart" else (a[0], a[1]); thr = np.where(pst < Ls * excl, 1 - es, thr)
        if name in ("age", "agestart"): ok = age >= a[0] * excl
        if name in ("jump", "jumpstart"):
            ok = sj >= a[0] * excl
            if name == "jumpstart": thr = np.where(pst < a[1] * excl, 1 - a[2], thr)
        acc = (mass >= thr) & ok & (xh >= 0)
        m = N.rule_metrics(acc, gd, z["inm"], z["offm"], seqs, int(z["H"]))
        e = N.track(acc, xf, qp, z["o_q"], bool(z["real"]), seqs, hz, seed, ds == "nclt")
        pos = {c: [int(sum(bool(acc[g].any()) for g, c_ in segs if c_ == c)), int(sum(1 for _, c_ in segs if c_ == c))] for c in PA.CLASSES}
        out[v] = dict(recall=m["recall"], FL=m["FL"], seg_FAR=m["seg_FAR"], err_mean=float(np.nanmean(e)), pos=pos)
    return tag, dict(ds=_dsname(base), seed=seed, variants=out)


def _dsname(base):
    for s in ("4s_office_loop", "4s_old_town", "4s_countryside"):
        if base.startswith(s): return s.replace("4s_", "4s:")
    return base.split("_")[0]


def main():
    fdir, cdirs, outf = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    variants = opt("--variants", DEFAULT).split(";"); pat = opt("--glob", "*"); jobs = int(opt("--jobs", "4")); eps0 = float(opt("--eps0", "1e-3"))
    fs = sorted(glob.glob(os.path.join(fdir, f"fr_{pat}_b1.npz")))
    with Pool(jobs) as p: R = {k: v for k, v in p.imap_unordered(one, [(f, cdirs, variants, eps0) for f in fs], chunksize=1) if v is not None}
    json.dump(R, open(outf, "w"), indent=0)
    print(f"{len(R)} runs -> {outf}")


if __name__ == "__main__":
    main()
