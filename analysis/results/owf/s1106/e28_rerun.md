# Entry 28 — second audit: causal hindsight branch (HSI-VNc) in every column, 2026-11-07

Fresh groups, development set A and generality sets; pre-registered rules of Entries 23, 24, 26 re-applied (e28_eval2.py).

```
== seeds 64-66, Q2 (causal hsq2) + HSI-VNc, 144 runs
   R_new: recall 0.9327, mean segFAR 0.0058, runs>a 3, worst 0.0255, nav 14.88
   C10  : recall 0.9237, mean segFAR 0.0026, runs>a 0, worst 0.0131, nav 15.34
   vs same rule with HSI-VN (first audit): recall 0.9323 msf 0.0059 runs>a 4 nav 14.56; delta recall +0.0005 [-0.0005, +0.0014]
   Entry 23 rule vs R_old+HSI-VNc (144 runs; R_old 0.9362/0.0076/4/15.15): V1 MET (3 vs 4, 0.0058 vs 0.0076); V2 MET (-0.0035 [-0.0068, -0.0006]); V3 MET (14.88 vs 15.15)
== seeds 64-66, QS (strict hsq2s) + HSI-VNc, 144 runs
   R_new: recall 0.9324, mean segFAR 0.0075, runs>a 5, worst 0.0364, nav 15.13
   C10  : recall 0.9232, mean segFAR 0.0045, runs>a 4, worst 0.0280, nav 15.57
   vs same rule with HSI-VN (first audit): recall 0.9321 msf 0.0071 runs>a 5 nav 14.80; delta recall +0.0003 [-0.0007, +0.0013]
   Entry 23 rule vs R_old+HSI-VNc (144 runs; R_old 0.9362/0.0076/4/15.15): V1 NOT (5 vs 4, 0.0075 vs 0.0076); V2 MET (-0.0038 [-0.0071, -0.0009]); V3 MET (15.13 vs 15.15)
== seeds 67-69, Q2 (causal hsq2) + HSI-VNc, 144 runs
   R_new: recall 0.9275, mean segFAR 0.0029, runs>a 0, worst 0.0096, nav 12.58
   C10  : recall 0.9204, mean segFAR 0.0007, runs>a 0, worst 0.0029, nav 12.93
   vs same rule with HSI-VN (first audit): recall 0.9268 msf 0.0029 runs>a 0 nav 12.53; delta recall +0.0007 [-0.0002, +0.0015]
   Entry 23 rule vs R_old+HSI-VNc (144 runs; R_old 0.9311/0.0033/1/12.12): V1 MET (0 vs 1, 0.0029 vs 0.0033); V2 MET (-0.0036 [-0.0068, -0.0007]); V3 MET (12.58 vs 12.12)
   HSI-VNc baseline: recall 0.7945 msf 0.0030 runs>a 0 nav 14.51 (HSI-VN first audit: 0.7910 / 0 / 15.48)
   Entry 24/26 rule (144 runs): C1 MET; C2 MET (+0.1330 [+0.1150, +0.1514]); C3 MET (TAO26 valid=False runs>a 130 diff +0.094; Xu21 valid=False runs>a 81 diff +0.235; Claxton24 valid=False runs>a 104 diff +0.190); C4 MET (12.58 vs 14.51) -> CONFIRMED
   safe point C10: S1 MET (0 runs>a, worst 0.0029); S2 MET (-0.0071) -> CONFIRMED
== seeds 67-69, QS (strict hsq2s) + HSI-VNc, 144 runs
   R_new: recall 0.9271, mean segFAR 0.0031, runs>a 0, worst 0.0095, nav 12.59
   C10  : recall 0.9198, mean segFAR 0.0010, runs>a 0, worst 0.0033, nav 12.97
   vs same rule with HSI-VN (first audit): recall 0.9266 msf 0.0032 runs>a 0 nav 12.54; delta recall +0.0006 [-0.0003, +0.0014]
   Entry 23 rule vs R_old+HSI-VNc (144 runs; R_old 0.9311/0.0033/1/12.12): V1 MET (0 vs 1, 0.0031 vs 0.0033); V2 MET (-0.0039 [-0.0072, -0.0010]); V3 MET (12.59 vs 12.12)
   HSI-VNc baseline: recall 0.7945 msf 0.0030 runs>a 0 nav 14.51 (HSI-VN first audit: 0.7910 / 0 / 15.48)
   Entry 24/26 rule (144 runs): C1 MET; C2 MET (+0.1326 [+0.1149, +0.1509]); C3 MET (TAO26 valid=False runs>a 130 diff +0.094; Xu21 valid=False runs>a 81 diff +0.235; Claxton24 valid=False runs>a 104 diff +0.190); C4 MET (12.59 vs 14.51) -> CONFIRMED
   safe point C10: S1 MET (0 runs>a, worst 0.0033); S2 MET (-0.0073) -> CONFIRMED
== seeds 70-72, Q2 (causal hsq2) + HSI-VNc, 144 runs
   R_new: recall 0.9263, mean segFAR 0.0034, runs>a 0, worst 0.0087, nav 14.01
   C10  : recall 0.9188, mean segFAR 0.0013, runs>a 0, worst 0.0038, nav 14.62
   vs same rule with HSI-VN (first audit): recall 0.9255 msf 0.0035 runs>a 0 nav 13.97; delta recall +0.0008 [-0.0001, +0.0017]
   Entry 23 rule vs R_old+HSI-VNc (144 runs; R_old 0.9313/0.0049/1/14.19): V1 MET (0 vs 1, 0.0034 vs 0.0049); V2 MET (-0.0050 [-0.0084, -0.0019]); V3 MET (14.01 vs 14.19)
   HSI-VNc baseline: recall 0.8098 msf 0.0026 runs>a 0 nav 15.44 (HSI-VN first audit: 0.8087 / 0 / 15.24)
   Entry 24/26 rule (144 runs): C1 MET; C2 MET (+0.1165 [+0.1002, +0.1329]); C3 MET (TAO26 valid=False runs>a 126 diff +0.087; Xu21 valid=False runs>a 83 diff +0.230; Claxton24 valid=False runs>a 101 diff +0.187); C4 MET (14.01 vs 15.44) -> CONFIRMED
   safe point C10: S1 MET (0 runs>a, worst 0.0038); S2 MET (-0.0075) -> CONFIRMED
== seeds 70-72, QS (strict hsq2s) + HSI-VNc, 144 runs
   R_new: recall 0.9259, mean segFAR 0.0040, runs>a 0, worst 0.0116, nav 14.15
   C10  : recall 0.9190, mean segFAR 0.0019, runs>a 0, worst 0.0071, nav 14.75
   vs same rule with HSI-VN (first audit): recall 0.9252 msf 0.0041 runs>a 0 nav 14.06; delta recall +0.0008 [-0.0001, +0.0017]
   Entry 23 rule vs R_old+HSI-VNc (144 runs; R_old 0.9313/0.0049/1/14.19): V1 MET (0 vs 1, 0.0040 vs 0.0049); V2 MET (-0.0053 [-0.0088, -0.0023]); V3 MET (14.15 vs 14.19)
   HSI-VNc baseline: recall 0.8098 msf 0.0026 runs>a 0 nav 15.44 (HSI-VN first audit: 0.8087 / 0 / 15.24)
   Entry 24/26 rule (144 runs): C1 MET; C2 MET (+0.1161 [+0.0999, +0.1325]); C3 MET (TAO26 valid=False runs>a 126 diff +0.087; Xu21 valid=False runs>a 83 diff +0.230; Claxton24 valid=False runs>a 101 diff +0.187); C4 MET (14.15 vs 15.44) -> CONFIRMED
   safe point C10: S1 MET (0 runs>a, worst 0.0071); S2 MET (-0.0069) -> CONFIRMED
TOTAL Q2: 432 runs; R_new runs>a 3; C10 runs>a 0
TOTAL QS: 432 runs; R_new runs>a 5; C10 runs>a 4
dev set A (399): HSI-VNc 0.9287 / worst 0.0093 / mean 0.0032 / runs>a 0 / nav 13.54 | HSI-VN 0.9285 / 0.0089 / 0.0034 / 0 / 13.01 | delta recall +0.0002 [-0.0005, +0.0008]
   4s:countryside   HSI-VNc 0.836/0.0024/0  HSI-VN 0.833/0.0049/0
   4s:office_loop   HSI-VNc 0.969/0.0002/0  HSI-VN 0.969/0.0002/0
   4s:old_town      HSI-VNc 0.933/0.0014/0  HSI-VN 0.932/0.0009/0
   boreas           HSI-VNc 0.962/0.0019/0  HSI-VN 0.962/0.0021/0
   cmu              HSI-VNc 0.859/0.0062/0  HSI-VN 0.862/0.0066/0
   nord             HSI-VNc 0.970/0.0026/0  HSI-VN 0.970/0.0026/0
   oxford           HSI-VNc 0.942/0.0093/0  HSI-VN 0.943/0.0089/0
   stlucia          HSI-VNc 0.985/0.0016/0  HSI-VN 0.985/0.0013/0
holes 10 % (108): HSI-VNc 0.9319 / worst 0.0038 / mean 0.0016 / runs>a 0 / nav 9.23 | HSI-VN 0.9317 / 0.0054 / 0.0020 / 0 / 9.49 | delta recall +0.0002 [-0.0006, +0.0009]
holes 50 % (108): HSI-VNc 0.8724 / worst 0.0280 / mean 0.0067 / runs>a 4 / nav 21.91 | HSI-VN 0.8728 / 0.0302 / 0.0069 / 4 / 20.28 | delta recall -0.0003 [-0.0021, +0.0013]
natural off-map (36): HSI-VNc 0.9448 / worst 0.0039 / mean 0.0039 / runs>a 0 / nav 108584.74 | HSI-VN 0.9429 / 0.0025 / 0.0025 / 0 / 85447.70 | delta recall +0.0019 [+0.0004, +0.0036]
NCLT (6): HSI-VNc 0.7691 / worst 0.0011 / mean 0.0011 / runs>a 0 / nav 4.75 | HSI-VN 0.7696 / 0.0016 / 0.0016 / 0 / 4.82 | delta recall -0.0005 [-0.0015, +0.0004]
```

## Generality and development set A, every column with HSI-VNc (e28_gen_eval2.py)

| Set | Ours (hsq2 + HSI-VNc) | OWF-HWA-S5 (+ HSI-VNc) | HSI-VNc |
|---|---|---|---|
| holes 10 % (108) | 0.932 / 0.004 / 0 | 0.933 / 0.008 / 1 | 0.777 / 0.003 / 0 |
| holes 50 % (108) | 0.872 / 0.028 / 4 | 0.894 / 0.030 / 4 | 0.751 / 0.027 / 4 |
| natural off-map (36) | 0.945 / 0.004 / 0 | 0.954 / 0.012 / 1 | 0.756 / 0.011 / 0 |
| NCLT (6) | 0.769 / 0.001 / 0 | 0.780 / 0.003 / 0 | — |

dev set A (399): final 0.9287 / worst 0.0093 / mean 0.0032 / runs>a 0 / nav 13.54 | S5 0.9328 / 0.0092 / 0.0040 / 0 / 12.36 | delta recall -0.0041 [-0.0061, -0.0022]
   4s:countryside   final 0.836/0.0024/0/22.4  S5 0.855/0.0022/0/21.7
   4s:office_loop   final 0.969/0.0002/0/9.0  S5 0.969/0.0002/0/8.9
   4s:old_town      final 0.933/0.0014/0/29.1  S5 0.946/0.0013/0/20.9
   boreas           final 0.962/0.0019/0/6.6  S5 0.971/0.0025/0/5.3
   cmu              final 0.859/0.0062/0/3.7  S5 0.848/0.0092/0/4.3
   nord             final 0.970/0.0026/0/5.0  S5 0.968/0.0069/0/6.2
   oxford           final 0.942/0.0093/0/18.3  S5 0.949/0.0082/0/17.7
   stlucia          final 0.985/0.0016/0/16.3  S5 0.980/0.0013/0/16.6

## End-to-end causality test (analysis/tests/test_hsi_causality.py)
```
== cmu_cosplace_s64 (hybrid navcache of the final rule, seeds 64-67)
HSI-VN   cut 0.2 (R=4279): reports changed in the past: 1837 of 4280 frames (2282 reports)
HSI-VN   cut 0.5 (R=10697): reports changed in the past: 2839 of 10698 frames (6889 reports)
HSI-VN   cut 0.8 (R=17116): reports changed in the past: 988 of 17117 frames (10982 reports)
HSI-VNc  cut 0.2 (R=4279): reports changed in the past: 0 of 4280 frames (2267 reports)
HSI-VNc  cut 0.5 (R=10697): reports changed in the past: 0 of 10698 frames (6900 reports)
HSI-VNc  cut 0.8 (R=17116): reports changed in the past: 0 of 17117 frames (11037 reports)
PASS
== nord_cosplace_s65 (hybrid navcache of the final rule, seeds 64-67)
HSI-VN   cut 0.2 (R=2700): reports changed in the past: 730 of 2701 frames (1134 reports)
HSI-VN   cut 0.5 (R=6750): reports changed in the past: 197 of 6751 frames (3826 reports)
HSI-VN   cut 0.8 (R=10800): reports changed in the past: 3 of 10801 frames (6597 reports)
HSI-VNc  cut 0.2 (R=2700): reports changed in the past: 0 of 2701 frames (1134 reports)
HSI-VNc  cut 0.5 (R=6750): reports changed in the past: 0 of 6751 frames (3825 reports)
HSI-VNc  cut 0.8 (R=10800): reports changed in the past: 0 of 10801 frames (6603 reports)
PASS
== 4s_old_town_cosplace_s67 (hybrid navcache of the final rule, seeds 64-67)
HSI-VN   cut 0.2 (R=1969): reports changed in the past: 586 of 1970 frames (1243 reports)
HSI-VN   cut 0.5 (R=4924): reports changed in the past: 508 of 4925 frames (3143 reports)
HSI-VN   cut 0.8 (R=7879): reports changed in the past: 165 of 7880 frames (4923 reports)
HSI-VNc  cut 0.2 (R=1969): reports changed in the past: 0 of 1970 frames (1245 reports)
HSI-VNc  cut 0.5 (R=4924): reports changed in the past: 0 of 4925 frames (3206 reports)
HSI-VNc  cut 0.8 (R=7879): reports changed in the past: 0 of 7880 frames (5015 reports)
PASS
```
