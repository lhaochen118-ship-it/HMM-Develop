"""Figure for Proposition 6 (Entries 21-22): the odometry-unobservable alias on CMU.
Left: seed 60, CosPlace. Map images of the run (grey), queries inside the hole that received a false fix (blue) and the map images reported
for them (red), with a few offset arrows. The copy is the true track shifted ~204 m back along the same straight road.
Right: what separates a weak true match from the alias. Robust z of the true place (full map, seed 58) vs the best alias in the seed-60 hole
overlap; the raw cosine similarity separates them.
Usage: fig_shifted_alias.py <navcache_dir r55> <dump_dir> <hsifr_dir t58NT> <out.png>"""
import sys, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    nc, dump, hdir, out = sys.argv[1:5]; sys.argv = sys.argv[:1]
    import vprlib as V
    from owf import robust_z
    from scipy.spatial import cKDTree
    z60 = np.load(os.path.join(nc, "navcache_cmu_cosplace_s60.npz"), allow_pickle=True)
    hm = np.load(os.path.join(hdir, "hsifr_cmu_cosplace_s60_t58NTxms09_16.npz")); n = int(hm["n"])
    acc = np.unpackbits(hm["HSI-VN"])[:n].astype(bool)
    MP = z60["MP"].astype(float)[:, :2]; qp = z60["q_pos"].astype(float)[:, :2]; offm = np.asarray(z60["offm"], bool)
    top = z60["top"].astype(int)
    holeA = np.linalg.norm(qp - np.array([1180, -340.]), axis=1) < 70                  # the straight-road hole (slices 11-12)
    i = np.where(acc & offm & holeA)[0]
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6), gridspec_kw=dict(width_ratios=[1.3, 1, 1]))
    a = ax[0]; box = (MP[:, 0] > 900) & (MP[:, 0] < 1320) & (MP[:, 1] > -480) & (MP[:, 1] < -290)
    a.scatter(MP[box, 0], MP[box, 1], s=10, c="0.55", marker="s", label="map images (seed 60)")
    a.scatter(qp[i, 0], qp[i, 1], s=4, c="tab:blue", label="query in hole, false fix")
    a.scatter(MP[top[i], 0], MP[top[i], 1], s=6, c="tab:red", label="reported map image")
    for j in i[:: max(1, len(i) // 12)]:
        a.annotate("", xy=MP[top[j]], xytext=qp[j], arrowprops=dict(arrowstyle="->", color="0.3", lw=0.6))
    off = np.median(MP[top[i]] - qp[i], 0)
    a.set_title(f"CMU seed 60 (CosPlace): copy offset {off[0]:.0f}, {off[1]:.0f} m"); a.set_aspect("equal"); a.legend(fontsize=7, loc="lower right")
    a.set_xlabel("x (m)"); a.set_ylabel("y (m)")
    ep = V.load_cmu_merged(dump, "cosplace"); Q = ep.q / np.linalg.norm(ep.q, axis=1, keepdims=True)
    res = {}
    for s in (58, 60):
        z = np.load(os.path.join(nc, f"navcache_cmu_cosplace_s{s}.npz"), allow_pickle=True)
        M = ep.m[z["kidx"]]; M = M / np.linalg.norm(M, axis=1, keepdims=True); S = Q @ M.T; Z = robust_z(S)
        _, nn = cKDTree(z["MP"][:, :2].astype(float)).query(ep.q_pos[:, :2]); r = np.arange(len(Z))
        res[s] = dict(z_true=Z[r, nn], s_true=S[r, nn], zmax=Z.max(1), smax=S.max(1), inm=np.asarray(z["inm"], bool), offm=np.asarray(z["offm"], bool))
    hole = res[60]["offm"] & (np.linalg.norm(ep.q_pos[:, :2] - np.array([1180, -340.]), axis=1) < 70)
    for k, (key_t, key_a, lab) in enumerate([("z_true", "zmax", "robust z"), ("s_true", "smax", "cosine similarity")]):
        a = ax[1 + k]; t = res[58][key_t][res[58]["inm"]]; al = res[60][key_a][hole]
        bins = np.linspace(min(np.percentile(t, 0.5), al.min()), max(np.percentile(t, 99.5), al.max()), 60)
        a.hist(t, bins, density=True, alpha=0.55, color="tab:green", label="true place, on-map frames (full map, s58)")
        a.hist(al, bins, density=True, alpha=0.55, color="tab:red", label="best match in the s60 hole (alias)")
        a.axvline(np.percentile(t, 5), color="tab:green", ls="--", lw=1); a.axvline(np.median(al), color="tab:red", ls="--", lw=1)
        a.set_xlabel(lab); a.set_title(f"{lab}: true 5th pct {np.percentile(t, 5):.2f}, alias median {np.median(al):.2f}"); a.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(out, dpi=150); print("saved", out)


if __name__ == "__main__":
    main()
