#!/usr/bin/env python3
"""Pull the outputs of the Kaggle kernels listed in handoff/RUNNING_KERNELS.md (table rows `| run | `acc/slug` | ...`)
and copy their results/*.json into analysis/results/, in table order (later runs supersede earlier ones).
Kernels still RUNNING are skipped and reported. Usage: pull_kernels.py [out_dir=/tmp/kpull] [--only run1,run2]"""
import sys, os, re, glob, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
if only: args = [a for a in args if a != ",".join(only)]
out = args[0] if args else "/tmp/kpull"
rows = re.findall(r"^\| (\w+) \| `([\w-]+)/([\w-]+)` \|", open(os.path.join(ROOT, "handoff", "RUNNING_KERNELS.md")).read(), re.M)
pending = []
for run, acc, slug in rows:
    if only and run not in only: continue
    env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser(f"~/.kaggle/tok_{acc}")).read().strip())
    st = subprocess.run(["kaggle", "kernels", "status", f"{acc}/{slug}"], capture_output=True, text=True, env=env).stdout
    if "COMPLETE" not in st:
        pending.append((f"{acc}/{slug}", st.strip()[-40:])); continue
    d = os.path.join(out, slug); os.makedirs(d, exist_ok=True)
    subprocess.run(["kaggle", "kernels", "output", f"{acc}/{slug}", "-p", d, "-o"], capture_output=True, text=True, env=env)
    res = glob.glob(os.path.join(d, "results", "*.json")) + glob.glob(os.path.join(d, "*.json"))
    for f in res:
        if os.path.basename(f).startswith(("hmmfix_", "nav_", "cert_", "natural_", "hmmdiag_")): shutil.copy(f, os.path.join(ROOT, "analysis", "results"))
    print(f"{run:6s} {acc}/{slug}: {len(res)} results", flush=True)
for k, s in pending: print("not complete:", k, s)
