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
