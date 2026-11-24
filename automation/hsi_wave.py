#!/usr/bin/env python3
"""(the runner of make_eval_kernel.py resolves DIR:navcache_ to a mounted cache dir and does not prepend the dump dir;
hsi_eval.find() falls back to searching /kaggle/input, so Oxford / St Lucia caches of another dataset are found too)
Build the groups file of an HSI evaluation wave (one line = one Kaggle kernel, jobs ';'-separated), LPT-packed by an
estimated cost (frames x variants; measured on the local 28-run design set: ~0.35 ms per frame per variant, 1 thread).
Usage: hsi_wave.py <groups_out> <n_kernels> <variants> [--sets main|all] [--tag t]
  main: 6 holed datasets x 6 descriptors x seeds 0-9, NCLT x 6 (seed 0), Oxford (cosplace/netvlad/megaloc 0-4, others 0-9),
        St Lucia x 6 (seeds 0-4)."""
import sys

FRAMES = {"boreas": 74394, "cmu": 21395, "nord": 13500, "4s:office_loop": 15000, "4s:old_town": 9900, "4s:countryside": 16000,
          "nclt": 33000, "oxford": 8000, "stlucia": 3000}
DESCS = ["cosplace", "netvlad", "megaloc", "dinov2", "salad", "mixvpr"]


def runs():
    out = []
    for ds in ("boreas", "cmu", "nord", "4s:office_loop", "4s:old_town", "4s:countryside"):
        for d in DESCS:
            if ds == "boreas": out += [(ds, d, "0-4"), (ds, d, "5-9")]        # long sequences: split the seeds
            else: out.append((ds, d, "0-9"))
    out += [("nclt", d, "0") for d in DESCS]
    out += [("oxford", d, "0-4" if d in ("cosplace", "netvlad", "megaloc") else "0-9") for d in DESCS]
    out += [("stlucia", d, "0-4") for d in DESCS]
    return out


def nseeds(s):
    if "-" in s: a, b = s.split("-"); return int(b) - int(a) + 1
    return len(s.split(","))


def main():
    out, K, variants = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
    nv = len(variants.split(","))
    src = lambda ds: "DIR:navcache_@hmm-e37-caches" if ds in ("oxford", "stlucia") else "DIR:navcache_@hmm-navcache-v2"   # explicit mount
    jobs = [(FRAMES[ds] * nseeds(s) * nv, f"hsi_eval.py {src(ds)} {ds} {d} {s} --variants {variants} --frames" + (f" --tag {tag}" if tag else ""))
            for ds, d, s in runs()]
    jobs.sort(reverse=True); bins = [[0, []] for _ in range(K)]
    for c, j in jobs:
        b = min(bins, key=lambda x: x[0]); b[0] += c; b[1].append(j)
    with open(out, "w") as f:
        for c, js in bins: f.write(";".join(js) + "\n")
    for c, js in bins: print(f"{len(js):3d} jobs, est {c * 0.35e-3 / 4 / 60:.1f} min on 4 cores")


if __name__ == "__main__":
    main()
