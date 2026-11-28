#!/usr/bin/env python3
"""Local CPU test of the L4x4 runner machinery (queue, claim, respawn, merge) with a fake task kind.
One fake worker crashes on its first unit to exercise reclaim/respawn. Run: python3 kaggle/l4x4/test_runner_local.py"""
import os, sys, json, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = '''
import os, time
KIND = "fake"; NEEDS_LG = False
def accept(cfg, d, f): return cfg["slug"] in d
def needed(cfg): return {f"img{i}" for i in range(cfg["n"])}
def make_units(tid, cfg, unit_sec=60, smoke=False):
    return [{"task": tid, "uid": f"{tid}-{s:04d}", "rows": [s, min(cfg["n"], s + 7)], "cost": 7.0} for s in range(0, cfg["n"], 7)]
def merge(tid, cfg, parts):
    import numpy as np
    cover = np.zeros(cfg["n"], int); vals = [None] * cfg["n"]
    for p in parts:
        s, e = p["rows"]; cover[s:e] += 1
        for i, v in zip(range(s, e), p["out"]): vals[i] = v
    return f"fake_{tid}.json", vals, {"missing": int((cover == 0).sum()), "dup": int((cover > 1).sum())}
def prepare(cfg, ctx): return {"idx": ctx["index"][cfg["task_id"]], "w": ctx["worker"]}
def run_unit(st, unit, hb):
    s, e = unit["rows"]
    flag = os.path.join(os.environ["HMMJOB_DIR"], "crashed_once")
    if st["w"] == "w01" and not os.path.exists(flag):
        open(flag, "w").close(); os._exit(3)          # simulate a hard worker crash mid-unit
    time.sleep(0.05); hb(done=e - s, total=e - s)
    return {"rows": [s, e], "out": [os.path.basename(st["idx"][f"img{i}"]) for i in range(s, e)]}
'''


def main():
    root = tempfile.mkdtemp(prefix="l4x4test_")
    job, inp, out = (os.path.join(root, x) for x in ("job", "input", "out"))
    for x in (job, out):
        os.makedirs(x)
    for slug, n in (("ds-a", 40), ("ds-b", 23)):
        d = os.path.join(inp, slug, "imgs"); os.makedirs(d)
        for i in range(n):
            open(os.path.join(d, f"img{i}.jpg"), "w").write("x")
    for f in ("common.py", "launcher.py", "worker.py"):
        shutil.copy(os.path.join(HERE, f), job)
    open(os.path.join(job, "task_fake.py"), "w").write(FAKE)
    os.environ.update(HMMJOB_DIR=job, HMMJOB_OUT=out, HMMJOB_INPUT=inp, CUDA_VISIBLE_DEVICES="")
    sys.path.insert(0, job)
    import launcher
    bundle = {"opts": {"run_id": "test", "wpg": 1, "cpu_workers": 3, "requested_gpus": 0},
              "tasks": {"A": {"kind": "fake", "task_id": "A", "slug": "ds-a", "n": 40},
                        "B": {"kind": "fake", "task_id": "B", "slug": "ds-b", "n": 23}}}
    ok = launcher.main(bundle)
    man = json.load(open(os.path.join(out, "manifest.json")))
    a = json.load(open(os.path.join(out, "fake_A.json"))); b = json.load(open(os.path.join(out, "fake_B.json")))
    assert ok and a == [f"img{i}.jpg" for i in range(40)] and b == [f"img{i}.jpg" for i in range(23)], (ok, a[:3])
    assert any(e["event"] == "worker_died" for e in man["events"]), man["events"]
    print("LOCAL TEST PASSED", man["checks"], man["events"])
    shutil.rmtree(root)


if __name__ == "__main__":
    main()
