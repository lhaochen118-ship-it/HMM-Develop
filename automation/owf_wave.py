#!/usr/bin/env python3
"""Job groups (one line = one Kaggle CPU kernel, jobs ';'-separated) for the idea-2 OWF wave (RESEARCH_LOG Entry 1).
Each job is one run (dataset, descriptor, seed) of analysis/owf.py on the public navcache (holes, odometry, labels) + dumps.
Packing: LPT over estimated run cost (ms/frame measured on the design runs x query frames x descriptor factor), PER_KERNEL
parallel jobs per session; the most expensive groups first.
Usage: owf_wave.py <out_groups.txt> [--set main|abl|holes|design|r19|r19hsi|all] [--kernels N] [--par 4]
  r19: OWF on the reserve decision set (seeds 25-27, caotienminh1/hmm-navcache-r19; Entry 10 Set B);
  r19hsi: HSI-VN / HSI-VMN / HSI-rot-m-sc / oracle (hsi_eval.py, cache only: build with --nodumps) on the same runs."""
import sys, json

DS = {  # name -> (cache token, frames, ms/frame of the 3-filter OWF on one core, seeds of the held-out set)
    "boreas": ("DIR:navcache_@hmm-navcache-v2", 76435, 11.0, range(1, 10)),
    "cmu": ("DIR:navcache_@hmm-navcache-v2", 21395, 10.0, range(1, 10)),
    "nord": ("DIR:navcache_@hmm-navcache-v2", 13500, 2.5, range(1, 10)),
    "4s:office_loop": ("DIR:navcache_@hmm-navcache-v2", 13563, 5.0, range(1, 10)),
    "4s:countryside": ("DIR:navcache_@hmm-navcache-v2", 15859, 12.0, range(1, 10)),
    "4s:old_town": ("DIR:navcache_@hmm-navcache-v2", 9849, 11.0, range(1, 10)),
    "nclt": ("DIR:navcache_@hmm-navcache-v2", 38919, 11.0, range(0, 1)),
    "oxford": ("DIR:navcache_@hmm-e37-caches", 12000, 10.0, None),        # seeds as published (cosplace/megaloc/netvlad 0-4, others 0-9)
    "stlucia": ("DIR:navcache_@hmm-e37-caches", 6000, 10.0, range(0, 5)),
}
DESCS = ["cosplace", "netvlad", "megaloc", "salad", "mixvpr", "dinov2"]
DFAC = {"cosplace": 1.0, "dinov2": 1.0, "netvlad": 1.1, "mixvpr": 1.1, "megaloc": 1.25, "salad": 1.25}
OX_SEEDS = {"cosplace": range(5), "megaloc": range(5), "netvlad": range(5), "dinov2": range(10), "mixvpr": range(10), "salad": range(10)}
EXTRA_DS = ("nhatlong1103/hmm-navcache-v2,nhatlong1103/hmm-e37-caches,nhatlong1103/nclt-vpr-dump,nhatlong1103/oxford-robotcar-vpr-dump,"
            "nhatlong1103/stlucia-vpr-dump,nhatlong1103/hmm-navcache-holes")


def job(ds, desc, seed, cache=None, flags="", tag=""):
    t = ds.replace(":", "_") + f"_{desc}_s{seed}" + (f"_{tag}" if tag else "")
    c = cache or DS[ds][0]
    return (f"owf.py {c} DUMP {ds} {desc} {seed} --out results/owf_{t}.json --frames results/fr_{t} {flags}".strip(),
            DS[ds][1] * DS[ds][2] * DFAC[desc] / 1e3 * (1.0 if "--qx" not in flags else 0.4))


def main():
    out = sys.argv[1]; opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    which = opt("--set", "main"); nk = int(opt("--kernels", "30")); par = int(opt("--par", "4"))
    J = []
    if which in ("main", "all"):          # pre-registered held-out set (Entry 1 §4): seeds 1-9 (NCLT: the 5 other descriptors), Oxford, St Lucia
        for ds, (_, _, _, seeds) in DS.items():
            for desc in DESCS:
                ss = OX_SEEDS[desc] if ds == "oxford" else seeds
                for s in ss:
                    if ds == "nclt" and desc == "cosplace": continue
                    J.append(job(ds, desc, s))
    if which in ("design", "all"):        # seed 0 of every descriptor (cosplace / netvlad seed 0 = design set)
        for ds in ("boreas", "cmu", "nord", "4s:office_loop", "4s:countryside", "4s:old_town"):
            for desc in DESCS: J.append(job(ds, desc, 0))
        J.append(job("nclt", "cosplace", 0))
    if which in ("abl", "all"):           # ablations (secondary): seeds 1-2, cosplace + megaloc, 7 datasets
        for ds in ("boreas", "cmu", "nord", "4s:office_loop", "4s:countryside", "4s:old_town", "nclt"):
            for desc in ("cosplace", "megaloc"):
                for s in ((0,) if ds == "nclt" else (1, 2)):
                    J.append(job(ds, desc, s, flags="--closed", tag="closed"))
                    J.append(job(ds, desc, s, flags="--ellx 0", tag="notemper"))
                    J.append(job(ds, desc, s, flags="--qx 0.02", tag="fixq"))
                    J.append(job(ds, desc, s, flags="--pkid 1e-4", tag="kid"))
    if which == "r19":
        for ds in ("boreas", "cmu", "nord", "4s:office_loop", "4s:countryside", "4s:old_town"):
            for desc in DESCS:
                for sd in (25, 26, 27): J.append(job(ds, desc, sd, cache="DIR:navcache_@hmm-navcache-r19", tag="r25"))
    if which == "r19hsi":
        fr = {"boreas": 74394, "cmu": 21395, "nord": 13500, "4s:office_loop": 15000, "4s:old_town": 9900, "4s:countryside": 16000}
        for ds in fr:
            for desc in DESCS:
                for sd in (25, 26, 27):
                    J.append((f"hsi_eval.py DIR:navcache_@hmm-navcache-r19 {ds} {desc} {sd} --variants HSI-VN,HSI-VMN,HSI-rot-m-sc,oracle --frames --tag r25",
                              fr[ds] * 4 * 0.35e-3))
    if which.startswith("fresh:"):        # another fresh pool, e.g. fresh:49-54 (caches kept in navcache_r<first seed>)
        a, b = [int(x) for x in which.split(":")[1].split("-")]
        cost = {"boreas": 95, "4s:countryside": 47, "cmu": 20, "nord": 12, "4s:office_loop": 12, "4s:old_town": 10, "oxford": 6, "stlucia": 4}
        for ds, c in cost.items():
            for desc in DESCS:
                for sd in range(a, b + 1):
                    J.append((f"hsi_fresh.py {ds} {desc} {sd} 1 --keep navcache_r{a} --variants HSI-VN,HSI-VMN,oracle --tag r{a}", c * 60 * DFAC[desc]))
    if which == "fresh":                  # AUTOLOOP fresh pool: seeds 40-48 of 8 holed datasets, caches kept in /kaggle/working/navcache_r40,
        # HSI-VN / HSI-VMN / HSI-rot-m-sc / oracle evaluated on the same caches (hsi_fresh.py; the runner prepends the dump dir)
        cost = {"boreas": 95, "4s:countryside": 47, "cmu": 20, "nord": 12, "4s:office_loop": 12, "4s:old_town": 10, "oxford": 6, "stlucia": 4}
        for ds, c in cost.items():
            for desc in DESCS:
                for sd in range(40, 49):
                    J.append((f"hsi_fresh.py {ds} {desc} {sd} 1 --keep navcache_r40 --variants HSI-VN,HSI-VMN,HSI-rot-m-sc,oracle --tag r40", c * 60 * DFAC[desc]))
    if which.startswith("fresh_owf"):     # AUTOLOOP fresh test: OWF + OWF->HSI hybrid on the fresh pool (seeds of the group, e.g. fresh_owf:40-42)
        # --pool r49: cache dataset hmm-navcache-r49 (default r40); --bank: also the odometry-scale-bank OWF (tag r<a>S, 6 filters);
        # --hsiframes: HSI report masks for owf_union.py
        a, b = which.split(":")[1].split("-"); modes = opt("--modes", "xms0.9_8:HSI-VN"); pool = opt("--pool", "r40")
        hf = " --hsiframes" if "--hsiframes" in sys.argv else ""
        cfgs = [(f"r{a}", "", 1.0)] + ([(f"r{a}S", " --qx 0.005,0.02 --scales 0.97,1.0,1.03", 2.5)] if "--bank" in sys.argv else [])
        if "--banks" in sys.argv:          # e.g. --banks "S:0.97,1.0,1.03;S5:0.94,0.97,1.0,1.03,1.06" (tag suffix:scales; qx 0.005,0.02)
            cfgs = [] if "--noplain" in sys.argv else cfgs[:1]
            for bk in opt("--banks", "").split(";"):
                suf, _, sc = bk.partition(":"); cfgs.append((f"r{a}{suf}", f" --qx 0.005,0.02 --scales {sc}", 0.85 * len(sc.split(","))))
        for ds in ("boreas", "cmu", "nord", "4s:office_loop", "4s:countryside", "4s:old_town", "oxford", "stlucia"):
            for desc in DESCS:
                for sd in range(int(a), int(b) + 1):
                    for tg, fl, cm in cfgs:
                        J.append((f"owf_hsi_job.py DIR:navcache_@hmm-navcache-{pool} DUMP {ds} {desc} {sd} --tag {tg} --modes {modes}{hf}{fl}",
                                  DS[ds][1] * DS[ds][2] * DFAC[desc] / 1e3 * 1.3 * cm))
    if which.startswith("inc:"):          # 2026-11-05: the incumbent pipeline (OWF S5 bank on the GPU -> OWF-H HSI-VN / VMN masks) on a named
        # set: inc:setA (development: seeds 1-9 of the 6 holed datasets, NCLT 5 desc, Oxford, St Lucia), inc:holes (10 % / 50 % holes, seeds
        # 0-2), inc:natural (4Seasons cross-scene, natural off-map), inc:nclt (NCLT seed 0, 6 desc); several sets: inc:setA+holes+...
        bank = " --qx 0.005,0.02 --scales 0.94,0.97,1.0,1.03,1.06 --engine torch"; tg = opt("--tag", "S5")
        hm = " --modes xms0.9_16:HSI-VN,HSI-VMN --hsiframes"; gpu_fac = 0.08          # GPU engine: ~1/12 of the CPU cost per frame (measured)
        def ij(cache, ds, desc, sd, tag):
            return (f"owf_hsi_job.py {cache} DUMP {ds} {desc} {sd} --tag {tag}{hm}{bank}", DS.get(ds, ("", 16000, 10.0))[1] * 10.0 * DFAC[desc] / 1e3 * gpu_fac + DS.get(ds, ("", 16000))[1] * 4e-3)
        for part in which.split(":")[1].split("+"):
            if part == "setA":
                for ds, (c_, _, _, seeds) in DS.items():
                    for desc in DESCS:
                        ss = OX_SEEDS[desc] if ds == "oxford" else (range(0, 1) if ds == "nclt" else seeds)
                        for s in ss:
                            if ds == "nclt": continue                                  # NCLT: own part below (all 6 descriptors)
                            J.append(ij(c_, ds, desc, s, f"a{tg}"))
            if part in ("nclt", "setA"):
                for desc in DESCS: J.append(ij("DIR:navcache_@hmm-navcache-v2", "nclt", desc, 0, f"n{tg}"))
            if part == "holes":
                for dr in ("d10", "d50"):
                    for ds in ("boreas", "cmu", "nord", "4s:office_loop", "4s:countryside", "4s:old_town"):
                        for desc in DESCS:
                            for s in (0, 1, 2): J.append(ij(f"DIR:navcache_@{dr}", ds, desc, s, f"{dr}{tg}"))
            if part == "natural":
                sc = ("office_loop", "old_town", "countryside")
                for a_ in sc:
                    for b_ in sc:
                        if a_ == b_: continue
                        for desc in DESCS:
                            DS.setdefault(f"4sx:{a_}{b_}", ("", 15000, 10.0, None))
                            J.append(ij("DIR:navcache_@hmm-natural-cache", f"4sx:{a_}{b_}", desc, 0, f"x{tg}"))
    if which in ("holes", "all"):         # hole ratio 10 % / 50 % (hmm-navcache-holes, seeds 0-2, 6 datasets x 6 descriptors)
        for dr in ("d10", "d50"):
            for ds in ("boreas", "cmu", "nord", "4s:office_loop", "4s:countryside", "4s:old_town"):
                for desc in DESCS:
                    for s in (0, 1, 2):
                        J.append(job(ds, desc, s, cache=f"DIR:navcache_@{dr}", tag=dr))
    J.sort(key=lambda x: -x[1]); bins = [[0.0, []] for _ in range(nk)]
    for j, c in J:                        # LPT on par lanes per kernel: kernel load = sum / par (approx.)
        b = min(bins, key=lambda x: x[0]); b[0] += c / par; b[1].append(j)
    bins = [b for b in sorted(bins, key=lambda x: -x[0]) if b[1]]
    open(out, "w").write("\n".join(";".join(b[1]) for b in bins) + "\n")
    print(f"{len(J)} jobs -> {len(bins)} kernels; est. load per kernel (min): max {bins[0][0] / 60:.0f}, min {bins[-1][0] / 60:.0f}; "
          f"total {sum(c for _, c in J) / 3600:.1f} core-h; extra datasets: {EXTRA_DS}")


if __name__ == "__main__":
    main()
