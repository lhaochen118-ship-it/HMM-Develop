"""Tables of Entry 36 (forward counterfactual surgery CST-F; N = 40; St Lucia / SafeVPR'26) -> paper/e36_tables.md
  --main DIR      oc_*_e36_s*.json (seeds 0-2, 114 runs, e36_run.py)
  --audit FILE    cst_audit.py json over the same runs with FWD_DIR (pass rates of real off-map segments)
  --oxford DIR    oc_oxford_*_e36_s*.json
  --stlucia DIR   oc_stlucia_*_e36_s*.json
  --n40 DIR       sub-dirs n20/ and n40/ with oc_*.json of the N = 40 confirmation (seeds 1-9)
  --safevpr FILE  safevpr26_eval.py json (direct comparison on St Lucia)
Usage: build_e36_report.py [--main DIR] [--audit F] [--oxford DIR] [--stlucia DIR] [--n40 DIR] [--safevpr F]"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis")); sys.path.insert(0, HERE)
import e26_summary as E
from build_e28_report import tab_def

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
MAIN = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
E.DS_NAME.update({"stlucia": "St Lucia", "oxford": "Oxford RobotCar"})
SH, SHCST, CST, CSTF = "CMS-CPC/H+SH+G+NGRr", "CMS-CPC/H+SH+CST+G+NGRr", "CMS-CPC/H+CST+G+NGRr", "CMS-CPC/H+CSTF+G+NGRr"
ROWS = [("CPC-SC-T0.5+SH", "CPC-SC-T½+SH (null bản đồ)"), (SH, "CMS-CPC/H+SH+G+NGRr (SH chọn tay)"), (SHCST, "SH ∧ CST (Entry 35)"),
        (CST, "CST (Entry 34)"), (CSTF, "**CMS-CPC/H+CSTF+G+NGRr (CST-F, đề xuất)**"), ("CMS-CPC/H+SH+CSTF+G+NGRr", "SH ∧ CST-F"),
        ("CMS-CPCW/H+CSTF+NGRr", "CMS-CPCW/H+CSTF+NGRr"), ("CMS-CPC/H+CSTF+G[both]+NGRr", "CST-F [both] (nhân quả)"),
        ("CMS-CPCW/H+CSTF[both]+NGRr", "CMS-CPCW/H+CSTF[both]+NGRr (nhân quả)"), ("CMS-CPC/H+CSTF+G", "CST-F không cổng +NGRr")]


def m(T, d, n, k):
    v = np.array(T.get(d, {}).get(n, []), float)
    return np.nanmean(v[:, k]) if len(v) else np.nan


def runs_over(T, dss, n, al=0.05):
    v = np.array([x for d in dss for x in T.get(d, {}).get(n, [])], float)
    return (np.mean(v[:, 1] > al), np.nanmax(v[:, 1]), len(v)) if len(v) else (np.nan, np.nan, 0)


def audit_table(f):
    R = json.load(open(f)); agg = {}
    for tag, r in R.items():
        if r is None: continue
        ds = "4s_" + ("countryside" if "countryside" in tag else ("old_town" if "old_town" in tag else "office_loop")) if tag.startswith("4s_") else tag.split("_")[0]
        for nm in ("cf", "Fmin"):
            if nm not in r: continue
            x = r[nm]; agg.setdefault((ds, nm), []).append([x.get(k) if x.get(k) is not None else np.nan for k in
                                                               ("pass_all", "pass_b0", "pass_deep", "pass_full", "pass_trunc", "eps_med")] + [r.get("eps_oracle") or np.nan])
    nm_ds = {"4s_office_loop": "4S office", "4s_old_town": "4S old town", "4s_countryside": "4S countryside", "boreas": "Boreas", "nclt": "NCLT",
             "cmu": "CMU", "nord": "Nordland", "oxford": "Oxford", "stlucia": "St Lucia"}
    L = ["### Kiểm toán (S3-T) / (S3-F): tỷ lệ đoạn off-map THẬT qua phép thử hình dạng (mục tiêu ≤ a = 0.05; nhãn chỉ để đánh giá)", "",
         "| Dataset | run | CST: tất cả / mép / sâu | CST-F: tất cả / mép / sâu | CST-F: cửa sổ đủ / bị cắt | ε CST / ε CST-F / oracle |", "|---|---|---|---|---|---|"]
    for ds in ("boreas", "nclt", "cmu", "nord", "4s_office_loop", "4s_old_town", "4s_countryside", "oxford", "stlucia"):
        a = np.array(agg.get((ds, "cf"), []), float); b = np.array(agg.get((ds, "Fmin"), []), float)
        if not len(a) or not len(b): continue
        ma, mb = np.nanmean(a, 0), np.nanmean(b, 0)
        L.append(f"| {nm_ds[ds]} | {len(b)} | {ma[0]:.3f} / {ma[1]:.3f} / {ma[2]:.3f} | **{mb[0]:.3f}** / {mb[1]:.3f} / {mb[2]:.3f} | "
                 f"{mb[3]:.3f} / {mb[4]:.3f} | {ma[5]:.1f} / {mb[5]:.1f} / {ma[6]:.1f} |")
    return L + [""], agg


def hyp(T, dss, agg):
    L = ["**Kiểm giả thuyết (đăng ký trước, Entry 36):**", ""]
    if agg:
        ok = sum(np.nanmean(np.array(agg.get((d.replace(":", "_"), "Fmin"), [[np.nan] * 7]), float)[:, 0]) <= 0.07 for d in dss)
        lo = sum(np.nanmean(np.array(agg.get((d.replace(":", "_"), "Fmin"), [[np.nan] * 7]), float)[:, 0]) <
                 np.nanmean(np.array(agg.get((d.replace(":", "_"), "cf"), [[np.nan] * 7]), float)[:, 0]) for d in dss)
        L.append(f"- H36a: tỷ lệ qua của CST-F ≤ 0.07 trên {ok}/{len(dss)} (cần ≥ 6/7); thấp hơn CST trên {lo}/{len(dss)} (cần 7/7)")
    ok = sum(m(T, d, CSTF, 1) <= 0.05 for d in dss); L.append(f"- H36b: segFAR TB của CST-F ≤ 0.05 trên {ok}/{len(dss)}")
    de = [m(T, d, CSTF, 4) - m(T, d, SH, 4) for d in dss]; ok = sum(x <= 1.0 for x in de)
    L.append(f"- H36c: sai số điều hướng CST-F − SH ≤ 1 m trên {ok}/{len(dss)} (cần ≥ 6/7): " + ", ".join(f"{E.DS_NAME[d]} {x:+.1f}" for d, x in zip(dss, de)))
    dr = [m(T, d, CSTF, 0) - m(T, d, SH, 0) for d in dss]; ok = sum(x >= -0.03 for x in dr)
    L.append(f"- H36d: recall CST-F − SH ≥ −0.03 trên {ok}/{len(dss)} (cần ≥ 4/7): " + ", ".join(f"{E.DS_NAME[d]} {x:+.3f}" for d, x in zip(dss, dr)))
    dc = [m(T, d, CSTF, 4) - m(T, d, CST, 4) for d in dss]
    L.append("- So với CST (Entry 34) về sai số điều hướng: " + ", ".join(f"{E.DS_NAME[d]} {x:+.1f} m" for d, x in zip(dss, dc)))
    return L + [""]


def main():
    L = []; agg = None
    if arg("--audit"):
        La, agg = audit_table(arg("--audit")); L += La
    if arg("--main"):
        R = E.load(arg("--main")); T = E.defaults(R); dss = [d for d in MAIN if d in T]
        n = sum(len(runs) for bd in R.values() for runs in bd.values() if True)
        L += tab_def(T, ROWS, dss, f"### Entry 36 — CST-F (seed 0–2, {n} run, α = 0.05): recall / segFAR TB / tệ nhất / sai số điều hướng (m)", oracle=False)
        L += hyp(T, dss, agg)
        L += ["Tỷ lệ run có segFAR > α / segFAR tệ nhất (mọi dataset):", "", "| Luật | run > α | tệ nhất | số run |", "|---|---|---|---|"]
        for nm, lab in ROWS[1:8]:
            a, b, c = runs_over(T, dss, nm); L.append(f"| {lab} | {a:.3f} | {b:.3f} | {c} |")
        L.append("")
    for key, ds, title in (("--oxford", "oxford", "Oxford RobotCar"), ("--stlucia", "stlucia", "St Lucia")):
        if not arg(key): continue
        R = E.load(arg(key)); T = E.defaults(R); nr = sum(len(v) for v in R.get(ds, {}).values())
        L += tab_def(T, ROWS, [ds], f"### {title} ({nr} run, 30 % lỗ): recall / segFAR TB / tệ nhất / sai số (m)", oracle=False)
        for nmr, lab in ROWS[1:6]:
            a, b, c = runs_over(T, [ds], nmr); L.append(f"- {lab}: run segFAR > α = {a:.2f}, tệ nhất {b:.3f} ({c} run)")
        L.append("")
    if arg("--n40"):
        d20, d40 = os.path.join(arg("--n40"), "n20"), os.path.join(arg("--n40"), "n40")
        if os.path.isdir(d20) and os.path.isdir(d40):
            T20, T40 = E.defaults(E.load(d20)), E.defaults(E.load(d40)); dss = [d for d in MAIN if d in T40]
            L += ["### Cửa sổ niềm tin N = 40 so với N = 20 (seed 1–9, cùng run): recall / segFAR TB / sai số (m)", "",
                  "| Luật | N | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (2 + len(dss)) + "|"]
            for nm in (SH, "CMS-CPCW/H+SH+NGRr"):
                for lab, T_ in (("20", T20), ("40", T40)):
                    L.append(f"| {nm} | {lab} | " + " | ".join(f"{m(T_, d, nm, 0):.3f} / {m(T_, d, nm, 1):.3f} / {m(T_, d, nm, 4):.1f}" for d in dss) + " |")
            ok = sum(m(T40, d, SH, 1) <= 0.05 for d in dss); up = sum(m(T40, d, SH, 0) >= m(T20, d, SH, 0) for d in dss)
            L += ["", f"- H36f: N = 40 segFAR ≤ 0.05 trên {ok}/{len(dss)} (cần {len(dss)}/{len(dss)}); recall ≥ N = 20 trên {up}/{len(dss)} (cần ≥ {len(dss) - 1}/{len(dss)}): "
                  + ", ".join(f"{E.DS_NAME[d]} {m(T40, d, SH, 0) - m(T20, d, SH, 0):+.3f}" for d in dss), ""]
    if arg("--safevpr") and os.path.exists(arg("--safevpr")):
        S = json.load(open(arg("--safevpr")))
        L += ["### So sánh trực tiếp với SafeVPR'26 trên St Lucia (giao thức của SafeVPR: không lỗ, mỗi lượt truy vấn là một điều kiện giữ ra)", "",
              "| Phương pháp | α | hợp lệ (FDR ≤ α) | FDR chấp nhận TB | TPR TB | nhãn |", "|---|---|---|---|---|---|"]
        for row in S["rows"]:
            L.append(f"| {row['method']} | {row['alpha']} | {row['valid']} | {row['fdr']:.4f} | {row['tpr']:.3f} | {row['labels']} |")
        L.append("")
    tables = "\n".join(L) + "\n"
    open(os.path.join(HERE, "e36_tables.md"), "w").write(tables); print(tables)


if __name__ == "__main__":
    main()
