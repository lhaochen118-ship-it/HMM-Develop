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
