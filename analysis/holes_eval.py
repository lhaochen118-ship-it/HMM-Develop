"""Hole-ratio robustness of the CMS rules (Entry 28): map with 10 % / 50 % of the blocks removed (nhatlong1103/hmm-navcache-holes,
same constants as 30 %). Per seed: top-100 against the reduced map (as topk_dump.py, CPU or GPU), the CMS statistics
(cms.cms_stats), a route cache (TAO cost = the real part of the CMS statistics), then oc_curves.py on the label-free CMS
rules, CPC-SC+CS and the label-based baselines (TAO-SC / CPC-SC-T need the map-null top-K and are skipped here).
Usage: holes_eval.py <dump_dir> <any dir of the holes dataset> <ratio 10|50> <ds> <desc> --seeds 0,1,2 [--fams a,b]
Output: results/oc_<ds>_<desc>_d<ratio>_s<seed>.json, results/cms_d<ratio>_<ds>_<desc>_s<seed>.npz"""
import sys, os, glob, subprocess, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cms
import cms_exact as CE
import topk_dump as TKD

SEEDS = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")] if "--seeds" in sys.argv else [0, 1, 2]
FAMS = sys.argv[sys.argv.index("--fams") + 1] if "--fams" in sys.argv else None
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    dump, anyd, ratio, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
    root = anyd if os.path.isdir(os.path.join(anyd, f"d{ratio}")) else os.path.dirname(anyd.rstrip("/"))
    cdir = os.path.join(root, f"d{ratio}"); tag = ds.replace(":", "_")
    W = os.path.abspath(f"_holes_d{ratio}_{tag}_{desc}"); tkd, cmd_, tcd = (os.path.join(W, x) for x in ("topk", "cms", "taoc"))
    for d in (tkd, cmd_, tcd, "results"): os.makedirs(d, exist_ok=True)
    t0 = time.time(); ep = TKD.load(dump, ds, desc); q, M = ep.q.astype(np.float32), ep.m.astype(np.float32)
    for s in SEEDS:
        f = os.path.join(cdir, f"navcache_{tag}_{desc}_s{s}.npz")
        if not os.path.exists(f): print("missing", f); continue
        z = np.load(f, allow_pickle=True); kidx = z["kidx"]
        IL, SL, sdL = CE.topk_long(q, M[kidx], 300)                      # Entry 29: exact counterfactual (top-300 list)
        tk = dict(idx=IL[:, :100], sim=SL[:, :100].astype(np.float16), std=sdL)
        np.savez(os.path.join(tkd, f"topk_{tag}_{desc}_s{s}.npz"), **tk)
        st = CE.stats(z, dict(idx=IL, sim=SL, std=sdL), ds=ds)
        np.savez_compressed(os.path.join(cmd_, f"cms_{tag}_{desc}_s{s}.npz"), **st)
        np.savez_compressed(f"results/cms_d{ratio}_{tag}_{desc}_s{s}.npz", **{k: (v.astype(np.float32) if isinstance(v, np.ndarray) and v.dtype == np.float64 else v) for k, v in st.items()})
        np.savez_compressed(os.path.join(tcd, f"tao_{tag}_{desc}_s{s}.npz"), cost=st["cost"].astype(np.float32), j=st["j"].astype(np.int32))
        print(f"d{ratio} {ds}/{desc} s{s}: topk + cms {time.time() - t0:.0f}s", flush=True)
        cmd = [sys.executable, os.path.join(HERE, "oc_curves.py"), cdir, ds, desc, "--seeds", str(s), "--jobs", "1", "--out-suffix", f"_d{ratio}_s{s}",
               "--topk", tkd, "--taocache", tcd, "--cms", cmd_, "--variants", "--light", "--cms-alpha", "0.05,0.01", "--nav-pts", "3", "--navgate"] + (["--fams", FAMS] if FAMS else [])
        r = subprocess.run(cmd, capture_output=True, text=True); print(r.stdout[-300:], r.stderr[-500:] if r.returncode else "", flush=True)


if __name__ == "__main__":
    main()
