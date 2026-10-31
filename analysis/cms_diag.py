"""Empirical check of the CMS assumptions and of Theorem 6 (labels used HERE ONLY, to evaluate).
Per run and query condition: pi = share of counterfactual H-frame segments whose windows are on-map with a correct belief
(every frame on-map and the route winner within excl of the truth), the bound alpha (n+1)/(pi n+1), and the realized
false-onset rate of CMS-T (share of real off-map H-frame segments, entered while not reporting, with a report);
S2 check: median and alpha-quantile of the counterfactual route cost on good frames vs the real cost on off-map frames.
Usage: cms_diag.py <cache_dir> <cms_dir> [--alpha 0.05] [--jobs 4] -> results/cms_diag.json + printed table per dataset"""
import sys, os, glob, json
import numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cms, nav_rules as NR

ALPHA = float(sys.argv[sys.argv.index("--alpha") + 1]) if "--alpha" in sys.argv else 0.05
JOBS = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4


def one(a):
    cf, cmd_ = a; tag = os.path.basename(cf)[9:-4]; f = os.path.join(cmd_, f"cms_{tag}.npz")
    if not os.path.exists(f): return None
    z = np.load(cf, allow_pickle=True); st = dict(np.load(f)); b = NR.base_parts(z); H = b["H"]
    MP = z["MP"]; xt = MP[np.maximum(st["j"], 0)]; good = z["inm"] & (np.linalg.norm(xt - z["q_pos"], axis=1) <= b["excl"]) & (st["j"] >= 0)
    off = z["offm"]; out = []
    for cn, sqs in cms.cond_seqs(z, b["seqs"]).items():
        segs = cms._segments(sqs, H)
        g = np.array([good[sg].all() for sg in segs]); n = len(segs); pi = g.mean() if n else np.nan
        k, _ = cms.kappa_min(st["cost_cf"], segs, ALPHA)
        # real off-map segments (disjoint H-frame runs fully off-map), onset = any frame with cost < kappa
        offsegs = [sg for sq in sqs for sg in cms._segments([sq], H) if off[sg].all()]
        rate = np.mean([np.any(st["cost"][sg] < k) for sg in offsegs]) if offsegs else np.nan
        cg = st["cost_cf"][np.concatenate(segs)][good[np.concatenate(segs)]]; co = st["cost"][off & np.isin(np.arange(len(off)), np.concatenate(sqs))]
        q = lambda x, p: float(np.nanpercentile(x[np.isfinite(x)], p)) if np.isfinite(x).any() else np.nan
        out.append(dict(tag=tag, cond=str(cn), n=n, pi=float(pi), bound=float(ALPHA * (n + 1) / (pi * n + 1)) if n and pi > 0 else np.nan,
                        realized=float(rate), n_off=len(offsegs), cf_good_med=q(cg, 50), off_med=q(co, 50), cf_good_q05=q(cg, 5), off_q05=q(co, 5)))
    return out


def main():
    cdir, cmd_ = sys.argv[1], sys.argv[2]
    files = sorted(glob.glob(os.path.join(cdir, "navcache_*.npz")))
    with Pool(JOBS) as p: res = [r for rr in p.map(one, [(f, cmd_) for f in files]) if rr for r in rr]
    os.makedirs("results", exist_ok=True); json.dump(res, open("results/cms_diag.json", "w"), indent=0, default=float)
    by = {}
    for r in res:
        ds = r["tag"].rsplit("_", 2)[0]; by.setdefault(ds, []).append(r)
    print("| dataset | conditions x runs | pi (mean) | bound alpha(n+1)/(pi n+1) | realized false onset (CMS-T) | realized / alpha | CF good median / off median | CF good q05 / off q05 |")
    print("|---|---|---|---|---|---|---|---|")
    for ds, rs in sorted(by.items()):
        f = lambda k: np.nanmean([r[k] for r in rs])
        print(f"| {ds} | {len(rs)} | {f('pi'):.2f} | {f('bound'):.3f} | {f('realized'):.3f} | {f('realized') / ALPHA:.2f} | {f('cf_good_med'):.3f} / {f('off_med'):.3f} | {f('cf_good_q05'):.3f} / {f('off_q05'):.3f} |")


if __name__ == "__main__":
    main()
