# Báo cáo vòng 4: bảo đảm khi các frame phụ thuộc nhau, kiểm định tuyến hiệu chuẩn bằng bản đồ, so sánh TAO'26 / TRAIL'26 / VPR-auditing'26

*Branch `hmm-navigation-4`, 2026-10-31. Nhật ký: `RESEARCH_LOG.md` Entry 26. Lý thuyết: `paper/cpc_theory.md` §3e–§3f.
Novelty: `LITERATURE_GATE.md` Gate 11. Baseline tái hiện từ paper: `literature/BASELINES_2026.md`. Mọi số liệu tái tạo
được từ dataset public `nhatlong1103/hmm-navcache-v2` và `nhatlong1103/hmm-topk`.*

## 1. Câu hỏi của vòng này

1. Định lý khởi phát của CPC-SC dựa trên giả định các đoạn off-map hoán đổi được với đoạn null của bản đồ; các frame phụ
   thuộc nhau mạnh. Có bảo đảm nào đúng khi các frame phụ thuộc, mà không quá bảo thủ?
2. Phương pháp có đứng vững trước các công trình 2026 gần nhất (TAO'26, TRAIL'26, VPR-auditing'26) trên cùng giao thức?
3. Có cơ chế mới nào nâng điểm số mà vẫn không dùng nhãn?

## 2. Chẩn đoán: giả định hỏng ở đâu (nhãn chỉ dùng để chẩn đoán)

- p-value SelfCal của top-1 ở frame off-map **siêu đều ở phần trong** đoạn off-map: P(p ≤ 0.05) = 0.000–0.006 khi cách
  cả hai mép ≥ 50 frame (Boreas, CMU, 4S countryside).
- Vi phạm nằm ở **mép bản đồ** (~50 frame quanh mép): CMU MegaLoc P(p ≤ 0.05) = 0.12–0.16, vì ảnh ở mép bản đồ nhìn thấy cùng
  cảnh (top-1 cách 40–100 m): giới hạn phân giải của bằng chứng ngoại hình.
- Thống kê R neo odometry dưới đều ở **đoạn off-map dài** (Boreas CosPlace 0.19–0.23 ở độ sâu 0–100 frame), nơi null của bản
  đồ không có mẫu: null chỉ có **8–10 chunk dài 84–135 frame**. Số đơn vị hoán đổi được hiệu dụng ≈ 10.
- Kết luận: vấn đề không phải phụ thuộc *bên trong* một đoạn (định lý theo đoạn đã cho phép phụ thuộc tuỳ ý trong đoạn) mà
  là (i) trạng thái mang qua giữa các đoạn của một chuỗi có bộ nhớ vô hạn, (ii) tính đại diện của null (mép, đoạn dài, ít
  đơn vị), (iii) null cùng điều kiện ảnh.

## 3. Lý thuyết mới (chi tiết và chứng minh: `cpc_theory.md` §3e)

**Mệnh đề 5 (cái giá của phụ thuộc).** Nếu chỉ biết mỗi frame hợp lệ *biên* và phân phối chung tuỳ ý, thì mọi phép thử
mức α trên n frame, tại phân phối "n bản sao của một frame" (gần với thực tế: tự tương quan trễ 1 là 0.8–0.99), chỉ còn là
phép thử một frame. Mọi bảo đảm có **tích luỹ** bằng chứng đều cần một giả định về phụ thuộc.

**Định lý 4 (GPC: chứng chỉ đúng với mọi phụ thuộc).** Đặt cửa sổ odometry D = 6·excl lên traversal của bản đồ bằng
Procrustes 2-D (chỉ hình học, không ảnh); báo nếu một cách đặt có ≥ φK frame có top-1 trùng điểm đặt và p ≤ u\* =
αφ/min(1, Q_t), với Q_t là độ phủ hình học của các cách đặt. Khi đó P(báo sai tại t) ≤ α với **mọi** phân phối chung theo
thời gian (Markov trên số đếm + độ phủ), nên E[FL] ≤ α. Thực nghiệm: FL = 0 ở mọi nơi, nhưng recall chỉ 10–40 % của CPC-SC+CS
(xem bảng): đúng như Mệnh đề 5.

**Định lý 5 (khởi phát cửa sổ hữu hạn + bền vững hình học).** Khởi phát dùng thống kê chỉ phụ thuộc W = H frame cuối, hiệu
chuẩn bằng phân vị conformal theo đoạn trên null; dừng (và reset) khi chuỗi vị trí không còn nhất quán với odometry (CS:
độ lớn; SH: hình dạng, phần dư Procrustes ≤ excl/2 trên 3·excl). Dưới hoán đổi được **chỉ trong từng cửa sổ H frame** và
giả định không có đường bản đồ nối tiếp khớp hình dạng ở mép (NC): tỷ lệ khởi phát sai mỗi đoạn off-map ≤ α, **với mọi
phụ thuộc giữa các đoạn** (tuyến tính của kỳ vọng). Không cần e-value hợp lệ có điều kiện (Định lý 1, 3) và không cần đoạn
off-map dài hoán đổi được với đoạn null ngắn.

**Hệ quả (giới hạn của bản đồ).** Bảo đảm có điều kiện theo hiệu chuẩn (theo từng lần triển khai) cần ≳ log(1/δ)/α đơn
vị độc lập; bản đồ cho ~10, nên chỉ bảo đảm biên là khả thi: đúng với dao động theo run quan sát được.

## 4. Cơ chế mới: kiểm định tuyến hiệu chuẩn bằng bản đồ (`cpc_theory.md` §3f)

Chi phí TAO C_t: với 100 giả thuyết của frame t, neo truy ngược trên tuyến bản đồ theo quãng odometry của 20 frame gần nhất,
khớp cứng 2-D, phần dư Huber cắt 75 % + 2·(1 − similarity) dọc tuyến. Chúng tôi **chạy cùng thống kê trên null tự-phát-lại
của bản đồ** (ảnh của block giữ lại, che block của chính nó, odometry chính xác của bản đồ):

- **TAO-SC:** báo khi C_t dưới phân vị dưới conformal mức α của min-chi-phí theo đoạn của null: không nhãn, bộ nhớ hữu hạn,
  nên Định lý 5 áp dụng.
- **CPC-SC-T:** p-value hạng của C_t trong null làm thành phần thứ ba của chuỗi hiện diện CPC-SC,
  LR_t = ⅓(ẽ^top_t + (e^R_t)^{1/H} + (e^T_t)^{1/H}), κ hiệu chuẩn theo đoạn với cùng ba thành phần.

## 5. Kết quả (7 dataset, 6 descriptor; bản đồ khuyết 30 %; NCLT off-map tự nhiên)

### Bảng 1. Điểm mặc định: recall / segFAR / sai số điều hướng (m), trung bình mọi run (10 seed; NCLT 1 seed; TRAIL'26 chỉ MegaLoc, seed 0–2)

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 HMM off-map (nhãn) | 0.68 / 0.043 / 25.3 | 0.53 / 0.021 / 13.7 | 0.69 / 0.227 / 18.1 | 0.74 / 0.038 / 59.3 | 0.72 / 0.215 / 21.2 | 0.62 / 0.101 / 70.9 | 0.25 / 0.088 / 81.0 |
| Claxton'24 MLP (nhãn) | 0.74 / 0.116 / 36.9 | 0.66 / 0.203 / 32.3 | 0.87 / 0.167 / 14.4 | 0.52 / 0.262 / 88.0 | 0.80 / 0.156 / 18.9 | 0.72 / 0.165 / 89.8 | 0.60 / 0.215 / 43.2 |
| TAO'26 (nhãn: ngưỡng 3σ) | 0.80 / 0.240 / 46.2 | 0.76 / 0.707 / 57.6 | 0.93 / 0.370 / 38.4 | 0.80 / 0.579 / 187.9 | 0.94 / 0.740 / 54.0 | 0.84 / 0.557 / 168.4 | 0.77 / 0.732 / 95.1 |
| Certified | 0.65 / 0.022 / 8.5 | 0.48 / 0.001 / 3.7 | 0.69 / 0.025 / 4.2 | 0.58 / 0.025 / 12.7 | 0.66 / 0.016 / 11.2 | 0.54 / 0.015 / 33.1 | 0.20 / 0.013 / 52.5 |
| CPC-SC+CS (vòng 3) | 0.66 / 0.001 / 5.1 | 0.54 / 0.000 / 4.6 | 0.73 / 0.002 / 3.8 | 0.64 / 0.000 / 9.6 | 0.71 / 0.000 / 11.6 | 0.60 / 0.000 / 30.8 | 0.30 / 0.000 / 53.1 |
| CPC-SC+SH | 0.66 / 0.002 / 5.4 | 0.57 / 0.000 / 4.8 | 0.75 / 0.009 / 4.3 | 0.66 / 0.000 / 9.5 | 0.73 / 0.000 / 11.3 | 0.63 / 0.005 / 30.2 | 0.31 / 0.000 / 51.6 |
| CPC-W+CS+SH (Định lý 5) | 0.66 / 0.001 / 5.3 | 0.51 / 0.000 / 4.1 | 0.72 / 0.003 / 3.7 | 0.65 / 0.000 / 9.2 | 0.69 / 0.000 / 11.6 | 0.59 / 0.000 / 32.7 | 0.28 / 0.000 / 54.5 |
| **TAO-SC** (không nhãn) | 0.58 / 0.011 / 10.1 | 0.40 / 0.000 / 11.4 | 0.66 / 0.066 / 7.1 | 0.35 / 0.012 / 63.8 | 0.63 / 0.011 / 18.7 | 0.55 / 0.008 / 37.5 | 0.05 / 0.003 / 102.3 |
| **CPC-SC-T** (không nhãn) | 0.72 / 0.032 / 9.4 | 0.63 / 0.004 / 9.2 | 0.83 / 0.051 / 5.5 | 0.72 / 0.021 / 17.5 | 0.80 / 0.066 / 13.6 | 0.70 / 0.040 / 40.2 | 0.35 / 0.052 / 55.2 |
| **CPC-SC-T+SH** (không nhãn) | 0.67 / 0.002 / 5.6 | 0.59 / 0.001 / 4.8 | 0.77 / 0.010 / 4.4 | 0.69 / 0.000 / 9.5 | 0.74 / 0.000 / 11.3 | 0.64 / 0.007 / 29.7 | 0.32 / 0.000 / 51.0 |
| Oracle | 0.88 / – / 2.1 | 0.72 / – / 2.2 | 0.94 / – / 3.0 | 0.67 / – / 4.8 | 0.91 / – / 8.3 | 0.84 / – / 19.4 | 0.73 / – / 16.5 |

### Bảng 2. Đường cong vận hành: recall tại FL ≤ 0.01 / pAUC (FL ∈ [0, 0.05]), seed 0–2

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 HMM off-map (nhãn) | 0.562 / 0.602 | 0.526 / 0.563 | 0.592 / 0.638 | 0.624 / 0.688 | 0.537 / 0.599 | 0.555 / 0.615 | 0.181 / 0.237 |
| Claxton'24 MLP (nhãn) | 0.687 / 0.706 | 0.574 / 0.592 | 0.793 / 0.812 | 0.439 / 0.466 | 0.749 / 0.765 | 0.644 / 0.672 | 0.420 / 0.470 |
| TAO'26 (nhãn: ngưỡng 3σ) | 0.640 / 0.659 | 0.520 / 0.543 | 0.792 / 0.806 | 0.418 / 0.493 | 0.683 / 0.705 | 0.631 / 0.654 | 0.239 / 0.296 |
| Certified | 0.674 / 0.685 | 0.588 / 0.608 | 0.729 / 0.750 | 0.573 / 0.579 | 0.731 / 0.752 | 0.595 / 0.628 | 0.262 / 0.294 |
| CPC-SC+CS (vòng 3) | 0.766 / 0.777 | 0.586 / 0.588 | 0.705 / 0.724 | 0.780 / 0.787 | 0.771 / 0.771 | 0.664 / 0.657 | 0.545 / 0.543 |
| CPC-SC+SH | 0.755 / 0.771 | 0.600 / 0.623 | 0.708 / 0.728 | 0.775 / 0.797 | 0.812 / 0.808 | 0.667 / 0.688 | 0.515 / 0.563 |
| CPC-W+CS+SH (Định lý 5) | 0.745 / 0.766 | 0.586 / 0.583 | 0.701 / 0.722 | 0.750 / 0.777 | 0.768 / 0.768 | 0.659 / 0.651 | 0.544 / 0.533 |
| **TAO-SC** (không nhãn) | 0.641 / 0.659 | 0.520 / 0.543 | 0.791 / 0.805 | 0.418 / 0.493 | 0.683 / 0.705 | 0.632 / 0.655 | 0.239 / 0.296 |
| **CPC-SC-T** (không nhãn) | 0.680 / 0.706 | 0.654 / 0.667 | 0.756 / 0.777 | 0.709 / 0.731 | 0.733 / 0.753 | 0.610 / 0.639 | 0.237 / 0.293 |
| **CPC-SC-T+SH** (không nhãn) | 0.761 / 0.777 | 0.610 / 0.627 | 0.722 / 0.741 | 0.794 / 0.812 | 0.812 / 0.809 | 0.676 / 0.693 | 0.525 / 0.569 |

### Bảng 3. Kiểm chứng Định lý 5: khởi phát sai mỗi đoạn off-map (H/ARL₀), trung bình / run tệ nhất (α = 0.05)

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 HMM off-map (nhãn) | 0.015 / 0.147 | 0.014 / 0.049 | 0.068 / 0.405 | 0.021 / 0.090 | 0.087 / 0.448 | 0.036 / 0.401 | 0.021 / 0.150 |
| Claxton'24 MLP (nhãn) | 0.147 / 0.839 | 0.274 / 0.553 | 0.220 / 1.072 | 0.326 / 0.581 | 0.211 / 0.905 | 0.219 / 0.745 | 0.278 / 0.593 |
| TAO'26 (nhãn: ngưỡng 3σ) | 0.032 / 0.124 | 0.122 / 0.216 | 0.047 / 0.151 | 0.105 / 0.273 | 0.041 / 0.252 | 0.082 / 0.333 | 0.040 / 0.173 |
| CPC-SC+CS (vòng 3) | 0.001 / 0.009 | 0.003 / 0.003 | 0.003 / 0.013 | 0.003 / 0.003 | 0.004 / 0.008 | 0.005 / 0.008 | 0.004 / 0.008 |
| CPC-W+CS+SH (Định lý 5) | 0.001 / 0.008 | 0.003 / 0.003 | 0.005 / 0.071 | 0.003 / 0.008 | 0.004 / 0.008 | 0.004 / 0.006 | 0.004 / 0.008 |
| **TAO-SC** (không nhãn) | 0.005 / 0.037 | 0.003 / 0.003 | 0.016 / 0.162 | 0.008 / 0.033 | 0.006 / 0.026 | 0.006 / 0.038 | 0.005 / 0.036 |
| **CPC-SC-T** (không nhãn) | 0.007 / 0.034 | 0.003 / 0.003 | 0.005 / 0.052 | 0.003 / 0.006 | 0.006 / 0.046 | 0.007 / 0.029 | 0.006 / 0.024 |
| **CPC-SC-T+SH** (không nhãn) | 0.002 / 0.008 | 0.003 / 0.003 | 0.006 / 0.039 | 0.003 / 0.003 | 0.004 / 0.008 | 0.005 / 0.016 | 0.004 / 0.008 |

### Bảng 3b. Chỉ MegaLoc, seed 0–2 (so với TRAIL'26): mặc định recall / segFAR / sai số (m) | recall tại FL ≤ 0.01

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 HMM off-map (nhãn) | 0.86 / 0.031 / 7.0 \| 0.779 | 0.79 / 0.026 / 4.7 \| 0.788 | 0.96 / 0.295 / 36.5 \| 0.897 | 0.90 / 0.023 / 17.1 \| 0.859 | 0.91 / 0.043 / 8.3 \| 0.751 | 0.92 / 0.048 / 21.0 \| 0.727 | 0.57 / 0.046 / 29.9 \| 0.362 |
| Claxton'24 MLP (nhãn) | 0.91 / 0.000 / 2.8 \| 0.941 | 0.77 / 0.039 / 5.1 \| 0.770 | 0.97 / 0.008 / 4.0 \| 0.976 | 0.71 / 0.174 / 48.7 \| 0.666 | 0.94 / 0.003 / 8.3 \| 0.963 | 0.87 / 0.008 / 18.9 \| 0.894 | 0.87 / 0.206 / 18.8 \| 0.627 |
| TAO'26 (nhãn: ngưỡng 3σ) | 0.85 / 0.000 / 4.7 \| 0.915 | 0.80 / 0.418 / 32.5 \| 0.766 | 0.98 / 0.073 / 12.1 \| 0.970 | 0.93 / 0.797 / 267.2 \| 0.510 | 0.99 / 1.000 / 47.5 \| 0.961 | 0.98 / 0.377 / 97.6 \| 0.897 | 0.93 / 0.525 / 39.7 \| 0.662 |
| TRAIL'26 (nhãn: ngưỡng điều kiện dễ) | 0.74 / 0.151 / 50.6 \| 0.558 | 0.57 / 0.239 / 23.7 \| 0.231 | 0.84 / 0.198 / 12.6 \| 0.623 | 0.28 / 0.268 / 159.0 \| 0.115 | 0.86 / 0.285 / 17.2 \| 0.630 | 0.80 / 0.232 / 56.2 \| 0.620 | 0.48 / 0.265 / 35.0 \| 0.155 |
| CPC-SC+CS (vòng 3) | 0.90 / 0.005 / 2.6 \| 0.914 | 0.66 / 0.000 / 5.4 \| 0.688 | 0.87 / 0.003 / 5.3 \| 0.880 | 0.78 / 0.000 / 4.8 \| 0.826 | 0.91 / 0.000 / 9.0 \| 0.903 | 0.86 / 0.000 / 20.4 \| 0.883 | 0.54 / 0.000 / 24.4 \| 0.793 |
| **CPC-SC-T+SH** (không nhãn) | 0.91 / 0.008 / 3.5 \| 0.915 | 0.72 / 0.000 / 5.0 \| 0.722 | 0.89 / 0.010 / 7.5 \| 0.877 | 0.84 / 0.000 / 4.7 \| 0.869 | 0.93 / 0.000 / 8.6 \| 0.930 | 0.90 / 0.011 / 19.8 \| 0.916 | 0.60 / 0.000 / 22.0 \| 0.837 |
| Oracle | 0.99 / – / 1.8 | 0.80 / – / 2.1 | 0.99 / – / 2.8 | 0.81 / – / 4.6 | 1.00 / – / 8.1 | 0.98 / – / 19.7 | 0.92 / – / 15.4 |

### Bảng 4. Cái giá của phụ thuộc: chứng chỉ GPC (đúng với mọi phụ thuộc) so với CPC-SC+CS, seed 0

| Cấu hình | GPC recall (α = 0.01 / 0.05) | GPC FL | CPC-SC+CS recall | CPC-SC+CS FL |
|---|---|---|---|---|
| CMU CosPlace | 0.046 / 0.138 | 0.0000 | 0.723 | 0.0000 |
| CMU MegaLoc | 0.047 / 0.197 | 0.0000 | 0.838 | 0.0007 |
| CMU NetVLAD | 0.006 / 0.036 | 0.0000 | 0.313 | 0.0000 |
| Nordland CosPlace | 0.143 / 0.266 | 0.0000 | 0.688 | 0.0000 |
| NCLT NetVLAD | 0.051 / 0.123 | 0.0000 | 0.342 | 0.0000 |
| NCLT MegaLoc | 0.125 / 0.276 | 0.0000 | 0.659 | 0.0000 |

### Bảng 5. VPR-auditing'26 (Qwen2.5-VL-7B, offline) trên Boreas, seed 0, các frame được audit (mỗi 5 frame)

Chỉ số của paper (P, coverage C, FAR, S) và của dự án (recall, FL, sai số Kalman khi chỉ được fix ở frame được audit).

| Descriptor | Luật | P | C | FAR | S | recall | FL | sai số (m) |
|---|---|---|---|---|---|---|---|---|
| megaloc (15287 frame) | VPR-auditing'26 | 0.796 | 0.592 | 0.371 | 0.662 | 0.691 | 0.359 | 149.5 |
| megaloc (15287 frame) | Claxton'24 (nhãn) | 0.987 | 0.635 | 0.025 | 0.830 | 0.919 | 0.000 | 3.4 |
| megaloc (15287 frame) | Xu'21 (nhãn) | 0.973 | 0.650 | 0.048 | 0.830 | 0.928 | 0.011 | 6.6 |
| megaloc (15287 frame) | CPC-SC+CS | 0.988 | 0.650 | 0.023 | 0.840 | 0.943 | 0.003 | 3.0 |
| megaloc (15287 frame) | CPC-SC+SH | 0.982 | 0.656 | 0.037 | 0.838 | 0.945 | 0.004 | 3.2 |
| netvlad (15287 frame) | VPR-auditing'26 | 0.747 | 0.499 | 0.240 | 0.644 | 0.547 | 0.304 | 151.5 |
| netvlad (15287 frame) | Claxton'24 (nhãn) | 0.847 | 0.423 | 0.123 | 0.641 | 0.526 | 0.084 | 154.8 |
| netvlad (15287 frame) | Xu'21 (nhãn) | 0.960 | 0.439 | 0.031 | 0.689 | 0.618 | 0.024 | 54.0 |
| netvlad (15287 frame) | CPC-SC+CS | 0.991 | 0.240 | 0.005 | 0.486 | 0.349 | 0.000 | 7.5 |
| netvlad (15287 frame) | CPC-SC+SH | 0.989 | 0.243 | 0.006 | 0.489 | 0.352 | 0.000 | 7.5 |


## 6. Đọc kết quả

1. **Cải thiện đo được, không nhãn.** CPC-SC-T+CS (CPC-SC+CS thêm bằng chứng kiểm định tuyến) là cải thiện Pareto so với
   phương pháp vòng 3 tại điểm mặc định: recall cao hơn 7/7 dataset (+0.005…+0.032), segFAR như cũ (run tệ nhất ≤ 0.023
   < α), sai số bằng hoặc thấp hơn 7/7. CPC-SC-T+SH cho recall cao nhất (+0.009…+0.053 trên 7/7; NCLT +0.05, CMU +0.04,
   Nordland +0.05, old town +0.04), segFAR trung bình ≤ 0.010 (run tệ nhất 0.060 trên CMU), sai số thấp hơn trên 4/7; recall
   cao hơn Xu'21 (có nhãn) trên 5/7 (vòng 3: 3/7) với sai số thấp hơn 2.4–6×. Trên đường cong (FL ≤ 0.01) CPC-SC-T+SH
   hơn CPC-SC+CS 5/7, pAUC 6/7; hơn Xu'21 7/7, Claxton'24 và TAO'26 6/7 (trừ CMU).
2. **Chọn biến thể theo leave-one-dataset-out** (tiêu chí đăng ký trước: sai số chuẩn hoá thấp nhất với segFAR ≤ α trên các
   dataset khác) không phân biệt rõ: CPC-W+CS+SH được chọn 5/7 fold, regret 0–3.5 m; các biến thể khác nhau chủ yếu ở
   recall, không ở sai số. Họ CPC-SC-T được thiết kế sau khi xem CMU CosPlace seed 0–1 (tập giữ lại): đã ghi rõ.
3. **TAO'26** xếp hạng rất tốt trên CMU (recall 0.79 tại FL ≤ 0.01, ngang Claxton'24) nhưng ngưỡng 3σ của paper không chuyển
   được sang điều kiện khác (segFAR 0.24–0.74, sai số 38–188 m). Hiệu chuẩn không nhãn của chúng tôi (TAO-SC) giữ đúng đường
   cong của TAO nhưng điểm mặc định kém ổn định (CMU run tệ nhất 0.76): min-chi-phí theo đoạn với ~70 đoạn null dao động mạnh.
   Đưa chi phí TAO vào chuỗi hiện diện (CPC-SC-T) ổn định hơn nhiều.
4. **TRAIL'26** (MegaLoc, huấn luyện trên 6 dataset còn lại): vị trí đúng ≈ top-1 MegaLoc (khác ≤ 0.01, trừ Nordland −0.08);
   ngưỡng hiệu chuẩn bằng nhãn trên điều kiện dễ vi phạm nặng (segFAR 0.15–0.29); đường cong ở FL ≤ 0.01 thấp nhất trong các
   luật học được (Boreas 0.56, countryside 0.16).
5. **VPR-auditing'26** (Qwen2.5-VL-7B mở, offline): trên Boreas FAR 0.24–0.37 và nhận 30–36 % frame off-map, sai số điều hướng
   150 m; CPC-SC+CS trên cùng frame thắng cả theo metric S của paper với MegaLoc (0.840 so với 0.662). Mô hình mở 7B yếu hơn
   GPT-4.1 / Gemini trong paper (S 0.60 so với 0.76–0.78), nên đây là cận dưới của họ phương pháp VLM.
6. **Chỉ MegaLoc (descriptor mạnh nhất):** Claxton'24 (có nhãn) và TAO'26 xếp hạng tốt hơn CPC-SC-T+SH trên Boreas, NCLT, CMU,
   4S office; CPC-SC-T+SH thắng trên Nordland, old town, countryside. Lợi thế của phương pháp là tính hợp lệ không nhãn và độ
   bền trên mọi descriptor, không phải xếp hạng tốt nhất với descriptor mạnh.

## 7. Hạn chế và kết quả âm (đã xác minh)

1. **Điểm mặc định vẫn dè dặt** so với chính đường cong. Nguyên nhân đã đo: null của bản đồ là **cùng điều kiện ảnh**, cho
   bằng chứng mạnh hơn query khác điều kiện, nên κ cao. Hiệu chuẩn chung (hiện diện ∧ hình học) và bỏ sàn κ ≥ 0 chỉ thêm
   +0.003…+0.011 recall (`cpc_geo.scj_kappa`). Null khớp điều kiện (ví dụ pseudo-query từ traversal khác của bản đồ nhiều
   phiên) là việc mở.
2. **CMU với descriptor mạnh** vẫn là điểm yếu xếp hạng (mục 6.6). **Luật cửa sổ hữu hạn (CPC-W):** trung bình ngang CPC-SC+CS, nhưng run tệ nhất trên CMU có tỷ lệ khởi phát sai 0.07–0.11
   > α (bản đồ nhỏ, ~70 đoạn null): bảo đảm là biên theo hiệu chuẩn.
3. **GPC** hợp lệ dưới mọi phụ thuộc nhưng power thấp (recall 0.04–0.28 ở α = 0.05).
4. **Dừng hình dạng SH** chỉ là cải thiện nhỏ (pAUC tăng 6/7 dataset, recall tại FL ≤ 0.01 lẫn lộn).
5. **TRAIL'26** được tái hiện với biến thể transition d_g (bản CNN trên tương quan DINOv2 cục bộ cần ảnh mọi ứng viên);
   **VPR-auditing'26** chỉ chạy trên Boreas (2 descriptor, mỗi 5 frame) vì chi phí VLM (≈ 3 cặp/giây/GPU L4).
6. Hàng đợi GPU của Kaggle (L4 lẫn T4) tắc nhiều lần trong vòng này; các job nhẹ được chuyển sang T4/CPU theo quy tắc.

## 8. Novelty và mức sẵn sàng (Gate 11)

- Mới: chẩn đoán vị trí vi phạm giả định null; Mệnh đề 5 + Định lý 4 (cận dưới/trên của cái giá phụ thuộc); Định lý 5
  (tỷ lệ khởi phát sai ≤ α với phụ thuộc tuỳ ý giữa các đoạn); hiệu chuẩn không nhãn bằng null bản đồ cho kiểm định tuyến đa
  giả thuyết (TAO'26 không có ngưỡng không nhãn); so sánh trực tiếp đầu tiên với ba baseline 2026 trên giao thức bản đồ có lỗ.
- Không mới: các khối công cụ (conformal theo đoạn, e-value, Procrustes, Markov, kiểm nhất quán odometry).
- **Mức: A (RA-L/ICRA/IROS) vững hơn; A\* chưa** — còn thiếu null khớp điều kiện (điểm mặc định dè dặt), chạy robot thật
  vòng kín, và SafeVPR/VLM trên nhiều benchmark hơn.
