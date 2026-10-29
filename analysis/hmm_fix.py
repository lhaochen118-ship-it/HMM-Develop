"""CEE-HMM: Calibrated Evidence Emissions that fix the two structural weaknesses of HMM localization found by hmm_diag.py.

Root causes (hmm_diag): (A) the softmax emission exp(s/T) only carries RELATIVE evidence (place vs place); the posterior
is exactly invariant to a per-frame shift of all similarities, so the HMM cannot see ABSENCE (off-map), which is a
statement about the absolute similarity level vs the non-match law. (B) consecutive frames are nearly duplicate
observations (rho ~ 0.85-0.95) but are multiplied as independent evidence -> overconfident posterior, lock-in.

Generative view: s_tj ~ f1 if j = x_t, else f0; LR(j : i) = f1(s_j) f0(s_i) / (f0(s_j) f1(s_i)) (relative) but
LR(j : off-map) = f1(s_j) / f0(s_j) (absolute). CEE emission of map state j at frame t (off-map state: log-emission 0):
    log e_t(j) = w_t * [ lambda_t + (s_tj - s_t,top) / (tau * sd_far,t) ]
    lambda_t   = log a + (a - 1) log p_t       (Beta(a,1)-alternative likelihood ratio of the map-calibrated SelfCal-AA
                                                p-value of the top match; an e-value: E_null[exp(lambda)] = 1; a fitted
                                                label-free by EM on the traversal's own p-values: pi0*U + (1-pi0)*Beta(a,1))
    sd_far,t   = spread of the far-region maxima of frame t (affine-invariant relative part)
    tau        = Gumbel scale of the map null's z_far (label-free)
    w_t        = 1 - rho_t^2, rho_t = correlation of the similarity vectors of frames t-1 and t (redundancy tempering)
Ablations: rel (only the affine-invariant relative part, Xu'21 k-th-best off-map), abs (+lambda), red (+w_t), full.
Baseline: Xu'21-style HMM, emission exp(s/T), off-map exp(s_(k)/T), T and k tuned WITH LABELS on the 2 most benign
conditions under off-map false-localisation <= alpha (the label-calibrated operating point of that family).
Protocol: map with 30 % of its blocks removed (3 seeds), odometry (simulated / real VIO / wheel+gyro).
Metrics: on-map recall@tol at the default decision (MAP state; abstain if off-map wins), off-map false localisation,
AUROC / recall at FL 1 %, 5 % of the posterior confidence, ECE, lock-in share of error, navigation error (Kalman +
fixes when the HMM reports a place).  Usage: hmm_fix.py <dump> <ds> <desc> [seeds=3]"""
import sys, os, json, time
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V, selfcal as SC
from sc_eval import CFG
from hmm_eval import sims
from hmm_diag import DiagFilter, auroc, recall_at_fl
from cert_seq import odometry_sim, odometry_real, running, chunks

A = 0.05
DROP = 0.3                                   # share of map blocks removed (off-map excursions); --drop f overrides
if "--drop" in sys.argv:
    i = sys.argv.index("--drop"); DROP = float(sys.argv[i + 1]); del sys.argv[i:i + 2]


def beta_em(p, iters=200):
    """fit pi0 * U(0,1) + (1 - pi0) * Beta(a, 1) to p-values (a < 1) by EM; returns a (clipped to [0.02, 0.99])"""
    p = np.clip(p, 1e-6, 1); lp = np.log(p); pi0, a = 0.5, 0.3
    for _ in range(iters):
        f1 = a * p ** (a - 1); r = (1 - pi0) * f1 / (pi0 + (1 - pi0) * f1)
        pi0 = float(np.clip(1 - r.mean(), 0.01, 0.99)); a = float(np.clip(-r.sum() / (r * lp).sum(), 0.02, 0.99))
    return a, pi0


def main():
    dump, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3]; seeds = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    if ds.startswith("4s:"): ep = V.load_4seasons(dump, desc, ds[3:]); c = CFG["cmu"]
    elif ds == "boreas": ep = V.load_boreas(dump, desc); c = CFG["cmu"]
    else: ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
    q_sid, q_k, _, _ = V.frame_order(dump, ds, ep, desc); nord = ds in ("nord", "nordw"); tol = c["tol"][0]
    cond = np.asarray(ep.q_cond).astype(str); conds = sorted(set(cond))
    seqs = [np.where(q_sid == s)[0][np.argsort(q_k[q_sid == s])] for s in np.unique(q_sid)]
    q = ep.q.astype(np.float32); nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
    out = {"ds": ds, "desc": desc, "drop": DROP, "runs": []}
    for seed in range(seeds):
        t0 = time.time(); rng = np.random.default_rng(seed); bid, _ = V.map_cells(ep.m_pos, c["block"]); ub = np.unique(bid)
        keep = ~np.isin(bid, rng.choice(ub, int(round(DROP * len(ub))), replace=False)); mp = ep.m_pos[keep]
        M = ep.m[keep].astype(np.float32); mu = M.mean(0, keepdims=True); Mc = nrm(M - mu); qc = nrm(q - mu)
        S = sims(q, M); dmap, _ = cKDTree(mp).query(ep.q_pos); onm, offm = dmap <= c["in_d"], dmap > c["off_d"]
        # map-calibrated per-frame evidence (SelfCal-AA on the reduced map; no labels)
        args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
        Nr, Nc = SC.map_null(M, mp, *args), SC.map_null(Mc, mp, *args)
        Fr, Fc = SC.qm_stats(q, M, mp, c["cell"], c["excl"], c["k"]), SC.qm_stats(qc, Mc, mp, c["cell"], c["excl"], c["k"])
        p = SC.SelfCalTest(SC.pack(Nr, Nc)).pvalue(**SC.pack(Fr, Fc))
        zf = Nc["z_far"][np.isfinite(Nc["z_far"])]; tau = float(zf.std() * np.sqrt(6) / np.pi)          # Gumbel scale (z units)
        sdf = np.maximum(np.nan_to_num(Fr["sd_far"], nan=np.nanmedian(Fr["sd_far"])), 1e-4)
        lam = np.zeros(len(q)); a_fit = {}
        for cn in conds:                                                                               # per traversal, label-free
            m = cond == cn; a, pi0 = beta_em(p[m]); a_fit[cn] = (a, pi0); lam[m] = np.log(a) + (a - 1) * np.log(np.clip(p[m], 1e-6, 1))
        rho = np.zeros(len(q))
        for idx in seqs:
            z = S[idx]; z = (z - z.mean(1, keepdims=True)) / (z.std(1, keepdims=True) + 1e-9); rho[idx[1:]] = (z[1:] * z[:-1]).mean(1)
        w = np.clip(1 - rho ** 2, 0.02, 1.0)
        o = odometry_real(ep, q_sid, q_k)
        if o is None: o = odometry_sim(ep.q_pos, q_sid, q_k, rng)
        U = np.zeros_like(ep.q_pos)
        for idx in seqs: U[idx[1:]] = np.diff(o[idx], axis=0)
        F = DiagFilter(mp, 1.0 if nord else 2.0, 6.0 if nord else 15.0, tol, c["excl"])
        smax = S.max(1, keepdims=True); srt = -np.sort(-S, 1)
        rel = (S - smax) / (tau * sdf[:, None])                                                         # affine-invariant relative part

        def run(logE, logoff, subset=None, filt=None):
            est = np.full(len(q), -1); conf = np.zeros(len(q)); offp = np.ones(len(q))
            for idx in seqs:
                if subset is not None and not subset[idx].any(): continue
                e, cf, of, _ = (filt or F).run(logE[idx], U[idx], None if logoff is None else logoff[idx]); est[idx], conf[idx], offp[idx] = e, cf, of
            return est, conf, offp

        def metrics(est, conf, offp, gate=None):
            rep = offp < 0.5 if gate is None else gate                                                 # reports a place
            err = np.linalg.norm(ep.q_pos - mp[np.maximum(est, 0)], axis=1); ok = err <= tol
            score = conf * (1 - offp)
            r = dict(recall=float((rep & ok)[onm].mean()), wrong=float((rep & ~ok)[onm].mean()), FL=float(rep[offm].mean()),
                     auroc=auroc(score[onm & ok], score[offm]), R_FL1=recall_at_fl((score[onm], ok[onm]), score[offm], 0.01),
                     R_FL5=recall_at_fl((score[onm], ok[onm]), score[offm], 0.05), ECE=V.ece(score[onm], ok[onm], 10),
                     overconf=float(score[onm].mean() - ok[onm].mean()))
            bad = rep & ((err > c["excl"]) | offm); r["confident_wrong_frames"] = float((bad & (score > 0.9)).mean())
            r["share_err_confident_wrong"] = float(err[bad & (score > 0.9)].sum() / max(err[rep].sum(), 1e-9))
            r["cond_recall"] = {cn: float((rep & ok)[onm & (cond == cn)].mean()) for cn in conds if (onm & (cond == cn)).any()}
            # ARL0: off-map frames per false-report onset (CUSUM view of the presence chain: >= (1-p)/p for sequential e-values);
            # re-entry delay: frames from re-entering the map (off-map run followed by on-map) to the first correct report
            onsets, delays = 0, []
            for idx in seqs:
                rp, of, on, gk = rep[idx], offm[idx], onm[idx], (rep & ok)[idx]
                onsets += int((of & rp & ~np.r_[False, rp[:-1]]).sum())
                last, nxt_off = 0, np.r_[np.flatnonzero(of), len(idx)]
                for i in range(len(idx)):
                    if of[i]: last = -1
                    elif on[i]:
                        if last == -1:                                      # censored at the next off-map frame
                            end = nxt_off[np.searchsorted(nxt_off, i)]; j = np.flatnonzero(gk[i:end])
                            delays.append(int(j[0]) if len(j) else end - i)
                        last = 1
            r["ARL0"] = float(offm.sum() / max(onsets, 1)); r["reentry_delay"] = float(np.mean(delays)) if delays else float("nan")
            r["n_reentry"] = len(delays)
            # navigation: Kalman filter with the HMM's reported places as fixes (sigma 5 m)
            e_nav = np.full(len(q), np.nan); xr = mp[np.maximum(est, 0)]
            for idx in seqs:
                x = ep.q_pos[idx[0]].copy(); P = 1.0; e_nav[idx[0]] = 0.0
                for aa, bb in zip(idx[:-1], idx[1:]):
                    x = x + (o[bb] - o[aa]); P = P + (0.05 * np.linalg.norm(o[bb] - o[aa])) ** 2 + 1e-4
                    if rep[bb]:
                        K = P / (P + 25.0); x = x + K * (xr[bb] - x); P = (1 - K) * P
                    e_nav[bb] = np.linalg.norm(x - ep.q_pos[bb])
            r.update(nav_mean=float(np.nanmean(e_nav)), nav_p95=float(np.nanpercentile(e_nav, 95)), nav_gt_rho=float(np.nanmean(e_nav > c["excl"])))
            return r

        res = {}
        # baseline: Xu'21-style, T, k tuned with labels (benign conditions, FL <= alpha)
        ok1 = lambda e: np.linalg.norm(ep.q_pos - mp[np.maximum(e, 0)], axis=1) <= tol
        r1 = {cn: (S.argmax(1) == S.argmax(1))[cond == cn].mean() for cn in conds}
        benign = sorted(conds, key=lambda cn: -((np.linalg.norm(ep.q_pos - mp[S.argmax(1)], axis=1) <= tol) & onm)[cond == cn].mean())[:2]
        bsel = np.isin(cond, benign); best = None
        for T in (0.01, 0.02, 0.05):
            for kk in (5, 10, 20):
                e, cf, of = run((S - smax) / T, (srt[:, kk - 1] - smax[:, 0]) / T, bsel)
                rep = (of < 0.5) & bsel; fl = rep[offm & bsel].mean() if (offm & bsel).any() else 0
                good = (rep & ok1(e) & onm).sum()
                if fl <= A and (best is None or good > best[0]): best = (good, T, kk)
        best = best or (0, 0.01, 20); T, kk = best[1], best[2]
        res["xu21_tuned"] = metrics(*run((S - smax) / T, (srt[:, kk - 1] - smax[:, 0]) / T)); res["xu21_tuned"]["T_k"] = [T, kk]
        res["hmm_nooff_tuned"] = metrics(*run((S - smax) / T, None))
        # same T, k with a symmetric off-map switching prior (p_in = p_out = 0.01): isolates the prior from the evidence
        Fs = DiagFilter(mp, 1.0 if nord else 2.0, 6.0 if nord else 15.0, tol, c["excl"], p_out=0.01, p_in=0.01)
        res["xu21_sym"] = metrics(*run((S - smax) / T, (srt[:, kk - 1] - smax[:, 0]) / T, filt=Fs))
        # CEE ablations (label-free)
        res["rel"] = metrics(*run(rel, (srt[:, kk - 1] - smax[:, 0]) / (tau * sdf)))                  # affine-invariant + k-th best
        res["abs_naive"] = metrics(*run(lam[:, None] + rel, np.zeros(len(q))))                          # presence LR, 1/N counted twice
        # Bayes-consistent presence emission: sum_j (1/N) P(s|j)/P(s|off) = LR_max(p) (the SelfCal p-value is a MAX statistic over
        # the map, so it already pays the multiplicity), and P(j | s, on-map) = softmax(rel)  =>  log e(j) = lam + log N + log softmax_j(rel)
        lse = np.log(np.exp(rel).sum(1)); absE = lam[:, None] + np.log(rel.shape[1]) + rel - lse[:, None]
        res["abs"] = metrics(*run(absE, np.zeros(len(q))))
        res["red_vec"] = metrics(*run(w[:, None] * absE, np.zeros(len(q))))                              # + tempering 1 - rho^2
        # redundancy of the EVIDENCE stream: lag-1 autocorrelation r of lambda WITHIN sequences (demeaned per sequence, so
        # between-sequence level differences do not inflate it), pooled per traversal; ESS factor w = (1-r)/(1+r)
        wl = np.ones(len(q)); r_fit = {}
        for cn in conds:
            xs, ys = [], []
            for i in seqs:
                if cond[i[0]] != cn or len(i) < 4: continue
                v = lam[i] - lam[i].mean(); xs.append(v[1:]); ys.append(v[:-1])
            x = np.concatenate(xs) if xs else np.zeros(0); y = np.concatenate(ys) if ys else np.zeros(0)
            r = float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum())) if len(x) > 10 and (x * x).sum() > 0 else 0.0
            r = min(max(r, 0.0), 0.95); r_fit[cn] = r; wl[cond == cn] = (1 - r) / (1 + r)
        res["full_joint"] = metrics(*run(wl[:, None] * absE, np.zeros(len(q))))                           # joint state space + ESS tempering
        # FACTORISED CEE-HMM: place chain (WHERE, relative evidence) x presence chain (WHETHER, calibrated absolute evidence)
        #   place chain   : HMM without off-map state, emission w_pl * rel (affine-invariant)
        #   presence chain: 2-state HMM, P(on_t) = (1-p_out) P(on_{t-1}) + p_in P(off_{t-1}); log-odds += w_pr * log LR_t,
        #                   LR_t = a p_t^(a-1) (e-value); gate: frames whose top-1 disagrees with the place MAP count as p = 1
        top = Fr["top"].astype(int); loga = np.log(np.array([a_fit[cn][0] for cn in cond])); place_cache = {}
        one = np.ones(len(q))
        for name, w_pl, w_pr, p_in, p_out, gate in (
                ("fac_now", one, one, 0.05, 0.01, True), ("fac_now_sym", one, one, 0.01, 0.01, True),
                ("fac_now_nogate", one, one, 0.01, 0.01, False),
                ("fac_ess_pr", one, wl, 0.01, 0.01, True), ("fac_ess_both", wl, wl, 0.01, 0.01, True),
                ("fac_sqrt_both", np.sqrt(wl), np.sqrt(wl), 0.01, 0.01, True)):
            key = tuple(np.round(w_pl[:5], 6)) + (float(w_pl.mean()),)
            if key not in place_cache: place_cache[key] = run(w_pl[:, None] * rel, None)
            est, conf, _ = place_cache[key]
            agree = np.linalg.norm(mp[top] - mp[est], axis=1) <= c["excl"]
            ll = np.where(agree | (not gate), lam, loga)
            pon = np.zeros(len(q))
            for idx in seqs:
                pr = 0.5
                for t in idx:
                    pr = (1 - p_out) * pr + p_in * (1 - pr)
                    lo = np.log(pr / (1 - pr)) + w_pr[t] * ll[t]; pr = 1 / (1 + np.exp(-np.clip(lo, -50, 50))); pon[t] = pr
            res[name] = metrics(est, conf, 1 - pon)
        # SECOND presence e-value from the place chain itself: its posterior concentration conf_t is calibrated against the
        # same HMM run on the map's own held-out blocks (off-map by construction, odometry simulated from the map poses);
        # p_conf = conformal p of conf_t; e_conf = a p^(a-1) (EM per traversal). Mixed with the top-1 e-value by averaging
        # (e = (e1 + e2) / 2 is an e-value under ANY dependence between the two) and fed to the same presence chain.
        bidk, _ = V.map_cells(mp, c["block"]); ubk = np.unique(bidk); nul_conf = []
        msid = np.zeros(len(mp), int); mk = np.arange(len(mp))
        for b in ubk[1::2][:20]:
            hold = np.flatnonzero(bidk == b); rest = bidk != b
            if len(hold) < 10 or rest.sum() < 50: continue
            Sb = M[hold] @ M[rest].T
            stb = SC.qm_stats(M[hold], M[rest], mp[rest], c["cell"], c["excl"], c["k"])
            sdb = np.maximum(np.nan_to_num(stb["sd_far"], nan=np.nanmedian(sdf)), 1e-4)
            relb = (Sb - Sb.max(1, keepdims=True)) / (tau * sdb[:, None])
            ob = odometry_sim(mp[hold], np.zeros(len(hold), int), np.arange(len(hold)), rng); Ub = np.vstack([np.zeros((1, mp.shape[1])), np.diff(ob, axis=0)])
            Fb = DiagFilter(mp[rest], 1.0 if nord else 2.0, 6.0 if nord else 15.0, tol, c["excl"])
            _, cfb, _, _ = Fb.run(relb, Ub); nul_conf.append(cfb)
        nul_conf = np.sort(np.concatenate(nul_conf)) if nul_conf else np.zeros(1)
        est, conf, _ = place_cache[next(iter(place_cache))] if place_cache else run(rel, None)
        pc = (1 + len(nul_conf) - np.searchsorted(nul_conf, conf, side="left")) / (1 + len(nul_conf))
        e_top = np.exp(lam); e_conf = np.zeros(len(q))
        for cn in conds:
            m = cond == cn; a2, _ = beta_em(pc[m]); e_conf[m] = a2 * np.clip(pc[m], 1e-6, 1) ** (a2 - 1)
        agree = np.linalg.norm(mp[top] - mp[est], axis=1) <= c["excl"]
        e_top_g = np.where(agree, e_top, np.exp(loga))
        # BELIEF-INDEPENDENT sequence evidence for presence: the odometry-anchored statistic R_t (ANCH, cert_seq) of the top-1
        # stream, calibrated per frame against R on the map's own held-out traversal (map null items, odometry from map poses)
        Hh = 10; rho_o = 1.0 if nord else 5.0
        sub = np.arange(0, len(mp), 2)                                       # map_null(stride=2): rows of Nr/Nc = map items sub
        ok_n = np.isfinite(Nr["maxsim"]) & np.isfinite(Nc["z_far"])
        p_n = SC.SelfCalTest(SC.pack(Nr, Nc)).pvalue(**SC.pack(Nr, Nc))
        o_m = odometry_sim(mp[sub], np.zeros(len(sub), int), np.arange(len(sub)), rng); Rn = np.full(len(sub), np.nan)
        for ch in chunks(np.arange(len(sub)), ok_n, bidk[sub]): Rn[ch] = running(p_n, Nr["top"], np.array(ch), o_m, mp, "ANCH", c["excl"], rho_o, Hh)
        rn = np.sort(Rn[np.isfinite(Rn)]); Rq = np.zeros(len(q))
        for idx in seqs: Rq[idx] = running(p, Fr["top"], idx, o, mp, "ANCH", c["excl"], rho_o, Hh)
        pR = (1 + len(rn) - np.searchsorted(rn, Rq, side="left")) / (1 + len(rn)); e_anch = np.zeros(len(q))
        for cn in conds:
            m = cond == cn; a3, _ = beta_em(pR[m]); e_anch[m] = a3 * np.clip(pR[m], 1e-6, 1) ** (a3 - 1)
        # each frame enters H overlapping windows of R_t, so the ANCH e-value is tempered by 1/H (e^w is an e-value, Jensen)
        for name, ee in (("fac_conf", e_conf), ("fac_mix", 0.5 * (e_top_g + e_conf)), ("fac_anch", e_anch),
                         ("fac_anch_mix", 0.5 * (e_top_g + e_anch)), ("fac_anchT_mix", 0.5 * (e_top_g + e_anch ** (1.0 / Hh))),
                         ("fac_anchS_mix", 0.5 * (e_top_g + e_anch ** (1.0 / np.sqrt(Hh))))):
            ll = np.log(np.maximum(ee, 1e-300)); pon = np.zeros(len(q))
            for idx in seqs:
                pr = 0.5
                for t in idx:
                    pr = 0.99 * pr + 0.01 * (1 - pr)
                    lo = np.log(pr / (1 - pr)) + ll[t]; pr = 1 / (1 + np.exp(-np.clip(lo, -50, 50))); pon[t] = pr
            res[name] = metrics(est, conf, 1 - pon)
        res["fac_mix"]["n_null_conf"] = int(len(nul_conf))

        # THEORY CHECKS of the presence chain (CPC-HMM = fac_anchT_mix):
        # (1) switching-probability sweep: odds O_t <= (O_{t-1} + p/(1-p)) LR_t, i.e. dominated by a Shiryaev-Roberts e-detector
        #     -> ARL0 >= (1-p)/p - R0; re-entry delay ~ log((1-p)/p) / KL1 (Wald), KL1 = E_on[log LR_t]
        # (2) PREDICTABLE e-values: a_t refitted every 25 frames on the traversal's PAST frames only (no look-ahead), so
        #     LR_t is an e-value conditionally on the past under the map-null dominance assumption (an e-process)
        def presence(ee, p):
            ll = np.log(np.maximum(ee, 1e-300)); pon = np.zeros(len(q))
            for idx in seqs:
                pr = 0.5
                for t in idx:
                    pr = (1 - p) * pr + p * (1 - pr)
                    lo = np.log(pr / (1 - pr)) + ll[t]; pr = 1 / (1 + np.exp(-np.clip(lo, -50, 50))); pon[t] = pr
            return pon

        def predictable(pv):
            e, a_t = np.ones(len(q)), np.ones(len(q))
            for cn in conds:
                order = np.concatenate([i for i in seqs if cond[i[0]] == cn]); a = 1.0       # a = 1: no evidence yet
                for j, t in enumerate(order):
                    if j >= 25 and j % 25 == 0: a, _ = beta_em(pv[order[:j]], iters=50)
                    a_t[t] = a; e[t] = a * np.clip(pv[t], 1e-6, 1) ** (a - 1)
            return e, a_t

        ee_cpc = 0.5 * (e_top_g + e_anch ** (1.0 / Hh)); lcpc = np.log(np.maximum(ee_cpc, 1e-300))
        run_kl = {"KL_on": float(lcpc[onm].mean()), "KL_off": float(lcpc[offm].mean()), "KL_on_correct": float(lcpc[onm & (np.linalg.norm(ep.q_pos - mp[est], axis=1) <= tol)].mean())}
        for pp in (0.001, 0.003, 0.03, 0.1):
            res[f"cpc_p{pp}"] = metrics(est, conf, 1 - presence(ee_cpc, pp))
        e1p, a1p = predictable(p); e3p, _ = predictable(pR)
        res["cpc_pred"] = metrics(est, conf, 1 - presence(0.5 * (np.where(agree, e1p, a1p) + e3p ** (1.0 / Hh)), 0.01))
        run_rec = {"seed": seed, "tau": tau, "a_fit": a_fit, "rho_mean": float(rho.mean()), "w_mean": float(w.mean()), "r_lambda": r_fit, "KL": run_kl, "methods": res}
        out["runs"].append(run_rec)
        print(f"[{ds}/{desc} s{seed}] r_lam {np.mean(list(r_fit.values())):.2f} tau {tau:.2f} rho {rho.mean():.2f} w {w.mean():.2f} a {np.mean([v[0] for v in a_fit.values()]):.2f} ({time.time()-t0:.0f}s)", flush=True)
        for n, r in res.items():
            print(f"   {n:16s} recall {r['recall']:.3f} wrong {r['wrong']:.3f} FL {r['FL']:.3f} | AUROC {r['auroc']:.3f} R@FL5 {r['R_FL5']:.3f} "
                  f"ECE {r['ECE']:.3f} overconf {r['overconf']:+.3f} | conf-wrong {r['confident_wrong_frames']:.3f} | nav {r['nav_mean']:.1f} p95 {r['nav_p95']:.1f} "
                  f"| ARL0 {r['ARL0']:.0f} re-entry {r['reentry_delay']:.1f} (n {r['n_reentry']})", flush=True)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/hmmfix{'' if DROP == 0.3 else f'_d{round(DROP * 100)}'}_{ds.replace(':', '_')}_{desc}.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
