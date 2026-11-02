"""Global descriptors of an image folder on CPU or GPU (Entry 36, St Lucia), with the same models, preprocessing (square resize to
322 px, ImageNet normalisation) and L2-normalised fp16 output as the dump notebooks (nb15_src/20_extract.src, vpr_extra.py), plus
the frozen DINOv2 ViT-B/14 PATCH tokens used by the SafeVPR'26 verifier (short side 224 px, as analysis/safevpr_mnn.py).
Usage: extract_desc_cpu.py <img_root> <meta_dir> <out_dump> <weights_root> <bundle_root> --descs cosplace,netvlad,... [--trav a,b]
  img_root/<trav>/<name>.jpg, meta_dir/<prefix>_<trav>.npz (names) -> out_dump/<desc>/<prefix>_<trav>.npy (fp16)
  desc "dinov2patch" -> out_dump/patch/<prefix>_<trav>.npy (n, P, 768) fp16 patch tokens (L2-normalised)"""
import sys, os, time
import numpy as np
import torch
from PIL import Image
import torchvision.transforms as T

HERE = os.path.dirname(os.path.abspath(__file__))


def build(name, wroot, broot, dev):
    sys.path.insert(0, HERE); import vpr_extra as VX
    if name in VX.BUILDERS: return VX.BUILDERS[name](wroot, dev)
    if name in ("salad", "dinov2", "dinov2patch"):
        for p in (os.path.join(broot, "sources", "dinov2"), os.path.join(broot, "sources", "salad")):
            if p not in sys.path: sys.path.insert(0, p)
    if name == "salad":
        from models import helper
        bb = helper.get_backbone("dinov2_vitb14", {"num_trainable_blocks": 4, "return_token": True, "norm_layer": True})
        ag = helper.get_aggregator("SALAD", {"num_channels": 768, "num_clusters": 64, "cluster_dim": 128, "token_dim": 256})
        sd = torch.load(os.path.join(broot, "checkpoints", "dino_salad.ckpt"), map_location="cpu"); sd = sd.get("state_dict", sd)
        bb.load_state_dict({k[9:]: v for k, v in sd.items() if k.startswith("backbone.")}, strict=False)
        ag.load_state_dict({k[11:]: v for k, v in sd.items() if k.startswith("aggregator.")}, strict=False)
        m = torch.nn.Module(); m.backbone, m.aggregator = bb, ag; m.eval().to(dev)
        return torch.no_grad()(lambda x: m.aggregator(m.backbone(x)))
    from dinov2.models.vision_transformer import vit_base
    vit = vit_base(patch_size=14, img_size=518, init_values=1.0, block_chunks=0)
    sd = torch.load(os.path.join(broot, "checkpoints", "dinov2_vitb14_pretrain.pth"), map_location="cpu"); vit.load_state_dict(sd.get("state_dict", sd), strict=False)
    vit.eval().to(dev)
    if name == "dinov2":
        def f(x):
            o = vit.forward_features(x); return torch.cat([o["x_norm_clstoken"], o["x_norm_patchtokens"].mean(1)], 1)
        return torch.no_grad()(f)
    return torch.no_grad()(lambda x: vit.forward_features(x)["x_norm_patchtokens"])


class Imgs(torch.utils.data.Dataset):
    def __init__(self, paths, tx): self.paths, self.tx = paths, tx
    def __len__(self): return len(self.paths)
    def __getitem__(self, i): return self.tx(Image.open(self.paths[i]).convert("RGB")), i


def main():
    img_root, meta_dir, out, wroot, broot = sys.argv[1:6]
    descs = sys.argv[sys.argv.index("--descs") + 1].split(",")
    travs = sys.argv[sys.argv.index("--trav") + 1].split(",") if "--trav" in sys.argv else None
    prefix = sys.argv[sys.argv.index("--prefix") + 1] if "--prefix" in sys.argv else "stlucia"
    bs = int(sys.argv[sys.argv.index("--bs") + 1]) if "--bs" in sys.argv else 32
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    metas = sorted(f for f in os.listdir(meta_dir) if f.startswith(prefix + "_"))
    for name in descs:
        fwd = build(name, wroot, broot, dev); t0 = time.time()
        if name == "dinov2patch":
            tx = T.Compose([T.Resize(224, antialias=True), T.CenterCrop((224, 294)), T.ToTensor(), T.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))])
            od = os.path.join(out, "patch")
        else:
            tx = T.Compose([T.Resize((322, 322), antialias=True), T.ToTensor(), T.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))])
            od = os.path.join(out, name)
        os.makedirs(od, exist_ok=True)
        for mf in metas:
            tr = mf[len(prefix) + 1:-4]
            if travs and tr not in travs: continue
            of = os.path.join(od, f"{prefix}_{tr}.npy")
            if os.path.exists(of): continue
            names = np.load(os.path.join(meta_dir, mf), allow_pickle=True)["names"]
            paths = [os.path.join(img_root, tr, f"{n}.jpg") for n in names]
            dl = torch.utils.data.DataLoader(Imgs(paths, tx), batch_size=bs, num_workers=2)
            res = None
            for x, i in dl:
                d = torch.nn.functional.normalize(fwd(x.to(dev)).float(), dim=-1).cpu().numpy().astype(np.float16)
                if res is None: res = np.zeros((len(paths),) + d.shape[1:], np.float16)
                res[i.numpy()] = d
            np.save(of, res); print(f"{name} {tr}: {res.shape} {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
