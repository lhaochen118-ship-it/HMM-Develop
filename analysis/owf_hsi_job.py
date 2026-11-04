"""One fresh-set job of the AUTOLOOP (OWF estimator + HSI decision): run the open-world filter on a run's navcache, then the OWF+HSI hybrid
(owf_hybrid.py) on the frames it just wrote, in the same kernel (no round trip). Usage (kernel tokens resolved by the runner):
  owf_hsi_job.py <cache_dir> <dump_dir> <ds> <desc> <seed> --tag r40 [--modes xm0.5:HSI-VN,HSI-VMN+xmc0.5:HSI-VN] [owf.py options]
Writes results/owf_<ds>_<desc>_s<seed>_<tag>.json, results/fr_..._b1.npz and results/hsi_<ds>_<desc>_s<seed>_<tag><mode>.json."""
import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    cdir, dump, ds, desc, seed = sys.argv[1:6]; rest = sys.argv[6:]
    def pop(k, d):
        if k in rest: i = rest.index(k); v = rest[i + 1]; del rest[i:i + 2]; return v
        return d
    tag = pop("--tag", "r40"); modes = pop("--modes", "xm0.5:HSI-VN,HSI-VMN")
    t = f"{ds.replace(':', '_')}_{desc}_s{seed}_{tag}"; os.makedirs("results", exist_ok=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, "owf.py"), cdir, dump, ds, desc, seed, "--out", f"results/owf_{t}.json",
                        "--frames", f"results/fr_{t}"] + rest)
    if r.returncode: sys.exit(r.returncode)
    rc = 0
    for m in modes.replace(";", "+").split("+"):                       # modes separated by "+" (";" separates jobs in a groups file)
        mode, _, var = m.partition(":")
        r = subprocess.run([sys.executable, os.path.join(HERE, "owf_hybrid.py"), "results", cdir, f"w_{t}_{mode}", ds, desc, seed, "--mode", mode,
                            "--variants", var, "--tag", f"{tag}{mode.replace('.', '')}", "--ftag", f"_{tag}"])
        rc = rc or r.returncode
    sys.exit(rc)


if __name__ == "__main__":
    main()
