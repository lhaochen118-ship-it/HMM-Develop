"""Build kernel K01 (Nordland contiguous video-rate segments, 4 seasons) from the proven nb15c dump notebook.
Usage: python kaggle/build_k01.py <nb15c.ipynb> <out_dir>"""
import json, sys, re, os
src, out = sys.argv[1], sys.argv[2]
nb = json.load(open(src))
cells = nb["cells"]
def code(c): return "".join(c["source"])
NEW_NORD = r'''
# === L.NORDSEG — Nordland 4 seasons, CONTIGUOUS stride-1 blocks (for stride/dependence/time-warp studies) ===
NORD_BLOCKS = [(10000, 12500), (25000, 27500)]   # index ranges into the common (all-season) frame-id list
def load_nordland():
    root = PATHS["nordland"]; assert root, "nordland mount not found"
    def season_dir(s):
        c = [d for d, _, fs in os.walk(root) if os.path.basename(d).lower() == s and any(f.lower().endswith((".png", ".jpg")) for f in fs)]
        return sorted(c, key=lambda p: -p.count(os.sep))[0] if c else None
    def fid(f):
        d = "".join(ch for ch in os.path.splitext(f)[0] if ch.isdigit()); return int(d) if d else None
    tracks = {}
    for s in ["summer", "spring", "fall", "winter"]:
        d = season_dir(s)
        if d: tracks[s] = {fid(f): os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith((".png", ".jpg")) and fid(f) is not None}
    common = sorted(set.intersection(*[set(v) for v in tracks.values()]))
    sel = []; blk = []
    for b, (a, e) in enumerate(NORD_BLOCKS):
        e = min(e, len(common)); sel += list(range(a, e)); blk += [b] * (e - a)
    fids = [common[i] for i in sel]
    log("L.NORD", "ok", f"seasons={list(tracks)} common={len(common)} selected={len(fids)} blocks={NORD_BLOCKS}")
    return {"parts": [(s, [tracks[s][f] for f in fids]) for s in tracks],
            "meta": {"frame_ids": np.array(fids), "common_index": np.array(sel), "block": np.array(blk), "seasons": np.array(list(tracks))}}
'''
newcells = []
for c in cells:
    s = code(c)
    if c["cell_type"] != "code": newcells.append(c); continue
    if s.startswith("DUMP ="):
        s = 'DUMP = ["nord"]\nDESCRIPTORS = ["salad", "megaloc", "netvlad", "cosplace"]\n'
    elif "L.NORD" in s and "def load_nordland" in s:
        s = NEW_NORD
    c = dict(c); c["source"] = s; c["outputs"] = []; c["execution_count"] = None
    newcells.append(c)
nb["cells"] = newcells
os.makedirs(out, exist_ok=True)
json.dump(nb, open(os.path.join(out, "k01-nordseg.ipynb"), "w"), indent=1)
meta = {"id": "nhatlong1103/hmm-k01-nordseg", "title": "hmm-k01-nordseg", "code_file": "k01-nordseg.ipynb",
        "language": "python", "kernel_type": "notebook", "is_private": True, "enable_gpu": True, "enable_tpu": False,
        "enable_internet": False, "dataset_sources": ["nhatlong1103/bundle", "nhatlong1103/nordland-full-47-6gb",
        "nhatlong1103/vpr-descriptor-weights"], "kernel_sources": [], "competition_sources": [], "model_sources": [],
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:9a6bcfda6d03b2cd9aa347ee8c1bae62043328ed0f4afe9bda014e4f8bbf9435",
        "machine_shape": "NvidiaTeslaT4"}
json.dump(meta, open(os.path.join(out, "kernel-metadata.json"), "w"), indent=2)
for c in newcells:
    if c["cell_type"] == "code": compile(code(c), "cell", "exec")
print("built", out, len(newcells), "cells")
