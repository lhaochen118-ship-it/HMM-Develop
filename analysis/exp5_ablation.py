"""E5 — ablations of SelfCal-AA. The evaluation protocol (which queries are off-map: block 300 m / off_d 40 m) is fixed;
only the method's own null construction (block_m, off_d_m, stride) and statistic parameters (cell, excl) vary.
Usage: exp5_ablation.py <dump> <rc|nord|cmu> [desc]"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC
from sc_eval import CFG

dump, ds = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
u = 1.0 if ds != "nord" else 0.2          # Nordland positions are subsampled frame indices
inm = V.nearest_map_dist(ep) <= c["in_d"]; _, dt, _ = V.top1_errors(ep)
corr = V.correct(ep, *c["tol"]) & inm; alias = inm & (dt > c["excl"])
qr, mr = ep.q.astype(np.float32), ep.m.astype(np.float32); qc, mc = SC.center(ep.q, ep.m)


def run(cell, excl, block_m, off_d_m, stride, centered=True, alphas=(0.05,)):
    k = c["k"]; qz, mz = (qc, mc) if centered else (qr, mr)
    nr = SC.lobo_stats(mr, ep.m_pos, block_m, off_d_m, mr[::stride], ep.m_pos[::stride], cell, excl, k)
    nz = SC.lobo_stats(mz, ep.m_pos, block_m, off_d_m, mz[::stride], ep.m_pos[::stride], cell, excl, k)
    o_r = SC.lobo_stats(mr, ep.m_pos, c["block"], c["off_d"], qr, ep.q_pos, cell, excl, k)
    o_z = SC.lobo_stats(mz, ep.m_pos, c["block"], c["off_d"], qz, ep.q_pos, cell, excl, k)
    f_r = SC.query_stats(qr @ mr.T, ep.m_pos, cell, excl, k); f_z = SC.query_stats(qz @ mz.T, ep.m_pos, cell, excl, k)
    offm = np.isfinite(o_r["maxsim"]) & np.isfinite(o_z["z_far"])
    nul = [nr["maxsim"], nz["z_far"]]
    pco_o, pco_i = SC.combined_p(nul, [o_r["maxsim"], o_z["z_far"]]), SC.combined_p(nul, [f_r["maxsim"], f_z["z_far"]])
    pg_o, pg_i = SC.conformal_p(nz["z_gap"], o_z["z_gap"]), SC.conformal_p(nz["z_gap"], f_z["z_gap"])
    po, pi = np.maximum(pco_o, pg_o), np.maximum(pco_i, pg_i)
    res = {}
    for a in alphas:
        fc = [np.mean(po[offm & (ep.q_cond == cc)] <= a) for cc in sorted(set(ep.q_cond)) if (offm & (ep.q_cond == cc)).sum() >= 20]
        res[a] = dict(FAR=float(np.mean(po[offm] <= a)), worst=float(max(fc)), TPR=float(np.mean(pi[corr] <= a)),
                      alias=float(np.mean(pi[alias] <= a)) if alias.any() else float("nan"), n_null=int(np.isfinite(nz["z_far"]).sum()))
    return res


base = dict(cell=10 * u, excl=25 * u, block_m=300 * (u if ds != "nord" else 2 / 3), off_d_m=40 * u, stride=2)
if ds == "nord": base = dict(cell=3.0, excl=5.0, block_m=200.0, off_d_m=10.0, stride=2)
grid = [("default", {})]
for key, vals in [("cell", [0.5, 2.0]), ("excl", [0.4, 2.0]), ("block_m", [0.5, 2.0]), ("off_d_m", [0.6, 2.0])]:
    for v in vals: grid.append((f"{key} x{v}", {key: base[key] * v}))
for st in [1, 4, 8]: grid.append((f"stride {st}", {"stride": st}))
grid.append(("no centering", {"centered": False}))
out = {}
print(f"### ablation {ds}/{desc} (alpha=0.05): base={base}")
for name, ch in grid:
    cfg = {**base, **ch}; r = run(**cfg)[0.05]; out[name] = {"cfg": cfg, **r}
    print(f"  {name:16s} FAR {r['FAR']:.3f} worst {r['worst']:.3f} TPR {r['TPR']:.3f} alias {r['alias']:.3f} (null n={r['n_null']})", flush=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
json.dump(out, open(os.path.join(os.path.dirname(__file__), "results", f"ablation_{ds}_{desc}.json"), "w"), default=float, indent=1)
