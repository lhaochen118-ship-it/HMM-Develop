"""OWF + HSI hybrid (AUTOLOOP iteration 1): the open-world filter as the ESTIMATOR, HSI's hindsight-calibrated layer as the DECISION.
HSI reads the place chain from the cache field `est_c` (and its confidence `conf_c`, `lo_c`); this script writes a copy of a run's navcache
with those fields replaced by the OWF outputs saved by owf.py --frames:
  mode "x"  : est_c := OWF reported image (posterior-mean disc, snapped to the map)
  mode "xc" : + conf_c := OWF disc mass, lo_c := logit(disc mass)
  mode "xmc<t>": as xm<t> + conf_c / lo_c := OWF disc mass / its logit where replaced (HSI's learned score sees the OWF confidence)
  mode "xma<t>_<D>": as xm<t> and only where the OWF track is settled (confident and jump-free for >= D excl); "xms<t>_<D>": and only
             after D excl of path since the sequence start (CMU: confident-but-wrong OWF starts were certified by HSI in mode xm)
  mode "xm<t>": est_c := OWF image only where its disc mass >= t (default 0.5), the topological chain elsewhere (HSI's geometric
             certificate assumes a FREE chain that wanders in holes; the dead-reckoned OWF track is odometry-consistent even when wrong)
and then runs hsi_eval.py (unchanged code) on the copies. Usage:
  owf_hybrid.py <frames_dir> <navcache_dir>[,dir2] <work_dir> <ds> <desc> <seeds> [--mode x|xc] [--variants HSI-VN,HSI-VMN] [--tag hybx]
Results: <cwd>/results/hsi_<ds>_<desc>_s<seed>_<tag>.json (as hsi_eval.py)."""
import sys, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def seeds_of(s):
    if "-" in s: a, b = s.split("-"); return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def settled(z, xh, mass, kind, D):
    """True where the OWF track is SETTLED: (age) confident (mass >= 0.5) and jump-free for >= D excl of odometry, or (start) the odometry
    path since the sequence start >= D excl"""
    sys.path.insert(0, HERE); import owf_decide as OD
    excl = float(z["excl"]); MP = z["MP"]; sid, k = z["q_sid"], z["q_k"]
    seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    hz = list(z["hz"]); U = z["U"].astype(float); U = U if U.ndim > 1 else U[:, None]
    xf = MP[np.maximum(xh, 0)].astype(float); xf = xf if xf.ndim > 1 else xf[:, None]
    if kind == "a": return OD.track_age(mass, xf, U, seqs, excl, hz) >= D * excl
    return OD.path_from_start(U, seqs, hz) >= D * excl


def build(frames, cache, out, mode):
    z = dict(np.load(cache, allow_pickle=True)); fr = np.load(frames, allow_pickle=True)
    xh = np.asarray(fr["xhat"]).astype(int); bad = xh < 0; mass = np.asarray(fr["mass"], float)
    if mode.startswith(("xma", "xms")):                     # xma<t>_<D> / xms<t>_<D>: confident AND settled (track age / path from start)
        t, D = mode[3:].split("_"); bad = bad | (mass < float(t)) | ~settled(z, xh, mass, mode[2], float(D))
    elif mode.startswith("xm"): bad = bad | (mass < float(mode.lstrip("xmc") or 0.5))   # replace only where OWF is confident
    est = z["est_c"].astype(int).copy(); est[~bad] = xh[~bad]; z["est_c"] = est
    if mode == "xc" or mode.startswith("xmc"):
        m = np.clip(np.asarray(fr["mass"], float), 1e-9, 1 - 1e-9)
        z["conf_c"] = np.where(bad, z["conf_c"], m); z["lo_c"] = np.where(bad, z["lo_c"], np.log(m / (1 - m)))
    np.savez_compressed(out, **z)


def main():
    fdir, cdirs, work, ds, desc, seeds = sys.argv[1], sys.argv[2].split(","), sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    mode, variants, tag = opt("--mode", "x"), opt("--variants", "HSI-VN,HSI-VMN"), opt("--tag", "hyb")
    ftag = opt("--ftag", "")                                   # frames file suffix (e.g. _r40)
    os.makedirs(work, exist_ok=True); base = ds.replace(":", "_"); done = []
    for s in seeds_of(seeds):
        ff = os.path.join(fdir, f"fr_{base}_{desc}_s{s}{ftag}_b1.npz")
        cf = next((os.path.join(d, f"navcache_{base}_{desc}_s{s}.npz") for d in cdirs if os.path.exists(os.path.join(d, f"navcache_{base}_{desc}_s{s}.npz"))), None)
        if not os.path.exists(ff) or cf is None: print("missing", ff, cf, flush=True); continue
        build(ff, cf, os.path.join(work, f"navcache_{base}_{desc}_s{s}.npz"), mode); done.append(s)
    if not done: sys.exit(1)
    r = subprocess.run([sys.executable, os.path.join(HERE, "hsi_eval.py"), work, ds, desc, ",".join(map(str, done)), "--variants", variants, "--tag", tag])
    for s in done:
        try: os.remove(os.path.join(work, f"navcache_{base}_{desc}_s{s}.npz"))
        except OSError: pass
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
