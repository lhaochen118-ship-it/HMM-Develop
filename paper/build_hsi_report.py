"""Build paper/BAO_CAO_HSI.md (+ PDF) from the collected HSI results and the idea-1 baselines.
Usage: build_hsi_report.py <hsi_results_dir> <idea1_oc_dir> [<idea1_oc_dir> ...] [--cmp name=dir ...] [--confirm dir]
--cmp: extra result dirs (holes 10 % / 50 %, natural off-map) compared variant by variant (analysis/hsi_compare.py --all);
--confirm: the fresh confirmation set (seeds 10-12); placeholders {{CMP_MAIN}}, {{CMP_<name>}}, {{CONFIRM}}, {{ALPHA}} in the text.
Writes paper/hsi_tables_e1.md (main rule HSI, Entry 1), paper/hsi_tables_e2.md (HSI-rot-m, Entry 2) and stitches them with
paper/hsi_report_text.md (narrative, written by hand) into paper/BAO_CAO_HSI.md, then md2pdf."""
import sys, os, subprocess, json, shutil, tempfile, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def summary(rdir, bases, main, out_md):
    """run analysis/hsi_summary.py with `main` renamed to HSI (the summary script reports the variant called HSI)"""
    tmp = tempfile.mkdtemp()
    for f in glob.glob(os.path.join(rdir, "hsi_*.json")):
        j = json.load(open(f)); v = j["variants"]
        if main not in v: continue
        if main != "HSI":
            v = {("HSI" if k == main else ("HSI-e1" if k == "HSI" else k)): x for k, x in v.items()}; j["variants"] = v
        json.dump(j, open(os.path.join(tmp, os.path.basename(f)), "w"))
    subprocess.run([sys.executable, os.path.join(ROOT, "analysis", "hsi_summary.py"), tmp] + bases + ["--md", out_md, "--json", out_md[:-3] + ".json"], check=True,
                   stdout=subprocess.DEVNULL)
    shutil.rmtree(tmp)


CMPV = "HSI-rot-m-sc,HSI-V,HSI-VN,HSI-VMN,HSI-VM,geo-rm"


def compare(rdir, extra, out_md):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "analysis", "hsi_compare.py"), rdir, CMPV] + extra, capture_output=True, text=True, check=True)
    open(out_md, "w").write(r.stdout); return r.stdout


def main():
    a = sys.argv[1:]; cmp_, confirm = {}, None
    if "--confirm" in a: i = a.index("--confirm"); confirm = a[i + 1]; a = a[:i] + a[i + 2:]
    if "--cmp" in a:
        i = a.index("--cmp"); j = i + 1
        while j < len(a) and "=" in a[j]: k, v = a[j].split("=", 1); cmp_[k] = v; j += 1
        a = a[:i] + a[j:]
    rdir, bases = a[0], a[1:]
    P = os.path.join(ROOT, "paper"); T = os.path.join(P, "tables")
    summary(rdir, bases, "HSI-VN", os.path.join(P, "hsi_tables_e1.md"))
    summary(rdir, bases, "HSI", os.path.join(P, "hsi_tables_e2.md"))
    text = open(os.path.join(P, "hsi_report_text.md")).read()
    t1 = open(os.path.join(P, "hsi_tables_e1.md")).read().replace("# HSI wave summary", "### Bảng A — luật khuyến nghị HSI-VN (Entry 8–9), seed 0–9 (phát triển, so với SH trên cùng run); Ablation: mọi biến thể")
    t2 = open(os.path.join(P, "hsi_tables_e2.md")).read().replace("# HSI wave summary", "### Bảng B — cấu hình Entry 1 (cửa sổ theo frame), để đối chiếu")
    md = text.replace("{{TABLES_E1}}", t1).replace("{{TABLES_E2}}", t2)
    md = md.replace("{{CMP_MAIN}}", compare(rdir, ["--base"] + bases, os.path.join(T, "hsi_compare_main.md")))
    for k, v in cmp_.items():                                    # name=dir or name=dir@v1,v2,... (custom variant list); name ending
        d_, _, vs_ = v.partition("@")                            # in "_ho" = held-out subset only (with SH), else every run
        extra = (["--base"] + bases) if k.endswith("_ho") else ["--all"]
        if vs_:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "analysis", "hsi_compare.py"), d_, vs_] + extra, capture_output=True, text=True, check=True)
            open(os.path.join(T, f"hsi_compare_{k}.md"), "w").write(r.stdout); md = md.replace("{{CMP_%s}}" % k, r.stdout)
        else: md = md.replace("{{CMP_%s}}" % k, compare(d_, extra, os.path.join(T, f"hsi_compare_{k}.md")))
    if confirm:
        CV = "HSI-rot-m-sc,HSI-V,HSI-VM,HSI-VM-nosc,geo-rm,Xu21,Claxton24,oracle"   # variants evaluated on the seed 10-12 set (before HSI-VN existed)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "analysis", "hsi_compare.py"), confirm, CV, "--all"], capture_output=True, text=True, check=True)
        open(os.path.join(T, "hsi_compare_confirm.md"), "w").write(r.stdout); md = md.replace("{{CONFIRM}}", r.stdout)
    al = os.path.join(T, "hsi_alpha.md")
    if os.path.isfile(al): md = md.replace("{{ALPHA}}", open(al).read().replace("### α sweep (held-out runs)\n\n", ""))
    out = os.path.join(P, "BAO_CAO_HSI.md"); open(out, "w").write(md)
    subprocess.run([sys.executable, os.path.join(ROOT, "automation", "md2pdf.py"), out, out[:-3] + ".pdf"])
    print("wrote", out)


if __name__ == "__main__":
    main()
