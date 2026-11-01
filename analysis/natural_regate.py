"""Natural off-map runs (4sx, natural_eval.py) re-evaluated at the default points from their saved caches (navcache, exact
counterfactual statistics, route cache; Kaggle dataset nhatlong1103/hmm-natural-cache), e.g. for the rate-limited gate (+NGRr).
No top-K (TAO'26 is not re-run). Two passes: ground-truth init and --nav-init top1.
Usage: natural_regate.py <any dir> <A+B> <desc> [--fams @E30R] [extra oc_curves flags, e.g. --gate-rate]
Output: results/oc_4sx_<A+B>_<desc>_r_s0.json and _top1r_s0.json"""
import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FAMS = sys.argv[sys.argv.index("--fams") + 1] if "--fams" in sys.argv else "@E30R"


def find(root, prefix):
    for d, _, fs in os.walk(root, followlinks=True):
        if any(f.startswith(prefix) for f in fs): return d
    return None


def main():
    pair, desc = sys.argv[2], sys.argv[3]; ds = "4sx:" + pair; tag = ds.replace(":", "_")
    root = "/kaggle/input" if os.path.isdir("/kaggle/input") else sys.argv[1]
    W = os.path.abspath(f"_natr_{tag}_{desc}"); os.makedirs(W, exist_ok=True)
    for pre in ("navcache", "cms", "tao"):                       # Kaggle drops "+" from dataset file names: look for both spellings
        nm = f"{pre}_{tag}_{desc}_s0.npz"
        for cand in (nm, nm.replace("+", "")):
            d = find(root, cand)
            if d:
                dst = os.path.join(W, nm)
                if not os.path.exists(dst): os.symlink(os.path.join(d, cand), dst)
                break
        else:
            print("missing input", nm); sys.exit(1)
    cdir = sdir = tdir = W
    extra = ["--gate-rate"] if "--gate-rate" in sys.argv else []
    base = [sys.executable, os.path.join(HERE, "oc_curves.py"), cdir, ds, desc, "--seeds", "0", "--jobs", "1", "--defaults-only", "--taocache", tdir,
            "--cms", sdir, "--tw", "0.5", "--variants", "--light", "--cms-alpha", "0.05,0.01", "--cms-groups", "cond,loco,online", "--navgate", "--fams", FAMS] + extra
    for sfx, fl in (("_r_s0", []), ("_top1r_s0", ["--nav-init", "top1"])):
        r = subprocess.run(base + ["--out-suffix", sfx] + fl, capture_output=True, text=True)
        print(f"{ds}/{desc}{sfx} rc={r.returncode}", r.stdout[-200:], r.stderr[-800:] if r.returncode else "", flush=True)


if __name__ == "__main__":
    main()
