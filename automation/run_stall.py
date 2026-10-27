#!/usr/bin/env python3
"""Push a Kaggle kernel, poll to completion, auto-restart on a stall, pull+decode output.

Stall rule (user policy): if the kernel is RUNNING/queued but has produced ZERO stdout for
~STALL_SECS (default 600s = 10 min), it is queue-stuck -> push a fresh version (Kaggle runs
only the latest version, so a re-push supersedes the stuck one) and keep polling. Up to
MAX_RETRIES restarts. On a terminal status, pull output and print decoded stdout.

Usage: python run_stall.py <kernel_dir> <out_dir> [stall_secs] [max_retries] [hard_timeout_secs]
Prints a final line  STATUS=DONE:<complete|error|cancel|timeout>  the parent can grep.
"""
import sys, subprocess, time, os, json, glob

kdir = sys.argv[1]; outdir = sys.argv[2]
STALL = int(sys.argv[3]) if len(sys.argv) > 3 else 600
MAX_RETRIES = int(sys.argv[4]) if len(sys.argv) > 4 else 3
HARD = int(sys.argv[5]) if len(sys.argv) > 5 else 7200
kid = json.load(open(os.path.join(kdir, "kernel-metadata.json")))["id"]

def kg(*a):
    r = subprocess.run(["kaggle"] + list(a), capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()

def stdout_bytes(tmp):
    """Pull whatever partial output exists; return decoded stdout length (0 if none yet)."""
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(["kaggle", "kernels", "output", kid, "-p", tmp], capture_output=True, text=True)
    n = 0
    for f in glob.glob(tmp + "/*.log"):
        try:
            recs = json.loads(open(f, encoding="utf-8", errors="ignore").read())
            n += sum(len(r.get("data", "")) for r in recs if r.get("stream_name") == "stdout")
        except Exception:
            pass
    return n

def push():
    o = kg("kernels", "push", "-p", kdir)
    print(time.strftime("%H:%M:%S"), "PUSH:", o.splitlines()[-1] if o else "", flush=True)
    return "error" not in o.lower() or "pushed" in o.lower()

tmp = outdir + "_partial"
t_start = time.time()
retries = 0
if not push():
    print("STATUS=PUSH_FAILED", flush=True); sys.exit(1)
time.sleep(10)

last_status = None
run_started = time.time()      # when the current attempt began
saw_output_at = None
s = ""
while True:
    now = time.time()
    st = kg("kernels", "status", kid); low = st.lower()
    if low != last_status:
        print(time.strftime("%H:%M:%S"), st[:130], flush=True); last_status = low

    if ".complete" in low or ".error" in low or ".cancel" in low:
        s = low.split(".")[-1].strip('"').strip(); break

    nb = stdout_bytes(tmp)
    if nb > 0 and saw_output_at is None:
        saw_output_at = now
        print(time.strftime("%H:%M:%S"), f"first stdout seen ({nb} bytes)", flush=True)

    # stall: running but no stdout for STALL secs since this attempt started
    if saw_output_at is None and (now - run_started) > STALL:
        if retries < MAX_RETRIES:
            retries += 1
            print(time.strftime("%H:%M:%S"),
                  f"STALL ({int(now-run_started)}s, 0 stdout) -> restart {retries}/{MAX_RETRIES}", flush=True)
            push(); run_started = time.time(); saw_output_at = None
            time.sleep(10); continue
        else:
            print("STATUS=STALL_GIVEUP", flush=True); s = "stall"; break

    if now - t_start > HARD:
        print("STATUS=HARD_TIMEOUT", flush=True); s = "timeout"; break
    time.sleep(20)

os.makedirs(outdir, exist_ok=True)
print(f"=== PULL ({s}) -> {outdir} ===", flush=True)
print(kg("kernels", "output", kid, "-p", outdir), flush=True)
# decode + print stdout
for f in sorted(glob.glob(outdir + "/*.log")):
    try:
        recs = json.loads(open(f, encoding="utf-8", errors="ignore").read())
        txt = "".join(r.get("data", "") for r in recs if r.get("stream_name") == "stdout")
        print("========== STDOUT (" + os.path.basename(f) + ") ==========", flush=True)
        print(txt, flush=True)
    except Exception as e:
        print("decode failed:", e, flush=True)
print("FILES:", os.listdir(outdir), flush=True)
print(f"STATUS=DONE:{s}", flush=True)
