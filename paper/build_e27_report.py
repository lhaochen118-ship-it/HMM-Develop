"""Tables of the Entry 27 report -> paper/e27_tables.md and paper/BAO_CAO_E27.md (= paper/e27_text.md with the tables at
{{TABLES}}); PDF: python3 automation/md2pdf.py paper/BAO_CAO_E27.md paper/BAO_CAO_E27.pdf
Usage: build_e27_report.py --def d1,d2,... --cur d1,d2,... [--xdef d] [--xcur d] [--vlm j1,j2,...] [--lodo file.md]"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis"))
import e26_summary as E

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
MAIN = [("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("SafeVPR", "SafeVPR'26 (nhãn)"), ("TAO26", "TAO'26 (nhãn)"),
        ("CPC-SC+CS", "CPC-SC+CS (vòng 3)"), ("CPC-SC-T+SH", "CPC-SC-T+SH (vòng 4)"), ("CPC-SC-T0.5+SH", "**CPC-SC-T½+SH**"),
        ("CPC-SC-T0.5+CS", "CPC-SC-T½+CS"), ("CPC-SC-Tmin+SH", "CPC-SC-Tmin+SH (thăm dò)"), ("CPC-SC-Tonly+SH", "CPC-SC-Tonly+SH (thăm dò)"),
        ("oracle", "Oracle")]
XRULES = [("CPC-SC+CS", "CPC-SC+CS (null bản đồ)"), ("CPC-SC(X)+CS", "CPC-SC(X)+CS"), ("CPC-SC(X)+SH", "CPC-SC(X)+SH"),
          ("CPC-SC-T+CS", "CPC-SC-T+CS (null bản đồ)"), ("CPC-SC-T(X)+CS", "CPC-SC-T(X)+CS"), ("CPC-SC-T+SH", "CPC-SC-T+SH (null bản đồ)"),
          ("CPC-SC-T(X)+SH", "CPC-SC-T(X)+SH")]


def load_many(dirs):
    R = {}
    for d in dirs.split(","):
        if not d: continue
        for k, bd in E.load(d).items():
            for desc, runs in bd.items():
                tgt = R.setdefault(k, {}).setdefault(desc, {})
                for rk, run in runs.items():
                    if rk in tgt: tgt[rk]["families"].update(run["families"]); tgt[rk].setdefault("oracle", run.get("oracle"))
                    else: tgt[rk] = run
    return R


def table(T, C, rules, dss, title_d, title_c):
    L = [title_d, "", "| Luật | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|"]
    for n, lab in rules:
        cells = []
        for d in dss:
            v = np.array(T.get(d, {}).get(n, []), float)
            cells.append("–" if not len(v) else (f"{np.nanmean(v[:, 0]):.2f} / {np.nanmean(v[:, 1]):.3f} / {np.nanmax(v[:, 1]):.3f} / {np.nanmean(v[:, 4]):.1f}"
                                               if n != "oracle" else f"{np.nanmean(v[:, 0]):.2f} / – / – / {np.nanmean(v[:, 4]):.1f}"))
        L.append(f"| {lab} | " + " | ".join(cells) + " |")
    L += ["", title_c, "", "| Luật | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|"]
    for n, lab in rules:
        if n == "oracle": continue
        cells = []
        for d in dss:
            v = np.array(C.get(d, {}).get(n, []), float); cells.append("–" if not len(v) else f"{v[:, 1].mean():.3f} / {v[:, 3].mean():.3f}")
        L.append(f"| {lab} | " + " | ".join(cells) + " |")
    return L


def main():
    T, C = E.defaults(load_many(arg("--def"))), E.curves(load_many(arg("--cur")))
    dss = [d for d in E.DS_ORDER if d in T]
    L = ["## 4. Kết quả\n"]
    L += table(T, C, MAIN, dss, "### Bảng 1. Điểm mặc định: recall / segFAR trung bình / segFAR run tệ nhất / sai số (m); 10 seed (NCLT 1); SafeVPR seed 0–2",
               "### Bảng 2. Đường cong: recall tại FL ≤ 0.01 / pAUC (FL ∈ [0, 0.05]); seed 0–2")
    if arg("--xdef"):
        TX, CX = E.defaults(load_many(arg("--xdef"))), E.curves(load_many(arg("--xcur") or arg("--xdef")))
        L += [""] + table(TX, CX, XRULES, ["boreas"], "### Bảng 3. Boreas: null chéo traversal (X) so với null bản đồ — mặc định (10 seed)",
                          "### Bảng 3b. Boreas: đường cong (seed 0–2)")
    if arg("--vlm"):
        L += ["", "### Bảng 4. VPR-auditing'26 (Qwen2.5-VL-7B offline) trên các frame được audit (mỗi 5 frame), seed 0", "",
              "| Dataset · descriptor | Luật | P | C | FAR | S | recall | FL | sai số (m) |", "|---|---|---|---|---|---|---|---|---|"]
        for f in arg("--vlm").split(","):
            j = json.load(open(f))
            for k, lab in (("VPR-auditing (Qwen2.5-VL-7B)", "VPR-auditing'26"), ("Claxton24 MLP (labels)", "Claxton'24 (nhãn)"), ("CPC-SC+CS", "CPC-SC+CS")):
                r = j["rules"].get(k)
                if r: L.append(f"| {E.DS_NAME.get(j['ds'], j['ds'])} · {j['desc']} | {lab} | {r['P']:.3f} | {r['C']:.3f} | {r['FAR']:.3f} | {r['S']:.3f} | {r['recall']:.3f} | {r['FL']:.3f} | {r['err_mean']:.1f} |")
    if arg("--lodo"): L += ["", "### Bảng 5. Chọn biến thể leave-one-dataset-out (tiêu chí đăng ký trước)", "", open(arg("--lodo")).read()]
    tables = "\n".join(L) + "\n"
    open(os.path.join(HERE, "e27_tables.md"), "w").write(tables)
    open(os.path.join(HERE, "BAO_CAO_E27.md"), "w").write(open(os.path.join(HERE, "e27_text.md")).read().replace("{{TABLES}}", tables)); print(tables)


if __name__ == "__main__":
    main()
