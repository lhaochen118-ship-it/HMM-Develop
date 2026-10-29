# DATA_AUDIT — dataset check for the HMM direction (Step 1, 2026-10-29)

Sources: meta files of `nhatlong1103/vpr-descriptor-dumps` (checked locally), raw-dataset file listings on Kaggle,
`robotcar_v2_train.txt`, `4seasons-poses`. Retrieval numbers come from `analysis/audit_data.py` (24 jobs, 6 descriptors ×
4 datasets, Kaggle T4, kernels `hmm-audit-*`); the JSON files are in `analysis/results/audit_*.json`.

## 1. Verdict per dataset

| Dataset | Structure (verified) | Usable for HMM? | Problems |
|---|---|---|---|
| **RobotCar-Seasons v2** | Map: 6,954 `overcast-reference` **rear** images (= 20,862 / 3 cameras of the official release). Queries: the 1,906 public **train** queries (rear only, 9 conditions, 187–239 each). `robotcar_v2_train.txt` = 4×4 **camera→world** matrix `[R | C]`, translation = camera centre (equals `q_C`). Verified independently: the rear camera's optical axis (column 3 of R) is anti-parallel to the direction of travel (median cos −0.98). Map step 0.97 m (median); map splits into 10 time-contiguous runs (longest 2,522). | **Weak for sequences.** Queries form **225 short snippets of 9 frames** (max 11, ≈ 9 m, step 0.98 m, dt 0.18 s), so an HMM sees at most ~10 frames. | No GT for the test queries (server only). **No odometry** in the release (Oxford RobotCar VO/INS is in the raw dataset, not on Kaggle). Only the rear camera is dumped. |
| **Extended CMU Seasons** | 11 slices with public query GT (6, 7, 8, 10, 11, 12, 13, 21, 22, 23, 24); **camera c0 only**; 11 conditions (dates 2010-09-01 … 2011-07-28; s13 has 10). 21,395 queries, map 2,418 (160–272 per slice). No NaN/zero poses. R convention as RobotCar (column 3 of R vs. motion: cos 0.72, c0 looks ≈ 45° to the side). | **Good.** Query sequences are long: 130 sequences, median 186 frames (max 257), step 0.95 m. | No odometry → simulate from GT. Slices are separate segments (gaps between slice groups 6–8, 10–13, 21–24). Small map per slice. |
| **Nordland** | 4 seasons, frame-aligned 1:1, every 8th frame (4,500 of 35,768; 225 steps of 7). Position = frame index; no 6DOF. | **Good for long sequences** (one 4,500-frame sequence per season). | Tunnels and station stops are **not removed** (the standard partition removes them), so R@1 is not directly comparable with published Nordland numbers. Repetitive railway = aliasing. |
| **MSLS val (CPH + SF)** | 18,871 map / 11,084 queries (all queries, panoramas removed), UTM + compass + view (Forward / Sideways / Backward). Conditions: city × season, plus cph-night (55). | Only after adding sequence keys. | **The dump meta has no sequence key** (only key, UTM, compass, view, date); the handoff note "có sequence key" is wrong. The sequence order must come from the raw MSLS `seq_info.csv`. Not the standard 740-query val subset. |
| **4Seasons** (`4seasons`, `4seasons-poses`) | 30 recordings with reference poses, 9 scenes (office_loop ×6, neighborhood ×7, countryside ×4, city_loop ×3, old_town ×4, business_campus ×3, parking_garage ×3). `result.txt` = metric stereo-VIO poses (`t tx ty tz qx qy qz qw`, 5–30 k per recording); `GNSSPoses.txt` = globally aligned poses with fusion quality; `Transformations.txt` gives the frames. Stereo **grayscale** undistorted images. | **Best candidate for real odometry** (true VIO, long routes, multiple seasons, natural route deviations). | **Not dumped yet**. Images are grayscale (replicate channels for the RGB descriptors). Four recordings have no released poses. |

## 2. Retrieval accuracy (top-1, pose copy)

R@1 at 5 / 10 / 25 m (Nordland: ±1 / 2 / 5 subsampled frames). Sattler'18 thresholds (0.25 m 2°, 0.5 m 5°, 5 m 10°) by
copying the pose of the top-1 map image. All numbers in %.

| ds | descriptor | R@1 | worst condition | Sattler (pose copy) |
|---|---|---|---|---|
| rc | megaloc | 90.8 / 92.2 / 96.0 | night 86.3 | 4.5 / 20.9 / 90.5 |
| rc | salad | 91.5 / 92.5 / 96.0 | night 87.8 | 4.7 / 21.7 / 91.1 |
| rc | mixvpr | 86.7 / 89.2 / 90.0 | night 57.9 | 4.9 / 22.7 / 85.0 |
| rc | cosplace | 78.2 / 80.5 / 82.7 | night 33.5 | 4.0 / 17.2 / 76.7 |
| rc | netvlad | 67.4 / 70.2 / 73.3 | night-rain 10.7 | 4.5 / 18.1 / 66.6 |
| rc | dinov2 | 55.1 / 63.8 / 72.7 | night 20.3 | 1.3 / 6.8 / 53.6 |
| cmu | megaloc | 93.0 / 98.4 / 99.3 | 20100901 89.2 | 6.9 / 19.9 / 92.6 |
| cmu | salad | 94.0 / 98.3 / 99.0 | 20101112 90.8 | 7.1 / 20.7 / 93.5 |
| cmu | mixvpr | 94.1 / 97.5 / 98.3 | 20100901 90.6 | 9.5 / 26.6 / 93.5 |
| cmu | cosplace | 90.6 / 96.3 / 97.4 | 20100901 84.5 | 5.8 / 17.1 / 90.2 |
| cmu | netvlad | 64.7 / 71.0 / 76.6 | 20101112 52.9 | 5.4 / 15.4 / 63.9 |
| cmu | dinov2 | 64.1 / 75.7 / 85.5 | 20101112 59.3 | 2.9 / 8.7 / 63.6 |
| nord | megaloc | 78.9 / 79.9 / 82.5 | winter 76.2 | – |
| nord | salad | 78.0 / 79.1 / 81.5 | winter 73.0 | – |
| nord | mixvpr | 74.0 / 74.8 / 77.3 | winter 65.0 | – |
| nord | cosplace | 62.8 / 64.0 / 66.6 | winter 45.7 | – |
| nord | netvlad | 35.6 / 36.6 / 39.1 | winter 12.2 | – |
| nord | dinov2 | 44.6 / 45.9 / 48.8 | winter 15.2 | – |
| msls | megaloc | 25.3 / 57.4 / 91.0 | cph-fall 16.1 (@5 m) | – |
| msls | salad | 24.5 / 55.7 / 88.2 | cph-fall 15.6 | – |
| msls | mixvpr | 23.5 / 53.2 / 83.1 | cph-night 1.8 | – |
| msls | cosplace | 22.2 / 49.6 / 78.9 | cph-night 3.6 | – |
| msls | netvlad | 14.4 / 31.3 / 46.9 | cph-night 0.0 | – |
| msls | dinov2 | 10.1 / 22.6 / 37.2 | cph-night 0.0 | – |

**Consistency with published numbers:**

- MSLS-val R@1@25 m for MegaLoc is 91.0, the same as its paper (91.0 on the 740-query subset). SALAD, MixVPR and
  CosPlace are 4–8 points below their papers because our query set is all 11,084 queries (sideways views, night),
  not the standard subset.
- The descriptor ranking (MegaLoc ≈ SALAD > MixVPR > CosPlace > NetVLAD/DINOv2) and the collapse at night
  (RobotCar) and in winter (Nordland) match the literature.
- Pose copy gives the expected Sattler'18 profile: high at (5 m, 10°) and very low at (0.25 m, 2°). **Global
  descriptors alone cannot reach the fine thresholds**; that needs local features and a 3-D model.

**The descriptor dumps are correct:** row order matches the meta files, GT poses are valid, and the conventions are
consistent. The previous audit kernels (`nguynduylm/hmm-audit-5`, `hmm-aud2-4`) give the same numbers.

## 3. Consequences for the HMM direction

1. **Odometry is the main gap.** RobotCar, CMU, Nordland and MSLS have none. Options:
   - simulate it from GT (noise + scale error), the standard practice in HMM-VPR papers that lack VO;
   - **4Seasons, which has real VIO** (needs a new descriptor dump).
2. **Sequence length.**
   - Long sequences: CMU (median 186 frames), Nordland (4,500) and 4Seasons.
   - RobotCar train queries are only 9-frame snippets. Fine for "short-window" evaluation, unsuitable for
     convergence or latency studies.
3. **With strong descriptors, place-level localisation is near saturation on RobotCar and CMU** (R@1@10 m ≈ 92–98 %).
   - A quick test (CMU, CosPlace) gives R@5 m of 90.7 % single-frame and 90.9 % for an HMM random walk.
   - An HMM with simulated odometry reaches 92.5 %.
   - The worst condition barely moves (84.5 → 84.8 %).
   - The headroom is in hard conditions (RobotCar night, Nordland winter), weak descriptors, off-map / changed map
     areas, and **reliability** (knowing when the estimate is wrong), not in average place recall.
4. **Step 2 (supplementary datasets):**
   - (a) Dump 4Seasons: subsample to about 1 m with the VIO poses, take cam0, run all 6 descriptors.
   - (b) Optionally add MSLS `seq_info` to get sequences.
   - Aachen Day-Night is single images, so it is not needed for the HMM.
