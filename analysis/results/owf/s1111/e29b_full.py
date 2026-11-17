"""Entry 29b, full set-A subset (CMU 54 + Oxford 45 + St Lucia 30 = 129 runs, simulated 2-D odometry): final rule at heading drift 0.13
deg / sqrt(m) (owf_union of the aY13 frames) against the Entry 28 numbers at drift 0 (un2_aQ2.json, same code; GPU atomics give per-run
recall differences <= 0.004, mean -0.0002, measured on 18 re-run runs), and standalone HSI-VNc at 0 / 0.13 (hsi_eval.py, local).
Usage: e29b_full.py <un_aY13.json> <un_aY13V.json> <un2_aQ2.json> <un2_aQ2V or ''> <dir with hsi_*_hY0.json / hsi_*_hY013.json>"""
import json, glob, os, sys
import numpy as np
A = 0.05; inc = "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"
U13, V13, U0 = (json.load(open(f)) for f in sys.argv[1:4]); V0 = json.load(open(sys.argv[4])) if sys.argv[4] else {}
H = {"0": {}, "0.13": {}}
for lv, tg in (("0", "hY0"), ("0.13", "hY013")):
    for f in glob.glob(os.path.join(sys.argv[5], f"hsi_*_{tg}.json")):
        j = json.load(open(f)); H[lv][f"{j['ds']}_{j['desc']}_s{j['seed']}"] = j["variants"]["HSI-VNc"]
ks = sorted(k for k in U13 if k in U0 and k.split("_")[0] in ("cmu", "oxford", "stlucia"))
rng = np.random.default_rng(0)


def stats(rs):
    r = np.array([x["recall"] for x in rs]); s = np.array([x["seg_FAR"] for x in rs])
    return f"{r.mean():.3f} / {s.mean():.4f} / {(s > A).sum()} / {np.nanmean([x['err_mean'] for x in rs]):.1f}"


def paired(a, b):
    d = np.array([x["recall"] - y["recall"] for x, y in zip(a, b)]); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    return f"{d.mean():+.4f} [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}]"


print(f"{len(ks)} runs; cell = recall / mean segFAR / runs > alpha / navigation error (m)")
print("| set | runs | final rule, drift 0 (Entry 28) | final rule, drift 0.13 | change in recall [95% CI] | + veto, drift 0 | + veto, drift 0.13 | HSI-VNc, drift 0 | HSI-VNc, drift 0.13 | HSI-VNc change |")
print("|---|---|---|---|---|---|---|---|---|---|")
for ds in ("cmu", "oxford", "stlucia", "all"):
    kk = [k for k in ks if ds == "all" or k.startswith(ds + "_")]
    a = [U0[k]["variants"][inc] for k in kk]; b = [U13[k]["variants"][inc] for k in kk]
    va = [V0[k]["variants"][inc] for k in kk if k in V0]; vb = [V13[k]["variants"][inc] for k in kk if k in V13]
    hk = [k for k in kk if k in H["0"] and k in H["0.13"]]; ha = [H["0"][k] for k in hk]; hb = [H["0.13"][k] for k in hk]
    print(f"| {ds} | {len(kk)} | {stats(a)} | {stats(b)} | {paired(b, a)} | {stats(va) if va else '–'} | {stats(vb) if vb else '–'} | "
          f"{stats(ha) if ha else '–'} | {stats(hb) if hb else '–'} | {paired(hb, ha) if hk else '–'} |")
