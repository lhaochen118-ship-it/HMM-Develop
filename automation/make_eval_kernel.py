#!/usr/bin/env python3
"""Run analysis/ evaluation jobs on a Kaggle CPU kernel instead of the local container (user policy).

1. Uploads (or versions) the code dataset `<owner>/dive-vpr-analysis` with analysis/*.py.
2. Writes a CPU/GPU script kernel that mounts the public dump dataset, symlinks every dump into one
   directory, runs the jobs in parallel (one process per core) and saves results/*.json + logs to /kaggle/working.
Then run it with:  python automation/run_kernel.py <kernel_dir> <out_dir>   and copy <out_dir>/results/*.json.

Usage: make_eval_kernel.py <kernel_dir> <slug> "<script> <ds> <desc>;<script> <ds> <desc>;..." [dump_kernels,...] [--gpu]
  --acc2/--acc3/--owner <user>: run under another Kaggle account (export KAGGLE_API_TOKEN for both scripts)
  --gpu : T4 kernel, SELFCAL_DEVICE=cuda (PyTorch backend in selfcal.qm_stats); default CPU/numpy.
  script = eval_all.py | exp9_natural.py | ... ; for exp9_natural.py write "exp9_natural.py <desc>" (dumps auto).
  Any other argument order: put the literal token DUMP where the merged dump directory goes, e.g. "exp10_shiftfix.py salad DUMP".
"""
import sys, os, json, glob, shutil, subprocess

# Descriptor dumps: the PUBLIC dataset nhatlong1103/vpr-descriptor-dumps (any account can mount it, no upload).
# Account = whose token is in KAGGLE_API_TOKEN (default ~/.kaggle/access_token = nhatlong1103):
#   --acc2 (yuan1103), --acc3 (synchan5704), or --owner <username> for any new account.
ACC = 3 if "--acc3" in sys.argv else 2 if "--acc2" in sys.argv else 1
OWNER = sys.argv[sys.argv.index("--owner") + 1] if "--owner" in sys.argv else {1: "nhatlong1103", 2: "yuan1103", 3: "synchan5704"}[ACC]
CODE_DS = f"{OWNER}/dive-vpr-analysis"
_tok = os.path.expanduser(f"~/.kaggle/tok_{OWNER}")                     # per-account token file, if present
if os.path.isfile(_tok): os.environ["KAGGLE_API_TOKEN"] = open(_tok).read().strip()
DUMPS = []
DUMP_DS = ["nhatlong1103/vpr-descriptor-dumps", "nhatlong1103/vpr-dumps-4seasons"]   # + boreas-vpr when published
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPU = "--gpu" in sys.argv; argv = [a for i, a in enumerate(sys.argv) if a not in ("--gpu", "--acc2", "--acc3", "--owner") and sys.argv[i - 1] != "--owner"]
kdir, slug, jobs = argv[1], argv[2], [j.split() for j in argv[3].split(";") if j.strip()]
dumps = argv[4].split(",") if len(argv) > 4 and argv[4] else DUMPS

# --- 1. code dataset
stage = os.path.join(kdir, "_code"); shutil.rmtree(stage, ignore_errors=True); os.makedirs(stage)
for f in glob.glob(os.path.join(ROOT, "analysis", "*.py")) + glob.glob(os.path.join(ROOT, "analysis", "*.sh")):
    shutil.copy(f, stage)
json.dump({"title": "dive-vpr-analysis", "id": CODE_DS, "licenses": [{"name": "CC0-1.0"}]}, open(os.path.join(stage, "dataset-metadata.json"), "w"))
exists = subprocess.run(["kaggle", "datasets", "status", CODE_DS], capture_output=True, text=True).stdout.strip().lower() == "ready"
cmd = ["kaggle", "datasets", "version", "-p", stage, "-m", "update", "-q"] if exists else ["kaggle", "datasets", "create", "-p", stage, "-q"]
r = subprocess.run(cmd, capture_output=True, text=True); print("code dataset:", (r.stdout + r.stderr).strip().splitlines()[-1:])

# --- 2. kernel
runner = r'''
import os, sys, glob, json, shutil, subprocess, time
from concurrent.futures import ThreadPoolExecutor
JOBS = %s
os.environ["SELFCAL_DEVICE"] = "%s"
t0 = time.time()
code = [d for d, _, fs in os.walk("/kaggle/input") if "selfcal.py" in fs][0]
W = "/kaggle/working"; C = os.path.join(W, "code"); shutil.copytree(code, C, dirs_exist_ok=True)
os.makedirs(os.path.join(C, "results"), exist_ok=True); os.makedirs(os.path.join(C, "logs"), exist_ok=True)
D = os.path.join(W, "dump_all")
for meta in [d for d, _, _ in os.walk("/kaggle/input") if os.path.basename(d) == "meta"]:
    src = os.path.dirname(meta)
    for sub in os.listdir(src):
        p = os.path.join(src, sub)
        if not os.path.isdir(p): continue
        os.makedirs(os.path.join(D, sub), exist_ok=True)
        for f in os.listdir(p):
            dst = os.path.join(D, sub, f)
            if not os.path.exists(dst): os.symlink(os.path.join(p, f), dst)
import torch
print("dump dirs:", {s: len(os.listdir(os.path.join(D, s))) for s in sorted(os.listdir(D))}, "| cpus", os.cpu_count(), "| device", os.environ["SELFCAL_DEVICE"], "| cuda", torch.cuda.is_available(), flush=True)
def run(j):
    script, args = j[0], j[1:]
    if "DUMP" in args: cmd = [sys.executable, script] + [D if a == "DUMP" else a for a in args]
    else: cmd = [sys.executable, script] + ([args[0], D, D] if script == "exp9_natural.py" else [D] + args) + (["%%s" %% D] if script == "exp9_natural.py" else [])
    t = time.time(); log = os.path.join(C, "logs", "_".join(j).replace(".py", "") + ".log")
    r = subprocess.run(cmd, cwd=C, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    print(f"done {' '.join(j)} rc={r.returncode} {time.time()-t:.0f}s", flush=True); return r.returncode
with ThreadPoolExecutor(max(1, (os.cpu_count() or 4) - 1)) as ex: rcs = list(ex.map(run, JOBS))
shutil.copytree(os.path.join(C, "results"), os.path.join(W, "results"), dirs_exist_ok=True)
shutil.copytree(os.path.join(C, "logs"), os.path.join(W, "logs"), dirs_exist_ok=True)
if os.path.isdir(os.path.join(C, "figs")): shutil.copytree(os.path.join(C, "figs"), os.path.join(W, "figs"), dirs_exist_ok=True)
shutil.rmtree(D, ignore_errors=True); shutil.rmtree(C, ignore_errors=True)
print("EVAL_DONE", rcs, f"{time.time()-t0:.0f}s", flush=True)
''' % (json.dumps(jobs), "cuda" if GPU else "numpy")
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(runner)
meta = {"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": GPU, "enable_tpu": False, "enable_internet": False,
        "dataset_sources": [CODE_DS] + DUMP_DS, "competition_sources": [], "kernel_sources": dumps, "model_sources": []}
json.dump(meta, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
shutil.rmtree(stage, ignore_errors=True)
print("kernel dir:", kdir, "| jobs:", len(jobs), "| sources:", dumps)
