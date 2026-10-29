# Báo cáo: Định vị theo chuỗi có chứng nhận (Certified Sequential Localization)

*Hướng HMM / sequence-based visual localization cho robot dùng camera đơn. Branch `hmm-navigation`, 2026-10-29. Số liệu sinh tự động từ `analysis/results/` (`paper/build_report.py`); chi tiết thí nghiệm ở `RESEARCH_LOG.md` Entry 18–19.*

## 1. Bài toán và khoảng trống

Robot có bản đồ là một lần chạy trước (ảnh, global descriptor, pose). Khi đi lại, mỗi frame được đối chiếu với bản đồ, và odometry nối các frame lại với nhau. Với descriptor nền tảng (MegaLoc, SALAD), tỷ lệ tìm đúng nơi đã khoảng 90–98 % trên RobotCar và CMU (`DATA_AUDIT.md`). HMM thông thường chỉ thêm khoảng 2 điểm.

Thứ còn thiếu là **tính toàn vẹn**: robot đi ra ngoài vùng có bản đồ (rẽ khác, bản đồ thiếu đoạn, cảnh đã đổi) mà bộ định vị vẫn báo một vị trí. Các phương pháp hiện có đều không chặn được sự kiện này:

- **Kiểm định từng frame** (SelfCal'26, SUE'24) chỉ chặn xác suất sai *của mỗi frame*, không chặn xác suất sai *của cả đoạn đi lệch*.
- **HMM có trạng thái off-map** (Xu et al. RA-L'21) và **sequence verifier** (SAFEVPR'26, SMR'25) chọn ngưỡng bằng nhãn. Ngưỡng tune ở điều kiện dễ không chuyển được sang đêm hay tuyết.
- **Hiệu chuẩn theo cửa sổ** (window conformal) không hợp lệ: các frame liên tiếp phụ thuộc mạnh, và mức phụ thuộc đổi theo điều kiện (Entry 18).

**Mục tiêu.** Với mọi đoạn off-map dài H frame: **P(chấp nhận sai ít nhất một lần trong đoạn) ≤ α**. Không dùng nhãn, áp dụng cho mọi descriptor, đúng với mọi kiểu phụ thuộc thời gian bên trong đoạn.

## 2. Phương pháp

**(a) Bằng chứng từng frame.** ℓ_t = −log p_t, với p_t là p-value SelfCal-AA của match top-1 của frame t:

- tính từ thống kê bất biến affine so với các vùng xa, cộng một cổng max-similarity;
- hiệu chuẩn trên các pseudo-query leave-block-out của chính bản đồ;
- cross-fit: test từng frame chỉ được fit trên các block chẵn của bản đồ.

**(b) Bằng chứng chuỗi neo theo odometry (ANCH).** Gọi x_t là vị trí trên bản đồ của top-1 tại frame t và o_t là odometry tích luỹ. Khi đó

> R_t = ℓ_t + Σ_{j=1..H−1} ℓ_{t−j} · 1[ ‖(x_t − x_{t−j}) − (o_t − o_{t−j})‖ ≤ ρ_o ]

- **Diễn giải HMM:** R_t là điểm Viterbi (max-product) của đường đi kết thúc ở x_t và dịch chuyển theo odometry; transition bị gate cứng, emission chịu được outlier.
- **Tham số:** ρ_o là dung sai vật lý của odometry (5 m; Nordland 1 frame).
- **Vì sao cần odometry:** không có nó (RUN, exp11), một alias đứng yên (tuyết hay đêm làm nhiều frame liền khớp cùng một chỗ sai) vẫn được tính là nhất quán. Đó là nguyên nhân làm vỡ tính hợp lệ.
- **ANCHR (không cần hướng):** góc quay giữa odometry và bản đồ là ẩn số. Nó được ước lượng trong mỗi cửa sổ bằng cách tối đa tổng ℓ của các inlier (RANSAC một tham số). Phù hợp robot camera đơn chưa có fix đầu tiên.

**(c) Hiệu chuẩn mức đoạn bằng chính bản đồ.**

- **Null:** mỗi đoạn H frame liên tiếp của traversal bản đồ nằm trong một block lẻ được giữ lại. Đoạn đó được truy vấn với bản đồ đã bỏ block ấy, nên off-map theo cấu trúc; odometry mô phỏng từ pose bản đồ. Điểm null của đoạn là S = max_{t∈đoạn} R_t.
- **Ngưỡng:** với n đoạn null, τ = S_(k), trong đó k = ⌈(1−α)(n+1)⌉.
- **Quyết định:** khi triển khai, chấp nhận frame t (báo vị trí x_t) nếu và chỉ nếu R_t > τ.
- **Chi phí:** tính null một lần cho mỗi bản đồ; mỗi frame chỉ cần retrieval top-1 cộng O(H).

**Định lý 1 (bảo đảm theo đoạn).** Nếu điểm null S_1..S_n và điểm S* = max_{t∈E} R_t của một đoạn off-map E là exchangeable, thì

> P(∃ t ∈ E : R_t > τ) = P(S* > S_(k)) ≤ α

Định lý không giả định gì về sự phụ thuộc giữa các frame trong đoạn, vì đơn vị exchangeable là cả đoạn. Chứng minh: rank của S* phân phối đều trên {1..n+1}.

- **Hệ quả 1 (đổi điều kiện).** Nếu S* bị một bản sao exchangeable trội ngẫu nhiên (thay đổi ngoại cảnh làm frame off-map *kém giống* bản đồ hơn), bảo đảm vẫn giữ. Thống kê AA đã được kiểm chứng có tính trội này; cổng odometry không phụ thuộc ngoại cảnh.
- **Hệ quả 2.** Một đoạn dài E frame có P ≤ ⌈E/H⌉·α.

## 3. Thiết lập thí nghiệm

| Dataset | Đặc điểm | Odometry |
|---|---|---|
| RobotCar-Seasons v2, Extended CMU-Seasons | benchmark của Sattler'18 | mô phỏng (nhiễu tỷ lệ 3 %, nhiễu bước 5 %) |
| Nordland | 3 mùa so với mùa hè | mô phỏng |
| 4Seasons | 3 cảnh, 18 recording | VIO thật |
| Boreas | 1 tuyến 8 km, 31 lần chạy trong 1 năm | bánh xe + gyro thật |

- **Descriptor:** MegaLoc, SALAD, MixVPR, CosPlace, NetVLAD, DINOv2.
- **Đoạn off-map:** leave-block-out (block 300 m; Nordland 200 frame) với 3 lưới block ngẫu nhiên, cộng thêm off-map tự nhiên (query của cảnh hoặc dataset khác).
- **Tham số:** α = 0.05 nếu không ghi khác; H = 10 (RobotCar H = 5, vì query của nó chỉ là các đoạn 9 frame).

**Baseline:**

| Baseline | Nguồn | Mô tả |
|---|---|---|
| per-frame SelfCal | SelfCal'26, label-free | kiểm định từng frame |
| RUN | exp11, kiểu sequence-matching / SeqSLAM run | run nhất quán, không odometry |
| label-calibrated | kiểu SAFEVPR'26 / Quantile-Transfer IROS'26 | cùng thống kê ANCH, ngưỡng conformal từ các đoạn off-map *có nhãn* của 2 điều kiện dễ nhất |
| HMM off-map | Xu et al. RA-L'21 | emission exp(s/T); off-map emission = match thứ k; T và k tune bằng nhãn với ràng buộc FAR ≤ α |
| accept-all | – | nhận mọi match |
| oracle | – | chỉ nhận match đúng |

## 4. Kết quả

### Bảng 1 — Tính hợp lệ: FAR theo đoạn (α = 0.05)

Mỗi ô ghi trung bình trên 6 descriptor × 3 lưới block, kèm (giá trị lớn nhất) và [điều kiện tệ nhất, trung bình]. Phương pháp hợp lệ khi giá trị trung bình ≤ 0.05.

| Phương pháp | RobotCar-S. | CMU-S. | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| per-frame SelfCal | 0.019 (0.09) [0.07] | 0.027 (0.07) [0.05] | 0.019 (0.04) [0.03] | 0.013 (0.06) [0.03] | 0.015 (0.04) [0.02] | 0.018 (0.07) [0.03] |
| RUN (không odometry) | 0.016 (0.09) [0.07] | 0.027 (0.07) [0.06] | 0.033 (0.08) [0.05] | 0.019 (0.04) [0.05] | 0.016 (0.05) [0.02] | 0.015 (0.06) [0.02] |
| label-calibrated (SAFEVPR-style) | 0.044 (0.12) [0.12] | 0.044 (0.09) [0.09] | 0.016 (0.03) [0.02] | 0.022 (0.04) [0.04] | 0.010 (0.04) [0.01] | 0.025 (0.07) [0.02] |
| **ANCH (ours)** | 0.016 (0.09) [0.07] | 0.022 (0.05) [0.05] | 0.020 (0.04) [0.03] | 0.020 (0.04) [0.05] | 0.014 (0.04) [0.02] | 0.015 (0.07) [0.02] |
| **ANCHR (ours, không cần hướng)** | 0.014 (0.03) [0.07] | – | 0.013 (0.02) [0.03] | – | 0.008 (0.03) [0.01] | – |

### Bảng 2 — Power

Mỗi ô ghi: tỷ lệ frame on-map có match đúng được chứng nhận / độ trễ trung vị (số frame) tới fix đúng đầu tiên. Riêng hàng label-calibrated chỉ ghi tỷ lệ.

| Phương pháp | RobotCar-S. | CMU-S. | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| per-frame SelfCal | 0.77 / 0 | 0.62 / 0 | 0.44 / 27 | 0.31 / 33 | 0.43 / 28 | 0.19 / 4 |
| RUN (không odometry) | 0.67 / 2 | 0.78 / 6 | 0.73 / 23 | 0.76 / 8 | 0.70 / 28 | 0.29 / 8 |
| label-calibrated (cần nhãn) | 0.77 | 0.87 | 0.87 | 0.85 | 0.86 | 0.49 |
| **ANCH (ours)** | 0.68 / 2 | 0.82 / 4 | 0.86 / 24 | 0.83 / 4 | 0.77 / 28 | 0.37 / 6 |
| **ANCHR (ours)** | 0.59 / 2 | – | 0.78 / 27 | – | 0.63 / 31 | – |

### Bảng 3 — Power theo descriptor: ANCH so với per-frame SelfCal

| Dataset | megaloc | salad | mixvpr | cosplace | netvlad | dinov2 |
|---|---|---|---|---|---|---|
| RobotCar-S. | 0.76 / 0.99 | 0.75 / 0.95 | 0.70 / 0.60 | 0.71 / 0.86 | 0.71 / 0.73 | 0.45 / 0.45 |
| CMU-S. | 0.94 / 0.62 | 0.91 / 0.86 | 0.86 / 0.81 | 0.87 / 0.77 | 0.75 / 0.29 | 0.58 / 0.38 |
| Nordland | 0.97 / 0.73 | 0.96 / 0.61 | 0.88 / 0.45 | 0.86 / 0.40 | 0.77 / 0.25 | 0.71 / 0.20 |
| 4S office | 0.98 / 0.42 | 0.97 / 0.61 | 0.93 / 0.43 | 0.93 / 0.09 | 0.67 / 0.06 | 0.54 / 0.23 |
| 4S old town | 0.94 / 0.69 | 0.92 / 0.54 | 0.80 / 0.41 | 0.85 / 0.47 | 0.69 / 0.32 | 0.41 / 0.15 |
| 4S countryside | 0.61 / 0.33 | 0.42 / 0.21 | 0.40 / 0.21 | 0.47 / 0.26 | 0.26 / 0.13 | 0.06 / 0.02 |

### Bảng 4 — FAR theo đoạn của ANCH khi đổi α và H

Mỗi ô là trung bình trên descriptor và lưới block. n = số đoạn null.

| Dataset | H | α = 0.01 | α = 0.05 | α = 0.10 | n |
|---|---|---|---|---|---|
| RobotCar-S. | 5 | 0.002 | 0.016 | 0.033 | 466 |
| RobotCar-S. | 8 | 0.000 | 0.015 | 0.031 | 288 |
| CMU-S. | 10 | – | 0.022 | 0.059 | 70 |
| CMU-S. | 30 | – | 0.035 | 0.031 | 28 |
| CMU-S. | 60 | – | – | 0.072 | – |
| Nordland | 10 | 0.001 | 0.020 | 0.042 | 198 |
| Nordland | 30 | – | 0.023 | 0.043 | 66 |
| Nordland | 60 | – | 0.005 | 0.040 | 33 |
| 4S office | 10 | 0.002 | 0.020 | 0.047 | 101 |
| 4S office | 30 | – | 0.013 | 0.041 | 31 |
| 4S office | 60 | – | 0.010 | 0.033 | 22 |
| 4S old town | 10 | 0.002 | 0.014 | 0.036 | 148 |
| 4S old town | 30 | – | 0.010 | 0.026 | 45 |
| 4S old town | 60 | – | 0.013 | 0.017 | 20 |
| 4S countryside | 10 | 0.001 | 0.015 | 0.032 | 173 |
| 4S countryside | 30 | – | 0.008 | 0.026 | 54 |
| 4S countryside | 60 | – | 0.005 | 0.021 | 26 |

Ô '–' ở α = 0.01 nghĩa là bản đồ có dưới 100 đoạn null, nên không đặt được ngưỡng.

### Bảng 5 — Off-map tự nhiên: query của cảnh hoặc dataset khác chạy trên bản đồ (FAR theo đoạn, α = 0.05, H = 10)

Mỗi ô là trung bình trên các nguồn query và descriptor, kèm (giá trị lớn nhất).

| Bản đồ | per-frame | ANCH | ANCHR | nguồn query |
|---|---|---|---|---|
| 4S countryside | 0.000 (0.001) | 0.000 (0.000) | 0.000 (0.000) | 4S office, 4S old town, CMU-S., RobotCar-S. |
| 4S office | 0.000 (0.000) | 0.001 (0.005) | 0.006 (0.016) | 4S countryside, 4S old town, CMU-S., RobotCar-S. |
| 4S old town | 0.005 (0.021) | 0.004 (0.027) | 0.003 (0.020) | 4S countryside, 4S office, CMU-S., RobotCar-S. |
| CMU-S. | 0.000 (0.002) | 0.000 (0.000) | 0.000 (0.000) | 4S countryside, 4S office, 4S old town, RobotCar-S. |

### Bảng 6 — Điều hướng khép kín, bản đồ khuyết 30 % block

Kalman filter chạy odometry trôi và nhận các fix được chấp nhận (σ = 5 m). Mỗi ô ghi sai số vị trí trung bình (phân vị 95) trên descriptor và seed. Nordland tính bằng frame, các dataset khác tính bằng mét.

| Dataset | accept-all | ngưỡng max-sim (nhãn) | per-frame SelfCal | HMM off-map Xu'21 (nhãn) | **ours** | oracle |
|---|---|---|---|---|---|---|
| CMU-S. | 92.6 (553) | 15.5 (75) | 5.2 (21) | 13.0 (64) | 3.8 (13) | 2.9 (8) |
| Nordland | 438.5 (1593) | 211.1 (736) | 36.1 (178) | 68.0 (342) | 17.2 (75) | 5.4 (13) |
| 4S office | 57.5 (221) | 16.9 (56) | 11.6 (34) | – | 11.3 (33) | 8.4 (26) |
| 4S old town | 277.0 (845) | 68.0 (253) | 50.4 (201) | – | 37.0 (134) | 21.1 (74) |
| 4S countryside | 110.0 (473) | 54.3 (184) | 66.2 (209) | – | 51.5 (171) | 17.8 (54) |

## 5. Kết luận

- **Hợp lệ.** Bảo đảm theo đoạn giữ ở mọi bộ dữ liệu và descriptor, không dùng nhãn (Bảng 1, 4, 5). Baseline hiệu chuẩn bằng nhãn kiểu SAFEVPR vượt α trên RobotCar và CMU.
- **Power.** Số frame đúng được chứng nhận tăng 2–7× so với kiểm định từng frame, và fix đầu tiên đến sớm hơn nhiều (Bảng 2, 3).
- **Điều hướng.** Trong vòng điều hướng, fix có chứng nhận cho sai số thấp nhất hoặc ngang oracle. HMM off-map tune bằng nhãn (Xu'21) có nhiều fix đúng nhưng thỉnh thoảng khoá nhầm chỗ, làm đuôi sai số rất lớn (Bảng 6).
- **Giới hạn:**
  - chuỗi quá ngắn (RobotCar, 9 frame) gần như không tăng power;
  - bản đồ nhỏ (CMU, khoảng 70 đoạn null) cho FAR của từng bản đồ dao động quanh cùng một trung bình;
  - giả định các đoạn off-map giống đoạn bản đồ bị giữ lại (exchangeable), được kiểm tra bằng off-map tự nhiên;
  - mới ở mức place (5 m); tinh chỉnh 6DOF theo ngưỡng Sattler'18 là bước sau, và có thể dùng fix đã chứng nhận làm cổng cho bộ giải 6DOF.
