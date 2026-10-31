"""Sensitivity of CMS to the surgery radius rho = off_d + k * excl (Entry 28; pre-registered value k = 1).
Usage: rho_eval.py <cache_dir> <topk_dir> <taocache_dir> <ds> <desc> --seeds 0 --rho-add k [--fams a,b]
Output: results/oc_<ds>_<desc>_rho<k>_s<seed>.json (CMS families only)."""
import sys, os, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cms

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")] if "--seeds" in sys.argv else [0]
K = float(sys.argv[sys.argv.index("--rho-add") + 1]) if "--rho-add" in sys.argv else 1.0
FAMS = sys.argv[sys.argv.index("--fams") + 1] if "--fams" in sys.argv else "CMS*"


def main():
    cdir, tkd, tcd, ds, desc = sys.argv[1:6]; tag = ds.replace(":", "_")
    W = os.path.abspath(f"_rho{K:g}_{tag}_{desc}"); os.makedirs(W, exist_ok=True); os.makedirs("results", exist_ok=True)
    for s in SEEDS:
        z = np.load(os.path.join(cdir, f"navcache_{tag}_{desc}_s{s}.npz"), allow_pickle=True)
        rho = cms.OFF_D.get(ds.split(":")[0], 40.0) + K * float(z["excl"])
        st = cms.cms_stats(z, np.load(os.path.join(tkd, f"topk_{tag}_{desc}_s{s}.npz")), rho=rho, ds=ds)
        np.savez_compressed(os.path.join(W, f"cms_{tag}_{desc}_s{s}.npz"), **st)
        cmd = [sys.executable, os.path.join(HERE, "oc_curves.py"), cdir, ds, desc, "--seeds", str(s), "--jobs", "1", "--defaults-only",
               "--out-suffix", f"_rho{K:g}_s{s}", "--topk", tkd, "--taocache", tcd, "--cms", W, "--cms-alpha", "0.05,0.01", "--fams", FAMS]
        r = subprocess.run(cmd, capture_output=True, text=True); print(ds, desc, s, "rho", rho, r.returncode, r.stderr[-300:] if r.returncode else "", flush=True)


if __name__ == "__main__":
    main()
