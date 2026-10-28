"""Paper figures from an Episode (matplotlib, saved as PNG+PDF into analysis/figs)."""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, exp1_validity as E1

FIG = os.path.join(os.path.dirname(__file__), "figs"); os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})
PALETTE = ["#2a6fdb", "#e4572e", "#29a36a", "#f2a541", "#8e5ad6", "#6c757d", "#17becf", "#bc5090", "#003f5c"]


def save(fig, name):
    for ext in ("png", "pdf"): fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)


def fig_offmap_qq(ep, cfg, title, name, seed=0):
    """QQ plot of EVS p-values on OFF-MAP queries, one line per condition (uniform = valid)."""
    eh, off, _ = E1.make_holes(ep, cell=cfg["hole_cell"], frac=cfg["hole_frac"], seed=seed, off_d=cfg["off_d"], in_d=cfg["in_d"])
    p = V.evs_test(eh, cell=cfg["cell"], excl=cfg["excl"], k=cfg["k"])
    fig, ax = plt.subplots(figsize=(3.2, 3.0))
    for i, c in enumerate(sorted(set(eh.q_cond))):
        m = off & (eh.q_cond == c)
        if m.sum() < 10: continue
        q = np.sort(p[m]); u = (np.arange(1, len(q) + 1) - 0.5) / len(q)
        ax.plot(u, q, lw=1.2, color=PALETTE[i % len(PALETTE)], label=str(c)[:12])
    ax.plot([0, 1], [0, 1], "k--", lw=0.8); ax.set_xlabel("Uniform quantile"); ax.set_ylabel("EVS p-value (off-map)")
    ax.set_title(title); ax.legend(fontsize=6, frameon=False); save(fig, name)


def fig_far_vs_alpha(rows, title, name, methods, alphas=(0.01, 0.05, 0.1)):
    """Worst-condition realised false-accept rate vs target alpha for each method."""
    fig, ax = plt.subplots(figsize=(3.2, 3.0))
    for i, mt in enumerate(methods):
        ys = []
        for a in alphas:
            by = {}
            for r in rows:
                if r["method"] == mt and r["alpha"] == a and np.isfinite(r["FAR"]): by.setdefault(r["cond"], []).append(r["FAR"])
            ys.append(max(np.mean(v) for v in by.values()) if by else np.nan)
        ax.plot(alphas, ys, "o-", color=PALETTE[i % len(PALETTE)], lw=1.2, ms=3, label=mt)
    ax.plot([0, max(alphas)], [0, max(alphas)], "k--", lw=0.8)
    ax.set_xlabel(r"target $\alpha$"); ax.set_ylabel("worst-condition false-accept rate"); ax.set_title(title)
    ax.legend(fontsize=6, frameon=False); save(fig, name)
