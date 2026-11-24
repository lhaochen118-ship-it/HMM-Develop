#!/usr/bin/env python3
"""Pull files matching a pattern from every FINISHED kernel of a central_monitor state file (kernels already pulled are remembered in
<dest>/.fetched), e.g. the navcache_*.npz that hsi_fresh.py --keep left in /kaggle/working/navcache_r40 of each kernel.
Usage: fetch_done.py <state.json> <dest_dir> <slug_regex> --pattern REGEX [--gap 4]"""
import sys, os, re, json, glob, shutil, subprocess, time


def main():
    a = sys.argv[1:]; st, dest, rx = a[0], a[1], re.compile(a[2]); pat = a[a.index("--pattern") + 1]
    gap = float(a[a.index("--gap") + 1]) if "--gap" in a else 4.0
    os.makedirs(dest, exist_ok=True); mf = os.path.join(dest, ".fetched")
    done = set(open(mf).read().split()) if os.path.exists(mf) else set(); n = 0
    for slug, s in sorted(json.load(open(st)).items()):
        if not rx.search(slug) or not s.get("done") or slug in done: continue
        owner = s["kid"].split("/")[0]; tmp = os.path.join(dest, "_" + slug); os.makedirs(tmp, exist_ok=True)
        env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser(f"~/.kaggle/tok_{owner}")).read().strip())
        r = subprocess.run(["kaggle", "kernels", "output", s["kid"], "-p", tmp, "-o", "-q", "--file-pattern", pat], capture_output=True, text=True, env=env)
        got = [f for f in glob.glob(os.path.join(tmp, "**", "*"), recursive=True) if os.path.isfile(f) and re.search(pat, os.path.basename(f))]
        for f in got: shutil.move(f, os.path.join(dest, os.path.basename(f)))
        shutil.rmtree(tmp, ignore_errors=True)
        if got and r.returncode == 0:
            done.add(slug); open(mf, "w").write("\n".join(sorted(done)))
        n += len(got); print(f"{slug}: {len(got)} files rc={r.returncode} {(r.stderr or '').strip()[-100:]}", flush=True); time.sleep(gap)
    print("total new", n, "| kernels fetched", len(done))


if __name__ == "__main__":
    main()
