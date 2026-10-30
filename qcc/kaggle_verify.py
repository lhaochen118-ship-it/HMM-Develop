"""Run the official invsqrt verifier on candidate circuits in Kaggle CPU sessions.

Each kernel is a self-contained script: candidates (lzma + base64) and the verifier are embedded,
kickmix comes from PyPI, so no dataset is needed and concurrent kernels cannot race on versions.

    python kaggle_verify.py --acc nhatlong1103 --slug qcc-v-refit1 cand1.kmx [cand2.kmb ...] \
        [--verifier PATH] [--args "--shots-per-x 64"] [--launch]

Without --launch it only writes the kernel directory (`runs/<slug>/kernel`). With --launch it
starts `automation/run_kernel.py` in the background (stall 300 s, 4 restarts) writing
`runs/<slug>/run.log`; the last line becomes `STATUS=DONE:<state>` and results land in
`runs/<slug>/out/results.json`.
"""

from __future__ import annotations

import argparse
import base64
import json
import lzma
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = Path(os.environ.get('QCC_RUNS', HERE / 'runs'))
DEFAULT_VERIFIER = os.environ.get('QCC_VERIFIER', '')

KERNEL = r'''
import base64, json, lzma, os, subprocess, sys, time
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'kickmix==1.0.0'], check=True)
W = '/kaggle/working'
FILES = json.loads(lzma.decompress(base64.b64decode(BLOB)))
os.makedirs(W + '/c', exist_ok=True)
for name, text in FILES.items():
    mode = 'wb' if name.endswith('.kmb') else 'w'
    data = base64.b64decode(text) if name.endswith('.kmb') else text
    with open(f'{W}/c/{name}', mode) as f:
        f.write(data)
results = {}
for name in sorted(FILES):
    if name == 'verify_submission_invsqrt.py':
        continue
    t = time.time()
    r = subprocess.run([sys.executable, f'{W}/c/verify_submission_invsqrt.py', f'{W}/c/{name}', *ARGS],
                       capture_output=True, text=True)
    try:
        res = json.loads(r.stdout)
    except Exception:
        res = {'status': 'CRASH', 'stdout': r.stdout[-2000:], 'stderr': r.stderr[-2000:]}
    res['wall_s'] = round(time.time() - t, 1)
    results[name] = res
    print(name, json.dumps(res), flush=True)
    json.dump(results, open(f'{W}/results.json', 'w'), indent=1)
print('ALL_DONE', flush=True)
'''


def build(acc: str, slug: str, cands: list[str], verifier: str, vargs: list[str]) -> Path:
    files = {'verify_submission_invsqrt.py': Path(verifier).read_text()}
    for c in cands:
        p = Path(c)
        files[p.name] = (base64.b64encode(p.read_bytes()).decode() if p.suffix == '.kmb' else p.read_text())
    blob = base64.b64encode(lzma.compress(json.dumps(files).encode(), preset=9)).decode()
    kdir = RUNS / slug / 'kernel'
    kdir.mkdir(parents=True, exist_ok=True)
    (kdir / 'main.py').write_text(f'BLOB = {blob!r}\nARGS = {vargs!r}\n' + KERNEL)
    (kdir / 'kernel-metadata.json').write_text(json.dumps({
        'id': f'{acc}/{slug}', 'title': slug, 'code_file': 'main.py', 'language': 'python',
        'kernel_type': 'script', 'is_private': True, 'enable_gpu': False, 'enable_internet': True,
        'dataset_sources': [], 'competition_sources': [], 'kernel_sources': []}, indent=1))
    print(f'{kdir}: {len(blob) // 1024} KB payload, {len(cands)} candidates')
    return kdir


def launch(kdir: Path) -> None:
    run = kdir.parent
    log = open(run / 'run.log', 'w')
    subprocess.Popen([sys.executable, str(HERE.parent / 'automation' / 'run_kernel.py'), str(kdir),
                      str(run / 'out'), '300', '4', '10800'], stdout=log, stderr=subprocess.STDOUT,
                     start_new_session=True)
    with open(RUNS / 'active_runs.txt', 'a') as f:
        f.write(run.name + '\n')
    print('launched', run.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cands', nargs='+')
    ap.add_argument('--acc', required=True)
    ap.add_argument('--slug', required=True)
    ap.add_argument('--verifier', default=DEFAULT_VERIFIER)
    ap.add_argument('--args', default='')
    ap.add_argument('--launch', action='store_true')
    a = ap.parse_args()
    kdir = build(a.acc, a.slug, a.cands, a.verifier, a.args.split())
    if a.launch:
        launch(kdir)


if __name__ == '__main__':
    main()
