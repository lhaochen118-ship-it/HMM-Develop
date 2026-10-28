"""E3 — deployment batches: BH false-discovery control and label-free calibrated confidence from SelfCal p-values.
Batch (one per condition) = all in-map queries + a share of off-map query instances. Errors:
  gross = accepted & (off-map or top-1 farther than 25 m / 5 frames from the truth)   <- what SelfCal targets
  fine  = accepted & in-map & 5 m (2 frames) < error <= 25 m (5 frames)
Usage: exp3_fdr.py <dump> <rc|cmu|nord> [desc]"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC, exp2_calib as E2
from sc_eval import CFG
from eval_all import signals


def main(dump, ds, desc="salad", mixes=(0.1, 0.3, 0.5), qs=(0.05, 0.1), seed=0):
    ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
    raw = signals(ep, c, False, f"{ds}_{desc}"); cen = signals(ep, c, True, f"{ds}_{desc}")
    p_in, p_off = SC.selfcal_p(raw[0], cen[0], raw[2], cen[2]), SC.selfcal_p(raw[0], cen[0], raw[1], cen[1])
    inm = V.nearest_map_dist(ep) <= c["in_d"]; _, dt, da = V.top1_errors(ep)
    gross_thr = c["excl"]
    corr = V.correct(ep, *c["tol"]) & inm; near = inm & (dt <= gross_thr)
    offm = np.isfinite(raw[1]["maxsim"]) & np.isfinite(cen[1]["z_far"])
    rng = np.random.default_rng(seed); rows = []
    for mix in mixes:
        for cond in sorted(set(ep.q_cond)):
            ii = np.where((ep.q_cond == cond) & inm)[0]; oo = np.where((ep.q_cond == cond) & offm)[0]
            n_off = min(len(oo), int(round(mix / (1 - mix) * len(ii))))
            if len(ii) < 20 or n_off < 5: continue
            oo = rng.choice(oo, n_off, replace=False)
            p = np.r_[p_in[ii], p_off[oo]]; y = np.r_[corr[ii], np.zeros(n_off, bool)]; ok_gross = np.r_[near[ii], np.zeros(n_off, bool)]
            conf, pi0 = E2.labelfree_confidence(p)
            r = dict(mix=mix, cond=str(cond), n=len(p), frac_correct=float(y.mean()), pi0_hat=pi0, true_null=float(1 - ok_gross.mean()),
                     ECE_labelfree=V.ece(conf, y), ECE_labelfree_gross=V.ece(conf, ok_gross))
            for q in qs:
                acc = E2.bh_accept(p, q)
                r[f"BH{q}_FDR_gross"] = float((~ok_gross[acc]).mean()) if acc.any() else 0.0
                r[f"BH{q}_FDR_5m"] = float((~y[acc]).mean()) if acc.any() else 0.0
                r[f"BH{q}_power"] = float(acc[y].mean()) if y.any() else np.nan
            rows.append(r)
    print(f"### {ds}/{desc} deployment batches (BH on SelfCal-AA p-values)")
    for mix in mixes:
        R = [r for r in rows if r["mix"] == mix]
        if not R: continue
        f = lambda k: (np.mean([r[k] for r in R]), np.max([r[k] for r in R]))
        print(f"  off-map share {mix:.1f}: pi0^ {f('pi0_hat')[0]:.2f} (true gross-null {f('true_null')[0]:.2f}) | ECE label-free (vs 5m) {f('ECE_labelfree')[0]:.3f} "
              f"(vs gross) {f('ECE_labelfree_gross')[0]:.3f} | " + " | ".join(
              f"BH q={q}: FDR_gross mean {f(f'BH{q}_FDR_gross')[0]:.3f} max {f(f'BH{q}_FDR_gross')[1]:.3f}, FDR_5m {f(f'BH{q}_FDR_5m')[0]:.3f}, power {f(f'BH{q}_power')[0]:.3f}" for q in qs))
    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
    json.dump(rows, open(os.path.join(os.path.dirname(__file__), "results", f"fdr_{ds}_{desc}.json"), "w"), default=float, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "salad")
