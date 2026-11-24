#!/usr/bin/env python3
"""Publish the Boreas outputs of the make_dump_boreas.py kernels as two PUBLIC Kaggle datasets of nhatlong1103:
  dump   -> nhatlong1103/boreas-vpr-dump   (dump/<desc>/boreas_<seq>.npy, dump/meta/boreas_<seq>.npz, README.md)
  images -> nhatlong1103/boreas-vpr-images (img/<seq>/<timestamp_us>.jpg, 640-px JPEG copies of the selected frames)
The dump layout matches vpr-descriptor-dumps, so make_eval_kernel.py runners merge it automatically.
Usage: upload_boreas.py <dump|images> <stage_dir> <kernel_out_dir> [...]"""
import sys, os, glob, json, shutil, subprocess
import numpy as np

PART = None
if "--part" in sys.argv:                       # images only: "--part i/n" publishes sequences i::n as boreas-vpr-images-<i+1>
    i = sys.argv.index("--part"); PART = tuple(int(x) for x in sys.argv[i + 1].split("/")); del sys.argv[i:i + 2]
what, stage, outs = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(stage, exist_ok=True)


def place(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst): return
    try: os.link(src, dst)
    except OSError: shutil.copy(src, dst)


if what == "dump":
    for o in outs:
        for f in glob.glob(os.path.join(o, "dump", "*", "boreas_*")): place(f, os.path.join(stage, "dump", os.path.basename(os.path.dirname(f)), os.path.basename(f)))
    D = os.path.join(stage, "dump"); descs = sorted(d for d in os.listdir(D) if d != "meta"); rows = []
    for m in sorted(glob.glob(os.path.join(D, "meta", "boreas_*.npz"))):
        tag = os.path.basename(m)[:-4]; z = np.load(m, allow_pickle=True); n = len(z["names"])
        ok = all(os.path.isfile(os.path.join(D, d, tag + ".npy")) and np.load(os.path.join(D, d, tag + ".npy"), mmap_mode="r").shape[0] == n for d in descs)
        if not ok: print("incomplete, skipped:", tag); os.remove(m); continue
        rows.append((tag[7:], n, float(np.linalg.norm(np.diff(z["C"][:, :2], axis=0), axis=1).sum())))
    readme = ["# Boreas global-descriptor dump (HMM / sequence localization study)", "",
              "Boreas (Burnett et al., IJRR 2023; public S3 `boreas.s3.amazonaws.com`): the Glen Shields route (~8 km) driven over a year.",
              "Camera frames sub-sampled to >= 1 m of travel; descriptors (float16, L2-normalised) of " + ", ".join(descs) + ".",
              "Layout `dump/<desc>/boreas_<seq>.npy`; rows follow `dump/meta/boreas_<seq>.npz`: names (image timestamp us = file name),",
              "C (easting, northing, altitude; one fixed ENU frame for all sequences), rpy, vel, dmi (wheel-encoder pulse count) and",
              "gyro_yaw (integrated IMU yaw rate) at the frame times = real odometry. Images: `nhatlong1103/boreas-vpr-images`.",
              "Built by `automation/make_dump_boreas.py` (repo lhaochen118-ship-it/hmm-develop, branch hmm-navigation).", "",
              "| sequence | frames | path (m) |", "|---|---|---|"] + [f"| {s} | {n} | {p:.0f} |" for s, n, p in rows]
    slug, title, sub = "boreas-vpr-dump", "Boreas VPR descriptor dump", "Global VPR descriptors, poses and wheel/gyro odometry of Boreas"
    print(f"{len(rows)} sequences, {sum(r[1] for r in rows)} frames")
else:
    allseq = sorted({os.path.basename(d) for o in outs for d in glob.glob(os.path.join(o, "img", "*"))})
    want = set(allseq if PART is None else allseq[PART[0]::PART[1]])
    for o in outs:
        for f in glob.glob(os.path.join(o, "img", "*", "*.jpg")):
            if os.path.basename(os.path.dirname(f)) in want: place(f, os.path.join(stage, "img", os.path.basename(os.path.dirname(f)), os.path.basename(f)))
    seqs = sorted(os.listdir(os.path.join(stage, "img")))
    readme = ["# Boreas selected camera frames (640-px JPEG)", "",
              "Frames of the Boreas Glen Shields sequences sub-sampled to >= 1 m of travel (see `nhatlong1103/boreas-vpr-dump` for poses,",
              "odometry and descriptors). `img/<seq>/<timestamp_us>.jpg`, resized from the original 2448x2048 PNG. Source: Boreas, CC BY 4.0.", "",
              f"{len(seqs)} sequences: " + ", ".join(seqs)]
    sfx = "" if PART is None else f"-{PART[0] + 1}"
    slug, title, sub = "boreas-vpr-images" + sfx, "Boreas VPR frames 640px" + (f" part {PART[0] + 1}" if PART else ""), "Boreas camera frames sub-sampled to 1 m, 640-px JPEG"
open(os.path.join(stage, "README.md"), "w").write("\n".join(readme) + "\n")
json.dump({"title": title, "id": f"nhatlong1103/{slug}", "subtitle": sub, "isPrivate": False, "licenses": [{"name": "CC-BY-4.0"}]},
          open(os.path.join(stage, "dataset-metadata.json"), "w"))
env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser("~/.kaggle/tok_nhatlong1103")).read().strip())
chk = subprocess.run(["kaggle", "datasets", "files", f"nhatlong1103/{slug}", "--page-size", "1"], capture_output=True, text=True, env=env)
exists = chk.returncode == 0 and "404" not in chk.stdout + chk.stderr and "not found" not in (chk.stdout + chk.stderr).lower()
cmd = (["kaggle", "datasets", "version", "-m", "update", "-r", "zip", "-q", "-p", stage] if exists
       else ["kaggle", "datasets", "create", "-r", "zip", "-q", "-u", "-p", stage])
r = subprocess.run(cmd, capture_output=True, text=True, env=env); print((r.stdout + r.stderr)[-500:])
