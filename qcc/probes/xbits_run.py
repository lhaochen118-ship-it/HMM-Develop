"""Are idle x-register wires quadratic in the live wires at the ends of their idle intervals?

Usage: python xbits_run.py <dir with best_pub.kmx> """
import sys, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
from ksim import Kmx, simulate, pack
from redundancy import express, smallest_support
D = sys.argv[1]
c = Kmx.load(f'{D}/best_pub.kmx'); N = len(c.ops)
touch = {q: [] for q in range(c.num_qubits)}
for i, op in enumerate(c.ops):
    for q in op.qs: touch[q].append(i)
cands = []
for q in list(range(14)) + [23]:
    t = [0] + touch[q] + [N]
    a, b = max(zip(t[:-1], t[1:]), key=lambda p: p[1] - p[0])
    cands.append((q, a, b))
pts = {}
for q, a, b in cands: pts[a + 1] = None; pts[b] = None
xs = np.arange(1, 3133453, dtype=np.int64)
simulate(c, xs, c.registers['x'], seed=4, snap_at=pts)
valid = pack(np.ones(len(xs), bool))
for q, a, b in cands:
    for t, lab in ((a + 1, 'erase'), (b, 'recompute')):
        st = pts[t]
        live = [w for w in range(c.num_qubits) if w != q and (st[w] & valid).any()]
        r = express(st, q, live, 2, valid=valid)
        print(f'q{q} ({a},{b}) {lab}@{t}: live {len(live)} quad={None if r is None else r[:8]}', flush=True)
