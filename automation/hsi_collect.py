#!/usr/bin/env python3
"""Collect the results of an HSI wave (every <run_dir>/<slug>_out/results/hsi_*.json and hsifr_*.npz) into one directory, merging
the variants of the same run (dataset, descriptor, seed) coming from several waves / tags.
Usage: hsi_collect.py <out_dir> <run_dir> [<run_dir> ...]"""
import sys, os, glob, json, shutil


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True); n = 0; merged = {}
    for rd in sys.argv[2:]:
        for f in glob.glob(os.path.join(rd, "*_out", "results", "hsi_*.json")):
            j = json.load(open(f)); key = (j["ds"].replace(":", "_"), j["desc"], int(j["seed"]))
            if key in merged: merged[key]["variants"].update(j["variants"])
            else: merged[key] = j
            n += 1
        for f in glob.glob(os.path.join(rd, "*_out", "results", "hsifr_*.npz")):
            shutil.copy(f, out)
    for (ds, desc, seed), j in merged.items():
        json.dump(j, open(os.path.join(out, f"hsi_{ds}_{desc}_s{seed}.json"), "w"), indent=1, default=float)
    print(f"{n} result files -> {len(merged)} runs in {out}")


if __name__ == "__main__":
    main()
