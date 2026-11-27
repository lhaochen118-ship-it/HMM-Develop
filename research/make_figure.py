"""Figure 1: R@1 of Single vs tuned SeqSLAM vs IA-HMM (dev-selected) — small multiples per dataset.
Numbers are read from research/runs via the registry (E18 runs). Table view: research/reports/RESULTS_TABLES.md."""
import json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
ROOT = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "registry", "runs.jsonl"))]
def get(ds, desc, seed):
    c = [r for r in rows if r.get("experiment_id") == "E18" and r.get("dataset") == ds and r.get("descriptor") == desc and r.get("seed") == seed]
    return json.load(open(os.path.join(ROOT, "..", c[-1]["artifacts"], "metrics.json")))["results"] if c else None
PANELS = [("nord", 0, "Nordland (synchronised)"), ("nord-tw", 1, "Nordland, time-warped speed"), ("cmu", 0, "Extended CMU Seasons"), ("rc", 0, "RobotCar Seasons v2"), ("4s", 0, "4Seasons office_loop (real speed)"), ("4s2", 0, "4Seasons countryside (real speed)")]
DESCS = [("netvlad", "NetVLAD"), ("cosplace", "CosPlace"), ("salad", "SALAD"), ("megaloc", "MegaLoc")]
SER = [("single", "Single image", "#257de0"), ("seqslam", "SeqSLAM (tuned)", "#f47230"), ("OURS_devselected", "IA-HMM (ours)", "#00b894")]
INK, INK2, GRID = "#191919", "#666666", "#e6e6e6"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
fig, axes = plt.subplots(2, 3, figsize=(13, 6.6), sharey=True); axes = axes.ravel()
w = 0.26
for ax, (ds, seed, title) in zip(axes, PANELS):
    x = np.arange(len(DESCS))
    for i, (key, name, col) in enumerate(SER):
        vals = []
        for d, _ in DESCS:
            r = get(ds, d, seed); vals.append(r[key]["R@1"] if r and key in r else np.nan)
        b = ax.bar(x + (i - 1) * w, vals, width=w - 0.03, color=col, label=name, zorder=3)
        if key == "OURS_devselected":
            for xi, v in zip(x + (i - 1) * w, vals):
                if np.isfinite(v): ax.text(xi, v + 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=7.5, color=INK)
    ax.set_xticks(x); ax.set_xticklabels([n for _, n in DESCS])
    ax.set_title(title, fontsize=10, color=INK, loc="left")
    ax.set_ylim(0, 1.08); ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.tick_params(length=0)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
axes[0].set_ylabel("Recall@1 (test sequences)"); axes[3].set_ylabel("Recall@1 (test sequences)")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02))
fig.tight_layout(rect=(0, 0, 1, 0.95))
out = os.path.join(ROOT, "figures", "fig1_r1_small_multiples.png"); fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
print("saved", out)
