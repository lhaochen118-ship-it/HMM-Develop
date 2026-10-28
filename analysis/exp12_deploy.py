"""E12 — downstream demo: localisation with drifting odometry + VPR fixes on a map with holes.
A random 30 % of the 300 m map blocks is removed (the robot drives through unmapped areas); SelfCal is fitted on the
remaining map only. Every query sequence (one traversal, ~1 m steps) is tracked by a position Kalman filter driven by
simulated odometry (scale bias, heading random walk, white noise); each ACCEPTED VPR match adds a position fix at the
matched map image (sigma 5 m). Acceptance rules: accept-all, benign label-calibrated max-sim threshold, SelfCal-AA per
frame, sequence SelfCal (window L, cross-fitted map pseudo-sequences), and an oracle that accepts only correct matches.
Reported per rule: wrong fixes accepted (off-map or top-1 > rho from truth), correct fixes, mean / median / 95 %
position error and the share of frames with error > rho (25 m; 5 frames on Nordland).
Usage: exp12_deploy.py <dump> <cmu|nord> [desc] [drop=0.3] [L=5] [seed=0] -> results/deploy_<ds>_<desc>_s<seed>.json"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC
from sc_eval import CFG

dump, ds = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
DROP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3; L = int(sys.argv[5]) if len(sys.argv) > 5 else 5
A, SIG_FIX = 0.05, 5.0; SEED = int(sys.argv[6]) if len(sys.argv) > 6 else 0
ep = V.LOADERS[ds](dump, desc); c = CFG[ds]; rng = np.random.default_rng(SEED)
q_sid, q_k, m_sid, m_k = V.frame_order(dump, ds, ep, desc)

# ---- map with holes
bid, _ = V.map_cells(ep.m_pos, c["block"]); ub = np.unique(bid)
dropped = rng.choice(ub, int(round(DROP * len(ub))), replace=False); keep = ~np.isin(bid, dropped)
M, MP = ep.m[keep].astype(np.float32), ep.m_pos[keep]
d_map = np.array([np.sqrt(((MP - x) ** 2).sum(1)).min() for x in ep.q_pos])
inm, offm = d_map <= c["in_d"], d_map > c["off_d"]

# ---- per-frame statistics against the reduced map, SelfCal fitted on the reduced map only
nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
mu = M.mean(0, keepdims=True); Mc = nrm(M - mu); q = ep.q.astype(np.float32); qc = nrm(q - mu)
args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
Nr, Nc = SC.map_null(M, MP, *args, stride=1), SC.map_null(Mc, MP, *args, stride=1)
Fr, Fc = SC.qm_stats(q, M, MP, c["cell"], c["excl"], c["k"]), SC.qm_stats(qc, Mc, MP, c["cell"], c["excl"], c["k"])
top = Fr["top"].astype(int); x_fix = MP[top]
err_top = np.sqrt(((x_fix - ep.q_pos) ** 2).sum(1)); good_fix = inm & (err_top <= c["excl"]); bad_fix = offm | (err_top > c["excl"])
bidM, _ = V.map_cells(MP, c["block"]); half = bidM % 2 == 0          # cross-fit: even blocks -> per-frame test
sub = lambda d, m: {k: np.where(m, v, np.nan) for k, v in d.items()}
test_full = SC.SelfCalTest(SC.pack(Nr, Nc))
p_frame = test_full.pvalue(**SC.pack(Fr, Fc))
test_half = SC.SelfCalTest(SC.pack(sub(Nr, half), sub(Nc, half)))
p_q, p_n = test_half.pvalue(**SC.pack(Fr, Fc)), test_half.pvalue(**SC.pack(Nr, Nc))


def windows(sid, k, valid, Lw):
    key = {(s, j): i for i, (s, j) in enumerate(zip(sid, k))}; ends, W = [], []
    for i in range(len(sid)):
        w = [key.get((sid[i], k[i] - Lw + 1 + j)) for j in range(Lw)]
        if None in w or not valid[w].all(): continue
        ends.append(i); W.append(w)
    return np.array(ends, int), np.array(W, int).reshape(-1, Lw)


null_ok = np.isfinite(Nr["maxsim"]) & np.isfinite(Nc["z_far"]) & ~half
mk_sid, mk_k = m_sid[keep], m_k[keep]
_, NW = windows(mk_sid, mk_k, null_ok, L); NW = NW[(bidM[NW] == bidM[NW[:, :1]]).all(1)]
s_null = SC.run_evidence(p_n, MP[np.nan_to_num(Nr["top"]).astype(int)], NW, c["excl"])   # top-1 positions of the map pseudo-queries
qe, QW = windows(q_sid, q_k, np.ones(len(q), bool), L)
p_seq = np.ones(len(q)); p_seq[qe] = SC.conformal_p(s_null, SC.run_evidence(p_q, x_fix, QW, c["excl"]))

# ---- label-calibrated baseline: split-conformal max-sim threshold on off-map queries of the two most benign conditions
conds = sorted(set(ep.q_cond)); r1 = {cc: good_fix[(ep.q_cond == cc) & inm].mean() for cc in conds}
benign = sorted(conds, key=lambda cc: -r1[cc])[:2]; cal = np.sort(Fr["maxsim"][offm & np.isin(ep.q_cond, benign)])
thr = cal[min(len(cal) - 1, int(np.ceil((len(cal) + 1) * (1 - A))) - 1)]
RULES = {"accept all": np.ones(len(q), bool), "benign threshold (labels)": Fr["maxsim"] > thr,
         "SelfCal-AA (frame)": p_frame <= A, f"SelfCal-Seq (L={L})": p_seq <= A, "oracle (correct only)": good_fix}

# ---- localisation: per-sequence position Kalman filter with drifting odometry
P_dims = ep.q_pos.shape[1]
hz = [0, 1] if P_dims >= 2 else [0]
if P_dims == 3: hz = list(np.argsort(ep.q_pos.var(0))[1:])          # two horizontal axes (largest variance)


def track(acc, seed=1):
    r = np.random.default_rng(seed); est = np.full_like(ep.q_pos, np.nan)
    for s in np.unique(q_sid):
        idx = np.where(q_sid == s)[0]; idx = idx[np.argsort(q_k[idx])]
        scale, th = 1 + r.normal(0, 0.03), 0.0
        x = ep.q_pos[idx[0]].copy(); P = 1.0
        est[idx[0]] = x
        for a, b in zip(idx[:-1], idx[1:]):
            d = ep.q_pos[b] - ep.q_pos[a]; th += r.normal(0, np.deg2rad(0.3)); step = np.linalg.norm(d)
            u = d * scale
            if len(hz) == 2:
                R2 = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]); u[hz] = R2 @ u[hz]
            u = u + r.normal(0, 0.02 * step / np.sqrt(len(d)) + 1e-3, len(d))
            x = x + u; P = P + (0.05 * step) ** 2 + 1e-4
            if acc[b]:
                K = P / (P + SIG_FIX ** 2); x = x + K * (x_fix[b] - x); P = (1 - K) * P
            est[b] = x
    return np.sqrt(((est - ep.q_pos) ** 2).sum(1))


res = {"meta": dict(drop=DROP, L=L, n_map=int(keep.sum()), n_q=len(q), n_seq=int(q_sid.max() + 1), off_frac=float(offm.mean()),
                    in_frac=float(inm.mean()), benign=list(map(str, benign)), n_null_windows=len(NW))}
print(f"{ds}/{desc}: map {keep.sum()}/{len(keep)} kept, {res['meta']['n_seq']} sequences, off-map {offm.mean():.2f} in-map {inm.mean():.2f}")
for name, acc in RULES.items():
    e = track(acc, SEED + 1)
    r = dict(wrong_fixes=int((acc & bad_fix).sum()), correct_fixes=int((acc & good_fix).sum()), wrong_fix_rate=float((acc & bad_fix).sum() / max(acc.sum(), 1)),
             FAR_offmap=float(acc[offm].mean()), err_mean=float(np.nanmean(e)), err_median=float(np.nanmedian(e)),
             err_p95=float(np.nanpercentile(e, 95)), frac_err_gt_rho=float(np.nanmean(e > c["excl"])))
    res[name] = r
    print(f"  {name:28s} wrong fixes {r['wrong_fixes']:6d} correct {r['correct_fixes']:6d} | off-map FAR {r['FAR_offmap']:.3f} | "
          f"err mean {r['err_mean']:7.1f} median {r['err_median']:6.1f} p95 {r['err_p95']:7.1f} | >rho {r['frac_err_gt_rho']:.3f}", flush=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
json.dump(res, open(os.path.join(os.path.dirname(__file__), "results", f"deploy_{ds}_{desc}_s{SEED}.json"), "w"), indent=1, default=float)
