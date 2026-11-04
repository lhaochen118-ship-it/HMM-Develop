#!/usr/bin/env python3
"""Gather the per-run JSONs of the Entry 10 waves (central_monitor pulls every kernel into <work>/<slug>_out/results/) into one folder
per set, so analysis/owf_summary.py can read them:
  owfb-* -> <out>/setB   (OWF, reserve seeds 25-27: owf_*_r25.json)      hsib-* -> <out>/setB_hsi (hsi_*.json, HSI-VN on the same caches)
  owfa-* -> <out>/setA   (OWF, Set A)                                     owfx-* -> <out>/abl (closed / notemper / fixq / kid)
  owfh-* -> <out>/holes  (d10 / d50)                                      owfp-* -> <out>/setA (probe jobs belong to Set A)
Frame files (fr_*.npz) are copied with --frames. Usage: owf_collect.py <work_dir> <out_dir> [--frames]"""
import sys, os, glob, shutil

MAP = {"owfb": "setB", "hsib": "setB_hsi", "owfa": "setA", "owfx": "abl", "owfh": "holes", "owfp": "setA"}


def main():
    work, out = sys.argv[1], sys.argv[2]; fr = "--frames" in sys.argv; n = {}
    for d in sorted(glob.glob(os.path.join(work, "*_out"))):
        pre = os.path.basename(d).split("-")[0]
        if pre not in MAP: continue
        dst = os.path.join(out, MAP[pre]); os.makedirs(dst, exist_ok=True)
        for f in glob.glob(os.path.join(d, "results", "*.json")) + (glob.glob(os.path.join(d, "results", "*.npz")) if fr else []):
            if os.path.basename(f).startswith(("owf_", "hsi_", "fr_")):
                shutil.copy(f, dst); n[MAP[pre]] = n.get(MAP[pre], 0) + 1
    print(n)


if __name__ == "__main__":
    main()
