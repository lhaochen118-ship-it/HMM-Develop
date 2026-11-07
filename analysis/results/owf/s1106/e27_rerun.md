# Entry 27 — audited re-run (hsq2 = causal HQ, hsq2s = strictly online fallback), 2026-11-07

## Fresh groups 64–72 (432 runs) — pre-registered rules of Entries 23, 24, 26 re-applied
```
== seeds 64-66, Q2 (causal hsq2), 144 runs
   R_new: recall 0.9323, mean segFAR 0.0059, runs>a 4, worst 0.0254, nav 14.56
   C10  : recall 0.9235, mean segFAR 0.0024, runs>a 0, worst 0.0129, nav 14.91
   vs tested hsq: identical runs 33/144; hsq recall 0.9323 msf 0.0057 runs>a 4; delta recall -0.0001 [-0.0002, +0.0001]
   Entry 23 rule vs R_old (144 runs): V1 MET (4 vs 4, 0.0059 vs 0.0074); V2 MET (-0.0038 [-0.0071, -0.0010]); V3 MET (14.56 vs 14.67)
== seeds 64-66, QS (strict hsq2s), 144 runs
   R_new: recall 0.9321, mean segFAR 0.0071, runs>a 5, worst 0.0366, nav 14.80
   C10  : recall 0.9231, mean segFAR 0.0044, runs>a 4, worst 0.0284, nav 15.21
   vs tested hsq: identical runs 3/144; hsq recall 0.9323 msf 0.0057 runs>a 4; delta recall -0.0002 [-0.0007, +0.0002]
   Entry 23 rule vs R_old (144 runs): V1 NOT (5 vs 4, 0.0071 vs 0.0074); V2 MET (-0.0040 [-0.0072, -0.0011]); V3 MET (14.80 vs 14.67)
== seeds 67-69, Q2 (causal hsq2), 144 runs
   R_new: recall 0.9268, mean segFAR 0.0029, runs>a 0, worst 0.0085, nav 12.53
   C10  : recall 0.9201, mean segFAR 0.0009, runs>a 0, worst 0.0029, nav 12.93
   vs tested hsq: identical runs 39/144; hsq recall 0.9269 msf 0.0031 runs>a 0; delta recall -0.0001 [-0.0003, +0.0001]
   Entry 23 rule vs R_old (144 runs): V1 MET (0 vs 1, 0.0029 vs 0.0035); V2 MET (-0.0041 [-0.0074, -0.0011]); V3 MET (12.53 vs 12.07)
   Entry 24/26 rule (144 runs): C1 MET; C2 MET (+0.1358 [+0.1175, +0.1543]); C3 MET (TAO26 valid=False runs>a 130 diff +0.093; Xu21 valid=False runs>a 81 diff +0.235; Claxton24 valid=False runs>a 104 diff +0.189); C4 MET (12.53 vs 15.48) -> CONFIRMED
   safe point C10: S1 MET (0 runs>a, worst 0.0029); S2 MET (-0.0067) -> CONFIRMED
== seeds 67-69, QS (strict hsq2s), 144 runs
   R_new: recall 0.9266, mean segFAR 0.0032, runs>a 0, worst 0.0080, nav 12.54
   C10  : recall 0.9197, mean segFAR 0.0011, runs>a 0, worst 0.0037, nav 12.95
   vs tested hsq: identical runs 5/144; hsq recall 0.9269 msf 0.0031 runs>a 0; delta recall -0.0004 [-0.0010, +0.0003]
   Entry 23 rule vs R_old (144 runs): V1 MET (0 vs 1, 0.0032 vs 0.0035); V2 MET (-0.0043 [-0.0076, -0.0013]); V3 MET (12.54 vs 12.07)
   Entry 24/26 rule (144 runs): C1 MET; C2 MET (+0.1355 [+0.1173, +0.1541]); C3 MET (TAO26 valid=False runs>a 130 diff +0.093; Xu21 valid=False runs>a 81 diff +0.234; Claxton24 valid=False runs>a 104 diff +0.189); C4 MET (12.54 vs 15.48) -> CONFIRMED
   safe point C10: S1 MET (0 runs>a, worst 0.0037); S2 MET (-0.0069) -> CONFIRMED
== seeds 70-72, Q2 (causal hsq2), 144 runs
   R_new: recall 0.9255, mean segFAR 0.0035, runs>a 0, worst 0.0092, nav 13.97
   C10  : recall 0.9181, mean segFAR 0.0013, runs>a 0, worst 0.0042, nav 14.56
   vs tested hsq: identical runs 35/144; hsq recall 0.9259 msf 0.0034 runs>a 0; delta recall -0.0004 [-0.0005, -0.0002]
   Entry 24/26 rule (144 runs): C1 MET; C2 MET (+0.1169 [+0.1006, +0.1337]); C3 MET (TAO26 valid=False runs>a 126 diff +0.087; Xu21 valid=False runs>a 83 diff +0.229; Claxton24 valid=False runs>a 101 diff +0.186); C4 MET (13.97 vs 15.24) -> CONFIRMED
   safe point C10: S1 MET (0 runs>a, worst 0.0042); S2 MET (-0.0074) -> CONFIRMED
== seeds 70-72, QS (strict hsq2s), 144 runs
   R_new: recall 0.9252, mean segFAR 0.0041, runs>a 0, worst 0.0121, nav 14.06
   C10  : recall 0.9184, mean segFAR 0.0020, runs>a 0, worst 0.0077, nav 14.69
   vs tested hsq: identical runs 2/144; hsq recall 0.9259 msf 0.0034 runs>a 0; delta recall -0.0007 [-0.0013, -0.0001]
   Entry 24/26 rule (144 runs): C1 MET; C2 MET (+0.1165 [+0.1001, +0.1332]); C3 MET (TAO26 valid=False runs>a 126 diff +0.086; Xu21 valid=False runs>a 83 diff +0.229; Claxton24 valid=False runs>a 101 diff +0.186); C4 MET (14.06 vs 15.24) -> CONFIRMED
   safe point C10: S1 MET (0 runs>a, worst 0.0077); S2 MET (-0.0068) -> CONFIRMED
TOTAL Q2: 432 runs; R_new runs>a 4; C10 runs>a 0
TOTAL QS: 432 runs; R_new runs>a 5; C10 runs>a 4
```

## Development set A (399 runs)
```
dev set A: 399 runs in common (hsq2 399, hsq 399, S5 399)
  hsq2 (audited)  recall 0.9285  mean segFAR 0.0034  runs>a 0  nav 13.01
  hsq (tested)    recall 0.9287  mean segFAR 0.0034  runs>a 0  nav 13.03
  S5 (old rule)   recall 0.9327  mean segFAR 0.0045  runs>a 1  nav 12.66
  hsq2 vs hsq: identical runs 96/399, delta recall -0.0002 [-0.0003, -0.0000], max |delta| 0.0079
  4s:countryside   n= 54  hsq2 0.833/0.0049/0  hsq 0.833/0.0049/0  S5 0.852/0.0056/0
  4s:office_loop   n= 54  hsq2 0.969/0.0002/0  hsq 0.970/0.0002/0  S5 0.969/0.0001/0
  4s:old_town      n= 54  hsq2 0.932/0.0009/0  hsq 0.932/0.0007/0  S5 0.946/0.0010/0
  boreas           n= 54  hsq2 0.962/0.0021/0  hsq 0.962/0.0022/0  S5 0.971/0.0027/0
  cmu              n= 54  hsq2 0.862/0.0066/0  hsq 0.863/0.0066/0  S5 0.852/0.0095/1
  nord             n= 54  hsq2 0.970/0.0026/0  hsq 0.970/0.0026/0  S5 0.968/0.0069/0
  oxford           n= 45  hsq2 0.943/0.0089/0  hsq 0.943/0.0089/0  S5 0.949/0.0078/0
  stlucia          n= 30  hsq2 0.985/0.0013/0  hsq 0.986/0.0013/0  S5 0.980/0.0013/0
```

## Generality sets: hsq2 | hsq (tested) | S5 (old rule) | runs identical hsq2 vs hsq
| Set | hsq2 | hsq | S5 | identical |
|---|---|---|---|---|
| holes 10 % (108) | 0.932 / 0.005 / 0 | 0.932 / 0.005 / 0 | 0.933 / 0.008 / 1 | 37/108 |
| holes 50 % (108) | 0.873 / 0.030 / 4 | 0.873 / 0.030 / 4 | 0.894 / 0.032 / 4 | 31/108 |
| natural off-map (36) | 0.943 / 0.003 / 0 | 0.943 / 0.003 / 0 | 0.952 / 0.010 / 2 | 16/36 |
| NCLT (6) | 0.770 / 0.002 / 0 | 0.768 / 0.001 / 0 | 0.781 / 0.005 / 0 | 0/6 |

## Seeds 70-72 with the old-rule reference (t70ref, reported late)
\`\`\`
== seeds 70-72, Q2 (causal hsq2), 144 runs
   R_new: recall 0.9255, mean segFAR 0.0035, runs>a 0, worst 0.0092, nav 13.97
   C10  : recall 0.9181, mean segFAR 0.0013, runs>a 0, worst 0.0042, nav 14.56
   vs tested hsq: identical runs 35/144; hsq recall 0.9259 msf 0.0034 runs>a 0; delta recall -0.0004 [-0.0005, -0.0002]
   Entry 23 rule vs R_old (144 runs): V1 MET (0 vs 1, 0.0035 vs 0.0053); V2 MET (-0.0053 [-0.0088, -0.0022]); V3 MET (13.97 vs 14.19)
   Entry 24/26 rule (144 runs): C1 MET; C2 MET (+0.1169 [+0.1006, +0.1337]); C3 MET (TAO26 valid=False runs>a 126 diff +0.087; Xu21 valid=False runs>a 83 diff +0.229; Claxton24 valid=False runs>a 101 diff +0.186); C4 MET (13.97 vs 15.24) -> CONFIRMED
   safe point C10: S1 MET (0 runs>a, worst 0.0042); S2 MET (-0.0074) -> CONFIRMED
\`\`\`
