# Baselines 2026 reproduced from the papers (no code read) — specs and our choices (Entry 26)

Paper text read on 2026-10-31 (arXiv HTML). Items the papers leave open are marked **choice**; every choice is the same
for every dataset.

## TAO'26 — Lu & Tanaka, arXiv 2607.04745 v1 "Trajectory-Anchor Optimization for Overconfident Thermal VPR" (v2 = Route-MHT)

- Per frame t: K = 100 retrieval hypotheses j (top-100 of the global descriptor). No hypothesis tree, no pruning, no
  state across frames: every hypothesis is re-solved every frame (batched 2-D Procrustes / SVD).
- Window N = 20 frames of odometry positions p_i. Anchors q_j(i): traced BACKWARD along the map route from hypothesis j by
  the odometry path length (v2 wording; v1 leaves it open). **Choice:** both traversal directions, the better is kept.
- Cost (v1 Eq. 1): sum_i w_i rho_delta(||q_j(i) - (R p_i + t)||) + lambda sum ||dq - R dp||^2 + gamma sum w_i (1 - s_{i, c_j(i)}).
  v2 constants: Huber delta = 8 m, 75 %-trimmed residual, appearance weight 2, anchor tolerance 4 m along the route.
  **Choices:** w_i = 1; lambda = 0 (the increment term duplicates the position residual after the rigid fit); the Huber
  term divided by delta^2 so that both terms are dimensionless; s_{i, c} = the largest similarity of frame i's top-100
  entries within 4 m of the anchor along the same route chunk, else frame i's 100th similarity.
- Winner j* = argmin_j C(j); reported place = map position of j*. Map-out: reject if C(j*) > tau_OOD, tau_OOD "frozen
  from the 3-sigma residual bounds of the calibration split". **Choice (labels, as Xu'21 / Claxton'24 here):** tau_OOD =
  mean + 3 std of C(j*) over the correctly localised on-map frames of the two easiest query conditions (`bsel`). The
  operating curve sweeps tau_OOD (label-free ranking).
- Reported: map-out FPR 0.583 -> 0.259 / 0.238 -> 0.049 / 0.326 -> 0.119 (three scenarios, thermal STheReO-KAIST); v2
  SVD baseline FPR 0.116, Route-MHT 0.061.

## TRAIL'26 — Kloepfer & Wenzel, arXiv 2609.07373 "Trajectory-Aware VPR against Unordered Databases"

- Linear-chain CRF over the top-K (K = 10) of frozen MegaLoc; no odometry; reference positions used for the transition
  cutoff Delta = 75 m and the location kernel kappa.
- Emission phi_e = MLP(d_g(r) * d_g(q)) (8448 -> 64 -> 1, LeakyReLU, dropout 0.1).
- Transition: main model CNN on DINOv2 local-feature correlations; ablation "phi_tr uses d_g" (Eq. 51, 2 x 512 MLP)
  performs the same (Nordland R@5 83.2 vs 81.3). **Choice:** the d_g variant, input D * (d_g(r_i) * d_g(r_j)) *
  (d_g(q_t) * d_g(q_{t-1})), 8448 -> 512 -> 512 -> 1; phi_tr = -inf beyond Delta.
- Dustbin: phi_tr(i, dust) = phi_e(r_i, q_t) (stated). **Choice:** learnable dustbin emission bias, transitions into the
  dustbin with log-potential 0.
- Forward filter in log space, posterior over candidates, location posterior P(s_i) = sum_j kappa(|x_i - x_j|) P(c_j),
  kappa(x) = exp(-(x / 20 m)^4) 1(x <= 25 m) (Eq. 50, beta fixed at its initial value 4). Prediction = argmax.
- Training stages A (emission, softmax over top-K, lr 1e-3, wd 1e-3), B (transition, lr 1e-3, wd 1e-4), C (end to end,
  lr 1e-4, wd 1e-3, sequences of 10). Paper trains on MSLS. **Choice:** leave-one-dataset-out (train on the other
  datasets' queries, test on the held-out one), so training and test data never share a dataset.
- TRAIL has no rejection. **Choice:** score = P(s_{i*}); default point = label-calibrated threshold on the two easiest
  conditions (FL <= alpha there), like the other label baselines; curves sweep the threshold.
- Reported R@1/5/10 (MegaLoc): MSLS 56.5/65.2/66.7, Nordland 75.3/81.3/78.1, 4Seasons 71.0/78.2/79.0.

## VPR auditing'26 — Waheed, Milford, Ramchurn, Ehsan, arXiv 2607.12818 "Breaking Deja Vu"

- VLM verifies the top-1 pair (query, retrieved); accept iff JSON is_same_place is true; unparsable = accept. Prompt not
  printed: conservative default (different places unless strong evidence), compare permanent structure and spatial
  configuration, search for inconsistencies, ignore vehicles / pedestrians / lighting / weather.
- Open models in the paper: Qwen2.5-VL-7B / 32B-Instruct (avg composite S 0.60 / 0.67; closed GPT-4.1 0.76, Gemini 0.78).
- Metrics: P = TP/(TP+FP), coverage C = (TP+FP)/N, FAR = FP/(FP+TN), S = harmonic mean of P, C, 1-FAR; tolerance 25 m.
- **Ours (`analysis/vlm_audit.py`):** Qwen2.5-VL-7B-Instruct (Kaggle model qwen-lm/qwen2.5-vl, offline, bf16, one replica
  per L4), images resized to <= 448 px, the prompt in the script; the answer is pre-filled with '{"is_same_place": ' and
  one forward pass gives log p(true) - log p(false) (same token as greedy decoding; the log-odds also give curves). Every
  5th query frame (cost).
