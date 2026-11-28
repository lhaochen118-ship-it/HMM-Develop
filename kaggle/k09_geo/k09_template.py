"""K09 — geometric verification for HMM fusion (I30): SuperPoint(2048)+LightGlue matches and fundamental-matrix
RANSAC inliers for a chunk of (query, reference) pairs. Output: /kaggle/working/geo_<chunk>.json"""
import os, sys, json, zlib, base64, time, shutil
import numpy as np, torch, cv2
DS, CHUNK = "__DS__", "__CHUNK__"
PAIRS = json.loads(zlib.decompress(base64.b64decode("__B64__")))
DEV = "cuda" if torch.cuda.is_available() else "cpu"; t00 = time.time()
print("device", DEV, torch.cuda.get_device_name(0) if DEV == "cuda" else "", "| pairs", len(PAIRS), flush=True)
def walk_find(root, name, depth=6):
    for d, subs, fs in os.walk(root):
        if d.count(os.sep) - root.count(os.sep) >= depth: subs[:] = []
        if name in fs: return os.path.join(d, name)
lg = None
for d, subs, fs in os.walk("/kaggle/input"):
    if os.path.basename(d) == "lightglue" and "lightglue.py" in fs: lg = os.path.dirname(d); break
sys.path.insert(0, lg)
ck = os.path.dirname(walk_find("/kaggle/input", "superpoint_v1.pth"))
hub = os.path.expanduser("~/.cache/torch/hub/checkpoints"); os.makedirs(hub, exist_ok=True)
for f in ("superpoint_v1.pth", "superpoint_lightglue_v0-1_arxiv.pth"): shutil.copy(os.path.join(ck, f), hub)
from lightglue import LightGlue, SuperPoint
from lightglue.utils import load_image, rbd
ext = SuperPoint(max_num_keypoints=2048).eval().to(DEV); mat = LightGlue(features="superpoint").eval().to(DEV)
need = {p[0] for p in PAIRS} | {p[1] for p in PAIRS}; idx = {}
for d, subs, fs in os.walk("/kaggle/input"):
    if "/sources" in d or "/checkpoints" in d: continue
    if DS == "rc" and os.path.basename(d) != "rear": continue
    for f in fs:
        k = os.path.splitext(f)[0]
        if k in need and f.lower().endswith((".jpg", ".png")): idx[k] = os.path.join(d, f)
print("resolved", len(idx), "/", len(need), f"{time.time()-t00:.0f}s", flush=True)
FC = {}
@torch.no_grad()
def feats(k):
    if k not in FC:
        if len(FC) > 6000: FC.clear()
        FC[k] = ext.extract(load_image(idx[k]).to(DEV))
    return FC[k]
out = []; t0 = time.time()
for n, (q, r) in enumerate(sorted(PAIRS)):
    if q not in idx or r not in idx: out.append([q, r, -1, -1]); continue
    fq, fr = feats(q), feats(r)
    with torch.no_grad(): m = rbd(mat({"image0": fq, "image1": fr}))["matches"].cpu().numpy()
    inl = 0
    if len(m) >= 8:
        a = fq["keypoints"][0].cpu().numpy()[m[:, 0]]; b = fr["keypoints"][0].cpu().numpy()[m[:, 1]]
        F, mask = cv2.findFundamentalMat(a, b, cv2.USAC_MAGSAC, 3.0, 0.999, 5000)
        inl = int(mask.sum()) if mask is not None else 0
    out.append([q, r, int(len(m)), inl])
    if n % 500 == 0: print(f"  {n}/{len(PAIRS)} ({time.time()-t0:.0f}s)", flush=True)
os.makedirs("/kaggle/working", exist_ok=True); json.dump(out, open(f"/kaggle/working/geo_{DS}_{CHUNK}.json", "w"))
print("K09_DONE", len(out), f"{time.time()-t00:.0f}s", flush=True)
