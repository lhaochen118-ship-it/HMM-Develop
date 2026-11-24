#!/usr/bin/env python3
"""Collect the 4Seasons descriptor dumps from the dump kernels' outputs and publish them as the PUBLIC Kaggle dataset
nhatlong1103/vpr-dumps-4seasons (same layout as vpr-descriptor-dumps: dump/<desc>/4s_<scene>_<rec>.npy, dump/meta/
4s_<scene>_<rec>.npz), so the eval runner (make_eval_kernel.py) merges it with the main dump automatically.
Usage: upload_4s_dump.py <stage_dir> <kernel_out_dir> [<kernel_out_dir> ...]"""
import sys, os, glob, json, shutil, subprocess
import numpy as np

stage, outs = sys.argv[1], sys.argv[2:]
D = os.path.join(stage, "dump"); os.makedirs(os.path.join(D, "meta"), exist_ok=True)
for o in outs:
    for f in glob.glob(os.path.join(o, "dump", "*", "*")):
        sub = os.path.basename(os.path.dirname(f)); os.makedirs(os.path.join(D, sub), exist_ok=True)
        dst = os.path.join(D, sub, os.path.basename(f))
        if not os.path.exists(dst): os.link(f, dst) if os.stat(f).st_dev == os.stat(stage).st_dev else shutil.copy(f, dst)
descs = sorted(d for d in os.listdir(D) if d != "meta" and os.path.isdir(os.path.join(D, d)))
metas = sorted(glob.glob(os.path.join(D, "meta", "4s_*.npz"))); rows = []
for m in metas:
    tag = os.path.basename(m)[:-4]; z = np.load(m, allow_pickle=True); n = len(z["names"])
    for d in descs:
        a = np.load(os.path.join(D, d, tag + ".npy"), mmap_mode="r"); assert a.shape[0] == n, (tag, d, a.shape, n)
    rows.append((str(z["scene"]), str(z["rec"]), n, float(np.linalg.norm(np.diff(z["C"], axis=0), axis=1).sum())))
readme = ["# 4Seasons global-descriptor dump (HMM / sequence localization study)", "",
          "Descriptors (float16, L2-normalised) of 4Seasons cam0 frames sub-sampled to >= 1 m of travel, for the 6 VPR networks of",
          "`nhatlong1103/vpr-descriptor-dumps` (" + ", ".join(descs) + "). Layout `dump/<desc>/4s_<scene>_<recording>.npy`; rows follow",
          "`dump/meta/4s_<scene>_<recording>.npz`: names (image timestamp ns), C (camera centre, per-scene ENU frame from the GNSS-fused",
          "poses), R (camera->ENU), vio_C / vio_q (recording-local metric VIO pose = odometry), fq (GNSS fusion quality).",
          "Built by `automation/make_dump4s.py` (repo lhaochen118-ship-it/hmm-develop, branch hmm-navigation). Source: 4Seasons",
          "(Wenzel et al., GCPR 2020), CC BY-NC-SA 4.0.", "", "| scene | recording | frames | path (m) |", "|---|---|---|---|"]
readme += [f"| {s} | {r} | {n} | {p:.0f} |" for s, r, n, p in rows]
open(os.path.join(stage, "README.md"), "w").write("\n".join(readme) + "\n")
json.dump({"title": "VPR descriptor dumps 4Seasons", "id": "nhatlong1103/vpr-dumps-4seasons", "subtitle": "Global VPR descriptors + poses + VIO of 4Seasons",
           "isPrivate": False, "licenses": [{"name": "CC-BY-NC-SA-4.0"}]}, open(os.path.join(stage, "dataset-metadata.json"), "w"))
print(f"{len(metas)} recordings, {sum(r[2] for r in rows)} frames, descriptors {descs}")
env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser("~/.kaggle/tok_nhatlong1103")).read().strip())
st = subprocess.run(["kaggle", "datasets", "status", "nhatlong1103/vpr-dumps-4seasons"], capture_output=True, text=True, env=env).stdout
cmd = (["kaggle", "datasets", "version", "-m", "update", "-r", "zip", "-q", "-p", stage] if "ready" in st.lower()
       else ["kaggle", "datasets", "create", "-r", "zip", "-q", "-p", stage, "--public"])
r = subprocess.run(cmd, capture_output=True, text=True, env=env); print((r.stdout + r.stderr)[-600:])
