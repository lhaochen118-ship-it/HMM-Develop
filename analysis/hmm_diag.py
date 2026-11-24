"""Diagnostics: WHY does the HMM lose to simpler baselines (off-map discrimination, lock-in, overconfidence)?

Runs the standard HMM localizer (forward filter over map images, odometry transitions, emission exp(s/T), optional
Xu'21 off-map state with emission exp(s_(k)/T)) on a map with 30 % of its blocks removed, and records per frame:
  conf      posterior mass within tol of the MAP place
  off       posterior mass of the off-map state
  err       distance of the MAP place to the truth
  lo        log-odds of the MAP place vs the runner-up place farther than excl (accumulated evidence)
  rho       redundancy of frame t w.r.t. frame t-1: Pearson correlation of their similarity vectors over the map
  inc       per-frame evidence increment of the eventual MAP place: (s_t,map - s_t,runner-up)/T
Reports:
  D1 off-map / error discrimination (AUROC, recall at false-localisation 1/5 %) of conf, 1-off, raw max-sim, SelfCal p
  D2 calibration of conf on on-map frames (reliability bins, ECE, mean conf vs accuracy)
  D3 lock-in episodes: maximal runs of frames with err > excl while conf > 0.9 (count, length, share of total error)
  D4 temporal dependence of the evidence: lag-1 autocorrelation of inc along sequences, implied variance inflation
     (1+r)/(1-r) of the accumulated log-odds, mean rho
  D5 invariance: AUROC of conf after adding a per-frame constant to all similarities (should be identical)
Usage: hmm_diag.py <dump> <ds> <desc> [T=0.02] [k=10] -> results/hmmdiag_<ds>_<desc>.json"""
import sys, os, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V
from sc_eval import CFG
from hmm_eval import sims
from cert_seq import odometry_sim, odometry_real


class DiagFilter:
    """forward filter with off-map state, exposing posterior internals; w_t (emission exponent) and an optional
    calibrated off-map log-likelihood ratio per frame (for the fixes evaluated later)."""

    def __init__(self, m_pos, sigma, radius, conf_r, excl, p_out=0.01, p_in=0.05, eps=1e-4):
        self.n = len(m_pos); tr = cKDTree(m_pos); pr = tr.query_pairs(radius, output_type="ndarray")
        self.ii = np.r_[pr[:, 0], pr[:, 1], np.arange(self.n)]; self.jj = np.r_[pr[:, 1], pr[:, 0], np.arange(self.n)]
        self.D = m_pos[self.jj] - m_pos[self.ii]; self.sigma, self.p_out, self.p_in, self.eps = sigma, p_out, p_in, eps
        self.nbr = tr.query_ball_point(m_pos, conf_r); self.far = excl; self.pos = m_pos; self.tree = tr

    def run(self, logE, U, logoff=None):
        """logE (L,N) log-emissions, U (L,dim) odometry increments (world), logoff (L,) off-map log-emission or None"""
        L = len(logE); b = np.full(self.n, 1.0 / self.n); bo = 0.5 if logoff is not None else 0.0; b *= (1 - bo)
        est = np.empty(L, int); conf = np.empty(L); offm = np.zeros(L); lo = np.empty(L)
        self.last_pred = np.full(L, -1)                                  # argmax of the PREDICTED belief (F_{t-1}-measurable; -1 at t=0)
        for t in range(L):
            if t > 0:
                w = np.exp(-0.5 * ((self.D - U[t][None]) ** 2).sum(1) / self.sigma ** 2)
                z = np.bincount(self.ii, w, self.n); z[z == 0] = 1
                nb = np.bincount(self.jj, b[self.ii] * w / z[self.ii], self.n)
                if logoff is not None:
                    stay = nb.sum(); nb = (1 - self.p_out) * nb + self.p_in * bo / self.n; bo = (1 - self.p_in) * bo + self.p_out * stay
                b = (1 - self.eps) * nb + self.eps * (nb.sum() + bo) / self.n
                self.last_pred[t] = int(b.argmax())
            m = logE[t].max() if logoff is None else max(logE[t].max(), logoff[t])
            b = b * np.exp(logE[t] - m)
            if logoff is not None: bo = bo * np.exp(logoff[t] - m)
            s = b.sum() + bo; b /= s; bo /= s
            j = int(b.argmax()); est[t] = j; conf[t] = b[self.nbr[j]].sum(); offm[t] = bo
            far = np.linalg.norm(self.pos - self.pos[j], axis=1) > self.far
            r = b[far].max() if far.any() else 1e-300
            lo[t] = np.log(max(b[j], 1e-300)) - np.log(max(r, 1e-300))
        return est, conf, offm, lo


def auroc(pos, neg):
    if not len(pos) or not len(neg): return float("nan")
    return V.auroc(np.r_[pos, neg], np.r_[np.ones(len(pos)), np.zeros(len(neg))])


def recall_at_fl(c_on_ok, c_off, a):
    """share of on-map frames that are correct AND above the threshold giving off-map false-localisation <= a"""
    vals, ok = c_on_ok
    thr = np.quantile(c_off, 1 - a) if len(c_off) else -np.inf
    return float(((vals > thr) & ok).mean())


def main():
    dump, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3]
    T = float(sys.argv[4]) if len(sys.argv) > 4 else 0.02; kk = int(sys.argv[5]) if len(sys.argv) > 5 else 10
    if ds.startswith("4s:"): ep = V.load_4seasons(dump, desc, ds[3:]); c = CFG["cmu"]
    elif ds == "boreas": ep = V.load_boreas(dump, desc); c = CFG["cmu"]
    else: ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
    q_sid, q_k, _, _ = V.frame_order(dump, ds, ep, desc); nord = ds in ("nord", "nordw"); tol = c["tol"][0]
    rng = np.random.default_rng(0); bid, _ = V.map_cells(ep.m_pos, c["block"]); ub = np.unique(bid)
    keep = ~np.isin(bid, rng.choice(ub, int(round(0.3 * len(ub))), replace=False)); mp = ep.m_pos[keep]
    S = sims(ep.q, ep.m[keep]); dmap, _ = cKDTree(mp).query(ep.q_pos); onm, offm_ = dmap <= c["in_d"], dmap > c["off_d"]
    seqs = [np.where(q_sid == s)[0][np.argsort(q_k[q_sid == s])] for s in np.unique(q_sid)]
    o = odometry_real(ep, q_sid, q_k)
    if o is None: o = odometry_sim(ep.q_pos, q_sid, q_k, rng)
    U = np.zeros_like(ep.q_pos)
    for idx in seqs: U[idx[1:]] = np.diff(o[idx], axis=0)
    F = DiagFilter(mp, 1.0 if nord else 2.0, 6.0 if nord else 15.0, tol, c["excl"])
    srt = -np.sort(-S, 1)
    # redundancy rho_t: Pearson correlation of consecutive similarity vectors
    rho = np.zeros(len(S))
    for idx in seqs:
        a = S[idx]; a = (a - a.mean(1, keepdims=True)) / (a.std(1, keepdims=True) + 1e-9)
        rho[idx[1:]] = (a[1:] * a[:-1]).mean(1)
    out = {"ds": ds, "desc": desc, "T": T, "k": kk, "n_on": int(onm.sum()), "n_off": int(offm_.sum())}
    res = {}
    for name, use_off in (("hmm", False), ("hmm_off", True)):
        est = np.empty(len(S), int); conf = np.empty(len(S)); offp = np.zeros(len(S)); lo = np.empty(len(S))
        for idx in seqs:
            e, cf, of, l = F.run(S[idx] / T, U[idx], (srt[idx, kk - 1] / T) if use_off else None)
            est[idx], conf[idx], offp[idx], lo[idx] = e, cf, of, l
        err = np.linalg.norm(ep.q_pos - mp[est], axis=1); ok = err <= tol
        r = {}
        # D1 discrimination: on-map correct vs off-map
        cands = {"conf": conf, "1-off": 1 - offp, "conf*(1-off)": conf * (1 - offp), "raw_maxsim": S.max(1), "lo": lo}
        r["D1"] = {k: dict(auroc=auroc(v[onm & ok], v[offm_]), R_at_FL1=recall_at_fl((v[onm], ok[onm]), v[offm_], 0.01),
                           R_at_FL5=recall_at_fl((v[onm], ok[onm]), v[offm_], 0.05)) for k, v in cands.items()}
        # D2 calibration of conf on on-map frames
        bins = np.linspace(0, 1, 11); idb = np.clip(np.digitize(conf[onm], bins[1:-1]), 0, 9); okm = ok[onm]
        rel = [(float(conf[onm][idb == b].mean()), float(okm[idb == b].mean()), int((idb == b).sum())) for b in range(10) if (idb == b).any()]
        r["D2"] = dict(ECE=V.ece(conf[onm], okm, 10), mean_conf=float(conf[onm].mean()), acc=float(okm.mean()),
                       acc_when_conf_gt_0_99=float(okm[conf[onm] > 0.99].mean()) if (conf[onm] > 0.99).any() else None,
                       frac_conf_gt_0_99=float((conf[onm] > 0.99).mean()), reliability=rel)
        # D3 lock-in episodes: runs with err > excl (or off-map frame reported as a place) while conf > 0.9
        bad = ((err > c["excl"]) | offm_) & (conf > 0.9) & ~(use_off & (offp > 0.5))
        eps_len, eps_err = [], []
        for idx in seqs:
            bb = bad[idx]; i = 0
            while i < len(bb):
                if bb[i]:
                    j = i
                    while j < len(bb) and bb[j]: j += 1
                    eps_len.append(j - i); eps_err.append(float(err[idx[i:j]].sum())); i = j
                else: i += 1
        tot = float(err[onm | offm_].sum())
        r["D3"] = dict(n_episodes=len(eps_len), mean_len=float(np.mean(eps_len)) if eps_len else 0, max_len=int(max(eps_len)) if eps_len else 0,
                       frac_frames=float(bad.mean()), share_of_total_error=float(sum(eps_err) / max(tot, 1e-9)))
        res[name] = r
        # D4 dependence of the evidence stream of the MAP hypothesis (per sequence, lag-1 autocorr of increments)
        if name == "hmm":
            ac = []
            for idx in seqs:
                if len(idx) < 20: continue
                j = est[idx[-1]]                                   # final hypothesis of the sequence
                far = np.linalg.norm(mp - mp[j], axis=1) > c["excl"]
                inc = (S[idx][:, j] - S[idx][:, far].max(1)) / T
                if inc.std() > 0: ac.append(np.corrcoef(inc[1:], inc[:-1])[0, 1])
            rr = float(np.nanmedian(ac)) if ac else float("nan")
            out["D4"] = dict(lag1_autocorr_median=rr, variance_inflation=(1 + rr) / (1 - rr) if rr < 1 else float("inf"),
                             rho_mean=float(rho.mean()), rho_on=float(rho[onm].mean()), rho_off=float(rho[offm_].mean()),
                             consecutive_desc_cos=float(np.mean([(ep.q[i[1:]].astype(np.float32) * ep.q[i[:-1]].astype(np.float32)).sum(1).mean() for i in seqs if len(i) > 1])))
            # D5 invariance: shift each frame's similarities by a random constant
            sh = rng.normal(0, 0.1, len(S))[:, None]; conf2 = np.empty(len(S))
            for idx in seqs:
                _, cf, _, _ = F.run((S[idx] + sh[idx]) / T, U[idx]); conf2[idx] = cf
            out["D5"] = dict(max_abs_conf_change=float(np.abs(conf2 - conf).max()))
    out["methods"] = res
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/hmmdiag_{ds.replace(':', '_')}_{desc}.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "methods"}, default=float))
    for n, r in res.items():
        print(n, "D1", {k: (round(v["auroc"], 3), round(v["R_at_FL5"], 3)) for k, v in r["D1"].items()})
        print(n, "D2", {k: v for k, v in r["D2"].items() if k != "reliability"})
        print(n, "D3", r["D3"])


if __name__ == "__main__":
    main()
