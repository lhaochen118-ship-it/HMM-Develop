"""Hindsight-calibrated open-world decisions (offline; 2026-11-05, Entry 16 development).

The incumbent rule OWF-HWA-S5 (Entry 15) reports where OWF-H (HSI-VN on the hybrid chain) reports OR where the open-world filter's disc
mass passes FIXED thresholds that depend on the path since the sequence start: m(1e-5,16) | m(1e-8,2) | t(3e-4,0.5). Those constants were
chosen on development seeds. Here the OWF branch is instead thresholded by split-conformal calibration on the run's OWN hindsight-null
segments (HSI's labels: possibly off-map or possibly wrong or never verified; held-out calibration units; each label used only after the
bridge that produces it has closed), separately per evidence stratum (Mondrian by path since the sequence start):
  score s_t = -log10(1 - disc mass_t) (the filter's own confidence, decades), +inf inside a segment where the H branch reports (joint
  calibration of the union: a report of either branch inside a held-out null segment counts against alpha);
  tau_k(T) = conformal (1 - alpha) quantile of the segment maxima of stratum k among the segments available before deployment rank T;
  report at t iff H_t OR s_t > tau_{k(t)}(T_t) [and, variant "a", three-way agreement].
Guarantee (HSI Proposition 4 per stratum): for a new null segment exchangeable with the held-out ones of its stratum, P(any report) <=
alpha. Variants (names): INC (incumbent, as owf_union.py), HC<bins>[a][@alpha] e.g. HC3, HC5a, HC3@0.1; C3 (OWF branch alone, no H).
Usage: owf_hcal.py <frames_dir> <hsifr_dir> <navcache_dir>[,dir2] <out.json> --tag <hsifr tag> [--ftag _<tag>] [--variants INC,HC3,HC5]
       [--hvar HSI-VN] [--jobs 4]"""
import sys, os, glob, json
import numpy as np
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.environ.get("HCAL_BRIDGE", "topo")                     # source of the hindsight bridges (see one())
BINS = {"3": [0, 2, 16], "5": [0, 0.5, 2, 8, 16], "1": [0]}       # stratum lower edges, path since the sequence start (excl units)


def parse(v):
    """HC3a@0.05 -> dict(kind='HC', bins='3', agree=True, alpha=0.05, null='u'); suffix v = null without never-verified frames"""
    a = 0.05
    if "@" in v: v, a = v.split("@"); a = float(a)
    kind = "C" if v.startswith("C") else "HC"; rest = v[len(kind):]
    nl = "v" if rest.endswith("v") else "u"; rest = rest.rstrip("v")
    return dict(kind=kind, bins=rest.rstrip("a"), agree=rest.endswith("a"), alpha=a, null=nl)


def calibrated(score, strat, seqs, null, cal, unit, avail, H, accH, alpha, chunk=200, joint=True):
    """causal per-stratum split-conformal thresholds on held-out null segments; returns the OWF-branch report mask"""
    sys.path.insert(0, HERE); import hsi
    n = len(score); order = np.concatenate(seqs); rank = np.empty(n, np.int64); rank[order] = np.arange(n)
    segs = hsi.null_segments(seqs, null, cal, unit, H, strat)
    if not segs: return np.zeros(n, bool), {}
    sk = np.array([strat[s[0]] for s in segs]); sav = np.array([avail[s].max() for s in segs])
    smax = np.array([np.inf if (joint and accH[s].any()) else score[s].max() for s in segs])
    min_seg = int(np.ceil(1 / alpha)) - 1
    rep = np.zeros(n, bool); thr_log = {}
    for c0 in range(0, n, chunk):
        cur = order[c0:c0 + chunk]; T = c0
        for k in np.unique(strat[cur]):
            m = (sk == k) & (sav < T)
            thr = hsi.conformal_thr(smax[m], alpha) if m.sum() >= min_seg else np.inf
            sel = cur[strat[cur] == k]; rep[sel] = score[sel] > thr
            thr_log.setdefault(int(k), []).append(float(thr))
    return rep, {k: dict(final=v[-1], n_seg=int((sk == k).sum())) for k, v in thr_log.items()}


def one(args):
    ff, hdir, cdirs, variants, tag, ftag, hvar = args
    sys.argv = sys.argv[:1]; sys.path.insert(0, HERE)
    import nav_demo as N, position_audit as PA, owf_decide as OD, owf_union as OU, hsi
    t = os.path.basename(ff)[3:].rsplit("_b1.npz", 1)[0]
    if ftag: t = t[: -len(ftag)]
    base, _, rest = t.rpartition("_s"); seed = int(rest)
    cf = next((os.path.join(d, f"navcache_{base}_s{seed}.npz") for d in cdirs if os.path.exists(os.path.join(d, f"navcache_{base}_s{seed}.npz"))), None)
    hf = os.path.join(hdir, f"hsifr_{base}_s{seed}_{tag}.npz")
    if cf is None or not os.path.exists(hf): return t, None
    z = dict(np.load(cf, allow_pickle=True)); fr = np.load(ff, allow_pickle=True); hm = np.load(hf)
    n = int(hm["n"]); accH = np.unpackbits(hm[hvar])[:n].astype(bool)
    excl = float(z["excl"]); MP = z["MP"]; qp = z["q_pos"]; H = int(z["H"])
    sid, k = z["q_sid"], z["q_k"]; seqs = [np.where(sid == s)[0][np.argsort(k[sid == s])] for s in np.unique(sid)]
    hz = list(z["hz"]); U = z["U"].astype(float); U = U if U.ndim > 1 else U[:, None]
    mass, xh = np.asarray(fr["mass"], float), np.asarray(fr["xhat"]).astype(int)
    pst = OD.path_from_start(U, seqs, hz) / excl
    est_h = z["est_c"].astype(int).copy(); rep = (xh >= 0) & (mass >= 0.9) & (pst >= 16); est_h[rep] = xh[rep]
    # hindsight state of the hybrid chain (HSI-VN's bridges: anchors = verified | trusted geometry, blended bridges), recomputed here
    # (no learned score needed); the OWF branch's null judges the OWF REPORT itself: possibly off-map | OWF image possibly wrong |
    # never verified (as HSI's "offwrong+unl", with the OWF image in place of the chain)
    import hsi_eval as HE
    kw = {a: b for a, b in HE.VARIANTS["HSI-VN"].items() if a in ("rot_max", "metric_windows")}
    # bridge source: the topological chain (independent of the OWF; default) or the hybrid chain ("hyb": OWF's own settled track can
    # certify itself through the odometry-consistency test -- the circularity found in Entry 11)
    zh = dict(z); name = f"{base}_s{seed}"
    if BRIDGE == "hyb": zh["est_c"] = est_h
    cfg = hsi.Cfg(zh, name, **kw); dseqs = hsi.deployment_seqs(zh); order = np.concatenate(dseqs)
    rank = np.empty(n, np.int64); rank[order] = np.arange(n)
    eb = zh["est_c"].astype(int)
    anc = hsi.causal_anchor(MP, eb, zh["o_q"], dseqs, cfg, n); ra, rb, *_ = hsi.trusted_geometry(zh, dseqs, cfg, anc)
    ver = hsi.hindsight_verified(MP, eb, zh["o_q"], dseqs, cfg, n)
    xt, sd, avail, *_ = hsi.hindsight_bridge(zh, dseqs, cfg, ver | ra | rb)
    _, _, dmap = hsi.hindsight_labels(zh, hsi.Cfg(zh, name, null_kind="off", **kw), xt, sd)
    fin = np.isfinite(sd); dm_ = np.nan_to_num(dmap, nan=-np.inf)
    null_off = fin & (dm_ > cfg.off_d - np.minimum(cfg.zm * sd, 0.25 * cfg.off_d))
    M2_ = MP.astype(float); M2_ = M2_ if M2_.ndim > 1 else M2_[:, None]; xt2 = xt if xt.ndim > 1 else xt[:, None]
    e_o = np.linalg.norm(M2_[np.maximum(xh, 0)] - np.nan_to_num(xt2), axis=1)
    NULLS = {"u": null_off | (fin & (e_o > cfg.excl + cfg.zm * sd)) | ~fin,            # + never verified (conservative)
             "v": null_off | (fin & (e_o > cfg.excl + cfg.zm * sd))}                   # verified-or-bridged frames only
    unit = np.zeros(n, np.int64)
    for si, idx in enumerate(dseqs):
        unit[idx] = si * 100000 + np.arange(len(idx)) // cfg.unit
        nv = ~fin[idx]; avail[idx[nv]] = rank[idx[-1]]                                # unlabelled frames: known at sequence end
    cal = hsi.calib_units(unit, cfg.cal_mod)
    M2 = MP.astype(float); M2 = M2 if M2.ndim > 1 else M2[:, None]; xs = np.maximum(xh, 0); ec = z["est_c"].astype(int)
    agt = (xh >= 0) & (np.linalg.norm(M2[xs] - M2[ec], axis=1) <= excl) & (np.linalg.norm(M2[xs] - M2[z["top"].astype(int)], axis=1) <= excl)
    score = np.where(xh >= 0, -np.log10(np.maximum(1 - mass, 1e-300)), -np.inf)
    ds = OD._dsname(base); segs_pa = PA.seg_classes(z, PA.OFF_D[ds.split(":")[0]])
    q2 = qp if qp.ndim > 1 else qp[:, None]; out = {}
    for v in variants:
        info = {}
        if v == "INC":
            ok = np.zeros(n, bool)
            for kind, e, D, L in OU.terms("H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"):
                c = (xh >= 0) & (mass >= 1 - e) & (pst >= D)
                if kind == "t": c &= agt
                ok |= c
            extra = ok & ~accH
        elif v == "H":
            extra = np.zeros(n, bool)
        else:
            p = parse(v); edges = np.array(BINS[p["bins"]]); strat = (np.searchsorted(edges, pst, side="right") - 1).astype(np.int64)
            sc = np.where(agt, score, -np.inf) if p["agree"] else score
            base_acc = accH if p["kind"] == "HC" else np.zeros(n, bool)
            c, info = calibrated(sc, strat, dseqs, NULLS[p["null"]], cal, unit, avail, H, base_acc, p["alpha"])
            extra = c & ~base_acc
        base_acc = np.zeros(n, bool) if (v not in ("INC", "H") and parse(v)["kind"] == "C") else accH
        acc = base_acc | extra; est = np.where(extra, xs, est_h)
        xf = MP[est].astype(float); xf = xf if xf.ndim > 1 else xf[:, None]
        err = np.linalg.norm(xf - q2, axis=1); gd = z["inm"] & (err <= excl)
        m = N.rule_metrics(acc, gd, z["inm"], z["offm"], seqs, H)
        e = N.track(acc, MP[est], qp, z["o_q"], bool(z["real"]), seqs, hz, seed, ds == "nclt")
        pos = {c_: [int(sum(bool(acc[g].any()) for g, cc in segs_pa if cc == c_)), int(sum(1 for _, cc in segs_pa if cc == c_))] for c_ in PA.CLASSES}
        out[v] = dict(recall=m["recall"], FL=m["FL"], seg_FAR=m["seg_FAR"], err_mean=float(np.nanmean(e)), pos=pos, thr=info,
                      frac_extra=float(extra.mean()))
    return t, dict(ds=ds, seed=seed, variants=out)


def main():
    fdir, hdir, cdirs, outf = sys.argv[1], sys.argv[2], sys.argv[3].split(","), sys.argv[4]
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    variants = opt("--variants", "INC,H,HC3,HC5,HC3a,C3").split(","); tag = opt("--tag", "aS5xms09_16"); ftag = opt("--ftag", "")
    jobs = int(opt("--jobs", "4")); hvar = opt("--hvar", "HSI-VN")
    fs = sorted(glob.glob(os.path.join(fdir, f"fr_*{ftag}_b1.npz")))
    with Pool(jobs) as p:
        R = {k: v for k, v in p.imap_unordered(one, [(f, hdir, cdirs, variants, tag, ftag, hvar) for f in fs], chunksize=1) if v is not None}
    json.dump(R, open(outf, "w"), indent=0, default=float); print(f"{len(R)} runs -> {outf}")


if __name__ == "__main__":
    main()
