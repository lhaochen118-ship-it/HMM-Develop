"""CPC-SC+CS: the label-free acceptance rule adopted in RESEARCH_LOG Entry 25 (replaces CPC-HMM +TCEmin).

  presence chain   CPC-HMM (marginal map-calibrated e-values of the top-1 SelfCal p-value and of the anchored R
                   statistic, gated by top-1 = place-chain MAP), p_in = p_out = 0.01
  onset            log-odds > kappa: kappa = conformal (1 - alpha) quantile of the max log-odds over H-frame segments of
                   the map self-replay null (exchangeability -> a segment entered while not reporting gets a report with
                   prob. <= alpha, any dependence inside the segment; paper/cpc_theory.md section 3d)
  persistence      log-odds > 0 (MAP decision of the presence chain)
  stop rule CS     report only while the reported place moves with the odometry: no lag k with odometry path
                   <= 3 excl and | ||m_t - m_{t-k}|| - ||o_t - o_{t-k}|| | > excl (only removes reports: keeps every
                   guarantee, Lemma 7; stops reports of a place chain stuck at the map edge before off_d, Prop. 4)
Every constant is in units of the problem (excl = localisation tolerance, H, alpha); nothing is tuned per dataset.
Inputs: `z` = nav_demo --cache arrays (or a dict with the same keys), `b` = nav_rules.base_parts(z)."""
import numpy as np
from hmm_fix import beta_em


def logodds(ll, seqs, p_in=0.01, p_out=0.01):
    """presence log-odds (cpc_presence recursion) for per-frame log LR `ll`"""
    lo = np.zeros(len(ll))
    for idx in seqs:
        pon = 0.5
        for i, t in enumerate(idx):
            pr = pon * (1 - p_out) + (1 - pon) * p_in if i > 0 else 0.5
            l = float(np.clip(np.log(pr / (1 - pr)) + ll[t], -50, 50)); pon = 1 / (1 + np.exp(-l)); lo[t] = l
    return lo


def hyst(lo, seqs, on_thr, keep_thr):
    """report from the frame the log-odds exceeds on_thr (onset) while it stays above keep_thr (Schmitt trigger)"""
    acc = np.zeros(len(lo), bool); on_thr, keep_thr = np.broadcast_to(on_thr, lo.shape), np.broadcast_to(keep_thr, lo.shape)
    for idx in seqs:
        rep = False
        for t in idx: rep = lo[t] > (keep_thr[t] if rep else on_thr[t]); acc[t] = rep
    return acc


def sc_evidence(z, b, alpha=0.05, p_in=0.01, p_out=0.01):
    """CPC-SC: CPC-HMM presence chain + SEGMENT-CALIBRATED ONSET threshold (label-free).
    Query and null use the SAME statistics so that they are exchangeable: the top-1 SelfCal p-value of the half-map test
    (p_q for queries, p_n for the held-out map frames), the anchored R p-value (pR, pRn), and per query condition the
    calibrators a1 = Beta-EM of p_q, a2 = Beta-EM of pR. Per frame LR = 1/2 (e~_top + e_R^(1/H)), gated as CPC-HMM; the
    null uses max(e_top, a1) >= any gated value. kappa (per condition) = conformal (1 - alpha) quantile of the MAX
    presence log-odds over disjoint H-frame segments of the map self-replay null, the chain started at odds 1 (the most a
    non-reporting chain holds; log-odds are monotone in the initial odds). Decision: start reporting when the log-odds
    exceed kappa, keep reporting while they exceed 0. If the query off-map segments are exchangeable with the null
    segments, a segment entered while not reporting contains a report with probability <= alpha, for ANY dependence
    inside the segment (as `certified`). Returns (query log-odds, kappa per frame)."""
    H = b["H"]; fl, ln = z["nchunk_flat"], z["nchunk_len"]; nch = np.split(fl, np.cumsum(ln)[:-1]) if len(ln) else []
    segs = [ch[i:i + H] for ch in nch for i in range(0, len(ch) - H + 1, H)]
    cl = lambda x: np.clip(np.nan_to_num(x, nan=1.0), 1e-6, 1)
    pn, prn, pq, pr = cl(z["p_n"]), cl(z["pRn"]), cl(z["p_q"]), cl(z["pR"])
    MP, est, top = b["MP"], b["est_c"], b["top"]; agree = np.linalg.norm(MP[top] - MP[est], axis=1) <= b["excl"]
    llq, kap = np.zeros(len(pq)), np.zeros(len(pq))
    for cn in sorted(set(z["cond"])):
        m = z["cond"] == cn; a1, _ = beta_em(pq[m]); a2, _ = beta_em(pr[m])
        et = a1 * pq[m] ** (a1 - 1); llq[m] = np.log(0.5 * (np.where(agree[m], et, a1) + (a2 * pr[m] ** (a2 - 1)) ** (1.0 / H)))
        ll = np.log(0.5 * (np.maximum(a1 * pn ** (a1 - 1), a1) + (a2 * prn ** (a2 - 1)) ** (1.0 / H)))
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


def consistency_ok(x_m, o_q, seqs, excl, span=3.0, reported=None, thr=1.0):
    """ODOMETRY-CONSISTENCY of the reported place: False at frame t when, for some lag k whose odometry path stays within
    span * excl, the travelled distance of the reported place differs from the odometry distance by more than excl:
        max_k | ||m_t - m_{t-k}|| - ||o_t - o_{t-k}|| | > excl.
    On the map with correct tracking the MAP moves with the odometry; after leaving the map the place chain (no off-map
    state) either sticks at the map edge (distance ~0 while the odometry moves) or jumps to a look-alike place (distance
    >> odometry). Magnitudes only: invariant to the heading drift of the odometry (NCLT). Used only to STOP reports.
    reported (bool mask): compare only with earlier frames the base rule reported (the reported track): a place chain that
    corrects itself after an unreported stretch is not penalised; one that sticks / jumps while reporting still is."""
    ok = np.ones(len(x_m), bool)
    for idx in seqs:
        if len(idx) < 2: continue
        m, o = x_m[idx].astype(float), o_q[idx].astype(float)
        step = np.linalg.norm(np.diff(o, axis=0), axis=1); K = int(min(len(idx) - 1, np.ceil(span * excl / max(np.median(step), 1e-3))))
        cum = np.r_[0, np.cumsum(step)]; bad = np.zeros(len(idx), bool)
        for k in range(1, K + 1):
            dm = np.linalg.norm(m[k:] - m[:-k], axis=1); do = np.linalg.norm(o[k:] - o[:-k], axis=1)
            win = (cum[k:] - cum[:-k]) <= span * excl
            if reported is not None: win &= reported[idx][:-k]
            bad[k:] |= win & (np.abs(dm - do) > thr * excl)
        ok[idx] = ~bad
    return ok


def cpc_sc_cs(z, b, alpha=0.05, span=3.0):
    """accept mask of CPC-SC+CS and the presence log-odds"""
    lo, kap = sc_evidence(z, b, alpha)
    cs = consistency_ok(b["MP"][b["est_c"]], z["o_q"], b["seqs"], b["excl"], span)
    return hyst(lo, b["seqs"], kap, 0.0) & cs, lo, kap, cs
