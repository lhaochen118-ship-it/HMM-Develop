"""alpha sweep of the recommended rule (HSI-sc@alpha = HSI-rot-m-sc at level alpha; alpha = 0.05 is HSI-rot-m-sc itself) and the
Claxton'24 labelled reference, on the held-out runs (design set excluded as in hsi_summary.py).
Usage: hsi_alpha.py <hsi_results_dir> [--md out.md] [--png out.png] [--family PREFIX BASE]
--family: alpha variants named PREFIX@<alpha> with BASE as the alpha = 0.05 rule (default HSI-sc / HSI-rot-m-sc).
Per alpha: mean / max realized segFAR (per dataset mean, then over datasets), runs with segFAR > alpha, pooled recall, nav error."""
import sys, os, glob, json
import numpy as np

DESIGN = {"cosplace", "netvlad", "megaloc", "dinov2"}


def held(j):
    ds = j["ds"]
    return not (int(j["seed"]) == 0 and j["desc"] in DESIGN and ds not in ("oxford", "stlucia"))


def main():
    rd = sys.argv[1]; md = sys.argv[sys.argv.index("--md") + 1] if "--md" in sys.argv else None
    R = [j for j in (json.load(open(f)) for f in glob.glob(os.path.join(rd, "hsi_*.json"))) if held(j) and ":" not in j["ds"].replace("4s:", "")]
    R = [j for j in R if not j["ds"].startswith("4sx")]
    pre, base = (sys.argv[sys.argv.index("--family") + 1], sys.argv[sys.argv.index("--family") + 2]) if "--family" in sys.argv else ("HSI-sc", "HSI-rot-m-sc")
    rows = [(f"{pre}@0.01", 0.01), (f"{pre}@0.02", 0.02), (base, 0.05), (f"{pre}@0.1", 0.1), (f"{pre}@0.2", 0.2), ("Claxton24", 0.05), ("Xu21", 0.05), ("oracle", 0.0)]
    out = ["| rule | nominal α | runs | segFAR mean of dataset means | max dataset mean | runs > α | runs > 0.05 | pooled recall | nav err (m) |", "|---|---|---|---|---|---|---|---|---|"]
    for v, a in rows:
        J = [j for j in R if v in j["variants"]]
        if not J: continue
        byds = {}
        for j in J: byds.setdefault(j["ds"], []).append(j["variants"][v])
        dm = [np.mean([x["seg_FAR"] for x in L]) for L in byds.values()]
        nviol = sum(j["variants"][v]["seg_FAR"] > max(a, 1e-9) for j in J)
        rec = np.mean([j["variants"][v]["recall"] for j in J]); err = np.nanmean([j["variants"][v].get("err_mean", np.nan) for j in J])
        n05 = sum(j["variants"][v]["seg_FAR"] > 0.05 for j in J)
        out.append(f"| {v} | {a} | {len(J)} | {np.mean(dm):.4f} | {np.max(dm):.4f} | {nviol} ({nviol / len(J):.1%}) | {n05} | {rec:.3f} | {err:.1f} |")
    txt = "\n".join(out); print(txt)
    if md: open(md, "w").write("### α sweep (held-out runs)\n\n" + txt + "\n")
    if "--png" in sys.argv: plot(R, sys.argv[sys.argv.index("--png") + 1], rows[:5])


def plot(R, out, pts=None):
    """two panels, one axis each: realized segFAR vs nominal alpha (with the y = x bound), recall vs nominal alpha"""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    pts = pts or [("HSI-sc@0.01", 0.01), ("HSI-sc@0.02", 0.02), ("HSI-rot-m-sc", 0.05), ("HSI-sc@0.1", 0.1), ("HSI-sc@0.2", 0.2)]
    A, M, MX, F, RC = [], [], [], [], []
    for v, a in pts:
        J = [j["variants"][v] for j in R if v in j["variants"]]
        if not J: continue
        byds = {}
        for j in R:
            if v in j["variants"]: byds.setdefault(j["ds"], []).append(j["variants"][v]["seg_FAR"])
        A.append(a); M.append(np.mean([x["seg_FAR"] for x in J])); MX.append(max(np.mean(L) for L in byds.values()))
        F.append(np.mean([x["seg_FAR"] > a for x in J])); RC.append(np.mean([x["recall"] for x in J]))
    blue, ink, muted, grid = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": muted, "axes.labelcolor": ink, "xtick.color": muted, "ytick.color": muted})
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), dpi=200)
    a0 = ax[0]; lim = max(A) * 1.08
    a0.plot([0, lim], [0, lim], ls="--", lw=1, color=muted); a0.text(lim * 0.80, lim * 0.62, "bound\nsegFAR = α", color=muted, fontsize=8, ha="left", va="top")
    a0.plot(A, M, color=blue, lw=2, marker="o", ms=5, mec="white", mew=1.5)
    a0.plot(A, MX, color=blue, lw=1, ls=":", marker="s", ms=4, mec="white", mew=1)
    a0.text(A[-1], M[-1], "  mean over runs", color=ink, fontsize=8, va="center"); a0.text(A[-1], MX[-1], "  worst dataset", color=ink, fontsize=8, va="center")
    a0.set_xlim(0, lim * 1.35); a0.set_ylim(0, lim); a0.set_xlabel("nominal α"); a0.set_ylabel("realized segFAR (held-out)")
    a0.set_title("Validity: realized vs nominal", fontsize=9, color=ink, loc="left")
    a1 = ax[1]; a1.plot(A, RC, color=blue, lw=2, marker="o", ms=5, mec="white", mew=1.5)
    for i, (x, y) in enumerate(zip(A, RC)):
        a1.annotate(f"{y:.3f}", (x, y), xytext=(7, -3) if i < 2 else (-4, 7), textcoords="offset points", color=ink, fontsize=7,
                    ha="left" if i < 2 else "right", va="top" if i < 2 else "bottom")
    a1.set_xlabel("nominal α"); a1.set_ylabel("recall (held-out, pooled)"); a1.set_title("Power: recall vs nominal α", fontsize=9, color=ink, loc="left")
    a1.set_ylim(min(RC) - 0.01, max(RC) + 0.012)
    for a_ in ax:
        a_.grid(True, color=grid, lw=0.6); a_.set_axisbelow(True)
        for sp in ("top", "right"): a_.spines[sp].set_visible(False)
    fig.tight_layout(); fig.savefig(out, facecolor="#fcfcfb"); print("wrote", out)


if __name__ == "__main__":
    main()
