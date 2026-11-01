"""Figure: the validity-recall plane (mean segFAR vs mean recall per dataset) for the proposed CMS rules, the best previous
label-free rule and the label-calibrated baselines. 7 main datasets (366 runs, Entry 33) + Oxford RobotCar (60 runs).
Usage: fig_validity_recall.py <dir of oc_*_nb_s*.json> <dir of oc_oxford_*.json> <out.png>"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis"))
import e26_summary as E

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"            # validated categorical slots 1-3 (light surface)
INK, INK2, SURF, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
RULES = [("CMS-CPC/H+SH+G+NGRr", "CMS (ours)", BLUE, "o"), ("CMS-CPCW/H+SH+NGRr", "CMS-W (ours)", BLUE, "D"),
         ("CPC-SC-T0.5+SH", "map-null CPC-SC-T", AQUA, "s"),
         ("Xu21", "Xu'21", ORANGE, "^"), ("Claxton24", "Claxton'24", ORANGE, "v"), ("TAO26", "TAO'26", ORANGE, "<"),
         ("SUE24-seg", "SUE'24-seg", ORANGE, ">"), ("SU25-seg", "SU'25-seg", ORANGE, "P"), ("Carson23", "Carson'23", ORANGE, "X")]
DS = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside", "oxford"]


def main():
    T = E.defaults(E.load(sys.argv[1])); T.update(E.defaults(E.load(sys.argv[2])))
    fig, axs = plt.subplots(2, 4, figsize=(13, 6.4), sharex=True, sharey=True, facecolor=SURF)
    for ax, d in zip(axs.ravel(), DS):
        ax.set_facecolor(SURF); ax.set_xscale("log"); ax.set_xlim(8e-4, 1.3); ax.set_ylim(0, 1)
        ax.axvspan(8e-4, 0.05, color="#eef4fc", zorder=0); ax.axvline(0.05, color=INK2, lw=1, ls=(0, (4, 3)), zorder=1)
        ax.grid(True, color=GRID, lw=0.6, zorder=0)
        for n, lab, c, mk in RULES:
            v = np.array(T.get(d, {}).get(n, []), float)
            if not len(v): continue
            x, y = max(np.nanmean(v[:, 1]), 1e-3), np.nanmean(v[:, 0])
            ax.scatter([x], [y], s=64, marker=mk, color=c, edgecolor=SURF, linewidth=1.5, zorder=3, label=lab)
        ax.set_title(E.DS_NAME.get(d, d), fontsize=10, color=INK, loc="left")
        for s in ("top", "right"): ax.spines[s].set_visible(False)
        for s in ("left", "bottom"): ax.spines[s].set_color(INK2)
        ax.tick_params(colors=INK2, labelsize=8)
    axs[0, 0].text(0.0012, 0.04, "valid\n(segFAR ≤ α)", fontsize=8, color=INK2)
    for ax in axs[1]: ax.set_xlabel("mean segFAR (log)", fontsize=9, color=INK2)
    for ax in axs[:, 0]: ax.set_ylabel("recall", fontsize=9, color=INK2)
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=9, frameon=False, fontsize=8.5, labelcolor=INK)
    fig.suptitle("Validity vs recall (means per dataset): CMS rules are valid and have the highest recall among valid rules on all 8 datasets",
                 fontsize=11, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.06, 1, 0.95)); fig.savefig(sys.argv[3], dpi=160, facecolor=SURF)
    print("saved", sys.argv[3])


if __name__ == "__main__":
    main()
