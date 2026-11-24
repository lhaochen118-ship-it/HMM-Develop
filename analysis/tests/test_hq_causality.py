"""Causality test of the hindsight-calibrated absolute evidence (Entry 23 / audit 2026-11-07).
Perturb the FUTURE of one session (its frame statistics from frame T on, and its first-pass samples from frame T on); the unmapped-cell
log-LR of every frame before T must not change. Run: python3 tests/test_hq_causality.py"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.argv = sys.argv[:1]
import owf


def synth(seed=0, nseq=4, n=900):
    rng = np.random.default_rng(seed); seqs = []; off = 0
    cm = rng.normal(0.4, 0.1, nseq * n); st, sa, tt = [], [], []
    for k in range(nseq):
        idx = np.arange(off, off + n); seqs.append(idx); off += n
        t = np.sort(rng.choice(n, 600, replace=False))
        st.append(rng.normal(0.55, 0.08, 600)); sa.append(rng.normal(0.35, 0.07, 600)); tt.append(t)
    return seqs, cm, st, sa, tt


def perturb(seqs, cm, st, sa, tt, k, T, seed=1):
    rng = np.random.default_rng(seed); cm2 = cm.copy(); idx = seqs[k]
    cm2[idx[T:]] = rng.normal(0.9, 0.3, len(idx) - T)                      # future frame statistics change
    keep = tt[k] < T                                                         # future samples change
    st2 = list(st); sa2 = list(sa); tt2 = list(tt)
    st2[k] = np.r_[st[k][keep], rng.normal(0.2, 0.05, (~keep).sum())]; sa2[k] = np.r_[sa[k][keep], rng.normal(0.6, 0.05, (~keep).sum())]
    tt2[k] = np.r_[tt[k][keep], tt[k][~keep]]
    return cm2, st2, sa2, tt2


def check(fn, name, k=2, T=437):
    seqs, cm, st, sa, tt = synth()
    a, _ = fn(seqs, cm, st, sa, tt)
    cm2, st2, sa2, tt2 = perturb(seqs, cm, st, sa, tt, k, T)
    b, _ = fn(seqs, cm2, st2, sa2, tt2)
    past = seqs[k][:T]; d = float(np.abs(a[past] - b[past]).max())
    print(f"{name}: max |change| of log-LR before the perturbation = {d:.3g}")
    return d


if __name__ == "__main__":
    d_old = check(lambda *a: owf.hindsight_lu_causal(*a), "hsq  (as tested in Entries 23-26)")
    d_new = check(lambda *a: owf.hindsight_lu_causal2(*a), "hsq2 (audit fix)")
    d_str = check(lambda *a: owf.hindsight_lu_causal2(*a, strict=True), "hsq2s (audit fix, earlier sessions only)")
    assert d_new == 0.0 and d_str == 0.0, "hsq2 must be causal"
    print("PASS: hsq2 / hsq2s are causal within a session" + ("; hsq leaks (expected)" if d_old > 0 else "; hsq did not leak on this case"))
