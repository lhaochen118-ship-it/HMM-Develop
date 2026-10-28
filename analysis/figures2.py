"""Paper figures for SelfCal (uses cached statistics). Usage: figures2.py <dump_rc_nord> <dump_cmu> [desc]"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import vprlib as V, selfcal as SC
from sc_eval import CFG
from eval_all import signals

FIG = os.path.join(os.path.dirname(__file__), "figs"); os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 200,
                     "axes.titlesize": 8, "legend.fontsize": 6})
C_OURS, C_OURS2, C_LAB, C_LOCO, C_QT, C_CRSG, C_OR = "#1f5fbf", "#6aa5ee", "#d1495b", "#edae49", "#8e5ad6", "#66a182", "#555555"


def save(fig, name):
    for ext in ("png", "pdf"): fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)


def load(ds, dump, desc):
    ep = V.LOADERS[ds](dump, desc); c = CFG[ds]
    raw = signals(ep, c, False, f"{ds}_{desc}"); cen = signals(ep, c, True, f"{ds}_{desc}")
    inm = V.nearest_map_dist(ep) <= c["in_d"]; _, dt, _ = V.top1_errors(ep)
    corr = V.correct(ep, *c["tol"]) & inm; alias = inm & (dt > c["excl"])
    offm = np.isfinite(raw[1]["maxsim"]) & np.isfinite(cen[1]["z_far"])
    return ep, c, raw, cen, corr, alias, offm


def fig_survival(ep, raw, cen, offm, name, title):
    """Mechanism: off-map statistic distribution per condition vs the map pseudo-query null."""
    conds = sorted(set(ep.q_cond)); cmap = plt.get_cmap("viridis", len(conds))
    fig, axs = plt.subplots(1, 2, figsize=(5.6, 2.2))
    for ax, (src, st, lab) in zip(axs, [(raw, "maxsim", "max similarity (raw)"), (cen, "z_far", r"$z_{far}$ (affine-invariant, centred)")]):
        nul = np.sort(src[0][st][np.isfinite(src[0][st])])
        ax.plot(nul, 1 - np.arange(1, len(nul) + 1) / len(nul), "k-", lw=1.6, label="map pseudo-queries (null)")
        for i, cc in enumerate(conds):
            v = np.sort(src[1][st][offm & (ep.q_cond == cc)])
            ax.plot(v, 1 - np.arange(1, len(v) + 1) / len(v), color=cmap(i), lw=0.8, alpha=0.9, label=str(cc)[:12])
        ax.set_yscale("log"); ax.set_ylim(5e-3, 1); ax.set_xlabel(lab); ax.set_ylabel("P(statistic ≥ t)")
    axs[0].set_title(f"{title}: max similarity"); axs[1].set_title(r"$z_{far}$ (affine-invariant, centred)")
    axs[1].legend(frameon=False, ncol=2, loc="lower left"); fig.tight_layout(); save(fig, name)


def method_pvals(raw, cen, cond, offm, cal):
    """p-values (off-map, in-map) per method; label methods via split-conformal on calib-condition off-map."""
    nul = [raw[0]["maxsim"], cen[0]["z_far"]]
    pco = (SC.combined_p(nul, [raw[1]["maxsim"], cen[1]["z_far"]]), SC.combined_p(nul, [raw[2]["maxsim"], cen[2]["z_far"]]))
    paa = (SC.selfcal_p(raw[0], cen[0], raw[1], cen[1]), SC.selfcal_p(raw[0], cen[0], raw[2], cen[2]))
    lab = lambda st: (SC.conformal_p(raw[1][st][cal & offm], raw[1][st]), SC.conformal_p(raw[1][st][cal & offm], raw[2][st]))
    loco_o, loco_i = np.ones(len(cond)), np.ones(len(cond))
    for cc in set(cond):
        m = cond == cc; nv = raw[1]["maxsim"][(~m) & offm]
        loco_o[m] = SC.conformal_p(nv, raw[1]["maxsim"][m]); loco_i[m] = SC.conformal_p(nv, raw[2]["maxsim"][m])
    return {"SelfCal (ours)": (pco, C_OURS2), "SelfCal-AA (ours)": (paa, C_OURS),
            "LabelCal benign→all": (lab("maxsim"), C_LAB), "LabelCal LOCO (SAFEVPR-style)": ((loco_o, loco_i), C_LOCO)}


def fig_far_power(datasets, name):
    alphas = np.array([0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2])
    fig, axs = plt.subplots(2, len(datasets), figsize=(2.3 * len(datasets), 4.0))
    for j, (title, ep, c, raw, cen, corr, alias, offm) in enumerate(datasets):
        cond = ep.q_cond; conds = sorted(set(cond))
        calib = c["calib"] or sorted(conds, key=lambda x: -corr[cond == x].mean())[:2]; cal = np.isin(cond, calib)
        for mname, ((po, pi), col) in method_pvals(raw, cen, cond, offm, cal).items():
            worst = [max(np.mean(po[offm & (cond == cc)] <= a) for cc in conds if (offm & (cond == cc)).sum() >= 20) for a in alphas]
            axs[0, j].plot(alphas, worst, "o-", ms=2.5, lw=1.1, color=col, label=mname)
            axs[1, j].plot(alphas, [np.mean(pi[corr] <= a) for a in alphas], "o-", ms=2.5, lw=1.1, color=col)
        axs[0, j].plot([0, .2], [0, .2], "k--", lw=0.7); axs[0, j].set_title(title)
        axs[0, j].set_xlabel(r"target $\alpha$"); axs[1, j].set_xlabel(r"target $\alpha$")
    axs[0, 0].set_ylabel("worst-condition off-map\nfalse-accept rate"); axs[1, 0].set_ylabel("TPR (correct in-map)")
    axs[0, 0].legend(frameon=False, loc="upper left"); fig.tight_layout(); save(fig, name)


def fig_alias(datasets, name, a=0.05):
    fig, ax = plt.subplots(figsize=(4.2, 2.0)); W = 0.2
    for j, (title, ep, c, raw, cen, corr, alias, offm) in enumerate(datasets):
        cond = ep.q_cond; conds = sorted(set(cond))
        calib = c["calib"] or sorted(conds, key=lambda x: -corr[cond == x].mean())[:2]; cal = np.isin(cond, calib)
        for i, (mname, ((po, pi), col)) in enumerate(method_pvals(raw, cen, cond, offm, cal).items()):
            ax.bar(j + (i - 1.5) * W, np.mean(pi[alias] <= a), W, color=col, label=mname if j == 0 else None)
    ax.axhline(a, color="k", ls="--", lw=0.7); ax.set_xticks(range(len(datasets))); ax.set_xticklabels([d[0] for d in datasets])
    ax.set_ylabel(f"accepted aliasing errors\n(in-map, >25 m) at α={a}"); ax.legend(frameon=False, ncol=2, fontsize=5.5)
    fig.tight_layout(); save(fig, name)


if __name__ == "__main__":
    d1, d2 = sys.argv[1], sys.argv[2]; desc = sys.argv[3] if len(sys.argv) > 3 else "salad"
    D = []
    for ds, dump, title in [("rc", d1, "RobotCar-Seasons"), ("cmu", d2, "Extended-CMU"), ("nord", d1, "Nordland")]:
        ep, c, raw, cen, corr, alias, offm = load(ds, dump, desc); D.append((title, ep, c, raw, cen, corr, alias, offm))
        if ds == "rc": fig_survival(ep, raw, cen, offm, f"fig_survival_{ds}_{desc}", title)
    fig_far_power(D, f"fig_far_power_{desc}"); fig_alias(D, f"fig_alias_{desc}")
    print("figures written to", FIG, sorted(os.listdir(FIG)))
