"""Offline builders for extra VPR descriptors (packaged in the Kaggle dataset `vpr-descriptor-weights`).

Each builder takes the dataset root and returns `fwd(x) -> (B, D)` for ImageNet-normalised images (B,3,H,W).
Weights: MixVPR (official ResNet50 4096-d ckpt), CosPlace (ResNet50 2048-d), NetVLAD (VGG16 Pitts30K, hloc .mat,
4096-d whitened), MegaLoc (DINOv2-B + optimal-transport aggregation, 8448-d, HF gberton/MegaLoc).
Model code adapted from the public MixVPR / CosPlace / VPR-methods-evaluation / MegaLoc implementations (MIT).
"""
import os, sys
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision

IMNET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
IMNET_STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)


# ----------------------------------------------------------------------------- MixVPR
class FeatureMixerLayer(nn.Module):
    def __init__(self, in_dim, mlp_ratio=1):
        super().__init__()
        self.mix = nn.Sequential(nn.LayerNorm(in_dim), nn.Linear(in_dim, int(in_dim * mlp_ratio)), nn.ReLU(),
                                 nn.Linear(int(in_dim * mlp_ratio), in_dim))

    def forward(self, x):
        return x + self.mix(x)


class MixVPRAgg(nn.Module):
    def __init__(self, in_channels=1024, in_h=20, in_w=20, out_channels=1024, mix_depth=4, mlp_ratio=1, out_rows=4):
        super().__init__()
        hw = in_h * in_w
        self.mix = nn.Sequential(*[FeatureMixerLayer(hw, mlp_ratio) for _ in range(mix_depth)])
        self.channel_proj = nn.Linear(in_channels, out_channels)
        self.row_proj = nn.Linear(hw, out_rows)

    def forward(self, x):
        x = self.mix(x.flatten(2)).permute(0, 2, 1)
        x = self.channel_proj(x).permute(0, 2, 1)
        return F.normalize(self.row_proj(x).flatten(1), p=2, dim=-1)


class MixVPRResNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = torchvision.models.resnet50()
        self.model.avgpool = nn.Identity(); self.model.fc = nn.Identity(); self.model.layer4 = nn.Identity()

    def forward(self, x):
        m = self.model
        x = m.maxpool(m.relu(m.bn1(m.conv1(x))))
        return m.layer3(m.layer2(m.layer1(x)))


class MixVPRModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = MixVPRResNet(); self.aggregator = MixVPRAgg()

    def forward(self, x):
        x = F.interpolate(x, size=(320, 320), mode="bilinear", align_corners=False, antialias=True)
        return self.aggregator(self.backbone(x))


def build_mixvpr(root, device):
    m = MixVPRModel()
    sd = torch.load(os.path.join(root, "mixvpr", "resnet50_MixVPR_4096_channels(1024)_rows(4).ckpt"), map_location="cpu")
    sd = sd.get("state_dict", sd)
    missing, unexpected = m.load_state_dict(sd, strict=False)
    assert len(missing) == 0, f"MixVPR missing keys: {missing[:5]}"
    m.eval().to(device)
    return torch.no_grad()(lambda x: m(x))


# ----------------------------------------------------------------------------- CosPlace
class GeM(nn.Module):
    def __init__(self, p=3, eps=1e-6):
        super().__init__(); self.p = nn.Parameter(torch.ones(1) * p); self.eps = eps

    def forward(self, x):
        return F.avg_pool2d(x.clamp(min=self.eps).pow(self.p), (x.size(-2), x.size(-1))).pow(1. / self.p)


class L2Norm(nn.Module):
    def forward(self, x):
        return F.normalize(x, p=2.0, dim=1)


class Flatten(nn.Module):
    def forward(self, x):
        return x[:, :, 0, 0]


class CosPlaceNet(nn.Module):
    def __init__(self):
        super().__init__()
        r = torchvision.models.resnet50()
        self.backbone = nn.Sequential(*list(r.children())[:-2])
        self.aggregation = nn.Sequential(L2Norm(), GeM(), Flatten(), nn.Linear(2048, 2048), L2Norm())

    def forward(self, x):
        return self.aggregation(self.backbone(x))


def build_cosplace(root, device):
    m = CosPlaceNet()
    sd = torch.load(os.path.join(root, "cosplace", "ResNet50_2048_cosplace.pth"), map_location="cpu")
    missing, unexpected = m.load_state_dict(sd, strict=False)
    assert len(missing) == 0, f"CosPlace missing keys: {missing[:5]}"
    m.eval().to(device)
    return torch.no_grad()(lambda x: m(x))


# ----------------------------------------------------------------------------- NetVLAD (hloc VGG16 Pitts30K)
class NetVLADLayer(nn.Module):
    def __init__(self, input_dim=512, num_clusters=64):
        super().__init__()
        self.score_proj = nn.Conv1d(input_dim, num_clusters, kernel_size=1, bias=False)
        self.centers = nn.Parameter(torch.empty([input_dim, num_clusters]))
        self.output_dim = input_dim * num_clusters

    def forward(self, x):
        b = x.size(0)
        scores = F.softmax(self.score_proj(x), dim=1)
        diff = x.unsqueeze(2) - self.centers.unsqueeze(0).unsqueeze(-1)
        desc = F.normalize((scores.unsqueeze(1) * diff).sum(dim=-1), dim=1)
        return F.normalize(desc.view(b, -1), dim=1)


class NetVLADNet(nn.Module):
    def __init__(self, mat_path):
        super().__init__()
        from scipy.io import loadmat
        vgg = list(torchvision.models.vgg16().children())[0]
        self.backbone = nn.Sequential(*list(vgg.children())[:-2])
        self.netvlad = NetVLADLayer(); self.whiten = nn.Linear(self.netvlad.output_dim, 4096)
        mat = loadmat(mat_path, struct_as_record=False, squeeze_me=True)
        for layer, ml in zip(self.backbone.children(), mat["net"].layers):
            if isinstance(layer, nn.Conv2d):
                layer.weight = nn.Parameter(torch.tensor(ml.weights[0]).float().permute([3, 2, 0, 1]))
                layer.bias = nn.Parameter(torch.tensor(ml.weights[1]).float())
        L = mat["net"].layers
        self.netvlad.score_proj.weight = nn.Parameter(torch.tensor(L[30].weights[0]).float().permute([1, 0]).unsqueeze(-1))
        self.netvlad.centers = nn.Parameter(torch.tensor(-L[30].weights[1]).float())
        self.whiten.weight = nn.Parameter(torch.tensor(L[33].weights[0]).float().squeeze().permute([1, 0]))
        self.whiten.bias = nn.Parameter(torch.tensor(L[33].weights[1].squeeze()).float())
        self.register_buffer("mean", torch.tensor(np.asarray(mat["net"].meta.normalization.averageImage[0, 0], np.float32)).view(1, -1, 1, 1))

    def forward(self, x):
        img = (x * IMNET_STD.to(x) + IMNET_MEAN.to(x)).clamp(0, 1) * 255.0 - self.mean.to(x)
        d = self.backbone(img); b, c = d.shape[:2]
        d = self.netvlad(F.normalize(d.view(b, c, -1), dim=1))
        return F.normalize(self.whiten(d), dim=1)


def build_netvlad(root, device):
    m = NetVLADNet(os.path.join(root, "netvlad", "Pitts30K_struct.mat")).eval().to(device)
    return torch.no_grad()(lambda x: m(x.float()))


# ----------------------------------------------------------------------------- MegaLoc
def build_megaloc(root, device):
    d = os.path.join(root, "megaloc")
    if d not in sys.path: sys.path.insert(0, d)
    from megaloc_model import MegaLoc
    from safetensors.torch import load_file
    m = MegaLoc()
    missing, unexpected = m.load_state_dict(load_file(os.path.join(d, "model.safetensors")), strict=False)
    assert len(missing) == 0, f"MegaLoc missing keys: {missing[:5]}"
    m.eval().to(device)
    return torch.no_grad()(lambda x: m(x))


BUILDERS = {"mixvpr": build_mixvpr, "cosplace": build_cosplace, "netvlad": build_netvlad, "megaloc": build_megaloc}
