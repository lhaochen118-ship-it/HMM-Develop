"""Re-evaluate acceptance rules from nav_demo --cache files (results/navcache_<ds>_<desc>_s<seed>.npz, published as the
public dataset nhatlong1103/hmm-navcache) WITHOUT recomputing SelfCal statistics, map nulls, the place chain or Xu'21:
only presence recursions, the Kalman navigation and the metrics run (minutes instead of hours on Boreas).
New rule variants go in EXTRA (name -> function(z, base) returning (accept mask, fix positions, P(on) or None)).
Usage: nav_rules.py <cache_dir> <ds> <desc> [--safevpr <dir>] [--only extra]   -> results/navr_<ds>_<desc>.json"""
import sys, os, json, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nav_demo as N
from hmm_fix import beta_em

A = N.A


def base_parts(z):
    """the e-values and helpers every CPC variant shares (exactly as in nav_demo.main)"""
    H, conds, cond = int(z["H"]), sorted(set(z["cond"])), z["cond"]
    sid, k = z["q_sid"], z["q_k"]; seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    MP, est_c, top, excl = z["MP"], z["est_c"], z["top"], float(z["excl"])
    e_top1, e_a1, e_r1 = np.exp(z["lam"]), np.exp(z["loga"]), z["e_R"] ** (1.0 / H)
    fl, ln = z["nchunk_flat"], z["nchunk_len"]; nch = np.split(fl, np.cumsum(ln)[:-1]) if len(ln) else []
    u1, u2, _ = N.tce(nch, np.nan_to_num(z["p_n"], nan=1.0), np.nan_to_num(z["pRn"], nan=1.0), seqs, z["p_q"], z["pR"])
    et, ea, er = np.ones(len(cond)), np.ones(len(cond)), np.ones(len(cond))
    for cn in conds:
        m = cond == cn; b1, _ = beta_em(u1[m]); b2, _ = beta_em(u2[m])
        et[m] = b1 * np.clip(u1[m], 1e-6, 1) ** (b1 - 1); ea[m] = b1; er[m] = b2 * np.clip(u2[m], 1e-6, 1) ** (b2 - 1)
    pres = lambda xt, xa, xr, gate="post", rho=0.1, p_in=0.01, p_out=0.01: N.cpc_presence(est_c, MP, top, xt, xa, xr, seqs, excl, gate=gate,
                                                                                       rho=rho, s0=excl, U=z["U"], p_in=p_in, p_out=p_out)
    return dict(H=H, seqs=seqs, MP=MP, est_c=est_c, top=top, excl=excl, cond=cond, e=(e_top1, e_a1, e_r1), tce=(et, ea, er), pres=pres, u=(u1, u2))


def presence_legacy(ll, seqs, p_in, p_out):
    """nav_demo.main's presence(): the prediction step is applied at the first frame too (matters only if p_out != p_in)"""
    pon = np.zeros(len(ll))
    for idx in seqs:
        pr = 0.5
        for t in idx:
            pr = (1 - p_out) * pr + p_in * (1 - pr); lo = np.log(pr / (1 - pr)) + ll[t]; pr = 1 / (1 + np.exp(-np.clip(lo, -50, 50))); pon[t] = pr
    return pon


def base_rules(z, b, safevpr=None, ds=None, desc=None):
    MP, est_c, top = b["MP"], b["est_c"], b["top"]; x_fix, x_cpc = MP[top], MP[est_c]; e1, ea, er = b["e"]; et, eat, ert = b["tce"]
    R, X, P = {}, {}, {}
    def add(n, acc, xf, pon=None): R[n] = acc; X[n] = xf; P[n] = pon
    add("accept all", np.ones(len(top), bool), x_fix); add("label threshold", z["maxsim"] > z["thr_ms"], x_fix)
    add("SelfCal frame", z["p_frame"] <= A, x_fix); add("HMM off-map (labels)", z["acc_h"], z["x_hmm"])
    pon = b["pres"](e1, ea, er); add("CPC-HMM (ours)", pon > 0.5, x_cpc, pon)
    agree = np.linalg.norm(MP[top] - MP[est_c], axis=1) <= b["excl"]
    ll = np.log(np.maximum(0.5 * (np.where(agree, e1, ea) + er), 1e-300))
    for po in (0.05, 0.1, 0.2): add(f"CPC-HMM p_out={po}", presence_legacy(ll, b["seqs"], 0.01, po) > 0.5, x_cpc)
    for n, rho in (("CPC-HMM +GG", 0.1), ("CPC-HMM +GG(rho=.01)", 0.01)): p = b["pres"](e1, ea, er, "ghost", rho); add(n, p > 0.5, x_cpc, p)
    em = (np.minimum(e1, et), np.minimum(ea, eat), np.minimum(er, ert))
    for n, g, xs in (("CPC-HMM +TCE", "post", (et, eat, ert)), ("CPC-HMM +TCE+GG", "ghost", (et, eat, ert)),
                     ("CPC-HMM +TCEmin", "post", em), ("CPC-HMM +TCEmin+GG", "ghost", em)):
        p = b["pres"](*xs, gate=g); add(n, p > 0.5, x_cpc, p)
    add("certified (ours)", z["Rq"] > z["thr"], x_fix); add("oracle", z["good"], x_fix)
    bad_top = z["offm"] | (z["err_top"] > b["excl"])
    add("Claxton24 MLP (labels)", N.claxton_rule(z["srt10"], z["Smean"], z["Sstd"], z["bsel"], z["good"], bad_top, int(z["seed"])), x_fix)
    if safevpr:
        mtop = np.zeros(len(top)); ftop = z["kidx"][top]
        for f in sorted(glob.glob(os.path.join(safevpr, f"safevpr_{ds.replace(':', '_')}_p*.npz"))):
            q = np.load(f); r_, cd, mn = q["q_rows"], q[f"cand_{desc}"], q[f"mnn_{desc}"]
            hit = cd == ftop[r_][:, None]; mtop[r_] = np.where(hit.any(1), (mn * hit).sum(1), 0.0)
        add("SafeVPR (labels)", N.safevpr_rule(mtop, z["maxsim"], z["bsel"], bad_top), x_fix)
    for n in ("HMM off-map (labels)", "SelfCal frame", "certified (ours)", "Claxton24 MLP (labels)", "SafeVPR (labels)"):
        if n in R: add(n + " +DRgate", N.dr_gate(R[n], X[n], b["seqs"], z["U"], b["excl"]), X[n])
    return R, X, P


EXTRA = {}                                       # experimental rules: name -> f(z, b) -> (acc, xf, pon)


def main():
    cdir, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3]
    sv = sys.argv[sys.argv.index("--safevpr") + 1] if "--safevpr" in sys.argv else None; only = "--only" in sys.argv
    files = sorted(glob.glob(os.path.join(cdir, f"navcache_{ds.replace(':', '_')}_{desc}_s*.npz")), key=lambda f: int(f.rsplit("_s", 1)[1][:-4]))
    out = {"ds": ds, "desc": desc, "runs": [], "source": "nav_rules (cache)"}
    for f in files:
        z = np.load(f, allow_pickle=True); b = base_parts(z)
        R, X, P = ({}, {}, {}) if only else base_rules(z, b, sv, ds, desc)
        for n, fn in EXTRA.items(): R[n], X[n], P[n] = fn(z, b)
        cx = dict(q_pos=z["q_pos"], o_q=z["o_q"], real=bool(z["real"]), q_seqs=b["seqs"], hz=list(z["hz"]), seed=int(z["seed"]), excl=b["excl"],
                  inm=z["inm"], offm=z["offm"], H=b["H"])
        run = {"seed": int(z["seed"]), "n_map": int(z["n_map"]), "n_null_seg": int(z["n_null_seg"]), "thr": float(z["thr"]),
               "off_frac": float(z["offm"].mean()), "hmm_T_k": [float(x) for x in z["hmm_T_k"]]}
        run["rules"] = N.evaluate(R, X, {k: v for k, v in P.items() if v is not None}, cx, f"{ds}/{desc} s{int(z['seed'])}")
        out["runs"].append(run)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/navr_{ds.replace(':', '_')}_{desc}.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
