#!/usr/bin/env python3
"""Kaggle kernel (GPU + internet) that builds the Oxford RobotCar part of the study from the public Kaggle copy of the
PointNetVLAD / OpenPlaceRecognition split (creatorofuniverses/oxfordrobotcar-iprofi-hack-23) and PUBLISHES the result as
two public datasets of nhatlong1103 (user rule 2026-11-01: every new dataset is re-published under nhatlong1103 for reuse):
  nhatlong1103/oxford-robotcar-vpr-dump    dump/<desc>/oxford_<track>.npy (6 descriptors, fp16, L2-normalised),
                                           dump/meta/oxford_<track>.npz (names = stereo_centre timestamps us, C = easting,
                                           northing, 0; split = PointNetVLAD split of every frame)
  nhatlong1103/oxford-robotcar-vpr-images  img/<track>/<timestamp>.jpg (stereo_centre images_small, 320 x 224, JPEG q 92)
Frames: every row of train / val / test.csv of a track (the full traversal, ~10 m apart), sorted by time.
Usage: make_dump_oxford.py <kernel_dir> <slug> [--tracks a,b,...] [--owner nhatlong1103] [--no-publish]"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def code_cells(f):
    """code cells of an nb15_src/*.src file (the shared extraction code; same helper as make_dump_boreas.py)"""
    txt = open(os.path.join(ROOT, "nb15_src", f)).read(); out, cur, on = [], [], False
    for ln in txt.splitlines():
        if ln.strip() in ("#%%CODE", "#%%MARKDOWN"):
            if on and cur: out.append("\n".join(cur))
            cur, on = [], ln.strip() == "#%%CODE"
        elif on: cur.append(ln)
    if on and cur: out.append("\n".join(cur))
    return "\n\n".join(out)


kdir, slug = sys.argv[1], sys.argv[2]
OWNER = sys.argv[sys.argv.index("--owner") + 1] if "--owner" in sys.argv else "nhatlong1103"
TRACKS = sys.argv[sys.argv.index("--tracks") + 1].split(",") if "--tracks" in sys.argv else []
PUBLISH = "--no-publish" not in sys.argv
TOKEN = open(os.path.expanduser("~/.kaggle/tok_nhatlong1103")).read().strip() if PUBLISH else ""

body = r'''
# ================================================================ Oxford RobotCar (PointNetVLAD split) -> JPEG + descriptors + meta
import csv, subprocess, shutil
from PIL import Image
TRACKS, PUBLISH, TOKEN = %s, %s, %s
DESCRIPTORS = ["megaloc", "salad", "mixvpr", "cosplace", "netvlad", "dinov2"]
SRC = next(d for d, _, fs in os.walk("/kaggle/input") if "train.csv" in fs and "test.csv" in fs)
IMG = "/kaggle/working/img"; os.makedirs(os.path.join(CONFIG.OUT_DIR, "meta"), exist_ok=True)
rows = []
for split in ("train", "val", "test"):
    rows += [dict(r, split=split) for r in csv.DictReader(open(os.path.join(SRC, split + ".csv")))]
by = {}
for r in rows: by.setdefault(r["track"], []).append(r)
tracks = TRACKS or sorted(by)
log("O.0", "ok", f"src {SRC}: {len(rows)} rows, {len(by)} tracks, using {len(tracks)}")
PARTS = []
for tr in tracks:
    rs = sorted(by[tr], key=lambda r: int(r["stereo_centre"])); seen = set(); keep = []
    for r in rs:
        t = int(r["stereo_centre"])
        if t not in seen: seen.add(t); keep.append(r)
    ts = np.array([int(r["stereo_centre"]) for r in keep], np.int64)
    C = np.array([[float(r["easting"]), float(r["northing"]), 0.0] for r in keep])
    src = [os.path.join(SRC, tr, "images_small", "stereo_centre", f"{t}.png") for t in ts]
    ok = np.array([os.path.isfile(p) for p in src]); ts, C, src = ts[ok], C[ok], [p for p, o in zip(src, ok) if o]
    sp = np.array([r["split"] for r, o in zip(keep, ok) if o])
    d = os.path.join(IMG, tr); os.makedirs(d, exist_ok=True); paths = []
    for p, t in zip(src, ts):
        q = os.path.join(d, f"{t}.jpg")
        if not os.path.exists(q): Image.open(p).convert("RGB").save(q, quality=92)
        paths.append(q)
    np.savez(os.path.join(CONFIG.OUT_DIR, "meta", f"oxford_{tr}.npz"), names=ts, C=C, split=sp, track=tr)
    step = np.linalg.norm(np.diff(C[:, :2], axis=0), axis=1)
    log(f"O.{tr}", "ok", f"{len(ts)} frames (missing {int((~ok).sum())}), path {step.sum():.0f} m, median step {np.median(step):.1f} m")
    PARTS.append((f"oxford_{tr}", paths))

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
    for d in outs: assert np.isfinite(outs[d].astype(np.float32)).all(), (tag, d)
    log(f"X.{tag}", "ok" if bad == 0 else "warn", f"{len(paths)} imgs in {time.time()-t0:.0f}s, unreadable={bad}")
    return outs

for tag, paths in PARTS:
    o = extract_multi(paths, tag)
    for d, a in o.items(): np.save(os.path.join(CONFIG.OUT_DIR, d, tag + ".npy"), a)
json.dump(REPORT, open(os.path.join(CONFIG.OUT_DIR, "report_oxford.json"), "w"), indent=1, default=str)

def publish(path, slug, title, sub):
    json.dump({"title": title, "id": f"nhatlong1103/{slug}", "subtitle": sub, "isPrivate": False,
               "licenses": [{"name": "CC-BY-NC-SA-4.0"}]}, open(os.path.join(path, "dataset-metadata.json"), "w"))
    env = dict(os.environ, KAGGLE_API_TOKEN=TOKEN)
    st = subprocess.run(["kaggle", "datasets", "status", f"nhatlong1103/{slug}"], capture_output=True, text=True, env=env).stdout.strip().lower()
    cmd = (["kaggle", "datasets", "version", "-p", path, "-m", "update"] if st == "ready" else ["kaggle", "datasets", "create", "-p", path, "--public"]) + ["-r", "zip", "-q"]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env); print("PUBLISH", slug, (r.stdout + r.stderr)[-400:], flush=True)

if PUBLISH:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "kaggle"], capture_output=True)
    pub = "/kaggle/working/pub_dump"; os.makedirs(pub, exist_ok=True)
    for sub in os.listdir(CONFIG.OUT_DIR):
        if os.path.isdir(os.path.join(CONFIG.OUT_DIR, sub)): shutil.copytree(os.path.join(CONFIG.OUT_DIR, sub), os.path.join(pub, sub), dirs_exist_ok=True)
    publish(pub, "oxford-robotcar-vpr-dump", "Oxford RobotCar VPR descriptor dump",
            "6 VPR descriptors + UTM poses, 44 Oxford RobotCar traversals (PointNetVLAD split)")
    pubi = "/kaggle/working/pub_img"; os.makedirs(pubi, exist_ok=True); shutil.move(IMG, os.path.join(pubi, "img"))
    publish(pubi, "oxford-robotcar-vpr-images", "Oxford RobotCar VPR images (small)",
            "stereo_centre 320x224 JPEG frames of 44 RobotCar traversals, PointNetVLAD split")
print("DUMP_DONE", {k: v["status"] for k, v in REPORT.items() if v["status"] != "ok"}, flush=True)
''' % (json.dumps(TRACKS), PUBLISH, json.dumps(TOKEN))

src = "\n\n".join([code_cells("10_p0.src"), code_cells("20_extract.src"), code_cells("25_extra.src"), body])
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(src)
meta = {"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": True, "enable_tpu": False, "enable_internet": True,
        "dataset_sources": ["nhatlong1103/bundle", "nhatlong1103/vpr-descriptor-weights", "creatorofuniverses/oxfordrobotcar-iprofi-hack-23"],
        "competition_sources": [], "kernel_sources": [], "model_sources": []}
json.dump(meta, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
compile(src, "run.py", "exec"); print("kernel written:", kdir, len(src), "chars")
