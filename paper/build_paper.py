"""Assemble paper/selfcal_paper.md + generated tables + figures -> paper/SelfCal_paper_full.md and .pdf"""
import os, re, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); FIG = os.path.join(ROOT, "analysis", "figs")
subprocess.run([sys.executable, os.path.join(H, "build_tables.py")], check=True, capture_output=True)
txt = open(os.path.join(H, "selfcal_paper.md")).read()
tabs = {}
for block in open(os.path.join(H, "tables.md")).read().split("\n### ")[1:]:
    head = block.split("\n", 1)[0]; key = head.split(".")[0].strip()        # "Table 1 (α = 0.05)" / "Table 2 (α = 0.05)" ...
    tabs.setdefault(key, "**" + head.strip() + "**\n" + block.split("\n", 1)[1])


import shutil
os.makedirs(os.path.join(H, "figs"), exist_ok=True)


def fig(name, cap):
    p = os.path.join(FIG, name + ".png")
    if not os.path.isfile(p): return ""
    shutil.copy(p, os.path.join(H, "figs", name + ".png"))
    return f"\n![{cap}](figs/{name}.png)\n\n*{cap}*\n"


def after(heading, insert):
    global txt
    i = txt.index(heading); j = txt.find("\n## ", i + len(heading)); j2 = txt.find("\n# ", i + len(heading))
    j = min(x for x in (j, j2) if x > 0)
    txt = txt[:j] + "\n" + insert + "\n" + txt[j:]


t1 = tabs.get("Table 1 (α = 0", ""); t1b = [v for k, v in tabs.items() if k.startswith("Table 1")]
after("## 6.2 Main result", "\n".join(t1b[:1]) + fig("fig_far_power_salad", "Figure 2. Worst-condition off-map false-accept rate (top) and TPR (bottom) versus the target level, SALAD."))
after("## 6.3 Why it works", fig("fig_survival_rc_salad", "Figure 1. Survival functions of the off-map statistic per RobotCar condition (coloured) vs. the map pseudo-query null (black)."))
t3 = [v for k, v in tabs.items() if k.startswith("Table 3")]
if t3: after("## 6.3 Why it works", t3[0])
t2 = [v for k, v in tabs.items() if k.startswith("Table 2")]
if t2:
    t2 = sorted(t2, key=lambda x: 0 if "Table 2a" in x[:30] else 1)
    txt = txt.replace("Table 2a aggregates all six descriptors", "\n\n".join(t2) + "\n\nTable 2a aggregates all six descriptors", 1)
after("## 6.5 Batches: FDR and label-free confidence", "\n".join(v for k, v in tabs.items() if k.startswith("Table 5")))
after("## 6.6 Robustness and ablations", "\n".join(v for k, v in tabs.items() if k.startswith("Table 4")) + fig("fig_alias_salad", "Figure 3. Acceptance rate of in-map aliasing errors (>25 m) at α = 0.05."))
after("## 6.7 Foreign cities and datasets", "\n".join(v for k, v in tabs.items() if k.startswith("Table 6")))
after("## 6.8 Sequences: more power, but a caveat", "\n".join(v for k, v in tabs.items() if k.startswith("Table 7")))
after("## 6.9 Downstream: localisation on a map with holes", "\n".join(v for k, v in tabs.items() if k.startswith("Table 8")))
txt = re.sub(r"^---\ntitle:.*?---\n", "", txt, flags=re.S)
txt = "# Your Map Is Its Own Calibration Set: Label-Free, Shift-Robust Rejection of False Matches in Visual Place Recognition\n\n" + txt.replace("# Abstract", "## Abstract", 1)
out_md = os.path.join(H, "SelfCal_paper_full.md"); open(out_md, "w").write(txt)
subprocess.run([sys.executable, os.path.join(ROOT, "automation", "md2pdf.py"), out_md, os.path.join(H, "SelfCal_paper_full.pdf")], check=True)
print("wrote", out_md, "and PDF")
