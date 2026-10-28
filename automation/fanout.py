#!/usr/bin/env python3
"""Spread evaluation jobs over every Kaggle account's GPU slots (2 T4 sessions per account) and run them all.
Tokens: ~/.kaggle/tok_<username> (one file per account). Jobs are split round-robin into `n_kernels` kernels, each
kernel goes to the next free (account, slot); kernels beyond 2 x #accounts become CPU kernels (use only for light jobs).
Usage: fanout.py <work_dir> <slug_prefix> <jobs_file|"job;job;..."> [n_kernels=all GPU slots] [--accounts a,b,...] [--cpu]
Each kernel: <work_dir>/<slug>/ (kernel dir), <work_dir>/<slug>_out/ (outputs), <work_dir>/<slug>.log (runner log).
Prints one line per kernel; waits for all runners; then copies every results/*.json into analysis/results/."""
import sys, os, glob, subprocess, shutil, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS = sorted(os.path.basename(f)[4:] for f in glob.glob(os.path.expanduser("~/.kaggle/tok_*")))
ACCOUNTS = ["nhatlong1103"] + [a for a in ACCOUNTS if a != "nhatlong1103"]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if "--accounts" in sys.argv: ACCOUNTS = sys.argv[sys.argv.index("--accounts") + 1].split(","); args = [a for a in args if a != ",".join(ACCOUNTS)]
work, prefix, jobs = args[0], args[1], args[2]
jobs = [j.strip() for j in (open(jobs).read().replace("\n", ";") if os.path.isfile(jobs) else jobs).split(";") if j.strip()]
slots = [(a, s) for s in (0, 1) for a in ACCOUNTS]                       # spread over accounts first
nk = min(int(args[3]) if len(args) > 3 else len(slots), len(jobs))
os.makedirs(work, exist_ok=True); procs = []
for k in range(nk):
    part = jobs[k::nk]; acc, _ = slots[k % len(slots)]; gpu = k < len(slots) and "--cpu" not in sys.argv
    slug = f"{prefix}-{k + 1}"; kd = os.path.join(work, slug)
    cmd = [sys.executable, os.path.join(ROOT, "automation", "make_eval_kernel.py"), kd, slug, ";".join(part), "", "--owner", acc] + (["--gpu"] if gpu else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"{slug}: {acc} {'GPU' if gpu else 'CPU'} {len(part)} jobs | {(r.stdout + r.stderr).strip().splitlines()[-1][:60]}", flush=True)
time.sleep(30)                                                             # let the code datasets finish versioning
for acc in sorted({slots[k % len(slots)][0] for k in range(nk)}):
    env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser(f"~/.kaggle/tok_{acc}")).read().strip())
    for _ in range(40):
        if subprocess.run(["kaggle", "datasets", "status", f"{acc}/dive-vpr-analysis"], capture_output=True, text=True, env=env).stdout.strip().endswith("ready"): break
        time.sleep(10)
for k in range(nk):
    slug = f"{prefix}-{k + 1}"
    procs.append(subprocess.Popen([sys.executable, os.path.join(ROOT, "automation", "run_kernel.py"), os.path.join(work, slug),
                                   os.path.join(work, slug + "_out"), "600", "3", "14400"], stdout=open(os.path.join(work, slug + ".log"), "w"), stderr=subprocess.STDOUT))
    time.sleep(2)
print(f"launched {nk} kernels", flush=True)
for k, p in enumerate(procs):
    p.wait(); slug = f"{prefix}-{k + 1}"; log = open(os.path.join(work, slug + ".log")).read()
    res = glob.glob(os.path.join(work, slug + "_out", "results", "*.json"))
    for f in res: shutil.copy(f, os.path.join(ROOT, "analysis", "results"))
    print(f"{slug}: {'OK' if 'STATUS=DONE:complete' in log else 'FAILED'} {len(res)} results, rc!=0: {log.count('rc=') - log.count('rc=0')}", flush=True)
