"""Paired comparison of two rules at their default points over the SAME runs (dataset x descriptor x seed): mean
difference with a 95 % bootstrap CI (runs resampled, 5000 draws) and a two-sided sign test, for recall, navigation error and
segment FAR. Audit (Entry 29): the round-6 tables reported means and win counts only.
CIs: cluster bootstrap over hole-layout seeds; sign test over the per-seed mean differences (NCLT: one seed, the 6 runs are
descriptors -> its CI is over descriptors).
Usage: paired_stats.py <dir with oc_*.json (recursive)> <ruleA> <ruleB> [ruleA2 ruleB2 ...] -> markdown table on stdout"""
import sys, os, glob, json
import numpy as np
from scipy.stats import binomtest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e26_summary as E


def per_run(R, name):
    out = {}
    for ds, bd in R.items():
        for desc, runs in bd.items():
            for rk, run in runs.items():
                f = run["families"].get(name, {}).get("default")
                if f: out[(ds, desc, rk)] = (f["recall"], f.get("err_mean", np.nan), f["seg_FAR"])
    return out


def boot(d, cl, B=5000, seed=0):
    """cluster bootstrap: the clusters (hole-layout seeds; the 6 descriptors of a seed share images and holes) are resampled"""
    r = np.random.default_rng(seed); u = np.unique(cl)
    if len(u) < 2: u, cl = np.arange(len(d)), np.arange(len(d))                     # one seed (NCLT): resample runs
    idx = [np.flatnonzero(cl == c) for c in u]
    m = np.array([d[np.concatenate([idx[i] for i in r.integers(0, len(u), len(u))])].mean() for _ in range(B)])
    return d.mean(), np.quantile(m, 0.025), np.quantile(m, 0.975)


def main():
    R = E.load(sys.argv[1]); pairs = list(zip(sys.argv[2::2], sys.argv[3::2]))
    print("| A vs B | dataset | runs | Δ recall [95 % CI] (sign p) | Δ error m [95 % CI] (sign p) | Δ segFAR [95 % CI] |")
    print("|---|---|---|---|---|---|")
    for a, b in pairs:
        A, Bv = per_run(R, a), per_run(R, b)
        for ds in [d for d in E.DS_ORDER if d in R]:
            keys = [k for k in A if k[0] == ds and k in Bv]
            if not keys: continue
            da = np.array([A[k] for k in keys]); db = np.array([Bv[k] for k in keys]); d = da - db; cells = []
            cl = np.array([int(k[2].rsplit("_s", 1)[1].split(".")[0]) for k in keys])      # seed of the run
            for c in range(3):
                f = np.isfinite(d[:, c]); x, cx = d[f, c], cl[f]; m, lo, hi = boot(x, cx)
                ps = np.array([x[cx == u].mean() for u in np.unique(cx)])                     # sign test over seeds
                nz = ps[np.abs(ps) > 1e-12]; p = binomtest(int((nz > 0).sum()), len(nz)).pvalue if len(nz) else 1.0
                fmt = "{:+.3f}" if c != 1 else "{:+.1f}"
                cells.append(f"{fmt.format(m)} [{fmt.format(lo)}, {fmt.format(hi)}]" + (f" (p={p:.1e})" if c < 2 else ""))
            print(f"| {a} vs {b} | {E.DS_NAME.get(ds, ds)} | {len(keys)} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
