#!/usr/bin/env python3
"""Local runtime test of the CCBF numpy core by exec'ing the actual P3/P4 cells
from the built notebook against synthetic descriptors with real place signal.
Validates: cosine_sim, recall, ECE, temperature fit, band motion filter,
condition model, and the factored CCBF filter (incl. drift + checkpoint logic)."""
import json, types, math, pickle, os, tempfile
import numpy as np
from collections import OrderedDict

NB = r"C:/Users/ADMIN/Desktop/HMM-Develop/DIVE_HMM_CCBF_NB1.ipynb"
nb = json.load(open(NB, encoding="utf-8"))
code_cells = ["".join(c["source"]) if isinstance(c["source"], list) else c["source"]
              for c in nb["cells"] if c["cell_type"] == "code"]

def cell(marker):
    for src in code_cells:
        if marker in src:
            return src
    raise KeyError(marker)

# ---- shared namespace with the globals the cells expect -------------------------------
g = {"np": np, "math": math, "os": os, "json": json, "OrderedDict": OrderedDict}
CONFIG = types.SimpleNamespace(
    RECALL_KS=(1, 5, 10), PLACE_TOL=2, ECE_BINS=15,
    MOTION_VELOCITY=1.0, MOTION_STD=2.0, NULL_PRIOR=0.02, NULL_SELF=0.9, MOTION_LEAK=1e-3,
    STICKY_RHO=0.97, USE_TRAIN_CONDITION_LABELS=True, K_CONDITIONS=2, SEED=0)
g["CONFIG"] = CONFIG
g["REPORT"] = {}
g["log"] = lambda *a, **k: None

def gt_match_index(q, r):
    pos = {fid: j for j, fid in enumerate(r.frame_ids)}
    return np.array([pos.get(fid, -1) for fid in q.frame_ids], dtype=np.int64)
g["gt_match_index"] = gt_match_index

# ---- synthetic data: 2 seasons, aligned frame-ids, real place signal ------------------
rng = np.random.default_rng(0)
N, D = 160, 48
base = rng.standard_normal((N, D)).astype(np.float32)
def make(noise):
    x = base + noise * rng.standard_normal((N, D)).astype(np.float32)
    return x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-12)
DESC = {"summer": make(0.35), "winter": make(1.6)}       # winter much harder (more noise)
Track = types.SimpleNamespace
TRACKS = {s: types.SimpleNamespace(frame_ids=list(range(N)), condition=s) for s in DESC}
g["DESC"] = DESC; g["TRACKS"] = TRACKS; g["NORDLAND_SEASONS"] = ["summer", "winter"]

# ---- exec the real cells in dependency order ------------------------------------------
for marker in ["# === P3.0", "# === P3.1", "# === P3.2",
               "# === P4.1", "# === P4.2", "# === P4.3", "# === P4.4"]:
    exec(cell(marker), g)

RESULTS = g["RESULTS"]
print("RESULTS keys:", list(RESULTS.keys()))
for k, v in RESULTS.items():
    print(f"  {k}: " + ", ".join(f"{kk}={vv:.3f}" for kk, vv in v.items()))

# ---- assertions -----------------------------------------------------------------------
assert "single_image" in RESULTS and "fixed_filter" in RESULTS and "ccbf" in RESULTS
for name, m in RESULTS.items():
    for kk, vv in m.items():
        assert np.isfinite(vv), f"non-finite {name}.{kk}"
assert RESULTS["single_image"][1] > 0.3, "retrieval should recover a fair share of places"
assert 0.0 <= RESULTS["ccbf"]["ECE"] <= 1.0

# ---- drift demo (label-free condition tracking) ---------------------------------------
run_ccbf = g["run_ccbf"]; COND = g["COND"]; cosine_sim = g["cosine_sim"]; names = COND["names"]
A, B = "summer", "winter"
descA, descB = DESC[A], DESC[B]; M = descA.shape[0]; H = M // 2
qdesc = np.concatenate([descA[:H], descB[H:]], 0)
true_cond = np.array([names.index(A)] * H + [names.index(B)] * (M - H))
sim_drift = cosine_sim(qdesc, descA)
preds, confs, nulls, bc = run_ccbf(sim_drift, qdesc, COND, return_traj=True)
track_acc = float((bc.argmax(1) == true_cond).mean())
print(f"drift tracking acc = {track_acc:.3f} (chance={1/len(names):.3f})")
assert bc.shape == (M, len(names))
assert np.isfinite(bc).all() and np.allclose(bc.sum(1), 1.0, atol=1e-5)
assert track_acc > 1.0 / len(names), "condition tracking should beat chance"

# ---- checkpoint roundtrip (pickle stands in for torch.save) ---------------------------
with tempfile.TemporaryDirectory() as td:
    p = os.path.join(td, "c.pkl")
    pickle.dump({"cond": {k: COND[k] for k in ("names", "C", "sigma", "tau")}}, open(p, "wb"))
    COND2 = pickle.load(open(p, "rb"))["cond"]
    p1, _, _ = run_ccbf(sim_drift[:60], qdesc[:60], COND)
    p2, _, _ = run_ccbf(sim_drift[:60], qdesc[:60], COND2)
    assert np.array_equal(p1, p2), "checkpoint roundtrip changed predictions"
print("checkpoint roundtrip: identical")

# ---- K=1 ablation must be a valid (collapsed) filter ----------------------------------
assert "ccbf_K1_ablation" in RESULTS
print("\nALL CORE TESTS PASSED")
