<div align="center">

# LACUNA

**L**ocalization **A**ware of **C**overage and **UN**mapped **A**reas

### Open-World Sequential Visual Localization on Maps with Holes

[![Paper](https://img.shields.io/badge/Paper-Coming%20Soon-b31b1b?style=flat-square&logo=arxiv&logoColor=white)](#-news)
[![Code](https://img.shields.io/badge/Code-Coming%20Soon-2563eb?style=flat-square&logo=github&logoColor=white)](#roadmap)
[![PyTorch](https://img.shields.io/badge/PyTorch-GPU%20engine-ee4c2c?style=flat-square&logo=pytorch&logoColor=white)](#method)
[![Task](https://img.shields.io/badge/Task-Visual%20Localization-16a34a?style=flat-square)](#abstract)

<img src="assets/overview.svg" alt="LACUNA overview" width="100%">

<sub><b>(a)</b> A closed-world filter keeps all of its belief on map places. When the robot enters an unmapped area, that belief has
nowhere to go but a look-alike street, and the filter reports a confident false fix. <b>(b)</b> LACUNA keeps its belief on a metric grid
that covers mapped and unmapped space. The map's known coverage and dead reckoning predict that the robot has left the map, so the filter
does not report a fix.</sub>

</div>

> [!NOTE]
> 📄 **The paper and 💻 code will be released soon.** Click **Watch → Custom → Releases** to get a notification, and consider giving the repository a ⭐.

## 🔥 News

- **[Nov 2026]** Project page created. The paper, code, evaluation protocol and pre-computed descriptor caches will follow.

## Abstract

Sequence-based visual localization against a geo-referenced image map is a core capability for long-term autonomous navigation, yet
real-world maps are inevitably incomplete: streets are never surveyed, and construction or seasonal change removes coverage. When a robot
traverses such unmapped areas, conventional topological filters, which confine all belief to mapped places, are forced to commit to
look-alike locations and emit confident false position fixes that corrupt downstream navigation. We present **LACUNA**, an open-world
Bayesian filter that treats map coverage as part of the state rather than as an afterthought. LACUNA maintains a mass-conserving belief over
a metric grid that spans both mapped and unmapped space, together with a far state. Leaving the map is therefore *predicted* by dead
reckoning against the map's known coverage instead of being *detected* by a separate test. Odometry noise and scale are self-calibrated
online by Bayesian model selection over a filter bank. We further identify a failure mode shared by every filter that normalizes appearance
evidence per frame: *odometry-unobservable aliasing*, in which a weakly similar copy of the trajectory, shifted along a straight road,
accumulates evidence without bound. We resolve it by giving the unmapped cells an absolute likelihood ratio that is calibrated causally,
and without labels, from the filter's own confident fixes. In pre-registered experiments on freshly sampled hole layouts spanning eight
datasets and six global descriptors (432 runs), LACUNA reports correct fixes on 93% of on-map frames, 12–13 points more than its
closed-world counterpart, and exceeds a 5% false-report budget on only 0.7% of runs. On 288 of these runs, we compare against three recent
integrity-monitoring and off-map detection methods. Even when their decision thresholds are tuned on the labels of each test run, they
report 26–28 points fewer correct fixes than LACUNA. At their published operating points, they violate the budget on 57–89% of runs. A
batched GPU implementation runs the complete two-pass system at about 6 ms per frame.

## Highlights

- **Holes are part of the state space.** Probability mass is carried into, through and out of unmapped areas by odometry. Presence on the
  map is a deterministic function of position, so no separate "off-map" detector is needed.
- **Self-calibrating odometry.** A bank of filters over process noise and odometry scale, selected online by the cumulative predictive
  likelihood, absorbs the 3–7% scale error of real visual-inertial odometry without labels.
- **Robust to shifted look-alikes.** We characterize odometry-unobservable aliasing and counter it with label-free, causally calibrated
  absolute evidence for unmapped cells. The evidence becomes neutral by itself when the true place does not stand out (e.g. at night).
- **One configuration, no labels at deployment.** All constants are shared across every dataset and descriptor. Causality is enforced by
  unit tests: changing a session's future never changes its past decisions.
- **Fast.** The whole filter bank of a run advances as a single GPU tensor at 2.7–3.4 ms/frame per pass, 8–10× faster than a NumPy
  reference that makes identical decisions.

## Method

LACUNA runs in two causal passes over a deployment (a set of sessions driven on the same map).

1. **Open-world filter.** The belief lives on a metric grid over the map's bounding region plus a far state $`\Omega`$. Odometry shifts the
   belief by whole cells, with process noise applied as an exact Gaussian blur. Mass that leaves the region is absorbed by $`\Omega`$, and
   nothing is ever renormalized over the mapped cells.
2. **Likelihood-ratio emission.** Similarities between the current frame and the map images are turned into likelihood ratios. Unmapped
   cells act as the natural null hypothesis, and evidence is weighted by the distance travelled.
3. **Hindsight-calibrated absolute evidence.** For the frame statistic
   $`x_t = \max_i s_{t,i} - \mathrm{median}_i\, s_{t,i}`$, unmapped cells receive
   $`\log f_{\text{off}}(x_t) - \log f_{\text{on}}(x_t)`$. The two densities are estimated without labels from the first pass's confident
   fixes. $`f_{\text{on}}`$ uses the frame maximum at a fix. $`f_{\text{off}}`$ uses the best look-alike far from the fix.
4. **Decision.** A position fix is reported only when the posterior mass near a mapped place passes extreme-confidence tiers, or when a
   self-supervised conformal branch confirms it. Otherwise the system abstains.

Full derivations are given in the paper: no net pull of a diffuse belief, a Ville-type bound on false reports within an off-map stretch
(under an e-value assumption), and the crossover analysis behind odometry-unobservable aliasing.

## Results

**Protocol.** 30% of the map is removed with freshly sampled hole layouts for each test group, and every decision rule is pre-registered
before the test. We report the following metrics.

- **Recall:** the fraction of on-map frames with a correct reported fix.
- **segFAR:** the fraction of 10-frame off-map segments with at least one report. The target is ≤ α = 0.05 *per run*.
- **Navigation error:** the error of a Kalman filter fed with the reported fixes.

One run is one dataset × descriptor × hole layout.

### Comparison with state-of-the-art methods (288 runs, same runs for every method)

| Method | Operating point | Recall ↑ | Runs violating α ↓ (of 288) | Nav. error (m) ↓ |
|:---|:---|:---:|:---:|:---:|
| Xu *et al.*, RA-L 2021 | published | 0.694 | 164 | 53.8 |
| | calibrated to segFAR ‡ | 0.642 | 106 | 44.6 |
| | per-run oracle threshold † | 0.651 | 0 | 44.5 |
| Claxton *et al.*, RA-L 2024 | published | 0.738 | 205 | 46.6 |
| | calibrated to segFAR ‡ | 0.684 | 142 | 30.3 |
| | per-run oracle threshold † | 0.670 | 0 | 28.1 |
| TAO, arXiv 2026 | published | 0.836 | 256 | 112.2 |
| | calibrated to segFAR ‡ | 0.629 | 53 | 37.3 |
| | per-run oracle threshold † | 0.651 | 0 | 37.1 |
| Closed-world hindsight baseline | label-free | 0.802 | 0 | 15.0 |
| **LACUNA** (safe operating point) | label-free | 0.920 | **0** | 13.8 |
| **LACUNA** | label-free | **0.927** | **0** | **13.3** |

LACUNA reports **26–28 points more correct fixes** than every baseline, even when the baseline's threshold is set with the labels of the
test run itself. Its navigation error is **2.1–3.3× lower**. Over all three fresh test groups (432 runs), LACUNA exceeds α on **3 runs
(0.7%)**, and on **none** at its safe operating point.

<sub>† The threshold that maximizes recall subject to segFAR ≤ α, chosen with the ground truth of each test run. This is an upper bound
for any threshold on the method's score, not a deployable rule. ‡ Thresholds tuned with labels on the two easiest conditions to meet the
segment-level target, which does not carry over to harder conditions. External baselines are re-implemented from their papers.</sub>

### Generalization to settings never used for tuning

Each cell shows *recall / runs violating α*.

| Setting (runs) | **LACUNA** | Closed-world baseline | Top-1 retrieval with perfect rejection § |
|:---|:---:|:---:|:---:|
| Holes 10% (108) | **0.932 / 0** | 0.777 / 0 | 0.827 / 0 |
| Holes 50% (108) | **0.872 / 4** | 0.751 / 4 | 0.829 / 0 |
| Natural off-map, 4Seasons cross-scene (36) | **0.945 / 0** | 0.756 / 0 | 0.822 / 0 |
| NCLT (6) | **0.769 / 0** | — | 0.724 / 0 |

<sub>§ Reports exactly the correct top-1 retrievals using ground truth, i.e. per-frame top-1 accuracy with perfect rejection. It is a
reference, not a deployable method.</sub>

> [!IMPORTANT]
> **Known limitation.** On CMU, Oxford and St Lucia the odometry is simulated and keeps the true heading. With a heading random walk of
> 0.13°/√m, recall on those datasets drops by 4.8 points (St Lucia: 14.5) and validity is unchanged. LACUNA still outperforms
> oracle-thresholded Claxton'24 and Xu'21 by 8.6 and 14.1 points. Adding heading offset to the self-calibrating odometry bank is
> work in progress.

## Datasets and Descriptors

| | |
|:---|:---|
| **Main benchmarks (8)** | Oxford RobotCar · Nordland · Extended CMU Seasons · St Lucia · Boreas · 4Seasons (office loop, old town, countryside) |
| **Generalization** | NCLT · 4Seasons cross-scene (natural off-map) · VPR-Space (planetary / lunar, descriptive) |
| **Global descriptors (6)** | NetVLAD · CosPlace · MixVPR · SALAD · MegaLoc · DINOv2 |

## Roadmap

- [x] Project page and overview
- [ ] Paper (arXiv)
- [ ] Core open-world filter: NumPy reference and batched PyTorch engine
- [ ] Evaluation protocol: hole generation, metrics (recall, segFAR, navigation error) and position audit
- [ ] Re-implemented baselines (TAO'26, Xu'21, Claxton'24) at all three operating points
- [ ] Pre-computed descriptor caches and scripts to reproduce every table

## Citation

If you find this work useful, please consider citing it. The BibTeX entry will be updated when the paper is released.

```bibtex
@misc{lacuna2026,
  title        = {{LACUNA}: Open-World Sequential Visual Localization on Maps with Holes},
  author       = {TBA},
  year         = {2026},
  howpublished = {\url{https://github.com/nhatlong113/LACUNA---Localization-Aware-of-Coverage-and-UNmapped-Areas}},
  note         = {Paper and code coming soon}
}
```

## Acknowledgements

This work follows the long-term visual localization evaluation tradition of Sattler *et al.* (CVPR 2018). We thank the authors of
Oxford RobotCar, Nordland, CMU Seasons, St Lucia, Boreas, 4Seasons, NCLT and VPR-Space for releasing their datasets, and the authors of
NetVLAD, CosPlace, MixVPR, SALAD, MegaLoc and DINOv2 for releasing their models.

## Contact

For questions or collaboration, please open an [issue](https://github.com/nhatlong113/LACUNA---Localization-Aware-of-Coverage-and-UNmapped-Areas/issues).
