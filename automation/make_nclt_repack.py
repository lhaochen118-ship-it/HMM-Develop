#!/usr/bin/env python3
"""NCLT stage 1b (CPU, no internet): repack first-format stage-1 outputs (thousands of img/<session>/<utime>.jpg files,
which `kaggle kernels output` cannot pull completely) into one img_<session>.tar + meta/nclt_<session>.npz per session,
so the images can be pulled once and published as a PUBLIC dataset that every account can mount for stage 2.
Private kernel outputs can only be mounted by their owner, so this kernel runs on the account that ran stage 1.
Usage: make_nclt_repack.py <kernel_dir> <slug> <stage1_slug,...> [--owner nhatlong1103]"""
import sys, os, json

kdir, slug, srcs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
OWNER = sys.argv[sys.argv.index("--owner") + 1] if "--owner" in sys.argv else "nhatlong1103"
run = r'''
import os, shutil, subprocess, time
W = "/kaggle/working"; t0 = time.time(); os.makedirs(os.path.join(W, "meta"), exist_ok=True); done = []
for d, subs, fs in os.walk("/kaggle/input"):
    if os.path.basename(d) == "meta":
        for f in fs:
            if f.startswith("nclt_") and f.endswith(".npz"): shutil.copy(os.path.join(d, f), os.path.join(W, "meta", f))
    if os.path.basename(os.path.dirname(d)) == "img" and any(f.endswith(".jpg") for f in fs):
        s = os.path.basename(d); subprocess.run(["tar", "-cf", os.path.join(W, f"img_{s}.tar"), "-C", os.path.dirname(os.path.dirname(d)), f"img/{s}"], check=True)
        done.append((s, len(fs))); subs[:] = []
    for f in fs:
        if f.startswith("img_") and f.endswith(".tar"): shutil.copy(os.path.join(d, f), os.path.join(W, f))
print("meta", sorted(os.listdir(os.path.join(W, "meta"))), flush=True)
print("DONE repacked", done, f"{time.time()-t0:.0f}s", flush=True)
'''
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(run)
json.dump({"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
           "is_private": True, "enable_gpu": False, "enable_tpu": False, "enable_internet": False, "dataset_sources": [],
           "competition_sources": [], "kernel_sources": [f"{OWNER}/{s}" for s in srcs], "model_sources": []},
          open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
print("kernel dir:", kdir, "| sources", srcs, "| owner", OWNER)
