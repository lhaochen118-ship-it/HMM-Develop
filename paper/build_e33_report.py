"""Tables of the Entry 33 evaluation -> paper/e33_tables.md.
  --nb <dir>      oc_*_nb_s*.json of the 366 main runs (@E33B --newbase --shcf): new competitors (H33a), SHcf vs SH (H33b)
  --oxford <dir>  oc_oxford_*.json (Oxford RobotCar, PointNetVLAD split, 30 % holes, 10 seeds x 6 descriptors)
Usage: build_e33_report.py [--nb DIR] [--oxford DIR]"""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis")); sys.path.insert(0, HERE)
import e26_summary as E
from build_e28_report import tab_def

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
MAIN = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
PROP = "CMS-CPC/H+SH+G+NGRr"
NEW = [("SU25", "SU'25 (Doubt), nhãn frame"), ("SU25-seg", "SU'25, nhãn đoạn"), ("SUE24", "SUE'24, nhãn frame"),
       ("SUE24-seg", "SUE'24, nhãn đoạn"), ("Carson23", "Carson'23 (đồng thuận, không nhãn)")]
OLD = [("max-sim", "max-sim (nhãn)"), ("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("TAO26", "TAO'26 (nhãn)"),
       ("CPC-SC+CS", "CPC-SC+CS"), ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH")]
OURS = [(PROP, "**CMS-CPC/H+SH+G+NGRr (đề xuất)**"), ("CMS-CPCW/H+SH+NGRr", "CMS-CPCW/H+SH+NGRr"),
        ("CMS-CPCW/H+SH[both]+NGRr", "CMS-CPCW/H+SH[both]+NGRr (nhân quả)"), ("CMS-CPC/H+SH+G(a=0.01)+NGRr", "đề xuất, α = 0.01")]
SHCF = [("CMS-CPC/H+SH+G+NGRr", "CMS-CPC/H+SHcf+G+NGRr", 0.05), ("CMS-CPCW/H+SH+NGRr", "CMS-CPCW/H+SHcf+NGRr", 0.05),
        ("CMS-CPC/H+SH+G", "CMS-CPC/H+SHcf+G", 0.05), ("CMS-CPCW/H+SH", "CMS-CPCW/H+SHcf", 0.05),
        ("CMS-CPC/H+SH+G(a=0.01)+NGRr", "CMS-CPC/H+SHcf+G(a=0.01)+NGRr", 0.01)]


def m(T, d, n, k):
    v = np.array(T.get(d, {}).get(n, []), float)
    return np.nanmean(v[:, k]) if len(v) else np.nan


def h33a(T, dss, alpha=0.05):
    """per dataset: is the proposed recall above every NEW competitor whose mean segFAR <= alpha? (pre-registered H33a)"""
    L = ["**H33a** (đề xuất có recall cao hơn mọi đối thủ mới có segFAR TB ≤ α): ô = recall đối thủ / segFAR TB "
         "(✗ = vi phạm α, ✓ = hợp lệ nhưng thua đề xuất, ▲ = hợp lệ và cao hơn đề xuất)", "",
         "| Dataset | đề xuất | " + " | ".join(lab for _, lab in NEW) + " | H33a |", "|---" * (3 + len(NEW)) + "|"]
    ok_n = 0
    for d in dss:
        rp = m(T, d, PROP, 0); cells, ok = [], True
        for n, _ in NEW:
            r, f = m(T, d, n, 0), m(T, d, n, 1)
            if np.isnan(r): cells.append("–"); continue
            tag = "✗" if f > alpha else ("▲" if r >= rp else "✓"); ok &= tag != "▲"
            cells.append(f"{r:.3f} / {f:.3f} {tag}")
        ok_n += ok
        L.append(f"| {E.DS_NAME[d]} | {rp:.3f} / {m(T, d, PROP, 1):.3f} | " + " | ".join(cells) + f" | {'đạt' if ok else 'không'} |")
    return L + ["", f"H33a đạt trên {ok_n}/{len(dss)} dataset (ngưỡng đăng ký: ≥ 6/7).", ""], ok_n


def h33b(T, dss):
    L = ["**H33b** (dung sai SH hiệu chuẩn phản thực, β = 0.01, thay hằng số 0.5 excl): Δrecall = SHcf − SH / segFAR TB của SHcf", "",
         "| Cặp | " + " | ".join(E.DS_NAME[d] for d in dss) + " | \\|Δrecall\\| ≤ 0.01 | segFAR ≤ α |", "|---" * (3 + len(dss)) + "|"]
    res = {}
    for a, b, al in SHCF:
        cells, close, valid = [], 0, 0
        for d in dss:
            ra, rb, fb = m(T, d, a, 0), m(T, d, b, 0), m(T, d, b, 1)
            if np.isnan(rb): cells.append("–"); continue
            cells.append(f"{rb - ra:+.3f} / {fb:.3f}"); close += abs(rb - ra) <= 0.01; valid += fb <= al
        res[b] = (close, valid)
        L.append(f"| {b} vs SH (α = {al}) | " + " | ".join(cells) + f" | {close}/{len(dss)} | {valid}/{len(dss)} |")
    return L + [""], res


def main():
    L = []
    if arg("--nb"):
        R = E.load(arg("--nb")); T = E.defaults(R); dss = [d for d in MAIN if d in T]
        n = sum(len(runs) for bd in R.values() for runs in bd.values())
        L += tab_def(T, OLD + NEW + OURS, dss, f"### Đối thủ mới trên các dataset chính ({n} run, điểm mặc định): recall / segFAR TB / tệ nhất / sai số (m)")
        a, _ = h33a(T, dss); L += a
        b, _ = h33b(T, dss); L += b
    if arg("--oxford"):
        R = E.load(arg("--oxford")); T = E.defaults(R)
        nr = sum(len(v) for v in R.get("oxford", {}).values())
        L += tab_def(T, OLD + NEW + OURS + [("CMS-CPC/H+SHcf+G+NGRr", "CMS-CPC/H+SHcf+G+NGRr")], ["oxford"],
                     f"### Oxford RobotCar (PointNetVLAD split, 44 lượt chạy, 30 % lỗ bản đồ, {nr} run): recall / segFAR TB / tệ nhất / sai số (m)")
        L += ["Theo descriptor (đề xuất vs CPC-SC-T½+SH vs SUE'24-seg): recall / segFAR TB", "", "| Descriptor | đề xuất | CPC-SC-T½+SH | SUE'24-seg | Xu'21 |", "|---|---|---|---|---|"]
        for de, runs in sorted(R.get("oxford", {}).items()):
            Td = E.defaults({"oxford": {de: runs}})
            L.append(f"| {de} | " + " | ".join(f"{m(Td, 'oxford', n, 0):.3f} / {m(Td, 'oxford', n, 1):.3f}" for n in (PROP, "CPC-SC-T0.5+SH", "SUE24-seg", "Xu21")) + " |")
        v = np.array(T.get("oxford", {}).get(PROP, []), float)
        if len(v): L += ["", f"Đề xuất: {np.mean(v[:, 1] > 0.05):.2f} tỷ lệ run có segFAR > α = 0.05 ({len(v)} run).", ""]
    tables = "\n".join(L) + "\n"
    open(os.path.join(HERE, "e33_tables.md"), "w").write(tables); print(tables)


if __name__ == "__main__":
    main()
