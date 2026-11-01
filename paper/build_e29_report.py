"""Tables of the Entry 29 report (navigation-risk gate, exact counterfactual, audit fixes) -> paper/e29_tables.md and
paper/BAO_CAO_E29.md (= paper/e29_text.md with the tables at {{TABLES}}); PDF via automation/md2pdf.py.
Usage: build_e29_report.py <eval dir (E29)> [--e28 <eval dir E28, truncated counterfactual>] [--holes <dir with d10, d50>]
       [--lodo05 f] [--lodo01 f] [--paired f] [--diag f]"""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis")); sys.path.insert(0, HERE)
import e26_summary as E
from build_e28_report import tab_def, tab_cur, tab_tight, wins

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
LAB = [("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("SafeVPR", "SafeVPR'26 (nhãn)"), ("TAO26", "TAO'26 (nhãn)")]
OLD = [("CPC-SC+CS", "CPC-SC+CS (vòng 3)"), ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH (vòng 5)")]
NEW = [("CMS-CPC/H+SH", "CMS-CPC/H+SH (vòng 6)"), ("CMS-CPC/H+SH+NGR", "**CMS-CPC/H+SH+NGR**"), ("CMS-CPC/H+SH+G+NGR", "CMS-CPC/H+SH+G+NGR"),
       ("CMS-CPCW/H+SH", "CMS-CPCW/H+SH (khởi phát cửa sổ)"), ("CMS-CPCW/H+SH+NGR", "**CMS-CPCW/H+SH+NGR**"), ("CMS-T/H+SH+NGR", "CMS-T/H+SH+NGR"),
       ("CMS-CPC/H+SH+NG", "ablation: +NG (không mở khoá)"), ("CMS-CPC/H+SH+DRG", "ablation: +DRG (cổng dead-reckoning cổ điển)"),
       ("CPC-SC-T0.5+SH+NGR", "ablation: CPC-SC-T½+SH+NGR (cổng trên luật cũ)"), ("CMS-CPC/H+SH[loco]", "CMS-CPC/H+SH [nhân quả]"),
       ("CMS-CPCW/H+SH[loco]", "CMS-CPCW/H+SH [nhân quả]")]
A01 = lambda L: [(k.replace("+NGR", "(a=0.01)+NGR").replace("+NG", "(a=0.01)+NG") if "+NG" in k else (k.replace("[loco]", "[loco](a=0.01)") if "[loco]" in k else k + "(a=0.01)"), v) for k, v in L]


def a01(L):
    out = []
    for k, v in L:
        if k.endswith("+DRG"): k2 = k[:-4] + "(a=0.01)+DRG"
        elif k.endswith("+NGR"): k2 = k[:-4] + "(a=0.01)+NGR"
        elif k.endswith("+NG"): k2 = k[:-3] + "(a=0.01)+NG"
        elif k.endswith("[loco]"): k2 = k + "(a=0.01)"
        else: k2 = k + "(a=0.01)"
        out.append((k2, v))
    return out


def main():
    R = E.load(sys.argv[1]); T, C = E.defaults(R), E.curves(R); dss = [d for d in E.DS_ORDER if d in T]
    L = ["## 4. Kết quả (null phản thực chính xác; 366 run)\n"]
    L += tab_def(T, LAB + OLD + NEW, dss, "### Bảng 1. Điểm mặc định, α = 0.05: recall / segFAR trung bình / segFAR run tệ nhất / sai số điều hướng (m)")
    L += tab_def(T, [("CPC-SC+CS(alpha=0.01)", "CPC-SC+CS, α = 0.01 (null bản đồ)")] + a01([x for x in NEW if not x[0].startswith("CPC-SC-T0.5")]), dss,
                 "### Bảng 2. Điểm mặc định, α = 0.01")
    L += tab_cur(C, LAB + OLD + [x for x in NEW if "[" not in x[0] and "+NG" not in x[0] and "DRG" not in x[0]] +
                 [("CMS-CPC/H+SH+NGR", "CMS-CPC/H+SH+NGR"), ("CMS-CPCW/H+SH+NGR", "CMS-CPCW/H+SH+NGR")], dss,
                 "### Bảng 3. Đường cong: recall tại FL ≤ 0.01 / pAUC (seed 0–2; luật có cổng: điểm số bị che ở các frame cổng loại tại điểm mặc định)")
    L += tab_tight(T, [("CPC-SC+CS", "CPC-SC+CS", 0.05), ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH", 0.05), ("CMS-CPC/H+SH+NGR", "CMS-CPC/H+SH+NGR", 0.05),
                       ("CMS-CPCW/H+SH+NGR", "CMS-CPCW/H+SH+NGR", 0.05), ("CMS-CPC/H+SH(a=0.01)+NGR", "CMS-CPC/H+SH+NGR", 0.01),
                       ("CMS-CPCW/H+SH(a=0.01)+NGR", "CMS-CPCW/H+SH+NGR", 0.01)], dss,
                   "### Bảng 4. Độ chặt: tỷ lệ khởi phát sai mỗi đoạn / α và segFAR / α")
    if arg("--paired"): L += ["### Bảng 5. So sánh ghép cặp trên cùng run: trung bình hiệu [CI 95 % bootstrap cụm theo seed] (p sign test theo seed)", "", open(arg("--paired")).read(), ""]
    if arg("--e28"):
        R8 = E.load(arg("--e28")); T8 = E.defaults(R8)
        L += ["### Bảng 6. Null phản thực chính xác (vòng 7) so với bản cắt cụt top-100 (vòng 6): CMS-CPC/H+SH recall / segFAR / run tệ nhất / sai số", "",
              "| Null | α | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (2 + len(dss)) + "|"]
        from build_e28_report import cell_def
        for lab, TT in (("cắt cụt (vòng 6)", T8), ("chính xác (vòng 7)", T)):
            for n, a in (("CMS-CPC/H+SH", "0.05"), ("CMS-CPC/H+SH(a=0.01)", "0.01"), ("CMS-T", "0.05 (CMS-T)")):
                L.append(f"| {lab} | {a} | " + " | ".join(cell_def(np.array(TT.get(d, {}).get(n, []), float)) for d in dss) + " |")
        L.append("")
    for k, lab in (("--lodo05", "### Bảng 7a. LODO, α = 0.05"), ("--lodo01", "### Bảng 7b. LODO, α = 0.01")):
        if arg(k): L += [lab, "", open(arg(k)).read(), ""]
    if arg("--holes"):
        for ratio in ("10", "50"):
            d = os.path.join(arg("--holes"), f"d{ratio}")
            if not os.path.isdir(d): continue
            TH = E.defaults(E.load(d)); dh = [x for x in E.DS_ORDER if x in TH]
            L += tab_def(TH, [("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("CPC-SC+CS", "CPC-SC+CS"), ("CMS-CPC/H+SH", "CMS-CPC/H+SH"),
                              ("CMS-CPC/H+SH+NGR", "CMS-CPC/H+SH+NGR"), ("CMS-CPCW/H+SH+NGR", "CMS-CPCW/H+SH+NGR"),
                              ("CMS-CPC/H+SH(a=0.01)+NGR", "CMS-CPC/H+SH+NGR, α = 0.01"), ("CMS-CPCW/H+SH(a=0.01)+NGR", "CMS-CPCW/H+SH+NGR, α = 0.01")], dh,
                         f"### Bảng 8{'a' if ratio == '10' else 'b'}. Bản đồ khuyết {ratio} % (null chính xác, 3 seed × 6 descriptor)")
    if arg("--diag"): L += ["### Bảng 9. Kiểm chứng Định lý 6 với null chính xác (CMS-T, α = 0.05)", "", open(arg("--diag")).read(), ""]
    tables = "\n".join(L) + "\n"
    open(os.path.join(HERE, "e29_tables.md"), "w").write(tables)
    tx = os.path.join(HERE, "e29_text.md")
    if os.path.exists(tx): open(os.path.join(HERE, "BAO_CAO_E29.md"), "w").write(open(tx).read().replace("{{TABLES}}", tables))
    print(tables)


if __name__ == "__main__":
    main()
