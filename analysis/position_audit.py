"""Audit by position (from Entry 37 of idea 1; generic: any rule whose per-frame decisions are dumped) (H37b; labels used ONLY to evaluate): the report rate of REAL off-map segments under each rule, split by
where the segment lies.
Segments are the disjoint H-frame off-map segments of nav_demo.rule_metrics (the segFAR unit). Classes (disjoint):
  start = the segment starts within the start horizon of its sequence (odometry path <= off_d + 20 excl from the sequence start:
          the horizon of the exact start null, mode 2 of cms_fwd), whatever its position in the excursion;
  edge  = first segment of an excursion (not start);
  deep  = later segments of an excursion (not start).
A segment is "reported" iff the rule accepts at least one of its frames (= a false fix in an off-map segment).
Inputs: oc_curves --dump-frames files (results/frames_<tag>_<desc>_e37_s<seed>.npz: names, acc) + the run's navcache.
Usage: e37_audit.py <navcache_dir> <frames_dir> <out.json> [--rules a,b] [--runs regex] [--jobs 4] [--lab e37|e38]
Prints per dataset (pooled over runs, counts summed): n segments and report rate per class for every rule."""
import sys, os, json, glob, re
import numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OFF_D = {"boreas": 40.0, "cmu": 40.0, "4s": 40.0, "4sx": 40.0, "oxford": 40.0, "nclt": 20.0, "nord": 10.0, "rc": 40.0, "stlucia": 40.0, "vs": None}   # vs: VPR-Space, off_d = 1.6 excl (tau-scaled)   # sc_eval.CFG off_d

RULES = ["CMS-CPC/H+CSTJSU+G+NGRr", "CMS-CPC/H+CSTJSB+G+NGRr", "CMS-CPC/H+SH+CSTJSU+G+NGRr", "CMS-CPC/H+CSTJSU+G[both]+NGRr",
         "CMS-CPC/H+CSTJS+G+NGRr", "CMS-CPC/H+SH+CSTJS+G+NGRr", "CMS-CPC/H+CSTJS+G[both]+NGRr", "CMS-CPC/H+CSTJs+G+NGRr",
         "CMS-CPC/H+SH+CSTJs+G+NGRr", "CMS-CPC/H+CSTJ+G+NGRr", "CMS-CPC/H+CSTF+G+NGRr", "CMS-CPC/H+SH+G+NGRr", "CMS-CPC/H+SH+CST+G+NGRr",
         "CMS-CPC/H+CSTJS0+G+NGRr", "CMS-CPC/H+CSTJSL+G+NGRr", "CMS-CPC/H+CSTJF0+G+NGRr"]
CLASSES = ("start", "edge", "deep")


def seg_classes(z, off_d):
    """[(frames, class)] of the run's real off-map segments (off_d: the dataset's off-map distance = rho of the surgery)"""
    H = int(z["H"]); sid, k = z["q_sid"], z["q_k"]; offm = np.asarray(z["offm"], bool); excl = float(z["excl"])
    if off_d is None: off_d = 1.6 * excl
    seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    hz = list(z["hz"]); o = z["o_q"]; o = (o[:, hz] if o.ndim > 1 and o.shape[1] > 2 else o).astype(float); o = o if o.ndim > 1 else o[:, None]
    Ds = off_d + 20.0 * excl; out = []
    for idx in seqs:
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o[idx], axis=0), axis=1))]; of = offm[idx]; i = 0
        while i < len(idx):
            if of[i]:
                j = i
                while j < len(idx) and of[j]: j += 1
                for n_, a in enumerate(range(i, j - H + 1, H)):
                    out.append((idx[a:a + H], "start" if cum[a] <= Ds else ("edge" if n_ == 0 else "deep")))
                i = j
            else: i += 1
    return out


LAB = sys.argv[sys.argv.index("--lab") + 1] if "--lab" in sys.argv else "e37"   # Entry 38: --lab e38 (frames_*_e38_s*.npz)


def one(args):
    nf, fdir, rules = args
    tag = os.path.basename(nf)[len("navcache_"):-4]; base, seed = tag.rsplit("_s", 1)
    ff = os.path.join(fdir, f"frames_{base}_{LAB}_s{seed}.npz")
    if not os.path.exists(ff): return tag, None
    z = np.load(nf, allow_pickle=True); fr = np.load(ff, allow_pickle=True); names = list(fr["names"]); acc = fr["acc"]
    segs = seg_classes(z, OFF_D[dataset_of(tag).split("_")[0]]); res = {"n": {c: sum(1 for _, c_ in segs if c_ == c) for c in CLASSES}}
    for r in rules:
        if r not in names: continue
        a = acc[names.index(r)]
        res[r] = {c: int(sum(bool(a[g].any()) for g, c_ in segs if c_ == c)) for c in CLASSES}
    return tag, res


def dataset_of(tag):
    if tag.startswith("4s_"):
        return "4s_" + next(s for s in ("countryside", "old_town", "office_loop") if s in tag)
    return tag.split("_")[0]


def main():
    nd, fdir, out = sys.argv[1:4]
    rules = sys.argv[sys.argv.index("--rules") + 1].split(",") if "--rules" in sys.argv else RULES
    rx = sys.argv[sys.argv.index("--runs") + 1] if "--runs" in sys.argv else "."
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4
    fs = [f for f in sorted(glob.glob(os.path.join(nd, "navcache_*.npz"))) if re.search(rx, os.path.basename(f))]
    with Pool(jobs) as p: R = {k: v for k, v in p.map(one, [(f, fdir, rules) for f in fs], chunksize=1) if v is not None}
    agg = {}
    for tag, r in R.items():
        ds = dataset_of(tag); a = agg.setdefault(ds, {"runs": 0, "n": dict.fromkeys(CLASSES, 0)}); a["runs"] += 1
        for c in CLASSES: a["n"][c] += r["n"][c]
        for rl in rules:
            if rl in r:
                for c in CLASSES: a.setdefault(rl, dict.fromkeys(CLASSES, 0))[c] += r[rl][c]
    rate = {ds: {rl: {c: (a[rl][c] / a["n"][c] if a["n"][c] else None) for c in CLASSES} for rl in rules if rl in a} for ds, a in agg.items()}
    json.dump(dict(runs=R, pooled=agg, rate=rate), open(out, "w"), indent=1)
    for ds, a in sorted(agg.items()):
        print(f"{ds}: {a['runs']} runs, segments " + ", ".join(f"{c} {a['n'][c]}" for c in CLASSES))
        for rl in rules:
            if rl in rate[ds]:
                print(f"   {rl:34s} " + "  ".join(f"{c} {rate[ds][rl][c]:.3f}" if rate[ds][rl][c] is not None else f"{c}   -  " for c in CLASSES))


if __name__ == "__main__":
    main()
