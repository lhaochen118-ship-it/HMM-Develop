"""Sequence-level SelfCal with ODOMETRY-consistent evidence (hypothesis H1 of the HMM direction).

exp11 (branch claude/selfcal-seq) accumulated per-frame evidence -log p over the trailing run of frames whose
consecutive top-1 map positions stay within rho of each other. Its validity failed on Nordland: under snow, off-map
frames keep retrieving the SAME wrong place, so runs of "consistent" (= stationary) aliases are longer than in the
map's own pseudo-sequences. H1: requiring the matches to move WITH THE ODOMETRY (anchored at the last frame:
||x_t - x_{t-j} - (o_t - o_{t-j})|| <= rho_o) removes that failure, because a stuck alias is inconsistent with a
moving robot, and the remaining false runs (parallel aliases) have the same structure in map pseudo-sequences.

Per-frame p = SelfCal-AA (cross-fitted: per-frame test on map items of even blocks, pseudo-windows from odd blocks).
Odometry o: integrated GT displacement with multiplicative scale error + per-step noise (seeded), for queries and
map pseudo-sequences alike.
Usage: seq_odo.py <dump> <rc|cmu|nord> [desc] -> results/seqodo_<ds>_<desc>.json"""
import sys, os, json
import numpy as np
from scipy.stats import binom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V, selfcal as SC
from sc_eval import CFG

dump, ds = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
LS, A = (1, 3, 5, 10, 20), 0.05
ep = V.LOADERS[ds](dump, desc); c = CFG[ds]; rho = c["excl"]
RHO_O = [rho / 5, rho / 2.5, rho]
q_sid, q_k, m_sid, m_k = V.frame_order(dump, ds, ep, desc)


def violations(acc_off, cond, offm, a):
    cs = [x for x in sorted(set(cond)) if (offm & (cond == x)).sum() >= 20]; nv = 0; fars = {}
    for x in cs:
        m = offm & (cond == x); k, n = int(acc_off[m].sum()), int(m.sum()); fars[x] = k / n
        if binom.sf(k - 1, n, a) < 0.05 / len(cs): nv += 1
    return nv, fars


def windows(sid, k, L, valid):
    key = {(s, j): i for i, (s, j) in enumerate(zip(sid, k))}; ends, W = [], []
    for i in range(len(sid)):
        if k[i] < L - 1: continue
        w = [key.get((sid[i], k[i] - L + 1 + j)) for j in range(L)]
        if None in w or not valid[w].all(): continue
        ends.append(i); W.append(w)
    return np.array(ends, int), np.array(W, int).reshape(-1, L)


def odometry(pos, sid, k, seed, scale_sd=0.03, step_sd=0.05):
    """integrated noisy odometry per sequence: o_t = o_{t-1} + (1+e_s) * dx_t + N(0, step_sd*|dx_t|)"""
    rng = np.random.default_rng(seed); o = np.zeros_like(pos)
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(k[idx])]
        dx = np.diff(pos[idx], axis=0); sc = 1 + rng.normal(0, scale_sd)
        nz = rng.normal(0, 1, dx.shape) * step_sd * np.linalg.norm(dx, axis=1, keepdims=True)
        o[idx] = np.vstack([np.zeros((1, pos.shape[1])), np.cumsum(sc * dx + nz, axis=0)])
    return o


def run_len(cons):
    """cons (n, L-1): cons[:, j] = frame j (oldest first) consistent with the last frame -> length of the trailing run"""
    return np.cumprod(cons[:, ::-1], axis=1).sum(1)


def wstats(p, top, W, o):
    lp = -np.log(np.clip(p[W], 1e-12, 1)); L = W.shape[1]; out = {"F": lp.mean(1)}
    X = ep.m_pos[np.nan_to_num(top).astype(int)][W]
    take = lambda run: (lp * (np.arange(L)[None, ::-1] <= run[:, None])).sum(1)
    if L == 1:
        out["RUN"] = lp[:, 0]
        for r in RHO_O: out[f"RUNO{r:g}"] = lp[:, 0]
        return out
    out["RUN"] = take(run_len(np.linalg.norm(X[:, 1:] - X[:, :-1], axis=-1) <= rho))     # exp11 (chain, no odometry)
    O = o[W]
    dev = np.linalg.norm((X[:, -1:] - X[:, :-1]) - (O[:, -1:] - O[:, :-1]), axis=-1)     # anchored at the last frame
    for r in RHO_O: out[f"RUNO{r:g}"] = take(run_len(dev <= r))
    return out


# ---- per-frame statistics (as exp11)
args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
mr = ep.m.astype(np.float32); mu = mr.mean(0, keepdims=True); nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
mc = nrm(mr - mu); q = ep.q.astype(np.float32); qc = nrm(q - mu)
Nr, Nc = SC.map_null(mr, ep.m_pos, *args, stride=1), SC.map_null(mc, ep.m_pos, *args, stride=1)
Or_ = SC.lobo_stats(mr, ep.m_pos, c["block"], c["off_d"], q, ep.q_pos, c["cell"], c["excl"], c["k"])
Oc = SC.lobo_stats(mc, ep.m_pos, c["block"], c["off_d"], qc, ep.q_pos, c["cell"], c["excl"], c["k"])
Fr, Fc = SC.qm_stats(q, mr, ep.m_pos, c["cell"], c["excl"], c["k"]), SC.qm_stats(qc, mc, ep.m_pos, c["cell"], c["excl"], c["k"])
bid, _ = V.map_cells(ep.m_pos, c["block"]); half = bid % 2 == 0
sub = lambda d, m: {k: np.where(m, v, np.nan) for k, v in d.items()}
test = SC.SelfCalTest(SC.pack(sub(Nr, half), sub(Nc, half)))
p_null, p_off, p_full = (test.pvalue(**SC.pack(r, cc)) for r, cc in ((Nr, Nc), (Or_, Oc), (Fr, Fc)))
nn = np.array([np.argmin(((ep.m_pos - x) ** 2).sum(1)) for x in ep.q_pos]); q_block = bid[nn]
inm = V.nearest_map_dist(ep) <= c["in_d"]; corr = V.correct(ep, *c["tol"]) & inm; _, dt, _ = V.top1_errors(ep); alias = inm & (dt > c["excl"])
null_ok = np.isfinite(Nr["maxsim"]) & np.isfinite(Nc["z_far"]) & ~half; off_ok = np.isfinite(Or_["maxsim"]) & np.isfinite(Oc["z_far"])
cond = np.asarray(ep.q_cond).astype(str)
os.makedirs("results", exist_ok=True)
np.savez_compressed(f"results/seqodo_cache_{ds}_{desc}.npz", p_null=p_null, p_off=p_off, p_full=p_full, top_null=Nr["top"], top_off=Or_["top"],
                    top_full=Fr["top"], null_ok=null_ok, off_ok=off_ok, corr=corr, alias=alias, q_block=q_block, bid=bid)

res = {"meta": dict(n_null=int(null_ok.sum()), n_off=int(off_ok.sum()), n_corr=int(corr.sum()), rho=rho, rho_o=RHO_O)}
for seed in range(3):
    o_m, o_q = odometry(ep.m_pos, m_sid, m_k, 100 + seed), odometry(ep.q_pos, q_sid, q_k, 200 + seed)
    for L in LS:
        if seed > 0 and L == 1: continue
        ne, NW = windows(m_sid, m_k, L, null_ok); NW = NW[(bid[NW] == bid[NW[:, :1]]).all(1)]
        oe, OW = windows(q_sid, q_k, L, off_ok); keep = (q_block[OW] == q_block[OW[:, :1]]).all(1); oe, OW = oe[keep], OW[keep]
        fe, FW = windows(q_sid, q_k, L, np.ones(len(q), bool))
        if len(NW) < 50 or len(OW) < 20: continue
        S0, So, Sf = wstats(p_null, Nr["top"], NW, o_m), wstats(p_off, Or_["top"], OW, o_q), wstats(p_full, Fr["top"], FW, o_q)
        for name in S0:
            if L == 1 and name != "F": continue
            po, pf = SC.conformal_p(S0[name], So[name]), SC.conformal_p(S0[name], Sf[name])
            acc_off = np.zeros(len(q), bool); offm = np.zeros(len(q), bool); offm[oe] = True; acc_off[oe] = po <= A
            nv, fars = violations(acc_off, cond, offm, A)
            if not fars: continue
            acc_in = np.zeros(len(q), bool); has = np.zeros(len(q), bool); acc_in[fe] = pf <= A; has[fe] = True
            r = dict(seed=seed, L=L, stat=name, n_null_windows=len(NW), n_off_windows=len(oe), FAR=float(acc_off[offm].mean()),
                     worst=float(max(fars.values())), n_viol=nv, n_cond=len(fars), per_cond=fars, TPR=float(acc_in[corr & has].mean()),
                     alias=float(acc_in[alias & has].mean()) if (alias & has).any() else None, TPR_frame=float(np.mean(p_full[corr & has] <= A)))
            res[f"s{seed}:L{L}:{name}"] = r
            print(f"{ds}/{desc} s{seed} L={L:2d} {name:9s} nullw {len(NW):5d} offw {len(oe):5d} | FAR {r['FAR']:.3f} worst {r['worst']:.3f} "
                  f"viol {nv}/{len(fars)} | TPR {r['TPR']:.3f} (frame {r['TPR_frame']:.3f}) alias {r['alias']}", flush=True)
json.dump(res, open(f"results/seqodo_{ds}_{desc}.json", "w"), indent=1, default=float)
