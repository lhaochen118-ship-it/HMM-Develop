#!/usr/bin/env python3
"""KITTI Odometry loop-closure sequences for sequential place recognition (resumable; HTTP range reads, no 69 GB download).
Sequences 00, 02, 05, 06, 08 (revisits; 08 revisits in the OPPOSITE direction), left colour camera image_2, every
`--every`-th frame (10 Hz -> 5 Hz with 2), JPEG q=92, + GT poses (dataset/poses/XX.txt, 3x4 camera-to-world) and times.
Source: Geiger et al., CVPR 2012, cvlibs.net/datasets/kitti (public S3 mirror s3.eu-central-1.amazonaws.com/avg-kitti),
licence CC BY-NC-SA 3.0.
Output: <OUT>/vpr-kitti-odometry-loops/<seq>/{image_2/<frame:06d>.jpg, poses.txt, times.txt, frames.csv}
frames.csv: name, frame, t_s, x, y, z (camera centre in the sequence's first-camera frame; x right, z forward).
Usage: fetch_kitti_loops.py <OUT> [--every 2] [--seqs 00,02,05,06,08]"""
import os, sys, io, csv, zipfile, urllib.request
import numpy as np
from remotezip import RemoteZip
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import threading
_TL = threading.local()


def _rz():
    if not hasattr(_TL, "z"):                       # one remote handle per thread: the central directory is read once
        _TL.z = RemoteZip(S3 + "data_odometry_color.zip")
    return _TL.z

OUT = os.path.join(sys.argv[1], "vpr-kitti-odometry-loops")
EVERY = int(sys.argv[sys.argv.index("--every") + 1]) if "--every" in sys.argv else 2
SEQS = (sys.argv[sys.argv.index("--seqs") + 1] if "--seqs" in sys.argv else "00,02,05,06,08").split(",")
S3 = "https://s3.eu-central-1.amazonaws.com/avg-kitti/"
os.makedirs(OUT, exist_ok=True)


def small_zip(name):
    p = os.path.join(sys.argv[1], "_downloads", name); os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p):
        urllib.request.urlretrieve(S3 + name, p + ".tmp"); os.replace(p + ".tmp", p)
    return zipfile.ZipFile(p)


poses = small_zip("data_odometry_poses.zip")
calib = small_zip("data_odometry_calib.zip")
with RemoteZip(S3 + "data_odometry_color.zip") as rz:
    names = rz.namelist()
    for seq in SEQS:
        d = os.path.join(OUT, seq); done = os.path.join(d, "frames.csv")
        if os.path.exists(done):
            continue
        os.makedirs(os.path.join(d, "image_2"), exist_ok=True)
        P = np.loadtxt(io.BytesIO(poses.read(f"dataset/poses/{seq}.txt"))).reshape(-1, 3, 4)
        T = np.loadtxt(io.BytesIO(calib.read(f"dataset/sequences/{seq}/times.txt")))
        open(os.path.join(d, "poses.txt"), "wb").write(poses.read(f"dataset/poses/{seq}.txt"))
        open(os.path.join(d, "times.txt"), "wb").write(calib.read(f"dataset/sequences/{seq}/times.txt"))
        open(os.path.join(d, "calib.txt"), "wb").write(calib.read(f"dataset/sequences/{seq}/calib.txt"))
        members = sorted(n for n in names if n.startswith(f"dataset/sequences/{seq}/image_2/") and n.endswith(".png"))
        keep = members[::EVERY]

        def grab(m):
            fr = int(os.path.basename(m)[:-4]); dst = os.path.join(d, "image_2", f"{fr:06d}.jpg")
            if not os.path.exists(dst):
                for att in range(6):                # proxy may drop connections: fresh handle + back-off
                    try:
                        im = Image.open(io.BytesIO(_rz().read(m))).convert("RGB"); break
                    except Exception:
                        import time; _TL.__dict__.pop("z", None); time.sleep(2 * (att + 1))
                else:
                    raise RuntimeError("failed " + m)
                im.save(dst + ".tmp.jpg", quality=92); os.replace(dst + ".tmp.jpg", dst)
            return fr
        with ThreadPoolExecutor(8) as ex:
            frs = sorted(ex.map(grab, keep))
        with open(done + ".tmp", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["name", "frame", "t_s", "x", "y", "z"])
            for fr in frs:
                c = P[fr][:, 3]; w.writerow([f"{fr:06d}.jpg", fr, f"{T[fr]:.6f}", f"{c[0]:.4f}", f"{c[1]:.4f}", f"{c[2]:.4f}"])
        os.replace(done + ".tmp", done)
        print(f"seq {seq}: {len(members)} frames -> kept {len(frs)} (every {EVERY})", flush=True)
open(os.path.join(OUT, "SOURCE.md"), "w").write(
    "# KITTI Odometry — loop-closure sequences (00, 02, 05, 06, 08)\nGeiger, Lenz, Urtasun, CVPR 2012. Source: "
    "cvlibs.net/datasets/kitti (S3 mirror avg-kitti), licence CC BY-NC-SA 3.0. Left colour camera (image_2), every "
    f"{EVERY}th frame (10 Hz -> {10 / EVERY:g} Hz), JPEG q=92; GT poses from data_odometry_poses (3x4 cam-to-world, first "
    "camera frame: x right, y down, z forward). Use: revisit place recognition (query = later pass, map = earlier pass); "
    "sequence 08 revisits in the opposite direction.\n")
print("KITTI_DONE", flush=True)
