#!/usr/bin/env python3
"""A33 fix: re-extract NetVLAD and CosPlace at NATIVE aspect ratio (long side 640 px, multiple of 16) instead of the
322x322 squashed resize the original dump notebooks used for every model (correct only for SALAD/MegaLoc/DINOv2/MixVPR).
Patches an existing extraction notebook (.ipynb) or script (.py) and writes a kernel dir. Outputs are renamed to
dump/netvlad_nat and dump/cosplace_nat so nothing old is overwritten.
Usage: build_a33.py <src .ipynb|.py> <src kernel-metadata.json> <out dir> <owner/slug> [--dump rc,nord] [--cities cph]"""
import sys, os, json, re

src, meta_src, out, kid = sys.argv[1:5]; a = sys.argv[5:]
DUMP = a[a.index("--dump") + 1].split(",") if "--dump" in a else None
CITIES = a[a.index("--cities") + 1].split(",") if "--cities" in a else None
NATIVE = '''
# === A33 — native-aspect input for CNN descriptors (NetVLAD / CosPlace evaluate at full/native resolution) ===
def _native_size(paths, long_side=640, mult=16):
    from PIL import Image as _I
    w, h = _I.open(paths[0]).size; s = long_side / max(w, h)
    return (max(mult, int(round(h * s / mult)) * mult), max(mult, int(round(w * s / mult)) * mult))

def _native_bs(paths, base=48, ref=322 * 322):
    # batch scaled by pixel count (64 @ 322x322 ran out of T4 memory at 640x480 -> R16)
    h, w = _native_size(paths); return max(4, int(base * ref / (h * w)))
'''
FINAL = '''
# === A33 — keep the new features apart from the 322-px ones ===
import shutil as _sh
for _d in ("netvlad", "cosplace"):
    _p = os.path.join(CONFIG.OUT_DIR, _d)
    if os.path.isdir(_p): _sh.move(_p, _p + "_nat")
print("A33_DONE", sorted(os.listdir(CONFIG.OUT_DIR)), flush=True)
'''


def patch(code):
    n0 = code
    code = code.replace("T.Resize((sz, sz), antialias=True)", "T.Resize(sz if isinstance(sz, tuple) else (sz, sz), antialias=True)")
    code = code.replace("ImageList(paths, CONFIG.IMG_SIZE)", "ImageList(paths, _native_size(paths))")
    code = code.replace("ImageList(paths, _native_size(paths)), batch_size=CONFIG.BATCH_SIZE", "ImageList(paths, _native_size(paths)), batch_size=_native_bs(paths)")
    code = re.sub(r'^DESCRIPTORS = \[[^\]]*\]', 'DESCRIPTORS = ["netvlad", "cosplace"]', code, flags=re.M)
    if DUMP: code = re.sub(r'^DUMP = \[[^\]]*\]', f'DUMP = {json.dumps(DUMP)}', code, flags=re.M)
    if CITIES: code = re.sub(r'^CONFIG.MSLS_CITIES = \([^)]*\)', f'CONFIG.MSLS_CITIES = {tuple(CITIES)!r}', code, flags=re.M)
    # the build_extractor smoke test feeds a square tensor: keep it, CNNs accept any size
    return code, code != n0


os.makedirs(out, exist_ok=True)
m = json.load(open(meta_src)); m.update(id=kid, title=kid.split("/")[1]); m.pop("id_no", None)
if src.endswith(".ipynb"):
    nb = json.load(open(src)); changed = False; inserted = False
    for c in nb["cells"]:
        if c["cell_type"] != "code": continue
        s = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
        s2, ch = patch(s); changed |= ch
        if not inserted and "class ImageList" in s2:
            s2 = NATIVE + "\n" + s2; inserted = True
        c["source"] = s2; c["outputs"] = []; c["execution_count"] = None
    nb["cells"].append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": FINAL})
    assert changed and inserted, "patch did not apply"
    fn = os.path.basename(src); json.dump(nb, open(os.path.join(out, fn), "w")); m["code_file"] = fn
else:
    s, ch = patch(open(src).read())
    assert ch and "class ImageList" in s, "patch did not apply"
    s = s.replace("class ImageList", NATIVE + "\nclass ImageList", 1) + FINAL
    fn = os.path.basename(src); open(os.path.join(out, fn), "w").write(s); m["code_file"] = fn
json.dump(m, open(os.path.join(out, "kernel-metadata.json"), "w"), indent=2)
txt = open(os.path.join(out, m["code_file"])).read()
print(f"built {out} -> {kid}: native resize {txt.count('_native_size(paths)')}x, descriptors patched "
      f"{'DESCRIPTORS = [\\\"netvlad\\\", \\\"cosplace\\\"]' in txt or 'DESCRIPTORS = [\"netvlad\", \"cosplace\"]' in txt}, sources {m['dataset_sources']}")
