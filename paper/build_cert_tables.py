#!/usr/bin/env python3
"""Tables of the certified-sequential-localization paper, built from analysis/results/{cert,nav,natural}_*.json.
Usage: build_cert_tables.py [results_dir] -> paper/cert_tables.md"""
import sys, os, json, glob
import numpy as np

R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "analysis", "results")
OUT = os.path.join(os.path.dirname(__file__), "cert_tables.md")
DS_ORDER = ["rc", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside", "boreas"]
DS_NAME = {"rc": "RobotCar-Seasons", "cmu": "CMU-Seasons", "nord": "Nordland", "4s:office_loop": "4Seasons office",
           "4s:old_town": "4Seasons old town", "4s:countryside": "4Seasons countryside", "boreas": "Boreas"}
KINDS = ["FRAME", "RUN", "RUNO", "ANCH", "ANCHR"]
KNAME = {"FRAME": "per-frame (SelfCal)", "RUN": "run, no odometry (exp11)", "RUNO": "odometry run", "ANCH": "ours: anchored",
         "ANCHR": "ours: anchored, heading-free"}
H0 = {"rc": 5}


def rows():
    out = []
    for f in glob.glob(os.path.join(R, "cert_*.json")):
        r = json.load(open(f))
        for run in r["runs"]:
            for row in run["rows"]:
                row = dict(row); row["ds"], row["desc"], row["seed"] = r["ds"], r["desc"], run["seed"]; row.setdefault("alpha", 0.05); out.append(row)
    return out


def fmt(x, d=3): return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def main():
    rs = rows(); L = []
    dss = [d for d in DS_ORDER if any(r["ds"] == d for r in rs)]
    L.append("# Certified sequential localization — tables (auto-generated)\n")
    L.append("Excursion FAR = share of H-frame off-map excursions (leave-block-out) with any accepted frame; mean over 6 descriptors x 3 "
             "block grids, (max over runs), [worst condition, mean over runs]. alpha = 0.05; H = 10 frames (RobotCar: 5, its queries are "
             "9-frame snippets). Power = share of correctly matched on-map frames accepted; latency = median frames to the first correct acceptance.\n")
    for metric in ("validity", "power"):
        L.append(f"\n## Table {1 if metric == 'validity' else 2}: {metric}\n")
        L.append("| method | " + " | ".join(DS_NAME[d] for d in dss) + " |"); L.append("|---|" + "---|" * len(dss))
        for k in KINDS + ["LABEL"]:
            cells = []
            for d in dss:
                sel = [r for r in rs if r["ds"] == d and r["kind"] == (k if k != "LABEL" else "ANCH") and r["H"] == H0.get(d, 10) and r["alpha"] == 0.05]
                if k == "LABEL": sel = [r for r in sel if "label" in r]
                if not sel: cells.append("–"); continue
                if metric == "validity":
                    if k == "LABEL":
                        far = [r["label"]["FAR"] for r in sel]; wc = [max(r["label"]["cond"].values()) for r in sel if r["label"]["cond"]]
                    else:
                        far = [r["FAR_iso"] for r in sel]; wc = [max(r["cond_iso"].values()) for r in sel if r["cond_iso"]]
                    cells.append(f"{np.mean(far):.3f} ({np.max(far):.3f}) [{np.mean(wc):.3f}]")
                else:
                    if k == "LABEL": cells.append(f"{np.mean([r['label']['TPR'] for r in sel]):.2f}")
                    else: cells.append(f"{np.mean([r['TPR'] for r in sel]):.2f} / {np.median([r['latency_med'] for r in sel]):.0f}")
            L.append(f"| {KNAME.get(k, 'label-calibrated (ANCH stat., labels of 2 benign conditions)')} | " + " | ".join(cells) + " |")
    L.append("\n## Table 3: validity across alpha and horizon (ours: ANCH; mean excursion FAR over descriptors and grids)\n")
    L.append("| dataset | H | alpha=0.01 | alpha=0.05 | alpha=0.1 | null segments |"); L.append("|---|---|---|---|---|---|")
    for d in dss:
        for H in sorted({r["H"] for r in rs if r["ds"] == d}):
            cells = []
            for a in (0.01, 0.05, 0.1):
                sel = [r["FAR_iso"] for r in rs if r["ds"] == d and r["kind"] == "ANCH" and r["H"] == H and r["alpha"] == a]
                cells.append(fmt(np.mean(sel)) if sel else "–")
            ns = [r["n_null_seg"] for r in rs if r["ds"] == d and r["kind"] == "ANCH" and r["H"] == H]
            L.append(f"| {DS_NAME[d]} | {H} | " + " | ".join(cells) + f" | {np.mean(ns):.0f} |")
    # per-descriptor power
    L.append("\n## Table 4: power per descriptor (ANCH vs per-frame), H = 10 (RobotCar 5), alpha = 0.05\n")
    descs = ["megaloc", "salad", "mixvpr", "cosplace", "netvlad", "dinov2"]
    L.append("| dataset | " + " | ".join(descs) + " |"); L.append("|---|" + "---|" * len(descs))
    for d in dss:
        cells = []
        for de in descs:
            a = [r["TPR"] for r in rs if r["ds"] == d and r["desc"] == de and r["kind"] == "ANCH" and r["H"] == H0.get(d, 10) and r["alpha"] == 0.05]
            b = [r["TPR"] for r in rs if r["ds"] == d and r["desc"] == de and r["kind"] == "FRAME" and r["H"] == H0.get(d, 10) and r["alpha"] == 0.05]
            cells.append(f"{np.mean(a):.2f} vs {np.mean(b):.2f}" if a and b else "–")
        L.append(f"| {DS_NAME[d]} | " + " | ".join(cells) + " |")
    # navigation
    nav = [json.load(open(f)) for f in glob.glob(os.path.join(R, "nav_*.json"))]
    if nav:
        rules = []
        for n in nav:
            for k in n["runs"][0]["rules"]:
                if k not in rules: rules.append(k)
        L.append("\n## Table 5: navigation with 30 % map holes — mean position error (share of frames with error > rho), mean over descriptors and seeds\n")
        L.append("| dataset | " + " | ".join(rules) + " |"); L.append("|---|" + "---|" * len(rules))
        for d in DS_ORDER:
            ns = [n for n in nav if n["ds"] == d]
            if not ns: continue
            cells = []
            for k in rules:
                v = [run["rules"][k] for n in ns for run in n["runs"] if k in run["rules"]]
                cells.append(f"{np.mean([x['err_mean'] for x in v]):.1f} ({np.mean([x['frac_gt_rho'] for x in v]):.2f})" if v else "–")
            L.append(f"| {DS_NAME[d]} | " + " | ".join(cells) + " |")
        L.append("\nNordland errors are in frames; all others in metres. 4Seasons uses real VIO odometry.\n")
    nat = [json.load(open(f)) for f in glob.glob(os.path.join(R, "natural_*.json"))]
    if nat:
        L.append("\n## Table 6: natural off-map excursions (queries of other scenes/datasets driven against the map), excursion FAR at alpha = 0.05\n")
        L.append("| map | source | H | FRAME | ANCH | ANCHR |"); L.append("|---|---|---|---|---|---|")
        keys = sorted({(n["map"], r["src"], r["H"]) for n in nat for r in n["rows"]})
        for m, s, H in keys:
            cells = []
            for k in ("FRAME", "ANCH", "ANCHR"):
                v = [r["FAR"]["0.05"] for n in nat if n["map"] == m for r in n["rows"] if r["src"] == s and r["H"] == H and r["kind"] == k]
                cells.append(f"{np.mean(v):.3f} ({np.max(v):.3f})" if v else "–")
            L.append(f"| {DS_NAME.get(m, m)} | {DS_NAME.get(s, s)} | {H} | " + " | ".join(cells) + " |")
    open(OUT, "w").write("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    main()
