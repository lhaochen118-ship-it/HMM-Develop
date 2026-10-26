#!/usr/bin/env python3
"""Poll a running kernel's partial log until the GPU-name line appears (or it ends).
Usage: python gpu_watch.py <user/slug> <tmp_dir>"""
import sys, subprocess, time, os, glob, re
kid, d = sys.argv[1], sys.argv[2]
def kg(*a): return subprocess.run(["kaggle"]+list(a), capture_output=True, text=True).stdout
for i in range(45):                        # ~30 min
    os.makedirs(d, exist_ok=True)
    subprocess.run(["kaggle","kernels","output",kid,"-p",d], capture_output=True, text=True)
    t = "".join(open(f, encoding="utf-8", errors="ignore").read() for f in glob.glob(d+"/*.log"))
    gpu = re.findall(r'(Tesla T4|RTX ?PRO ?6000|RTX ?Pro ?6000|Blackwell|GPU: [^\\"]+)', t, re.I)
    if gpu:
        print("GPU_FOUND:", sorted(set(gpu))[:6], flush=True); break
    st = kg("kernels","status",kid).lower()
    if ".complete" in st or ".error" in st or ".cancel" in st:
        print("ENDED_BEFORE_GPU_LINE status=", st[:80], flush=True); break
    print(f"try {i}: still provisioning (0 cell output)", flush=True)
    time.sleep(40)
print("WATCH_DONE", flush=True)
