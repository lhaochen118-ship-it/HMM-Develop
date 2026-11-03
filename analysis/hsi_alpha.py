"""alpha sweep of the recommended rule (HSI-sc@alpha = HSI-rot-m-sc at level alpha; alpha = 0.05 is HSI-rot-m-sc itself) and the
Claxton'24 labelled reference, on the held-out runs (design set excluded as in hsi_summary.py).
Usage: hsi_alpha.py <hsi_results_dir> [--md out.md]
Per alpha: mean / max realized segFAR (per dataset mean, then over datasets), runs with segFAR > alpha, pooled recall, nav error."""
import sys, os, glob, json
import numpy as np

DESIGN = {"cosplace", "netvlad", "megaloc", "dinov2"}


def held(j):
    ds = j["ds"]
    return not (int(j["seed"]) == 0 and j["desc"] in DESIGN and ds not in ("oxford", "stlucia"))


def main():
    rd = sys.argv[1]; md = sys.argv[sys.argv.index("--md") + 1] if "--md" in sys.argv else None
    R = [j for j in (json.load(open(f)) for f in glob.glob(os.path.join(rd, "hsi_*.json"))) if held(j) and ":" not in j["ds"].replace("4s:", "")]
    R = [j for j in R if not j["ds"].startswith("4sx")]
    rows = [("HSI-sc@0.01", 0.01), ("HSI-sc@0.02", 0.02), ("HSI-rot-m-sc", 0.05), ("HSI-sc@0.1", 0.1), ("HSI-sc@0.2", 0.2), ("Claxton24", 0.05), ("Xu21", 0.05), ("oracle", 0.0)]
    out = ["| rule | nominal α | runs | segFAR mean of dataset means | max dataset mean | runs > α | pooled recall | nav err (m) |", "|---|---|---|---|---|---|---|---|"]
    for v, a in rows:
        J = [j for j in R if v in j["variants"]]
        if not J: continue
        byds = {}
        for j in J: byds.setdefault(j["ds"], []).append(j["variants"][v])
        dm = [np.mean([x["seg_FAR"] for x in L]) for L in byds.values()]
        nviol = sum(j["variants"][v]["seg_FAR"] > max(a, 1e-9) for j in J)
        rec = np.mean([j["variants"][v]["recall"] for j in J]); err = np.nanmean([j["variants"][v].get("err_mean", np.nan) for j in J])
        out.append(f"| {v} | {a} | {len(J)} | {np.mean(dm):.4f} | {np.max(dm):.4f} | {nviol} ({nviol / len(J):.1%}) | {rec:.3f} | {err:.1f} |")
    txt = "\n".join(out); print(txt)
    if md: open(md, "w").write("### α sweep (held-out runs)\n\n" + txt + "\n")


if __name__ == "__main__":
    main()
