"""Write the --groups job file for fanout.py: one cms_dump job per (ds, desc, seed), longest-processing-time balanced
over n kernels (each kernel runs `workers` jobs in parallel). Usage: cms_jobs.py <cache_dir> <n_kernels> <workers> <out>
[--seeds 0,1,2] [--script cms_dump.py] [--extra "<args>"]"""
import sys, os, glob, numpy as np
cdir, nk, nw, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
SEEDS = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")] if "--seeds" in sys.argv else None
SCRIPT = sys.argv[sys.argv.index("--script") + 1] if "--script" in sys.argv else "cms_dump.py"
EXTRA = sys.argv[sys.argv.index("--extra") + 1] if "--extra" in sys.argv else ""
NFR = {"boreas": 76435, "nclt": 38919, "cmu": 21395, "4s_countryside": 15859, "nord": 13500, "4s_office_loop": 13563, "4s_old_town": 9849}
jobs = []
for f in glob.glob(os.path.join(cdir, "navcache_*.npz")):
    tag = os.path.basename(f)[9:-4]; base, seed = tag.rsplit("_s", 1); ds, desc = base.rsplit("_", 1)
    if SEEDS is not None and int(seed) not in SEEDS and ds != "nclt": continue
    if ds == "4s_office": ds, desc = "4s_office_loop", desc
    if "office_loop" in base: ds, desc = "4s_office_loop", base.rsplit("_", 1)[1]
    ds_arg = ds.replace("4s_", "4s:", 1) if ds.startswith("4s_") else ds
    if SCRIPT == "oc_curves.py":                     # Entry 28 evaluation: curves on seeds 0-2, default points on 3-9
        cur = int(seed) <= 2
        jobs.append((NFR[ds] * (3 if cur else 1), f"oc_curves.py CACHE {ds_arg} {desc} --seeds {seed} --jobs 1 --out-suffix _s{seed} "
                     f"{'' if cur else '--defaults-only '}{EXTRA}".strip()))
    else:
        jobs.append((NFR[ds], f"{SCRIPT} CACHE TOPK {ds_arg} {desc} --seeds {seed} --jobs 1 {EXTRA}".strip()))
jobs.sort(key=lambda x: -x[0]); load = np.zeros(nk); groups = [[] for _ in range(nk)]
for w, j in jobs:
    k = int(np.argmin(load)); groups[k].append(j); load[k] += w / nw
open(out, "w").write("\n".join(";".join(g) for g in groups if g) + "\n")
print(len(jobs), "jobs ->", sum(1 for g in groups if g), "kernels; max/min load (frames/worker):", int(load.max()), int(load.min()))
