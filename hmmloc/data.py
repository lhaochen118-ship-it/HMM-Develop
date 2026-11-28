"""Episode loaders for the cached feature bank (Kaggle dumps nb15a-d, k01).

An Episode bundles: map descriptors R (M,D), map positions s (M,) along the reference chain
(metres for RobotCar/CMU, frame index for Nordland), map centres C (M,3) (if any),
query descriptors Q (T,D), sequence ids (T,), conditions (T,), a positives mask (T,M),
a `near` matrix (M,M bool, map-only tolerance neighbourhood) and a calibration/test split by sequence.
Only map poses are used to build the map graph; query poses are used ONLY for ground truth.
"""
from __future__ import annotations
import os, re, glob
import numpy as np
from dataclasses import dataclass, field

FB = os.environ.get("HMMLOC_FB", "/tmp/claude-0/-home-user-HMM-Develop/865660f3-ecf6-5c6c-b462-db1884ef1e8f/scratchpad/fb")
DUMP_OF = {  # (dataset, descriptor) -> dump dir
    ("nord", "salad"): "dive-vpr-nb15a-dump", ("rc", "salad"): "dive-vpr-nb15a-dump",
    ("cmu", "salad"): "dive-vpr-nb15b-dump",
}
for d in ["dinov2", "netvlad", "cosplace", "mixvpr", "megaloc"]:
    DUMP_OF[("nord", d)] = DUMP_OF[("rc", d)] = "dive-vpr-nb15c-dump"; DUMP_OF[("cmu", d)] = "dive-vpr-nb15d-dump"
for d in ["salad", "megaloc", "netvlad", "cosplace"]:
    DUMP_OF[("nordseg", d)] = "hmm-k01-nordseg"
for _ds in ("nord", "rc", "cmu"):
    DUMP_OF[(_ds, "jist")] = "hmm-k07-jist"          # JIST (ResNet-18 + SeqGeM) per-frame descriptors
    for _d in ("seqvlad", "seqvlad_raw"):            # SeqVLAD (CCT384, MSLS-trained) per-frame, kernels k12
        DUMP_OF[(_ds, _d)] = "hmm-k12-seqvlad"
CMU_SLICES = [6, 7, 8, 10, 11, 12, 13, 21, 22, 23, 24]


@dataclass
class Episode:
    name: str
    R: np.ndarray
    s: np.ndarray
    Q: np.ndarray
    seq: np.ndarray
    cond: np.ndarray
    pos: np.ndarray
    near: np.ndarray
    calib_seq: set
    unit: str = "m"
    C: np.ndarray = None
    Rrot: np.ndarray = None
    qC: np.ndarray = None
    qR: np.ndarray = None
    qt: np.ndarray = None
    meta: dict = field(default_factory=dict)

    @property
    def T(self): return len(self.Q)
    @property
    def M(self): return len(self.R)

    def sim(self):
        if not hasattr(self, "_S"):
            self._S = (self.Q.astype(np.float32) @ self.R.astype(np.float32).T)
        return self._S

    def rows(self, which):
        c = np.array([q in self.calib_seq for q in self.seq])
        return np.where(c if which == "calib" else ~c)[0]

    def reset_mask(self):
        r = np.zeros(self.T, bool); r[0] = True; r[1:] = self.seq[1:] != self.seq[:-1]; return r

    def blocks(self, rows):
        return [rows[self.seq[rows] == q] for q in np.unique(self.seq[rows])]


def _rot_deg(Ra, Rb):
    c = (np.einsum("...ij,...ij->...", Ra, Rb) - 1) / 2       # trace(Ra^T Rb)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def _pose_pos(qC, qR, C, Rr, dist, ang):
    D = np.linalg.norm(qC[:, None, :] - C[None, :, :], axis=-1)
    A = np.zeros_like(D)
    for i in range(len(qC)): A[i] = _rot_deg(qR[i][None], Rr)
    return (D <= dist) & (A <= ang), D, A


def _near_from_C(C, Rr, dist, ang):
    D = np.linalg.norm(C[:, None] - C[None], axis=-1)
    A = np.stack([_rot_deg(Rr[i][None], Rr) for i in range(len(C))])
    return (D <= dist) & (A <= ang)


def load_nordland(desc, ref="summer", queries=("spring", "fall", "winter"), tol=1, nblocks=10, calib_every=3):
    d = os.path.join(FB, DUMP_OF[("nord", desc)], "dump")
    meta = np.load(os.path.join(FB, "dive-vpr-nb15a-dump", "dump", "meta", "nord.npz"))
    R = np.load(os.path.join(d, desc, f"nord_{ref}.npy"))
    M = len(R); idx = np.arange(M)
    Qs, seq, cond, pos = [], [], [], []
    blen = int(np.ceil(M / nblocks)); calib = set()
    for qi, qs in enumerate(queries):
        Q = np.load(os.path.join(d, desc, f"nord_{qs}.npy")); Qs.append(Q)
        b = idx // blen; seq.append(qi * 100 + b); cond += [qs] * M
        pos.append(np.abs(idx[:, None] - idx[None, :]) <= tol)
        for bb in range(nblocks):
            if bb % calib_every == 0: calib.add(qi * 100 + bb)
    near = np.abs(idx[:, None] - idx[None, :]) <= tol
    return Episode(f"nord/{desc}", R, idx.astype(float), np.concatenate(Qs), np.concatenate(seq), np.array(cond),
                   np.concatenate(pos), near, calib, unit="frame", meta={"frame_ids": meta["frame_ids"]})


def load_nordseg(desc, ref="summer", queries=("spring", "fall", "winter"), tol=10, sublen=500, calib_every=3, stride=1):
    """Video-rate Nordland blocks (k01). Each block (2500 contiguous frames) is cut into sub-sequences."""
    d = os.path.join(FB, DUMP_OF[("nordseg", desc)], "dump")
    meta = np.load(os.path.join(d, "meta", "nord.npz"))
    blk = meta["block"]; ci = meta["common_index"]
    R = np.load(os.path.join(d, desc, f"nord_{ref}.npy"))
    keep = np.zeros(len(R), bool)
    for b in np.unique(blk):
        w = np.where(blk == b)[0]; keep[w[::stride]] = True
    R = R[keep]; ci = ci[keep]; blk = blk[keep]
    M = len(R); s = ci.astype(float) / stride   # position in SAMPLED-frame units (A23: was raw frames for stride>1)
    Qs, seq, cond, pos = [], [], [], []; calib = set(); sid = 0
    for qi, qs in enumerate(queries):
        Q = np.load(os.path.join(d, desc, f"nord_{qs}.npy"))[keep]; Qs.append(Q); cond += [qs] * M
        sq = np.empty(M, int)
        for b in np.unique(blk):
            w = np.where(blk == b)[0]
            n_sub = max(1, len(w) * stride // sublen)
            for k, part in enumerate(np.array_split(w, n_sub)):
                sq[part] = sid
                if sid % calib_every == 0: calib.add(sid)
                sid += 1
        seq.append(sq)
        pos.append((np.abs(s[:, None] - s[None, :]) * stride <= tol))      # tolerance stays in raw frames
    near = np.abs(s[:, None] - s[None, :]) * stride <= tol
    return Episode(f"nordseg/{desc}/x{stride}", R, s, np.concatenate(Qs), np.concatenate(seq), np.array(cond),
                   np.concatenate(pos), near, calib, unit="frame")


def load_robotcar(desc, dist=5.0, ang=30.0, gap_s=2.0, calib_every=3):
    d = os.path.join(FB, DUMP_OF[("rc", desc)], "dump")
    z = np.load(os.path.join(FB, "dive-vpr-nb15a-dump", "dump", "meta", "rc.npz"))
    rts = np.array([int(re.findall(r"(\d+)\.\w+$", n)[0]) for n in z["ref_names"]])
    ro = np.argsort(rts)
    R = np.load(os.path.join(d, desc, "rc_ref.npy"))[ro]; C = z["ref_C"][ro]; Rr = z["ref_R"][ro]
    from .hmm import arc_length
    steps = np.linalg.norm(np.diff(C, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(np.minimum(steps, 30.0))])     # cap gaps (map discontinuities)
    qts = np.array([int(re.findall(r"(\d+)\.\w+$", n)[0]) for n in z["q_names"]])
    qc = z["q_cond"]; o = np.lexsort((qts, qc))
    Q = np.load(os.path.join(d, desc, "rc_q.npy"))[o]; qC = z["q_C"][o]; qR = z["q_R"][o]; qc = qc[o]; qts = qts[o]
    seq = np.zeros(len(o), int); sid = 0
    for t in range(1, len(o)):
        if qc[t] != qc[t - 1] or (qts[t] - qts[t - 1]) / 1e6 > gap_s: sid += 1
        seq[t] = sid
    calib = {q for q in np.unique(seq) if q % calib_every == 0}
    pos, _, _ = _pose_pos(qC, qR, C, Rr, dist, ang)
    near = _near_from_C(C, Rr, dist, ang)
    return Episode(f"rc/{desc}", R, s, Q, seq, qc, pos, near, calib, unit="m", C=C, Rrot=Rr, qC=qC, qR=qR,
                   qt=qts / 1e6)


def load_cmu(desc, slices=CMU_SLICES, dist=5.0, ang=30.0, gap_s=2.0, calib_every=3):
    """All slices concatenated into one block-diagonal map? No: each slice is its own map. Returns a list."""
    eps = []
    for sl in slices:
        d = os.path.join(FB, DUMP_OF[("cmu", desc)], "dump")
        z = np.load(os.path.join(FB, "dive-vpr-nb15b-dump", "dump", "meta", f"cmu_s{sl}.npz"))
        R = np.load(os.path.join(d, desc, f"cmu_s{sl}_db.npy")); C = z["db_C"]; Rr = z["db_R"]
        steps = np.linalg.norm(np.diff(C, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(np.minimum(steps, 30.0))])
        qts = np.array([int(re.findall(r"_(\d+)us", n)[0]) for n in z["q_names"]]); qc = z["q_cond"]
        o = np.lexsort((qts, qc))
        Q = np.load(os.path.join(d, desc, f"cmu_s{sl}_q.npy"))[o]; qC = z["q_C"][o]; qR = z["q_R"][o]; qc = qc[o]; qts = qts[o]
        seq = np.zeros(len(o), int); sid = sl * 1000
        dates = sorted(np.unique(qc)); seq[0] = sid
        for t in range(1, len(o)):
            if qc[t] != qc[t - 1] or (qts[t] - qts[t - 1]) / 1e6 > gap_s: sid += 1
            seq[t] = sid
        calib = set()
        for q in np.unique(seq):
            di = dates.index(qc[seq == q][0])
            if (di + sl) % calib_every == 0: calib.add(q)
        pos, _, _ = _pose_pos(qC, qR, C, Rr, dist, ang)
        near = _near_from_C(C, Rr, dist, ang)
        eps.append(Episode(f"cmu/s{sl}/{desc}", R, s, Q, seq, qc, pos, near, calib, unit="m", C=C, Rrot=Rr,
                           qC=qC, qR=qR, qt=qts / 1e6))
    return eps


def timewarp(ep: Episode, speeds=(0.0, 0.5, 1.0, 2.0, 3.0), mean_dwell=40, seed=0, max_len=None):
    """Controlled variant (Master Plan T2.5/E08): re-time each query sequence with a piecewise-constant random
    speed (frames of the original synchronised stream per output frame); 0 = standstill (exact duplicates),
    0.5 = slow (repeated frames), >1 = fast (skipped frames). Map and GT definition unchanged."""
    rng = np.random.default_rng(seed)
    rows, seq_new, spd = [], [], []
    for q in np.unique(ep.seq):
        idx = np.where(ep.seq == q)[0]
        x, out, sp_ = 0.0, [], []
        v = rng.choice(speeds[1:])
        while True:
            if rng.random() < 1.0 / mean_dwell: v = rng.choice(speeds)
            if not out and v == 0: v = 1.0
            i = int(round(x))
            if i >= len(idx): break
            out.append(idx[i]); sp_.append(v); x += v
            if max_len and len(out) >= max_len: break
            if len(out) > 20 * len(idx): break
        rows += out; seq_new += [q] * len(out); spd += sp_
    rows = np.array(rows)
    e = Episode(ep.name + f"/tw{seed}", ep.R, ep.s, ep.Q[rows], np.array(seq_new), ep.cond[rows], ep.pos[rows],
                ep.near, ep.calib_seq, unit=ep.unit)
    e.meta["speed"] = np.array(spd); e.meta["src_rows"] = rows
    return e


def true_speed(ep: Episode):
    """Per-frame GT displacement into frame t (map units/frame); NaN at sequence starts. Calibration use only."""
    T = ep.T; sp = np.full(T, np.nan)
    if "speed" in ep.meta:                        # synthetic time-warp: speed applied after frame t-1
        sp[1:] = ep.meta["speed"][:-1]
    elif ep.qC is not None and getattr(ep, "graph", None) == "spatial":
        sp[1:] = np.linalg.norm(np.diff(ep.qC, axis=0), axis=1)      # spatial graph: metric displacement is the state unit
    elif ep.qC is not None:
        # A26: speed in MAP COORDINATES. Map arc-length grows faster than metric distance (noisy reference poses), so
        # metric query steps are rescaled by the LOCAL map ratio  (s[j+w]-s[j-w]) / ||C[j+w]-C[j-w]||  at the nearest
        # node. Robust to loops (a wrong nearest node only changes a ratio ~1-2, never the step itself).
        w = 5; M = len(ep.s); jj = np.arange(M); lo = np.clip(jj - w, 0, M - 1); hi = np.clip(jj + w, 0, M - 1)
        ratio = (ep.s[hi] - ep.s[lo]) / np.maximum(np.linalg.norm(ep.C[hi] - ep.C[lo], axis=1), 1e-6)
        ratio = np.clip(np.where(np.isfinite(ratio), ratio, 1.0), 1.0, 3.0)
        D = np.linalg.norm(ep.qC[:, None, :] - ep.C[None, :, :], axis=-1); nn = D.argmin(1)
        sp[1:] = np.linalg.norm(np.diff(ep.qC, axis=0), axis=1) * ratio[nn[1:]]
    else:
        sp[1:] = 1.0
    sp[ep.reset_mask()] = np.nan
    return sp


FOURS_SCENE = {"hmm-k02-4s-stopgo": "office_loop", "hmm-k03-4s-scene2": "countryside", "hmm-k04-4s-scene3": "old_town"}


def load_4s_stopgo(desc, dist=5.0, ang=30.0, calib_every=3, kdir="hmm-k02-4s-stopgo"):
    """4Seasons, one scene (kernel k02): map = first traversal sampled every >=1 m; queries = the other traversals
    sampled every 0.5 s in TIME (real stops kept). Each query traversal is one sequence (cut at gaps > 2 s)."""
    scene = FOURS_SCENE[kdir]
    if desc == "jist": kdir = "hmm-k08-jist4s"       # all three scenes extracted together with JIST
    if desc.startswith("seqvlad"): kdir = "hmm-k12-seqvlad"
    d = os.path.join(FB, kdir, "dump")
    metas = sorted(m for m in glob.glob(os.path.join(d, "meta", "*.npz")) if f"4s_{scene}_" in os.path.basename(m))
    mp = [m for m in metas if "_map_" in os.path.basename(m)][0]
    zm = np.load(mp); tag = os.path.basename(mp)[:-4]
    R = np.load(os.path.join(d, desc, tag + ".npy")); C = zm["C"]; Rr = zm["R"]
    steps = np.linalg.norm(np.diff(C, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(np.minimum(steps, 30.0))])
    Qs, seq, cond, qC, qR, qt = [], [], [], [], [], []; calib = set(); sid = 0
    for k, m in enumerate([m for m in metas if "_q_" in os.path.basename(m)]):
        z = np.load(m); t = os.path.basename(m)[:-4]
        Q = np.load(os.path.join(d, desc, t + ".npy")); ts = z["ns"] / 1e9
        sq = np.zeros(len(Q), int); cur = sid
        for i in range(1, len(Q)):
            if ts[i] - ts[i - 1] > 2.0: cur += 1
            sq[i] = cur
        sq[0] = sid
        for q in np.unique(sq):
            if k % calib_every == 0: calib.add(q)
        sid = sq.max() + 1
        Qs.append(Q); seq.append(sq); cond += [str(z["rec"])] * len(Q); qC.append(z["C"]); qR.append(z["R"]); qt.append(ts)
    Q = np.concatenate(Qs); qC = np.concatenate(qC); qR = np.concatenate(qR)
    pos, _, _ = _pose_pos(qC, qR, C, Rr, dist, ang)
    near = _near_from_C(C, Rr, dist, ang)
    return Episode(f"{kdir}/{desc}", R, s, Q, np.concatenate(seq), np.array(cond), pos, near, calib, unit="m", C=C, Rrot=Rr,
                   qC=qC, qR=qR, qt=np.concatenate(qt))


def subsample_queries(ep: Episode, k: int):
    """Keep every k-th query frame within each sequence (raises per-frame displacement / map spacing ratio)."""
    keep = np.zeros(ep.T, bool)
    for q in np.unique(ep.seq):
        i = np.where(ep.seq == q)[0]; keep[i[::k]] = True
    r = np.where(keep)[0]
    e = Episode(ep.name + f"/q{k}", ep.R, ep.s, ep.Q[r], ep.seq[r], ep.cond[r], ep.pos[r], ep.near, ep.calib_seq, unit=ep.unit,
                C=ep.C, Rrot=ep.Rrot, qC=None if ep.qC is None else ep.qC[r], qR=None if ep.qR is None else ep.qR[r],
                qt=None if ep.qt is None else ep.qt[r])
    return e


def load_msls(desc, city="cph", dist=25.0, calib_every=3, gap_m=40.0):
    """MSLS (Copenhagen / San Francisco test cities; dumps nb16a/b). Sequences = consecutive rows with the same date and
    step < gap_m (rows are stored in Mapillary-sequence order). Map is a SPATIAL graph (Episode.graph='spatial')."""
    kd = {"cph": "dive-vpr-nb16a-msls", "sf": "dive-vpr-nb16b-msls"}[city]
    if desc.startswith("seqvlad"): kd = "hmm-k12-seqvlad"
    d = os.path.join(FB, kd, "dump"); z = np.load(os.path.join(d, "meta", f"msls_{city}.npz"))
    R = np.load(os.path.join(d, desc, f"msls_{city}_db.npy")); Q = np.load(os.path.join(d, desc, f"msls_{city}_q.npy"))
    C = np.c_[z["db_C"], np.zeros(len(z["db_C"]))]; qC = np.c_[z["q_C"], np.zeros(len(z["q_C"]))]
    seq = np.zeros(len(Q), int)
    for t in range(1, len(Q)):
        brk = z["q_date"][t] != z["q_date"][t - 1] or np.linalg.norm(qC[t] - qC[t - 1]) > gap_m
        seq[t] = seq[t - 1] + int(brk)
    calib = {q for q in np.unique(seq) if q % calib_every == 0}
    from scipy.spatial import cKDTree
    pos = np.zeros((len(Q), len(R)), bool)
    for i, js in enumerate(cKDTree(C).query_ball_point(qC, r=dist)): pos[i, js] = True
    near = np.zeros((len(R), len(R)), bool)
    for i, js in enumerate(cKDTree(C).query_ball_point(C, r=dist)): near[i, js] = True
    ep = Episode(f"msls/{city}/{desc}", R, None, Q, seq, z["q_cond"], pos, near, calib, unit="m", C=C, qC=qC)
    ep.graph = "spatial"; ep.heading = z["db_ca"]; return ep


# ---------------------------------------------------------------- multi-traversal datasets (research/DATASETS.md, B/C)
TRAV = {  # name -> dump dir (Kaggle dataset slug, mounted/copied into FB), file prefix, default map traversal, dist m, angle deg
    "stlucia": ("stlucia-vpr-dump", "stlucia", "190809_0845", 25.0, None),
    "boreas": ("boreas-vpr-dump", "boreas", "boreas-2020-11-26-13-58", 10.0, 30.0),
    "nclt": ("nclt-vpr-dump", "nclt", "2012-01-08", 10.0, 30.0),
    "brisbane": ("hmm-k13-newds", "bris", "daytime", 25.0, None),        # 6 times of day, GPS, 1 fps (kernel k13)
    "oxford": ("oxford-robotcar-vpr-dump", "oxford", "2014-12-09-13-21-02", 25.0, 30.0),   # INS/GPS UTM, 43 traversals
}
TRAV_QUERIES = {  # standard condition set for Oxford RobotCar (overcast reference 2014-12-09)
    "oxford": ["2015-05-19-14-06-38", "2015-08-13-16-02-58", "2014-11-14-16-34-33", "2014-12-10-18-10-50",
               "2014-12-16-18-44-24", "2015-02-03-08-45-10", "2015-10-30-13-52-14"],   # sun, summer, dusk, night, night-rain, snow, rain
}
HEADING = {"stlucia": None, "boreas": "traj", "nclt": "rpy", "oxford": "traj", "brisbane": None}   # Boreas rpy = camera attitude -> use driving direction


def _heading(meta, ds=None, C=None):
    mode = HEADING.get(ds, "rpy")
    if mode == "traj" and C is not None:                 # direction of travel, smoothed over +-3 frames
        n = len(C); i = np.arange(n); a = C[np.clip(i + 3, 0, n - 1)] - C[np.clip(i - 3, 0, n - 1)]
        h = np.arctan2(a[:, 1], a[:, 0]); ok = np.linalg.norm(a[:, :2], axis=1) >= 1.0    # stopped: arctan2 is noise
        if ok.any():
            idx = np.where(ok, i, 0); np.maximum.accumulate(idx, out=idx)           # last valid index (forward fill)
            first = np.argmax(ok); idx[:first] = first                               # leading stop: next valid
            h = h[idx]
        return h
    if mode == "rpy" and "rpy" in meta.files: return np.asarray(meta["rpy"], float)[:, 2]
    return None


def load_traversals(ds, desc, map_trav=None, queries=None, dist=None, ang=None, calib_every=3, jump_m=50.0, max_q=None):
    """Repeated traversals of one route (St Lucia, Boreas, NCLT, ...): map = one traversal (metric chain, arc length s),
    queries = the other traversals in time order; one sequence per traversal, cut only at GPS jumps > jump_m.
    Calibration/test split by WHOLE traversals (traversal k is calibration iff k % calib_every == 0).
    Positives: centre distance <= dist (and heading difference <= ang when headings exist)."""
    kdir, pre, dmap, ddist, dang = TRAV[ds]
    dist = ddist if dist is None else dist; ang = dang if ang is None else ang
    root = os.path.join(FB, kdir); d = os.path.join(root, "dump") if os.path.isdir(os.path.join(root, "dump")) else root
    travs = sorted(os.path.basename(m)[len(pre) + 1:-4] for m in glob.glob(os.path.join(d, "meta", f"{pre}_*.npz")))
    mp = map_trav or dmap; qs = [t for t in (queries or TRAV_QUERIES.get(ds) or travs) if t != mp and t in travs][:max_q]
    def one(t):
        z = np.load(os.path.join(d, "meta", f"{pre}_{t}.npz"), allow_pickle=True)
        X = np.load(os.path.join(d, desc, f"{pre}_{t}.npy")); C = np.asarray(z["C"], float)
        if C.shape[1] == 2: C = np.c_[C, np.zeros(len(C))]
        assert len(X) == len(C), (t, X.shape, C.shape)
        ts = np.asarray(z["t"], float) if "t" in z.files else np.array([float(n) for n in z["names"]]) / 1e6
        return X, C, _heading(z, ds, C), ts
    R, C, hm, _ = one(mp)
    steps = np.linalg.norm(np.diff(C, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(np.minimum(steps, 30.0))])
    Qs, seq, cond, qC, qh, qt = [], [], [], [], [], []; calib = set(); sid = 0
    for k, t in enumerate(qs):
        Q, c, h, ts = one(t); sq = np.full(len(Q), sid)
        jumps = np.where(np.linalg.norm(np.diff(c, axis=0), axis=1) > jump_m)[0]
        for j in jumps: sq[j + 1:] += 1
        for q in np.unique(sq):
            if k % calib_every == 0: calib.add(int(q))
        sid = sq.max() + 1
        Qs.append(Q); seq.append(sq); cond += [t] * len(Q); qC.append(c); qh.append(h); qt.append(ts)
    Q = np.concatenate(Qs); qC = np.concatenate(qC); seq = np.concatenate(seq)
    from scipy.spatial import cKDTree
    tree = cKDTree(C); pos = np.zeros((len(Q), len(R)), bool); near = np.zeros((len(R), len(R)), bool)
    use_h = ang is not None and hm is not None and all(h is not None for h in qh)
    qhh = np.concatenate(qh) if use_h else None
    def hdiff(a, b): return np.degrees(np.abs((a - b + np.pi) % (2 * np.pi) - np.pi))
    for i, js in enumerate(tree.query_ball_point(qC, r=dist)):
        js = np.asarray(js, int)
        if use_h and len(js): js = js[hdiff(qhh[i], hm[js]) <= ang]
        pos[i, js] = True
    for i, js in enumerate(tree.query_ball_point(C, r=dist)):
        js = np.asarray(js, int)
        if use_h and len(js): js = js[hdiff(hm[i], hm[js]) <= ang]
        near[i, js] = True
    return Episode(f"{ds}/{desc}/map{mp}", R, s, Q, seq, np.array(cond), pos, near, calib, unit="m", C=C, qC=qC,
                   qt=np.concatenate(qt), meta={"map": mp, "queries": qs})


def load_qut(desc, which="gp", tol=2, nblocks=4, calib_every=3):
    """QUT day/night + lateral shift (kernel k13): frame i of every traversal shows place i (frame-index chain, like
    Nordland). Gardens Point: map = day_right, queries = day_left (lateral shift) + night_right (illumination);
    SouthBank: map = frames1, query = frames2. Each query traversal is cut into `nblocks` blocks; calibration = every
    `calib_every`-th block."""
    root = os.path.join(FB, "hmm-k13-newds"); d = os.path.join(root, "dump") if os.path.isdir(os.path.join(root, "dump")) else root
    ref, qs = (("qutgp_day_right", ["qutgp_day_left", "qutgp_night_right"]) if which == "gp" else ("qutsb_frames1", ["qutsb_frames2"]))
    R = np.load(os.path.join(d, desc, ref + ".npy")); M = len(R); idx = np.arange(M)
    Qs, seq, cond, pos = [], [], [], []; calib = set(); blen = int(np.ceil(M / nblocks))
    for qi, q in enumerate(qs):
        Q = np.load(os.path.join(d, desc, q + ".npy")); n = min(len(Q), M); Q = Q[:n]; Qs.append(Q)
        b = np.arange(n) // blen; seq.append(qi * 100 + b); cond += [q] * n
        pos.append(np.abs(np.arange(n)[:, None] - idx[None, :]) <= tol)
        for bb in range(nblocks):
            if bb % calib_every == 0: calib.add(qi * 100 + bb)
    near = np.abs(idx[:, None] - idx[None, :]) <= tol
    return Episode(f"qut-{which}/{desc}", R, idx.astype(float), np.concatenate(Qs), np.concatenate(seq), np.array(cond),
                   np.concatenate(pos), near, calib, unit="frame")


def load_kitti(desc, seqs=("00", "02", "05", "06", "08"), dist=10.0, block=100, calib_every=3):
    """KITTI Odometry loop sequences (kernel k14, 5 Hz): REVISIT protocol per sequence — map = first half of the
    sequence (metric chain), queries = second half; positives = map frames within `dist` m (no heading test: sequence 08
    revisits in the opposite direction). Query frames on new road are off-map (no positive). Queries cut into blocks of
    `block` frames; calibration = every `calib_every`-th block. Returns one Episode per sequence."""
    root = os.path.join(FB, "hmm-k14-kitti"); d = os.path.join(root, "dump") if os.path.isdir(os.path.join(root, "dump")) else root
    from scipy.spatial import cKDTree
    eps = []
    for sq in seqs:
        z = np.load(os.path.join(d, "meta", f"kitti_{sq}.npz")); X = np.load(os.path.join(d, desc, f"kitti_{sq}.npy"))
        C = np.asarray(z["C"], float); n = len(C); h = n // 2
        R, Cm, Q, qC = X[:h], C[:h], X[h:], C[h:]
        steps = np.linalg.norm(np.diff(Cm, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(steps)])
        seq = int(sq) * 1000 + np.arange(len(Q)) // block
        calib = {q for q in np.unique(seq) if (q % 1000) % calib_every == 0}
        tree = cKDTree(Cm); pos = np.zeros((len(Q), h), bool); near = np.zeros((h, h), bool)
        for i, js in enumerate(tree.query_ball_point(qC, r=dist)): pos[i, js] = True
        for i, js in enumerate(tree.query_ball_point(Cm, r=dist)): near[i, js] = True
        eps.append(Episode(f"kitti/{sq}/{desc}", R, s, Q, seq, np.array([sq] * len(Q)), pos, near, calib, unit="m",
                           C=Cm, qC=qC, qt=np.asarray(z["t"], float)[h:]))
    return eps
