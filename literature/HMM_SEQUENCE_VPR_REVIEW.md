# Tổng quan: HMM / Bayes-filter / sequence-based cho Visual Localization & Navigation

*Viết 2026-10-28. Mục đích: trước khi đề xuất ý tưởng mới, Claude đọc file này để KHÔNG trùng method/contribution
đã có. Chỉ đọc paper (không đọc repo code).*

**Mức độ đọc:**
- **[F]** đọc full text qua alphaXiv trong phiên này.
- **[R]** đọc report/abstract của alphaXiv.
- **[C]** chỉ biết qua trích dẫn trong các paper [F], hoặc qua kiến thức nền. Phải verify lại trước khi trích số liệu.

---

## 0. Bức tranh chung (5 dòng)

1. Bài toán chuẩn hoá thành: state rời rạc = index ảnh map (place) hoặc pose liên tục; observation = similarity của
   global descriptor; transition = band quanh index (vận tốc) hoặc odometry. Suy luận bằng forward filter, Viterbi,
   forward–backward, hoặc particle filter (MCL).
2. Các hướng đã khai thác: (a) chuẩn hoá emission; (b) transition dùng odometry 1/3-dof; (c) smoothing ngược;
   (d) trạng thái **off-map / new place**; (e) map tăng trưởng và nén map; (f) độ dài sequence động;
   (g) học sequence descriptor; (h) introspection (dự đoán khi nào sequence matching có lợi); (i) CRF học được trên
   database không có thứ tự.
3. Quyết định accept/reject hầu như luôn dựa trên **ngưỡng heuristic** trên belief/score: τ_thres, MaxAP ≥ γ,
   R@99%P được tune bằng nhãn. **Không** paper HMM nào cho đảm bảo thống kê (FAR/FDR) dưới appearance shift.
4. Emission hầu hết là `exp(−λ‖z_q − z_r‖)`. λ được tune hoặc chuẩn hoá theo quantile khoảng cách của frame đầu
   (Xu'20). Không ai calibrate emission sao cho likelihood ratio có nghĩa xác suất qua các điều kiện ánh sáng/mùa.
5. Kinh nghiệm nội bộ của chúng ta (CCBF, Entries 1–10): temperature/likelihood theo điều kiện **trơ** với HMM
   filter. Calibrate belief không cứu được filter khi descriptor đã mạnh (SALAD). Đây là negative result đã có.

---

## 1. Họ SeqSLAM / sequence matching (không xác suất)

| Paper | Method (tóm tắt) | (+) Đóng góp | (−) Hạn chế |
|---|---|---|---|
| **SeqSLAM** (Milford & Wyeth, ICRA'12) [C] | Ảnh downsample + patch-norm, SAD. Contrast-normalise ma trận khác biệt. Tìm quỹ đạo thẳng trong ma trận theo một dải vận tốc. | Chứng minh sequence thắng day↔night, summer↔winter ngay cả với feature rất yếu. | Giả định vận tốc gần hằng và route lặp lại. Nhạy viewpoint. Latency = độ dài sequence. Không có xác suất/confidence. |
| **OpenSeqSLAM2.0** (Talbot'18) [C] | Toolbox, tham số hoá search. | Chuẩn hoá baseline. | Như trên. |
| **Network flows** (Naseer'14 AAAI; T-RO'18) [C] | Data association = min-cost flow trên đồ thị (query × map), cho phép node "hidden/non-matching". | Xử lý được đoạn không match. Tối ưu toàn cục. | Offline/batch. Chi phí non-match là heuristic. |
| **Lazy data association** (Vysotska & Stachniss, RA-L'16) và **GPS-prior** (ICRA'15) [C] | Mở rộng đồ thị lazily (A*-like). Ngưỡng non-match ŵ. | Online, nhanh, chịu được vận tốc thay đổi. | Ngưỡng tay. Không có đảm bảo. |
| **Adaptive thresholding for sequence-based PR** (Vysotska et al., ICRA'25) [C, qua Trinh&Lyons'25] | Tune ngưỡng similarity trên một batch nhỏ của sequence cho từng query. | Ngưỡng thích nghi online. | Per-query tuning. Giả định "đa số cặp là khác nơi". Không có đảm bảo FAR. **Gần SelfCal nhất trong họ này, cần trích dẫn và phân biệt.** |
| **Beyond ANN** (Schubert, Neubert, Protzel, ICRA'21) [C] | Dùng cấu trúc sequence/so sánh nội bộ. Ngưỡng θ_DB ước lượng từ dữ liệu, giả định số cặp khác nơi nhiều hơn. | Ngưỡng tự động, không nhãn. | Heuristic, không có đảm bảo, không xét shift. Đã ghi trong Gate 2. |
| **ABLE** (Arroyo'15) [C] | Binary sequence descriptor. | Rẻ. | Yếu với viewpoint. |
| **ConvSequential-SLAM** (Tomită'20) [R] | Sequence length động theo entropy, HOG. | Training-free. | Feature cũ. |
| **Weighted / anchored sequence** (Carson, Ford, Milford, ICRA'23) [F] | Unsupervised quality prediction: match được coi là "tốt" nếu argmin khoảng cách và argmax gradient của vector khoảng cách trùng nhau ±1 frame. Hạ khoảng cách các điểm "tốt" rồi convolution SeqSLAM. | Training-free, real-time (<20 ms), tăng AUC ở vùng high-precision. | Cần reference có thứ tự. Kết quả binary, không có xác suất. Recall bị cắt. Không có đảm bảo. Bản supervised trước đó (RA-L'22) cần 2 traverse có GT. |
| **SMR predictor** (Hussaini, Fischer, Milford, 2025, arXiv 2503.06840) [F] | MLP supervised dự đoán, cho từng frame, sequence matching sẽ giữ/sửa/làm hỏng match (4 lớp). Input: 4 attribute từ ma trận khoảng cách (min-sum rate, …). Loại match bị dự đoán sai sau SM. | Agnostic với 7 descriptor (gồm SALAD, MixVPR). Giảm AOC trung bình 26 %. | Supervised trên từng dataset (500 ảnh có GT). F1 chỉ 0.37–0.54. Restore match thất bại. Có trường hợp xấu đi (RobotCar AP-GeM, CosPlace). Không có đảm bảo. |

## 2. Họ HMM / discrete Bayes filter (trọng tâm)

| Paper | Method | (+) | (−) |
|---|---|---|---|
| **HMM sequence matching** (Hansen & Browning, IROS'14) [C] | HMM trên ma trận similarity. Viterbi tìm quỹ đạo phi tuyến (thay đường thẳng của SeqSLAM). | Cho phép vận tốc thay đổi. | Phải giữ cả ma trận similarity query×DB nên không scale. Không có off-map. |
| **Multi-Process Fusion, MPF** (Hausler, Jacobson, Milford, RA-L'19) [F] | 4 "cảm biến ảo" (SAD, HOG, CNN max-pool, CNN argmax-coord). Emission = Σ log observation đã chuẩn hoá về [0.001, 0.999] và floor dưới O_thresh. Transition band (V_max = 5 frame). Viterbi bỏ initial prior. **Độ dài sequence động** theo rate-of-change của quality score (tỉ số best/second ngoài cửa sổ, dạng log). Vote loại method tệ nhất mỗi frame. | Fusion nhiều xử lý ảnh trên một camera. Latency giảm tới 5 frame. F1 trung bình 0.96. | Giả định độc lập có điều kiện giữa các method (sai). Chuẩn hoá emission ad-hoc. Novelty = ngưỡng quality heuristic. Không có đảm bảo. Feature cũ (HybridNet). |
| **Scalable PR under appearance change** (Doan et al., ICCV'19) [F] | HMM trên đồ thị map. Node = mọi ảnh của mọi video, cạnh nối ảnh overlap FOV, trọng số Gaussian theo khoảng cách index. Emission xấp xỉ từ L-NN của k-means tree (SIFT-VLAD, PCA 4096), giá trị nền e^{−β/σ}. MaxAP belief ≥ γ = 0.3 thì accept, ngược lại là new place. **Map update:** cull node mới trùng chỗ cũ, combine node cũ cùng nơi, giữ ma trận transition không tăng. Không cần GNSS/VO. | Map tăng trưởng liên tục nhưng chi phí suy luận không tăng (~4 ms). Gộp các traverse khác điều kiện. Retrain vài phút thay vì vài giờ (MapNet). | Accept/new-place bằng ngưỡng γ heuristic. Không đo FAR off-map. Lỗi trung bình vẫn 15–30 m với một số sequence. Descriptor cũ. Giả định camera cùng hướng. |
| **Filtering approaches** (Doan et al., DICTA'19, arXiv 1811.08063) [F] | HMM (band v_max, emission exp(−D/σ)) cùng MCVL (particle 6-DoF, measurement = mean-shift trên top-R pose). GTA-V synthetic + RobotCar. | Chứng minh filter + retrieval thắng pose regression (PoseNet/MapNet) dưới appearance change. | Không có off-map. Ngưỡng/tham số tay. So sánh với baseline yếu. |
| **Probabilistic VPR for hierarchical localization** (Xu, Sünderhauf, Milford, RA-L'20, arXiv 2105.03091) [F] | (1) Topological discrete Bayes filter, band transition [w_l, w_u]. Emission exp(−λ‖·‖) với λ = log δ / (d_0.975 − d_0.025) tính từ **quantile khoảng cách của query đầu tiên**. (2) 6-DoF MCL kết hợp VO. Measurement Σ_k exp(−λ1 d_desc − λ2 d_SE3). **Convergence detection:** khối belief trong cửa sổ quanh MAP > τ thì localize, nên latency tự scale theo aliasing. | R@99%P tăng mạnh (đêm: single 1–5 %, Topological 58–80 %). Latency tự thích nghi. Chạy được ở tolerance 3–5 m. | MCL cần pose RTK cho map. Khó tune (λ2, Σ). Ngưỡng τ chọn bằng PR curve có nhãn. Giả định query đi lại đúng route của map. |
| **Topometric localization with new place awareness** (Xu, Fischer, Sünderhauf, Milford, RA-L'21, arXiv 2107.07707) [F] | Discrete Bayes filter trên map topometric. Transition dùng **odometry 3-dof**: khoảng cách Mahalanobis đến đoạn quỹ đạo nội suy. **Off-map state O:** E_{i→O} = min_j χ²₃(d²_ij); emission của O = likelihood của match thứ k (k ≫ 1); E_{O→O} cố định, O→map đồng đều. Forward–backward smoothing cho loop closure; convergence score τ. | **Off-map/detour state đầu tiên cho VPR appearance-invariant.** R@99%P trên route có detour tăng từ 69→96 % và 76→98 %. Smoothing hơn hẳn MCL. Có code. | Emission off-map = "match thứ k" là heuristic, không calibrate. E_{O→O} và ngưỡng τ tune trên dữ liệu có nhãn ("parameters optimized on the LCD task"). Chỉ RobotCar, một reference. Không có đảm bảo FAR. Off-map chỉ phát hiện được khi tích luỹ đủ odometry bất nhất. |
| **Using image sequences for long-term visual localization** (Stenborg, Sattler, Hammarstrand, 3DV'20) [C] | Discrete filter với odometry 1-D (forward) và backward smoothing để lọc retrieval trước khi refine pose 6-DoF. | Smoothing có ích cho hierarchical localization. | Giả định không có route deviation (Xu'21 chỉ ra điều này làm hỏng kết quả khi có detour). |
| **Bayesian selective fusion / reference curation** (Molloy, Fischer, Milford, Nair, RA-L'21) [C] | Bayes chọn tập reference (nhiều traverse) để fuse cho từng query. | Tận dụng multi-reference. | Không phải bài toán accept/off-map. |
| **CAT-SLAM / CAT-Graph** (Maddern, Milford, Wyeth, IJRR'12, RSS'12) [C] | Particle filter trên quỹ đạo appearance liên tục (FAB-MAP). New place = bài toán structured prediction. | Có new-place awareness sớm. | Feature BoW SURF không chịu được appearance change. |
| **FAB-MAP** (Cummins & Newman, IJRR'08) [C] | Recursive Bayes trên BoW, có mô hình new place qua sampling. | Mô hình new-place có xác suất. | BoW handcrafted. Không chịu shift mạnh. |
| **Badino topometric** (IV'11) [C] | Discrete Bayes filter, SURF cùng odometry 1-D. | Topometric sớm. | Như trên. |

## 3. Họ learned sequence / CRF / introspection gần đây

| Paper | Method | (+) | (−) |
|---|---|---|---|
| **SeqNet / SeqMatchNet** (Garg & Milford, RA-L'21, CoRL'21) [C] | Học sequence descriptor (1-D conv). Hierarchical: SeqNet lọc rồi re-rank bằng single-image. SeqMatchNet học contrastive cùng sequence matching. | Sequence descriptor ngắn mà mạnh. | Cần train. Giả định reference có thứ tự. Không có confidence. |
| **SeqVLAD / learning sequential descriptors** (Mereu et al., RA-L'22), **JIST** (Berton et al., 2024), **spatio-temporal attention** (2023), **DeepSeqSLAM** (CNN+RNN, 2020) [R] | Aggregate sequence thành một descriptor học được. | Giữ SOTA recall cho sequence-VPR. | Không có off-map/confidence. Cần train trên MSLS. |
| **TRAIL** (Kloepfer & Wenzel, 2026, arXiv 2609.07373) [R] | Query là sequence nhưng **database không có thứ tự** (chỉ có vị trí). Linear-chain CRF trên top-K candidate (K = 10, frozen MegaLoc). Emission: MLP trên tích global descriptor. Transition: CNN trên tương quan local DINOv2, so sánh "chuyển động query" với "chuyển động reference". Có **dustbin state**. Aggregation xác suất theo không gian κ. | Định nghĩa task mới: sequence query với map không thứ tự. MSLS R@10 58.3→66.7, Nordland +9.3 điểm, chi phí bằng 1/7–1/9 re-ranker. | Cần train (MSLS). Phụ thuộc top-K. Không dùng odometry. Dustbin không calibrate, không có đảm bảo. PairVPR vẫn hơn trên 4Seasons. |
| **Route-MHT / TAO** (Lu & Tanaka, 2026, arXiv 2607.04745, thermal) [R] | Thay MHT bằng K = 100 nhánh hypothesis song song. Mỗi nhánh giải SE(2) Procrustes có trọng số, có ràng buộc vận tốc và chi phí similarity, bằng batched SVD (O(KN), <1.2 ms). Singular value dùng làm uncertainty. Đánh giá **"zero-leakage", map-out bằng cách xoá các đoạn map liên tiếp**. | Fail-safe macro-scale: FPR từ 32.6 % xuống 4.9–11.9 %. Kidnapped recovery trong 4–5 frame. Tự công bố giới hạn ở micro-scale (AUC 0.54–0.57 ở 5 m). | Cần odometry. Không có đảm bảo thống kê. Ngưỡng tune trên calibration split có nhãn. Chỉ thermal. **Cần trích dẫn: protocol map-out = xoá đoạn map giống leave-block-out của SelfCal ở mặt *đánh giá*.** |
| **SAFEVPR** (2026, arXiv 2605.28048) [đã đọc ở Gate 1] | Conformal verification (LTT/Mondrian) trên patch-score cho sequence VPR cross-condition. | Có đảm bảo conformal. | Cần nhãn calibration từ các điều kiện khác. Gate 1 và SelfCal Table 2a cho thấy LOCO vi phạm 38/138. |
| **Quantile Transfer** (2026, arXiv 2602.04401) [Gate 2] | Ánh xạ ngưỡng qua quantile của batch deployment. | Label-free tại deployment. | Vi phạm 64/138 trong benchmark của ta. |
| **Integrity / introspection** (Carson'22 RA-L supervised, Claxton'24 RA-L verify estimates) [C] | Dự đoán in-tolerance từ ma trận khoảng cách hoặc kiểm chứng ước lượng. | Mở hướng "localization integrity". | Supervised, cần GT target-domain. |
| **Training-free uncertainty RS/SD/SU** (Miller, Milford, …, 2025, arXiv 2510.13464) [R] | RS = trung bình s_i/s_1 (i = 2..k), SD = median/best, SU = 0.5·RS + 0.5·SD. Training-free, <0.03 ms. | AUC-PR 0.92 trên 9 descriptor × 6 dataset, gần GV. | Chỉ là score xếp hạng, không có ngưỡng có đảm bảo. Phải chọn ngưỡng bằng nhãn. Đã có trong Gate 1 (RS-SD-SU) và là baseline của SelfCal. |
| **Adaptive thresholding via negative GMM** (Trinh & Lyons, 2025, arXiv 2512.09071) [F] | Ngưỡng **riêng cho từng place** = trung bình (có trọng số 1/σ²) của các mean similarity giữa ảnh của place đó và **ảnh của các place khác** (negative statistics). Filter-then-rank. | Tự động, không cần nhãn ngoài place-id. Tăng R@1 trên mini-dataset (GardensPoint 20 place, SFU, Nordland). | Cần nhiều ảnh mỗi place trong DB (multi-condition). Không có đảm bảo FAR. Không xét off-map. Không xét shift (DB đã chứa mọi điều kiện). Dataset rất nhỏ. Không có lý thuyết. **Trùng một phần ý "dùng negatives trong map" của SelfCal: phải trích dẫn. Khác biệt: SelfCal dùng held-out *spatial block* làm off-map null, conformal p-value, statistic bất biến affine, có đảm bảo dưới shift.** |

## 4. "Ý tưởng đã bị chiếm": checklist chống trùng lặp

Một ý tưởng mới **không được** là (hoặc chỉ là) những điều sau, vì đã có paper:

1. HMM/Viterbi thay đường thẳng SeqSLAM (Hansen'14). Banded transition theo vận tốc (Doan'19, Xu'20).
2. Emission exp(−λd) với λ chuẩn hoá theo quantile khoảng cách (Xu'20). Emission = log-sum nhiều descriptor (MPF'19).
3. Odometry 1-dof hoặc 3-dof trong transition (Stenborg'20, Xu'21). Forward–backward smoothing (Stenborg'20, Xu'21).
4. **Off-map / new-place state trong HMM** (Xu'21; FAB-MAP/CAT-SLAM sớm hơn). Dustbin state trong CRF (TRAIL'26).
5. Độ dài sequence động theo quality (MPF'19, Bruce'17 "Look no further"). Latency tự scale theo convergence (Xu'20).
6. Map tăng trưởng, cull/combine node (Doan'19). Multi-experience (Churchill & Newman'13).
7. Học sequence descriptor (SeqNet, SeqVLAD, JIST). CRF học được trên DB không thứ tự (TRAIL'26).
8. Introspection cho sequence matching (SMR'25). Unsupervised gradient-consensus (Carson'23). RS/SD/SU (Miller'25).
   Negative-stat threshold (Trinh & Lyons'25). Adaptive threshold per batch (Vysotska'25, Schubert'21).
9. Multi-hypothesis/Procrustes back-end cho OOD/map-out (TAO'26). Protocol đánh giá xoá đoạn map (TAO'26).
10. Temperature/likelihood theo điều kiện cho HMM: **negative result nội bộ** (CCBF). Không lặp lại.

## 5. Khoảng trống còn mở (gợi ý cho Claude sau này)

- **Đảm bảo thống kê cho quyết định của filter/HMM.** Chưa paper nào cho "P(accept loop closure | robot đang
  off-map) ≤ α" dưới appearance/domain shift mà không cần nhãn. SelfCal làm điều này cho từng frame. Mở rộng sang
  **sequence** là khoảng trống tự nhiên: calibrate statistic của cả cửa sổ trên *pseudo-sequence* của chính map
  (các traversal giữ ngoài). Dependence giữa các frame khi đó được hấp thụ, nên không cần giả định độc lập. Chưa
  thấy paper nào làm. Cần kiểm tra thêm keyword "conformal sequential test / e-process place recognition" trước
  khi claim.
- **Off-map state được calibrate:** emission của trạng thái O trong Xu'21 là "match thứ k", một heuristic. Có thể
  thay bằng likelihood ratio ước lượng từ map null (two-groups/π0). Cần thận trọng vì thí nghiệm nội bộ đã cho
  thấy calibrate likelihood không cứu được filter; phải đo FAR, không chỉ R@99%P.
- **Domain shift (query từ thành phố khác):** thí nghiệm nội bộ 2026-10-28 cho thấy statistic chuẩn hoá theo
  spread (z_far, z_gap, T_spacing) có thể **anti-conservative** với query ngoại miền (CosPlace, map CMU, query
  RobotCar: FAR 0.13 tại α = 0.05). Raw max-sim thì bảo thủ. Paper HMM nào dùng score chuẩn hoá (MPF, Xu'20 λ
  theo quantile) đều có thể dính lỗi này nhưng chưa ai đo.
- **Map không thứ tự cùng đảm bảo:** TRAIL có dustbin nhưng không calibrate. Kết hợp với SelfCal là hướng mở.

## 6. Tài liệu (ID alphaXiv/arXiv)

2107.07707 (Xu'21), 2105.03091 (Xu'20), 1908.00178 (Doan ICCV'19), 1811.08063 (Doan DICTA'19), 1903.03305 (MPF),
2503.06840 (SMR), 2307.01464 (Carson'23), 2609.07373 (TRAIL), 2607.04745 (TAO/Route-MHT), 2512.09071 (Trinh &
Lyons), 2510.13464 (RS/SD/SU), 2605.28048 (SAFEVPR), 2602.04401 (Quantile Transfer), 2011.08518 (DeepSeqSLAM),
2207.03868 (SeqVLAD), 2403.19787 (JIST), 1804.02156 (OpenSeqSLAM2), 2009.13454 (ConvSequential-SLAM).
Chưa có arXiv/chưa đọc: Hansen & Browning IROS'14, SeqSLAM ICRA'12, Naseer AAAI'14/T-RO'18, Vysotska RA-L'16 &
ICRA'25, Stenborg 3DV'20, Molloy RA-L'21, Schubert ICRA'21.
