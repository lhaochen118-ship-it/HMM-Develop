"""Sensitivity of the decision layer (RESEARCH_LOG Entry 32): every a-priori constant of the proposed rules is moved one at a
time around its default, on the cached exact counterfactual statistics (no recomputation of the statistics).
Constants (default): W onset window (H = 10), wr route weight in the e-value mixture (0.5), p presence transition (0.01),
g agreement radius of +G in excl (1), shd SH shape tolerance factor (1), beta gate quantile (0.05), R gate release length (H = 10).
Usage: sens_eval.py <cache dir> <topk dir> <tao dir> <cms dir> <ds> <desc> <seed>
Output: results/oc_<ds>_<desc>_sv<name>_s<seed>.json (families @E32S, --gate-rate)"""
import sys, os, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANTS = [("W5", "W=5"), ("W20", "W=20"), ("wr25", "wr=0.25"), ("wr100", "wr=1.0"), ("p005", "p=0.005"), ("p02", "p=0.02"),
            ("g05", "g=0.5"), ("g2", "g=2"), ("shd05", "shd=0.5"), ("shd2", "shd=2"), ("b01", "beta=0.01"), ("b10", "beta=0.1"),
            ("R5", "R=5"), ("R20", "R=20")]


def main():
    cdir, tkd, tcd, cmd_, ds, desc, seed = sys.argv[1:8]
    for name, kv in VARIANTS:
        t = time.time()
        cmd = [sys.executable, os.path.join(HERE, "oc_curves.py"), cdir, ds, desc, "--seeds", seed, "--jobs", "1", "--defaults-only",
               "--out-suffix", f"_sv{name}_s{seed}", "--topk", tkd, "--taocache", tcd, "--cms", cmd_, "--tw", "0.5", "--variants", "--light",
               "--cms-alpha", "0.05,0.01", "--cms-groups", "cond", "--navgate", "--gate-rate", "--fams", "@E32S", "--sens", kv]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"{ds}/{desc} s{seed} {name} rc={r.returncode} {time.time() - t:.0f}s", r.stderr[-600:] if r.returncode else "", flush=True)


if __name__ == "__main__":
    main()
