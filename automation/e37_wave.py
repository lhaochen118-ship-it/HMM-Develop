#!/usr/bin/env python3
"""Entry 37 Kaggle wave: job list + packing into kernels (one line per kernel, for `fanout.py --groups --build-only`).
Jobs (L4 sessions; the place chain runs on the CPU, the route test on the CPU or GPU, cms_torch / CMS_DEVICE):
  F   e37_fwd.py DUMP DIR:navcache_ <ds> <desc> <seed> <k/n>      forward null with presence, one part of a run (balanced by frames)
  E   e37_eval.py DUMP DIR:navcache_ DIR:cms_ DIR:topk_ DIR:tao_ <ds> <desc> <seed> <n> --wait
                                                                    merge the n parts of the run + rules @E36,@E37 (fused wave 2)
  OX  e37_prep.py DUMP oxford <desc> <seed> --no-fwd                Oxford: navcache + exact statistics (inputs not in the caches)
  N40 n40_run.py --one DUMP DIR:navcache_ DIR:cms_ results/cms40 DIR:topk_ DIR:tao_ <ds> <desc> <seed>   (item 3b)
A RUN (all its parts + its eval job; Oxford: + its prep) is one packing unit, so every part of a run lands in the same kernel and the
run is evaluated there. Sets (RESEARCH_LOG Entry 37 pre-registration): main = seeds 0-2 x 6 holed datasets x 6 descriptors + NCLT
seed 0 x 6; held-out = seeds 6-9 x the same; design = CMU seeds 3-5 x CosPlace / NetVLAD / MegaLoc; Oxford = seeds 0-4 x 6 +
held-out seeds 5-9 x SALAD / MixVPR / DINOv2; N = 40 = seeds 1-9 x 6 holed datasets x the 5 descriptors other than CosPlace +
Boreas CosPlace seeds 4-9.
Cost model (seconds of one worker): forward part = frames x ms/frame of its dataset (costs JSON, measured on the probe kernel
e37p-1 under full load) + 60 s load; eval = per-dataset seconds; N = 40 = per-dataset seconds. Packing: longest-processing-time first
over n_kernels; inside a kernel: Oxford preps first, then longest first, eval jobs last (they wait for their parts; FIFO pool ->
no deadlock: every part an eval job waits for was taken by a worker before it).
--skip FILE: job strings already done (e.g. by the probe kernel) are left out; a run whose parts are partly done keeps only the
missing parts (the eval job then needs the done parts in the same kernel -> such runs are kept whole, only fully done runs skipped).
Usage: e37_wave.py <frames.json> <costs.json> <out_groups.txt> [n_kernels 13] [--skip done_runs.txt]"""
import sys, json

DESC = ["cosplace", "netvlad", "megaloc", "salad", "mixvpr", "dinov2"]
HOLED = ["cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside", "boreas"]
OX_FRAMES = 33236
NOX = 7
CACHES = "DUMP DIR:navcache_ DIR:cms_ DIR:topk_ DIR:tao_"


def parts(fr, ds):
    t = fr[ds.replace(":", "_")]; return max(1, min(len(t["seqs"]), round(t["n"] / 5000)))


def main():
    fr = json.load(open(sys.argv[1])); C = json.load(open(sys.argv[2])); out = sys.argv[3]
    skip = set(l.strip() for l in open(sys.argv[sys.argv.index("--skip") + 1])) if "--skip" in sys.argv else set()
    rest = [a for i, a in enumerate(sys.argv[4:], 4) if not a.startswith("--") and sys.argv[i - 1] != "--skip"]
    nk = int(rest[0]) if rest else 13
    ms = lambda ds: C["ms"][ds]                                       # ms / frame of a forward part under full load, per dataset
    units = []                                                        # [(cost, job string)]
    def run_unit(ds, desc, seed, pre=()):
        if f"{ds} {desc} {seed}" in skip: return
        t = fr[ds.replace(":", "_")] if ds != "oxford" else None
        if ds == "oxford":
            n = NOX; load = [OX_FRAMES / NOX] * n; src = "DUMP results"; ev = "DUMP results results/cms results/topk results/tao"
        else:
            n = parts(fr, ds); load = [0] * n; src = "DUMP DIR:navcache_"; ev = CACHES
            for L in sorted(t["seqs"], reverse=True): load[load.index(min(load))] += L
        u = list(pre)
        for k in range(n):
            u.append((load[k] * ms(ds) / 1e3 + 60, f"e37_fwd.py {src} {ds} {desc} {seed} {k}/{n}" + (" --wait" if ds == "oxford" else "")))
        u.append((C["eval"].get(ds.split(":")[0], 300), f"e37_eval.py {ev} {ds} {desc} {seed} {n} --wait"))
        units.append(u)
    if "--e38" in sys.argv:                                           # Entry 38: block-shaped virtual holes
        NV, CM, TK, TA, FW = ("DIR:navcache_@hmm-navcache-v2", "DIR:cms_@hmm-cms-cache-exact", "DIR:topk_@hmm-topk", "DIR:tao_@hmm-route-cache",
                              "DIR:fwd_@hmm-fwd-null-e37")
        OXC = "@hmm-e37-caches"
        def unit38(ds, d, s, corridor):
            if ds == "oxford":
                n = NOX; load = [OX_FRAMES / NOX] * n; nv = "DIR:navcache_" + OXC; ev = f"DUMP {nv} DIR:cms_{OXC} DIR:topk_{OXC} DIR:tao_{OXC}"
            else:
                n = parts(fr, ds); load = [0] * n; t = fr[ds.replace(":", "_")]; nv = NV; ev = f"DUMP {NV} {CM} {TK} {TA}"
                for L in sorted(t["seqs"], reverse=True): load[load.index(min(load))] += L
            u = [(load[k] * ms(ds) / 1e3 + 60, f"e37_fwd.py DUMP {nv} {ds} {d} {s} {k}/{n} --shape block") for k in range(n)]
            if corridor: u += [(load[k] * ms(ds) / 1e3 + 60, f"e37_fwd.py DUMP {nv} {ds} {d} {s} {k}/{n}") for k in range(n)]
            u.append((C["eval"].get(ds.split(":")[0], 300) * 1.3, f"e37_eval.py {ev} {ds} {d} {s} {n} --wait --block" + ("" if corridor else f" --corr {FW}")))
            units.append(u)
        for s in (0, 1, 2, 6, 7, 8, 9):                                 # design: the Entry 37 main + held-out runs (corridor nulls published)
            for ds in HOLED:
                for d in DESC: unit38(ds, d, s, False)
        for d in DESC: unit38("nclt", d, 0, False)
        for s, d in [(s, d) for s in range(5) for d in DESC] + [(s, d) for s in range(5, 10) for d in ("salad", "mixvpr", "dinov2")]:
            unit38("oxford", d, s, False)
        for s in (3, 4, 5):                                             # fresh held-out: seeds 3-5, never used for an Entry 37/38 rule
            for ds in HOLED:
                for d in DESC:
                    if ds == "cmu" and d in ("cosplace", "netvlad", "megaloc"): continue   # Entry 37 design runs
                    unit38(ds, d, s, True)
    elif "--holes" in sys.argv:                                       # H37h: 10 % / 50 % holes, seeds 0-2 (separate wave)
        for r in sys.argv[sys.argv.index("--holes") + 1].split(","):
            for s in (0, 1, 2):
                for ds in HOLED:
                    for d in DESC:
                        n = parts(fr, ds); load = [0] * n; t = fr[ds.replace(":", "_")]
                        for L in sorted(t["seqs"], reverse=True): load[load.index(min(load))] += L
                        u = [(load[k] * ms(ds) / 1e3 + 60, f"envrun.py @results/d{r} e37_fwd.py DUMP DIR:navcache_@d{r} {ds} {d} {s} {k}/{n}") for k in range(n)]
                        hc = f"DIR:cms_@hcms_d{r}"
                        u.append((C["eval"].get(ds.split(":")[0], 300), f"envrun.py @results/d{r} e37_eval.py DUMP DIR:navcache_@d{r} {hc} {hc} {hc} {ds} {d} {s} {n} --wait"))
                        units.append(u)
    else:
        main_sets(run_unit, units, C, skip)
    pack(units, nk, out, C)


def main_sets(run_unit, units, C, skip):
    for s in (0, 1, 2):
        for ds in HOLED:
            for d in DESC: run_unit(ds, d, s)
    for d in DESC: run_unit("nclt", d, 0)
    for s in (6, 7, 8, 9):
        for ds in HOLED:
            for d in DESC: run_unit(ds, d, s)
    for s in (3, 4, 5):
        for d in ("cosplace", "netvlad", "megaloc"): run_unit("cmu", d, s)
    for s, d in [(s, d) for s in range(5) for d in DESC] + [(s, d) for s in range(5, 10) for d in ("salad", "mixvpr", "dinov2")]:
        run_unit("oxford", d, s, pre=[(C["prep_ox"], f"e37_prep.py DUMP oxford {d} {s} --no-fwd")])
    for s in range(1, 10):
        for ds in HOLED:
            for d in DESC[1:]:
                j = f"n40_run.py --one DUMP DIR:navcache_ DIR:cms_ results/cms40 DIR:topk_ DIR:tao_ {ds} {d} {s}"
                if j not in skip: units.append([(C["n40"][ds.split(":")[0]] * (2.0 if d in ("salad", "megaloc") else 1.0), j)])
    for s in range(4, 10):
        j = f"n40_run.py --one DUMP DIR:navcache_ DIR:cms_ results/cms40 DIR:topk_ DIR:tao_ boreas cosplace {s}"
        if j not in skip: units.append([(C["n40"]["boreas"], j)])


def pack(units, nk, out, C):
    units.sort(key=lambda u: -sum(c for c, _ in u)); bins = [[0.0, []] for _ in range(nk)]
    for u in units:
        b = min(bins, key=lambda x: x[0]); b[0] += sum(c for c, _ in u); b[1] += u
    jobs = [j for u in units for j in u]
    has = lambda j, p_: p_ in j.split()[:3]                           # script name, possibly behind envrun.py VAR=... @dir
    rank = lambda j: (0 if has(j[1], "e37_prep.py") else 2 if has(j[1], "e37_eval.py") else 1, -j[0])
    with open(out, "w") as f:
        for _, js in bins: f.write(";".join(j for _, j in sorted(js, key=rank)) + "\n")
    tot = sum(c for c, _ in jobs); par = C.get("par", 46)
    cnt = lambda p: sum(1 for _, j in jobs if has(j, p))
    print(f"{len(jobs)} jobs ({cnt('e37_fwd.py')} fwd parts, {cnt('e37_eval.py')} runs evaluated, {cnt('e37_prep.py')} Oxford preps, {cnt('n40_run.py')} N=40) in "
          f"{nk} kernels; worker-seconds per kernel {min(b[0] for b in bins):.0f}-{max(b[0] for b in bins):.0f} (total {tot:.0f}; "
          f"~{max(b[0] for b in bins) / par / 60:.0f} min per kernel at {par} workers), jobs per kernel {min(len(b[1]) for b in bins)}-{max(len(b[1]) for b in bins)}")


if __name__ == "__main__":
    main()
