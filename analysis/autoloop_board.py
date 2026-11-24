"""AUTOLOOP scoreboard: every rule tried on the FRESH test groups (seeds 40-42, 43-45, 46-48, ...), with the loop Score (pooled recall when
V1: every dataset mean segFAR <= 0.05, V2: <= 2 % runs above alpha, N1: pooled navigation error <= HSI-VN + 0.5 m on the same runs).
Inputs are directories of per-run JSONs: --rule NAME=kind:dir[@variant] with kind hsi (hsi_*.json, variant), owf (owf_*.json default point) or
decide (owf_decide / owf_union JSON file, variant). Usage: autoloop_board.py --group 40-42 --rule ... [--md out.md]"""
import sys, os, json, glob
import numpy as np

ALPHA = 0.05


def load(kind, path, var, seeds):
    R = {}
    if kind == "hsi":
        for f in glob.glob(os.path.join(path, "**", "hsi_*.json"), recursive=True):
            j = json.load(open(f)); k = (j["ds"], j["desc"], int(j["seed"]))
            if k[2] in seeds and var in j.get("variants", {}): R[k] = j["variants"][var]
    elif kind == "owf":
        for f in glob.glob(os.path.join(path, "owf_*.json")):
            j = json.load(open(f)); k = (j["ds"], j["desc"], int(j["seed"]))
            if k[2] in seeds: R[k] = j["runs"]["1.0"]["default"]
    else:
        d = json.load(open(path))
        for tag, r in d.items():
            base = tag.rpartition("_s")[0]; desc = base.rsplit("_", 1)[1]; k = (r["ds"], desc, int(r["seed"]))
            if k[2] in seeds and var in r["variants"]: R[k] = r["variants"][var]
    return R


def main():
    a = sys.argv[1:]; g0, g1 = [int(x) for x in a[a.index("--group") + 1].split("-")]; seeds = set(range(g0, g1 + 1))
    rules = {}
    for i, x in enumerate(a):
        if x == "--rule":
            name, _, spec = a[i + 1].partition("="); kind, _, rest = spec.partition(":"); path, _, var = rest.partition("@")
            rules[name] = load(kind, path, var, seeds)
    common = set.intersection(*[set(v) for v in rules.values()])
    ref = rules.get("HSI-VN"); out = []
    out.append(f"Fresh group seeds {g0}-{g1}: {len(common)} common runs")
    out.append("| Rule | pooled recall | runs > α | worst dataset segFAR | nav (m) | Score |"); out.append("|---|---|---|---|---|---|")
    dss = sorted({k[0] for k in common})
    eref = float(np.mean([ref[k]["err_mean"] for k in common])) if ref else np.inf
    for n, R in sorted(rules.items(), key=lambda kv: -np.mean([kv[1][k]["recall"] for k in common])):
        rec = float(np.mean([R[k]["recall"] for k in common])); ab = int(sum(R[k]["seg_FAR"] > ALPHA for k in common))
        worst = max(float(np.mean([R[k]["seg_FAR"] for k in common if k[0] == d])) for d in dss); err = float(np.mean([R[k]["err_mean"] for k in common]))
        ok = worst <= ALPHA and ab <= 0.02 * len(common) and err <= eref + 0.5
        out.append(f"| {n} | {rec:.4f} | {ab} | {worst:.4f} | {err:.2f} | {'**%.4f**' % rec if ok else '–'} |")
    txt = "\n".join(out); print(txt)
    if "--md" in a: open(a[a.index("--md") + 1], "w").write(txt + "\n")


if __name__ == "__main__":
    main()
