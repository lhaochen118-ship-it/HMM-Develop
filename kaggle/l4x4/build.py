#!/usr/bin/env python3
"""Build one Kaggle kernel (script) that runs a list of k11/k09 tasks on every GPU of the session.
Usage:
  build.py <out_dir> <owner/slug> <tier l4|t4> <run_id> [--smoke] [--wpg N] [--ds a,b,c] TASK...
TASK = k11:<path to an existing single-GPU k11.py>:<name>:<family cmu|4s>:<dataset slug substring>
     | k09:<path to an existing single-GPU k09.py>:<dataset slug substring>
The CFG / PAIRS payloads are decoded from the single-GPU scripts (kaggle/k11_6dof, kaggle/k09_geo templates), so the
inputs are byte-identical to the paused jobs. Metadata for tier l4: machine_shape NvidiaL4 + competition grant
gemma-4-developer-agent (read from the user's L4 notebook with `kaggle kernels pull -m`; user confirmed the grant is
allowed, 28/11/2026). Tier t4: machine_shape NvidiaTeslaT4, no competition."""
import os, sys, re, json, zlib, base64

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["common.py", "launcher.py", "worker.py", "task_k11.py", "task_k09.py"]


def payload(path):
    s = open(path).read()
    m = re.search(r'b64decode\("([A-Za-z0-9+/=]+)"\)', s)
    obj = json.loads(zlib.decompress(base64.b64decode(m.group(1))))
    dc = re.search(r'DS, CHUNK = "([^"]+)", "([^"]+)"', s)
    return obj, (dc.groups() if dc else None)


def main(a):
    out, kid, tier, run_id = a[:4]; rest = a[4:]
    smoke = "--smoke" in rest
    wpg = int(rest[rest.index("--wpg") + 1]) if "--wpg" in rest else 3
    ds = rest[rest.index("--ds") + 1].split(",") if "--ds" in rest else []
    pds = rest[rest.index("--payload-dataset") + 1] if "--payload-dataset" in rest else None
    tasks = {}
    for t in [x for x in rest if x.startswith(("k11:", "k09:"))]:
        f = t.split(":")
        if f[0] == "k11":
            cfg, _ = payload(f[1]); tid = f"k11_{f[2]}"
            tasks[tid] = {"kind": "k11", "task_id": tid, "name": f[2], "family": f[3], "slug": f[4], "CFG": cfg}
        else:
            pairs, (dsn, chunk) = payload(f[1]); tid = f"k09_{dsn}_{chunk}"
            tasks[tid] = {"kind": "k09", "task_id": tid, "ds": dsn, "chunk": chunk, "slug": f[2], "PAIRS": pairs}
    bundle = {"opts": {"run_id": run_id, "smoke": smoke, "wpg": wpg, "requested": tier,
                       "requested_gpus": 4 if tier == "l4" else 1},
              "tasks": tasks, "files": {n: open(os.path.join(HERE, n)).read() for n in FILES}}
    if pds:                                # Kaggle refuses scripts > ~1 MB: ship the task payload as a dataset
        tf = f"tasks_{run_id}.json"; pdir = os.path.join(out, "payload"); os.makedirs(pdir, exist_ok=True)
        json.dump(tasks, open(os.path.join(pdir, tf), "w"))
        json.dump({"title": pds.split("/")[1], "id": pds, "licenses": [{"name": "CC0-1.0"}]},
                  open(os.path.join(pdir, "dataset-metadata.json"), "w"))
        bundle["tasks"] = {}; bundle["tasks_file"] = tf; ds = ds + [pds]
    b64 = base64.b64encode(zlib.compress(json.dumps(bundle).encode(), 9)).decode()
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "run.py"), "w") as f:
        f.write('"""HMM L4x4 runner (kaggle/l4x4 in branch claude/nice-fermi-l7bzd6): ' + run_id + '"""\n'
                "import os, sys, json, zlib, base64\n"
                f'BUNDLE = json.loads(zlib.decompress(base64.b64decode("{b64}")))\n'
                'JOBD = os.environ.setdefault("HMMJOB_DIR", "/kaggle/tmp/hmmjob"); os.makedirs(JOBD, exist_ok=True)\n'
                'for _n, _s in BUNDLE["files"].items():\n'
                '    open(os.path.join(JOBD, _n), "w").write(_s)\n'
                'if "tasks_file" in BUNDLE:\n'
                '    for _d, _s, _f in os.walk("/kaggle/input"):\n'
                '        if _d.count(os.sep) >= 6: _s[:] = []\n'
                '        if BUNDLE["tasks_file"] in _f:\n'
                '            BUNDLE["tasks"] = json.load(open(os.path.join(_d, BUNDLE["tasks_file"]))); break\n'
                '    print("payload", BUNDLE["tasks_file"], "tasks", sorted(BUNDLE["tasks"]), flush=True)\n'
                "sys.path.insert(0, JOBD)\n"
                "import launcher\n"
                "launcher.main(BUNDLE)\n")
    meta = {"id": kid, "title": kid.split("/")[1], "code_file": "run.py", "language": "python",
            "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_tpu": False,
            "enable_internet": False, "dataset_sources": ds, "kernel_sources": [], "model_sources": [],
            "competition_sources": ["gemma-4-developer-agent"] if tier == "l4" else [],
            "machine_shape": "NvidiaL4" if tier == "l4" else "NvidiaTeslaT4"}
    json.dump(meta, open(os.path.join(out, "kernel-metadata.json"), "w"), indent=2)
    print(f"built {out}: {len(tasks)} tasks {sorted(tasks)} | run.py {os.path.getsize(os.path.join(out, 'run.py')) / 1e6:.2f} MB | tier {tier} smoke={smoke}")


if __name__ == "__main__":
    main(sys.argv[1:])
