"""Tables for the report answering "is the method only more conservative?" (RESEARCH_LOG Entry 25).
Reads oc_curves.py outputs (curves + default points of every rule, --variants --cs-sens) and oc_matched.py outputs.
Usage: build_oc_report.py <oc_dir> <matched_dir> [--drop10 <oc_dir>] [--drop50 <oc_dir>] -> paper/oc_tables.md"""
import sys, os, json, glob
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
from oc_summary import recall_at, pauc

ORDER = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
NAME = {"boreas": "Boreas", "nclt": "NCLT", "cmu": "CMU", "nord": "Nordland", "4s:office_loop": "4S office",
        "4s:old_town": "4S old town", "4s:countryside": "4S countryside"}
RULES = [("Xu21", "Xu'21 HMM off-map (nhãn)"), ("Claxton24", "Claxton'24 MLP (nhãn)"), ("SafeVPR", "SafeVPR (nhãn, Boreas)"),
         ("max-sim", "Ngưỡng max-sim (nhãn)"), ("certified", "Certified"), ("TCEmin", "CPC-HMM +TCEmin (cũ)"),
         ("CPC-HMM", "CPC-HMM (không TCE)"), ("CPC-HMM+CS", "CPC-HMM +CS"), ("CPC-SC+CS", "**CPC-SC+CS (đề xuất)**")]


def load(d):
    R = {}
    for f in sorted(glob.glob(os.path.join(d, "oc_*.json"))):
        x = json.load(open(f))
        for run in x["runs"].values(): R.setdefault(x["ds"], []).append(run)
    return R


def mean_def(runs, fam, key):
    v = [r["families"][fam]["default"][key] for r in runs if fam in r["families"] and "default" in r["families"][fam]]
    return float(np.mean(v)) if v else float("nan")


def table_defaults(R, title):
    L = [f"### {title}\n", "Ô: recall / segFAR / sai số điều hướng trung bình (m); trung bình 6 descriptor × 3 seed (NCLT: × 1).\n",
         "| Luật | " + " | ".join(NAME[d] for d in ORDER if d in R) + " |", "|---" * (1 + sum(d in R for d in ORDER)) + "|"]
    for fam, lab in RULES + [("oracle", "Oracle")]:
        cells = []
        for d in ORDER:
            if d not in R: continue
            if fam == "oracle":
                cells.append(f"{np.mean([r['oracle']['recall'] for r in R[d]]):.2f} / – / {np.mean([r['oracle']['err_mean'] for r in R[d]]):.1f}")
            else:
                rc = mean_def(R[d], fam, "recall")
                cells.append("–" if np.isnan(rc) else f"{rc:.2f} / {mean_def(R[d], fam, 'seg_FAR'):.3f} / {mean_def(R[d], fam, 'err_mean'):.1f}")
        L.append(f"| {lab} | " + " | ".join(cells) + " |")
    return L


def table_matched_fl(R):
    L = ["### Recall ở cùng mức báo sai (đường cong vận hành)\n",
         "Ô: recall khi FL ≤ 0.01 / recall khi segFAR ≤ 0.025 / pAUC (recall trung bình trên FL ∈ [0, 0.05]). Mỗi luật quét ngưỡng "
         "của chính nó; nhãn chỉ dùng để đánh giá.\n",
         "| Luật | " + " | ".join(NAME[d] for d in ORDER if d in R) + " |", "|---" * (1 + sum(d in R for d in ORDER)) + "|"]
    best = {}
    for d in ORDER:
        if d not in R: continue
        best[d] = max(np.mean([recall_at(r["families"][f]["curve"], "FL", 0.01) for r in R[d]]) for f, _ in RULES
                      if all(f in r["families"] and r["families"][f]["curve"] for r in R[d]))
    for fam, lab in RULES:
        cells = []
        for d in ORDER:
            if d not in R: continue
            rs = [r for r in R[d] if fam in r["families"] and r["families"][fam]["curve"]]
            if len(rs) < len(R[d]): cells.append("–"); continue
            a = np.mean([recall_at(r["families"][fam]["curve"], "FL", 0.01) for r in rs])
            b = np.mean([recall_at(r["families"][fam]["curve"], "seg_FAR", 0.025) for r in rs])
            c = np.mean([pauc(r["families"][fam]["curve"]) for r in rs])
            cells.append(("**%.3f**" % a if abs(a - best[d]) < 1e-9 else "%.3f" % a) + f" / {b:.3f} / {c:.3f}")
        L.append(f"| {lab} | " + " | ".join(cells) + " |")
    return L


def table_paired(mdir, ours="CPC-SC+CS", bases=("Xu21", "Claxton24", "certified", "TCEmin")):
    rows = {}
    for f in sorted(glob.glob(os.path.join(mdir, "matched_*.json"))):
        x = json.load(open(f))
        for run in x["runs"].values():
            for bn in bases:
                r = run["matched"].get(ours, {}).get(bn); bp = run["defaults"].get(bn)
                if r is None or bp is None: continue
                t = rows.setdefault((x["ds"], bn), {"recall@FL": [], "err_mean@FL": [], "FL@recall": [], "err_mean@recall": []})
                for k in t: t[k].append(r[k] - bp[k.split("@")[0]] if k in r else np.nan)
    L = [f"### {ours} đặt tại đúng điểm vận hành mặc định của từng baseline (so khớp chính xác)\n",
         "Ô: trung vị chênh lệch theo cặp (đề xuất − baseline) và số run thắng / số run so được. Cột 1–2: cùng FL với baseline; "
         "cột 3–4: cùng recall với baseline (\"không đạt\" = đường cong của đề xuất không với tới recall đó). Sai số: Kalman chạy "
         "thật tại ngưỡng khớp.\n",
         "| Dataset | Baseline | Δrecall @ FL của baseline | Δsai số @ FL của baseline | ΔFL @ recall của baseline | Δsai số @ recall của baseline |",
         "|---|---|---|---|---|---|"]
    for d in ORDER:
        for bn in bases:
            t = rows.get((d, bn))
            if not t: continue
            cells = []
            for k, v in t.items():
                v = np.array(v, float); ok = np.isfinite(v)
                if not ok.any(): cells.append("không đạt"); continue
                w = int((v[ok] > 0).sum() if k == "recall@FL" else (v[ok] < 0).sum())
                cells.append((f"{np.median(v[ok]):+.1f}" if "err" in k else f"{np.median(v[ok]):+.3f}") + f" ({w}/{ok.sum()})")
            L.append(f"| {NAME[d]} | {bn} | " + " | ".join(cells) + " |")
    return L


def table_sens(R):
    fams = ["CPC-SC+CS", "CPC-HMM+CS", "CPC-HMM+CS(span2,thr1)", "CPC-HMM+CS(span4,thr1)", "CPC-HMM+CS(span3,thr0.75)",
            "CPC-HMM+CS(span3,thr1.25)", "CPC-SC+CS(alpha=0.01)", "CPC-SC+CS(alpha=0.1)"]
    L = ["### Độ nhạy một-tham-số-một-lần (điểm mặc định)\n", "Ô: recall / segFAR / sai số (m).\n",
         "| Biến thể | " + " | ".join(NAME[d] for d in ORDER if d in R) + " |", "|---" * (1 + sum(d in R for d in ORDER)) + "|"]
    for fam in fams:
        cells = []
        for d in ORDER:
            if d not in R: continue
            rc = mean_def(R[d], fam, "recall")
            cells.append("–" if np.isnan(rc) else f"{rc:.2f} / {mean_def(R[d], fam, 'seg_FAR'):.3f} / {mean_def(R[d], fam, 'err_mean'):.1f}")
        L.append(f"| {fam} | " + " | ".join(cells) + " |")
    return L


def main():
    R = load(sys.argv[1]); L = []
    L += table_defaults(R, "Điểm vận hành mặc định (bản đồ khuyết 30 % block)"); L.append("")
    L += table_matched_fl(R); L.append("")
    L += table_paired(sys.argv[2]); L.append("")
    L += table_sens(R); L.append("")
    for tag in ("--drop10", "--drop50"):
        if tag in sys.argv:
            Rd = load(sys.argv[sys.argv.index(tag) + 1])
            L += table_defaults(Rd, f"Điểm vận hành mặc định, bản đồ khuyết {tag[-2:]} % block"); L.append("")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oc_tables.md")
    open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    main()
