#!/usr/bin/env python3
"""Push a Kaggle kernel, poll until it finishes, pull its output.
Usage: python kaggle_run.py <kernel_dir> <output_dir>
Prints progress; writes a STATUS line the parent can grep."""
import sys, subprocess, time, os, json, re

kdir, outdir = sys.argv[1], sys.argv[2]
kid = json.load(open(os.path.join(kdir, "kernel-metadata.json")))["id"]

def kg(*args):
    r = subprocess.run(["kaggle"] + list(args), capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()

print(f"=== PUSH {kid} ===", flush=True)
push_out = kg("kernels", "push", "-p", kdir)
print(push_out, flush=True)
if "error" in push_out.lower() and "pushed" not in push_out.lower():
    print("STATUS=PUSH_FAILED", flush=True); sys.exit(1)

time.sleep(8)
t0 = time.time()
last = None
s = ""
while True:
    out = kg("kernels", "status", kid)
    low = out.lower()                       # e.g. 'has status "KernelWorkerStatus.COMPLETE"'
    if low != last:
        print(time.strftime("%H:%M:%S"), out[:140], flush=True); last = low
    if ".complete" in low or ".error" in low or ".cancel" in low:
        s = low.split(".")[-1].strip('"').strip(); break
    if time.time() - t0 > 5400:
        print("STATUS=TIMEOUT", flush=True); s = "timeout"; break
    time.sleep(20)

os.makedirs(outdir, exist_ok=True)
print(f"=== PULL -> {outdir} ===", flush=True)
print(kg("kernels", "output", kid, "-p", outdir), flush=True)
print("FILES:", os.listdir(outdir), flush=True)
print(f"STATUS=DONE:{s}", flush=True)
