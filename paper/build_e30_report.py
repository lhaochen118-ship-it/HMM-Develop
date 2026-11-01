"""Tables of the Entry 30 report (causal online calibration, filter robustness, natural off-map benchmark) ->
paper/e30_tables.md and paper/BAO_CAO_E30.md (= paper/e30_text.md with the tables at {{TABLES}}); PDF via automation/md2pdf.py.
Usage: build_e30_report.py --main <dir> [--f1 d --f2 d --f3 d] [--nat d] [--nat1 d] [--paired f] [--paired-f f] [--lodo05 f] [--lodo01 f]"""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis")); sys.path.insert(0, HERE)
import e26_summary as E
from build_e28_report import tab_def, tab_tight

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
LAB = [("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("TAO26", "TAO'26 (nhãn)")]
OLD = [("CPC-SC+CS", "CPC-SC+CS (vòng 3)"), ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH (vòng 5)"), ("CPC-SC-T0.5+SH+NGRr", "CPC-SC-T½+SH+NGRr"), ("CPC-SC-T0.5+SH+NGR", "CPC-SC-T½+SH+NGR")]
GRP = [("", "phiên (chuyển đạo)"), ("[loco]", "phiên khác"), ("[online]", "online nhân quả"), ("[both]", "giao phiên ∧ phiên khác")]


GATES = ("", "+NGRr", "+NGR")                    # no gate, rate-limited release (Entry 29 code), streak-open release (Entry 30)


def fam(base, g, a01=False, gate=""):
    gate = "+NGR" if gate is True else ("" if gate is False else gate)
    return base + g + ("(a=0.01)" if a01 else "") + gate


def rows(a01=False):
    R = []
    for base, nm in (("CMS-CPCW/H+SH", "CMS-CPCW/H+SH"), ("CMS-CPC/H+SH+G", "CMS-CPC/H+SH+G")):
        for g, gl in GRP:
            for gate in GATES:
                R.append((fam(base, g, a01, gate), f"{nm}{gate} [{gl}]"))
    return R


def tab_nat(T, rules, title):
    dss = [d for d in E.DS_ORDER if d.startswith("4sx:") and d in T]
    if not dss: return []
    L = tab_def(T, rules, dss, title, oracle=False)
    # pooled over the 36 runs: mean recall (scene A), mean / worst segFAR (scene B), share of runs with segFAR > alpha, error A
    L += ["Gộp 36 run: recall cảnh A / segFAR TB / segFAR tệ nhất / tỷ lệ run segFAR > α / sai số cảnh A (m)", "",
          "| Luật | gộp |", "|---|---|"]
    for n, lab in rules:
        v = np.array([x for d in dss for x in T[d].get(n, [])], float)
        if not len(v): continue
        al = 0.01 if "(a=0.01)" in n else 0.05
        L.append(f"| {lab} | {np.nanmean(v[:, 0]):.3f} / {np.nanmean(v[:, 1]):.3f} / {np.nanmax(v[:, 1]):.3f} / {np.mean(v[:, 1] > al):.2f} / {np.nanmean(v[:, 4]):.1f} |")
    return L + [""]


def main():
    L = []
    if arg("--main"):
        T = E.defaults(E.load(arg("--main"))); dss = [d for d in E.DS_ORDER if d in T and not d.startswith("4sx")]
        L += ["## 4. Kết quả\n"]
        L += tab_def(T, LAB + OLD + rows(), dss, "### Bảng 1. Hiệu chuẩn theo nhóm, α = 0.05: recall / segFAR TB / segFAR run tệ nhất / sai số điều hướng (m), 366 run")
        L += tab_def(T, [("CMS-CPC/H+SH+NGR", "CMS-CPC/H+SH+NGR"), ("CMS-CPC/H+SH(a=0.01)+NGR", "CMS-CPC/H+SH+NGR, α = 0.01")] + rows(True), dss,
                     "### Bảng 2. Như Bảng 1, α = 0.01", oracle=False)
        L += tab_tight(T, [(fam("CMS-CPCW/H+SH", g, False, "+NGRr"), f"CMS-CPCW/H+SH+NGRr [{gl}]", 0.05) for g, gl in GRP] +
                       [(fam("CMS-CPCW/H+SH", g, True, "+NGRr"), f"CMS-CPCW/H+SH+NGRr [{gl}]", 0.01) for g, gl in GRP], dss,
                       "### Bảng 3. Độ chặt: tỷ lệ khởi phát sai mỗi đoạn / α và segFAR / α", 0.05)
    if arg("--paired"): L += ["### Bảng 4. So sánh ghép cặp (cùng run): trung bình hiệu [CI 95 % bootstrap cụm theo seed] (p sign test theo seed)", "", open(arg("--paired")).read(), ""]
    FR = [("CPC-SC+CS", "CPC-SC+CS"), ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH"), ("CPC-SC-T0.5+SH+NGRr", "CPC-SC-T½+SH+NGRr"), ("CPC-SC-T0.5+SH+NGR", "CPC-SC-T½+SH+NGR"),
          ("CMS-CPCW/H+SH", "CMS-CPCW/H+SH"), ("CMS-CPCW/H+SH+NGRr", "CMS-CPCW/H+SH+NGRr"), ("CMS-CPCW/H+SH+NGR", "CMS-CPCW/H+SH+NGR"),
          ("CMS-CPC/H+SH+G", "CMS-CPC/H+SH+G"), ("CMS-CPC/H+SH+G+NGRr", "CMS-CPC/H+SH+G+NGRr"), ("CMS-CPC/H+SH+G+NGR", "CMS-CPC/H+SH+G+NGR"),
          ("CMS-CPC/H+SH", "CMS-CPC/H+SH"), ("CMS-CPC/H+SH+NGRr", "CMS-CPC/H+SH+NGRr"), ("CMS-CPC/H+SH+NGR", "CMS-CPC/H+SH+NGR"), ("CMS-CPC/H+SH+NG", "ablation +NG"), ("CMS-CPC/H+SH+DRG", "ablation +DRG"),
          ("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("TAO26", "TAO'26 (nhãn)")]
    for k, lab in (("--f1", "F1: nhiễu quá trình 0.2·L (×4)"), ("--f2", "F2: F1 + σ fix 10 m"), ("--f3", "F3: khởi tạo không nhãn (top-1 frame đầu, σ 1 km)")):
        if arg(k):
            TF = E.defaults(E.load(arg(k))); dF = [d for d in E.DS_ORDER if d in TF and not d.startswith("4sx")]
            L += tab_def(TF, FR, dF, f"### Bảng 5{'abc'[int(k[-1]) - 1]}. Độ bền bộ lọc — {lab}, α = 0.05", oracle=False)
    if arg("--paired-f"): L += ["### Bảng 6. Ghép cặp dưới F1–F3", "", open(arg("--paired-f")).read(), ""]
    NR = LAB + OLD + [(fam("CMS-CPCW/H+SH", g, a, gt), f"CMS-CPCW/H+SH{gt} [{gl}]{', α = 0.01' if a else ''}")
                      for a in (False, True) for g, gl in GRP for gt in GATES] + \
         [(fam("CMS-CPC/H+SH+G", g, False, gt), f"CMS-CPC/H+SH+G{gt} [{gl}]") for g, gl in GRP for gt in GATES]
    if arg("--nat"): L += tab_nat(E.defaults(E.load(arg("--nat"))), NR, "### Bảng 7. Off-map tự nhiên (4Seasons chéo cảnh, bản đồ A ← truy vấn B): recall cảnh A / segFAR TB / tệ nhất / sai số cảnh A (m)")
    if arg("--nat1"): L += tab_nat(E.defaults(E.load(arg("--nat1"))), NR, "### Bảng 8. Off-map tự nhiên, khởi tạo không nhãn (F3)")
    if arg("--holes"):
        HR = [("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("CPC-SC+CS", "CPC-SC+CS"), ("CPC-SC+CS+NGRr", "CPC-SC+CS+NGRr"),
              ("CMS-CPC/H+SH", "CMS-CPC/H+SH"), ("CMS-CPC/H+SH+NGRr", "CMS-CPC/H+SH+NGRr"), ("CMS-CPC/H+SH+NGR", "CMS-CPC/H+SH+NGR"),
              ("CMS-CPC/H+SH+G+NGRr", "**CMS-CPC/H+SH+G+NGRr**"), ("CMS-CPC/H+SH+G+NGR", "CMS-CPC/H+SH+G+NGR"),
              ("CMS-CPCW/H+SH+NGRr", "**CMS-CPCW/H+SH+NGRr**"), ("CMS-CPCW/H+SH+NGR", "CMS-CPCW/H+SH+NGR"),
              ("CMS-CPC/H+SH(a=0.01)+NGRr", "CMS-CPC/H+SH+NGRr, α = 0.01"), ("CMS-CPCW/H+SH(a=0.01)+NGRr", "CMS-CPCW/H+SH+NGRr, α = 0.01")]
        for ratio, sub in (("10", "a"), ("50", "b")):
            d = os.path.join(arg("--holes"), f"d{ratio}")
            if not os.path.isdir(d): continue
            TH = E.defaults(E.load(d)); dh = [x for x in E.DS_ORDER if x in TH]
            L += tab_def(TH, HR, dh, f"### Bảng 10{sub}. Bản đồ khuyết {ratio} % (3 seed × 6 descriptor, cổng sửa/giới hạn tốc độ)")
    if arg("--e31"):
        TJ = E.defaults(E.load(arg("--e31"))); dj = [d for d in E.DS_ORDER if d in TJ]
        JR = [("CPC-SC-T0.5+SH", "CPC-SC-T½+SH")]
        for base in ("CMS-CPCW/{}+SH", "CMS-CPC/{}+SH+G"):
            for gt in ("", "+NGRr"):
                for pl, pn in (("H", "chuỗi vị trí gốc"), ("R", "dựng lại, không OFF"), ("J", "**HMM liên hợp**")):
                    JR.append((base.format(pl) + gt, f"{base.format(pl)}{gt} ({pn})"))
        for g in ("[both]", "[online]"):
            for pl in ("H", "J"): JR.append((f"CMS-CPCW/{pl}+SH{g}+NGRr", f"CMS-CPCW/{pl}+SH{g}+NGRr"))
        L += tab_def(TJ, JR, dj, "### Bảng 11. HMM liên hợp (Entry 31, seed 0–2, 114 run): /H chuỗi vị trí gốc, /R dựng lại từ top-K không OFF, /J liên hợp có OFF hiệu chuẩn", oracle=False)
        if arg("--paired-j"): L += ["### Bảng 12. Ghép cặp HMM liên hợp", "", open(arg("--paired-j")).read(), ""]
    for k, lab in (("--lodo05", "### Bảng 9a. LODO, α = 0.05"), ("--lodo01", "### Bảng 9b. LODO, α = 0.01")):
        if arg(k): L += [lab, "", open(arg(k)).read(), ""]
    tables = "\n".join(L) + "\n"
    open(os.path.join(HERE, "e30_tables.md"), "w").write(tables)
    tx = os.path.join(HERE, "e30_text.md")
    if os.path.exists(tx): open(os.path.join(HERE, "BAO_CAO_E30.md"), "w").write(open(tx).read().replace("{{TABLES}}", tables))
    print(tables)


if __name__ == "__main__":
    main()
