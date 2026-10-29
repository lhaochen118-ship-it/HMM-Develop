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
from cert_seq import odometry_sim, odometry_real

A = 0.05


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
    out = {"ds": ds, "desc": desc, "runs": []}
    for seed in range(seeds):
        t0 = time.time(); rng = np.random.default_rng(seed); bid, _ = V.map_cells(ep.m_pos, c["block"]); ub = np.unique(bid)
        keep = ~np.isin(bid, rng.choice(ub, int(round(0.3 * len(ub))), replace=False)); mp = ep.m_pos[keep]
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

        def run(logE, logoff, subset=None):
            est = np.full(len(q), -1); conf = np.zeros(len(q)); offp = np.ones(len(q))
            for idx in seqs:
                if subset is not None and not subset[idx].any(): continue
                e, cf, of, _ = F.run(logE[idx], U[idx], None if logoff is None else logoff[idx]); est[idx], conf[idx], offp[idx] = e, cf, of
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
        run_rec = {"seed": seed, "tau": tau, "a_fit": a_fit, "rho_mean": float(rho.mean()), "w_mean": float(w.mean()), "r_lambda": r_fit, "methods": res}
        out["runs"].append(run_rec)
        print(f"[{ds}/{desc} s{seed}] r_lam {np.mean(list(r_fit.values())):.2f} tau {tau:.2f} rho {rho.mean():.2f} w {w.mean():.2f} a {np.mean([v[0] for v in a_fit.values()]):.2f} ({time.time()-t0:.0f}s)", flush=True)
        for n, r in res.items():
            print(f"   {n:16s} recall {r['recall']:.3f} wrong {r['wrong']:.3f} FL {r['FL']:.3f} | AUROC {r['auroc']:.3f} R@FL5 {r['R_FL5']:.3f} "
                  f"ECE {r['ECE']:.3f} overconf {r['overconf']:+.3f} | conf-wrong {r['confident_wrong_frames']:.3f} | nav {r['nav_mean']:.1f} p95 {r['nav_p95']:.1f}", flush=True)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/hmmfix_{ds.replace(':', '_')}_{desc}.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
