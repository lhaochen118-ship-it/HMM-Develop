#!/usr/bin/env python3
"""Generate kernel-metadata.json for a Kaggle kernel run.
Two tiers (policy: iterate on T4, reserve RTX 6000 for large-scale/large-model runs):
  t4  (default): default GPU (T4 x2) -> allocated instantly, no competition/machine_shape/docker pin.
  cpu          : no accelerator (analysis/evaluation jobs on descriptor dumps).
  rtx          : RTX PRO 6000 (96GB) via the ARC-Prize-2026 competition grant + byod docker image.
Usage: make_meta.py <dir> <id> <code_file> <comma-datasets> [tier] [comma-competitions] [docker_image]
"""
import sys, json, os

d, kid, code = sys.argv[1], sys.argv[2], sys.argv[3]
datasets = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else []
tier = (sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else "t4").lower()

meta = {
    "id": kid, "title": kid.split("/")[-1], "code_file": code,
    "language": "python", "kernel_type": "notebook", "is_private": True,
    "enable_gpu": True, "enable_tpu": False, "enable_internet": False,
    "dataset_sources": datasets,
    "competition_sources": [], "kernel_sources": [], "model_sources": [],
}

if tier == "rtx":
    meta["machine_shape"] = "NvidiaRtxPro6000"
    comps = sys.argv[6].split(",") if len(sys.argv) > 6 and sys.argv[6] else ["arc-prize-2026-arc-agi-3"]
    meta["competition_sources"] = comps
    docker = sys.argv[7] if len(sys.argv) > 7 and sys.argv[7] else \
        "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
    if docker.lower() != "none":
        meta["docker_image"] = docker
if tier == "cpu":
    meta["enable_gpu"] = False
# tier == "t4": leave machine_shape/competition/docker unset -> default GPU (instant, no queue)

os.makedirs(d, exist_ok=True)
json.dump(meta, open(os.path.join(d, "kernel-metadata.json"), "w"), indent=2)
print(f"wrote {os.path.join(d,'kernel-metadata.json')} | tier={tier.upper()}"
      + (" (RTX PRO 6000)" if tier == "rtx" else (" (CPU only)" if tier == "cpu" else " (default T4 x2, instant)")))
