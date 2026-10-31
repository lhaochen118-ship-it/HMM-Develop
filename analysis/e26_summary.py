"""Entry 26 summary of oc_curves.py outputs: default points (all seeds) and curve statistics (seeds with curves).

Default point per (dataset, rule): mean recall, mean / worst segFAR, false-ONSET rate per off-map segment
(= H / ARL0, the quantity bounded by the windowed-onset theorem, cpc_theory.md 3e), mean navigation error.
Curves: recall at FL <= 0.005 / 0.01 / 0.02, pAUC (mean recall over FL in [0, 0.05]).
Usage: e26_summary.py <dir with oc_*.json (defaults)> [<dir with oc_*.json (curves)>] [--rules a,b,...] [--md out.md]"""
import sys, os, json, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oc_summary import recall_at, pauc

DS_ORDER = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
DS_NAME = {"boreas": "Boreas", "nclt": "NCLT", "cmu": "CMU", "nord": "Nordland", "4s:office_loop": "4S office",
           "4s:old_town": "4S old town", "4s:countryside": "4S countryside"}


def load(d):
    R = {}
    for f in sorted(glob.glob(os.path.join(d, "**", "oc_*.json"), recursive=True)):
        j = json.load(open(f)); runs = R.setdefault(j["ds"], {}).setdefault(j["desc"], {})
        for rk, run in j["runs"].items():                      # merge families of the same run from several files
            if rk in runs: runs[rk]["families"].update(run["families"]); runs[rk].setdefault("oracle", run.get("oracle"))
            else: runs[rk] = run
    return R


def defaults(R, H=10):
    T = {}
    for ds, bd in R.items():
        for desc, runs in bd.items():
            for rk, run in runs.items():
                for name, fam in run["families"].items():
                    df = fam.get("default")
                    if not df: continue
                    on = H / df["ARL0"] if df.get("ARL0", 0) > 0 else float("nan")
                    T.setdefault(ds, {}).setdefault(name, []).append((df["recall"], df["seg_FAR"], df["FL"], on, df.get("err_mean", np.nan)))
                og = run.get("oracle")
                if og: T.setdefault(ds, {}).setdefault("oracle", []).append((og["recall"], np.nan, np.nan, np.nan, og.get("err_mean", np.nan)))
    return T


def curves(R):
    C = {}
    for ds, bd in R.items():
        for desc, runs in bd.items():
            for rk, run in runs.items():
                for name, fam in run["families"].items():
                    cv = fam.get("curve")
                    if not cv: continue
                    C.setdefault(ds, {}).setdefault(name, []).append((recall_at(cv, "FL", 0.005), recall_at(cv, "FL", 0.01), recall_at(cv, "FL", 0.02), pauc(cv)))
    return C


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--") and x not in (sys.argv[sys.argv.index("--rules") + 1] if "--rules" in sys.argv else "",
                                                                         sys.argv[sys.argv.index("--md") + 1] if "--md" in sys.argv else "")]
    rules = sys.argv[sys.argv.index("--rules") + 1].split(",") if "--rules" in sys.argv else None
    out = []
    def load_many(ds_):
        R = {}
        for d in ds_.split(","):
            for k, bd in load(d).items():
                for desc, runs in bd.items():
                    tgt = R.setdefault(k, {}).setdefault(desc, {})
                    for rk, run in runs.items():
                        if rk in tgt: tgt[rk]["families"].update(run["families"])
                        else: tgt[rk] = run
        return R
    T = defaults(load_many(a[0])); C = curves(load_many(a[1])) if len(a) > 1 else {}
    dss = [d for d in DS_ORDER if d in T]
    names = rules or sorted({n for d in dss for n in T[d]})
    out.append("### Default points: recall / mean segFAR / worst segFAR / false onsets per segment / error (m), mean over runs\n")
    out.append("| rule | " + " | ".join(DS_NAME[d] for d in dss) + " |"); out.append("|---|" + "---|" * len(dss))
    for n in names:
        cells = []
        for d in dss:
            v = np.array(T[d].get(n, []), float)
            cells.append("–" if not len(v) else f"{np.nanmean(v[:, 0]):.3f} / {np.nanmean(v[:, 1]):.3f} / {np.nanmax(v[:, 1]):.3f} / {np.nanmean(v[:, 3]):.3f} / {np.nanmean(v[:, 4]):.1f} (n={len(v)})")
        out.append(f"| {n} | " + " | ".join(cells) + " |")
    if C:
        out.append("\n### Operating curves: recall at FL <= 0.01 / pAUC (FL in [0, 0.05]), mean over runs\n")
        out.append("| rule | " + " | ".join(DS_NAME[d] for d in dss) + " |"); out.append("|---|" + "---|" * len(dss))
        for n in names:
            cells = []
            for d in dss:
                v = np.array(C.get(d, {}).get(n, []), float)
                cells.append("–" if not len(v) else f"{v[:, 1].mean():.3f} / {v[:, 3].mean():.3f}")
            out.append(f"| {n} | " + " | ".join(cells) + " |")
    txt = "\n".join(out); print(txt)
    if "--md" in sys.argv: open(sys.argv[sys.argv.index("--md") + 1], "w").write(txt + "\n")


if __name__ == "__main__":
    main()
