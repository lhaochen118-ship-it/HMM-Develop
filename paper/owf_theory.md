# Open-world filter (OWF) — theory (RESEARCH_LOG Entry 10)

*Idea 2b of branch `hmm-2nd-idea`. Code: `analysis/owf.py`. Notation follows the code.*

## 1. Model

**State.** A grid G of cells c (size g = excl / 5) over the map's bounding box grown by a band B, cells farther than B from every map image
removed, plus a far state Ω. Map images i = 1..n with positions m_i. A cell is *mapped* (c ∈ 𝓜) when it contains at least one image.
N = cells within excl of some image (𝓜 ⊂ N); U = G \ N ∪ {Ω}.

**Motion (mass-conserving).** b⁻_t = K_t b_{t−1}: shift by the odometry increment u_t, Gaussian blur with variance
q|u_t| + drift²(2L_s|u_t| + |u_t|²) per axis, mass leaving the band moved to Ω, kidnap: (1 − p_kid) b + p_kid π₀, Ω re-entry p_in Ω π₀.
Every step maps a probability vector to a probability vector (K_t is stochastic); **no step renormalises over 𝓜**.

**Emission (likelihood ratios against one reference p₀).** For the frame z_t: robust z-scores z_{t,i} of its similarities over all n images;
L_{t,i} = exp(β z_{t,i}) / ((1/n) Σ_j exp(β z_{t,j})), L_t(c) = mean_{i∈c} L_{t,i} for c ∈ 𝓜, L_t(c) = 1 for c ∉ 𝓜 and for Ω. Evidence weight
w_t = min(1, |u_t| / ℓ), ℓ = 0.4 excl: the update uses L_t^{w_t} (cells outside 𝓜 keep 1). Posterior b_t ∝ b⁻_t L_t^{w_t}.

**Decision.** D_t = max over the 12 heaviest mapped cells c of b_t(disc(c, excl)); report the image nearest to the posterior mean of that disc
iff D_t ≥ 1 − ε.

## 2. Proposition 1 (no net pull of a diffuse belief)

*If the predicted belief restricted to the images is uniform, b⁻_t(i) = a / n for every image i (a = b⁻_t(map images)), then with w_t = 1
Σ_i b⁻_t(i) L_{t,i} = a for every frame z_t.*

*Proof.* Σ_i (a/n) L_{t,i} = a · (1/n) Σ_i exp(βz_{t,i}) / ((1/n) Σ_j exp(βz_{t,j})) = a. ∎

*Meaning.* A robot with no positional knowledge gains or loses mapped mass only through the SHAPE of the profile (which image is high),
never through its level (how similar the frame is to the map as a whole); in a topological HMM the mapped mass is 1 by construction. With
w_t < 1, Jensen gives Σ_i (1/n) L_{t,i}^{w} ≤ 1: distance weighting adds a slight pull towards the unmapped space.

## 3. Proposition 2 (false reports in an off-map stretch)

*Setting.* An off-map stretch is a time interval [t₀, t₁] during which the robot is farther than off_d from every image. A report at t
implies b_t(N) ≥ 1 − ε (the reporting disc lies in N). Let π̃_t be the UNNORMALISED filter: π̃_t = K_t π̃_{t−1} ⊙ L_t^{w_t} (π̃_{t₀} = b_{t₀}).
Let λ ∈ [0, 1) bound a.s. the share of the U-mass that the motion and the seeds move into N during the stretch.

*Assumption (E1).* For every cell c of N and every t in the stretch, E[L_t(c)^{w_t} | 𝓕_{t−1}] ≤ 1 (the weighted LR of every near-map cell is a
conditional e-value while the robot is elsewhere).

*Claim.* P(∃ t ∈ [t₀, t₁]: report at t) ≤ ε (1 + O₀) / ((1 − ε)(1 − λ)), with O₀ = b_{t₀}(N) / b_{t₀}(U).

*Proof.* (i) T_t = π̃_t(N) + π̃_t(U) is a nonnegative supermartingale: K_t conserves total mass; on U the LR is 1; on N, by (E1),
E[Σ_{c∈N} (K_t π̃_{t−1})(c) L_t(c)^{w_t} | 𝓕_{t−1}] ≤ (K_t π̃_{t−1})(N). (ii) On U the LR is 1, so π̃_t(U) only decreases through mass moved
into N: π̃_t(U) ≥ (1 − λ) π̃_{t₀}(U). (iii) A report needs b_t(N) ≥ 1 − ε, i.e. π̃_t(N) ≥ k π̃_t(U) with k = (1 − ε)/ε, hence
T_t ≥ k (1 − λ) π̃_{t₀}(U). (iv) Ville's inequality: P(sup_t T_t ≥ x) ≤ T_{t₀} / x with x = k (1 − λ) π̃_{t₀}(U) gives
(π̃_{t₀}(N) + π̃_{t₀}(U)) / (k (1 − λ) π̃_{t₀}(U)) = (1 + O₀) ε / ((1 − ε)(1 − λ)). ∎

**Consequences.** (a) *Edges.* A robot tracked into a hole enters the stretch with its mass dead-reckoned into U (O₀ ≈ motion tail, λ ≈
tail + p_kid (t₁ − t₀)), so the bound is ≈ ε — there is no separate edge term (contrast: the topological filter puts all mass on the
remaining nodes at the hole border; idea 1's audit found edge rates 0.08–0.11). (b) *Starts.* At a sequence start O₀ = p_map0 / (1 − p_map0)
≈ 1 and λ can be large (diffuse U mass flows into N), so the start is the weak case — the design failures (CMU starts at ε ≥ 0.05; Nordland
sequences that START in a hole) are exactly there. (c) *Kidnap.* p_kid enters λ linearly with the stretch length: the design moved it from
1e-4 to 1e-12 after the Boreas look-alike 170 m behind a hole entry. (d) *(E1) and coherent aliasing.* (E1) fails when consecutive off-map
frames match the same look-alike stretch: then E[L_t(c) | 𝓕_{t−1}] > 1 at the look-alike cell. The evidence weight w_t is a crude
correction (views ℓ apart counted as independent); the empirical inflation (observed false-report rate / bound) is measured by the position
audit, and ε = 1e-3 = α / 50 is chosen to absorb it.

## 4. Proposition 3 (presence by position: the hole is not a test)

*Let the motion model be exact (the true increment lies within the blur) and the robot be localised at t₀ (b_{t₀}(disc(x_{t₀}, r)) ≥ 1 − δ).
Then for every later t at which the robot is farther than off_d from the map and no frame since t₀ has had LR evidence (all w_s L_s = 1),
b_t(N) ≤ δ + P(|e_t| > off_d − excl − r), e_t = accumulated dead-reckoning error since t₀.*

*Proof.* Without evidence the posterior is the motion prediction: the mass that was within r of x_{t₀} is carried to within r + |e_t| of x_t,
and it lies outside N when r + |e_t| < off_d − excl (x_t is more than off_d from every image, N is within excl of an image). The rest has mass
≤ δ. ∎

*Meaning.* Leaving the map is decided by dead reckoning against the map's known coverage, not by an appearance test; appearance evidence can
only move mass by the LR mechanism of Proposition 2. The quantity that matters is the drift of the odometry over the hole (Boreas wheel
odometry: 2–6 m over 8 km; 4Seasons VIO: 1–12 % of the path), which the process noise and the online evidence selection of q absorb.

## 5. Cost

One grid filter per q value: per frame a whole-cell shift (O(|G|)), a blur only when the accumulated variance passes (g/2)², one
bincount over the n images, a normalisation, and the disc masses of 12 candidate cells. |G| ≈ 0.7–1.0 × 10⁵ cells for the 2-D datasets
(Nordland 4.5 × 10³). Three filters (online q selection): 2–14 ms/frame on one local CPU core, 22–41 ms/frame on a Kaggle CPU session
running four jobs on four vCPUs. No forward simulation, no map surgery, no learned score, no calibration data.

## 6. Proposition 4 (hindsight-calibrated open-world decision; Entry 16, drafted before its test)

*Why.* Proposition 2 needs (E1): the weighted likelihood ratio of every near-map cell is a conditional e-value while the robot is elsewhere.
Coherent perceptual aliasing breaks (E1): consecutive off-map views keep matching one look-alike stretch whose images then get an expected
LR far above 1. Measured on development runs (`analysis/owf_alias_diag.py`): on Nordland, confident-but-wrong hypotheses arise deep inside
holes (path ≥ 32 excl from the sequence start, 82 % of their frames off the map), last a median 2.3 excl (p90 16 excl) and reach disc mass
1 − 1e-10, i.e. evidence ~1e10 against a dead-reckoned tail mass. The incumbent rule (Entry 15) therefore does not read the decision off the
posterior at one ε: it ORs fixed tiers m(1e-5, 16), m(1e-8, 2), t(3e-4, 0.5) chosen on development seeds. Proposition 4 replaces those
constants by thresholds the deployment calibrates on its own hindsight, with a finite-sample guarantee that does not need (E1).

*Setting.* Score s_t = −log10(1 − D_t) (D_t: OWF disc mass, Section 1). Stratum k(t) = bin of the odometry path since the sequence start
(excl units; edges fixed in advance, e.g. {0, 2, 16}). Hindsight null (HSI, `paper/hsi_theory.md`): frames whose two-sided dead-reckoning
bridge, anchored on stretches where an INDEPENDENT estimator (the topological chain) is geometrically self-verified, places the robot
possibly off the map, or possibly farther than excl from the OWF report, or that are never bridged; each label becomes usable at the
deployment rank at which its bridge closes. Calibration units (300 m of path) are held out with probability 1/2, independently of the data.
A null segment = H consecutive null frames of one held-out unit and one stratum; its conformity score is the segment maximum of s_t, or +∞
if the other report branch (OWF-H) reports inside it (joint calibration of the union). At deployment rank T the threshold of stratum k is
τ_k(T) = the ⌈(1 − α)(m + 1)⌉-th smallest score among the m stratum-k segments available before T (τ = ∞ if m < 1/α − 1).
Report at t iff OWF-H reports or s_t > τ_{k(t)}(T_t).

*Claim.* Let S be a future H-frame stretch of stratum k on which the robot is off the map, and assume (X) its score is exchangeable with
the scores of the m calibration segments of stratum k used at its time. Then P(the rule reports somewhere in S) ≤ α (and ≥ α − 1/(m+1)
for continuous scores). The bound holds whatever the emission model, its misspecification under aliasing, or the dependence between frames.

*Proof.* Split conformal (Vovk et al.; Lei et al. 2018): with exchangeable scores, the rank of the new score among the m + 1 is uniform, so
P(score_S > τ_k) ≤ 1 − ⌈(1 − α)(m + 1)⌉/(m + 1) ≤ α. A report in S happens iff the segment maximum of the rule's score exceeds τ_k
(either branch; the OWF-H branch enters the score as +∞). ∎

*Assumptions and scope.* (X) is where the hindsight labels enter: the null is a superset of the off-map frames when the bridges are correct
(it also holds possibly-wrong and never-verified frames), which makes the threshold conservative but keeps (X) plausible only if the
off-map stretches of a stratum are not systematically harder than the null stretches of the same stratum. Bridges built on the OWF's own
track would certify a coherent alias (its track is odometry-consistent by construction; Entry 11), so the bridges come from the topological
chain, which is computed independently of the OWF. Mondrian strata by path since the start make the guarantee hold per stratum, so the
weak start case of Proposition 2 is calibrated on start segments only. The guarantee is marginal over segments of the deployment, not per
run; the per-run tail is measured (runs > α).

**Result (Entry 16, development set A, 399 runs): Proposition 4 does not replace the fixed tiers.** Every hindsight-calibrated variant lost to
the incumbent on recall (−0.017 … −0.027), per-run validity (23–46 runs above α vs 1) and navigation (+2 … +4.6 m). The guarantee bounds the
EXPECTED share of null segments with a report; the per-run segFAR then scatters around α, whereas the incumbent operates about ten times
below α. The proposition stays true; it is the wrong target for a per-run requirement.

## 7. Proposition 2′ (Ville bound with an inflation budget) and its measured inflation

*Assumption (E1-K).* Over an off-map stretch S = [t₀, t₁], E[L_t(c)^{w_t} | 𝓕_{t−1}] ≤ κ_t for every near-map cell c, with κ_t ≥ 1 and
Π_{t∈S} κ_t ≤ K almost surely (K = 1 is (E1)).

*Claim.* P(∃ t ∈ S: report at t) ≤ K · ε (1 + O₀) / ((1 − ε)(1 − λ)).

*Proof.* As in Proposition 2, with T_t / Π_{s ≤ t} κ_s a nonnegative supermartingale: E[T_t | 𝓕_{t−1}] ≤ π̃_{t−1}(U-part) + κ_t
π̃_{t−1}(N-part) ≤ κ_t T_{t−1}. A report needs T_t ≥ k(1 − λ) π̃_{t₀}(U) (k = (1 − ε)/ε), hence T_t / Π κ_s ≥ k(1 − λ) π̃_{t₀}(U) / K; Ville's
inequality gives the claim. ∎

*Meaning.* A fixed threshold ε is safe at level α while the inflation budget satisfies K ≲ α / (2ε) (O₀ ≈ 1 at a start, λ ≈ 0). Examples:
ε = 1e-3 tolerates K ≈ 25; ε = 1e-5 tolerates K ≈ 2.5 · 10³; ε = 1e-8 tolerates K ≈ 2.5 · 10⁶. Coherent perceptual aliasing makes K a heavy-tailed
property of the (map, descriptor, route) triple.

*Measured inflation* (`analysis/results/owf/s1105/inflation_dev_a.json`): OWF alone on set A, K̂(ε) = observed segFAR(ε) / (2ε), pooled per
dataset.

| dataset | ε = 1e-2 | 1e-3 | 1e-4 | 1e-5 | 1e-6 | 1e-8 | 1e-10 |
|---|---|---|---|---|---|---|---|
| 4Seasons (3 scenes), St Lucia | ≤ 0.4 | ≤ 1 | 0 | 0 | 0 | 0 | 0 |
| Boreas | 0.25 | 1.3 | 6.3 | 21 | 33 | 0 | 0 |
| Oxford | 0.04 | 0.27 | 1.4 | 9.7 | 97 | 8.7 · 10³ | 8.7 · 10⁵ (one persistent segment) |
| Nordland | 3.4 | 12 | 56 | 200 | 1.1 · 10³ | 4.1 · 10⁴ | 0 |
| CMU | 4 | 22 | 140 | 880 | 3.6 · 10³ | 4.3 · 10³ | 0 |

**Reading.**
- Where aliasing is mild (4Seasons, St Lucia, Boreas at ε ≥ 1e-3), (E1) holds empirically and Proposition 2 is valid as stated.
- On CMU (short sequences, global starts) and Nordland (repetitive railway, long holes), K̂ GROWS as ε shrinks. Alias evidence is
  heavy-tailed: segFAR falls far more slowly than ε. That is why OWF alone needs ε ≈ 1e-8 there, and why the incumbent combines extreme
  fixed thresholds with path conditions and a calibrated learned branch.
- A per-run guarantee in this regime needs either a bound on K from the map itself (how strongly and for how long two places of the map
  look alike) or a decision whose risk does not grow with the evidence. Both are open.

## 8. Proposition 5 (no teleport: re-entry seeds and coherent aliasing; Entry 19, drafted before the development wave is read)

*Observation that motivates it.* The filter of Section 1 moves the mass of the far state Ω back into the grid at rate p_in per frame,
distributed over the START prior (half of it on the map images in proportion to their counts). In steady state the mass leaving the band
equals the re-entering mass, so every frame seeds every map image with roughly p_in · Ω / n mass, wherever the robot is. A coherent alias
needs only such a seed: with evidence K ≈ 10¹⁰ over an episode (Nordland, Section 7), a seed of 10⁻⁸ becomes certainty. Measured on the
Nordland design run (cosplace, seed 1): reports wrong at 1 − 1e-5 / 1 − 1e-8 = 26 / 22 frames with p_in = 0.01; **0 / 0 with p_in = 0**.
segFAR at ε = 1e-3 falls 0.038 → 0.015, navigation error 15.3 → 9.1 m, and recall rises 0.975 → 0.980.

*Claim.* In Proposition 2, let the seeds be the kidnap redraw (rate p_kid over the prior) and the far-state re-entry (rate p_in over a
distribution ρ). Then the share of U- and Ω-mass moved into N over a stretch of m frames by seeds alone is
λ_seed ≤ m (p_kid + p_in · Ω_max · ρ(N)), with Ω_max the largest far-state mass in the stretch. With ρ = the start prior, ρ(N) ≥ p_map0 = 0.5:
λ_seed grows linearly with the stretch and is multiplied by the evidence inflation K of Proposition 2′. With ρ supported on the band edge,
ρ(N) = 0 whenever the band is wider than excl (always, band = 12 excl), so λ_seed = m · p_kid (10⁻¹² per frame). With p_in = 0 the far state
is absorbing, and λ_seed is the same.

*Proof.* Each predict step moves p_kid · tot · prior(N) ≤ p_kid of mass into N by the kidnap redraw and p_in · Ω_t · ρ(N) by re-entry; sum
over the m steps of the stretch. ∎

*Meaning.* The bound of Proposition 2′ is K · ε (1 + O₀) / ((1 − ε)(1 − λ)) with λ ≥ λ_seed. A re-entry over the map makes the aliasing
risk depend on how many seeds coherent evidence can amplify; a physical re-entry (from far away the robot can only come back through the band
edge) removes that channel, leaving the motion tails as the only way mass reaches a look-alike. The price is slower recovery when the
belief has lost the true position everywhere (only kidnap and the motion blur can re-seed it), which the development wave measures.

## 9. Proposition 6 (the crossover of the emission, and aliases the odometry cannot see; Entry 22, drafted before its development wave)

*Observation that motivates it (Entry 21).* On CMU seed 60 the hole covers a straight road (slices 11–12). Every filter (OWF, HSI) follows a
copy of the true track shifted about 204 m back along the same road. The offset (−188, −78) m is constant over 17 sequences, along the road
direction, and two independent descriptors pick the same copy (median 4.9 m apart). The copy matches weakly: CosPlace cosine median 0.445
vs 0.77 at the true place with the full map; robust z median 3.3 vs 7.3 for true matches. But a shift along a straight line is invisible to
the odometry, so the motion model cannot reject it.

*Setting.* Frame t has robust z-scores z_ti over the n map images (median 0, MAD-scaled). The filter of Section 1 uses
log L_ti = β z_ti − A_t, with A_t = log mean_j exp(β z_tj), and LR 1 for unmapped cells and Ω. Write w_t ∈ [0, 1] for the path weight
(min(1, |u_t| / ℓ)).

*Claim (a): crossover.* Relative to the unmapped cells, image i gains mass at frame t iff z_ti > c_t := A_t / β. For a background-only
profile with i.i.d. N(0, 1) scores, A_t → β² / 2 as n grows, so c_t → β / 2. With β = 1 the crossover is about 0.5 robust SD: any image above
roughly the 70th percentile of the background gains mass.

*Claim (b): a track the odometry cannot see.* Let a = (a_t) be a motion-consistent copy of the true trajectory, with all of its positions
unmapped except the copy's images (straight road, shift s along the road), and let the true positions be unmapped (hole). The motion
likelihoods of the true track and the copy are equal. Their posterior log ratio after m frames is therefore
Σ_t w_t β (z_t,a_t − c_t) (copy minus true), which grows without bound whenever the copy's mean z exceeds c ≈ 1/2. No decision threshold
fixes this, because the copy's mass converges to 1.

*Claim (c): Gaussian-shift crossover.* Suppose the true-match score is N(μ₁, 1) and every other image is background N(0, 1). The exact LR is
exp(μ₁ z − μ₁² / 2). Tempering it to the filter's slope β (correlated evidence, Section 7) gives log L_ti = β (z_ti − μ₁ / 2). The crossover
is then μ₁ / 2, independent of β and of the frame. In the frame normalisation this is the same as giving unmapped cells and Ω the log-LR
lu_t = β μ₁ / 2 − A_t instead of 0. Two properties follow:
- a frame without a match pulls the map mass towards the unmapped cells (map mean LR ≈ exp(β² / 2 − β μ₁ / 2) < 1);
- the copy of (b) loses evidence iff its mean z is below μ₁ / 2.

μ₁ is estimated without labels as the median over the run of max_i z_ti, since most frames are on the map (`owf.py --lu half`).

*Proof.* (a) Relative LR of image i to an unmapped cell is exp(β z_ti − A_t). For Gaussian background, mean_j exp(β z_j) → E exp(β Z) =
exp(β² / 2). (b) The predict steps of the two tracks are identical shifts, so only the update terms differ. Their log ratio per frame is
w_t (β z_t,a_t − A_t) − w_t · 0. (c) Algebra. ∎

*Predictions, written before the development wave.*
- CMU seed 60, CosPlace: μ̂₁ / 2 = 3.02 and copy median z = 3.27. The copy's per-frame evidence drops from about e^2.8 to about e^0.25 but stays
  positive, so (c) slows the copy without reversing it there.
- Cost: on-map frames whose true-match z is below μ₁ / 2 now push mass off the map, which lowers recall. The cost should be largest for weak
  descriptors (NetVLAD) and the hardest conditions (CMU, countryside).
- The open-world veto of Entry 21 turns a lower near-map mass mN into fewer HSI reports, so (c) and the veto act together.
