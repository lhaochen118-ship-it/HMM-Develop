"""AUTOLOOP score table: per rule and dataset the mean recall, mean segFAR, runs above alpha and navigation error on a set of runs, plus the
loop SCORE = pooled recall if (V1) every dataset mean segFAR <= 0.05, (V2) <= 2 % of runs above alpha and (N1) pooled navigation error <=
the reference's (HSI-VN) + 0.5 m on the same runs; otherwise the score is reported with the failed constraints.
Inputs (any mix): owf_decide.py JSON (--decide f.json), hsi_eval-style result dirs (--hsi name=dir@variant, e.g. HSIVN=dir@HSI-VN), owf
result dirs (--owf name=dir). Usage: owf_score.py [--decide f.json] [--hsi n=dir@var ...] [--owf n=dir] [--ref HSIVN] [--md out.md]"""
import sys, os, json, glob
import numpy as np

ALPHA = 0.05
ORDER = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside", "oxford", "stlucia"]


def load(argv):
    rules = {}                                                      # rule -> {(ds, desc, seed): dict(recall, seg_FAR, err_mean)}
    def add(rule, key, m): rules.setdefault(rule, {})[key] = dict(recall=m["recall"], seg_FAR=m["seg_FAR"], err_mean=m.get("err_mean", np.nan))
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--decide":
            d = json.load(open(argv[i + 1]))
            for tag, r in d.items():
                base, _, rest = tag.rpartition("_s"); desc = base.rsplit("_", 1)[1]
                for v, m in r["variants"].items(): add("OWF:" + v, (r["ds"], desc, int(r["seed"])), m)
            i += 2; continue
        if a == "--hsi":
            n, _, dv = argv[i + 1].partition("="); dr, _, var = dv.partition("@")
            for f in glob.glob(os.path.join(dr, "**", "hsi_*.json"), recursive=True):
                j = json.load(open(f))
                if var in j.get("variants", {}): add(n, (j["ds"], j["desc"], int(j["seed"])), j["variants"][var])
            i += 2; continue
        if a == "--owf":
            n, _, dr = argv[i + 1].partition("=")
            for f in glob.glob(os.path.join(dr, "owf_*.json")):
                j = json.load(open(f)); add(n, (j["ds"], j["desc"], int(j["seed"])), j["runs"]["1.0"]["default"])
            i += 2; continue
        i += 1
    return rules


def score(rules, ref, keys=None):
    common = set.intersection(*[set(v) for v in rules.values()]) if keys is None else keys
    out = {}
    for r, R in rules.items():
        ks = [k for k in common if k in R]; dss = [d for d in ORDER if any(k[0] == d for k in ks)]
        per = {}
        for d in dss:
            kk = [k for k in ks if k[0] == d]
            per[d] = dict(n=len(kk), recall=float(np.mean([R[k]["recall"] for k in kk])), seg=float(np.mean([R[k]["seg_FAR"] for k in kk])),
                          above=int(sum(R[k]["seg_FAR"] > ALPHA for k in kk)), err=float(np.nanmean([R[k]["err_mean"] for k in kk])))
        pooled = float(np.mean([R[k]["recall"] for k in ks])); above = sum(R[k]["seg_FAR"] > ALPHA for k in ks)
        err = float(np.nanmean([R[k]["err_mean"] for k in ks]))
        out[r] = dict(per=per, n=len(ks), pooled=pooled, above=int(above), err=err)
    if ref in out:
        for r, o in out.items():
            v1 = all(p["seg"] <= ALPHA for p in o["per"].values()); v2 = o["above"] <= 0.02 * o["n"]; n1 = o["err"] <= out[ref]["err"] + 0.5
            o.update(V1=v1, V2=v2, N1=n1, valid=v1 and v2 and n1)
    return out, common


def main():
    argv = sys.argv[1:]; ref = argv[argv.index("--ref") + 1] if "--ref" in argv else "HSIVN"
    rules = load(argv); out, common = score(rules, ref)
    lines = [f"Common runs: {len(common)}", "", "| Rule | runs | pooled recall | runs > α | nav err (m) | V1 | V2 | N1 | SCORE |", "|---|---|---|---|---|---|---|---|---|"]
    for r, o in sorted(out.items(), key=lambda x: -x[1]["pooled"]):
        ok = lambda b: "yes" if b else "**no**"
        lines.append(f"| {r} | {o['n']} | {o['pooled']:.4f} | {o['above']} | {o['err']:.2f} | {ok(o.get('V1'))} | {ok(o.get('V2'))} | {ok(o.get('N1'))} | "
                     + (f"**{o['pooled']:.4f}**" if o.get("valid") else "–") + " |")
    lines += ["", "| Rule | " + " | ".join(d for d in ORDER if any(d in o["per"] for o in out.values())) + " |",
              "|---|" + "---|" * sum(1 for d in ORDER if any(d in o["per"] for o in out.values()))]
    for r, o in sorted(out.items(), key=lambda x: -x[1]["pooled"]):
        lines.append(f"| {r} | " + " | ".join((f"{o['per'][d]['recall']:.3f} / {o['per'][d]['seg']:.3f} / {o['per'][d]['above']} / {o['per'][d]['err']:.1f}"
                                             if d in o["per"] else "–") for d in ORDER if any(d in x["per"] for x in out.values())) + " |")
    txt = "\n".join(lines); print(txt)
    if "--md" in argv: open(argv[argv.index("--md") + 1], "w").write(txt + "\n")


if __name__ == "__main__":
    main()
