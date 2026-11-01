"""Tables of Entry 34 (counterfactual segment shape test CST) and of the Oxford RobotCar evaluation -> paper/e34_tables.md.
  --e34 <dir>     oc_*_e34_s*.json (366 runs, `oc_curves.py --cst --fams @E34`, groups cond + loco)
  --sens <dir>    oc_*_cst05_s*.json / oc_*_cst2_s*.json (a_sh = 0.5 / 2 x alpha, seeds 0-2)
  --oxford <dir>  oc_oxford_*.json (natural_eval.py, 10 seeds x 6 descriptors, @E33B,@E34)
Usage: build_e34_report.py [--e34 DIR] [--sens DIR] [--oxford DIR]"""
import sys, os, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis")); sys.path.insert(0, HERE)
import e26_summary as E
from build_e28_report import tab_def

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
MAIN = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
SH, CSTM, CSTW = "CMS-CPC/H+SH+G+NGRr", "CMS-CPC/H+CST+G+NGRr", "CMS-CPCW/H+CST+NGRr"
ROWS = [("CPC-SC-T0.5+SH", "CPC-SC-T½+SH"), (SH, "**CMS-CPC/H+SH+G+NGRr** (SH chọn tay)"), ("CMS-CPCW/H+SH+NGRr", "CMS-CPCW/H+SH+NGRr"),
        (CSTM, "**CMS-CPC/H+CST+G+NGRr** (CST, a_sh = α)"), (CSTW, "CMS-CPCW/H+CST+NGRr"),
        ("CMS-CPC/H+CST+G[both]+NGRr", "CMS-CPC/H+CST+G[both]+NGRr (nhân quả)"), ("CMS-CPCW/H+CST[both]+NGRr", "CMS-CPCW/H+CST[both]+NGRr (nhân quả)"),
        ("CMS-CPC/H+CST2+G+NGRr", "CST2 (α/2 + α/2)"), ("CMS-CPC/H+CSTt+G+NGRr", "CSTt (tuyến thật, cùng bộ ước lượng)"),
        ("CMS-CPC/H+CST+G", "CMS-CPC/H+CST+G (không cổng)")]


def m(T, d, n, k):
    v = np.array(T.get(d, {}).get(n, []), float)
    return np.nanmean(v[:, k]) if len(v) else np.nan


def hyp(T, dss):
    L = ["**Kiểm giả thuyết (đăng ký trước, Entry 34):**", ""]
    for n in (CSTM, CSTW):
        ok = sum(m(T, d, n, 1) <= 0.05 for d in dss)
        close = sum(m(T, d, n, 0) >= m(T, d, SH, 0) - 0.02 for d in dss)
        win = sum(m(T, d, n, 0) > m(T, d, "CPC-SC-T0.5+SH", 0) for d in dss)
        dr = [m(T, d, n, 0) - m(T, d, SH, 0) for d in dss]
        L.append(f"- {n}: segFAR ≤ 0.05 trên {ok}/{len(dss)} (H34a); recall ≥ SH − 0.02 trên {close}/{len(dss)} (H34b, cần ≥ 5/7); "
                 f"> CPC-SC-T½+SH trên {win}/{len(dss)} (cần ≥ 6/7); Δrecall vs SH: " + ", ".join(f"{E.DS_NAME[d]} {x:+.3f}" for d, x in zip(dss, dr)))
    for n in ("CMS-CPC/H+CST+G[both]+NGRr", "CMS-CPCW/H+CST[both]+NGRr"):
        ok = sum(m(T, d, n, 1) <= 0.05 for d in dss); L.append(f"- {n}: segFAR ≤ 0.05 trên {ok}/{len(dss)} (H34c)")
    return L + [""]


def runs_over(T, dss, n, al=0.05):
    v = np.array([x for d in dss for x in T.get(d, {}).get(n, [])], float)
    return (np.mean(v[:, 1] > al), np.nanmax(v[:, 1]), len(v)) if len(v) else (np.nan, np.nan, 0)


def main():
    L = []
    if arg("--e34"):
        R = E.load(arg("--e34")); T = E.defaults(R); dss = [d for d in MAIN if d in T]
        n = sum(len(runs) for bd in R.values() for runs in bd.values())
        L += tab_def(T, ROWS, dss, f"### Phép thử hình dạng phản thực CST ({n} run, α = 0.05): recall / segFAR TB / tệ nhất / sai số (m)")
        L += hyp(T, dss)
        L += ["Tỷ lệ run có segFAR > α / segFAR tệ nhất (mọi dataset):", "", "| Luật | run > α | tệ nhất | số run |", "|---|---|---|---|"]
        for nm, lab in ROWS[1:6]:
            a, b, c = runs_over(T, dss, nm); L.append(f"| {lab} | {a:.3f} | {b:.3f} | {c} |")
        L.append("")
    if arg("--sens"):
        Rs = {v: E.load(os.path.join(arg("--sens"), v)) for v in ("cst05", "cst2") if os.path.isdir(os.path.join(arg("--sens"), v))}
        if Rs:
            L += ["### Độ nhạy của mức a_sh của CST (seed 0–2): recall / segFAR TB", "",
                  "| a_sh | " + " | ".join(E.DS_NAME[d] for d in MAIN) + " | segFAR ≤ α |", "|---" * (2 + len(MAIN)) + "|"]
            for v, lab in (("cst05", "0.5 α = 0.025"), ("cst2", "2 α = 0.10")):
                if v not in Rs: continue
                T = E.defaults(Rs[v]); cells = [f"{m(T, d, CSTM, 0):.3f} / {m(T, d, CSTM, 1):.3f}" for d in MAIN]
                L.append(f"| {lab} | " + " | ".join(cells) + f" | {sum(m(T, d, CSTM, 1) <= 0.05 for d in MAIN)}/7 |")
            L.append("")
    if arg("--oxford"):
        R = E.load(arg("--oxford")); T = E.defaults(R); nr = sum(len(v) for v in R.get("oxford", {}).values())
        OX = [("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("TAO26", "TAO'26 (nhãn)"), ("max-sim", "max-sim (nhãn)"),
              ("SU25-seg", "SU'25, nhãn đoạn"), ("SUE24-seg", "SUE'24, nhãn đoạn"), ("Carson23", "Carson'23"), ("CPC-SC+CS", "CPC-SC+CS"),
              ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH"), (SH, "**CMS-CPC/H+SH+G+NGRr**"), ("CMS-CPCW/H+SH+NGRr", "CMS-CPCW/H+SH+NGRr"),
              ("CMS-CPCW/H+SH[both]+NGRr", "CMS-CPCW/H+SH[both]+NGRr"), (CSTM, "CMS-CPC/H+CST+G+NGRr"), (CSTW, "CMS-CPCW/H+CST+NGRr"),
              ("CMS-CPC/H+SHcf+G+NGRr", "CMS-CPC/H+SHcf+G+NGRr")]
        L += tab_def(T, OX, ["oxford"], f"### Oxford RobotCar (PointNetVLAD split, 43 lượt chạy, bản đồ 2014-12-09, 30 % lỗ, {nr} run): "
                     "recall / segFAR TB / tệ nhất / sai số (m)")
        L += ["Theo descriptor: recall / segFAR TB", "", "| Descriptor | CMS-CPC/H+SH+G+NGRr | CMS-CPCW/H+SH+NGRr | CPC-SC-T½+SH | CST | SUE'24-seg | Xu'21 |",
              "|---|---|---|---|---|---|---|"]
        for de, runs in sorted(R.get("oxford", {}).items()):
            Td = E.defaults({"oxford": {de: runs}})
            L.append(f"| {de} | " + " | ".join(f"{m(Td, 'oxford', n, 0):.3f} / {m(Td, 'oxford', n, 1):.3f}"
                                               for n in (SH, "CMS-CPCW/H+SH+NGRr", "CPC-SC-T0.5+SH", CSTM, "SUE24-seg", "Xu21")) + " |")
        L.append("")
        for n, lab in ((SH, "đề xuất"), ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH"), ("Xu21", "Xu'21")):
            a, b, c = runs_over(T, ["oxford"], n); L.append(f"- {lab}: tỷ lệ run segFAR > α = {a:.2f}, tệ nhất {b:.3f} ({c} run)")
        L.append("")
    tables = "\n".join(L) + "\n"
    open(os.path.join(HERE, "e34_tables.md"), "w").write(tables); print(tables)


if __name__ == "__main__":
    main()
