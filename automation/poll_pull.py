#!/usr/bin/env python3
"""Poll an already-running Kaggle kernel and pull its output when done (no push).
Usage: python poll_pull.py <user/slug> <output_dir>"""
import sys, subprocess, time, os
kid, outdir = sys.argv[1], sys.argv[2]
def kg(*a):
    r = subprocess.run(["kaggle"] + list(a), capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()
t0 = time.time(); last = None; s = ""
while True:
    out = kg("kernels", "status", kid); low = out.lower()
    if low != last:
        print(time.strftime("%H:%M:%S"), out[:140], flush=True); last = low
    if ".complete" in low or ".error" in low or ".cancel" in low:
        s = low.split(".")[-1].strip('"').strip(); break
    if time.time() - t0 > 5400:
        print("TIMEOUT", flush=True); s = "timeout"; break
    time.sleep(20)
os.makedirs(outdir, exist_ok=True)
print(f"=== PULL ({s}) -> {outdir} ===", flush=True)
print(kg("kernels", "output", kid, "-p", outdir), flush=True)
print("FILES:", os.listdir(outdir), flush=True)
print(f"POLL_DONE:{s}", flush=True)
