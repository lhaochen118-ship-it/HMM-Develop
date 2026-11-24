# Pilot P0 — Temporal dependence of evidence in a place-HMM (SYNTHETIC ONLY)

**Evidence level: P (pilot/synthetic).** This is NOT evidence about real data. It motivates H5/H6 in
`docs/MASTER_RESEARCH_PLAN.md` and gives the agent a ready-made test harness. The decisive test is
T3.4/T4.3 on real sequences (Nordland native-rate stride sweep, 4Seasons, RobotCar).

Script: `p0_dependence_tempering_synthetic.py` (numpy only, CPU, ~15 s per seed measured; deterministic — rerun of seed 0 is bit-identical).
Runs: `R20261124-001_P0` (seed 0, `p0_results_seed0.json`), `R20261124-002_P0` (seed 1, `p0_results_seed1.json`).

## Setup
M=400 places on a 1-D route, true velocity 1, T=60 frames/sequence, 25 calibration + 60 test sequences per ρ.
Similarity field S[t,j] = μ·1[j=p_t] + σ·N[t,j] with AR(1) noise **along the v=1 diagonals**
(the direction the HMM integrates). Emission = β·S/τ, τ from single-frame NLL (= the repo's temperature scaling).
Motion: banded Gaussian (v=1, std=1) + leak 1e-3. Correct = within ±1 place. Metrics after a 10-frame burn-in.

## Results (both seeds agree qualitatively)

| ρ | naive acc | naive NLL | naive conf>0.9 & wrong | β asymptotic (1−ρ)/(1+ρ) | β NLL-fit | β = 1/VIF(ρ̂, L_eff) | tempered acc | tempered conf>0.9 & wrong |
|---|---|---|---|---|---|---|---|---|
| 0.00 | 0.91 / 0.92 | 0.67 / 0.68 | 0.2% / 0.1% | 1.00 | 0.85 / 0.95 | 0.99 / 1.00 | ≈ naive | ≈ naive |
| 0.30 | 0.81 / 0.80 | 1.05 / 1.10 | 0.4% / 0.2% | 0.54 | 0.70 / 0.80 | 0.69 / 0.78 | 0.86 / 0.83 | 0% / 0.1% |
| 0.50 | 0.65 / 0.63 | 2.04 / 2.15 | 1.4% / 1.3% | 0.33 | 0.55 / 0.55 | 0.55 / 0.55 | 0.73 / 0.75 | 0% / 0% |
| 0.70 | 0.38 / 0.39 | 4.70 / 4.38 | 6.4% / 2.8% | 0.18 | 0.40 / 0.45 | 0.375 / 0.45 | 0.51 / 0.48 | 0% / 0% |
| 0.85 | 0.18 / 0.21 | 8.37 / 7.96 | 18.2% / 18.8% | 0.08 | 0.20 / 0.25 | 0.19 / 0.23 | 0.18 / 0.29 | 0% / 0% |

(seed0 / seed1; "tempered" = the 1/VIF(ρ̂, L_eff) variant, L_eff picked on the calibration sequences.)

## What the pilot shows (synthetic)
1. **Label-free ρ̂ works:** masking each row's top matches and correlating R[t,j] with R[t−1,j−1] recovers
   ρ within ±0.02 without any GT.
2. **Correlated errors hurt a naive HMM badly:** accuracy 0.91→0.18–0.21, NLL ×12, confident-wrong ×100
   as ρ goes 0→0.85. Wrong diagonals that look consistent over time are integrated as independent evidence.
3. **The textbook correction is wrong for a filter:** β=(1−ρ)/(1+ρ) (infinite-horizon effective sample
   size) over-tempers and makes the filter under-confident. A **finite-window** variance-inflation factor
   VIF(ρ,L)=1+2Σ_{k<L}(1−k/L)ρ^k with a single "effective memory" L_eff (2–8, growing with ρ) matches the
   NLL-optimal β almost exactly on both seeds. → H6 must be stated with L_eff, not asymptotically.
4. **Tempering removes confident-wrong failures and helps accuracy at moderate ρ** (0.65→0.73–0.75 at
   ρ=0.5), but cannot recover information that dependence destroys (ρ=0.85).
5. **Naive diagonal whitening (AR-HMM approximation along the nominal velocity only) is worse** than
   tempering (it removes signal and is misaligned with the motion-kernel spread). A proper AR-HMM needs
   pair states (p_{t−1},p_t); do not ship the cheap approximation.
6. **ECE alone is misleading:** at ρ=0.5 the naive filter has the *best* ECE (0.03–0.04) while its NLL and
   accuracy are clearly worse — an under-confidence source (motion kernel wider than truth) and an
   over-confidence source (correlated evidence) cancel. Always report NLL/Brier + confident-wrong rate +
   controlled interventions, never ECE alone.

## Limits
Gaussian, homogeneous, diagonal-only correlation; exact v=1 truth; no aliasing structure, no outages,
no condition change. Real similarity fields have heavy tails, place-dependent aliasing and correlation
along both the diagonal and the same-reference axis. These are exactly what Phase 4 measures.

---

# Pilot P0b — Is L_eff a property of the filter? (SYNTHETIC ONLY)

Script: `p0b_leff_vs_motion_synthetic.py` (reuses P0's generator; ~6 s/seed). Runs: `R20261124-003_P0b` (seed 0),
`R20261124-004_P0b` (seed 1). L grid {1,2,3,4,6,8,12,20,40}; L_eff = NLL-argmin on calibration sequences.

**Prediction:** wider motion kernel (more diffusion) and larger leak ⇒ faster forgetting ⇒ smaller L_eff ⇒ β closer to 1.

| ρ | motion std | leak | L_eff (s0 / s1) | β (s0 / s1) | NLL β=1 → tempered (s0) |
|---|---|---|---|---|---|
| 0.5 | 0.5 | 1e-3 | 6 / 8 | 0.44 / 0.41 | 1.52 → 0.69 |
| 0.5 | 1.0 | 1e-3 | 4 / 3 | 0.50 / 0.55 | 2.35 → 1.66 |
| 0.5 | 2.0 | 1e-3 | 2 / 2 | 0.67 / 0.67 | 2.94 → 2.40 |
| 0.5 | 1.0 | 3e-2 | 4 / 4 | 0.50 / 0.49 | 2.77 → 1.87 |
| 0.7 | 0.5 | 1e-3 | 8 / 6 | 0.27 / 0.30 | 4.23 → 1.54 |
| 0.7 | 1.0 | 1e-3 | 3 / 4 | 0.45 / 0.375 | 4.28 → 2.47 |
| 0.7 | 2.0 | 1e-3 | 2 / 3 | 0.59 / 0.45 | 4.24 → 3.21 |
| 0.7 | 1.0 | 3e-2 | 4 / 4 | 0.375 / 0.375 | 4.55 → 2.70 |

**Verdict (synthetic):**
- **Motion-diffusion prediction supported** on both seeds and both ρ: L_eff decreases monotonically with motion std
  (0.5 → 6–8; 1 → 3–4; 2 → 2–3). L_eff behaves like the filter's memory, not a free fudge factor.
- **Leak prediction NOT supported:** leak 3e-2 vs 1e-3 leaves L_eff at 3–4 (one case moves the wrong way). Leak mainly
  changes the prior floor, not the evidence-accumulation window, in this regime.
- **Interaction (new, → H18):** the sharper (more accurate) the motion prior, the larger the damage from correlated
  evidence and the larger the tempering gain (NLL 1.52→0.69 at std 0.5 vs 2.94→2.40 at std 2). Prediction for real data:
  improving the transition model (M3) *increases* the need for dependence correction (M2) — test as an M2×M3 interaction
  in the ablation (T6.3).
