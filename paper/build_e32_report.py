"""Tables of the Entry 32 report (sensitivity, running time, natural near off-map on NCLT) -> paper/e32_tables.md and
paper/BAO_CAO_E32.md (= paper/e32_text.md with the tables at {{TABLES}}).
Usage: build_e32_report.py --base <E30 merged main dir> --sens <dir with one sub-dir per variant> --cf <dir with one sub-dir per
       variant> --time <dir with time_*.json> --nclt <dir with oc_nclt_* of the 8 new maps> [--nclt0 <dir with the main NCLT runs>]"""
import sys, os, glob, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "analysis")); sys.path.insert(0, HERE)
import e26_summary as E
from build_e28_report import tab_def

arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
MAIN = ["boreas", "nclt", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"]
SV = [("W5", "W = 5"), ("W20", "W = 20"), ("wr25", "w_route = 0.25"), ("wr100", "w_route = 1"), ("p005", "p = 0.005"), ("p02", "p = 0.02"),
      ("g05", "bán kính +G = 0.5 excl"), ("g2", "bán kính +G = 2 excl"), ("shd05", "dung sai SH × 0.5"), ("shd2", "dung sai SH × 2"),
      ("b01", "β cổng = 0.01"), ("b10", "β cổng = 0.10"), ("R5", "R mở khoá = 5"), ("R20", "R mở khoá = 20")]
CF = [("base", "N = 20, ρ = off_d (tính lại)"), ("N10", "N = 10"), ("N40", "N = 40"), ("rho075", "ρ = 0.75 off_d"), ("rho125", "ρ = 1.25 off_d")]


def mean_cell(T, d, n, k):
    v = np.array(T.get(d, {}).get(n, []), float)
    return v[:, k].mean() if len(v) else np.nan


def restrict(R, keys):
    """the runs of R whose (ds, desc, run) key is in keys"""
    return {ds: {de: {rk: run for rk, run in rs.items() if (ds, de, rk) in keys} for de, rs in bd.items()} for ds, bd in R.items()}


def keys_of(R):
    return {(ds, de, rk) for ds, bd in R.items() for de, rs in bd.items() for rk in rs}


def sens_table(Ts, labels, rule, ref_T, title, alpha):
    """rows = variants; cells = recall / mean segFAR / error; last columns: #datasets recall > CPC-SC-T(1/2)+SH, #segFAR <= alpha"""
    L = [title, "", "| Biến thể | " + " | ".join(E.DS_NAME[d] for d in MAIN) + " | recall > CPC-SC-T½+SH | segFAR ≤ α |",
         "|---" * (3 + len(MAIN)) + "|"]
    for key, lab in labels:
        T = Ts.get(key)
        if not T: continue
        cells, win, ok = [], 0, 0
        for d in MAIN:
            r, f, e = mean_cell(T, d, rule, 0), mean_cell(T, d, rule, 1), mean_cell(T, d, rule, 4)
            cells.append("–" if np.isnan(r) else f"{r:.3f} / {f:.3f} / {e:.1f}")
            rb = mean_cell(ref_T, d, "CPC-SC-T0.5+SH", 0)
            win += int(r > rb) if not np.isnan(r) else 0; ok += int(f <= alpha) if not np.isnan(f) else 0
        L.append(f"| {lab} | " + " | ".join(cells) + f" | {win}/{len(MAIN)} | {ok}/{len(MAIN)} |")
    return L + [""]


def main():
    L = []
    RB = E.load(arg("--base")) if arg("--base") else {}; TB = E.defaults(RB)
    for flag, labels, nm in (("--sens", SV, "lớp quyết định"), ("--cf", CF, "dựng null phản thực (seed 0, 42 run)")):
        if not arg(flag): continue
        Rs = {k: E.load(os.path.join(arg(flag), k)) for k, _ in labels if os.path.isdir(os.path.join(arg(flag), k))}
        if not Rs: continue
        common = set.intersection(*[keys_of(R) for R in Rs.values()])          # the runs every variant has (paired rows)
        Ts = {k: E.defaults(restrict(R, common)) for k, R in Rs.items()}
        Tref = E.defaults(restrict(RB, common))                               # CPC-SC-T(1/2)+SH on the same runs
        if flag == "--sens": Ts = {"default": Tref, **Ts}; labels = [("default", f"**mặc định** ({len(common)} run)")] + labels
        for rule, al in (("CMS-CPC/H+SH+G+NGRr", 0.05), ("CMS-CPCW/H+SH+NGRr", 0.05), ("CMS-CPC/H+SH+G(a=0.01)+NGRr", 0.01)):
            L += sens_table(Ts, labels, rule, Tref, f"### Độ nhạy — {nm}: {rule} (recall / segFAR TB / sai số m), α = {al}", al)
    if arg("--time"):
        rows = {}
        for f in glob.glob(os.path.join(arg("--time"), "**", "time_*.json"), recursive=True):
            t = json.load(open(f)); ds = os.path.basename(f)[5:].split("_cf")[0].rsplit("_", 1)[0]
            rows.setdefault(ds, []).append(t)
        L += ["### Thời gian chạy mỗi frame (phiên L4: top-300 trên GPU, phần còn lại một nhân CPU)", "",
              "| Dataset | frame | bản đồ | chiều | top-300 (ms/frame) | thống kê phản thực (ms/frame) | lớp quyết định (ms/frame) |", "|---|---|---|---|---|---|---|"]
        for ds, ts in sorted(rows.items()):
            ts = [t for t in ts if t.get("N", 20) == 20 and abs(t.get("rho", 0) - ts[0].get("rho", 0)) < 1e9]
            if not ts: continue
            f = lambda k: np.median([1000 * t[k] / t["n_frames"] for t in ts])
            L.append(f"| {ds} | {int(np.median([t['n_frames'] for t in ts]))} | {int(np.median([t['n_map'] for t in ts]))} | {int(np.median([t['dim'] for t in ts]))} | "
                     f"{f('topk300_s'):.2f} | {f('cms_stats_s'):.2f} | {f('rules_s'):.2f} |")
        L.append("")
    if arg("--nclt"):
        TN = E.defaults(E.load(arg("--nclt")))
        if arg("--nclt0"):
            T0 = E.defaults(E.load(arg("--nclt0")))
            if "nclt" in T0: TN["nclt:2012-01-08"] = T0["nclt"]
        dn = [d for d in E.DS_ORDER if d.startswith("nclt:") and d in TN]
        R = [("Xu21", "Xu'21 (nhãn)"), ("Claxton24", "Claxton'24 (nhãn)"), ("TAO26", "TAO'26 (nhãn)"), ("CPC-SC+CS", "CPC-SC+CS"), ("CPC-SC-T0.5+SH", "CPC-SC-T½+SH"),
             ("CMS-CPC/H+SH+G+NGRr", "**CMS-CPC/H+SH+G+NGRr**"), ("CMS-CPCW/H+SH+NGRr", "CMS-CPCW/H+SH+NGRr"),
             ("CMS-CPCW/H+SH[both]+NGRr", "CMS-CPCW/H+SH[both]+NGRr"), ("CMS-CPCW/H+SH[online]+NGRr", "CMS-CPCW/H+SH[online]+NGRr"),
             ("CMS-CPC/H+SH+G(a=0.01)+NGRr", "CMS-CPC/H+SH+G+NGRr, α = 0.01")]
        L += tab_def(TN, R, dn, "### NCLT, mỗi phiên làm bản đồ (off-map tự nhiên sát bản đồ): recall / segFAR TB / tệ nhất / sai số (m)", oracle=True)
        L += ["Gộp các bản đồ: recall / segFAR TB / segFAR tệ nhất / tỷ lệ run segFAR > α / sai số; số bản đồ recall > CPC-SC-T½+SH", "", "| Luật | gộp | thắng |", "|---|---|---|"]
        for n, lab in R:
            v = np.array([x for d in dn for x in TN[d].get(n, [])], float)
            if not len(v): continue
            al = 0.01 if "a=0.01" in n else 0.05
            w = sum(mean_cell(TN, d, n, 0) > mean_cell(TN, d, "CPC-SC-T0.5+SH", 0) for d in dn)
            L.append(f"| {lab} | {np.nanmean(v[:, 0]):.3f} / {np.nanmean(v[:, 1]):.3f} / {np.nanmax(v[:, 1]):.3f} / {np.mean(v[:, 1] > al):.2f} / {np.nanmean(v[:, 4]):.1f} | {w}/{len(dn)} |")
        L.append("")
    tables = "\n".join(L) + "\n"
    open(os.path.join(HERE, "e32_tables.md"), "w").write(tables)
    tx = os.path.join(HERE, "e32_text.md")
    if os.path.exists(tx): open(os.path.join(HERE, "BAO_CAO_E32.md"), "w").write(open(tx).read().replace("{{TABLES}}", tables))
    print(tables)


if __name__ == "__main__":
    main()
