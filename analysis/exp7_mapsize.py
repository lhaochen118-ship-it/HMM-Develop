"""E7 — how large must the map be? Keep a spatially contiguous fraction of RobotCar/CMU map area around the centroid
(and the queries whose nearest map item lies there), then rerun the full comparison. Usage: exp7_mapsize.py <dump> <rc|cmu>"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, eval_all as EA
from sc_eval import CFG
dump, ds = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
P = ep.m_pos[:, :2]; d0 = np.linalg.norm(P - np.median(P, 0), axis=1)
nn = np.array([np.argmin(((ep.m_pos - q) ** 2).sum(1)) for q in ep.q_pos])
out = {}
for frac in (0.25, 0.5, 1.0):
    keep = d0 <= np.quantile(d0, frac); qsel = np.where(keep[nn])[0]
    e = ep.subset_map(keep).subset_q(qsel)
    rows, meta = EA.evaluate(e, c, desc)
    R = {r["method"]: r for r in rows if abs(r["alpha"] - 0.05) < 1e-9}
    ext = np.ptp(e.m_pos[:, :2], 0)
    out[frac] = {"n_map": int(keep.sum()), "extent_m": ext.tolist(), "meta": meta, "rows": {k: R[k] for k in R}}
    s, l, o = R["SelfCal-AA[combo AND z_gap+c]"], R["LabelCal[maxsim] (day->all)"], R["Oracle[maxsim] (labels per cond.)"]
    print(f"{ds} map {frac:.2f} ({keep.sum()} imgs, {ext[0]:.0f}x{ext[1]:.0f} m, null n={meta['n_null']}, off n={meta['n_off']}): "
          f"SelfCal-AA FAR {s['FAR']:.3f} viol {s['n_viol']}/{s['n_cond']} TPR {s['TPR']:.3f} alias {s['alias_acc']:.3f} | "
          f"LabelCal viol {l['n_viol']}/{l['n_cond']} | oracle TPR {o['TPR']:.3f}", flush=True)
json.dump(out, open(os.path.join(os.path.dirname(__file__), "results", f"mapsize_{ds}_{desc}.json"), "w"), default=float, indent=1)
