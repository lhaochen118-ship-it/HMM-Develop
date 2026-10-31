"""CMS: Counterfactual Map Surgery -- self-calibration of sequential localisation on the deployment stream itself
(RESEARCH_LOG Entry 28, paper/cms_theory.md).

Principle. Every label-free guarantee so far (SelfCal, certified, CPC-SC, CPC-SC-T) calibrates the decision on the MAP's
own self-replay null: map frames, with their block removed, act as off-map pseudo-queries. That null (i) has the map's
image condition, not the deployment condition (night, snow), (ii) uses exact map poses as odometry, and (iii) has only
~10 exchangeable chunks, so long-excursion dependence is missing and alpha = 0.01 is infeasible on small maps.

CMS builds the null from the QUERY STREAM: for every frame t the evidence statistic is recomputed on a surgically altered
map M \\ B_t, where B_t is the corridor of radius rho = off_d + excl around the system's OWN belief (the anchors of the
winning route hypothesis of the last N frames). If the belief is right (|belief - truth| <= excl), every frame of the
window is > off_d from the remaining map: the counterfactual statistic is a draw of the OFF-MAP law, under the query's
own condition, odometry noise and temporal dependence. If the belief is wrong the true place survives the surgery and the
counterfactual statistic is high (the conservative direction). The decision threshold is a conformal quantile of the
counterfactual stream (segment-level, as SC), per query condition -> hundreds of calibration segments per condition.

Statistics (computed IDENTICALLY for the real map and for the surgically altered map, from top-K lists only):
  route cost   C_t = TAO'26 route-verification cost (tao.py: N = 20 frames, both directions, rigid 2-D fit, Huber,
               trimmed mean, appearance of the anchors); under surgery, hypotheses inside B_t are removed, anchor look-ups
               of masked entries fall back to the frame's K-th similarity, and an anchor trace that enters B_t leaves the
               route chunk from there on (exactly what a real hole does: route chunks end at holes).
  distinctiveness  z_t = (s1 - s_far) / std_t: best similarity minus the best one farther than excl from it (spatial
               ratio test), in units of the frame's similarity spread (affine invariant); under surgery both maxima are
               taken over unmasked entries (entries beyond the top-K: the K-th similarity, an upper bound -> conservative).
Rules (all constants in problem units: excl, off_d, H, alpha; one setting for every dataset):
  CMS-T        report iff C_t < kappa_T, kappa_T = floor(alpha (n+1))-th smallest segment-minimum of the counterfactual
               cost over disjoint H-frame segments of the condition's counterfactual stream
  CMS-CPC      presence chain (CPC recursion, p_in = p_out = 0.01) with LR_t = 1/2 (e^z_t + (e^C_t)^(1/2)), e = a p^(a-1),
               p = conformal rank of the real statistic in the counterfactual pool of the condition, a = Beta-EM of the
               query p-values of the condition; onset when log-odds > kappa (conformal (1 - alpha) quantile of the max
               fresh-start log-odds over counterfactual H-frame segments, the counterfactual chain fed with the leave-one-out
               ranks of the counterfactual statistics), persistence while log-odds > 0, optional SH stop (shape test of
               the reported track, cpc_geo.shape_ok; only removes reports).
Guarantee (cms_theory.md, Theorem 6): if a fraction pi of the counterfactual segments come from correctly believed on-map
windows and the off-map law is surgery-invariant and decreasing in the distance to the map, then
P(false onset in an off-map segment) <= alpha (n + 1) / (pi n + 1) ~ alpha / pi, with any dependence inside segments.
Usage (library): cms_stats(z, tk) -> dict; rules(z, b, st) -> name -> (score, fix positions, default threshold, accept)."""
import numpy as np
from hmm_fix import beta_em
from cpc_sc import logodds, consistency_ok
import cpc_geo as CG
import tao as TAO

OFF_D = {"boreas": 40.0, "cmu": 40.0, "4s": 40.0, "nclt": 20.0, "nord": 10.0, "rc": 40.0}


def _lookup(ks, ss, key, tol, K, valid=None):
    """largest similarity among a frame's top-K entries (sorted by route key) within tol of each key; K-th value if none"""
    p = np.searchsorted(ks, key); best = np.full(len(key), ss.min())
    for off in (-2, -1, 0, 1):
        pp = np.clip(p + off, 0, K - 1); okk = np.abs(ks[pp] - key) <= tol
        if valid is not None: okk &= valid[pp]
        best = np.where(okk, np.maximum(best, ss[pp]), best)
    return best


def cms_stats(z, tk, rho=None, N=20, delta=8.0, trim=0.75, wapp=2.0, tol=4.0, ds=None):
    """real and counterfactual (map surgery around the winner's anchors) route cost and distinctiveness of every frame"""
    MP = z["MP"]; one_d = MP.ndim == 1 or MP.shape[1] == 1; hz = list(z["hz"]); excl = float(z["excl"])
    if rho is None: rho = OFF_D.get((ds or "cmu").split(":")[0].split("_")[0], 40.0) + excl
    P, cid, arc = TAO.route(MP[:, hz] if (not one_d and MP.shape[1] > 2) else MP)
    o_all = z["o_q"]; o_all = (o_all[:, hz] if (not one_d and o_all.shape[1] > 2) else o_all).astype(float)
    if one_d: o_all = o_all.reshape(-1, 1)
    I, Sm = tk["idx"].astype(np.int64), tk["sim"].astype(np.float32); K = I.shape[1]; sd = np.maximum(tk["std"].astype(np.float32), 1e-6)
    BIG = 1e7; key_all = cid * BIG + arc
    starts = {c: arc[cid == c].min() for c in np.unique(cid)}; ends = {c: arc[cid == c].max() for c in np.unique(cid)}
    lo_arc = np.array([starts[c] for c in cid]); hi_arc = np.array([ends[c] for c in cid])
    n = len(I)
    out = {k: np.full(n, np.inf) for k in ("cost", "cost_cf")}
    out.update(j=np.full(n, -1), j_cf=np.full(n, -1), z=np.full(n, -np.inf), z_cf=np.full(n, -np.inf), n_mask=np.zeros(n, np.int32))
    order = np.argsort(key_all[I], axis=1); Ks = np.take_along_axis(key_all[I], order, 1); Ss = np.take_along_axis(Sm, order, 1)
    EP = P[I]                                                                    # (n, K, d) entry positions
    # distinctiveness on the real map (no surgery): best minus best farther than excl from it
    d01 = np.linalg.norm(EP - EP[:, :1], axis=2); far = d01 > excl
    sfar = np.where(far.any(1), np.where(far, Sm, -np.inf).max(1), Sm[:, -1])
    out["z"] = (Sm[:, 0] - sfar) / sd
    sid, kk = z["q_sid"], z["q_k"]
    for s in np.unique(sid):
        idx = np.where(sid == s)[0]; idx = idx[np.argsort(kk[idx])]; o = o_all[idx]
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        for i in range(len(idx)):
            t = idx[i]; w = np.arange(max(0, i - N + 1), i + 1)[::-1]
            if len(w) < 3: continue
            dl = cum[i] - cum[w]; j = I[t]; c, a0 = cid[j], arc[j]; fw = idx[w]
            per = []
            for sgn in (1.0, -1.0):
                aa = a0[:, None] - sgn * dl[None, :]
                inside = (aa >= lo_arc[j][:, None]) & (aa <= hi_arc[j][:, None])
                q = np.empty(aa.shape + (P.shape[1],))
                for d in range(P.shape[1]): q[..., d] = np.interp((c[:, None] * BIG + aa).ravel(), key_all, P[:, d]).reshape(aa.shape)
                pw = o[w]; pc = pw - pw.mean(0); qc = q - q.mean(1, keepdims=True)
                if P.shape[1] == 1:
                    res = np.abs(qc[..., 0] - pc[None, :, 0])
                else:
                    a_ = (pc[None, :, 0] * qc[..., 0] + pc[None, :, 1] * qc[..., 1]).sum(1)
                    b_ = (pc[None, :, 0] * qc[..., 1] - pc[None, :, 1] * qc[..., 0]).sum(1)
                    th = np.arctan2(b_, a_); cs, sn = np.cos(th)[:, None], np.sin(th)[:, None]
                    rx = cs * pc[None, :, 0] - sn * pc[None, :, 1]; ry = sn * pc[None, :, 0] + cs * pc[None, :, 1]
                    res = np.sqrt((qc[..., 0] - rx) ** 2 + (qc[..., 1] - ry) ** 2)
                hub0 = np.where(res <= delta, 0.5 * res ** 2, delta * (res - 0.5 * delta)) / delta ** 2
                m = max(1, int(np.ceil(trim * len(w))))
                geo = np.sort(np.where(inside, hub0, 10.0), 1)[:, :m].mean(1)
                keys = c[:, None] * BIG + aa
                app = np.stack([_lookup(Ks[f], Ss[f], keys[:, l], tol, K) for l, f in enumerate(fw)], 1)
                per.append(dict(aa=aa, inside=inside, q=q, hub0=hub0, keys=keys, C=geo + wapp * (1.0 - app).mean(1)))
            Cb = np.stack([per[0]["C"], per[1]["C"]]); dr, kb = np.unravel_index(int(np.argmin(Cb)), Cb.shape)
            out["cost"][t], out["j"][t] = float(Cb[dr, kb]), int(j[kb])
            # ---- surgery: corridor of radius rho around the winner's anchors
            A = per[dr]["q"][kb]                                                 # (n_w, d) believed positions of the window
            def inB(X):                                                          # X (..., d) -> within rho of the corridor
                dd = np.sqrt(((X[..., None, :] - A) ** 2).sum(-1)); return dd.min(-1) <= rho
            ent_m = inB(EP[fw])                                                  # (n_w, K) masked entries of window frames
            out["n_mask"][t] = int(ent_m[0].sum())
            hyp_ok = ~ent_m[0]                                                   # hypotheses of frame t outside the corridor
            # distinctiveness after surgery (frame t's own unmasked entries)
            v = ~ent_m[0]
            if v.any():
                i1 = int(np.flatnonzero(v)[0]); s1c = Sm[t, i1]
                farc = v & (np.linalg.norm(EP[t] - EP[t, i1], axis=1) > excl)
                sfc = Sm[t, farc].max() if farc.any() else Sm[t, -1]
            else:
                s1c, sfc = np.nan, np.nan                                        # all top-K masked: unknown -> missing (excluded)
            out["z_cf"][t] = (s1c - sfc) / sd[t]
            if not hyp_ok.any(): out["cost_cf"][t] = np.inf; continue
            best = (np.inf, -1)
            for pr in per:
                am = inB(pr["q"])                                                # anchors inside the corridor
                ins = pr["inside"] & ~np.maximum.accumulate(am, axis=1)          # trace leaves the chunk at the corridor
                geo = np.sort(np.where(ins, pr["hub0"], 10.0), 1)[:, :m].mean(1)
                vs = [(~ent_m[l])[order[f]] for l, f in enumerate(fw)]
                app = np.stack([_lookup(Ks[f], Ss[f], pr["keys"][:, l], tol, K, vs[l]) for l, f in enumerate(fw)], 1)
                C = np.where(hyp_ok, geo + wapp * (1.0 - app).mean(1), np.inf); kb2 = int(np.argmin(C))
                if C[kb2] < best[0]: best = (float(C[kb2]), int(j[kb2]))
            out["cost_cf"][t], out["j_cf"][t] = best
    out["rho"] = rho
    return out


def _segments(seqs, H):
    return [sq[i:i + H] for sq in seqs for i in range(0, len(sq) - H + 1, H)]


GROUP = "cond"                      # calibration unit: "cond" (Mondrian by condition, small ones pooled), "run", "loco" (causal)
ALPHA_MIN = [0.05]                  # smallest alpha the current rules use (sets the minimum calibration size)


def cond_seqs(z, seqs):
    """sequences grouped by query condition (Mondrian calibration). A conformal quantile at level alpha is non-degenerate
    only with n >= 2/alpha - 1 calibration segments, so conditions with fewer counterfactual segments than 2/alpha_min are
    pooled together (and, if the pool is still too small, with every condition). GROUP = "run": one group."""
    if GROUP == "run": return {"all": list(seqs)}
    cond, H = z["cond"], int(z["H"]); g = {}
    for sq in seqs: g.setdefault(cond[sq[0]], []).append(sq)
    nmin = int(np.ceil(2.0 / min(ALPHA_MIN)))
    nseg = lambda sqs: sum(len(q) // H for q in sqs)
    small = [k for k, v in g.items() if nseg(v) < nmin]
    if not small: return g
    pool = [q for k in small for q in g.pop(k)]
    if nseg(pool) >= nmin or not g: g["_pooled"] = pool; return g
    return {"all": list(seqs)}


def cal_groups(z, seqs):
    """[(test sequences, calibration sequences)]: GROUP "cond"/"run": transductive (a condition is calibrated on its own
    counterfactual stream); GROUP "loco": CAUSAL deployment protocol -- a condition is calibrated on the counterfactual
    streams of the OTHER conditions only (the robot's previous sessions), nothing of the current session is looked at."""
    if GROUP != "loco": return [(v, v) for v in cond_seqs(z, seqs).values()]
    cond = z["cond"]; g = {}
    for sq in seqs: g.setdefault(cond[sq[0]], []).append(sq)
    if len(g) < 2: return [(v, v) for v in g.values()]
    return [(v, [q for k2, v2 in g.items() if k2 != k for q in v2]) for k, v in g.items()]


def kappa_min(cf, segs, alpha):
    """floor(alpha (n+1))-th smallest segment minimum of a counterfactual statistic (lower = more on-map)"""
    mins = np.sort([np.min(cf[sg]) for sg in segs]); k = int(np.floor(alpha * (len(mins) + 1)))
    return (float(mins[k - 1]) if k >= 1 else -np.inf), len(mins)


def kappa_max_chain(ll_cf, segs, alpha, p_in=0.01, p_out=0.01):
    """conformal (1 - alpha) quantile of the max fresh-start presence log-odds over counterfactual segments"""
    mx = []
    for sg in segs:
        pon, best = 0.5, -np.inf
        for i, t in enumerate(sg):
            pr_ = pon * (1 - p_out) + (1 - pon) * p_in if i > 0 else 0.5
            l = float(np.clip(np.log(pr_ / (1 - pr_)) + ll_cf[t], -50, 50)); pon = 1 / (1 + np.exp(-l)); best = max(best, l)
        mx.append(best)
    mx = np.sort(mx); k = int(np.ceil((1 - alpha) * (len(mx) + 1)))
    return (max(mx[k - 1], 0.0) if 0 < k <= len(mx) else np.inf), len(mx)


def rank_p(pool, x, lower_is_on):
    """conformal p-value of x against the counterfactual pool (small p = evidence of presence)"""
    srt = np.sort(pool[np.isfinite(pool)]) if lower_is_on else np.sort(-pool[np.isfinite(pool)])
    v = x if lower_is_on else -x
    return (1 + np.searchsorted(srt, v, side="right")) / (1 + len(srt))


def chain_parts(z, b, st, w_route=0.5, alpha=0.05, use=("z", "cost")):
    """per-condition CMS presence chain: query log LR, counterfactual log LR, kappa per frame, n segments per frame"""
    H, seqs = b["H"], b["seqs"]; n = len(z["cond"])
    llq, llc, kap, nseg = np.zeros(n), np.zeros(n), np.full(n, np.inf), np.zeros(n, int)
    for sqs, cqs in cal_groups(z, seqs):
        m = np.concatenate(sqs); mc = np.concatenate(cqs); comps_q, comps_c = [], []
        for key, low in (("cost", True), ("z", False)):
            if key not in use: continue
            real, cf = st[key][m], st[key + "_cf"][mc]
            fin = np.isfinite(cf)
            pq = np.clip(rank_p(cf, real, low), 1e-6, 1)
            # leave-one-out rank of every counterfactual value within the pool (exchangeable with a fresh off-map draw)
            srt = np.sort(cf[fin] if low else -cf[fin]); v = np.where(fin, cf if low else -cf, np.inf)
            pc = np.clip(np.searchsorted(srt, v, side="right") / (1 + len(srt)), 1e-6, 1)
            a, _ = beta_em(pq); pw = w_route if key == "cost" else 1.0
            ec = (a * pc ** (a - 1)) ** pw; ec[~fin] = 1.0                       # missing counterfactual: neutral e-value
            comps_q.append((a * pq ** (a - 1)) ** pw); comps_c.append(ec)
        llq[m] = np.log(np.mean(comps_q, 0)); llc_g = np.zeros(n); llc_g[mc] = np.log(np.mean(comps_c, 0))
        if mc is m or np.array_equal(mc, m): llc[m] = llc_g[m]
        segs = _segments(cqs, H); k, ns = kappa_max_chain(llc_g, segs, alpha); kap[m] = k; nseg[m] = ns
    return llq, llc, kap, nseg


def kappa_seg_max(cf_score, segs, alpha, delta=None):
    """threshold on a score (higher = more on-map) from the max of the counterfactual score over disjoint segments.
    delta None: marginal conformal (1 - alpha) quantile (P(report in an exchangeable segment) <= alpha);
    delta: training-conditional (PAC) version, P(exceedance rate > alpha | calibration) <= delta (Vovk 2012): the k-th
    largest segment maximum with the largest k such that P(Bin(n, alpha) <= k - 1) <= delta."""
    mx = np.sort([np.max(cf_score[sg]) for sg in segs])[::-1]; n = len(mx)
    if delta is None:
        k = n + 1 - int(np.ceil((1 - alpha) * (n + 1)))                  # = floor(alpha (n+1)) largest -> report iff score > it
    else:
        from scipy.stats import binom
        ks = np.arange(1, n + 1); ok = binom.cdf(ks - 1, n, alpha) <= delta; k = int(ks[ok].max()) if ok.any() else 0
    return (float(mx[k - 1]) if k >= 1 else np.inf), n


def fisher_parts(z, b, st, keys=(("cost", True), ("z", False))):
    """CMS-F: per-condition score = sum_k -log p_k with p_k the conformal rank of the real statistic in the condition's
    counterfactual pool; counterfactual score with leave-one-out ranks inside the pool (missing -> p = 1/2)."""
    H, seqs = b["H"], b["seqs"]; n = len(z["cond"]); sq_ = np.zeros(n); segs_by = {}
    for gi, (sqs, cqs) in enumerate(cal_groups(z, seqs)):
        m = np.concatenate(sqs); mc = np.concatenate(cqs); sc_ = np.zeros(n)
        for key, low in keys:
            real, cf = st[key][m], st[key + "_cf"][mc]; fin = np.isfinite(cf)
            pq = np.clip(rank_p(cf, real, low), 1e-6, 1)
            srt = np.sort(cf[fin] if low else -cf[fin]); v = np.where(fin, cf if low else -cf, np.inf)
            pc = np.clip(np.searchsorted(srt, v, side="right") / (1 + len(srt)), 1e-6, 1); pc[~fin] = 0.5
            sq_[m] += -np.log(pq); sc_[mc] += -np.log(pc)
        segs_by[gi] = (m, _segments(cqs, H), sc_)
    return sq_, None, segs_by


def rules(z, b, st, alpha=0.05, delta=0.1):
    """CMS decision rules: name -> (score, fix positions, default threshold, default accept)"""
    ALPHA_MIN[0] = alpha                                                     # Mondrian minimum size for this alpha
    H, seqs, excl, MP = b["H"], b["seqs"], b["excl"], b["MP"]; hz = list(z["hz"])
    jj = np.maximum(st["j"], 0); xt = MP[jj]; okj = st["j"] >= 0
    F = {}
    kT = np.full(len(jj), -np.inf); nT = np.zeros(len(jj), int)
    for sqs, cqs in cal_groups(z, seqs):
        m = np.concatenate(sqs); k, ns = kappa_min(st["cost_cf"], _segments(cqs, H), alpha); kT[m] = k; nT[m] = ns
    sc_t = np.where(okj, -st["cost"], -np.inf)
    F["CMS-T"] = (sc_t + kT, xt, 0.0, sc_t > -kT)
    sh_t = CG.shape_ok(xt, z["o_q"], seqs, excl, 3.0, 0.5, hz=hz) & okj
    F["CMS-T+SH"] = (np.where(sh_t, sc_t + kT, -np.inf), xt, 0.0, (sc_t > -kT) & sh_t)
    for nm, keys in (("CMS-F", (("cost", True), ("z", False))), ("CMS-Tc", (("cost", True),))):
        sq_, sc_, segs_by = fisher_parts(z, b, st, keys)
        for tg, dl in (("", None), ("-PAC", delta)):
            kF = np.full(len(jj), np.inf)
            for gi, (m, segs, scg) in segs_by.items(): kF[m] = kappa_seg_max(scg, segs, alpha, dl)[0]
            sF = np.where(okj, sq_, -np.inf)
            F[nm + tg] = (sF - kF, xt, 0.0, sF > kF)
            if tg == "": F[nm + "+SH"] = (np.where(sh_t, sF - kF, -np.inf), xt, 0.0, (sF > kF) & sh_t)
    lo_parts = chain_parts(z, b, st, alpha=alpha)
    llq, _, kap, _ = lo_parts; lo = logodds(llq, seqs)
    F["CMS-CPC"] = (lo - kap, xt, 0.0, CG.hyst_ok(lo > kap, lo > 0, np.ones(len(lo), bool), seqs) & okj)
    F["CMS-CPC+SH"] = (np.where(sh_t, lo - kap, -np.inf), xt, 0.0, CG.hyst_ok(lo > kap, lo > 0, np.ones(len(lo), bool), seqs) & sh_t)
    # reported place = the HMM place-chain MAP (smooth track; the paper's HMM decision), shape stop on that track and the
    # agreement gate |TAO winner - MAP| <= excl (both the route evidence and the place chain point at the same place)
    xc = MP[b["est_c"]]; agree = okj & (np.linalg.norm(xc - xt, axis=1) <= excl)
    sh_c = CG.shape_ok(xc, z["o_q"], seqs, excl, 3.0, 0.5, hz=hz)
    one = np.ones(len(lo), bool)
    for tg, ok in (("H", one), ("H+SH", sh_c), ("H+SH+G", sh_c & agree), ("H+G", agree)):
        F[f"CMS-CPC/{tg}"] = (np.where(ok, lo - kap, -np.inf), xc, 0.0, CG.hyst_ok(lo > kap, lo > 0, one, seqs) & ok)
        F[f"CMS-T/{tg}"] = (np.where(ok, sc_t + kT, -np.inf), xc, 0.0, (sc_t > -kT) & ok)
    # CMS-U: union of the route test and the presence-chain onset, each at alpha/2 (union bound: false onset <= alpha)
    ALPHA_MIN[0] = alpha / 2
    kT2 = np.full(len(jj), -np.inf)
    for sqs, cqs in cal_groups(z, seqs):
        m = np.concatenate(sqs); kT2[m] = kappa_min(st["cost_cf"], _segments(cqs, H), alpha / 2)[0]
    llq2, _, kap2, _ = chain_parts(z, b, st, alpha=alpha / 2); lo2 = logodds(llq2, seqs)
    onU = (sc_t > -kT2) | (lo2 > kap2); keepU = (sc_t > -kT2) | (lo2 > 0)
    scU = np.maximum(sc_t + kT2, lo2 - kap2)
    for tg, ok in (("H", one), ("H+SH", sh_c), ("H+SH+G", sh_c & agree)):
        F[f"CMS-U/{tg}"] = (np.where(ok, scU, -np.inf), xc, 0.0, CG.hyst_ok(onU, keepU, one, seqs) & ok)
    ALPHA_MIN[0] = alpha
    return F, dict(kT=kT, nT=nT, kap=kap, lo=lo)
