#!/usr/bin/env python3
"""Re-run every E18 cell (dataset x descriptor x seed) of the registry with the current code on Kaggle CPU kernels
(A32 leak selection -> OURS_leak; heading fix for Boreas/Oxford). Two jobs per kernel, round-robin over CPU accounts.
Usage: dispatch_e18_wave.py <scratch dir> <wave tag> [--dry]     (writes <scratch>/cpu/jobs_<tag>.tsv)"""
import os, sys, json, subprocess, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP, TAG = sys.argv[1], sys.argv[2]; DRY = "--dry" in sys.argv
MODULE = sys.argv[sys.argv.index("--module") + 1] if "--module" in sys.argv else "hmmloc.exp.e07_motionev"
ONLY = sys.argv[sys.argv.index("--descs") + 1].split(",") if "--descs" in sys.argv else None
NOSEED = "--noseed" in sys.argv
CPU_ACC = ["quynhle07", "nguyenhoa99", "synchan5704", "anderson1202", "loinguyentran", "yeshenhi", "mucnokieu",
           "nguynduylm", "phuongnehe", "thnliu", "linhmai24", "lelynhan", "mxuanquy", "duylnng"]
VDD = "ds:nhatlong1103/vpr-descriptor-dumps=" + "+".join(["dive-vpr-nb15a-dump", "dive-vpr-nb15b-dump", "dive-vpr-nb15c-dump",
                                                          "dive-vpr-nb15d-dump", "dive-vpr-nb16a-msls", "dive-vpr-nb16b-msls"])
EXTRA = "ds:nhatlong1103/hmm-featbank-extra=hmm-k01-nordseg+hmm-k02-4s-stopgo+hmm-k03-4s-scene2+hmm-k04-4s-scene3"
OWN = "nhatlong1103/dive-vpr-nb15a-dump,nhatlong1103/dive-vpr-nb15b-dump,nhatlong1103/dive-vpr-nb16a-msls,nhatlong1103/dive-vpr-nb16b-msls"


def sources(ds, desc):
    base = ds.split(":")[0].replace("-tw", "").split("-q")[0]
    if desc == "jist":                                  # JIST dumps = owner's kernel outputs k07 (nord/rc/cmu) + k08 (4Seasons)
        return OWN + ",nhatlong1103/hmm-k07-jist,nhatlong1103/hmm-k08-jist4s", "nhatlong1103"
    if desc.startswith("seqvlad"):
        return "ds:nhatlong1103/hmm-seqvlad-frames=hmm-k12-seqvlad," + VDD, None
    if base in ("nord", "msls-cph", "msls-sf") and desc == "salad":
        return OWN, "nhatlong1103"                      # SALAD nord/msls only in the owner's kernel outputs
    if base in ("nord", "rc", "cmu", "msls-cph", "msls-sf"):
        return VDD, None
    if base.startswith("nordseg") or base in ("4s", "4s2", "4s3"):
        return EXTRA, None
    if base in ("oxford", "nclt", "stlucia", "boreas"):
        slug = {"oxford": "oxford-robotcar-vpr-dump"}.get(base, f"{base}-vpr-dump")
        return f"ds:nhatlong1103/{slug}={slug}", None
    return None, None                                    # brisbane / qut: run locally (seconds)


cells = collections.OrderedDict()
for l in open(os.path.join(ROOT, "research", "registry", "runs.jsonl")):
    r = json.loads(l)
    if r.get("experiment_id") == "E18" and r["run_id"].split("_")[1] == "E18" and r.get("status") == "ok":
        if ONLY and r["descriptor"] not in ONLY: continue
        if NOSEED and (r["dataset"].endswith("-tw") or "-q" in r["dataset"]): continue
        cells[(r["dataset"], r["descriptor"], 0 if NOSEED else r.get("seed", 1))] = 1
if MODULE.endswith("e07_motionev"):
    for d in ("netvlad", "cosplace", "salad", "megaloc", "dinov2"):
        cells[("boreas:8", d, 0)] = 1                    # Boreas: heading fix (old runs still in flight)
groups = collections.defaultdict(list); local = []
for ds, desc, seed in cells:
    src, acc = sources(ds, desc)
    if src is None:
        local.append(f"{MODULE} {ds} {desc}" + ("" if NOSEED else f" {seed}")); continue
    heavy = ds.startswith("boreas") or (desc.startswith("seqvlad") and ds.startswith("msls"))   # R15: 1 job/session
    groups[(src, acc, heavy)].append(f"{MODULE} {ds} {desc}" + ("" if NOSEED else f" {seed}"))
kernels = []
for (src, acc, heavy), jobs in groups.items():
    step = 1 if heavy else 2
    for i in range(0, len(jobs), step):
        kernels.append((src, acc, jobs[i:i + step]))
print(f"{len(cells)} cells -> {len(kernels)} kernels (+{len(local)} local)")
open(os.path.join(ROOT, "research", f"jobs_{TAG}_local.txt"), "w").write("\n".join(local) + "\n")
tsv = open(os.path.join(SP, "cpu", f"jobs_{TAG}.tsv"), "w"); k_rr = 0
for n, (src, acc, jobs) in enumerate(kernels):
    if acc is None:
        acc = CPU_ACC[k_rr % len(CPU_ACC)]; k_rr += 1
    slug = f"hmm-cpu-{TAG}-{n:03d}"; out = os.path.join(SP, "cpu", slug)
    subprocess.run([sys.executable, os.path.join(ROOT, "kaggle", "cpu", "build_cpu.py"), out, f"{acc}/{slug}", str(len(jobs)), src] + jobs,
                   check=True, capture_output=True)
    msg = "dry" if DRY else subprocess.run([os.path.join(SP, "kag.sh"), acc, "kernels", "push", "-p", out], capture_output=True, text=True).stdout.strip().splitlines()[-1][:40]
    tsv.write(f"{acc}\t{slug}\n"); tsv.flush()
    print(acc, slug, jobs, msg, flush=True)
