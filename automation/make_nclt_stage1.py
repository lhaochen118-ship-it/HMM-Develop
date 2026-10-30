#!/usr/bin/env python3
"""NCLT stage 1 (Kaggle CPU kernel WITH internet): public S3 -> selected Cam5 frames (JPEG 640 px) + GT + wheel odometry.

NCLT (Carlevaris-Bianco et al., IJRR 2016): 27 sessions over 15 months on the U. Michigan North Campus, Segway robot,
Ladybug3 (6 cameras), wheel odometry, GT poses from LiDAR SLAM in ONE frame for all sessions. Routes differ between
sessions (indoor/outdoor, different paths), so a query session leaves the map session's coverage NATURALLY (no
synthetic map holes). The image tarball is ~114 GB per session, so it is STREAMED (curl | gzip -dc | tarfile r|):
every Cam5 TIFF is rotated (NCLT images are stored rotated by 90 deg), downscaled to 640 px on the long side and kept as
JPEG; after the stream, frames >= SPACING m apart along the GT path are kept (others deleted).
Output (kernel /kaggle/working): img/<session>/<utime>.jpg, meta/nclt_<session>.npz with names (utime, us), C (x, y, z
GT, interpolated at the image time), rpy (GT roll, pitch, yaw), odo (wheel odometry x, y, yaw at the image time).
Stage 2 (L4, no internet) extracts the 6 global descriptors from the published image dataset.
Usage: make_nclt_stage1.py <kernel_dir> <slug> <session> [--owner nhatlong1103] [--spacing 1.0] [--cam 5]"""
import sys, os, json

kdir, slug, sess = sys.argv[1], sys.argv[2], sys.argv[3]
OWNER = sys.argv[sys.argv.index("--owner") + 1] if "--owner" in sys.argv else "nhatlong1103"
SP = float(sys.argv[sys.argv.index("--spacing") + 1]) if "--spacing" in sys.argv else 1.0
CAM = int(sys.argv[sys.argv.index("--cam") + 1]) if "--cam" in sys.argv else 5

run = r'''
import os, io, sys, time, tarfile, subprocess, urllib.request, numpy as np
from PIL import Image
SESS, SPACING, CAM = %r, %f, %d
S3 = "https://s3.us-east-2.amazonaws.com/nclt.perl.engin.umich.edu/"
W = "/kaggle/working"; T = os.path.join(W, "tmpimg", SESS); os.makedirs(T, exist_ok=True)
os.makedirs(os.path.join(W, "meta"), exist_ok=True); t0 = time.time()
def get(url, path):
    for k in range(5):
        try: urllib.request.urlretrieve(url, path); return
        except Exception as e: print("retry", url, e, flush=True); time.sleep(10 * (k + 1))
    raise RuntimeError(url)
get(S3 + f"ground_truth/groundtruth_{SESS}.csv", "/tmp/gt.csv")
gt = np.genfromtxt("/tmp/gt.csv", delimiter=","); gt = gt[np.all(np.isfinite(gt[:, :7]), 1)]; gt = gt[np.argsort(gt[:, 0])]
get(S3 + f"sensor_data/{SESS}_sen.tar.gz", "/tmp/sen.tar.gz")
with tarfile.open("/tmp/sen.tar.gz") as tf:
    m = [x for x in tf.getmembers() if x.name.endswith("odometry_mu_100hz.csv")][0]
    odo = np.genfromtxt(io.BytesIO(tf.extractfile(m).read()), delimiter=",")
odo = odo[np.all(np.isfinite(odo[:, :7]), 1)]; odo = odo[np.argsort(odo[:, 0])]
print("gt", gt.shape, "odo", odo.shape, f"{time.time()-t0:.0f}s", flush=True)
# stream the 114 GB image tarball: keep every Cam<CAM> frame as a 640-px JPEG
cmd = f"curl -sS --retry 5 --retry-delay 10 {S3}images/{SESS}_lb3.tar.gz | gzip -dc"
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, bufsize=1 << 24)
n_all = n_cam = 0
with tarfile.open(fileobj=p.stdout, mode="r|") as tf:
    for mem in tf:
        n_all += 1
        if not mem.isfile() or f"/Cam{CAM}/" not in mem.name or not mem.name.endswith(".tiff"): continue
        ut = int(os.path.basename(mem.name)[:-5])
        if ut < gt[0, 0] or ut > gt[-1, 0]: continue
        im = Image.open(io.BytesIO(tf.extractfile(mem).read())).convert("RGB").transpose(Image.Transpose.ROTATE_270)
        im.thumbnail((640, 640)); im.save(os.path.join(T, f"{ut}.jpg"), quality=90); n_cam += 1
        if n_cam %% 2000 == 0: print(f"  {n_cam} frames ({n_all} members) {time.time()-t0:.0f}s", flush=True)
p.wait(); print("stream done", n_cam, "frames", f"{time.time()-t0:.0f}s rc", p.returncode, flush=True)
# select frames >= SPACING m apart along the GT path (time order)
uts = np.array(sorted(int(f[:-4]) for f in os.listdir(T)))
xyz = np.stack([np.interp(uts, gt[:, 0], gt[:, k]) for k in (1, 2, 3)], 1)
keep, last = [], None
for i, x in enumerate(xyz):
    if last is None or np.linalg.norm(x[:2] - last) >= SPACING: keep.append(i); last = x[:2]
keep = np.array(keep); D = os.path.join(W, "img", SESS); os.makedirs(D, exist_ok=True)
for i in keep: os.replace(os.path.join(T, f"{uts[i]}.jpg"), os.path.join(D, f"{uts[i]}.jpg"))
subprocess.run(["rm", "-rf", os.path.join(W, "tmpimg")])
u = uts[keep]; un = lambda a: np.unwrap(a)
rpy = np.stack([np.interp(u, gt[:, 0], un(gt[:, k])) for k in (4, 5, 6)], 1)
od = np.stack([np.interp(u, odo[:, 0], odo[:, 1]), np.interp(u, odo[:, 0], odo[:, 2]), np.interp(u, odo[:, 0], un(odo[:, 6]))], 1)
np.savez(os.path.join(W, "meta", f"nclt_{SESS}.npz"), names=u, C=xyz[keep], rpy=rpy, odo=od)
L = float(np.linalg.norm(np.diff(xyz[keep][:, :2], axis=0), axis=1).sum())
subprocess.run(["tar", "-cf", os.path.join(W, f"img_{SESS}.tar"), "-C", W, f"img/{SESS}"]); subprocess.run(["rm", "-rf", os.path.join(W, "img")])
print("DONE", SESS, "kept", len(keep), "of", len(uts), f"path {L/1000:.2f} km", f"{time.time()-t0:.0f}s", flush=True)   # one tar: fast output pull
''' % (sess, SP, CAM)
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(run)
json.dump({"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
           "is_private": True, "enable_gpu": False, "enable_tpu": False, "enable_internet": True, "dataset_sources": [],
           "competition_sources": [], "kernel_sources": [], "model_sources": []}, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
print("kernel dir:", kdir, "| session", sess, "| owner", OWNER)
