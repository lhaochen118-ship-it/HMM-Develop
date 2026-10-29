#!/usr/bin/env python3
"""Offline variants of the CPC-HMM presence chain on nav_demo --dump arrays (navframes_*.npz): FL / recall / wrong fixes.
Usage: presence_variants.py <npz> [...]"""
import numpy as np, sys
def chain(ll, sid, k, p=0.01):
    pon=np.zeros(len(ll))
    for s in np.unique(sid):
        i=np.where(sid==s)[0]; i=i[np.argsort(k[i])]; pr=0.5
        for t in i:
            pr=(1-p)*pr+p*(1-pr); lo=np.log(pr/(1-pr))+ll[t]; pr=1/(1+np.exp(-np.clip(lo,-50,50))); pon[t]=pr
    return pon
for f in sys.argv[1:]:
    z=np.load(f,allow_pickle=True); off,inm=z["offm"],z["inm"]; ok=inm&(z["err_cpc"]<=z["excl"])
    etop=np.where(z["agree"],np.exp(z["lam"]),np.exp(z["loga"])); eR=z["e_R"]; H=10
    V={"full ½(top+R^1/H)":0.5*(etop+eR**(1/H)), "top only":etop, "½(top+R^1/H) R capped p>=.05": 0.5*(etop+np.minimum(eR,np.max(eR[z['pR']>=0.05]) if (z['pR']>=0.05).any() else eR)**(1/H)),
       "top·R^1/H product?":etop*eR**(1/H), "½(top+R^(1/2H))":0.5*(etop+eR**(1/(2*H)))}
    print(f.split("navframes_")[1])
    for n,e in V.items():
        acc=chain(np.log(np.maximum(e,1e-300)),z["q_sid"],z["q_k"])>0.5
        wrong=acc&(off|(z["err_cpc"]>z["excl"]))
        print(f"   {n:32s} FL {acc[off].mean():.3f}  recall {(acc&ok)[inm].mean():.3f}  wrong {wrong.sum()}")
