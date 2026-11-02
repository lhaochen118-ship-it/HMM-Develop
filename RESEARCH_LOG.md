# Research Log

*Branch `hmm-navigation` (2026-10-29): hướng mới là HMM sequence-based visual localization. Các entry dưới đây thuộc
hướng cũ (CCBF/HMM filter → SelfCal), giữ lại làm lịch sử và bài học. Entry mới bắt đầu từ 18, đặt ở trên cùng. Kết quả
và script SelfCal được nhắc tới nằm ở branch `claude/selfcal-aa` / `claude/selfcal-seq`.*

Newest entry at the top. Each entry: hypothesis, experiment, honest verdict. Compute runs on Kaggle (see
`handoff/02_ENGINEERING_OPS_NOTES.md`).

## Entry 36 (branch `hmm-navigation-5`) — forward counterfactual surgery: the null of the system's own ghost track; vectorised statistics; St Lucia (2026-11-02)

**Context.** Open items after Entry 35 (user, 2026-11-02): (1) "forward surgery" for the segments at the edge of an excursion, where
CST lets false fixes through and SH must stay; (2) confirm the belief window N = 40 on seeds 1-9; (3) vectorise the counterfactual
statistics (the pre-registered < 10 ms / frame of Entry 32 was missed: 10.3-17.5 ms); (4) St Lucia and a direct comparison with
SafeVPR'26. No Kaggle token was available in this session: everything ran on the session's 4 CPU cores from the public caches.

**Step 3 first: vectorised exact counterfactual statistics (`analysis/cms_vec.py`, default of `cms_exact.stats`).** Same arithmetic as
`cms_exact.cms_stats_exact`, batched over frames (window groups by length, batched Procrustes, per-row searchsorted by offsets with an
exact correction, two-stage corridor test with an anchor cover). Checks: identical to the loop on 4S old town CosPlace s0 (all 8
outputs, max |diff| 0); against the PUBLISHED Kaggle cache (CMU CosPlace s0, top-300 recomputed locally): cost, cost_cf, z, z_cf
100 %, j / j_cf 99.85 / 99.80 % (fp16 ties of the GPU lists). Bug found on the way: the CPU path of `cms_exact.topk_long` used the
biased row std, the GPU path (torch) the unbiased one -> z differed by sqrt(N/(N-1)); CPU path fixed to ddof = 1. Speed on one core:
3.9 ms / frame (KL = 300, K = 100, N = 20) vs 9.4 ms for the loop on the same core (Kaggle: 10.3-17.5 ms) -> the pre-registered
< 10 ms / frame now holds.

**Step 1 (diagnosis, labels only to evaluate): Proposition 14's assumption (S3-T) fails, at every depth, not only at the edge.**
`analysis/cst_audit.py` measures the quantity Prop. 14 bounds, P(exists t in G0: r_t <= eps), on the real off-map segments
(seeds 0-1, 84 runs). Pass rate of the current CST (target <= a/pi ~ 0.05): Nordland 0.28, NCLT 0.19, Boreas 0.17, old town 0.14,
office 0.10, CMU 0.07, countryside 0.06; first segment of an excursion 0.09-0.44; CST threshold 1.2-2.3 x the oracle one (a-quantile
of the real segment minima; e.g. Boreas 18.0 vs 12.3 m, Nordland 3.5 vs 1.7 frames). Two causes found:
(i) *incoherent null track.* MP[j_cf] is the sequence of PER-FRAME counterfactual route winners, each from its own surgery and from
another estimator (the route test): consecutive winners are unrelated places (residual median 240-570 m). The ghost the place chain
really follows after an exit is coherent (moves with the odometry, sticks to the hole edge, locks onto a parallel street or a far
look-alike; traced on CMU: 1.1 km error with residual 6-15 m). Diagnosis of the navigation cost of CST (Entry 35): on Boreas NetVLAD
s7 CST lets 345 false fixes through (338 removed by SH), 269 of them >= 80 frames deep, median error 419 m; on old town NetVLAD s8
three frames with 1.5 km error (+128 m mean navigation error). Only CMU s0 matches the "edge" picture (61 of 83 within 10 frames,
error ~44 m).
(ii) *truncated shape windows.* CMU sequences are short (130 per run): 43 % of the frames have a shape window cut by the start of
their sequence; a robot that starts inside a hole initialises its chain on a look-alike and every track has a small residual on a
short window (off-map pass rate 0.19-0.32 on these segments). Other datasets: 0.3-2 % of frames.
The CST rules were valid in Entry 34 only because the presence onset also had to fire; Corollary 15's "the guarantee comes from CST
alone" does not hold on the data.
Recall loss on Oxford (Entry 35, H35d) is a different matter: there CST alone has recall 0.697, SH AND CST 0.691, SH alone 0.719 ->
CST is STRICTER than SH on Oxford (not a leak at the boundary).

**Step 2 (mechanism): forward counterfactual surgery (`analysis/cms_fwd.py`, `paper/cms_theory.md` section 4f).** A virtual EXIT at
frame tau (every 1 excl of path): remove the map region visited AFTER tau (corridor rho = off_d around the believed positions of the
next off_d + 20 excl of path, Voronoi cut against the believed positions before tau, so the map before the exit point stays, as at a
real hole edge), then run the system's OWN place chain FORWARD from its belief at tau on the altered map with the real frames. The
place chain is replicated exactly (hmm_diag.DiagFilter, emission (s - s_max)/(tau_e sd_far) recomputed on the altered map; MAP
agreement with the stored chain 99.95-100 %). Its MAP after tau is the ghost the system would follow if the map ended at tau. A
virtual START (chain restarted uniform at tau, corridor around the next 3 excl, window cut at tau) gives the null of truncated
windows. CST-F: per calibration group, eps_X = min over excursion-position bins (>= 2/a segments each) of the floor(a (n_b+1))-th
smallest virtual-segment minimum of the spliced-track residual; eps_S = the same over virtual starts; a frame passes iff r_t <= eps_X
(full window) or r_t <= min(eps_S, eps_X) (truncated); windows < 1 excl are not certified. Proposition 16 / Corollary 17 (section 4f):
under (S3-F), every off-map segment, edge included, passes with probability <= a(n_b+1)/(pi_b n_b+1), whatever the presence chain.
*Design checks (labels only to evaluate; exits only, before the starts were added).* Horizon 6 excl, pooled threshold: CMU s0 pass
0.164 -> 0.122, Nordland s0 0.267 -> 0.107 (per-position thresholds decrease with depth: the ghost locks in -> horizon too short).
Horizon 20 excl + min over position bins: full-window pass rate CMU s0 0.052 (deep 0.057), Nordland s0 0.044 (deep 0.049), i.e. at
the nominal a = 0.05; eps_X 10.0 m (CMU, SH tolerance 12.5, CST 15.5) and 1.4 frames (Nordland, SH 2.5, CST 3.1).

*Design runs with the final construction (exits + starts, horizon 20 excl, exits every 1 excl, thresholds = min over position bins
of >= 2/a segments, cond groups; labels only to evaluate), recall / segFAR / navigation error of the +G+NGRr rules:*
- CMU CosPlace s0: audit pass rate 0.037 (full windows 0.052, truncated 0.018; CST 0.164). CSTF 0.668 / 0.000 / 2.8 m vs SH 0.814 /
  0.014 / 4.4 m. The recall price sits at the sequence starts: on full windows CSTF keeps 86.4 % of the correct frames (SH 88.3 %); on
  truncated windows 48 % (SH 86 %), 37 % of them have a window < 1 excl, which CSTF does not certify.
- Nordland CosPlace s0: pass 0.043 (CST 0.267); CSTF 0.794 / 0.000 / 0.7 vs SH 0.826 / 0.000 / 0.7 (eps 1.4 frames vs SH 2.5).
- 4S old town NetVLAD s0 (the worst navigation case of CST): pass 0.046 (CST 0.211); CSTF 0.511 / 0.006 / 36.9 m, SH 0.514 / 0.003 /
  37.5 m, CST 0.541 / 0.012 / **82.0 m**. CSTF removes the navigation cost of CST at no recall cost here.
- Threshold variants (fixed 3 position bins; one group per run): recall within 0.01 of the min-over-bins version, audit pass rate
  0.062-0.067 (vs 0.044-0.052) -> min over bins kept.

**Pre-registration of the Entry 36 evaluation (written before any evaluation run; labels only to evaluate).** Data: seeds 0-2 of the 7
datasets x 6 descriptors (114 runs, the Entry 35 evaluation set; the design runs above are part of it and are flagged), Oxford
RobotCar (seeds 0-4, 30 runs; the Entry 35 Oxford numbers are on 60 runs, the same rules are re-evaluated on these 30) and St Lucia
(new, see below). Rules at alpha = 0.05, groups cond + loco, `e36_run.py` (`oc_curves.py --cst --fwd --fams @E36`).
Main rule: **CMS-CPC/H+CSTF+G+NGRr** (every report must pass CST-F; validity from Proposition 16 alone). Practical variant
CMS-CPC/H+SH+CSTF+G+NGRr; causal CMS-CPC/H+CSTF+G[both]+NGRr; references SH, SH AND CST, CST.
- H36a (audit of S3-F): pass rate of real off-map segments under CST-F (all positions, edge included, full and truncated windows)
  <= 0.07 on >= 6/7 datasets, and lower than CST's on 7/7.
- H36b (validity without any hand-set tolerance): mean segFAR of the main rule <= 0.05 on 7/7, Oxford and St Lucia.
- H36c (navigation): mean navigation error of the main rule within 1 m of the SH rule (CMS-CPC/H+SH+G+NGRr) or lower on >= 6/7
  (the CST penalty, Boreas +9.0 m and old town +13.6 m in Entry 35, disappears).
- H36d (price, reported whatever the outcome): recall of the main rule within 0.03 of the SH rule on >= 4/7 datasets; expected loss
  on CMU (short sequences, truncated windows).
- H36e (Oxford): main rule valid; recall compared with SH (0.719 on 60 runs) and SH AND CST (0.691) on the same 30 runs.

**Amendment (design runs only, before any evaluation result was read; the queue was stopped after 3 Nordland runs whose results were
not opened): CST-J, joint forward calibration (Proposition 18, `cms_fwd.joint_segments`).** Motivation: on the Oxford design run
(cosplace s0) CST-F is valid on its own (audit pass rate 0.050 vs CST 0.180, oracle eps 4.9 m) but its recall is 0.587 vs 0.763 (SH):
on Oxford the residuals of correct tracks (median 2.5 m, p80 7.5 m) and of real ghosts overlap, so a shape-only guarantee must be
strict. CST-J simulates the WHOLE decision along every virtual run (presence chain continued from its real state at the exit with
the counterfactual log-LR, agreement gate on the ghost, shape residual) and calibrates the tolerance so that the simulated report
rate of virtual off-map segments is <= a at every position bin (eps may be infinite). Design runs (+G+NGRr; recall / segFAR / error):
Oxford 0.781 / 0.034 / 18.6 (SH 0.763 / 0.004 / 18.6; without the gate CST-J breaks alpha: 0.103), Nordland 0.851 / 0.003 / 0.7
(SH 0.826), CMU 0.680 / 0.025 / 3.3 (SH 0.815: sequence starts), old town NetVLAD 0.542 / 0.009 / **86.2 m** (SH 37.5 m): CST-J spends
the alpha budget and the navigation cost of the spent false fixes returns. CST-J (CMS-CPC/H+CSTJ+G+NGRr) and its [both] version are
added as PRE-SPECIFIED SECONDARY rules; the main rule stays CST-F. Extra hypothesis H36g: CST-J has mean segFAR <= 0.05 on 7/7 and
recall >= SH on >= 4/7 and on Oxford. The forward nulls are recomputed for every run (ghost places are now stored).

**Exploratory variant found DURING the evaluation (after the CMU results were read) and its held-out confirmation, pre-registered
before running it.** On CMU (18 runs) every fully calibrated rule loses ~0.15 recall (CST-F 0.603, CST-J 0.644, SH AND CST-J 0.615 vs
SH 0.764): frames whose shape window is < 1 excl (the first 25 m of each of the 130 short sequences, ~16 % of the correct frames)
are never certified. *CST-J\** lets them pass and accounts for it in the same joint simulation (virtual starts in which the chain may
report on a short window count as false reports, residual -inf); if the simulated rate cannot be met, they fall back to "not
certified". CMU CosPlace s0 (design): SH AND CST-J\* 0.8144 / 0.0135 / 4.37 m vs SH 0.8145 / 0.0135 / 4.38 m; CST-J\* alone 0.816 /
0.031. Confirmation set (held out, never looked at): seeds 3-5 of Nordland, CMU, 4S office / old town / countryside x CosPlace,
NetVLAD, MegaLoc (45 runs) and Oxford seeds 5-9 x the same 3 descriptors (15 runs). H36h: SH AND CST-J\* (+G+NGRr) has recall within
0.01 of SH on >= 5/6 (Oxford included), navigation error within 1 m on >= 5/6 and mean segFAR <= 0.05 on 6/6; CST-J\* alone has mean
segFAR <= 0.05 on 6/6. The 114 evaluation runs are re-scored with CST-J\* too (labelled exploratory there).

**Deviation (compute; decided before any Boreas or NCLT result existed).** On the local CPU a NCLT run takes ~23 min and a Boreas run
~40 min (76 k frames, horizon 20 excl). Boreas is evaluated on 8 of its 18 planned runs (seed 0 x 6 descriptors, seeds 1-2 x CosPlace; a
Boreas run takes ~47 min with the other queues running); every other dataset keeps its full pre-registered set. The N = 40
confirmation runs on CosPlace only, Boreas on seeds 1-3 (48 runs instead of 108).

**Pre-registration of the N = 40 confirmation (item 2; before any of its runs).** Entry 32 (seed 0, 42 runs) found the belief window
N = 40 better than N = 20 (recall +0.015 Boreas, +0.015 CMU, +0.027 countryside, validity unchanged). Confirmation on the held-out
seeds 1-9 of the 6 holed datasets (NCLT has one run per descriptor, seed 0 only). Compute is local CPU only, so the descriptors are
restricted to CosPlace and MegaLoc (108 runs; NetVLAD added if time allows, reported separately). Exact top-300 recomputed from the
dumps, counterfactual statistics with N = 40 (`cms_vec`, checked against the loop), N = 20 = the published exact cache; same rules
(@E32S: CMS-CPC/H+SH+G+NGRr, CMS-CPCW/H+SH+NGRr), group cond, alpha 0.05. H36f: with N = 40 the main rule keeps mean segFAR <= 0.05
on 6/6 and its recall is >= the N = 20 recall on >= 5/6. N = 40 becomes the default only if H36f holds.

**Results (labels only to evaluate; raw `analysis/results/e36/` (main, oxford, stlucia, conf, conf_oxford, n40, design .tgz;
audit_s3f.json, safevpr26_stlucia.json), tables `paper/e36_tables.md`, report `paper/BAO_CAO_E36.pdf`).** Main set = 104 runs (seeds
0-2; Boreas 8 runs, see the deviation), Oxford 30 runs (seeds 0-4), St Lucia 5 runs (CosPlace), confirmation 45 + 15 runs.
1. *H36a supported (7/7, Oxford and St Lucia too).* Pass rate of real off-map segments under CST-F (edge included): Boreas 0.025, NCLT
   0.025, CMU 0.019, Nordland 0.036, office 0.004, old town 0.019, countryside 0.015, Oxford 0.033, St Lucia 0.047; CST: 0.182, 0.187,
   0.067, 0.302, 0.099, 0.147, 0.051, 0.321, 0.219. The guarantee of the shape test now holds on the data, including the edge.
2. *H36b supported.* CST-F (CMS-CPC/H+CSTF+G+NGRr) mean segFAR <= 0.004 on 7/7 (no run above alpha, worst 0.013), Oxford 0.001, St
   Lucia 0.000. Causal [both] versions likewise.
3. *H36c supported (6/7).* Navigation error vs the SH rule: Boreas -0.9 m, NCLT -1.0, CMU -0.9, Nordland +0.1, office +0.1, old town
   +1.0, countryside +5.3; vs CST (Entry 34): Boreas -12.5 m, old town -13.0 m. The navigation cost of CST is removed.
4. *H36d NOT supported (3/7).* Recall vs SH: Boreas -0.011, NCLT -0.032, CMU -0.161, Nordland -0.027, office -0.024, old town -0.050,
   countryside -0.036; Oxford 0.550 vs 0.729 (H36e: valid, recall criterion NOT met by CST-F); St Lucia 0.622 vs 0.820. A guarantee
   from the shape test alone is strict where correct and ghost tracks overlap (Oxford, 10 m frames) and at sequence starts (CMU).
5. *H36g (secondary, CST-J) supported on the evaluation set.* Mean segFAR 0.005-0.030 on 7/7, Oxford 0.041 (30 % of runs > alpha);
   recall >= SH on 6/7 (CMU 0.644 vs 0.764) and Oxford (0.755 vs 0.729). Navigation cost returns where alpha is spent on harmful
   false fixes (Boreas 11.6 vs 4.7 m, old town 39.4 vs 27.5 m). SH AND CST-J: recall within 0.007 of SH on 6/7, CMU -0.149.
6. *Exploratory CST-J\* and its held-out confirmation H36h: partly supported.* Evaluation set: SH AND CST-J\* recall = SH within 0.003
   on 7/7 (Boreas 0.814 / 0.815, NCLT 0.612 / 0.612, CMU 0.764 / 0.764, Nordland 0.752, office 0.794 / 0.795, old town 0.686 / 0.687,
   countryside 0.511 / 0.513) and Oxford (0.729 = 0.729; SH AND CST 0.694 -> the Oxford criterion of Entry 35 is met), errors within
   0.3 m except countryside (+1.5 m). Held out (45 + 15 runs): SH AND CST-J\* recall within 0.01 of SH, error within 1 m and segFAR <=
   0.05 on 6/6; but CST-J\* ALONE breaks alpha on CMU (mean segFAR 0.068, worst 0.135; pre-registered CST-J 0.065): the joint
   simulation is anti-conservative there (its presence evidence is the full-surgery null, approximate at the edge and at sequence
   starts), so the validity of SH AND CST-J\* on CMU rests on SH, not on Proposition 18.
7. *H36f (N = 40) supported on CosPlace (48 runs, seeds 1-9).* Mean segFAR <= 0.011 on 6/6; recall vs N = 20: Boreas +0.002, CMU
   -0.003, Nordland +0.012, office +0.004, old town +0.004, countryside +0.069 (>= on 5/6). Per the pre-registration N = 40 becomes the
   recommended belief window; confirmation on the other descriptors is still open.
8. *St Lucia (new dataset; CosPlace; map 100909_0845, 5 query traversals; 10 m frames).* Protocol with 30 % holes: SH 0.820 / 0.000,
   CPCW 0.857 / 0.006, CST-F 0.622 / 0.000; the map-null rule CPC-SC-T(1/2)+SH is better here (0.920 / 0.021): on a single 17 km route
   the map self-replay null works and CMS is conservative. *Direct comparison with SafeVPR'26* (reproduced from the paper; verifier
   DINOv2 ViT-B/14, not the paper's ViT-L/14; Mondrian LTT with labels on the other traversals; SafeVPR's own metric, accepted-set FDR /
   TPR): without holes every method is saturated (FDR <= 0.0001, recall 0.994-0.999); with 30 % holes (25 held-out conditions)
   SafeVPR'26 alpha 0.05: FDR 0.008, TPR 0.655, recall 0.462; alpha 0.10: 0.020 / 0.795 / 0.557; ours without any label: SH rule 0.002 /
   0.821 / 0.592, SH AND CST-J\* 0.002 / 0.818 / 0.590, CPCW 0.010 / 0.864 / 0.623; all 25/25 valid. Our recall is higher than
   SafeVPR'26 at both levels, with lower FDR, and no calibration traversal.
9. *Running time.* Counterfactual statistics 3.9 ms / frame (vectorised, one core); forward null 4-31 ms / frame (one core shared by
   ~5 jobs; horizon 20 excl; the cost grows with map size: Boreas / NCLT the highest); decision layer ~1-2 ms. Real time at 10 Hz holds.
**Verdict.** (i) The forward surgery delivers what the theory promised: a null of the system's own ghost track that makes the shape test
valid on its own at every position of an excursion, edge included (audit 9/9 dataset groups), with no hand-set tolerance and without
CST's navigation cost; its price is recall (-0.01 to -0.18). (ii) Calibrating the whole decision on forward simulations (CST-J) keeps
the recall of the hand-set rule and fixes Oxford, but its assumption is approximate and fails on held-out CMU, so it is not a
guarantee. (iii) Recommended: **CMS-CPC/H+CSTF+G+NGRr** when a certified per-segment bound is required (and N = 40); **SH AND CST-J\***
(= SH recall, Oxford criterion met, guarantee approximate) as the practical rule. Novelty: forward counterfactual simulation of the
system's own failure from virtual exits (Gate 14 to do). Open: forward surgery of the PRESENCE evidence (the CST-J approximation),
an exact null for sequence starts, N = 40 on all descriptors, Boreas on all seeds (GPU).

## Entry 35 (branch `hmm-navigation-5`) — SH AND CST: the guarantee from the surgery, the protection from the hand-set stop (2026-11-01)

**Step 5 analysis of Entry 34 (paired cluster bootstrap, 366 runs).** CST vs the hand-set SH: recall +0.003 to +0.022 with CI > 0
on 5/7 datasets, but navigation error is significantly HIGHER on Boreas (+9.0 m [7.1, 10.8]) and 4S old town (+13.6 m [10.1, 16.9]),
with segFAR +0.014 / +0.016. CST admits a few false fixes that SH rejects, and they damage the Kalman filter. They lie mostly at
excursion boundaries (Entry 34 diagnosis: 94 of 126 within 20 frames), where Proposition 14 does not apply. A lower level does
not remove the cost (a_sh = 0.5 alpha: still +7.1 m Boreas, +7.5 m old town).

**Hypothesis / mechanism.** Report only if BOTH SH and CST pass. Every report must pass CST, so Proposition 14 / Corollary 15
bound the segment false-fix rate whatever SH does. SH can only remove reports (Lemma 7), so the bound holds for ANY SH tolerance.
SH keeps its practical protection at the boundaries. Prediction: the fragility of Entry 32 disappears (SH x 2 can no longer break
validity), at almost no cost against SH alone.

**Pre-registration (before any run of it; seeds 0-2, 114 runs, local CPU, exact cache, `--cst --fams @E35`, group cond, alpha
0.05; default SH and `--sens shd=2`).** H35a: CMS-CPC/H+SH+CST+G+NGRr has mean segFAR <= 0.05 on 7/7 with the default SH AND with
SH x 2 (where SH alone broke alpha on CMU and 4S countryside, Entry 32). H35b: at the default SH, its recall is within 0.01 of
CMS-CPC/H+SH+G+NGRr and its navigation error within 1 m on >= 6/7.

**Results (228 runs; raw `analysis/results/e35/e35.tgz`, tables in `paper/e34_tables.md`).**
1. *H35a supported.* SH AND CST has mean segFAR <= 0.05 on 7/7 with the default SH (max 0.004) AND with SH x 2 (max 0.017;
   CPCW variant max 0.023). SH x 2 alone on the same runs: CMS-CPC 4S countryside 0.100; CMS-CPCW 4S office 0.066 and countryside
   0.108. The tolerance can no longer break validity.
2. *H35b supported (6/7 for recall, 7/7 for error).* At the default SH, recall vs SH alone: -0.001 (Boreas), -0.004 (NCLT), -0.002
   (CMU), 0.000 (Nordland), -0.003 (4S office), -0.001 (old town), -0.014 (countryside). Navigation error is within 1 m on 7/7
   (countryside +0.9 m, the others <= 0.1 m). SH x 2 AND CST behaves like CST alone (the loose SH removes nothing), with its
   navigation cost (Boreas 14.7 m).
**Verdict and recommended rule: CMS-CPC/H+SH+CST+G+NGRr.** Its validity rests on the counterfactual surgery alone (Theorems 6/6',
Proposition 14), for any SH tolerance. Its navigation performance equals the hand-set rule's, because SH keeps rejecting the
boundary false fixes that are outside Proposition 14. The fragility found in Entry 32 is removed at a cost of <= 0.014 recall. The
causal deployment variant is the same rule with [both] calibration. Open: confirm on all 10 seeds (366 runs) and on Oxford; forward
surgery for the boundary segments.

**Pre-registration of the confirmation (21:12, before running it).** H35c: on the held-out seeds 3-9 of the 6 holed datasets
(252 runs; seeds 0-2 were the E35 evaluation), the H35a and H35b criteria hold (validity 7/7 including NCLT seed 0 for default SH
and SH x 2; recall within 0.01 and error within 1 m of SH alone on >= 5/6 holed datasets). H35d: on Oxford RobotCar (60 runs,
statistics from the E33 jobs, top-100 recomputed from the local dump), SH AND CST is valid with recall within 0.01 of SH alone.

**H35c result (held-out seeds 3-9, 252 runs x 2 SH settings): supported.** Default SH: SH AND CST is valid on 6/6 holed datasets
(max mean segFAR 0.008). Recall vs SH alone: 0.000 (Boreas), -0.003 (CMU), 0.000 (Nordland), -0.004 (4S office), -0.001 (old
town), -0.014 (countryside): within 0.01 on 5/6. Error is within 1 m on 6/6 (countryside +0.7 m). SH x 2: SH alone breaks alpha
again (CMU 0.087, 4S office 0.052, countryside 0.100; CPCW CMU 0.096, office 0.079, countryside 0.125). SH x 2 AND CST is valid
on 6/6 (max 0.023; CPCW 0.029). The seed 0-2 result replicates on held-out seeds.

**H35d result (Oxford, 60 runs; local reproduction of the Kaggle run exact to 4 decimals): NOT supported.** SH AND CST is valid in
every run (mean segFAR 0.002, 0 % of runs > alpha; error 21.9 m vs 21.7 m), but its recall is 0.691 vs 0.719 for SH alone (-0.029;
CPCW -0.033). On Oxford the counterfactual track test is stricter than the hand-set stop. The guarantee still comes at a recall
cost there, so "no cost" is shown on the 7 main datasets only.

## Entry 34 (branch `hmm-navigation-5`) — counterfactual segment shape test: the surgery also calibrates the EXIT (2026-11-01)

**Step 1 (core limitation, diagnosed with labels on CMU / 4S countryside CosPlace s0-1).** Theorems 6 / 6' / 6'' bound the ONSET
of a report chain inside an excursion. They say nothing about PERSISTENCE: a chain that is ON when the robot leaves the map is
kept while log-odds > 0. The presence chain's log-odds are capped near log((1-p)/p) = 4.6 and off-map evidence is weak, so a
carried chain survives ~20 frames. Without the shape stop SH (CMS-CPC/H+G) the off-map false fixes are 491 / 174 / 374 / 28
frames per run (4S countryside s0 / s1, CMU s0 / s1; exact cache, re-run after the correction below). 65 / 29 / 18 / 61 % of them
are in streaks that started ON the map, and 73 / 72 / 70 / 39 % are at depth >= 20 frames into the excursion. SH removes almost
all of them (0 / 0 / 74 / 0). CST (exact cache) leaves 0 / 0 / 126 / 1; on CMU s0, 94 of the 126 are within 20 frames of the
excursion start, i.e. the boundary region outside Proposition 14. SH is therefore the only guard against persistence errors, and its
tolerance is the one hand-set constant that validity depends on (Entry 32: x 2 breaks validity).

**Step 2 (hypothesis and mechanism).** The map surgery gives a null for the TRACK as well as for the presence statistics. The
counterfactual route MP[j_cf] is false by construction (the true region is removed): it is the ghost track that a chain follows
after a real exit. *Counterfactual Shape Test (CST):* per calibration group, eps = lower conformal quantile at level a_sh of the
per-segment (H frames) MINIMUM shape residual of the counterfactual track. A frame passes iff the residual of its own MAP track is
<= eps. Proposition (to be written in `paper/cms_theory.md` section 4e): under S1-S3 applied to the track (real ghost segments
exchangeable with counterfactual ghost segments of the same group), a real off-map segment deep in an excursion passes the test
at least once with probability <= a_sh (n+1)/(pi n+1), whatever the chain state at entry. With onset at a_on, the segment false-fix
rate is <= (a_on + a_sh)/pi (union bound) and covers persistence too. CST2 = a/2 + a/2 (end-to-end <= a/pi). CST = a + a
(practical; theory only <= 2a/pi). No tolerance constant enters validity. Boundary segments (depth < N) stay outside the
statement, as in Theorem 6'.

**Design check (8 runs, CosPlace: CMU s0-1, countryside s0-1, old town, Nordland, Boreas, NCLT s0; labels only to evaluate).**
Recall / segFAR of the +G+NGRr rule: SH (hand-set) vs CST2. Countryside 0.673/0 vs 0.641/0, 0.583/0 vs 0.560/0; old town
0.704/0.003 vs 0.706/0.003; Boreas 0.877/0.018 vs 0.882/0.028; CMU 0.820/0.015 vs 0.805/0.010, 0.883/0 vs 0.867/0; NCLT 0.672/0
vs 0.659/0; Nordland 0.825/0 vs 0.806/0. CST (a + a) has recall above SH by 0.004-0.017, but Boreas s0 reaches segFAR 0.058,
which is consistent with its 2a bound.

**Pre-registration (366 runs, before the full evaluation; local CPU, cached statistics; `oc_curves.py --cst --fams @E34`,
groups cond + loco, alpha 0.05).** H34a (end-to-end validity): CMS-CPC/H+CST2+G+NGRr and CMS-CPCW/H+CST2+NGRr have mean segFAR
<= 0.05 on 7/7 datasets. H34b (price of removing the constant): their recall is within 0.02 of the hand-set SH rule
(CMS-CPC/H+SH+G+NGRr) on >= 5/7 and above CPC-SC-T(1/2)+SH on >= 6/7. H34c (causal): the [both] variants of CST2 are valid on
7/7. Diagnostic: the fraction of datasets where CST (a + a) exceeds a, and its maximum (expected <= 2a).

**Amendment (written while proving Proposition 14, BEFORE any full-evaluation result; the first full run was stopped after 5 min,
nothing of it was read).** (1) *Theory correction:* a false fix needs the chain to report AND the frame to pass CST. That is an
intersection, so P <= min(...), not a sum: CST with a_sh = a alone bounds the segment false-fix rate by a/pi (Corollary 15
rewritten). CST2 (a/2 + a/2) is only more conservative. (2) *Same-estimator variant CSTt:* the tested track is the real route
winner MP[j], the same estimator as the null track MP[j_cf], so (S3-T) compares like with like. CST tests the HMM MAP track
against route ghosts, which is an approximation of (S3-T). Design check (same 8 runs): CSTt+G+NGRr has much lower recall (CMU 0.745 vs
SH 0.820, Nordland 0.751 vs 0.825, countryside 0.596 vs 0.673; the route track is noisier, so correct tracks fail too); Boreas
s0 segFAR CST 0.058, CSTt 0.048, SH 0.018. **Main rule of H34a / H34b is therefore CST (MAP track, a_sh = a = 0.05)**:
CMS-CPC/H+CST+G+NGRr and CMS-CPCW/H+CST+NGRr; CST2 and CSTt are reported as pre-specified alternatives. H34c applies to
CST[both]. Preset `@E34` (updated), groups cond + loco, alpha 0.05, 366 runs, local CPU.

**Correction (18:15, after the first full local run, before any conclusion was written).** The local counterfactual-statistics
cache was the OLD approximate one (Entry 28: top-100 truncation, shown anti-conservative by the Entry 29 audit). Every Kaggle
evaluation since Entry 29 uses `nhatlong1103/hmm-cms-cache-exact`. Consequences:
- The Step-1 diagnosis numbers, the two design checks above and the first full local run (kept in the scratchpad as
  `results_approx_cache`, not reported) were computed on the approximate null. They are void as evidence.
- The exact cache was downloaded. A local run on it reproduces the Kaggle E33 result of the same run to 4 decimals (4S
  countryside CosPlace s0: 0.6588 / 0.0 for the main rule, 0.5023 / 0.0 for CPC-SC-T(1/2)+SH).
- The evaluation was restarted on the exact cache, with the hypotheses and the main rule unchanged: Boreas (60 runs) plus the
  Boreas part of the a_sh sensitivity on 20 Kaggle CPU kernels, the other 306 runs locally.

**Results (366 runs, exact cache; raw `analysis/results/e34/`, tables `paper/e34_tables.md`).**
1. *H34a supported (7/7).* CMS-CPC/H+CST+G+NGRr mean segFAR 0.001-0.022 (Boreas 0.018, CMU 0.016, 4S office 0.016, old town
   0.022); CMS-CPCW/H+CST+NGRr 0.004-0.028. Every one is <= 0.05.
2. *H34b supported.* Recall of CST vs the hand-set SH rule: +0.008 (Boreas), +0.005 (NCLT), +0.003 (CMU), +0.010 (Nordland),
   +0.008 (4S office), +0.022 (old town), -0.005 (countryside): within 0.02 on 7/7 and higher on 6/7. CPCW+CST is within 0.02 on
   6/7 (countryside -0.028). Both are above CPC-SC-T(1/2)+SH on 7/7.
3. *H34c supported (7/7).* The causal [both] variants are valid on 7/7 (CPC+G: 0.000-0.016) with only 3.6 % of runs above alpha.
4. *Price (diagnostic).* CST spends the alpha budget instead of being over-conservative: 6.0 % of runs have segFAR > alpha
   (worst 0.109), against 0.5 % for the hand-set SH (worst 0.051). The guarantee is on the expected segment rate, not per run.
5. *Level sensitivity (seeds 0-2, 114 runs per variant): the calibrated level degrades gracefully, unlike the tolerance.*
   a_sh = 0.5 alpha: valid 7/7, recall -0.01 to -0.04. a_sh = 2 alpha: STILL valid on 7/7 (worst mean segFAR 0.041, Boreas),
   recall +0.01 to +0.05. Compare the SH tolerance x 2 of Entry 32, which broke alpha on 2/7 (CMU 0.071, countryside 0.100).
6. *Alternatives.* CST2 (a/2 + a/2): valid 7/7, recall -0.01 to -0.05 vs CST. CSTt (same-estimator route track): valid 7/7,
   recall lower than CST on 6/7 (Nordland -0.07, CMU -0.05).
**Verdict.** The counterfactual surgery calibrates the exit of a report chain as well as its onset. The one a-priori constant
that validity depended on (Entry 32) is replaced by a level a_sh with a statement (Proposition 14). Recall is preserved, and the
behaviour under mis-specification of the level is graceful. The proposed rule can be presented as CMS-CPC/H+CST+G+NGRr (fully
calibrated) with the hand-set SH as the conservative variant. Open: segments within N frames of the excursion start are outside
Proposition 14; forward surgery would close this gap.

## Entry 33 (branch `hmm-navigation-5`) — competitors read in full, improvement attempts, reputable new datasets (2026-11-01)

**Competitors (read in full; `literature/RELATED_WORK_E32.md` section 7).** SafeVPR'26 (labelled Mondrian LTT, FDR under
exchangeability only, per 10-frame sequence, Oxford RobotCar / NCLT / St Lucia), Through-the-Lens-of-Doubt'25 (SU score, training
free, no threshold), SUE (CVPR'24, score), To-Match-or-Not'25 (RANSAC inliers, needs images), Carson'23 (label-free consensus
rule), SMR'25 (supervised per dataset), Valentin'26 (filter calibration check, needs ground truth). None addresses per-frame,
label-free fix acceptance with off-map regions and a guarantee. Added as baselines (`oc_curves.py --newbase`, `@E33B`):
SU25, SUE24 (threshold = conformal quantile of the score on the labelled off-map frames of the benign conditions; "-seg" variants
calibrated on labelled off-map SEGMENTS, the most favourable fair version), Carson23. Design run Nordland CosPlace s0:
SU25 0.379 / segFAR 0.354, SU25-seg 0.150 / 0.046, SUE24 0.458 / 0.336, SUE24-seg 0.347 / 0.038, Carson23 0.603 / 0.982,
proposed 0.826 / 0.000.

**Pre-registration of the Entry 33 evaluation (366 runs, before any of it).** (a) New competitor baselines SU25, SUE24, SU25-seg,
SUE24-seg, Carson23 (`--newbase`). (b) *Counterfactual-calibrated SH* (`--shcf`, families /H+SHcf): the shape tolerance eps of
the SH stop = beta-quantile (beta = 0.01) of the shape residual of the COUNTERFACTUAL track MP[j_cf] (false by construction) in
the calibration group, instead of the a-priori 0.5 excl; on the 5 design runs it recovers eps = 0.39-0.58 excl. Hypotheses:
H33a the proposed rule has higher recall than every new competitor whose mean segFAR <= alpha, on >= 6/7 datasets; H33b
CMS-CPC/H+SHcf+G+NGRr is within 0.01 recall of CMS-CPC/H+SH+G+NGRr on >= 5/7 with mean segFAR <= alpha on 7/7 (the hand-set
tolerance is replaceable by a calibrated one). (c) New dataset: Oxford RobotCar (PointNetVLAD split, 44 traversals), dump
kernel republishes it as `nhatlong1103/oxford-robotcar-vpr-dump` / `-images`; evaluated with the same protocol (30 % holes).

**Results (366 runs, `@E33B --newbase --shcf`; raw `analysis/results/e33/nb.tgz`, tables `paper/e33_tables.md`).**
1. *H33a supported (7/7).* Every new competitor either breaks alpha or has much lower recall than the proposed rule
   CMS-CPC/H+SH+G+NGRr. SU'25 and SUE'24 calibrated on labelled off-map frames: segFAR 0.19-0.36 on every dataset. Carson'23
   (label-free consensus): segFAR 0.72-0.99. The most favourable fair versions, calibrated on labelled off-map SEGMENTS:
   SU'25-seg breaks alpha on 4/7 and reaches recall 0.05-0.33 where valid; SUE'24-seg is valid on 7/7 with recall 0.09-0.39
   against 0.49-0.82 for the proposed rule (Boreas 0.248 vs 0.775, CMU 0.268 vs 0.822, Nordland 0.391 vs 0.765). The older label
   baselines confirm the picture: Xu'21 0.021-0.227, Claxton'24 0.12-0.26, TAO'26 0.24-0.74, max-sim 0.08-0.19 mean segFAR.
2. *H33b not supported.* SHcf (tolerance = 1 % quantile of the counterfactual-track residual) keeps validity on 7/7
   (segFAR 0.000-0.013) but its recall is within 0.01 of the hand-set SH on only 4/7 (NCLT -0.012, 4S countryside -0.024, old town
   +0.011). The frame-level quantile is not a sufficient replacement; Entry 34 tests the segment-level counterfactual test CST.

3. *(c) Oxford RobotCar (new reputable dataset; 60 runs = 6 descriptors x 10 seeds, 30 % holes, map = 2014-12-09, 42 query
   traversals, 33 236 query frames, map 803 frames before holes; exact counterfactual statistics computed in the job; raw
   `analysis/results/e33/oxford.tgz`).* The dump is published as `nhatlong1103/oxford-robotcar-vpr-dump`.
   - *Map-null baselines degenerate.* CPC-SC-T(1/2)+SH and CPC-SC+CS report NOTHING in 36/60 runs: after the holes the map has
     ~670 frames, too few null segments to reach a finite alpha-quantile. This is exactly the n ~ 10 regime of Corollary 9.
   - *CMS calibrates in every run.* Its null comes from the query stream (thousands of segments). CMS-CPC/H+SH+G+NGRr:
     recall 0.719, segFAR 0.003, 0 % of runs > alpha, error 21.7 m. CMS-CPCW/H+SH+NGRr: 0.753 / 0.006 / 0 % / 21.0 m.
     CPC-SC-T(1/2)+SH over all runs: 0.311 / 0.007 / 43.7 m.
   - *Paired, on the 24 runs where the map null works:* CMS-CPCW has recall +0.008 vs CPC-SC-T(1/2)+SH (higher in 14/24), error
     -1.9 m (lower in 19/24) and segFAR 0.008 vs 0.018. The main rule (with +G) has recall -0.026 there (higher in 7/24).
     On Oxford the recall advantage of CMS over a WORKING map null is therefore small. The gain is robustness: no degeneracy, lower
     error, lower segFAR.
   - *Label baselines break alpha:* Xu'21 segFAR 0.547 (100 % of runs > alpha), TAO'26 0.478 (93 %), Claxton'24 0.156 (72 %),
     SUE'24-seg 0.066 (40 %), SU'25-seg 0.076 (52 %), Carson'23 0.984 (100 %).

**Improvement attempts (design runs only, labels only to diagnose; negative results recorded).**
1. *SU as a third CMS statistic:* AUROC (correct on-map vs off-map) of the logistic combination route cost + z vs + SU:
   0.949 -> 0.952 (Nordland), unchanged on 4S old town / countryside, Boreas, CMU; SU alone 0.48-0.84 (route cost 0.90-0.98)
   -> not added (no information beyond the CMS statistics).
2. *Where the proposed rule loses recall* (correct HMM place on-map but not reported): the SH shape stop 3.7-10.3 % of the on-map
   frames, the presence onset 0.4-7 %, +G 0.2-2.2 %.
3. *Streak-aware SH ("SHs", `cpc_geo.hyst_shape`: shape window = the onset window, then the frames since the onset):* recall
   +5 to +10 points but segFAR 0.06-0.18 (> alpha) on 4/5 design runs -> rejected. The full-window SH is part of the segment-level
   validity at excursion boundaries and for re-onsets inside holes (Theorem 6' covers segments deep in an excursion only).

## Entry 32 (branch `hmm-navigation-5`) — sensitivity, running time, natural near off-map (NCLT, every session as the map), literature (2026-11-01)

**Pre-registration (design: Nordland CosPlace s0, 4S old town CosPlace s0, NCLT map 2013-04-05 CosPlace).**
1. *Decision-layer sensitivity (`analysis/sens_eval.py`, `cms.SENS`, `oc_curves.py --sens`; 366 runs).* One constant at a time:
   onset window W in {5, 20} (default H = 10), route weight of the e-value mixture wr in {0.25, 1.0} (0.5), presence transitions
   p in {0.005, 0.02} (0.01), agreement radius of +G g in {0.5, 2} x excl (1), SH tolerance shd in {0.5, 2} x default, gate quantile
   beta in {0.01, 0.10} (0.05), release length R in {5, 20} (H). Defaults reproduce Entry 30 exactly (checked, max |diff| 1e-16).
   Rules: CMS-CPC/H+SH+G(+NGRr), CMS-CPCW/H+SH(+NGRr) at alpha 0.05 / 0.01 (`@E32S`).
2. *Counterfactual construction (`analysis/sens_cf.py`; seed 0, 42 runs).* Belief window N in {10, 40} (20) and corridor radius
   rho in {0.75, 1.25} x off_d, recomputing the exact top-300 and the statistics; "base" (N = 20, rho = off_d) recomputed in the
   same job for the timing reference. Wall time of every stage (top-300 on the GPU, counterfactual statistics, decision layer).
3. *Natural near off-map (`natural_eval.py nclt:<ref>`).* NCLT with each of the 8 other sessions as the map (no hole, real wheel+FOG
   odometry; 6-13 % of the query frames naturally > 20 m from the map, 26-93 excursions >= 10 frames per map; MSLS val and 4Seasons
   within-scene were checked and have <= 1.2 % / 0 % natural off-map, unusable), 48 runs, both inits.
4. *Hypotheses.* H32a: for every variant of 1-2 the proposed rule keeps mean segFAR <= alpha on 7/7 and its recall stays above
   CPC-SC-T(1/2)+SH on >= 6/7 (robust to the a-priori constants); H32b: the decision layer costs < 1 ms per frame and the
   counterfactual statistics < 10 ms per frame (real-time at 10 Hz on one CPU core); H32c: on the 9 NCLT maps the causal CMS rules
   keep segFAR <= alpha (pooled) and beat CPC-SC-T(1/2)+SH in recall on >= 6/9 maps.

**Results, part 1: decision-layer sensitivity (all 366 runs x 14 variants; raw `analysis/results/e32/sens.tgz`).**
1. *H32a supported for 12 of the 14 constants.* Varying W, the route weight, the presence transitions, the +G radius, the gate
   quantile or the release length moves the recall of CMS-CPC/H+SH+G+NGRr by at most 0.03 on any dataset (default
   0.775 / 0.612 / 0.822 / 0.765 / 0.800 / 0.703 / 0.491 on Boreas / NCLT / CMU / Nordland / 4S office / old town / countryside).
   Every one of those variants keeps mean segFAR <= 0.05 on 7/7 and recall above CPC-SC-T(1/2)+SH on 7/7. The same holds for
   CMS-CPCW/H+SH+NGRr. W does not enter CMS-CPC/H+SH+G (identical rows, as expected).
2. *H32a not supported for the SH shape tolerance* (pre-registered as one of the constants). x 2 breaks validity:
   segFAR 0.071 (CMU) and 0.100 (4S countryside) for the proposed rule (5/7 valid), 4/7 for CMS-CPCW. x 0.5 stays valid
   but loses recall (NCLT 0.612 -> 0.511, old town 0.703 -> 0.627; above CPC-SC-T(1/2)+SH on 5/7 only). The SH tolerance is the one
   a-priori constant the guarantee depends on: SH is part of the segment-level validity at excursion boundaries (Entry 33,
   attempt 3). Its label-free calibration from the counterfactual track (SHcf) is the Entry 33 hypothesis H33b.
3. *alpha = 0.01:* every variant except SH x 2 keeps segFAR <= 0.01 on 7/7 (CMU 0.007 at the default).

**Results, part 2: counterfactual construction, running time, natural near off-map (all kernels done; raw `analysis/results/e32/`).**
1. *Counterfactual construction (seed 0, 42 runs per variant): H32a supported.* N in {10, 20, 40} and rho in {0.75, 1, 1.25} off_d
   keep mean segFAR <= 0.05 on 7/7 and recall above CPC-SC-T(1/2)+SH on 7/7 for CMS-CPC/H+SH+G+NGRr and CMS-CPCW/H+SH+NGRr.
   A LONGER belief window helps: N = 40 vs 20 gives recall +0.015 (Boreas), +0.015 (CMU), +0.027 (4S countryside), validity
   unchanged. N = 10 costs 0.01-0.03. rho moves recall by <= 0.008.
2. *Running time: H32b not supported as pre-registered, real time holds.* Median per frame on a Kaggle L4 session (top-300 on
   the GPU, the rest on one CPU core): top-300 0.01-0.05 ms, counterfactual statistics 10.3-17.5 ms (pre-registered < 10 ms),
   decision layer 1.7-2.8 ms (pre-registered < 1 ms; it includes process start-up and the evaluation of 9 rule families). Total
   ~20 ms per frame, i.e. real time at 10 Hz (and ~50 Hz) on one core. The counterfactual statistics are a pure-Python loop over
   frames (vectorisation is the obvious next speed-up).
3. *NCLT, every session as the map (48 runs, 9 maps; natural near off-map): H32c supported.* Pooled over the 9 maps:
   CMS-CPC/H+SH+G+NGRr recall 0.599 / mean segFAR 0.007 / worst 0.033 / 0 % of runs > alpha / error 3.8 m, recall above
   CPC-SC-T(1/2)+SH (0.575 / 0.010 / 0.053 / 4 % / 4.6 m) on 9/9 maps; the causal [both] and [online] variants also 9/9 with
   segFAR 0.006. Label baselines: Xu'21 0.500 / 0.036 / 26 % of runs > alpha, Claxton'24 81 %, TAO'26 100 %.

## Entry 31 (branch `hmm-navigation-5`) — HMM-centric CMS: joint place-presence HMM with a calibrated OFF state (2026-11-01)

**Pre-registration (design runs: Nordland CosPlace s0, 4S countryside MegaLoc s0, 4S old town CosPlace s0).**
1. *Model (`analysis/cms_hmm.py`).* State space {map places} U {OFF}; place transitions = the odometry kernel of the place chain;
   presence transitions p_in = p_out = 0.01. The OFF emission is set so that the posterior odds ON:OFF are multiplied by
   exp(l_t), l_t = the CMS-calibrated presence log LR (`cms.chain_parts`) => the OFF marginal of the HMM IS the calibrated CMS
   presence chain (checked numerically: identical log-odds to 1e-6), so Theorems 6 / 6' / 6'' are statements about the HMM.
   Place update "temper" (exact for a model where the place keeps evolving while OFF and an OFF frame carries no place
   information): b+ ~ b- (q_t L_t / <b-, L_t> + 1 - q_t), q_t = P(on at t). Design alternative "reset" (uniform OFF -> ON
   re-entry) was rejected on the design runs (recall -0.01 to -0.02 on 4S: a dip of P(on) inside the map erased a correct
   place belief). Emissions from the exact top-K list (outside entries at the K-th value), scale tau chosen label-free by
   agreement with the stored place chain (98 % agreement on on-map frames, Nordland s0).
2. *Design results (labels only to evaluate).* Place accuracy in the first 30 on-map frames after an off-map stretch:
   0.80 -> 0.90 (Nordland, reset mode, vs the same re-implemented chain without OFF). Default points, /J (temper) vs /R
   (same emissions, no OFF): recall +0.002 / ±0.003 / -0.009 (countryside / old town / Nordland), Nordland CMS-CPCW error
   27.3 -> 6.0 m and segFAR 0.008 -> 0.003; vs the stored full-similarity chain /H both /R and /J are ~0.01 lower in recall
   (emission re-implementation, not the coupling).
3. *Hypotheses.* H31a: /J matches /H within 0.01 recall on >= 5/7 datasets (the coupling is not harmful); H31b: /J has lower
   mean error than /R on >= 4/7 (the coupling cures lock-in of the same chain); H31c (exploratory): /J beats /H.
4. *Evaluation.* Seeds 0-2 of all 7 datasets x 6 descriptors (126 runs), defaults, alpha 0.05 / 0.01, groups cond, [online],
   [both], +NGRr (`oc_curves.py --joint --fams @E31J`).

**Results (114 runs, seeds 0-2; raw `analysis/results/e31/`, report `paper/BAO_CAO_E30.pdf` Tables 11-12).**
1. *H31a supported:* /J within 0.01 recall of /H on 6/7 datasets (CMS-CPCW+NGRr and CMS-CPC+G+NGRr); exception Nordland -0.021 to
   -0.030 (CI < 0), the same gap as the re-implemented chain /R (emission from the top-100 list, not the coupling). Error: 4S
   countryside -3.5 / -1.1 m (CI < 0), Nordland +1.4 m (CMS-CPCW, CI > 0), others within 1.1 m.
2. *H31b not supported:* coupling vs the same chain without OFF (/J vs /R): recall within 0.003 on 7/7, error lower on 3/7 (CMS-CPCW;
   Boreas -2.6 m, CI < 0) and 1/7 (CMS-CPC+G); old town / countryside +1.3 to +2.8 m (not significant).
3. *H31c not supported:* /J does not beat /H. /J still beats CPC-SC-T(1/2)+SH on recall 7/7 and error 7/7 (CI 5/7).
**Verdict.** The HMM-centric formulation is exact (Prop 13: the OFF marginal of the joint HMM IS the calibrated presence chain), so
the method can be presented as one HMM with a counterfactually calibrated off-map state; the exact coupled place update brings no
consistent gain over the factorised implementation (/H), which stays the evaluated and recommended form.

## Entry 30 (branch `hmm-navigation-5`) — causal online calibration, filter robustness, natural off-map benchmark (2026-11-01)

**Pre-registration (written before the full evaluation; design used Nordland CosPlace s0 and 4sx office loop + old town CosPlace).**
Motivation: on datasets alone (no robot), the open questions of Entry 29 are (i) the CMS null is calibrated transductively
per session (the whole session's counterfactual stream, future frames included); (ii) the navigation gate and the error
metric are tied to one Kalman configuration with a ground-truth initial pose; (iii) every off-map frame except NCLT's comes
from synthetic block removal; a session that is ENTIRELY off the map has pi = 0 good segments, where the self-contamination
bound of Theorem 6 is vacuous for the per-session (cond) calibration.
1. *Causal calibration groups (`analysis/cms.py: online_parts, rules_online`; `oc_curves.py --cms-groups cond,loco,online`).*
   `[loco]` = other sessions only (Entry 28). `[online]` = other sessions + the current session's counterfactual segments that
   ENDED before t (insertion per H-block), the e-value transform and Beta-EM a fixed from the other sessions: a strictly
   causal, sequentially updated quantile. `[both]` = report iff the cond rule AND the [loco] rule report (valid if either
   null is valid: the intersection of two accept sets has false-onset probability <= min of the two). The +NGR gate radius of
   the causal variants is calibrated with the [loco] groups. Families: CMS-CPCW/H+SH and CMS-CPC/H+SH+G x {cond, [loco],
   [online], [both]} x {alpha 0.05, 0.01} x {no gate, +NGR} (preset `@E30`).
2. *Filter robustness (`nav_demo.py --nav-q --nav-sig --nav-init`).* Three a-priori alternative evaluation filters, applied
   to the gate AND the error metric of every rule: F1 process noise 0.2 L (4x), F2 = F1 + fix sigma 10 m, F3 label-free
   initialisation at the first frame's top-1 retrieval with sigma 1 km (`--nav-init top1`; design check: with sigma 25 m
   a wrong first retrieval, 4 km on Nordland, decays only as 1/n even under oracle fixes, 385 m mean error; the error of F3 is averaged from each sequence's first
   localisable frame on, since the wrong-init offset before it is the same for every rule). Families `@E30F`.
3. *Natural off-map benchmark (`analysis/natural_eval.py`, `vprlib.load_4s_cross`).* Map = reference recording of a 4Seasons
   scene A without holes; queries = the other recordings of A, then every recording of another scene B (all off-map, real
   images and VIO). 6 ordered pairs of {office loop, old town, countryside} x 6 descriptors = 36 runs, one seed. Label baselines
   are trained on the most benign A recording plus one LABELLED B recording (favourable to them). Navigation error is
   reported on scene A only (B coordinates are unrelated to the map frame); second pass with F3 initialisation.
4. *Hypotheses.* H30a (causal validity): [online] and [both] variants have mean segFAR <= alpha on 7/7 datasets at alpha =
   0.05 and 0.01. H30b (causal recall): CMS-CPCW/H+SH[both]+NGR has recall above CPC-SC-T(1/2)+SH (round-5 best) on >= 6/7 and
   navigation error lower on >= 5/7. H30c (filter robustness): under each of F1-F3, CMS-CPC/H+SH+G+NGR and CMS-CPCW/H+SH+NGR
   have error lower than CPC-SC-T(1/2)+SH on >= 5/7 and the +NGR gate lowers the error of CMS-CPC/H+SH on >= 4/7.
   H30d (natural off-map): the causal variants ([loco], [online], [both]) keep the scene-B segFAR <= alpha (mean over the 36
   runs, alpha = 0.05) and their scene-A recall exceeds CPC-SC-T(1/2)+SH on >= 4/6 pairs; the transductive cond variant may
   violate (pi = 0 sessions) -- reported, not hidden.
5. *Gate fixes found in the F3 design check (Nordland CosPlace s0), adopted before the evaluation (`analysis/navrisk.py`).*
   (a) The release re-tested coherence after every accepted fix, which sees the innovation jump caused by the filter's own
   update: a released streak was accepted only every R-th frame (implementation did not match the Entry 29 description "the
   gate opens for that streak"); now the gate stays open until the streak ends. (b) Gate radius max(tau, 3 sqrt(P^-)): the
   prior uncertainty of the filter keeps the gate open while the filter is not localised (inactive when sqrt(P) ~ 0.6 m).
   With the ground-truth init the s0 results are unchanged (recall / segFAR / error identical for every +NGR family); with F3
   the +NGR error drops from 58 to 32 m. Every +NGR family of the main evaluation is recomputed with the fixed gate.
   *Deviation noted at launch (before any result):* the `@E30F` output list does not contain the ungated CMS-CPC/H+SH, so the
   gate effect of H30c is measured on the pairs CMS-CPCW/H+SH(+NGR) and CMS-CPC/H+SH+G(+NGR) of the same runs.
   *Mid-evaluation note (written after 202/366 main runs, before any other analysis).* Ungated families reproduce Entry 29
   exactly run by run (202/202). The pre-registered streak-open release (a) is MIXED with the ground-truth init: Boreas
   +1.3 to +2.6 m mean error (one run +36 m: a coherent FALSE streak passes once released), CMU +0.5 m, Nordland / 4S old town /
   countryside lower. The Entry 29 code is therefore a legitimate design, not only a bug: a RATE-LIMITED release (one fix per R
   frames while a coherent streak stays outside the gate) bounds the harm of a coherent false streak. Both are kept: "+NGR" =
   streak-open (pre-registered), "+NGRr" = rate-limited (Entry 29 behaviour) with the uncertainty floor (b); every run is
   recomputed with +NGRr (`oc_curves.py --gate-rate`, preset `@E30R`) and LODO chooses among both, no choice from the tables.
6. *Selection.* Deployment default = the highest-recall calibration group that satisfies H30a and the natural-benchmark
   validity of H30d; main rule CMS-CPCW/H+SH+NGR (exact onset theorem, Theorem 6'), recall-oriented variant
   CMS-CPC/H+SH+G+NGR (LODO choice of Entry 29). Paired cluster-bootstrap CIs by seed (`analysis/paired_stats.py`).

**Results (366 main runs x {F0, F1, F2, F3}, 36 natural runs x 2 inits, 216 hole runs; both gate variants; report
`paper/BAO_CAO_E30.pdf`; raw `analysis/results/e30/`).**
1. *Reproducibility:* ungated families identical to Entry 29 on 366/366 runs; +NGRr identical to the Entry 29 gate on 360/366
   (6 NCLT runs differ by <= 0.001 recall through the uncertainty floor).
2. *Selection:* LODO over every label-free family (both gate variants, all calibration groups) picks **CMS-CPC/H+SH+G+NGRr** in
   7/7 folds at alpha = 0.05 (regret 0.1-2.5 m) and its alpha = 0.01 version in 6/7 folds at alpha = 0.01. Streak-open vs
   rate-limited release (same runs): Boreas +2.0 to +2.9 m, CMU +0.5 m (CI > 0), 4S countryside -0.5 to -1.0 m.
3. *H30a supported:* [online] and [both] mean segFAR <= alpha on 7/7 at both alphas (max mean 0.009 at alpha 0.05).
4. *H30b supported (with +NGRr):* CMS-CPCW/H+SH[both]+NGRr vs CPC-SC-T(1/2)+SH: recall higher 7/7 (CI > 0 6/7), error lower 7/7
   (CI < 0 7/7); CMS-CPC/H+SH+G[both]+NGRr: recall 7/7 (CI 6/7), error 7/7 (CI 5/7). [online] loses recall on Nordland.
5. *H30c:* proposed rule vs CPC-SC-T(1/2)+SH under F1 / F2 / F3: recall 7/7 / 7/7 / 7/7 (CI 6/7 each), error 7/7 / 7/7 / 7/7 (CI 5/7,
   7/7, 6/7) -> supported. Gate effect: 7/7 under F1 and F2, only 2/7 under F3 (label-free init: the gate assumes a localised
   filter) -> partially supported.
6. *H30d supported:* natural off-map (36 runs): every CMS variant valid at alpha = 0.05 (no run above alpha; worst 0.044 ungated,
   0.013 with +NGRr); scene-A recall above CPC-SC-T(1/2)+SH on 6/6 pairs (pooled 0.70-0.72 vs 0.59; error 18-20 vs 26 m); label
   baselines exceed alpha in 11-28 % of the runs. The transductive cond variant exceeds alpha = 0.01 in 2/36 runs (1/36 with the
   gate), the causal variants never.
**Verdict.** Proposed method unchanged: CMS-CPC/H+SH+G+NGRr (rate-limited release); deployable causal version
CMS-CPCW/H+SH[both]+NGRr or [online]+NGRr; conclusions robust to the evaluation filter.

## Entry 29 (branch `hmm-navigation-5`) — navigation-risk calibration and self-audit (2026-11-01)

**Pre-registration (written before the full evaluation; design used 6 runs: Boreas MegaLoc s1, 4S old town CosPlace s0,
4S countryside MegaLoc s0, CMU CosPlace s7, Nordland CosPlace s0, NCLT MegaLoc s0).**
1. *Diagnosis (labels only to classify).* Accepted TRUE fixes have small innovations (median 0.5-8 m, 90th pct 2.6-40 m),
   the harmful FALSE fixes large ones (90th pct 42-856 m); the evaluation filter's sqrt(P) is ~0.6 m (gain ~0.014), so a
   chi^2 / dead-reckoning gate locks out after drift (Entry 23 +GG).
2. *Method +NGR (`analysis/navrisk.py`): counterfactual innovation gate.* The counterfactual winner of CMS is a false fix by
   construction; its displacement from the belief d_cf is the innovation a false fix would cause. Gate radius tau =
   beta-quantile of d_cf in the calibration group (beta = 0.05, a priori); report iff the base CMS rule reports and the
   online innovation <= tau; release for a streak when the base rule reported the last H frames with coherent innovation
   vectors (spread <= excl/2). Only removes reports (segment guarantees kept). Candidates: CMS-CPC/H+SH(+G), CMS-CPCW/H+SH(+G),
   CMS-T/H+SH at alpha 0.05 / 0.01 with +NGR; ablations +NG (no release), +DRG (classical dead-reckoning gate), +NGR on the
   old rules (CPC-SC-T(1/2)+SH, CPC-SC+CS).
3. *Audit fixes adopted before the evaluation.* (a) CMS-CPCW: onset by the finite-memory window chain (the fresh-start
   calibration of a full-memory chain does not dominate a non-reporting chain entering a segment with log-odds in (0, kappa];
   the CPC-SC / CMS-CPC onset statements need this correction); (b) EXACT counterfactual (`analysis/cms_exact.py`, top-300
   lists, first 100 unmasked entries for hypotheses, look-ups and fallback): the top-100 truncation of Entry 28 was checked to
   shift the route cost little (median +0.004) but made the distinctiveness null anti-conservative (z_cf median 0.264 vs 0.287).
   All 366 runs and the hole-ratio runs are recomputed with (b).
4. *Hypotheses.* H29a: at alpha = 0.05, +NGR lowers the navigation error of CMS-CPC/H+SH on >= 5/7 datasets with recall loss
   <= 0.01 and no mean-segFAR increase; H29b: CMS-CPC/H+SH+NGR at alpha = 0.05 has error <= CPC-SC-T(1/2)+SH (the previous best)
   on >= 5/7 and recall higher on >= 6/7; H29c: +NG and +DRG lock out on at least one VIO dataset (recall drop > 0.1);
   H29d: CMS-CPCW is valid (mean segFAR <= alpha on 7/7 at both alphas).
5. *Selection.* LODO (Entry 25 criterion) over all label-free rules, at alpha = 0.05 and 0.01.

**Results (366 runs, exact counterfactual `nhatlong1103/hmm-cms-cache-exact`; report `paper/BAO_CAO_E29.pdf`; raw
`analysis/results/e29/`, `nhatlong1103/hmm-e29-results`; audit `paper/AUDIT_E29.md`).**
1. *H29a (gate effect) supported:* CMS-CPC/H+SH+NGR vs CMS-CPC/H+SH: error lower with a cluster-bootstrap CI below 0 on 6/7
   (Boreas -5.8, NCLT -3.2, CMU -2.7, Nordland -7.3, office -0.2, old town -1.4 m), segFAR lower 7/7, recall loss <= 0.011.
2. *H29b supported:* CMS-CPC/H+SH+NGR (alpha 0.05) vs CPC-SC-T(1/2)+SH: recall higher 7/7 (CI > 0 on 7/7), error lower on 6/7
   means (CI < 0 on 4/7, none worse). LODO picks **CMS-CPC/H+SH+G+NGR** in 7/7 folds (alpha 0.05, regret 0-2.5 m) and its
   alpha = 0.01 version in 7/7 folds (regret 0-2.4 m): recall higher than CPC-SC-T(1/2)+SH 7/7 and error lower 7/7 (CI: 6/7 and 6/7).
   Curves: recall at FL <= 0.01 of CMS-CPC/H+SH+NGR above CPC-SC-T(1/2)+SH 7/7, above Claxton'24 / TAO'26 (labels) 6/7.
3. *H29c supported:* +NG locks out on VIO (old town 0.485 / 73.8 m, countryside 0.313 / 72.7 m); +DRG on NCLT (56.3 m), old town (68.9 m).
4. *H29d supported:* CMS-CPCW mean segFAR <= alpha on 7/7 at both alphas; CMS-CPCW/H+SH+NGR beats CPC-SC-T(1/2)+SH on recall 7/7 and
   error 7/7 (onset rate 0.03-0.09 alpha).
5. *Exact vs truncated counterfactual:* results differ by <= 0.005 recall (Entry 28 numbers stand); Theorem 6 check with the exact null:
   realized / alpha 0.46-1.18, below the bound on 7/7.
6. *Hole ratio (exact, gate; 216/216 runs, one d50 Boreas SALAD run OOM-killed at 23 jobs/session and re-run at 12):* 10 %: recall > CPC-SC+CS 6/6, segFAR <=
   0.017, error lower 4/6; 50 %: recall higher 6/6, the gate brings CMU from 0.051 to 0.027, error lower 4/6.
**Verdict.** Proposed method: CMS-CPC/H+SH+G+NGR (LODO-selected) with CMS-CPCW/H+SH+NGR as the variant with the exact onset theorem.

## Entry 28 (branch `hmm-navigation-5`) — Counterfactual Map Surgery (CMS): self-calibration on the deployment stream (2026-11-01)

**Motivation (Entries 25-27).** Every label-free rule so far is calibrated on the MAP's self-replay null (map frames with
their block removed): same image condition as the map, exact map poses as odometry, ~10 exchangeable chunks. Consequences
measured before: realized false-onset rate 0.001-0.006 << alpha (structural slack), alpha = 0.01 infeasible on maps with
< 99 null segments (CMU, 4S office: kappa = inf), and the long-excursion dependence is missing from the null.

**Idea.** Build the null from the QUERY stream: for every frame t, recompute the evidence statistic on the map with the
corridor of radius rho = off_d + excl around the system's OWN belief removed (the anchors of the winning route hypothesis
over the last N = 20 frames). If the belief is right, every frame of the window is > off_d from the remaining map, so the
counterfactual statistic is a draw from the OFF-MAP law under the query's condition, odometry noise and dependence; if
the belief is wrong, the true place survives the surgery (conservative). Thresholds = conformal quantiles of the
counterfactual stream (segment-level, H frames), per query condition (Mondrian; conditions with fewer than 2/alpha
counterfactual segments pooled). Code: `analysis/cms.py` (statistics + rules), `analysis/cms_dump.py` (Kaggle),
`oc_curves.py --cms DIR [--cms-alpha a] [--cms-groups cond,run]`. Theory: `paper/cms_theory.md`.

**Statistics (identical for real and counterfactual maps, from the top-100 lists `hmm-topk` only):** TAO'26 route cost C_t
(surgery: hypotheses in the corridor removed, masked anchor look-ups fall back to the K-th similarity, a backward trace
entering the corridor leaves the route chunk -- what a real hole does) and the spatial distinctiveness
z_t = (s1 - s_far)/std_t (s_far: best entry > excl from the top-1; all top-100 masked -> missing).

**Pre-registration (written before the full evaluation; seeds 1-9 and every other (dataset, descriptor) not looked at).**
Design was informed by seed 0 of four held-out runs (4S old town CosPlace, Nordland CosPlace, 4S office MegaLoc, CMU
CosPlace): that is where the choices below (HMM place reported, shape stop on the HMM track, Mondrian pooling) were made;
these four runs are flagged in the report. Constants a priori: rho = off_d + excl, N = 20 and every TAO constant from TAO'26,
route e-value power 1/2 (Entry 27), H = 10, p_in = p_out = 0.01, delta = 0.1 for the PAC variants.
1. *Primary rule* **CMS-CPC/H+SH**: presence chain with LR = 1/2 (e^z + (e^C)^(1/2)), e = a p^(a-1), p = conformal rank of
   the real statistic in the counterfactual pool, a = Beta-EM per condition; onset when log-odds > kappa (conformal
   (1 - alpha) quantile of max fresh-start counterfactual log-odds over H-frame segments), persistence log-odds > 0;
   reported place = HMM place-chain MAP; shape stop SH on that track. Reported at alpha = 0.05 and alpha = 0.01.
2. *Secondary:* CMS-T (route cost alone, finite memory, no hysteresis: report iff C_t < kappa_T; TAO winner reported),
   CMS-T/H (HMM place), CMS-U/H+SH (union of route test and chain onset at alpha/2 each), CMS-F (sum of -log p of both
   components), PAC versions, `[run]` (whole-stream calibration) versions; CMS-CPC without stop (expected to violate segFAR:
   reports carried out of the map, diagnostic only).
3. *Hypotheses.* H28a: mean segFAR <= alpha on every dataset at both alphas (validity) with realized/alpha in [0.1, 1.5]
   (tightness, vs <= 0.1 for CPC-SC). H28b: alpha = 0.01 feasible on all 7 datasets (finite kappa, recall > 0). H28c: at
   alpha = 0.01 the primary rule has recall >= CPC-SC-T(1/2)+SH on >= 5/7 datasets with navigation error not worse by
   > 10 % on >= 5/7. H28d: curves (recall at FL <= 0.01, pAUC) of the primary rule >= CPC-SC-T(1/2)+SH on >= 5/7.
4. *Selection.* Leave-one-dataset-out over all label-free rules (old and CMS) with the Entry 25 criterion (navigation
   error at the default point subject to mean segFAR <= alpha on the training folds).

**Deviation from the pre-registration (2026-11-01 ~17:45 UTC, written BEFORE the full evaluation of either radius).**
Theorem-6 diagnostics on all 366 runs of the pre-registered radius rho = off_d + excl (`analysis/cms_diag.py`, labels
only for checking) show realized false-onset rates of CMS-T (route test alone, alpha = 0.05) that depend strongly on the
SEED (hole layout): e.g. CMU CosPlace 0.006 (s0) but 0.14-0.25 (s5-s9), Boreas MegaLoc 0.0-0.16; the bound
alpha (n+1)/(pi n+1) is exceeded on CMU on average. Mechanism (checked on CMU s7): the false onsets are deep inside the
excursions (not a window carry-over at the map edge); the real off-map route cost has q05 0.74 while kappa_T = 0.84-0.86,
i.e. the counterfactual null is LESS on-map-like than the real off-map frames. The pre-registered argument for
rho = off_d + excl ("belief within excl -> every counterfactual frame > off_d") was wrong in direction: with a near-exact
belief the counterfactual frames sit ~off_d + excl = 65 m from the remaining map, while real off-map frames can be at
40-65 m; under S2 the conservative counterfactual is the one AT the off-map boundary, rho = off_d. Correction: rho = off_d
becomes the main setting (all 366 runs recomputed, `nhatlong1103/hmm-cms-cache`); the pre-registered rho = off_d + excl
is kept as `{r1}` families (`nhatlong1103/hmm-cms-cache-r1`) and reported. Local check CMU CosPlace s7: CMS-T segFAR
0.254 -> 0.089 (alpha 0.05), 0.136 -> 0.008 (alpha 0.01); the hysteresis chain CMS-CPC/H+SH still exceeds alpha = 0.01
there (0.042: a false streak that passes the shape stop), the finite-memory CMS-T/H+SH does not (0.000-0.008).

**Results (all 366 runs, 10 seeds, NCLT 1; report `paper/BAO_CAO_E28.pdf`, tables `paper/e28_tables.md`, raw
`analysis/results/e28/` and `nhatlong1103/hmm-e28-results`).**
1. *Theorem 6 check (rho = off_d, labels only to check):* realized false-onset rate of the bare route test CMS-T / alpha =
   0.48-1.14 on 7/7 datasets, <= the bound alpha(n+1)/(pi n+1) on 7/7 (pi = 0.49-0.65); counterfactual cost tail below the real
   off-map tail on 7/7 (S2 direction). Map-null rules use 0.00-0.09 of the budget (CPC-SC+CS). H28a: holds for the primary rule
   (mean segFAR <= alpha on 7/7 at both alphas; 0.04-0.37 alpha at 0.05, 0.05-0.97 alpha at 0.01); the bare CMS-T is tight but
   slightly above alpha on CMU (0.055 at 0.05) and on 4/7 at 0.01 (0.011-0.016) -- within the 1/pi factor of the bound.
2. *H28b (alpha = 0.01 feasible):* yes on 7/7 (map null: recall 0 on CMU and 4S office).
3. *H28c (alpha = 0.01, primary vs CPC-SC-T(1/2)+SH at 0.05):* recall higher on 6/7 (office -0.004), error lower on 5/7
   (Boreas 6.9 vs 5.7, Nordland 10.3 vs 9.5 m worse), mean segFAR <= 0.010 on 7/7: **supported**. At alpha = 0.05 recall is higher
   on 7/7 (+0.041..+0.189) but the error is lower only on 3/7 (Boreas 11.2 vs 5.7 m).
4. *H28d (curves):* recall at FL <= 0.01 >= CPC-SC-T(1/2)+SH on 5/7 (NCLT 0.592 vs 0.612, Nordland 0.790 vs 0.794), pAUC >= on 6/7;
   vs Claxton'24 / TAO'26 (labels) 6/7 each (CMU 0.778 vs 0.791 / 0.792), SafeVPR'26 5/5: **supported (5/7)**.
5. *LODO (pre-registered criterion):* alpha = 0.01: CMS-CPC/H+SH+G chosen in 7/7 folds, regret 0.0-1.8 m (error lower than
   CPC-SC-T(1/2)+SH on 6/7, recall higher on 3/7); alpha = 0.05: the old conservative CPC-SC-T(1/2)+CS is chosen in 5/7 folds
   (spending the 0.05 budget costs navigation error).
6. *Same score, three nulls:* TAO'26 route cost with the labelled 3-sigma threshold violates (segFAR 0.24-0.74), with the map
   null (TAO-SC) recall 0.048-0.659, with the counterfactual null (CMS-T) 0.284-0.819 (> TAO-SC on 7/7), segFAR 0.024-0.055.
7. *Causal [loco] (calibration on the other sessions only):* alpha = 0.01 segFAR <= 0.010 on 7/7, recall > CPC-SC-T(1/2)+SH on 6/7.
8. *Hole ratio (same constants):* 10 %: recall > CPC-SC+CS on 6/6 at both alphas, segFAR <= 0.031 (0.05) and <= 0.005 on 5/6
   (0.01; CMU 0.017), error lower on 4/6; 50 %: recall higher 6/6, CMU above alpha (0.053 / 0.029), error higher on 4/6.
9. *Pre-registered radius {r1}:* the chain + stop stays valid on average at 0.05, CMU exceeds 0.01 (0.013); the bare test is
   seed-dependent anti-conservative -> rho = off_d confirmed. CMS-CPC without stop violates (0.075-0.196), as predicted.
**Correction (Entry 29 audit, cluster bootstrap over seeds + sign test, `analysis/paired_stats.py`).** CMS-CPC/H+SH at
alpha = 0.01 vs CPC-SC-T(1/2)+SH: recall higher with a 95 % CI excluding 0 on 4/7 (Boreas +0.084, Nordland +0.010, old town
+0.060, countryside +0.076; CMU +0.006 and NCLT +0.007 not significant; office -0.005 [-0.10, +0.06]); navigation error lower with
CI excluding 0 on 2/7 (old town -1.7 m, countryside -6.6 m), no dataset significantly worse. The "6/7 / 5/7" counts above are
counts of mean differences, not significant wins. The onset statement of CMS-CPC (and of CPC-SC, Entry 25) is only approximate
(fresh-start calibration does not dominate a non-reporting chain entering with log-odds in (0, kappa]); the exact version is
CMS-CPCW (Entry 29). The counterfactual of this entry is truncated at top-100 (exact version: `analysis/cms_exact.py`).
**Verdict.** New mechanism (Gate 12), tight label-free calibration, alpha = 0.01 feasible, recall gains at a 5x stricter
guarantee with lower navigation error on 5/7, ranking gains 5/7. Open: navigation risk at alpha = 0.05, CMU at small
conditions, S1 only on average over hole layouts, closed-loop robot. Not claimed A* yet.

## Entry 27 (in progress, branch `hmm-navigation-4`) — condition-matched null, route-evidence power, SafeVPR / VLM beyond Boreas (2026-10-31)

**Pre-registration (written before any result of these variants).**
1. *Cross-traversal null (Boreas only; `analysis/xnull.py`).* The 17 Boreas traversals that are neither the map nor a
   query (map-side data, other dates / weather / light) become leave-block-out pseudo-queries (own block masked, kept only
   > off_d from the reduced map), with their real wheel + gyro odometry; same SelfCal half-map test, same R null, top-100
   with the own block masked (route cost). Candidates: CPC-SC(X)+CS, CPC-SC(X)+SH, CPC-SC-T(X)+CS, CPC-SC-T(X)+SH: the
   onset threshold kappa is calibrated on these chunks instead of the map self-replay null; everything else unchanged.
   Hypothesis: less conservative default point (recall up) with segFAR still <= alpha, and a more stable kappa (~340 chunks
   instead of ~10).
2. *Power of the route component (all datasets).* CPC-SC-T used e_T^(1/H); candidates e_T^(1/2) and e_T^1 (fixed a
   priori; validity is unchanged since the whole chain is segment-calibrated on the null). Hypothesis: better ranking with
   strong descriptors (CMU) where the route cost ranks best.
3. *SafeVPR'26 and VPR auditing'26 on NCLT and 4Seasons* (images `nclt-cam5-*`, `4seasons`; shared resolver
   `analysis/vpr_images.py`), same protocol as Boreas.
Criteria as Entries 25-26 (mean segFAR <= 0.05 per dataset, then error and recall at the default point, then curves);
final choice by leave-one-dataset-out over all label-free variants. Seeds 3-9 not looked at for any of these variants.

**Results (all batches; report `paper/BAO_CAO_E27.pdf`, tables `paper/e27_tables.md`, raw `analysis/results/e27/`).**
1. *Cross-traversal null (Boreas, 10 seeds):* 76-85k pseudo off-map frames in 300-360 chunks per seed (map null: ~10).
   kappa from it raises recall by +0.007..+0.008 for every rule (CPC-SC(X)+CS 0.669 vs 0.661, CPC-SC-T(X)+SH 0.677 vs
   0.670), mean segFAR 0.002-0.003, worst run <= 0.029, error equal or lower; curves unchanged. P(p <= .05) of the
   pseudo-queries 0.010-0.035 vs 0.004-0.079 on the map null: the cross-condition null is NOT much weaker. The hypothesis
   "the default is conservative because the null is same-condition" is only weakly supported; the conservativeness is
   structural (kappa covers the presence chain alone, the CS / SH stop then removes most false reports: actual false-onset
   rate 0.001-0.006 << alpha). Joint calibration on this null needs the place chain run on the pseudo-queries (open).
2. *Route power (pre-registered):* w3 = 1/2 gives recall at FL <= 0.01 >= w3 = 1/H on 7/7 (CMU +0.022), pAUC above
   CPC-SC+CS on 7/7, above Claxton'24 (labels) 6/7, SafeVPR'26 (labels) 4/5, TAO'26 6/7 (CMU 0.744 vs ~0.79 remains the
   gap). Default points: CPC-SC-T(1/2)+CS recall above CPC-SC+CS on 7/7 with worst-run segFAR <= 0.046; CPC-SC-T(1/2)+SH CMU
   recall 0.789 but one CMU run at segFAR 0.188 > alpha. Exploratory route-only / min combinations (designed after looking
   at CMU): good with strong descriptors (CMU seed 0 CosPlace 0.819, MegaLoc 0.866) but not general (CMU 6-descriptor mean
   0.658 / 0.693, worse on NCLT / Nordland): dropped. LODO (error criterion) again does not separate the variants
   (CPC-W+CS+SH 5/7 folds, regret <= 3.5 m).
3. *SafeVPR'26 beyond Boreas (labels):* mean segFAR 0.004-0.041, worst run up to 0.22; recall at FL <= 0.01 0.397 / 0.757
   / 0.698 / 0.252 (NCLT / office / old town / countryside) vs CPC-SC-T(1/2)+SH 0.612 / 0.812 / 0.680 / 0.528.
   *VPR auditing'26 (Qwen2.5-VL-7B) beyond Boreas:* precision 0.50-0.93, FAR 0.13-0.46, accepts 8-18 % of off-map frames,
   navigation error 23-102 m; CPC-SC+CS on the same frames FAR 0.002-0.085 and higher S on every MegaLoc set (VLM higher S
   only with NetVLAD, through coverage).

## Entry 26 (in progress, branch `hmm-navigation-4`) — dependence diagnosis, shape-consistency stop, finite-memory onset, dependence-free certificate (2026-10-31)

**Diagnosis before any new rule (labels used only here; `analysis/dep_diag.py`, seed 0).** (1) The top-1 SelfCal p-value of
off-map query frames is super-uniform in the interior of excursions (P(p <= .05) 0.000-0.006 at >= 50 frames from both
edges) but sub-uniform within ~50 frames of the map edge (CMU MegaLoc 0.12-0.16): view overlap, the top-1 is the edge
image 40-100 m away. (2) The anchored-R p-value is sub-uniform in long excursions (Boreas CosPlace P(pR <= .05) 0.19-0.23
at depth 0-100) where the map null has no samples: null chunks are short (mean 84-135 frames) and few (8-10 per map), so
the null cannot represent long excursions and its effective number of exchangeable units is ~10. (3) Fresh-start segment
exceedance of kappa (the SC onset quantity) is <= alpha on most runs but concentrated at shallow depth (Boreas CosPlace
0.18-0.22 at depth < 50) and 0.099 on 4S countryside CosPlace.

**Shape consistency (`analysis/geo_cons.py`, seed 0 of CMU / Boreas / countryside / NCLT / Nordland).** RMS Procrustes
residual of the place-chain MAP track vs the odometry over 3 excl of path: off-map pass rate at eps = excl/4 0.000-0.005
(CS: 0.002-0.088) at on-map pass rate 0.52-0.88 (lower than CS where sequences are shorter than the window). These seed-0
looks are disclosed; seeds 3-9 of the held-out sets were not looked at.

**Dependence-free certificate GPC (`analysis/gpc.py`).** Placements of the odometry window on the map traversal (shape fit
only) + Markov on hit counts: P(false certificate at t) <= alpha for ANY temporal dependence (per-frame assumptions D and
geometry-appearance independence). Seed 0: FL 0 at every alpha, recall 0.04-0.20 at alpha 0.05 (CPC-SC+CS 0.72-0.84):
without an assumption on the dependence, evidence cannot accumulate beyond one frame (the price of dependence).

**Pre-registered protocol for the new rules (written before the held-out results).** Development sets: Boreas, NCLT.
Held-out: CMU, Nordland, 4S office / old town / countryside, seeds 0-9 (seed 0 partly seen as above). Candidates (all
constants in units of excl / H / alpha, one setting for every dataset; `analysis/cpc_geo.py`): M5 CPC-SC+SH (shape stop
D = 3 excl, eps = excl/2, replaces CS), M6 CPC-SC+CS+SH, M7 CPC-SC+CS+SH4 (eps = excl/4), M8 = M5-M7 with reset-on-stop,
M9 CPC-W+CS+SH (onset from the windowed log-odds over the last H frames, kappa_W from the map null; persistence full
memory; reset-on-stop; the rule covered by the onset + geometric-persistence theorem). Reference: M4 CPC-SC+CS (Entry 25).
Order of criteria as Entry 25: mean segFAR <= 0.05 per dataset, then error and recall at the default point, then recall at
matched FL / segFAR (operating curves); final choice by leave-one-dataset-out over all label-free variants.

**Results so far (CPU kernels on 19 accounts; default points 10 seeds = 366 runs, curves seeds 0-2 = 114 runs;
`analysis/results/e26/`).** The pipeline reproduces Entry 25 exactly (CPC-SC+CS recall at FL <= 0.01: 0.766 / 0.586 /
0.705 / 0.780 / 0.771 / 0.664 / 0.545). Recall at FL <= 0.01 / pAUC:

| rule | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| CPC-SC+CS (Entry 25) | 0.766 / 0.777 | 0.586 / 0.588 | 0.705 / 0.724 | 0.780 / 0.787 | 0.771 / 0.771 | 0.664 / 0.657 | 0.545 / 0.543 |
| CPC-SC+SH (M5) | 0.755 / 0.771 | 0.600 / 0.623 | 0.708 / 0.728 | 0.775 / 0.797 | 0.812 / 0.808 | 0.667 / 0.688 | 0.515 / 0.563 |
| CPC-W+CS+SH (M9) | 0.745 / 0.766 | 0.586 / 0.583 | 0.701 / 0.722 | 0.750 / 0.777 | 0.768 / 0.768 | 0.659 / 0.651 | 0.544 / 0.533 |

Default points (recall / mean segFAR / worst-run false onsets per off-map segment): CPC-SC+SH raises recall on 7/7 by
0.004-0.035 at slightly higher segFAR (CMU 0.009, worst run 0.054); M9 is within -0.03..+0.02 of CPC-SC+CS. The false-onset
rate per segment (the quantity of Theorem 5, cpc_theory 3e) is 0.001-0.006 on average for every CPC rule on 7/7 datasets
(alpha = 0.05); worst run <= 0.013 for CPC-SC+CS but 0.071-0.114 for the CPC-W rules on CMU (small map: ~70 null segments,
the conformal quantile varies by run; the guarantee is marginal over calibration). Verdict: SH is a small, mixed gain
(pAUC up on 6/7, recall at FL 0.01 up on 4/7); the finite-memory onset buys the dependence theorem at almost no cost on
the mean and a worse worst case on small maps.

**Negative: joint onset calibration (`cpc_geo.scj_kappa`, presence AND geometric stop on the null place chain, seeds 3-9
only because `est_n` is cached only there).** Recall +0.003..+0.011 (CMU, countryside), also without the kappa >= 0
floor: the joint null quantile is itself well above 0. The default point is conservative because the map self-replay
null is SAME-condition (stronger evidence than cross-condition off-map queries), not because of the geometric stop or the
floor. A condition-matched null (e.g. cross-traversal pseudo-queries of a multi-session map) is the open fix.

**Baselines (paper-only reimplementations, `literature/BASELINES_2026.md`).** TAO'26 (`analysis/tao.py`), TRAIL'26
(`analysis/trail.py`, d_g transition, leave-one-dataset-out training), VPR auditing'26 (`analysis/vlm_audit.py`,
Qwen2.5-VL-7B offline). Inputs: `analysis/topk_dump.py` (top-100 per seed; GPU; top-1 agrees with the caches 1.000).
First looks: TAO on CMU CosPlace seed 0 ranks well (recall 0.725 at FL 0.000 at the median cost, label-calibrated default
recall 0.947 / FL 0.083); Qwen2.5-VL-7B on 77 Boreas MegaLoc pairs: precision 0.70, FAR 0.52 (CPC-SC+CS on the same frames
0.98 / 0.037).

**Final (all batches; tables `paper/e26_tables.md`, report `paper/BAO_CAO_E26.pdf`, raw `analysis/results/e26/`).**
Route-verification evidence calibrated on the map null (`cpc_theory` 3f): TAO'26 cost of the K = 100 route-anchored
hypotheses, run on the map self-replay null too; its map-null rank p-value is a third presence component (CPC-SC-T).
Designed after seeing CMU CosPlace seeds 0-1 (held-out set; disclosed). Default points, 10 seeds (recall / mean segFAR /
error m):

| rule | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| CPC-SC+CS (Entry 25) | 0.661/0.001/5.1 | 0.537/0.000/4.6 | 0.731/0.002/3.8 | 0.644/0.000/9.6 | 0.709/0.000/11.6 | 0.600/0.000/30.8 | 0.297/0.000/53.1 |
| CPC-SC-T+CS | 0.666/0.001/5.1 | 0.552/0.000/4.6 | 0.749/0.002/3.8 | 0.676/0.000/9.5 | 0.719/0.000/11.6 | 0.614/0.000/30.5 | 0.310/0.000/52.6 |
| CPC-SC-T+SH | 0.670/0.002/5.6 | 0.590/0.001/4.8 | 0.773/0.010/4.4 | 0.692/0.000/9.5 | 0.739/0.000/11.3 | 0.642/0.007/29.7 | 0.324/0.000/51.0 |
| TAO'26 (3-sigma, labels) | 0.801/0.240/46.2 | 0.756/0.707/57.6 | 0.930/0.370/38.4 | 0.805/0.579/187.9 | 0.935/0.740/54.0 | 0.839/0.557/168.4 | 0.769/0.732/95.1 |
| TAO-SC (map-null, ours) | 0.584/0.011/10.1 | 0.400/0.000/11.4 | 0.659/0.066/7.1 | 0.348/0.012/63.8 | 0.630/0.011/18.7 | 0.547/0.008/37.5 | 0.048/0.003/102.3 |

CPC-SC-T+CS is a Pareto improvement over CPC-SC+CS (recall up on 7/7, worst-run segFAR <= 0.023, error equal or lower on
7/7). CPC-SC-T+SH: recall +0.009..+0.053 on 7/7, recall above Xu'21 (labels) on 5/7 (Entry 25: 3/7), mean segFAR <= 0.010
(worst run 0.060 on CMU), error lower than CPC-SC+CS on 4/7. Recall at FL <= 0.01 (seeds 0-2): CPC-SC-T+SH 0.761 / 0.610 /
0.722 / 0.794 / 0.812 / 0.676 / 0.525 (CPC-SC+CS 0.766 / 0.586 / 0.705 / 0.780 / 0.771 / 0.664 / 0.545): higher on 5/7,
pAUC higher on 6/7 (Boreas equal); above Xu'21 7/7, above Claxton'24 and TAO'26 6/7 (both win CMU, ~0.79). False onsets per
off-map segment (Theorem 5 quantity): CPC-SC-T+SH mean 0.002-0.006, worst run <= 0.039 < alpha on 7/7. LODO with the
pre-registered error criterion does not separate the variants (CPC-W+CS+SH chosen in 5/7 folds, regret 0-3.5 m).

Baselines. TAO'26: strong ranking on CMU, its 3-sigma threshold does not transfer (segFAR 0.24-0.74). TAO-SC keeps TAO's
curve but its default point is unstable (CMU worst run 0.76: segment minima over ~70 null segments). TRAIL'26 (MegaLoc,
trained on the other 6 datasets): place ~= MegaLoc top-1 (<= 0.01 apart, Nordland -0.08), label-calibrated threshold
segFAR 0.15-0.29, recall at FL <= 0.01 0.12-0.63. VPR auditing'26 (Qwen2.5-VL-7B, Boreas, every 5th frame, 15.3k frames
per descriptor): P 0.75-0.80, FAR 0.24-0.37, accepts 30-36 % of off-map frames, navigation error 150 m; CPC-SC+CS on the same
frames P 0.99, FAR 0.005-0.023, error 3.0-7.5 m, S 0.840 vs 0.662 (MegaLoc). MegaLoc only (seeds 0-2): Claxton'24 and TAO'26
rank better than CPC-SC-T+SH on Boreas / NCLT / CMU / 4S office; CPC-SC-T+SH wins Nordland / old town / countryside.
GPC (valid under any dependence): FL 0 everywhere, recall at alpha 0.05 only 0.04-0.28 (CPC-SC+CS 0.31-0.84).

## Entry 25 — "Only more conservative?": recall diagnosis, operating curves, odometry-consistency stop (2026-10-31)

**Question (reviewer).** CPC-HMM +TCEmin has low error but also low recall. Is it better, or only more conservative?

**Diagnosis (Boreas + NCLT caches, `analysis/recall_diag.py`).** On-map frames split into hit / place chain wrong /
not yet reported in this on-map run (re-entry) / dropped after reporting (dropout):
- Strong descriptors lose little (Boreas MegaLoc: hit 0.94-0.97). Weak descriptors lose most of it in the PRESENCE chain
  while the place chain is right: Boreas NetVLAD place chain correct on 0.85 of on-map frames, reported 0.30
  (re-entry 0.30, dropout 0.25); Boreas DINOv2: 83 % of on-map frames lie in on-map runs that are never reported
  (whole traversals), although the place chain is correct on 86 % of them.
- Per-frame presence evidence is weak there (AUC dropout-vs-off 0.62-0.88 for every component). The TCE min is the main
  recall cost: NCLT DINOv2 recall 0.16 (TCEmin) vs 0.50 (CPC-HMM), Boreas DINOv2 0.01 vs 0.13.
- First operating curve (NCLT NetVLAD): at CPC-HMM's recall, TCEmin has error 12.9 vs 6.3 m and pAUC 0.490 vs 0.525, so
  relative to CPC-HMM, TCEmin IS mostly a more conservative point on a slightly worse curve; both are far above the
  baselines (Claxton'24 pAUC 0.37, SelfCal frame 0.31, max-sim 0.02).
- Tried and dropped on the development sets: hedged two-group e-values 1 - l + l e (recall +0.006 / +0.02);
  process-averaged e-detectors (small gain); TCE min on one component only (moves along the trade-off); hysteresis
  TCEmin onset / CPC persistence (moves along the trade-off); CPC-SC = CPC chain + segment-calibrated onset threshold:
  the ONSET part holds (segments with a false onset 0.010-0.041 <= alpha), but CARRIED report streaks (place chain stuck
  at the map edge or jumped to a look-alike place, presence chain still on) give segFAR up to 0.10.
- Predictive cell rank (PCR, IPDA-style gate at the place chain's predicted place, `analysis/pcr.py`, `nav_demo --pred`):
  under H0 the predicted place is also the top cell in 62 % of frames (CMU CosPlace null 0.624, off-map queries 0.606,
  on-map 0.968): consecutive frames are near-duplicates, so the chain follows the top-1 whether on or off the map. The
  null calibration matches (null ~ off-map), but the likelihood ratio is only ~1.5. Kept as an exploratory variant.

**New module: odometry-consistency stop (CS).** Stop reporting at frame t when, for a lag k whose odometry path is
<= 3 excl, | ||m_t - m_{t-k}|| - ||o_t - o_{t-k}|| | > excl (m = reported place). Leaving the map makes the place chain
(no off-map state) stick at the edge or jump; magnitudes only, so heading drift (NCLT) does not trigger it. It only
removes reports, so it cannot raise segFAR or FL (it can split a false streak into two onsets, so an onset-count ARL0 is
not covered).

**Held-out result (pre-registered protocol; default points, 6 descriptors x 3 seeds = 18 runs per dataset; recall /
segFAR / error m).**

| rule | Boreas* | NCLT* | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (labels) | 0.62/0.028/22.6 | 0.53/0.021/13.7 | 0.65/0.127/13.0 | 0.73/0.040/68.0 | 0.76/0.284/22.7 | 0.60/0.030/76.9 | 0.31/0.095/76.0 |
| Claxton'24 (labels) | 0.74/0.111/43.6 | 0.66/0.213/33.2 | 0.85/0.111/14.5 | 0.51/0.288/90.0 | 0.80/0.160/18.0 | 0.71/0.142/100.7 | 0.59/0.201/41.7 |
| certified | 0.66/0.039/15.7 | 0.48/0.001/3.7 | 0.65/0.012/3.8 | 0.57/0.039/17.2 | 0.66/0.018/11.3 | 0.53/0.016/37.0 | 0.22/0.018/51.5 |
| TCEmin (Entry 24 method) | 0.66/0.013/8.9 | 0.49/0.000/3.7 | 0.68/0.009/3.5 | 0.56/0.002/16.2 | 0.71/0.017/12.5 | 0.58/0.007/36.3 | 0.23/0.012/59.8 |
| CPC-HMM (no TCE) | 0.73/0.066/17.7 | 0.64/0.005/7.9 | 0.80/0.040/5.7 | 0.69/0.009/19.7 | 0.81/0.069/12.8 | 0.70/0.038/46.3 | 0.36/0.069/52.2 |
| CPC-HMM+CS | 0.67/0.004/5.2 | 0.55/0.000/4.6 | 0.70/0.006/4.6 | 0.63/0.000/11.7 | 0.72/0.000/11.5 | 0.59/0.000/31.6 | 0.31/0.000/54.6 |
| **CPC-SC+CS** | 0.66/0.003/5.3 | 0.54/0.000/4.6 | 0.66/0.001/3.7 | 0.64/0.000/11.6 | 0.71/0.000/12.1 | 0.58/0.000/32.8 | 0.30/0.000/54.3 |
| oracle | 0.89/-/2.3 | 0.72/-/2.2 | 0.91/-/2.9 | 0.66/-/5.4 | 0.91/-/8.4 | 0.84/-/21.1 | 0.73/-/17.8 |

\*development sets. Replacing the TCE min by the CS stop (CPC-HMM+CS vs TCEmin) raises recall on 7/7 datasets
(Nordland +0.07, countryside +0.09, NCLT +0.06, others +0.01), lowers mean segFAR on 6/7 (NCLT both 0; worst run 0.021
vs 0.138) and lowers the error on 5/7 (CMU +1.1 m, NCLT +0.9 m). CPC-SC+CS (onset threshold calibrated on the map null)
is slightly more conservative than CPC-HMM+CS (recall -0.00 to -0.03 except Nordland +0.01; CMU error 3.7 vs 4.6 m);
against TCEmin its recall is higher on NCLT / Nordland / countryside (+0.05 / +0.08 / +0.07) and within -0.02 elsewhere.
Against Xu'21 (labels), both CS rules have 1.4-5.9x lower error and segFAR ~0 on 7/7 (Xu'21: 0.021-0.284). Recall:
CPC-HMM+CS is higher on Boreas / NCLT / CMU, within 0.005 on old town / countryside, lower on Nordland (-0.10) and 4S office
(-0.05); CPC-SC+CS is higher on Boreas / NCLT / CMU, -0.02 on old town / countryside, -0.09 / -0.06 on Nordland / office.

**Leave-one-dataset-out choice** (`analysis/lodo_select.py`, 15 label-free variants: segFAR <= 0.05 on every other
dataset, then lowest mean error / oracle error): CPC-SC+CS is chosen for 6/7 held-out datasets, CPC-HMM+CS for CMU; regret
0-3.5 m (Entry 24: TCEmin, regret up to 30 m). Adopted rule: **CPC-SC+CS** (`analysis/cpc_sc.py`, also in `nav_rules.py`).

**Negative results kept.** W-CPC (finite-memory chain + segment calibration, W = 10 / 20): Boreas segFAR 0.030 (worst
0.099), same failure as `certified` there: the map self-replay null under-represents the dependence of long off-map
excursions. PCR: FL 0.35-0.63; besides the weak likelihood ratio, a scale bug (masked own-block cells make null rank-1
values larger than query rank-1 values); not pursued. Place-chain confidence as a second gate: no change (overconfident).

**Operating curves (all 7 datasets, 114 runs; `oc_curves.py`, tables `paper/oc_tables.md`, raw curves
`results/oc_curves_entry25.tgz`).** Every rule's own threshold is swept; labels only evaluate. Recall at FL <= 0.01:

| rule | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (labels) | 0.562 | 0.526 | 0.592 | 0.624 | 0.537 | 0.555 | 0.181 |
| Claxton'24 (labels) | 0.687 | 0.574 | **0.793** | 0.439 | 0.749 | 0.644 | 0.420 |
| max-sim (labels) | 0.594 | 0.495 | 0.752 | 0.112 | 0.655 | 0.582 | 0.191 |
| certified | 0.674 | 0.588 | 0.729 | 0.573 | 0.731 | 0.595 | 0.262 |
| TCEmin (Entry 24) | 0.692 | 0.590 | 0.713 | 0.619 | 0.733 | 0.616 | 0.245 |
| CPC-HMM | 0.688 | **0.645** | 0.747 | 0.693 | 0.722 | 0.622 | 0.236 |
| **CPC-SC+CS** | **0.766** | 0.586 | 0.705 | **0.780** | **0.771** | **0.664** | **0.545** |

At the same false-report rate CPC-SC+CS finds more correct fixes than Xu'21 on 7/7 datasets and than the
label-trained Claxton'24 on 6/7 (exception CMU). At segFAR <= 0.025: 6/7 vs both (NCLT -0.006 vs Xu'21, CMU vs
Claxton'24). pAUC (mean recall over FL in [0, 0.05]): 7/7 vs Xu'21 but only 4/7 vs Claxton'24 (NCLT -0.004, CMU,
old town -0.015): the advantage is in the low-false-report regime. So the new rule is not a more conservative point on
the same curve. Two exceptions, kept: on CMU (strong descriptors, easy data) Claxton'24 and
even the raw max-sim score rank frames better than every presence chain; on NCLT the CS stop removes correct frames and
CPC-HMM without CS has the best curve. The large gains (countryside x3 vs Xu'21, Nordland +0.16, Boreas +0.20) come from
the odometry-consistency stop: on 4S countryside the best recall at FL <= 0.01 of every "+CS" rule is reached with a
presence threshold of only P(on) ~ 0.02, i.e. CS alone removes almost all off-map reports.

**Exact matched points** (`oc_matched.py`: Kalman at the exact matched threshold; the interpolated error of oc_summary
was unreliable because the error is not monotone along a curve). CPC-SC+CS placed at Xu'21's own default FL: recall
+0.197 (17/18 runs) countryside, +0.128 (16/18) Boreas, +0.040 Nordland, +0.038 old town, +0.021 office, -0.043 CMU,
-0.026 NCLT; error lower on 6/7. In the high-FL regime (FL 3-8 %, Claxton'24's default) Claxton'24 has more recall on
5/7 datasets (all but Boreas, Nordland), at segFAR 0.11-0.27.

**Sensitivity (default points).** CS span 2 / 4 excl: recall +0.02-0.04 / -0.01-0.04, segFAR <= 0.014 everywhere;
threshold 0.75 / 1.25 excl: small changes; alpha 0.1: as 0.05; alpha 0.01: recall 0 on CMU / office (old town 0.19,
countryside 0.18)
because the map null has fewer than 1/alpha - 1 = 99 segments, so the conformal quantile is infinite: CPC-SC needs enough
null segments for small alpha (a limitation to report).

**Hole ratio 10 % / 50 % (same constants; `nav_demo --drop`; 6 descriptors x 3 seeds).** recall / segFAR / error m:

| | CMU | Nordland | 4S office | 4S old town | 4S countryside | Boreas |
|---|---|---|---|---|---|---|
| 10 %: Xu'21 (labels) | 0.70/0.047/5.6 | 0.75/0.027/29.3 | 0.73/0.145/12.4 | 0.65/0.072/37.5 | 0.28/0.093/60.1 | 0.77/0.076/19.9 |
| 10 %: TCEmin | 0.74/0.012/3.0 | 0.56/0.000/13.0 | 0.70/0.013/12.0 | 0.60/0.007/28.5 | 0.20/0.003/55.9 | 0.65/0.007/4.8 |
| 10 %: CPC-SC+CS | 0.76/0.001/3.0 | 0.65/0.000/10.7 | 0.72/0.000/9.5 | 0.64/0.000/26.0 | 0.31/0.000/50.4 | 0.69/0.000/4.4 |
| 50 %: Xu'21 (labels) | 0.57/0.080/21.9 | 0.75/0.037/121.5 | 0.79/0.381/56.0 | 0.56/0.029/98.8 | 0.27/0.221/156.2 | 0.71/0.027/32.1 |
| 50 %: TCEmin | 0.63/0.017/6.3 | 0.59/0.002/18.4 | 0.70/0.023/16.8 | 0.54/0.004/50.3 | 0.17/0.032/73.0 | 0.63/0.002/5.9 |
| 50 %: CPC-SC+CS | 0.61/0.012/6.9 | 0.67/0.000/13.7 | 0.70/0.000/15.5 | 0.57/0.000/41.0 | 0.25/0.001/59.5 | 0.60/0.000/5.8 |

segFAR <= 0.012 at every hole ratio; error below Xu'21 everywhere (10 %: 1.2-4.5x, 50 %: 2.4-8.9x); against TCEmin higher recall at 10 %
on 6/6, at 50 % higher on Nordland / old town / countryside and lower on Boreas / CMU (-0.03 / -0.02). The first
10 / 50 % runs silently used 30 % holes (hmm_fix strips --drop at import, fixed); 3 Boreas jobs at 10 % were killed
by memory (two 8448-d descriptors per T4 session) and were rerun one per session.

**10 seeds (seeds 3-9 added; default points; 60 runs per dataset, NCLT 6; 366 runs).** recall / segFAR / error m:

| rule | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (labels) | 0.68/0.043/25.3 | 0.53/0.021/13.7 | 0.69/0.227/18.1 | 0.74/0.038/59.3 | 0.72/0.215/21.2 | 0.62/0.101/70.9 | 0.25/0.088/81.0 |
| TCEmin | 0.66/0.008/6.4 | 0.49/0.000/3.7 | 0.75/0.018/3.9 | 0.57/0.002/13.0 | 0.70/0.013/12.5 | 0.59/0.008/33.7 | 0.21/0.010/59.1 |
| CPC-SC+CS | 0.66/0.001/5.1 | 0.54/0.000/4.6 | 0.73/0.002/3.8 | 0.64/0.000/9.6 | 0.71/0.000/11.6 | 0.60/0.000/30.8 | 0.30/0.000/53.1 |

Worst single-run segFAR of CPC-SC+CS: 0.021 (all 366 runs below alpha = 0.05); TCEmin up to 0.171, Xu'21 up to 1.0.
Against TCEmin: recall higher on 5/7 (CMU -0.02, Boreas equal), segFAR lower or equal on 7/7, error lower on 6/7 (NCLT
+0.9 m). Against Xu'21: error 1.5-6.2x lower on 7/7; recall higher on 3/7, lower on 4/7 (Nordland -0.10, others <= 0.02).

**Joint calibration of presence AND CS on the map null (`cpc_sc.cs_cal`, null place chain `est_n`): negative.** The
null replay passes CS 2.6x more often than real off-map queries (CMU CosPlace: 0.229 vs 0.088; exact map odometry and
same-condition images make the null track look-alikes more coherently), so the jointly calibrated threshold is MORE
conservative (recall 0.64 vs 0.72). The default point of CPC-SC+CS therefore stays conservative relative to its own
curve (countryside: 0.30 at FL 0.000 vs 0.55 at FL 0.01); a valid but less conservative null for CS is open.

**Pre-registered protocol (written before the held-out results).** Development sets: Boreas, NCLT (seen). Held-out:
CMU, Nordland, 4S office / old town / countryside. Candidates: M1 TCEmin, M2 TCEmin+CS, M3 CPC-HMM+CS, M4 CPC-SC+CS;
CS span 3 excl, threshold excl (span off_d/excl was dropped: Boreas MegaLoc segFAR 0.057). Order of criteria: mean
segFAR <= 0.05 per dataset, then error and recall at the default point, then recall at matched FL / segFAR and error at
matched recall (operating curves, `analysis/oc_curves.py`, `oc_summary.py`).

## Entry 24 — Self-audit: is the method general, or tuned to these datasets? NCLT as a hold-out (2026-10-30)

**Question (user).** Is the proposed method sound and general, or do the scores come from choices fitted to these
datasets?

**Known risks before the check.** (1) The ghost-gate floor rho = 0.1 was picked after the Nordland lock-out. (2) There are
many variants (CPC, +GG, +TCEmin, +TCEmin+GG, certified, +DRgate); picking the best per dataset is selection bias.
(3) Constants (KAPPA, p_in/p_out, s0, TCE bins) had little sensitivity analysis.

**Check 1: NCLT as a true hold-out** (designed and frozen before NCLT was loaded; map 2012-01-08, query 2013-04-05,
natural off-map 14% of frames, no synthetic holes, 6 descriptors, 1 seed, 53 off-map segments). NCLT-specific
code is limited to the evaluation (config by robot scale: excl 10 m; heading-offset EKF tracker and FOG heading for every rule,
because the Segway heading drifts 10-25 deg per session and a position-only filter lags 20-40 m even with perfect fixes).

| rule | err | p95 | recall | segFAR |
|---|---|---|---|---|
| Xu'21 (labels) | 37.5 | 173.0 | 0.55 | 0.057 |
| Claxton'24 (labels) | 21.6 | 87.2 | 0.56 | 0.079 |
| SelfCal frame | 9.1 | 42.2 | 0.28 | 0.006 |
| certified | 6.8 | 22.1 | 0.42 | 0.003 |
| CPC-HMM | 13.2 | 53.1 | 0.56 | 0.013 |
| CPC-HMM +GG | 11.4 | 51.3 | 0.53 | 0.009 |
| CPC-HMM +TCEmin | 7.2 | 25.4 | 0.43 | 0 |
| CPC-HMM +TCEmin+GG | 7.5 | 26.2 | 0.39 | 0 |
| oracle | 4.9 | 13.1 | 0.62 | 0 |

The DRgate versions of the baselines lock out on NCLT (Xu +DRgate 199 m): a hard dead-reckoning gate is fragile with
drifting heading.

**Check 1b: NCLT, all 8 query sessions** (2012-02 to 2013-04 against the 2012-01-08 map; 38,919 query frames, 3-14%
off-map per session, 306 off-map segments; 6 descriptors x 3 seeds, but without synthetic holes the seeds only change
the Claxton'24 MLP, so this is 6 independent runs; frozen method, nothing tuned on NCLT):

| rule | err | median | p95 | recall | segFAR |
|---|---|---|---|---|---|
| accept all | 70.9 | 28.5 | 294.5 | 0.72 | 1.000 |
| Xu'21 (labels) | 13.7 | 2.5 | 69.8 | 0.53 | 0.021 |
| Claxton'24 (labels) | 33.3 | 9.9 | 154.1 | 0.66 | 0.214 |
| SelfCal frame | 9.2 | 2.3 | 46.6 | 0.31 | 0.005 |
| certified | 3.6 | 1.6 | 11.7 | 0.48 | 0.001 |
| CPC-HMM | 7.9 | 2.1 | 31.5 | 0.64 | 0.005 |
| CPC-HMM +GG | 6.2 | 2.2 | 23.3 | 0.61 | 0.005 |
| **CPC-HMM +TCEmin** | **3.7** | 2.0 | 13.2 | 0.49 | **0** |
| CPC-HMM +TCEmin+GG | 4.4 | 2.0 | 16.8 | 0.46 | 0 |
| oracle | 2.2 | 1.4 | 7.1 | 0.72 | 0 |

TCEmin is within 0.3-1.8 m of the oracle error with every descriptor except DINOv2 (7.3 vs 2.4 m) and has no false
report in any of the 306 off-map segments; Xu'21 is 3.7x worse in error, Claxton'24 9x (mean segFAR 0.21: its MLP,
trained on two benign sessions, accepts many off-map frames). The 1-session table above was an early subset.

**Check 2: all 7 datasets, every seed** (10 seeds except NCLT; err / recall / segFAR):

| dataset | Xu'21 | Claxton'24 | cert | CPC+GG | TCEmin | TCEmin+GG | oracle |
|---|---|---|---|---|---|---|---|
| Boreas | 25.3/0.68/0.043 | 43.6/0.74/0.111 | 8.5/0.65/0.022 | 6.6/0.72/0.016 | 6.4/0.66/0.008 | **5.1**/0.66/0.002 | 2.1 |
| 4S countryside | 81.0/0.25/0.088 | 90.7/0.25/0.232 | **52.5**/0.20/0.013 | 53.7/0.35/0.042 | 59.1/0.21/0.010 | 69.2/0.19/0.008 | 16.5 |
| 4S office | 21.2/0.72/0.215 | 39.4/0.60/0.424 | **11.2**/0.66/0.016 | 11.8/0.81/0.046 | 12.5/0.70/0.013 | 12.9/0.69/0.007 | 8.3 |
| 4S old town | 70.9/0.62/0.101 | 234.8/0.55/0.373 | **33.1**/0.54/0.015 | 41.2/0.68/0.021 | 33.7/0.59/0.008 | 63.4/0.49/0.003 | 19.4 |
| Nordland | 59.3/0.74/0.038 | 159.1/0.26/0.285 | 12.7/0.58/0.025 | 14.5/0.68/0.006 | 13.0/0.57/0.002 | **12.5**/0.56/0.001 | 4.8 |
| CMU | 18.1/0.69/0.227 | 33.3/0.66/0.386 | 4.2/0.69/0.025 | 6.5/0.84/0.047 | 3.9/0.75/0.018 | **3.8**/0.74/0.015 | 3.0 |
| NCLT | 37.5/0.55/0.057 | 21.6/0.56/0.079 | **6.8**/0.42/0.003 | 11.4/0.53/0.009 | 7.2/0.43/0 | 7.5/0.39/0 | 4.9 |

**Check 3: leave-one-dataset-out variant choice** (pick the variant on the other 6 datasets: mean error / oracle error,
segFAR <= 0.05; regret = held-out error minus the best variant on the held-out dataset): the pick is TCEmin for 6 of the
7 held-out datasets (regret 0.1-6.6 m); with old town held out it is TCEmin+GG (regret 30 m).

**Check 4: one-at-a-time sensitivity** of TCEmin+GG (`nav_sensitivity.py`, Boreas 18 runs and NCLT 6 runs; each constant
x1/3 and x3 around the default): rho 0.03-0.3, p_in = p_out 0.003-0.03, s0 0.5-2 excl, KAPPA 0.02-0.1, TCE bins
4x3-8x6 change the mean error by <= 0.7 m and segFAR by <= 0.002. Only the P(on) threshold matters (0.3 -> Boreas 34.5 m,
segFAR 0.14); 0.5 is the MAP decision of the presence chain, not a tuned value.

**Verdict.**
- General and well founded: the validity part. With alpha fixed at 0.05 and no tuning, certified and TCEmin keep segFAR
  <= 0.025 on 7/7 datasets, including the hold-out. Plain CPC-HMM violates it on 3/7 (0.055-0.067), which is exactly
  the case the TCE theory predicts (dependent evidence). All label-free rules beat the label-calibrated baselines on 7/7
  datasets in error and segFAR.
- Not general: the ghost gate. It was designed after the Boreas diagnosis, helps on Boreas, and locks out on 4Seasons
  old town / countryside (+30 / +10 m) and on NCLT. It must be an optional module, not part of the main method.
- Modest: TCEmin vs certified. TCEmin has higher recall (+0.01 to +0.05) and lower segFAR on every dataset, but the error is
  about the same (better on Boreas / CMU, worse by 0.3-6.6 m on the others). The gain of the HMM machinery is recall and
  validity, not error.
- Constants are not fragile (Check 4); per-dataset choices are the physical tolerance excl (vehicle 25 m, train 5 m,
  robot 10 m) and the evaluation tracker.
- Main method from now on: CPC-HMM +TCEmin (the leave-one-out choice). Open: GG lock-out (needs a valid re-acquisition
  step), recall gap to the oracle (0.21 vs 0.73 on countryside), stronger baseline protocols (our Claxton'24 / SafeVPR
  re-implementations are calibrated on two benign conditions only), NCLT with all 8 query sessions.

## Entry 23 — TCE/TCEmin across 6 datasets, Boreas on 10 seeds, label-calibrated baselines SafeVPR / Claxton'24 (2026-10-30)

**Hypothesis.** The map-calibrated e-values of CPC-HMM assume that consecutive query frames are independent given the
state, which is false: evidence is autocorrelated. TCE (Mondrian conformal p-values conditioned on the previous evidence
state, from map self-replay null pairs; `paper/cpc_theory.md` §3c, Lemma 5) removes the first-order dependence. TCEmin
(componentwise min of marginal and TCE e-values, Lemma 6) is valid if EITHER independence OR transition exchangeability
holds. Theorem 3 bounds P(any false report during an off-map excursion of length L) by p_in/(1-p_in)·(R0 + L).

**navT2** (6 datasets × 6 descriptors × 3 seeds; mean err m / recall / segFAR):

| dataset | Xu'21 (labels) | certified | CPC-HMM | +GG | +TCEmin | oracle |
|---|---|---|---|---|---|---|
| Boreas | 22.6/0.62/0.028 | 15.7/0.66/0.039 | 17.7/0.73/0.066 | 7.1/0.72/0.023 | 8.9/0.66/0.013 | 2.3 |
| 4S countryside | 76.0/0.31/0.095 | 51.5/0.22/0.018 | 52.2/0.36/0.069 | 52.3/0.35/0.052 | 59.8/0.23/0.012 | 17.8 |
| 4S office | 22.7/0.76/0.284 | 11.3/0.66/0.018 | 12.8/0.81/0.069 | 11.6/0.80/0.047 | 12.5/0.71/0.017 | 8.4 |
| 4S old town | 76.9/0.60/0.030 | 37.0/0.53/0.016 | 46.3/0.70/0.038 | 43.3/0.67/0.016 | 36.3/0.58/0.007 | 21.1 |
| Nordland | 68.0/0.73/0.040 | 17.2/0.57/0.039 | 19.7/0.69/0.009 | 19.1/0.68/0.007 | 16.2/0.56/0.002 | 5.4 |
| CMU | 13.0/0.65/0.127 | 3.8/0.65/0.012 | 5.7/0.80/0.040 | 5.5/0.79/0.029 | 3.5/0.68/0.009 | 2.9 |

TCEmin has the lowest segFAR on all 6 datasets and the best error on 3/6; its recall is about that of `certified` (the
price of the min). It is weaker on countryside and office. TCE alone is liberal on CMU (segFAR 0.156), hence the min.

**Boreas, 10 seeds** (navC seeds 0-2 + navS seeds 3-9, 6 descriptors; err / p95 / recall / segFAR; sd over seeds of the
descriptor-mean error):

| rule | err | p95 | recall | segFAR | sd(seed) |
|---|---|---|---|---|---|
| Xu'21 HMM off-map (labels) | 25.3 | 165.6 | 0.684 | 0.043 | 7.10 |
| Xu'21 +DRgate | 15.8 | 117.8 | 0.669 | 0.022 | 6.96 |
| certified | 8.5 | 45.7 | 0.651 | 0.022 | 8.58 |
| certified +DRgate | 4.8 | 22.1 | 0.645 | 0.004 | 0.54 |
| CPC-HMM | 11.3 | 66.6 | 0.725 | 0.042 | 6.52 |
| CPC-HMM +GG | 6.6 | 33.8 | 0.723 | 0.016 | 1.33 |
| CPC-HMM +TCEmin | 6.4 | 34.3 | 0.658 | 0.008 | 3.07 |
| **CPC-HMM +TCEmin+GG** | **5.1** | **21.1** | 0.657 | **0.002** | **0.34** |
| oracle | 2.1 | 6.5 | 0.879 | 0 | 0.22 |

On seeds 0-2 the means are higher (17.7 for CPC-HMM): seed 0-2 contain the hard Boreas seeds, so 3-seed tables overstate
the error. TCEmin+GG is the most stable rule (sd 0.34 m across seeds) and the only one with segFAR <= 0.002.

**Label-calibrated baselines on Boreas** (seeds 0-2, 6 descriptors, calibrated WITH labels on the same `bsel` frames):

| rule | err | p95 | recall | segFAR | FL |
|---|---|---|---|---|---|
| SafeVPR (MNN patch + Mondrian LTT) | 20.8 | 143.4 | 0.604 | 0.046 | 0.018 |
| SafeVPR +DRgate | 13.5 | 69.6 | 0.556 | 0.003 | 0.001 |
| Claxton'24 MLP | 43.6 | 207.9 | 0.738 | 0.111 | 0.033 |
| Claxton'24 +DRgate | 24.2 | 128.7 | 0.647 | 0.011 | 0.005 |
| CPC-HMM +TCEmin+GG (label-free) | 5.2 | 20.9 | 0.661 | 0.002 | 0.002 |

Claxton'24 is excellent with strong descriptors (MegaLoc 2.8 m, SALAD 3.5 m, recall 0.85-0.92) but collapses with
NetVLAD/DINOv2 (102-220 m): an MLP trained on in-tolerance labels does not transfer to the off-map frames, which the
calibration traversal under-represents. SafeVPR only scores candidates in its own global top-20 (the HMM's top is
there for 71% of frames), so its accepted set is small and conservative.

**Two bugs fixed before these numbers.** (1) `ltt_threshold` ran the fixed-sequence test over every unique score from the
strictest; at n = 1 even zero errors give binom.cdf = 0.95 > delta/3, so the sequence stopped at once and SafeVPR
accepted nothing (recall 0 in the raw navC output). The sequence now starts at the first threshold with
n >= log(delta)/log(1-alpha). The order depends only on the scores, so validity is kept. (2) `nav_rules.py` lost
`--safevpr` because `nav_demo` strips it from sys.argv on import; it now reads `N.SAFEVPR`. The SafeVPR rules in
`results/nav_boreas_<desc>.json` were re-evaluated from the caches (all other rules reproduce exactly).

**Public reusable datasets.** `nhatlong1103/hmm-navcache` (18 Boreas caches, every rule re-evaluates from them in about
1 min with `nav_rules.py`), `vpr-safevpr-scores`, `boreas-vpr-images-5`.

**NCLT (natural off-map).** Stage 1 is streaming the 114 GB image tarballs (Cam5, 640 px, frames >= 1 m apart). 2012-11-16
died on a dropped S3 connection under the old curl pipe and was relaunched with the resumable Range reader;
2012-01-08 and 2013-04-05 are done (outputs being re-pulled after a container restart).

**Verdict.** TCEmin+GG is the strongest and most stable rule on Boreas, ahead of every label-calibrated baseline,
including the two 2024-2026 integrity monitors. Open: TCEmin recall (≈ certified, about 0.07 below CPC-HMM) and the
countryside dataset.

## Entry 22 — Full Boreas results, the real cause of far wrong fixes, dead-reckoning ghost gate (2026-10-29, night)

**Pulled** (new chat, branch `hmm-navigation-2`): fix7 (14 kernels), navF, navFc, navG, bfix. Every Boreas result now
uses the fixed odometry, 6 descriptors, 3 seeds.

**Boreas with all 6 descriptors** (`nav_demo`, mean navigation error, m):

| | MegaLoc | SALAD | MixVPR | CosPlace | NetVLAD | DINOv2 | mean |
|---|---|---|---|---|---|---|---|
| Xu'21 (labels) | **7.0** | **5.0** | 5.5 | **7.4** | 38.8 | 71.6 | 22.6 |
| CPC-HMM | 34.1 | 12.7 | 9.7 | 27.6 | 11.6 | 10.2 | 17.7 |
| CPC-HMM p_out = 0.2 | 14.9 | 6.9 | 6.8 | 12.1 | 8.1 | 11.3 | 10.0 |
| certified | 39.1 | 9.6 | **5.1** | 23.6 | **8.1** | **8.4** | 15.7 |

- Averaged over descriptors, CPC-HMM no longer loses to Xu'21 on Boreas: Xu'21 breaks on NetVLAD/DINOv2. On the 4 strong
  descriptors Xu'21 still wins.
- `hmm_fix` (fix7, its own Kalman metric): Boreas Xu'21 40.3 vs CPC 28.2; RobotCar `cpc_pred` 0.73 vs Xu'21 1.28.
- A constant p_out does not transfer: p_out = 0.05 helps Nordland (19.7 → 14.5) but hurts 4S countryside (52.2 → 61.4).
  The p_out derived from KL₀ alone (lag ≤ L frames) kills countryside recall (0.51 → 0.02). Rejected.

**Root cause of the Boreas loss (offline, `navframes_*.npz`).**

- The false locations are NOT mainly exit lag: 47–72 % of FL frames are > 100 frames after the last on-map frame, deep in
  holes. An oracle p_out = 0.6 placed exactly at the map edge leaves FL unchanged.
- CPC-HMM's wrong fixes are FAR: median 111–182 m, p90 up to 954 m. Xu'21's are 37–56 m (gray zone at the edges).
- Mechanism: in a hole the place chain (no off-map state) drifts to an aliased stretch Y; the MAP-agreement gate then
  always passes, and weak but dependent evidence (p ≈ 0.15 for many frames) accumulates into a false onset.

**Tried and rejected: predictive gate (+PG) and dead-reckoned re-entry state (+DR)** (`cpc_joint`, navH/navHc).
Neutral everywhere (Boreas CosPlace 27.6 → 24.3, countryside 52.2 → 51.9). Reason: inside a hole P(on) hovers at a few %
≫ p_in, so the on-conditioned place chain keeps its memory and drifts to Y by itself; re-entry mass never matters.

**New: dead-reckoning ghost gate (+GG).** While no place is reported, the top-1 e-value counts with weight
g = exp(−d²/2s²), d = |m_top − ghost|, ghost = last reported fix + odometry, s = excl + 0.05·path. Still an e-value
(Lemma 4: a ≤ ẽ ≤ e), so ARL₀ is unchanged. Offline upper-bound test (GT lower bound on d): Boreas sum of wrong-fix error
CosPlace 308k → 9k m, MegaLoc 286k → 19k, SALAD 159k → 38k, recall unchanged; countryside slightly better. Implemented
without GT in `nav_demo` (+GG, +GG+DR). Fair baselines: the same gate post hoc on Xu'21 / SelfCal / certified
(`+DRgate`). Running: navI (Boreas 6 desc + 4S ×3 + Nordland + CMU).

**Final run (navJ/navJc, ghost gate with floor ρ = 0.1, 6 datasets × 6 descriptors × 3 seeds; `nav_demo`, mean navigation
error, m; Nordland frames):**

| Dataset | Xu'21 (labels) | Xu'21 + DR gate | certified | certified + DR gate | CPC-HMM | CPC +GG ρ=.01 | **CPC +GG ρ=.1** |
|---|---|---|---|---|---|---|---|
| Boreas | 22.6 | 12.5 | 15.7 | **4.8** | 17.7 | 8.0 | 7.1 |
| 4S countryside | 76.0 | 73.1 | **51.5** | 69.7 | 52.2 | 53.8 | 52.3 |
| 4S office | 22.7 | 32.0 | **11.3** | 11.2 | 12.8 | 12.3 | 11.6 |
| 4S old town | 76.9 | 140.4 | **37.0** | 87.3 | 46.3 | 102.0 | 43.3 |
| CMU | 13.0 | 10.1 | **3.8** | 4.1 | 5.7 | 6.2 | 5.5 |
| Nordland | 68.0 | 281.2 | **17.2** | 39.0 | 19.7 | 63.4 | 19.1 |

Boreas per descriptor (CPC +GG vs Xu'21, m): MegaLoc 5.3 vs 7.0, SALAD 3.4 vs 5.0, MixVPR 5.0 vs 5.5, CosPlace 5.5 vs 7.4,
NetVLAD 11.7 vs 38.8, DINOv2 11.5 vs 71.6. CPC +GG keeps 28–40 % more correct fixes than Xu'21 on the strong descriptors.

**Verdict.**

- **The Boreas loss is fixed:** CPC-HMM +GG beats Xu'21 on 6/6 Boreas descriptors (mean 7.1 vs 22.6 m) and on the mean of
  every dataset, with one label-free configuration. The handoff's stopping criterion for Step 1 is met.
- **The gate never hurts CPC-HMM:** −10.6 m on Boreas, −3.0 old town, −1.2 office, −0.6 Nordland, −0.2 CMU, +0.1 countryside.
- **The floor matters:** ρ = 0.01 locks out after a wrong report (old town 102.0, Nordland 63.4).
- **The same gate used post hoc (hard, no escape) is unsafe:** it is the best rule on Boreas (certified + DR gate 4.8 m;
  near-GT odometry) but breaks every other dataset (old town 37.0 → 87.3, Nordland 17.2 → 39.0, Xu'21 Nordland 68 → 281).
  CPC +GG is the only rule that gains on Boreas without losing elsewhere.
- **Honest limits:** certified (ungated) is still slightly better than CPC +GG on 5/6 datasets; CPC +GG wins only on
  Boreas among the label-free rules that are safe everywhere. ρ = 0.1 was chosen after looking at Boreas/Nordland
  (offline), then fixed. RobotCar is not in the navigation grid (9-frame snippets). `hmm_fix` (ARL₀, recall) has not been
  re-run with +GG; ARL₀ is covered by Lemma 4.

**ρ sensitivity (navK/navKc, ρ ∈ {0.01, 0.03, 0.1, 0.3}, mean navigation error):**

| Dataset | CPC | ρ=0.01 | ρ=0.03 | ρ=0.1 | ρ=0.3 | Xu'21 |
|---|---|---|---|---|---|---|
| 4S countryside | 52.2 | 53.8 | 52.7 | 52.3 | 51.8 | 76.0 |
| 4S office | 12.8 | 12.3 | 12.0 | 11.6 | 12.0 | 22.7 |
| 4S old town | 46.3 | 102.0 | 62.0 | 43.3 | 38.4 | 76.9 |
| Nordland | 19.7 | 63.4 | 20.8 | 19.1 | 19.4 | 68.0 |
| CMU | 5.7 | 6.2 | 6.2 | 5.5 | 5.5 | 13.0 |
| Boreas MegaLoc / SALAD / CosPlace | 34.1 / 12.7 / 27.6 | 7.0 / 3.4 / 9.1 | 5.4 / 3.4 / 5.4 | 5.3 / 3.4 / 5.5 | 8.3 / 5.1 / 9.4 | 7.0 / 5.0 / 7.4 |

- Trade-off: small ρ locks out (old town, Nordland); ρ = 0.3 is best off Boreas but on Boreas loses to Xu'21 on MegaLoc
  and CosPlace. No single ρ is best everywhere; ρ = 0.1 (fixed before this grid) is the balance point.
- **Correction:** "the gate never hurts" holds for per-dataset means only. Per descriptor, 4S old town DINOv2 48.9 → 73.8 m
  and NetVLAD 35.4 → 45.6 m at ρ = 0.1 (CosPlace 116.9 → 65.9 m compensates).

## Entry 21 — Boreas failure analysis, CPC-HMM theory, asymmetric presence switching (2026-10-29, evening)

**Theory** (`paper/cpc_theory.md`):

- Predictable e-values.
- The gate, the tempering and the average all preserve the e-value property.
- **Theorem:** the presence odds are dominated by a Shiryaev–Roberts e-detector, so ARL₀ ≥ (1−p_in)/p_in − R₀ whenever
  p_out ≥ p_in.
- The re-entry delay is ≈ log((1−p)/p)/KL₁.
- **Lemma (Anderson):** a noise-free odometry null is conservative.

**Empirical ARL₀** (fix5) is 762–3930 frames on the long-sequence datasets, all above the bound of 98. Xu'21 gets 41 on
CMU.

**Boreas root causes** (`nav_demo --dump`, offline `analysis/navdiag.py`):

1. **Data bug.** The wheel-pulse counter has one discontinuity in 4/13 sequences, a single step of 8.7 km. It broke the
   place chain: 2 % correct while top-1 was 99 % correct.
   - Fixed in `cert_seq.odometry_wheel`.
   - Every Boreas result before 14:00 UTC is void.
   - After the fix, CPC-HMM navigation error: MegaLoc 107 → 34 m, SALAD 58 → 12.7 m. Xu'21 still has 7.0 / 5.0 m.
2. **Remaining FL 0.07–0.085 is mostly the EXIT LAG of the presence chain, not false onsets.**
   - A smaller p makes FL worse.
   - With asymmetric switching (p_in = 0.01 keeps ARL₀; p_out up), offline:
     - Boreas MegaLoc: FL 0.029 → 0.007 at recall 0.956 (p_out = 0.2);
     - Nordland and 4S countryside lose a lot of recall.
   - Full navigation grid with `CPC-HMM p_out ∈ {0.05, 0.1, 0.2}`: runs navF/navFc/navG.
3. **e_R violates D_R.** P(p^R ≤ 0.01 | off) = 0.059 on 4S countryside; P(p^R ≤ 0.05 | off) = 0.075 on Boreas MegaLoc.
   p^top is super-uniform everywhere.
   - The violations sit deep inside long off-map runs, i.e. coherent aliasing.
   - The noise-free odometry null did NOT help (0.059 → 0.059). Still open.

**Robustness to map holes** (navigation error of `hmm_fix`, CPC vs Xu'21):

- **50 %:** CPC wins everywhere except RobotCar. Boreas 13.7 vs 40.8; Nordland 23.8 vs 169; 4S office 26.3 vs 79.1.
- **10 %:** CPC loses on 4S old town (44 vs 30).

**Verdict.** CPC-HMM beats Xu'21 on 5/7 datasets without labels. It still loses on Boreas at 30 % holes (21 vs 6 m) and
on RobotCar (2.1 vs 1.3 m). Next steps: `handoff/03_HANDOFF.md` §5.

## Entry 20 — Why the HMM loses to simple baselines, and the CPC-HMM fix (2026-10-29)

**Where the HMM lost:**

- (L1) Its posterior confidence separates on-map from off-map worse than the raw top-1 similarity (RobotCar, CMU,
  4Seasons).
- (L2) Catastrophic lock-ins in navigation: the Xu'21-style HMM with a label-tuned off-map state has mean error up to
  10–40× that of the certified fixes.
- (L3) The off-map state costs recall.
- (L4) It gains nothing on short sequences (RobotCar).

**Diagnostics** (`analysis/hmm_diag.py`, 6 datasets × 6 descriptors; `paper/BAO_CAO_CertSeq.md` §5.1):

| ID | Finding |
|---|---|
| D5 | The posterior changes by ≤ 4e-6 when a random per-frame constant is added to all similarities: the softmax HMM is exactly invariant to the absolute level, i.e. blind to absence. |
| D1 | R@FL5 of the posterior is 0.44 vs 0.55 for raw max-sim on average (CMU 0.43 vs 0.74). Nordland is the exception, because its absolute level is shifted by winter. |
| D2 | Mean confidence 0.91 vs accuracy 0.77, ECE 0.14. |
| D3 | Confident-but-wrong frames are about 16 % of frames and cause about 41 % of the total error. |
| D4 | The evidence increments have lag-1 autocorrelation 0.8–0.99, i.e. variance inflation (1+r)/(1−r) of 8–136×: the independence assumption over-counts evidence. |

**Theory:**

- Relative vs absolute: LR(j:i) depends on differences; LR(j:∅) = f₁(s_j)/f₀(s_j) depends on the level.
- Composite-likelihood over-counting (Var ∝ (1+r)/(1−r)).
- The SelfCal p-value is a max-statistic p-value, so its evidence must enter a separate presence chain.
- Evidence derived from the HMM's own belief (posterior concentration, a p-value at the MAP place) re-confirms a
  lock-in.

**Fix: CPC-HMM** (`analysis/hmm_fix.py`, method `fac_anchT_mix`).

- *Place chain:* the HMM without an off-map state, with an affine-invariant emission (s − s_max)/(τ σ_far,t);
  τ = Gumbel scale of the map null.
- *Presence chain:* two states, symmetric p_in = p_out = 0.01. Its evidence is the mixed e-value
  ½(e_top + (e_R)^(1/H)):
  - e_top = a p^(a−1), the SelfCal-AA top-1 p-value, gated by agreement with the place MAP; a fitted by EM on the
    traversal's own p-values;
  - e_R = the e-value of the odometry-anchored statistic R_t, calibrated on the map's held-out traversal, tempered by
    1/H because of the window overlap.
- Report the place when P(on) > 0.5. Label-free and tuning-free.

**Local results** (CosPlace, 1 seed), CPC-HMM vs Xu'21 tuned with labels:

| Dataset | FL | Navigation error | R@FL5 |
|---|---|---|---|
| Nordland | 0.007 vs 0.033 | 23 vs 184 frames | 0.85 vs 0.82 |
| CMU | 0.055 vs 0.965 | 9.4 vs 125 m | 0.83 vs 0.37 |
| RobotCar | 0.068 vs 0.071 | 3.4 vs 2.4 m | 0.64 vs 0.52 |

**Negative variants** (kept in the code as ablations):

- The joint state space with the e-value per place: double multiplicity (too conservative) or prior–observation
  dependence (FL ≈ 0.9).
- Place-conditional evidence and posterior-concentration evidence: both feed the lock-in.
- The un-tempered ANCH e-value: CMU FL 0.15.
- ESS tempering of the place chain: it removes lock-ins but hurts ranking.

Full grid: `fix4` (7 datasets × 6 descriptors × 2 seeds; Boreas 1 seed), running on 14 Kaggle CPU kernels.

## Entry 19 — Certified sequential localization: excursion-level guarantee from the map (2026-10-29)

**Method** (`analysis/cert_seq.py`; draft `paper/certseq_draft.md`).

- Per-frame SelfCal-AA p-values (cross-fitted).
- Odometry-anchored sequence evidence R_t: the sum of −log p over frames of the last H whose top-1 is consistent with
  the current hypothesis plus the odometry (ANCH). ANCHR additionally fits the unknown odometry→map heading per window.
- Calibration: the conformal quantile of max R over H-frame segments of the map's own held-out traversal.
- Guarantee: P(any false acceptance during an H-frame off-map excursion) ≤ α under segment exchangeability. It is exact
  for any within-segment dependence, which is why the window-level calibration of exp11 / seq_odo failed.

**Validity** (6 descriptors × 3 random block grids, α = 0.05, H = 10, RobotCar H = 5).

- Mean excursion FAR of ANCH, worst condition in brackets:

  | RobotCar | CMU | Nordland | 4S office | 4S old town | 4S countryside |
  |---|---|---|---|---|---|
  | 0.016 [0.067] | 0.022 [0.052] | 0.020 [0.033] | 0.020 [0.049] | 0.014 [0.022] | 0.015 [0.025] |

- α = 0.01 / 0.1 track the target (`paper/cert_tables.md` Table 3).
- The label-calibrated baseline (same statistic, threshold from labelled off-map segments of the 2 most benign
  conditions) violates on RobotCar and CMU: mean FAR 0.044, worst condition 0.125 / 0.089.

**Power** (share of correct frames accepted, ANCH vs per-frame SelfCal):

| Nordland | CMU | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|
| 0.86 vs 0.44 | 0.82 vs 0.62 | 0.83 vs 0.31 | 0.77 vs 0.43 | 0.37 vs 0.19 |

- Latency to the first certified fix drops by 5–20×.
- Alias acceptance ≤ 0.03.
- RobotCar's 9-frame snippets are too short to accumulate evidence: 0.68 vs 0.77. This is kept as a stated
  limitation; long-sequence benchmarks were added instead (user instruction).
- ANCHR (no heading needed) on CMU CosPlace: FAR 0.037 vs 0.030 for ANCH, power equal (0.883).

**Navigation** (Kalman filter + drifting odometry, 30 % map holes, `nav_demo.py`). Mean position error with certified
fixes vs per-frame SelfCal vs label threshold vs accept-all:

| dataset | certified | per-frame SelfCal | label threshold | accept-all |
|---|---|---|---|---|
| Nordland, 6 desc. (frames) | 7.7–34.8 | 21.7–72.4 | 85–475 | – |
| CMU (m) | ≈ oracle (2.8–5.0 vs 2.7–3.2) | – | – | – |
| 4Seasons, real VIO | best or tied in most | – | – | – |

The Xu'21-style HMM with a label-tuned off-map state (added to nav_demo) gives many correct fixes, but has
catastrophic lock-ins. On Nordland CosPlace: mean 167, p95 1416 frames, vs 10.2 / 53 for the certified method.

**New data:**

- `nhatlong1103/vpr-dumps-4seasons` (public): 18 recordings, 62,875 frames, real VIO.
- Boreas from public S3 (31 sequences of one 8 km route over a year, wheel + gyro odometry):
  `automation/make_dump_boreas.py`, 15 T4 kernels running.
- `4seasons-poses` and `vpr-descriptor-weights` made public.

**Next:**

- Final round with ANCHR on every dataset including Boreas.
- Natural off-map (`cert_natural.py`: queries of other scenes/datasets).
- Ablations: ρ_o and odometry noise.
- Paper.

## Entry 18 — HMM direction, first round: data audit, sequence validity root cause, EVT-HMM (2026-10-29)

**Data (Step 1):** see `DATA_AUDIT.md`. The dumps are correct. RobotCar train queries are only 9-frame snippets.
CMU (median 186 frames) and Nordland have long sequences. No dataset has odometry except 4Seasons (real VIO). On
RobotCar/CMU, MegaLoc/SALAD place recall is at 92–98 % @10 m.

**HMM headroom check (CMU, CosPlace, local):**

| method | R@5 m |
|---|---|
| single frame | 90.7 |
| HMM random walk | 91.0 |
| HMM + simulated odometry | 92.5 |

The worst condition stays at 84.5 → 84.8. Average place recall is not where an HMM paper can win on these
benchmarks.

**H1: odometry-consistent sequence evidence (`analysis/seq_odo.py`, 18 settings, 6 T4 accounts).**
- exp11's run statistic counts a *stationary* alias as consistent. Requiring the matches to move with the odometry,
  anchored at the last frame with a tight tolerance (`RUNO`, 1 frame on Nordland), removes the Nordland MegaLoc
  violations at every L (0/18 conditions, worst 0.050). It also lifts power: DINOv2 0.44 → 0.63, NetVLAD
  0.57 → 0.70, CosPlace 0.67 → 0.81, MixVPR 0.73 → 0.88. The alias acceptance drops below the RUN statistic's.
- On CMU, long windows (L = 20) still "violate" (DINOv2 3/11, worst 0.14).
- **Root cause:** windows inside one 300 m block are strongly dependent. The map null of CMU has only ~500
  pseudo-windows ≈ 10–20 independent blocks, so the realised FAR of all 11 conditions (same calibration set) moves
  together. The per-window binomial violation test is itself anti-conservative for clustered windows.
- A deployment-condition null (calibrating on the same condition's own LOBO query windows, cross-fit by block parity)
  is *worse* (`proto/dcn.py`): violations already at L = 1–5. Spatial heterogeneity between blocks dominates.
- An excursion-level guarantee (null unit = whole held-out segment, scan max) would be exact under within-segment
  dependence. But CMU gives only 61 ten-frame null segments, too few.
- **Verdict:** the sequence guarantee is limited by the effective sample size of the spatial null. Not pursued as the
  main claim. The odometry-consistency fix is kept.

**EVT-HMM (new idea, `analysis/hmm_eval.py`).** Turn the map's leave-block-out null into the *HMM itself*. With
per-query affine-invariant z-scores of the cell maxima:

- the best non-matching z follows a Gumbel law (μ, β), estimated from map pseudo-queries;
- emission of place j = exp((z_j − μ)/β), the Gumbel-tail likelihood ratio;
- the off-map state is a "phantom place" at μ.

No temperature or threshold is tuned, and the HMM prior gives the multiplicity correction (z_1 > μ + β ln n is
needed to leave the off-map state when not localised).

Navigation protocol: 30 % of the map blocks removed, simulated odometry. First local run, CMU CosPlace, seed 0:

| method | recall | wrong | off-map false loc. | tuned |
|---|---|---|---|---|
| single | 0.878 | 0.122 | 1.000 | – |
| HMM exp(s/T) | 0.918 | 0.082 | 1.000 | T on 1 condition |
| HMM + k-th-best off-map (Xu'21) | 0.867 | 0.060 | 0.108 | T, k |
| **EVT-HMM** | 0.868 | 0.060 | **0.048** | none |
| EVT emission, no off-map | **0.927** | 0.073 | 1.000 | none |

Full run (6 descriptors × 3 datasets × 3 seeds) on Kaggle CPU: pending. The 4Seasons dump (21 of 30 recordings have
images on Kaggle, about 65 k frames, 6 descriptors, 7 T4) is running.

## History before SelfCal (Entries 0–10, condensed; full text in git history before branch `claude/selfcal-aa`)

- **CCBF / HMM sequence filter (Entries 0–3, 5–8).** A Bayes filter over (place, condition) with per-condition
  temperatures. The filter fixes single-image calibration on dense Nordland (ECE 0.076 → 0.028) and its off-map
  detection beats SUE there (AUROC 0.99 vs 0.94). But the condition temperatures barely differ (spread ≈ 1.2×), and
  on RobotCar/CMU the filter's reliability fails (off-map 0.23). Verdict: reliability is regime-dependent; the CCBF
  method was dropped.
- **CRSG (Entries 4, 8, 9).** A label-calibrated logistic gate on [margin, max-sim, entropy] with conformal risk
  control. It looked strong, but Entry 11's literature gate found it pre-empted (PA ratio, RS/SD/SU, integrity MLPs,
  SAFEVPR's Mondrian conformal). It survives only as a baseline.
- **Ops (Entry 10).** RTX full-scale runs and the Kaggle stall/re-push rules, now in the ops notes.
- **Lesson carried forward.** Labels from benign conditions do not transfer to hard ones. This motivates a label-free
  null drawn from the map itself, which is SelfCal (Entry 12).


## Entry 17 — SelfCal-Gap, sequence-level SelfCal, localisation demo (summary; full entry on branch `claude/selfcal-seq`)

- **SelfCal-Gap** (z_gap only + strata + gate): 0/192 violations, TPR **0.746** (oracle 0.706, AA 0.646), MSLS 0.603,
  worst point FAR 0.073.
  - Reason it helps: z_far's dominance fails on MSLS (alone it reaches FAR 0.40–0.88 there).
  - Ported here additively: `SelfCalTest(mode="gap")`, rows in `analysis/results/gap/`. The 1,275 AA rows of the
    rerun equal this branch's results exactly.
- **Sequence SelfCal** (window, map pseudo-sequences): large power gains, but window validity fails (Nordland MegaLoc
  2–3/3 seasons). Not a claim.
- **Localisation demo** (map with 30 % holes, 10 seeds): per-frame SelfCal-AA beats the label-calibrated threshold in
  all 12 descriptor × dataset pairs (mean error 1.3–12.6× lower). Details in `handoff/01_SCIENTIFIC_FINDINGS.pdf`.

## Entry 16 — Full rerun with the adopted SelfCal-AA (Mondrian strata by sd_far + domain gate), 6 T4 on 3 accounts (2026-10-28)

Branch `claude/selfcal-aa`. Rule = `selfcal.SelfCalTest` (B=10 strata of the null's sd_far, gate p_maxsim ≤ 0.8).
6 descriptors × 4 datasets = 24 settings, 192 deployment conditions, α = 0.05 (`paper/tables.md`, Table 2a):

| method | labels | viol. cond. | settings ≥1 viol. | mean TPR | median alias-accept | max worst FAR |
|---|---|---|---|---|---|---|
| **SelfCal-AA** | none | **0/192** | **0/24** | **0.646** | 0.011 | **0.048** |
| − strata | none | 0/192 | 0/24 | 0.612 | 0.008 | 0.140 |
| − gate | none | 0/192 | 0/24 | 0.648 | 0.012 | 0.048 |
| − both (original AA) | none | 0/192 | 0/24 | 0.617 | 0.011 | 0.140 |
| − alias guard | none | 5/192 | 3/24 | 0.667 | 0.072 | 0.721 |
| SUE [Zaffar'24] | benign | 16/192 | 10/24 | 0.661 | 0.070 | 0.163 |
| Threshold benign→all | benign | 36/192 | 15/24 | 0.652 | 0.218 | 0.281 |
| CRSG | benign | 32/192 | 14/24 | 0.757 | 0.169 | 0.356 |
| Conformal LOCO (SAFEVPR) | other cond. | 51/192 | 24/24 | 0.699 | 0.217 | 0.419 |
| Quantile Transfer | benign | 79/192 | 23/24 | 0.769 | 0.405 | 0.483 |
| Oracle | all | 0/192 | 0/24 | 0.706 | — | 0.050 |

- **Validity:**
  - No violating condition anywhere. The worst single-condition FAR is now ≤ α (0.048).
  - The original rule reached 0.140 in one condition. That is not significant after Bonferroni, but the point
    estimate is above α. Strata fix it.
- **Natural off-map (exp9):** deployable `SelfCalAA` on queries from the other datasets/cities. 0/120 cells > α, max
  FAR 0.007. The original rule leaked 0.134 (CosPlace, CMU map).
- **Power:** on RobotCar, CMU and Nordland the TPR is 0.708 vs oracle 0.721 (original rule 0.676).
- **MSLS is still the weak spot:** TPR 0.460 vs oracle 0.661 (original 0.439).

  | descriptor | v2 | v1 | oracle |
  |---|---|---|---|
  | MegaLoc | 0.879 | 0.878 | 0.965 |
  | CosPlace | 0.578 | 0.535 | 0.736 |
  | SALAD | 0.528 | 0.549 | 0.820 |
  | MixVPR | 0.517 | 0.480 | 0.747 |
  | NetVLAD | 0.218 | 0.135 | 0.377 |
  | DINOv2 | 0.040 | 0.060 | 0.320 |

  Label-based baselines get their extra MSLS power by violating 6–15 of the 54 conditions.
- **Ablations (SALAD):** centring still matters on Nordland (TPR 0.742 vs 0.568 without).
- **Map size (RobotCar, SALAD):** 0/9 violations at 25 %, 50 % and 100 % of the map. TPR 0.964 / 0.843 / 0.978.
  The 50 % dip has 115 null items per stratum; to look at.
- **Ops:**
  - The GPU backend makes `eval_all` take 0.5–1 min per setting (RobotCar/CMU/Nordland) and about 40–50 min for MSLS.
  - Natural off-map on CPU takes 17–40 min per descriptor.
  - Dumps are now a public dataset, `nhatlong1103/vpr-descriptor-dumps`.
- **Next for A\*:**
  1. Power on MSLS (large, heterogeneous maps): a better nuisance variable for the strata, or per-city/per-view nulls.
  2. Sequence-level anytime-valid acceptance.
  3. A SLAM/loop-closure demo.

## Entry 15 — MSLS (4th dataset) and the domain-shift fix: a lenient raw-similarity gate (2026-10-28)

**MSLS-val, both cities (CPH+SF, 9 conditions, 6 descriptors, Kaggle CPU):** SelfCal-AA has **0/54** significant
violations at α=0.05. The label-based methods all violate somewhere: SUE 5, CRSG 7, benign threshold 11, LOCO
(SAFEVPR) 13, Quantile Transfer 15. SelfCal without the AA guard has 5. Power is conservative on MSLS: MegaLoc 0.878
vs oracle 0.965, SALAD/CosPlace/MixVPR 0.48–0.55 vs 0.74–0.82. Natural off-map (exp9, now with MSLS): CPH↔SF cross-city
FAR ≤ 0.005 for all descriptors. The only failure is CosPlace with the CMU map (rc 0.134, msls-cph 0.135, msls-sf 0.089).

**exp10 (account yuan1103, 2×T4 + CPU): 8 variants × 6 descriptors × 5 maps.** 192 LOBO conditions, 120 natural
map/source cells.

| variant | LOBO viol. | worst LOBO | natural cells > α | natural max | mean TPR |
|---|---|---|---|---|---|
| AA (current) | 0/192 | 0.047 | 3/120 | 0.143 | 0.587 |
| **AA & p_maxsim ≤ 0.8** | **0/192** | 0.040 | **0/120** | **0.008** | **0.583** |
| AA & p_maxsim ≤ 0.5 | 0/192 | 0.040 | 0/120 | 0.004 | 0.567 |
| AND-ms (gate at α) | 0/192 | 0.029 | 0/120 | 0.000 | 0.432 |
| Mondrian by sd_far (5 strata) | 0/192 | 0.061 | 2/120 | 0.061 | 0.621 |
| Mondrian by maxsim | 0/192 | 0.074–0.094 | 15–20/120 | 0.179 | 0.46–0.49 |

**Decision:** adopt **SelfCal-AA with a lenient raw-similarity gate** (accept only if the raw max-sim is above the
20 % quantile of the map null, p_ms ≤ 0.8). It removes every domain-shift failure for a TPR cost of 0.004 on average
(Nordland 0.533 → 0.524).
- **Theory (to write):** the acceptance set is an intersection, so FAR ≤ min(P(p_AA ≤ α), P(p_ms ≤ 0.8)). The test
  is valid if **either** (A) the invariant statistics are dominated (appearance shift) **or** (B) foreign-domain
  queries fall below the null's 20 % max-sim quantile with probability ≥ 1−α (domain shift). This is a
  "union of assumptions" robustness result.
- **Next:**
  - Mondrian-by-sd_far gains power (0.621) but leaks under domain shift. Test it **with** the gate for more power.
  - Power on MSLS is still the main weakness.
- **Follow-up (Mondrian-by-sd_far + gate; kernels dive-vpr-shiftfix2-*, 6 descriptors × 5 maps):**

  | variant | LOBO viol. | max worst FAR | natural cells > α | natural max | mean TPR |
  |---|---|---|---|---|---|
  | AA&ms<=0.8 | 0/192 | 0.040 | 0/120 | 0.008 | 0.583 |
  | **Mondrian-sdf-10&ms<=0.8** | **0/192** | **0.048** | **0/120** | **0.006** | **0.612** |
  | Mondrian-sdf-5&ms<=0.8 | 0/192 | 0.061 (SALAD rc, n.s.) | 0/120 | 0.006 | 0.618 |

  The gate also fixes Mondrian's domain-shift leaks (2/120 → 0/120). The gain is largest where SelfCal was weakest:
  DINOv2 TPR 0.124 → 0.218 (B=10), CosPlace 0.624 → 0.677, NetVLAD 0.410 → 0.447, CMU map 0.692 → 0.749,
  Nordland 0.524 → 0.567. MegaLoc, MixVPR and SALAD are unchanged (±0.01). MSLS improves only slightly
  (0.45 → 0.46–0.48).
  **Candidate main method:** Mondrian-sdf-10 + gate, because its worst condition stays ≤ α everywhere. Caveat: B
  and γ were chosen after seeing these results. Either fix them a priori in the paper and report B ∈ {5,10} as a
  sensitivity check, or select them on the map null only. Mondrian conformal is valid per stratum under
  exchangeability, so T1–T6 carry over conditionally on the sd_far stratum.

## Entry 14 — SUE baseline, natural off-map stress test (a validity gap), MSLS + 4Seasons data (2026-10-28)

**SUE baseline** (Zaffar CVPR'24, published K=10, λ=350; label-calibrated benign→all) on SALAD, α=0.05:
- RobotCar: 1/9 violations (worst 0.102), TPR 0.934.
- CMU: 0/11, TPR 0.516.
- Nordland: 0/3, TPR 0.865, which is higher than SelfCal-AA's 0.754.

SUE is more shift-robust than a max-sim threshold, but it still needs labels and still violates on RobotCar.
SelfCal-calibrated SUE alone is not invariant (CMU 1/11 violations). Putting SUE inside the AA combination
(SelfCal-AA+SUE) stays valid and lifts Nordland TPR 0.754→0.806 (winter map 0.593→0.663). Added to eval_all.

**Natural off-map stress test (exp9_natural.py).** Every query of *another* dataset/city is scored against a map,
so all such queries are truly unmapped with no leave-block-out simulation. At α=0.05 most cells have FAR ≤ 0.035.
**One violation:** CosPlace with the CMU map and RobotCar queries gives FAR 0.134 (dawn 0.27).
- **Diagnosis:** raw max-sim is strongly dominated (FAR 0.000), but z_far (0.200), z_gap (0.218) and T_spacing
  (0.12) are inflated. For foreign-domain queries the far-region scores are compressed into a light-tailed bulk,
  so the top-1 stands out in spread-normalised units. The T2 dominance assumption ("shift only makes off-map
  queries less map-like") holds for raw similarity but **not** for scale-normalised statistics under *domain*
  (not appearance) shift.
- **Tried:**
  - (a) Location-only statistics (s1−μ_far, s1−best far): valid but Nordland TPR collapses (0.35→0.10).
  - (b) AND-gate with max-sim: valid but Nordland TPR is about 0.06 (CosPlace).
  - (c) Dual null (map null AND background-image null, intersection-union): fixes the violation only if the
    background resembles the foreign domain (bg=RobotCar fixes it, bg=Nordland does not), and costs CMU TPR
    0.81→0.48.
- **Status: open.** Must be fixed or stated as a scoped limitation (guarantee covers off-map places of the same
  environment/domain as the map).

**MSLS-val** added as the 4th benchmark (CPH 12.5k map / 6.6k queries, SF 6.3k / 4.5k; conditions = city ×
season + night). NB15 loader added. Two T4 kernels `dive-vpr-nb16{a,b}-msls` dump 6 descriptors.

**4Seasons poses** (user request): all 30 `reference_poses` archives + calibration downloaded from TUM and
uploaded as Kaggle dataset `nhatlong1103/4seasons-poses` (layout scene/date like `nhatlong1103/4seasons`).

**Literature:** `literature/VISUAL_LOCALIZATION_REVIEW.md` §6 (HMM/sequence VPR, anti-overlap checklist) and
LITERATURE_GATE Gate 3. Newly found related papers are Trinh & Lyons'25 (negative-stat thresholds), TAO'26
(map-out protocol) and Vysotska ICRA'25. SelfCal is still novel, but these must be cited.

## Entry 13 — SelfCal-AA validated on 6 descriptors × 3 datasets (138 deployment conditions)

**Aliasing guard.** The union rule controls *off-map* false accepts but accepts many in-map aliasing errors on
repetitive Nordland (52%). AND-rule with the gap to the best far region (`z_gap`, map-self-calibrated):
SelfCal-AA = accept iff max(p_comb, p_gap) ≤ α. SALAD α=0.05: aliasing accept 0.000 / 0.015 / 0.057 (RobotCar / CMU /
Nordland) vs 0.33–0.80 for every label-calibrated baseline; BH on AA p-values controls gross FDR on Nordland too
(≤ 0.030 at q=0.1).

**All descriptors (NetVLAD, CosPlace, MixVPR, DINOv2 CLS+mean, SALAD, MegaLoc), α=0.05:**

| method | violating cells (of 138) | settings with ≥1 violation (of 18) | mean TPR | median aliasing-accept |
|---|---|---|---|---|
| SelfCal-AA (no labels) | **0** | **0** | 0.676 | **0.008** |
| SelfCal (no labels) | **0** | **0** | **0.718** | 0.060 |
| Oracle (labels of every condition) | 0 | 0 | 0.721 | — |
| Conformal LOCO (SAFEVPR protocol) | 38 | **18** | 0.716 | 0.231 |
| Quantile Transfer | 64 | 18 | 0.799 | 0.440 |
| Threshold benign→all / CRSG | 25 / 25 | 10 / 10 | 0.664 / 0.785 | 0.218 / 0.173 |
| Gaussian z-norm null | 112 | 16 | 0.740 | 0.451 |

- Honest weak spot: **DINOv2 CLS+mean** (generic, not VPR-trained) — valid but very conservative (TPR 0.06–0.33 vs
  oracle 0.39–0.70): its global feature encodes the capture condition, so same-condition map pseudo-queries are far more
  map-like than deployment queries. Dual (session-mean) centring recovers only 0.33→0.41 → reported as a limitation.
- Robustness: winter-as-map Nordland 0/3; 25% of RobotCar map (650 pseudo-queries) FAR 0, TPR 0.994; ablations
  insensitive; centring essential on Nordland (0.754 vs 0.329).
- Mechanism: one-sided KS excess-risk bound Δ⁺ ≤ 0.052 with the map null vs up to 0.255 with a labelled benign null.
- Cost: offline 24 s (7k-image map, CPU); online ≈10 ms/query incl. similarity products (`selfcal.SelfCalAA`).
- 4Seasons on Kaggle has no pose files → not usable for evaluation.
- Paper: `paper/SelfCal_paper_full.pdf` (built by `paper/build_paper.py` from `paper/selfcal_paper.md` + results).

---

## Entry 12 — New direction: self-calibrating maps (label-free, shift-robust acceptance for VPR)

**Gap.** Every guarantee-giving VPR acceptance method needs labelled calibration data (integrity MLPs, Quantile
Transfer, SAFEVPR LTT/Mondrian, our CRSG+conformal) and breaks under unseen appearance shift. No method controls the
false-accept (wrong loop-closure / off-map) rate without labels.

**Idea.** (1) In VPR the map is a free source of *off-map* calibration queries: each map image with its own spatial
block removed from the map is off-map by construction (leave-one-block-out) — labelled nulls at zero cost.
(2) Use per-query statistics invariant to affine score changes (z-norm of the top-1 vs the far-region maxima, EVT
spacing), so that appearance shift (night compresses scores) does not move their null distribution. (3) Split-conformal
p-values of a deployment query against the map pseudo-queries → FAR control with no labels. (4) Centering descriptors on
the map mean (hubness reduction, map-only).

**Infra.** NB15 dumps fp16 descriptors once (T4): RobotCar-Seasons overcast-reference **rear map with NVM poses** (6954)
+ 1906 train queries (poses cam→world, verified); Extended-CMU **official databases of 11 slices merged into one city
map** (2418 db, 21.4k queries, 11 dates; slices share one world frame); Nordland 4×4500. All analysis local (CPU).
Off-map protocol = leave-one-300m-block-out (RobotCar 1386, CMU 14117, Nordland 12180 off-map queries).

**Results (SALAD, α=0.05; FAR on off-map, #conditions significantly violating, TPR on correct in-map):**

| | RobotCar (9 cond.) | CMU (11 dates) | Nordland (3 seasons) |
|---|---|---|---|
| SelfCal[z_all] (ours, no labels) | 0.009, 0/9, **0.987** | 0.034, 1/11, 0.848 | 0.046, 0/3, 0.304 |
| SelfCal[z_far+center] (ours) | 0.012, 0/9, 0.995 | 0.019, **0/11**, 0.864 | 0.048, **0/3**, **0.840** |
| SelfCal[maxsim] (non-invariant) | 0.001, 0/9, 0.979 | 0.010, 0/11, 0.949 | 0.022, 0/3, 0.411 |
| LabelCal[maxsim] day→all | 0.109, **5/9**, 0.997 | 0.052, **4/11**, 0.985 | 0.037, 0/3, 0.630 |
| LabelCal[CRSG] day→all | 0.099, **4/9**, 0.996 | 0.054, **4/11**, 0.982 | 0.041, 0/3, 0.814 |
| Oracle[maxsim] (labels of every cond.) | 0.040, 0/9, 0.995 | 0.049, 0/11, 0.992 | 0.050, 0/3, 0.780 |
| Theory-only Gaussian z-norm | 0.350, 9/9 | 0.250, 11/11 | 0.125, 3/3 |

- Label-calibrated thresholds transferred from benign conditions **violate the target in 4–5 conditions** on the two
  realistic datasets; map self-calibration is valid everywhere tested (0 significant violations for z_far+center).
- Pure EVT spacing test (closed-form F(2,2k)) is close to valid but mildly anti-conservative (night-rain 0.109@0.05);
  cause = **hubness** (5% of map cells win 59% of null competitions). Map self-calibration + centering fix it.
- No single statistic has the best power everywhere (maxsim strong on CMU, z_far+center on Nordland) → next: self-
  calibrate a *combination* (min of conformal p-values, re-calibrated on the map null).
- Honest caveats: worst-condition FAR at α=0.1 reaches ~0.11–0.13 on RobotCar (within binomial noise, n≈150/cond);
  RobotCar GT only exists for the public train split (test GT withheld), official thresholds applied to top-1 poses.

**Ops lesson (2026-10-28 05:05):** a "RUNNING but silent for 60 min → cancel+restart" rule in `run_kernel.py`
killed two *healthy* multi-descriptor dump kernels (Kaggle's output API hides logs until a run ends). Silent-restart is
now OFF by default; only QUEUED > 10 min triggers cancel (`kaggle kernels delete -y`) + re-push. `--attach` waits for
an already-running kernel after a local container restart without re-pushing.

**Ablation (Nordland, SALAD, α=0.05):** SelfCal-AA is insensitive to cell / exclusion / block / δ / calibration-set
size (TPR 0.72–0.76, FAR ≤ 0.011, aliasing ≤ 0.058, even with 497 null items); **without map-centring TPR drops to
0.33** (hubness), so centring is essential on Nordland. RobotCar: TPR 0.94–0.99 across all variants.

---

## Entry 11 — Literature gate (Bước 0)  →  VERDICT: OVERLAP on method + conformal; reality-check still novel

Full report: `LITERATURE_GATE.md`. Read 9 closest papers in full (paper text only, no code).

- **CRSG-as-a-method is pre-empted.** Its features are standard retrieval-based uncertainty: margin ≈ PA-score d1/d2
  (Hausler'21; baseline in Zaffar CVPR'24), NN-distance = L2-distance RUE (Zaffar'24), score-distribution shape ≈
  RS/SD/SU (Miller et al., RA-L'26, 9 descriptors incl. SALAD/MixVPR). A supervised classifier on distance-vector
  statistics predicting in-tolerance correctness already exists (Carson RA-L'22 SVM; Claxton RA-L'24 MLP with 192
  features, incl. SALAD). CRSG is a 3-feature logistic special case; only the calibrated (ECE/AURC) framing differs.
- **Conformal C2/C3 is pre-empted** by SAFEVPR (2026-05): LTT on cosine breaks under cross-condition shift on Oxford
  RobotCar/NCLT/St Lucia; Mondrian (score-bin) conformal restores FDR validity. Our C3 additionally uses condition
  labels at test time — a real weakness.
- **Naming bug (must fix in any direction):** our "SUE" baseline is `sqrt(2-2*max cos)`, i.e. Zaffar's *L2-distance*
  RUE baseline, NOT SUE (spatial spread of the top-K reference poses). True SUE was never compared.
- **Still novel:** reliability (ECE/AURC/off-map) of sequential filtering is regime-dependent — near-oracle on dense
  Nordland, failing on RobotCar/CMU (off-map 0.23), with the NB8 mechanism; condition-temperature inert. SMR
  (Hussaini'25) only shows sequence matching can hurt *accuracy*.

**Decision:** per the handoff gate rule, do NOT proceed to the official benchmark / BoQ-MixVPR / full paper under the
current "CRSG is a new method" framing. Options (A) reframe as a cross-regime reliability analysis with correct
baselines + label-free Mondrian conformal, or (B) return to Phase 2 — put to the user.

---
