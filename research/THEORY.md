# THEORY — derivations used by IA-HMM (status: [H]/[P] unless a run ID says otherwise)

## T1. Information-matched power likelihood for AR(1)-dependent evidence
Setting. Fix a candidate node j and the true trajectory staying matched to j for a run of frames (e.g. a stop,
or a slowly moving camera at high frame rate). Model the per-frame LLR as l_t = δ·m + e_t, m∈{0,1}
(match / non-match), with stationary Gaussian AR(1) noise e_t = ρ e_{t−1} + σ√(1−ρ²) ξ_t.

Exact conditional evidence. p(l_t | l_{t−1}, m) is Gaussian with mean ρ l_{t−1} + δ m (1−ρ) and variance σ²(1−ρ²).
The Fisher information about m carried by frame t given the past is
  J_t = δ²(1−ρ)² / (σ²(1−ρ²)) = (δ²/σ²) · (1−ρ)/(1+ρ),
whereas a naive HMM treats each frame as independent and adds information δ²/σ² per frame.
Hence a naive filter's log-odds grow (1+ρ)/(1−ρ) times too fast (ρ=0.9 → 19×) ⇒ over-confidence/lock-in.

Power-likelihood correction. Replacing l_t by β_t l_t with β_t = (1−ρ_t)/(1+ρ_t) matches the *expected*
information increment of the exact conditional update (both scale linearly in the same sufficient statistic
when ρ is small; for ρ→1 both tend to 0). This is a generalised-Bayes (tempered) emission — the model remains an
HMM over the same state space; only the emission exponent varies with t. It is an approximation:
(a) it ignores the ρ l_{t−1} mean shift term (exact AR-HMM would need pair states (z_{t−1},z_t)),
(b) assumes Gaussian LLR and a known ρ_t. These are stated limitations, not claims.

Label-free ρ_t. Descriptor change d_t = 1 − q_t·q_{t−1}. If the appearance process is a random walk on the unit
sphere that decorrelates on a scale κ (squared-chord distance between two "independent" views of nearby places),
then a first-order estimate is ρ_t ≈ 1 − min(1, d_t/κ). Then β_t = β₀ u_t/(2−u_t), u_t = min(1, d_t/κ).
β₀ absorbs a global miscalibration of the LLR scale and the residual dependence not explained by d_t
(both fit on calibration). Testable predictions:
 P1 exact duplicates (stops) ⇒ β_t≈0 ⇒ no confidence growth while stationary;
 P2 at low frame rate (d_t≫κ) IA-HMM ≡ fixed-β HMM;
 P3 the benefit of IA over the best fixed β increases with frame rate and with the fraction of stops.

## T2. Null state with LLR emission
If l_t(j) = log p(o_t|z=j)/p(o_t|∅) with p(o_t|∅) = Π_i h0(s_ti) (all non-match) and p(o_t|z=j) = h1(s_tj)
Π_{i≠j} h0(s_ti) (independence of non-match scores — an assumption), then l_t(j) = log h1(s_tj)/h0(s_tj)
and l_t(∅)=0. The logistic model estimates log h1/h0 up to the prior log-odds (Bayes' rule), corrected with the
population match rate π (Horvitz–Thompson weighted sampling). Violations: dependent non-match scores (neighbouring
reference frames are correlated) — handled empirically by β (tempering) and checked by calibration metrics.

## T3. Information vs model mismatch (inherited from Master Plan v2.0 §4.2)
R_seq − R_img = −I(Z_t;H_t|O_t) + ε_seq − ε_img (expected log-loss). Sequence filtering can only lose to the
single image through model error ε_seq; IA-HMM targets ε_seq from dependence, M3 targets ε_seq from motion.
