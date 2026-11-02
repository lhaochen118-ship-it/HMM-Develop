"""Run a list of e36_run.py jobs with a fixed number of worker processes (largest jobs first unless --fifo).
Usage: e36_queue.py <jobs.txt> <workers> -- <e36_run.py fixed args before ds desc seed...>
jobs.txt: one "ds desc seed" per line. Every job's output line goes to stdout."""
import sys, os, subprocess
from multiprocessing.pool import ThreadPool
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    jf, nw = sys.argv[1], int(sys.argv[2]); k = sys.argv.index("--"); fixed = sys.argv[k + 1:]
    pre = [a for a in fixed if not a.startswith("+")]; post = [a[1:] for a in fixed if a.startswith("+")]
    jobs = [l.split() for l in open(jf) if l.strip()]
    def run(j):
        r = subprocess.run([sys.executable, os.path.join(HERE, "e36_run.py")] + pre + j + post, capture_output=True, text=True,
                           env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1"))
        print(" ".join(j), "|", (r.stdout.strip().splitlines() or [""])[-1][:300], r.stderr[-300:] if r.returncode else "", flush=True)
    with ThreadPool(nw) as p: list(p.imap_unordered(run, jobs))


if __name__ == "__main__":
    main()
