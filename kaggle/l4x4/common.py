"""Shared helpers for the L4x4 multi-GPU runner (parent launcher and GPU workers).
File-based work queue (see research/reports/HUONG_DAN_L4x4.md, section 4.3):
  queue/todo/p<rank>__<task>__<uid>.json   unit waiting (rank = LPT priority, lower first)
  queue/claimed/<worker>__<file>           unit owned by a worker (atomic os.rename -> only one worker wins)
  queue/done/<uid>                         unit finished; its result is parts/<uid>.json (written atomically first)
  queue/failed/<file>                      unit that failed twice
"""
import os, json, time

JOB = os.environ.get("HMMJOB_DIR", "/kaggle/tmp/hmmjob")
Q = os.path.join(JOB, "queue")
SUBDIRS = ("todo", "claimed", "done", "failed")


def ensure_dirs():
    for s in SUBDIRS:
        os.makedirs(os.path.join(Q, s), exist_ok=True)
    for s in ("parts", "hb", "logs"):
        os.makedirs(os.path.join(JOB, s), exist_ok=True)


def atomic_write_json(path, obj):
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def unit_file(rank, unit):
    return f"p{rank:05d}__{unit['task']}__{unit['uid']}.json"


def task_of(fname):
    return fname.split("__")[1]


def enqueue(units):
    """units: list already sorted by priority (most expensive first)."""
    ensure_dirs()
    for r, u in enumerate(units):
        u["attempt"] = u.get("attempt", 0)
        u["file"] = unit_file(r, u)
        atomic_write_json(os.path.join(Q, "todo", u["file"]), u)


def claim_next(worker, prefer=()):
    """Claim the highest-priority unit, preferring tasks this worker already has loaded (cache locality)."""
    todo = os.path.join(Q, "todo")
    files = sorted(os.listdir(todo))
    files = [f for f in files if f.endswith(".json")]
    order = [f for f in files if task_of(f) in prefer] + [f for f in files if task_of(f) not in prefer]
    for f in order:
        dst = os.path.join(Q, "claimed", f"{worker}__{f}")
        try:
            os.rename(os.path.join(todo, f), dst)
        except FileNotFoundError:
            continue
        with open(dst) as h:
            return json.load(h), dst
    return None, None


def mark_done(unit, claimed_path, part):
    atomic_write_json(os.path.join(JOB, "parts", unit["uid"] + ".json"), part)
    open(os.path.join(Q, "done", unit["uid"]), "w").close()
    os.remove(claimed_path)


def release(unit, claimed_path, max_attempts=2):
    """Put a unit back after a failure; after max_attempts it goes to failed/."""
    unit["attempt"] = unit.get("attempt", 0) + 1
    dst_dir = "todo" if unit["attempt"] < max_attempts else "failed"
    atomic_write_json(os.path.join(Q, dst_dir, unit["file"]), unit)
    if claimed_path and os.path.exists(claimed_path):
        os.remove(claimed_path)


def reclaim_worker(worker):
    """Return every unit claimed by a dead worker to the queue (unless already done)."""
    n = 0
    cdir = os.path.join(Q, "claimed")
    for f in os.listdir(cdir):
        if not f.startswith(worker + "__"):
            continue
        p = os.path.join(cdir, f)
        try:
            u = json.load(open(p))
        except Exception:
            continue
        if not os.path.exists(os.path.join(Q, "done", u["uid"])):
            release(u, p)
            n += 1
        else:
            os.remove(p)
    return n


def heartbeat(worker, **kw):
    kw.update(worker=worker, t=time.time())
    atomic_write_json(os.path.join(JOB, "hb", f"{worker}.json"), kw)


def counts():
    return {s: len([f for f in os.listdir(os.path.join(Q, s)) if not f.startswith(".")]) for s in SUBDIRS}
