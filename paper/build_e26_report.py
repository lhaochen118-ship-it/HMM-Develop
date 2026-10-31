"""Tables of the Entry 26 report -> paper/e26_tables.md and paper/BAO_CAO_E26.md (= paper/e26_text.md with the tables at
{{TABLES}}); PDF: python3 automation/md2pdf.py paper/BAO_CAO_E26.md paper/BAO_CAO_E26.pdf
Usage: build_e26_report.py --def <dir> --cur <dir>[,<dir>] [--trail <dir>] [--vlm <json,...>] [--gpc <json>]"""
import sys, os, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis"))
import e26_summary as E

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
RULES = [("Xu21", "Xu'21 HMM off-map (nhãn)"), ("Claxton24", "Claxton'24 MLP (nhãn)"), ("TAO26", "TAO'26 (nhãn: ngưỡng 3σ)"),
         ("TRAIL26", "TRAIL'26 (nhãn: ngưỡng điều kiện dễ)"), ("certified", "Certified"), ("CPC-SC+CS", "CPC-SC+CS (vòng 3)"),
         ("CPC-SC+SH", "CPC-SC+SH"), ("CPC-W+CS+SH", "CPC-W+CS+SH (Định lý 5)"), ("TAO-SC", "**TAO-SC** (không nhãn)"),
         ("CPC-SC-T", "**CPC-SC-T** (không nhãn)"), ("CPC-SC-T+SH", "**CPC-SC-T+SH** (không nhãn)"), ("oracle", "Oracle")]


def fmt_def(T, ds, n):
    v = np.array(T.get(ds, {}).get(n, []), float)
    if not len(v): return "–"
    return f"{np.nanmean(v[:, 0]):.2f} / {np.nanmean(v[:, 1]):.3f} / {np.nanmean(v[:, 4]):.1f}" if n != "oracle" else f"{np.nanmean(v[:, 0]):.2f} / – / {np.nanmean(v[:, 4]):.1f}"


def main():
    Rd = {}
    for d in arg("--def").split(","):
        for ds, bd in E.load(d).items():
            for desc, runs in bd.items():
                tgt = Rd.setdefault(ds, {}).setdefault(desc, {})
                for rk, run in runs.items():
                    if rk in tgt: tgt[rk]["families"].update(run["families"])
                    else: tgt[rk] = run
    if arg("--trail"):
        for ds, bd in E.load(arg("--trail")).items():
            for desc, runs in bd.items():
                tgt = Rd.setdefault(ds, {}).setdefault(desc, {})
                for rk, run in runs.items():
                    if rk in tgt: tgt[rk]["families"].update(run["families"])
                    else: tgt[rk] = run
    T = E.defaults(Rd); dss = [d for d in E.DS_ORDER if d in T]
    Rc = {}
    for d in arg("--cur").split(",") + ([arg("--trail")] if arg("--trail") else []):
        for ds, bd in E.load(d).items():
            for desc, runs in bd.items():
                tgt = Rc.setdefault(ds, {}).setdefault(desc, {})
                for rk, run in runs.items():
                    if rk in tgt: tgt[rk]["families"].update(run["families"])
                    else: tgt[rk] = run
    C = E.curves(Rc)
    L = ["## 5. Kết quả (7 dataset, 6 descriptor; bản đồ khuyết 30 %; NCLT off-map tự nhiên)\n",
         "### Bảng 1. Điểm mặc định: recall / segFAR / sai số điều hướng (m), trung bình mọi run (10 seed; NCLT 1 seed; "
         "TRAIL'26 chỉ MegaLoc, seed 0–2)\n",
         "| Luật | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|"]
    for n, lab in RULES: L.append(f"| {lab} | " + " | ".join(fmt_def(T, d, n) for d in dss) + " |")
    L += ["", "### Bảng 2. Đường cong vận hành: recall tại FL ≤ 0.01 / pAUC (FL ∈ [0, 0.05]), seed 0–2\n",
          "| Luật | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|"]
    for n, lab in RULES:
        if n == "oracle": continue
        cells = []
        for d in dss:
            v = np.array(C.get(d, {}).get(n, []), float); cells.append("–" if not len(v) else f"{v[:, 1].mean():.3f} / {v[:, 3].mean():.3f}")
        L.append(f"| {lab} | " + " | ".join(cells) + " |")
    L += ["", "### Bảng 3. Kiểm chứng Định lý 5: khởi phát sai mỗi đoạn off-map (H/ARL₀), trung bình / run tệ nhất (α = 0.05)\n",
          "| Luật | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|"]
    for n in ("Xu21", "Claxton24", "TAO26", "CPC-SC+CS", "CPC-W+CS+SH", "TAO-SC", "CPC-SC-T", "CPC-SC-T+SH"):
        cells = []
        for d in dss:
            v = np.array(T.get(d, {}).get(n, []), float); cells.append("–" if not len(v) else f"{np.nanmean(v[:, 3]):.3f} / {np.nanmax(v[:, 3]):.3f}")
        L.append(f"| {dict(RULES).get(n, n)} | " + " | ".join(cells) + " |")
    if arg("--gpc"):
        g = json.load(open(arg("--gpc")))
        L += ["", "### Bảng 4. Cái giá của phụ thuộc: chứng chỉ GPC (đúng với mọi phụ thuộc) so với CPC-SC+CS, seed 0\n",
              "| Cấu hình | GPC recall (α = 0.01 / 0.05) | GPC FL | CPC-SC+CS recall | CPC-SC+CS FL |", "|---|---|---|---|---|"]
        for k, r in g.items(): L.append(f"| {k} | {r[0]:.3f} / {r[1]:.3f} | {r[2]:.4f} | {r[3]:.3f} | {r[4]:.4f} |")
    if arg("--vlm"):
        L += ["", "### Bảng 5. VPR-auditing'26 (Qwen2.5-VL-7B, offline) trên Boreas, seed 0, các frame được audit (mỗi 5 frame)\n",
              "Chỉ số của paper (P, coverage C, FAR, S) và của dự án (recall, FL, sai số Kalman khi chỉ được fix ở frame được audit).\n",
              "| Descriptor | Luật | P | C | FAR | S | recall | FL | sai số (m) |", "|---|---|---|---|---|---|---|---|---|"]
        for f in arg("--vlm").split(","):
            j = json.load(open(f))
            for k, lab in (("VPR-auditing (Qwen2.5-VL-7B)", "VPR-auditing'26"), ("Claxton24 MLP (labels)", "Claxton'24 (nhãn)"),
                           ("HMM off-map (labels)", "Xu'21 (nhãn)"), ("CPC-SC+CS", "CPC-SC+CS"), ("CPC-SC+SH", "CPC-SC+SH")):
                r = j["rules"].get(k)
                if r: L.append(f"| {j['desc']} ({j['n_audited']} frame) | {lab} | {r['P']:.3f} | {r['C']:.3f} | {r['FAR']:.3f} | {r['S']:.3f} | {r['recall']:.3f} | {r['FL']:.3f} | {r['err_mean']:.1f} |")
    tables = "\n".join(L) + "\n"
    open(os.path.join(HERE, "e26_tables.md"), "w").write(tables)
    txt = open(os.path.join(HERE, "e26_text.md")).read().replace("{{TABLES}}", tables)
    open(os.path.join(HERE, "BAO_CAO_E26.md"), "w").write(txt); print(tables)


if __name__ == "__main__":
    main()
