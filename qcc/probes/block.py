"""Phase and wire changes of an instruction block [A, B): is it a clean, coin-independent phase oracle?

Usage: python block.py <dir with best_pub.kmx> A B"""
import sys, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
from ksim import Kmx, simulate, unpack, angle_class
D = sys.argv[1]; A = int(sys.argv[2]); B = int(sys.argv[3])
c = Kmx.load(f'{D}/best_pub.kmx')
xs = np.arange(1, 3133453, dtype=np.int64)[::3]
n = len(xs)
res = {}
for seed in (7, 8):
    pts = {A: None, B: None}
    r = simulate(c, xs, c.registers['x'], seed=seed, snap_at=pts)
    qa, ha, ea, ra = pts[A]; qb, hb, eb, rb = pts[B]
    ang = np.array([float(a) / 2 for a in r.rot_angles[ra:rb]])
    ph = ((eb - ea) / 8.0 + 0.5 * unpack(hb ^ ha, n) + ang @ r.rot_bits[ra:rb]) % 1.0
    res[seed] = (qa, qb, ph)
qa, qb, ph = res[7]
same = [w for w in range(c.num_qubits) if np.array_equal(qa[w], qb[w])]
gone = [w for w in range(c.num_qubits) if qa[w].any() and not qb[w].any()]
new = [w for w in range(c.num_qubits) if qb[w].any() and not np.array_equal(qa[w], qb[w]) and w not in gone]
print('wires unchanged', len(same), 'erased in block', gone, 'changed/new', new)
print('rotations in block', rb - ra, 'phase coin-independent:', np.allclose(res[7][2], res[8][2], atol=1e-15))
d = (res[7][2] - res[8][2] + 0.5) % 1 - 0.5
print('max coin diff', np.abs(d).max())
np.save(f'{D}/blockphase_{A}_{B}.npy', ph)
