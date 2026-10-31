"""CPC-W/G: presence decision with a FINITE-MEMORY onset, reset-on-stop persistence and a SHAPE-consistency stop (Entry 26).

Why (RESEARCH_LOG Entry 26, dep_diag.py):
  * off-map SelfCal p-values are marginally valid in the interior of excursions; the violations sit within ~50 m of the
    map edge (view overlap) and in the odometry-anchored R statistic of long excursions, where the map self-replay null
    has no samples (its chunks are ~100 frames, ~10 per map);
  * a full-memory presence chain makes a segment deep inside an excursion depend on the whole excursion (carried state),
    so segment exchangeability with the short null chunks cannot hold there;
  * the magnitude-only consistency stop CS misses tracks that move at the right speed on a wrong-shaped path; the 2-D
    Procrustes residual of the reported track against the odometry (turns included) is far more specific
    (geo_cons.py: off-map pass rate 0.000-0.005 vs 0.002-0.088 for CS at similar on-map pass rate).
Rule (all constants in units of excl, H, alpha; one setting for every dataset):
  onset        windowed presence log-odds over the last W = H frames (chain restarted at odds 1, cpc_sc.window_logodds)
               above kappa_W = conformal (1 - alpha) quantile of the max windowed log-odds over disjoint H-frame segments of
               the map self-replay null (oc_curves.wcpc)  -> depends on the last H frames only
  persistence  full-memory CPC log-odds > 0
  stop         shape test fails (RMS Procrustes residual of the place-chain MAP track vs the odometry over the last
               D_s = 3 excl of path > eps = excl/2) or the magnitude test CS fails; a stop RESETS the decision (a new
               onset is needed)
Guarantee (cpc_theory.md section 3e): every off-map report belongs to a streak that started with an onset inside the
excursion (no carried streak survives the stop beyond the map edge, geometric persistence lemma), and an onset in a segment
lying >= W - 1 frames inside an excursion has probability <= alpha if query windows there are exchangeable with null
windows; dependence inside windows and between segments is arbitrary (linearity), so E[segment onset rate] <= alpha."""
import numpy as np
from geo_cons import window_points, procrustes2
from cpc_sc import logodds, window_logodds, consistency_ok, sc_evidence
from hmm_fix import beta_em


def shape_ok(x_m, o_q, seqs, excl, D_x=3.0, eps_x=0.5, step_x=0.2, min_x=1.0, hz=None):
    """False at frame t when the reported track over the last D_x excl of odometry path does not fit the odometry by a
    rigid 2-D motion within RMS eps_x excl (windows shorter than min_x excl of path always pass). 1-D maps: translation only."""
    one_d = x_m.ndim == 1 or x_m.shape[1] == 1
    if not one_d and hz is not None and x_m.shape[1] > 2: x_m, o_q = x_m[:, hz], o_q[:, hz]
    ok = np.ones(len(x_m), bool); D, eps, step = D_x * excl, eps_x * excl, step_x * excl
    for idx in seqs:
        m, o = x_m[idx].astype(float), o_q[idx].astype(float)
        if one_d: m, o = m.reshape(-1, 1), o.reshape(-1, 1)
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(o, axis=0), axis=1))]
        for i in range(len(idx)):
            w = window_points(o, cum, i, D, step)
            if len(w) < 3 or cum[i] - cum[w[0]] < min_x * excl: continue
            if one_d:
                d = (m[w, 0] - m[w, 0].mean()) - (o[w, 0] - o[w, 0].mean()); r = float(np.sqrt((d ** 2).mean()))
            else:
                r = procrustes2(m[w], o[w])[0]
            ok[idx[i]] = r <= eps
    return ok


def hyst_ok(start, keep, ok, seqs):
    """report from an onset (start & ok) while keep & ok; any frame with ok False ends the streak (reset: next report needs
    a new onset)"""
    acc = np.zeros(len(start), bool)
    for idx in seqs:
        rep = False
        for t in idx:
            rep = ok[t] and (keep[t] if rep else start[t]); acc[t] = rep
    return acc


def wcpc_parts(z, b, W, alpha=0.05):
    """windowed CPC log-odds of the queries and kappa_W per frame (as oc_curves.wcpc, without the floor at 0)"""
    H = b["H"]; fl, ln = z["nchunk_flat"], z["nchunk_len"]; nch = np.split(fl, np.cumsum(ln)[:-1]) if len(ln) else []
    cl = lambda x: np.clip(np.nan_to_num(x, nan=1.0), 1e-6, 1)
    pn, prn, pq, pr = cl(z["p_n"]), cl(z["pRn"]), cl(z["p_q"]), cl(z["pR"])
    MP, est, top = b["MP"], b["est_c"], b["top"]; agree = np.linalg.norm(MP[top] - MP[est], axis=1) <= b["excl"]
    llq = np.zeros(len(pq)); kap = np.zeros(len(pq))
    for cn in sorted(set(z["cond"])):
        m = z["cond"] == cn; a1, _ = beta_em(pq[m]); a2, _ = beta_em(pr[m])
        llq[m] = np.log(0.5 * (np.where(agree[m], a1 * pq[m] ** (a1 - 1), a1) + (a2 * pr[m] ** (a2 - 1)) ** (1.0 / H)))
        lln = np.log(0.5 * (np.maximum(a1 * pn ** (a1 - 1), a1) + (a2 * prn ** (a2 - 1)) ** (1.0 / H)))
        mx = []
        for ch in nch:
            if len(ch) < W + H - 1: continue
            w = window_logodds(lln, [ch], W)[ch][W - 1:]
            mx += [w[i:i + H].max() for i in range(0, len(w) - H + 1, H)]
        mx = np.sort(mx); k = int(np.ceil((1 - alpha) * (len(mx) + 1)))
        kap[m] = mx[k - 1] if 0 < k <= len(mx) else np.inf
    return window_logodds(llq, b["seqs"], W), llq, kap


def rules(z, b, alpha=0.05):
    """name -> (score for operating curves, accept mask at the default point) for the Entry 26 variants"""
    excl, seqs, MP, est = b["excl"], b["seqs"], b["MP"], b["est_c"]; x_c = MP[est]; hz = list(z["hz"])
    cs = consistency_ok(x_c, z["o_q"], seqs, excl, 3.0)
    sh = shape_ok(x_c, z["o_q"], seqs, excl, 3.0, 0.5, hz=hz)
    sh4 = shape_ok(x_c, z["o_q"], seqs, excl, 3.0, 0.25, hz=hz)
    lo_s, kap = sc_evidence(z, b, alpha)                       # CPC-SC (Entry 25): full-memory log-odds, segment kappa
    W = b["H"]; wlo, llq, kw = wcpc_parts(z, b, W, alpha); lo_full = logodds(llq, seqs)
    out = {}
    for tag, ok in (("+CS", cs), ("+SH", sh), ("+CS+SH", cs & sh), ("+CS+SH4", cs & sh4)):
        out["CPC-SC" + tag] = (np.where(ok, lo_s - kap, -np.inf), hyst_ok(lo_s > kap, lo_s > 0, np.ones(len(ok), bool), seqs) & ok)
        out["CPC-SC" + tag + "(reset)"] = (np.where(ok, lo_s - kap, -np.inf), hyst_ok(lo_s > kap, lo_s > 0, ok, seqs))
        out["CPC-W" + tag] = (np.where(ok, wlo - kw, -np.inf), hyst_ok(wlo > kw, lo_full > 0, ok, seqs))
    return out, x_c


def scj_kappa(z, b, ok_kind="CS", alpha=0.05, p_in=0.01, p_out=0.01, floor=0.0):
    """JOINT segment calibration of the onset: kappa_J (per query condition) = conformal (1 - alpha) quantile, over disjoint
    H-frame segments of the map self-replay null, of max_t (fresh-start presence log-odds_t if ok_t else -inf), ok computed
    on the NULL place chain (est_n, exact map odometry) exactly as on the queries (CS, SH or both). The null passes the
    geometric tests more often than real off-map queries (Entry 25: 2.6x for CS on CMU CosPlace), so it is conservative
    for the geometric part; kappa_J <= kappa (SC) because the max runs over fewer frames."""
    H, excl, MP = b["H"], b["excl"], b["MP"]; fl, ln = z["nchunk_flat"], z["nchunk_len"]
    bounds = np.r_[0, np.cumsum(ln)]; nseqs = [np.arange(a, c) for a, c in zip(bounds[:-1], bounds[1:])]
    x_n, o_n = MP[z["est_n"]], MP[fl].astype(float); hz = list(z["hz"])
    ok_n = np.ones(len(fl), bool)
    if "CS" in ok_kind: ok_n &= consistency_ok(x_n, o_n, nseqs, excl, 3.0)
    if "SH" in ok_kind: ok_n &= shape_ok(x_n, o_n, nseqs, excl, 3.0, 0.5, hz=hz)
    segs = [sq[i:i + H] for sq in nseqs for i in range(0, len(sq) - H + 1, H)]
    cl = lambda x: np.clip(np.nan_to_num(x, nan=1.0), 1e-6, 1)
    pn, prn, pq, pr = cl(z["p_n"][fl]), cl(z["pRn"][fl]), cl(z["p_q"]), cl(z["pR"])
    kap = np.zeros(len(pq))
    for cn in sorted(set(z["cond"])):
        m = z["cond"] == cn; a1, _ = beta_em(pq[m]); a2, _ = beta_em(pr[m])
        ll = np.log(0.5 * (np.maximum(a1 * pn ** (a1 - 1), a1) + (a2 * prn ** (a2 - 1)) ** (1.0 / H)))
        mx = []
        for sg in segs:
            pon, best = 0.5, -np.inf
            for i, t in enumerate(sg):
                pr_ = pon * (1 - p_out) + (1 - pon) * p_in if i > 0 else 0.5
                l = float(np.clip(np.log(pr_ / (1 - pr_)) + ll[t], -50, 50)); pon = 1 / (1 + np.exp(-l))
                if ok_n[t]: best = max(best, l)
            mx.append(best)
        mx = np.sort(mx); k = int(np.ceil((1 - alpha) * (len(mx) + 1)))
        kap[m] = max(mx[k - 1] if 0 < k <= len(mx) else np.inf, floor)
    return kap, float(ok_n.mean())


def rules_scj(z, b, alpha=0.05):
    """CPC-SCJ: CPC-SC presence log-odds, onset above the JOINTLY calibrated kappa_J, persistence > 0, stop + reset"""
    excl, seqs, MP, est = b["excl"], b["seqs"], b["MP"], b["est_c"]; x_c = MP[est]; hz = list(z["hz"])
    if "est_n" not in z or len(z["est_n"]) != len(z["nchunk_flat"]): return {}, x_c
    cs = consistency_ok(x_c, z["o_q"], seqs, excl, 3.0); sh = shape_ok(x_c, z["o_q"], seqs, excl, 3.0, 0.5, hz=hz)
    lo_s, _ = sc_evidence(z, b, alpha); out = {}
    for tag, ok in (("CS", cs), ("SH", sh), ("CS+SH", cs & sh)):
        kj, _ = scj_kappa(z, b, tag, alpha)
        out[f"CPC-SCJ+{tag}"] = (np.where(ok, lo_s - kj, -np.inf), hyst_ok(lo_s > kj, lo_s > 0, ok, seqs))
        # no floor: the onset threshold is the null quantile itself (may be < 0, i.e. P(on) < 1/2); persistence at min(0, kappa)
        ku, _ = scj_kappa(z, b, tag, alpha, floor=-np.inf)
        out[f"CPC-SCJu+{tag}"] = (np.where(ok, lo_s - ku, -np.inf), hyst_ok(lo_s > ku, lo_s > np.minimum(ku, 0), ok, seqs))
    return out, x_c


def sc_evidence_x(z, b, pq3, pn3, alpha=0.05, w3=None, p_in=0.01, p_out=0.01):
    """CPC-SC with a THIRD presence component: per-frame p-value pq3 of the queries and pn3 of the map self-replay null
    (indexed by map row, like p_n), e.g. the map-null rank of the TAO route-verification cost. LR = mean of the gated
    top-1 e-value, e_R^(1/H) and e_3^(w3) (w3 = 1/H by default, as e_R: the statistic spans a window); kappa from the same
    statistics on the null segments (SC). Validity as SC: segment exchangeability with the null, any dependence inside."""
    H = b["H"]; w3 = 1.0 / H if w3 is None else w3
    fl, ln = z["nchunk_flat"], z["nchunk_len"]; nch = np.split(fl, np.cumsum(ln)[:-1]) if len(ln) else []
    segs = [ch[i:i + H] for ch in nch for i in range(0, len(ch) - H + 1, H)]
    cl = lambda x: np.clip(np.nan_to_num(x, nan=1.0), 1e-6, 1)
    pn, prn, pq, pr, q3, n3 = cl(z["p_n"]), cl(z["pRn"]), cl(z["p_q"]), cl(z["pR"]), cl(pq3), cl(pn3)
    MP, est, top = b["MP"], b["est_c"], b["top"]; agree = np.linalg.norm(MP[top] - MP[est], axis=1) <= b["excl"]
    llq, kap = np.zeros(len(pq)), np.zeros(len(pq))
    for cn in sorted(set(z["cond"])):
        m = z["cond"] == cn; a1, _ = beta_em(pq[m]); a2, _ = beta_em(pr[m]); a3, _ = beta_em(q3[m])
        et = a1 * pq[m] ** (a1 - 1)
        llq[m] = np.log((np.where(agree[m], et, a1) + (a2 * pr[m] ** (a2 - 1)) ** (1.0 / H) + (a3 * q3[m] ** (a3 - 1)) ** w3) / 3)
        ll = np.log((np.maximum(a1 * pn ** (a1 - 1), a1) + (a2 * prn ** (a2 - 1)) ** (1.0 / H) + (a3 * n3 ** (a3 - 1)) ** w3) / 3)
        mx = []
        for sg in segs:
            pon, best = 0.5, -np.inf
            for i, t in enumerate(sg):
                pr_ = pon * (1 - p_out) + (1 - pon) * p_in if i > 0 else 0.5
                l = float(np.clip(np.log(pr_ / (1 - pr_)) + ll[t], -50, 50)); pon = 1 / (1 + np.exp(-l)); best = max(best, l)
            mx.append(best)
        mx = np.sort(mx); k = int(np.ceil((1 - alpha) * (len(mx) + 1)))
        kap[m] = max(mx[k - 1] if k <= len(mx) else np.inf, 0.0)
    return logodds(llq, b["seqs"], p_in, p_out), kap
