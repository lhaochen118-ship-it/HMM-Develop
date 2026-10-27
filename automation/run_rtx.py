#!/usr/bin/env python3
"""RTX-aware monitor: ATTACH to an already-pushed kernel (no immediate re-push), apply the user's
15-min stall rule (RUNNING/queued with 0 stdout for STALL s -> re-push a fresh version = restart the
queue attempt), up to MAX_RETRIES restarts, then give up so errors can be inspected.
Usage: run_rtx.py <kernel_dir> <out_dir> [stall_s=900] [max_retries=2] [hard=10800]"""
import sys, subprocess, time, os, json, glob
kdir, outdir = sys.argv[1], sys.argv[2]
STALL = int(sys.argv[3]) if len(sys.argv) > 3 else 900
MAXR = int(sys.argv[4]) if len(sys.argv) > 4 else 2
HARD = int(sys.argv[5]) if len(sys.argv) > 5 else 10800
kid = json.load(open(os.path.join(kdir, "kernel-metadata.json")))["id"]
def kg(*a):
    r = subprocess.run(["kaggle"]+list(a), capture_output=True, text=True); return (r.stdout+r.stderr).strip()
def stdout_bytes(tmp):
    os.makedirs(tmp, exist_ok=True); subprocess.run(["kaggle","kernels","output",kid,"-p",tmp], capture_output=True, text=True)
    n = 0
    for f in glob.glob(tmp+"/*.log"):
        try: recs = json.loads(open(f, encoding="utf-8", errors="ignore").read()); n += sum(len(r.get("data","")) for r in recs if r.get("stream_name")=="stdout")
        except Exception: pass
    return n
def push(): o = kg("kernels","push","-p",kdir); print(time.strftime("%H:%M:%S"),"REPUSH:",o.splitlines()[-1] if o else "", flush=True)
tmp = outdir+"_partial"; t0 = time.time(); run_started = time.time(); saw = None; retries = 0; last = None; s = ""
print(time.strftime("%H:%M:%S"), f"ATTACH {kid} stall={STALL}s maxretries={MAXR}", flush=True)
while True:
    now = time.time(); st = kg("kernels","status",kid); low = st.lower()
    if low != last: print(time.strftime("%H:%M:%S"), st[:130], flush=True); last = low
    if ".complete" in low or ".error" in low or ".cancel" in low: s = low.split(".")[-1].strip('"').strip(); break
    nb = stdout_bytes(tmp)
    if nb > 0 and saw is None: saw = now; print(time.strftime("%H:%M:%S"), f"first stdout ({nb}B)", flush=True)
    if saw is None and (now-run_started) > STALL:
        if retries < MAXR:
            retries += 1; print(time.strftime("%H:%M:%S"), f"STALL {int(now-run_started)}s 0-output -> restart {retries}/{MAXR}", flush=True)
            push(); run_started = time.time(); saw = None; time.sleep(10); continue
        else:
            print("STATUS=STALL_GIVEUP (check for errors)", flush=True); s = "stall"; break
    if now-t0 > HARD: print("STATUS=HARD_TIMEOUT", flush=True); s = "timeout"; break
    time.sleep(20)
os.makedirs(outdir, exist_ok=True); print(f"=== PULL ({s}) -> {outdir} ===", flush=True); print(kg("kernels","output",kid,"-p",outdir), flush=True)
for f in sorted(glob.glob(outdir+"/*.log")):
    try:
        recs = json.loads(open(f, encoding="utf-8", errors="ignore").read()); txt = "".join(r.get("data","") for r in recs if r.get("stream_name")=="stdout")
        print("========== STDOUT =========="); print(txt)
    except Exception as e: print("decode err", e)
print(f"STATUS=DONE:{s}", flush=True)
