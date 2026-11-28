"""Parent launcher of the L4x4 runner (research/reports/HUONG_DAN_L4x4.md, sections 4-7).
S0 probe hardware (requested vs actual) -> S1 stage-in (one walk of /kaggle/input, checkpoints into the hub cache,
pre-read every needed image into the page cache with 32 threads) -> S2 unit queue (LPT order) -> S3 spawn NG x WPG
worker processes (CUDA_VISIBLE_DEVICES=i) -> S4 monitor (heartbeat + nvidia-smi every 30-60 s, respawn dead workers,
reclaim their units) -> S5 merge with completeness/duplicate checks -> S6 outputs + manifest (sha256) in /kaggle/working."""
import os, sys, json, time, subprocess, shutil, threading, hashlib, importlib
from concurrent.futures import ThreadPoolExecutor


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def nvsmi():
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used,memory.total",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=20)
        return [[float(x) for x in ln.split(",")] for ln in r.stdout.strip().splitlines() if ln.strip()]
    except Exception:
        return []


def main(BUNDLE):
    T0 = time.time()
    JOBD = os.environ["HMMJOB_DIR"]; OUT = os.environ.get("HMMJOB_OUT", "/kaggle/working"); INP = os.environ.get("HMMJOB_INPUT", "/kaggle/input")
    import common
    common.ensure_dirs()
    OPTS, TASKS = BUNDLE["opts"], BUNDLE["tasks"]; SMOKE = bool(OPTS.get("smoke"))
    MODS = {k: importlib.import_module("task_" + k) for k in {c["kind"] for c in TASKS.values()}}
    events = []

    # ---------------- S0 probe
    try:
        import torch
        NG = torch.cuda.device_count()
        gpus = [(torch.cuda.get_device_name(i), torch.cuda.get_device_properties(i).total_memory / 2**30) for i in range(NG)]
        tv = f"torch {torch.__version__} cuda {torch.version.cuda}"
    except Exception:
        NG, gpus, tv = 0, [], "torch n/a"
    ncpu = os.cpu_count() or 1
    ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
    disk = shutil.disk_usage(OUT).free / 2**30
    print(f"[S0] run {OPTS['run_id']} | python {sys.version.split()[0]} {tv} | requested {OPTS.get('requested','?')} | "
          f"actual {NG} GPU {gpus} | vCPU {ncpu} | RAM {ram:.0f} GB | disk {disk:.0f} GB | smoke={SMOKE}", flush=True)
    if NG < OPTS.get("requested_gpus", 0):
        events.append({"event": "tier_mismatch", "requested": OPTS.get("requested_gpus"), "actual": NG})
        print("[S0] WARNING: fewer GPUs than requested -> shards/workers recomputed", flush=True)
    wpg = OPTS.get("wpg", 3)
    if NG:
        wpg = max(1, min(wpg, ncpu // (3 * NG)))         # >= 3 vCPU per worker (RANSAC/PnP + loader)
        NW = NG * wpg
        vram = min(g[1] for g in gpus) * 2**30
        fc_cap = int(max(300, min(6000, 0.55 * vram / wpg / 2.3e6)))   # ~2.2 MB per cached SuperPoint image
    else:
        NW, fc_cap = max(1, OPTS.get("cpu_workers", 2)), 1500
    thr = max(1, ncpu // NW - 1)
    print(f"[S0] workers {NW} ({wpg}/GPU) | threads/worker {thr} | feature-cache cap {fc_cap} images/worker", flush=True)

    # ---------------- S1 stage-in
    t1 = time.time(); lg = None; ck = {}
    for d, subs, fs in os.walk(INP):
        if os.path.basename(d) == "lightglue" and "lightglue.py" in fs and lg is None:
            lg = os.path.dirname(d)
        for f in ("superpoint_v1.pth", "superpoint_lightglue_v0-1_arxiv.pth"):
            if f in fs and f not in ck:
                ck[f] = os.path.join(d, f)
    hub = os.path.expanduser("~/.cache/torch/hub/checkpoints"); os.makedirs(hub, exist_ok=True)
    for f, p in ck.items():
        if not os.path.exists(os.path.join(hub, f)):
            shutil.copy(p, hub)                           # once in the parent, not once per worker
    need = {tid: MODS[c["kind"]].needed(c) for tid, c in TASKS.items()}
    def walk_index(cfgs):
        idx = {tid: {} for tid in cfgs}
        for d, subs, fs in os.walk(INP):
            for tid, c in cfgs.items():
                acc = MODS[c["kind"]].accept
                for f in fs:
                    k = os.path.splitext(f)[0]
                    if k in need[tid] and acc(c, d, f):
                        idx[tid][k] = os.path.join(d, f)
        return idx
    index = walk_index(TASKS)
    low = {tid: dict(c, slug="") for tid, c in TASKS.items() if c.get("slug") and len(index[tid]) < 0.5 * len(need[tid])}
    if low:                                   # mount path without the dataset slug -> retry without that filter
        print(f"[S1] slug filter resolved <50% for {sorted(low)}; retrying without it", flush=True)
        events.append({"event": "slug_fallback", "tasks": sorted(low)})
        index.update(walk_index(low))
    for tid in TASKS:
        print(f"[S1] {tid}: resolved {len(index[tid])}/{len(need[tid])}", flush=True)
        if len(index[tid]) < 0.95 * len(need[tid]):
            events.append({"event": "low_resolve", "task": tid, "resolved": len(index[tid]), "need": len(need[tid])})
    common.atomic_write_json(os.path.join(JOBD, "index.json"), index)
    common.atomic_write_json(os.path.join(JOBD, "tasks.json"), TASKS)
    files = sorted({p for v in index.values() for p in v.values()})

    def _rd(p):
        with open(p, "rb") as h:
            while h.read(16 << 20):
                pass
        return os.path.getsize(p)
    t2 = time.time(); nb = sum(ThreadPoolExecutor(32).map(_rd, files))
    print(f"[S1] lightglue {lg} | ckpt {sorted(ck)} | walk {t2 - t1:.0f}s | pre-read {len(files)} images "
          f"{nb / 1e9:.2f} GB in {time.time() - t2:.0f}s", flush=True)

    # ---------------- S2 queue (LPT: most expensive unit first)
    units = []
    for tid, c in TASKS.items():
        units += MODS[c["kind"]].make_units(tid, c, smoke=SMOKE)
    units.sort(key=lambda u: -u["cost"])
    common.enqueue(units)
    est = sum(u["cost"] for u in units)
    print(f"[S2] {len(units)} units | T4-equivalent work {est / 60:.1f} min | ideal wall on {NW} workers "
          f"~{est / max(1, NW) / 60:.1f} min (before L4 speed-up / contention)", flush=True)

    # ---------------- S3 spawn
    wsrc = os.path.join(JOBD, "worker.py")

    def spawn(i):
        g = i % NG if NG else None
        env = dict(os.environ, WORKER=f"w{i:02d}", HMMJOB_DIR=JOBD, LG_PATH=lg or "", FC_CAP=str(fc_cap),
                   TORCH_THREADS=str(min(4, thr)), CV_THREADS=str(thr), OMP_NUM_THREADS=str(thr),
                   MKL_NUM_THREADS=str(thr), PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
        if g is not None:
            env["CUDA_VISIBLE_DEVICES"] = str(g)
        log = open(os.path.join(JOBD, "logs", f"w{i:02d}.log"), "a")
        return subprocess.Popen([sys.executable, wsrc], env=env, stdout=log, stderr=subprocess.STDOUT)
    procs = {i: spawn(i) for i in range(NW)}; restarts = {i: 0 for i in range(NW)}

    # ---------------- S4 monitor
    util_rows = []; stop = threading.Event()

    def sampler():
        while not stop.is_set():
            for r in nvsmi():
                util_rows.append([round(time.time() - T0, 1)] + r)
            stop.wait(30)
    th = threading.Thread(target=sampler, daemon=True); th.start()
    last_print = 0
    while True:
        alive = [i for i, p in procs.items() if p.poll() is None]
        for i, p in list(procs.items()):
            rc = p.poll()
            if rc not in (None, 0):
                n = common.reclaim_worker(f"w{i:02d}")
                events.append({"event": "worker_died", "worker": i, "rc": rc, "reclaimed": n, "t": time.time() - T0})
                print(f"[S4] worker w{i:02d} died rc={rc}, reclaimed {n} units", flush=True)
                if restarts[i] < 2 and common.counts()["todo"] > 0:
                    restarts[i] += 1; procs[i] = spawn(i)
                else:
                    procs[i] = subprocess.Popen(["true"])   # retire slot
        if not alive and all(p.poll() is not None for p in procs.values()):
            c = common.counts()
            if c["todo"] > 0 and any(r < 2 for r in restarts.values()):
                i = min(restarts, key=restarts.get); restarts[i] += 1; procs[i] = spawn(i); continue
            break
        for i, p in list(procs.items()):                  # hung worker: no heartbeat for HB_MAX s while alive -> kill
            hbp = os.path.join(JOBD, "hb", f"w{i:02d}.json")
            if p.poll() is None and os.path.exists(hbp) and time.time() - os.path.getmtime(hbp) > OPTS.get("hb_max", 900):
                print(f"[S4] worker w{i:02d} silent > {OPTS.get('hb_max', 900)} s -> kill", flush=True); p.kill()
        if time.time() - last_print >= 60:
            last_print = time.time(); c = common.counts(); u = nvsmi()
            ut = " ".join(f"g{int(r[0])}:{int(r[1])}%/{r[2] / 1024:.1f}G" for r in u)
            print(f"[S4] {time.time() - T0:6.0f}s todo {c['todo']} run {c['claimed']} done {c['done']} "
                  f"failed {c['failed']} | {ut}", flush=True)
        time.sleep(5)
    stop.set()

    # ---------------- S5 merge
    parts_by = {tid: [] for tid in TASKS}; walls = []
    for u in units:
        p = os.path.join(JOBD, "parts", u["uid"] + ".json")
        if os.path.exists(p):
            d = json.load(open(p)); parts_by[u["task"]].append(d); walls.append([u["uid"], d.get("worker"), d.get("gpu"), round(d.get("wall", 0), 1), round(u["cost"], 1)])
    manifest = {"run_id": OPTS["run_id"], "smoke": SMOKE, "gpus": gpus, "vcpu": ncpu, "workers": NW, "wpg": wpg,
                "fc_cap": fc_cap, "events": events, "outputs": {}, "checks": {}, "units": len(units),
                "t4_equiv_min": round(est / 60, 1), "wall_min": None, "gpu_util_mean": {}}
    for tid, c in TASKS.items():
        fname, obj, chk = MODS[c["kind"]].merge(tid, c, parts_by[tid])
        p = os.path.join(OUT, fname)
        with open(p, "w") as f:
            json.dump(obj, f)
        manifest["outputs"][fname] = {"task": tid, "sha256": sha256_file(p), "bytes": os.path.getsize(p)}
        manifest["checks"][tid] = chk
        print(f"[S5] {tid} -> {fname} {chk}", flush=True)

    # ---------------- S6 outputs
    if util_rows:
        import statistics
        for g in sorted({int(r[1]) for r in util_rows}):
            manifest["gpu_util_mean"][g] = round(statistics.mean(r[2] for r in util_rows if int(r[1]) == g), 1)
        with open(os.path.join(OUT, "gpu_util.csv"), "w") as f:
            f.write("t_s,gpu,util_pct,mem_used_mib,mem_total_mib\n")
            for r in util_rows:
                f.write(",".join(str(x) for x in r) + "\n")
    with open(os.path.join(OUT, "unit_walls.csv"), "w") as f:
        f.write("uid,worker,gpu,wall_s,t4_est_s\n")
        for w in walls:
            f.write(",".join(str(x) for x in w) + "\n")
    os.makedirs(os.path.join(OUT, "logs"), exist_ok=True)
    for f in os.listdir(os.path.join(JOBD, "logs")):
        shutil.copy(os.path.join(JOBD, "logs", f), os.path.join(OUT, "logs", f))
    manifest["wall_min"] = round((time.time() - T0) / 60, 2)
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    ok = all(ch.get("missing", 1) == 0 and ch.get("dup", 1) == 0 and ch.get("conv_consistent", True) and ch.get("order_ok", True)
             for ch in manifest["checks"].values())
    print(f"L4X4_DONE ok={ok} wall {manifest['wall_min']} min | gpu util mean {manifest['gpu_util_mean']}", flush=True)
    return ok
