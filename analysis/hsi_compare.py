"""side-by-side comparison of several HSI variants (and idea-1 SH) on the held-out runs of a result directory.
Usage: hsi_compare.py <hsi_results_dir> <v1,v2,...> [--base <idea1_oc_dir> ...] [--all] [--md out.md]
Held-out = everything except seed 0 x {cosplace, netvlad, megaloc, dinov2} of the non-Oxford / St Lucia datasets (--all: every run).
Per dataset: mean recall / mean segFAR / runs with segFAR > 0.05 / mean nav error; pooled over runs; a run counts only if it has
every requested variant (paired)."""
import sys, os, glob, json
import numpy as np

DESIGN = {"cosplace", "netvlad", "megaloc", "dinov2"}


def load_sh(dirs):
    SH = {}
    for d in dirs:
        for f in glob.glob(os.path.join(d, "**", "oc_*.json"), recursive=True):
            j = json.load(open(f))
            for k, r in j["runs"].items():
                v = r["families"].get("CMS-CPC/H+SH+G+NGRr", {}).get("default")
                if v: SH[os.path.basename(k)[9:-4]] = v
    return SH


def main():
    a = sys.argv[1:]; rd, vs = a[0], a[1].split(",")
    bases = a[a.index("--base") + 1:] if "--base" in a else []
    bases = [b for b in bases if not b.startswith("--")]
    md = a[a.index("--md") + 1] if "--md" in a else None
    SH = load_sh(bases) if bases else {}
    rows = {}
    for f in glob.glob(os.path.join(rd, "hsi_*.json")):
        j = json.load(open(f)); ds = j["ds"]
        if "--all" not in a and int(j["seed"]) == 0 and j["desc"] in DESIGN and ds not in ("oxford", "stlucia"): continue
        if not all(v in j["variants"] for v in vs): continue
        nm = f"{ds.replace(':', '_')}_{j['desc']}_s{j['seed']}"
        V = dict(j["variants"])
        if nm in SH: V["SH"] = SH[nm]
        rows.setdefault(ds, []).append(V)
    cols = vs + (["SH"] if SH else [])
    out = ["| dataset | n | " + " | ".join(f"{v} rec / seg / >α / err" for v in cols) + " |", "|---|---|" + "---|" * len(cols)]
    allr = []
    for ds in sorted(rows):
        L = rows[ds]; allr += L; cells = []
        for v in cols:
            X = [x[v] for x in L if v in x]
            if not X: cells.append("–"); continue
            cells.append(f"{np.mean([x['recall'] for x in X]):.3f} / {np.mean([x['seg_FAR'] for x in X]):.4f} / {sum(x['seg_FAR'] > 0.05 for x in X)} / "
                         f"{np.nanmean([x.get('err_mean', np.nan) for x in X]):.1f}")
        out.append(f"| {ds} | {len(L)} | " + " | ".join(cells) + " |")
    cells = []
    for v in cols:
        X = [x[v] for x in allr if v in x]
        cells.append(f"**{np.mean([x['recall'] for x in X]):.3f}** / {np.mean([x['seg_FAR'] for x in X]):.4f} / {sum(x['seg_FAR'] > 0.05 for x in X)} / "
                     f"{np.nanmean([x.get('err_mean', np.nan) for x in X]):.1f}")
    out.append(f"| **pooled** | {len(allr)} | " + " | ".join(cells) + " |")
    txt = "\n".join(out); print(txt)
    if md: open(md, "w").write(txt + "\n")


if __name__ == "__main__":
    main()
