#!/usr/bin/env python3
"""Build a Kaggle CPU kernel that runs hmmloc experiment jobs on the cached feature bank (no GPU quota; immune to
restarts of the local container). Feature-bank dumps are mounted as kernel_sources (outputs of the owner's kernels).
Usage: build_cpu.py <out_dir> <owner/slug> <par> <kernel_source,...> JOB [JOB ...]
JOB = "<module> <args...>" e.g. "hmmloc.exp.e07_motionev msls-cph megaloc 0".
Each job runs in its OWN copy of the repo subset (separate registry, no run-id race); outputs land in
/kaggle/working/jobs/<i>/research/{runs,registry,logs}. Merge locally with research/merge_remote_runs.py."""
import os, sys, io, json, tarfile, base64, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pack():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for d, subs, fs in os.walk(os.path.join(ROOT, "hmmloc")):
            subs[:] = [s for s in subs if s != "__pycache__"]
            for f in fs:
                if f.endswith(".py"):
                    p = os.path.join(d, f); tf.add(p, arcname=os.path.relpath(p, ROOT))
        tf.add(os.path.join(ROOT, "research", "registry", "runs.jsonl"), arcname="research/registry/runs.jsonl")
    return base64.b64encode(buf.getvalue()).decode()


RUNNER = r'''
import os, sys, io, json, time, tarfile, base64, subprocess, shutil
from concurrent.futures import ThreadPoolExecutor
T0 = time.time(); W = "/kaggle/working"; FB = os.path.join(W, "fb"); os.makedirs(FB, exist_ok=True)
print("[cpu] vCPU", os.cpu_count(), "| jobs", len(JOBS), "| par", PAR, flush=True)
# feature bank: symlink every mounted kernel output whose folder name is a dump slug -> /kaggle/working/fb/<slug>
for d, subs, fs in os.walk("/kaggle/input"):
    if d.count(os.sep) > 6: subs[:] = []; continue
    b = os.path.basename(d)
    if b in SOURCES and "dump" in subs and not os.path.exists(os.path.join(FB, b)):
        os.symlink(d, os.path.join(FB, b)); subs[:] = []
print("[cpu] feature bank:", sorted(os.listdir(FB)), "missing:", sorted(set(SOURCES) - set(os.listdir(FB))), flush=True)
def run(i):
    jd = os.path.join(W, "jobs", f"{i:02d}"); os.makedirs(jd, exist_ok=True)
    tarfile.open(fileobj=io.BytesIO(base64.b64decode(CODE)), mode="r:gz").extractall(jd)
    os.makedirs(os.path.join(jd, "research", "logs"), exist_ok=True)
    env = dict(os.environ, HMMLOC_FB=FB, OMP_NUM_THREADS=str(max(1, os.cpu_count() // PAR)), PYTHONPATH=jd)
    t = time.time(); log = os.path.join(jd, "research", "logs", "job.log")
    rc = subprocess.run([sys.executable, "-m"] + JOBS[i].split(), cwd=jd, env=env, stdout=open(log, "w"), stderr=subprocess.STDOUT).returncode
    tail = open(log).read().strip().splitlines()[-3:]
    print(f"[cpu] job {i} '{JOBS[i]}' rc={rc} {time.time() - t:.0f}s | {tail}", flush=True)
    return rc
with ThreadPoolExecutor(PAR) as ex:
    rcs = list(ex.map(run, range(len(JOBS))))
json.dump({"jobs": JOBS, "rc": rcs, "wall_min": (time.time() - T0) / 60}, open(os.path.join(W, "cpu_manifest.json"), "w"), indent=1)
for i in range(len(JOBS)):                               # keep only results (code copies are not needed)
    jd = os.path.join(W, "jobs", f"{i:02d}"); shutil.rmtree(os.path.join(jd, "hmmloc"), ignore_errors=True)
shutil.rmtree(FB, ignore_errors=True)
print("CPU_DONE rc", rcs, f"{(time.time() - T0) / 60:.1f} min", flush=True)
'''


def main(a):
    out, kid, par, srcs = a[0], a[1], int(a[2]), a[3].split(","); jobs = a[4:]
    os.makedirs(out, exist_ok=True)
    slugs = [s.split("/")[1] for s in srcs]
    with open(os.path.join(out, "run.py"), "w") as f:
        f.write(f'"""hmmloc CPU jobs (kaggle/cpu/build_cpu.py, branch claude/nice-fermi-l7bzd6)"""\n'
                f"JOBS = {json.dumps(jobs)}\nPAR = {par}\nSOURCES = {json.dumps(slugs)}\nCODE = \"{pack()}\"\n" + RUNNER)
    meta = {"id": kid, "title": kid.split("/")[1], "code_file": "run.py", "language": "python", "kernel_type": "script",
            "is_private": True, "enable_gpu": False, "enable_tpu": False, "enable_internet": False,
            "dataset_sources": [], "kernel_sources": srcs, "competition_sources": [], "model_sources": []}
    json.dump(meta, open(os.path.join(out, "kernel-metadata.json"), "w"), indent=2)
    print(f"built {out}: {len(jobs)} jobs, par {par}, sources {slugs}, run.py {os.path.getsize(os.path.join(out, 'run.py')) / 1e3:.0f} KB")


if __name__ == "__main__":
    main(sys.argv[1:])
