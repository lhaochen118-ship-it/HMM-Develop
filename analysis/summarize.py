"""Cross-descriptor summary from results/eval_<ds>_<desc>.json. Usage: summarize.py [alpha] -> prints + writes results/summary.md"""
import sys, os, json, glob
import numpy as np

R = os.path.join(os.path.dirname(__file__), "results"); A = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
SHOW = [("SelfCal-AA[combo AND z_gap+c]", "SelfCal-AA (ours)"), ("SelfCal[min(maxsim, z_far+c)]", "SelfCal (ours)"),
        ("LabelCal[maxsim] (day->all)", "LabelCal benign→all"), ("LabelCal[maxsim] (day, neg=off+alias)", "LabelCal benign, neg=off+alias"),
        ("LabelCal[maxsim] (LOCO, SAFEVPR-style)", "LabelCal LOCO (SAFEVPR-style)"), ("QuantileTransfer[maxsim] (day->all)", "Quantile Transfer"),
        ("LabelCal[CRSG] (day->all)", "CRSG benign→all"), ("Oracle[maxsim] (labels per cond.)", "Oracle (labels, every cond.)")]
DS = [("rc", "RobotCar"), ("cmu", "CMU"), ("nord", "Nordland")]
descs = sorted({os.path.basename(f).split("_", 2)[2][:-5] for f in glob.glob(os.path.join(R, "eval_*_*.json"))})
lines = [f"# Cross-descriptor summary (alpha = {A}) — cell: FAR / worst-cond FAR / #significant violations / TPR / aliasing-accept\n"]
for desc in descs:
    lines.append(f"\n## {desc}\n\n| method | " + " | ".join(n for _, n in DS) + " |\n|---|" + "---|" * len(DS))
    data = {}
    for ds, _ in DS:
        f = os.path.join(R, f"eval_{ds}_{desc}.json")
        if os.path.isfile(f): data[ds] = {r["method"]: r for r in json.load(open(f))["rows"] if abs(r["alpha"] - A) < 1e-9}
    for key, name in SHOW:
        cells = []
        for ds, _ in DS:
            r = data.get(ds, {}).get(key)
            if r is None: cells.append("—"); continue
            al = r.get("alias_acc", float("nan"))
            cells.append(f"{r['FAR']:.3f} / {r['worstFAR']:.3f} / {r['n_viol']}/{r['n_cond']} / {r['TPR']:.3f} / " + ("—" if al != al else f"{al:.3f}"))
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
txt = "\n".join(lines); print(txt); open(os.path.join(R, f"summary_a{A}.md"), "w").write(txt + "\n")
