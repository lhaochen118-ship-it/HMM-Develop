"""Where does the recall of a presence rule go? Decomposes the on-map frames of nav_demo --cache files into
  hit         reported and correct
  place       the reported place estimate is wrong (would be wrong even if reported)
  reentry     place estimate correct, not yet reported since the robot (re-)entered the map / the sequence started
  dropout     place estimate correct, not reported although the rule already reported in this on-map run
plus the oracle (top-1 correct) and the evidence of each class (median per-frame log LR of the presence chain).
Usage: recall_diag.py <cache_dir> <ds> <desc,...>  -> prints a table and results/recalldiag_<ds>.json"""
import sys, os, json, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nav_rules as NR


def decompose(acc, ok, inm, offm, seqs):
    """per on-map frame: 0 hit, 1 place wrong, 2 re-entry (no report yet in this on-map run), 3 dropout"""
    cls = np.full(len(acc), -1)
    for idx in seqs:
        started = False
        for t in idx:
            if offm[t]: started = False; continue
            if not inm[t]: continue
            if acc[t] and ok[t]: cls[t] = 0; started = True
            elif not ok[t]: cls[t] = 1; started = started or acc[t]
            else: cls[t] = 3 if started else 2
    return cls


def main():
    cdir, ds, descs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    out = {}
    for desc in descs:
        for f in sorted(glob.glob(os.path.join(cdir, f"navcache_{ds.replace(':', '_')}_{desc}_s*.npz"))):
            z = np.load(f, allow_pickle=True); b = NR.base_parts(z); e1, ea, er = b["e"]; et, eat, ert = b["tce"]
            inm, offm, q = z["inm"], z["offm"], z["q_pos"]; ex = b["excl"]
            ok_c = np.linalg.norm(b["MP"][b["est_c"]] - q, axis=1) <= ex
            ok_h = np.linalg.norm(z["x_hmm"] - q, axis=1) <= ex
            em = (np.minimum(e1, et), np.minimum(ea, eat), np.minimum(er, ert))
            rules = {"CPC-HMM": (b["pres"](e1, ea, er) > 0.5, ok_c), "TCEmin": (b["pres"](*em) > 0.5, ok_c),
                     "Xu21": (z["acc_h"], ok_h), "certified": (z["Rq"] > z["thr"], z["good"]), "oracle": (z["good"], z["good"])}
            agree = np.linalg.norm(b["MP"][b["top"]] - b["MP"][b["est_c"]], axis=1) <= ex
            ll = np.log(np.maximum(0.5 * (np.where(agree, em[0], em[1]) + em[2]), 1e-300))
            key = f"{desc}_s{int(z['seed'])}"; out[key] = {}
            for n, (acc, ok) in rules.items():
                c = decompose(acc, ok, inm, offm, b["seqs"]); non = max(inm.sum(), 1)
                r = {k: float((c == i).sum() / non) for i, k in enumerate(("hit", "place", "reentry", "dropout"))}
                if n == "TCEmin":
                    for i, k in enumerate(("hit", "place", "reentry", "dropout")):
                        r["ll_" + k] = float(np.median(ll[c == i])) if (c == i).any() else float("nan")
                    r["ll_off"] = float(np.median(ll[offm]))
                    r["p_top_dropout"] = float(np.median(z["p_frame"][c == 3])) if (c == 3).any() else float("nan")
                    r["agree_dropout"] = float(agree[c == 3].mean()) if (c == 3).any() else float("nan")
                    r["agree_hit"] = float(agree[c == 0].mean()) if (c == 0).any() else float("nan")
                out[key][n] = r
            print(key, " | ".join(f"{n}: " + " ".join(f"{k[:4]} {v:.3f}" for k, v in r.items() if not k.startswith(("ll", "p_", "agree")))
                                  for n, r in out[key].items()), flush=True)
            t = out[key]["TCEmin"]
            print("   TCEmin median ll: " + " ".join(f"{k} {v:.2f}" for k, v in t.items() if k.startswith(("ll", "p_", "agree"))), flush=True)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/recalldiag_{ds.replace(':', '_')}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
