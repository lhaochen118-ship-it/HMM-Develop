"""Entry 30 development (set A subset: CMU / Oxford / St Lucia x CosPlace / MegaLoc x seeds 1-3, 18 runs): heading-offset bank
(--headings -6,-3,0,3,6; H5) and + selection with forgetting over 20 excl (H5m), at heading drift 0 and 0.13 deg / sqrt(m), against the
final rule on the same runs (Entry 29: un_aY0.json, un_aY13.json).
Usage: e30_dev_eval.py <dir with un_d<cfg>y<lv>.json> <un_aY0.json> <un_aY13.json>"""
import json, os, sys
import numpy as np
W = sys.argv[1]; R = {"0": json.load(open(sys.argv[2])), "013": json.load(open(sys.argv[3]))}
A = 0.05; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"; rng = np.random.default_rng(0)


def cell(rs):
    r = np.array([x["recall"] for x in rs]); s = np.array([x["seg_FAR"] for x in rs])
    return f"{r.mean():.3f} / {s.mean():.4f} / {(s > A).sum()} / {np.nanmean([x['err_mean'] for x in rs]):.1f}"


print("cell = recall / mean segFAR / runs > alpha / navigation error (m); delta = recall vs final rule on the same runs [95% CI]")
print("| drift | final rule (S5) | H5 | delta H5 | H5m | delta H5m |"); print("|---|---|---|---|---|---|")
for lv in ("0", "013"):
    ref = R[lv]; row = [f"| {lv.replace('013', '0.13')} | "]; ks = sorted(ref)
    row.append(cell([ref[k]["variants"][inc] for k in ks]) + " | ")
    for cfg in ("H5", "H5m"):
        f = os.path.join(W, f"un_d{cfg}y{lv}.json")
        if not os.path.exists(f): row.append("– | – | "); continue
        U = json.load(open(f)); kk = [k for k in ks if k in U]
        d = np.array([U[k]["variants"][inc]["recall"] - ref[k]["variants"][inc]["recall"] for k in kk])
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
        per = " ".join(f"{ds}:{np.mean([U[k]['variants'][inc]['recall'] - ref[k]['variants'][inc]['recall'] for k in kk if k.startswith(ds)]):+.3f}" for ds in ("cmu", "oxford", "stlucia"))
        row.append(cell([U[k]["variants"][inc] for k in kk]) + f" | {d.mean():+.4f} [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}] ({per}) | ")
    print("".join(row))
