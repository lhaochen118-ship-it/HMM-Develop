"""Figure 2: component ablation under variable speed — Nordland time-warp (3 seeds, mean and per-seed dots) and
real 4Seasons office_loop. Single series per panel row => no legend needed beyond axis labels."""
import json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
ROOT = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "registry", "runs.jsonl"))]
def res(ds, desc, seed):
    c = [r for r in rows if r.get("experiment_id") == "E18" and r.get("dataset") == ds and r.get("descriptor") == desc and r.get("seed") == seed]
    return json.load(open(os.path.join(ROOT, "..", c[-1]["artifacts"], "metrics.json")))["results"] if c else None
M = [("single", "Single image"), ("seqslam", "SeqSLAM (tuned)"), ("hmm_fixed", "HMM, fixed kernel"), ("LV", "+ latent velocity"),
     ("LV+ME", "+ change emission"), ("LV+ME+IA", "+ info-aware β (full)")]
INK, INK2, GRID, C1, C2 = "#191919", "#666666", "#e6e6e6", "#257de0", "#9c9c9c"
plt.rcParams.update({"font.size": 9})
panels = [("nord-tw", "netvlad", [1, 2, 3], "Nordland time-warp · NetVLAD"), ("nord-tw", "salad", [1, 2, 3], "Nordland time-warp · SALAD"),
          ("4s", "netvlad", [0], "4Seasons office_loop (real) · NetVLAD"), ("4s3", "salad", [0], "4Seasons old_town (real stops) · SALAD")]
fig, axes = plt.subplots(1, 4, figsize=(13, 3.2), sharey=True)
for ax, (ds, d, seeds, title) in zip(axes, panels):
    y = np.arange(len(M))[::-1]
    for i, (k, name) in enumerate(M):
        vals = [r[k]["R@1"] for s in seeds if (r := res(ds, d, s)) and k in r]
        if not vals: continue
        ax.scatter(vals, [y[i]] * len(vals), s=14, color=C2, zorder=3)
        ax.scatter([np.mean(vals)], [y[i]], s=46, color=C1, zorder=4)
        ax.text(np.mean(vals), y[i] + 0.3, f"{np.mean(vals):.2f}", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_yticks(y); ax.set_yticklabels([n for _, n in M]); ax.set_xlim(0.3, 1.02); ax.set_ylim(-0.5, len(M) - 0.2)
    ax.set_title(title, fontsize=9.5, loc="left", color=INK); ax.grid(axis="x", color=GRID, lw=0.8, zorder=0)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.tick_params(length=0, colors=INK2); ax.set_xlabel("Recall@1 (test)", color=INK2)
fig.text(0.01, -0.04, "Large dot = mean over time-warp seeds; small grey dots = individual seeds (Nordland). Tables: reports/RESULTS_TABLES.md",
         fontsize=7.5, color=INK2)
fig.tight_layout()
out = os.path.join(ROOT, "figures", "fig2_ablation_variable_speed.png"); fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
print("saved", out)
