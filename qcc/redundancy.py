"""Is a wire, at a given moment, a low-degree GF(2) function of the other live wires?

`express(state, target, live, degree)` solves `state[target] = sum of monomials (degree <= 2) of
state[live]` on a shot sample and confirms on all shots. Used to find wires that can be erased
(HMR + Clifford repair if degree <= 2) and recomputed (one Toffoli per quadratic term) so that a
qubit can be freed over an idle interval.
"""

from __future__ import annotations

import itertools

import numpy as np

from peephole import gf2_solve

SAMPLE_WORDS = 64


def express(state: np.ndarray, target: int, live: list[int], degree: int = 2, words=None, valid=None):
    """Returns the list of monomials (tuples of wire indices; () = constant) or None."""
    W = state.shape[1]
    if words is None:
        words = np.random.default_rng(1).choice(W - 1, min(SAMPLE_WORDS, W - 1), replace=False)
    mons = [()] + [(w,) for w in live]
    if degree >= 2:
        mons += list(itertools.combinations(live, 2))
    cols = []
    for m in mons:
        v = np.full(len(words), ~np.uint64(0))
        for w in m:
            v = v & state[w][words]
        cols.append(v)
    A = np.unpackbits(np.stack(cols).view(np.uint8), axis=1, bitorder='little').T.astype(bool)
    y = np.unpackbits(state[target][words].view(np.uint8), bitorder='little').astype(bool)
    z = gf2_solve(A, y)
    if z is None:
        return None
    sel = [mons[k] for k in np.flatnonzero(z)]
    acc = np.zeros(W, dtype=np.uint64)
    for m in sel:
        v = np.full(W, ~np.uint64(0))
        for w in m:
            v = v & state[w]
        acc ^= v
    diff = acc ^ state[target]
    if valid is not None:
        diff &= valid
    return sel if not diff.any() else None


def smallest_support(state: np.ndarray, target: int, live: list[int], max_size: int = 4, words=None):
    """Smallest set S of live wires such that `target` is a function of S on the sampled shots.

    Returns (S, truth table dict) or None. Exhaustive over subsets by increasing size.
    """
    W = state.shape[1]
    if words is None:
        words = np.random.default_rng(2).choice(W - 1, min(256, W - 1), replace=False)
    bits = np.unpackbits(np.ascontiguousarray(state[:, words]).view(np.uint8), axis=1, bitorder='little').astype(np.int64)
    y = bits[target]
    for k in range(1, max_size + 1):
        for S in itertools.combinations(live, k):
            key = np.zeros(bits.shape[1], dtype=np.int64)
            for j, w in enumerate(S):
                key |= bits[w] << j
            # consistent iff every key maps to a single y
            lo = np.full(1 << k, 2)
            ok = True
            for kv in (0, 1):
                seen = np.unique(key[y == kv])
                if kv == 0:
                    zeros = set(seen.tolist())
                else:
                    if zeros & set(seen.tolist()):
                        ok = False
            if ok:
                table = {int(kk): int(y[key == kk][0]) for kk in np.unique(key)}
                return S, table
    return None
