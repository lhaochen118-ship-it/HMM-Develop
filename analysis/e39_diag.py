"""Entry 39 diagnostics of the edge excess (labels only to evaluate; pre-registered as D39-pi and D39-margin).
D39-pi   share pi of the virtual exits (mode 0 of the corridor forward null) whose exit frame is truly on-map with a correct belief
         (inm and |MP[est_c] - q_pos| <= excl); pi_edge = the same over the exits that produced a position-0 virtual off-map segment.
         Proposition 19 bounds the report rate of a real segment by a (n+1) / (pi n + 1) ~ a / pi.
D39-margin  edge / start / deep report rates of a rule when real off-map segments are redefined at off_d + delta (true distance to the
         nearest remaining map place), and the share of edge reports whose fix error is < off_d + 10 m (or + 2 frames, Nordland).
Usage: e39_diag.py <navcache_dir> <fwd_dir> <frames_dir> <lab e37|e38> <out.json> [--runs regex] [--jobs 3]"""
import sys, os, glob, re, json
import numpy as np
from multiprocessing import Pool
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e37_audit import seg_classes, dataset_of
from cms_fwd import OFF_D, load_recs

A = 0.05
RULES = ["CMS-CPC/H+CSTJS+G+NGRr", "CMS-CPC/H+CSTJSU+G+NGRr", "CMS-CPC/H+CSTJSU+G[both]+NGRr", "CMS-CPC/H+SH+CSTJS+G+NGRr", "CMS-CPC/H+SH+G+NGRr"]


def one(args):
    nf, fdir, frdir, lab = args
    tag = os.path.basename(nf)[9:-4]; base, seed = tag.rsplit("_s", 1); ds = dataset_of(tag); off_d = OFF_D[ds.split("_")[0]]
    z = np.load(nf, allow_pickle=True); zz = {k: z[k] for k in z.files}
    MP = np.asarray(z["MP"], float); qp = np.asarray(z["q_pos"], float); hz = list(z["hz"]); excl = float(z["excl"])
    P2 = MP[:, hz] if MP.ndim > 1 and MP.shape[1] > 2 else (MP if MP.ndim > 1 else MP[:, None])
    Q2 = qp[:, hz] if qp.ndim > 1 and qp.shape[1] > 2 else (qp if qp.ndim > 1 else qp[:, None])
    dmap, _ = cKDTree(P2).query(Q2)
    est = np.asarray(z["est_c"]); good = np.asarray(z["inm"], bool) & (np.linalg.norm(P2[est] - Q2, axis=1) <= excl)
    res = {"ds": ds}
    ff = os.path.join(fdir, f"fwd_{tag}.npz")
    if os.path.exists(ff):
        recs, _ = load_recs(ff); ex = np.array([r[0] for r in recs if r[5] == 0])
        ex0 = np.array([r[0] for r in recs if r[5] == 0 and r[3].any()])
        res["n_exit"], res["pi"] = len(ex), float(good[ex].mean()) if len(ex) else None
        res["n_exit_off"], res["pi_edge"] = len(ex0), float(good[ex0].mean()) if len(ex0) else None
    fr = os.path.join(frdir, f"frames_{base}_{lab}_s{seed}.npz")
    if os.path.exists(fr):
        F = np.load(fr, allow_pickle=True); names = list(F["names"])
        unit = 1.0 if ds.startswith("nord") else 1.0
        deltas = (0, 1, 2, 5) if ds.startswith("nord") else (0, 5, 10, 20)
        for dl in deltas:
            zz["offm"] = dmap > off_d + dl
            segs = seg_classes(zz, off_d)
            n = {c: sum(1 for _, c_ in segs if c_ == c) for c in ("start", "edge", "deep")}; r_ = {"n": n}
            for rl in RULES:
                if rl not in names: continue
                a = F["acc"][names.index(rl)].astype(bool)
                r_[rl] = {c: int(sum(bool(a[g].any()) for g, c_ in segs if c_ == c)) for c in ("start", "edge", "deep")}
            res[f"d{dl}"] = r_
        zz["offm"] = np.asarray(z["offm"], bool); segs = seg_classes(zz, off_d); marg = off_d + (2 if ds.startswith("nord") else 10)
        for rl in RULES:
            if rl not in names: continue
            i = names.index(rl); a = F["acc"][i].astype(bool); xf = np.asarray(F["xf"][i], float)
            xf2 = xf[:, hz] if xf.ndim > 1 and xf.shape[1] > 2 else (xf if xf.ndim > 1 else xf[:, None])
            errs = [np.linalg.norm(xf2[g][a[g]] - Q2[g][a[g]], axis=1).min() for g, c_ in segs if c_ == "edge" and a[g].any()]
            res.setdefault("edge_err", {})[rl] = (len(errs), int(sum(e < marg for e in errs)))
    return tag, res


def main():
    nd, fdir, frdir, lab, out = sys.argv[1:6]
    rx = sys.argv[sys.argv.index("--runs") + 1] if "--runs" in sys.argv else "."
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 3
    fs = [f for f in sorted(glob.glob(os.path.join(nd, "navcache_*.npz"))) if re.search(rx, os.path.basename(f))]
    with Pool(jobs) as p: R = dict(p.map(one, [(f, fdir, frdir, lab) for f in fs], chunksize=1))
    json.dump(R, open(out, "w"), indent=1)
    agg = {}
    for tag, r in R.items():
        a = agg.setdefault(r["ds"], {"pi": [], "pie": [], "cnt": {}, "err": {}})
        if r.get("pi") is not None: a["pi"].append((r["pi"], r["n_exit"])); a["pie"].append((r["pi_edge"] or 0, r["n_exit_off"]))
        for k, v in r.items():
            if k.startswith("d") and isinstance(v, dict) and "n" in v:
                c = a["cnt"].setdefault(k, {"n": {"start": 0, "edge": 0, "deep": 0}})
                for cl in ("start", "edge", "deep"): c["n"][cl] += v["n"][cl]
                for rl in RULES:
                    if rl in v:
                        for cl in ("start", "edge", "deep"): c.setdefault(rl, {"start": 0, "edge": 0, "deep": 0})[cl] += v[rl][cl]
        for rl, (n_, m_) in r.get("edge_err", {}).items():
            e = a["err"].setdefault(rl, [0, 0]); e[0] += n_; e[1] += m_
    for ds, a in sorted(agg.items()):
        w = lambda L: sum(x * n for x, n in L) / max(sum(n for _, n in L), 1)
        pi, pie = w(a["pi"]), w(a["pie"])
        print(f"{ds}: pi {pi:.3f}, pi_edge {pie:.3f}, a/pi_edge {A / max(pie, 1e-9):.3f}")
        for k in sorted(a["cnt"], key=lambda s: int(s[1:])):
            c = a["cnt"][k]; line = f"   off_d+{k[1:]:>2s}: n {c['n']['start']}/{c['n']['edge']}/{c['n']['deep']}"
            for rl in RULES[:3]:
                if rl in c:
                    line += f" | {rl.split('+')[1] + ('[both]' if 'both' in rl else '')} " + "/".join(f"{c[rl][cl] / c['n'][cl]:.3f}" if c['n'][cl] else "-" for cl in ("start", "edge", "deep"))
            print(line)
        for rl, (n_, m_) in a["err"].items():
            if rl in RULES[:3]: print(f"   edge reports with fix error < off_d + margin, {rl}: {m_}/{n_} = {m_ / max(n_, 1):.2f}")


if __name__ == "__main__":
    main()
