#!/usr/bin/env python3
"""Launch the Boreas dump kernels (make_dump_boreas.py) over all accounts' GPU slots, with failover to the next account
when an account's GPU-session cap is hit. Usage: launch_boreas.py <work_dir> <seqs.txt> [per_kernel=2] [--accounts a,b]"""
import sys, os, glob, subprocess, time, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
work, seqf = sys.argv[1], sys.argv[2]; per = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 2
ACC = sorted(os.path.basename(f)[4:] for f in glob.glob(os.path.expanduser("~/.kaggle/tok_*")))
if "--accounts" in sys.argv: ACC = sys.argv[sys.argv.index("--accounts") + 1].split(",")
seqs = [s.strip() for s in open(seqf) if s.strip()]
done = {os.path.basename(f)[7:-4] for f in glob.glob(os.path.join(work, "*_out", "dump", "meta", "boreas_*.npz"))}
seqs = [s for s in seqs if s not in done]; chunks = [seqs[i:i + per] for i in range(0, len(seqs), per)]
print(f"{len(seqs)} sequences to dump in {len(chunks)} kernels over {len(ACC)} accounts", flush=True)


def job(k, ch):
    tried = []
    for j in range(len(ACC)):
        acc = ACC[(k + j) % len(ACC)]; tried.append(acc); slug = f"hmm-boreas-{k + 1}"; kd = os.path.join(work, f"k{k + 1}")
        subprocess.run([sys.executable, os.path.join(ROOT, "automation", "make_dump_boreas.py"), kd, slug, ",".join(ch), "--owner", acc], capture_output=True)
        log = os.path.join(work, f"k{k + 1}.log")
        subprocess.run([sys.executable, os.path.join(ROOT, "automation", "run_kernel.py"), kd, kd + "_out", "600", "4", "14400"], stdout=open(log, "w"), stderr=subprocess.STDOUT)
        txt = open(log).read()
        if "STATUS=PUSH_FAILED" in txt: time.sleep(20); continue
        print(f"k{k + 1} {ch} on {acc}: {txt.strip().splitlines()[-1]}", flush=True); return
    print(f"k{k + 1} {ch}: no account free ({tried})", flush=True)


th = []
for k, ch in enumerate(chunks):
    t = threading.Thread(target=job, args=(k, ch)); t.start(); th.append(t); time.sleep(5)
for t in th: t.join()
print("ALL_DONE", flush=True)
