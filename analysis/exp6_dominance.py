"""E6 — excess-risk bound Delta_c^+ = sup_t [P(T^c>=t) - P(T^0>=t)]_+ (one-sided KS) per condition, for the map null
(SelfCal) vs a labelled benign-condition null (LabelCal), and for raw max-sim vs invariant z_far."""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V
from sc_eval import CFG
from eval_all import signals
def dplus(x, null):
    x, null = np.sort(x[np.isfinite(x)]), np.sort(null[np.isfinite(null)])
    t = np.r_[x, null]; Sx = 1 - np.searchsorted(x, t, "left") / len(x); Sn = 1 - np.searchsorted(null, t, "left") / len(null)
    return float(max(0.0, (Sx - Sn).max()))
dump, ds = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
raw = signals(ep, c, False, f"{ds}_{desc}"); cen = signals(ep, c, True, f"{ds}_{desc}")
inm = V.nearest_map_dist(ep) <= c["in_d"]; corr = V.correct(ep, *c["tol"]) & inm
offm = np.isfinite(raw[1]["maxsim"]) & np.isfinite(cen[1]["z_far"]); cond = ep.q_cond; conds = sorted(set(cond))
calib = c["calib"] or sorted(conds, key=lambda x: -corr[cond == x].mean())[:2]; cal = np.isin(cond, calib) & offm
out = {}
print(f"### {ds}/{desc}: Delta+ (excess-FAR bound) per condition; calib={list(calib)}")
print(f"{'condition':16s} {'maxsim|day':>11s} {'maxsim|map':>11s} {'z_far|day':>10s} {'z_far+c|map':>12s}")
for cc in conds:
    m = offm & (cond == cc)
    if m.sum() < 20: continue
    r = dict(maxsim_day=dplus(raw[1]["maxsim"][m], raw[1]["maxsim"][cal]), maxsim_map=dplus(raw[1]["maxsim"][m], raw[0]["maxsim"]),
             zfar_day=dplus(raw[1]["z_far"][m], raw[1]["z_far"][cal]), zfarc_map=dplus(cen[1]["z_far"][m], cen[0]["z_far"]))
    out[str(cc)] = r
    print(f"{str(cc)[:16]:16s} {r['maxsim_day']:11.3f} {r['maxsim_map']:11.3f} {r['zfar_day']:10.3f} {r['zfarc_map']:12.3f}")
json.dump(out, open(os.path.join(os.path.dirname(__file__), "results", f"dominance_{ds}_{desc}.json"), "w"), indent=1)
