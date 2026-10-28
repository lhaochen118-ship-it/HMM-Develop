"""E11 — sequence-level SelfCal: accept the match of frame t from the evidence of the window of the last L frames.
The null is built the SelfCal way: runs of L consecutive MAP images inside one held-out block, queried against the map
without that block, are off-map pseudo-sequences. A window statistic calibrated against these pseudo-windows gives a
conformal p-value per window with no independence assumption between frames (dependence is in the null too).
Window statistics (per-frame p_i = SelfCal-AA p-value against the per-item map null, top-1 positions x_i):
  F   = mean_i -log p_i   (evidence of the whole window; can vouch for a wrong last match — reported for contrast)
  RUN = selfcal.run_evidence: -log p summed over the trailing run of frames whose consecutive top-1 positions agree
        (within rho) with the last frame's match — the statistic we adopt.
Off-map windows: all L frames LOBO off-map in the same held-out block. Correct window: last frame correct in-map.
Cross-fitting (even blocks -> per-frame test, odd blocks -> pseudo-windows) makes the window p-value exactly valid.
Usage: exp11_sequence.py <dump> <rc|cmu|nord> [desc] -> results/seq_<ds>_<desc>.json"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC
from sc_eval import CFG
from eval_all import violations

dump, ds = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
LS, A = (1, 3, 5, 10), 0.05
ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
rho = c["excl"]


q_sid, q_k, m_sid, m_k = V.frame_order(dump, ds, ep, desc)


def windows(sid, k, L, valid):
    """index matrix (n_windows, L) of the L consecutive rows ending at each row (rows sorted within sequences)"""
    key = {(s, j): i for i, (s, j) in enumerate(zip(sid, k))}
    ends, W = [], []
    for i in range(len(sid)):
        if k[i] < L - 1: continue
        w = [key.get((sid[i], k[i] - L + 1 + j)) for j in range(L)]
        if None in w or not valid[w].all(): continue
        ends.append(i); W.append(w)
    return np.array(ends, int), np.array(W, int).reshape(-1, L)


# ---- per-frame statistics: map null with stride 1 (every map item, so map runs are consecutive), LOBO off-map, full
args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
mr = ep.m.astype(np.float32); mu = mr.mean(0, keepdims=True); nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
mc = nrm(mr - mu); q = ep.q.astype(np.float32); qc = nrm(q - mu)
Nr, Nc = SC.map_null(mr, ep.m_pos, *args, stride=1), SC.map_null(mc, ep.m_pos, *args, stride=1)
Or_ = SC.lobo_stats(mr, ep.m_pos, c["block"], c["off_d"], q, ep.q_pos, c["cell"], c["excl"], c["k"])
Oc = SC.lobo_stats(mc, ep.m_pos, c["block"], c["off_d"], qc, ep.q_pos, c["cell"], c["excl"], c["k"])
Fr, Fc = SC.qm_stats(q, mr, ep.m_pos, c["cell"], c["excl"], c["k"]), SC.qm_stats(qc, mc, ep.m_pos, c["cell"], c["excl"], c["k"])
# cross-fit for exact validity: the per-frame test is fitted on the map items of EVEN blocks; pseudo-windows come from
# ODD blocks, whose per-frame p-values are therefore computed exactly like those of deployment queries
bid, _ = V.map_cells(ep.m_pos, c["block"]); half = bid % 2 == 0
sub = lambda d, m: {k: np.where(m, v, np.nan) for k, v in d.items()}
test = SC.SelfCalTest(SC.pack(sub(Nr, half), sub(Nc, half)))
p_null, p_off, p_full = (test.pvalue(**SC.pack(r, cc)) for r, cc in ((Nr, Nc), (Or_, Oc), (Fr, Fc)))
nn = np.array([np.argmin(((ep.m_pos - x) ** 2).sum(1)) for x in ep.q_pos]); q_block = bid[nn]
inm = V.nearest_map_dist(ep) <= c["in_d"]; corr = V.correct(ep, *c["tol"]) & inm; _, dt, _ = V.top1_errors(ep); alias = inm & (dt > c["excl"])
null_ok = np.isfinite(Nr["maxsim"]) & np.isfinite(Nc["z_far"]) & ~half; off_ok = np.isfinite(Or_["maxsim"]) & np.isfinite(Oc["z_far"])


def wstats(p, top, W):
    lp = -np.log(np.clip(p[W], 1e-12, 1))
    return dict(F=lp.mean(1), RUN=SC.run_evidence(p, ep.m_pos[np.nan_to_num(top).astype(int)], W, rho))


res = {"meta": dict(n_null=int(null_ok.sum()), n_off=int(off_ok.sum()), n_corr=int(corr.sum()), rho=rho)}
cond = np.asarray(ep.q_cond)
for L in LS:
    ne, NW = windows(m_sid, m_k, L, null_ok)
    NW = NW[(bid[NW] == bid[NW[:, :1]]).all(1)]                       # one held-out block per pseudo-window
    oe, OW = windows(q_sid, q_k, L, off_ok)
    keep = (q_block[OW] == q_block[OW[:, :1]]).all(1); oe, OW = oe[keep], OW[keep]
    fe, FW = windows(q_sid, q_k, L, np.ones(len(q), bool))
    S0, So, Sf = wstats(p_null, Nr["top"], NW), wstats(p_off, Or_["top"], OW), wstats(p_full, Fr["top"], FW)
    P = {"F": (SC.conformal_p(S0["F"], So["F"]), SC.conformal_p(S0["F"], Sf["F"])),
         "RUN": (SC.conformal_p(S0["RUN"], So["RUN"]), SC.conformal_p(S0["RUN"], Sf["RUN"]))}
    for name, (po, pf) in P.items():
        acc_off = np.zeros(len(q), bool); offm = np.zeros(len(q), bool); offm[oe] = True; acc_off[oe] = po <= A
        nv, fars = violations(acc_off, cond, offm, A)
        if not fars: continue
        acc_in = np.zeros(len(q), bool); has = np.zeros(len(q), bool); acc_in[fe] = pf <= A; has[fe] = True
        r = dict(L=L, n_null_windows=len(NW), n_off_windows=len(oe), FAR=float(acc_off[offm].mean()), worst=float(max(fars.values())),
                 n_viol=nv, n_cond=len(fars), TPR=float(acc_in[corr & has].mean()), alias=float(acc_in[alias & has].mean()) if (alias & has).any() else None,
                 TPR_frame=float(np.mean(p_full[corr & has] <= A)))
        res[f"L{L}:{name}"] = r
        print(f"{ds}/{desc} L={L:2d} {name:4s} null w {len(NW):5d} off w {len(oe):5d} | FAR {r['FAR']:.3f} worst {r['worst']:.3f} viol {nv}/{len(fars)} "
              f"| TPR {r['TPR']:.3f} (per-frame on same frames {r['TPR_frame']:.3f}) alias {r['alias']}", flush=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
json.dump(res, open(os.path.join(os.path.dirname(__file__), "results", f"seq_{ds}_{desc}.json"), "w"), indent=1, default=float)
