#!/usr/bin/env python3
"""Kaggle kernel (GPU + internet) that builds the Boreas part of the HMM study straight from the public S3 bucket.

Boreas (Burnett et al., IJRR 2023): one ~8 km route (Glen Shields, Toronto) driven ~40 times over a year (sun, overcast,
rain, snow, night). Sequences with released GT have `applanix/camera_poses.csv` (camera poses in ONE fixed ENU frame for
all sequences, at the camera timestamps = image file names) plus raw wheel encoder (`dmi.csv`) and IMU (`imu.csv`).
Per sequence the kernel
  1. selects camera frames >= SPACING m apart (GT easting/northing),
  2. downloads them in parallel, stores a 640-px JPEG copy (img/<seq>/<ts>.jpg, for the dataset),
  3. extracts the 6 global descriptors (fp16 on T4) -> dump/<desc>/boreas_<seq>.npy,
  4. writes dump/meta/boreas_<seq>.npz: names (us), C (easting, northing, altitude), rpy (roll, pitch, heading),
     vel (ENU), dmi (wheel pulse count at the frame time) and gyro_yaw (integrated IMU yaw rate) = real odometry.
Usage: make_dump_boreas.py <kernel_dir> <slug> <seq,seq,...> [--owner nhatlong1103] [--spacing 1.0]"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def code_cells(f):
    """code cells of an nb15_src/*.src file (the shared extraction code)"""
    txt = open(os.path.join(ROOT, "nb15_src", f)).read(); out, cur, on = [], [], False
    for ln in txt.splitlines():
        if ln.strip() in ("#%%CODE", "#%%MARKDOWN"):
            if on and cur: out.append("\n".join(cur))
            cur, on = [], ln.strip() == "#%%CODE"
        elif on: cur.append(ln)
    if on and cur: out.append("\n".join(cur))
    return "\n\n".join(out)


kdir, slug, seqs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
OWNER = sys.argv[sys.argv.index("--owner") + 1] if "--owner" in sys.argv else "nhatlong1103"
SP = float(sys.argv[sys.argv.index("--spacing") + 1]) if "--spacing" in sys.argv else 1.0

body = r'''
# ================================================================ Boreas: S3 -> frames -> JPEG + descriptors + meta
import re, io, urllib.request, concurrent.futures as cf
from PIL import Image
SEQS, SPACING = %s, %f
DESCRIPTORS = ["megaloc", "salad", "mixvpr", "cosplace", "netvlad", "dinov2"]
S3 = "https://boreas.s3.amazonaws.com/"
IMG = "/kaggle/working/img"; os.makedirs(os.path.join(CONFIG.OUT_DIR, "meta"), exist_ok=True)

def _get(url, tries=5):
    for i in range(tries):
        try: return urllib.request.urlopen(url, timeout=60).read()
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(2 * (i + 1))

def _csv(seq, f, skip=1):
    return np.genfromtxt(io.BytesIO(_get(S3 + f"{seq}/applanix/{f}")), delimiter=",", skip_header=skip)

def _keys(prefix):
    out, tok = [], None
    while True:
        u = S3 + f"?list-type=2&prefix={prefix}" + (f"&continuation-token={urllib.parse.quote(tok)}" if tok else "")
        x = _get(u).decode(); out += re.findall(r"<Key>([^<]*)</Key>", x)
        m = re.search(r"<NextContinuationToken>([^<]*)</NextContinuationToken>", x)
        if not m: return out
        tok = m.group(1)

import urllib.parse
PARTS = []
for seq in SEQS:
    t0 = time.time()
    cp = _csv(seq, "camera_poses.csv")                                  # GPSTime(us), e, n, alt, ve, vn, vu, roll, pitch, heading, ...
    have = {int(os.path.basename(k)[:-4]) for k in _keys(f"{seq}/camera/") if k.endswith(".png")}
    ts = cp[:, 0].astype(np.int64); ok = np.array([t in have for t in ts]); cp, ts = cp[ok], ts[ok]
    sel, last = [], None
    for i in range(len(cp)):
        if last is None or np.linalg.norm(cp[i, 1:3] - last) >= SPACING: sel.append(i); last = cp[i, 1:3]
    cp, ts = cp[sel], ts[sel]
    d = os.path.join(IMG, seq); os.makedirs(d, exist_ok=True)
    def fetch(t):
        p = os.path.join(d, f"{t}.jpg")
        if not os.path.exists(p):
            im = Image.open(io.BytesIO(_get(S3 + f"{seq}/camera/{t}.png"))).convert("RGB")
            im.resize((640, int(round(640 * im.height / im.width))), Image.BILINEAR).save(p, quality=90)
        return p
    with cf.ThreadPoolExecutor(32) as ex: paths = list(ex.map(fetch, ts))
    dmi = _csv(seq, "dmi.csv"); imu = _csv(seq, "imu.csv")              # GPSTime(s), pulse_count | GPSTime(s), angvel_z, ...
    tsec = ts / 1e6
    pulses = np.interp(tsec, dmi[:, 0], dmi[:, 1])
    yaw = np.concatenate([[0], np.cumsum(0.5 * (imu[1:, 1] + imu[:-1, 1]) * np.diff(imu[:, 0]))]); gyro = np.interp(tsec, imu[:, 0], yaw)
    np.savez(os.path.join(CONFIG.OUT_DIR, "meta", f"boreas_{seq}.npz"), names=ts, C=cp[:, 1:4], rpy=cp[:, 7:10], vel=cp[:, 4:7],
             dmi=pulses, gyro_yaw=gyro, seq=seq)
    path = np.linalg.norm(np.diff(cp[:, 1:3], axis=0), axis=1).sum()
    log(f"B.{seq}", "ok", f"{len(ts)} frames, path {path:.0f} m, download {time.time()-t0:.0f}s, pulses/m {(pulses[-1]-pulses[0])/max(path,1):.2f}")
    PARTS.append((f"boreas_{seq}", paths))

FWDS, DIMS = {}, {}
for dname in DESCRIPTORS:
    try:
        FWDS[dname] = build_extractor(dname); DIMS[dname] = EXTRACTOR_INFO["dim"]
    except Exception as e:
        import traceback; traceback.print_exc(); log(f"R.1.{dname}", "fail", repr(e)[:200])
for dname in FWDS: os.makedirs(os.path.join(CONFIG.OUT_DIR, dname), exist_ok=True)

@torch.no_grad()
def extract_multi(paths, tag):
    dl = torch.utils.data.DataLoader(ImageList(paths, CONFIG.IMG_SIZE), batch_size=CONFIG.BATCH_SIZE, shuffle=False,
                                     num_workers=CONFIG.NUM_WORKERS, pin_memory=(DEVICE == "cuda"))
    outs = {d: np.empty((len(paths), DIMS[d]), np.float16) for d in FWDS}; t0 = time.time(); bad = 0
    amp = torch.bfloat16 if CONFIG.USE_BF16 else torch.float16
    for b, (x, idx, ok) in enumerate(dl):
        x = x.to(DEVICE, non_blocking=True); bad += int((ok == 0).sum())
        for d, fwd in FWDS.items():
            with torch.autocast("cuda", dtype=amp, enabled=(DEVICE == "cuda")):
                y = fwd(x)
            outs[d][idx.numpy()] = torch.nn.functional.normalize(y.float(), dim=1).cpu().numpy().astype(np.float16)
        if b %% 20 == 0: print(f"    {tag}: {min((b+1)*CONFIG.BATCH_SIZE, len(paths))}/{len(paths)} ({(b+1)*CONFIG.BATCH_SIZE/max(time.time()-t0,1e-3):.1f} img/s)", flush=True)
    for d in outs: assert np.isfinite(outs[d].astype(np.float32)).all(), (tag, d)
    log(f"X.{tag}", "ok" if bad == 0 else "warn", f"{len(paths)} imgs in {time.time()-t0:.0f}s, unreadable={bad}")
    return outs

for tag, paths in PARTS:
    o = extract_multi(paths, tag)
    for d, a in o.items(): np.save(os.path.join(CONFIG.OUT_DIR, d, tag + ".npy"), a)
json.dump(REPORT, open(os.path.join(CONFIG.OUT_DIR, f"report_{SEQS[0]}.json"), "w"), indent=1, default=str)
print("DUMP_DONE", {k: v["status"] for k, v in REPORT.items() if v["status"] != "ok"}, flush=True)
''' % (json.dumps(seqs), SP)

src = "\n\n".join([code_cells("10_p0.src"), code_cells("20_extract.src"), code_cells("25_extra.src"), body])
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(src)
meta = {"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": True, "enable_tpu": False, "enable_internet": True,
        "dataset_sources": ["nhatlong1103/bundle", "nhatlong1103/vpr-descriptor-weights"],
        "competition_sources": [], "kernel_sources": [], "model_sources": []}
json.dump(meta, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
compile(src, "run.py", "exec"); print("kernel written:", kdir, len(src), "chars")
