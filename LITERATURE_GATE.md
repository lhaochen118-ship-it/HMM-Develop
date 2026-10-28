# Literature Gate — novelty checks (paper text only, no code)

## Gate 1 (2026-10-28, condensed): CRSG — pre-empted, dropped

CRSG (a label-calibrated logistic gate on margin / max-sim / entropy, plus conformal risk control) overlaps existing
work. Its features are the PA ratio and the RS/SD/SU score-shape statistics, supervised verifiers already exist
(Carson'22 SVM, Claxton'24 MLP), and SAFEVPR's Mondrian conformal covers the conformal part. It is kept only as a
baseline. Note: the true SUE (spatial spread of the top-K poses) is the SUE baseline now used; the earlier "SUE" was
Zaffar's L2-distance baseline. Papers read in full for this gate (still the closest baselines for SelfCal):

- Zaffar, Nan, Kooij — *On the Estimation of Image-matching Uncertainty in VPR* (CVPR'24) — https://www.alphaxiv.org/abs/2404.00546
- Miller, Milford, Hafez, Ramchurn, Ehsan — *Through the Lens of Doubt* (RA-L'26) — https://www.alphaxiv.org/abs/2510.13464
- Claxton, Malone, Carson, Ford, …, Milford — *Improving VPR-Based Robot Navigation by Verifying Localization Estimates* (RA-L'24) — https://www.alphaxiv.org/abs/2407.08162
- Hussaini, Fischer, Milford — *Sequence-Matching Receptiveness Prediction* (2025) — https://www.alphaxiv.org/abs/2503.06840
- Sier et al. — *SAFEVPR: Patch-Based Conformal Verification* (2026) — https://www.alphaxiv.org/abs/2605.28048
- Yanko, Shavit — *KappaPlace* (2026) — https://www.alphaxiv.org/abs/2605.19435
- Rajani, Milford, Fischer — *Quantile Transfer for Operating Point Selection* (IROS'26) — https://www.alphaxiv.org/abs/2602.04401
- Trinh, Lyons — *Adaptive Thresholding via Negative Gaussian Mixture* (2025) — https://www.alphaxiv.org/abs/2512.09071
- Lu, Tanaka — *Route-MHT* (2026) — https://www.alphaxiv.org/abs/2607.04745


## Gate 2 (2026-10-28) — novelty of the new direction: self-calibrating maps (SelfCal)

Idea: the VPR map supplies labelled *off-map* queries for free (leave-one-spatial-block-out self-retrieval);
split-conformal p-values against these pseudo-queries, with affine-invariant far-region statistics, give label-free,
shift-robust false-accept control; an AND-rule with the gap to the best far region also suppresses aliasing.

| Closest work | What it does with the map / scores | Difference |
|---|---|---|
| RSF (Zaffar et al. 2025, arXiv 2510.03751) | uses the reference set (images+poses) to **fine-tune** the descriptor | not acceptance, no guarantee |
| Map-density selection (Hussaini et al. 2026, arXiv 2602.21473) | two reference traverses → predict local Recall@1 | needs 2 traversals + regression; no rejection test |
| Adaptive negative-GMM thresholds (Trinh & Lyons 2025) | per-place thresholds from database negatives | raw scores (= our non-invariant SelfCal[maxsim] ablation, low power under shift), no guarantee |
| Schubert et al. (robust-normal null) / meta-recognition (Scheirer 2011, EVT) | parametric null of the score distribution | = our "theory-only" baselines: invalid (FAR 0.13–0.35 at α=0.05) |
| SAFEVPR (2026), Quantile Transfer (IROS'26) | labelled calibration (other conditions / calibration traversal) | violate on 1–4/11 conditions in our protocol; need labels |
| Conformal outlier testing (Bates et al. 2023), conformal under shift (Barber et al. 2023) | theory | we instantiate: map pseudo-queries as the null sample; PRDS ⇒ BH |

Searches (alphaXiv, 2 rounds): "database images as pseudo-queries threshold calibration", "label-free FDR place
recognition", "EVT meta-recognition retrieval", "self-supervised calibration VPR" → no paper uses the map as a
conformal null sample for VPR acceptance. **Verdict: novel; proceed.**

## Gate 3 (2026-10-28): papers found while reviewing HMM/sequence VPR (see `literature/VISUAL_LOCALIZATION_REVIEW.md` §6)

- **Trinh & Lyons, arXiv 2512.09071 (2025).** Per-place thresholds from "negative" similarity statistics of other
  places in the database. It overlaps with SelfCal's "use the map's own negatives", but it has no held-out spatial
  block, no off-map null, no p-values, no guarantee and no appearance-shift analysis, and it only uses tiny
  multi-condition databases. **Must be cited and contrasted.**
- **Vysotska et al., ICRA'25 (adaptive thresholding for sequence PR) and Schubert et al., ICRA'21 (Beyond ANN).**
  Data-driven thresholds that assume most pairs are different places. Heuristic, no guarantee. Cite.
- **Lu & Tanaka, arXiv 2607.04745 (TAO / Route-MHT, thermal, 2026).** Its map-out benchmark deletes contiguous map
  segments, which matches our leave-block-out protocol *as an evaluation*. Our novelty is using held-out blocks
  as the **calibration null**, not as the evaluation protocol. Cite it for the protocol.
- **Xu et al., RA-L'21.** HMM off-map state, emission = k-th best match, thresholds tuned with labels. Already
  cited, no calibration.

Verdict: SelfCal's core (held-out map blocks as a conformal null, affine-invariant far-region statistics,
label-free FAR guarantee under shift) is still not pre-empted. Related-work must add the papers above.

## Gate 4 (2026-10-28): component-by-component overlap check for SelfCal (paper reading only)

New papers checked: TFA (arXiv 2609.25937), LocalScore (2602.01012), VPR Auditing with VLMs (2607.12818),
KappaPlace (2605.19435, abstract only), Mount et al. RA-L'20 [citation only], and Gates 1–3 again.

| SelfCal component | Closest prior work | Overlap |
|---|---|---|
| Map images as pseudo-queries | **TFA'26**: database images as leave-*self*-out pseudo-queries to calibrate the *aggregation head* (retrieval accuracy, hub detection). Hussaini'26: 2 reference traversals to pick map density. Trinh & Lyons'25: negative stats inside the DB. | **Partial (mechanism).** None removes a *spatial block* to create *off-map* nulls, and none uses them to calibrate an *accept/reject* test. Cite TFA explicitly. |
| Spatially-excluded gap (z_gap) | **MPF'19 quality score** (best vs next best *outside a window* around the best). SeqSLAM's quality ratio. PA ratio. | **Statistic family is known.** Our addition is the far-sd normalisation and conformal calibration on the map null. Do not claim the statistic itself. |
| Per-query z-norm / EVT spacing | Score normalisation (biometrics Z/T-norm), meta-recognition EVT (Scheirer'11), RS/SD/SU (Miller'25), LocalScore (k-NN gallery density, biometrics). | Known building blocks. Not novel alone. |
| Map-mean centring (hubness) | Radovanović'10, Jégou & Chum'12, TFA'26 (hub analysis). | Known. |
| Conformal p-values for outliers, BH | Bates et al.'23 (conformal outlier testing). | Standard theory, cited. |
| Label-free FAR control under appearance shift | SAFEVPR'26 (labelled), Quantile Transfer'26 (no guarantee), Mount'20 / Trinh'25 / Vysotska'25 (heuristic thresholds), VLM auditing'26 (no threshold, FAR ≈ 0.12–0.30, no guarantee). | **No paper found.** This is the contribution. |
| HMM / sequence | Xu'21 off-map state, etc. (see literature review) | SelfCal does **not** use an HMM. |

Verdict: no paper duplicates SelfCal as a whole. The novelty is the *combination*: a held-out-block map null + an
invariant statistic + a label-free conformal guarantee under shift. Every individual building block has precedent,
so the paper must be written as "a new calibration principle", not "new scores". The open domain-shift validity gap
(Entry 14) is the main threat to that claim.

## Gate 5 (2026-10-28): final novelty re-check of SelfCal-AA and SelfCal-Gap (paper reading only)

Scope: the final method (Mondrian strata on σ_far, domain gate, Gap mode, T1–T6). Searches: 9 alphaXiv rounds over the
six areas of `handoff/00_READ_ME_FIRST.md` §3 (Mondrian/conditional conformal on a nuisance variable; intersection–union
or multi-null conformal under shift; spatially excluded gap / distinctiveness; gallery or map as calibration/null set in
retrieval, face ID, re-ID, LiDAR PR; label-free FAR control under shift; new versions of the closest VPR papers).

### New papers read (full text or targeted PDF queries)

| Paper | What it does | Relation to SelfCal |
|---|---|---|
| **Bhatta, Dhakal, King, Bowyer — *Are you In or Out (of gallery)?* (2025)** https://www.alphaxiv.org/abs/2508.06357 | Face 1:N identification. Builds out-of-gallery training data by **removing the probe identity from the gallery** and re-searching; an MLP on the ranks of the rank-1 identity's other images predicts in/out-of-gallery; tested under blur/turbulence. | **Closest precedent for the *mechanism* "hold part of the gallery out to manufacture non-mated probes".** Differences: identity hold-out (not spatial), trains a classifier per condition, no p-value / FAR guarantee, no shift argument. Must cite; we can no longer say the "remove-and-requery" trick is new in general. |
| **Heo, Lee, Kwon, Lee — *Using the enrollment gallery as evidence: affine-invariant score calibration for target speaker tagging* (Oct 2026)** https://www.alphaxiv.org/abs/2610.11272 | Uses the *other enrolled speakers* as evidence because they "share the deployment domain and need no external cohort"; shows gallery-as-cohort Z/T-norm fails; proposes two **affine-invariant** terms: competitor-profile dispersion (inter-quantile radius) and enrollment-profile deviance. Threshold still tuned on labelled trials. | **Closest precedent for the *motivation + statistic family*** ("gallery is its own, in-domain evidence"; affine invariance to per-trial offset/scale). z_far ≈ score minus competitor level over competitor spread. Differences: speaker tagging, no spatial exclusion, no held-out null, no conformal p-value, no guarantee. Must cite. |
| **Khazem — *Identities, Not Pairs: Distribution-Free False-Accept Control for Embedding-Based Verification* (COVE, Oct 2026)** https://www.alphaxiv.org/abs/2610.35277 | Transductive conformal FAR control for 1:1 verification; proves hub identities limit calibration-only thresholds; cohort-normalised (CSLS/S-norm) scores keep the bound. Needs **labelled** calibration identities; validity under identity exchangeability only (shown to break across category splits). | Same goal (distribution-free FAR for frozen embeddings) and same enemy (hubness), but labelled, 1:1, no shift robustness. Cite as the general-retrieval analogue; our dominance/shift argument and label-free null are what it lacks. |
| **Kim, Choi, Kang, Kim — *QCSA: Calibrated keyframe-segment selection for LiDAR loop closure* (v3, Oct 2026)** https://www.alphaxiv.org/abs/2512.09447 | LiDAR loop-candidate admission; threshold = conformal-style quantile of the *strongest false segment per calibration query*, from **labelled** calibration trajectories; per descriptor and setting. | Uses the same "max over false candidates per query" null construction, but labelled and with no transfer guarantee. Cite. |
| **SAFEVPR (Sier et al. 2026)** — still v1 https://www.alphaxiv.org/abs/2605.28048 | Mondrian LTT with **bins = quintiles of the verifier score itself**, labelled calibration on other conditions; no gate, no map data, no IUT. | No new version. Our strata differ in kind (nuisance variable σ_far, label-free). |
| **TFA (Li et al. 2026)** — still v1 https://www.alphaxiv.org/abs/2609.25937 | DB images as leave-self-out pseudo-queries to choose an aggregation head; reports that DB-only evidence can fail to transfer to queries (4Seasons Office Loop 7.9% R@1). | No accept/reject. Its failure case supports our need for a shift argument (T2/T3) rather than trusting DB statistics blindly. |
| **Trinh & Lyons (2025)** — still v1 https://www.alphaxiv.org/abs/2512.09071 | Per-place thresholds = mean of negative scores against other places; evaluated by R@K only. | Unchanged; no hold-out, no p-values, no FAR. |
| **Yang & Jin — *Multi-Distribution Robust Conformal Prediction* (ICML'26)** https://www.alphaxiv.org/abs/2601.02998 | **max-p aggregation** of source-wise conformal p-values gives validity uniformly over several (labelled) source distributions. | Standard reference for our max(p_comb, p_zgap) and gate logic (validity under a union of nulls). |
| **Qian et al. — *Detecting Unseen Jailbreak Sources* (Oct 2026)** https://www.alphaxiv.org/abs/2610.09167 | Union null "stream comes from one of K known sources": reject only if *every* source-wise conformal p-value is small. | Same intersection–union structure as T6; confirms the device is known. |
| **Manoharan — *C3R: label-free per-domain contamination control* (2026)** https://www.alphaxiv.org/abs/2607.14157 | Mondrian-style risk control on an **inferred** (router-predicted) group, with an explicit transfer slack; abstains when infeasible. | Analogue of Mondrian on a query-computable variable; ours needs no slack because σ_far is computed identically for null and query (T1 holds exactly). |
| **Wu, Liu, Ren, Zou — *Conformal Novelty Detection via Data-enhanced Localization* (Oct 2026)** https://www.alphaxiv.org/abs/2610.34999 | Localised (kernel-weighted) conformal p-values for *conditional* novelty given a covariate; finite-sample FDR. | General theory for "p-value conditional on a nuisance covariate"; our hard bins are the Mondrian special case. |
| **Zhou & Wang — *When EER hides deployment failure* (2026)** https://www.alphaxiv.org/abs/2606.21584 | Audit: source-calibrated thresholds fail under domain shift; monotone unlabeled corrections (z-norm, temperature) cannot fix ranking, only the operating point, and are fragile. | Independent evidence for our premise (label-calibrated thresholds break under shift) from speech anti-spoofing. Optional cite. |

### Component-by-component overlap matrix (after Gate 5)

| SelfCal component | Closest prior work (all gates) | Overlap | Claim status |
|---|---|---|---|
| Map pseudo-queries (leave-one-300 m-block-out ⇒ off-map *by construction*) | Bhatta'25 (identity hold-out ⇒ out-of-gallery training data), TFA'26 (leave-self-out pseudo-queries), Trinh'25 (DB negatives), Lu & Tanaka'26 (map-out as evaluation), QCSA'26 (max false per query, labelled) | **Partial (mechanism).** Remove-and-requery exists in face ID; nobody uses *spatial* hold-out as a **conformal null** for an accept/reject test, and nobody in VPR/localisation. | Novel *as a calibration principle with guarantee*; not novel as a trick. |
| z_far / z_gap, affine-invariant, far-region (spatially excluded) | Heo'26 (affine-invariant gallery dispersion/deviance), biometrics Z/T/AS-norm, MPF'19 quality score, SeqSLAM ratio, PA ratio, Lowe, RS/SD/SU (Miller'26), LocalScore | **Statistic family known.** Our specific form (cell maxima, ρ-exclusion, σ_far scaling) is new in detail only. | Do not claim the statistics; claim *why they transfer* (affine distortion + dominance). |
| Map centring (hubness) | Radovanović'10, Suzuki'13, Jégou & Chum'12, CSLS, TFA'26, COVE'26 | Known. | Engineering choice. |
| Self-calibrated min-p (re-ranked) | Bates'23 / conformal p-value combination; MDCP'26 | Known construction. | T4 is a standard corollary. |
| Aliasing guard max(p_comb, p_zgap) | Berger'82 IUT; MDCP'26 max-p; Qian'26 union null | **Device known.** | Claim only the *use* (aliasing in VPR) and its empirical effect. |
| Mondrian strata on σ_far | Vovk'03/'05 Mondrian; SAFEVPR'26 (bins on the score, labelled); C3R'26 (inferred groups); localized conformal (Guan'23, Hore & Barber'24, Wu'26) | **Device known.** σ_far as the stratifier (label-free, from the query's own far regions) is new but a design choice. | Present as instantiation; do not list as a contribution on its own. |
| Domain gate p_maxsim ≤ 0.8 (IUT, T6) | Berger'82; MDCP'26; Qian'26 | Device known; **no VPR paper guards label-free scores against foreign-domain inflation.** | Keep as a component; T6 is a one-line corollary — present as such. |
| SelfCal-Gap (p_zgap alone, same strata/gate) | MPF'19 / PA ratio as statistics; no calibrated version | Statistic known; calibrated-on-map version not found. | Report as an operating point, flag post-hoc selection. |
| T1, T4, T5 | Vovk'05, Bates'23 | Standard. | Cite, do not claim. |
| T2 (dominance ⇒ conservative), T3 (one-sided Kolmogorov excess) | Barber'23 (TV coverage gap), robust conformal | Generic form known; **the VPR-specific dominance hypothesis and its verification (exp6, 192 conditions) are new.** | Claim as "auditable sufficient condition", not as new theory. |
| T6 (FAR ≤ min(α+Δ⁺, ε_c)) | IUT | Trivial bound; novelty is the *two-assumption* framing for appearance vs domain shift. | Keep, short. |
| Protocol: LOBO off-map, foreign-domain off-map, 4 datasets × 6 descriptors, 192 conditions | SAFEVPR (23 setups, 3 backbones), Route-MHT (map-out), Quantile Transfer | Broader than any VPR acceptance paper found. | Strength, not novelty. |

### Verdict

1. **Still not pre-empted as a whole.** No paper (VPR, LiDAR, face/speaker/re-ID, retrieval, conformal) combines
   (a) a null sample manufactured from the map/gallery by structural hold-out, (b) conformal p-values with a
   label-free FAR guarantee, and (c) an argument (dominance + gate) for validity under appearance *and* domain shift.
   SelfCal-AA and SelfCal-Gap remain novel in that sense.
2. **New partial overlaps that change the framing** (must be cited and contrasted in Related Work):
   Bhatta'25 (gallery hold-out to simulate out-of-gallery probes), Heo'26 (gallery as in-domain evidence with
   affine-invariant terms), COVE'26 (distribution-free FAR control for embeddings, hubness). Our slogan
   "the map is its own calibration set" has a close cousin in Heo'26 ("enrollment gallery as evidence"); the
   difference is the held-out null + guarantee, so the slogan must be tied to *calibration with a guarantee*.
3. **Components that are not novel and must not be listed as contributions:** Mondrian strata, max-p / IUT
   aliasing guard and domain gate, min-p recalibration, centring, the z-type statistics. They are instantiations of
   standard devices; the contribution is choosing label-free, map-computable versions and showing they make the
   map null valid across 192 conditions.
4. **Reframed claim (use in abstract/intro):** "In VPR the map's geometry labels off-map queries for free:
   spatial hold-out turns the map into a conformal null sample. With scale-free far-region statistics this null
   *dominates* off-map queries under appearance change, giving the first label-free acceptance test with a
   false-accept guarantee that we verify across 192 conditions; a raw-similarity gate extends validity to foreign
   domains." Avoid "first to use the database for calibration" and "new uncertainty scores".
5. **A/A\* potential.** RA-L / ICRA / IROS (A): yes, novelty is adequate and the evaluation is broad. T-RO / IJRR or
   CVPR (A\*): novelty alone is not enough because each building block is known and close cousins now exist in
   biometrics. Levers: (i) independent validation of the post-hoc choices (γ = 0.8, B = 10, Gap) on unseen datasets;
   (ii) MSLS power; (iii) a short generality experiment showing the same principle on an open-set retrieval task with
   metadata (e.g. landmark retrieval or re-ID with identity hold-out) against COVE/Bhatta-style baselines — this would
   turn the overlap with biometrics into evidence of generality; (iv) a testable diagnostic for the dominance
   assumption at deployment time without labels.
