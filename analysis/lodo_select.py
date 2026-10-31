"""Leave-one-dataset-out choice among LABEL-FREE rule variants (selection-bias check, as Entry 24 Check 3).

For every held-out dataset D, the variant is chosen on the OTHER datasets only, by a fixed rule:
  among variants whose mean segment FAR at the default point is <= ALPHA on EVERY other dataset, the one with the lowest
  mean (navigation error / oracle error) over the other datasets; ties by higher mean recall.
Reported per D: the chosen variant, its held-out default point, and the regret (held-out err minus the best label-free
variant on D). A method is general if the choice is stable across folds and the regret is small.
Usage: lodo_select.py <results_dir with oc_*.json> [--alpha 0.05] [--cands a,b,...]"""
import sys, os, json, glob
import numpy as np

ALPHA = float(sys.argv[sys.argv.index("--alpha") + 1]) if "--alpha" in sys.argv else 0.05
LABELS = {"Xu21", "Claxton24", "SafeVPR", "max-sim", "oracle", "place conf"}     # use labels or have no default point


def load(rdir):
    D = {}
    for f in sorted(glob.glob(os.path.join(rdir, "oc_*.json"))):
        d = json.load(open(f))
        for run in d["runs"].values():
            og = run["oracle"]["err_mean"]
            for n, fam in run["families"].items():
                if "default" not in fam: continue
                r = fam["default"]
                D.setdefault(d["ds"], {}).setdefault(n, []).append((r["err_mean"] / max(og, 1e-6), r["seg_FAR"], r["recall"], r["err_mean"]))
    return {ds: {n: np.mean(v, 0) for n, v in fams.items()} for ds, fams in D.items()}


def main():
    M = load(sys.argv[1]); dss = sorted(M)
    cands = sys.argv[sys.argv.index("--cands") + 1].split(",") if "--cands" in sys.argv else \
        sorted({n for ds in dss for n in M[ds]} - LABELS)
    cands = [c for c in cands if all(c in M[ds] for ds in dss)]
    print(f"datasets {dss}\ncandidates {cands}\n")
    print("| held-out | chosen on the others | held-out err | recall | segFAR | best label-free on held-out | regret (m) |")
    print("|---|---|---|---|---|---|---|")
    for h in dss:
        others = [d for d in dss if d != h]
        ok = [c for c in cands if all(M[d][c][1] <= ALPHA for d in others)] or cands
        score = {c: (np.mean([M[d][c][0] for d in others]), -np.mean([M[d][c][2] for d in others])) for c in ok}
        ch = min(ok, key=lambda c: score[c])
        valid_h = [c for c in cands if M[h][c][1] <= ALPHA] or cands
        best = min(valid_h, key=lambda c: M[h][c][3])
        e, sfar, rc = M[h][ch][3], M[h][ch][1], M[h][ch][2]
        print(f"| {h} | {ch} | {e:.1f} | {rc:.3f} | {sfar:.3f} | {best} ({M[h][best][3]:.1f}) | {e - M[h][best][3]:.1f} |")


if __name__ == "__main__":
    main()
