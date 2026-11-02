"""Entry 36 step 1 diagnosis (labels used ONLY to classify): where do the false fixes that pass CST sit, and why does CST lose
recall on Oxford? For one run: per-frame shape residual of the reported HMM track (r), of the counterfactual track (r_cf),
the CST threshold eps, the SH decision, the default decisions of the E35 rules (oc_curves --dump-frames), and the labels.
Prints: (a) false fixes of the CST / SH / SH AND CST rules split by excursion depth (frames since the first off-map frame and
odometry path since the last on-map frame) and by SH / CST verdict; (b) recall loss of each guard on correct on-map frames.
Usage: fwd_diag.py <navcache.npz> <cms.npz> <frames.npz> [--json out.json]"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv += ["--cst"] if "--cst" not in sys.argv else []
import nav_rules as NR
import cms as CMS
import cpc_geo as CG


def excursion_depth(seqs, offm, inm, o):
    """per frame: frames since the start of the current off-map run (-1 if not off-map) and odometry path since the last
    on-map frame (nan before the first one)"""
    dep = np.full(len(offm), -1); pth = np.full(len(offm), np.nan)
    for idx in seqs:
        oo = o[idx].astype(float); cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(oo, axis=0), axis=1))]
        k, last = -1, None
        for i, t in enumerate(idx):
            if offm[t]: k = k + 1 if k >= 0 else 0
            else: k = -1
            dep[t] = k
            if inm[t]: last = cum[i]
            if last is not None: pth[t] = cum[i] - last
    return dep, pth


def main():
    zf, cf, ff = sys.argv[1:4]
    z = np.load(zf, allow_pickle=True); st = dict(np.load(cf)); fr = np.load(ff, allow_pickle=True)
    b = NR.base_parts(z); seqs, excl, MP = b["seqs"], b["excl"], b["MP"]; hz = list(z["hz"])
    xc = MP[b["est_c"]]; jj = np.maximum(st["j"], 0)
    r = CG.shape_resid(xc, z["o_q"], seqs, excl, hz=hz)
    jc = np.where(st["j_cf"] >= 0, st["j_cf"], jj); rcf = CG.shape_resid(MP[jc], z["o_q"], seqs, excl, hz=hz)
    sh = CG.shape_ok(xc, z["o_q"], seqs, excl, 3.0, 0.5, hz=hz)
    eps = np.full(len(r), -np.inf); CMS.GROUP = "cond"; CMS.ALPHA_MIN[0] = 0.05
    for sqs, cqs in CMS.cal_groups(z, seqs):
        m = np.concatenate(sqs); mins = []
        for sg in CMS._segments(cqs, b["H"]):
            v = rcf[sg]; v = v[np.isfinite(v)]
            if len(v): mins.append(v.min())
        mins = np.sort(mins); k = int(np.floor(0.05 * (len(mins) + 1))); eps[m] = mins[k - 1] if k >= 1 else -np.inf
    cst = ~(r > eps)
    names = list(fr["names"]); acc = dict(zip(names, fr["acc"]))
    offm, inm = z["offm"], z["inm"]; err = np.linalg.norm(xc - z["q_pos"], axis=1); good = inm & (err <= excl)
    dep, pth = excursion_depth(seqs, offm, inm, z["o_q"][:, hz] if z["o_q"].ndim > 1 and z["o_q"].shape[1] > 2 else z["o_q"])
    out = dict(run=os.path.basename(zf), eps=float(np.median(eps[np.isfinite(eps)])) if np.isfinite(eps).any() else None,
               sh_tol=0.5 * excl, excl=excl, n_off=int(offm.sum()), n_good=int(good.sum()))
    print(f"{out['run']}: eps(CST) median {out['eps']}, SH tol {0.5 * excl}, off-map {offm.sum()}, correct on-map {good.sum()}")
    bins = [(0, 10), (10, 20), (20, 40), (40, 80), (80, 10 ** 9)]
    for rule in ("CMS-CPC/H+CST+G+NGRr", "CMS-CPC/H+SH+G+NGRr", "CMS-CPC/H+SH+CST+G+NGRr"):
        if rule not in acc: continue
        a = acc[rule]; ff_ = a & offm
        row = {f"d{lo}-{hi}": int((ff_ & (dep >= lo) & (dep < hi)).sum()) for lo, hi in bins}
        row["total"] = int(ff_.sum()); row["sh_rejects"] = int((ff_ & ~sh).sum()); row["err_med"] = float(np.median(err[ff_])) if ff_.any() else None
        row["path_since_on_med"] = float(np.nanmedian(pth[ff_])) if ff_.any() else None
        out[rule] = row; print(f"  false fixes {rule:28s} {row}")
    # recall: of correct on-map frames reported by the base presence decision, how many does each guard remove
    base = acc.get("CMS-CPC/H+SH+G+NGRr")
    g = good
    out["guards"] = dict(sh_fail=float((g & ~sh).mean() / max(g.mean(), 1e-9)), cst_fail=float((g & ~cst).mean() / max(g.mean(), 1e-9)),
                         both_fail=float((g & ~sh & ~cst).mean() / max(g.mean(), 1e-9)),
                         r_good_med=float(np.nanmedian(r[g])), r_good_p90=float(np.nanpercentile(r[g], 90)),
                         rcf_med=float(np.nanmedian(rcf)), rcf_p05=float(np.nanpercentile(rcf, 5)))
    print("  correct on-map frames failing:", {k: round(v, 4) for k, v in out["guards"].items()})
    if "--json" in sys.argv: json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)


if __name__ == "__main__":
    main()
