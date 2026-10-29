"""Data audit for the HMM direction (DATA_AUDIT.md): retrieval accuracy, Sattler'18 pose-copy accuracy and sequence
structure of one (dataset, descriptor) dump. Usage: audit_data.py <dump_dir> <ds> <desc>  ->  results/audit_<ds>_<desc>.json"""
import sys, os, json
import numpy as np
import vprlib as V

dump, ds, desc = sys.argv[1], sys.argv[2], sys.argv[3]
ep = V.LOADERS[ds](dump, desc)
try:
    import torch
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    q, m = torch.from_numpy(ep.q.astype(np.float32)).to(dev), torch.from_numpy(ep.m.astype(np.float32)).to(dev)
    top, s1, s2 = [], [], []
    for i in range(0, len(q), 4096):
        v, ix = (q[i:i + 4096] @ m.T).topk(2, dim=1); top.append(ix[:, 0].cpu()); s1.append(v[:, 0].cpu()); s2.append(v[:, 1].cpu())
    top, s1, s2 = torch.cat(top).numpy(), torch.cat(s1).numpy(), torch.cat(s2).numpy()
except ImportError:
    S = ep.S; top = S.argmax(1); s1 = S.max(1); s2 = np.sort(S, 1)[:, -2]

dt = np.linalg.norm(ep.q_pos - ep.m_pos[top], axis=1)
da = V.rot_angle_deg(ep.q_R, ep.m_R[top]) if ep.q_R is not None else None
near = V.nearest_map_dist(ep)
tols = [1, 2, 5] if ds in ("nord", "nordw") else [5, 10, 25]


def block(sel):
    r = {"n": int(sel.sum()), "top1_sim_med": float(np.median(s1[sel])), "margin_med": float(np.median(s1[sel] - s2[sel])),
         "median_err": float(np.median(dt[sel])), "frac_has_map_within_tol0": float((near[sel] <= tols[0]).mean())}
    for t in tols: r[f"R1@{t}"] = float((dt[sel] <= t).mean())
    if da is not None:
        for a, b in [(0.25, 2), (0.5, 5), (5, 10)]: r[f"sattler_{a}m_{b}deg"] = float(((dt[sel] <= a) & (da[sel] <= b)).mean())
    return r


conds = np.asarray(ep.q_cond).astype(str)
out = {"ds": ds, "desc": desc, "n_q": len(ep.q), "n_map": len(ep.m), "dim": int(ep.q.shape[1]),
       "nearest_map_dist_pct": [float(x) for x in np.percentile(near, [50, 90, 99, 100])],
       "per_cond": {c: block(conds == c) for c in sorted(set(conds))}, "ALL": block(np.ones(len(conds), bool))}

if ds in ("rc", "cmu", "nord", "nordw"):
    qs, qk, ms, mk = V.frame_order(dump, ds, ep, desc)
    L = np.bincount(qs); Lm = np.bincount(ms)
    o = np.lexsort((qk, qs)); same = qs[o][1:] == qs[o][:-1]
    step = np.linalg.norm(np.diff(ep.q_pos[o], axis=0), axis=1)[same]
    qn = ep.q.astype(np.float32); cos = (qn[o][1:] * qn[o][:-1]).sum(1)[same]
    jump = np.linalg.norm(np.diff(ep.m_pos[top[o]], axis=0), axis=1)[same]     # top-1 map jump between consecutive queries
    out["seq"] = {"n_qseq": int(len(L)), "qlen_pct": [float(x) for x in np.percentile(L, [0, 25, 50, 75, 100])],
                  "qstep_pct": [float(x) for x in np.percentile(step, [10, 50, 90, 99])],
                  "consec_q_cos_pct": [float(x) for x in np.percentile(cos, [10, 50, 90])],
                  "n_mseq": int(len(Lm)), "mlen": [int(x) for x in sorted(Lm)[::-1][:12]],
                  "top1_jump_gt25": float((jump > 25).mean()), "top1_jump_gt5": float((jump > 5).mean())}

os.makedirs("results", exist_ok=True)
json.dump(out, open(f"results/audit_{ds}_{desc}.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "per_cond"}))
for c, r in out["per_cond"].items(): print(c, r)
