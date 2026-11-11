<div align="center">

# LACUNA

**L**ocalization-**A**ware of **C**overage and **UN**mapped **A**reas

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
datasets and six global descriptors (432 runs), LACUNA reports correct fixes on 93% of on-map frames. This exceeds a single-frame retrieval
oracle by about 8 points and its closed-world counterpart by 12–13 points, and the 5% false-report budget is exceeded on only 0.7% of runs.
Under the same protocol, three recent integrity-monitoring and off-map detection methods, tuned with ground-truth labels, violate the
budget on 56–90% of runs and incur 3.5–8.7× larger navigation errors. A batched GPU implementation runs the complete two-pass system at
about 6 ms per frame.

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

Full derivations are given in the paper: no net pull of a diffuse belief, a Ville-type bound on false reports within an off-map stretch (under an e-value assumption),
and the crossover analysis behind odometry-unobservable aliasing.

## Results

**Protocol.** 30% of the map is removed with freshly sampled hole layouts for each test group, and every decision rule is pre-registered
before the test. We report the following metrics.

- **Recall:** the fraction of on-map frames with a correct reported fix.
- **segFAR:** the fraction of 10-frame off-map segments with at least one report. The target is ≤ α = 0.05 *per run*.
- **Navigation error:** the error of a Kalman filter fed with the reported fixes.

One run is one dataset × descriptor × hole layout.

### Main comparison: two fresh test groups (144 runs each, same runs for every method)

Each cell shows *group 1 / group 2*.

| Method | Labels for tuning | Recall ↑ | Runs violating α ↓ (of 144) | Nav. error (m) ↓ |
|:---|:---:|:---:|:---:|:---:|
| Xu *et al.*, RA-L 2021 | ✓ | 0.692 / 0.696 | 81 / 83 | 51.0 / 56.6 |
| Claxton *et al.*, RA-L 2024 | ✓ | 0.738 / 0.739 | 104 / 101 | 44.3 / 48.9 |
| TAO, arXiv 2026 | ✓ | 0.834 / 0.839 | 130 / 126 | 109.5 / 114.9 |
| Closed-world hindsight baseline | ✗ | 0.795 / 0.810 | 0 / 0 | 14.5 / 15.4 |
| **LACUNA** (safe operating point) | ✗ | 0.920 / 0.919 | **0 / 0** | 12.9 / 14.6 |
| **LACUNA** | ✗ | **0.928 / 0.926** | **0 / 0** | **12.6 / 14.0** |
| *Single-frame oracle* † | *GT* | *0.847 / 0.848* | *0 / 0* | *10.6 / 11.7* |

Over all three fresh groups (432 runs), LACUNA exceeds α on **3 runs (0.7%)**, and on **none** at its safe operating point.

### Generalization to settings never used for tuning

Each cell shows *recall / runs violating α*.

| Setting (runs) | **LACUNA** | Closed-world baseline | TAO'26 | Xu'21 | Claxton'24 | Oracle † |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Holes 10% (108) | **0.932 / 0** | 0.777 / 0 | 0.843 / 92 | 0.646 / 35 | 0.737 / 86 | 0.827 |
| Holes 50% (108) | **0.872 / 4** | 0.751 / 4 | 0.842 / 93 | 0.609 / 30 | 0.678 / 60 | 0.829 |
| Natural off-map, 4Seasons cross-scene (36) | **0.945 / 0** | 0.756 / 0 | 0.578 / 4 | 0.581 / 10 | 0.678 / 5 | 0.822 |
| NCLT (6) | **0.769 / 0** | — | 0.756 / 6 | 0.526 / 1 | 0.663 / 5 | 0.724 |

<sub>† The oracle reports exactly the correct top-1 retrievals using ground truth. It is an upper reference for single-frame methods, not
a deployable system. LACUNA exceeds it because sequence evidence recovers frames whose top-1 retrieval is wrong. External baselines are
re-implemented from their papers, and their thresholds are tuned with labels on the two easiest conditions, as in the original works.</sub>

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
- [ ] Re-implemented baselines (TAO'26, Xu'21, Claxton'24)
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
