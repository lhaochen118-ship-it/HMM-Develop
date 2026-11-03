#!/usr/bin/env python3
"""Entry 37 Kaggle wave 1: job list + packing into kernels (one line per kernel, for `fanout.py --groups --build-only`).
Jobs (all on GPU sessions; every job is CPU + GPU: place chain on the CPU, route test on the GPU, cms_torch):
  F   e37_fwd.py DUMP DIR:navcache_ <ds> <desc> <seed> <k/n>      forward null with presence, one part of a run (balanced by frames)
  OX  e37_prep.py DUMP oxford <desc> <seed>                        Oxford: navcache + exact statistics + forward null (one job)
  N40 n40_run.py --one DUMP DIR:navcache_ DIR:cms_ results/cms40 DIR:topk_ DIR:tao_ <ds> <desc> <seed>   (item 3b)
Sets (pre-registered in RESEARCH_LOG Entry 37): main = seeds 0-2 x 6 holed datasets x 6 descriptors + NCLT seed 0 x 6; held-out =
seeds 6-9 x the same; design = CMU seeds 3-5 x CosPlace / NetVLAD / MegaLoc; Oxford = seeds 0-4 x 6 + held-out seeds 5-9 x SALAD /
MixVPR / DINOv2; N = 40 = seeds 1-9 x 6 holed datasets x the 5 descriptors other than CosPlace + Boreas CosPlace seeds 4-9.
Packing: longest-processing-time first over n_kernels by estimated cost (frames x per-frame cost of the job type), so every kernel
ends at about the same time. Usage: e37_wave.py <frames.json> <out_groups.txt> [n_kernels 14]"""
import sys, json, math

DESC = ["cosplace", "netvlad", "megaloc", "salad", "mixvpr", "dinov2"]
HOLED = ["cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside", "boreas"]
OX_FRAMES = 33236


def parts(fr, ds):
    t = fr[ds.replace(":", "_")]; return max(1, min(len(t["seqs"]), round(t["n"] / 5000)))


def main():
    fr = json.load(open(sys.argv[1])); out = sys.argv[2]; nk = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    jobs = []                                                         # (cost, job string)
    def fwd(ds, desc, seed):
        t = fr[ds.replace(":", "_")]; n = parts(fr, ds)
        # cost of a part ~ its frames (longest-first greedy split of the sequences, as cms_fwd.part_seqs)
        load = [0] * n
        for L in sorted(t["seqs"], reverse=True): load[load.index(min(load))] += L
        for k in range(n): jobs.append((load[k] * 1.0 + 300, f"e37_fwd.py DUMP DIR:navcache_ {ds} {desc} {seed} {k}/{n}"))
    for s in (0, 1, 2):
        for ds in HOLED:
            for d in DESC: fwd(ds, d, s)
    for d in DESC: fwd("nclt", d, 0)
    for s in (6, 7, 8, 9):
        for ds in HOLED:
            for d in DESC: fwd(ds, d, s)
    for s in (3, 4, 5):
        for d in ("cosplace", "netvlad", "megaloc"): fwd("cmu", d, s)
    units = []                                                        # Oxford: prep + its parts must share a kernel (one unit)
    NOX = 7
    for s, ds_ in [(s, d) for s in range(5) for d in DESC] + [(s, d) for s in range(5, 10) for d in ("salad", "mixvpr", "dinov2")]:
        u = [(200.0, f"e37_prep.py DUMP oxford {ds_} {s} --no-fwd")] + [(OX_FRAMES * 4.5 / NOX + 300, f"e37_fwd.py DUMP results oxford {ds_} {s} {k}/{NOX} --wait") for k in range(NOX)]
        units.append(u)
    for s in range(1, 10):
        for ds in HOLED:
            for d in DESC[1:]: jobs.append((fr[ds.replace(":", "_")]["n"] * 0.35 + 240, f"n40_run.py --one DUMP DIR:navcache_ DIR:cms_ results/cms40 DIR:topk_ DIR:tao_ {ds} {d} {s}"))
    for s in range(4, 10):
        jobs.append((fr["boreas"]["n"] * 0.35 + 240, f"n40_run.py --one DUMP DIR:navcache_ DIR:cms_ results/cms40 DIR:topk_ DIR:tao_ boreas cosplace {s}"))
    units += [[j] for j in jobs]
    units.sort(key=lambda u: -sum(c for c, _ in u)); bins = [[0.0, []] for _ in range(nk)]
    for u in units:
        b = min(bins, key=lambda x: x[0]); b[0] += sum(c for c, _ in u); b[1] += u
    jobs = [j for u in units for j in u]
    with open(out, "w") as f:                                         # inside a kernel: Oxford preps first, then longest first
        for _, js in bins: f.write(";".join(j for _, j in sorted(js, key=lambda x: (not x[1].startswith("e37_prep"), -x[0]))) + "\n")
    tot = sum(c for c, _ in jobs)
    print(f"{len(jobs)} jobs ({sum(1 for _, j in jobs if j.startswith('e37_fwd'))} fwd parts, {sum(1 for _, j in jobs if j.startswith('e37_prep'))} Oxford, "
          f"{sum(1 for _, j in jobs if j.startswith('n40'))} N=40) in {nk} kernels; cost per kernel {min(b[0] for b in bins):.0f}-{max(b[0] for b in bins):.0f} "
          f"(total {tot:.0f} frame-units), jobs per kernel {min(len(b[1]) for b in bins)}-{max(len(b[1]) for b in bins)}")


if __name__ == "__main__":
    main()
