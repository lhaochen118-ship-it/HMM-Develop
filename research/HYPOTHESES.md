# HYPOTHESES — pre-registered (thresholds locked before the corresponding test run)

Status: [H] untested · [S+] supported on dev/limited · [S−] refuted on dev/limited · [V+]/[V−] verified · [~] inconclusive
H1–H19 are inherited verbatim from Master Plan v2.0 §5.3. H20+ are new in Master Plan v3 (HMM-centred method).
Evidence for each status change must cite run IDs from `registry/runs.jsonl`.

| ID | Statement (short) | Support criterion | Refute criterion | Status | Evidence |
|---|---|---|---|---|---|
| H1 | Non-oracle HMM ΔR@1>0 vs single image (paired block CI95 excl. 0) | ≥3/4 datasets with single R@1 in 0.3–0.95 | CI∋0 or negative on ≥2 datasets | [S+] | E01/E18: Nordland (incl. time-warp), CMU, RobotCar all CIs >0 for NetVLAD/CosPlace; F01, F08 |
| H2 | Inverted-U gain vs single-image accuracy | ≥30 cells, quadratic coef<0, peak 0.3–0.8 | monotone/flat | [H] | |
| H3 | Time-warp removes ≥50% of the v=1 legacy gain | — | <20% | [S+] | fixed-kernel gain SALAD 0.175→0.061 (−65%); F04 |
| H5 | ρ̂ increases as stride decreases; NLL/CW grow with frame rate for naive HMM | ρ̂≥0.3 at stride 1 on ≥3 datasets | ρ̂<0.1 or no dose-response | [H] | |
| H6b | β=1/VIF(ρ̂) close to dev-optimal β* | |β−β*|≤0.1 in ≥80% cells | >0.2 in >50% cells | [H] | |
| H7 | Calibrated LLR + null reduces NLL ≥10% vs softmax-τ | ≥2 datasets | <3% on ≥2 datasets | [S−] | E01 v2: LLR NLL ≥ τ on CMU/Nordland; off-map AUROC 0.979 vs 0.988 (F12) |
| H9 | Distinctiveness (hubness) correction reduces lock-in ≥30% | | <10% | [H] | |
| H10 | Oracle-emission swap reduces error more than oracle-transition swap | ≥3/4 datasets | reverse | [H] | |
| H13 | Held-out dataset keeps ≥50% in-domain gain | | | [H] | |
| H14 | Filter update ≤10 ms/frame at M≈30k | | >50 ms | [H] | |
| H17 | (p,v) / latent-velocity recovers ≥70% of oracle gain under time-warp | | <40% | [S+]/partial | full IA-HMM: NetVLAD 84% (s1), CosPlace 81%, SALAD 61%, MegaLoc 70% (F04, F08); real 4Seasons: beats fair fixed kernel in 6/7 cells, CI excl. 0 in 2 (F15) |
| H19 | Recovery + multi-mode reduces false-lock duration | | | [H] | |
| **H20** (status [S−] standalone, [S+] jointly with LV+ME under variable speed — F04, F11) | **Information-aware HMM (IA-HMM):** per-frame evidence weight β_t = β₀·(1−ρ_t)/(1+ρ_t), with ρ_t predicted *label-free* from consecutive query-descriptor similarity, beats the best *fixed* β (selected on dev) in test NLL by ≥5% and is not worse in R@1 (−0.5 pt) on ≥2 datasets with video-rate queries | ≥2 datasets | NLL gain <2% or R@1 drop >1 pt | [H] | |
| **H21** (status partial — F10) | **Fixed-lag HMM smoothing** (lag ℓ frames) improves R@1 over causal filtering by ≥2 pt at ℓ≤10 frames on ≥2 datasets | | <0.5 pt | [H] | |
| **H22** (status [S+] 27 W / 5 T / 1 L over 33 cells — F15) | **Calibrated-LLR HMM beats tuned SeqSLAM** (same descriptor, same causal window budget, both tuned on dev) in R@1 on ≥3 datasets | | worse on ≥2 | [H] | |
| **H23** (status [S+] — F01, F09) | **Weak-descriptor amplification:** HMM gain over single-image is ≥10 pt for NetVLAD/CosPlace on Nordland and RobotCar-night while ≤3 pt for MegaLoc/SALAD on easy conditions (consistent with H2) | | | [H] | |
