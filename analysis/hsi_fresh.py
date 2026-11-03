"""Fresh confirmation runs: build nav_demo caches for NEW hole layouts (seeds seed0 .. seed0+n-1, never used before) from the
descriptor dumps, evaluate HSI variants on them, then delete the caches (kernel outputs stay small; regenerating is cheap and
bit-exact: the same code reproduces the public seed-0 caches).
Usage (kernel runner prepends the dump dir): hsi_fresh.py <dump> <ds> <desc> <seed0> <n> [hsi_eval options: --variants ... --tag ...]"""
import os, sys, subprocess, shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    dump, ds, desc, s0, n = sys.argv[1:6]; rest = sys.argv[6:]; s0, n = int(s0), int(n)
    work = os.path.join(os.getcwd(), f"fresh_{ds.replace(':', '_')}_{desc}_{s0}")
    os.makedirs(work, exist_ok=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, "nav_demo.py"), dump, ds, desc, str(n), "--seed0", str(s0), "--cache", "--cache-only"], cwd=work)
    print("nav_demo rc", r.returncode, flush=True)
    if r.returncode: sys.exit(r.returncode)
    r = subprocess.run([sys.executable, os.path.join(HERE, "hsi_eval.py"), os.path.join(work, "results"), ds, desc, f"{s0}-{s0 + n - 1}"] + rest)
    shutil.rmtree(work, ignore_errors=True)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
