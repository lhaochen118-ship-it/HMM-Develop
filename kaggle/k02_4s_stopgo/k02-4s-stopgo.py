# === P0.0 — imports / device ==========================================================
import os, sys, json, time, glob, math, warnings
from dataclasses import dataclass, asdict
from collections import OrderedDict
import numpy as np
import torch
REPORT = OrderedDict()
def log(step, status, msg=""):
    REPORT[step] = {"status": status, "msg": msg}
    print({"ok": "[ OK ]", "warn": "[WARN]", "fail": "[FAIL]", "info": "[info]"}.get(status, "[??]"), step + ":", msg, flush=True)
torch.manual_seed(0); np.random.seed(0)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BF16_OK = (DEVICE == "cuda" and torch.cuda.is_bf16_supported())
print("torch", torch.__version__, "| device", DEVICE, "| bf16", BF16_OK, flush=True)
if DEVICE == "cuda": print("GPU:", torch.cuda.get_device_properties(0).name, flush=True)


# === P0.1 — CONFIG ======================================================================
@dataclass
class Config:
    INPUT_ROOTS: tuple = ("/kaggle/input",)
    OUT_DIR: str = "/kaggle/working/dump"
    IMG_SIZE: int = 322
    BATCH_SIZE: int = 64
    NUM_WORKERS: int = 4
    USE_BF16: bool = True
    NORD_PER_SEASON: int = 4500
    CMU_MAX_IMAGES: int = 24000
    MSLS_CITIES: tuple = ("cph", "sf")
    CMU_SLICE_ORDER: tuple = (7, 10, 19, 8, 11, 20, 6, 12, 21, 5, 13, 22, 4, 14, 23, 3, 15, 24, 2, 16, 17, 18, 9, 25)
CONFIG = Config(NUM_WORKERS=4)
CONFIG.USE_BF16 = CONFIG.USE_BF16 and BF16_OK
if DEVICE == "cuda":
    g = torch.cuda.get_device_properties(0).total_memory / 1e9
    CONFIG.BATCH_SIZE = 256 if g >= 70 else 64
os.makedirs(CONFIG.OUT_DIR, exist_ok=True)
print(asdict(CONFIG), flush=True)


# === P0.2 — offline env + path discovery ===============================================
for k, v in {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PIP_NO_INDEX": "1", "WANDB_MODE": "offline"}.items():
    os.environ.setdefault(k, v)

def _find_dir(markers_any, markers_all=(), roots=None, max_depth=4):
    roots = roots or CONFIG.INPUT_ROOTS; seen = set()
    for root in roots:
        if not os.path.isdir(root): continue
        frontier = [(root, 0)]
        while frontier:
            d, dep = frontier.pop(0)
            if d in seen or dep > max_depth: continue
            seen.add(d)
            try: entries = set(os.listdir(d))
            except Exception: continue
            ok_all = all(any(m.lower() in e.lower() for e in entries) for m in markers_all) if markers_all else True
            ok_any = any(any(m.lower() in e.lower() for e in entries) for m in markers_any) if markers_any else True
            if ok_all and ok_any: return d
            for e in sorted(entries):
                sub = os.path.join(d, e)
                if os.path.isdir(sub): frontier.append((sub, dep + 1))
    return None

PATHS = {
    "bundle":   _find_dir(["checkpoints"], ["checkpoints", "sources"]),
    "robotcar": _find_dir(["images"], ["images", "3D-models"]),
    "nordland": _find_dir(["data"], ["data", "annotations"]),
}
for n, p in PATHS.items(): log(f"P0.2.path.{n}", "ok" if p else "warn", p or "not found")
if PATHS["bundle"]:
    for sub in ["salad", "dinov2", ""]:
        p = os.path.join(PATHS["bundle"], "sources", sub) if sub else os.path.join(PATHS["bundle"], "sources")
        if os.path.isdir(p) and p not in sys.path: sys.path.insert(0, p)
print("inputs:", sorted(os.listdir("/kaggle/input")) if os.path.isdir("/kaggle/input") else None, flush=True)

# === E.0 — descriptor registry ===========================================================
EXTRACTOR_INFO = {"name": None, "dim": None}

def _try_salad():
    """serizba/salad via helper.get_* with the released dino_salad.ckpt config (dim 8448)."""
    ck = os.path.join(PATHS["bundle"], "checkpoints", "dino_salad.ckpt")
    salad_dir = os.path.join(PATHS["bundle"], "sources", "salad")
    if not (os.path.isfile(ck) and os.path.isdir(salad_dir)): return None
    if salad_dir not in sys.path: sys.path.insert(0, salad_dir)
    from models import helper
    backbone = helper.get_backbone("dinov2_vitb14", {"num_trainable_blocks": 4, "return_token": True, "norm_layer": True})
    aggregator = helper.get_aggregator("SALAD", {"num_channels": 768, "num_clusters": 64, "cluster_dim": 128, "token_dim": 256})
    sd = torch.load(ck, map_location="cpu"); sd = sd.get("state_dict", sd)
    backbone.load_state_dict({k[9:]: v for k, v in sd.items() if k.startswith("backbone.")}, strict=False)
    aggregator.load_state_dict({k[11:]: v for k, v in sd.items() if k.startswith("aggregator.")}, strict=False)
    m = torch.nn.Module(); m.backbone = backbone; m.aggregator = aggregator; m.eval().to(DEVICE)
    @torch.no_grad()
    def fwd(x): return m.aggregator(m.backbone(x))
    return fwd

def _try_dinov2():
    pth = os.path.join(PATHS["bundle"], "checkpoints", "dinov2_vitb14_pretrain.pth")
    vit_base = __import__("dinov2.models.vision_transformer", fromlist=["vit_base"]).vit_base
    vit = vit_base(patch_size=14, img_size=518, init_values=1.0, block_chunks=0)
    sd = torch.load(pth, map_location="cpu"); vit.load_state_dict(sd.get("state_dict", sd), strict=False)
    vit.eval().to(DEVICE)
    @torch.no_grad()
    def fwd(x):
        f = vit.forward_features(x)
        return torch.cat([f["x_norm_clstoken"], f["x_norm_patchtokens"].mean(1)], 1)
    return fwd

REGISTRY = {"salad": _try_salad, "dinov2": _try_dinov2}

def build_extractor(name):
    fwd = REGISTRY[name]()
    assert fwd is not None, f"extractor {name} unavailable"
    with torch.no_grad():
        d = fwd(torch.zeros(2, 3, CONFIG.IMG_SIZE, CONFIG.IMG_SIZE, device=DEVICE))
    assert torch.isfinite(d).all() and d.ndim == 2
    EXTRACTOR_INFO.update(name=name, dim=int(d.shape[1]))
    log("E.0.extractor", "ok", f"{name} dim={d.shape[1]}")
    return fwd


# === E.1 — image dataset + fp16 extraction ================================================
from PIL import Image
import torchvision.transforms as T

class ImageList(torch.utils.data.Dataset):
    def __init__(self, paths, sz):
        self.paths = paths; self.sz = sz
        self.tx = T.Compose([T.Resize((sz, sz), antialias=True), T.ToTensor(),
                             T.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))])
    def __len__(self): return len(self.paths)
    def __getitem__(self, i):
        try: im = Image.open(self.paths[i]).convert("RGB"); ok = 1
        except Exception: im = Image.new("RGB", (self.sz, self.sz)); ok = 0
        return self.tx(im), i, ok

THROUGHPUT = []
@torch.no_grad()
def extract(paths, fwd, tag):
    dl = torch.utils.data.DataLoader(ImageList(paths, CONFIG.IMG_SIZE), batch_size=CONFIG.BATCH_SIZE, shuffle=False,
                                     num_workers=CONFIG.NUM_WORKERS, pin_memory=(DEVICE == "cuda"))
    out = np.empty((len(paths), EXTRACTOR_INFO["dim"]), np.float16); bad = 0; t0 = time.time()
    amp = torch.bfloat16 if CONFIG.USE_BF16 else torch.float16
    for b, (x, idx, ok) in enumerate(dl):
        x = x.to(DEVICE, non_blocking=True)
        with torch.autocast("cuda", dtype=amp, enabled=(DEVICE == "cuda")):
            d = fwd(x)
        out[idx.numpy()] = torch.nn.functional.normalize(d.float(), dim=1).cpu().numpy().astype(np.float16)
        bad += int((ok == 0).sum())
        if b % 20 == 0: print(f"    {tag}: {min((b+1)*CONFIG.BATCH_SIZE, len(paths))}/{len(paths)} "
                              f"({(b+1)*CONFIG.BATCH_SIZE/max(time.time()-t0,1e-3):.1f} img/s)", flush=True)
    dt = time.time() - t0; THROUGHPUT.append((tag, len(paths), dt))
    assert np.isfinite(out.astype(np.float32)).all(), f"non-finite descriptors in {tag}"
    log(f"E.1.{tag}", "ok" if bad == 0 else "warn", f"{out.shape} in {dt:.0f}s ({len(paths)/max(dt,1e-3):.1f} img/s), unreadable={bad}")
    return out

def quat_to_R(q):
    w, x, y, z = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

def rot_angle_deg(Ra, Rb):
    c = (np.trace(Ra.T @ Rb) - 1) / 2
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))

# === E.2 — extra descriptors from the `vpr-descriptor-weights` dataset (MixVPR / CosPlace / NetVLAD / MegaLoc) ===
def _find_file_dir(fname, roots=("/kaggle/input",), max_depth=4):
    for root in roots:
        for d, subs, files in os.walk(root):
            if d.count(os.sep) - root.count(os.sep) >= max_depth: subs[:] = []
            if fname in files: return d
    return None

WROOT = _find_file_dir("vpr_extra.py")
if WROOT:
    if WROOT not in sys.path: sys.path.insert(0, WROOT)
    import vpr_extra
    for _n, _b in vpr_extra.BUILDERS.items():
        REGISTRY[_n] = (lambda b=_b: b(WROOT, DEVICE))
    print("extra descriptors available:", list(vpr_extra.BUILDERS), "| weights:",
          {d: sorted(os.listdir(os.path.join(WROOT, d))) for d in vpr_extra.BUILDERS if os.path.isdir(os.path.join(WROOT, d))}, flush=True)
else:
    print("vpr-descriptor-weights not attached -> only bundle descriptors", flush=True)


def _walk_find(root, name, max_depth=4):
    for d, subs, files in os.walk(root):
        if d.count(os.sep) - root.count(os.sep) >= max_depth: subs[:] = []
        if name in files: return os.path.join(d, name)
    return None



# ================================================================ 4Seasons loader + dump
import re
MAP_SPACING, Q_DT = 1.0, 0.5            # map: >=1 m apart; queries: uniform in TIME every 0.5 s (stops kept!)
DESCRIPTORS = ["salad", "netvlad", "cosplace"]
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

from collections import defaultdict
by_scene = defaultdict(list)
for s, r in recs:
    if r in CAM0: by_scene[s].append(r)
print("scenes with images:", {s: len(v) for s, v in by_scene.items()}, flush=True)
SCENE = max(by_scene, key=lambda s: len(by_scene[s]))
RECS = sorted(by_scene[SCENE])
print("chosen scene:", SCENE, RECS, flush=True)
ORIG = {}
s = SCENE; r0 = RECS[0]
TT = _readT(os.path.join(POSES, s, r0, "Transformations.txt"))
g = np.loadtxt(os.path.join(POSES, s, r0, "GNSSPoses.txt"), delimiter=",", comments="#", ndmin=2)
p0 = _glob(TT, g[:1, 1:4])[0][0]; ORIG[s] = (p0, _ecef2enu_R(*_ecef2geo(p0)))
os.makedirs(os.path.join(CONFIG.OUT_DIR, "meta"), exist_ok=True)
PARTS = []
for k, r in enumerate(RECS):
    d = os.path.join(POSES, s, r); TT = _readT(os.path.join(d, "Transformations.txt"))
    g = np.loadtxt(os.path.join(d, "GNSSPoses.txt"), delimiter=",", comments="#", ndmin=2)
    cam = CAM0.get(r); p0, Renu = ORIG[s]
    sel, lastP, lastT = [], None, None
    for i in range(len(g)):
        P = g[i, 1:4]; ns = int(g[i, 0]); f = os.path.join(cam, f"{ns}.png")
        if k == 0:
            if lastP is not None and np.linalg.norm(P - lastP) < MAP_SPACING: continue
        else:
            if lastT is not None and (ns - lastT) / 1e9 < Q_DT: continue
        if not os.path.isfile(f): continue
        sel.append((i, f, ns)); lastP = P; lastT = ns
    gi = np.array([x[0] for x in sel])
    pe, Rg = _glob(TT, g[gi, 1:4], np.stack([_q2R(*g[i, 4:8]) for i in gi]))
    C = (Renu @ (pe - p0).T).T; R = np.einsum("ij,njk->nik", Renu, Rg)
    tag = f"4s_{s}_{'map' if k == 0 else 'q'}_{r}"
    np.savez(os.path.join(CONFIG.OUT_DIR, "meta", tag + ".npz"), ns=np.array([x[2] for x in sel], np.int64), C=C, R=R, scene=s, rec=r)
    step = np.linalg.norm(np.diff(C, axis=0), axis=1)
    log(f"4s.{tag}", "ok", f"{len(sel)} frames, path {step.sum():.0f} m, step med {np.median(step):.2f}, stopped frac {np.mean(step < 0.2):.3f}")
    PARTS.append((tag, [x[1] for x in sel]))

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
        if b % 20 == 0: print(f"    {tag}: {min((b+1)*CONFIG.BATCH_SIZE, len(paths))}/{len(paths)} ({(b+1)*CONFIG.BATCH_SIZE/max(time.time()-t0,1e-3):.1f} img/s)", flush=True)
    for d in outs: assert np.isfinite(outs[d].astype(np.float32)).all(), (tag, d)
    log(f"X.{tag}", "ok" if bad == 0 else "warn", f"{len(paths)} imgs in {time.time()-t0:.0f}s, unreadable={bad}")
    return outs

for tag, paths in PARTS:
    o = extract_multi(paths, tag)
    for d, a in o.items(): np.save(os.path.join(CONFIG.OUT_DIR, d, tag + ".npy"), a)
json.dump(REPORT, open(os.path.join(CONFIG.OUT_DIR, "report_k02.json"), "w"), indent=1, default=str)
print("DUMP_DONE", {k: v["status"] for k, v in REPORT.items() if v["status"] != "ok"}, flush=True)
