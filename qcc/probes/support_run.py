"""Smallest support (<= 3 live wires) of the wires freed by the qubit-cover plan (needs cover.pkl).

Usage: python support_run.py <dir with best_pub.kmx> """
import pickle, sys, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
from ksim import Kmx, simulate, pack
from redundancy import smallest_support
D = sys.argv[1]
c = Kmx.load(f'{D}/best_pub.kmx')
cover = pickle.load(open(f'{D}/cover.pkl', 'rb'))
pts = {}
for (q, a, b), g in cover: pts[a + 1] = None; pts[b] = None
xs = np.arange(1, 3133453, dtype=np.int64)
simulate(c, xs, c.registers['x'], seed=3, snap_at=pts)
valid = pack(np.ones(len(xs), bool))
for (q, a, b), g in cover:
    for t, lab in ((a + 1, 'erase'), (b, 'recompute')):
        st = pts[t]
        live = [w for w in range(c.num_qubits) if w != q and (st[w] & valid).any()]
        r = smallest_support(st, q, live, 3)
        print(f'q{q} {lab}@{t}: {r}', flush=True)
