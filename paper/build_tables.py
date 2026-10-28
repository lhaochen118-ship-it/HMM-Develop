"""Build markdown tables for the paper from analysis/results/*.json -> paper/tables.md"""
import os, json, glob
import numpy as np

R = os.path.join(os.path.dirname(__file__), "..", "analysis", "results")
OUT = os.path.join(os.path.dirname(__file__), "tables.md")
DS = [("rc", "RobotCar-Seasons (9 cond.)"), ("cmu", "Extended-CMU (11 dates)"), ("nord", "Nordland (3 seasons)")]
DESC_NAMES = {"salad": "SALAD", "megaloc": "MegaLoc", "dinov2": "DINOv2 (CLS+mean)", "mixvpr": "MixVPR", "cosplace": "CosPlace", "netvlad": "NetVLAD"}
MAIN = [("SelfCal-AA[combo AND z_gap+c]", "**SelfCal-AA (ours)**", "none"), ("SelfCal[min(maxsim, z_far+c)]", "SelfCal (ours, no alias guard)", "none"),
        ("LabelCal[maxsim] (day->all)", "Threshold, benign→all", "benign"), ("LabelCal[maxsim] (day, neg=off+alias)", "Threshold, benign, neg. incl. aliasing", "benign"),
        ("LabelCal[maxsim] (LOCO, SAFEVPR-style)", "Conformal LOCO (SAFEVPR protocol)", "other cond."),
        ("QuantileTransfer[maxsim] (day->all)", "Quantile Transfer", "benign"), ("LabelCal[CRSG] (day->all)", "Learned calibrator (CRSG), benign→all", "benign"),
        ("LabelCal[PA] (day->all)", "PA ratio, benign→all", "benign"), ("Theory Gauss[z_all]", "Gaussian z-norm null", "none"),
        ("Theory F-test[T_spacing]", "EVT spacing test (F(2,2k))", "none"), ("SelfCal[maxsim] (non-invariant)", "SelfCal on raw max-sim (ablation)", "none"),
        ("Oracle[maxsim] (labels per cond.)", "Oracle (labels of every condition)", "all")]


def load(ds, desc):
    f = os.path.join(R, f"eval_{ds}_{desc}.json")
    return {(r["method"], round(r["alpha"], 3)): r for r in json.load(open(f))["rows"]} if os.path.isfile(f) else {}


def cell(r, alias=True):
    if r is None: return "—"
    v = f"{r['FAR']:.3f} / {r['n_viol']}/{r['n_cond']} / {r['TPR']:.3f}"
    al = r.get("alias_acc", float("nan"))
    return v + (f" / {al:.2f}" if alias and al == al else (" / —" if alias else ""))


lines = []
for a in (0.05, 0.1):
    lines.append(f"\n### Table 1 (α = {a}). SALAD. Cell: off-map FAR / #conditions significantly above α (binomial, Bonferroni) / TPR / aliasing-accept rate\n")
    lines.append("| method | labels | " + " | ".join(n for _, n in DS) + " |\n|---|---|" + "---|" * len(DS))
    data = {ds: load(ds, "salad") for ds, _ in DS}
    for key, name, lab in MAIN:
        lines.append(f"| {name} | {lab} | " + " | ".join(cell(data[ds].get((key, a))) for ds, _ in DS) + " |")

descs = [d for d in ["netvlad", "cosplace", "mixvpr", "dinov2", "salad", "megaloc"] if glob.glob(os.path.join(R, f"eval_*_{d}.json"))]
lines.append("\n### Table 2 (α = 0.05). Descriptors. Cell: FAR / #viol / TPR / aliasing for SelfCal-AA | #viol for benign threshold, LOCO, CRSG | oracle TPR\n")
lines.append("| descriptor | dataset | R@1 (5 m,10° / 2 fr) | SelfCal-AA | benign thr. #viol (alias) | LOCO #viol | CRSG #viol | oracle TPR |\n|---|---|---|---|---|---|---|---|")
for d in descs:
    for ds, dn in DS:
        D = load(ds, d)
        if not D: continue
        g = lambda k: D.get((k, 0.05))
        s, b, lo, cr, orc = g(MAIN[0][0]), g(MAIN[2][0]), g(MAIN[4][0]), g(MAIN[6][0]), g(MAIN[-1][0])
        meta = json.load(open(os.path.join(R, f"eval_{ds}_{d}.json")))["meta"]
        lines.append(f"| {DESC_NAMES.get(d, d)} | {dn.split(' ')[0]} | {meta.get('r1', float('nan')):.3f} | {cell(s)} | "
                     f"{b['n_viol']}/{b['n_cond']} ({b['alias_acc']:.2f}) | {lo['n_viol']}/{lo['n_cond']} | {cr['n_viol']}/{cr['n_cond']} | {orc['TPR']:.3f} |")

AGG = [("SelfCal-AA[combo AND z_gap+c]", "SelfCal-AA (ours)", "none"), ("SelfCal[min(maxsim, z_far+c)]", "SelfCal (ours)", "none"),
       ("LabelCal[maxsim] (day->all)", "Threshold, benign→all", "benign"), ("LabelCal[maxsim] (day, neg=off+alias)", "Threshold, benign, neg. incl. aliasing", "benign"),
       ("LabelCal[maxsim] (LOCO, SAFEVPR-style)", "Conformal LOCO (SAFEVPR protocol)", "other cond."), ("QuantileTransfer[maxsim] (day->all)", "Quantile Transfer", "benign"),
       ("LabelCal[CRSG] (day->all)", "Learned calibrator (CRSG)", "benign"), ("LabelCal[PA] (day->all)", "PA ratio", "benign"),
       ("Theory Gauss[z_all]", "Gaussian z-norm null", "none"), ("Theory F-test[T_spacing]", "EVT spacing test", "none"),
       ("Oracle[maxsim] (labels per cond.)", "Oracle (labels of every condition)", "all")]
for a in (0.05, 0.1):
    lines.append(f"\n### Table 2a (α = {a}). All 6 descriptors × 3 datasets (18 settings, 138 deployment conditions)\n")
    lines.append("| method | labels | violating conditions | settings with ≥1 violation | mean TPR | median aliasing-accept | max worst-cond. FAR |\n|---|---|---|---|---|---|---|")
    for key, name, lab in AGG:
        v = c_ = sv = 0; tp, al, wf = [], [], []
        for f in glob.glob(os.path.join(R, "eval_*_*.json")):
            if "nordw" in f: continue
            for r in json.load(open(f))["rows"]:
                if r["method"] != key or abs(r["alpha"] - a) > 1e-9: continue
                v += r["n_viol"]; c_ += r["n_cond"]; sv += int(r["n_viol"] > 0); tp.append(r["TPR"]); wf.append(r["worstFAR"])
                if r.get("alias_acc") is not None and r["alias_acc"] == r["alias_acc"]: al.append(r["alias_acc"])
        if c_: lines.append(f"| {name} | {lab} | {v}/{c_} | {sv}/18 | {np.mean(tp):.3f} | " + (f"{np.median(al):.3f}" if al else "—") + f" | {max(wf):.3f} |")

lines.append("\n### Table 3. Excess-FAR bound Δ⁺_c (one-sided KS) — labelled benign null vs map null\n")
for ds, dn in DS:
    f = os.path.join(R, f"dominance_{ds}_salad.json")
    if not os.path.isfile(f): continue
    d = json.load(open(f)); keys = ["maxsim_day", "maxsim_map", "zfar_day", "zfarc_map"]
    mx = {k: max(v[k] for v in d.values()) for k in keys}
    lines.append(f"- {dn}: max over conditions — max-sim | benign null {mx['maxsim_day']:.3f}, max-sim | map null {mx['maxsim_map']:.3f}, "
                 f"z_far | benign null {mx['zfar_day']:.3f}, z_far+centring | map null {mx['zfarc_map']:.3f}")

lines.append("\n### Table 4. Ablations of SelfCal-AA (SALAD, α = 0.05): FAR / worst / TPR / aliasing\n")
for ds, dn in DS:
    f = os.path.join(R, f"ablation_{ds}_salad.json")
    if not os.path.isfile(f): continue
    d = json.load(open(f)); lines.append(f"\n**{dn}**\n\n| variant | FAR | worst | TPR | aliasing | null n |\n|---|---|---|---|---|---|")
    for k, v in d.items(): lines.append(f"| {k} | {v['FAR']:.3f} | {v['worst']:.3f} | {v['TPR']:.3f} | {v['alias']:.3f} | {v['n_null']} |")

lines.append("\n### Table 5. Deployment batches: BH on SelfCal p-values (SALAD), label-free confidence\n")
for ds, dn in DS:
    f = os.path.join(R, f"fdr_{ds}_salad.json")
    if not os.path.isfile(f): continue
    rows = json.load(open(f))
    for mix in sorted({r["mix"] for r in rows}):
        Rm = [r for r in rows if r["mix"] == mix]; m = lambda k: np.mean([r[k] for r in Rm]); M = lambda k: np.max([r[k] for r in Rm])
        lines.append(f"- {dn}, off-map share {mix}: π̂0 {m('pi0_hat'):.2f} (true {m('true_null'):.2f}); ECE label-free {m('ECE_labelfree'):.3f}; "
                     f"BH q=0.1: gross FDR mean {m('BH0.1_FDR_gross'):.3f} (max {M('BH0.1_FDR_gross'):.3f}), power {m('BH0.1_power'):.3f}")
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
