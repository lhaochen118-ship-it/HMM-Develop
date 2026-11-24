#!/usr/bin/env python3
"""Collect the results of an HSI wave (every <run_dir>/<slug>_out/results/hsi_*.json and hsifr_*.npz) into one directory, merging
the variants of the same run (dataset, descriptor, seed) coming from several waves / tags.
Usage: hsi_collect.py <out_dir> <run_dir> [<run_dir> ...] [--tagre REGEX]
--tagre: only files whose name matches REGEX (e.g. '_(e4|e5|as)[.]' for the main protocol, '_d10' for 10 % holes): main-protocol and
holes runs share (dataset, descriptor, seed) and must NOT be merged."""
import sys, os, glob, json, shutil, re


def main():
    a = sys.argv[1:]; rx = None
    if "--tagre" in a: i = a.index("--tagre"); rx = re.compile(a[i + 1]); a = a[:i] + a[i + 2:]
    out = a[0]; os.makedirs(out, exist_ok=True); n = 0; merged = {}
    for rd in a[1:]:
        for f in glob.glob(os.path.join(rd, "*_out", "results", "hsi_*.json")):
            if rx and not rx.search(os.path.basename(f)): continue
            j = json.load(open(f)); key = (j["ds"].replace(":", "_"), j["desc"], int(j["seed"]))
            if key in merged: merged[key]["variants"].update(j["variants"])
            else: merged[key] = j
            n += 1
        for f in glob.glob(os.path.join(rd, "*_out", "results", "hsifr_*.npz")):
            if rx and not rx.search(os.path.basename(f)): continue
            shutil.copy(f, out)
    for (ds, desc, seed), j in merged.items():
        json.dump(j, open(os.path.join(out, f"hsi_{ds}_{desc}_s{seed}.json"), "w"), indent=1, default=float)
    print(f"{n} result files -> {len(merged)} runs in {out}")


if __name__ == "__main__":
    main()
