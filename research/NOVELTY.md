# NOVELTY matrix (T1.3) — status 2026-11-27. ✓ verified source seen this session · ○ classic, not re-verified · ⚠ unverified

| Module / claim | Closest prior art | What is the same | What would be new here | Verdict |
|---|---|---|---|---|
| HMM over map nodes with velocity constraints | Hansen & Browning, IROS 2014 (HMM sequence matching; velocity constraints fixed, Viterbi) ✓ [CMU RI page]; Doan et al. ICCV'19 / HM⁴ ✓; MPF Hausler et al. RA-L'19 (HMM over recent images) ✓ | HMM state = place, banded transitions | nothing by itself — **baseline**, not a contribution | prior art |
| M1 calibrated LLR emission with exact null (l(∅)=0), HT-weighted logistic fit | Molloy et al. training-free likelihood for VPR + Bayesian fusion ✓ (search result, details to read); SUE (Zaffar CVPR'24) ✓; FAB-MAP null/new place ○ | likelihood-style emission, off-map handling | exact LLR null within a mass-conserving HMM + case-control-correct calibration — **incremental** | weak novelty; value = correctness |
| M2 information-aware β_t from AR(1) emission, ρ_t label-free from descriptor change | generalised Bayes / coarsening (Bissiri'16, Miller & Dunson'19) ○; keyframing ○; Hussaini et al. receptiveness prediction (2503.06840) ✓; Malone dynamic sequence length ✓(v2.0) | tempering / deciding how much sequence evidence to trust | per-frame, label-free weight derived from an AR(1) conditional-emission Fisher-information argument | **possible novelty — but naive IA hurt under time-warp (E08); only claimable jointly with ME (below) if it wins** |
| ME: appearance-change emission for the latent velocity state | RatSLAM scanline-intensity visual odometry (speed from image-difference magnitude, Milford & Wyeth T-RO'08) ○; DPVO/ORB-SLAM mono VO ○ | image change as a speed cue | calibrated probabilistic *emission* of global-descriptor change observed by the HMM velocity state, coupled with evidence redundancy (same signal used for M2 and M3) | **candidate main contribution — requires E18 evidence** |
| Fixed-lag smoothing for VPR | standard HMM inference ○; SeqSLAM is non-causal in its original form ○ | — | none (reported as a capability/latency trade-off) | prior art |

Search queries run (WebSearch, 27/11/2026): "sequence-based visual place recognition HMM latent velocity image difference speed
estimate stop frames"; "visual place recognition temporal filtering correlated observations overconfidence tempering likelihood sequence".
No direct match for M2/ME was found in these two searches — this is **absence of evidence**, not proof of novelty.
Next: targeted search on RatSLAM VO details, "speed-adaptive SeqSLAM", "HMM place recognition odometry-free stop detection".
