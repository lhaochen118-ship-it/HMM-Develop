# Literature Gate (Bước 0) — CRSG có trùng ý tưởng với paper nào không?

*Ngày: 2026-10-28. Phương pháp: chỉ đọc paper (alphaXiv full-text), không đọc code. Đọc kỹ 9 paper sát nhất,
quét ~40 kết quả tìm kiếm theo các từ khóa trong handoff §4.*

## Kết luận một dòng

**CÓ TRÙNG — mạnh ở phần *method* (CRSG) và phần *conformal* (C2/C3); phần *reality-check* (filter regime-dependent
về reliability, condition-temperature inert, cơ chế NB8) chưa thấy ai làm.** Theo luật gate trong handoff, claim
"CRSG là method mới" **không đứng được** ở tầm A*. Không nên chạy tiếp Bước 1–3 với framing hiện tại.

## Phát hiện phụ quan trọng (lỗi đặt tên — phải sửa dù đi hướng nào)

Baseline gọi là **"SUE" trong toàn bộ NB2–NB14 thực chất là L2-distance tới NN** (`sqrt(2-2*max cos)`, xem
`nb*_src/20_lib.src: sue_uncertainty`). Trong Zaffar et al. (CVPR'24), đó là baseline **RUE "L2-distance"**; còn
**SUE thật = độ phân tán không gian (trace hiệp phương sai có trọng số) của pose top-K reference** (K=10, λ=350).
→ Mọi chỗ ghi "SUE 0.95/0.895/0.935" trong RESULTS/PAPER_DRAFT phải đổi thành "L2-NN (RUE)". SUE thật **chưa
từng được so sánh** — reviewer sẽ bắt lỗi này ngay.

## Ma trận chồng lấn

| Thành phần của ta | Paper trùng gần nhất | Mức trùng | Ghi chú |
|---|---|---|---|
| Feature margin top1−top2 | **PA-score** d1/d2 (Hausler'21), baseline chuẩn trong Zaffar CVPR'24, KappaPlace'26; Lowe ratio | **Mạnh** | Cùng tín hiệu |
| Feature NN-distance | **L2-distance RUE** (Zaffar CVPR'24, "đơn giản mà mạnh hơn BTL/STUN") | **Mạnh** | Chính là "SUE" của ta |
| Feature hình dạng phân phối điểm (entropy) | **RS / SD / SU** (Miller, Milford et al., RA-L 2026, arXiv 2510.13464): training-free, 9 descriptor gồm SALAD & MixVPR, 6 dataset | **Mạnh** | Họ không calibrate, chỉ AUC-PR |
| Classifier có giám sát trên thống kê vector khoảng cách → P(đúng trong tolerance) | **Integrity monitor**: Carson et al. RA-L'22 (SVM), **Claxton et al. RA-L'24** (MLP, 192 feature thống kê, có SALAD, có RobotCar/Nordland) | **Mạnh** | CRSG = trường hợp đặc biệt (logistic, 3 feature). Khác: họ đo precision/recall, không ECE/AURC |
| Calibrated confidence (ECE) cho VPR | **KappaPlace** (arXiv 2605.19435, 2026): vMF κ, có biến thể post-hoc frozen backbone, ECE@K | Trung bình | Học từ ảnh; ECE@K là ECE theo rank, khác ECE chuẩn |
| Conformal / risk control cho accept-reject VPR | **SAFEVPR** (arXiv 2605.28048, 05/2026): LTT + **Mondrian**, 23 setup cross-condition (Oxford RobotCar, NCLT, St Lucia) | **Mạnh với C2+C3** | Họ đã chỉ ra cosine+LTT **vỡ dưới condition shift** và Mondrian (theo score-bin) khôi phục — đúng thông điệp C2/C3 của ta |
| Chọn ngưỡng có calibration traversal, chuyển sang deployment | **Quantile Transfer** (IROS'26, arXiv 2602.04401), 7 descriptor gồm BoQ/MixVPR/SALAD | Trung bình | Mục tiêu 100% precision |
| "Sequence matching có thể làm tệ hơn" | **SMR predictor** (Hussaini, Fischer, Milford 2025, arXiv 2503.06840): Nordland + RobotCar, 7 descriptor | Một phần | Họ chỉ xét accuracy (PR-AUC), không xét calibration/off-map |
| Filter: reliability (ECE/AURC/off-map) tốt trên Nordland dày nhưng sụp trên RobotCar/CMU thưa; calibrate posterior không phục hồi discrimination (NB8) | — không tìm thấy — | **Thấp → còn mới** | Tài sản mạnh nhất còn lại |
| Condition-aware temperature trơ (τ spread 1.2–1.5×, ΔECE≈0) | — không tìm thấy — | Thấp | Negative nhỏ |
| Off-map detection | Route-MHT (thermal, learned, 2026); OOD tổng quát | Trung bình | Không dùng retrieval geometry calibrated |

## Paper đã đọc (full text)

- Zaffar, Nan, Kooij — *On the Estimation of Image-matching Uncertainty in VPR* (CVPR'24) — https://www.alphaxiv.org/abs/2404.00546
- Miller, Milford, Hafez, Ramchurn, Ehsan — *Through the Lens of Doubt* (RA-L'26) — https://www.alphaxiv.org/abs/2510.13464
- Claxton, Malone, Carson, Ford, …, Milford — *Improving VPR-Based Robot Navigation by Verifying Localization Estimates* (RA-L'24) — https://www.alphaxiv.org/abs/2407.08162
- Hussaini, Fischer, Milford — *Sequence-Matching Receptiveness Prediction* (2025) — https://www.alphaxiv.org/abs/2503.06840
- Sier et al. — *SAFEVPR: Patch-Based Conformal Verification* (2026) — https://www.alphaxiv.org/abs/2605.28048
- Yanko, Shavit — *KappaPlace* (2026) — https://www.alphaxiv.org/abs/2605.19435
- Rajani, Milford, Fischer — *Quantile Transfer for Operating Point Selection* (IROS'26) — https://www.alphaxiv.org/abs/2602.04401
- Trinh, Lyons — *Adaptive Thresholding via Negative Gaussian Mixture* (2025) — https://www.alphaxiv.org/abs/2512.09071
- Lu, Tanaka — *Route-MHT* (2026) — https://www.alphaxiv.org/abs/2607.04745

## Cái gì còn đứng được (tài sản cho bước tiếp)

1. **Reality-check về reliability theo regime**: sequential filter ≈ oracle trên Nordland dày (AURC 0.019 vs oracle
   0.018; off-map 0.99) nhưng thất bại trên RobotCar/CMU (off-map CMU 0.23); cơ chế NB8. SMR chỉ đo accuracy; SAFEVPR
   loại Nordland. → mới.
2. **Condition-temperature trơ** trên 2 dataset → negative result nhỏ nhưng sạch.
3. **Protocol** ECE + AURC + conf-AUROC + open-set + tolerance sweep: các paper VPR-uncertainty dùng AUC-PR (Zaffar,
   Miller), ECE@K (KappaPlace), precision@100% (Quantile Transfer) — chưa ai hợp nhất. → đóng góp vừa phải.
4. **Hạ tầng**: descriptor SALAD/DINOv2 đã trích trên 3 dataset, loader đã debug, conformal code.

## Hai hướng đi (đề xuất)

**A (khuyến nghị) — Reframe thành paper phân tích/benchmark + 1 bổ sung phương pháp nhỏ nhưng mới:**
"VPR reliability is regime-dependent: a cross-benchmark reality check of uncertainty estimators, sequential
filtering and conformal abstention".
- Hạ CRSG xuống thành *"calibrated combination of known RUE scores"* (baseline mạnh, không claim là method mới).
- Bắt buộc thêm baseline đúng: L2, PA-score, **SUE thật** (pose-spread), RS/SD/SU, integrity-MLP kiểu Claxton,
  SeqSLAM/HMM filter, (KappaPlace nếu khả thi) — tất cả qua cùng protocol.
- Bổ sung mới so với SAFEVPR: **Mondrian conformal theo điều kiện *suy ra không nhãn*** (ta đã có label-free
  condition tracking 0.974 từ CCBF) cho single-frame — C3 hiện tại dùng nhãn điều kiện ở test-time, đây là điểm yếu
  cần sửa và cũng là chỗ khác SAFEVPR (Mondrian theo score-bin).
- Bước 1 (RobotCar-Seasons chính thức) và Bước 2 (BoQ/MixVPR) **vẫn cần** cho hướng này (paper phân tích cần nhiều
  descriptor + protocol chuẩn). Venue thực tế: RA-L / ICRA / IROS; A* (CVPR) khó với paper phân tích.

**B — Quay lại Phase 2 (sinh ý tưởng mới)** dùng tài sản §"còn đứng được". Hạt giống:
- B1: conformal *label-free, shift-aware* cho VPR (Mondrian theo latent condition + test-time reweighting), so với
  SAFEVPR/Quantile Transfer.
- B2: *self-supervised calibration từ chính bản đồ* (pseudo-query từ multi-traversal của reference map) → reliability
  calibrated mà không cần query có nhãn.
- Rủi ro: tốn thêm nhiều vòng và có thể lại va chạm literature (mảng này đang nóng: 6/9 paper trên là 2025–2026).

**C — Chạy tiếp như cũ (không khuyến nghị):** reviewer sẽ trỏ ngay vào PA-score/L2 (Zaffar), RS/SD/SU (Miller),
integrity-MLP (Claxton) và SAFEVPR.
