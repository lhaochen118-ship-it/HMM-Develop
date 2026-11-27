"""T6.7 — Holm-Bonferroni over the family of E18 cells, using the stored paired-block-bootstrap CIs.
p-values from a normal approximation of the bootstrap distribution: SE=(hi-lo)/3.92, z=est/SE (two-sided).
Contrasts: (a) HMM fixed kernel vs single image, (b) IA-HMM (dev-selected) vs fixed-kernel HMM, (c) best IA variant
LV+ME vs fixed (component test). Output: research/reports/HOLM.md"""
import json, os, math
ROOT = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "registry", "runs.jsonl"))]
cells = {}
for r in rows:
    if r.get("experiment_id") == "E18" and r.get("status") == "ok": cells[(r["dataset"], r["descriptor"], r.get("seed"))] = r
def p_from_ci(est, lo, hi):
    se = max((hi - lo) / 3.92, 1e-9); z = est / se
    return math.erfc(abs(z) / math.sqrt(2))
fam = {"fixed_vs_single": [], "devsel_vs_fixed": [], "LVME_vs_fixed": []}
for k, r in sorted(cells.items()):
    m = json.load(open(os.path.join(ROOT, "..", r["artifacts"], "metrics.json")))["results"]
    lo, hi = m["single"]["dR1_vs_fixed_CI"]; est = m["hmm_fixed"]["R@1"] - m["single"]["R@1"]
    fam["fixed_vs_single"].append((k, est, p_from_ci(est, -hi, -lo)))
    for key, name in (("OURS_devselected", "devsel_vs_fixed"), ("LV+ME", "LVME_vs_fixed")):
        lo, hi = m[key]["dR1_vs_fixed_CI"]; est = m[key]["R@1"] - m["hmm_fixed"]["R@1"]
        if not (lo == 0 and hi == 0): fam[name].append((k, est, p_from_ci(est, lo, hi)))
out = ["# Holm–Bonferroni over E18 cells (α = 0.05; normal approx. of paired sequence-bootstrap CIs)\n"]
for name, L in fam.items():
    L = sorted(L, key=lambda x: x[2]); n = len(L); sig = []; stop = False
    for i, (k, est, p) in enumerate(L):
        if not stop and p <= 0.05 / (n - i): sig.append((k, est, p))
        else: stop = True
    pos = sum(1 for _, e, _ in sig if e > 0); neg = sum(1 for _, e, _ in sig if e < 0)
    out.append(f"## {name}: {n} tests · Holm-significant: {len(sig)} (improvements {pos}, degradations {neg})\n")
    out.append("| cell | Δ R@1 | p (approx) | Holm-significant |\n|---|---|---|---|")
    sset = {s[0] for s in sig}
    for k, est, p in sorted(L, key=lambda x: str(x[0])):
        out.append(f"| {k[0]} {k[1]} s{k[2]} | {est:+.3f} | {p:.1e} | {'yes' if k in sset else ''} |")
    out.append("")
open(os.path.join(ROOT, "reports", "HOLM.md"), "w").write("\n".join(out)); print("\n".join(l for l in out if l.startswith("##")))
