#!/usr/bin/env python3
"""Kaggle kernel that dumps global descriptors (6 networks, one image pass) for 4Seasons, with metric VIO odometry.

Frames: GNSS-fused poses (`GNSSPoses.txt`, every ~0.1 s) sub-sampled to >= SPACING m of travel; image = cam0
undistorted `<ns>.png` (grayscale -> RGB). Per recording, meta/4s_<scene>_<date>.npz holds:
  names (image ns), C (n,3) camera position in a per-scene ENU frame (GNSS fusion, via transform_e_gpsw -> ECEF ->
  ENU at the scene's first recording start; ECEF = T_e_gpsw * (scale * T_w_gpsw^-1 * T_S_AS * p), which
  aligns different recordings of a scene to 0.34 m median, checked on office_loop), R (n,3,3) camera->ENU rotation (GNSS pose; its 3rd column is the direction of travel), vio_C (n,3) / vio_q (n,4) the
  recording-local VIO pose (`result.txt`, metric) = real odometry, fq (GNSS fusion quality).
Descriptors: dump/<desc>/4s_<scene>_<date>.npy (float16, L2-normalised), same row order.
Usage: make_dump4s.py <kernel_dir> <slug> <part> <n_parts> [--owner nhatlong1103]
The extraction cells are those of nb15_src (10_p0 config/paths, 20_extract registry, 25_extra extra networks)."""
import sys, os, json, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kdir, slug, part, nparts = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
OWNER = sys.argv[sys.argv.index("--owner") + 1] if "--owner" in sys.argv else "nhatlong1103"


def code_cells(f):
    txt = open(os.path.join(ROOT, "nb15_src", f)).read(); out, cur, on = [], [], False
    for ln in txt.splitlines():
        if ln.strip() in ("#%%CODE", "#%%MARKDOWN"):
            if on and cur: out.append("\n".join(cur))
            cur, on = [], ln.strip() == "#%%CODE"
        elif on: cur.append(ln)
    if on and cur: out.append("\n".join(cur))
    return "\n\n".join(out)


body = r'''
# ================================================================ 4Seasons loader + dump
import re
PART, NPARTS, SPACING = %d, %d, 1.0
DESCRIPTORS = ["megaloc", "salad", "mixvpr", "cosplace", "netvlad", "dinov2"]
POSES = os.path.dirname(_walk_find("/kaggle/input", "recordings.csv", 6))
print("poses root:", POSES, flush=True)

def _q2R(x, y, z, w):
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

def _glob(TT, p, R=None):
    """GNSSPoses frame -> ECEF (position) and the matching rotation"""
    Ras, Rw, Re = _q2R(*TT["transform_S_AS"][3:7]), _q2R(*TT["transform_w_gpsw"][3:7]), _q2R(*TT["transform_e_gpsw"][3:7])
    q = (Ras @ p.T).T + TT["transform_S_AS"][:3]; q = (Rw.T @ (q - TT["transform_w_gpsw"][:3]).T).T * TT["GNSS scale"][0]
    pe = (Re @ q.T).T + TT["transform_e_gpsw"][:3]
    return pe, (None if R is None else np.einsum("ij,njk->nik", Re @ Rw.T @ Ras, R))

def _readT(f):
    L = [l.strip() for l in open(f) if l.strip()]; return {l[2:].split(":")[0]: np.array(L[i+1].split(","), float) for i, l in enumerate(L) if l.startswith("#")}

def _ecef2enu_R(lat, lon):
    sl, cl, sp, cp = np.sin(lon), np.cos(lon), np.sin(lat), np.cos(lat)
    return np.array([[-sl, cl, 0], [-sp*cl, -sp*sl, cp], [cp*cl, cp*sl, sp]])

def _ecef2geo(p):
    a, e2 = 6378137.0, 6.69437999014e-3; x, y, z = p; lon = np.arctan2(y, x); r = np.hypot(x, y); lat = np.arctan2(z, r*(1-e2))
    for _ in range(5):
        N = a / np.sqrt(1 - e2*np.sin(lat)**2); lat = np.arctan2(z + e2*N*np.sin(lat), r)
    return lat, lon

# image dirs: recording_<date>/undistorted_images/cam0
CAM0 = {}
for d, subs, files in os.walk("/kaggle/input"):
    if d.endswith(os.path.join("undistorted_images", "cam0")):
        m = re.search(r"recording_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})", d)
        if m: CAM0[m.group(1)] = d; subs[:] = []
print("cam0 dirs found:", len(CAM0), flush=True)
recs = sorted((s, r) for s in os.listdir(POSES) if os.path.isdir(os.path.join(POSES, s)) and s != "calibration"
              for r in os.listdir(os.path.join(POSES, s)))
mine = [x for i, x in enumerate([x for x in recs if x[1] in CAM0]) if i %% NPARTS == PART]
print("recordings (all/mine):", len(recs), len(mine), mine, flush=True)
ORIG = {}
for s, r in recs:          # per-scene ENU origin = first recording's first GNSS pose (all parts agree)
    if s in ORIG: continue
    TT = _readT(os.path.join(POSES, s, r, "Transformations.txt"))
    g = np.loadtxt(os.path.join(POSES, s, r, "GNSSPoses.txt"), delimiter=",", comments="#", ndmin=2)
    p0 = _glob(TT, g[:1, 1:4])[0][0]; ORIG[s] = (p0, _ecef2enu_R(*_ecef2geo(p0)))
os.makedirs(os.path.join(CONFIG.OUT_DIR, "meta"), exist_ok=True)
PARTS = []
for s, r in mine:
    d = os.path.join(POSES, s, r); TT = _readT(os.path.join(d, "Transformations.txt"))
    g = np.loadtxt(os.path.join(d, "GNSSPoses.txt"), delimiter=",", comments="#", ndmin=2)
    vio = np.loadtxt(os.path.join(d, "result.txt"), ndmin=2); vt = np.round(vio[:, 0] * 1e9).astype(np.int64)
    cam = CAM0.get(r)
    if cam is None: log(f"4s.{s}.{r}", "warn", "no cam0 dir"); continue
    p0, Renu = ORIG[s]
    sel, last = [], None
    for i in range(len(g)):
        P = g[i, 1:4]
        if last is not None and np.linalg.norm(P - last) < SPACING: continue
        ns = int(g[i, 0]); f = os.path.join(cam, f"{ns}.png")
        j = np.searchsorted(vt, ns); j = min(max(j, 0), len(vt) - 1)
        if j > 0 and abs(vt[j-1] - ns) < abs(vt[j] - ns): j -= 1
        if abs(vt[j] - ns) > 2e6 or not os.path.isfile(f): continue
        sel.append((i, j, f, ns)); last = P
    gi = np.array([x[0] for x in sel]); vj = np.array([x[1] for x in sel])
    pe, Rg = _glob(TT, g[gi, 1:4], np.stack([_q2R(*g[i, 4:8]) for i in gi]))
    C = (Renu @ (pe - p0).T).T; R = np.einsum("ij,njk->nik", Renu, Rg)
    tag = f"4s_{s}_{r}"
    np.savez(os.path.join(CONFIG.OUT_DIR, "meta", tag + ".npz"), names=np.array([x[3] for x in sel], np.int64), C=C, R=R,
             vio_C=vio[vj, 1:4], vio_q=vio[vj, 4:8], fq=g[gi, 9], scene=s, rec=r, TS_cam_imu=TT.get("TS_cam_imu"))
    step = np.linalg.norm(np.diff(C, axis=0), axis=1); vstep = np.linalg.norm(np.diff(vio[vj, 1:4], axis=0), axis=1)
    log(f"4s.{tag}", "ok", f"{len(sel)} frames, ENU path {step.sum():.0f} m, VIO path {vstep.sum():.0f} m, step med {np.median(step):.2f}")
    PARTS.append((tag, [x[2] for x in sel]))

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
json.dump(REPORT, open(os.path.join(CONFIG.OUT_DIR, f"report_part{PART}.json"), "w"), indent=1, default=str)
print("DUMP_DONE", {k: v["status"] for k, v in REPORT.items() if v["status"] != "ok"}, flush=True)
''' % (part, nparts)

helpers = '''
def _walk_find(root, name, max_depth=4):
    for d, subs, files in os.walk(root):
        if d.count(os.sep) - root.count(os.sep) >= max_depth: subs[:] = []
        if name in files: return os.path.join(d, name)
    return None
'''
src = "\n\n".join([code_cells("10_p0.src"), code_cells("20_extract.src"), code_cells("25_extra.src"), helpers, body])
src = src.replace('CONFIG = Config()', 'CONFIG = Config(NUM_WORKERS=4)')
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(src)
meta = {"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": True, "enable_tpu": False, "enable_internet": False,
        "dataset_sources": ["nhatlong1103/4seasons", "nhatlong1103/4seasons-poses", "nhatlong1103/bundle", "nhatlong1103/vpr-descriptor-weights"],
        "competition_sources": [], "kernel_sources": [], "model_sources": []}
json.dump(meta, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
compile(src, "run.py", "exec"); print("kernel written:", kdir, len(src), "chars")
