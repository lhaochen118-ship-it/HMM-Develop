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
KAPPA = 0.05                                   # ghost position uncertainty growth per metre of odometry (as the nav filter)


def cpc_joint(Fp, rel, U, e_top, e_a, e_r, top, excl_nbr, p_in=0.01, p_out=0.01, gate="pred", ghost=True, s0=25.0, eps=1e-4, couple=True):
    """CPC-HMM with the place and presence chains run JOINTLY on one sequence (needed for the two couplings below).
    b_t = P(x_t | on_t): place chain without off-map state (DiagFilter transitions, affine-invariant emission `rel`).
    Couplings (both label-free; both keep LR_t an e-value, so the ARL0 bound of the presence chain is unchanged):
      * off->on re-entry: P(x_t | on_t) = [P(on_{t-1})(1-p_out) K*b_{t-1} + P(off_{t-1}) p_in G_t] / norm, where G_t is the
        DEAD-RECKONED OFF-MAP STATE (ghost): position of the last reported fix propagated by odometry, sd s0 + KAPPA * path
        length (ghost=True); ghost=False -> G uniform (position-less off-map state, as Xu'21).
      * gate of the top-1 e-value: 'post' = 1[top-1 within excl of the posterior MAP] (CPC-HMM), 'pred' = g_t = PREDICTED
        place mass b_pred within excl of the top-1 (F_{t-1}-measurable kernel); e~ = a + g (e_top - a) <= e_top pointwise;
        'ghost' = 'post' x, while no place is reported (P(on_{t-1}) <= 1/2), the DEAD-RECKONING gate g = exp(-d^2 / 2 s^2),
        d = |m_top - ghost|: an off-map stretch cannot be reported at a place the odometry says the robot cannot be.
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
        if gate == "ghost" and have and pon <= 0.5: g *= float(np.exp(-0.5 * ((pos[top[t]] - mu) ** 2).sum() / s ** 2))
        ee = 0.5 * (e_a[t] + min(g, 1.0) * (e_top[t] - e_a[t]) + e_r[t])
        lo = np.log(pr / (1 - pr)) + np.log(max(ee, 1e-300)); pon = 1 / (1 + np.exp(-np.clip(lo, -50, 50))); out[t] = pon
        if pon > 0.5: mu, s, have = pos[j].astype(float), s0, True        # ghost = last reported fix (+ odometry while off)
    return est, out


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
    for seed in range(seeds):
        rng = np.random.default_rng(seed); bid0, _ = V.map_cells(ep.m_pos, c["block"]); ub = np.unique(bid0)
        keep = ~np.isin(bid0, rng.choice(ub, int(round(DROP * len(ub))), replace=False))
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
        for jn, gt, gh, cp in (("CPC-HMM +PG+DR", "pred", True, True), ("CPC-HMM +GG", "ghost", False, False), ("CPC-HMM +GG+DR", "ghost", True, True)):
            ej, pj = np.zeros(len(q), int), np.zeros(len(q))
            for idx in q_seqs:
                ej[idx], pj[idx] = cpc_joint(Fp, rel[idx], U[idx], e_top1[idx], e_a1[idx], e_r1[idx], top[idx], nbr_x, gate=gt, ghost=gh, s0=c["excl"], couple=cp)
            joint[jn] = (pj > 0.5, MP[ej], pj)
        if DUMP:
            os.makedirs("results", exist_ok=True)
            np.savez_compressed(f"results/navframes_{ds.replace(':', '_')}_{desc}_s{seed}.npz", pon=pon, est_c=est_c, top=top, e_h=e_h,
                                err_top=err_top, err_cpc=np.linalg.norm(x_cpc - ep.q_pos, axis=1), err_hmm=np.linalg.norm(x_hmm - ep.q_pos, axis=1),
                                inm=inm, offm=offm, cond=cond, q_sid=q_sid, q_k=q_k, p_frame=p_frame, pR=pR, Rq=Rq, thr=thr, lam=lam, loga=loga,
                                e_R=e_R, agree=agree, maxsim=Fr["maxsim"], q_pos=ep.q_pos, o_q=o_q, excl=c["excl"], tol=c["tol"][0],
                                **{"pon_" + k.split()[-1].replace("+", "_"): v[2] for k, v in joint.items()},
                                **{"err_" + k.split()[-1].replace("+", "_"): np.linalg.norm(v[1] - ep.q_pos, axis=1) for k, v in joint.items()})
        rules = {"accept all": np.ones(len(q), bool), "label threshold": Fr["maxsim"] > thr_ms, "SelfCal frame": p_frame <= A,
                 "HMM off-map (labels)": acc_h, "CPC-HMM (ours)": acc_c,
                 **{f"CPC-HMM p_out={po}": a for po, a in acc_po.items()}, **{k: v[0] for k, v in joint.items()},
                 "certified (ours)": Rq > thr, "oracle": good}
        for bn, xb in (("HMM off-map (labels)", x_hmm), ("SelfCal frame", x_fix), ("certified (ours)", x_fix)):
            rules[bn + " +DRgate"] = dr_gate(rules[bn], xb, q_seqs, U, c["excl"])
        hz = [0] if ep.q_pos.shape[1] == 1 else ([0, 1] if ep.q_pos.shape[1] == 2 else list(np.argsort(ep.q_pos.var(0))[1:]))

        def track(acc, xf=None):
            xf = x_fix if xf is None else xf
            r = np.random.default_rng(seed + 7); est = np.full_like(ep.q_pos, np.nan)
            for idx in q_seqs:
                x = ep.q_pos[idx[0]].copy(); P = 1.0; est[idx[0]] = x; thh = 0.0; sc = 1 + r.normal(0, 0.03)
                for a, b in zip(idx[:-1], idx[1:]):
                    if real: u = o_q[b] - o_q[a]                                          # real VIO / wheel+gyro increment
                    else:
                        d = ep.q_pos[b] - ep.q_pos[a]; u = d * sc; thh += r.normal(0, np.deg2rad(0.3))
                        if len(hz) == 2:
                            R2 = np.array([[np.cos(thh), -np.sin(thh)], [np.sin(thh), np.cos(thh)]]); u[hz] = R2 @ u[hz]
                        u = u + r.normal(0, 0.02 * np.linalg.norm(d) / np.sqrt(len(d)) + 1e-3, len(d))
                    x = x + u; P = P + (0.05 * np.linalg.norm(u)) ** 2 + 1e-4
                    if acc[b]:
                        K = P / (P + SIG_FIX ** 2); x = x + K * (xf[b] - x); P = (1 - K) * P
                    est[b] = x
            return np.linalg.norm(est - ep.q_pos, axis=1)

        run = {"seed": seed, "n_map": int(keep.sum()), "n_null_seg": len(ns), "thr": float(thr), "off_frac": float(offm.mean()), "rules": {}}
        run["hmm_T_k"] = [best[1], best[2]]
        for name, acc in rules.items():
            xf = x_hmm if name.startswith("HMM") else joint[name][1] if name in joint else (x_cpc if name.startswith("CPC") else x_fix)
            e = track(acc, xf); err_f = np.linalg.norm(xf - ep.q_pos, axis=1)
            gd, bd = inm & (err_f <= c["excl"]), offm | (err_f > c["excl"])
            run["rules"][name] = dict(wrong_fixes=int((acc & bd).sum()), correct_fixes=int((acc & gd).sum()), FAR_offmap=float(acc[offm].mean()),
                                      err_mean=float(np.nanmean(e)), err_median=float(np.nanmedian(e)), err_p95=float(np.nanpercentile(e, 95)),
                                      frac_gt_rho=float(np.nanmean(e > c["excl"])))
            rr = run["rules"][name]
            print(f"{ds}/{desc} s{seed} {name:17s} wrong {rr['wrong_fixes']:6d} correct {rr['correct_fixes']:6d} offFAR {rr['FAR_offmap']:.3f} "
                  f"| err mean {rr['err_mean']:8.1f} med {rr['err_median']:6.1f} p95 {rr['err_p95']:8.1f} >rho {rr['frac_gt_rho']:.3f}", flush=True)
        out["runs"].append(run)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/nav_{ds.replace(':', '_')}_{desc}.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
