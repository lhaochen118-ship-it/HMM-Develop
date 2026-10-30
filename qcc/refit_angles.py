"""LP refit of the fine rotation angles of an invsqrt circuit to maximize the phase margin.

The tracked phase is `phase8(x)/8 + sum_r theta_r * B_r(x)` turns, with `B_r(x)` the bit rotation `r`
acts on (see ksim). The verifier prices each rotation at `0.56 log2(1/eps) + 5.3` T with
`eps = pi * margin / n_rot`, `margin = min_x tol(x) - |error(x)|`, so a larger margin is cheaper.
Around the current angles the error is linear in `d = theta - theta0`; we solve

    max t  s.t.  |e0(x) + B(x) d| <= tol(x) - t   for all x

by cutting planes over x (HiGHS), then optionally test dropping rotations (`--drop`).
Writes the circuit with refitted angles to `--out`.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
from fractions import Fraction

import numpy as np
from scipy.optimize import linprog

from ksim import Kmx, simulate

T_TOFF = 4
UNIT = 2.0**-40  # LP works in units of 2^-40 turns (HiGHS tolerances are absolute)


def rotation_cost(margin_turns: float, n_rot: int) -> float:
    """Toffoli-equivalents spent on fine rotations."""
    eps = math.pi * margin_turns / n_rot
    return n_rot * (0.56 * math.log2(1 / eps) + 5.3) / T_TOFF if eps > 0 else math.inf


def solve(e0, B, tol, free, iters=60, batch=5000):
    """Cutting-plane LP; returns (d, margin) in turns, d only on `free` rotations."""
    e0, tol = e0 / UNIT, tol / UNIT
    rows = np.unique(np.concatenate([np.argsort(tol - np.abs(e0))[:batch], [np.argmax(np.abs(e0) / tol)]]))
    Bf = B[free].T.astype(float)  # shots x free
    nf = len(free)
    for _ in range(iters):
        Bs = Bf[rows]
        # vars: d (nf), t ; maximize t -> minimize -t
        A = np.block([[Bs, np.ones((len(rows), 1))], [-Bs, np.ones((len(rows), 1))]])
        ub = np.concatenate([tol[rows] - e0[rows], tol[rows] + e0[rows]])
        res = linprog(np.r_[np.zeros(nf), -1.0], A_ub=A, b_ub=ub,
                      bounds=[(-1e5, 1e5)] * nf + [(None, None)], method='highs')
        if res.status != 0:
            raise RuntimeError(res.message)
        d, t = res.x[:nf], res.x[-1]
        err = e0 + Bf @ d
        slack = tol - np.abs(err)
        bad = np.flatnonzero(slack < t - 1e-6)
        if len(bad) == 0:
            return d * UNIT, float(slack.min()) * UNIT
        rows = np.unique(np.concatenate([rows, bad[np.argsort(slack[bad])[:batch]]]))
    return d * UNIT, float((tol - np.abs(e0 + Bf @ d)).min()) * UNIT


def targets(xs):
    """(target mod 1, tol) in turns, as the verifier computes them; cached on disk."""
    cache = os.path.join(os.environ.get('QCC_CACHE', '/tmp'), f'invsqrt_targets_{len(xs)}.npz')
    if os.path.exists(cache):
        z = np.load(cache)
        return z['tgt'], z['tol']
    mask65 = (1 << 65) - 1  # r = floor(2^65 / sqrt(x)); target = r / 2^65 mod 1
    rs = [math.isqrt((1 << 130) // v) for v in xs.tolist()]
    tgt = np.array([(r & mask65) / 2.0**65 for r in rs])
    tol = np.array([(r >> 25) / 2.0**64 for r in rs])  # floor(r / 2^25) units of 2^-64
    np.savez(cache, tgt=tgt, tol=tol)
    return tgt, tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit')
    ap.add_argument('--out')
    ap.add_argument('--drop', action='store_true', help='greedily try removing each rotation')
    args = ap.parse_args()

    circ = Kmx.load(args.circuit)
    xs = np.arange(1, 3 * (2**10 - 2)**2 + 1, dtype=np.int64)
    r = simulate(circ, xs, circ.registers['x'], seed=1)
    theta0 = np.array([float(a) / 2 for a in r.rot_angles])
    B = r.rot_bits
    tgt, tol = targets(xs)
    phase = (r.phase8 / 8.0 + theta0 @ B) % 1.0
    e0 = (phase - tgt + 0.5) % 1.0 - 0.5
    m0 = float((tol - np.abs(e0)).min())
    n = len(theta0)
    print(f'baseline margin {m0:.4e}  rot cost {rotation_cost(m0, n):.2f}')

    free = list(range(n))
    d, m = solve(e0, B, tol, free)
    print(f'refit margin {m:.4e}  rot cost {rotation_cost(m, n):.2f}')
    theta = theta0.copy()
    theta[free] += d

    if args.drop:
        keep = list(range(n))
        dropped = []
        for k in sorted(range(n), key=lambda k: abs(theta0[k])):
            trial = [j for j in keep if j != k]
            e_k = e0 - B[dropped + [k]].T @ theta0[dropped + [k]]
            try:
                d2, m2 = solve(e_k, B, tol, trial)
            except RuntimeError:
                continue
            if m2 > 0 and rotation_cost(m2, len(trial)) < rotation_cost(m, len(keep)):
                keep, m = trial, m2
                dropped.append(k)
                theta = theta0.copy()
                theta[dropped] = 0.0
                theta[trial] += d2
                print(f'dropped rotation {k}: margin {m:.4e} cost {rotation_cost(m, len(keep)):.2f}')

    if args.out:
        it = iter(range(n))
        for idx in r.rot_ops:
            k = next(it)
            circ.ops[idx].angle = Fraction(float(theta[k] * 2))
        circ.ops = [op for i, op in enumerate(circ.ops)
                    if not (op.name == 'Z_POW' and op.angle == 0)]
        open(args.out, 'w').write(circ.dump())
        print('wrote', args.out)


if __name__ == '__main__':
    main()
