"""Certified sequential localization: excursion-level false-localization control from the map itself.

Evidence. Per frame t: SelfCal-AA p-value p_t of its top-1 match (cross-fitted: the per-frame test is fitted on map
items of even blocks). Running statistic R_t = sum of -log p over the trailing run of frames whose top-1 map positions
move with the odometry (anchored at t: ||x_t - x_{t-j} - (o_t - o_{t-j})|| <= rho_o, j < Lmax): a max-product (Viterbi)
path evidence of an HMM whose transitions are gated by the odometry.  Variants: FRAME (R_t = -log p_t, i.e. the per-frame
test), RUN (exp11: consecutive top-1 positions within rho, no odometry), RUNO (ours).

Calibration (the guarantee). Null unit = an H-frame segment of the map's own traversal inside one held-out ODD block,
queried against the map without that block (so it is off-map by construction); its score = max_t R_t over the segment.
A deployment frame is accepted iff R_t > the conformal (1-alpha) quantile of the null segment scores. If an H-frame
off-map excursion is exchangeable with the null segments, P(any false acceptance during the excursion) <= alpha, for
ANY temporal dependence inside the segment (the segment is the exchangeable unit).

Evaluation. Off-map excursions = H-frame segments of query frames whose map block is held out (LOBO), two versions:
  iso   : the run may only use frames inside the excursion;
  lead  : the run may also reach back into the preceding on-map frames (matched against the full map), as on a robot
          that drives out of the mapped area.
Power = fraction of correctly matched on-map frames (full map) accepted; alias = accepted frames whose top-1 is wrong
by > excl; latency = frames from the start of each query sequence to its first correct acceptance.
Seeds randomise the block grid (V.GRID_OFFSET) and the odometry noise.
Usage: cert_seq.py <dump> <rc|cmu|nord|4s:<scene>> <desc> [seeds=3] -> results/cert_<ds>_<desc>.json"""
import sys, os, json, time
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V, selfcal as SC
from sc_eval import CFG

A = 0.05
ALPHAS = (0.01, 0.05, 0.1)
KINDS = ("FRAME", "RUN", "RUNO", "ANCH")
COUPLE = "--lmax30" not in sys.argv          # default: evidence horizon Lmax = guarantee horizon H
sys.argv = [a for a in sys.argv if a != "--lmax30"]


def odometry_sim(pos, sid, k, rng, R=None, scale_sd=0.03, step_sd=0.05):
    """integrated simulated odometry o_t in the WORLD frame of the first frame of each sequence: body-frame increments
    (with scale error and noise) are re-rotated by the GT orientation, i.e. the heading is assumed known (compass/VIO
    attitude); returned as cumulative positions per sequence"""
    o = np.zeros_like(pos)
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(k[idx])]; dx = np.diff(pos[idx], axis=0)
        noisy = (1 + rng.normal(0, scale_sd)) * dx + rng.normal(0, 1, dx.shape) * step_sd * np.linalg.norm(dx, axis=1, keepdims=True)
        o[idx] = np.vstack([np.zeros((1, pos.shape[1])), np.cumsum(noisy, axis=0)])
    return o


def odometry_vio(ep, sid, k):
    """real VIO: integrated VIO translation rotated into the ENU frame by a per-sequence rigid alignment of its first
    frame (the VIO frame is gravity-aligned; the yaw offset is fitted on the first 20 frames only)"""
    o = np.zeros_like(ep.q_pos)
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(k[idx])]; v = ep.q_vio[idx] - ep.q_vio[idx[0]]
        g = ep.q_pos[idx] - ep.q_pos[idx[0]]; n = min(20, len(idx))
        U, _, Vt = np.linalg.svd(g[:n].T @ v[:n]); X = U @ np.diag([1, 1, np.linalg.det(U @ Vt)]) @ Vt
        o[idx] = v @ X.T
    return o


def odometry_wheel(ep, sid, k, n_cal=50):
    """real wheel + gyro dead reckoning (Boreas): distance = pulse increments x scale, heading = h0 + sign x integrated
    gyro yaw. scale, sign and the initial heading h0 are calibrated per sequence on its first n_cal frames only."""
    o = np.zeros_like(ep.q_pos)
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(k[idx])]; n = min(n_cal, len(idx) - 1)
        dp = np.diff(ep.q_dmi[idx]); g = ep.q_pos[idx]; dg = np.diff(g, axis=0)
        scale = np.linalg.norm(dg[:n], axis=1).sum() / max(dp[:n].sum(), 1e-9)
        best = None
        for sign in (1.0, -1.0):
            yaw = sign * (ep.q_gyro[idx] - ep.q_gyro[idx[0]])
            h0 = np.arctan2(dg[:n, 1], dg[:n, 0]) - yaw[1:n + 1]; h0 = np.arctan2(np.sin(h0).mean(), np.cos(h0).mean())
            steps = (scale * dp)[:, None] * np.stack([np.cos(h0 + yaw[1:]), np.sin(h0 + yaw[1:])], 1)
            oo = np.vstack([[0, 0], np.cumsum(steps, 0)]); err = np.linalg.norm(oo[:n + 1] - (g[:n + 1] - g[0]), axis=1).mean()
            if best is None or err < best[0]: best = (err, oo)
        o[idx] = best[1]
    return o


def odometry_real(ep, sid, k):
    if hasattr(ep, "q_vio"): return odometry_vio(ep, sid, k)
    if hasattr(ep, "q_dmi"): return odometry_wheel(ep, sid, k)
    return None


def running(p, top, order, o, m_pos, kind, rho, rho_o, Lmax, alt=None):
    """running statistic at every frame listed in `order` (one sequence, time order). alt=(p2, top2, mask): frames with
    mask False use (p2, top2) instead (lead-in frames matched against the full map)."""
    n = len(order); out = np.empty(n)
    P = p[order].copy(); T = top[order].copy()
    if alt is not None:
        p2, t2, msk = alt; use = ~msk[order]; P[use] = p2[order][use]; T[use] = t2[order][use]
    lp = -np.log(np.clip(P, 1e-12, 1)); X = m_pos[np.nan_to_num(T).astype(int)]; O = o[order]
    if kind == "ANCH":            # all frames of the last Lmax whose match agrees with the last frame's hypothesis + odometry
        for t in range(n):
            j0 = max(0, t - Lmax + 1)
            ok = np.linalg.norm((X[t] - X[j0:t + 1]) - (O[t] - O[j0:t + 1]), axis=1) <= rho_o
            out[t] = lp[j0:t + 1][ok].sum()
        return out
    for t in range(n):
        s = lp[t]
        if kind != "FRAME":
            for j in range(1, min(Lmax, t + 1)):
                if kind == "RUN": ok = np.linalg.norm(X[t - j + 1] - X[t - j]) <= rho
                else: ok = np.linalg.norm((X[t] - X[t - j]) - (O[t] - O[t - j])) <= rho_o
                if not ok: break
                s += lp[t - j]
        out[t] = s
    return out


def chunks(order, ok, block):
    """maximal runs of consecutive valid frames inside one block (index lists into the global arrays)"""
    out, cur = [], []
    for i in order:
        if ok[i] and (not cur or block[i] == block[cur[-1]]): cur.append(i)
        else:
            if cur: out.append(cur)
            cur = [i] if ok[i] else []
    if cur: out.append(cur)
    return out


def main():
    dump, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3]; seeds = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    if ds.startswith("4s:"): ep = V.load_4seasons(dump, desc, ds[3:]); c = CFG["cmu"]
    elif ds == "boreas": ep = V.load_boreas(dump, desc); c = CFG["cmu"]
    else: ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
    q_sid, q_k, m_sid, m_k = V.frame_order(dump, ds, ep, desc)
    nord = ds in ("nord", "nordw"); rho = c["excl"]; rho_o = 1.0 if nord else 5.0; LMAX0 = 30
    HS = (5, 8) if ds == "rc" else (10, 30, 60)
    cond = np.asarray(ep.q_cond).astype(str); conds = sorted(set(cond))
    q_seqs = [np.where(q_sid == s)[0][np.argsort(q_k[q_sid == s])] for s in np.unique(q_sid)]
    m_seqs = [np.where(m_sid == s)[0][np.argsort(m_k[m_sid == s])] for s in np.unique(m_sid)]
    mr = ep.m.astype(np.float32); mu = mr.mean(0, keepdims=True); nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
    mc = nrm(mr - mu); q = ep.q.astype(np.float32); qc = nrm(q - mu)
    Fr, Fc = SC.qm_stats(q, mr, ep.m_pos, c["cell"], c["excl"], c["k"]), SC.qm_stats(qc, mc, ep.m_pos, c["cell"], c["excl"], c["k"])
    inm = V.nearest_map_dist(ep) <= c["in_d"]; corr = V.correct(ep, *c["tol"]) & inm; _, dt, _ = V.top1_errors(ep)
    alias = inm & (dt > c["excl"])
    out = {"ds": ds, "desc": desc, "alpha": A, "rho_o": rho_o, "Lmax": "H" if COUPLE else LMAX0, "runs": []}
    for seed in range(seeds):
        t0 = time.time(); rng = np.random.default_rng(seed)
        V.GRID_OFFSET = None if seed == 0 else rng.uniform(0, 1, 2)
        args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
        Nr, Nc = SC.map_null(mr, ep.m_pos, *args, stride=1), SC.map_null(mc, ep.m_pos, *args, stride=1)
        Or_ = SC.lobo_stats(mr, ep.m_pos, c["block"], c["off_d"], q, ep.q_pos, c["cell"], c["excl"], c["k"])
        Oc = SC.lobo_stats(mc, ep.m_pos, c["block"], c["off_d"], qc, ep.q_pos, c["cell"], c["excl"], c["k"])
        bid, _ = V.map_cells(ep.m_pos, c["block"]); half = bid % 2 == 0
        sub = lambda d, m: {kk: np.where(m, v, np.nan) for kk, v in d.items()}
        test = SC.SelfCalTest(SC.pack(sub(Nr, half), sub(Nc, half)))
        p_null, p_off, p_full = (test.pvalue(**SC.pack(r, cc)) for r, cc in ((Nr, Nc), (Or_, Oc), (Fr, Fc)))
        _, nn = cKDTree(ep.m_pos).query(ep.q_pos); qb = bid[nn]
        null_ok = np.isfinite(Nr["maxsim"]) & np.isfinite(Nc["z_far"]) & ~half
        off_ok = np.isfinite(Or_["maxsim"]) & np.isfinite(Oc["z_far"])
        if hasattr(ep, "q_vio") or hasattr(ep, "q_dmi"):
            o_q = odometry_real(ep, q_sid, q_k)
            o_m = odometry_sim(ep.m_pos, m_sid, m_k, rng)          # map pseudo-trajectories: simulated odometry
        else:
            o_q = odometry_sim(ep.q_pos, q_sid, q_k, rng); o_m = odometry_sim(ep.m_pos, m_sid, m_k, rng)
        run = {"seed": seed, "n_null_items": int(null_ok.sum()), "n_off": int(off_ok.sum()), "rows": []}
        for kind, H in [(k, h) for k in KINDS for h in HS]:
            Lmax = H if COUPLE else LMAX0
            Rn = np.full(len(ep.m), np.nan); Ri = np.full(len(q), np.nan); Rl = np.full(len(q), np.nan); Rf = np.full(len(q), np.nan)
            for order in m_seqs:
                for ch in chunks(order, null_ok, bid): Rn[ch] = running(p_null, Nr["top"], np.array(ch), o_m, ep.m_pos, kind, rho, rho_o, Lmax)
            for order in q_seqs:
                for ch in chunks(order, off_ok, qb): Ri[ch] = running(p_off, Or_["top"], np.array(ch), o_q, ep.m_pos, kind, rho, rho_o, Lmax)
                Rf[order] = running(p_full, Fr["top"], order, o_q, ep.m_pos, kind, rho, rho_o, Lmax)
                # lead-in: frames of each held-out block use the LOBO match, all other frames the full-map match
                for b in np.unique(qb[order][off_ok[order]]):
                    msk = off_ok & (qb == b); ii = np.flatnonzero(msk[order])
                    if not len(ii): continue
                    lo = max(0, ii.min() - Lmax); sl = order[lo:ii.max() + 1]
                    r = running(p_off, Or_["top"], sl, o_q, ep.m_pos, kind, rho, rho_o, Lmax, alt=(p_full, Fr["top"], msk))
                    Rl[sl[msk[sl]]] = r[msk[sl]]
            for al in ALPHAS:
                nseg = [s for order in m_seqs for ch in chunks(order, null_ok, bid) for s in (ch[i:i + H] for i in range(0, len(ch) - H + 1, H))]
                oseg = [s for order in q_seqs for ch in chunks(order, off_ok, qb) for s in (ch[i:i + H] for i in range(0, len(ch) - H + 1, H))]
                if len(nseg) < 1 / al or not oseg: continue
                ns = np.sort([Rn[s].max() for s in nseg]); kq = int(np.ceil((1 - al) * (len(ns) + 1)))
                thr = ns[kq - 1] if kq <= len(ns) else np.inf
                fi = np.array([Ri[s].max() > thr for s in oseg]); fl = np.array([Rl[s].max() > thr for s in oseg])
                oc = np.array([cond[s[0]] for s in oseg])
                acc = Rf > thr
                # label-calibrated baseline: threshold = conformal quantile of LABELLED off-map segments of the calibration
                # conditions (deployment-like data with labels, SAFEVPR / Quantile-Transfer style); tested on the others
                cal = c.get("calib") or sorted(conds, key=lambda x: -corr[cond == x].mean())[:2]
                lc = np.sort([Ri[s].max() for s, x in zip(oseg, oc) if x in cal]); kl = int(np.ceil((1 - al) * (len(lc) + 1)))
                thr_l = lc[kl - 1] if 0 < kl <= len(lc) else np.inf
                fl_l = np.array([Ri[s].max() > thr_l for s in oseg]); acc_l = Rf > thr_l
                lat = []
                for order in q_seqs:
                    hit = np.flatnonzero(acc[order] & corr[order])
                    lat.append(hit[0] if len(hit) else len(order))
                row = dict(alpha=al, kind=kind, H=H, Lmax=Lmax, n_null_seg=len(ns), n_off_seg=len(oseg), thr=float(thr),
                           FAR_iso=float(fi.mean()), FAR_lead=float(fl.mean()),
                           cond_iso={x: float(fi[oc == x].mean()) for x in conds if (oc == x).sum() >= 10},
                           cond_lead={x: float(fl[oc == x].mean()) for x in conds if (oc == x).sum() >= 10},
                           TPR=float(acc[corr].mean()), alias=float(acc[alias].mean()) if alias.any() else None,
                           cond_TPR={x: float(acc[corr & (cond == x)].mean()) for x in conds if (corr & (cond == x)).any()},
                           latency_med=float(np.median(lat)), latency_mean=float(np.mean(lat)),
                           label=dict(calib=list(cal), thr=float(thr_l), FAR=float(fl_l[~np.isin(oc, cal)].mean()),
                                      cond={x: float(fl_l[oc == x].mean()) for x in conds if x not in cal and (oc == x).sum() >= 10},
                                      TPR=float(acc_l[corr].mean())))
                run["rows"].append(row)
                if al != 0.05: continue
                print(f"{ds}/{desc} s{seed} {kind:5s} H={H:2d} nullseg {len(ns):4d} offseg {len(oseg):5d} | FAR iso {row['FAR_iso']:.3f} "
                      f"(worst {max(row['cond_iso'].values() or [0]):.3f}) lead {row['FAR_lead']:.3f} (worst {max(row['cond_lead'].values() or [0]):.3f}) "
                      f"| TPR {row['TPR']:.3f} alias {row['alias']} latency {row['latency_med']:.0f}", flush=True)
        out["runs"].append(run); print(f"seed {seed} done in {time.time() - t0:.0f}s", flush=True)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/cert_{ds.replace(':', '_')}_{desc}.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
