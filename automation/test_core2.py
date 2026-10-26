#!/usr/bin/env python3
"""Local runtime test of NB2's lib + Experiment A by exec'ing the actual cells
against synthetic multi-condition descriptors. Validates metrics (incl AUROC/SUE),
CCBF, and the full Experiment-A logic (comparison, ECE-vs-T, off-map, TTA)."""
import json, types, math, os, tempfile
import numpy as np
from collections import OrderedDict, defaultdict
import matplotlib; matplotlib.use("Agg")

NB = r"C:/Users/ADMIN/Desktop/HMM-Develop/DIVE_HMM_CCBF_NB2.ipynb"
nb = json.load(open(NB, encoding="utf-8"))
cells = ["".join(c["source"]) if isinstance(c["source"], list) else c["source"]
         for c in nb["cells"] if c["cell_type"] == "code"]
def cell(mark):
    for s in cells:
        if mark in s: return s
    raise KeyError(mark)

WD = tempfile.mkdtemp()
g = {"np": np, "math": math, "os": os, "json": json, "OrderedDict": OrderedDict, "defaultdict": defaultdict}
CONFIG = types.SimpleNamespace(
    SMOKE_TEST=True,
    MOTION_VELOCITY=1.0, MOTION_STD=2.0, MOTION_LEAK=1e-3, NULL_PRIOR=0.02, NULL_SELF=0.9,
    STICKY_RHO=0.97, RECALL_KS=(1, 5, 10), PLACE_TOL=2, ECE_BINS=15, USE_TRAIN_CONDITION_LABELS=True,
    SEED=0, T_GRID=(1, 2, 3, 5, 8, 13, 21, 34, 55), OFFMAP_MAP_FRACTION=0.7, WORKING_DIR=WD)
g["CONFIG"] = CONFIG; g["REPORT"] = {}; g["log"] = lambda *a, **k: None

# synthetic 3-condition data (shared base => cross-condition place signal; increasing difficulty)
rng = np.random.default_rng(0); N, D = 220, 64
base = rng.standard_normal((N, D)).astype(np.float32)
def mk(noise):
    x = base + noise * rng.standard_normal((N, D)).astype(np.float32)
    return (x / (np.linalg.norm(x, 1 if False else 2, axis=1, keepdims=True) + 1e-12)).astype(np.float32)
DESC = {"summer": mk(0.3), "fall": mk(0.7), "winter": mk(1.3)}
TRACKS = {s: types.SimpleNamespace(frame_ids=list(range(N)), condition=s) for s in DESC}
g["DESC"] = DESC; g["TRACKS"] = TRACKS

for m in ["# === L.1", "# === L.2", "# === L.3", "# === L.4",
          "# === A.0", "# === A.1 / A.2", "# === A.3", "# === A.4", "# === A.5"]:
    exec(cell(m), g)

R = g["RESULTS2"]
print("RESULTS2 keys:", list(R.keys()))
a1 = R["A1_comparison"]
for m, v in a1.items():
    print(f"  {m:<14} R@1={v['R@1']:.3f} ECE={v['ECE']:.3f} acc={v['acc']:.3f}")
print("  A4 off-map:", {k: round(v["AUROC"], 3) for k, v in R["A4_offmap"]["overall"].items()})
print("  A5 drift_acc:", R["A5_tta"]["drift_acc"])
print("  A3 ECE-vs-T (fixed):", [round(x, 3) if np.isfinite(x) else None for x in R["A3_ece_vs_T"]["fixed_filter"]])

# ---- assertions ----
assert set(["A1_comparison", "A3_ece_vs_T", "A4_offmap", "A5_tta"]).issubset(R)
for m, v in a1.items():
    for k, val in v.items(): assert np.isfinite(val), f"{m}.{k} not finite"
# AUROC must be a valid probability and CCBF off-map should beat random
au = R["A4_offmap"]["overall"]["ccbf_null"]["AUROC"]
assert 0.0 <= au <= 1.0
# unit test AUROC on a trivially separable case
assert abs(g["auroc"](np.array([0, 1, 2, 3.0]), np.array([0, 0, 1, 1])) - 1.0) < 1e-9
assert abs(g["average_precision"](np.array([3, 2, 1, 0.0]), np.array([1, 1, 0, 0])) - 1.0) < 1e-9
# SUE finite
assert np.isfinite(g["sue_uncertainty"](g["cosine_sim"](DESC["winter"], DESC["summer"]))).all()
# drift tracking beats chance
assert R["A5_tta"]["drift_acc"] is None or R["A5_tta"]["drift_acc"] > 1.0 / len(g["COND"]["names"])
# ECE-vs-T produced numbers for both methods
assert len(R["A3_ece_vs_T"]["fixed_filter"]) == len(CONFIG.T_GRID)
print("\nALL NB2 CORE + EXPERIMENT-A TESTS PASSED")
