"""Condensed main table for REPORT_v1 (generated from the registry; replaces text between <!--MAIN_TABLE--> markers)."""
import json, os, re
ROOT = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "registry", "runs.jsonl"))]
def res(ds, d, seed=0):
    c = [r for r in rows if r.get("experiment_id") == "E18" and r.get("dataset") == ds and r.get("descriptor") == d and r.get("seed") == seed]
    return json.load(open(os.path.join(ROOT, "..", c[-1]["artifacts"], "metrics.json")))["results"] if c else None
SETS = [("Nordland đồng bộ", "nord", 0), ("Nordland time-warp s1", "nord-tw", 1), ("Extended CMU (11 slice)", "cmu", 0),
        ("RobotCar Seasons v2", "rc", 0), ("4Seasons office_loop (thật)", "4s", 0), ("4Seasons countryside (thật)", "4s2", 0),
        ("4Seasons old_town (thật)", "4s3", 0), ("Nordland video-rate (k01)", "nordseg1", 0), ("Nordland video-rate time-warp", "nordseg1-tw", 1)]
DESC = ["netvlad", "cosplace", "salad", "megaloc"]
out = ["| Dataset (NetVLAD / CosPlace / SALAD / MegaLoc) | Single | SeqSLAM (tuned) | HMM kernel cố định | **IA-HMM (dev-sel.)** |", "|---|---|---|---|---|"]
W = {"seq": [0, 0, 0], "fix": [0, 0, 0]}; n = 0; geq = 0
for name, ds, seed in SETS:
    cells = {k: [] for k in ("single", "seqslam", "hmm_fixed", "OURS_devselected")}
    for d in DESC:
        r = res(ds, d, seed)
        for k in cells: cells[k].append("—" if r is None or k not in r else f"{r[k]['R@1']:.3f}")
        if r:
            o, s, q, f = r["OURS_devselected"]["R@1"], r["single"]["R@1"], r["seqslam"]["R@1"], r["hmm_fixed"]["R@1"]
            n += 1; geq += o >= s
            for key, b in (("seq", q), ("fix", f)):
                W[key][0 if o > b + 0.005 else (2 if o < b - 0.005 else 1)] += 1
    if all(c == "—" for c in cells["single"]): continue
    out.append(f"| {name} | " + " | ".join(" / ".join(cells[k]) for k in ("single", "seqslam", "hmm_fixed")) + " | **" + " / ".join(cells["OURS_devselected"]) + "** |")
summary = (f"Tổng hợp {n} ô (seed 0/1 như trong bảng): IA-HMM ≥ ảnh đơn {geq}/{n}; so với SeqSLAM tuned {W['seq'][0]} thắng / {W['seq'][1]} hòa "
           f"(±0.5 điểm) / {W['seq'][2]} thua; so với HMM kernel cố định {W['fix'][0]} / {W['fix'][1]} / {W['fix'][2]}.")
block = summary + "\n\n" + "\n".join(out)
p = os.path.join(ROOT, "reports", "REPORT_v1.md"); s = open(p).read()
s = re.sub(r"<!--MAIN_TABLE-->.*?<!--/MAIN_TABLE-->", "<!--MAIN_TABLE-->\n" + block + "\n<!--/MAIN_TABLE-->", s, flags=re.S)
open(p, "w").write(s); print(block)
