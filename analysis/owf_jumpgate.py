"""Entry 10 post-hoc DIAGNOSTIC (development data only, no decision). Usage: owf_jumpgate.py <dir of fr_*.npz> <navcache dir> [glob]
post-hoc diagnostic (development data): jump gate on OWF reports. A report whose fix is farther than r_gate from the dead-reckoned last
report (last fix + odometry since, sd s0 + kappa * path) is suppressed until the new place has been reported-eligible (mass >= 1 - eps) for
D metres of odometry; then the gate re-anchors. Navigation error recomputed with nav_demo.track."""
import sys, os, glob, json, numpy as np
sys.argv_ = sys.argv; sys.argv = sys.argv[:1]
sys.path.insert(0, "analysis"); import nav_demo as N
res_dir, cache_dir = sys.argv_[1], sys.argv_[2]; pat = sys.argv_[3] if len(sys.argv_) > 3 else "*"
out = {}
for f in sorted(glob.glob(os.path.join(res_dir, f"fr_{pat}_b1.npz"))):
    tag = os.path.basename(f)[3:-7]
    base, seed = tag.rsplit("_s", 1); seed = int(seed.split("_")[0])
    cf = os.path.join(cache_dir, f"navcache_{base}_s{seed}.npz")
    if not os.path.exists(cf): continue
    z = np.load(cf, allow_pickle=True); fr = np.load(f, allow_pickle=True)
    excl = float(z["excl"]); MP = z["MP"]; qp = z["q_pos"]; o = z["o_q"]; sid, k = z["q_sid"], z["q_k"]
    seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    rep0 = (fr["mass"] >= 1 - 1e-3) & (fr["xhat"] >= 0); xf = MP[np.maximum(fr["xhat"], 0)]
    hz = list(z["hz"]); U = z["U"]
    def gate(D, rg):
        acc = np.zeros(len(rep0), bool)
        for idx in seqs:
            have = False; pend = 0.0; mu = None; s_ = 0.0
            for t in idx:
                if have: mu = mu + U[t]; s_ += np.linalg.norm(U[t][hz] if U.ndim > 1 else U[t])
                if not rep0[t]: pend = 0.0; continue
                d = np.linalg.norm((xf[t] - mu)[hz]) if have else 0.0
                if not have or d <= rg + 0.05 * s_: acc[t] = True; mu, s_, have = xf[t].astype(float), 0.0, True; pend = 0.0
                else:
                    pend += np.linalg.norm(U[t][hz] if U.ndim > 1 else U[t])
                    if pend >= D: acc[t] = True; mu, s_, have = xf[t].astype(float), 0.0, True; pend = 0.0
        return acc
    err = np.linalg.norm(xf - qp, axis=1); gd = z["inm"] & (err <= excl) & (fr["xhat"] >= 0)
    r = {}
    for name, acc in (("base", rep0), ("gate", gate(4 * excl, excl)), ("gate2", gate(8 * excl, excl))):
        e = N.track(acc, xf, qp, o, bool(z["real"]), seqs, hz, seed, base.split("_")[0] == "nclt")
        m = N.rule_metrics(acc, gd, z["inm"], z["offm"], seqs, int(z["H"]))
        r[name] = (m["recall"], m["seg_FAR"], float(np.nanmean(e)))
    out[tag] = r; print(tag, {k_: tuple(round(x, 3) for x in v) for k_, v in r.items()}, flush=True)
json.dump(out, open(os.path.join(res_dir, f"jumpgate_{pat.replace('*', 'all')}.json"), "w"))
