#!/usr/bin/env python3
"""Kaggle CPU kernel WITH internet: fetch the Boreas query frames whose 640-px JPEG is missing from the published image
datasets nhatlong1103/boreas-vpr-images-{1..4} (they hold 133k of the 182k dumped frames), straight from the public S3
bucket, so image-based baselines (SafeVPR) see exactly the frames the descriptor dump uses.
Output (kernel /kaggle/working): img/<seq>/<timestamp_us>.jpg for the missing frames only (to be published as
nhatlong1103/boreas-vpr-images-5). Usage: make_boreas_missing.py <kernel_dir> <slug> <seq,seq,...> [--owner nhatlong1103]"""
import sys, os, json

kdir, slug, seqs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
OWNER = sys.argv[sys.argv.index("--owner") + 1] if "--owner" in sys.argv else "nhatlong1103"
run = r'''
import os, io, time, urllib.request, concurrent.futures as cf, numpy as np
from PIL import Image
SEQS = %r; S3 = "https://boreas.s3.amazonaws.com/"; W = "/kaggle/working/img"; t0 = time.time()
have = set()
for d, _, fs in os.walk("/kaggle/input"):
    if "/img/" in d + "/":
        for f in fs:
            if f.endswith(".jpg"): have.add((os.path.basename(d), f[:-4]))
meta = [d for d, _, fs in os.walk("/kaggle/input") if os.path.basename(d) == "meta" and any(f.startswith("boreas_") for f in fs)][0]
print("have", len(have), "meta", meta, flush=True)
def get(url, tries=6):
    for i in range(tries):
        try: return urllib.request.urlopen(url, timeout=60).read()
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(2 * (i + 1))
for seq in SEQS:
    names = np.load(os.path.join(meta, f"boreas_{seq}.npz"), allow_pickle=True)["names"]
    miss = [int(n) for n in names if (seq, str(int(n))) not in have]
    d = os.path.join(W, seq); os.makedirs(d, exist_ok=True)
    def fetch(t):
        p = os.path.join(d, f"{t}.jpg")
        if not os.path.exists(p):
            im = Image.open(io.BytesIO(get(S3 + f"{seq}/camera/{t}.png"))).convert("RGB")
            im.resize((640, int(round(640 * im.height / im.width))), Image.BILINEAR).save(p, quality=90)
        return 1
    with cf.ThreadPoolExecutor(48) as ex: n = sum(ex.map(fetch, miss))
    print(f"{seq}: {len(names)} frames, fetched {n} missing, {time.time()-t0:.0f}s", flush=True)
print("DONE", f"{time.time()-t0:.0f}s", flush=True)
''' % (seqs,)
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(run)
json.dump({"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
           "is_private": True, "enable_gpu": False, "enable_tpu": False, "enable_internet": True,
           "dataset_sources": ["nhatlong1103/boreas-vpr-dump"] + [f"nhatlong1103/boreas-vpr-images-{k}" for k in (1, 2, 3, 4)],
           "competition_sources": [], "kernel_sources": [], "model_sources": []}, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
print("kernel dir:", kdir, "| seqs", seqs, "| owner", OWNER)
