#!/usr/bin/env python3
"""Merge runs produced on Kaggle CPU kernels (kaggle/cpu/build_cpu.py) into the local registry.
Each remote job had its own copy of research/registry/runs.jsonl (snapshot of the local one at build time); rows beyond
that snapshot are new. They get a fresh local run_id (next registry number, same task suffix); the run folder is copied
to research/runs/<new id>; the remote id is kept as `remote_run_id`, plus `remote_kernel`.
Usage: merge_remote_runs.py <kernel_output_dir> <owner/slug>"""
import sys, os, json, re, shutil, glob, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "research", "registry", "runs.jsonl")
out, kid = sys.argv[1], sys.argv[2]
_lines = open(REG).read().splitlines(); _rows = [json.loads(l) for l in _lines]
local_lines = set(_lines)                                 # rows a remote job inherited from the build-time snapshot are
                                                          # byte-identical to local lines -> never re-merged
local_ids = {r["run_id"] for r in _rows}
local_stamp = {(r["run_id"], r.get("date_utc")) for r in _rows}   # inherited row edited locally later (e.g. superseded)
merged_keys = {(r.get("remote_kernel"), r.get("remote_run_id")) for r in _rows if r.get("remote_kernel")}
n_local = sum(1 for _ in open(REG)); added = 0
for jd in sorted(glob.glob(os.path.join(out, "jobs", "*"))):
    reg = os.path.join(jd, "research", "registry", "runs.jsonl")
    if not os.path.exists(reg):
        continue
    for line in open(reg).read().splitlines():
        if not line.strip() or line in local_lines:
            continue
        row = json.loads(line)
        if (row["run_id"], row.get("date_utc")) in local_stamp or (kid, row["run_id"]) in merged_keys:          # this kernel's row was merged before (idempotent re-run)
            continue
        old = row["run_id"]; suffix = old.split("_", 1)[1]
        n_local += 1; new = f"{old.split('-')[0]}-{n_local:03d}_{suffix}"
        src = os.path.join(jd, "research", "runs", old)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(ROOT, "research", "runs", new), dirs_exist_ok=True)
        row.update(run_id=new, remote_run_id=old, remote_kernel=kid, artifacts=f"research/runs/{new}")
        if not row.get("git_commit"):                   # no git inside the kernel: code = local HEAD at build time
            import subprocess
            row["git_commit"] = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() + "(remote)"
        with open(REG, "a") as f:
            f.write(json.dumps(row, default=float) + "\n")
        log = os.path.join(jd, "research", "logs", "job.log")
        if os.path.exists(log):
            shutil.copy(log, os.path.join(ROOT, "research", "logs", f"remote_{new}.log"))
        local_ids.add(new); added += 1
        print("merged", old, "->", new)
print("added", added, "rows")
