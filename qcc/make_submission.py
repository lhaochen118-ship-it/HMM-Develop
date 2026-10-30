"""Assemble submission.zip: our invsqrt plus the dqi and dfthcsos circuits from given sources.

    python make_submission.py --invsqrt inv.kmb --dqi dqi.kmb --chem chem_dir --out submission.zip

`chem_dir` holds angle_k_0..angle_k_{n-1} (.kmb/.kmx) and submission.npz. A .kmx invsqrt is
converted to .kmb first (the verifier hashes the canonical .kmb either way).
"""

from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--invsqrt', required=True)
    ap.add_argument('--dqi', required=True)
    ap.add_argument('--chem', required=True)
    ap.add_argument('--out', default='submission.zip')
    args = ap.parse_args()

    inv = Path(args.invsqrt)
    if inv.suffix == '.kmx':
        import kickmix as km
        kmb = inv.with_suffix('.kmb')
        km.Circuit.from_file(str(inv), format='kmx').to_file(str(kmb), format='kmb')
        inv = kmb
    chem = Path(args.chem)
    angles = sorted(chem.glob('angle_k_*.km[bx]'), key=lambda p: int(re.findall(r'\d+', p.stem)[0]))
    assert [int(re.findall(r'\d+', p.stem)[0]) for p in angles] == list(range(len(angles))), 'angle gaps'
    with zipfile.ZipFile(args.out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(inv, 'invsqrt.kmb')
        z.write(args.dqi, 'dqi' + Path(args.dqi).suffix)
        for p in angles + [chem / 'submission.npz']:
            z.write(p, f'dfthcsos/{p.name}')
    print(f'{args.out}: invsqrt {sha(inv)}, dqi {sha(Path(args.dqi))}, {len(angles)} angle circuits')


if __name__ == '__main__':
    main()
