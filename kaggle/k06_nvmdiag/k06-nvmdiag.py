"""K06 (CPU) — diagnose the coordinate convention of RobotCar Seasons all.nvm observations vs image pixels."""
import os, numpy as np, cv2, time
from scipy.spatial import cKDTree
def walk_find(root, name, depth=6):
    for d, subs, fs in os.walk(root):
        if d.count(os.sep) - root.count(os.sep) >= depth: subs[:] = []
        if name in fs: return os.path.join(d, name)
nvm = walk_find("/kaggle/input", "all.nvm"); RC = nvm.split("/3D-models")[0]
print([f for f in os.listdir(RC)], flush=True)
for d, _, fs in os.walk(RC):
    for f in fs:
        if "intrinsic" in f.lower() or f.endswith(".txt") and "3D-models" not in d: print("txt:", os.path.join(d, f))
idx = {}
for d, _, fs in os.walk(os.path.join(RC, "images")):
    for f in fs: idx[(os.path.basename(d), os.path.splitext(f)[0])] = os.path.join(d, f)
def q2R(q):
    w, x, y, z = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
with open(nvm) as fh:
    fh.readline(); line = fh.readline()
    while not line.strip(): line = fh.readline()
    n = int(line.split()[0]); pick = {}; names = []
    for i in range(n):
        t = fh.readline().split(); names.append(t[0])
        parts = t[0].replace("\\", "/").split("/")
        if parts[-3] == "overcast-reference" and parts[-2] == "rear" and len(pick) < 4 and i % 1500 == 7:
            pick[i] = (os.path.splitext(parts[-1])[0], float(t[1]), q2R(list(map(float, t[2:6]))), np.array(list(map(float, t[6:9]))), t[9:])
    print("example cam lines:", names[:2], {k: (v[0], v[1], v[4]) for k, v in pick.items()}, flush=True)
    line = fh.readline()
    while not line.strip(): line = fh.readline()
    npts = int(line.split()[0]); obs = {k: [] for k in pick}
    for k in range(npts):
        t = fh.readline().split(); nm = int(t[6])
        for m in range(nm):
            ci = int(t[7 + 4 * m])
            if ci in pick: obs[ci].append([float(t[9 + 4*m]), float(t[10 + 4*m]), float(t[0]), float(t[1]), float(t[2])])
sift = cv2.SIFT_create(nfeatures=8000)
for ci, (ts, f, R, C, extra) in pick.items():
    o = np.array(obs[ci]); img = cv2.imread(idx[("rear", ts)], cv2.IMREAD_GRAYSCALE); H, W = img.shape
    kp = np.array([k.pt for k in sift.detect(img, None)]); tree = cKDTree(kp)
    Xc = (R @ (o[:, 2:5] - C).T).T; proj = f * Xc[:, :2] / Xc[:, 2:3]
    print(f"\n== ref {ts} img {W}x{H} f={f:.1f} extra={extra} n_obs={len(o)} | obs x range {o[:,0].min():.0f}..{o[:,0].max():.0f} y {o[:,1].min():.0f}..{o[:,1].max():.0f}")
    print("   projection vs obs: median |proj-obs| =", np.median(np.linalg.norm(proj - o[:, :2], axis=1)).round(2),
          "| depth>0 frac", (Xc[:, 2] > 0).mean().round(3))
    for name, uv in [("center", o[:, :2] + [W/2, H/2]), ("raw", o[:, :2]), ("center_flipy", np.c_[o[:, 0] + W/2, H/2 - o[:, 1]]),
                     ("center_x2", o[:, :2] * 2 + [W/2, H/2]), ("center_x0.5", o[:, :2] * 0.5 + [W/2, H/2]),
                     ("proj_center", proj + [W/2, H/2])]:
        d, _ = tree.query(uv); print(f"   {name:12s} median NN dist to SIFT {np.median(d):6.2f} px | frac<3px {np.mean(d<3):.3f}")
print("K06_DONE")
