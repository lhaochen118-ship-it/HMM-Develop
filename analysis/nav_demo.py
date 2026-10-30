"""Navigation demo: drifting odometry + VPR position fixes on a map with holes (as exp12, branch claude/selfcal-seq),
with the certified sequential acceptance rule of cert_seq.py.

A random 30 % of the map's blocks is removed (the robot drives through unmapped areas). Every acceptance rule is fitted
on the REMAINING map only, without labels unless stated:
  accept all            every top-1 match is a fix
  label threshold       max-sim threshold = conformal quantile of LABELLED off-map queries of the 2 most benign conditions
  SelfCal frame         per-frame SelfCal-AA p <= alpha
  certified (ours)      ANCH sequence statistic > conformal quantile of held-out map segments (H frames, Lmax = H)
  oracle                only correct matches
A position Kalman filter integrates the odometry (simulated: scale error, heading random walk, noise; 4Seasons: real
VIO) and fuses each accepted fix (sigma 5 m). Reported: wrong fixes, correct fixes, error mean/median/p95 and the share
of frames with error > rho.  Usage: nav_demo.py <dump> <cmu|nord|4s:<scene>> <desc> [seeds=3] [H=10]"""
import sys, os, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V, selfcal as SC
from sc_eval import CFG
from cert_seq import running, chunks, odometry_sim, odometry_real
from hmm_eval import Filter
from hmm_diag import DiagFilter
from hmm_fix import beta_em

A, SIG_FIX, DROP = 0.05, 5.0, 0.3
DUMP = "--dump" in sys.argv                    # also save per-frame arrays (results/navframes_<ds>_<desc>_s<seed>.npz)
if DUMP: sys.argv.remove("--dump")
RHOS = []                                      # --rhos 0.03,0.3: extra ghost-gate floors (sensitivity of rho)
if "--rhos" in sys.argv:
    i = sys.argv.index("--rhos"); RHOS = [float(x) for x in sys.argv[i + 1].split(",")]; del sys.argv[i:i + 2]
SAFEVPR = None                                 # --safevpr <dir>: safevpr_<ds>_p*.npz (MNN patch scores, safevpr_mnn.py) -> SafeVPR baseline
if "--safevpr" in sys.argv:
    i = sys.argv.index("--safevpr"); SAFEVPR = sys.argv[i + 1]; del sys.argv[i:i + 2]
CACHE = "--cache" in sys.argv                  # --cache: save results/navcache_<ds>_<desc>_s<seed>.npz (reusable inputs of every rule)
if CACHE: sys.argv.remove("--cache")
SEED0 = 0                                      # --seed0 k: run seeds k .. k+seeds-1 (results file gets the suffix _s<k>)
if "--seed0" in sys.argv:
    i = sys.argv.index("--seed0"); SEED0 = int(sys.argv[i + 1]); del sys.argv[i:i + 2]
KAPPA = 0.05                                   # ghost position uncertainty growth per metre of odometry (as the nav filter)


def cpc_joint(Fp, rel, U, e_top, e_a, e_r, top, excl_nbr, p_in=0.01, p_out=0.01, gate="pred", ghost=True, s0=25.0, eps=1e-4, couple=True, rho=0.1):
    """CPC-HMM with the place and presence chains run JOINTLY on one sequence (needed for the two couplings below).
    b_t = P(x_t | on_t): place chain without off-map state (DiagFilter transitions, affine-invariant emission `rel`).
    Couplings (both label-free; both keep LR_t an e-value, so the ARL0 bound of the presence chain is unchanged):
      * off->on re-entry: P(x_t | on_t) = [P(on_{t-1})(1-p_out) K*b_{t-1} + P(off_{t-1}) p_in G_t] / norm, where G_t is the
        DEAD-RECKONED OFF-MAP STATE (ghost): position of the last reported fix propagated by odometry, sd s0 + KAPPA * path
        length (ghost=True); ghost=False -> G uniform (position-less off-map state, as Xu'21).
      * gate of the top-1 e-value: 'post' = 1[top-1 within excl of the posterior MAP] (CPC-HMM), 'pred' = g_t = PREDICTED
        place mass b_pred within excl of the top-1 (F_{t-1}-measurable kernel); e~ = a + g (e_top - a) <= e_top pointwise;
        'ghost' = 'post' x, while no place is reported (P(on_{t-1}) <= 1/2), the DEAD-RECKONING gate g = exp(-d^2 / 2 s^2),
        d = |m_top - ghost|: an off-map stretch cannot be reported at a place the odometry says the robot cannot be;
        g is floored at rho (prior that the ghost is wrong, 0.1) so evidence still re-localises after a wrong report
        (rho = 0.01 locks out on Nordland after one wrong report: recall 0.74 -> 0.31; rho = 0.1 keeps the Boreas gain).
    couple=False: place chain exactly as CPC-HMM (b_pred = K*b), only the gate changes.
    e_top = a p^(a-1), e_a = a (gate-off value), e_r = (e^R)^(1/H). Returns (est, pon)."""
    L, n = rel.shape; pos = Fp.pos; b = np.full(n, 1.0 / n); pon = 0.5
    est = np.empty(L, int); out = np.empty(L); mu, s, have = None, s0, False
    for t in range(L):
        if t > 0:
            w = np.exp(-0.5 * ((Fp.D - U[t][None]) ** 2).sum(1) / Fp.sigma ** 2)
            z = np.bincount(Fp.ii, w, n); z[z == 0] = 1
            nb = np.bincount(Fp.jj, b[Fp.ii] * w / z[Fp.ii], n); nb /= nb.sum()
            w_on, w_off = pon * (1 - p_out), (1 - pon) * p_in
            if have:
                mu = mu + U[t]; s = s + KAPPA * np.linalg.norm(U[t])
            if ghost and have:
                G = np.exp(-0.5 * ((pos - mu) ** 2).sum(1) / s ** 2); sg = G.sum()
                G = G / sg if sg > 1e-12 else np.full(n, 1.0 / n)
            else: G = np.full(n, 1.0 / n)
            b = (w_on * nb + w_off * G) / (w_on + w_off) if couple else nb; b = (1 - eps) * b + eps / n
            pr = w_on + w_off
        else: pr = 0.5
        g = b[excl_nbr[top[t]]].sum() if gate == "pred" else None
        b = b * np.exp(rel[t] - rel[t].max()); b /= b.sum(); j = int(b.argmax()); est[t] = j
        if gate in ("post", "ghost"): g = float(np.linalg.norm(pos[top[t]] - pos[j]) <= Fp.far)
        if gate == "ghost" and have and pon <= 0.5:                   # floor rho: prior that the ghost itself is wrong (lock-out escape)
            g *= (1 - rho) * float(np.exp(-0.5 * ((pos[top[t]] - mu) ** 2).sum() / s ** 2)) + rho
        ee = 0.5 * (e_a[t] + min(g, 1.0) * (e_top[t] - e_a[t]) + e_r[t])
        lo = np.log(pr / (1 - pr)) + np.log(max(ee, 1e-300)); pon = 1 / (1 + np.exp(-np.clip(lo, -50, 50))); out[t] = pon
        if pon > 0.5: mu, s, have = pos[j].astype(float), s0, True        # ghost = last reported fix (+ odometry while off)
    return est, out


def cpc_presence(est, pos, top, e_top, e_a, e_r, seqs, excl, gate="post", rho=0.1, s0=25.0, U=None, p_in=0.01, p_out=0.01):
    """FAST path of cpc_joint for couple=False: the place chain does not depend on the presence chain then, so its MAP
    (est, computed once) is reused and only the scalar presence recursion runs per variant (identical output)."""
    pon_all = np.zeros(len(e_top))
    for idx in seqs:
        pon, have, mu, s = 0.5, False, None, s0
        for i, t in enumerate(idx):
            if i > 0:
                if have: mu = mu + U[t]; s = s + KAPPA * np.linalg.norm(U[t])
                pr = pon * (1 - p_out) + (1 - pon) * p_in
            else: pr = 0.5
            j = est[t]; g = float(np.linalg.norm(pos[top[t]] - pos[j]) <= excl)
            if gate == "ghost" and have and pon <= 0.5:
                g *= (1 - rho) * float(np.exp(-0.5 * ((pos[top[t]] - mu) ** 2).sum() / s ** 2)) + rho
            ee = 0.5 * (e_a[t] + min(g, 1.0) * (e_top[t] - e_a[t]) + e_r[t])
            lo = np.log(pr / (1 - pr)) + np.log(max(ee, 1e-300)); pon = 1 / (1 + np.exp(-np.clip(lo, -50, 50))); pon_all[t] = pon
            if pon > 0.5: mu, s, have = pos[j].astype(float), s0, True
    return pon_all


def tce(null_chunks, p_null, r_null, q_seqs, p_q, r_q, nb_p=6, nb_r=4, min_n=30):
    """TRANSITION-CALIBRATED conformal p-values (Mondrian over the previous evidence state), from map self-replay.
    Null pool: consecutive held-out map frames (s-1, s) of the map traversal (off-map by construction). The cell of a
    frame is Z = (bin of log p_{s-1}, bin of log pR_{s-1}) (F_{s-1}-measurable; 'start' for the first frame of a run).
    Query frame t in cell Z_t: u_t = (1 + #{null p_s <= p_t : Z_s = Z_t}) / (1 + n_Z), same for pR. Under transition
    exchangeability (query off-map transitions exchangeable with null transitions within a cell) and first-order Markov
    sufficiency of Z, u_t is super-uniform CONDITIONALLY on the past -> a p^(a-1) of it is a conditional e-value, so the
    Shiryaev-Roberts bound of the presence chain holds under temporal dependence (coherent aliasing no longer
    accumulates: given a mid p-value last frame, another mid p-value is typical under the null).
    Sparse cells (< min_n pairs) fall back to the p-only cell, then to the marginal pool."""
    lp = lambda x: np.log(np.clip(x, 1e-9, 1))
    allp = np.concatenate([p_null[ch] for ch in null_chunks if len(ch)]); allr = np.concatenate([r_null[ch] for ch in null_chunks if len(ch)])
    ep_ = np.quantile(lp(allp), np.linspace(0, 1, nb_p + 1)[1:-1]); er_ = np.quantile(lp(allr), np.linspace(0, 1, nb_r + 1)[1:-1])
    cell = lambda pp, rr: (int(np.searchsorted(ep_, lp(pp))), int(np.searchsorted(er_, lp(rr))))
    pool = {}
    for ch in null_chunks:
        for i in range(len(ch)):
            z = (-1, -1) if i == 0 else cell(p_null[ch[i - 1]], r_null[ch[i - 1]])
            for key in (z, (z[0], -2), (-2, -2)):
                pool.setdefault(key, ([], []))[0].append(p_null[ch[i]]); pool[key][1].append(r_null[ch[i]])
    pool = {k: (np.sort(v[0]), np.sort(v[1])) for k, v in pool.items()}
    u1, u2, nz = np.ones(len(p_q)), np.ones(len(p_q)), np.zeros(len(p_q), int)
    for idx in q_seqs:
        for i, t in enumerate(idx):
            z = (-1, -1) if i == 0 else cell(p_q[idx[i - 1]], r_q[idx[i - 1]])
            for key in (z, (z[0], -2), (-2, -2)):
                if key in pool and len(pool[key][0]) >= min_n: break
            a1, a2 = pool[key]; n = len(a1)
            u1[t] = (1 + np.searchsorted(a1, p_q[t], side="right")) / (1 + n); u2[t] = (1 + np.searchsorted(a2, r_q[t], side="right")) / (1 + n); nz[t] = n
    return u1, u2, nz


def rule_metrics(acc, ok_on, inm, offm, seqs, H, pon=None):
    """hmm_fix-style metrics for any acceptance rule: recall (correct reports / on-map frames), FL (reports / off-map
    frames), segment FAR (share of disjoint H-frame off-map segments with >= 1 report), ARL0 (off-map frames per false
    onset), re-entry delay (frames from re-entering the map to the first correct report), ECE of P(on) when available"""
    onsets, segs, seg_bad, delays = 0, 0, 0, []
    for idx in seqs:
        rp, of, on, gk = acc[idx], offm[idx], inm[idx], (acc & ok_on)[idx]
        onsets += int((of & rp & ~np.r_[False, rp[:-1]]).sum())
        i = 0
        while i < len(idx):
            if of[i]:
                j = i
                while j < len(idx) and of[j]: j += 1
                for k in range(i, j - H + 1, H): segs += 1; seg_bad += int(rp[k:k + H].any())
                k = j
                while k < len(idx) and not on[k] and not of[k]: k += 1
                if k < len(idx) and on[k]:
                    e = k
                    while e < len(idx) and not of[e]: e += 1
                    g = np.flatnonzero(gk[k:e]); delays.append(int(g[0]) if len(g) else e - k)
                i = j
            else: i += 1
    r = dict(recall=float((acc & ok_on)[inm].mean()), FL=float(acc[offm].mean()), seg_FAR=float(seg_bad / max(segs, 1)), n_seg=segs,
             ARL0=float(offm.sum() / max(onsets, 1)), reentry_delay=float(np.mean(delays)) if delays else float("nan"))
    if pon is not None: r["ECE"] = float(V.ece(pon[inm], ok_on[inm], 10)); r["overconf"] = float(pon[inm].mean() - ok_on[inm].mean())
    return r


def ltt_threshold(score, bad, alpha=0.05, delta=0.1):
    """Learn-Then-Test (fixed sequence, binomial p-values): the most permissive threshold lam (from strict to loose) whose
    accepted set {score >= lam} has FDR <= alpha with confidence 1 - delta on the (labelled) calibration frames.
    The sequence starts at the first threshold whose accepted set can be rejected at all (n >= log delta / log(1-alpha),
    i.e. zero errors would pass): the order depends on the scores only, not on the labels, so validity is kept; starting
    at n = 1 stops the sequence immediately (0.95 > delta) and accepts nothing"""
    from scipy.stats import binom
    lam = np.inf; n_min = int(np.ceil(np.log(delta) / np.log(1 - alpha)))
    for l in np.unique(score)[::-1]:
        a = score >= l; n = int(a.sum()); f = int((a & bad).sum())
        if n < n_min: continue
        if binom.cdf(f, n, alpha) > delta: break
        lam = l
    return lam


def safevpr_rule(mnn_top, cos_top, calib, bad, nbins=3, alpha=0.05, delta=0.1):
    """SafeVPR (Sier et al. 2026): Mondrian conformal LTT on the MNN patch score, one threshold per bin of the global
    cosine score (Bonferroni delta / nbins), calibrated WITH LABELS on `calib` frames"""
    edges = np.quantile(cos_top[calib], np.linspace(0, 1, nbins + 1)[1:-1]); b = np.searchsorted(edges, cos_top)
    acc = np.zeros(len(mnn_top), bool)
    for k in range(nbins):
        m = calib & (b == k)
        lam = ltt_threshold(mnn_top[m], bad[m], alpha, delta / nbins) if m.any() else np.inf
        acc |= (b == k) & (mnn_top >= lam)
    return acc


def claxton_rule(srt10, Smean, Sstd, calib, good, bad, seed):
    """Claxton et al. RA-L'24 style integrity monitor: MLP on similarity-profile features, trained WITH LABELS on the
    `calib` frames (in tolerance vs not), accept when P(in tolerance) > 0.5"""
    from sklearn.neural_network import MLPClassifier
    s1 = srt10[:, 0]
    X = np.stack([s1, s1 - srt10[:, 1], s1 - srt10[:, 4], s1 - srt10[:, 9], s1 - Smean, Sstd], 1)
    X = (X - X[calib].mean(0)) / (X[calib].std(0) + 1e-9); tr = calib & (good | bad)
    clf = MLPClassifier((32, 16), max_iter=500, random_state=seed).fit(X[tr], good[tr])
    return clf.predict_proba(X)[:, 1] > 0.5


def track_head(acc, xf, q_pos, o_q, q_seqs, sig_th=0.004):
    """EKF with a heading-offset state (x, y, theta): odometry increments are rotated by theta, theta is estimated from
    the accepted fixes (sigma SIG_FIX). For robots whose odometry heading drifts (NCLT Segway: 10-25 deg per session),
    which a position-only filter turns into a steady lag behind the fixes. sig_th: heading random walk, rad / sqrt(m)."""
    est = np.full_like(q_pos, np.nan); I3 = np.eye(3); Hm = np.eye(2, 3); Rf = SIG_FIX ** 2 * np.eye(2)
    for idx in q_seqs:
        m = np.r_[q_pos[idx[0]], 0.0]; P = np.diag([1.0, 1.0, np.deg2rad(5) ** 2]); est[idx[0]] = m[:2]
        for a, b in zip(idx[:-1], idx[1:]):
            u = o_q[b] - o_q[a]; c, s_ = np.cos(m[2]), np.sin(m[2]); Ru = np.array([c * u[0] - s_ * u[1], s_ * u[0] + c * u[1]])
            m[:2] += Ru; F = I3.copy(); F[0, 2], F[1, 2] = -Ru[1], Ru[0]; L = np.linalg.norm(u)
            P = F @ P @ F.T + np.diag([(0.05 * L) ** 2 + 1e-4, (0.05 * L) ** 2 + 1e-4, sig_th ** 2 * L + 1e-8])
            if acc[b]:
                K = P @ Hm.T @ np.linalg.inv(Hm @ P @ Hm.T + Rf); m = m + K @ (xf[b] - m[:2]); P = (I3 - K @ Hm) @ P
            est[b] = m[:2]
    return np.linalg.norm(est - q_pos, axis=1)


def track(acc, xf, q_pos, o_q, real, q_seqs, hz, seed, head=False):
    """position Kalman filter: odometry (real increments, or simulated: scale error, heading random walk, noise) + accepted
    fixes (sigma SIG_FIX); returns the per-frame position error. head=True: EKF with a heading-offset state (track_head)"""
    if head and real and q_pos.shape[1] == 2: return track_head(acc, xf, q_pos, o_q, q_seqs)
    r = np.random.default_rng(seed + 7); est = np.full_like(q_pos, np.nan)
    for idx in q_seqs:
        x = q_pos[idx[0]].copy(); P = 1.0; est[idx[0]] = x; thh = 0.0; sc = 1 + r.normal(0, 0.03)
        for a, b in zip(idx[:-1], idx[1:]):
            if real: u = o_q[b] - o_q[a]                                          # real VIO / wheel+gyro increment
            else:
                d = q_pos[b] - q_pos[a]; u = d * sc; thh += r.normal(0, np.deg2rad(0.3))
                if len(hz) == 2:
                    R2 = np.array([[np.cos(thh), -np.sin(thh)], [np.sin(thh), np.cos(thh)]]); u[hz] = R2 @ u[hz]
                u = u + r.normal(0, 0.02 * np.linalg.norm(d) / np.sqrt(len(d)) + 1e-3, len(d))
            x = x + u; P = P + (0.05 * np.linalg.norm(u)) ** 2 + 1e-4
            if acc[b]:
                K = P / (P + SIG_FIX ** 2); x = x + K * (xf[b] - x); P = (1 - K) * P
            est[b] = x
    return np.linalg.norm(est - q_pos, axis=1)


def evaluate(rules, xfs, pons, cx, tag):
    """navigation + hmm_fix-style metrics of every rule. rules: name -> accept mask; xfs: name -> fix positions;
    pons: name -> P(on) (ECE) or None; cx: context dict (q_pos, o_q, real, q_seqs, hz, seed, excl, inm, offm, H)"""
    res = {}
    for name, acc in rules.items():
        xf = xfs[name]; e = track(acc, xf, cx["q_pos"], cx["o_q"], cx["real"], cx["q_seqs"], cx["hz"], cx["seed"], cx.get("head", False))
        err_f = np.linalg.norm(xf - cx["q_pos"], axis=1); inm, offm = cx["inm"], cx["offm"]
        gd, bd = inm & (err_f <= cx["excl"]), offm | (err_f > cx["excl"])
        rr = dict(wrong_fixes=int((acc & bd).sum()), correct_fixes=int((acc & gd).sum()), FAR_offmap=float(acc[offm].mean()),
                  err_mean=float(np.nanmean(e)), err_median=float(np.nanmedian(e)), err_p95=float(np.nanpercentile(e, 95)),
                  frac_gt_rho=float(np.nanmean(e > cx["excl"])))
        rr.update(rule_metrics(acc, gd, inm, offm, cx["q_seqs"], cx["H"], pons.get(name))); res[name] = rr
        print(f"{tag} {name:17s} wrong {rr['wrong_fixes']:6d} correct {rr['correct_fixes']:6d} offFAR {rr['FAR_offmap']:.3f} "
              f"| err mean {rr['err_mean']:8.1f} med {rr['err_median']:6.1f} p95 {rr['err_p95']:8.1f} >rho {rr['frac_gt_rho']:.3f} "
              f"| recall {rr['recall']:.3f} segFAR {rr['seg_FAR']:.3f} ARL0 {rr['ARL0']:.0f} ECE {rr.get('ECE', float('nan')):.3f}", flush=True)
    return res


def dr_gate(acc, xf, seqs, U, s0):
    """fairness baseline: the same dead-reckoning gate applied post hoc to any rule's fixes. A fix that STARTS a reporting
    streak (previous frame not reported) is kept only if it lies within 2 s of the ghost (last kept fix + odometry,
    s = s0 + KAPPA * path since that fix)."""
    out = np.zeros(len(acc), bool)
    for idx in seqs:
        have, prev = False, False
        for t in idx:
            if have: mu = mu + U[t]; s = s + KAPPA * np.linalg.norm(U[t])
            ok = acc[t] and (prev or not have or np.linalg.norm(xf[t] - mu) <= 2 * s)
            if ok: mu, s, have = xf[t].astype(float), s0, True
            out[t] = prev = ok
    return out


def main():
    dump, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3]
    seeds = int(sys.argv[4]) if len(sys.argv) > 4 else 3; H = int(sys.argv[5]) if len(sys.argv) > 5 else 10
    if ds.startswith("4s:"): ep = V.load_4seasons(dump, desc, ds[3:]); c = CFG["cmu"]
    elif ds == "boreas": ep = V.load_boreas(dump, desc); c = CFG["cmu"]
    else: ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
    q_sid, q_k, m_sid, m_k = V.frame_order(dump, ds, ep, desc)
    nord = ds in ("nord", "nordw"); rho_o = 1.0 if nord else 5.0
    q_seqs = [np.where(q_sid == s)[0][np.argsort(q_k[q_sid == s])] for s in np.unique(q_sid)]
    cond = np.asarray(ep.q_cond).astype(str); conds = sorted(set(cond)); q = ep.q.astype(np.float32)
    out = {"ds": ds, "desc": desc, "H": H, "runs": []}
    for seed in range(SEED0, SEED0 + seeds):
        rng = np.random.default_rng(seed); bid0, _ = V.map_cells(ep.m_pos, c["block"]); ub = np.unique(bid0)
        keep = ~np.isin(bid0, rng.choice(ub, int(round((0.0 if ds == "nclt" else DROP) * len(ub))), replace=False))   # NCLT: natural off-map, no holes
        M, MP = ep.m[keep].astype(np.float32), ep.m_pos[keep]
        d_map, _ = cKDTree(MP).query(ep.q_pos); inm, offm = d_map <= c["in_d"], d_map > c["off_d"]
        nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True); mu = M.mean(0, keepdims=True); Mc = nrm(M - mu); qc = nrm(q - mu)
        args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
        Nr, Nc = SC.map_null(M, MP, *args, stride=1), SC.map_null(Mc, MP, *args, stride=1)
        Fr, Fc = SC.qm_stats(q, M, MP, c["cell"], c["excl"], c["k"]), SC.qm_stats(qc, Mc, MP, c["cell"], c["excl"], c["k"])
        top = Fr["top"].astype(int); x_fix = MP[top]; err_top = np.linalg.norm(x_fix - ep.q_pos, axis=1)
        good = inm & (err_top <= c["excl"]); bad = offm | (err_top > c["excl"])
        bidM, _ = V.map_cells(MP, c["block"]); half = bidM % 2 == 0
        sub = lambda d, m: {kk: np.where(m, v, np.nan) for kk, v in d.items()}
        p_frame = SC.SelfCalTest(SC.pack(Nr, Nc)).pvalue(**SC.pack(Fr, Fc))
        th = SC.SelfCalTest(SC.pack(sub(Nr, half), sub(Nc, half)))
        p_q, p_n = th.pvalue(**SC.pack(Fr, Fc)), th.pvalue(**SC.pack(Nr, Nc))
        # map pseudo-sequences of the reduced map (map rows of `keep`, in their original order)
        kidx = np.flatnonzero(keep); m_sid_k, m_k_k = m_sid[keep], m_k[keep]
        m_seqs = [np.where(m_sid_k == s)[0][np.argsort(m_k_k[m_sid_k == s])] for s in np.unique(m_sid_k)]
        o_m = odometry_sim(MP, m_sid_k, m_k_k, rng)
        real = hasattr(ep, "q_vio") or hasattr(ep, "q_dmi")
        o_q = odometry_real(ep, q_sid, q_k) if real else odometry_sim(ep.q_pos, q_sid, q_k, rng)
        null_ok = np.isfinite(Nr["maxsim"]) & np.isfinite(Nc["z_far"]) & ~half
        Rn = np.full(len(MP), np.nan)
        for order in m_seqs:
            for ch in chunks(order, null_ok, bidM):
                # map rows must be split into contiguous chunks also where dropped blocks interrupt the traversal
                Rn[ch] = running(p_n, Nr["top"], np.array(ch), o_m, MP, "ANCH", c["excl"], rho_o, H)
        nseg = [s for order in m_seqs for ch in chunks(order, null_ok, bidM) for s in (ch[i:i + H] for i in range(0, len(ch) - H + 1, H))]
        ns = np.sort([Rn[s].max() for s in nseg]); kq = int(np.ceil((1 - A) * (len(ns) + 1))); thr = ns[kq - 1] if kq <= len(ns) else np.inf
        Rq = np.full(len(q), np.nan)
        for order in q_seqs: Rq[order] = running(p_q, Fr["top"], order, o_q, MP, "ANCH", c["excl"], rho_o, H)
        r1 = {x: good[(cond == x) & inm].mean() for x in conds}; benign = sorted(conds, key=lambda x: -r1[x])[:2]
        cal = np.sort(Fr["maxsim"][offm & np.isin(cond, benign)]); kl = int(np.ceil((len(cal) + 1) * (1 - A)))
        thr_ms = cal[min(len(cal) - 1, kl - 1)] if len(cal) else np.inf
        # HMM with an off-map state (Xu et al. RA-L'21 style): emission exp(s/T), off-map emission exp(s_(k)/T); fixes = MAP
        # place whenever the off-map state is not the argmax. T, k tuned WITH LABELS on the benign conditions: most correct
        # fixes subject to off-map FAR <= alpha there (the label-calibrated operating point of that family).
        S = q @ M.T; srt = -np.sort(-S, 1); smax = S.max(1, keepdims=True)
        U = np.zeros_like(ep.q_pos)
        for idx in q_seqs: U[idx[1:]] = np.diff(o_q[idx], axis=0)
        Fh = Filter(MP, 1.0 if nord else 2.0, 6.0 if nord else 15.0, conf_r=c["tol"][0])
        def hmm_fix(T, kk, subset):
            est = np.full(len(q), -1)
            for idx in q_seqs:
                if not subset[idx].any(): continue
                e, _ = Fh.run(np.exp((S[idx] - smax[idx]) / T), U[idx], np.exp((srt[idx, kk - 1] - smax[idx, 0]) / T)); est[idx] = e
            return est
        bsel = np.isin(cond, benign); best = None
        for T in (0.01, 0.02, 0.05):
            for kk in (5, 10, 20):
                e = hmm_fix(T, kk, bsel); acc_b = (e >= 0) & bsel
                far_b = acc_b[offm & bsel].mean() if (offm & bsel).any() else 0
                ok_b = (acc_b & (np.linalg.norm(MP[np.maximum(e, 0)] - ep.q_pos, axis=1) <= c["excl"]))[bsel].sum()
                if far_b <= A and (best is None or ok_b > best[0]): best = (ok_b, T, kk)
        best = best or (0, 0.01, 20)
        e_h = hmm_fix(best[1], best[2], np.ones(len(q), bool)); acc_h = e_h >= 0
        x_hmm = MP[np.maximum(e_h, 0)]
        # CPC-HMM (hmm_fix.py, method fac_anchT_mix): place chain with affine-invariant emission + presence chain fed by the
        # mixed belief-independent e-value 1/2 (e_top + e_R^(1/H)); fixes = place MAP whenever P(on) > 0.5 (label-free)
        zf = Nc["z_far"][np.isfinite(Nc["z_far"])]; tau = float(zf.std() * np.sqrt(6) / np.pi)
        sdf = np.maximum(np.nan_to_num(Fr["sd_far"], nan=np.nanmedian(Fr["sd_far"])), 1e-4)
        rel = (S - smax) / (tau * sdf[:, None])
        Fp = DiagFilter(MP, 1.0 if nord else 2.0, 6.0 if nord else 15.0, c["tol"][0], c["excl"])
        est_c = np.zeros(len(q), int)
        for idx in q_seqs: est_c[idx], _, _, _ = Fp.run(rel[idx], U[idx])
        lam = np.zeros(len(q)); loga = np.zeros(len(q)); e_R = np.zeros(len(q))
        # CPC-HMM presence e-value: the R null uses NOISE-FREE map odometry (exact map poses). Adding independent symmetric
        # unimodal noise to the displacements can only lower P(|dx - do| <= rho_o) (Anderson), so this null dominates R of
        # off-map queries under any real odometry -> super-uniform p^R (the simulated-noise null was sub-uniform on Boreas/4S)
        Rn0 = np.full(len(MP), np.nan)
        for order in m_seqs:
            for ch in chunks(order, null_ok, bidM): Rn0[ch] = running(p_n, Nr["top"], np.array(ch), MP.astype(float), MP, "ANCH", c["excl"], rho_o, H)
        rn = np.sort(Rn0[np.isfinite(Rn0)]); pR = (1 + len(rn) - np.searchsorted(rn, Rq, side="left")) / (1 + len(rn))
        for cn in conds:
            m = cond == cn; a1, _ = beta_em(p_frame[m]); a2, _ = beta_em(pR[m])
            lam[m] = np.log(a1) + (a1 - 1) * np.log(np.clip(p_frame[m], 1e-6, 1)); loga[m] = np.log(a1)
            e_R[m] = a2 * np.clip(pR[m], 1e-6, 1) ** (a2 - 1)
        agree = np.linalg.norm(MP[top] - MP[est_c], axis=1) <= c["excl"]
        ee = 0.5 * (np.exp(np.where(agree, lam, loga)) + e_R ** (1.0 / H)); ll = np.log(np.maximum(ee, 1e-300))
        def presence(p_in, p_out):
            pon = np.zeros(len(q))
            for idx in q_seqs:
                pr = 0.5
                for t in idx:
                    pr = (1 - p_out) * pr + p_in * (1 - pr); lo = np.log(pr / (1 - pr)) + ll[t]; pr = 1 / (1 + np.exp(-np.clip(lo, -50, 50))); pon[t] = pr
            return pon
        # p_in sets the false-onset bound ARL0 >= (1-p_in)/p_in (needs p_out >= p_in); p_out sets the exit lag after leaving
        # the map, ~ log((1-p_out)/p_out) / |E0 log LR| (the dominant source of off-map fixes)
        pon = presence(0.01, 0.01); acc_c = pon > 0.5; x_cpc = MP[est_c]
        acc_po = {po: presence(0.01, po) > 0.5 for po in (0.05, 0.1, 0.2)}
        # joint CPC-HMM variants (cpc_joint): predictive gate (PG) and/or dead-reckoned off-map state (DR)
        e_top1, e_a1, e_r1 = np.exp(lam), np.exp(loga), e_R ** (1.0 / H)
        nbr_x = cKDTree(MP).query_ball_point(MP, c["excl"]); joint = {}
        for jn, gt, gh, cp, rh in (("CPC-HMM +GG", "ghost", False, False, 0.1), ("CPC-HMM +GG(rho=.01)", "ghost", False, False, 0.01),
                                   *((f"CPC-HMM +GG(rho={r:g})", "ghost", False, False, r) for r in RHOS)):
            if not cp and not gh:                                       # fast path: place chain = est_c (identical)
                pj = cpc_presence(est_c, MP, top, e_top1, e_a1, e_r1, q_seqs, c["excl"], gate=gt, rho=rh, s0=c["excl"], U=U); ej = est_c
            else:
                ej, pj = np.zeros(len(q), int), np.zeros(len(q))
                for idx in q_seqs:
                    ej[idx], pj[idx] = cpc_joint(Fp, rel[idx], U[idx], e_top1[idx], e_a1[idx], e_r1[idx], top[idx], nbr_x, gate=gt, ghost=gh, s0=c["excl"], couple=cp, rho=rh)
            joint[jn] = (pj > 0.5, MP[ej], pj)
        # TCE (transition-calibrated e-values from map self-replay) fed to the same CPC-HMM (post gate) and to +GG
        nchunks = [np.array(ch) for order in m_seqs for ch in chunks(order, null_ok, bidM) if len(ch) >= 2]
        pRn = (1 + len(rn) - np.searchsorted(rn, Rn0, side="left")) / (1 + len(rn))
        u1, u2, _ = tce(nchunks, np.nan_to_num(p_n, nan=1.0), np.nan_to_num(pRn, nan=1.0), q_seqs, p_q, pR)
        et_t, ea_t, er_t = np.ones(len(q)), np.ones(len(q)), np.ones(len(q))
        for cn in conds:
            m = cond == cn; b1, _ = beta_em(u1[m]); b2, _ = beta_em(u2[m])
            et_t[m] = b1 * np.clip(u1[m], 1e-6, 1) ** (b1 - 1); ea_t[m] = b1; er_t[m] = b2 * np.clip(u2[m], 1e-6, 1) ** (b2 - 1)
        # TCEmin: componentwise min of the marginal (CPC) and the transition-calibrated e-values. min(e1, e2) <= e_i, so it is an
        # e-value as soon as EITHER validity assumption holds (marginal map-null dominance OR transition exchangeability):
        # robust when the map replay is smoother than cross-condition queries (CMU), still blocks coherent aliasing (Boreas)
        em_t, em_a, em_r = np.minimum(e_top1, et_t), np.minimum(e_a1, ea_t), np.minimum(e_r1, er_t)
        for jn, gt, (xt, xa, xr) in (("CPC-HMM +TCE", "post", (et_t, ea_t, er_t)), ("CPC-HMM +TCE+GG", "ghost", (et_t, ea_t, er_t)),
                                     ("CPC-HMM +TCEmin", "post", (em_t, em_a, em_r)), ("CPC-HMM +TCEmin+GG", "ghost", (em_t, em_a, em_r))):
            pj = cpc_presence(est_c, MP, top, xt, xa, xr, q_seqs, c["excl"], gate=gt, rho=0.1, s0=c["excl"], U=U)
            joint[jn] = (pj > 0.5, MP[est_c], pj)
        if DUMP:
            os.makedirs("results", exist_ok=True)
            np.savez_compressed(f"results/navframes_{ds.replace(':', '_')}_{desc}_s{seed}.npz", pon=pon, est_c=est_c, top=top, e_h=e_h,
                                err_top=err_top, err_cpc=np.linalg.norm(x_cpc - ep.q_pos, axis=1), err_hmm=np.linalg.norm(x_hmm - ep.q_pos, axis=1),
                                inm=inm, offm=offm, cond=cond, q_sid=q_sid, q_k=q_k, p_frame=p_frame, pR=pR, Rq=Rq, thr=thr, lam=lam, loga=loga,
                                e_R=e_R, agree=agree, maxsim=Fr["maxsim"], q_pos=ep.q_pos, o_q=o_q, x_top=x_fix, x_cpc=x_cpc, x_hmm=x_hmm, U=U, excl=c["excl"], tol=c["tol"][0],
                                **{"pon_" + k.split()[-1].replace("+", "_"): v[2] for k, v in joint.items()},
                                **{"err_" + k.split()[-1].replace("+", "_"): np.linalg.norm(v[1] - ep.q_pos, axis=1) for k, v in joint.items()})
        rules = {"accept all": np.ones(len(q), bool), "label threshold": Fr["maxsim"] > thr_ms, "SelfCal frame": p_frame <= A,
                 "HMM off-map (labels)": acc_h, "CPC-HMM (ours)": acc_c,
                 **{f"CPC-HMM p_out={po}": a for po, a in acc_po.items()}, **{k: v[0] for k, v in joint.items()},
                 "certified (ours)": Rq > thr, "oracle": good}
        bad_top = offm | (err_top > c["excl"])
        rules["Claxton24 MLP (labels)"] = claxton_rule(srt[:, :10], S.mean(1), S.std(1), bsel, good, bad_top, seed)
        if SAFEVPR:
            import glob as _g
            sv = SAFEVPR
            if sv == "auto":                                        # mounted dataset nhatlong1103/vpr-safevpr-scores
                sv = next((d for d, _, fs in os.walk("/kaggle/input") if f"safevpr_{ds.replace(':', '_')}_p0.npz" in fs), "")
            parts = [np.load(f) for f in sorted(_g.glob(os.path.join(sv, f"safevpr_{ds.replace(':', '_')}_p*.npz")))]
            mtop = np.zeros(len(q)); ftop = kidx[top]
            for z in parts:
                r_, cd, mn = z["q_rows"], z[f"cand_{desc}"], z[f"mnn_{desc}"]
                hit = cd == ftop[r_][:, None]; mtop[r_] = np.where(hit.any(1), (mn * hit).sum(1), 0.0)
            rules["SafeVPR (labels)"] = safevpr_rule(mtop, Fr["maxsim"], bsel, bad_top)
        for bn, xb in (("HMM off-map (labels)", x_hmm), ("SelfCal frame", x_fix), ("certified (ours)", x_fix),
                       ("Claxton24 MLP (labels)", x_fix), *((("SafeVPR (labels)", x_fix),) if SAFEVPR else ())):
            rules[bn + " +DRgate"] = dr_gate(rules[bn], xb, q_seqs, U, c["excl"])
        hz = [0] if ep.q_pos.shape[1] == 1 else ([0, 1] if ep.q_pos.shape[1] == 2 else list(np.argsort(ep.q_pos.var(0))[1:]))

        run = {"seed": seed, "n_map": int(keep.sum()), "n_null_seg": len(ns), "thr": float(thr), "off_frac": float(offm.mean()), "rules": {}}
        run["hmm_T_k"] = [best[1], best[2]]
        xfs = {n: (x_hmm if n.startswith("HMM") else joint[n][1] if n in joint else (x_cpc if n.startswith("CPC") else x_fix)) for n in rules}
        pons = {"CPC-HMM (ours)": pon, **{k: v[2] for k, v in joint.items()}}
        cx = dict(q_pos=ep.q_pos, o_q=o_q, real=real, q_seqs=q_seqs, hz=hz, seed=seed, excl=c["excl"], inm=inm, offm=offm, H=H,
                  head=ds == "nclt")                                 # NCLT: heading-offset EKF (Segway heading drifts)
        if CACHE:                                                  # everything a new presence rule needs (nav_rules.py), no recompute
            os.makedirs("results", exist_ok=True)
            fl = np.concatenate(nchunks) if nchunks else np.zeros(0, int)
            np.savez_compressed(f"results/navcache_{ds.replace(':', '_')}_{desc}_s{seed}.npz", MP=MP, kidx=kidx, est_c=est_c, top=top, x_hmm=x_hmm,
                                acc_h=acc_h, good=good, inm=inm, offm=offm, err_top=err_top, q_pos=ep.q_pos, o_q=o_q, U=U, q_sid=q_sid, q_k=q_k,
                                cond=cond, real=real, excl=c["excl"], tol=c["tol"][0], H=H, hz=np.array(hz), lam=lam, loga=loga, e_R=e_R,
                                p_frame=p_frame, p_q=p_q, pR=pR, p_n=p_n, pRn=pRn, nchunk_flat=fl, nchunk_len=np.array([len(x) for x in nchunks]),
                                Rq=Rq, thr=thr, maxsim=Fr["maxsim"], thr_ms=thr_ms, srt10=srt[:, :10], Smean=S.mean(1), Sstd=S.std(1), bsel=bsel,
                                seed=seed, n_map=int(keep.sum()), n_null_seg=len(ns), hmm_T_k=np.array([best[1], best[2]]))
        run["rules"] = evaluate(rules, xfs, pons, cx, f"{ds}/{desc} s{seed}")
        out["runs"].append(run)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/nav_{ds.replace(':', '_')}_{desc}{f'_s{SEED0}' if SEED0 else ''}.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
