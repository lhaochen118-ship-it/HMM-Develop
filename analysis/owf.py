"""Open-world filter (OWF): Bayes filter on a METRIC grid that covers the mapped AND the unmapped space around the map.

Idea 2 (branch hmm-2nd-idea). The hidden state is the robot position x_t on a grid (cell g) over the map's bounding box
grown by a band B, plus one position-less state Omega (farther than B from every map image). Presence on the map is not a
separate latent variable: it is a function of x_t (a frame is on the map iff x_t lies near map images). Consequences:
  * transitions are MASS-CONSERVING: the odometry moves the belief, and mass that moves into a hole stays in the hole
    (unmapped cells), instead of being renormalised onto the remaining map nodes (topological HMMs, DiagFilter);
  * emissions are likelihood RATIOS against a common reference p0 ("the view is unrelated to this map image"):
      unmapped cell: L = 1 (no map image can explain or contradict the view),
      mapped cell c: L_c = mean_{i in c} L_i,  log L_i = beta z_i - log mean_j exp(beta z_j),
    z_i = robust z-score of the similarity of the frame to map image i within the frame's own similarity profile over the
    whole map; the normaliser makes the mean LR over the map exactly 1 (the frame's own profile is its null p0), so an
    off-map frame has no net pull towards the map;
  * the decision is read from the posterior: report the map image x_hat whose excl-disc holds the largest posterior
    mass P(|x - x_hat| <= excl); report iff that mass >= 1 - eps.
Grid motion: the belief array is only shifted by WHOLE cells; the sub-cell part of the odometry is kept as a phase phi
(world position of cell c = origin + g c + phi), so deterministic motion adds no numerical diffusion; the process noise
(variance q |u_t| + s0^2 per axis) is applied as an exact Gaussian blur once the accumulated variance exceeds (g/2)^2.
Usage (design runs on the public navcache + descriptor dumps):
  owf.py <navcache_dir> <dump_dir> <ds> <desc> <seed> [--beta b|ml] [--ell L] [--eps e1,e2] [--out f.json]"""
import sys, os, json, time
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter


def robust_z(S):
    """per-frame robust z-scores of the similarities to every map image (median / 1.4826 MAD of the frame's profile)"""
    med = np.median(S, 1, keepdims=True); mad = np.median(np.abs(S - med), 1, keepdims=True) * 1.4826
    return (S - med) / np.maximum(mad, 1e-6)


def corr_weight(Z, power=2.0):
    """evidence weight of every frame = share of its similarity profile NOT predicted by the previous frame's profile:
    w_t = 1 - max(r_t, 0)^power, r_t = Pearson correlation of z_t and z_{t-1} over the map images (w_0 = 1). Label-free;
    adapts to frame rate, speed (a stopped vehicle repeats its view: w ~ 0) and to self-similar stretches."""
    a = Z - Z.mean(1, keepdims=True); a /= np.linalg.norm(a, axis=1, keepdims=True) + 1e-12
    r = np.r_[0.0, (a[1:] * a[:-1]).sum(1)]
    return 1.0 - np.clip(r, 0, 1) ** power, r


def log_lr(Z, beta):
    """log L_i = beta z_i - log mean_j exp(beta z_j) (exponential tilt of the frame's own profile; mean_j L_j = 1)"""
    a = beta * Z; m = a.max(1, keepdims=True)
    return a - (m + np.log(np.mean(np.exp(a - m), 1, keepdims=True)))


class OpenWorldFilter:
    def __init__(self, MP, g, band, q, s0=0.0, p_kid=1e-4, p_in=0.01, p_omega0=0.1, p_map0=0.5):
        self.MP = np.asarray(MP, float); self.d = self.MP.shape[1]; self.g, self.band, self.q, self.s0 = g, band, q, s0
        self.p_kid, self.p_in, self.p_omega0, self.p_map0 = p_kid, p_in, p_omega0, p_map0
        lo, hi = self.MP.min(0) - band - g, self.MP.max(0) + band + g
        self.origin = lo; self.shape = tuple(int(np.ceil((h - l) / g)) + 1 for l, h in zip(lo, hi))
        axes = [self.origin[k] + g * (np.arange(self.shape[k]) + 0.5) for k in range(self.d)]
        cen = np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, self.d)
        dist, _ = cKDTree(self.MP).query(cen); self.inband = (dist <= band).reshape(self.shape)
        self.nb = int(self.inband.sum()); self.cen = cen; self.tree = cKDTree(self.MP)
        # prior (start and kidnap re-draw), in-band part sums to 1 - p_omega0: p_map0 spread over the map images (cells in
        # proportion to their image counts), the rest uniform over the band; Omega gets p_omega0
        pm = np.bincount(self._cells(np.zeros(self.d)), None, int(np.prod(self.shape))).reshape(self.shape)
        self.prior = p_map0 * pm / pm.sum() + (1 - p_omega0 - p_map0) * self.inband / self.nb

    def _cells(self, phi):
        """flat cell index of every map image under the current phase (world pos of cell c = origin + g c + phi)"""
        c = np.floor((self.MP - self.origin - phi) / self.g).astype(int)
        c = np.clip(c, 0, np.array(self.shape) - 1)
        return np.ravel_multi_index(c.T, self.shape)

    def _shift(self, B, k, s):
        """shift array B by s whole cells along axis k (no wrap); returns shifted array and the mass pushed out"""
        if s == 0: return B, 0.0
        out = np.zeros_like(B); sl_src = [slice(None)] * self.d; sl_dst = [slice(None)] * self.d
        if s > 0: sl_src[k] = slice(0, -s); sl_dst[k] = slice(s, None); lost = B[tuple([slice(None)] * k + [slice(-s, None)])].sum()
        else: sl_src[k] = slice(-s, None); sl_dst[k] = slice(0, s); lost = B[tuple([slice(None)] * k + [slice(0, -s)])].sum()
        out[tuple(sl_dst)] = B[tuple(sl_src)]
        return out, float(lost)

    def run(self, logL, U, excl, ell=0.0, top_c=12, drift=0.0, w=None, q=None, closed=False, xmode="mean"):
        """logL (T, n) item log-LRs, U (T, d) odometry increments (world frame). Returns per frame: mass (largest posterior
        mass in an excl-disc around a map image), xhat (index of that image), cov (posterior mass within excl of ANY map
        image), om (mass of Omega), logml (log predictive mean LR = log p(z_t | z_<t) / p0(z_t))."""
        T, n = logL.shape; g, d = self.g, self.d; qq = self.q if q is None else q
        B = self.prior.copy(); om = self.p_omega0; prior = self.prior / self.prior.sum()
        phi = np.zeros(d); var = 0.0
        r = int(np.ceil(excl / g)); offs = np.stack(np.meshgrid(*[np.arange(-r, r + 1)] * d, indexing="ij"), -1).reshape(-1, d)
        offs = offs[np.linalg.norm(offs * g, axis=1) <= excl]                     # disc of radius excl (cell centres)
        mass, xhat, cov, oms, lml = np.zeros(T), np.zeros(T, int), np.zeros(T), np.zeros(T), np.zeros(T)
        shp = np.array(self.shape); Ls = 0.0                                       # Ls: odometry path since the last confident frame
        for t in range(T):
            if t > 0:                                                                # ---- predict
                u = U[t]; phi = phi + u; lost = 0.0
                for k in range(d):
                    s = int(np.trunc(phi[k] / g))
                    if s: B, l_ = self._shift(B, k, s); lost += l_; phi[k] -= s * g
                du = float(np.linalg.norm(u)); var += qq * du + self.s0 ** 2 + drift ** 2 * (2 * Ls * du + du * du); Ls += du
                # drift: systematic odometry error grows LINEARLY with the path since the last confident fix (sd = drift * Ls)
                if var >= (0.5 * g) ** 2:
                    m0 = B.sum(); B = gaussian_filter(B, np.sqrt(var) / g, mode="constant", truncate=3.0); lost += m0 - B.sum(); var = 0.0
                out = B[~self.inband].sum(); B[~self.inband] = 0.0; lost += out
                tot = B.sum() + om + lost
                B = (1 - self.p_kid) * B + self.p_kid * tot * prior * (1 - self.p_omega0)
                om = (1 - self.p_kid) * (om + lost) + self.p_kid * tot * self.p_omega0
                re = self.p_in * om; om -= re; B += re * prior
            # ---- update: mapped cells get the mean LR of their images, unmapped cells LR = 1
            if w is not None: lt = logL[t] * w[t]                               # per-frame evidence weight (e.g. 1 - r_t^2)
            else: lt = logL[t] if ell <= 0 or t == 0 else logL[t] * min(1.0, float(np.linalg.norm(U[t])) / ell)
            cid = self._cells(phi); mx = max(lt.max(), 0.0); Li = np.exp(lt - mx)
            sl = np.bincount(cid, Li, B.size); cn = np.bincount(cid, None, B.size)
            l0 = np.exp(-mx) * (1e-12 if closed else 1.0)                       # LR of unmapped cells / Omega (closed: ~0)
            Lc = np.full(B.size, l0); mapped = cn > 0; Lc[mapped] = sl[mapped] / cn[mapped]
            Bf = B.reshape(-1) * Lc; z = Bf.sum() + om * l0; lml[t] = np.log(z) + mx
            B = (Bf / z).reshape(self.shape); om = om * l0 / z
            # ---- decision statistics
            Bf = B.reshape(-1); mc = np.flatnonzero(mapped)
            cand = mc[np.argsort(-Bf[mc])[:top_c]] if len(mc) > top_c else mc
            best, bi, bcells = -1.0, -1, None
            for c in cand:
                cc = np.array(np.unravel_index(c, self.shape)); nbc = cc[None] + offs
                ok = np.all((nbc >= 0) & (nbc < shp), 1); fl = np.ravel_multi_index(nbc[ok].T, self.shape); ms = Bf[fl].sum()
                if ms > best: best, bi, bcells = ms, c, fl
            if xmode == "mean" and bcells is not None and best > 0:
                # report the map image nearest to the posterior MEAN of the disc (MMSE within the disc, snapped onto the map)
                wgt = Bf[bcells]; pos = self.origin + g * (np.stack(np.unravel_index(bcells, self.shape), 1) + 0.5) + phi
                xhat[t] = int(self.tree.query((wgt[:, None] * pos).sum(0) / wgt.sum())[1])
            else:
                items = np.flatnonzero(cid == bi); xhat[t] = items[np.argmax(lt[items])] if len(items) else -1
            mass[t] = best; oms[t] = om
            if best >= 0.5: Ls = 0.0
            cov[t] = Bf[mapped].sum()                                                # posterior mass on mapped cells
        return dict(mass=mass, xhat=xhat, cov=cov, om=oms, lml=lml)


def load_run(cache_dir, dump, ds, desc, seed):
    """navcache of (ds, desc, seed) (holes, odometry, labels; nav_demo --cache) + the query / reduced-map descriptors"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import vprlib as V
    z = dict(np.load(os.path.join(cache_dir, f"navcache_{ds.replace(':', '_')}_{desc}_s{seed}.npz"), allow_pickle=True))
    if ds.startswith("4sx:"):                       # natural off-map pair (Entry 30 caches; published file names lost the "+")
        nm = ds[4:].replace("+", ""); sc = ("office_loop", "old_town", "countryside")
        pair = next(f"{a}+{b}" for a in sc for b in sc if a != b and a + b == nm)
        ep = V.load_4s_cross(dump, desc, pair)
    elif ds.startswith("4s:"): ep = V.load_4seasons(dump, desc, ds[3:])
    elif ds == "boreas": ep = V.load_boreas(dump, desc)
    else: ep = V.LOADERS[ds](dump, desc)
    assert np.allclose(ep.q_pos, z["q_pos"]), "query order differs from the cache"
    M = ep.m[z["kidx"]].astype(np.float32)
    return z, ep.q, M


def main():
    cache_dir, dump, ds, desc, seed = sys.argv[1:6]; seed = int(seed)
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    betas = [float(b) for b in opt("--beta", "1").split(",")]; ellx = float(opt("--ellx", "0.4")); drift = float(opt("--drift", "0"))
    qxs, pkid = [float(x) for x in opt("--qx", "0.005,0.02,0.08").split(",")], float(opt("--pkid", "1e-12"))
    scales = [float(x) for x in opt("--scales", "1").split(",")]      # AUTOLOOP iteration 3: odometry scale hypotheses (bank = q x scale)
    bandx, pin = float(opt("--bandx", "1")), float(opt("--pin", "0.01")); temper = opt("--temper", "ell")
    closed = "--closed" in sys.argv; eps0 = float(opt("--eps0", "1e-3")); tag = opt("--tag", ""); xmode = opt("--xhat", "mean")
    eps_l = [float(e) for e in opt("--eps", "0.2,0.1,0.05,0.02,0.01,0.005,0.002,0.001,5e-4,2e-4,1e-4,1e-5").split(",")]
    fr_out, fo = opt("--frames", None), opt("--out", None)
    engine = opt("--engine", "numpy")                                  # numpy (reference) | torch (owf_torch.py; CUDA when available)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.argv = sys.argv[:1]
    import nav_demo as N
    from sc_eval import CFG
    z, Q, M = load_run(cache_dir, dump, ds, desc, seed)
    c = CFG["cmu"] if (ds.startswith("4s") or ds == "boreas") else CFG[ds.split(":")[0]]
    hz = list(z["hz"]); MP = z["MP"][:, hz].astype(float); U = z["U"][:, hz].astype(float); excl = float(z["excl"])
    sid, k = z["q_sid"], z["q_k"]; seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    g = excl / 5; band = bandx * c["block"]
    F = OpenWorldFilter(MP, g, band, qxs[0] * excl, p_kid=pkid, p_in=pin); ell = ellx * excl; nq = len(Q)
    inm, offm = z["inm"], z["offm"]; qp = z["q_pos"]
    res = {"ds": ds, "desc": desc, "seed": seed, "grid": list(F.shape), "n_band": F.nb, "runs": {}}
    print("grid", F.shape, "band cells", F.nb, flush=True)
    for beta in betas:
        t0 = time.time(); out = {k_: np.zeros(nq) for k_ in ("mass", "cov", "om", "lml", "qsel")}; xh = np.zeros(nq, int)
        for idx in seqs:
            Zs = robust_z(Q[idx].astype(np.float32) @ M.T); LL = log_lr(Zs, beta)
            wt = corr_weight(Zs, float(temper[4:] or 2))[0] if temper.startswith("corr") else None
            bank = [(qx, sc) for sc in scales for qx in qxs]
            if engine == "torch":                                          # same filter, all bank members in one GPU tensor (owf_torch.py)
                assert wt is None and drift == 0 and not closed and xmode == "mean", "--engine torch: default filter configuration only"
                import owf_torch as OT
                o = OT.run_bank(F, LL, U[idx], [(qx * excl, sc) for qx, sc in bank], excl, ell)
                xm = F.tree.query(o["mean"].reshape(-1, F.d))[1].reshape(len(bank), -1)
                rs = [dict(mass=o["mass"][j], xhat=xm[j], cov=o["cov"][j], om=o["om"][j], lml=o["lml"][j]) for j in range(len(bank))]
            else:
                rs = [F.run(LL, U[idx] * sc, excl, ell=ell, drift=drift, w=wt, q=qx * excl, closed=closed, xmode=xmode) for qx, sc in bank]
            # ONLINE self-calibration of the odometry noise (and scale): at frame t follow the filter with the largest cumulative log evidence
            # sum_{s<=t} log p(z_s | z_<s) (causal; ties -> the first = smallest q, first scale)
            cum = np.cumsum(np.stack([r_["lml"] for r_ in rs]), 1); ks = np.argmax(cum, 0); tt = np.arange(len(idx))
            for k_ in ("mass", "cov", "om", "lml"): out[k_][idx] = np.stack([r_[k_] for r_ in rs])[ks, tt]
            xh[idx] = np.stack([r_["xhat"] for r_ in rs])[ks, tt]; out["qsel"][idx] = np.array([b[0] for b in bank])[ks]
            out.setdefault("ssel", np.ones(nq))[idx] = np.array([b[1] for b in bank])[ks]
        dt = (time.time() - t0) / nq * 1e3
        xf = z["MP"][np.maximum(xh, 0)]; err = np.linalg.norm(xf - qp, axis=1); gd = inm & (err <= excl) & (xh >= 0)
        rows = []
        xf = z["MP"][np.maximum(xh, 0)]
        import position_audit as PA
        segs = PA.seg_classes(z, PA.OFF_D[ds.split(":")[0].replace("4s", "4s")])
        for e in eps_l:
            acc = (out["mass"] >= 1 - e) & (xh >= 0)
            m = N.rule_metrics(acc, gd, inm, offm, seqs, int(z["H"]))
            pos = {cl: (sum(bool(acc[g].any()) for g, c_ in segs if c_ == cl), sum(1 for _, c_ in segs if c_ == cl)) for cl in PA.CLASSES}
            rows.append(dict(eps=e, **{k_: m[k_] for k_ in ("recall", "FL", "seg_FAR", "reentry_delay")}, pos=pos))
        ceil = float(gd[inm].mean())
        # navigation (Kalman with the reported fixes, nav_demo.track) at the default operating point eps0
        acc0 = (out["mass"] >= 1 - eps0) & (xh >= 0)
        e_nav = N.track(acc0, xf, qp, z["o_q"], bool(z["real"]), seqs, list(z["hz"]), seed, ds.split(":")[0] == "nclt")
        m0 = N.rule_metrics(acc0, gd, inm, offm, seqs, int(z["H"]))
        default = dict(eps=eps0, **{k_: m0[k_] for k_ in ("recall", "FL", "seg_FAR", "n_seg", "ARL0", "reentry_delay")},
                       err_mean=float(np.nanmean(e_nav)), err_p95=float(np.nanpercentile(e_nav, 95)),
                       precision=float((acc0 & gd).sum() / max(acc0.sum(), 1)), frac_reported=float(acc0.mean()),
                       pos={cl: (int(sum(bool(acc0[g].any()) for g, c_ in segs if c_ == cl)), int(sum(1 for _, c_ in segs if c_ == cl))) for cl in PA.CLASSES})
        print(f"   DEFAULT eps {eps0:g}: recall {default['recall']:.3f} segFAR {default['seg_FAR']:.4f} FL {default['FL']:.4f} err_mean {default['err_mean']:.1f} m p95 {default['err_p95']:.1f}", flush=True)
        if fr_out:
            np.savez_compressed(fr_out + f"_b{beta:g}.npz", mass=out["mass"], cov=out["cov"], om=out["om"], lml=out["lml"], xhat=xh,
                                err=err, inm=inm, offm=offm, q_sid=sid, q_k=k, q_pos=qp, cond=z["cond"])
        res["runs"][str(beta)] = dict(ms_per_frame=dt, logml=float(out["lml"].sum()), map_correct_on=ceil, curve=rows, default=default,
                                      qsel={str(x): float(np.mean(out["qsel"] == x)) for x in qxs},
                                      ssel={str(x): float(np.mean(out.get("ssel", np.ones(nq)) == x)) for x in scales})
        print(f"{ds}/{desc} s{seed} beta {beta}: {dt:.1f} ms/frame logml {out['lml'].sum():.1f} MAP-correct(on) {ceil:.3f} q-share",
              {x: round(float(np.mean(out["qsel"] == x)), 2) for x in qxs}, flush=True)
        for rr in rows: print("   eps %-7g recall %.3f FL %.4f segFAR %.4f delay %.1f" % (rr["eps"], rr["recall"], rr["FL"], rr["seg_FAR"], rr["reentry_delay"]),
                              " ".join(f"{cl} {a}/{b}" for cl, (a, b) in rr["pos"].items()), flush=True)
    if fo: json.dump(res, open(fo, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
