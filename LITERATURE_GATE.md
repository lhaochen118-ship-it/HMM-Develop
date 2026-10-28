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
