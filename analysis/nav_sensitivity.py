"""One-at-a-time sensitivity of the final rule (CPC-HMM +TCEmin+GG) to every constant it uses, re-evaluated from nav_demo
--cache files (no recomputation of map statistics): ghost-gate floor rho, presence switching p_in = p_out, ghost base sd s0
(in units of excl), ghost growth KAPPA per metre, TCE Mondrian bins (nb_p, nb_r), and the decision threshold on P(on).
Defaults: rho 0.1, p 0.01, s0 1 x excl, KAPPA 0.05, bins (6, 4), threshold 0.5 (none tuned on NCLT, which was added later).
Usage: nav_sensitivity.py <cache_dir> <ds> <desc,...>   -> results/navsens_<ds>.json (per descriptor and seed)"""
import sys, os, json, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nav_demo as N
import nav_rules as NR
from hmm_fix import beta_em

GRID = [("default", {})] + [(f"rho={v}", {"rho": v}) for v in (0.03, 0.3)] + [(f"p={v}", {"p": v}) for v in (0.003, 0.03)] + \
       [(f"s0={v}excl", {"s0": v}) for v in (0.5, 2.0)] + [(f"kappa={v}", {"kappa": v}) for v in (0.02, 0.1)] + \
       [(f"bins={a}x{b}", {"bins": (a, b)}) for a, b in ((4, 3), (8, 6))] + [(f"thr={v}", {"thr": v}) for v in (0.3, 0.7)]


def tce_e(z, b, nb_p, nb_r):
    """TCEmin e-values with other Mondrian bins (as base_parts, which uses 6 x 4)"""
    fl, ln = z["nchunk_flat"], z["nchunk_len"]; nch = np.split(fl, np.cumsum(ln)[:-1]) if len(ln) else []
    u1, u2, _ = N.tce(nch, np.nan_to_num(z["p_n"], nan=1.0), np.nan_to_num(z["pRn"], nan=1.0), b["seqs"], z["p_q"], z["pR"], nb_p=nb_p, nb_r=nb_r)
    cond = b["cond"]; et, ea, er = np.ones(len(cond)), np.ones(len(cond)), np.ones(len(cond))
    for cn in sorted(set(cond)):
        m = cond == cn; b1, _ = beta_em(u1[m]); b2, _ = beta_em(u2[m])
        et[m] = b1 * np.clip(u1[m], 1e-6, 1) ** (b1 - 1); ea[m] = b1; er[m] = b2 * np.clip(u2[m], 1e-6, 1) ** (b2 - 1)
    return et, ea, er


def main():
    cdir, ds, descs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    out = {}
    for desc in descs:
        for f in sorted(glob.glob(os.path.join(cdir, f"navcache_{ds.replace(':', '_')}_{desc}_s*.npz"))):
            z = np.load(f, allow_pickle=True); b = NR.base_parts(z); e1, ea1, er1 = b["e"]
            cx = dict(q_pos=z["q_pos"], o_q=z["o_q"], real=bool(z["real"]), q_seqs=b["seqs"], hz=list(z["hz"]), seed=int(z["seed"]),
                      excl=b["excl"], inm=z["inm"], offm=z["offm"], H=b["H"], head=ds == "nclt")
            R, X = {}, {}; cache_tce = {(6, 4): b["tce"]}
            for name, kw in GRID:
                bins = kw.get("bins", (6, 4))
                if bins not in cache_tce: cache_tce[bins] = tce_e(z, b, *bins)
                et, eat, ert = cache_tce[bins]
                em = (np.minimum(e1, et), np.minimum(ea1, eat), np.minimum(er1, ert))
                N.KAPPA = kw.get("kappa", 0.05); p = kw.get("p", 0.01)
                pon = N.cpc_presence(b["est_c"], b["MP"], b["top"], *em, b["seqs"], b["excl"], gate="ghost", rho=kw.get("rho", 0.1),
                                     s0=kw.get("s0", 1.0) * b["excl"], U=z["U"], p_in=p, p_out=p)
                R[name] = pon > kw.get("thr", 0.5); X[name] = b["MP"][b["est_c"]]
            N.KAPPA = 0.05
            res = N.evaluate(R, X, {}, cx, f"{ds}/{desc} s{int(z['seed'])}")
            out[f"{desc}_s{int(z['seed'])}"] = {n: {k: res[n][k] for k in ("err_mean", "err_p95", "recall", "seg_FAR")} for n in res}
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/navsens_{ds.replace(':', '_')}_{'-'.join(descs)}.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
