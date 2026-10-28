"""E4 — aliasing: accept-rate of in-map GROSS errors (top-1 > excl from truth) under union vs intersection rules."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC, exp2_calib as E2
from sc_eval import CFG
from eval_all import signals
dump, ds = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
ep = {"rc": V.load_robotcar, "cmu": V.load_cmu_merged, "nord": V.load_nordland, "nordw": lambda d, x: V.load_nordland(d, x, ref="winter")}[ds](dump, desc); c = CFG[ds]
raw = signals(ep, c, False, f"{ds}_{desc}"); cen = signals(ep, c, True, f"{ds}_{desc}")
inm = V.nearest_map_dist(ep) <= c["in_d"]; _, dt, _ = V.top1_errors(ep); corr = V.correct(ep, *c["tol"]) & inm
gross = inm & (dt > c["excl"]); offm = np.isfinite(raw[1]["maxsim"]) & np.isfinite(cen[1]["z_far"])
nul2 = [raw[0]["maxsim"], cen[0]["z_far"]]
P = {"combo": (SC.combined_p(nul2, [raw[2]["maxsim"], cen[2]["z_far"]]), SC.combined_p(nul2, [raw[1]["maxsim"], cen[1]["z_far"]]))}
for st, src, key in [("T_spacing", raw, "T_spacing"), ("T_spacing_c", cen, "T_spacing"), ("z_gap", raw, "z_gap"), ("z_gap_c", cen, "z_gap")]:
    P[st] = (SC.conformal_p(src[0][key], src[2][key]), SC.conformal_p(src[0][key], src[1][key]))
rules = {"combo (union)": lambda k: P["combo"][k],
         "combo AND spacing": lambda k: np.maximum(P["combo"][k], P["T_spacing"][k]),
         "combo AND spacing_c": lambda k: np.maximum(P["combo"][k], P["T_spacing_c"][k]),
         "combo AND z_gap": lambda k: np.maximum(P["combo"][k], P["z_gap"][k]),
         "combo AND z_gap_c": lambda k: np.maximum(P["combo"][k], P["z_gap_c"][k])}
print(f"### {ds}/{desc}: in-map gross errors n={gross.sum()} ({gross[inm].mean():.3f} of in-map), correct n={corr.sum()}, off-map n={offm.sum()}")
for name, f in rules.items():
    pi, po = f(0), f(1)
    line = []
    for a in (0.01, 0.05, 0.1):
        line.append(f"a={a}: FAR_off {np.mean(po[offm] <= a):.3f} acc_alias {np.mean(pi[gross] <= a):.3f} TPR {np.mean(pi[corr] <= a):.3f}")
    print(f"  {name:22s} " + " | ".join(line))
