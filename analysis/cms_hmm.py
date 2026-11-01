"""CMS-HMM (Entry 31): a joint place-presence HMM whose OFF-MAP state has a COUNTERFACTUALLY CALIBRATED emission.

State space {map places} U {OFF}. Place transitions = the odometry kernel of the place chain (hmm_diag.DiagFilter: Gaussian on
the displacement between map places, radius r, epsilon mixing); presence transitions p_out (on -> off), p_in (off -> on); an
OFF -> ON transition re-enters at a uniform place (re-localisation). Emissions: places exp(E_tj), E_tj = (s_tj - s_t1) /
(tau sd_t) from the exact top-K list (entries outside the list at the K-th value); the OFF state gets the emission

    log e_OFF(t) = log sum_j b-_j exp(E_tj) / sum_j b-_j  -  l_t ,

l_t = the per-frame log likelihood ratio of the CMS presence chain (cms.chain_parts: e-values calibrated on the counterfactual
stream). Consequence (exact): the posterior odds ON:OFF are updated by exp(l_t) -> the OFF MARGINAL of the joint HMM is the
calibrated CMS presence chain (cpc_sc.logodds), so Theorems 6 / 6' / 6'' apply to the HMM itself; what changes is the PLACE
posterior: its mass flows to OFF along an excursion and re-enters spread over the map, which removes the lock-in of the
plain place chain at the edge of a hole (hmm_diag D3: the chain cannot cross a gap wider than r, only eps-mixing moves it).
The reported place is the MAP of the ON-conditional place posterior.
Library: place_hmm(z, b, tk, ll=None, tau=None) -> (est, pon); tau_fit(...) picks the emission scale label-free (agreement
with the stored place chain est_c on two sequences)."""
import numpy as np
from scipy.spatial import cKDTree


class SparsePlaceHMM:
    def __init__(self, MP, sigma, radius, eps=1e-4):
        MP = MP if MP.ndim > 1 else MP[:, None]
        tr = cKDTree(MP); pr = tr.query_pairs(radius, output_type="ndarray"); n = len(MP)
        self.ii = np.r_[pr[:, 0], pr[:, 1], np.arange(n)]; self.jj = np.r_[pr[:, 1], pr[:, 0], np.arange(n)]
        self.D = MP[self.jj] - MP[self.ii]; self.sigma, self.n, self.eps = sigma, n, eps

    def run(self, idx, isim, ssim, sd, tau, U, ll=None, p_in=0.01, p_out=0.01, mode="temper"):
        """one sequence. isim/ssim (L,K) top-K map rows / similarities, sd (L,) scale, U (L,dim) odometry increments,
        ll (L,) presence log LR (None: plain place chain, no OFF state). mode "reset": OFF -> ON re-entry at a uniform place;
        "temper": the place keeps evolving under the motion model while OFF and an OFF frame carries no information about the
        place -> exact place update b+ ~ b- * (q_t L_tj / sum_k b-_k L_tk + 1 - q_t), q_t = posterior P(on at t).
        Returns MAP place and P(on) per frame."""
        n, L = self.n, len(idx); b = np.full(n, 1.0 / n); pon = 0.5
        est = np.empty(L, int); po = np.full(L, np.nan)
        for i in range(L):
            if i > 0:
                w = np.exp(-0.5 * ((self.D - U[i][None]) ** 2).sum(1) / self.sigma ** 2)
                zz = np.bincount(self.ii, w, n); zz[zz == 0] = 1
                nb = np.bincount(self.jj, b[self.ii] * w / zz[self.ii], n); nb /= max(nb.sum(), 1e-300)
                if ll is not None:
                    pr_on = pon * (1 - p_out) + (1 - pon) * p_in; stay = pon * (1 - p_out) / pr_on
                    if mode == "reset": nb = stay * nb + (1 - stay) / n  # OFF -> ON re-entry: uniform place
                b = (1 - self.eps) * nb + self.eps / n
            else:
                pr_on = 0.5
            sc = max(tau * sd[i], 1e-6); s1 = ssim[i, 0]
            E = np.full(n, (ssim[i, -1] - s1) / sc); E[isim[i]] = (ssim[i] - s1) / sc
            Lk = np.exp(E - E.max())
            if ll is not None:
                l = float(np.clip(np.log(pr_on / (1 - pr_on)) + ll[i], -50, 50)); pon = 1 / (1 + np.exp(-l)); po[i] = pon
            if ll is not None and mode == "temper":
                bl = b * Lk; b = pon * bl / max(bl.sum(), 1e-300) + (1 - pon) * b
            else:
                b = b * Lk
            b /= b.sum()
            est[i] = int(b.argmax())
        return est, po


def _params(z):
    nord = bool(z["MP"].ndim == 1 or z["MP"].shape[1] == 1)
    return (1.0, 6.0) if nord else (2.0, 15.0)


def place_hmm(z, b, tk, ll=None, tau=1.0, seqs=None, mode="temper"):
    sig, rad = _params(z); MP = z["MP"]; hz = list(z["hz"]); P = MP[:, hz] if (MP.ndim > 1 and MP.shape[1] > 2) else MP
    H = SparsePlaceHMM(P, sig, rad); U = z["U"]; U = U[:, hz] if U.shape[1] > 2 else U
    I, Sm, sd = tk["idx"], tk["sim"].astype(np.float32), tk["std"]
    est = np.array(z["est_c"]).copy(); pon = np.full(len(est), np.nan)
    for idx in (seqs if seqs is not None else b["seqs"]):
        e, p = H.run(idx, I[idx], Sm[idx], sd[idx], tau, U[idx], None if ll is None else ll[idx], mode=mode); est[idx] = e; pon[idx] = p
    return est, pon


def tau_fit(z, b, tk, grid=(0.05, 0.1, 0.2, 0.4, 0.8), nseq=2):
    """emission scale of the re-implemented place chain: the grid value whose MAP agrees most with the stored place chain
    est_c on the first nseq sequences (label-free; est_c is itself label-free)"""
    seqs = sorted(b["seqs"], key=len)[-nseq:]; m = np.concatenate(seqs); best = None
    for t in grid:
        e, _ = place_hmm(z, b, tk, None, t, seqs)
        a = float(np.mean(np.linalg.norm(np.atleast_2d(z["MP"][e[m]] - z["MP"][z["est_c"][m]]).reshape(len(m), -1), axis=1) <= float(z["excl"])))
        if best is None or a > best[1]: best = (t, a)
    return best
