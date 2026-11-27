# LITERATURE (T1.2) — working bibliography

Full 94-entry catalogue: *HMM_Master_Research_Plan_Integrated.pdf*, Phụ lục C (statuses ✓/○/⚠ as reported
there on 24/11/2026; not re-verified unless marked "re-checked 27/11"). This file keeps the entries that the
current method/experiments depend on, with their role. ⚠ entries are never used as evidence.

| Group | Reference | Role in this project | Status |
|---|---|---|---|
| Benchmark | Sattler et al., "Benchmarking 6DOF Outdoor Visual Localization in Changing Conditions", CVPR 2018 | foundation: RobotCar Seasons / CMU Seasons, day–night difficulty, multi-image motivation | ✓ |
| Benchmark | Toft et al., "Long-Term Visual Localization Revisited", TPAMI 2022 | v2 datasets/protocol | ✓ |
| Sequence (non-prob.) | Milford & Wyeth, SeqSLAM, ICRA 2012 | baseline B04 (causal, tuned) | ✓ |
| Sequence (non-prob.) | Pepperell et al. SMART ICRA'14; Naseer et al. AAAI'14; Vysotska & Stachniss RA-L'16 | related sequence matching | ✓ |
| HMM / Bayes VPR | Hansen & Browning, "Visual place recognition using HMM sequence matching", IROS 2014 | closest HMM prior art (velocity constraints, Viterbi) | ✓ re-checked 27/11 (CMU RI page) |
| HMM / Bayes VPR | Doan et al., ICCV 2019; HM⁴ RA-L 2021 | HMM VPR at scale | ✓ re-checked 27/11 (arXiv 2011.00450) |
| HMM / Bayes VPR | Hausler et al., Multi-Process Fusion, RA-L 2019 (arXiv 1903.03305) | HMM over recent images, dynamic sequence length | ✓ re-checked 27/11 |
| HMM / Bayes VPR | Xu, Sünderhauf, Milford RA-L 2021 (topometric, new place); Jaenal et al. IJRR 2023 | open-set / topometric baselines | ✓ |
| HMM / Bayes VPR | Cummins & Newman FAB-MAP IJRR 2008/2011 | probabilistic appearance + new place | ✓ |
| Appearance VO | Milford & Wyeth, RatSLAM scanline-intensity visual odometry (T-RO 2008) | prior art for "image change as speed cue" (ME module) | ○ (classic, not re-checked) |
| Uncertainty | Zaffar et al., SUE, CVPR 2024 | off-map / uncertainty baseline (L2 to nearest ref) | ✓ |
| Uncertainty | Hussaini et al., sequence-matching receptiveness prediction, arXiv 2503.06840 | gating when sequences help (novelty threat for M2) | ✓ re-checked 27/11 |
| Uncertainty | Miller et al., "Through the lens of doubt", arXiv 2510.13464 | overconfidence of training-free uncertainty in aliasing | ✓ re-checked 27/11 |
| Likelihood | Molloy et al., training-free likelihood for VPR + Bayesian fusion | closest to M1 | ✓ seen in search 27/11 (details not yet read) |
| Gen. Bayes | Bissiri, Holmes, Walker JRSS-B 2016; Miller & Dunson JASA 2019 | tempered / coarsened likelihood theory behind β | ✓ |
| Descriptors | NetVLAD (CVPR'16), CosPlace (CVPR'22), MixVPR (WACV'23), SALAD (CVPR'24), MegaLoc (CVPRW'25), DINOv2 | descriptor ladder (feature bank) | ✓/○ |
| HMM theory | Rabiner 1989; Cappé, Moulines, Rydén 2005; Yu HSMM 2010 | forward/Viterbi/HSMM | ○ |
| 2026 preprints | TRAIL (2609.07373), UniPR-3D, SG2Loc, Adapt-STformer | possible novelty threats | ⚠ unverified |
