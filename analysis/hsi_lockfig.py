"""Figure for Prop 7 (calibration lock-out cliff): CMU development runs, HSI-rot-m-sc vs HSI-VN.
Usage: hsi_lockfig.py <results_dir> <out.png>"""
import sys, glob, json
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt


def main():
    rd, out = sys.argv[1], sys.argv[2]
    R = [json.load(open(f))["variants"] for f in glob.glob(rd + "/hsi_cmu_*.json")]
    R = [v for v in R if "HSI-rot-m-sc" in v and "HSI-VN" in v]
    a = np.array([[v["HSI-rot-m-sc"].get("frac_c", np.nan), v["HSI-VN"].get("frac_c", np.nan), v["HSI-rot-m-sc"]["recall"], v["HSI-VN"]["recall"]] for v in R])
    locked = a[:, 0] < 0.1
    blue, orange, ink, muted, grid = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": muted, "axes.labelcolor": ink, "xtick.color": muted, "ytick.color": muted})
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0), dpi=200)
    rng = np.random.default_rng(0)
    for i, (col, lab) in enumerate(((0, "HSI-rot-m-sc"), (1, "HSI-VN"))):
        y = a[:, col]; x = i + rng.uniform(-0.12, 0.12, len(y))
        ax[0].scatter(x, y, s=16, color=[orange if l else blue for l in locked], edgecolor="white", linewidth=0.6, zorder=3)
    ax[0].axhline(0.1, ls="--", lw=1, color=muted); ax[0].text(1.35, 0.115, "locked (< 0.1)", color=muted, fontsize=7, va="center")
    ax[0].set_xticks([0, 1]); ax[0].set_xticklabels(["HSI-rot-m-sc", "HSI-VN"]); ax[0].set_xlim(-0.5, 1.9)
    ax[0].set_ylabel("fraction of frames reported by (c)"); ax[0].set_title(f"Learned branch: locked runs {int(locked.sum())} → {int((a[:, 1] < 0.1).sum())} / {len(a)}", fontsize=9, color=ink, loc="left")
    for k in range(len(a)):
        ax[1].plot([0, 1], [a[k, 2], a[k, 3]], color=orange if locked[k] else blue, lw=1, alpha=0.8, marker="o", ms=3, mec="white", mew=0.5)
    ax[1].set_xticks([0, 1]); ax[1].set_xticklabels(["HSI-rot-m-sc", "HSI-VN"]); ax[1].set_xlim(-0.3, 1.3)
    ax[1].set_ylabel("recall (per run)"); ax[1].set_title(f"CMU recall {a[:, 2].mean():.3f} → {a[:, 3].mean():.3f}", fontsize=9, color=ink, loc="left")
    ax[1].text(1.05, np.mean(a[locked, 3]), "locked under\nHSI-rot-m-sc", color=orange, fontsize=7, va="center")
    ax[1].text(1.05, np.mean(a[~locked, 3]) + 0.03, "not locked", color=blue, fontsize=7, va="center")
    for a_ in ax:
        a_.grid(True, axis="y", color=grid, lw=0.6); a_.set_axisbelow(True)
        for sp in ("top", "right"): a_.spines[sp].set_visible(False)
    fig.tight_layout(); fig.savefig(out, facecolor="#fcfcfb"); print("wrote", out, len(a), "runs")


if __name__ == "__main__":
    main()
