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


def discrimination(ep, tol, cfg, seed=0):
    """AUROC (correct in-map vs off-map+wrong) and AURC for every score; p-values used as -p."""
    eh, off, inm = E1.make_holes(ep, cell=cfg["hole_cell"], frac=cfg["hole_frac"], seed=seed, off_d=cfg["off_d"], in_d=cfg["in_d"])
    corr = V.correct(eh, *tol) & inm; use = inm | off
    pv = E1.pvalue_methods(eh, cfg); sc, b = E1.score_methods(eh)
    allsc = {**{k: -v for k, v in pv.items()}, **sc, "softmax": b["softmax"], "neg_entropy": b["neg_entropy"]}
    res = {}
    for k, s in allsc.items():
        res[k] = {"AUROC_correct": V.auroc(s[use], corr[use]), "AUROC_offmap": V.auroc(s[inm | off], inm[inm | off]),
                  "AURC": V.aurc(s[use], corr[use])}
    return res, corr[use].mean()


def calib_fdr(ep, tol, cfg, calib_conds, seed=0, alpha=0.1):
    """Per condition (one deployment batch each): ECE of label-free EVS confidence vs label-trained CRSG
    transferred from calib conds; BH(alpha) realised FDR and power."""
    eh, off, inm = E1.make_holes(ep, cell=cfg["hole_cell"], frac=cfg["hole_frac"], seed=seed, off_d=cfg["off_d"], in_d=cfg["in_d"])
    corr = V.correct(eh, *tol) & inm; use = inm | off
    p = V.evs_test(eh, cell=cfg["cell"], excl=cfg["excl"], k=cfg["k"]); b = V.baseline_scores(eh)
    X = np.column_stack([b["margin"], b["neg_L2"], b["neg_entropy"]]); cal = np.isin(eh.q_cond, calib_conds) & use
    crsg = V.logistic_model(X[cal], corr[cal].astype(float))(X)
    rows = []
    for c in sorted(set(eh.q_cond)):
        m = (eh.q_cond == c) & use
        if m.sum() < 30: continue
        conf, pi0 = E2.labelfree_confidence(p[m])
        acc = E2.bh_accept(p[m], alpha); y = corr[m]
        rows.append(dict(cond=str(c), n=int(m.sum()), acc_rate=float(y.mean()), pi0_hat=pi0,
                         ECE_EVS_labelfree=V.ece(conf, y), ECE_CRSG_transfer=V.ece(crsg[m], y),
                         ECE_softmax=V.ece(b["softmax"][m], y),
                         BH_FDR=float((~y[acc]).mean()) if acc.any() else 0.0, BH_power=float(acc[y].mean()) if y.any() else np.nan))
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
        rows = E1.run(ep, tol, calc, cfg=cfg)
        for a in (0.05, 0.1): E1.summarise(rows, a)
        disc, base = discrimination(ep, tol, cfg)
        print(f"  discrimination (base acc {base:.2f}):")
        for k, v in sorted(disc.items(), key=lambda kv: -np.nan_to_num(kv[1]["AUROC_correct"])):
            print(f"    {k:14s} AUROC(correct)={v['AUROC_correct']:.3f} AUROC(offmap)={v['AUROC_offmap']:.3f} AURC={v['AURC']:.3f}")
        cf = calib_fdr(ep, tol, cfg, calc)
        print("  label-free calibration / BH(0.1) per condition:")
        for r in cf:
            print(f"    {r['cond'][:16]:16s} n={r['n']:4d} acc={r['acc_rate']:.2f} pi0^={r['pi0_hat']:.2f} | ECE EVS-lf={r['ECE_EVS_labelfree']:.3f} "
                  f"CRSG-transfer={r['ECE_CRSG_transfer']:.3f} softmax={r['ECE_softmax']:.3f} | BH FDR={r['BH_FDR']:.3f} power={r['BH_power']:.3f}")
        results[name] = {"E1": rows, "disc": disc, "calib": cf, "calib_conds": calc, "tol": tol, "cfg": cfg}
        print(f"  [{name}] done in {time.time()-t0:.0f}s\n", flush=True)
    json.dump(results, open(os.path.join(OUT, f"run_all_{DESC}.json"), "w"), default=float)


if __name__ == "__main__":
    main()
