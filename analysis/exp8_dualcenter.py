"""E8 — dual centring: map descriptors centred on the map mean (as before) AND query descriptors centred on the mean of
their own deployment session (all queries of the same condition/date; label-free, = a running mean online).
Compares SelfCal-AA with map-only centring vs dual centring. Usage: exp8_dualcenter.py <dump> <ds> <desc>"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC
from sc_eval import CFG

dump, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3]
ep = {"rc": V.load_robotcar, "cmu": V.load_cmu_merged, "nord": V.load_nordland}[ds](dump, desc); c = CFG[ds]
nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)
inm = V.nearest_map_dist(ep) <= c["in_d"]; _, dt, _ = V.top1_errors(ep)
corr = V.correct(ep, *c["tol"]) & inm; alias = inm & (dt > c["excl"])
m = ep.m.astype(np.float32); q = ep.q.astype(np.float32); mu_m = m.mean(0, keepdims=True); mc = nrm(m - mu_m)
q_mapc = nrm(q - mu_m)
q_dual = np.empty_like(q)
for cc in set(ep.q_cond):
    sel = ep.q_cond == cc; q_dual[sel] = nrm(q[sel] - q[sel].mean(0, keepdims=True))
args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
nul_raw = SC.map_null(m, ep.m_pos, *args); off_raw = SC.lobo_stats(m, ep.m_pos, c["block"], c["off_d"], q, ep.q_pos, c["cell"], c["excl"], c["k"])
full_raw = SC.query_stats(q @ m.T, ep.m_pos, c["cell"], c["excl"], c["k"])
nul_c = SC.map_null(mc, ep.m_pos, *args)
res = {}
for name, qq in [("map-centring", q_mapc), ("dual-centring", q_dual)]:
    off_c = SC.lobo_stats(mc, ep.m_pos, c["block"], c["off_d"], qq, ep.q_pos, c["cell"], c["excl"], c["k"])
    full_c = SC.query_stats(qq @ mc.T, ep.m_pos, c["cell"], c["excl"], c["k"])
    offm = np.isfinite(off_raw["maxsim"]) & np.isfinite(off_c["z_far"])
    for combo_name, nul, offs, fulls in [("combo(maxsim_raw, z_far_c)", [nul_raw["maxsim"], nul_c["z_far"]], [off_raw["maxsim"], off_c["z_far"]], [full_raw["maxsim"], full_c["z_far"]]),
                                          ("combo(maxsim_c, z_far_c)", [nul_c["maxsim"], nul_c["z_far"]], [off_c["maxsim"], off_c["z_far"]], [full_c["maxsim"], full_c["z_far"]])]:
        po, pi = SC.combined_p(nul, offs), SC.combined_p(nul, fulls)
        pgo, pgi = SC.conformal_p(nul_c["z_gap"], off_c["z_gap"]), SC.conformal_p(nul_c["z_gap"], full_c["z_gap"])
        for rule, (a_o, a_i) in [("SelfCal", (po, pi)), ("SelfCal-AA", (np.maximum(po, pgo), np.maximum(pi, pgi)))]:
            fc = [np.mean(a_o[offm & (ep.q_cond == cc)] <= .05) for cc in sorted(set(ep.q_cond)) if (offm & (ep.q_cond == cc)).sum() >= 20]
            r = dict(FAR=float(np.mean(a_o[offm] <= .05)), worst=float(max(fc)), TPR=float(np.mean(a_i[corr] <= .05)), alias=float(np.mean(a_i[alias] <= .05)))
            res[f"{name} | {combo_name} | {rule}"] = r
            print(f"{ds}/{desc} {name:14s} {combo_name:27s} {rule:10s} FAR {r['FAR']:.3f} worst {r['worst']:.3f} TPR {r['TPR']:.3f} alias {r['alias']:.3f}", flush=True)
json.dump(res, open(os.path.join(os.path.dirname(__file__), "results", f"dualcenter_{ds}_{desc}.json"), "w"), indent=1)
