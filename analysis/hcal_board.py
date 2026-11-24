"""Scoreboard for owf_hcal.py / owf_union.py JSON files: per dataset recall / mean segFAR / runs > alpha / navigation error, pooled numbers,
and the paired difference of every variant against a reference variant on the SAME runs (bootstrap over runs, 95 % CI).
Usage: hcal_board.py <json>[,json2] --ref INC [--variants A,B] [--seeds 55-57] [--md out.md]"""
import sys, json
import numpy as np

ALPHA = 0.05


def main():
    a = sys.argv[1:]; opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    R = {}
    for f in a[0].split(","): R.update(json.load(open(f)))
    ref = opt("--ref", "INC"); seeds = opt("--seeds", None)
    if seeds:
        s0, s1 = [int(x) for x in seeds.split("-")]; R = {k: v for k, v in R.items() if s0 <= int(v["seed"]) <= s1}
    allv = sorted({v for r in R.values() for v in r["variants"]})
    vs = opt("--variants", ",".join([ref] + [v for v in allv if v != ref])).split(",")
    keys = sorted(k for k, r in R.items() if all(v in r["variants"] for v in vs))
    dss = sorted({R[k]["ds"] for k in keys})
    L = [f"{len(keys)} runs (common to every variant), reference {ref}", "",
         "| dataset | n | " + " | ".join(vs) + " |", "|---|---|" + "---|" * len(vs)]
    cell = lambda xs: (f"{np.mean([x['recall'] for x in xs]):.3f} / {np.mean([x['seg_FAR'] for x in xs]):.4f} / "
                       f"{sum(x['seg_FAR'] > ALPHA for x in xs)} / {np.nanmean([x['err_mean'] for x in xs]):.1f}")
    for ds in dss + ["pooled"]:
        ks = [k for k in keys if ds == "pooled" or R[k]["ds"] == ds]
        L.append(f"| {ds} | {len(ks)} | " + " | ".join(cell([R[k]["variants"][v] for k in ks]) for v in vs) + " |")
    L += ["", "cell = recall / mean segFAR / runs > alpha / navigation error (m)", "",
          "| variant | Δ recall vs ref (CI 95 %) | wins / ties / losses | Δ nav (m) | worst-dataset mean segFAR | runs > α |", "|---|---|---|---|---|---|"]
    rng = np.random.default_rng(0)
    for v in vs:
        if v == ref: continue
        d = np.array([R[k]["variants"][v]["recall"] - R[k]["variants"][ref]["recall"] for k in keys])
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
        dn = np.nanmean([R[k]["variants"][v]["err_mean"] for k in keys]) - np.nanmean([R[k]["variants"][ref]["err_mean"] for k in keys])
        worst = max(np.mean([R[k]["variants"][v]["seg_FAR"] for k in keys if R[k]["ds"] == ds]) for ds in dss)
        nab = sum(R[k]["variants"][v]["seg_FAR"] > ALPHA for k in keys)
        L.append(f"| {v} | {d.mean():+.4f} [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}] | "
                 f"{int((d > 1e-9).sum())} / {int((abs(d) <= 1e-9).sum())} / {int((d < -1e-9).sum())} | {dn:+.2f} | {worst:.4f} | {nab} |")
    txt = "\n".join(L); print(txt)
    if "--md" in a: open(opt("--md", ""), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
