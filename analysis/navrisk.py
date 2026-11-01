"""Navigation-risk calibration of the CMS decision (RESEARCH_LOG Entry 29): a COUNTERFACTUAL INNOVATION GATE.

Why (Entry 29 diagnosis, labels used only to classify): the harm of a false fix to the navigation filter is proportional
to its innovation nu = |fix - prior estimate| (each fix moves the estimate by K nu); accepted TRUE fixes have small
innovations (median 0.5-8 m), the harmful false fixes large ones (90th percentile 42-856 m). The filter's own variance is
useless as a gate (sqrt P ~ 0.6 m: a chi^2 gate would reject every fix after a drift -> lock-out, Entry 23 +GG).

Counterfactual null of the innovation. The counterfactual winner j_cf of CMS (cms.cms_stats) is the place the system would
report if the corridor around its belief were not in the map, i.e. a FALSE fix by construction when the belief is right.
Its displacement from the belief, d_cf = |m(j_cf) - m(j)|, is the innovation such a false fix would cause on a filter that
tracks the belief. Gate radius tau = beta-quantile of d_cf over the calibration stream of the condition (same Mondrian
groups as CMS): a counterfactual false fix passes the gate with probability <= beta.
Rule (+NG): report t iff the base CMS rule reports t AND nu_t <= max(tau, 3 sqrt(P_t^-)), nu_t computed online on the
navigation filter (Entry 30: the floor 3 sqrt(P^-) of the filter's own prior uncertainty keeps the gate open while the
filter is not localised, e.g. a label-free initialisation; with a localised filter, sqrt(P) ~ 0.6 m << tau, it is inactive).
Release (+NGR, against lock-out after a long drift): if the base rule reported the last R = H frames and their innovation
VECTORS are coherent (spread <= excl / 2: the filter is offset from a consistent reported track, the drift case), the gate
opens for that streak. The gate only REMOVES reports, so every segment-level guarantee of the base rule (segFAR, FL;
Theorem 6, Lemma 7) is kept; it adds: P(an accepted false fix has innovation > tau) <= beta (under S1-S3, at the boundary).
Usage (library): gate_tau(z, b, st, beta) -> tau per frame; nav_gate(acc, xf, z, b, tau, ...) -> accept mask (replicates
the evaluation filter nav_demo.track / track_head exactly, so the decisions see the same prior estimates)."""
import numpy as np
import cms
import nav_demo as N


def cf_disp(z, st):
    """displacement between the counterfactual winner and the winner (the belief), in the planar coordinates"""
    MP = z["MP"]; hz = list(z["hz"]); P = MP[:, hz] if (MP.ndim > 1 and MP.shape[1] > 2) else (MP if MP.ndim > 1 else MP[:, None])
    j, jc = st["j"], st["j_cf"]; ok = (j >= 0) & (jc >= 0) & np.isfinite(st["cost_cf"])
    d = np.full(len(j), np.nan); d[ok] = np.linalg.norm(P[jc[ok]] - P[j[ok]], axis=1)
    return d


def gate_tau(z, b, st, beta=0.05):
    """gate radius per frame: beta-quantile of the counterfactual displacement of the frame's calibration group"""
    d = cf_disp(z, st); tau = np.full(len(d), np.inf)
    keep = cms.ALPHA_MIN[0]; cms.ALPHA_MIN[0] = 0.05          # Mondrian minimum size fixed (not left over from the last rules call)
    groups = cms.cal_groups(z, b["seqs"]); cms.ALPHA_MIN[0] = keep
    for sqs, cqs in groups:
        m = np.concatenate(sqs); mc = np.concatenate(cqs); v = d[mc]; v = v[np.isfinite(v)]
        if len(v): tau[m] = float(np.quantile(v, beta))
    return tau


def nav_gate(acc, xf, z, b, tau, release=True, R=None, head=None):
    """online filter (identical to nav_demo.track / track_head) with the counterfactual innovation gate"""
    q_pos, o_q, seqs, hz, seed, real = z["q_pos"], z["o_q"], b["seqs"], list(z["hz"]), int(z["seed"]), bool(z["real"])
    excl = b["excl"]; R = R or b["H"]; out = np.zeros(len(acc), bool)
    head = (b.get("ds") == "nclt") if head is None else head
    if head and real and q_pos.shape[1] == 2:
        I3 = np.eye(3); Hm = np.eye(2, 3); Rf = N.nav_sig() ** 2 * np.eye(2)
        for idx in seqs:
            x0, p0 = N.nav_init(q_pos, idx[0]); m = np.r_[x0, 0.0]; P = np.diag([p0, p0, np.deg2rad(5) ** 2]); buf = []
            for a, bb in zip(idx[:-1], idx[1:]):
                u = o_q[bb] - o_q[a]; c, s_ = np.cos(m[2]), np.sin(m[2]); Ru = np.array([c * u[0] - s_ * u[1], s_ * u[0] + c * u[1]])
                m[:2] += Ru; F = I3.copy(); F[0, 2], F[1, 2] = -Ru[1], Ru[0]; L = np.linalg.norm(u)
                P = F @ P @ F.T + np.diag([(N.NAV_Q * L) ** 2 + 1e-4, (N.NAV_Q * L) ** 2 + 1e-4, 0.004 ** 2 * L + 1e-8])
                ok = _decide(acc[bb], xf[bb] - m[:2], max(tau[bb], 3.0 * np.sqrt(max(P[0, 0], P[1, 1]))), buf, release, R, excl)
                if ok:
                    K = P @ Hm.T @ np.linalg.inv(Hm @ P @ Hm.T + Rf); m = m + K @ (xf[bb] - m[:2]); P = (I3 - K @ Hm) @ P
                out[bb] = ok
        return out
    r = np.random.default_rng(seed + 7)
    for idx in seqs:
        x, P = N.nav_init(q_pos, idx[0]); thh = 0.0; sc = 1 + r.normal(0, 0.03); buf = []
        for a, bb in zip(idx[:-1], idx[1:]):
            if real: u = o_q[bb] - o_q[a]
            else:
                d = q_pos[bb] - q_pos[a]; u = d * sc; thh += r.normal(0, np.deg2rad(0.3))
                if len(hz) == 2:
                    R2 = np.array([[np.cos(thh), -np.sin(thh)], [np.sin(thh), np.cos(thh)]]); u[hz] = R2 @ u[hz]
                u = u + r.normal(0, 0.02 * np.linalg.norm(d) / np.sqrt(len(d)) + 1e-3, len(d))
            x = x + u; P = P + (N.NAV_Q * np.linalg.norm(u)) ** 2 + 1e-4
            ok = _decide(acc[bb], np.atleast_1d(xf[bb] - x)[:len(np.atleast_1d(x))], max(tau[bb], 3.0 * np.sqrt(np.max(P))), buf, release, R, excl)
            if ok:
                K = P / (P + N.nav_sig() ** 2); x = x + K * (xf[bb] - x); P = (1 - K) * P
            out[bb] = ok
    return out


def _decide(base, nu_vec, tau, buf, release, R, excl):
    """gate decision for one frame; buf keeps the innovation vectors of the current streak of base reports. Once the release
    fires, the gate stays open until the streak ends (Entry 30 fix: re-testing the coherence after each accepted fix sees
    the innovation jump caused by the filter's own update, so the Entry 29 code reopened only every R-th frame)"""
    if not base:
        buf.clear(); return False
    if buf and buf[0] is None: return True                       # released streak
    nu_vec = np.asarray(nu_vec, float).ravel(); buf.append(nu_vec)
    if np.linalg.norm(nu_vec) <= tau: return True
    if release and len(buf) >= R:
        V = np.array(buf[-R:]); spread = np.sqrt(((V - V.mean(0)) ** 2).sum(1).mean())
        if spread <= 0.5 * excl:
            buf.clear(); buf.append(None); return True
    return False
