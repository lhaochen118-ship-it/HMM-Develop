#!/usr/bin/env python3
"""RTX runner with clean restart: push RTX; poll; on 15-min zero-output stall, FIRST stop the stuck GPU
session (push a CPU no-op to the same kernel -> frees the GPU slot), then push RTX fresh. Up to MAXR
restarts, then surface for error inspection. Pull+decode on completion.
Usage: run_rtx2.py <rtx_dir> <stop_cpu_dir> <out_dir> [stall=900] [maxr=4] [hard=14400]"""
import sys, subprocess, time, os, json, glob
rtxdir, stopdir, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
STALL = int(sys.argv[4]) if len(sys.argv) > 4 else 900
MAXR = int(sys.argv[5]) if len(sys.argv) > 5 else 4
HARD = int(sys.argv[6]) if len(sys.argv) > 6 else 14400
kid = json.load(open(os.path.join(rtxdir, "kernel-metadata.json")))["id"]
def kg(*a):
    r = subprocess.run(["kaggle"]+list(a), capture_output=True, text=True); return (r.stdout+r.stderr).strip()
def sob(tmp):
    os.makedirs(tmp, exist_ok=True); subprocess.run(["kaggle","kernels","output",kid,"-p",tmp], capture_output=True, text=True); n=0
    for f in glob.glob(tmp+"/*.log"):
        try: recs=json.loads(open(f,encoding="utf-8",errors="ignore").read()); n+=sum(len(r.get("data","")) for r in recs if r.get("stream_name")=="stdout")
        except Exception: pass
    return n
def push(d, tag):
    o = kg("kernels","push","-p",d); line = o.splitlines()[-1] if o else ""
    print(time.strftime("%H:%M:%S"), tag, line, flush=True); return ("successfully pushed" in o.lower())
def free_and_restart():
    # stop stuck GPU session with CPU no-op, wait for it to register, then push RTX fresh
    push(stopdir, "STOP(cpu-noop):")
    for _ in range(9):
        time.sleep(20); st = kg("kernels","status",kid).lower()
        if ".complete" in st or ".running" in st: break   # cpu version took over -> GPU freed
    time.sleep(10); return push(rtxdir, "REPUSH(rtx):")

tmp = outdir+"_partial"; t0 = time.time()
push(rtxdir, "PUSH(rtx):"); time.sleep(10)
run_started = time.time(); saw = None; retries = 0; last = None; s = ""
while True:
    now = time.time(); st = kg("kernels","status",kid); low = st.lower()
    if low != last: print(time.strftime("%H:%M:%S"), st[:120], flush=True); last = low
    if ".complete" in low or ".error" in low: s = low.split(".")[-1].strip('"').strip(); break
    nb = sob(tmp)
    if nb > 0 and saw is None: saw = now; print(time.strftime("%H:%M:%S"), f"first stdout ({nb}B) - RTX running", flush=True)
    if saw is None and (now-run_started) > STALL:
        if retries < MAXR:
            retries += 1; print(time.strftime("%H:%M:%S"), f"STALL {int(now-run_started)}s 0-output -> clean restart {retries}/{MAXR}", flush=True)
            free_and_restart(); run_started = time.time(); saw = None; time.sleep(10); continue
        else:
            print("STATUS=STALL_GIVEUP (RTX persistently queued; check errors / consider T4)", flush=True); s="stall"; break
    if now-t0 > HARD: print("STATUS=HARD_TIMEOUT", flush=True); s="timeout"; break
    time.sleep(20)
os.makedirs(outdir, exist_ok=True); print(f"=== PULL ({s}) -> {outdir} ===", flush=True); print(kg("kernels","output",kid,"-p",outdir), flush=True)
for f in sorted(glob.glob(outdir+"/*.log")):
    try: recs=json.loads(open(f,encoding="utf-8",errors="ignore").read()); print("==STDOUT=="); print("".join(r.get("data","") for r in recs if r.get("stream_name")=="stdout"))
    except Exception as e: print("decode err", e)
print(f"STATUS=DONE:{s}", flush=True)
