"""Batched open-world filter bank on a GPU (PyTorch, float64): same arithmetic as OpenWorldFilter.run in owf.py, for every member
of an odometry bank (q x scale) of ONE run at once.

Why: the decision thresholds go down to 1 - 1e-8 (owf_union tiers), so the belief must stay float64; every per-frame step of the
filter (whole-cell shift, Gaussian blur, band mask, kidnap / far-state bookkeeping, likelihood-ratio update, excl-disc masses of the
12 heaviest mapped cells) is an elementwise / gather / small-convolution operation on a (n_filters, *grid) tensor, so all bank
members advance in the same kernel launches. Everything that depends only on the odometry (phase, whole-cell shifts, process-noise
accumulator and blur times, distance weights of the evidence) is computed on the CPU before the loop.

Equivalence with owf.py (checked by owf_torch_check.py on design runs): shifts fill with zeros (mass pushed out of the array is lost, as
in _shift); the blur is scipy's gaussian_filter(mode="constant", truncate=3.0) written as two zero-padded 1-D convolutions with the same
normalised kernel; the lost mass is the mass before the prediction minus the in-band mass after it (the same sum, regrouped). Only the
filter with drift = 0 and the "mean" report position are implemented (the configuration of every OWF run since Entry 10).

API: run_bank(F, logL, U, members, excl, ell, device) -> dict of (n_members, T) arrays mass, cov, om, lml and (n_members, T, d) mean
(posterior mean of the reporting disc; the caller snaps it to the nearest map image, as owf.py does)."""
import numpy as np
import torch
import torch.nn.functional as TF


def _kernel1d(sigma, truncate=3.0):
    """scipy.ndimage._gaussian_kernel1d(sigma, 0, radius) with radius = int(truncate * sigma + 0.5)"""
    r = int(truncate * float(sigma) + 0.5); x = np.arange(-r, r + 1, dtype=float)
    k = np.exp(-0.5 / (sigma * sigma) * x * x); return k / k.sum()


def _odometry_plan(U, g, q, ell, d):
    """per frame: integer cell shift (d,), blur sigma in cells (0 = no blur), phase phi (d,), evidence weight. Mirrors the predict
    bookkeeping of OpenWorldFilter.run (drift = 0, s0 = 0)."""
    T = len(U); sh = np.zeros((T, d), np.int64); sig = np.zeros(T); ph = np.zeros((T, d)); w = np.ones(T)
    phi = np.zeros(d); var = 0.0; thr = (0.5 * g) ** 2
    for t in range(T):
        if t > 0:
            u = U[t]; phi = phi + u
            for k in range(d):
                s = int(np.trunc(phi[k] / g))
                if s: sh[t, k] = s; phi[k] -= s * g
            du = float(np.linalg.norm(u)); var += q * du
            if var >= thr: sig[t] = np.sqrt(var) / g; var = 0.0
            if ell > 0: w[t] = min(1.0, du / ell)
        ph[t] = phi
    return sh, sig, ph, w


def run_bank(F, logL, U, members, excl, ell, device=None, top_c=12):
    """F: OpenWorldFilter (grid, band, prior, p_kid, p_in, p_omega0); logL (T, n) item log-LRs of one sequence; U (T, d) odometry
    increments; members: list of (q, scale) (q in metres, as F.run's q); returns stacked outputs in member order."""
    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu")); f64 = torch.float64
    T, n = logL.shape; d = F.d; g = F.g; shape = tuple(F.shape); nb = len(members); ncell = int(np.prod(shape))
    assert d in (1, 2), "grid dimension"
    plans = [_odometry_plan(np.asarray(U, float) * sc, g, q, ell, d) for q, sc in members]
    SH = np.stack([p[0] for p in plans], 1); SIG = np.stack([p[1] for p in plans], 1)           # (T, nb, d), (T, nb)
    PH = np.stack([p[2] for p in plans], 1); W = np.stack([p[3] for p in plans], 1)            # (T, nb, d), (T, nb)
    # ---- static tensors
    prior0 = torch.tensor(F.prior, dtype=f64, device=dev)                                    # unnormalised start belief (in band)
    priorn = prior0 / prior0.sum()                                                           # kidnap / re-entry draw
    inband = torch.tensor(F.inband, device=dev)
    MPo = torch.tensor(F.MP - F.origin, dtype=f64, device=dev)                                 # (n, d)
    shp = torch.tensor(shape, device=dev)
    strides = torch.tensor([int(np.prod(shape[k + 1:])) for k in range(d)], device=dev)
    r = int(np.ceil(excl / g)); offs = np.stack(np.meshgrid(*[np.arange(-r, r + 1)] * d, indexing="ij"), -1).reshape(-1, d)
    offs = torch.tensor(offs[np.linalg.norm(offs * g, axis=1) <= excl], device=dev)            # (nO, d) disc offsets (cells)
    cen = [torch.arange(shape[k], dtype=f64, device=dev) for k in range(d)]
    LL = torch.tensor(np.asarray(logL), device=dev)                                          # float32 (as computed by owf.log_lr)
    Wt = torch.tensor(W, dtype=LL.dtype, device=dev); PHt = torch.tensor(PH, dtype=f64, device=dev)
    pk, pin, po = F.p_kid, F.p_in, F.p_omega0
    # ---- state
    B = prior0.expand(nb, *shape).clone(); om = torch.full((nb,), F.p_omega0, dtype=f64, device=dev)
    o_mass = torch.zeros((nb, T), dtype=f64, device=dev); o_cov = torch.zeros_like(o_mass); o_om = torch.zeros_like(o_mass)
    o_lml = torch.zeros_like(o_mass); o_mean = torch.zeros((nb, T, d), dtype=f64, device=dev)
    o_best = torch.zeros((nb, T), dtype=torch.long, device=dev)
    ar = [torch.arange(shape[k], device=dev) for k in range(d)]; bi = torch.arange(nb, device=dev)
    for t in range(T):
        if t > 0:                                                                            # ---- predict
            m_prev = B.reshape(nb, -1).sum(1) + om
            s = SH[t]
            if s.any():                                                                      # whole-cell shift, zero fill (per member)
                st = torch.tensor(s, device=dev)
                if d == 1:
                    src = ar[0][None, :] - st[:, :1]; ok = (src >= 0) & (src < shape[0])
                    B = torch.gather(B, 1, src.clamp(0, shape[0] - 1)) * ok
                else:
                    s0_ = ar[0][None, :] - st[:, :1]; s1_ = ar[1][None, :] - st[:, 1:2]
                    ok = ((s0_ >= 0) & (s0_ < shape[0]))[:, :, None] & ((s1_ >= 0) & (s1_ < shape[1]))[:, None, :]
                    B = B[bi[:, None, None], s0_.clamp(0, shape[0] - 1)[:, :, None], s1_.clamp(0, shape[1] - 1)[:, None, :]] * ok
            sg = SIG[t]
            if (sg > 0).any():                                                               # Gaussian blur where the noise accumulator fired
                ks = [_kernel1d(x) if x > 0 else np.ones(1) for x in sg]; R = max(len(k) for k in ks) // 2
                Kt = np.zeros((nb, 2 * R + 1))
                for j, k in enumerate(ks): rr = len(k) // 2; Kt[j, R - rr:R + rr + 1] = k
                Kt = torch.tensor(Kt, dtype=f64, device=dev)
                if d == 1:
                    B = TF.conv1d(B[None], Kt[:, None, :], padding=R, groups=nb)[0]
                else:
                    x = TF.conv2d(B[None], Kt[:, None, :, None], padding=(R, 0), groups=nb)
                    B = TF.conv2d(x, Kt[:, None, None, :], padding=(0, R), groups=nb)[0]
            B = B * inband                                                                    # mass leaving the band -> Omega
            lost = m_prev - om - B.reshape(nb, -1).sum(1)
            tot = B.reshape(nb, -1).sum(1) + om + lost
            B = (1 - pk) * B + (pk * tot * (1 - po)).view(nb, *[1] * d) * priorn
            om = (1 - pk) * (om + lost) + pk * tot * po
            re = pin * om; om = om - re; B = B + re.view(nb, *[1] * d) * priorn
        # ---- update: mapped cells get the mean LR of their images, unmapped cells LR = 1
        # dtypes as in owf.py: the item log-LRs are float32 (float32 similarities), so lt, mx, Li = exp(lt - mx) and l0 are float32, the
        # per-cell sums are float64 (np.bincount), and Lc = np.full(.., l0) is a float32 array, i.e. every cell LR is rounded to float32
        lt = LL[t][None, :] * Wt[t][:, None] if t > 0 else LL[t][None, :].expand(nb, n)      # (nb, n) float32
        mx = torch.clamp(lt.max(1).values, min=0.0)
        Li = torch.exp((lt - mx[:, None]).to(f64)).to(torch.float32)                          # correctly rounded float32 exp
        c = torch.floor((MPo[None] - PHt[t][:, None, :]) / g).long()                           # (nb, n, d) image cells under the phase
        c = torch.minimum(torch.clamp(c, min=0), shp - 1)
        cid = (c * strides).sum(-1)                                                          # flat cell index
        sl = torch.zeros((nb, ncell), dtype=f64, device=dev).scatter_add_(1, cid, Li.to(f64))
        cn = torch.zeros((nb, ncell), dtype=f64, device=dev).scatter_add_(1, cid, torch.ones_like(Li, dtype=f64))
        l0 = torch.exp((-mx).to(f64)).to(torch.float32).to(f64)
        mapped = cn > 0
        Lc = torch.where(mapped, sl / torch.where(mapped, cn, torch.ones_like(cn)), l0[:, None]).to(torch.float32).to(f64)
        mx = mx.to(f64)
        Bf = B.reshape(nb, -1) * Lc; z = Bf.sum(1) + om * l0
        o_lml[:, t] = torch.log(z) + mx
        Bf = Bf / z[:, None]; om = om * l0 / z; B = Bf.view(nb, *shape)
        # ---- decision statistics: largest excl-disc mass among the top_c heaviest mapped cells
        cand = torch.topk(torch.where(mapped, Bf, torch.full_like(Bf, -1.0)), top_c, dim=1).indices      # (nb, top_c), heaviest first
        cc = torch.stack([(cand // strides[k]) % shp[k] for k in range(d)], -1)                # (nb, top_c, d)
        nbc = cc[:, :, None, :] + offs[None, None]                                           # (nb, top_c, nO, d)
        ok = ((nbc >= 0) & (nbc < shp)).all(-1)
        fl = (torch.minimum(torch.clamp(nbc, min=0), shp - 1) * strides).sum(-1)              # (nb, top_c, nO)
        vals = torch.gather(Bf, 1, fl.reshape(nb, -1)).reshape(fl.shape) * ok
        ms = vals.sum(-1)                                                                    # (nb, top_c)
        best = torch.argmax(ms, 1)                                                           # first maximum (owf.py: strict >)
        o_mass[:, t] = ms[bi, best]; o_best[:, t] = cand[bi, best]
        wgt = vals[bi, best]                                                                 # (nb, nO)
        pos = (nbc[bi, best].to(f64) + 0.5) * g + PHt[t][:, None, :]                          # cell centre (relative to origin) + phase
        o_mean[:, t] = (wgt[:, :, None] * pos).sum(1) / torch.clamp(wgt.sum(1), min=1e-300)[:, None] + torch.tensor(F.origin, dtype=f64, device=dev)
        o_cov[:, t] = (Bf * mapped).sum(1); o_om[:, t] = om
    cpu = lambda x: x.detach().cpu().numpy()
    return dict(mass=cpu(o_mass), cov=cpu(o_cov), om=cpu(o_om), lml=cpu(o_lml), mean=cpu(o_mean), best=cpu(o_best))
