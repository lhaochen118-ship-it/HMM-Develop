"""Download every file of a PUBLIC Kaggle dataset without credentials (per-file API, parallel).

Usage: python3 automation/anon_download.py <owner/slug> <out_dir> [--jobs 8] [--match REGEX]

The anonymous endpoints used here work for public datasets only:
  list:     https://www.kaggle.com/api/v1/datasets/list/<owner>/<slug>?pageToken=...
  download: https://www.kaggle.com/api/v1/datasets/download/<owner>/<slug>/<file>
Files already present with the right size are skipped (resumable).
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://www.kaggle.com/api/v1/datasets"


def get_json(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # transient proxy / API errors
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def list_files(ref):
    out, tok = [], None
    while True:
        url = f"{API}/list/{ref}" + (f"?pageToken={urllib.parse.quote(tok)}" if tok else "")
        d = get_json(url)
        for f in d.get("datasetFiles", []):
            out.append((f["name"], int(f.get("totalBytes", 0))))
        tok = d.get("nextPageTokenNullable") or d.get("nextPageToken")
        if not tok:
            return out


def fetch(ref, name, size, out_dir, tries=6):
    dst = os.path.join(out_dir, name)
    if os.path.exists(dst) and (size == 0 or os.path.getsize(dst) == size):
        return name, "skip"
    os.makedirs(os.path.dirname(dst) or out_dir, exist_ok=True)
    url = f"{API}/download/{ref}/{urllib.parse.quote(name, safe='')}"   # "/" of sub-folder paths must be sent as %2F
    for i in range(tries):
        try:
            tmp = dst + ".part"
            with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as fh:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    fh.write(b)
            if size and os.path.getsize(tmp) != size:
                raise IOError(f"size {os.path.getsize(tmp)} != {size}")
            os.replace(tmp, dst)
            return name, "ok"
        except Exception as e:
            if i == tries - 1:
                return name, f"FAIL {type(e).__name__}: {e}"
            time.sleep(2 ** i)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("out")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--match", default=None)
    a = ap.parse_args()
    files = list_files(a.ref)
    if a.match:
        files = [f for f in files if re.search(a.match, f[0])]
    tot = sum(s for _, s in files)
    print(f"{len(files)} files, {tot / 1e9:.2f} GB", flush=True)
    os.makedirs(a.out, exist_ok=True)
    nfail = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = [ex.submit(fetch, a.ref, n, s, a.out) for n, s in files]
        for k, fu in enumerate(cf.as_completed(futs), 1):
            n, st = fu.result()
            if st.startswith("FAIL"):
                nfail += 1
                print(n, st, flush=True)
            if k % 50 == 0 or k == len(files):
                print(f"{k}/{len(files)} done, {nfail} failed", flush=True)
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
