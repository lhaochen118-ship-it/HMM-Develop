#!/usr/bin/env python3
"""After a container restart: re-attach every unfinished kernel of the active runs (names listed one per line in
<runs>/active_runs.txt) and pull + copy their results (automation/reattach.py). Idempotent: kernels whose runner or
attach log already ends with STATUS=DONE, and kernels already being monitored, are skipped.
Usage: resume.py <runs_dir>"""
import sys, os, glob, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
runs = sys.argv[1]
active = [l.strip() for l in open(os.path.join(runs, "active_runs.txt")) if l.strip()]
ps = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
todo = []
for r in active:
    if f"{os.path.join(runs, r)} " in ps: continue                 # its fanout is alive (it monitors its own kernels)
    for meta in sorted(glob.glob(os.path.join(runs, r, "*", "kernel-metadata.json"))):
        kd = os.path.dirname(meta)
        logs = [kd + ".log", kd + ".attach.log"]
        done = any(os.path.isfile(l) and ("STATUS=DONE" in open(l).read() or open(l).read().rstrip().endswith("STATUS=PUSH_FAILED"))
                   for l in logs)
        if not done and kd + " " not in ps + " ": todo.append(kd)
print(f"{len(todo)} kernels to re-attach", flush=True)
if todo:
    subprocess.Popen([sys.executable, os.path.join(ROOT, "automation", "reattach.py")] + todo,
                     stdout=open(os.path.join(runs, "resume.log"), "a"), stderr=subprocess.STDOUT, start_new_session=True)
