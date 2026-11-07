"""End-to-end causality test of the HSI decision branch (2026-11-07, second audit).

A rule is causal iff its report at deployment rank r depends only on the data of ranks <= r. The test cuts the deployment at rank R,
replaces every later frame's data (place chain est_c, odometry o_q, appearance features) by garbage, re-runs the online rule, and
counts the frames of rank <= R whose report changed. Expected: HSI-VN (historical code) can change (global drift / s0, early label
availability); HSI-VNc must change nowhere.
Usage: test_hsi_causality.py <hybrid navcache .npz> [cut fractions, default 0.3,0.6]"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import hsi, hsi_eval


def perturb(z, R, seed=0):
    z = dict(z); seqs = hsi.deployment_seqs(z); order = np.concatenate(seqs); rank = np.empty(len(order), np.int64)
    rank[order] = np.arange(len(order)); fut = rank > R; rng = np.random.default_rng(seed)
    est = z["est_c"].copy(); est[fut] = rng.integers(0, len(z["MP"]), fut.sum()); z["est_c"] = est
    o = z["o_q"].astype(float).copy(); o[fut] += rng.normal(0, 50.0, (fut.sum(), o.shape[1])); z["o_q"] = o
    for k in ("srt10", "Smean", "Sstd", "lo_c", "conf_c", "p_frame", "pR", "maxsim", "top"):
        if k in z:
            a = np.array(z[k]).copy()
            if k == "top": a[fut] = rng.integers(0, len(z["MP"]), fut.sum())
            else: a[fut] = rng.permutation(a[fut]) if a.ndim == 1 else rng.permutation(a[fut], axis=0)
            z[k] = a
    return z, rank


def main():
    f = sys.argv[1]; cuts = [float(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "0.3,0.6").split(",")]
    z0 = dict(np.load(f, allow_pickle=True)); name = os.path.basename(f)[9:-4]; n = len(z0["est_c"]); ok = True
    for v in ("HSI-VN", "HSI-VNc"):
        a0 = hsi.online_v2(z0, name, **hsi_eval.VARIANTS[v])["acc"]
        for c in cuts:
            R = int(c * n); z1, rank = perturb(z0, R)
            a1 = hsi.online_v2(z1, name, **hsi_eval.VARIANTS[v])["acc"]
            past = rank <= R; nd = int((a0[past] != a1[past]).sum())
            print(f"{v:8s} cut {c:.1f} (R={R}): reports changed in the past: {nd} of {int(past.sum())} frames"
                  f" ({int(a0[past].sum())} reports)", flush=True)
            if v == "HSI-VNc" and nd: ok = False
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
