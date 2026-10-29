"""Natural off-map excursions for certified sequential localization: every query sequence of OTHER scenes / datasets is
driven against a map (so every H-frame segment is a true off-map excursion, no leave-block-out simulation), with its own
odometry (4Seasons: real VIO; others: simulated from their GT). The threshold is the map-calibrated one of cert_seq.py
(seed-0 block grid, cross-fitted per-frame test). Statistics: FRAME, ANCH (heading from the source's own frame, i.e.
misaligned with the map: a deliberately unfavourable case) and ANCHR (heading fitted per window).
Usage: cert_natural.py <dump> <map: 4s:<scene>|cmu|rc|boreas> <desc> <src,src,...> [H=10,30]
  src = 4s:<scene> | cmu | rc | boreas  -> results/natural_<map>_<desc>.json"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V, selfcal as SC
from sc_eval import CFG
from cert_seq import running, chunks, odometry_sim, odometry_real

A = (0.01, 0.05, 0.1)


def load(dump, spec, desc):
    if spec.startswith("4s:"): return V.load_4seasons(dump, desc, spec[3:]), CFG["cmu"]
    if spec == "boreas": return V.load_boreas(dump, desc), CFG["cmu"]
    return V.LOADERS[spec](dump, desc), CFG[spec]


def main():
    dump, mspec, desc, srcs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(",")
    HS = [int(h) for h in sys.argv[5].split(",")] if len(sys.argv) > 5 else [10, 30]
    ep, c = load(dump, mspec, desc); rho_o = 5.0; rng = np.random.default_rng(0)
    _, _, m_sid, m_k = V.frame_order(dump, mspec, ep, desc)
    m_seqs = [np.where(m_sid == s)[0][np.argsort(m_k[m_sid == s])] for s in np.unique(m_sid)]
    mr = ep.m.astype(np.float32); mu = mr.mean(0, keepdims=True); nrm = lambda x: x / np.linalg.norm(x, axis=1, keepdims=True); mc = nrm(mr - mu)
    args = (c["block"], c["off_d"], c["cell"], c["excl"], c["k"])
    Nr, Nc = SC.map_null(mr, ep.m_pos, *args, stride=1), SC.map_null(mc, ep.m_pos, *args, stride=1)
    bid, _ = V.map_cells(ep.m_pos, c["block"]); half = bid % 2 == 0
    sub = lambda d, m: {kk: np.where(m, v, np.nan) for kk, v in d.items()}
    test = SC.SelfCalTest(SC.pack(sub(Nr, half), sub(Nc, half))); p_null = test.pvalue(**SC.pack(Nr, Nc))
    null_ok = np.isfinite(Nr["maxsim"]) & np.isfinite(Nc["z_far"]) & ~half
    o_m = odometry_sim(ep.m_pos, m_sid, m_k, rng)
    out = {"map": mspec, "desc": desc, "rows": []}
    for kind in ("FRAME", "ANCH", "ANCHR"):
        for H in HS:
            Rn = np.full(len(ep.m), np.nan)
            for order in m_seqs:
                for ch in chunks(order, null_ok, bid): Rn[ch] = running(p_null, Nr["top"], np.array(ch), o_m, ep.m_pos, kind, c["excl"], rho_o, H)
            nseg = [s for order in m_seqs for ch in chunks(order, null_ok, bid) for s in (ch[i:i + H] for i in range(0, len(ch) - H + 1, H))]
            ns = np.sort([Rn[s].max() for s in nseg])
            thr = {a: (ns[int(np.ceil((1 - a) * (len(ns) + 1))) - 1] if np.ceil((1 - a) * (len(ns) + 1)) <= len(ns) else np.inf) for a in A}
            for src in srcs:
                if src == mspec: continue
                es, _ = load(dump, src, desc); q_sid, q_k, _, _ = V.frame_order(dump, src, es, desc)
                q = es.q.astype(np.float32); qc = nrm(q - mu)
                Fr, Fc = SC.qm_stats(q, mr, ep.m_pos, c["cell"], c["excl"], c["k"]), SC.qm_stats(qc, mc, ep.m_pos, c["cell"], c["excl"], c["k"])
                p_q = test.pvalue(**SC.pack(Fr, Fc))
                o_q = odometry_real(es, q_sid, q_k)
                if o_q is None: o_q = odometry_sim(es.q_pos, q_sid, q_k, rng)
                if o_q.shape[1] != ep.m_pos.shape[1]:                     # pad / cut odometry to the map's dimension
                    o_q = np.pad(o_q, ((0, 0), (0, max(0, ep.m_pos.shape[1] - o_q.shape[1]))))[:, :ep.m_pos.shape[1]]
                seqs = [np.where(q_sid == s)[0][np.argsort(q_k[q_sid == s])] for s in np.unique(q_sid)]
                Rq = np.full(len(q), np.nan)
                for order in seqs: Rq[order] = running(p_q, Fr["top"], order, o_q, ep.m_pos, kind, c["excl"], rho_o, H)
                seg = [order[i:i + H] for order in seqs for i in range(0, len(order) - H + 1, H)]
                smax = np.array([Rq[s].max() for s in seg])
                row = dict(kind=kind, H=H, src=src, n_null_seg=len(ns), n_seg=len(seg), FAR={str(a): float((smax > thr[a]).mean()) for a in A},
                           frame_FAR={str(a): float((Rq > thr[a]).mean()) for a in A})
                out["rows"].append(row)
                print(f"{mspec}/{desc} {kind:5s} H={H:2d} src {src:16s} nullseg {len(ns):4d} segs {len(seg):5d} | excursion FAR "
                      + " ".join(f"a={a}:{row['FAR'][str(a)]:.3f}" for a in A), flush=True)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(f"results/natural_{mspec.replace(':', '_')}_{desc}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
