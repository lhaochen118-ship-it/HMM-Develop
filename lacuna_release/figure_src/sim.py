"""Illustrative simulation for the README GIF: the same Bayes filter run closed-world (belief only on mapped cells)
and open-world (LACUNA: belief on mapped + unmapped cells, unmapped cells get calibrated absolute evidence).
Synthetic map: a main street with a hole, a parallel look-alike street, two cross streets. Writes frames.json."""
import json, numpy as np

CELL, W, H = 4.0, 100, 50                     # 400 m x 200 m grid, 4 m cells
Y_MAIN, Y_ALIAS = 130.0, 50.0                 # cell-centre rows 32 and 12
X_CROSS = (42.0, 358.0)
HOLE = (150.0, 250.0)                         # main street has no map images here
X0, X1 = 22.0, 378.0
rng = np.random.default_rng(3)

cx = np.arange(W) * CELL + CELL / 2; cy = np.arange(H) * CELL + CELL / 2
img = []                                      # (x, y, kind)
for x in cx:
    if X0 <= x <= X1 and not (HOLE[0] <= x <= HOLE[1]): img.append((x, Y_MAIN, "main"))
    if X0 <= x <= X1: img.append((x, Y_ALIAS, "alias"))
for xc in X_CROSS:
    for y in cy:
        if Y_ALIAS < y < Y_MAIN: img.append((xc, y, "cross"))
img = np.array([(a, b, {"main": 0, "alias": 1, "cross": 2}[k]) for a, b, k in img])
ix = (img[:, 0] // CELL).astype(int); iy = (img[:, 1] // CELL).astype(int)
mapped = np.zeros((H, W), bool); mapped[iy, ix] = True


def blur(p, s):
    r = 3; k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum()
    q = np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 1, p)
    return np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 0, q)


def shift(p):                                 # odometry: +1 cell east; mass leaving the grid is returned
    out = np.zeros_like(p); out[:, 1:] = p[:, :-1]; return out, p[:, -1].sum()


def gauss(x, m, s): return np.exp(-0.5 * ((x - m) / s) ** 2) / s


def box3(p):
    q = np.pad(p, 1); return sum(q[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] for dy in (-1, 0, 1) for dx in (-1, 0, 1))


def decide(p):
    """report a fix when the mass within ~6 m of one mapped cell is >= 1 - 1e-3 (a simplified confidence tier)"""
    b = np.where(mapped, box3(p), 0); j = np.unravel_index(np.argmax(b), b.shape)
    if b[j] < 1 - 1e-3: return None
    ys, xs = slice(max(j[0] - 1, 0), j[0] + 2), slice(max(j[1] - 1, 0), j[1] + 2)
    w = p[ys, xs]; gy, gx = np.mgrid[ys, xs]
    return float((w * (gx * CELL + CELL / 2)).sum() / w.sum()), float((w * (gy * CELL + CELL / 2)).sum() / w.sum())


beta, eps, sig = 1.0, 1e-5, 0.35
start = np.zeros((H, W)); start[int(Y_MAIN // CELL), int(X0 // CELL)] = 1; start = blur(start, 1.0)
p_open = start.copy(); omega = 0.0
p_cw = np.where(mapped, start, 0); p_cw /= p_cw.sum()
frames = []
xr = X0
while xr <= X1 + 1e-9:
    # appearance: true place strong, look-alike street (motion-consistent copy) weak, everything else background
    s = 0.20 + 0.03 * rng.standard_normal(len(img))
    dx = img[:, 0] - xr
    s += np.where(img[:, 2] == 0, 0.55 * np.exp(-(dx / 6) ** 2), 0)
    s += np.where(img[:, 2] == 1, 0.25 * np.exp(-(dx / 6) ** 2), 0)
    med = np.median(s); mad = 1.4826 * np.median(np.abs(s - med)); z = (s - med) / mad
    L = np.exp(beta * z - (beta * z).max()); L /= L.mean()
    Lc = np.zeros((H, W)); Lc[iy, ix] = L
    x_stat = s.max() - med                                         # frame statistic of the calibrated evidence
    lu = np.clip(np.log(gauss(x_stat, 0.25, 0.06)) - np.log(gauss(x_stat, 0.55, 0.06)), -8, 8)
    if frames:                                                     # predict (first frame: prior only)
        p_open, out = shift(p_open); omega += out; p_open = blur(p_open, sig)
        tot = p_open.sum() + omega; p_open = (1 - eps) * p_open / tot + eps / (H * W + 1); omega = (1 - eps) * omega / tot + eps / (H * W + 1)
        p_cw, _ = shift(p_cw); p_cw = np.where(mapped, blur(p_cw, sig), 0); p_cw /= p_cw.sum()
        p_cw = np.where(mapped, (1 - eps) * p_cw + eps / mapped.sum(), 0)
    # update
    E = np.where(mapped, Lc, np.exp(lu)); p_open = p_open * E; omega *= np.exp(lu)
    tot = p_open.sum() + omega; p_open /= tot; omega /= tot
    p_cw = p_cw * Lc; p_cw /= p_cw.sum()
    dmap = np.min(np.hypot(img[:, 0] - xr, img[:, 1] - Y_MAIN))
    rec = dict(x=xr, y=Y_MAIN, off=bool(dmap > 10))
    for name, p in (("cw", p_cw), ("ow", p_open)):
        f = decide(p)
        rec[name] = dict(fix=f, ok=None if f is None else bool(np.hypot(f[0] - xr, f[1] - Y_MAIN) <= 10),
                         err=None if f is None else float(np.hypot(f[0] - xr, f[1] - Y_MAIN)), belief=p.tolist())
    frames.append(rec)
    xr += CELL

json.dump(dict(cell=CELL, W=W, H=H, y_main=Y_MAIN, y_alias=Y_ALIAS, x_cross=X_CROSS, hole=HOLE, x0=X0, x1=X1,
               img=img.tolist(), frames=frames), open("frames.json", "w"))
for name in ("cw", "ow"):
    ok = sum(1 for f in frames if f[name]["ok"] is True); bad = sum(1 for f in frames if f[name]["ok"] is False)
    ab = sum(1 for f in frames if f[name]["fix"] is None)
    print(f"{name}: correct {ok}, false {bad}, abstain {ab}, of {len(frames)}; off-map frames {sum(f['off'] for f in frames)}")
print("false-fix errors cw:", sorted({round(f['cw']['err']) for f in frames if f['cw']['ok'] is False})[:5])
print("first/last off-map frame:", [i for i, f in enumerate(frames) if f['off']][:1], [i for i, f in enumerate(frames) if f['off']][-1:])
print("cw decisions:", "".join('.' if f['cw']['fix'] is None else ('+' if f['cw']['ok'] else 'X') for f in frames))
print("ow decisions:", "".join('.' if f['ow']['fix'] is None else ('+' if f['ow']['ok'] else 'X') for f in frames))
print("off map     :", "".join('o' if f['off'] else '-' for f in frames))
