#!/usr/bin/env python3
"""NCLT stage 2 (GPU, no internet): 6 global descriptors for the Cam5 frames selected by stage 1 (make_nclt_stage1.py).

Stage-1 outputs are PRIVATE kernel outputs, so they are mounted with `kernel_sources` and the kernel must belong to the
same account (nhatlong1103 or huyenco). Each mounted output holds meta/nclt_<session>.npz and the images, either as
img/<session>/<utime>.jpg (first runs) or as one img_<session>.tar (later runs; unpacked to local disk first).
Every GPU of the session is used: the script re-launches itself once per GPU (CUDA_VISIBLE_DEVICES=i, WORKER=i); worker
i embeds rows i::n_gpu of every session, the parent re-assembles them in meta row order.
Output (/kaggle/working): dump/<desc>/nclt_<session>.npy (float16, L2-normalised), dump/meta/nclt_<session>.npz (copy of
the stage-1 meta), packed into one dump_nclt.tar (fast output pull).
Usage: make_dump_nclt.py <kernel_dir> <slug> <stage1_slug,...> [--owner nhatlong1103] [--l4] [--ds owner/dataset,...]
(stage1_slug may be empty when the images come from the public datasets given with --ds)
The extraction cells are those of nb15_src (10_p0 config/paths, 20_extract registry, 25_extra extra networks)."""
import sys, os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kdir, slug, srcs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
OWNER = sys.argv[sys.argv.index("--owner") + 1] if "--owner" in sys.argv else "nhatlong1103"
L4 = "--l4" in sys.argv
DS = sys.argv[sys.argv.index("--ds") + 1].split(",") if "--ds" in sys.argv else []   # public nclt-cam5-<date> datasets


def code_cells(f):
    txt = open(os.path.join(ROOT, "nb15_src", f)).read(); out, cur, on = [], [], False
    for ln in txt.splitlines():
        if ln.strip() in ("#%%CODE", "#%%MARKDOWN"):
            if on and cur: out.append("\n".join(cur))
            cur, on = [], ln.strip() == "#%%CODE"
        elif on: cur.append(ln)
    if on and cur: out.append("\n".join(cur))
    return "\n\n".join(out)


launcher = r'''
import os, sys, subprocess, time
if True:                                             # parent: one worker process per GPU, then re-assemble
    import numpy as np, torch, shutil, tarfile, glob
    W = "/kaggle/working"; T0 = time.time(); NG = max(1, torch.cuda.device_count()); TMP = "/kaggle/tmp/nclt_img"
    os.makedirs(TMP, exist_ok=True); SESS = {}
    for d, subs, fs in os.walk("/kaggle/input"):
        for f in fs:
            if f.startswith("nclt_") and f.endswith(".npz") and os.path.basename(d) == "meta": SESS[f[5:-4]] = os.path.join(d, f)
            if f.startswith("img_") and f.endswith(".tar"):
                with tarfile.open(os.path.join(d, f)) as tf: tf.extractall(TMP)
    print("sessions", sorted(SESS), "gpus", NG, f"untar {time.time()-T0:.0f}s", flush=True)
    for d, subs, fs in os.walk("/kaggle/input"):                # mount layout (debug: a dataset still processing is missing)
        if d.count(os.sep) <= 5: print("  in:", d, len(fs), "files", sorted(subs)[:4], flush=True)
        if d.count(os.sep) >= 5: subs[:] = []
    # torch.hub copies a file:// checkpoint into its cache at ~1 MB/s from /kaggle/input, once per worker (15 min for
    # DINOv2): link every bundle checkpoint into the cache first, so the workers find it there
    hub = os.path.expanduser("~/.cache/torch/hub/checkpoints"); os.makedirs(hub, exist_ok=True)
    for d, subs, fs in os.walk("/kaggle/input"):
        if os.path.basename(d) == "checkpoints":
            for f in fs:
                if not os.path.exists(os.path.join(hub, f)): os.symlink(os.path.join(d, f), os.path.join(hub, f))
    # the NG workers build the same 6 networks at once and all read the weights from the slow network mount (~490 s per
    # worker, vs ~30 s of extraction): read every weight file ONCE here with 16 threads into the page cache (197 GB RAM)
    import concurrent.futures as cf
    wf = [os.path.join(d, f) for d, _, fs in os.walk("/kaggle/input") for f in fs
          if ("/bundle" in d or "descriptor-weights" in d) and f.endswith((".pth", ".pt", ".ckpt", ".bin", ".safetensors", ".pth.tar"))]
    def _rd(f):
        with open(f, "rb") as h:
            while h.read(64 << 20): pass
        return os.path.getsize(f)
    t1 = time.time(); nb = sum(cf.ThreadPoolExecutor(16).map(_rd, wf))
    print(f"weights pre-read: {len(wf)} files, {nb/1e9:.2f} GB in {time.time()-t1:.0f}s", flush=True)
    os.makedirs(os.path.join(W, "dump", "meta"), exist_ok=True)
    for s, f in SESS.items(): shutil.copy(f, os.path.join(W, "dump", "meta", f"nclt_{s}.npz"))
    env = dict(os.environ, NCLT_TMP=TMP, NG=str(NG), OMP_NUM_THREADS=str(max(1, (os.cpu_count() or 4) // NG)))
    open("/kaggle/tmp/worker.py", "w").write(WORKER_SRC)     # kernels run as a converted notebook: spawn a real file
    ps = [subprocess.Popen([sys.executable, "/kaggle/tmp/worker.py"], env=dict(env, WORKER=str(i), CUDA_VISIBLE_DEVICES=str(i)),
                           stdout=open(f"/kaggle/working/worker{i}.log", "w"), stderr=subprocess.STDOUT) for i in range(NG)]
    while any(p.poll() is None for p in ps):                   # relay worker progress to the kernel log
        time.sleep(120); print(f"{time.time()-T0:.0f}s", [open(f"/kaggle/working/worker{i}.log").read().strip().splitlines()[-1:] for i in range(NG)], flush=True)
    rc = [p.wait() for p in ps]; print("workers rc", rc, f"{time.time()-T0:.0f}s", flush=True)
    for s in SESS:
        n = len(np.load(os.path.join(W, "dump", "meta", f"nclt_{s}.npz"))["names"])
        for d in sorted(os.listdir(os.path.join(W, "parts"))):
            ps_ = [os.path.join(W, "parts", d, f"nclt_{s}_w{i}.npy") for i in range(NG)]
            if not all(os.path.isfile(p) for p in ps_): print("MISSING", s, d, flush=True); continue
            a = [np.load(p) for p in ps_]; out = np.empty((n, a[0].shape[1]), np.float16)
            for i in range(NG): out[i::NG] = a[i]
            os.makedirs(os.path.join(W, "dump", d), exist_ok=True); np.save(os.path.join(W, "dump", d, f"nclt_{s}.npy"), out)
    shutil.rmtree(os.path.join(W, "parts"))
    subprocess.run(["tar", "-cf", os.path.join(W, "dump_nclt.tar"), "-C", W, "dump"]); shutil.rmtree(os.path.join(W, "dump"))
    print("DUMP_DONE", sorted(SESS), f"{time.time()-T0:.0f}s", flush=True)
    sys.exit(0 if all(r == 0 for r in rc) else 1)
'''

body = r'''
# ================================================================ worker: rows WORKER::NG of every session
WK, NG, TMP = int(os.environ["WORKER"]), int(os.environ["NG"]), os.environ["NCLT_TMP"]
DESCRIPTORS = ["megaloc", "salad", "mixvpr", "cosplace", "netvlad", "dinov2"]
W = "/kaggle/working"; IMGDIR = {}
for root in ("/kaggle/input", TMP):
    for d, subs, fs in os.walk(root):
        if os.path.basename(os.path.dirname(d)) == "img" and any(f.endswith(".jpg") for f in fs[:5]): IMGDIR[os.path.basename(d)] = d
PARTS = []
for f in sorted(os.listdir(os.path.join(W, "dump", "meta"))):
    s = f[5:-4]; names = np.load(os.path.join(W, "dump", "meta", f))["names"]
    if s not in IMGDIR: log(f"nclt.{s}", "fail", "no image dir"); continue
    PARTS.append((f"nclt_{s}", [os.path.join(IMGDIR[s], f"{int(u)}.jpg") for u in names[WK::NG]]))
print("worker", WK, "of", NG, [(t, len(p)) for t, p in PARTS], flush=True)

FWDS, DIMS = {}, {}
for dname in DESCRIPTORS:
    try:
        _t = time.time(); FWDS[dname] = build_extractor(dname); DIMS[dname] = EXTRACTOR_INFO["dim"]; print(f"  built {dname} in {time.time()-_t:.0f}s", flush=True)
    except Exception as e:
        import traceback; traceback.print_exc(); log(f"R.1.{dname}", "fail", repr(e)[:200])

@torch.no_grad()
def extract_multi(paths, tag):
    dl = torch.utils.data.DataLoader(ImageList(paths, CONFIG.IMG_SIZE), batch_size=CONFIG.BATCH_SIZE, shuffle=False,
                                     num_workers=CONFIG.NUM_WORKERS, pin_memory=(DEVICE == "cuda"))
    outs = {d: np.empty((len(paths), DIMS[d]), np.float16) for d in FWDS}; t0 = time.time(); bad = 0
    amp = torch.bfloat16 if CONFIG.USE_BF16 else torch.float16
    for b, (x, idx, ok) in enumerate(dl):
        x = x.to(DEVICE, non_blocking=True); bad += int((ok == 0).sum())
        for d, fwd in FWDS.items():
            with torch.autocast("cuda", dtype=amp, enabled=(DEVICE == "cuda")):
                y = fwd(x)
            outs[d][idx.numpy()] = torch.nn.functional.normalize(y.float(), dim=1).cpu().numpy().astype(np.float16)
        if b %% 50 == 0: print(f"    w{WK} {tag}: {min((b+1)*CONFIG.BATCH_SIZE, len(paths))}/{len(paths)} ({(b+1)*CONFIG.BATCH_SIZE/max(time.time()-t0,1e-3):.1f} img/s)", flush=True)
    for d in outs: assert np.isfinite(outs[d].astype(np.float32)).all(), (tag, d)
    log(f"X.{tag}.w{WK}", "ok" if bad == 0 else "warn", f"{len(paths)} imgs in {time.time()-t0:.0f}s, unreadable={bad}")
    return outs

for tag, paths in PARTS:
    o = extract_multi(paths, tag)
    for d, a in o.items():
        os.makedirs(os.path.join(W, "parts", d), exist_ok=True); np.save(os.path.join(W, "parts", d, f"{tag}_w{WK}.npy"), a)
json.dump(REPORT, open(os.path.join(W, f"report_w{WK}.json"), "w"), indent=1, default=str)
print("WORKER_DONE", WK, {k: v["status"] for k, v in REPORT.items() if v["status"] != "ok"}, flush=True)
'''

wsrc = "\n\n".join([code_cells("10_p0.src"), code_cells("20_extract.src"), code_cells("25_extra.src"), body % ()])
wsrc = wsrc.replace('CONFIG = Config()', 'CONFIG = Config(NUM_WORKERS=max(2, min(8, (os.cpu_count() or 4) // int(os.environ.get("NG", "1")) - 1)))')
compile(wsrc, "worker.py", "exec")
src = f"WORKER_SRC = {wsrc!r}\n" + launcher
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(src)
meta = {"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": True, "enable_tpu": False, "enable_internet": False,
        "dataset_sources": ["nhatlong1103/bundle", "nhatlong1103/vpr-descriptor-weights"] + DS,
        "competition_sources": [], "kernel_sources": [f"{OWNER}/{s}" for s in srcs if s], "model_sources": []}
if L4: meta.update(machine_shape="NvidiaL4", competition_sources=["gemma-4-developer-agent"])
json.dump(meta, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
compile(src, "run.py", "exec"); print("kernel written:", kdir, len(src), "chars | sources", meta["kernel_sources"])
