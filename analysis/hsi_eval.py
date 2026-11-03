"""Evaluate HSI variants on nav_demo caches (one job = one dataset x descriptor, several seeds).

Usage: hsi_eval.py <cache_dir|AUTO> <ds> <desc> <seeds: 0-9 | 0,1,2> [--variants a,b,...] [--tag t] [--frames]
  AUTO: search /kaggle/input (and the cwd) for navcache_<ds>_<desc>_s<seed>.npz (several datasets may be mounted).
Writes results/hsi_<ds>_<desc>_s<seed>[_<tag>].json: per variant the protocol metrics (nav_demo.rule_metrics), position
classes (start / edge / deep, as position_audit.py), navigation error (nav_demo.track) and run diagnostics; --frames also
writes results/hsifr_<ds>_<desc>_s<seed>[_<tag>].npz (packed report masks per variant, for later audits)."""
import os, sys, json, time, glob
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hsi

# variant name -> online_v2 keyword arguments ('geo' = geometric self-verification only, 'anc' = causal anchors only)
VARIANTS = {
    # main rule (frozen 2026-11-03 18:20 UTC on the seed-0 design runs, RESEARCH_LOG Entry 1)
    "HSI": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5),
    # ablations: one change each
    "HSI-adapt": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, adaptive="max"),          # self-calibrated (loosen-only) consistency tolerances
    "HSI-sess": dict(scope="session", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5),                           # calibration per session (Mondrian by condition) instead of pooled
    "HSI-regime": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="regime", floor=0.5),                         # conditional calibration on the (c) regime only
    "HSI-nosc": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", train_all=True, calib="joint", floor=0.5),                           # no short-track support for (c)
    "HSI-nounl": dict(scope="pooled", null_kind="offwrong", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5),                          # null without never-verified frames
    "HSI-nogate": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="none", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5),                         # no dead-reckoning contradiction gate for (c)
    "HSI-rigid": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="rigid", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5),                          # one rigid bridge per gap instead of blended dead reckoning
    "HSI-nofloor": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint"),                        # no MAP floor (conformal threshold only)
    "HSI-rot": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35),               # (Entry 2 candidate) bounded heading offset (20 deg) in the consistency tests
    "HSI-m": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, metric_windows=True),         # (Entry 2 candidate) windows in metres of path (Oxford / St Lucia: 10 m frames)
    "HSI-rot-m": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True),
    "HSI-rot-m-s": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True),            # (Entry 3 candidates) starts relaxed
    "HSI-rot-m-c": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, null_cap=0.25),              # null margin capped at off_d / 4
    "HSI-rot-m-sc": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25),
    "HSI-M": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, mondrian="ref"),   # (Entry 4) Mondrian by regime
    "HSI-M-nos": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, null_cap=0.25, mondrian="ref"),                   # Entry 4 without start relax
    "HSI-sc@0.01": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, alpha=0.01),
    "HSI-sc@0.02": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, alpha=0.02),
    "HSI-sc@0.1": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, alpha=0.1),
    "HSI-sc@0.2": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, alpha=0.2),
    # (Entry 5 candidates) split budget: geometric reports charged their own rate (measured on hindsight-confident null segments)
    "HSI-G": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, geo_budget="split"),
    "HSI-Gw": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, geo_budget="split-w"),
    "HSI-Gdrop": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, geo_budget="drop"),   # diagnostic: geometry not charged
    "HSI-V": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, anchors="ver+geo"),
    "HSI-Vc": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, anchors="ver+geo/charged"),
    "HSI-Vl": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, anchors="ver+geo/loo"),
    "HSI-Vle": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, anchors="ver+geo/loo-e"),
    "HSI-VM": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, start_relax=True, null_cap=0.25, anchors="ver+geo", mondrian="ref"),
    "HSI-VM-nos": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, null_cap=0.25, anchors="ver+geo", mondrian="ref"),
    "HSI-V-nos": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", floor=0.5, rot_max=0.35, metric_windows=True, null_cap=0.25, anchors="ver+geo"),
    "geo": None, "anc": None, "geo-rm": None,       # geo-rm: (a|b) with the rot-m geometry of Entry 2+ (diagnostic of the certificate alone)                       # geometric self-verification only (a|b); causal anchors only
    "Xu21": None, "oracle": None, "top1": None, "Claxton24": None,     # references from the cache: Xu'21 HMM off-map state (T, k tuned WITH labels on
}                                                   # the 2 easiest conditions, nav_demo), oracle (correct top-1 only), accept-all top-1


def find(cdir, fn):
    """the cache file in cdir; AUTO (or not found there): search /kaggle/input and the cwd (several datasets may be mounted)"""
    roots = ["/kaggle/input", "."] if cdir == "AUTO" else [cdir, "/kaggle/input"]
    for r in roots:
        for d, _, fs in os.walk(r, followlinks=True):
            if fn in fs: return os.path.join(d, fn)
    return None


def parse_seeds(s):
    if "-" in s: a, b = s.split("-"); return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def main():
    a = sys.argv[1:]
    vs = a[a.index("--variants") + 1].split(",") if "--variants" in a else list(VARIANTS)
    tag = ("_" + a[a.index("--tag") + 1]) if "--tag" in a else ""
    frames = "--frames" in a
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--variants", "--tag"))]
    cdir, ds, desc, seeds = pos[0], pos[1], pos[2], parse_seeds(pos[3])
    os.makedirs("results", exist_ok=True)
    for seed in seeds:
        fn = f"navcache_{ds.replace(':', '_')}_{desc}_s{seed}.npz"; f = find(cdir, fn)
        if f is None: print("missing", fn, flush=True); continue
        z = np.load(f, allow_pickle=True); name = fn[9:-4]; out = {"ds": ds, "desc": desc, "seed": seed, "cache_path": f, "variants": {}}; masks = {}
        print("cache", f, flush=True)
        cfg = hsi.Cfg(z, name); seqs = hsi.deployment_seqs(z); n = len(z["est_c"])
        for v in vs:
            t0 = time.time()
            if v == "Claxton24":                                 # Claxton et al. RA-L'24 style MLP monitor trained WITH labels on the 2 easiest conditions
                import nav_demo as N_
                bad_top = z["offm"] | (z["err_top"] > float(z["excl"]))
                acc = N_.claxton_rule(z["srt10"], z["Smean"], z["Sstd"], z["bsel"], z["good"], bad_top, int(z["seed"]))
                o = dict(acc=acc, seqs=seqs, cfg=cfg, xf=z["MP"][z["top"]]); diag = {}
            elif v in ("Xu21", "oracle", "top1"):
                MP_ = z["MP"]
                acc, xf = {"Xu21": (z["acc_h"], z["x_hmm"]), "oracle": (z["good"], MP_[z["top"]]), "top1": (np.ones(n, bool), MP_[z["top"]])}[v]
                o = dict(acc=acc, seqs=seqs, cfg=cfg, xf=xf); diag = {}
            elif v in ("geo", "anc"):
                cfg.tolarr = hsi.adaptive_tolerance(z, seqs, cfg)
                anc = hsi.causal_anchor(z["MP"], z["est_c"], z["o_q"], seqs, cfg, n)
                if v == "anc": acc = anc
                else: ra, rb, *_ = hsi.trusted_geometry(z, seqs, cfg, anc); acc = ra | rb
                o = dict(acc=acc, seqs=seqs, cfg=cfg); diag = {}
                cfg.tolarr = None
            elif v == "geo-rm":
                cg = hsi.Cfg(z, name, rot_max=0.35, metric_windows=True)
                anc = hsi.causal_anchor(z["MP"], z["est_c"], z["o_q"], seqs, cg, n); ra, rb, *_ = hsi.trusted_geometry(z, seqs, cg, anc)
                acc = ra | rb; o = dict(acc=acc, seqs=seqs, cfg=cg); diag = {}
            else:
                o = hsi.online_v2(z, name, **VARIANTS[v]); acc = o["acc"]
                diag = dict(n_cal_seg=o["n_cal_seg"], kappa=o["kappa"], frac_a=float(o["ra"].mean()), frac_b=float(o["rb"].mean()), frac_c=float(o["rc"].mean()))
            r = hsi.evaluate(z, name, o); r.update(diag); r["secs"] = time.time() - t0
            # per session (condition) segFAR / recall: the per-condition audit
            MP, est, q, inm, offm = z["MP"], z["est_c"], z["q_pos"], z["inm"], z["offm"]; cond = np.asarray(z["cond"]).astype(str)
            ok = np.linalg.norm(MP[est] - q, axis=1) <= cfg.excl; import nav_demo as N
            r["per_cond"] = {}
            for c in sorted(set(cond)):
                mc = cond == c; sq = [s for s in seqs if mc[s[0]]]
                rc = N.rule_metrics(acc & mc, ok & inm & mc, inm & mc, offm & mc, sq, cfg.H)
                r["per_cond"][c] = dict(recall=rc["recall"], seg_FAR=rc["seg_FAR"], n_seg=rc["n_seg"])
            out["variants"][v] = r; masks[v] = np.packbits(acc)
            print(f"{name} {v:10s} rec {r['recall']:.3f} seg {r['seg_FAR']:.3f} FL {r['FL']:.4f} err {r['err_mean']:.1f} "
                  + " ".join(f"{k}{c[0]}:{c[1]:.3f}" for k, c in r["classes"].items()) + f" | {r['secs']:.0f}s", flush=True)
        json.dump(out, open(f"results/hsi_{ds.replace(':', '_')}_{desc}_s{seed}{tag}.json", "w"), indent=1, default=float)
        if frames: np.savez_compressed(f"results/hsifr_{ds.replace(':', '_')}_{desc}_s{seed}{tag}.npz", n=n, **masks)


if __name__ == "__main__":
    main()
