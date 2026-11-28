"""K11 task (6DoF without an SfM model) for the L4x4 runner. Same algorithm as kaggle/k11_6dof/k11_template.py:
triangulate reference keypoints from the neighbouring reference with KNOWN poses, then PnP for the query
(SuperPoint+LightGlue); candidates single-image vs HMM posterior. A unit = a contiguous slice of queries of one
sequence (cache locality: consecutive queries share candidate references).
Differences to the single-GPU template (engineering only, same numbers): image index built once by the parent;
LRU feature cache sized from VRAM; per-worker convention self-check (deterministic, checked equal at merge)."""
import time
from collections import OrderedDict
import numpy as np

KIND = "k11"
COST_PER_QUERY = {"cmu": 0.85, "4s": 2.6}         # T4 seconds per query measured on hmm-k11 cmu0/cmu3/4s2 (28/11)


# ------------------------------------------------------------------ parent side
def index_rule(cfg):
    """(path substring required, cam_dir) used by the parent when it walks /kaggle/input once."""
    return {"slug": cfg["slug"], "cam_dir": cfg["CFG"]["cam_dir"], "exts": None}


def accept(cfg, d, f):
    C = cfg["CFG"]
    if "/sources" in d or "/checkpoints" in d or cfg["slug"] not in d:
        return False
    if C["cam_dir"] and (not d.endswith(C["cam_dir"]) or (C["cam_dir"] == "cam0" and "undistorted" not in d)):
        return False
    return True


def needed(cfg):
    C = cfg["CFG"]
    return set(C["refs"]) | {q["name"] for q in C["queries"]}


def make_units(task_id, cfg, unit_sec=120, smoke=False):
    C = cfg["CFG"]; cpq = COST_PER_QUERY[cfg["family"]]
    per = max(8, int(unit_sec / cpq)) if not smoke else 6
    units, s, n = [], 0, len(C["queries"])
    while s < n:                                     # split at sequence boundaries or every `per` queries
        e, seq = s, C["queries"][s]["seq"]
        while e < n and e - s < per and C["queries"][e]["seq"] == seq:
            e += 1
        units.append({"task": task_id, "uid": f"{task_id}-{s:05d}", "rows": [s, e], "cost": (e - s) * cpq})
        s = e
    if smoke:
        units = units[:2]
    return units


def merge(task_id, cfg, parts):
    """parts: list of part dicts. Returns (filename, object, check-dict)."""
    C = cfg["CFG"]; n = len(C["queries"])
    cover = np.zeros(n, int); conv = {}; res = {m: [] for m in C["methods"]}; recs = []
    for p in parts:
        s, e = p["rows"]; cover[s:e] += 1
        conv[p["convention"]] = conv.get(p["convention"], 0) + 1
        recs.extend(p["records"])
    recs.sort(key=lambda r: (r["qi"], C["methods"].index(r["meth"])))
    for r in recs:
        m = r.pop("meth"); r.pop("qi"); res[m].append(r)
    best = max(conv, key=conv.get) if conv else None
    chk = {"queries": n, "covered_once": int((cover == 1).sum()), "missing": int((cover == 0).sum()),
           "dup": int((cover > 1).sum()), "conventions": conv, "conv_consistent": len(conv) <= 1}
    sc = parts[0]["selfcheck"] if parts else {}
    return f"k11_out_{cfg['name']}.json", {"convention": best, "selfcheck": sc, "results": res, "merge_check": chk}, chk


# ------------------------------------------------------------------ worker side
class State:
    pass


def prepare(cfg, ctx):
    import cv2, torch
    st = State(); C = cfg["CFG"]; st.C = C; st.ctx = ctx
    st.idx = ctx["index"][cfg["task_id"]]
    st.K = np.array(C["K"], float); st.dist = np.array(C["dist"], float); st.REF = C["refs"]
    st.FC = OrderedDict(); st.cap = ctx["fc_cap"]; st.T3 = {}
    ext, mat, rbd, load_image, DEV = ctx["ext"], ctx["mat"], ctx["rbd"], ctx["load_image"], ctx["dev"]

    def norm_pts(uv):
        if len(uv) == 0:
            return uv.reshape(0, 2)
        return cv2.undistortPoints(uv.reshape(-1, 1, 2).astype(np.float64), st.K, st.dist).reshape(-1, 2)

    @torch.no_grad()
    def feats(k):
        if k in st.FC:
            st.FC.move_to_end(k); return st.FC[k]
        f = ext.extract(load_image(st.idx[k]).to(DEV)); v = (f, f["keypoints"][0].cpu().numpy())
        st.FC[k] = v
        if len(st.FC) > st.cap:
            st.FC.popitem(last=False)
        return v

    @torch.no_grad()
    def match(a, b):
        fa, ka = feats(a); fb, kb = feats(b)
        m = rbd(mat({"image0": fa, "image1": fb}))["matches"].cpu().numpy(); return m, ka, kb

    def pose(name, variant):
        R = np.array(st.REF[name]["R"]); Cc = np.array(st.REF[name]["C"]); Rv = np.array(C["variants"][variant])
        return R @ Rv, Cc

    def sampson(a, b, n1, n2, variant):
        R1, C1 = pose(n1, variant); R2, C2 = pose(n2, variant)
        Rrel = R2.T @ R1; t = R2.T @ (C1 - C2)
        tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]]); E = tx @ Rrel
        x1 = np.c_[a, np.ones(len(a))]; x2 = np.c_[b, np.ones(len(b))]
        Ex1 = x1 @ E.T; Etx2 = x2 @ E; num = np.sum(x2 * Ex1, 1) ** 2
        return num / (Ex1[:, 0] ** 2 + Ex1[:, 1] ** 2 + Etx2[:, 0] ** 2 + Etx2[:, 1] ** 2) * st.K[0, 0] ** 2

    st.norm_pts, st.feats, st.match, st.pose, st.sampson = norm_pts, feats, match, pose, sampson
    # convention self-check on the same 40 reference pairs as the template (deterministic)
    names = sorted(st.REF); report = {}
    pairs = [(n, st.REF[n]["nb"]) for n in names[::max(1, len(names) // 40)] if st.REF[n]["nb"] in st.idx and n in st.idx][:40]
    for v in C["variants"]:
        errs = []
        for a, b in pairs:
            m, ka, kb = match(a, b)
            if len(m) < 20:
                continue
            errs.append(np.median(np.sqrt(sampson(norm_pts(ka[m[:, 0]]), norm_pts(kb[m[:, 1]]), a, b, v))))
        report[v] = float(np.median(errs)) if errs else 1e9
    st.best_v = min(report, key=report.get); st.report = report
    print(f"[{ctx['worker']}] {cfg['task_id']} convention {report} -> {st.best_v}", flush=True)
    return st


def _tri3d(st, n):
    import cv2
    nb = st.REF[n]["nb"]
    if nb not in st.idx:
        return None
    m, ka, kb = st.match(n, nb)
    if len(m) < 15:
        return None
    a, b = st.norm_pts(ka[m[:, 0]]), st.norm_pts(kb[m[:, 1]])
    R1, C1 = st.pose(n, st.best_v); R2, C2 = st.pose(nb, st.best_v)
    P1 = np.c_[R1.T, -R1.T @ C1]; P2 = np.c_[R2.T, -R2.T @ C2]
    X = cv2.triangulatePoints(P1, P2, a.T, b.T); X = (X[:3] / X[3]).T
    z1 = (X - C1) @ R1[:, 2]; z2 = (X - C2) @ R2[:, 2]
    e = np.sqrt(st.sampson(a, b, n, nb, st.best_v)); good = (z1 > 0.5) & (z2 > 0.5) & (e < 4.0) & (z1 < 150)
    out = np.full((len(ka), 3), np.nan); out[m[good, 0]] = X[good]; return out


def _rerr(Ra, Rb):
    return float(np.degrees(np.arccos(np.clip((np.trace(Ra.T @ Rb) - 1) / 2, -1, 1))))


def run_unit(st, unit, hb):
    import cv2
    C = st.C; s, e = unit["rows"]; recs = []; t0 = time.time()
    for qi in range(s, e):
        q = C["queries"][qi]
        if q["name"] not in st.idx:
            continue
        fq, kq = st.feats(q["name"]); gC = np.array(q["C"]); gR = np.array(q["R"]) @ np.array(C["variants"][st.best_v])
        for meth in C["methods"]:
            P2, P3 = [], []
            for r in q["cands"][meth]:
                if r not in st.idx:
                    continue
                if r not in st.T3:
                    st.T3[r] = _tri3d(st, r)
                if st.T3[r] is None:
                    continue
                mm, _, _ = st.match(q["name"], r); X = st.T3[r][mm[:, 1]]; ok = np.isfinite(X[:, 0])
                P2.append(kq[mm[ok, 0]]); P3.append(X[ok])
            rec = {"qi": qi, "meth": meth, "q": q["name"], "seq": q["seq"], "ok": False, "n": int(sum(len(p) for p in P2))}
            if rec["n"] >= 8:
                u = st.norm_pts(np.concatenate(P2)); X = np.concatenate(P3)
                okp, rv, tv, inl = cv2.solvePnPRansac(X, u, np.eye(3), None, iterationsCount=5000,
                                                      reprojectionError=6.0 / st.K[0, 0], confidence=0.9999,
                                                      flags=cv2.SOLVEPNP_EPNP)
                if okp and inl is not None and len(inl) >= 12:
                    Rw = cv2.Rodrigues(rv)[0]; Cw = -Rw.T @ tv.ravel()
                    rec.update(ok=True, inl=int(len(inl)), dt=float(np.linalg.norm(Cw - gC)), dr=_rerr(gR, Rw.T))
            r0 = q["cands"][meth][0]
            if r0 in st.REF:
                Rr, Cr = st.pose(r0, st.best_v)
                rec["retr_dt"] = float(np.linalg.norm(Cr - gC)); rec["retr_dr"] = _rerr(gR, Rr)
            recs.append(rec)
        hb(done=qi - s + 1, total=e - s)
    return {"rows": [s, e], "records": recs, "convention": st.best_v, "selfcheck": st.report,
            "sec": time.time() - t0, "t3": len(st.T3)}
