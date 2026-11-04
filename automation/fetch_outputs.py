#!/usr/bin/env python3
"""Download the output files matching a regex from finished kernels of several accounts (each with its owner's token from
~/.kaggle/tok_<owner>), e.g. to gather caches that kernels kept in /kaggle/working before publishing them as a dataset.
Usage: fetch_outputs.py <state.json> <dest_dir> <slug_regex> --pattern REGEX [--flatten]
state.json: central_monitor state (slug -> {kid: owner/slug, ...}); --flatten moves every downloaded file into dest_dir."""
import sys, os, re, json, glob, shutil, subprocess


def main():
    a = sys.argv[1:]; st, dest, rx = a[0], a[1], re.compile(a[2])
    pat = a[a.index("--pattern") + 1]; os.makedirs(dest, exist_ok=True); n = 0
    for slug, s in sorted(json.load(open(st)).items()):
        if not rx.search(slug): continue
        owner = s["kid"].split("/")[0]; tmp = os.path.join(dest, "_" + slug); os.makedirs(tmp, exist_ok=True)
        env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser(f"~/.kaggle/tok_{owner}")).read().strip())
        r = subprocess.run(["kaggle", "kernels", "output", s["kid"], "-p", tmp, "-o", "-q", "--file-pattern", pat], capture_output=True, text=True, env=env)
        got = [f for f in glob.glob(os.path.join(tmp, "**", "*"), recursive=True) if os.path.isfile(f)]
        if "--flatten" in a:
            for f in got: shutil.move(f, os.path.join(dest, os.path.basename(f)))
            shutil.rmtree(tmp, ignore_errors=True)
        n += len(got); print(f"{slug}: {len(got)} files {(r.stderr or '').strip()[-120:]}", flush=True)
    print("total", n)


if __name__ == "__main__":
    main()
