#!/usr/bin/env python3
"""Entry 37: gather the outputs of the wave kernels (<slug>_out/results/ unpacked by central_monitor) into one result tree.
  oc/        oc_*_e37_s*.json (rules of every run)          frames/   frames_*_e37_s*.npz (per-frame default decisions)
  fwd/       fwd_<tag>_<desc>_s<seed>.npz (merged forward nulls with presence; dataset nhatlong1103/hmm-fwd-null-e37)
  n40/       oc_*_n40_s*.json, oc_*_n20_s*.json          cms40/    cms_*.npz (N = 40 statistics; dataset hmm-cms-cache-n40)
  cache/     navcache_/cms_/topk_/tao_ of the runs computed inside the kernels (Oxford, St Lucia)
  safevpr/   safevpr26_stlucia_*.npz                      logs/     <slug>/ job logs
Also checks completeness against the wave's group file (every e37_eval / n40 job must have its output) and lists the rc != 0 jobs.
Usage: e37_collect.py <out_root> <groups.txt|-> <kernel_out_dir> [...]"""
import sys, os, glob, shutil, re

out, gf, kouts = sys.argv[1], sys.argv[2], sys.argv[3:]
for d in ("oc", "frames", "fwd", "n40", "cms40", "cache", "safevpr", "logs"): os.makedirs(os.path.join(out, d), exist_ok=True)
cnt = {}
def put(f, sub):
    dst = os.path.join(out, sub, os.path.basename(f))
    if not os.path.exists(dst): shutil.copy2(f, dst)
    cnt[sub] = cnt.get(sub, 0) + 1
bad = []
for ko in kouts:
    r = os.path.join(ko, "results")
    for f in glob.glob(os.path.join(r, "oc_*_e37_s*.json")): put(f, "oc")
    for f in glob.glob(os.path.join(r, "oc_*_n[24]0_s*.json")): put(f, "n40")
    for f in glob.glob(os.path.join(r, "frames_*_e37_s*.npz")): put(f, "frames")
    for f in glob.glob(os.path.join(r, "fwd", "fwd_*.npz")): put(f, "fwd")
    for f in glob.glob(os.path.join(r, "cms40", "cms_*.npz")): put(f, "cms40")
    for f in glob.glob(os.path.join(r, "navcache_*.npz")) + glob.glob(os.path.join(r, "cms", "cms_*.npz")) + \
            glob.glob(os.path.join(r, "topk", "topk_*.npz")) + glob.glob(os.path.join(r, "tao", "tao_*.npz")): put(f, "cache")
    for f in glob.glob(os.path.join(r, "safevpr26_*.npz")): put(f, "safevpr")
    lg = os.path.join(ko, "logs")
    if os.path.isdir(lg): shutil.copytree(lg, os.path.join(out, "logs", os.path.basename(ko.rstrip("/"))), dirs_exist_ok=True)
    kl = glob.glob(os.path.join(os.path.dirname(ko.rstrip("/")), os.path.basename(ko.rstrip("/"))[:-4] + ".log"))
    for f in kl:
        for ln in open(f, errors="ignore"):
            m = re.search(r"done (.*) rc=(-?\d+)", ln)
            if m and m.group(2) != "0": bad.append((os.path.basename(ko), m.group(1)[:150], m.group(2)))
print("collected:", cnt)
if gf != "-":
    miss = []
    have_oc = {os.path.basename(f) for f in glob.glob(os.path.join(out, "oc", "*.json"))}
    have_n = {os.path.basename(f) for f in glob.glob(os.path.join(out, "n40", "*.json"))}
    for ln in open(gf):
        for j in [x.strip() for x in ln.split(";") if x.strip()]:
            w = j.split()
            if w[0] == "e37_eval.py":
                ds, desc, seed = w[-5], w[-4], w[-3]
                if f"oc_{ds.replace(':', '_')}_{desc}_e37_s{seed}.json" not in have_oc: miss.append(j)
            elif w[0] == "n40_run.py":
                ds, desc, seed = w[-3], w[-2], w[-1]
                for lab in ("n40", "n20"):
                    if f"oc_{ds.replace(':', '_')}_{desc}_{lab}_s{seed}.json" not in have_n: miss.append(j + f" [{lab}]")
    print(f"missing outputs: {len(miss)}"); [print("  ", x) for x in miss[:40]]
print(f"jobs with rc != 0: {len(bad)}"); [print("  ", *b) for b in bad[:40]]
