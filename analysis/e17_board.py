"""Entry 17 (pre-registered 2026-11-05 16:42 UTC): independent confirmation of OWF-HWA-S5 on a fresh seed group and external SOTA on the
same runs. Merges per-run results:
  --inc  <owf_hcal.py JSON>         variants INC (OWF-HWA-S5) and H (its OWF-H branch)
  --hsi  <dir of hsi_*_<tag>.json>  HSI-VN (hsi_fresh.py on the fresh caches)
  --sota <dir of sota_*_<tag>.json> TAO26, Xu21, Claxton24, top1, oracle (sota_job.py)
then prints the per-dataset table (hcal_board.py) and evaluates C1-C4. Usage:
  e17_board.py --inc f.json --hsi dir --sota dir --seeds 55-57 --out merged.json [--md out.md]"""
import sys, os, glob, json, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ALPHA = 0.05


def key(ds, desc, seed):
    return f"{ds.replace(':', '_')}_{desc}_s{int(seed)}"


def main():
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    s0, s1 = [int(x) for x in opt("--seeds").split("-")]; M = {}
    for t, r in json.load(open(opt("--inc"))).items():
        if s0 <= int(r["seed"]) <= s1:
            M.setdefault(t, dict(ds=r["ds"], seed=r["seed"], variants={})); M[t]["variants"].update({k: v for k, v in r["variants"].items() if k in ("INC", "H")})
    for f in glob.glob(os.path.join(opt("--hsi"), "**", "hsi_*.json"), recursive=True):
        j = json.load(open(f)); t = key(j["ds"], j["desc"], j["seed"])
        if t in M and "HSI-VN" in j["variants"]: M[t]["variants"]["HSI-VN"] = {k: j["variants"]["HSI-VN"][k] for k in ("recall", "seg_FAR", "err_mean", "FL")}
    for f in glob.glob(os.path.join(opt("--sota"), "**", "sota_*.json"), recursive=True):
        j = json.load(open(f)); t = key(j["ds"], j["desc"], j["seed"])
        if t in M: M[t]["variants"].update(j["variants"])
    json.dump(M, open(opt("--out"), "w"))
    vs = ["INC", "H", "HSI-VN", "TAO26", "Xu21", "Claxton24", "top1", "oracle"]
    cmd = [sys.executable, os.path.join(HERE, "hcal_board.py"), opt("--out"), "--ref", "INC", "--variants", ",".join(vs)] + (["--md", opt("--md")] if opt("--md") else [])
    print(subprocess.run(cmd, capture_output=True, text=True).stdout)
    keys = sorted(k for k, r in M.items() if all(v in r["variants"] for v in vs))
    dss = sorted({M[k]["ds"] for k in keys}); g = lambda v, f: np.array([M[k]["variants"][v][f] for k in keys])
    def valid(v):
        worst = max(np.mean([M[k]["variants"][v]["seg_FAR"] for k in keys if M[k]["ds"] == d]) for d in dss)
        nab = int((g(v, "seg_FAR") > ALPHA).sum()); return worst <= ALPHA and nab <= 2, worst, nab
    def diff(v, ref="INC"):
        d = g(ref, "recall") - g(v, "recall"); rng = np.random.default_rng(0)
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]; return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    print(f"Entry 17 criteria on {len(keys)} runs (seeds {s0}-{s1}):")
    ok1, w, nab = valid("INC"); print(f"  C1 validity INC: worst dataset mean segFAR {w:.4f}, runs > alpha {nab}/{len(keys)} -> {'MET' if ok1 else 'NOT MET'}")
    m, lo, hi = diff("HSI-VN"); ok2 = m >= 0.08 and lo > 0
    print(f"  C2 INC - HSI-VN recall {m:+.4f} [{lo:+.4f}, {hi:+.4f}] -> {'MET' if ok2 else 'NOT MET'}")
    ok3 = True
    for v in ("TAO26", "Xu21", "Claxton24"):
        vv, w, nab = valid(v); m, lo, hi = diff(v); o = (not vv) or lo > 0; ok3 &= o
        print(f"  C3 {v}: valid {vv} (worst mean segFAR {w:.4f}, runs > alpha {nab}); INC - {v} recall {m:+.4f} [{lo:+.4f}, {hi:+.4f}] -> {'MET' if o else 'NOT MET'}")
    ni, nh = np.nanmean(g("INC", "err_mean")), np.nanmean(g("HSI-VN", "err_mean")); ok4 = ni <= nh
    print(f"  C4 navigation INC {ni:.2f} m vs HSI-VN {nh:.2f} m -> {'MET' if ok4 else 'NOT MET'}")
    print("  DECISION:", "CONFIRMED (C1-C4 met)" if ok1 and ok2 and ok3 and ok4 else "NOT CONFIRMED (see the failing criterion)")


if __name__ == "__main__":
    main()
