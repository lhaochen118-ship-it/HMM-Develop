#!/usr/bin/env python3
"""One serial monitor for many Kaggle kernels. It replaces one run_kernel.py per kernel. On 2026-11-01, about 80 parallel
monitors hit the Kaggle API rate limit, which is shared by every account used from this machine's IP.

Every API call goes through one queue with a minimum gap between calls. The gap grows when Kaggle answers with a rate limit
(after a 10 min pause) and shrinks slowly while calls succeed.

What happens to each kernel:
  - Its status is polled: every 2 min while QUEUED, every --run-poll seconds (default 600) while RUNNING.
  - QUEUED for longer than the stall limit (8 min L4/CPU, 10 min T4; user rule) -> delete + re-push, at most 5 times.
    After that (user rule): an L4 kernel with no code error in its log (Traceback / ERROR status) is moved to 2x T4 (3 parallel
    jobs) and queued again; otherwise STALL_GIVEUP (NEEDS_FIX if its log has an error).
  - NEW kernels (dir built by `fanout.py --build-only`, no PUSH line in <slug>.log yet) wait for a slot: each is pushed to the
    FIRST account of automation/active_accounts.txt (at most 8 accounts; one fewer after every rate-limit answer, kept once
    calls pass again; state in <state.json>.nacc) that has a free session of its type (2 GPU / 5 CPU per
    account), so one account is filled before the next (user rule 2026-11-01 14:45); the kernel is moved to that account
    (metadata id + the account's code dataset) if it was built for another one.
  - COMPLETE / ERROR / CANCEL -> outputs are pulled into <slug>_out and results.tar is unpacked. The kernel stdout and
    STATUS=DONE:<state> are appended to <slug>.log, and results/*.json are copied to analysis/results/ (unless --nocopy).
    A kernel whose jobs returned rc != 0 is flagged NEEDS_FIX.

State (push time, restarts, done) is kept in <state.json>, so the monitor can be stopped and restarted at any time;
kernels that are already done are skipped.
--backoff s : pause after a rate-limit answer (default 600; user 2026-11-01 "only 1-2 streams": 1800).
--pull-first REGEX : kernels whose slug matches are expected to be finished: their outputs are pulled first (one call instead of
    status + output); a kernel whose pull brings no results.tar falls back to status polling.
Calls are grouped by account: a due kernel of the account used by the previous call goes first, so the monitor works through
the accounts one after another instead of touching all of them every minute.
Usage: central_monitor.py <state.json> [--gap 15] [--run-poll 600] [--backoff 600] [--pull-first REGEX] [--nocopy] <kernel_dir> [...]"""
import sys, os, re, json, glob, time, shutil, subprocess, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[1:]


def opt(k, d):
    if k in args:
        i = args.index(k); v = args[i + 1]; del args[i:i + 2]; return v
    return d


GAP_MIN = float(opt("--gap", "15")); RUN_POLL = float(opt("--run-poll", "600")); BACKOFF = float(opt("--backoff", "600"))
PULL_FIRST = re.compile(opt("--pull-first", "^$"))
NEVER = 1e18
NOCOPY = "--nocopy" in args
args = [a for a in args if a != "--nocopy"]
SF, KDIRS = args[0], [a.rstrip("/") for a in args[1:]]
ST = json.load(open(SF)) if os.path.exists(SF) else {}
gap, ok_calls, last_call = GAP_MIN, 0, 0.0


def ts():
    return time.strftime("%H:%M:%S")


def say(*a):
    print(ts(), *a, flush=True)


def save():
    json.dump(ST, open(SF + ".tmp", "w"), indent=1); os.replace(SF + ".tmp", SF)


def api(kid, *a):
    """one kaggle CLI call with the token of the kernel's account; waits for the global gap; backs off on a rate limit"""
    global gap, ok_calls, last_call
    acc = kid.split("/")[0]
    env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser(f"~/.kaggle/tok_{acc}")).read().strip())
    while True:
        w = last_call + gap - time.time()
        if w > 0: time.sleep(w)
        r = subprocess.run(["kaggle"] + list(a), capture_output=True, text=True, env=env); last_call = time.time()
        o = (r.stdout + r.stderr).strip()
        if "rate limit" in o.lower() or "429" in o:
            gap = min(gap * 1.5, 120.0); ok_calls = 0
            # user rule 2026-11-01 15:55: blocked by the API -> one account fewer for NEW kernels (min 1); once calls pass again the
            # number stays where it is (no further reduction)
            if N_ACT[0] > 1:
                N_ACT[0] -= 1; open(SF + ".nacc", "w").write(str(N_ACT[0]))
            say(f"rate limit -> pause {BACKOFF:.0f} s, gap {gap:.0f} s, accounts for new kernels now {N_ACT[0]}: {ACTIVE_ACC[:N_ACT[0]]}")
            time.sleep(BACKOFF + random.uniform(0, 60)); continue
        ok_calls += 1
        if ok_calls % 30 == 0: gap = max(gap * 0.9, GAP_MIN)
        return o


def pull(kd, s, state):
    slug = os.path.basename(kd); out = kd + "_out"; os.makedirs(out, exist_ok=True)
    o = api(s["kid"], "kernels", "output", s["kid"], "-p", out, "-o")
    if os.path.isfile(os.path.join(out, "results.tar")):
        subprocess.run(["tar", "-xf", os.path.join(out, "results.tar"), "-C", out])
    txt = ""
    for f in sorted(glob.glob(out + "/*.log")):
        try:
            recs = json.load(open(f, errors="ignore"))
            txt += "========== STDOUT ==========\n" + "".join(r.get("data", "") for r in recs if r.get("stream_name") == "stdout")[-20000:] + "\n"
            if state != "complete":
                txt += "========== STDERR (tail) ==========\n" + "".join(r.get("data", "") for r in recs if r.get("stream_name") == "stderr")[-4000:] + "\n"
        except Exception as e:
            txt += f"decode failed: {e}\n"
    res = glob.glob(os.path.join(out, "results", "*.json"))
    if not NOCOPY:
        for f in res: shutil.copy(f, os.path.join(ROOT, "analysis", "results"))
    nbad = txt.count("rc=") - txt.count("rc=0")
    with open(kd + ".log", "a") as fh:
        fh.write(f"=== PULL ({state}) -> {out} (central monitor) ===\n{o[-400:]}\n{txt}restarts {s['restarts']}\nSTATUS=DONE:{state}\n")
    flag = " NEEDS_FIX" if (nbad or state != "complete") else ""
    say(f"{slug}: DONE {state} {len(res)} results, rc!=0: {nbad}{flag}")


def pull_done(kd, s):
    """outputs already pulled (pull-first): unpack, log, copy, state read from the kernel stdout ('complete' if it has EVAL_DONE)"""
    out = kd + "_out"; subprocess.run(["tar", "-xf", os.path.join(out, "results.tar"), "-C", out]); txt = ""
    for f in sorted(glob.glob(out + "/*.log")):
        try: txt += "".join(r.get("data", "") for r in json.load(open(f, errors="ignore")) if r.get("stream_name") == "stdout")[-20000:]
        except Exception as e: txt += f"decode failed: {e}\n"
    state = "complete" if "EVAL_DONE" in txt else "partial"
    res = glob.glob(os.path.join(out, "results", "*.json"))
    if not NOCOPY:
        for f in res: shutil.copy(f, os.path.join(ROOT, "analysis", "results"))
    nbad = txt.count("rc=") - txt.count("rc=0")
    with open(kd + ".log", "a") as fh:
        fh.write(f"=== PULL-FIRST ({state}) -> {out} (central monitor) ===\n========== STDOUT ==========\n{txt}\nSTATUS=DONE:{state}\n")
    say(f"{os.path.basename(kd)}: DONE {state} (pull-first) {len(res)} results, rc!=0: {nbad}{' NEEDS_FIX' if nbad or state != 'complete' else ''}")


_act = os.path.join(ROOT, "automation", "active_accounts.txt")
ACTIVE_ACC = [l.strip() for l in open(_act) if l.strip() and not l.startswith("#")] if os.path.isfile(_act) else []
LIMIT = {"gpu": 2, "cpu": 5}                                           # Kaggle sessions per account
MAX_ACC = 10                                                           # user rule 2026-11-01 15:55: at most 8 accounts; 2026-11-03: the user gave 10 accounts for this round
N_ACT = [min(MAX_ACC, len(ACTIVE_ACC))]
if os.path.isfile(SF + ".nacc"): N_ACT[0] = max(1, min(N_ACT[0], int(open(SF + ".nacc").read().strip() or N_ACT[0])))


def retarget(kd, s, acc):
    """move a not-yet-pushed kernel to account acc (metadata id + that account's code dataset; fanout --build-only refreshed it)"""
    f = os.path.join(kd, "kernel-metadata.json"); md = json.load(open(f)); old = md["id"].split("/")[0]
    md["id"] = f"{acc}/{os.path.basename(kd)}"
    md["dataset_sources"] = [d.replace(f"{old}/dive-vpr-analysis", f"{acc}/dive-vpr-analysis") for d in md["dataset_sources"]]
    json.dump(md, open(f, "w"), indent=2); s["kid"] = md["id"]


def to_t4(kd, s):
    """L4 still queued after 5 restarts and no code error in its log -> 2x T4 (user rule): drop the L4 machine shape, 3 parallel
    jobs (4 CPUs / 30 GB), stall limit 10 min, restart counter reset; the kernel is queued for a free GPU slot again"""
    f = os.path.join(kd, "kernel-metadata.json"); md = json.load(open(f)); md.pop("machine_shape", None); md["competition_sources"] = []
    json.dump(md, open(f, "w"), indent=2)
    r = os.path.join(kd, md["code_file"]); src = open(r).read()
    src = re.sub(r"if (\d+): NW = min\(len\(JOBS\), (\d+)\)", lambda m: "if 3: NW = min(len(JOBS), 3)" if int(m.group(1)) else m.group(0), src)
    open(r, "w").write(src); s.update(stall=600, restarts=0, t4=True, unpushed=True, next=NEVER, queued_since=None, last=None)


for kd in KDIRS:
    slug = os.path.basename(kd)
    if slug in ST and ST[slug].get("done"): continue
    md = json.load(open(os.path.join(kd, "kernel-metadata.json")))
    t4 = "T4" in str(md.get("machine_shape", "")) or (md.get("enable_gpu") and not md.get("machine_shape"))
    pushed = os.path.isfile(kd + ".log") and "PUSH" in open(kd + ".log").read()
    ST.setdefault(slug, dict(kid=md["id"], kdir=kd, stall=600 if t4 else 480, restarts=0, queued_since=None, last=None, done=False,
                             gpu=bool(md.get("enable_gpu")), unpushed=not pushed))
    ST[slug]["gpu"] = bool(md.get("enable_gpu"))                       # session type (2 GPU / 5 CPU slots per account)
    if "unpushed" not in ST[slug]: ST[slug]["unpushed"] = not pushed
    ST[slug]["next"] = NEVER if ST[slug]["unpushed"] else 0.0
save()
pend = [k for k, s in ST.items() if not s["done"] and s["kdir"] in KDIRS]
say(f"monitoring {len(pend)} kernels ({sum(bool(ST[k].get('unpushed')) for k in pend)} waiting for a slot), gap {gap:.0f} s, "
    f"run poll {RUN_POLL:.0f} s, new kernels on {ACTIVE_ACC[:N_ACT[0]]}")
acct = lambda k: ST[k]["kid"].split("/")[0]
ktype = lambda k: "gpu" if ST[k].get("gpu") else "cpu"
prio = lambda k: KDIRS.index(ST[k]["kdir"]) if ST[k]["kdir"] in KDIRS else 1 << 30
busy = lambda a, t: [k for k in pend if acct(k) == a and ktype(k) == t and not ST[k].get("unpushed")]
last_acct = [None]; pushed_now = [False]
while pend:
    # user rule 2026-11-01 14:45: a new kernel goes to the FIRST account of active_accounts.txt (at most 4) with a free slot of its
    # type (2 GPU / 5 CPU sessions), i.e. one account is filled before the next; no free slot -> it waits. One push per iteration.
    for k in sorted([k for k in pend if ST[k].get("unpushed") and ST[k].get("retry", 0) <= time.time()], key=prio):
        a = next((a for a in ACTIVE_ACC[:N_ACT[0]] if len(busy(a, ktype(k))) < LIMIT[ktype(k)]), None)
        if a is None: continue
        s = ST[k]
        if acct(k) != a: retarget(s["kdir"], s, a)
        p = api(s["kid"], "kernels", "push", "-p", s["kdir"]); line = p.splitlines()[-1][:120] if p else ""
        with open(s["kdir"] + ".log", "a") as fh: fh.write(f"{ts()} PUSH: {line}\n")
        if "successfully pushed" in p.lower() or "kernel version" in p.lower():
            s.update(unpushed=False, queued_since=time.time(), last=None, next=time.time() + 120); say(f"{k}: PUSH -> {a} ({ktype(k)})")
            pushed_now[0] = True
        else:
            s["retry"] = time.time() + 600; say(f"{k}: PUSH_FAILED on {a}: {line}")
        save(); break
    if pushed_now[0]:                                                  # keep pushing while kernels wait for a free slot (status polls later)
        pushed_now[0] = False; continue
    due = [k for k in pend if ST[k]["next"] <= time.time()]
    same = [k for k in due if acct(k) == last_acct[0]]                 # stay on the account of the previous call while it has work
    slug = min(same or due or pend, key=lambda k: (ST[k]["next"] if not (same or due) else prio(k))); s = ST[slug]; last_acct[0] = acct(slug)
    w = s["next"] - time.time()
    # a kernel waiting for a free slot that has one now: do not sleep until the next status poll (the API gap still applies)
    pushable = any(ST[k].get("unpushed") and ST[k].get("retry", 0) <= time.time() and
                   any(len(busy(a, ktype(k))) < LIMIT[ktype(k)] for a in ACTIVE_ACC[:N_ACT[0]]) for k in pend)
    if w > 0: time.sleep(min(w, 2 if pushable else 60)); continue
    if PULL_FIRST.search(slug) and not s.get("pull_tried"):
        s["pull_tried"] = True; out = s["kdir"] + "_out"; os.makedirs(out, exist_ok=True)
        api(s["kid"], "kernels", "output", s["kid"], "-p", out, "-o")
        if os.path.isfile(os.path.join(out, "results.tar")):
            pull_done(s["kdir"], s); s["done"] = True; pend.remove(slug); save(); continue
        say(f"{slug}: no results.tar yet -> status polling"); save()
    o = api(s["kid"], "kernels", "status", s["kid"]); now = time.time()
    m = re.search(r"KernelWorkerStatus\.(\w+)", o)
    if not m:
        say(f"{slug}: no status ({o[-120:]!r})"); s["next"] = now + 120; save(); continue
    low = m.group(1).lower()
    if low != s["last"]: say(f"{slug}: {low}"); s["last"] = low
    if any(x in low for x in ("complete", "error", "cancel")):
        state = "complete" if "complete" in low else ("error" if "error" in low else "cancel")
        pull(s["kdir"], s, state); s["done"] = True; pend.remove(slug); save(); continue
    if "queued" in low:
        s["queued_since"] = s["queued_since"] or now
        if now - s["queued_since"] > s["stall"]:
            if s["restarts"] >= 5:
                api(s["kid"], "kernels", "delete", "-y", s["kid"])     # never leave a queued session behind
                log = open(s["kdir"] + ".log").read()
                err = "Traceback" in log or "STATUS=DONE:error" in log or "KernelWorkerStatus.ERROR" in log
                if s["gpu"] and not s.get("t4") and not err:
                    to_t4(s["kdir"], s); say(f"{slug}: L4 queue stuck after 5 restarts, no code error in its log -> 2x T4 (waits for a GPU slot)")
                    save(); continue
                say(f"{slug}: STALL_GIVEUP (queued after 5 restarts{', code error in its log: NEEDS_FIX' if err else ''})")
                with open(s["kdir"] + ".log", "a") as fh: fh.write("STATUS=STALL_GIVEUP\nSTATUS=DONE:stall\n")
                s["done"] = True; pend.remove(slug); save(); continue
            s["restarts"] += 1; say(f"{slug}: STUCK (queued {int(now - s['queued_since'])} s) -> delete + re-push {s['restarts']}/5")
            api(s["kid"], "kernels", "delete", "-y", s["kid"]); time.sleep(20)
            p = api(s["kid"], "kernels", "push", "-p", s["kdir"]); say(f"{slug}: PUSH {p.splitlines()[-1][:120] if p else ''}")
            s["queued_since"] = time.time()
        s["next"] = time.time() + 120
    else:
        s["queued_since"] = None; s["next"] = now + RUN_POLL * random.uniform(0.9, 1.2)
    save()
say("all kernels done")
