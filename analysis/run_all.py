"""Driver: load NB15 dumps and run E1 (validity under shift), E2 (label-free calibration), E3 (BH-FDR),
plus discrimination (AUROC / AURC) for every reliability score. Usage: run_all.py <dump_dir> [desc] [datasets]"""
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, exp1_validity as E1, exp2_calib as E2

DUMP = sys.argv[1]; DESC = sys.argv[2] if len(sys.argv) > 2 else "salad"
WHICH = sys.argv[3].split(",") if len(sys.argv) > 3 else ["rc", "cmu", "nord"]
OUT = os.path.join(os.path.dirname(__file__), "results"); os.makedirs(OUT, exist_ok=True)


def describe(ep, tol):
    ok = V.correct(ep, *tol); conds = sorted(set(ep.q_cond))
    print(f"[{ep.name}] Nq={len(ep.q)} Nm={len(ep.m)} | R@1 tol={tol}: " +
          ", ".join(f"{c}={ok[ep.q_cond == c].mean():.2f}" for c in conds))


def discrimination(info):
    """Accept/reject discrimination: positives = correct in-map, negatives = off-map (LOBO). p-values as -p."""
    si, so, off, corr = info["sig_in"], info["sig_off"], info["off"], info["corr"]
    res = {}
    for k in si:
        if k[:2] not in ("p:", "s:", "f:"): continue
        sgn = -1 if k.startswith("p:") else 1
        sc = np.r_[sgn * si[k][corr], sgn * so[k][off]]; y = np.r_[np.ones(corr.sum()), np.zeros(off.sum())]
        res[k] = {"AUROC": V.auroc(sc, y), "AURC": V.aurc(sc, y)}
    return res


def calib_fdr(ep, info, alpha=0.1, mix=0.3, seed=0):
    """Per condition = one deployment batch mixing correct in-map queries with a share `mix` of off-map ones.
    ECE of the label-free EVS confidence vs CRSG transferred from the day calibration; BH(alpha) FDR/power."""
    rng = np.random.default_rng(seed); si, so = info["sig_in"], info["sig_off"]; rows = []
    inm, off, corr = info["inm"], info["off"], info["corr"]
    for c in sorted(set(ep.q_cond)):
        ii = np.where((ep.q_cond == c) & inm)[0]; oo = np.where((ep.q_cond == c) & off)[0]
        if len(ii) < 20 or len(oo) < 10: continue
        n_off = min(len(oo), int(round(mix / (1 - mix) * len(ii)))); oo = rng.choice(oo, n_off, replace=False)
        p = np.r_[si["p:EVS"][ii], so["p:EVS"][oo]]; y = np.r_[corr[ii], np.zeros(n_off, bool)]
        crsg = np.r_[si["s:CRSG"][ii], so["s:CRSG"][oo]]
        conf, pi0 = E2.labelfree_confidence(p); acc = E2.bh_accept(p, alpha)
        rows.append(dict(cond=str(c), n=len(p), frac_correct=float(y.mean()), pi0_hat=pi0,
                         ECE_EVS_labelfree=V.ece(conf, y), ECE_CRSG_transfer=V.ece(crsg, y),
                         BH_FDR=float((~y[acc]).mean()) if acc.any() else 0.0, BH_power=float(acc[y].mean())))
    return rows


def main():
    results = {}
    eps = []
    if "rc" in WHICH and os.path.isfile(os.path.join(DUMP, "meta", "rc.npz")):
        eps.append(("rc", V.load_robotcar(DUMP, DESC), (5.0, 10.0), E1.DEFAULT_CFG, ["overcast-summer", "overcast-winter"]))
    if "cmu" in WHICH:
        for e in V.load_cmu(DUMP, DESC):
            ok = V.correct(e, 5.0, 10.0); conds = sorted(set(e.q_cond), key=lambda c: -ok[e.q_cond == c].mean())
            eps.append((e.name, e, (5.0, 10.0), E1.DEFAULT_CFG, conds[:2]))
    if "nord" in WHICH and os.path.isfile(os.path.join(DUMP, "meta", "nord.npz")):
        eps.append(("nord", V.load_nordland(DUMP, DESC), (2.0, None), E1.NORD_CFG, ["fall"]))
    for name, ep, tol, cfg, calc in eps:
        t0 = time.time(); describe(ep, tol)
        rows, info = E1.run(ep, tol, calc, cfg=cfg)
        print(f"  off-map (LOBO) queries: {int(info['off'].sum())} | in-map: {int(info['inm'].sum())} | correct in-map: {int(info['corr'].sum())}")
        for a in (0.01, 0.05, 0.1): E1.summarise(rows, a)
        disc = discrimination(info)
        print("  accept/reject discrimination (correct in-map vs off-map):")
        for k, v in sorted(disc.items(), key=lambda kv: -np.nan_to_num(kv[1]["AUROC"])):
            print(f"    {k:16s} AUROC={v['AUROC']:.3f} AURC={v['AURC']:.4f}")
        cf = calib_fdr(ep, info)
        print("  label-free calibration / BH(0.1) per condition (batch = in-map + 30% off-map):")
        for r in cf:
            print(f"    {r['cond'][:16]:16s} n={r['n']:4d} correct={r['frac_correct']:.2f} pi0^={r['pi0_hat']:.2f} | ECE EVS-labelfree={r['ECE_EVS_labelfree']:.3f} "
                  f"CRSG-transfer={r['ECE_CRSG_transfer']:.3f} | BH FDR={r['BH_FDR']:.3f} power={r['BH_power']:.3f}")
        results[name] = {"E1": rows, "disc": disc, "calib": cf, "calib_conds": list(calc), "tol": tol, "cfg": cfg}
        print(f"  [{name}] done in {time.time()-t0:.0f}s\n", flush=True)
    json.dump(results, open(os.path.join(OUT, f"run_all_{DESC}.json"), "w"), default=float)


if __name__ == "__main__":
    main()
