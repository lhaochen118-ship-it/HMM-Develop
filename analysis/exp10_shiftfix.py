"""E10 — keeping SelfCal valid under DOMAIN shift (foreign queries from another city/dataset) without losing power
under APPEARANCE shift (same environment). Each map M in {rc, cmu, nord, msls-cph, msls-sf}; evaluated on
  (a) LOBO off-map queries of M's own dataset (appearance shift)  -> FAR, worst condition, #violations
  (b) correct in-map queries -> TPR;  (c) in-map aliasing errors -> acceptance
  (d) natural off-map: queries of every OTHER dataset/city scored against M -> FAR per source
Variants of the SelfCal-AA p-value (alpha = 0.05):
  AA                 max(combo(maxsim, z_far), p(z_gap))                       (current method)
  AA&ms<=g           AA and p(maxsim) <= g        (lenient raw-similarity gate; valid if either test is)
  AND-ms             max(AA, p(maxsim))           (fully robust: valid if ANY component is dominated)
  Mondrian-<s>-B     AA computed within B quantile strata of a nuisance statistic s of the map null
                     (s = raw maxsim 'ms' or far-region spread 'sdf'); conditional conformal validity per stratum
Usage: exp10_shiftfix.py <desc> <dump> [datasets=rc,cmu,nord,msls-cph,msls-sf]
       exp10_shiftfix.py <desc> --stats <shiftstats_<desc>.npz>     (re-score new variants from cached statistics,
                                                                     seconds on CPU, no descriptors needed)
A run with a dump also writes results/shiftstats_<desc>.npz (all per-query statistics + masks)."""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC
from sc_eval import CFG
from eval_all import violations

desc, dump = sys.argv[1], sys.argv[2]
STATS = sys.argv[3] if dump == "--stats" else None
DS = (sys.argv[3] if len(sys.argv) > 3 and not STATS else "rc,cmu,nord,msls-cph,msls-sf").split(",")
A, NF = 0.05, 2000
KEYS = ("ms", "zf", "zg", "sdf")


def load(k):
    if k.startswith("msls-"): return V.load_msls(dump, desc, (k[5:],)), CFG["msls"]
    return V.LOADERS[k](dump, desc), CFG[k]


nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True)


def pack(r, c):
    return {"ms": r["maxsim"], "zf": c["z_far"], "zg": c["z_gap"], "sdf": c["sd_far"]}


def aa(N, X):
    return np.maximum(SC.combined_p([N["ms"], N["zf"]], [X["ms"], X["zf"]]), SC.conformal_p(N["zg"], X["zg"]))


def mondrian(N, X, s, B):
    ok = np.isfinite(N["ms"]) & np.isfinite(N["zf"]) & np.isfinite(N["zg"]) & np.isfinite(N[s])
    edges = np.quantile(N[s][ok], np.linspace(0, 1, B + 1)[1:-1])
    bn, bx = np.digitize(N[s], edges), np.digitize(np.nan_to_num(X[s], nan=-1e9), edges)
    p = np.ones(len(X[s]))
    for b in range(B):
        mn, mx = ok & (bn == b), bx == b
        if mx.any() and mn.sum() > 50:
            p[mx] = aa({k: v[mn] for k, v in N.items()}, {k: v[mx] for k, v in X.items()})
    return p


def variants(N, X):
    p_aa, p_ms = aa(N, X), SC.conformal_p(N["ms"], X["ms"])
    out = {"AA": p_aa, "AA&ms<=0.5": np.where(p_ms <= 0.5, p_aa, 1.0), "AA&ms<=0.8": np.where(p_ms <= 0.8, p_aa, 1.0),
           "AND-ms": np.maximum(p_aa, p_ms)}
    for s in ("ms", "sdf"):
        for B in (3, 5):
            out[f"Mondrian-{s}-{B}"] = mondrian(N, X, s, B)
    for B in (5, 10):   # power variant + the domain-shift gate
        pm = out.get(f"Mondrian-sdf-{B}", mondrian(N, X, "sdf", B))
        out[f"Mondrian-sdf-{B}&ms<=0.8"] = np.where(p_ms <= 0.8, pm, 1.0)
    out["SelfCal-AA (adopted: SelfCalTest B=10, gate 0.8)"] = SC.SelfCalTest(N).pvalue(**X)
    return out


def compute_stats():
    """all per-query statistics needed by any variant: map null N, LOBO off-map O, in-map F, natural foreign PN"""
    EP = {k: load(k) for k in DS}
    rng = np.random.default_rng(0)
    FOR = {k: e.q[np.sort(rng.choice(len(e.q), min(NF, len(e.q)), replace=False))].astype(np.float32) for k, (e, _) in EP.items()}
    S = {}
    for mk, (ep, c) in EP.items():
        args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
        mr = ep.m.astype(np.float32); mu = mr.mean(0, keepdims=True); mc = nrm(mr - mu)
        st = lambda qq: pack(SC.qm_stats(qq, mr, ep.m_pos, c["cell"], c["excl"], c["k"]), SC.qm_stats(nrm(qq - mu), mc, ep.m_pos, c["cell"], c["excl"], c["k"]))
        q = ep.q.astype(np.float32); qc = nrm(q - mu)
        inm = V.nearest_map_dist(ep) <= c["in_d"]; _, dt, _ = V.top1_errors(ep)
        S[mk] = dict(N=pack(SC.map_null(mr, ep.m_pos, *args), SC.map_null(mc, ep.m_pos, *args)),
                     O=pack(SC.lobo_stats(mr, ep.m_pos, c["block"], c["off_d"], q, ep.q_pos, c["cell"], c["excl"], c["k"]),
                            SC.lobo_stats(mc, ep.m_pos, c["block"], c["off_d"], qc, ep.q_pos, c["cell"], c["excl"], c["k"])),
                     F=st(q), nat={sk: st(fq) for sk, fq in FOR.items() if sk != mk},
                     cond=np.asarray(ep.q_cond, dtype=str), corr=V.correct(ep, *c["tol"]) & inm, alias=inm & (dt > c["excl"]))
    return S


def save_stats(S, path):
    flat = {}
    for mk, d in S.items():
        for part in ("N", "O", "F"):
            for key in KEYS: flat[f"{mk}|{part}|{key}"] = np.asarray(d[part][key], dtype=np.float64)
        for sk, X in d["nat"].items():
            for key in KEYS: flat[f"{mk}|nat:{sk}|{key}"] = np.asarray(X[key], dtype=np.float64)
        for key in ("cond", "corr", "alias"): flat[f"{mk}|{key}"] = d[key]
    np.savez_compressed(path, **flat)


def load_stats(path):
    z = np.load(path); S = {}
    for name in z.files:
        mk, part, *key = name.split("|"); d = S.setdefault(mk, {"nat": {}})
        if key and part.startswith("nat:"): d["nat"].setdefault(part[4:], {})[key[0]] = z[name]
        elif key: d.setdefault(part, {})[key[0]] = z[name]
        else: d[part] = z[name]
    return S


RD = os.path.join(os.path.dirname(__file__), "results"); os.makedirs(RD, exist_ok=True)
if STATS: S = load_stats(STATS)
else: S = compute_stats(); save_stats(S, os.path.join(RD, f"shiftstats_{desc}.npz"))
res = {}
for mk, d in S.items():
    N, O, F = d["N"], d["O"], d["F"]
    corr, alias = d["corr"], d["alias"]
    offm = np.isfinite(O["ms"]) & np.isfinite(O["zf"])
    PO, PF = variants(N, O), variants(N, F)
    PN = {sk: variants(N, X) for sk, X in d["nat"].items()}
    r = {}
    for name in PO:
        nv, fars = violations(PO[name] <= A, d["cond"], offm, A)
        nat = {sk: float(np.mean(PN[sk][name] <= A)) for sk in PN}
        r[name] = dict(FAR=float(np.mean(PO[name][offm] <= A)), worst=float(max(fars.values())), n_viol=nv, n_cond=len(fars),
                       TPR=float(np.mean(PF[name][corr] <= A)), alias=float(np.mean(PF[name][alias] <= A)) if alias.any() else None,
                       natural=nat, natural_max=float(max(nat.values())) if nat else None)
        print(f"{desc:8s} map={mk:8s} {name:14s} LOBO worst {r[name]['worst']:.3f} viol {nv}/{len(fars)} TPR {r[name]['TPR']:.3f} "
              f"alias {r[name]['alias'] if r[name]['alias'] is None else round(r[name]['alias'], 3)} | natural max {r[name]['natural_max']:.3f} "
              + " ".join(f"{k}:{v:.3f}" for k, v in nat.items()), flush=True)
    res[mk] = r
json.dump(res, open(os.path.join(RD, f"shiftfix_{desc}.json"), "w"), indent=1)
