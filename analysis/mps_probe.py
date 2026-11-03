"""Throughput probe on one L4 session: the same forward-null jobs (e37_fwd.py) run with N parallel processes, first plain (CUDA
time-slicing between the processes of a GPU), then under the CUDA Multi-Process Service (MPS: kernels of different processes run
concurrently on a GPU). Outputs of the two phases are compared bit by bit (MPS does not change the arithmetic).
Usage (kernel job, alone in its kernel so that every GPU is visible): mps_probe.py <dump> <navcache_dir> <jobs.txt> [--par 46]
jobs.txt lines: "<ds> <desc> <seed> <k/n>" (or inline "ds:desc:seed:k/n,ds:desc:seed:k/n,...")."""
import sys, os, time, subprocess, shutil, glob
from concurrent.futures import ThreadPoolExecutor
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))


def phase(tag, jobs, dump, nd, par, ngpu, env0):
    os.makedirs(tag, exist_ok=True); t0 = time.time()
    def run(ij):
        i, (ds, desc, seed, kn) = ij
        env = dict(env0, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", CUDA_VISIBLE_DEVICES=str(i % ngpu))
        r = subprocess.run([sys.executable, os.path.join(HERE, "e37_fwd.py"), dump, nd, ds, desc, seed, kn], cwd=tag, capture_output=True, text=True, env=env)
        return r.returncode, (r.stdout.strip().splitlines() or [""])[-1], r.stderr[-500:]
    with ThreadPoolExecutor(par) as ex: out = list(ex.map(run, enumerate(jobs)))
    wall = time.time() - t0; ms = []
    for rc, line, err in out:
        if rc: print(tag, "job failed:", err, flush=True)
        if "ms/frame" in line: ms.append(float(line.split("(")[1].split(" ms/frame")[0]))
    print(f"{tag}: {len(jobs)} jobs, wall {wall:.0f}s, ms/frame mean {np.mean(ms):.1f} (min {np.min(ms):.1f}, max {np.max(ms):.1f})", flush=True)
    return wall


def main():
    dump, nd, jf = sys.argv[1:4]; par = int(sys.argv[sys.argv.index("--par") + 1]) if "--par" in sys.argv else 46
    jobs = [l.split() for l in open(jf) if l.strip()] if os.path.isfile(jf) else [j.split(":") for j in jf.split(",") if j]   # or "ds:desc:seed:k/n,..."
    import torch
    ngpu = torch.cuda.device_count(); print("gpus", ngpu, "cpus", os.cpu_count(), flush=True)
    w0 = phase("plain", jobs, dump, nd, par, ngpu, dict(os.environ))
    mps = shutil.which("nvidia-cuda-mps-control"); print("nvidia-cuda-mps-control:", mps, flush=True)
    if not mps: return
    env = dict(os.environ, CUDA_MPS_PIPE_DIRECTORY="/tmp/mps_pipe", CUDA_MPS_LOG_DIRECTORY="/tmp/mps_log")
    for d in ("/tmp/mps_pipe", "/tmp/mps_log"): os.makedirs(d, exist_ok=True)
    r = subprocess.run([mps, "-d"], env=env, capture_output=True, text=True); print("mps start rc", r.returncode, r.stdout, r.stderr, flush=True)
    w1 = phase("mps", jobs, dump, nd, par, ngpu, env)
    subprocess.run(f"echo quit | {mps}", shell=True, env=env)
    same = all(np.array_equal(np.load(a)[k], np.load(b)[k], equal_nan=np.load(a)[k].dtype.kind == "f")
               for a in sorted(glob.glob("plain/results/*.npz")) for b in [a.replace("plain/", "mps/")] for k in np.load(a).files)
    print(f"MPS speed-up {w0 / w1:.2f}x (wall {w0:.0f}s -> {w1:.0f}s), outputs identical: {same}", flush=True)


if __name__ == "__main__":
    main()
