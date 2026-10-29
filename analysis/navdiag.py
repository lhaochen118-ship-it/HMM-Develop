"""Diagnose CPC-HMM acceptance from nav_demo --dump arrays: where do wrong fixes and missed fixes come from?"""
import sys, numpy as np
for f in sys.argv[1:]:
    z = np.load(f, allow_pickle=True); ex = float(z["excl"]); pon = z["pon"]; acc = pon > 0.5
    inm, offm = z["inm"], z["offm"]; et, ec, eh = z["err_top"], z["err_cpc"], z["err_hmm"]
    good_top, good_c = inm & (et <= ex), inm & (ec <= ex)
    wrong = acc & (offm | (ec > ex))
    print(f"== {f.split('/')[-1]}  n {len(pon)} on {inm.mean():.2f} off {offm.mean():.2f} | top1 ok|on {good_top[inm].mean():.2f} chain ok|on {good_c[inm].mean():.2f} hmm ok|on {(eh<=ex)[inm].mean():.2f}")
    print(f"   accepted {acc.mean():.3f}  wrong {wrong.sum()} (offmap {(acc&offm).sum()}, on-map wrong place {(acc&inm&(ec>ex)).sum()}, gray {(acc&~inm&~offm&(ec>ex)).sum()})  correct {(acc&good_c).sum()}  missed-correct {(~acc&good_c).sum()}")
    w = acc & inm & (ec > ex)
    if w.any(): print(f"   on-map wrong: top1 also wrong {(et[w]>ex).mean():.2f}, agree {z['agree'][w].mean():.2f}, median err {np.median(ec[w]):.0f}")
    for cn in np.unique(z["cond"]):
        m = z["cond"] == cn
        print(f"   {cn:28s} on {inm[m].mean():.2f} top1ok {good_top[m&inm].mean() if (m&inm).any() else 0:.2f} chainok {good_c[m&inm].mean() if (m&inm).any() else 0:.2f} "
              f"acc|on {acc[m&inm].mean() if (m&inm).any() else 0:.2f} acc|off {acc[m&offm].mean() if (m&offm).any() else 0:.2f} "
              f"med p|on {np.median(z['p_frame'][m&inm]) if (m&inm).any() else 1:.3f} med p|off {np.median(z['p_frame'][m&offm]) if (m&offm).any() else 1:.3f} "
              f"pR|on {np.median(z['pR'][m&inm]) if (m&inm).any() else 1:.3f} pR|off {np.median(z['pR'][m&offm]) if (m&offm).any() else 1:.3f} agree|on {z['agree'][m&inm].mean() if (m&inm).any() else 0:.2f}")
