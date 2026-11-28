#!/usr/bin/env python3
"""Single central monitor for a set of Kaggle kernels (Ops Plan v1.3 §3.3; guide section 7.3).
Usage: monitor.py <jobs.json> <kag_wrapper>     (kag_wrapper: `<wrapper> <account> <kaggle args...>`, token never printed)
jobs.json: [{"slug": "hmm-l4-k09", "dir": "<kernel dir>", "accounts": ["acc1", "acc2"], "tier": "l4"|"t4",
             "out": "<dir for outputs>", "max_queue_min": 8}]
Rules: QUEUED without progress > max_queue_min -> delete + re-push (next account in the list if any, <= 5 attempts);
RUNNING -> wait; COMPLETE/ERROR -> download output + log once. One status call per job per minute (API is IP-limited)."""
import sys, json, time, subprocess, os

jobs = json.load(open(sys.argv[1])); KAG = sys.argv[2]
T0 = time.time()


def kag(acc, *args, timeout=600):
    r = subprocess.run([KAG, acc, *args], capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr).strip()


def push(j):
    acc = j["accounts"][min(j["attempt"], len(j["accounts"]) - 1)]
    mp = os.path.join(j["dir"], "kernel-metadata.json"); m = json.load(open(mp))
    m["id"] = f"{acc}/{j['slug']}"; json.dump(m, open(mp, "w"), indent=2)
    out = kag(acc, "kernels", "push", "-p", j["dir"])
    j.update(acc=acc, pushed=time.time(), state="pushed", last_status=None)
    print(f"[{(time.time()-T0)/60:5.1f}m] push {m['id']} attempt {j['attempt']}: {out.splitlines()[-1][:120] if out else ''}", flush=True)


for j in jobs:
    j.setdefault("attempt", 0); j.setdefault("max_queue_min", 8 if j.get("tier") == "l4" else 10)
    if j.get("already_pushed"):
        j.update(acc=j["accounts"][0], pushed=time.time(), state="pushed", last_status=None)
    else:
        push(j)
while any(j["state"] not in ("done", "gaveup") for j in jobs):
    time.sleep(60)
    for j in jobs:
        if j["state"] in ("done", "gaveup"):
            continue
        kid = f"{j['acc']}/{j['slug']}"
        s = kag(j["acc"], "kernels", "status", kid, timeout=120)
        st = s.split('"')[-2] if '"' in s else s[-60:]
        if st != j["last_status"]:
            print(f"[{(time.time()-T0)/60:5.1f}m] {kid}: {st}", flush=True); j["last_status"] = st
            if "RUNNING" in st and "t_run" not in j:
                j["t_run"] = time.time()
        if "QUEUED" in st and time.time() - j["pushed"] > 60 * j["max_queue_min"]:
            if j["attempt"] >= 5:
                print(f"  {kid}: still queued after 5 attempts -> give up (needs a decision)", flush=True); j["state"] = "gaveup"; continue
            print(f"  {kid}: queued > {j['max_queue_min']} min -> delete + re-push", flush=True)
            print("  ", kag(j["acc"], "kernels", "delete", kid, "-y")[-120:], flush=True)
            j["attempt"] += 1; push(j)
        elif any(x in st for x in ("COMPLETE", "ERROR", "CANCEL")):
            os.makedirs(j["out"], exist_ok=True)
            o = kag(j["acc"], "kernels", "output", kid, "-p", j["out"], timeout=1800)
            run_min = (time.time() - j.get("t_run", j["pushed"])) / 60
            print(f"[{(time.time()-T0)/60:5.1f}m] {kid} {st} (~{run_min:.0f} min since RUNNING seen) -> {j['out']}: "
                  f"{sorted(os.listdir(j['out']))[:12]}", flush=True)
            j["state"] = "done"
print("MONITOR_DONE", json.dumps([{k: j.get(k) for k in ("slug", "acc", "attempt", "last_status")} for j in jobs]), flush=True)
