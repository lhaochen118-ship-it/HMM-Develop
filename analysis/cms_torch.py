"""GPU backend (torch, float64) of the TAO route test used by every CMS statistic (Entry 37).

cms_vec._route_cost evaluates, for B frames x Kh hypotheses x 2 directions x n_w window frames, the anchor traces along the map route
(np.interp on the route key), a batched 2-D Procrustes residual, Huber, trimmed mean, and the anchor appearance look-up (searchsorted
on each window frame's key-sorted top-K table, rule p-2..p+1 within tol). It is ~70 % of the forward counterfactual null of Entry 37
(the system's presence statistics re-run on every virtual run's altered map). This module runs the SAME arithmetic on the GPU in
float64, op by op:
  interp      numpy's arr_interp: j = last index with xp[j] <= x (searchsorted right - 1), y = slope (x - xp[j]) + fp[j] with
              slope = (fp[j+1] - fp[j]) / (xp[j+1] - xp[j]); y = fp[j] when x == xp[j]; fp[0] below the range, fp[-1] at / above its end
  look-up     torch.searchsorted (left) on the +inf padded rows == cms_vec._searchsorted_rows; clip to [0, CNT - 1]; same offsets
  masks       anchor traces leave the chunk from the first point inside the removed region (cumulative OR along the window):
              CorridorMask (full surgery: within rho of an anchor of the row) and cms_fwd.HoleMask (forward surgery: Voronoi hole of a
              virtual run) both provide .torch(q) with the exact distance tests of their numpy __call__
Only the order of floating-point summations (means over the window) and the last ulp of atan2 / cos / sin may differ from numpy
(~1e-16 relative); outputs are compared with the numpy path in cms_fwd.py --check-presence / --check-backend.
Selection: CMS_DEVICE=cuda (default when a GPU is visible) | cpu (torch on CPU: equivalence tests) | numpy (never torch)."""
import os
import numpy as np
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")   # many processes per GPU: less fragmentation

BIG = 1e7
_STATE = {}
_DEV = [None]


def device():
    """torch device of the route test, or None for the numpy path"""
    if _DEV[0] is not None: return _DEV[0] or None
    want = os.environ.get("CMS_DEVICE", "auto")
    dev = ""
    if want != "numpy":
        try:
            import torch
            if want in ("auto", "cuda") and torch.cuda.is_available(): dev = "cuda"
            elif want == "cpu": dev = "cpu"
        except Exception:
            dev = ""
    _DEV[0] = dev
    return dev or None


class RouteT:
    """route coordinates of a map on the device (float64)"""

    def __init__(self, S, dev):
        import torch
        f = lambda x: torch.as_tensor(np.ascontiguousarray(x, dtype=np.float64), device=dev)
        self.torch, self.dev = torch, dev
        self.P = f(S["P"]); self.key = f(S["key_all"]); self.cid = f(S["cid"]); self.arc = f(S["arc"])
        self.lo = f(S["lo_arc"]); self.hi = f(S["hi_arc"])

    def interp(self, x):
        """np.interp(x, key_all, P[:, d]) for every d: x (...,) -> (..., d)"""
        torch = self.torch; xf = x.reshape(-1); xp = self.key; n = xp.shape[0]; P = self.P
        j = torch.searchsorted(xp, xf, right=True) - 1
        jc = j.clamp(0, n - 2)
        x0 = xp[jc]; x1 = xp[jc + 1]; f0 = P[jc]; f1 = P[jc + 1]
        slope = (f1 - f0) / (x1 - x0)[:, None]
        y = slope * (xf - x0)[:, None] + f0
        y = torch.where((xf == x0)[:, None], f0, y)
        y = torch.where((j < 0)[:, None], P[0].expand_as(y), y)
        y = torch.where((j >= n - 1)[:, None], P[n - 1].expand_as(y), y)
        return y.reshape(x.shape + (P.shape[1],))


def state(S):
    dev = device(); k = (id(S), dev)
    if k not in _STATE:
        if len(_STATE) > 8: _STATE.clear()
        _STATE[k] = RouteT(S, dev)
    return _STATE[k]


def _lookup(R, TK, TS, FB, CNT, keys, tol=4.0):
    """cms_vec._lookup on the device: TK, TS (B, n_w, Kt), FB, CNT (B, n_w), keys (B, Kh, n_w) -> (B, Kh, n_w)"""
    torch = R.torch
    kq = keys.transpose(1, 2).contiguous()                             # (B, n_w, Kh)
    p = torch.searchsorted(TK, kq)                                       # left
    best = FB[:, :, None].expand_as(kq).clone()
    hi = (CNT - 1).clamp(min=0)[:, :, None]
    for off in (-2, -1, 0, 1):
        pp = torch.minimum((p + off).clamp(min=0), hi)
        ks = torch.gather(TK, 2, pp); ss = torch.gather(TS, 2, pp)
        ok = (ks - kq).abs() <= tol
        best = torch.where(ok, torch.maximum(best, ss), best)
    return best.transpose(1, 2)


def route_cost(S, J, hv, dl, ow, look, trim=0.75, delta=8.0, wapp=2.0, cmask=None):
    """cms_vec._route_cost on the device; same inputs (numpy), same outputs (numpy): cost (B,), winner map row (B,), anchors (B, n_w, d)"""
    R = state(S); torch = R.torch; dev = R.dev
    T = lambda x, dt=torch.float64: torch.as_tensor(np.ascontiguousarray(x), dtype=dt, device=dev)
    Jt = T(J, torch.int64); hvt = T(hv, torch.bool); dlt = T(dl); owt = T(ow)
    TK, TS, FB = T(look[0]), T(look[1]), T(look[2]); CNT = T(look[3], torch.int64)
    Bn, Kh = Jt.shape; n_w = dlt.shape[1]; dd = R.P.shape[1]
    c, a0, lo, hi = R.cid[Jt], R.arc[Jt], R.lo[Jt], R.hi[Jt]
    pc = owt - owt.mean(1, keepdim=True)                                # (B, n_w, d)
    m = max(1, int(np.ceil(trim * n_w))); ar = torch.arange(Bn, device=dev)
    best_C = torch.full((Bn,), float("inf"), dtype=torch.float64, device=dev); best_k = torch.zeros(Bn, dtype=torch.int64, device=dev); best_q = None
    for sgn in (1.0, -1.0):
        aa = a0[:, :, None] - sgn * dlt[:, None, :]                     # (B, Kh, n_w)
        inside = (aa >= lo[..., None]) & (aa <= hi[..., None])
        keys = c[..., None] * BIG + aa
        q = R.interp(keys)                                              # (B, Kh, n_w, d)
        qc = q - q.mean(2, keepdim=True)
        if dd == 1:
            res = (qc[..., 0] - pc[:, None, :, 0]).abs()
        else:
            p0, p1 = pc[:, None, :, 0], pc[:, None, :, 1]; q0, q1 = qc[..., 0], qc[..., 1]
            a_ = (p0 * q0 + p1 * q1).sum(2); b_ = (p0 * q1 - p1 * q0).sum(2)
            th = torch.atan2(b_, a_); cs, sn = torch.cos(th)[..., None], torch.sin(th)[..., None]
            rx = cs * p0 - sn * p1; ry = sn * p0 + cs * p1
            res = torch.sqrt((q0 - rx) ** 2 + (q1 - ry) ** 2)
        hub = torch.where(res <= delta, 0.5 * res ** 2, delta * (res - 0.5 * delta)) / delta ** 2
        if cmask is not None:
            inside = inside & ~(torch.cumsum(cmask.torch(q).to(torch.int32), dim=2) > 0)
        geo = torch.sort(torch.where(inside, hub, torch.full_like(hub, 10.0)), dim=2).values[..., :m].mean(2)
        app = _lookup(R, TK, TS, FB, CNT, keys)
        C = geo + wapp * (1.0 - app).mean(2)
        C = torch.where(hvt, C, torch.full_like(C, float("inf")))
        k = torch.argmin(C, 1); Ck = C[ar, k]
        upd = Ck < best_C
        best_C = torch.where(upd, Ck, best_C); best_k = torch.where(upd, k, best_k)
        qk = q[ar, k]
        best_q = qk if best_q is None else torch.where(upd[:, None, None], qk, best_q)
    bk = best_k.cpu().numpy()
    return best_C.cpu().numpy(), np.asarray(J)[np.arange(Bn), bk], best_q.cpu().numpy()


class CorridorMask:
    """full-surgery removed region of cms_vec: within rho of some anchor A[b, k] of the row (exact test sqrt(min_k |X - A_k|^2) <= rho)"""

    def __init__(self, A, rho):
        self.A, self.rho = A, rho

    def __call__(self, q):
        import cms_vec as CV
        return CV.in_corridor(q, self.A, self.rho)

    def torch(self, q):
        import torch
        A = torch.as_tensor(np.ascontiguousarray(self.A, dtype=np.float64), device=q.device)   # (B, n_a, d)
        Bn = q.shape[0]; qf = q.reshape(Bn, -1, q.shape[-1]); D = 0.0
        for d in range(q.shape[-1]): D = D + (qf[:, :, None, d] - A[:, None, :, d]) ** 2
        return (torch.sqrt(D.min(-1).values) <= self.rho).reshape(q.shape[:-1])
