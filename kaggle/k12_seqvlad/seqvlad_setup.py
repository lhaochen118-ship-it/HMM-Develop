# === S.0 — SeqVLAD (Mereu et al., RA-L 2022; vandal-vpr/vg-transformers, MIT) — CCT384 + SeqVLAD, MSLS-trained, L=5 ===
# Per frame we save the UNNORMALISED VLAD residual sum V_f (64x384). The official sequence descriptor (one VLAD over all
# tokens of all frames) equals  L2( intra-norm( sum_f V_f ) )  -> composed offline for any window (exact).
import subprocess, shutil as _sh, importlib
os.environ.pop("PIP_NO_INDEX", None)
_r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gdown", "einops", "timm"], capture_output=True, text=True); print("pip:", _r.returncode, flush=True)
VG = "/kaggle/working/vgt"
if not os.path.isdir(VG): subprocess.run(["git", "clone", "--depth", "1", "https://github.com/vandal-vpr/vg-transformers", VG], check=True)
print("vg-transformers commit:", subprocess.run(["git", "-C", VG, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(), flush=True)
PKG = "/kaggle/working/cctpkg"; os.makedirs(PKG, exist_ok=True); open(os.path.join(PKG, "__init__.py"), "w").close()
_sh.copy(os.path.join(VG, "tvg/models/cct.py"), PKG)
if not os.path.isdir(os.path.join(PKG, "cct_utils")): _sh.copytree(os.path.join(VG, "tvg/models/cct_utils"), os.path.join(PKG, "cct_utils"))
sys.path.insert(0, "/kaggle/working")
CKS = "/kaggle/working/seqvlad_cct384.pth"
if not os.path.isfile(CKS):
    import gdown; gdown.download(id="16n6CL2t-asQ_tf8x4ZyJT_Y4UQQedsxh", output=CKS, quiet=False)
_ck = torch.load(CKS, map_location="cpu", weights_only=False); _ck = _ck.get("model_state_dict", _ck)
_ck = {k.replace("module.", ""): v for k, v in _ck.items()}
print("seqvlad ckpt keys:", len(_ck), [k for k in _ck if not k.startswith("encoder.")][:10], flush=True)
def _try_seqvlad():
    cct = importlib.import_module("cctpkg.cct")
    enc = cct.cct_14_7x2_384(pretrained=False, progress=False)
    enc.classifier.blocks = torch.nn.ModuleList(list(enc.classifier.blocks.children())[:8])
    e = {k[len("encoder."):]: v for k, v in _ck.items() if k.startswith("encoder.")}
    mi, un = enc.load_state_dict(e, strict=False); print("SeqVLAD encoder missing", len(mi), mi[:6], "| unexpected", len(un), un[:6], flush=True)
    assert len([m for m in mi if "attention_pool" not in m]) == 0, "encoder weights not loaded"
    cen = [v for k, v in _ck.items() if k.endswith("centroids")][0].float().to(DEVICE)          # (64, 384)
    W = [v for k, v in _ck.items() if k.startswith("aggregator") and k.endswith("conv.weight")][0].float().to(DEVICE).reshape(cen.shape[0], -1)
    enc.eval().to(DEVICE)
    @torch.no_grad()
    def fwd(x):
        t = enc(x).float()                                       # (B, T, 384) all tokens, no class token
        t = torch.nn.functional.normalize(t, p=2, dim=2)         # normalize_input across descriptor dim
        a = torch.softmax(torch.einsum("btd,kd->btk", t, W), dim=2)
        V = torch.einsum("btk,btd->bkd", a, t) - a.sum(1)[..., None] * cen[None]
        return V.reshape(V.shape[0], -1)
    return fwd
REGISTRY["seqvlad"] = _try_seqvlad
