# Báo cáo: "Phương pháp chỉ đang thận trọng hơn?" — chẩn đoán, phương pháp CPC-SC+CS và đánh giá theo đường cong vận hành

*Branch `hmm-navigation-3`, 2026-10-31. Nhật ký chi tiết: `RESEARCH_LOG.md` Entry 25. Lý thuyết: `paper/cpc_theory.md` §3d.
Mã: `analysis/cpc_sc.py` (luật đề xuất), `oc_curves.py`, `oc_matched.py`, `lodo_select.py`, `recall_diag.py`.*

## 1. Câu hỏi phản biện

Phương pháp trước (CPC-HMM +TCEmin, Entry 24) có sai số điều hướng thấp nhưng recall cũng thấp. Phản biện: "mô hình chỉ
thận trọng hơn, nên ít sai nhưng cũng bắt ít mẫu đúng; không có bằng chứng nó tốt hơn". Câu hỏi đúng về mặt phương pháp
luận: mỗi luật chấp nhận là "báo khi điểm s_t vượt ngưỡng θ"; điểm mặc định chỉ là **một điểm** trên đường cong
(recall(θ), FL(θ), segFAR(θ)). Luật tốt hơn phải có đường cong **cao hơn** (nhiều fix đúng hơn ở cùng mức báo sai), không
chỉ có θ cao hơn.

## 2. Chẩn đoán (kết luận: phản biện đúng một phần với phương pháp cũ)

- **Recall mất ở chuỗi hiện diện, không ở chuỗi vị trí.** Với descriptor yếu, chuỗi vị trí vẫn đúng chỗ phần lớn thời
  gian nhưng chuỗi hiện diện không bật: Boreas NetVLAD, chuỗi vị trí đúng 85 % frame on-map, chỉ báo 30 %; Boreas DINOv2,
  83 % frame on-map nằm trong các đoạn **không bao giờ được báo** dù chuỗi vị trí đúng 86 % ở đó.
- **Phép min với TCE là nguyên nhân chính.** NCLT DINOv2: recall 0.16 (TCEmin) so với 0.50 (CPC-HMM không TCE).
- **So với CPC-HMM, TCEmin đúng là "chỉ thận trọng hơn"**: ở cùng recall, TCEmin có sai số cao hơn (NCLT NetVLAD 12.9 so
  với 6.3 m) và pAUC thấp hơn (0.490 so với 0.525).
- **Nhưng CPC-HMM không TCE thì vi phạm segFAR** (0.04–0.07 trên 4/7 dataset), và chẩn đoán cho thấy phần vi phạm đến từ
  báo cáo **kéo dài**: chuỗi vị trí không có trạng thái off-map, nên khi robot rời bản đồ, MAP bị buộc kẹt ở mép bản đồ hoặc
  nhảy sang nơi giống, trong khi chuỗi hiện diện vẫn tin là on. Phần **khởi phát** sai thì kiểm soát được (tỷ lệ đoạn có
  khởi phát sai 0.010–0.041 ≤ α khi hiệu chuẩn theo đoạn).

## 3. Phương pháp đề xuất: CPC-SC+CS (tổng quát, không nhãn, không tune theo dataset)

Ký hiệu: m_t nơi được báo (MAP của chuỗi vị trí), o_t odometry, p_t p-value SelfCal của top-1, p^R_t p-value của thống kê
neo odometry R_t, excl dung sai định vị, H độ dài đoạn, α mức FAR theo đoạn.

1. **Chuỗi hiện diện CPC-HMM** (giữ xếp hạng tốt, bỏ TCE):
   LR_t = ½ (ẽ^top_t + (e^R_t)^{1/H}),  e = a·p^{a−1} (a fit Beta-EM theo traversal, không nhãn), ẽ^top có cổng top-1 = MAP;
   log-odds ℓ_t = logit[(1−p_out)·P(on_{t−1}) + p_in·P(off_{t−1})] + log LR_t, p_in = p_out = 0.01.
2. **Ngưỡng khởi phát hiệu chuẩn theo đoạn (SC):** κ = phân vị conformal (1−α) của max ℓ trên các đoạn H frame của null
   tự-phát-lại của bản đồ (block giữ lại, chuỗi khởi đầu ở odds 1). Báo từ frame ℓ_t > κ, duy trì khi ℓ_t > 0.
   *Định lý (khởi phát):* nếu các đoạn off-map của query hoán đổi được với đoạn null thì một đoạn được đi vào khi chưa báo
   có khởi phát báo với xác suất ≤ α, với mọi phụ thuộc trong đoạn (log-odds đơn điệu theo odds ban đầu).
3. **Quy tắc dừng nhất quán odometry (CS):** dừng báo ở t nếu tồn tại độ trễ k với quãng odometry ≤ 3·excl sao cho
   | ‖m_t − m_{t−k}‖ − ‖o_t − o_{t−k}‖ | > excl  (chỉ độ lớn, bất biến với trôi hướng).
   *Bổ đề 7:* CS chỉ bỏ bớt báo cáo nên giữ các bảo đảm dạng "có báo cáo trong đoạn" (segFAR, FL) của luật gốc (không áp
   dụng cho ARL₀ đếm theo khởi phát). *Mệnh đề 4:* nếu MAP kẹt trong bán kính δ quanh
   nơi rời bản đồ và excl + in_d + ε + δ < off_d thì không có báo cáo ở frame off-map (ε: sai số độ lớn odometry trên 3·excl).

Mọi hằng số tính theo đơn vị của bài toán (excl, H, α); cùng một giá trị cho 7 dataset, 6 descriptor. Kiểm tra nhất quán với
odometry đã có tiền lệ (RRR, Latif et al. 2013; SeqSLAM), nên CS không mới tự thân; phần đóng góp là chẩn đoán đúng nguồn
vi phạm, vai trò trong khung có bảo đảm, và bằng chứng đường cong.

## 4. Giao thức đánh giá (chống thiên lệch chọn lựa)

- 7 dataset (Boreas, NCLT, CMU, Nordland, 4Seasons office/old town/countryside), 6 descriptor; bản đồ khuyết 30 % block
  (NCLT: off-map tự nhiên). Điểm mặc định: 10 seed; đường cong và so khớp: seed 0–2. Độ bền: bản đồ khuyết 10 % và 50 %
  với **cùng** hằng số.
- **Đăng ký trước** (ghi vào nhật ký trước khi xem): Boreas + NCLT là tập phát triển; 5 tập còn lại là tập giữ lại.
- **Chọn leave-one-dataset-out** trong 15 biến thể không nhãn: CPC-SC+CS được chọn ở 6/7 fold (CMU: CPC-HMM+CS), regret
  0–3.5 m (phương pháp cũ: tới 30 m).
- **Đường cong vận hành**: quét ngưỡng của từng luật (baseline dùng nhãn: Xu'21, Claxton'24, SafeVPR, ngưỡng max-sim;
  không nhãn: certified, per-frame SelfCal, các biến thể CPC); nhãn chỉ dùng để đánh giá. **So khớp chính xác**: đặt luật
  đề xuất tại đúng FL / recall của điểm mặc định từng baseline, chạy Kalman thật tại ngưỡng đó.

## 5. Kết quả

### Điểm vận hành mặc định, 10 seed (bản đồ khuyết 30 % block)

Ô: recall / segFAR / sai số điều hướng trung bình (m); trung bình trên các run (6 descriptor × số seed; NCLT không có lỗ tổng hợp nên 1 seed). Số run: Boreas 60, NCLT 6, CMU 60, Nordland 60, 4S office 60, 4S old town 60, 4S countryside 60.

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 HMM off-map (nhãn) | 0.68 / 0.043 / 25.3 | 0.53 / 0.021 / 13.7 | 0.69 / 0.227 / 18.1 | 0.74 / 0.038 / 59.3 | 0.72 / 0.215 / 21.2 | 0.62 / 0.101 / 70.9 | 0.25 / 0.088 / 81.0 |
| Claxton'24 MLP (nhãn) | 0.74 / 0.116 / 36.9 | 0.66 / 0.203 / 32.3 | 0.87 / 0.166 / 14.3 | 0.52 / 0.263 / 88.0 | 0.80 / 0.152 / 18.7 | 0.72 / 0.166 / 90.4 | 0.60 / 0.213 / 42.9 |
| Ngưỡng max-sim (nhãn) | 0.66 / 0.089 / 25.5 | 0.60 / 0.193 / 42.2 | 0.76 / 0.095 / 10.7 | 0.29 / 0.176 / 237.1 | 0.69 / 0.090 / 17.2 | 0.66 / 0.114 / 62.2 | 0.32 / 0.084 / 55.4 |
| Certified | 0.65 / 0.022 / 8.5 | 0.48 / 0.001 / 3.7 | 0.69 / 0.025 / 4.2 | 0.58 / 0.025 / 12.7 | 0.66 / 0.016 / 11.2 | 0.54 / 0.015 / 33.1 | 0.20 / 0.013 / 52.5 |
| CPC-HMM +TCEmin (cũ) | 0.66 / 0.008 / 6.4 | 0.49 / 0.000 / 3.7 | 0.75 / 0.018 / 3.9 | 0.57 / 0.002 / 13.0 | 0.70 / 0.013 / 12.5 | 0.59 / 0.008 / 33.7 | 0.21 / 0.010 / 59.1 |
| CPC-HMM (không TCE) | 0.72 / 0.042 / 11.3 | 0.64 / 0.005 / 7.9 | 0.85 / 0.058 / 7.1 | 0.68 / 0.008 / 15.3 | 0.82 / 0.067 / 13.1 | 0.71 / 0.047 / 43.5 | 0.36 / 0.055 / 51.6 |
| CPC-HMM +CS | 0.67 / 0.002 / 5.0 | 0.55 / 0.000 / 4.6 | 0.77 / 0.005 / 4.7 | 0.64 / 0.000 / 9.6 | 0.72 / 0.000 / 11.1 | 0.62 / 0.001 / 30.1 | 0.31 / 0.000 / 52.2 |
| **CPC-SC+CS (đề xuất)** | 0.66 / 0.001 / 5.1 | 0.54 / 0.000 / 4.6 | 0.73 / 0.002 / 3.8 | 0.64 / 0.000 / 9.6 | 0.71 / 0.000 / 11.6 | 0.60 / 0.000 / 30.8 | 0.30 / 0.000 / 53.1 |
| Oracle | 0.88 / – / 2.1 | 0.72 / – / 2.2 | 0.94 / – / 3.0 | 0.67 / – / 4.8 | 0.91 / – / 8.3 | 0.84 / – / 19.4 | 0.73 / – / 16.5 |

### Recall ở cùng mức báo sai (đường cong vận hành)

Ô: recall khi FL ≤ 0.01 / recall khi segFAR ≤ 0.025 / pAUC (recall trung bình trên FL ∈ [0, 0.05]). Mỗi luật quét ngưỡng của chính nó; nhãn chỉ dùng để đánh giá.

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 HMM off-map (nhãn) | 0.562 / 0.602 / 0.602 | 0.526 / 0.558 / 0.563 | 0.592 / 0.592 / 0.638 | 0.624 / 0.621 / 0.688 | 0.537 / 0.559 / 0.599 | 0.555 / 0.580 / 0.615 | 0.181 / 0.198 / 0.237 |
| Claxton'24 MLP (nhãn) | 0.687 / 0.662 / 0.706 | 0.574 / 0.522 / 0.592 | **0.793** / 0.769 / 0.812 | 0.439 / 0.387 / 0.466 | 0.749 / 0.717 / 0.765 | 0.644 / 0.622 / 0.672 | 0.420 / 0.396 / 0.470 |
| SafeVPR (nhãn, Boreas) | 0.486 / 0.433 / 0.551 (n=16) | – | – | – | – | – | – |
| Ngưỡng max-sim (nhãn) | 0.594 / 0.584 / 0.617 | 0.495 / 0.476 / 0.515 | 0.752 / 0.737 / 0.770 | 0.112 / 0.026 / 0.217 | 0.655 / 0.645 / 0.672 | 0.582 / 0.562 / 0.603 | 0.191 / 0.194 / 0.241 |
| Certified | 0.674 / 0.671 / 0.685 | 0.588 / 0.580 / 0.608 | 0.729 / 0.718 / 0.750 | 0.573 / 0.559 / 0.579 | 0.731 / 0.724 / 0.752 | 0.595 / 0.584 / 0.628 | 0.262 / 0.250 / 0.294 |
| CPC-HMM +TCEmin (cũ) | 0.692 / 0.704 / 0.702 | 0.590 / 0.512 / 0.630 | 0.713 / 0.698 / 0.753 | 0.619 / 0.618 / 0.634 | 0.733 / 0.751 / 0.756 | 0.616 / 0.631 / 0.635 | 0.245 / 0.292 / 0.301 |
| CPC-HMM (không TCE) | 0.688 / 0.714 / 0.714 | **0.645** / 0.640 / 0.669 | 0.747 / 0.750 / 0.765 | 0.693 / 0.704 / 0.710 | 0.722 / 0.740 / 0.756 | 0.622 / 0.661 / 0.661 | 0.236 / 0.278 / 0.287 |
| CPC-HMM +CS | **0.774** / 0.788 / 0.784 | 0.579 / 0.550 / 0.587 | 0.699 / 0.696 / 0.718 | 0.780 / 0.766 / 0.787 | **0.776** / 0.776 / 0.776 | 0.663 / 0.665 / 0.661 | 0.539 / 0.551 / 0.542 |
| **CPC-SC+CS (đề xuất)** | 0.766 / 0.782 / 0.777 | 0.586 / 0.552 / 0.588 | 0.705 / 0.703 / 0.724 | **0.780** / 0.766 / 0.787 | 0.771 / 0.771 / 0.771 | **0.664** / 0.664 / 0.657 | **0.545** / 0.551 / 0.543 |

### CPC-SC+CS đặt tại đúng điểm vận hành mặc định của từng baseline (so khớp chính xác)

Ô: trung vị chênh lệch theo cặp (đề xuất − baseline) và số run thắng / số run so được. Cột 1–2: cùng FL với baseline; cột 3–4: cùng recall với baseline ("không đạt" = đường cong của đề xuất không với tới recall đó). Sai số: Kalman chạy thật tại ngưỡng khớp.

| Dataset | Baseline | Δrecall @ FL của baseline | Δsai số @ FL của baseline | ΔFL @ recall của baseline | Δsai số @ recall của baseline |
|---|---|---|---|---|---|
| Boreas | Xu21 | +0.128 (16/18) | -1.6 (10/18) | -0.016 (16/18) | -1.2 (16/18) |
| Boreas | Claxton24 | +0.002 (9/18) | -1.5 (14/18) | +0.000 (9/18) | -1.3 (14/18) |
| Boreas | certified | -0.000 (9/18) | +0.4 (9/18) | +0.009 (8/18) | +41.6 (5/18) |
| Boreas | TCEmin | -0.015 (8/18) | +0.1 (9/18) | +0.018 (4/18) | +24.8 (4/18) |
| NCLT | Xu21 | -0.026 (2/6) | -5.3 (4/6) | +0.977 (1/6) | +43.5 (2/6) |
| NCLT | Claxton24 | -0.072 (1/6) | -19.9 (4/6) | +0.949 (1/6) | +35.1 (1/6) |
| NCLT | certified | +0.034 (6/6) | +1.3 (2/6) | +0.000 (1/6) | +0.9 (2/6) |
| NCLT | TCEmin | +0.028 (4/6) | +1.1 (1/6) | +0.000 (0/6) | +1.2 (1/6) |
| CMU | Xu21 | -0.043 (7/18) | +3.9 (6/18) | +0.290 (6/18) | +31.9 (7/18) |
| CMU | Claxton24 | -0.115 (2/18) | +2.1 (5/18) | +0.981 (2/18) | +83.0 (0/18) |
| CMU | certified | +0.053 (11/18) | +0.1 (4/18) | +0.000 (6/18) | +0.1 (2/18) |
| CMU | TCEmin | -0.000 (9/18) | +0.1 (4/18) | +0.000 (3/18) | +1.2 (3/18) |
| Nordland | Xu21 | +0.040 (9/18) | -4.3 (11/18) | +0.482 (9/18) | +169.7 (7/18) |
| Nordland | Claxton24 | +0.316 (18/18) | -29.5 (15/18) | -0.038 (18/18) | -73.1 (18/18) |
| Nordland | certified | +0.145 (18/18) | +3.0 (8/18) | -0.005 (17/18) | -3.1 (14/18) |
| Nordland | TCEmin | +0.151 (15/18) | -2.2 (16/18) | +0.000 (4/18) | -0.5 (14/18) |
| 4S office | Xu21 | +0.021 (10/18) | -3.6 (13/18) | +0.000 (8/17) | +1.0 (6/17) |
| 4S office | Claxton24 | -0.023 (4/18) | +0.2 (8/18) | +0.992 (4/18) | +33.1 (4/18) |
| 4S office | certified | +0.108 (15/18) | -0.2 (11/18) | +0.000 (7/18) | +0.5 (1/18) |
| 4S office | TCEmin | +0.030 (11/18) | +0.1 (8/18) | +0.000 (4/18) | +0.5 (4/18) |
| 4S old town | Xu21 | +0.038 (11/18) | -1.4 (10/18) | -0.005 (10/18) | -0.4 (9/18) |
| 4S old town | Claxton24 | -0.028 (6/18) | -20.6 (11/18) | +0.920 (6/18) | +123.4 (3/18) |
| 4S old town | certified | +0.071 (14/18) | +2.5 (5/18) | -0.002 (11/18) | +0.9 (7/18) |
| 4S old town | TCEmin | -0.020 (6/18) | +1.7 (5/18) | +0.001 (4/18) | +120.3 (4/18) |
| 4S countryside | Xu21 | +0.197 (17/18) | -21.3 (18/18) | -0.030 (17/18) | -13.7 (13/18) |
| 4S countryside | Claxton24 | -0.024 (5/18) | +0.2 (9/18) | +0.912 (5/18) | +24.8 (1/18) |
| 4S countryside | certified | +0.295 (18/18) | -13.1 (16/18) | -0.002 (11/18) | +4.2 (2/18) |
| 4S countryside | TCEmin | +0.269 (18/18) | -18.2 (16/18) | -0.002 (10/18) | +0.7 (7/18) |

### Độ nhạy một-tham-số-một-lần (điểm mặc định)

Ô: recall / segFAR / sai số (m).

| Biến thể | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| CPC-SC+CS | 0.66 / 0.003 / 5.3 | 0.54 / 0.000 / 4.6 | 0.66 / 0.001 / 3.7 | 0.64 / 0.000 / 11.6 | 0.71 / 0.000 / 12.1 | 0.58 / 0.000 / 32.8 | 0.30 / 0.000 / 54.3 |
| CPC-HMM+CS | 0.67 / 0.004 / 5.2 | 0.55 / 0.000 / 4.6 | 0.70 / 0.006 / 4.6 | 0.63 / 0.000 / 11.7 | 0.72 / 0.000 / 11.5 | 0.59 / 0.000 / 31.6 | 0.31 / 0.000 / 54.6 |
| CPC-HMM+CS(span2,thr1) | 0.69 / 0.014 / 6.5 | 0.58 / 0.000 / 5.3 | 0.73 / 0.010 / 4.5 | 0.65 / 0.001 / 11.7 | 0.75 / 0.001 / 10.9 | 0.63 / 0.005 / 30.1 | 0.33 / 0.000 / 51.7 |
| CPC-HMM+CS(span4,thr1) | 0.65 / 0.001 / 4.9 | 0.51 / 0.000 / 3.9 | 0.67 / 0.006 / 4.7 | 0.61 / 0.000 / 11.8 | 0.68 / 0.000 / 12.0 | 0.55 / 0.000 / 34.1 | 0.30 / 0.000 / 57.2 |
| CPC-HMM+CS(span3,thr0.75) | 0.66 / 0.002 / 5.0 | 0.49 / 0.000 / 4.5 | 0.68 / 0.006 / 4.4 | 0.62 / 0.000 / 11.7 | 0.69 / 0.000 / 11.9 | 0.56 / 0.000 / 32.1 | 0.30 / 0.000 / 54.3 |
| CPC-HMM+CS(span3,thr1.25) | 0.67 / 0.005 / 5.6 | 0.57 / 0.000 / 4.7 | 0.70 / 0.007 / 4.6 | 0.64 / 0.000 / 11.6 | 0.73 / 0.000 / 11.3 | 0.61 / 0.001 / 31.1 | 0.32 / 0.000 / 53.5 |
| CPC-SC+CS(alpha=0.01) | 0.64 / 0.001 / 5.3 | 0.49 / 0.000 / 4.1 | 0.00 / 0.000 / 4.0 | 0.63 / 0.000 / 11.7 | 0.00 / 0.000 / 37.4 | 0.19 / 0.000 / 76.7 | 0.18 / 0.000 / 75.1 |
| CPC-SC+CS(alpha=0.1) | 0.66 / 0.004 / 5.3 | 0.54 / 0.000 / 4.6 | 0.69 / 0.002 / 4.0 | 0.64 / 0.000 / 11.6 | 0.71 / 0.000 / 11.8 | 0.58 / 0.000 / 32.2 | 0.31 / 0.000 / 52.7 |

### Độ bền: điểm vận hành mặc định khi bản đồ khuyết 10 % block (cùng hằng số)

Ô: recall / segFAR / sai số điều hướng trung bình (m); trung bình trên các run (6 descriptor × số seed; NCLT không có lỗ tổng hợp nên 1 seed). Số run: Boreas 18, CMU 18, Nordland 18, 4S office 18, 4S old town 18, 4S countryside 18.

| Luật | Boreas | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| Xu'21 HMM off-map (nhãn) | 0.77 / 0.076 / 19.9 | 0.70 / 0.047 / 5.6 | 0.75 / 0.027 / 29.3 | 0.73 / 0.145 / 12.4 | 0.65 / 0.072 / 37.5 | 0.28 / 0.093 / 60.1 |
| Claxton'24 MLP (nhãn) | 0.79 / 0.218 / 33.8 | 0.89 / 0.266 / 10.5 | 0.55 / 0.517 / 66.7 | 0.81 / 0.211 / 17.4 | 0.75 / 0.257 / 85.2 | 0.62 / 0.260 / 37.6 |
| Ngưỡng max-sim (nhãn) | 0.65 / 0.084 / 12.2 | 0.71 / 0.083 / 7.4 | 0.29 / 0.246 / 200.2 | 0.70 / 0.113 / 13.2 | 0.67 / 0.125 / 54.5 | 0.34 / 0.093 / 54.9 |
| Certified | 0.65 / 0.029 / 4.4 | 0.72 / 0.032 / 3.2 | 0.57 / 0.014 / 8.9 | 0.68 / 0.022 / 9.1 | 0.57 / 0.017 / 25.8 | 0.18 / 0.004 / 54.1 |
| CPC-HMM +TCEmin (cũ) | 0.65 / 0.007 / 4.8 | 0.74 / 0.012 / 3.0 | 0.56 / 0.000 / 13.0 | 0.70 / 0.013 / 12.0 | 0.60 / 0.007 / 28.5 | 0.20 / 0.003 / 55.9 |
| CPC-HMM (không TCE) | 0.72 / 0.030 / 5.3 | 0.86 / 0.084 / 4.3 | 0.68 / 0.003 / 12.3 | 0.79 / 0.048 / 10.3 | 0.72 / 0.030 / 31.8 | 0.36 / 0.054 / 47.7 |
| CPC-HMM +CS | 0.70 / 0.000 / 4.3 | 0.79 / 0.006 / 3.4 | 0.65 / 0.000 / 10.7 | 0.73 / 0.000 / 9.3 | 0.66 / 0.000 / 25.1 | 0.33 / 0.000 / 49.0 |
| **CPC-SC+CS (đề xuất)** | 0.69 / 0.000 / 4.4 | 0.76 / 0.001 / 3.0 | 0.65 / 0.000 / 10.7 | 0.72 / 0.000 / 9.5 | 0.64 / 0.000 / 26.0 | 0.31 / 0.000 / 50.4 |
| Oracle | 0.88 / – / 1.8 | 0.94 / – / 2.7 | 0.66 / – / 4.3 | 0.90 / – / 6.3 | 0.84 / – / 15.9 | 0.74 / – / 14.2 |

### Độ bền: điểm vận hành mặc định khi bản đồ khuyết 50 % block (cùng hằng số)

Ô: recall / segFAR / sai số điều hướng trung bình (m); trung bình trên các run (6 descriptor × số seed; NCLT không có lỗ tổng hợp nên 1 seed). Số run: Boreas 18, CMU 18, Nordland 18, 4S office 18, 4S old town 18, 4S countryside 18.

| Luật | Boreas | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| Xu'21 HMM off-map (nhãn) | 0.71 / 0.027 / 32.1 | 0.57 / 0.080 / 21.9 | 0.75 / 0.037 / 121.5 | 0.79 / 0.381 / 56.0 | 0.56 / 0.029 / 98.8 | 0.27 / 0.221 / 156.2 |
| Claxton'24 MLP (nhãn) | 0.72 / 0.064 / 34.5 | 0.80 / 0.070 / 16.2 | 0.51 / 0.133 / 89.0 | 0.77 / 0.087 / 24.9 | 0.71 / 0.090 / 134.2 | 0.57 / 0.099 / 47.9 |
| Ngưỡng max-sim (nhãn) | 0.64 / 0.074 / 28.1 | 0.75 / 0.079 / 24.3 | 0.36 / 0.170 / 266.8 | 0.69 / 0.078 / 25.1 | 0.66 / 0.107 / 139.6 | 0.38 / 0.075 / 59.9 |
| Certified | 0.64 / 0.008 / 6.9 | 0.60 / 0.031 / 7.6 | 0.60 / 0.015 / 21.1 | 0.69 / 0.033 / 15.7 | 0.49 / 0.006 / 52.0 | 0.16 / 0.030 / 65.3 |
| CPC-HMM +TCEmin (cũ) | 0.63 / 0.002 / 5.9 | 0.63 / 0.017 / 6.3 | 0.59 / 0.002 / 18.4 | 0.70 / 0.023 / 16.8 | 0.54 / 0.004 / 50.3 | 0.17 / 0.032 / 73.0 |
| CPC-HMM (không TCE) | 0.72 / 0.026 / 15.8 | 0.76 / 0.086 / 23.0 | 0.73 / 0.009 / 28.4 | 0.81 / 0.068 / 21.5 | 0.70 / 0.035 / 79.3 | 0.34 / 0.161 / 73.0 |
| CPC-HMM +CS | 0.62 / 0.001 / 5.9 | 0.66 / 0.023 / 12.4 | 0.67 / 0.000 / 13.7 | 0.70 / 0.000 / 15.5 | 0.60 / 0.000 / 39.9 | 0.26 / 0.002 / 58.9 |
| **CPC-SC+CS (đề xuất)** | 0.60 / 0.000 / 5.8 | 0.61 / 0.012 / 6.9 | 0.67 / 0.000 / 13.7 | 0.70 / 0.000 / 15.5 | 0.57 / 0.000 / 41.0 | 0.25 / 0.001 / 59.5 |
| Oracle | 0.89 / – / 2.5 | 0.90 / – / 3.3 | 0.69 / – / 8.0 | 0.91 / – / 12.0 | 0.85 / – / 31.8 | 0.73 / – / 23.6 |


## 6. Trả lời phản biện

1. **Không chỉ thận trọng hơn.** Ở cùng mức báo sai FL ≤ 1 %, CPC-SC+CS bắt được nhiều fix đúng hơn Xu'21 trên 7/7
   dataset và hơn Claxton'24 (dùng nhãn) trên 6/7; đặt tại đúng FL của Xu'21, recall cao hơn trên 5/7 và sai số thấp hơn
   trên 6/7. Ở điểm mặc định (10 seed, 366 run), so với phương pháp cũ (TCEmin): recall cao hơn trên 5/7 (NCLT +0.05,
   Nordland +0.07, countryside +0.09, office/old town +0.01), bằng trên Boreas, thấp hơn 0.02 trên CMU; segFAR thấp hơn
   hoặc bằng trên 7/7; sai số thấp hơn trên 6/7 (NCLT +0.9 m). segFAR tệ nhất trong **từng run** là 0.021 (mọi run dưới
   α = 0.05), trong khi TCEmin tới 0.171 và Xu'21 tới 1.0; so với Xu'21 sai số thấp hơn 1.5–6.2× trên 7/7.
2. **Tổng quát, không tune theo dataset:** cùng một bộ hằng số (đơn vị excl, H, α) cho 7 dataset, 6 descriptor, 3 tỷ lệ
   lỗ bản đồ (10/30/50 %) và off-map tự nhiên (NCLT); segFAR trung bình ≤ 0.012 ở mọi cấu hình; chọn leave-one-dataset-out
   ổn định (6/7 fold).
3. **Phản biện đúng một phần với phương pháp cũ**: so với CPC-HMM, TCEmin là điểm thận trọng hơn trên một đường cong kém
   hơn; phép min với TCE đã được thay bằng hiệu chuẩn ngưỡng khởi phát và quy tắc dừng CS.

## 7. Hạn chế (giữ nguyên, không che)

- **Ở điểm mặc định, recall vẫn thấp hơn Xu'21 trên 4/7 dataset** (Nordland −0.10, Boreas/old town −0.02, office −0.01),
  dù sai số thấp hơn 1.5–6.2× và Xu'21 vi phạm segFAR; ở cùng FL thì đường cong của đề xuất cao hơn (mục 6).
- **CMU (descriptor mạnh, dữ liệu dễ):** Claxton'24 và cả điểm max-sim thô xếp hạng tốt hơn mọi chuỗi hiện diện; ở FL
  của Xu'21 recall của đề xuất thấp hơn 0.04.
- **Vùng FL cao (3–8 %):** Claxton'24 có recall cao hơn trên 5/7 dataset — nhưng ở đó segFAR của nó 0.11–0.27.
- **NCLT:** CS xoá frame đúng; CPC-HMM không CS có đường cong tốt nhất; sai số điều hướng nhạy với vài fix sai do EKF có
  trạng thái hướng.
- **Điểm mặc định còn dè dặt so với chính đường cong của nó** (countryside: recall 0.30 ở FL 0.000, 0.55 ở FL 0.01).
  Hiệu chuẩn chung (hiện diện ∧ CS) trên null tự-phát-lại không nới được ngưỡng vì null qua CS nhiều gấp 2.6× off-map thật.
- **α nhỏ cần đủ đoạn null:** α = 0.01 cần ≥ 99 đoạn; CMU/4S office có ít hơn nên κ = ∞ (recall 0).
- Đã thử và loại (kết quả âm, chi tiết trong nhật ký): e-value hai nhóm (hedge), trung bình e-process, TCE trên một thành
  phần, hysteresis TCEmin/CPC, CPC-SC không CS, W-CPC (bộ nhớ hữu hạn), PCR (cổng dự đoán kiểu IPDA: tự xác nhận, LR ≈ 1.5),
  cổng độ tin chuỗi vị trí, hiệu chuẩn chung CS.
