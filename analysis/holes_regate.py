"""Hole-ratio runs (10 % / 50 %) re-evaluated at the default points with the Entry 30 gate fixes (navrisk.py: streak release,
uncertainty floor). Inputs: the holes rule caches (nhatlong1103/hmm-navcache-holes, dirs d10 / d50) and the exact
counterfactual statistics already computed by holes_eval.py (nhatlong1103/hmm-holes-cms-exact, dirs hcms_d10 / hcms_d50 with
cms_<ds>_<desc>_s<seed>.npz and the route caches tao_*.npz). No top-K needed (TAO'26 is not re-run).
Usage: holes_regate.py <any mounted dir> <ratio 10|50> <ds> <desc> --seeds 0,1,2 [--fams @E30H]
Output: results/oc_<ds>_<desc>_d<ratio>g_s<seed>.json"""
import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = sys.argv[sys.argv.index("--seeds") + 1].split(",") if "--seeds" in sys.argv else ["0", "1", "2"]
FAMS = sys.argv[sys.argv.index("--fams") + 1] if "--fams" in sys.argv else "@E30H"


def find(root, name, prefix):
    for d, _, fs in os.walk(root, followlinks=True):
        if os.path.basename(d) == name and any(f.startswith(prefix) for f in fs): return d
    return None


def main():
    _, ratio, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    root = "/kaggle/input" if os.path.isdir("/kaggle/input") else sys.argv[1]
    cdir, sdir = find(root, f"d{ratio}", "navcache_"), find(root, f"hcms_d{ratio}", "cms_")
    if not cdir or not sdir: print("missing inputs", cdir, sdir); sys.exit(1)
    for s in SEEDS:
        cmd = [sys.executable, os.path.join(HERE, "oc_curves.py"), cdir, ds, desc, "--seeds", s, "--jobs", "1", "--defaults-only",
               "--out-suffix", f"_d{ratio}g_s{s}", "--taocache", sdir, "--cms", sdir, "--variants", "--light", "--cms-alpha", "0.05,0.01",
               "--navgate", "--fams", FAMS]
        r = subprocess.run(cmd, capture_output=True, text=True); print(f"d{ratio} {ds}/{desc} s{s} rc={r.returncode}", r.stdout[-200:], r.stderr[-800:] if r.returncode else "", flush=True)


if __name__ == "__main__":
    main()
