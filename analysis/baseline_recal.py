"""Audit 2026-11-11: external baselines at an operating point that targets the SAME quantity as the evaluation (segment FAR <= alpha).

Why. The protocol judges every rule by segFAR (share of disjoint H-frame off-map segments with >= 1 report) <= alpha = 0.05 per run. The
label baselines were set to OTHER targets:
  Xu21      T, k chosen for frame-level FL <= alpha on the two easiest conditions (nav_demo.main), i.e. up to ~H x alpha in segFAR;
  Claxton24 P(in tolerance) > 0.5 (no false-report target at all);
  TAO26     tau_OOD = mean + 3 sd of the winner cost of correct frames (an inlier bound, no false-report target).
So "invalid on 56-90 % of runs" measures the operating point, not the method. This module re-sets each baseline's threshold on a score
that the baseline already computes, without touching the method:
  @pub  the published / previous operating point (unchanged numbers);
  @seg  label calibration on the two easiest conditions (bsel, as before) but for SEGMENT FAR <= alpha: the most permissive threshold
        whose bsel off-map segments are reported in at most floor(alpha n) cases (point estimate, as the FL calibration it replaces);
  @orc  per-run oracle threshold (labels of the test run itself): the largest recall with segFAR <= alpha on that run, an UPPER bound
        of what any threshold on that score can reach (not a deployable rule; reported only to bound the baseline).
Scores (larger = more confident on the map): Claxton24 = P(in tolerance) of its MLP; Xu21 = 1 - posterior of the off-map state (cache
field pof_h, the run's final filter) with the best place decoded from e_h; TAO26 = -C(j*) (needs the per-frame cost, sota_job --scores).
Usage (library): variants(z, scores) -> {name: (acc, xf)}; CLI: baseline_recal.py <navcache_dir>[,dir2] <out.json> [--scores dir]
[--glob 'navcache_*_s6[7-9].npz'] [--jobs 4]  (Claxton24 / Xu21 from the navcache alone; TAO26 only where sotasc_*.npz exist)."""
import sys, os, glob, json
import numpy as np
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ALPHA = 0.05


def seqs_of(z):
    sid, k = z["q_sid"], z["q_k"]
    return [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]


def seg_max(score, offm, seqs, H, keep=None):
    """max score of every disjoint H-frame off-map segment (the segFAR unit of nav_demo.rule_metrics); keep: frame mask of the sequences
    to use (e.g. the labelled calibration conditions)"""
    out = []
    for idx in seqs:
        if keep is not None and not keep[idx[0]]: continue
        of = offm[idx]; s = score[idx]; i = 0; L = len(idx)
        while i < L:
            if of[i]:
                j = i
                while j < L and of[j]: j += 1
                out += [float(np.max(s[a:a + H])) for a in range(i, j - H + 1, H)]
                i = j
            else: i += 1
    return np.asarray(out)


def thr_segfar(segmax, alpha=ALPHA):
    """threshold lam (report iff score > lam) whose segment FAR on these segments is <= alpha: at most floor(alpha n) segment maxima may
    exceed it, so lam = the (floor(alpha n) + 1)-th largest maximum. No segment: +inf (report nothing)."""
    s = np.sort(segmax[np.isfinite(segmax)])[::-1]
    if not len(s): return np.inf
    return float(s[int(np.floor(alpha * len(s)))])


def thr_oracle(score, offm, seqs, H, alpha=ALPHA):
    """the threshold of thr_segfar on ALL segments of the run (labels of the test run): every lower threshold breaks segFAR <= alpha and
    recall is monotone in the threshold, so this is the best recall reachable with that score on that run"""
    return thr_segfar(seg_max(score, offm, seqs, H), alpha)


def baseline_scores(z, tao=None):
    """per-frame scores and fix positions of the external baselines (larger score = report)"""
    sys.path.insert(0, HERE); sys.argv = sys.argv[:1]
    import nav_demo as N
    MP = z["MP"]; excl = float(z["excl"]); out = {}
    bad_top = z["offm"] | (z["err_top"] > excl)
    p = N.claxton_rule(z["srt10"], z["Smean"], z["Sstd"], z["bsel"], z["good"], bad_top, int(z["seed"]), proba=True)
    out["Claxton24"] = (np.asarray(p, float), MP[z["top"]], p > 0.5)
    if "pof_h" in z and "e_h" in z:
        e = np.asarray(z["e_h"]).astype(int); j = np.where(e >= 0, e, -1 - e)
        out["Xu21"] = (1.0 - np.asarray(z["pof_h"], float), MP[j], np.asarray(z["acc_h"]).astype(bool))
    if tao is not None:
        c = np.asarray(tao["cost"], float); s = np.where(np.isfinite(c) & (np.asarray(tao["j"]) >= 0), -c, -np.inf)
        out["TAO26"] = (s, np.asarray(tao["x_fix"], float), np.asarray(tao["acc_pub"]).astype(bool))
    return out


def variants(z, tao=None, alpha=ALPHA):
    """{name@op: (acc, xf, thr)} for op in pub / seg / orc"""
    seqs = seqs_of(z); H = int(z["H"]); offm = np.asarray(z["offm"], bool)
    bsel = np.asarray(z["bsel"], bool); res = {}
    for name, (s, xf, acc_pub) in baseline_scores(z, tao).items():
        t_seg = thr_segfar(seg_max(s, offm, seqs, H, keep=bsel), alpha)
        t_orc = thr_oracle(s, offm, seqs, H, alpha)
        res[f"{name}@pub"] = (acc_pub, xf, np.nan)
        res[f"{name}@seg"] = (s > t_seg, xf, t_seg)
        res[f"{name}@orc"] = (s > t_orc, xf, t_orc)
    return res


def evaluate(z, V, seed):
    """protocol metrics (nav_demo.rule_metrics, nav_demo.track) of every variant, as sota_job.py"""
    sys.path.insert(0, HERE); sys.argv = sys.argv[:1]
    import nav_demo as N
    seqs = seqs_of(z); H = int(z["H"]); qp = z["q_pos"]; q2 = qp if qp.ndim > 1 else qp[:, None]; excl = float(z["excl"])
    hz = list(z["hz"]); ds = str(z.get("ds", "")); out = {}
    for name, (acc, xf, thr) in V.items():
        xf = np.asarray(xf, float); xf2 = xf if xf.ndim > 1 else xf[:, None]
        gd = z["inm"] & (np.linalg.norm(np.nan_to_num(xf2, nan=1e9) - q2, axis=1) <= excl)
        m = N.rule_metrics(acc, gd, z["inm"], z["offm"], seqs, H)
        e = N.track(acc, np.nan_to_num(xf, nan=0.0), qp, z["o_q"], bool(z["real"]), seqs, hz, seed, ds == "nclt")
        out[name] = dict(recall=m["recall"], FL=m["FL"], seg_FAR=m["seg_FAR"], err_mean=float(np.nanmean(e)), thr=float(thr))
    return out


def _one(a):
    f, sdir = a
    tag = os.path.basename(f)[len("navcache_"):-4]; base, seed = tag.rsplit("_s", 1); seed = int(seed)
    z = dict(np.load(f, allow_pickle=True)); z["ds"] = base.split("_")[0]
    tao = None
    if sdir:
        tf = next(iter(glob.glob(os.path.join(sdir, f"sotasc_{base}_s{seed}*.npz"))), None)
        if tf: tao = dict(np.load(tf))
    return tag, dict(ds=base, seed=seed, variants=evaluate(z, variants(z, tao), seed))


def main():
    dirs, outf = sys.argv[1].split(","), sys.argv[2]
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    pat, sdir, jobs = opt("--glob", "navcache_*.npz"), opt("--scores", ""), int(opt("--jobs", "4"))
    fs = sorted(f for d in dirs for f in glob.glob(os.path.join(d, pat)))
    with Pool(jobs) as p: R = dict(p.imap_unordered(_one, [(f, sdir) for f in fs], chunksize=1))
    json.dump(R, open(outf, "w"), indent=0)
    print(f"{len(R)} runs -> {outf}")
    allv = sorted({v for r in R.values() for v in r["variants"]})
    for v in allv:
        rs = [r["variants"][v] for r in R.values() if v in r["variants"]]
        sf = np.array([x["seg_FAR"] for x in rs])
        print(f"{v:16s} n={len(rs):4d} recall {np.mean([x['recall'] for x in rs]):.3f} mean segFAR {sf.mean():.4f} runs>a {(sf > ALPHA).sum():4d}"
              f" nav {np.nanmean([x['err_mean'] for x in rs]):.1f}")


if __name__ == "__main__":
    main()
