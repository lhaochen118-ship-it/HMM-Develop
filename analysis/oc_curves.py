"""Operating curves of every acceptance rule from nav_demo --cache files: is a rule BETTER, or only more conservative?

Each rule family reports when a scalar score exceeds a threshold. The default operating point of each rule is one point
on its curve; sweeping the threshold traces the whole curve, so rules can be compared at MATCHED recall or MATCHED false
reports instead of at their (different) default points. Labels are used here ONLY to evaluate (as everywhere).
  family            score                                   reported place      default point
  TCEmin            P(on) of CPC-HMM +TCEmin               place-chain MAP     P(on) > 0.5
  CPC-HMM           P(on) of CPC-HMM                       place-chain MAP     P(on) > 0.5
  Xu21              1 - P(off-map state) (T, k by labels)  MAP place           off-map state not the argmax
  certified         R_t (ANCH)                             top-1               R_t > conformal map quantile
  SelfCal frame     -log p (per-frame SelfCal-AA)          top-1               p <= alpha
  max-sim           top-1 cosine similarity                top-1               label-calibrated threshold
  Claxton24         MLP P(in tolerance) (labels)           top-1               > 0.5
  SafeVPR           MNN patch score of the top-1 (Boreas)  top-1               Mondrian LTT (labels)
  place conf        place-chain posterior mass near MAP    place-chain MAP     (none; HMM confidence, hmm_diag D1)
Per threshold: recall (correct reports / on-map frames), FL (reports / off-map frames), segment FAR, precision
(correct / all reports), navigation error (Kalman, only on NAV_PTS thresholds: it dominates the cost).
Usage: oc_curves.py <cache_dir> <ds> <desc,...> [--nav-pts 14] [--jobs 8]  -> results/oc_<ds>_<desc>.json"""
import sys, os, json, glob, io, contextlib
import numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nav_demo as N
import nav_rules as NR

from hmm_fix import beta_em
import pcr as PCR

NAV_PTS = int(sys.argv[sys.argv.index("--nav-pts") + 1]) if "--nav-pts" in sys.argv else 14
VARIANTS = "--variants" in sys.argv               # also the candidate fixes (TCE on R only, hysteresis, CPC-SC)
DEFAULTS_ONLY = "--defaults-only" in sys.argv     # only the default operating points (fast screening of variants)
JOBS = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4
OFF_D = {"boreas": 40.0, "cmu": 40.0, "4s": 40.0, "nclt": 20.0, "nord": 10.0, "rc": 40.0}   # map coverage radius (sc_eval CFG off_d)
N_PTS = 48                                       # thresholds per curve (quantiles of the score + the default threshold)


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


def hyst2(start, keep, seqs):
    """onset when `start` (bool), persistence while `keep` (bool)"""
    acc = np.zeros(len(start), bool)
    for idx in seqs:
        rep = False
        for t in idx: rep = keep[t] if rep else start[t]; acc[t] = rep
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


def consistency_ok(x_m, o_q, seqs, excl, span=3.0):
    """ODOMETRY-CONSISTENCY of the reported place: False at frame t when, for some lag k whose odometry path stays within
    span * excl, the travelled distance of the reported place differs from the odometry distance by more than excl:
        max_k | ||m_t - m_{t-k}|| - ||o_t - o_{t-k}|| | > excl.
    On the map with correct tracking the MAP moves with the odometry; after leaving the map the place chain (no off-map
    state) either sticks at the map edge (distance ~0 while the odometry moves) or jumps to a look-alike place (distance
    >> odometry). Magnitudes only: invariant to the heading drift of the odometry (NCLT). Used only to STOP reports."""
    ok = np.ones(len(x_m), bool)
    for idx in seqs:
        if len(idx) < 2: continue
        m, o = x_m[idx].astype(float), o_q[idx].astype(float)
        step = np.linalg.norm(np.diff(o, axis=0), axis=1); K = int(min(len(idx) - 1, np.ceil(span * excl / max(np.median(step), 1e-3))))
        cum = np.r_[0, np.cumsum(step)]; bad = np.zeros(len(idx), bool)
        for k in range(1, K + 1):
            dm = np.linalg.norm(m[k:] - m[:-k], axis=1); do = np.linalg.norm(o[k:] - o[:-k], axis=1)
            win = (cum[k:] - cum[:-k]) <= span * excl
            bad[k:] |= win & (np.abs(dm - do) > excl)
        ok[idx] = ~bad
    return ok


def families(z, b):
    """name -> (score, fix positions, default threshold or None, default accept mask)"""
    MP, est, top = b["MP"], b["est_c"], b["top"]; e1, ea, er = b["e"]; et, eat, ert = b["tce"]
    x_c, x_t = MP[est], MP[top]
    em = (np.minimum(e1, et), np.minimum(ea, eat), np.minimum(er, ert))
    p_t = b["pres"](*em); p_c = b["pres"](e1, ea, er)
    F = {"TCEmin": (p_t, x_c, 0.5, p_t > 0.5), "CPC-HMM": (p_c, x_c, 0.5, p_c > 0.5)}
    if VARIANTS:
        agree = np.linalg.norm(MP[top] - x_c, axis=1) <= b["excl"]
        p_r = b["pres"](e1, ea, np.minimum(er, ert)); F["TCEmin-R"] = (p_r, x_c, 0.5, p_r > 0.5)
        lo_s, kap = sc_evidence(z, b); b["kappa"] = kap
        F["CPC-SC"] = (lo_s - kap, x_c, 0.0, hyst(lo_s, b["seqs"], kap, 0.0))
        F["hyst TCEmin>CPC"] = (None, x_c, None, hyst2(p_t > 0.5, p_c > 0.5, b["seqs"]))
        for tag, span in (("+CS", 3.0), ("+CSd", OFF_D[b["ds"]] / b["excl"])):
            cs = consistency_ok(x_c, z["o_q"], b["seqs"], b["excl"], span)
            for n0 in ("TCEmin", "CPC-HMM", "CPC-SC"):
                sc0, xf0, t0, a0 = F[n0]; F[n0 + tag] = (np.where(cs, sc0, -np.inf), xf0, t0, a0 & cs)
    if "pcr_q" in z.files:                                       # predictive cell-rank evidence (nav_demo --pred)
        agree = np.linalg.norm(MP[top] - x_c, axis=1) <= b["excl"]
        pm, ptc, pmin = PCR.pcr_evalues(z, b["seqs"]); sig = lambda lo: 1 / (1 + np.exp(-lo))
        for name, comps in (("TCEmin+PCR", (np.where(agree, em[0], em[1]), em[2], pmin)),
                            ("CPC+PCR", (np.where(agree, e1, ea), er, pm)),
                            ("TCEmin+PCR(top,PCR)", (np.where(agree, em[0], em[1]), pmin))):
            lo = logodds(np.log(np.maximum(np.mean(comps, 0), 1e-300)), b["seqs"]); F[name] = (sig(lo), x_c, 0.5, lo > 0)
    if "pof_h" in z.files:
        eh = z["e_h"]; jh = np.where(eh >= 0, eh, -1 - eh)
        F["Xu21"] = (1 - z["pof_h"], MP[jh], None, z["acc_h"])
    if "conf_c" in z.files: F["place conf"] = (z["conf_c"], x_c, None, None)
    F["certified"] = (z["Rq"], x_t, float(z["thr"]), z["Rq"] > z["thr"])
    F["SelfCal frame"] = (-np.log(np.maximum(z["p_frame"], 1e-12)), x_t, -np.log(N.A), z["p_frame"] <= N.A)
    F["max-sim"] = (z["maxsim"], x_t, float(z["thr_ms"]), z["maxsim"] > z["thr_ms"])
    bad_top = z["offm"] | (z["err_top"] > b["excl"])
    pc = N.claxton_rule(z["srt10"], z["Smean"], z["Sstd"], z["bsel"], z["good"], bad_top, int(z["seed"]), proba=True)
    F["Claxton24"] = (pc, x_t, 0.5, pc > 0.5)
    if "mtop" in z.files: F["SafeVPR"] = (z["mtop"], x_t, None, None)
    return F


def point(acc, xf, z, b, cx, nav):
    err_f = np.linalg.norm(xf - z["q_pos"], axis=1); inm, offm = z["inm"], z["offm"]
    gd = inm & (err_f <= b["excl"]); r = N.rule_metrics(acc, gd, inm, offm, b["seqs"], b["H"])
    n = int(acc.sum()); r["precision"] = float((acc & gd).sum() / max(n, 1)); r["frac_reported"] = float(acc.mean())
    r["wrong_rate"] = float((acc & (offm | (err_f > b["excl"]))).sum() / len(acc))
    if nav:
        e = N.track(acc, xf, cx["q_pos"], cx["o_q"], cx["real"], cx["q_seqs"], cx["hz"], cx["seed"], cx["head"])
        r["err_mean"], r["err_p95"] = float(np.nanmean(e)), float(np.nanpercentile(e, 95))
    return r


def one(args):
    f, ds = args
    z = np.load(f, allow_pickle=True); b = NR.base_parts(z); b["ds"] = ds.split(":")[0]
    cx = dict(q_pos=z["q_pos"], o_q=z["o_q"], real=bool(z["real"]), q_seqs=b["seqs"], hz=list(z["hz"]), seed=int(z["seed"]),
              head=ds == "nclt")
    out = {"seed": int(z["seed"]), "families": {}}
    with contextlib.redirect_stdout(io.StringIO()):
        F = families(z, b)
    for name, (sc, xf, thr0, acc0) in F.items():
        if sc is None or DEFAULTS_ONLY:                           # rule without a scalar score: default point only
            if acc0 is not None: out["families"][name] = {"curve": [], "default": point(acc0, xf, z, b, cx, True)}
            continue
        sc = np.nan_to_num(sc, nan=-np.inf); fin = sc[np.isfinite(sc)]
        th = np.unique(np.quantile(fin, np.linspace(0, 1, N_PTS))) if len(fin) else np.array([np.inf])
        th = np.unique(np.r_[th, [thr0] if thr0 is not None else []]); th = th[np.argsort(th)]
        nav_idx = set(np.unique(np.linspace(0, len(th) - 1, NAV_PTS).round().astype(int)).tolist())
        curve = []
        for i, t in enumerate(th):
            r = point(sc > t if i > 0 else sc >= t, xf, z, b, cx, i in nav_idx); r["thr"] = float(t); curve.append(r)
        fam = {"curve": curve}
        if acc0 is not None: fam["default"] = point(acc0, xf, z, b, cx, True)
        out["families"][name] = fam
    og = point(z["good"], b["MP"][b["top"]], z, b, cx, True); out["oracle"] = og
    return os.path.basename(f), out


def main():
    cdir, ds, descs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    for desc in descs:
        files = sorted(glob.glob(os.path.join(cdir, f"navcache_{ds.replace(':', '_')}_{desc}_s*.npz")))
        if not files: continue
        with Pool(min(JOBS, len(files))) as p: res = dict(p.map(one, [(f, ds) for f in files]))
        os.makedirs("results", exist_ok=True)
        json.dump({"ds": ds, "desc": desc, "runs": res}, open(f"results/oc_{ds.replace(':', '_')}_{desc}.json", "w"), default=float)
        print(f"{ds}/{desc}: {len(res)} runs", flush=True)


if __name__ == "__main__":
    main()
