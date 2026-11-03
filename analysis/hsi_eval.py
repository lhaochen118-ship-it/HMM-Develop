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
    "HSI": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint", adaptive=True),
    "HSI-fixtol": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint"),
    "HSI-sess": dict(scope="session", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint"),
    "HSI-nosc": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", train_all=True, calib="joint"),
    "HSI-off": dict(scope="pooled", null_kind="off", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True, calib="joint"),
    "HSI-regime": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True),
    "HSI-v4": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="blend"),
    "HSI-rigid": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="loose", bridge="rigid", sc_lags=(5, 10, 20), train_all=True),
    "HSI-nounl": dict(scope="pooled", null_kind="offwrong", gate_kind="loose", bridge="blend", sc_lags=(5, 10, 20), train_all=True),
    "HSI-nogate": dict(scope="pooled", null_kind="offwrong+unl", gate_kind="none", bridge="blend", sc_lags=(5, 10, 20), train_all=True),
    "geo": None, "anc": None,
}


def find(cdir, fn):
    roots = ["/kaggle/input", "."] if cdir == "AUTO" else [cdir]
    for r in roots:
        for d, _, fs in os.walk(r, followlinks=True):
            if fn in fs: return os.path.join(d, fn)
    return None


def parse_seeds(s):
    if "-" in s: a, b = s.split("-"); return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def main():
    a = sys.argv[1:]
    vs = a[a.index("--variants") + 1].split(",") if "--variants" in a else ["HSI", "geo", "anc"]
    tag = ("_" + a[a.index("--tag") + 1]) if "--tag" in a else ""
    frames = "--frames" in a
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--variants", "--tag"))]
    cdir, ds, desc, seeds = pos[0], pos[1], pos[2], parse_seeds(pos[3])
    os.makedirs("results", exist_ok=True)
    for seed in seeds:
        fn = f"navcache_{ds.replace(':', '_')}_{desc}_s{seed}.npz"; f = find(cdir, fn)
        if f is None: print("missing", fn, flush=True); continue
        z = np.load(f, allow_pickle=True); name = fn[9:-4]; out = {"ds": ds, "desc": desc, "seed": seed, "variants": {}}; masks = {}
        cfg = hsi.Cfg(z, name); seqs = hsi.deployment_seqs(z); n = len(z["est_c"])
        for v in vs:
            t0 = time.time()
            if v in ("geo", "anc"):
                cfg.tolarr = hsi.adaptive_tolerance(z, seqs, cfg)
                anc = hsi.causal_anchor(z["MP"], z["est_c"], z["o_q"], seqs, cfg, n)
                if v == "anc": acc = anc
                else: ra, rb, *_ = hsi.trusted_geometry(z, seqs, cfg, anc); acc = ra | rb
                o = dict(acc=acc, seqs=seqs, cfg=cfg); diag = {}
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
