"""VPR-auditing baseline (Waheed, Milford, Ramchurn, Ehsan, arXiv 2607.12818, 2026), reproduced with an OPEN VLM offline.

The paper audits the top-1 retrieved image of each query with a VLM asked whether both images depict the same physical
place (conservative default: different places unless strong evidence; compare permanent structure, ignore dynamic
elements; JSON answer {"is_same_place": true|false, "reasoning": ...}); accept iff is_same_place is true; unparsable
answers count as accepted. The paper does not print its prompt; the prompt below follows its description (III-B, IV-D).
Model: Qwen2.5-VL-7B-Instruct (one of the paper's two open models), bf16, one replica per GPU of the session.
Speed-up that keeps the decision: the assistant answer is pre-filled with '{"is_same_place": ' and ONE forward pass gives
the logits of 'true' vs 'false' for the next token (greedy decoding would emit the same token); the log-odds
l = log p(true) - log p(false) is kept as the confidence (the paper's PR curves use the log-probability of 'true').
Pairs: query frame -> top-1 kept map image of nav_demo cache (ds, desc, seed), every `--every` query frame.
Usage: vlm_audit.py <dump> <ds> <desc> <cache_dir> [--seed 0] [--every 5] [--part i/n] [--bs 8] [--side 448]
Output: results/vlm_<ds>_<desc>_s<seed>_p<i>.npz rows (query rows), logodds, accept, missing."""
import sys, os, time, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vprlib as V

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
SEED, EVERY, BS, SIDE = arg("--seed", 0), arg("--every", 5), arg("--bs", 8), arg("--side", 448)
PART = tuple(int(x) for x in arg("--part", "0/1").split("/"))
PROMPT = ("The first image is a query photo taken by a robot. The second image is the database photo that a place "
          "recognition system retrieved as its best match. Decide whether both images depict the same physical place. "
          "Assume that they show different locations unless there is strong evidence that they match. "
          "First identify permanent structural elements in both images (buildings, road layout, intersections, poles, "
          "signs, fences, distinctive vegetation structure). Then compare their spatial configuration. Actively search "
          "for inconsistencies. Explicitly ignore dynamic elements such as vehicles, pedestrians, lighting and weather "
          "conditions (snow, rain, season, day or night). Answer only with JSON of the form "
          '{"is_same_place": true or false, "reasoning": "Both images show ..."}')


def image_index():
    idx = {}
    for d, _, fs in os.walk("/kaggle/input"):
        if "/img/" in d + "/":
            seq = os.path.basename(d)
            for f in fs:
                if f.endswith((".jpg", ".png")): idx[(seq, os.path.splitext(f)[0])] = os.path.join(d, f)
    return idx


def pairs_boreas(dump, desc, z, every):
    ep = V.load_boreas(dump, desc); ref = ep.ref
    nm = lambda r: np.load(os.path.join(dump, "meta", f"boreas_{r}.npz"), allow_pickle=True)["names"]
    key = lambda n: str(int(n)) if np.issubdtype(type(n), np.number) else os.path.basename(str(n)).split(".")[0]
    mnames = nm(ref); qrecs = list(dict.fromkeys(ep.q_rec)); qnames = np.concatenate([nm(r) for r in qrecs])
    rows = np.arange(0, len(qnames), every); mrow = z["kidx"][z["top"][rows]]
    return rows, [(ep.q_rec[r], key(qnames[r])) for r in rows], [(ref, key(mnames[j])) for j in mrow]


def find_model():
    for d, _, fs in os.walk("/kaggle/input"):
        if "config.json" in fs and any(f.endswith(".safetensors") for f in fs):
            if "qwen2_5_vl" in open(os.path.join(d, "config.json")).read().lower(): return d
    raise SystemExit("Qwen2.5-VL weights not mounted")


def main():
    dump, ds, desc, cdir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    try:
        from transformers import Qwen2_5_VLForConditionalGeneration as QVL
    except ImportError:
        from transformers import AutoModelForImageTextToText as QVL
    t0 = time.time(); z = np.load(os.path.join(cdir, f"navcache_{ds.replace(':', '_')}_{desc}_s{SEED}.npz"), allow_pickle=True)
    assert ds == "boreas", "image pairs implemented for boreas"
    rows, qk, mk = pairs_boreas(dump, desc, z, EVERY)
    sel = np.arange(PART[0], len(rows), PART[1]); rows = rows[sel]; qk = [qk[i] for i in sel]; mk = [mk[i] for i in sel]
    idx = image_index(); qp = [idx.get(k) for k in qk]; mp = [idx.get(k) for k in mk]
    ok = np.array([a is not None and b is not None for a, b in zip(qp, mp)])
    print(f"{ds}/{desc} s{SEED}: {len(rows)} pairs, images found {ok.mean():.3f}, {time.time() - t0:.0f}s", flush=True)
    mdir = find_model(); dev = "cuda:0"; print("model dir", mdir, sorted(os.listdir(mdir)), flush=True)
    # the Kaggle model's preprocessor_config.json names an image-processor class that newer transformers dropped: build a
    # symlinked copy with the class name patched (Qwen2VLImageProcessor is the image processor of Qwen2.5-VL)
    import json, tempfile
    wdir = os.path.join(tempfile.gettempdir(), "qwen_vl_patched"); os.makedirs(wdir, exist_ok=True)
    for f in os.listdir(mdir):
        dst = os.path.join(wdir, f)
        if f == "preprocessor_config.json":
            cfg = json.load(open(os.path.join(mdir, f))); print("preprocessor_config", cfg, flush=True)
            cfg["image_processor_type"] = "Qwen2VLImageProcessor"; cfg.pop("processor_class", None)
            json.dump(cfg, open(dst, "w"))
        elif not os.path.exists(dst): os.symlink(os.path.join(mdir, f), dst)
    try:
        proc = AutoProcessor.from_pretrained(wdir, min_pixels=64 * 28 * 28, max_pixels=SIDE * SIDE)
    except Exception as e:
        print("AutoProcessor failed:", repr(e)[:300], "-> manual processor", flush=True)
        from transformers import Qwen2VLImageProcessor, AutoTokenizer, Qwen2_5_VLProcessor
        tok = AutoTokenizer.from_pretrained(mdir); ctf = os.path.join(mdir, "chat_template.json")
        ct = json.load(open(ctf))["chat_template"] if os.path.exists(ctf) else tok.chat_template
        ip = Qwen2VLImageProcessor(min_pixels=64 * 28 * 28, max_pixels=SIDE * SIDE)
        try:
            proc = Qwen2_5_VLProcessor(image_processor=ip, tokenizer=tok, chat_template=ct)
        except TypeError:
            from transformers import Qwen2VLVideoProcessor
            proc = Qwen2_5_VLProcessor(image_processor=ip, tokenizer=tok, video_processor=Qwen2VLVideoProcessor(), chat_template=ct)
    mdir = wdir
    proc.tokenizer.padding_side = "left"
    model = QVL.from_pretrained(mdir, torch_dtype=torch.bfloat16, device_map=dev, attn_implementation="sdpa").eval()
    tt = [proc.tokenizer.encode(w, add_special_tokens=False)[0] for w in ("true", " true")]
    tf = [proc.tokenizer.encode(w, add_special_tokens=False)[0] for w in ("false", " false")]
    msg = [{"role": "user", "content": [{"type": "image"}, {"type": "image"}, {"type": "text", "text": PROMPT}]}]
    text = proc.apply_chat_template(msg, tokenize=False, add_generation_prompt=True) + '{"is_same_place": '
    lo = np.full(len(rows), np.nan, np.float32)

    def img(p):
        im = Image.open(p).convert("RGB"); w, h = im.size; s = SIDE / max(w, h)
        return im.resize((max(28, int(w * s)), max(28, int(h * s))), Image.BICUBIC) if s < 1 else im

    from concurrent.futures import ThreadPoolExecutor
    pool = ThreadPoolExecutor(8); todo = np.flatnonzero(ok); t1 = time.time()
    batches = [todo[i:i + BS] for i in range(0, len(todo), BS)]
    nxt = pool.submit(lambda b: [img(x) for i in b for x in (qp[i], mp[i])], batches[0]) if batches else None
    for bi, b in enumerate(batches):
        ims = nxt.result()
        if bi + 1 < len(batches): nxt = pool.submit(lambda b: [img(x) for i in b for x in (qp[i], mp[i])], batches[bi + 1])
        inp = proc(text=[text] * len(b), images=ims, return_tensors="pt", padding=True).to(dev)
        with torch.no_grad():
            lg = model(**inp).logits[:, -1].float().log_softmax(-1)
        pt, pf = torch.logsumexp(lg[:, tt], 1), torch.logsumexp(lg[:, tf], 1)
        lo[b] = (pt - pf).cpu().numpy()
        if bi % 50 == 0: print(f"  {bi + 1}/{len(batches)} batches, {(bi + 1) * BS / max(time.time() - t1, 1e-6):.1f} pairs/s", flush=True)
    os.makedirs("results", exist_ok=True)
    np.savez_compressed(f"results/vlm_{ds.replace(':', '_')}_{desc}_s{SEED}_p{PART[0]}.npz", rows=rows, logodds=lo,
                        accept=np.where(np.isfinite(lo), lo > 0, True), missing=~ok)
    print(f"done {len(todo)} pairs, accept rate {np.mean(lo[np.isfinite(lo)] > 0):.3f}, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
