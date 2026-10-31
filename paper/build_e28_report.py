"""Tables of the Entry 28 report (Counterfactual Map Surgery) -> paper/e28_tables.md and paper/BAO_CAO_E28.md
(= paper/e28_text.md with the tables at {{TABLES}}); PDF: python3 automation/md2pdf.py paper/BAO_CAO_E28.md paper/BAO_CAO_E28.pdf
Usage: build_e28_report.py <dir with oc_*.json (recursive)> [--lodo05 f.md] [--lodo01 f.md] [--rho dir1:lab1,dir2:lab2]"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis"))
import e26_summary as E

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
LAB = [("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("SafeVPR", "SafeVPR'26 (nhãn)"), ("TAO26", "TAO'26 (nhãn)")]
OLD = [("certified", "Certified (null bản đồ)"), ("TAO-SC", "TAO-SC (null bản đồ)"), ("CPC-SC+CS", "CPC-SC+CS (vòng 3)"),
       ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH (vòng 5, tốt nhất cũ)")]
CMS05 = [("CMS-T", "CMS-T (tuyến, winner TAO)"), ("CMS-T/H", "CMS-T/H (tuyến, vị trí HMM)"), ("CMS-T/H+SH", "CMS-T/H+SH"),
         ("CMS-CPC/H+SH", "**CMS-CPC/H+SH (đề xuất)**"), ("CMS-U/H+SH", "CMS-U/H+SH (hợp, α/2 mỗi nhánh)"),
         ("CMS-F-PAC", "CMS-F-PAC (δ = 0.1)"), ("CMS-CPC", "CMS-CPC không dừng (chẩn đoán)")]
A01 = lambda L: [(k + "(a=0.01)", v) for k, v in L]


def load(d):
    return E.load(d)


def cell_def(v, oracle=False):
    if not len(v): return "–"
    if oracle: return f"{np.nanmean(v[:, 0]):.2f} / – / – / {np.nanmean(v[:, 4]):.1f}"
    return f"{np.nanmean(v[:, 0]):.3f} / {np.nanmean(v[:, 1]):.3f} / {np.nanmax(v[:, 1]):.3f} / {np.nanmean(v[:, 4]):.1f}"


def tab_def(T, rules, dss, title, oracle=True):
    L = [title, "", "| Luật | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|"]
    for n, lab in rules + ([("oracle", "Oracle")] if oracle else []):
        L.append(f"| {lab} | " + " | ".join(cell_def(np.array(T.get(d, {}).get(n, []), float), n == "oracle") for d in dss) + " |")
    return L + [""]


def tab_cur(C, rules, dss, title):
    L = [title, "", "| Luật | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|"]
    for n, lab in rules:
        cells = []
        for d in dss:
            v = np.array(C.get(d, {}).get(n, []), float); cells.append("–" if not len(v) else f"{v[:, 1].mean():.3f} / {v[:, 3].mean():.3f}")
        L.append(f"| {lab} | " + " | ".join(cells) + " |")
    return L + [""]


def tab_tight(T, rules, dss, title, alpha):
    """realized false-onset rate per off-map segment (H / ARL0) and mean segFAR, as multiples of alpha"""
    L = [title, "", "| Luật | α | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (2 + len(dss)) + "|"]
    for n, lab, a in rules:
        cells = []
        for d in dss:
            v = np.array(T.get(d, {}).get(n, []), float)
            cells.append("–" if not len(v) else f"{np.nanmean(v[:, 3]) / a:.2f} / {np.nanmean(v[:, 1]) / a:.2f}")
        L.append(f"| {lab} | {a:g} | " + " | ".join(cells) + " |")
    return L + [""]


def wins(T, a, b, dss, k=0, better=max):
    """number of datasets where rule a beats rule b on column k of the default table (recall: higher, error: lower)"""
    w = 0
    for d in dss:
        va, vb = np.array(T.get(d, {}).get(a, []), float), np.array(T.get(d, {}).get(b, []), float)
        if len(va) and len(vb):
            x, y = np.nanmean(va[:, k]), np.nanmean(vb[:, k]); w += (x > y) if better is max else (x < y)
    return w


def main():
    R = load(sys.argv[1]); T, C = E.defaults(R), E.curves(R)
    dss = [d for d in E.DS_ORDER if d in T]
    L = ["## 4. Kết quả\n"]
    L += tab_def(T, LAB + OLD + CMS05, dss, "### Bảng 1. Điểm mặc định, α = 0.05: recall / segFAR trung bình / segFAR run tệ nhất / sai số điều hướng (m); "
                 "10 seed (NCLT 1), 6 descriptor")
    L += tab_def(T, [("CPC-SC+CS(alpha=0.01)", "CPC-SC+CS, α = 0.01 (null bản đồ)")] + A01(CMS05), dss,
                 "### Bảng 2. Điểm mặc định, α = 0.01 (cùng định dạng)")
    L += tab_cur(C, LAB + OLD + CMS05 + A01([("CMS-CPC/H+SH", "**CMS-CPC/H+SH, α = 0.01**")]), dss,
                 "### Bảng 3. Đường cong vận hành: recall tại FL ≤ 0.01 / pAUC (FL ∈ [0, 0.05]); seed 0–2")
    L += tab_def(T, [("TAO26", "ngưỡng nhãn 3σ (TAO'26)"), ("TAO-SC", "null bản đồ (TAO-SC)"), ("CMS-T", "null phản thực (CMS-T), α = 0.05"),
                     ("CMS-T(a=0.01)", "null phản thực (CMS-T), α = 0.01")], dss,
                 "### Bảng 4. Cùng một điểm số (chi phí tuyến TAO'26), ba cách đặt ngưỡng: recall / segFAR / run tệ nhất / sai số", oracle=False)
    L += tab_tight(T, [("CPC-SC+CS", "CPC-SC+CS", 0.05), ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH", 0.05), ("TAO-SC", "TAO-SC", 0.05),
                       ("CMS-T", "CMS-T", 0.05), ("CMS-CPC/H+SH", "CMS-CPC/H+SH", 0.05),
                       ("CMS-T(a=0.01)", "CMS-T", 0.01), ("CMS-CPC/H+SH(a=0.01)", "CMS-CPC/H+SH", 0.01)], dss,
                   "### Bảng 5. Độ chặt của bảo đảm: tỷ lệ khởi phát sai mỗi đoạn off-map / α và segFAR / α (1 = dùng đúng ngân sách)", 0.05)
    # win counts of the proposed rule vs the best previous label-free rule
    P05, P01, REF = "CMS-CPC/H+SH", "CMS-CPC/H+SH(a=0.01)", "CPC-SC-T0.5+SH"
    L += ["### Bảng 6. Số dataset (trên " + str(len(dss)) + ") mà luật đề xuất hơn CPC-SC-T½+SH", "",
          "| So sánh | recall mặc định cao hơn | sai số thấp hơn | recall tại FL ≤ 0.01 cao hơn |", "|---|---|---|---|"]
    for p, lab in ((P05, "CMS-CPC/H+SH α = 0.05"), (P01, "CMS-CPC/H+SH α = 0.01"), ("CMS-T(a=0.01)", "CMS-T α = 0.01"), ("CMS-U/H+SH", "CMS-U/H+SH α = 0.05")):
        cw = sum(1 for d in dss if len(C.get(d, {}).get(p, [])) and len(C.get(d, {}).get(REF, [])) and
                 np.mean(np.array(C[d][p])[:, 1]) > np.mean(np.array(C[d][REF])[:, 1]))
        L.append(f"| {lab} | {wins(T, p, REF, dss, 0)} | {wins(T, p, REF, dss, 4, min)} | {cw} |")
    L.append("")
    for k, lab in (("--lodo05", "### Bảng 7a. Chọn luật leave-one-dataset-out (α = 0.05, tiêu chí đăng ký trước)"),
                   ("--lodo01", "### Bảng 7b. Chọn luật leave-one-dataset-out (α = 0.01)")):
        if arg(k): L += [lab, "", open(arg(k)).read(), ""]
    if arg("--rho"):
        L += ["### Bảng 8. Độ nhạy bán kính phẫu thuật ρ (seed 0, 6 descriptor): CMS-CPC/H+SH α = 0.05 recall / segFAR / run tệ nhất / sai số", "",
              "| ρ | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|"]
        for item in arg("--rho").split(","):
            dr, lab = item.split(":"); TR = E.defaults(load(dr))
            L.append(f"| {lab} | " + " | ".join(cell_def(np.array(TR.get(d, {}).get(P05, []), float)) for d in dss) + " |")
        L.append("")
    tables = "\n".join(L) + "\n"
    open(os.path.join(HERE, "e28_tables.md"), "w").write(tables)
    tx = os.path.join(HERE, "e28_text.md")
    if os.path.exists(tx): open(os.path.join(HERE, "BAO_CAO_E28.md"), "w").write(open(tx).read().replace("{{TABLES}}", tables))
    print(tables)


if __name__ == "__main__":
    main()
