"""GPU worker of the L4x4 runner: sees exactly one GPU (CUDA_VISIBLE_DEVICES set by the parent), loads the
networks ONCE, then claims units from the shared file queue until it is empty (dynamic load balancing).
Several workers may share one GPU (WPG) when the work is partly CPU-bound (RANSAC/PnP)."""
import os, sys, json, time, traceback, importlib

JOBD = os.environ["HMMJOB_DIR"]
sys.path.insert(0, JOBD)
import common

WK = os.environ["WORKER"]
TASKS = json.load(open(os.path.join(JOBD, "tasks.json")))
INDEX = json.load(open(os.path.join(JOBD, "index.json")))
MODS = {k: importlib.import_module("task_" + k) for k in {c["kind"] for c in TASKS.values()}}
ctx = {"index": INDEX, "fc_cap": int(os.environ.get("FC_CAP", "2000")), "worker": WK, "dev": "cpu"}
t0 = time.time()

if any(getattr(m, "NEEDS_LG", True) for m in MODS.values()):
    import torch, cv2
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "2")))
    cv2.setNumThreads(int(os.environ.get("CV_THREADS", "2")))
    sys.path.insert(0, os.environ["LG_PATH"])
    from lightglue import LightGlue, SuperPoint
    from lightglue.utils import load_image, rbd
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    ctx.update(dev=dev, rbd=rbd, load_image=load_image,
               ext=SuperPoint(max_num_keypoints=2048).eval().to(dev),
               mat=LightGlue(features="superpoint").eval().to(dev))
    print(f"[{WK}] models on {dev} ({torch.cuda.get_device_name(0) if dev == 'cuda' else 'cpu'}) "
          f"in {time.time() - t0:.0f}s, fc_cap {ctx['fc_cap']}", flush=True)

loaded, ndone, cur = {}, 0, {"uid": None, "last": 0.0}


def hb(**kw):
    if time.time() - cur["last"] > 20:
        common.heartbeat(WK, unit=cur["uid"], units_done=ndone, elapsed=time.time() - t0, **kw)
        cur["last"] = time.time()


while True:
    unit, cpath = common.claim_next(WK, prefer=set(loaded))
    if unit is None:
        break
    tid = unit["task"]; cfg = TASKS[tid]; mod = MODS[cfg["kind"]]; cur["uid"] = unit["uid"]
    try:
        if tid not in loaded:
            tp = time.time(); loaded[tid] = mod.prepare(cfg, ctx)
            print(f"[{WK}] prepared {tid} in {time.time() - tp:.0f}s", flush=True)
        tu = time.time()
        part = mod.run_unit(loaded[tid], unit, hb)
        part.update(worker=WK, gpu=os.environ.get("CUDA_VISIBLE_DEVICES", ""), wall=time.time() - tu)
        common.mark_done(unit, cpath, part); ndone += 1
        print(f"[{WK}] done {unit['uid']} in {time.time() - tu:.0f}s (T4 est {unit['cost']:.0f}s)", flush=True)
    except Exception:
        traceback.print_exc()
        common.release(unit, cpath)
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
common.heartbeat(WK, unit=None, units_done=ndone, elapsed=time.time() - t0, finished=True)
print(f"[{WK}] exit: {ndone} units in {time.time() - t0:.0f}s", flush=True)
