#!/usr/bin/env python3
"""Spread evaluation jobs over every Kaggle account's GPU slots (2 T4 sessions per account) and run them all.
Tokens: ~/.kaggle/tok_<username> (one file per account). Jobs are split round-robin into `n_kernels` kernels, each
kernel goes to the next free (account, slot); kernels beyond 2 x #accounts become CPU kernels (use only for light jobs).
Usage: fanout.py <work_dir> <slug_prefix> <jobs_file|"job;job;..."> [n_kernels=all GPU slots] [--accounts a,b,...] [--cpu|--l4]
Each kernel: <work_dir>/<slug>/ (kernel dir), <work_dir>/<slug>_out/ (outputs), <work_dir>/<slug>.log (runner log).
Prints one line per kernel; waits for all runners; then copies every results/*.json into analysis/results/ (unless --nocopy).
--par N: parallel jobs per session; --ds a,b: extra dataset sources."""
import sys, os, glob, subprocess, shutil, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS = sorted(os.path.basename(f)[4:] for f in glob.glob(os.path.expanduser("~/.kaggle/tok_*")))
ACCOUNTS = ["nhatlong1103"] + [a for a in ACCOUNTS if a != "nhatlong1103"]
_res = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reserved_accounts.txt")   # kept for the user: never used
RESERVED = {l.strip() for l in open(_res) if l.strip() and not l.startswith("#")} if os.path.isfile(_res) else set()
ACCOUNTS = [a for a in ACCOUNTS if a not in RESERVED] + [a for a in ACCOUNTS if a in RESERVED]   # user 2026-10-31: use ALL accounts, reserved ones last
DSARG = ["--ds", sys.argv[sys.argv.index("--ds") + 1]] if "--ds" in sys.argv else []   # extra dataset sources for every kernel
DSARG += ["--par", sys.argv[sys.argv.index("--par") + 1]] if "--par" in sys.argv else []   # parallel jobs per session
DSARG += ["--models", sys.argv[sys.argv.index("--models") + 1]] if "--models" in sys.argv else []   # Kaggle model sources
DSARG += ["--nodumps"] if "--nodumps" in sys.argv else []                 # do not mount the descriptor dumps (cache-only jobs)
KSRC = sys.argv[sys.argv.index("--kernel-sources") + 1] if "--kernel-sources" in sys.argv else ""   # kernel outputs mounted as inputs (e.g. a dump kernel)
L4 = "--l4" in sys.argv                                                   # 4x L4 sessions (competition grant)
_val = {i + 1 for i, a in enumerate(sys.argv) if a in ("--ds", "--par", "--accounts", "--machine", "--models", "--kernel-sources")}  # positions of option values
args = [a for i, a in enumerate(sys.argv) if i > 0 and i not in _val and not a.startswith("--")]
if "--accounts" in sys.argv: ACCOUNTS = sys.argv[sys.argv.index("--accounts") + 1].split(",")
# user rule 2026-11-01 14:45 / 15:55: new kernels only on the accounts of automation/active_accounts.txt (at most 8 at the same time),
# packed in that order (2 GPU + 5 CPU sessions of one account before the next)
_act = os.path.join(os.path.dirname(os.path.abspath(__file__)), "active_accounts.txt")
if "--accounts" not in sys.argv and os.path.isfile(_act):
    ACCOUNTS = [l.strip() for l in open(_act) if l.strip() and not l.startswith("#")]
if len(ACCOUNTS) > 10: sys.exit(f"user rule: at most 10 accounts at the same time (2026-11-03), got {len(ACCOUNTS)}: {ACCOUNTS}")
work, prefix, jobs = args[0], args[1], args[2]
GROUPS = "--groups" in sys.argv                                          # --groups: each line of the jobs file is ONE kernel (jobs ';'-separated)
if GROUPS:
    groups = [[j.strip() for j in l.split(";") if j.strip()] for l in open(jobs) if l.strip()]
    jobs = [j for g in groups for j in g]
else:
    jobs = [j.strip() for j in (open(jobs).read().replace("\n", ";") if os.path.isfile(jobs) else jobs).split(";") if j.strip()]
slots = [(a, s) for a in ACCOUNTS for s in ((0, 1, 2, 3, 4) if "--cpu" in sys.argv else (0, 1))]   # GPU: fill BOTH sessions of an account before the next (user rule); CPU: 5 sessions per account
nk = len(groups) if GROUPS else min(int(args[3]) if len(args) > 3 else len(slots), len(jobs))
part_of = (lambda k: groups[k]) if GROUPS else (lambda k: jobs[k::nk])
os.makedirs(work, exist_ok=True); procs = []
for k in range(nk):
    part = part_of(k); acc, _ = slots[k % len(slots)]; gpu = k < len(slots) and "--cpu" not in sys.argv
    slug = f"{prefix}-{k + 1}"; kd = os.path.join(work, slug)
    cmd = [sys.executable, os.path.join(ROOT, "automation", "make_eval_kernel.py"), kd, slug, ";".join(part), KSRC, "--owner", acc] + ((["--l4"] if L4 else ["--gpu"]) if gpu else []) + DSARG
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"{slug}: {acc} {'GPU' if gpu else 'CPU'} {len(part)} jobs | {(r.stdout + r.stderr).strip().splitlines()[-1][:60]}", flush=True)
time.sleep(30)                                                             # let the code datasets finish versioning
for acc in sorted({slots[k % len(slots)][0] for k in range(nk)}):
    env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser(f"~/.kaggle/tok_{acc}")).read().strip())
    for _ in range(40):
        if subprocess.run(["kaggle", "datasets", "status", f"{acc}/dive-vpr-analysis"], capture_output=True, text=True, env=env).stdout.strip().endswith("ready"): break
        time.sleep(10)
def make(kd, slug, part, acc, gpu, t4=False):
    flag = (["--t4"] if t4 else (["--l4"] if L4 else ["--gpu"])) if gpu else []
    ds_ = DSARG
    if t4 and "--par" in ds_:                                              # 2x T4 session: 4 CPUs / 30 GB -> 3 parallel jobs
        i = ds_.index("--par"); ds_ = ds_[:i] + ["--par", "3"] + ds_[i + 2:]
    cmd = [sys.executable, os.path.join(ROOT, "automation", "make_eval_kernel.py"), kd, slug, ";".join(part), KSRC, "--owner", acc] + flag + ds_
    return subprocess.run(cmd, capture_output=True, text=True)


T4_FALLBACK = set()                                                        # kernels moved from a stuck L4 queue to 2x T4
if "--build-only" in sys.argv:
    # --build-only (2026-11-01 14:45): build the kernel dirs and exit WITHOUT pushing; automation/central_monitor.py pushes each one
    # when its account has a free slot of its type (2 GPU / 5 CPU), so a full account queues instead of spilling to new accounts
    # the monitor may move a kernel to any account of the list: bring the code dataset of the accounts not used above up to date
    for acc in [a for a in ACCOUNTS if a not in {slots[k % len(slots)][0] for k in range(nk)}]:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "automation", "make_eval_kernel.py"), os.path.join(work, f"_codesync_{acc}"),
                            "codesync", "true", "", "--owner", acc], capture_output=True, text=True)
        print(f"code dataset {acc}: {(r.stdout + r.stderr).strip().splitlines()[:1]}", flush=True)
    print(f"built {nk} kernels (not pushed): " + " ".join(os.path.join(work, f"{prefix}-{k + 1}") for k in range(nk)), flush=True); sys.exit(0)
if "--push-only" in sys.argv:
    # --push-only (2026-11-01): push every kernel one after another and exit; automation/central_monitor.py then watches all of
    # them through ONE rate-limited API queue (one run_kernel.py per kernel exceeded the Kaggle API rate limit of this IP)
    for k in range(nk):
        slug = f"{prefix}-{k + 1}"; acc = slots[k % len(slots)][0]
        env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser(f"~/.kaggle/tok_{acc}")).read().strip())
        for _ in range(6):
            r = subprocess.run(["kaggle", "kernels", "push", "-p", os.path.join(work, slug)], capture_output=True, text=True, env=env)
            o = (r.stdout + r.stderr).strip()
            if "rate limit" not in o.lower(): break
            time.sleep(600)
        open(os.path.join(work, slug + ".log"), "w").write(time.strftime("%H:%M:%S") + " PUSH: " + (o.splitlines()[-1] if o else "") + "\n")
        print(f"{slug}: PUSH {(o.splitlines()[-1] if o else '')[:100]}", flush=True); time.sleep(20)
    print(f"pushed {nk} kernels", flush=True); sys.exit(0)


def launch(k):
    slug = f"{prefix}-{k + 1}"; t4 = k in T4_FALLBACK
    # user rule (2026-11-01, updated): no output after 10 min on T4 / 8 min on L4 or CPU -> check; stuck in the queue -> cancel and
    # create a new session, at most 5 times
    stall, restarts = ("600", "5") if t4 else ("480", "5")
    return subprocess.Popen([sys.executable, os.path.join(ROOT, "automation", "run_kernel.py"), os.path.join(work, slug),
                             os.path.join(work, slug + "_out"), stall, restarts, "43200"], stdout=open(os.path.join(work, slug + ".log"), "a" if t4 else "w"), stderr=subprocess.STDOUT)


procs = {}
for k in range(nk):
    procs[k] = launch(k); time.sleep(2)
print(f"launched {nk} kernels", flush=True)
# failover: a kernel whose push hit the account's GPU-session cap (account busy elsewhere) moves to the next account
tried = {k: {slots[k % len(slots)][0]} for k in range(nk)}
while procs:
    for k, p in list(procs.items()):
        if p.poll() is None: continue
        del procs[k]; slug = f"{prefix}-{k + 1}"; log = open(os.path.join(work, slug + ".log")).read()
        gpu = k < len(slots) and "--cpu" not in sys.argv
        # user rule (2026-11-01, updated): L4 stuck in the queue after 5 restarts -> first check for a code / logic error (a crash in
        # any attempt's log): if there is one it must be fixed and re-run by hand (NEEDS_FIX); otherwise move the kernel to 2x T4
        if L4 and gpu and k not in T4_FALLBACK and ("STALL_GIVEUP" in log or "STATUS=DONE:stall" in log) and \
                ("Traceback" in log or "STATUS=DONE:error" in log or "KernelWorkerStatus.ERROR" in log):
            print(f"{slug}: NEEDS_FIX (L4 stuck AND an error in its log) -- not moved to T4", flush=True); continue
        if L4 and gpu and k not in T4_FALLBACK and ("STALL_GIVEUP" in log or "STATUS=DONE:stall" in log):
            acc = slots[k % len(slots)][0]; kid = f"{acc}/{slug}"
            env = dict(os.environ, KAGGLE_API_TOKEN=open(os.path.expanduser(f"~/.kaggle/tok_{acc}")).read().strip())
            subprocess.run(["kaggle", "kernels", "delete", "-y", kid], capture_output=True, text=True, env=env)   # never leave a queued L4 behind
            T4_FALLBACK.add(k); make(os.path.join(work, slug), slug, part_of(k), acc, gpu, t4=True); time.sleep(40)
            print(f"{slug}: L4 queue stuck after 5 restarts -> 2x T4 on {acc}", flush=True); procs[k] = launch(k); continue
        if "STATUS=PUSH_FAILED" in log and len(tried[k]) < len(ACCOUNTS):
            acc = [a for a in ACCOUNTS[k % len(ACCOUNTS):] + ACCOUNTS if a not in tried[k]][0]; tried[k].add(acc)
            make(os.path.join(work, slug), slug, part_of(k), acc, gpu); time.sleep(40)
            print(f"{slug}: push failed -> retry on {acc}", flush=True); procs[k] = launch(k); continue
        res = glob.glob(os.path.join(work, slug + "_out", "results", "*.json"))
        if "--nocopy" not in sys.argv:                                     # --nocopy: keep results in <work>/<slug>_out only
            for f in res: shutil.copy(f, os.path.join(ROOT, "analysis", "results"))
        nbad = log.count('rc=') - log.count('rc=0')
        print(f"{slug}: {'OK' if 'STATUS=DONE:complete' in log else 'FAILED'} {len(res)} results, rc!=0: {nbad}"
              + (" NEEDS_FIX (job errors: read <slug>_out/logs)" if nbad or "STATUS=DONE:error" in log else ""), flush=True)
    time.sleep(15)
