"""Tables of Entry 38 (block-shaped virtual holes: CST-JSB, CST-JSU) -> paper/e38_tables.md; hypotheses H38a-e as pre-registered in
RESEARCH_LOG.md Entry 38.
  --oc DIR        every oc_*_e38_s*.json (recursive); split into the fresh held-out (seeds 3-5), the E37 sets (seeds 0-2, 6-9; NCLT 0)
                  and Oxford (seeds 0-9)
  --audit-e37 F   e37_audit.py --lab e38 json over the E37 main + held-out runs
  --audit-new F   e37_audit.py --lab e38 json over the fresh held-out runs
Usage: build_e38_report.py --oc DIR [--audit-e37 F] [--audit-new F]"""
import sys, os, json, glob, re, shutil, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis")); sys.path.insert(0, HERE)
import e26_summary as E
from build_e28_report import tab_def

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
NEW_SEEDS = [int(x) for x in (arg("--new-seeds") or "3,4,5").split(",")]   # Entry 39: --new-seeds 10,11,12 (new hole layouts)
OUT = arg("--out") or "e38_tables.md"
MAIN = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
HOLED = ["boreas", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
E.DS_NAME.update({"oxford": "Oxford RobotCar"})
SH, CSTF, JS, SHJS = "CMS-CPC/H+SH+G+NGRr", "CMS-CPC/H+CSTF+G+NGRr", "CMS-CPC/H+CSTJS+G+NGRr", "CMS-CPC/H+SH+CSTJS+G+NGRr"
JSU, JSB, SHJSU, JSUB = "CMS-CPC/H+CSTJSU+G+NGRr", "CMS-CPC/H+CSTJSB+G+NGRr", "CMS-CPC/H+SH+CSTJSU+G+NGRr", "CMS-CPC/H+CSTJSU+G[both]+NGRr"
ROWS = [(SH, "SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay)"), (CSTF, "CST-F (Entry 36, chứng nhận)"), (JS, "CST-JS (Entry 37, lỗ ảo hành lang)"),
        (SHJS, "SH ∧ CST-JS (Entry 37, thực dụng)"), (JSB, "CST-JSB (lỗ ảo khối)"), (JSU, "**CST-JSU: hành lang ∧ khối (Entry 38, luật chính)**"),
        (SHJSU, "SH ∧ CST-JSU"), (JSUB, "CST-JSU [both] (nhân quả)"), ("CMS-CPC/H+CSTJSB+G[both]+NGRr", "CST-JSB [both]")]


def m(T, d, n, k):
    v = np.array(T.get(d, {}).get(n, []), float)
    return np.nanmean(v[:, k]) if len(v) else np.nan


def runs_over(T, dss, n, al=0.05):
    v = np.array([x for d in dss for x in T.get(d, {}).get(n, [])], float)
    return (np.mean(v[:, 1] > al), np.nanmax(v[:, 1]), len(v)) if len(v) else (np.nan, np.nan, 0)


def split(oc_dir):
    root = tempfile.mkdtemp(); sets = {}
    for f in sorted(glob.glob(os.path.join(oc_dir, "**", "oc_*_e38_s*.json"), recursive=True)):
        b = os.path.basename(f); seed = int(re.search(r"_s(\d+)\.json$", b).group(1))
        s = "oxford" if b.startswith("oc_oxford_") else ("new" if seed in NEW_SEEDS else "e37")
        d = os.path.join(root, s); os.makedirs(d, exist_ok=True); shutil.copy(f, d); sets[s] = d
    return sets


def audit(f, dss, title, need):
    A = json.load(open(f)); P = A["pooled"]; key = lambda d: d.replace(":", "_")
    rr = [(JSU, "CST-JSU"), (JSB, "CST-JSB"), (SHJSU, "SH ∧ CST-JSU"), (JSUB, "CST-JSU [both]"), (JS, "CST-JS"), (SHJS, "SH ∧ CST-JS"), (CSTF, "CST-F"), (SH, "SH")]
    L = [f"### {title}: tỷ lệ đoạn off-map THẬT có báo (start / mép / sâu; nhãn chỉ để đánh giá)", "",
         "| Luật | " + " | ".join(E.DS_NAME[d] for d in dss) + " |", "|---" * (1 + len(dss)) + "|",
         "| số đoạn | " + " | ".join("/".join(str(P[key(d)]["n"][c]) for c in ("start", "edge", "deep")) if key(d) in P else "–" for d in dss) + " |"]
    for r, lab in rr:
        cells = []
        for d in dss:
            p = P.get(key(d), {}); x = p.get(r)
            cells.append(" / ".join(f"{x[c] / p['n'][c]:.3f}" if p["n"][c] else "–" for c in ("start", "edge", "deep")) if x else "–")
        L.append(f"| {lab} | " + " | ".join(cells) + " |")
    res = {}
    for r in (JSU, JSB, JS):
        ok = 0
        for d in dss:
            p = P.get(key(d), {}); x = p.get(r)
            if x: ok += all(x[c] / p["n"][c] <= 0.07 for c in ("start", "edge", "deep") if p["n"][c] >= 50)
        res[r] = ok
    L += ["", f"- ≤ 0.07 ở mọi lớp có ≥ 50 đoạn: CST-JSU {res[JSU]}/{len(dss)} (cần ≥ {need}/{len(dss)}), CST-JSB {res[JSB]}/{len(dss)}, CST-JS {res[JS]}/{len(dss)}", ""]
    return L, res[JSU]


def main():
    L, H = [], ["**Kiểm giả thuyết (đăng ký trước, Entry 38):**", ""]
    sets = split(arg("--oc")); T = {k: E.defaults(E.load(v)) for k, v in sets.items()}
    if "new" in T:
        dn = [d for d in HOLED if d in T["new"]]; n = sum(len(T["new"][d].get(SH, [])) for d in dn)
        L += tab_def(T["new"], ROWS, dn, f"### Tập giữ ra MỚI (seed 3–5; {n} run, chưa từng dùng cho luật Entry 37/38): recall / segFAR TB / tệ nhất / sai số (m)", oracle=False)
        L += ["| Luật | run > α | tệ nhất | số run |", "|---|---|---|---|"]
        for nm, lab in ROWS:
            a, b_, c = runs_over(T["new"], dn, nm); L.append(f"| {lab} | {a:.3f} | {b_:.3f} | {c} |")
        L.append("")
    if "e37" in T:
        de = [d for d in MAIN if d in T["e37"]]; n = sum(len(T["e37"][d].get(SH, [])) for d in de)
        L += tab_def(T["e37"], ROWS, de, f"### Tập của Entry 37 (seed 0–2 + 6–9, NCLT 0; {n} run; nơi thất bại ở mép được phát hiện): recall / segFAR TB / tệ nhất / sai số (m)", oracle=False)
        L += ["| Luật | run > α | tệ nhất | số run |", "|---|---|---|---|"]
        for nm, lab in ROWS:
            a, b_, c = runs_over(T["e37"], de, nm); L.append(f"| {lab} | {a:.3f} | {b_:.3f} | {c} |")
        L.append("")
    if "oxford" in T:
        n = len(T["oxford"].get("oxford", {}).get(SH, []))
        L += tab_def(T["oxford"], ROWS, ["oxford"], f"### Oxford RobotCar (Entry 37 run, {n} run): recall / segFAR TB / tệ nhất / sai số (m)", oracle=False)
    if "new" in T and "e37" in T:
        Tn, Te = T["new"], T["e37"]; dn = [d for d in HOLED if d in Tn]; de = [d for d in MAIN if d in Te]
        H.append(f"- H38a: CST-JSU segFAR TB ≤ 0.05 trên {sum(m(Tn, d, JSU, 1) <= 0.05 for d in dn)}/{len(dn)} (giữ ra mới) và "
                 f"{sum(m(Te, d, JSU, 1) <= 0.05 for d in de)}/{len(de)} (tập E37), Oxford {m(T.get('oxford', {}), 'oxford', JSU, 1):.3f}: "
                 + ", ".join(f"{E.DS_NAME[d]} {m(Tn, d, JSU, 1):.3f}" for d in dn))
        dr = [m(Tn, d, JSU, 0) - m(Tn, d, SH, 0) for d in dn]
        H.append(f"- H38c: recall CST-JSU − SH ≥ −0.03 trên {sum(x >= -0.03 for x in dr)}/{len(dn)} (cần ≥ 4/6): " + ", ".join(f"{E.DS_NAME[d]} {x:+.3f}" for d, x in zip(dn, dr))
                 + f"; CMU CST-JSU − CST-F = {m(Tn, 'cmu', JSU, 0) - m(Tn, 'cmu', CSTF, 0):+.3f} (cần ≥ +0.05)")
        de_ = [m(Tn, d, JSU, 4) - m(Tn, d, SH, 4) for d in dn]
        H.append(f"- H38d: sai số CST-JSU − SH ≤ 1 m trên {sum(x <= 1.0 for x in de_)}/{len(dn)} (cần ≥ 5/6): " + ", ".join(f"{E.DS_NAME[d]} {x:+.1f}" for d, x in zip(dn, de_))
                 + f"; old town tập E37: CST-JSU {m(Te, '4s:old_town', JSU, 4) - m(Te, '4s:old_town', SH, 4):+.1f} m (CST-JS {m(Te, '4s:old_town', JS, 4) - m(Te, '4s:old_town', SH, 4):+.1f})")
    if "oxford" in T:
        To = T["oxford"]; H.append(f"- H38e: Oxford CST-JSU segFAR {m(To, 'oxford', JSU, 1):.3f}, recall {m(To, 'oxford', JSU, 0):.3f} vs SH {m(To, 'oxford', SH, 0):.3f}")
    for key, title, dss, need in (("--audit-e37", "Kiểm toán theo vị trí, tập E37", MAIN, 6), ("--audit-new", "Kiểm toán theo vị trí, tập giữ ra mới", HOLED, 5)):
        if arg(key) and os.path.exists(arg(key)):
            La, ok = audit(arg(key), dss, title, need); L += La
            H.append(f"- H38b ({title}): CST-JSU ≤ 0.07 ở mọi lớp ≥ 50 đoạn trên {ok}/{len(dss)} (cần ≥ {need}/{len(dss)})")
    tables = "\n".join(L + H) + "\n"
    open(os.path.join(HERE, OUT), "w").write(tables); print(tables)


if __name__ == "__main__":
    main()
