# Certified Sequential Localization (working draft)

*Draft for the A\* paper of the `hmm-navigation` direction. Numbers are filled in from `analysis/results/` as they come
in (RESEARCH_LOG Entry 18+).*

## 1. Problem

A robot with a monocular camera and odometry drives through a mapped area (map = one earlier traversal: images
with global descriptors and poses), which may have unmapped parts (route deviations, map holes, changed areas). At each
frame the localizer either reports a map place or abstains.

The safety-relevant error is **false localization during an excursion**: the robot is off the map for a while, and the
localizer reports a place at least once.

- Per-frame guarantees (P(accept | off-map frame) ≤ α, e.g. SelfCal) do **not** bound it. A 10-frame excursion gives
  10 chances to fail, and the failures are dependent.
- Window-level conformal tests do not bound it either. Exchangeability of windows fails under condition-dependent
  temporal dependence, and windows inside one spatial block are strongly correlated (Entry 18).

**Target.** For an excursion of H consecutive off-map frames,

> P( the localizer accepts any frame of the excursion ) ≤ α,

without labels, for any descriptor, and robust to appearance change.

## 2. Method

1. **Per-frame evidence.** For frame t, compute the SelfCal-AA p-value p_t of its top-1 match against the map's own
   leave-block-out null, cross-fitted (the per-frame test is fitted on map items of even blocks). Then
   ℓ_t = −log p_t.
2. **Odometry-gated sequence evidence (HMM view).**
   - The hypothesis of frame t is the HMM path that ends at its top-1 place x_t and moves with the odometry o.
   - The statistic is the evidence of all frames in the last L = H frames whose own top-1 lies on that path:

     R_t = Σ_{j<L} ℓ_{t−j} · 1[ ‖(x_t − x_{t−j}) − (o_t − o_{t−j})‖ ≤ ρ_o ]   (ANCH)

   - This is a max-product (Viterbi) score of an HMM with hard odometry gating and outlier-tolerant emissions.
   - Variants: RUNO (contiguous run only); RUN (exp11, consecutive matches within ρ, no odometry); FRAME (ℓ_t only).
3. **Excursion-level calibration on the map itself.**
   - Take every H-frame segment of the map's own traversal inside a held-out (odd) block.
   - Query it against the map without that block. It is off-map by construction, and its odometry comes from the
     map poses.
   - Its score is S = max over the segment of R_t.
   - With n null segments and k = ⌈(1−α)(n+1)⌉, set τ = S_(k).
   - At deployment, accept frame t iff R_t > τ, and report x_t.

**No labels, no training, no tuned threshold.** ρ_o is a physical odometry tolerance; H is the guarantee horizon.

## 3. Guarantees

**Theorem 1 (excursion-level validity).** Let S_1..S_n be the null segment scores and S* the score max_{t∈E} R_t of an
H-frame deployment excursion E. If (S_1, …, S_n, S*) are exchangeable, then

> P(∃ t ∈ E: R_t > τ) = P(S* > τ) ≤ α.

*Proof.* {∃t: R_t > τ} = {S* > S_(k)}. By exchangeability, the rank of S* among the n+1 scores is uniform (ties broken
at random). So P(S* > S_(k)) ≤ (n+1−k)/(n+1) ≤ α. ∎

- No assumption is made on the dependence of frames *inside* a segment. The segment is the exchangeable unit. This is
  exactly why window/frame-level calibration failed and segment-level calibration does not.
- The per-frame p-values of the null segments and of deployment frames are computed by the same cross-fitted test
  (fitted on even blocks only). The null segments are therefore processed identically to deployment data, as split
  conformal requires.

**Corollary 1 (appearance shift, dominance).** If the deployment excursion score is stochastically dominated by an
exchangeable copy (appearance change makes off-map frames *less* map-like), the bound still holds.

- The per-frame AA statistics are affine-invariant, and their dominance was validated in SelfCal (0/192 violations).
- The gate on odometry consistency does not depend on appearance.

**Corollary 2 (longer excursions).** An excursion of E frames is covered by ⌈E/H⌉ disjoint H-segments, so
P(false accept) ≤ ⌈E/H⌉ α (union bound). Alternatively, calibrate with H = E.

**Training-conditional validity.** With n null segments, the realised FAR given the map is Beta(k, n+1−k)
distributed. With α = 0.05:

| n | FAR exceeds 0.08 with probability |
|---|---|
| 200 | ≈ 0.03 |
| 70 (CMU) | ≈ 0.2 |

Large maps are needed for a tight per-map guarantee. A city-scale map has thousands of segments.

**Why gating by odometry matters (power and validity).**

- Without odometry (RUN), a *stationary* alias counts as consistent: a sequence of frames all retrieving the same wrong
  place. Its frequency depends on the condition (snow, night), and the map's same-condition null cannot represent it.
  The result is exp11's violations and high alias acceptance (0.09–0.15).
- With odometry, a false run must be a moving alias whose geometry follows the robot's motion. That is rare, and it is
  a property of the map's geometry, which the map null does represent.
- Under H1 (on-map, correct) the evidence grows linearly with L, so power increases with the horizon.

## 4. Experiments (status)

| Item | Status |
|---|---|
| Datasets | RobotCar-Seasons v2, Extended CMU-Seasons (Sattler'18 benchmarks), Nordland, 4Seasons (real VIO; dump in progress) |
| Descriptors | MegaLoc, SALAD, MixVPR, CosPlace, NetVLAD, DINOv2 |
| Validity | excursion FAR per condition, H ∈ {10, 30, 60} (RobotCar 5, 8), 3 random block grids, α ∈ {0.01, 0.05, 0.1} |
| Power | share of correct frames accepted, alias acceptance, latency to first correct acceptance |
| Baselines | FRAME (SelfCal per frame), RUN (exp11), label-calibrated thresholds (SAFEVPR / Quantile Transfer style), HMM with k-th-best off-map state (Xu'21, tuned), EVT-HMM (ours, tuning-free; ablation) |
| Navigation | Kalman filter + drifting odometry + accepted fixes, map with 30 % holes; 4Seasons with real VIO |

Preliminary numbers (Nordland, CosPlace, α = 0.05):

| statistic | FAR @ H=10 | FAR @ H=30 | correct frames accepted |
|---|---|---|---|
| FRAME | 0.030 | 0.030 | 0.42 |
| RUNO | 0.018 | 0.017 | 0.72 |
| ANCH | 0.019 | 0.020 | 0.87–0.93 |

All worst conditions are ≤ 0.037.

Navigation (Nordland, CosPlace, 30 % holes), mean / median error in frames:

| rule | mean | median |
|---|---|---|
| certified | 10.2 | 1.7 |
| SelfCal per frame | 23.6 | 6.8 |
| label threshold | 363 | 278 |
| accept all | 475 | 212 |
