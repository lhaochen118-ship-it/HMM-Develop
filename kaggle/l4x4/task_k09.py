"""K09 task (geometric verification for HMM fusion, I30) for the L4x4 runner. Same algorithm as
kaggle/k09_geo/k09_template.py (SuperPoint 2048 + LightGlue, fundamental-matrix USAC_MAGSAC inliers, A29 guard).
A unit = a contiguous slice of the sorted pair list (pairs sorted by query -> query features reused in the unit)."""
import time
from collections import OrderedDict
import numpy as np

KIND = "k09"
COST_PER_PAIR = 0.10                                 # T4 seconds per pair (hmm-k09 cmu2/3/4: 721-776 s / 7584 pairs)


def accept(cfg, d, f):
    if "/sources" in d or "/checkpoints" in d or cfg["slug"] not in d:
        return False
    if cfg["ds"] == "rc" and d.rstrip("/").split("/")[-1] != "rear":
        return False
    return f.lower().endswith((".jpg", ".png"))


def needed(cfg):
    return {p[0] for p in cfg["PAIRS"]} | {p[1] for p in cfg["PAIRS"]}


def make_units(task_id, cfg, unit_sec=60, smoke=False):
    P = sorted(map(tuple, cfg["PAIRS"])); per = max(50, int(unit_sec / COST_PER_PAIR)) if not smoke else 40
    units = [{"task": task_id, "uid": f"{task_id}-{s:06d}", "rows": [s, min(len(P), s + per)],
              "cost": (min(len(P), s + per) - s) * COST_PER_PAIR} for s in range(0, len(P), per)]
    return units[:2] if smoke else units


def merge(task_id, cfg, parts):
    P = sorted(map(tuple, cfg["PAIRS"])); n = len(P); cover = np.zeros(n, int); rows = [None] * n
    for p in parts:
        s, e = p["rows"]; cover[s:e] += 1
        for i, r in zip(range(s, e), p["out"]):
            rows[i] = r
    ok_order = all(rows[i] is None or (rows[i][0], rows[i][1]) == P[i] for i in range(n))
    chk = {"pairs": n, "covered_once": int((cover == 1).sum()), "missing": int((cover == 0).sum()),
           "dup": int((cover > 1).sum()), "order_ok": bool(ok_order)}
    return f"geo_{cfg['ds']}_{cfg['chunk']}.json", [r for r in rows if r is not None], chk


class State:
    pass


def prepare(cfg, ctx):
    st = State(); st.idx = ctx["index"][cfg["task_id"]]; st.P = sorted(map(tuple, cfg["PAIRS"]))
    st.FC = OrderedDict(); st.cap = ctx["fc_cap"]; st.ctx = ctx
    return st


def run_unit(st, unit, hb):
    import cv2, torch
    ext, mat, rbd, load_image, DEV = (st.ctx[k] for k in ("ext", "mat", "rbd", "load_image", "dev"))

    @torch.no_grad()
    def feats(k):
        if k in st.FC:
            st.FC.move_to_end(k); return st.FC[k]
        v = ext.extract(load_image(st.idx[k]).to(DEV)); st.FC[k] = v
        if len(st.FC) > st.cap:
            st.FC.popitem(last=False)
        return v

    s, e = unit["rows"]; out = []; t0 = time.time()
    for i in range(s, e):
        q, r = st.P[i]
        if q not in st.idx or r not in st.idx:
            out.append([q, r, -1, -1]); continue
        fq, fr = feats(q), feats(r)
        with torch.no_grad():
            m = rbd(mat({"image0": fq, "image1": fr}))["matches"].cpu().numpy()
        inl = 0
        if len(m) >= 8:
            a = fq["keypoints"][0].cpu().numpy()[m[:, 0]]; b = fr["keypoints"][0].cpu().numpy()[m[:, 1]]
            try:
                F, mask = cv2.findFundamentalMat(a, b, cv2.USAC_MAGSAC, 3.0, 0.999, 5000)
                inl = int(mask.sum()) if mask is not None else 0
            except cv2.error:                       # A29: degenerate configuration -> no geometric support
                inl = 0
        out.append([q, r, int(len(m)), inl])
        if (i - s) % 50 == 0:
            hb(done=i - s + 1, total=e - s)
    return {"rows": [s, e], "out": out, "sec": time.time() - t0}
