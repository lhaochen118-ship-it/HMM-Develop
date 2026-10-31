"""CCZ gates whose product a*b*c is 0, a single live wire or an AND of two live wires (Clifford-replaceable).

Usage: python ccz_fast.py <dir with best_pub.kmx> """
import sys, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
from ksim import Kmx, simulate, pack
D = sys.argv[1]
c = Kmx.load(f'{D}/best_pub.kmx')
xs = np.arange(1, 3133453, dtype=np.int64)
valid = pack(np.ones(len(xs), bool))
W = len(valid)
words = np.random.default_rng(0).choice(W - 1, 96, replace=False)
hits, seen = [], 0
def probe(idx, op, q, m):
    global seen
    if op.name != 'CCZ':
        return
    seen += 1
    a, b, cc = op.qs
    p = q[a] & q[b] & q[cc] & m & valid
    ps = p[words]
    live = [w for w in range(len(q)) if (q[w] & valid).any()]
    S = q[live][:, words]
    cand = []
    if not ps.any():
        cand.append(())
    for i in range(len(live)):
        if np.array_equal(S[i], ps): cand.append((live[i],))
    pair = S[:, None, :] & S[None, :, :]
    eq = (pair == ps).all(axis=2)
    for i, j in zip(*np.nonzero(np.triu(eq, 1))):
        cand.append((live[i], live[j]))
    for t in cand:
        v = np.full(W, ~np.uint64(0)) if t else np.zeros(W, np.uint64)
        for w in t: v = v & q[w]
        if t: v &= valid
        if np.array_equal(v, p):
            hits.append((idx, op.qs, op.cond, t)); print('HIT', idx, op.qs, op.cond, t, flush=True); break
simulate(c, xs, c.registers['x'], seed=9, probe=probe)
print('checked', seen, 'CCZ; replaceable:', len(hits), flush=True)
