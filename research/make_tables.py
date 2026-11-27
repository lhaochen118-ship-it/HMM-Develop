"""Generate result tables (markdown) from research/runs/*/metrics.json via the registry (no hand-typed numbers)."""
import json, os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "registry", "runs.jsonl"))]
def latest(exp, ds, desc, seed=None):
    c = [r for r in rows if r.get("experiment_id") == exp and r.get("dataset") == ds and r.get("descriptor") == desc
         and (seed is None or r.get("seed") == seed) and r.get("status") == "ok"]
    return c[-1] if c else None
METHODS = ["single", "seqslam", "hmm_fixed", "LV", "LV+ME", "LV+ME+IA", "OURS_devselected", "ORACLE_motion"]
NAMES = {"single": "Single", "seqslam": "SeqSLAM†", "hmm_fixed": "HMM (fixed kernel, β*)", "LV": "+latent vel.",
         "LV+ME": "+change emission", "LV+ME+IA": "+IA weighting", "OURS_devselected": "**IA-HMM (dev-selected)**",
         "ORACLE_motion": "oracle motion (diag.)"}
out = []
for metric in ("R@1", "NLL"):
    out.append(f"\n### {metric} (test sequences; ↑ better for R@1, ↓ for NLL)\n")
    hdr = "| Dataset | Descriptor | " + " | ".join(NAMES[m] for m in METHODS) + " | run |"
    out += [hdr, "|" + "---|" * (len(METHODS) + 3)]
    for ds, seed in [("nord", 0), ("nord-tw", 1), ("nord-tw", 2), ("nord-tw", 3), ("nordseg1", 0), ("nordseg1-tw", 1), ("cmu", 0), ("rc", 0), ("4s", 0)]:
        for desc in ("netvlad", "cosplace", "salad", "megaloc"):
            r = latest("E18", ds, desc, seed)
            if r is None: continue
            m = json.load(open(os.path.join(ROOT, "..", r["artifacts"], "metrics.json")))["results"]
            cells = []
            for k in METHODS:
                if k not in m: cells.append("–"); continue
                v = m[k][metric]; cells.append(f"{v:.3f}" + (f" ({m[k].get('picked')})" if k == "OURS_devselected" and metric == "R@1" else ""))
            out.append(f"| {ds}{'' if seed in (0, None) else ' s'+str(seed)} | {desc} | " + " | ".join(cells) + f" | {r['run_id']} |")
print("\n".join(out))
