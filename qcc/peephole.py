"""Find Toffoli-like gates whose action is an affine GF(2) function of the live qubits.

For every CCX / CCZ / CSWAP the probe takes the vector it acts with, `p = a & b & mask` (CSWAP:
`c & (a ^ b) & mask`), over all inputs x and random HMR outcomes, and solves `p = c0 + sum z_i q_i`
over the other qubits on a shot sample, then confirms on every shot. Such a CCX can become CNOTs
(saving one Toffoli); a CSWAP with `p == 0` can be deleted. Candidates are printed as JSON lines;
`apply` rewrites them and the result must still pass the official verifier (other HMR seeds).
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from ksim import Kmx, Op, simulate

SAMPLE_WORDS = 96


def gf2_solve(A: np.ndarray, y: np.ndarray):
    """Solve A z = y over GF(2); A is bool[rows, cols]. Returns z (uint8[cols]) or None."""
    A = A.astype(np.uint8)
    y = y.astype(np.uint8)
    rows, cols = A.shape
    piv, r = [], 0
    for c in range(cols):
        nz = np.flatnonzero(A[r:, c])
        if not len(nz):
            continue
        p = r + nz[0]
        A[[r, p]] = A[[p, r]]
        y[[r, p]] = y[[p, r]]
        hit = np.flatnonzero(A[:, c])
        hit = hit[hit != r]
        A[hit] ^= A[r]
        y[hit] ^= y[r]
        piv.append(c)
        r += 1
        if r == rows:
            break
    if y[r:].any():
        return None
    z = np.zeros(cols, dtype=np.uint8)
    z[piv] = y[:len(piv)]
    return z


def find(circ: Kmx, seed: int, words: np.ndarray):
    xs = np.arange(1, 3 * (2**10 - 2)**2 + 1, dtype=np.int64)
    found = {}

    def probe(idx, op, q, m):
        a, b2, c = (q[i] for i in op.qs)
        p = (a & (b2 ^ c) if op.name == 'CSWAP' else a & b2) & m
        if not p.any():
            found[idx] = ('zero', [])
            return
        if op.name == 'CSWAP':
            return
        others = [i for i in range(len(q)) if i not in op.qs] if op.name == 'CCX' else []
        if not others:
            return
        # bit matrix over sampled shots: columns = const + other qubits
        cols = [np.full(len(words), ~np.uint64(0))] + [q[i][words] for i in others]
        A = np.unpackbits(np.stack(cols).view(np.uint8), axis=1, bitorder='little').T.astype(bool)
        y = np.unpackbits(p[words].view(np.uint8), bitorder='little').astype(bool)
        z = gf2_solve(A, y)
        if z is None:
            return
        sel = [others[k - 1] for k in np.flatnonzero(z[1:]) + 1]
        acc = np.full_like(p, ~np.uint64(0)) if z[0] else np.zeros_like(p)
        for i in sel:
            acc ^= q[i]
        if not (((acc & m) ^ p) & _VALID[0]).any():
            found[idx] = ('affine', [int(z[0])] + sel)

    W = (len(xs) + 63) // 64
    _VALID[0] = np.full(W, ~np.uint64(0))
    _VALID[0][-1] = (np.uint64(1) << np.uint64(len(xs) % 64)) - np.uint64(1) if len(xs) % 64 else ~np.uint64(0)
    simulate(circ, xs, circ.registers['x'], seed=seed, probe=probe)
    return found


_VALID = [None]


def apply(circ: Kmx, cands: dict) -> Kmx:
    ops = []
    for idx, op in enumerate(circ.ops):
        if idx not in cands:
            ops.append(op)
            continue
        kind, terms = cands[idx]
        if kind == 'zero':
            continue
        t = op.qs[2]
        if terms[0]:
            ops.append(Op('X', (t,), (), op.cond))
        ops += [Op('CX', (s, t), (), op.cond) for s in terms[1:]]
    return Kmx(ops, circ.num_qubits, circ.num_bits, circ.registers)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit')
    ap.add_argument('--seeds', type=int, default=3)
    ap.add_argument('--out')
    args = ap.parse_args()
    circ = Kmx.load(args.circuit)
    W = (3 * (2**10 - 2)**2 + 63) // 64
    words = np.random.default_rng(0).choice(W - 1, SAMPLE_WORDS, replace=False)
    common = None
    for seed in range(args.seeds):
        f = find(circ, seed + 11, words)
        common = f if common is None else {k: v for k, v in common.items() if f.get(k) == v}
        print(f'seed {seed}: {len(f)} candidates, {len(common)} stable', flush=True)
    for k, v in sorted(common.items()):
        print(json.dumps({'idx': k, 'op': circ.ops[k].name, 'kind': v[0], 'terms': v[1]}))
    if args.out and common:
        open(args.out, 'w').write(apply(circ, common).dump())
        print('wrote', args.out)


if __name__ == '__main__':
    main()
