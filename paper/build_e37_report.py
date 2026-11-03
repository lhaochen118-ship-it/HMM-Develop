"""Tables of Entry 37 (forward surgery of the presence evidence, exact start null: CST-JS; N = 40 on every descriptor; St Lucia with
6 descriptors) -> paper/e37_tables.md. Hypotheses H37a-g as pre-registered in RESEARCH_LOG.md Entry 37.
  --oc DIR       every oc_*_e37_s*.json of the round (recursive; split here into main / held-out / design / Oxford / St Lucia sets)
  --audit FILE   e37_audit.py json over the main + held-out runs (report rate of real off-map segments by position class)
  --n40 DIR      oc_*_n40_s*.json and oc_*_n20_s*.json (recursive) + analysis/results/e36/n40 (CosPlace, Entry 36) if given twice
  --safevpr FILE safevpr26_eval json for St Lucia (6 descriptors, ViT-L/14 verifier)
Usage: build_e37_report.py --oc DIR [--audit F] [--n40 DIR[,DIR2]] [--safevpr F]"""
import sys, os, json, glob, re, shutil, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis")); sys.path.insert(0, HERE)
import e26_summary as E
from build_e28_report import tab_def

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
MAIN = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
HOLED = ["boreas", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
E.DS_NAME.update({"stlucia": "St Lucia", "oxford": "Oxford RobotCar"})
SH, SHCST, CSTF = "CMS-CPC/H+SH+G+NGRr", "CMS-CPC/H+SH+CST+G+NGRr", "CMS-CPC/H+CSTF+G+NGRr"
JS, SHJS, JSB = "CMS-CPC/H+CSTJS+G+NGRr", "CMS-CPC/H+SH+CSTJS+G+NGRr", "CMS-CPC/H+CSTJS+G[both]+NGRr"
JSTAR, SHJSTAR, CSTJ = "CMS-CPC/H+CSTJs+G+NGRr", "CMS-CPC/H+SH+CSTJs+G+NGRr", "CMS-CPC/H+CSTJ+G+NGRr"
ROWS = [("CPC-SC-T0.5+SH", "CPC-SC-T½+SH (null bản đồ)"), (SH, "SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay)"), (SHCST, "SH ∧ CST (Entry 35)"),
        (CSTF, "CST-F (Entry 36, đề xuất có chứng nhận)"), (CSTJ, "CST-J (Entry 36)"), (JSTAR, "CST-J\\* (Entry 36, thăm dò)"),
        (SHJSTAR, "SH ∧ CST-J\\* (Entry 36, thực dụng)"), (JS, "**CST-JS: CMS-CPC/H+CSTJS+G+NGRr (Entry 37, luật chính)**"),
        (SHJS, "SH ∧ CST-JS"), (JSB, "CST-JS [both] (nhân quả)"), ("CMS-CPC/H+SH+CSTJS+G[both]+NGRr", "SH ∧ CST-JS [both]"),
        ("CMS-CPC/H+CSTJS0+G+NGRr", "CST-JS0 (cửa sổ ngắn không chứng nhận)"), ("CMS-CPC/H+CSTJSL+G+NGRr", "CST-JSL (hiện diện = phẫu thuật đầy đủ E36)"),
        ("CMS-CPC/H+CSTJF0+G+NGRr", "CST-JF0 (khởi đầu min theo bin)"), ("CMS-CPC/H+CSTJS+G", "CST-JS không +NGRr")]


def m(T, d, n, k):
    v = np.array(T.get(d, {}).get(n, []), float)
    return np.nanmean(v[:, k]) if len(v) else np.nan


def runs_over(T, dss, n, al=0.05):
    v = np.array([x for d in dss for x in T.get(d, {}).get(n, [])], float)
    return (np.mean(v[:, 1] > al), np.nanmax(v[:, 1]), len(v)) if len(v) else (np.nan, np.nan, 0)


def split(oc_dir):
    """oc files -> {set: tmp dir} by (dataset, seed): main = seeds 0-2 (NCLT 0), held = 6-9, design = CMU 3-5, oxford = 0-4,
    oxheld = 5-9, stlucia = all"""
    root = tempfile.mkdtemp(); sets = {}
    for f in sorted(glob.glob(os.path.join(oc_dir, "**", "oc_*_e37_s*.json"), recursive=True)):
        b = os.path.basename(f); seed = int(re.search(r"_s(\d+)\.json$", b).group(1))
        if b.startswith("oc_oxford_"): s = "oxford" if seed <= 4 else "oxheld"
        elif b.startswith("oc_stlucia_"): s = "stlucia"
        elif b.startswith("oc_cmu_") and 3 <= seed <= 5: s = "design"
        elif seed <= 2: s = "main"
        elif seed >= 6: s = "held"
        else: s = "other"
        d = os.path.join(root, s); os.makedirs(d, exist_ok=True); shutil.copy(f, d); sets[s] = d
    return sets


def audit_tab(f, rules, labs, dss):
    A = json.load(open(f)); P = A["pooled"]; key = lambda d: d.replace(":", "_")
    L = ["### Kiểm toán theo vị trí (H37b): tỷ lệ đoạn off-map THẬT có báo, gộp mọi run main + giữ ra (start / mép / sâu; nhãn chỉ để đánh giá)", "",
         "| Luật | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|",
         "| số đoạn (start / mép / sâu) | " + " | ".join("/".join(str(P[key(d)]["n"][c]) for c in ("start", "edge", "deep")) if key(d) in P else "–" for d in dss) + " |"]
    for r, lab in zip(rules, labs):
        cells = []
        for d in dss:
            p = P.get(key(d), {}); x = p.get(r)
            cells.append(" / ".join(f"{x[c] / p['n'][c]:.3f}" if p["n"][c] else "–" for c in ("start", "edge", "deep")) if x else "–")
        L.append(f"| {lab} | " + " | ".join(cells) + " |")
    ok = 0; lo = 0
    for d in dss:
        p = P.get(key(d), {}); x = p.get(JS); y = p.get(JSTAR)
        if not x: continue
        rates = [x[c] / p["n"][c] for c in ("start", "edge", "deep") if p["n"][c] >= 50]
        ok += all(v <= 0.07 for v in rates)
        if y and p["n"]["edge"]: lo += x["edge"] / p["n"]["edge"] < y["edge"] / p["n"]["edge"]
    L += ["", f"- H37b: CST-JS ≤ 0.07 ở mọi lớp có ≥ 50 đoạn trên {ok}/{len(dss)} (cần ≥ 6/7); thấp hơn CST-J\\* ở mép trên {lo}/{len(dss)} (cần ≥ 5/7)", ""]
    return L


def main():
    L = []
    sets = split(arg("--oc")) if arg("--oc") else {}
    T = {k: E.defaults(E.load(v)) for k, v in sets.items()}
    if "main" in T:
        dss = [d for d in MAIN if d in T["main"]]; n = sum(len(v) for d in dss for v in [T["main"][d].get(SH, [])])
        L += tab_def(T["main"], ROWS, dss, f"### Entry 37 — tập chính (seed 0–2, NCLT seed 0; {n} run, α = 0.05): recall / segFAR TB / tệ nhất / sai số điều hướng (m)", oracle=False)
        L += ["Tỷ lệ run có segFAR > α / segFAR tệ nhất:", "", "| Luật | run > α | tệ nhất | số run |", "|---|---|---|---|"]
        for nm, lab in ROWS[1:11]:
            a, b, c = runs_over(T["main"], dss, nm); L.append(f"| {lab} | {a:.3f} | {b:.3f} | {c} |")
        L.append("")
    if "held" in T:
        dh = [d for d in HOLED if d in T["held"]]; n = sum(len(T["held"][d].get(SH, [])) for d in dh)
        L += tab_def(T["held"], ROWS, dh, f"### Tập giữ ra (seed 6–9; {n} run, chưa từng dùng cho luật CST nào): recall / segFAR TB / tệ nhất / sai số (m)", oracle=False)
        L += ["| Luật | run > α | tệ nhất | số run |", "|---|---|---|---|"]
        for nm, lab in ROWS[1:11]:
            a, b, c = runs_over(T["held"], dh, nm); L.append(f"| {lab} | {a:.3f} | {b:.3f} | {c} |")
        L.append("")
    for key, title in (("design", "Run thiết kế (CMU seed 3–5 × CosPlace / NetVLAD / MegaLoc; KHÔNG tính cho giả thuyết)"),
                       ("oxford", "Oxford RobotCar seed 0–4 × 6 descriptor"), ("oxheld", "Oxford RobotCar giữ ra: seed 5–9 × SALAD / MixVPR / DINOv2"),
                       ("stlucia", "St Lucia (6 descriptor × seed 0–4; 30 % lỗ)")):
        if key not in T: continue
        dd = [d for d in MAIN + ["oxford", "stlucia"] if d in T[key]]; n = sum(len(T[key][d].get(SH, [])) for d in dd)
        L += tab_def(T[key], ROWS, dd, f"### {title} ({n} run): recall / segFAR TB / tệ nhất / sai số (m)", oracle=False)
        for nm, lab in (ROWS[1], ROWS[3], ROWS[6], ROWS[7], ROWS[8]):
            a, b, c = runs_over(T[key], dd, nm); L.append(f"- {lab}: run segFAR > α = {a:.2f}, tệ nhất {b:.3f} ({c} run)")
        L.append("")
    # ---- hypotheses
    H = ["**Kiểm giả thuyết (đăng ký trước, Entry 37):**", ""]
    if "main" in T:
        Tm = T["main"]; dss = [d for d in MAIN if d in Tm]
        okm = sum(m(Tm, d, JS, 1) <= 0.05 for d in dss)
        oko = [m(T[k], "oxford", JS, 1) <= 0.05 for k in ("oxford", "oxheld") if k in T]
        okh = sum(m(T["held"], d, JS, 1) <= 0.05 for d in HOLED if "held" in T and d in T["held"])
        H.append(f"- H37a: segFAR TB của CST-JS ≤ 0.05 trên {okm}/{len(dss)} (tập chính), Oxford {oko} (chính, giữ ra), giữ ra {okh}/6: "
                 + ", ".join(f"{E.DS_NAME[d]} {m(Tm, d, JS, 1):.3f}" for d in dss)
                 + (" | giữ ra: " + ", ".join(f"{E.DS_NAME[d]} {m(T['held'], d, JS, 1):.3f}" for d in HOLED if d in T["held"]) if "held" in T else ""))
        cm = [m(T[k], "cmu", JS, 0) - m(T[k], "cmu", CSTF, 0) for k in ("main", "held") if k in T]
        dr = [m(Tm, d, JS, 0) - m(Tm, d, SH, 0) for d in dss]
        H.append(f"- H37c: recall CST-JS − CST-F trên CMU (chính, giữ ra) = {', '.join(f'{x:+.3f}' for x in cm)} (cần ≥ +0.05); CST-JS − SH ≥ −0.03 trên "
                 f"{sum(x >= -0.03 for x in dr)}/{len(dss)} (cần ≥ 4/7): " + ", ".join(f"{E.DS_NAME[d]} {x:+.3f}" for d, x in zip(dss, dr)))
        de = [m(Tm, d, JS, 4) - m(Tm, d, SH, 4) for d in dss]
        H.append(f"- H37d: sai số điều hướng CST-JS − SH ≤ 1 m trên {sum(x <= 1.0 for x in de)}/{len(dss)} (cần ≥ 5/7): "
                 + ", ".join(f"{E.DS_NAME[d]} {x:+.1f}" for d, x in zip(dss, de)))
        for k in ("oxford", "oxheld"):
            if k in T:
                To = T[k]; H.append(f"- H37e ({'Oxford seed 0–4' if k == 'oxford' else 'Oxford giữ ra'}): CST-JS segFAR {m(To, 'oxford', JS, 1):.3f}, recall {m(To, 'oxford', JS, 0):.3f} "
                                    f"vs SH {m(To, 'oxford', SH, 0):.3f} (Δ {m(To, 'oxford', JS, 0) - m(To, 'oxford', SH, 0):+.3f}; cần ≥ −0.03)")
        if "stlucia" in T:
            Ts = T["stlucia"]; H.append(f"- H37g (St Lucia): CST-JS segFAR {m(Ts, 'stlucia', JS, 1):.3f}, recall {m(Ts, 'stlucia', JS, 0):.3f} vs SH {m(Ts, 'stlucia', SH, 0):.3f}")
    if arg("--audit") and os.path.exists(arg("--audit")):
        rr = [JS, SHJS, JSB, JSTAR, SHJSTAR, CSTJ, CSTF, SH]; lab = ["CST-JS", "SH ∧ CST-JS", "CST-JS [both]", "CST-J\\*", "SH ∧ CST-J\\*", "CST-J", "CST-F", "SH"]
        L += audit_tab(arg("--audit"), rr, lab, [d for d in MAIN])
    if arg("--n40"):
        dirs = arg("--n40").split(","); root = tempfile.mkdtemp()
        for lab_ in ("n20", "n40"):
            os.makedirs(os.path.join(root, lab_), exist_ok=True)
            for d in dirs:
                for f in glob.glob(os.path.join(d, "**", f"oc_*_{lab_}_s*.json"), recursive=True): shutil.copy(f, os.path.join(root, lab_))
        R20, R40 = E.load(os.path.join(root, "n20")), E.load(os.path.join(root, "n40"))
        descs = sorted({desc for bd in R40.values() for desc in bd})
        dss = [d for d in HOLED if d in R40]
        L += ["### Cửa sổ niềm tin N = 40 so với N = 20 (seed 1–9; luật SH CMS-CPC/H+SH+G+NGRr): recall N20 → N40 / segFAR N40", "",
              "| Descriptor | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|"]
        pooled20, pooled40 = {}, {}
        for desc in descs:
            sub = lambda R: {ds: {desc: R[ds][desc]} for ds in R if desc in R[ds]}
            T20, T40 = E.defaults(sub(R20)), E.defaults(sub(R40))
            L.append(f"| {desc} | " + " | ".join(f"{m(T20, d, SH, 0):.3f} → {m(T40, d, SH, 0):.3f} / {m(T40, d, SH, 1):.3f}" for d in dss) + " |")
            for d in dss:
                pooled20.setdefault(d, []).extend(T20.get(d, {}).get(SH, [])); pooled40.setdefault(d, []).extend(T40.get(d, {}).get(SH, []))
        P20 = {d: {SH: v} for d, v in pooled20.items()}; P40 = {d: {SH: v} for d, v in pooled40.items()}
        L.append("| **gộp** | " + " | ".join(f"{m(P20, d, SH, 0):.3f} → {m(P40, d, SH, 0):.3f} / {m(P40, d, SH, 1):.3f}" for d in dss) + " |")
        okv = all(m(E.defaults({ds: {desc: R40[ds][desc]} for ds in R40 if desc in R40[ds]}), d, SH, 1) <= 0.05 for desc in descs for d in dss
                  if d in R40 and desc in R40[d])
        up = sum(m(P40, d, SH, 0) >= m(P20, d, SH, 0) for d in dss)
        H.append(f"- H37f: N = 40 segFAR TB ≤ 0.05 ở mọi (dataset, descriptor): {okv}; recall gộp N40 ≥ N20 trên {up}/{len(dss)} (cần ≥ 5/6)")
        L.append("")
    if arg("--safevpr") and os.path.exists(arg("--safevpr")):
        S = json.load(open(arg("--safevpr")))
        L += ["### So sánh trực tiếp với SafeVPR'26 trên St Lucia (verifier DINOv2 ViT-L/14 như bài báo; 30 % lỗ; FDR / TPR của tập được chấp nhận)", "",
              "| Descriptor | Phương pháp | α | hợp lệ | FDR TB | TPR TB | recall TB | nhãn |", "|---|---|---|---|---|---|---|---|"]
        for row in S["rows"]:
            a = row["alpha"] if "SafeVPR" in row["method"] else "–"
            L.append(f"| {row.get('desc', '')} | {row['method']} | {a} | {row['valid']} | {row['fdr']:.4f} | {row['tpr']:.3f} | {row.get('recall', float('nan')):.3f} | {row['labels']} |")
        L.append("")
    tables = "\n".join(L + H) + "\n"
    open(os.path.join(HERE, "e37_tables.md"), "w").write(tables); print(tables)


if __name__ == "__main__":
    main()
