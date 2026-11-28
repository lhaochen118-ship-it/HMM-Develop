#!/usr/bin/env python3
"""Summary table of the NEW datasets (research/DATASETS.md B/C) from the registry (latest ok E18 run per cell) and the
A32b post-hoc fallback (research/fallback/final.json). Output: research/reports/NEW_DATASETS_TABLE.md"""
import json, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW = [("oxford", "Oxford RobotCar (7 conditions vs overcast map)"), ("boreas:8", "Boreas (8 seasonal traversals)"),
       ("nclt", "NCLT (8 campus sessions, off-map parts)"), ("stlucia", "St Lucia (5 times of day)"),
       ("brisbane", "Brisbane-Event-VPR (5 times of day)"), ("qut-gp", "QUT Gardens Point (day/night, lateral)"),
       ("qut-sb", "QUT SouthBank bicycle"), ("kitti", "KITTI Odometry loops (revisit)")]
DESCS = ["netvlad", "cosplace", "mixvpr", "dinov2", "salad", "megaloc"]
reg = [json.loads(l) for l in open(os.path.join(ROOT, "research", "registry", "runs.jsonl"))]
latest = {}
for r in reg:
    if r.get("experiment_id") == "E18" and r["run_id"].split("_")[1] == "E18" and r.get("status") == "ok":
        latest[(r["dataset"], r["descriptor"])] = r
final = json.load(open(os.path.join(ROOT, "research", "fallback", "final.json")))
rows = ["| Dataset | Descriptor | Single | SeqSLAM (causal) | HMM fixed kernel | **HMM (ours, calib-selected + fallback)** | Δ vs SeqSLAM | Δ vs single | Note | run_id |",
        "|---|---|---|---|---|---|---|---|---|---|"]
stat = collections.Counter()
for ds, name in NEW:
    for d in DESCS:
        r = latest.get((ds, d))
        if not r: continue
        m = r["metrics"]; f = final.get(f"{ds}|{d}|{r.get('seed', 0)}", final.get(f"{ds}|{d}|1", {}))
        s, q, hf = m["single"]["R@1"], m["seqslam"]["R@1"], m["hmm_fixed"]["R@1"]
        o = f.get("R@1", m.get("OURS_leak", m["OURS_devselected"])["R@1"]); base = f.get("base", "")
        note = "saturated" if s >= 0.99 else ("fallback→single" if base.startswith("degenerate") else "")
        dq, ds_ = o - q, o - s
        if s < 0.99:
            stat["cells"] += 1; stat["win_vs_seqslam"] += dq > 0.005; stat["loss_vs_seqslam"] += dq < -0.005
            stat["win_vs_single"] += ds_ > 0.005; stat["loss_vs_single"] += ds_ < -0.005
        rows.append(f"| {name} | {d} | {s:.3f} | {q:.3f} | {hf:.3f} | **{o:.3f}** | {dq:+.3f} | {ds_:+.3f} | {note} | {r['run_id']} |")
out = os.path.join(ROOT, "research", "reports", "NEW_DATASETS_TABLE.md")
open(out, "w").write("# New datasets — R@1 on test sequences (PROTOCOL v1, hyper-parameters on calibration only)\n\n"
                     + "\n".join(rows) + "\n\n" + f"Non-saturated cells: {stat['cells']}; vs tuned causal SeqSLAM: {stat['win_vs_seqslam']} wins / "
                     f"{stat['cells'] - stat['win_vs_seqslam'] - stat['loss_vs_seqslam']} ties (±0.005) / {stat['loss_vs_seqslam']} losses; "
                     f"vs single image: {stat['win_vs_single']} / {stat['cells'] - stat['win_vs_single'] - stat['loss_vs_single']} / {stat['loss_vs_single']}.\n")
print(open(out).read()[-600:])
