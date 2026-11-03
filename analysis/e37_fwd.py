"""Entry 37 kernel job: the forward counterfactual null of ONE part of one run (ds, desc, seed), with the system's presence statistics
run forward on every virtual run's altered map (cms_fwd.FwdStats) and both virtual-start families (mode 1: 3 excl, the Entry 36
nulls; mode 2: the exits' full horizon, Entry 37). Exits every 1 excl, horizon 20 excl (as Entry 36).
Usage: e37_fwd.py <dump_dir> <navcache_dir> <ds> <desc> <seed> <k/n> [--wait]  ->  results/fwdp_<tag>_<desc>_s<seed>.p<k>of<n>.npz
(merge the n parts with `cms_fwd.py --merge results/fwd_<tag>_<desc>_s<seed>.npz <parts...>`)."""
import sys, os, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cms_fwd as CF


def main():
    dump, nd, ds, desc, seed, part = sys.argv[1:7]; tag = ds.replace(":", "_"); k, n = map(int, part.split("/"))
    import nav_rules as NR, topk_dump as TKD
    from sc_eval import CFG
    os.makedirs("results", exist_ok=True)
    of = os.path.join("results", f"fwdp_{tag}_{desc}_s{seed}.p{k}of{n}.npz")
    if os.path.exists(of): print(of, "exists"); return
    t0 = time.time(); nf = os.path.join(nd, f"navcache_{tag}_{desc}_s{seed}.npz")
    if "--wait" in sys.argv:                                            # the navcache is written by e37_prep.py in the same kernel
        while not (os.path.exists(nf) and os.path.exists(nf + ".done")):
            if time.time() - t0 > 3600: sys.exit(f"{nf}: not ready after 1 h")
            time.sleep(10)
    z = np.load(nf, allow_pickle=True); zz = {k_: z[k_] for k_ in z.files}
    b = NR.base_parts(z); b = dict(b, seqs=CF.part_seqs(b["seqs"], k, n))
    base = ds.split(":")[0]; c = CFG["cmu"] if base in ("4s", "4sx", "boreas") else CFG[base]   # as nav_demo.main / cms_fwd.main
    ep = TKD.load(dump, ds, desc); q = ep.q; M = ep.m.astype(np.float32)[z["kidx"]]; assert len(q) == len(z["top"])
    tl = time.time() - t0
    R = CF.fwd_null(zz, b, q, M, c, stride="1x", horizon=20.0, presence=True, start_h=(None, "full"), ds=ds)
    CF.save(of, R); open(of + ".done", "w").write("ok")                # complete-file marker for e37_eval.py --wait
    nf = R["n_frames"]; dt = time.time() - t0
    import resource, cms_torch as CT
    dev = CT.device() or "numpy"; gm = ""
    if dev == "cuda":
        import torch; gm = f", GPU peak {torch.cuda.max_memory_allocated() / 2 ** 30:.2f} GB"
    print(f"{of}: {len(R['recs'])} runs, {nf} frames, agreement {R['agree']:.4f}, load {tl:.0f}s, total {dt:.0f}s "
          f"({1e3 * (dt - tl) / max(nf, 1):.1f} ms/frame), device {dev}, peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20:.2f} GB{gm}",
          flush=True)


if __name__ == "__main__":
    main()
