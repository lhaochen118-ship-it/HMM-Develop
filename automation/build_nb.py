#!/usr/bin/env python3
"""Build DIVE-HMM CCBF NB1 .ipynb from .src cell files.

Cell format inside each *.src file:
    #%%MARKDOWN   -> start a markdown cell
    #%%CODE       -> start a code cell
Everything until the next marker (or EOF) is that cell's source.
Files are concatenated in sorted filename order.

After building, every code cell is compiled (syntax check) and the
notebook is validated with nbformat.
"""
import sys, glob, os
import nbformat as nbf

_BASE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_BASE, "DIVE_HMM_CCBF_NB1.ipynb")
SRC_DIR = os.path.join(_BASE, sys.argv[2]) if len(sys.argv) > 2 else os.path.join(_BASE, "nb_src")

MARKERS = {"#%%MARKDOWN": "markdown", "#%%CODE": "code"}


def parse_cells(text):
    cells = []
    cur_type = None
    cur_lines = []

    def flush():
        if cur_type is None:
            return
        src = "\n".join(cur_lines).strip("\n")
        # drop fully-empty trailing cells
        if src.strip() == "" and cur_type == "code":
            return
        cells.append((cur_type, src))

    for line in text.splitlines():
        stripped = line.rstrip("\r")
        if stripped in MARKERS:
            flush()
            cur_type = MARKERS[stripped]
            cur_lines = []
        else:
            if cur_type is not None:
                cur_lines.append(stripped)
    flush()
    return cells


def main():
    files = sorted(glob.glob(os.path.join(SRC_DIR, "*.src")))
    if not files:
        print("No .src files found in", SRC_DIR)
        sys.exit(1)
    all_cells = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            all_cells.extend(parse_cells(fh.read()))
    print(f"Parsed {len(all_cells)} cells from {len(files)} files.")

    nb = nbf.v4.new_notebook()
    nb_cells = []
    n_code = 0
    errors = []
    for i, (ctype, src) in enumerate(all_cells):
        if ctype == "markdown":
            nb_cells.append(nbf.v4.new_markdown_cell(src))
        else:
            n_code += 1
            try:
                compile(src, f"<cell {i}>", "exec")
            except SyntaxError as e:
                errors.append((i, str(e)))
            nb_cells.append(nbf.v4.new_code_cell(src))
    nb["cells"] = nb_cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
        "accelerator": "GPU",
    }

    if errors:
        print(f"\n!!! {len(errors)} SYNTAX ERRORS in code cells:")
        for idx, msg in errors:
            print(f"  cell {idx}: {msg}")
        sys.exit(2)

    nbf.validate(nb)
    with open(OUT, "w", encoding="utf-8") as fh:
        nbf.write(nb, fh)
    print(f"OK: {n_code} code cells compiled clean. Wrote {OUT}")
    print(f"Total cells: {len(nb_cells)}")


if __name__ == "__main__":
    main()
