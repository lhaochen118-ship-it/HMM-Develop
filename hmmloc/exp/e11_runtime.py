"""E23/H14 — Filter runtime per frame vs map size M and velocity bins K (CPU, numpy+scipy, batch 1).
Excludes descriptor extraction and the similarity product (reported separately)."""
import time, json, os, sys
import numpy as np
from .. import hmm
from .common import ROOT, new_run_id, log_run
out = {}
for M in (1000, 5000, 10000, 30000):
    s = np.arange(M, dtype=float)
    for K in (1, 6):
        ks = [hmm.chain_kernel(s, mean=v, std=1.0) for v in (np.linspace(0, 3, K) if K > 1 else [1.0])]
        cfg = hmm.HMMConfig(ks, Pv=hmm.sticky_velocity(K, 0.9) if K > 1 else None, use_null=True, exit_prob=0.01)
        T = 200; L = np.random.default_rng(0).normal(size=(T, M)).astype(np.float32)
        t0 = time.perf_counter(); hmm.forward(L, cfg, beta=0.5, loglik_null=np.zeros(T), vel_loglik=np.zeros((T, K)) if K > 1 else None)
        ms = (time.perf_counter() - t0) / T * 1e3
        D = 8448; q = np.random.default_rng(1).normal(size=(1, D)).astype(np.float32); R = np.random.default_rng(2).normal(size=(M, D)).astype(np.float32)
        t0 = time.perf_counter(); [q @ R.T for _ in range(20)]; sim_ms = (time.perf_counter() - t0) / 20 * 1e3
        out[f"M{M}_K{K}"] = {"filter_ms": ms, "sim_ms_d8448": sim_ms, "mem_MB_states": M * K * 8 / 1e6}
        print(f"M={M:6d} K={K} filter {ms:7.2f} ms/frame | dense sim (D=8448) {sim_ms:6.2f} ms", flush=True)
rid = new_run_id("E23_runtime")
od = os.path.join(ROOT, "research", "runs", rid); os.makedirs(od, exist_ok=True); json.dump(out, open(os.path.join(od, "metrics.json"), "w"), indent=1)
log_run({"run_id": rid, "task_id": "T3.7", "experiment_id": "E23", "hypothesis_ids": ["H14"], "dataset": "synthetic", "descriptor": "-",
         "status": "ok", "evidence_level": "S", "metrics": out, "compute": {"platform": "local-cpu (4 vCPU, shared with other jobs)"},
         "artifacts": f"research/runs/{rid}"})
print("RUN", rid)
