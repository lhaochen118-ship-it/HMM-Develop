# DATASETS — registry for the HMM sequence-localization study (updated 28/11/2026)

All datasets live on Kaggle under account **nhatlong1103** (public unless noted, so the 14 CPU-only lab accounts can mount
them). "Dump" = global descriptors (float16, L2-normalised) per image + `meta/*.npz` (names, poses/positions, conditions);
HMM experiments run on dumps only (CPU). Images are needed only for new descriptors (GPU) or geometry (k05/k09/k11).

## A. In use (main table, PROTOCOL v1)
| Short name | Kaggle ref | Content | Ground truth | Status in hmmloc |
|---|---|---|---|---|
| Nordland | `nordland-full-47-6gb` (images), dumps `vpr-descriptor-dumps` (`nord_*`) | 4 seasons, train route, frame-aligned | frame index | `load_nordland`, `load_nordseg` (k01 video-rate) |
| RobotCar Seasons v2 | `robotcar-seasons-v2`; dumps `vpr-descriptor-dumps` (`rc_*`) | 9 conditions incl. night | 6DoF (NVM) | `load_robotcar`, M5 k05 |
| Extended CMU Seasons | `extended-cmu-seasons`(+`-2`); dumps `vpr-descriptor-dumps` (`cmu_s*`) | 11 slices, 12 dates | 6DoF | `load_cmu`, k09/k11 |
| 4Seasons office_loop / countryside / old_town | `4seasons`, `4seasons-poses`; dumps = kernels hmm-k02/k03/k04 (+ `vpr-dumps-4seasons`) | real stop-and-go, night | 6DoF (RTK-GNSS+VIO) | `load_4s_stopgo` |
| MSLS val cph / sf | dumps `vpr-descriptor-dumps` (`msls_*`) | city-scale, many dates | UTM + compass | `load_msls` (spatial graph) |
| SeqVLAD per-frame (all of the above) | `hmm-seqvlad-frames` (public; flat: `seqvlad/`, `meta/`) + local raw sums (FB `hmm-k12-seqvlad/dump/seqvlad_raw`) | CCT384+SeqVLAD, MSLS-trained | — | `seqvlad`, `seqvlad_raw` descriptors |

## B. Already on Kaggle (uploaded by the `hmm-navigation` / `hmm-2nd-idea` branches) — NOT yet used here
| Short name | Kaggle ref | Content | Why it fits the HMM study | Status (28/11) |
|---|---|---|---|---|
| **Boreas** (Burnett et al., IJRR 2023, CC BY 4.0) | `boreas-vpr-dump` (9.7 GB, 6 descriptors), images `boreas-vpr-images-1..5` | 29 traversals of the same ~8 km Glen Shields route over one year (snow, rain, sun, night 2021-09-14), frames every >=1 m, **ENU positions + real odometry (wheel DMI, gyro yaw, velocity)** | Long repeated route with seasonal change + REAL odometry → test motion model with measured speed (latent velocity vs odometry-driven transition), multi-traversal maps | loader `load_traversals('boreas')` (heading from trajectory; rpy is camera attitude); E18 on `boreas:8` × 4 descriptors running on CPU accounts |
| **NCLT** (Carlevaris-Bianco et al., IJRR 2016) | `nclt-vpr-dump` (dumps + `sensors/*.npz` odometry), images `nclt-cam5-<date>` (6 sessions) | Campus, 9 sessions Jan 2012 – Apr 2013, Ladybug cam5, indoor/outdoor, foliage | Pedestrian-speed robot with stops and revisits → off-map / exit-re-entry (null state), dwell (HSMM) | loader `load_traversals('nclt')` (73 % of queries on-map → null state matters); E18 × 4 descriptors running on CPU accounts |
| **St Lucia** (Milford & Wyeth, ICRA 2008) | `stlucia-vpr-dump`, frames `stlucia-vpr-frames` | 6 traversals (Aug–Sep 2009) at different times of day, suburban driving, GPS | Classic SeqSLAM benchmark; varying speed, traffic stops | loader `load_traversals('stlucia')`; E18 done: NetVLAD single 0.606 → HMM 0.972; CosPlace/SALAD/MegaLoc saturated (single ≥ 0.995 at 25 m) → use a stricter tolerance (e.g. 10 m) if St Lucia is reported |
| **Oxford RobotCar (raw)** (Maddern et al., IJRR 2017) | `oxford-robotcar-vpr-dump`; raw `robotcardata`, `robotcarquery` | many traversals 2014–2015 (dumps per traversal) | Long-term, many conditions, INS poses → second RobotCar protocol beyond Seasons v2 | loader `load_oxford` |

## C. Added 28/11/2026 for this study
| Short name | Kaggle ref | Content | Ground truth | Licence | Next step |
|---|---|---|---|---|---|
| **QUT Gardens Point Walking + SouthBank Bicycle** | `vpr-qut-gardenspoint-southbank` | GP: day_left, day_right, night_right (200 frames each, walking, lateral shift); SouthBank: frames1/frames2 (bicycle) | frame i of each traversal = place i | CC BY 4.0 (Zenodo 4590133) | descriptors: kernel `huyenco/hmm-k13-newds` (T4); loader `load_qut` (`qut-gp`, `qut-sb`) |
| **Brisbane-Event-VPR (consumer-camera frames)** (Fischer & Milford, RA-L 2020) | `vpr-brisbane-6times-frames` (156 MB, ready; 6 × 629–715 frames, GPS tracks agree within 3–4 m median) | Same ~8 km suburban route driven 6 times: sunrise, morning, daytime, sunset1, sunset2, night; frames at 1 fps, 640 px | GPS ($GPRMC) per frame → local east/north metres; speed | CC BY-NC-SA 4.0 (Zenodo 4302805) | descriptors: kernel k13; loader `load_traversals('brisbane')` (map = daytime, 25 m) |

## D. Considered, not downloaded (reason)
| Dataset | Reason |
|---|---|
| SFU Mountain (Bruce et al., 2015, CC BY 4.0) | several hundred GB (torrent of ROS bags + JPEG); only 383 hand-matched places. Revisit if forest/trail domain is needed |
| Ford Multi-AV Seasonal, KITTI-360 | very large; Boreas already covers seasonal driving with odometry |
| Pittsburgh250k, Tokyo 24/7, SPED, Aachen | single images, no sequences → not suitable for HMM filtering |
| Brisbane-Event-VPR event streams (.bag, 79 GB) | event camera out of scope; only the consumer-camera mp4 + GPS are used |

## E. Compute plan for these datasets
- GPU (only the 5 GPU accounts: nhatlong1103, quynhtran35, yuan1103, phatle1578, huyenco): descriptor extraction for
  section C (one L4x4 session with the multi-model/one-decode extractor of guide §4–5, or a T4 session — total ~12k images).
- CPU (the other 14 accounts × 5 sessions): every HMM / baseline run on dumps via `kaggle/cpu/build_cpu.py`
  with `ds:nhatlong1103/<dump dataset>=<feature-bank name>` sources; merge with `research/merge_remote_runs.py`.
- Protocol: calibration/test split by whole traversals (PROTOCOL.md); hyper-parameters on calibration only.
