#!/usr/bin/env python3
"""Entry 37 item 3c: ONE L4 kernel (offline) that builds the St Lucia part of the study end to end.

Inputs: nhatlong1103/stlucia-vpr-frames (img/<trav>/<frame>.jpg every 10 m + frames_meta/stlucia_<trav>.npz, made locally by
automation/make_stlucia.py --spacing 5 and keeping every other frame, as the Entry 36 dump), the shared extraction code of every dump
(nb15_src cells: same models / 322 px / L2-normalised fp16 output; bundle + vpr-descriptor-weights), the Kaggle model
metaresearch/dinov2 large (HF format) for the SafeVPR'26 verifier at the paper's ViT-L/14, 224 x 224, and the code dataset.
Steps inside the kernel:
  1. 6 global descriptors of every traversal -> /kaggle/working/dump/<desc>/stlucia_<trav>.npy + dump/meta/ (GPU 0)
  2. ViT-L/14 patch tokens (final layer, L2-normalised, fp16) of every traversal -> /kaggle/working/patchL/ (GPU 0; not in the output)
  3. analysis jobs from the code dataset, in parallel (one BLAS thread per job, GPUs round robin):
       e37_prep.py <dump> stlucia <desc> <seed> --no-fwd   (navcache, exact statistics, top-K, route cost; 6 descriptors x seeds 0-4)
       e37_fwd.py  <dump> results stlucia <desc> <seed> k/n (forward null with presence, 2 parts per run, after its prep)
       e37_eval.py <dump> results results/cms results/topk results/tao stlucia <desc> <seed> n --wait   (merge + rules @E36,@E37)
       safevpr26.py --holes <dump> stlucia <desc> results --patch-dir patchL --tag vitl   (map-hole protocol, after the 5 preps)
       safevpr26.py <dump> - stlucia <desc> - --patch-dir patchL --tag vitl               (no-hole protocol)
  4. results.tar (results/ + logs/) and the dump (for nhatlong1103/stlucia-vpr-dump).
Usage: make_stlucia_kernel.py <kernel_dir> <slug> [--owner nhatlong1103] [--seeds 0,1,2,3,4] [--par 46] [--parts 2] [--test N]
  --test N: smoke test, first N frames of every traversal, 2 descriptors (cosplace, dinov2), seed 0 (local / any machine)."""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def code_cells(f):
    """code cells of an nb15_src/*.src file (the shared extraction code; same reader as make_dump_boreas.py)"""
    txt = open(os.path.join(ROOT, "nb15_src", f)).read(); out, cur, on = [], [], False
    for ln in txt.splitlines():
        if ln.strip() in ("#%%CODE", "#%%MARKDOWN"):
            if on and cur: out.append("\n".join(cur))
            cur, on = [], ln.strip() == "#%%CODE"
        elif on: cur.append(ln)
    if on and cur: out.append("\n".join(cur))
    return "\n\n".join(out)


def opt(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


kdir, slug = sys.argv[1], sys.argv[2]
OWNER = opt("--owner", "nhatlong1103"); SEEDS = [int(s) for s in opt("--seeds", "0,1,2,3,4").split(",")]
PAR = int(opt("--par", "46")); PARTS = int(opt("--parts", "2")); TEST = int(opt("--test", "0"))
DESCS = ["cosplace", "dinov2"] if TEST else ["megaloc", "salad", "mixvpr", "cosplace", "netvlad", "dinov2"]
if TEST: SEEDS = SEEDS[:1]

body = r'''
# ================================================================ St Lucia: frames -> descriptors -> ViT-L patches -> analysis chain
import shutil, subprocess, threading
from concurrent.futures import ThreadPoolExecutor
DESCRIPTORS, SEEDS, PAR, PARTS, TEST = %s, %s, %d, %d, %d
CONFIG.NUM_WORKERS = min(16, os.cpu_count() or 4)                    # first reads from /kaggle/input are slow: more parallel readers
W = "/kaggle/working"; DUMP = os.path.join(W, "dump"); PL = os.path.join(W, "patchL"); os.makedirs(PL, exist_ok=True)
os.makedirs(os.path.join(DUMP, "meta"), exist_ok=True)
FR = next(d for d, subs, _ in os.walk("/kaggle/input", followlinks=True) if "frames_meta" in subs)
TRAVS = sorted(f[len("stlucia_"):-4] for f in os.listdir(os.path.join(FR, "frames_meta")) if f.startswith("stlucia_") and f.endswith(".npz"))
PARTS_ = []
for tr in TRAVS:
    z = dict(np.load(os.path.join(FR, "frames_meta", f"stlucia_{tr}.npz"), allow_pickle=True))
    if TEST: z = {k: (v[:TEST] if isinstance(v, np.ndarray) and v.ndim and len(v) == len(z["names"]) else v) for k, v in z.items()}
    np.savez(os.path.join(DUMP, "meta", f"stlucia_{tr}.npz"), **z)
    PARTS_.append((f"stlucia_{tr}", [os.path.join(FR, "img", tr, f"{n}.jpg") for n in z["names"]]))
log("S.frames", "ok", f"{len(TRAVS)} traversals, {sum(len(p) for _, p in PARTS_)} frames: {TRAVS}")

# --- 1. global descriptors (shared extraction code of every dump)
FWDS, DIMS = {}, {}
for dname in DESCRIPTORS:
    try:
        FWDS[dname] = build_extractor(dname); DIMS[dname] = EXTRACTOR_INFO["dim"]
    except Exception as e:
        import traceback; traceback.print_exc(); log(f"R.1.{dname}", "fail", repr(e)[:200])
for dname in FWDS: os.makedirs(os.path.join(DUMP, dname), exist_ok=True)

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
        if b %% 20 == 0: print(f"    {tag}: {min((b+1)*CONFIG.BATCH_SIZE, len(paths))}/{len(paths)} ({(b+1)*CONFIG.BATCH_SIZE/max(time.time()-t0,1e-3):.1f} img/s)", flush=True)
    for d in outs: assert np.isfinite(outs[d].astype(np.float32)).all(), (tag, d)
    log(f"X.{tag}", "ok" if bad == 0 else "warn", f"{len(paths)} imgs in {time.time()-t0:.0f}s, unreadable={bad}")
    return outs

for tag, paths in PARTS_:
    o = extract_multi(paths, tag)
    for d, a in o.items(): np.save(os.path.join(DUMP, d, tag + ".npy"), a)
missing = [d for d in DESCRIPTORS if d not in FWDS]
del FWDS
if DEVICE == "cuda": torch.cuda.empty_cache()

# --- 2. SafeVPR'26 verifier tokens: DINOv2 ViT-L/14 (the paper's backbone), final layer patch tokens, 224 x 224, no CLS
t0 = time.time()
try:
    from transformers import AutoModel
    vl_dir = next(d for d, _, fs in os.walk("/kaggle/input", followlinks=True) if "config.json" in fs and "dinov2" in d.lower() and "large" in d.lower())
    vitl = AutoModel.from_pretrained(vl_dir, torch_dtype=torch.float32).eval().to(DEVICE)
    import torchvision.transforms as TT
    from PIL import Image
    txl = TT.Compose([TT.Resize((224, 224), antialias=True), TT.ToTensor(), TT.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))])
    class _PL(torch.utils.data.Dataset):
        def __init__(self, p): self.p = p
        def __len__(self): return len(self.p)
        def __getitem__(self, i): return txl(Image.open(self.p[i]).convert("RGB")), i
    with torch.no_grad():
        for tag, paths in PARTS_:
            out = None
            for x, idx in torch.utils.data.DataLoader(_PL(paths), batch_size=64, num_workers=CONFIG.NUM_WORKERS):
                with torch.autocast("cuda", dtype=torch.bfloat16 if CONFIG.USE_BF16 else torch.float16, enabled=(DEVICE == "cuda")):
                    h = vitl(pixel_values=x.to(DEVICE)).last_hidden_state[:, 1:]
                f = torch.nn.functional.normalize(h.float(), dim=-1).cpu().numpy().astype(np.float16)
                if out is None: out = np.zeros((len(paths),) + f.shape[1:], np.float16)
                out[idx.numpy()] = f
            np.save(os.path.join(PL, f"patch_{tag}.npy"), out)
    log("S.vitl", "ok", f"patch tokens {out.shape} per traversal, {time.time() - t0:.0f}s, model {vl_dir}")
    del vitl
    if DEVICE == "cuda": torch.cuda.empty_cache()
    VITL = True
except Exception as e:
    import traceback; traceback.print_exc(); log("S.vitl", "fail", repr(e)[:300]); VITL = False

# --- 3. analysis chain (code dataset), dependency-ordered pool
code = next(d for d, _, fs in os.walk("/kaggle/input", followlinks=True) if "selfcal.py" in fs)
C = os.path.join(W, "code"); shutil.copytree(code, C, dirs_exist_ok=True)
for d in ("results", "logs"): os.makedirs(os.path.join(C, d), exist_ok=True)
NGPU = torch.cuda.device_count() if DEVICE == "cuda" else 0
DESC_OK = [d for d in DESCRIPTORS if d not in missing]
lock = threading.Lock(); done = {}; cnt = [0]
def run(name, args, deps=()):
    for dpn in deps:
        done[dpn].wait()
    with lock: i = cnt[0]; cnt[0] += 1
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    if NGPU: env["CUDA_VISIBLE_DEVICES"] = str(i %% NGPU)
    t = time.time(); log_ = os.path.join(C, "logs", f"{i:03d}_{name}.log"); rc = -99
    try:
        rc = subprocess.run([sys.executable] + args, cwd=C, stdout=open(log_, "w"), stderr=subprocess.STDOUT, env=env).returncode
    finally:
        done[name].set()                                               # dependents never wait forever
    print(f"done {name} rc={rc} {time.time() - t:.0f}s", flush=True); return rc
JOBS = []
for d in DESC_OK:
    for s in SEEDS:
        JOBS.append((f"prep_{d}_s{s}", ["e37_prep.py", DUMP, "stlucia", d, str(s), "--no-fwd"], ()))
for d in DESC_OK:
    for s in SEEDS:
        for k in range(PARTS):
            JOBS.append((f"fwd_{d}_s{s}_p{k}", ["e37_fwd.py", DUMP, "results", "stlucia", d, str(s), f"{k}/{PARTS}"], (f"prep_{d}_s{s}",)))
        JOBS.append((f"eval_{d}_s{s}", ["e37_eval.py", DUMP, "results", "results/cms", "results/topk", "results/tao", "stlucia", d, str(s),
                                        str(PARTS), "--wait"], tuple(f"fwd_{d}_s{s}_p{k}" for k in range(PARTS))))
    if VITL:
        JOBS.append((f"sv_holes_{d}", ["safevpr26.py", "--holes", DUMP, "stlucia", d, "results", "--patch-dir", PL, "--tag", "vitl"],
                     tuple(f"prep_{d}_s{s}" for s in SEEDS)))
        JOBS.append((f"sv_nohole_{d}", ["safevpr26.py", DUMP, "-", "stlucia", d, "-", "--patch-dir", PL, "--tag", "vitl"], ()))
for n, _, _ in JOBS: done[n] = threading.Event()
# preps first (every other job waits on them), then the long forward parts, SafeVPR'26 last
with ThreadPoolExecutor(max(1, min(PAR, len(JOBS)))) as ex: rcs = list(ex.map(lambda j: run(*j), JOBS))
for sub in ("results", "logs"): shutil.copytree(os.path.join(C, sub), os.path.join(W, sub), dirs_exist_ok=True)
shutil.rmtree(C, ignore_errors=True); shutil.rmtree(PL, ignore_errors=True)
subprocess.run(["tar", "-cf", os.path.join(W, "results.tar"), "-C", W, "results", "logs"])
shutil.rmtree(os.path.join(W, "results"), ignore_errors=True); shutil.rmtree(os.path.join(W, "logs"), ignore_errors=True)
json.dump(REPORT, open(os.path.join(DUMP, "report_stlucia.json"), "w"), indent=1, default=str)
print("EVAL_DONE", rcs, "missing", missing, flush=True)
''' % (json.dumps(DESCS), json.dumps(SEEDS), PAR, PARTS, TEST)

src = "\n\n".join([code_cells("10_p0.src"), code_cells("20_extract.src"), code_cells("25_extra.src"), body])
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(src)
meta = {"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": True, "enable_tpu": False, "enable_internet": False,
        "dataset_sources": [f"{OWNER}/dive-vpr-analysis", "nhatlong1103/stlucia-vpr-frames", "nhatlong1103/bundle", "nhatlong1103/vpr-descriptor-weights"],
        "competition_sources": ["gemma-4-developer-agent"], "kernel_sources": [], "model_sources": ["metaresearch/dinov2/pyTorch/large/1"],
        "machine_shape": "NvidiaL4"}
json.dump(meta, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
compile(src, "run.py", "exec"); print("kernel written:", kdir, len(src), "chars")
