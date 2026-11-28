"""K11 — 6DoF without an SfM model: triangulate reference keypoints from neighbouring references with KNOWN poses,
then PnP for the query (SuperPoint+LightGlue). Candidates: single-image vs HMM posterior (k=3, same budget).
Self-checks camera conventions with the epipolar (Sampson) error of reference pairs before use."""
import os, sys, json, zlib, base64, time, shutil
import numpy as np, torch, cv2
CFG = json.loads(zlib.decompress(base64.b64decode("__B64__")))
DEV = "cuda" if torch.cuda.is_available() else "cpu"; t00 = time.time()
print("device", DEV, torch.cuda.get_device_name(0) if DEV == "cuda" else "", "| queries", len(CFG["queries"]), "| refs", len(CFG["refs"]), flush=True)
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
need = set(CFG["refs"]) | {q["name"] for q in CFG["queries"]}; idx = {}
for d, subs, fs in os.walk("/kaggle/input"):
    if "/sources" in d or "/checkpoints" in d: continue
    if CFG["cam_dir"] and (not d.endswith(CFG["cam_dir"]) or (CFG["cam_dir"] == "cam0" and "undistorted" not in d)): continue
    for f in fs:
        k = os.path.splitext(f)[0]
        if k in need: idx[k] = os.path.join(d, f)
print("resolved", len(idx), "/", len(need), f"{time.time()-t00:.0f}s", flush=True)
K = np.array(CFG["K"], float); dist = np.array(CFG["dist"], float)
def norm_pts(uv):
    if len(uv) == 0: return uv.reshape(0, 2)
    return cv2.undistortPoints(uv.reshape(-1, 1, 2).astype(np.float64), K, dist).reshape(-1, 2)
FC = {}
@torch.no_grad()
def feats(k):
    if k not in FC:
        if len(FC) > 5000: FC.clear()
        f = ext.extract(load_image(idx[k]).to(DEV)); FC[k] = (f, f["keypoints"][0].cpu().numpy())
    return FC[k]
@torch.no_grad()
def match(a, b):
    fa, ka = feats(a); fb, kb = feats(b); m = rbd(mat({"image0": fa, "image1": fb}))["matches"].cpu().numpy(); return m, ka, kb
REF = CFG["refs"]
def pose(name, variant):
    R = np.array(REF[name]["R"]); C = np.array(REF[name]["C"]); Rv = np.array(CFG["variants"][variant])
    return R @ Rv, C                                                  # camera->world rotation, centre
def sampson(a, b, n1, n2, variant):
    R1, C1 = pose(n1, variant); R2, C2 = pose(n2, variant)
    Rrel = R2.T @ R1; t = R2.T @ (C1 - C2); tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]]); E = tx @ Rrel
    x1 = np.c_[a, np.ones(len(a))]; x2 = np.c_[b, np.ones(len(b))]
    Ex1 = x1 @ E.T; Etx2 = x2 @ E; num = np.sum(x2 * Ex1, 1) ** 2
    return num / (Ex1[:, 0] ** 2 + Ex1[:, 1] ** 2 + Etx2[:, 0] ** 2 + Etx2[:, 1] ** 2) * K[0, 0] ** 2
# ---- self-check of conventions on reference pairs
names = sorted(REF); best_v, report = None, {}
pairs = [(n, REF[n]["nb"]) for n in names[::max(1, len(names) // 40)] if REF[n]["nb"] in idx and n in idx][:40]
for v in CFG["variants"]:
    errs = []
    for a, b in pairs:
        m, ka, kb = match(a, b)
        if len(m) < 20: continue
        errs.append(np.median(np.sqrt(sampson(norm_pts(ka[m[:, 0]]), norm_pts(kb[m[:, 1]]), a, b, v))))
    report[v] = float(np.median(errs)) if errs else 1e9
best_v = min(report, key=report.get); print("convention self-check (median Sampson px):", report, "->", best_v, flush=True)
def tri3d(n):
    nb = REF[n]["nb"]
    if nb not in idx: return None
    m, ka, kb = match(n, nb)
    if len(m) < 15: return None
    a, b = norm_pts(ka[m[:, 0]]), norm_pts(kb[m[:, 1]])
    R1, C1 = pose(n, best_v); R2, C2 = pose(nb, best_v)
    P1 = np.c_[R1.T, -R1.T @ C1]; P2 = np.c_[R2.T, -R2.T @ C2]
    X = cv2.triangulatePoints(P1, P2, a.T, b.T); X = (X[:3] / X[3]).T
    z1 = (X - C1) @ R1[:, 2]; z2 = (X - C2) @ R2[:, 2]
    e = np.sqrt(sampson(a, b, n, nb, best_v)); good = (z1 > 0.5) & (z2 > 0.5) & (e < 4.0) & (z1 < 150)
    out = np.full((len(ka), 3), np.nan); out[m[good, 0]] = X[good]; return out
T3 = {}
def rerr(Ra, Rb): return float(np.degrees(np.arccos(np.clip((np.trace(Ra.T @ Rb) - 1) / 2, -1, 1))))
RES = {m: [] for m in CFG["methods"]}; t0 = time.time()
for qi, q in enumerate(CFG["queries"]):
    if q["name"] not in idx: continue
    fq, kq = feats(q["name"]); gC = np.array(q["C"]); gR = np.array(q["R"]) @ np.array(CFG["variants"][best_v])
    for meth in CFG["methods"]:
        P2, P3 = [], []
        for r in q["cands"][meth]:
            if r not in idx: continue
            if r not in T3: T3[r] = tri3d(r)
            if T3[r] is None: continue
            mm, _, _ = match(q["name"], r); X = T3[r][mm[:, 1]]; ok = np.isfinite(X[:, 0])
            P2.append(kq[mm[ok, 0]]); P3.append(X[ok])
        rec = {"q": q["name"], "seq": q["seq"], "ok": False, "n": int(sum(len(p) for p in P2))}
        if rec["n"] >= 8:
            u = norm_pts(np.concatenate(P2)); X = np.concatenate(P3)
            okp, rv, tv, inl = cv2.solvePnPRansac(X, u, np.eye(3), None, iterationsCount=5000, reprojectionError=6.0 / K[0, 0],
                                                  confidence=0.9999, flags=cv2.SOLVEPNP_EPNP)
            if okp and inl is not None and len(inl) >= 12:
                Rw = cv2.Rodrigues(rv)[0]; C = -Rw.T @ tv.ravel()
                rec.update(ok=True, inl=int(len(inl)), dt=float(np.linalg.norm(C - gC)), dr=rerr(gR, Rw.T))
        r0 = q["cands"][meth][0]
        if r0 in REF:
            Rr, Cr = pose(r0, best_v); rec["retr_dt"] = float(np.linalg.norm(Cr - gC)); rec["retr_dr"] = rerr(gR, Rr)
        RES[meth].append(rec)
    if qi % 200 == 0: print(f"  q {qi}/{len(CFG['queries'])} ({time.time()-t0:.0f}s) refs3d {len(T3)}", flush=True)
json.dump({"convention": best_v, "selfcheck": report, "results": RES}, open("/kaggle/working/k11_out.json", "w"))
for m, L in RES.items():
    dt = np.array([r.get("dt", 1e9) for r in L]); dr = np.array([r.get("dr", 1e9) for r in L])
    print(m, len(L), "PnP", [round(float(np.mean((dt <= a) & (dr <= b))), 3) for a, b in ((0.25, 2), (0.5, 5), (5, 10))], flush=True)
print("K11_DONE", f"{time.time()-t00:.0f}s", flush=True)
