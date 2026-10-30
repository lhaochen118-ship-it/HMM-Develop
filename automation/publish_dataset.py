#!/usr/bin/env python3
"""Publish (create or version) a PUBLIC Kaggle dataset of nhatlong1103 from a local directory, so every account can mount
reusable artefacts (images, scores, caches) instead of recomputing them (user rule 2026-10-30).
Files are hard-linked into a staging dir (no copy); dataset-metadata.json is written there.
Usage: publish_dataset.py <src_dir> <slug> "<title 6-50 chars>" "<subtitle 20-80 chars>" [--license CC-BY-NC-SA-4.0]"""
import sys, os, json, shutil, subprocess

src, slug, title, sub = sys.argv[1:5]
lic = sys.argv[sys.argv.index("--license") + 1] if "--license" in sys.argv else "CC-BY-NC-SA-4.0"
assert 6 <= len(title) <= 50 and 20 <= len(sub) <= 80, "Kaggle limits: title 6-50, subtitle 20-80 characters"
env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser("~/.kaggle/tok_nhatlong1103")).read().strip())
stage = src.rstrip("/") + "_stage"; shutil.rmtree(stage, ignore_errors=True)
shutil.copytree(src, stage, copy_function=os.link)
json.dump({"title": title, "id": f"nhatlong1103/{slug}", "subtitle": sub, "isPrivate": False, "licenses": [{"name": lic}]},
          open(os.path.join(stage, "dataset-metadata.json"), "w"))
exists = subprocess.run(["kaggle", "datasets", "status", f"nhatlong1103/{slug}"], capture_output=True, text=True, env=env).stdout.strip().lower() == "ready"
mode = ["-r", "zip"]                                                   # Kaggle unzips directories on mount
cmd = (["kaggle", "datasets", "version", "-p", stage, "-m", "update"] if exists else ["kaggle", "datasets", "create", "-p", stage, "--public"]) + mode + ["-q"]
r = subprocess.run(cmd, capture_output=True, text=True, env=env)
print((r.stdout + r.stderr).strip()[-400:]); shutil.rmtree(stage, ignore_errors=True)
print(("versioned" if exists else "created"), f"https://www.kaggle.com/datasets/nhatlong1103/{slug}")
