#!/usr/bin/env python3
"""A34 tables from the registry: ONLINE (causal) vs OFFLINE (centred baselines, HMM fixed-lag smoothing with the same
look-ahead h, and lag 20). Latest ok E37 run per (dataset, descriptor); JIST / SeqVLAD centred rows from B10c / B11c.
Output: research/reports/OFFLINE_TABLE.md"""
import json, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
reg = [json.loads(l) for l in open(os.path.join(ROOT, "research", "registry", "runs.jsonl"))]
e37, bseq = {}, {}
for r in reg:
    if r.get("status") != "ok": continue
    if r.get("experiment_id") == "E37": e37[(r["dataset"], r["descriptor"])] = r
    if r["run_id"].split("_")[1] in ("B10c", "B11c"): bseq[(r["dataset"], r["descriptor"])] = r
ORDER = ["nord", "nordseg1", "rc", "cmu", "4s", "4s2", "4s3", "msls-cph", "msls-sf", "oxford", "boreas:8", "nclt", "stlucia",
         "brisbane", "qut-gp", "qut-sb", "kitti"]
rows = ["| Dataset | Desc | Single | SeqSLAM causal | HMM filter (causal) | SeqSLAM centred (L) | **HMM lag h** (same future) | HMM lag 20 | Δ lag-h vs centred | run_id |",
        "|---|---|---|---|---|---|---|---|---|---|"]
c = collections.Counter()
for ds in ORDER:
    for (d_, desc), r in sorted(e37.items()):
        if d_ != ds: continue
        m = r["metrics"]; dlt = m["hmm_lag_h"] - m["seqslam_centred"]
        sat = m["single"] >= 0.99
        if not sat:
            c["n"] += 1; c["win"] += dlt > 0.005; c["loss"] += dlt < -0.005
            c["online_win"] += (m["hmm_filter"] - m["seqslam_causal"]) > 0.005; c["online_loss"] += (m["hmm_filter"] - m["seqslam_causal"]) < -0.005
        rows.append(f"| {ds} | {desc} | {m['single']:.3f} | {m['seqslam_causal']:.3f} | {m['hmm_filter']:.3f} | {m['seqslam_centred']:.3f} ({m['seqslam_centred_L']}) | "
                    f"**{m['hmm_lag_h']:.3f}** (h={m['lag_h']}) | {m['hmm_lag_20']:.3f} | {dlt:+.3f}{' sat.' if sat else ''} | {r['run_id']} |")
seqrows = ["| Dataset | Learned seq. model | single (its frame desc.) | its sequence descriptor, CENTRED (L,k) | its seq. descriptor + HMM | run_id |", "|---|---|---|---|---|---|"]
for (ds, desc), r in sorted(bseq.items()):
    m = r["metrics"]; k = "JIST" if desc == "jist" else "SeqVLAD"
    seqrows.append(f"| {ds} | {k} | {m.get('single_' + desc, {}).get('R@1', float('nan')):.3f} | {m.get(k + '_seq', {}).get('R@1', float('nan')):.3f} | "
                   f"{m.get(k + '_seq+HMM', {}).get('R@1', float('nan')):.3f} | {r['run_id']} |")
txt = ("# Online vs offline comparison (A34) — R@1, test sequences\n\nOfficial SeqSLAM / SeqMatch / JIST / SeqVLAD use CENTRED windows "
       "(h = L//2 future frames). Offline columns give the HMM exactly that look-ahead (fixed-lag smoothing, lag h; no new "
       "hyper-parameters). Positives as in E18 (frame level).\n\n" + "\n".join(rows) +
       f"\n\nNon-saturated cells: {c['n']}. OFFLINE HMM lag-h vs centred SeqSLAM: {c['win']} wins / {c['n'] - c['win'] - c['loss']} ties / {c['loss']} losses. "
       f"ONLINE HMM filter vs causal SeqSLAM: {c['online_win']} / {c['n'] - c['online_win'] - c['online_loss']} / {c['online_loss']}.\n\n"
       "## Learned sequence descriptors with the official centred protocol\n\n" + "\n".join(seqrows) + "\n")
open(os.path.join(ROOT, "research", "reports", "OFFLINE_TABLE.md"), "w").write(txt)
print(txt[-900:])
