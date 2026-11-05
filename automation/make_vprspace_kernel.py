#!/usr/bin/env python3
"""VPR-Space step 2 (2026-11-05): ONE L4 kernel (offline) that extracts the 6 global descriptors of every VPR-Space trajectory.

Input: the output of the step-1 kernel `<owner>/vprspace-frames` (CPU, internet: release v0.1.0 streamed through tar, frames downsampled to
<= 322 px JPEG in vprspace/img/<trajectory>/, plus vprspace/poses/<trajectory>.npy and vprspace/vpr_gt/), mounted as a KERNEL SOURCE, so the
kernel must run on the same account (push it directly, not through central_monitor, which may move a kernel to another account).
Shared extraction code: nb15_src cells 10 / 20 / 25 (same models, 322 px, L2-normalised fp16), weights from nhatlong1103/bundle and
nhatlong1103/vpr-descriptor-weights (as automation/make_stlucia_kernel.py).
Output: /kaggle/working/dump/<desc>/vs_<key>.npy and dump/meta/vs_<key>.npz (names, C = camera positions (n, 3), poses = raw array,
traj = original trajectory name), key = trajectory name with '@' -> 'at' and '.' -> 'p'; vpr_gt copied to dump/vpr_gt.
Usage: make_vprspace_kernel.py <kernel_dir> <slug> --owner dinhthinh [--test N]"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "automation"))


def code_cells(f):
    txt = open(os.path.join(ROOT, "nb15_src", f)).read(); out, cur, on = [], [], False
    for ln in txt.splitlines():
        if ln.strip() in ("#%%CODE", "#%%MARKDOWN"):
            if on and cur: out.append("\n".join(cur))
            cur, on = [], ln.strip() == "#%%CODE"
        elif on: cur.append(ln)
    if on and cur: out.append("\n".join(cur))
    return "\n\n".join(out)


opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
kdir, slug = sys.argv[1], sys.argv[2]; OWNER = opt("--owner", "dinhthinh"); TEST = int(opt("--test", "0"))
DESCS = ["cosplace", "dinov2"] if TEST else ["megaloc", "salad", "mixvpr", "cosplace", "netvlad", "dinov2"]
body = r'''
# ================================================================ VPR-Space: frames -> 6 global descriptors
import shutil, glob
DESCRIPTORS, TEST = %s, %d
CONFIG.NUM_WORKERS = min(16, os.cpu_count() or 4)
W = "/kaggle/working"; DUMP = os.path.join(W, "dump"); os.makedirs(os.path.join(DUMP, "meta"), exist_ok=True)
VS = next(d for d, subs, _ in os.walk("/kaggle/input", followlinks=True) if "img" in subs and "poses" in subs)
key = lambda n: n.replace("@", "at").replace(".", "p")
def centres(P):
    P = np.asarray(P, float)
    if P.ndim == 3 and P.shape[1:] in ((4, 4), (3, 4)): return P[:, :3, 3]
    if P.ndim == 2 and P.shape[1] >= 3: return P[:, :3]
    raise ValueError(f"unknown pose format {P.shape}")
PARTS_ = []
for tdir in sorted(glob.glob(os.path.join(VS, "img", "*"))):
    n = os.path.basename(tdir); fs = sorted(glob.glob(os.path.join(tdir, "*.jpg")))
    P = np.load(os.path.join(VS, "poses", n + ".npy"), allow_pickle=True)
    if len(P) != len(fs): log(f"S.{n}", "warn", f"{len(fs)} frames vs {len(P)} poses (kept min)")
    m = min(len(P), len(fs)); fs = fs[:m]; P = P[:m]
    if TEST: fs, P = fs[:TEST], P[:TEST]
    np.savez(os.path.join(DUMP, "meta", f"vs_{key(n)}.npz"), names=np.array([os.path.basename(f)[:-4] for f in fs]), C=centres(P), poses=P, traj=n)
    PARTS_.append((f"vs_{key(n)}", fs))
if os.path.isdir(os.path.join(VS, "vpr_gt")): shutil.copytree(os.path.join(VS, "vpr_gt"), os.path.join(DUMP, "vpr_gt"), dirs_exist_ok=True)
log("S.frames", "ok", f"{len(PARTS_)} trajectories, {sum(len(p) for _, p in PARTS_)} frames")
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
    log(f"X.{tag}", "ok" if bad == 0 else "warn", f"{len(paths)} imgs in {time.time()-t0:.0f}s, unreadable={bad}")
    return outs

for tag, paths in PARTS_:
    o = extract_multi(paths, tag)
    for d, a in o.items(): np.save(os.path.join(DUMP, d, tag + ".npy"), a)
json.dump(REPORT, open(os.path.join(DUMP, "report_vprspace.json"), "w"), indent=1, default=str)
print("EVAL_DONE missing", [d for d in DESCRIPTORS if d not in FWDS], flush=True)
''' % (json.dumps(DESCS), TEST)
src = "\n\n".join([code_cells("10_p0.src"), code_cells("20_extract.src"), code_cells("25_extra.src"), body])
os.makedirs(kdir, exist_ok=True); open(os.path.join(kdir, "run.py"), "w").write(src)
meta = {"id": f"{OWNER}/{slug}", "title": slug, "code_file": "run.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": True, "enable_tpu": False, "enable_internet": False,
        "dataset_sources": ["nhatlong1103/bundle", "nhatlong1103/vpr-descriptor-weights"],
        "competition_sources": ["gemma-4-developer-agent"], "kernel_sources": [f"{OWNER}/vprspace-frames"], "model_sources": [],
        "machine_shape": "NvidiaL4"}
json.dump(meta, open(os.path.join(kdir, "kernel-metadata.json"), "w"), indent=2)
compile(src, "run.py", "exec"); print("kernel written:", kdir, len(src), "chars")
