#!/usr/bin/env python3
"""NCLT stage 1c (CPU kernel WITH internet): per session, the KVH fibre-optic-gyro heading (kvh.csv) and the wheel
odometry pose (odometry_mu_100hz.csv) from the small sensor tarball, decimated to 20 Hz, as sensors/nclt_<session>.npz
(kvh: utime, heading; odo: utime, x, y, yaw). Used to build a FOG-heading dead reckoning (wheel distance + FOG yaw):
the wheel-only heading of odometry_mu drifts ~25 deg over 4 km, which a position-only Kalman filter cannot absorb.
Usage: make_nclt_sensors.py <kernel_dir> <slug> <session,session,...> [--owner nhatlong1103]"""
import sys, os, json

kdir, slug, sess = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
OWNER = sys.argv[sys.argv.index("--owner") + 1] if "--owner" in sys.argv else "nhatlong1103"
run = r'''
import os, io, time, tarfile, urllib.request, numpy as np
SESS = %r; S3 = "https://s3.us-east-2.amazonaws.com/nclt.perl.engin.umich.edu/"; W = "/kaggle/working/sensors"
os.makedirs(W, exist_ok=True); t0 = time.time()
def get(url, path):
    for k in range(6):
        try: urllib.request.urlretrieve(url, path); return
        except Exception as e: print("retry", url, e, flush=True); time.sleep(10 * (k + 1))
    raise RuntimeError(url)
def dec(a, hz=20):                                   # keep one row per 1/hz s (rows sorted by utime)
    a = a[np.all(np.isfinite(a), 1)]; a = a[np.argsort(a[:, 0])]; b = np.floor(a[:, 0] / (1e6 / hz))
    return a[np.r_[True, b[1:] != b[:-1]]]
for s in SESS:
    get(S3 + f"sensor_data/{s}_sen.tar.gz", "/tmp/sen.tar.gz"); out = {}
    with tarfile.open("/tmp/sen.tar.gz") as tf:
        for m in tf.getmembers():
            b = os.path.basename(m.name)
            if b == "kvh.csv": out["kvh"] = dec(np.genfromtxt(io.BytesIO(tf.extractfile(m).read()), delimiter=",")[:, :2])
            if b == "odometry_mu_100hz.csv": out["odo"] = dec(np.genfromtxt(io.BytesIO(tf.extractfile(m).read()), delimiter=",")[:, [0, 1, 2, 6]])
    np.savez(os.path.join(W, f"nclt_{s}.npz"), **out)
    print(s, {k: v.shape for k, v in out.items()}, f"{time.time()-t0:.0f}s", flush=True)
print("DONE", f"{time.time()-t0:.0f}s", flush=True)
''' % (sess,)
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(run)
json.dump({"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
           "is_private": True, "enable_gpu": False, "enable_tpu": False, "enable_internet": True, "dataset_sources": [],
           "competition_sources": [], "kernel_sources": [], "model_sources": []}, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
print("kernel dir:", kdir, "| sessions", sess, "| owner", OWNER)
