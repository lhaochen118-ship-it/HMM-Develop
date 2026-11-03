"""Entry 37 kernel job (wave 1 + 2 fused): the rules of ONE run as soon as every part of its forward null exists in the kernel.
  1. --wait: until results/fwdp_<tag>_<desc>_s<seed>.p<k>of<n>.npz.done exists for every k < n (written by e37_fwd.py in the same
     kernel; at most 4 h)
  2. cms_fwd.merge -> results/fwd/fwd_<tag>_<desc>_s<seed>.npz (the part files are removed once the merged file is written)
  3. oc_curves defaults, exactly the Entry 36 call of e36_run.py step 3 (--cst --fwd --navgate --gate-rate, groups cond + loco,
     alpha 0.05) with --fams @E36,@E37 and --dump-frames -> results/oc_<tag>_<desc>_e37_s<seed>.json and
     results/frames_<tag>_<desc>_e37_s<seed>.npz (per-frame default decisions: the position audit H37b)
Usage: e37_eval.py <dump> <navcache_dir> <cms_dir> <topk_dir> <tao_dir> <ds> <desc> <seed> <n_parts> [--wait] [--fams @E36,@E37]"""
import sys, os, time, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)


def main():
    dump, nd, cd, kd, td, ds, desc, seed, n = sys.argv[1:10]; n = int(n); tag = ds.replace(":", "_"); t0 = time.time()
    fams = sys.argv[sys.argv.index("--fams") + 1] if "--fams" in sys.argv else "@E36,@E37"
    os.makedirs("results/fwd", exist_ok=True)
    out = f"results/oc_{tag}_{desc}_e37_s{seed}.json"
    if os.path.exists(out): print(out, "exists"); return
    ff = os.path.join("results", "fwd", f"fwd_{tag}_{desc}_s{seed}.npz")
    parts = [os.path.join("results", f"fwdp_{tag}_{desc}_s{seed}.p{k}of{n}.npz") for k in range(n)]
    if not os.path.exists(ff):
        while not all(os.path.exists(p + ".done") for p in parts):
            if "--wait" not in sys.argv or time.time() - t0 > 4 * 3600:
                sys.exit(f"missing parts: {[p for p in parts if not os.path.exists(p + '.done')]}")
            time.sleep(15)
        tw = time.time() - t0
        import cms_fwd as CF
        R = CF.merge(ff + ".tmp.npz", parts); os.replace(ff + ".tmp.npz", ff)
        for p in parts:
            os.remove(p); os.remove(p + ".done")
        print(f"merged {n} parts: {len(R['recs'])} virtual runs, {R['n_frames']} frames, agreement {R['agree']:.4f} (waited {tw:.0f}s)", flush=True)
    t = time.time()
    cmd = [sys.executable, os.path.join(HERE, "oc_curves.py"), nd, ds, desc, "--seeds", str(seed), "--jobs", "1", "--defaults-only",
           "--topk", kd, "--taocache", td, "--cms", cd, "--fwd", os.path.join("results", "fwd"), "--tw", "0.5", "--variants", "--light",
           "--cms-alpha", "0.05", "--cms-groups", "cond,loco", "--navgate", "--gate-rate", "--cst", "--fams", fams,
           "--out-suffix", f"_e37_s{seed}", "--dump-frames"]
    if ds in ("oxford", "stlucia"): cmd += ["--mapdump", dump]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"{tag}/{desc}/s{seed}: rules rc {r.returncode} {time.time() - t:.0f}s, total {time.time() - t0:.0f}s", flush=True)
    if r.returncode: print(r.stdout[-1500:], r.stderr[-3000:], flush=True); sys.exit(1)


if __name__ == "__main__":
    main()
