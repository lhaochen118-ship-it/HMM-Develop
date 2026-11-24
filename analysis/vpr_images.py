"""Image paths of every query row (in the order of the dataset loader) and every FULL-map row, for the datasets whose
images are public on Kaggle (one resolver for SafeVPR, VLM auditing and any image-level baseline):
  boreas  nhatlong1103/boreas-vpr-images-1..5   img/<seq>/<timestamp_us>.jpg
  nclt    nhatlong1103/nclt-cam5-<date>         img_<s>/img/<s>/<utime>.jpg
  4s:*    nhatlong1103/4seasons                 <scene>/<date>/.../recording_<date>/undistorted_images/cam0/<ns>.png
Directories are found by a pruned walk of /kaggle/input (the 4Seasons cam0 folders are not listed file by file; their paths
are built from the dump meta `names`). Usage: qpaths, mpaths = image_paths(ds, dump, ep)."""
import os
import numpy as np

_IMG, _CAM0 = None, None


def _scan(root="/kaggle/input"):
    global _IMG, _CAM0
    if _IMG is not None: return
    _IMG, _CAM0 = {}, {}
    for d, dirs, fs in os.walk(root):
        b = os.path.basename(d)
        if d.endswith(os.path.join("undistorted_images", "cam0")):
            rec = next((p[len("recording_"):] for p in d.split(os.sep) if p.startswith("recording_") and "_stereo" not in p), None)
            if rec: _CAM0[rec] = d
            dirs[:] = []; continue
        if b in ("cam1", "distorted_images") or b.startswith("models"): dirs[:] = []; continue
        if os.path.basename(os.path.dirname(d)) == "img":                    # img/<seq>/<name>.jpg (Boreas, NCLT)
            _IMG[b] = d; dirs[:] = []


def _names(dump, ds, rec):
    tag = {"boreas": f"boreas_{rec}", "nclt": f"nclt_{rec}"}.get(ds, f"4s_{ds[3:]}_{rec}")
    return np.load(os.path.join(dump, "meta", tag + ".npz"), allow_pickle=True)["names"]


def _path(ds, rec, name):
    key = str(int(name)) if np.issubdtype(type(name), np.number) else os.path.basename(str(name)).split(".")[0]
    if ds.startswith("4s:"):
        d = _CAM0.get(rec); return os.path.join(d, key + ".png") if d else None
    d = _IMG.get(rec); return os.path.join(d, key + ".jpg") if d else None


def image_paths(ds, dump, ep, check=None):
    """(query paths, full-map paths); None where the image is not mounted"""
    _scan(); qrecs = list(dict.fromkeys(ep.q_rec)); qp = []
    for r in qrecs: qp += [_path(ds, r, n) for n in _names(dump, ds, r)]
    mp = [_path(ds, ep.ref, n) for n in _names(dump, ds, ep.ref)]
    assert len(qp) == len(ep.q) and len(mp) == len(ep.m), (len(qp), len(ep.q), len(mp), len(ep.m))
    if check is None: check = not ds.startswith("4s:")      # 4Seasons cam0 paths are deterministic; stat() of ~20k PNGs on /kaggle/input costs 10-17 min
    if check:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(32) as ex:
            okq = list(ex.map(lambda p: p is not None and os.path.exists(p), qp)); okm = list(ex.map(lambda p: p is not None and os.path.exists(p), mp))
        qp = [p if o else None for p, o in zip(qp, okq)]; mp = [p if o else None for p, o in zip(mp, okm)]
    return qp, mp
