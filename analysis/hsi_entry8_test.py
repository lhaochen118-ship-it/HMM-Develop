"""Entry 8 pre-registered test (RESEARCH_LOG): T1-T4 for a candidate vs HSI-rot-m-sc on the seed 13-15 test set.
Usage: hsi_entry8_test.py <results_dir> [candidate ...]"""
import sys, os, glob, json
import numpy as np


def main():
    rd = sys.argv[1]; cands = sys.argv[2:] or ["HSI-VN", "HSI-VMN"]; ref = "HSI-rot-m-sc"
    R = [json.load(open(f)) for f in glob.glob(os.path.join(rd, "hsi_*.json"))]
    R = [r for r in R if all(v in r["variants"] for v in cands + [ref])]
    print(f"runs {len(R)}")
    for c in cands:
        seg = np.array([r["variants"][c]["seg_FAR"] for r in R]); nv = int((seg > 0.05).sum())
        byds = {}
        for r in R: byds.setdefault(r["ds"], []).append(r)
        dmeans = {ds: np.mean([r["variants"][c]["seg_FAR"] for r in L]) for ds, L in byds.items()}
        t1 = nv <= 0.05 * len(R) and all(v <= 0.05 for v in dmeans.values())
        d = np.array([r["variants"][c]["recall"] - r["variants"][ref]["recall"] for r in R])
        bs = [np.mean(np.random.default_rng(i).choice(d, len(d))) for i in range(4000)]
        t2 = d.mean() >= 0.01
        cmu = [r for r in R if r["ds"] == "cmu"]
        dc = np.mean([r["variants"][c]["recall"] - r["variants"][ref]["recall"] for r in cmu])
        lk = lambda v: sum(r["variants"][v].get("frac_c", 1) < 0.1 for r in cmu)
        t3 = dc >= 0.03 and lk(c) <= lk(ref) / 2
        de = np.nanmean([r["variants"][c]["err_mean"] - r["variants"][ref]["err_mean"] for r in R]); t4 = de <= 0.5
        print(f"{c}: T1 {'PASS' if t1 else 'FAIL'} (runs>0.05 {nv}/{len(R)}; max dataset mean {max(dmeans.values()):.4f}) | "
              f"T2 {'PASS' if t2 else 'FAIL'} (d_rec {d.mean():+.4f}, 95% [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}], wins {(d > 0).sum()}/{len(d)}) | "
              f"T3 {'PASS' if t3 else 'FAIL'} (CMU d {dc:+.4f}; locked {lk(c)} vs {lk(ref)}) | T4 {'PASS' if t4 else 'FAIL'} (d_err {de:+.2f} m) "
              f"=> {'ALL PASS' if t1 and t2 and t3 and t4 else 'not all'}")


if __name__ == "__main__":
    main()
