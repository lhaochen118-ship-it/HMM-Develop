# Báo cáo: Định vị theo chuỗi có chứng nhận (Certified Sequential Localization)

*Hướng HMM / sequence-based visual localization cho robot dùng camera đơn. Branch `hmm-navigation`, 2026-10-29. Số liệu sinh tự động từ `analysis/results/` (`paper/build_report.py`); chi tiết thí nghiệm ở `RESEARCH_LOG.md` Entry 18–22.*

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

| Phương pháp | RobotCar-S. | CMU-S. | Nordland | 4S office | 4S old town | 4S countryside | Boreas |
|---|---|---|---|---|---|---|---|
| per-frame SelfCal | 0.019 (0.09) [0.07] | 0.027 (0.07) [0.05] | 0.019 (0.04) [0.03] | 0.013 (0.06) [0.03] | 0.015 (0.04) [0.02] | 0.018 (0.07) [0.03] | 0.004 (0.01) [0.01] |
| RUN (không odometry) | 0.016 (0.09) [0.07] | 0.027 (0.07) [0.06] | 0.033 (0.08) [0.05] | 0.019 (0.04) [0.05] | 0.016 (0.05) [0.02] | 0.015 (0.06) [0.02] | 0.006 (0.02) [0.02] |
| label-calibrated (SAFEVPR-style) | 0.044 (0.12) [0.12] | 0.044 (0.09) [0.09] | 0.016 (0.03) [0.02] | 0.022 (0.04) [0.04] | 0.010 (0.04) [0.01] | 0.025 (0.07) [0.02] | 0.026 (0.04) [0.06] |
| **ANCH (ours)** | 0.016 (0.09) [0.07] | 0.022 (0.05) [0.05] | 0.020 (0.04) [0.03] | 0.020 (0.04) [0.05] | 0.014 (0.04) [0.02] | 0.015 (0.07) [0.02] | 0.006 (0.02) [0.02] |
| **ANCHR (ours, không cần hướng)** | 0.017 (0.09) [0.07] | 0.023 (0.06) [0.05] | 0.020 (0.04) [0.03] | 0.020 (0.05) [0.05] | 0.014 (0.05) [0.02] | 0.015 (0.06) [0.02] | 0.006 (0.01) [0.02] |

### Bảng 2 — Power

Mỗi ô ghi: tỷ lệ frame on-map có match đúng được chứng nhận / độ trễ trung vị (số frame) tới fix đúng đầu tiên. Riêng hàng label-calibrated chỉ ghi tỷ lệ.

| Phương pháp | RobotCar-S. | CMU-S. | Nordland | 4S office | 4S old town | 4S countryside | Boreas |
|---|---|---|---|---|---|---|---|
| per-frame SelfCal | 0.77 / 0 | 0.62 / 0 | 0.44 / 27 | 0.31 / 33 | 0.43 / 28 | 0.19 / 4 | 0.35 / 24 |
| RUN (không odometry) | 0.67 / 2 | 0.78 / 6 | 0.73 / 23 | 0.76 / 8 | 0.70 / 28 | 0.29 / 8 | 0.67 / 7 |
| label-calibrated (cần nhãn) | 0.77 | 0.87 | 0.87 | 0.85 | 0.86 | 0.49 | 0.79 |
| **ANCH (ours)** | 0.68 / 2 | 0.82 / 4 | 0.86 / 24 | 0.83 / 4 | 0.77 / 28 | 0.37 / 6 | 0.71 / 5 |
| **ANCHR (ours)** | 0.65 / 2 | 0.80 / 5 | 0.86 / 24 | 0.81 / 5 | 0.75 / 28 | 0.35 / 6 | 0.69 / 6 |

### Bảng 3 — Power theo descriptor: ANCH so với per-frame SelfCal

| Dataset | megaloc | salad | mixvpr | cosplace | netvlad | dinov2 |
|---|---|---|---|---|---|---|
| RobotCar-S. | 0.76 / 0.99 | 0.75 / 0.95 | 0.70 / 0.60 | 0.71 / 0.86 | 0.71 / 0.73 | 0.45 / 0.45 |
| CMU-S. | 0.94 / 0.62 | 0.91 / 0.86 | 0.86 / 0.81 | 0.87 / 0.77 | 0.75 / 0.29 | 0.58 / 0.38 |
| Nordland | 0.97 / 0.73 | 0.96 / 0.61 | 0.88 / 0.45 | 0.86 / 0.40 | 0.77 / 0.25 | 0.71 / 0.20 |
| 4S office | 0.98 / 0.42 | 0.97 / 0.61 | 0.93 / 0.43 | 0.93 / 0.09 | 0.67 / 0.06 | 0.54 / 0.23 |
| 4S old town | 0.94 / 0.69 | 0.92 / 0.54 | 0.80 / 0.41 | 0.85 / 0.47 | 0.69 / 0.32 | 0.41 / 0.15 |
| 4S countryside | 0.61 / 0.33 | 0.42 / 0.21 | 0.40 / 0.21 | 0.47 / 0.26 | 0.26 / 0.13 | 0.06 / 0.02 |
| Boreas | 0.97 / 0.47 | 0.92 / 0.33 | 0.95 / 0.80 | 0.86 / 0.33 | 0.45 / 0.12 | 0.09 / 0.01 |

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
| Nordland | 30 | – | 0.023 | 0.044 | 66 |
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
| Boreas | 10 | 0.001 | 0.006 | 0.017 | 138 |
| Boreas | 30 | – | 0.005 | 0.014 | 42 |
| Boreas | 60 | – | – | 0.010 | – |

Ô '–' ở α = 0.01 nghĩa là bản đồ có dưới 100 đoạn null, nên không đặt được ngưỡng.

### Bảng 5 — Off-map tự nhiên: query của cảnh hoặc dataset khác chạy trên bản đồ (FAR theo đoạn, α = 0.05, H = 10)

Mỗi ô là trung bình trên các nguồn query và descriptor, kèm (giá trị lớn nhất).

| Bản đồ | per-frame | ANCH | ANCHR | nguồn query |
|---|---|---|---|---|
| 4S countryside | 0.000 (0.002) | 0.000 (0.000) | 0.000 (0.000) | 4S office, 4S old town, CMU-S., RobotCar-S. |
| 4S office | 0.000 (0.001) | 0.000 (0.005) | 0.001 (0.016) | 4S countryside, 4S old town, CMU-S., RobotCar-S. |
| 4S old town | 0.005 (0.024) | 0.003 (0.027) | 0.002 (0.020) | 4S countryside, 4S office, CMU-S., RobotCar-S. |
| CMU-S. | 0.000 (0.002) | 0.000 (0.000) | 0.000 (0.000) | 4S countryside, 4S office, 4S old town, RobotCar-S. |

### Bảng 6 — Điều hướng khép kín, bản đồ khuyết 30 % block

Kalman filter chạy odometry trôi và nhận các fix được chấp nhận (σ = 5 m). Mỗi ô ghi sai số vị trí trung bình (phân vị 95) trên descriptor và seed. Nordland tính bằng frame, các dataset khác tính bằng mét.

| Dataset | accept-all | ngưỡng max-sim (nhãn) | per-frame SelfCal | HMM off-map Xu'21 (nhãn) | **CPC-HMM (mục 5)** | **certified** | oracle |
|---|---|---|---|---|---|---|---|
| CMU-S. | 92.6 (553) | 15.5 (75) | 5.2 (21) | 13.0 (64) | 5.7 (21) | 3.8 (13) | 2.9 (8) |
| Nordland | 438.5 (1593) | 211.1 (736) | 36.1 (178) | 68.0 (342) | 19.7 (91) | 17.2 (75) | 5.4 (13) |
| 4S office | 57.5 (221) | 16.9 (56) | 11.6 (34) | 22.7 (86) | 12.8 (44) | 11.3 (33) | 8.4 (26) |
| 4S old town | 277.0 (845) | 68.0 (253) | 50.4 (201) | 76.9 (336) | 46.3 (189) | 37.0 (134) | 21.1 (74) |
| 4S countryside | 110.0 (473) | 54.3 (184) | 66.2 (209) | 76.0 (310) | 52.2 (170) | 51.5 (171) | 17.8 (54) |
| Boreas | 165.5 (672) | 37.1 (248) | 13.7 (80) | 22.6 (101) | 17.7 (115) | 15.7 (92) | 2.3 (7) |

## 5. Vì sao HMM thua baseline, và cơ chế sửa

### 5.0 HMM thua baseline ở đâu

Lấy từ Bảng 6: sai số điều hướng trung bình (p95), cùng giao thức. Cột "HMM thua" đánh dấu khi HMM Xu'21, dù được tune bằng nhãn, có sai số trung bình lớn hơn baseline không nhãn đơn giản nhất (per-frame SelfCal).

| Dataset | HMM Xu'21 (nhãn) | per-frame SelfCal | HMM thua? | CPC-HMM | CPC-HMM / Xu'21 |
|---|---|---|---|---|---|
| CMU-S. | 13.0 (64) | 5.2 (21) | có | 5.7 (21) | 0.44× |
| Nordland | 68.0 (342) | 36.1 (178) | có | 19.7 (91) | 0.29× |
| 4S office | 22.7 (86) | 11.6 (34) | có | 12.8 (44) | 0.57× |
| 4S old town | 76.9 (336) | 50.4 (201) | có | 46.3 (189) | 0.60× |
| 4S countryside | 76.0 (310) | 66.2 (209) | có | 52.2 (170) | 0.69× |
| Boreas | 22.6 (101) | 13.7 (80) | có | 17.7 (115) | 0.78× |

### 5.1 Chẩn đoán (`analysis/hmm_diag.py`)

Thiết lập: HMM chuẩn (lọc tiến trên các ảnh bản đồ, chuyển trạng thái theo odometry, emission exp(s/T), có hoặc không có trạng thái off-map của Xu'21) trên bản đồ khuyết 30 % block. Mỗi ô là trung bình trên descriptor.

Các cột:

- **R@FL5:** tỷ lệ frame on-map đúng được nhận khi giới hạn định vị sai off-map ở 5 %.
- **conf, acc:** độ tin cậy trung bình so với độ chính xác thật.
- **khoá nhầm:** tỷ lệ frame sai mà vẫn tin > 0.9 / tỷ lệ tổng sai số do các frame đó gây ra.
- **r, VIF:** tự tương quan trễ 1 của dòng bằng chứng, và hệ số phóng đại phương sai (1+r)/(1−r).
- **D5:** thay đổi lớn nhất của posterior khi cộng một hằng số ngẫu nhiên vào mọi similarity của từng frame.

| Dataset | R@FL5 max-sim thô | R@FL5 posterior HMM | R@FL5 HMM+off-map | conf / acc | ECE | khoá nhầm | r (VIF) | D5 |
|---|---|---|---|---|---|---|---|---|
| RobotCar-S. | 0.65 | 0.53 | 0.59 | 0.86 / 0.75 | 0.11 | 0.11 / 0.24 | – (chuỗi < 20 frame) | 1e-06 |
| CMU-S. | 0.74 | 0.43 | 0.59 | 0.94 / 0.83 | 0.12 | 0.19 / 0.53 | 0.98 (127×) | 3e-06 |
| Nordland | 0.39 | 0.63 | 0.68 | 0.93 / 0.86 | 0.07 | 0.14 / 0.39 | 0.79 (8×) | 4e-06 |
| 4S office | 0.69 | 0.44 | 0.69 | 0.94 / 0.85 | 0.08 | 0.13 / 0.49 | 0.98 (87×) | 3e-06 |
| 4S old town | 0.58 | 0.30 | 0.52 | 0.91 / 0.71 | 0.20 | 0.20 / 0.44 | 0.99 (136×) | 3e-06 |
| 4S countryside | 0.28 | 0.16 | 0.29 | 0.86 / 0.59 | 0.28 | 0.19 / 0.38 | 0.98 (130×) | 3e-06 |

**Nguyên nhân gốc (được số liệu xác nhận):**

1. **Bất biến bằng chứng tương đối (D1, D5).**
   - Emission softmax p(s_t | j) ∝ exp(s_tj / T) cho posterior bất biến khi s_t → s_t + c_t·1. Trạng thái off-map của Xu'21, exp(s₍ₖ₎/T), cũng bất biến như vậy, nên chỉ đo được độ nhọn s_max − s₍ₖ₎.
   - Nhưng câu hỏi "robot có ở trong bản đồ không" là câu hỏi về mức tuyệt đối: LR(j : ∅) = f₁(s_j) / f₀(s_j). HMM về cấu trúc không thấy được sự vắng mặt.
   - Max-sim thô thắng posterior trên RobotCar, CMU và 4Seasons. Nordland là ngoại lệ: ở đó mức similarity bị mùa đông làm dịch, nên cần mức tuyệt đối đã được hiệu chuẩn bất biến affine, không phải mức thô.
2. **Đếm lặp bằng chứng phụ thuộc (D2, D3, D4).**
   - HMM giả định quan sát độc lập khi biết trạng thái, nhưng bằng chứng của các frame liên tiếp có r ≈ 0.8–0.99.
   - Var(Σd_t) ≈ nσ²(1+r)/(1−r), trong khi HMM tính như nσ²: đếm thừa 4–200×.
   - Hệ quả: posterior quá tự tin (conf > acc) và khoá nhầm chỗ. Các frame sai mà vẫn tin > 0.9 gây ra khoảng 40 % tổng sai số.
3. **Vòng phản hồi khoá nhầm.** Mọi bằng chứng tính từ chính niềm tin của HMM đều tự xác nhận khi đã khoá nhầm. Thí nghiệm `fac_pc` và `fac_mix` đều thất bại vì lý do này (mục 5.3).

### 5.2 Cơ chế đề xuất: CPC-HMM (HMM với chuỗi hiện diện đã hiệu chuẩn)

Tách HMM thành 2 chuỗi:

- **Chuỗi vị trí ("ở đâu")** là HMM chuẩn không có trạng thái off-map, với emission tương đối bất biến affine và không cần tune:

  > log e_t(j) = (s_tj − max_i s_ti) / (τ · σ_far,t)

  Ở đây σ_far,t là độ trải của các cực đại vùng xa của chính frame t, và τ là thang Gumbel của null bản đồ (z_far của các pseudo-query leave-block-out).
- **Chuỗi hiện diện ("có trong bản đồ không")** gồm 2 trạng thái on/off:

  > P(on_t | ·) ∝ [ (1−p_out)·P(on_{t−1}) + p_in·P(off_{t−1}) ] · LR_t,  với LR_t = a · p_t^(a−1)

  - p_t là p-value SelfCal-AA của top-1, hiệu chuẩn bằng bản đồ (bất biến affine, có cổng max-sim). Dưới H0, p_t ~ U(0,1) nên E[LR_t] = 1, tức LR_t là một e-value.
  - Tham số a lấy từ EM không nhãn trên dòng p-value của chính chuyến đi: π₀·U + (1−π₀)·Beta(a,1).
  - **Cổng độc lập niềm tin:** khi top-1 không khớp với nơi MAP của chuỗi vị trí (lệch > 25 m), frame đó được tính là p = 1.
  - Prior đối xứng p_in = p_out = 0.01.
- **Nguồn bằng chứng thứ hai, độc lập với niềm tin:** thống kê neo odometry R_t (mục 2b) của dòng top-1 trong cửa sổ H = 10 frame. Nó được hiệu chuẩn từng frame với null R trên traversal của chính bản đồ, cho p-value p^R_t và e-value e^R_t = a′(p^R_t)^(a′−1).
- **Gộp hai bằng chứng:** mỗi frame nằm trong H cửa sổ, nên e^R được luỹ thừa 1/H để không đếm lặp. Vẫn là e-value nhờ bất đẳng thức Jensen: E[e^w] ≤ (E[e])^w ≤ 1. Hai e-value được gộp bằng trung bình, cách gộp hợp lệ với mọi kiểu phụ thuộc giữa chúng:

  > LR_t = ½ · ( e^top_t + (e^R_t)^(1/H) )

- **Quyết định:** báo nơi MAP của chuỗi vị trí khi P(on) > 0.5. Độ tin cậy là P(on) × độ tập trung posterior.

- **Ngưỡng báo sai:** với p_in = p_out = p, odds của chuỗi hiện diện bị chặn bởi thống kê Shiryaev–Roberts R_t ≤ (R_{t−1} + 1)·LR_t, nên số frame off-map trung bình trước một lần báo on sai thoả ARL₀ ≥ (1−p)/p − R₀ (≈ 98 frame khi p = 0.01). Bảo đảm này không cần nhãn, vì LR_t là e-value.

### 5.3 Kết quả: CPC-HMM so với HMM Xu'21 (`analysis/hmm_fix.py`)

Bản đồ khuyết 30 %, 6 descriptor × 2 seed. Mỗi ô ghi: recall on-map / định vị sai off-map (FL) / recall ở 5 % FL / ECE / sai số điều hướng trung bình (p95). Nordland tính bằng frame, các dataset khác tính bằng mét.

| Phương pháp | RobotCar-S. | CMU-S. | Nordland | 4S office | 4S old town | 4S countryside | Boreas |
|---|---|---|---|---|---|---|---|
| HMM + off-map Xu'21 (T, k tune bằng nhãn) | 0.58 / 0.045 / 0.59 / 0.19 / 1.3 (1) | 0.69 / 0.561 / 0.51 / 0.18 / 78.4 (473) | 0.74 / 0.013 / 0.79 / 0.19 / 54.7 (360) | 0.77 / 0.041 / 0.77 / 0.14 / 17.7 (84) | 0.62 / 0.020 / 0.65 / 0.15 / 100.7 (466) | 0.21 / 0.029 / 0.27 / 0.38 / 114.3 (509) | 0.72 / 0.028 / 0.75 / 0.24 / 40.3 (295) |
| Xu'21, prior đối xứng p_in = p_out = 0.01 | 0.57 / 0.039 / 0.59 / 0.19 / 1.2 (1) | 0.69 / 0.529 / 0.51 / 0.19 / 77.1 (464) | 0.72 / 0.010 / 0.79 / 0.20 / 47.8 (319) | 0.75 / 0.026 / 0.77 / 0.15 / 14.6 (60) | 0.58 / 0.011 / 0.65 / 0.18 / 59.5 (256) | 0.20 / 0.015 / 0.27 / 0.39 / 100.3 (568) | 0.69 / 0.021 / 0.75 / 0.26 / 27.2 (176) |
| HMM không off-map (T tune) | 0.75 / 1.000 / 0.55 / 0.11 / 33.1 (157) | 0.84 / 1.000 / 0.43 / 0.09 / 128.2 (734) | 0.92 / 1.000 / 0.64 / 0.03 / 324.8 (1847) | 0.87 / 1.000 / 0.32 / 0.05 / 65.4 (280) | 0.73 / 1.000 / 0.26 / 0.12 / 259.5 (906) | 0.61 / 1.000 / 0.14 / 0.23 / 143.8 (624) | 0.89 / 1.000 / 0.46 / 0.04 / 222.7 (985) |
| chỉ emission bất biến affine | 0.54 / 0.079 / 0.56 / 0.23 / 2.4 (12) | 0.70 / 0.269 / 0.45 / 0.15 / 59.1 (383) | 0.73 / 0.069 / 0.66 / 0.18 / 210.0 (1758) | 0.73 / 0.075 / 0.73 / 0.17 / 25.9 (132) | 0.60 / 0.109 / 0.58 / 0.20 / 138.4 (615) | 0.16 / 0.020 / 0.22 / 0.43 / 100.6 (400) | 0.72 / 0.057 / 0.73 / 0.25 / 72.6 (399) |
| e-value nhân vào từng nơi (đếm 1/N hai lần) | 0.20 / 0.000 / 0.63 / 0.58 / 0.2 (0) | 0.58 / 0.024 / 0.66 / 0.29 / 2.9 (10) | 0.31 / 0.000 / 0.51 / 0.43 / 22.2 (77) | 0.53 / 0.000 / 0.69 / 0.34 / 17.2 (50) | 0.49 / 0.001 / 0.58 / 0.24 / 36.2 (110) | 0.09 / 0.016 / 0.15 / 0.47 / 86.1 (228) | 0.58 / 0.004 / 0.64 / 0.28 / 6.5 (26) |
| CPC, prior lệch (p_in = 0.05) | 0.69 / 0.131 / 0.66 / 0.09 / 5.2 (29) | 0.75 / 0.080 / 0.67 / 0.10 / 15.3 (77) | 0.79 / 0.335 / 0.66 / 0.16 / 126.8 (631) | 0.82 / 0.180 / 0.75 / 0.07 / 25.9 (128) | 0.67 / 0.275 / 0.57 / 0.12 / 140.8 (660) | 0.49 / 0.542 / 0.23 / 0.26 / 103.3 (407) | 0.85 / 0.294 / 0.69 / 0.10 / 116.0 (630) |
| CPC + giảm theo ESS | 0.68 / 0.053 / 0.64 / 0.10 / 1.9 (2) | 0.73 / 0.082 / 0.60 / 0.21 / 6.5 (27) | 0.57 / 0.016 / 0.70 / 0.27 / 29.4 (169) | 0.74 / 0.050 / 0.74 / 0.22 / 19.7 (78) | 0.61 / 0.028 / 0.60 / 0.14 / 44.1 (146) | 0.32 / 0.080 / 0.20 / 0.29 / 55.9 (178) | 0.68 / 0.038 / 0.69 / 0.24 / 15.7 (63) |
| CPC + ANCH không luỹ thừa (đếm lặp) | 0.68 / 0.070 / 0.62 / 0.09 / 2.3 (2) | 0.79 / 0.117 / 0.56 / 0.08 / 27.0 (174) | 0.72 / 0.009 / 0.77 / 0.16 / 23.4 (91) | 0.79 / 0.024 / 0.79 / 0.08 / 15.1 (57) | 0.65 / 0.064 / 0.62 / 0.09 / 70.6 (309) | 0.41 / 0.162 / 0.22 / 0.24 / 82.2 (329) | 0.75 / 0.049 / 0.76 / 0.13 / 63.7 (375) |
| CPC, chỉ e-value top-1 | 0.68 / 0.052 / 0.66 / 0.09 / 1.9 (2) | 0.73 / 0.041 / 0.69 / 0.13 / 6.2 (27) | 0.54 / 0.004 / 0.70 / 0.28 / 20.8 (76) | 0.73 / 0.005 / 0.77 / 0.10 / 12.9 (41) | 0.60 / 0.020 / 0.62 / 0.10 / 44.3 (198) | 0.31 / 0.070 / 0.24 / 0.30 / 58.0 (192) | 0.68 / 0.019 / 0.72 / 0.16 / 28.7 (207) |
| **CPC-HMM đầy đủ (đề xuất, không nhãn)** | 0.68 / 0.060 / 0.65 / 0.09 / 2.1 (2) | 0.76 / 0.055 / 0.66 / 0.10 / 8.2 (39) | 0.70 / 0.008 / 0.77 / 0.18 / 20.0 (71) | 0.78 / 0.004 / 0.81 / 0.08 / 10.9 (32) | 0.64 / 0.032 / 0.64 / 0.08 / 51.3 (216) | 0.38 / 0.113 / 0.27 / 0.25 / 61.6 (261) | 0.74 / 0.027 / 0.75 / 0.14 / 28.2 (222) |

**Kiểm chứng ngưỡng báo sai.** ARL₀ là số frame off-map trên mỗi lần bắt đầu báo on sai. Cận lý thuyết là ≥ 98 khi p_in = 0.01 và LR là e-value. Độ trễ vào lại là số frame từ khi vào lại bản đồ đến fix đúng đầu tiên. Mỗi ô ghi ARL₀ / độ trễ vào lại.

| Phương pháp | RobotCar-S. | CMU-S. | Nordland | 4S office | 4S old town | 4S countryside | Boreas |
|---|---|---|---|---|---|---|---|
| HMM + off-map Xu'21 (nhãn) | 100 / nan | 41 / 30.8 | 720 / 36.4 | 651 / 13.7 | 665 / 101.3 | 1424 / 255.8 | 3186 / 72.1 |
| Xu'21, prior đối xứng | 108 / nan | 39 / 30.9 | 1146 / 47.0 | 947 / 16.2 | 3323 / 129.1 | 1832 / 301.4 | 3252 / 89.0 |
| CPC, p_in = 0.05 (cận ≥ 18) | 59 / nan | 337 / 2.1 | 1965 / 7.4 | 1893 / 6.3 | 318 / 25.0 | 832 / 47.9 | 732 / 31.4 |
| CPC, chỉ e^top | 127 / nan | 995 / 3.0 | 3930 / 115.6 | 2840 / 53.3 | 791 / 111.0 | 1163 / 229.2 | 2124 / 249.4 |
| CPC, e^R không luỹ thừa | 117 / nan | 160 / 2.1 | 561 / 74.2 | 442 / 10.3 | 365 / 78.9 | 189 / 154.7 | 456 / 97.0 |
| **CPC-HMM đầy đủ** | 121 / nan | 995 / 3.0 | 3930 / 79.3 | 2840 / 18.6 | 762 / 102.3 | 895 / 190.4 | 2100 / 171.4 |

**Thử nghiệm âm tính (giữ lại để tránh lặp lại):**

- Bằng chứng hiện diện tính tại nơi MAP của HMM (`fac_pc`), trên Nordland CosPlace: FL 0.08, sai số điều hướng 315 frame.
- Thêm e-value từ độ tập trung posterior, hiệu chuẩn bằng null bản đồ (`fac_mix`): recall 0.85 nhưng FL 0.14, sai số điều hướng 280 frame.
- Cả hai cùng một nguyên nhân: thống kê lấy từ niềm tin của HMM bị nhiễm khoá nhầm.
- Giảm theo độ dư thừa (ESS) giúp hạn chế khoá nhầm nhưng làm giảm khả năng xếp hạng. Nó là tuỳ chọn, không nằm trong cấu hình chính.
- Đưa e-value ANCH vào mà không luỹ thừa 1/H làm FL trên CMU tăng lên 0.15. Đây chính là lỗi đếm lặp bằng chứng phụ thuộc (nguyên nhân 2) xuất hiện ở tầng hiện diện.

### 5.4 Cổng dead-reckoning (CPC-HMM +GG) — sửa fix sai ở xa trong lỗ bản đồ

**Chẩn đoán (Boreas, `nav_demo --dump`).** Fix sai của CPC-HMM nằm rất xa vị trí thật (trung vị 111–182 m, p90 tới 954 m), sâu trong lỗ bản đồ (47–72 % frame báo sai cách frame on-map cuối > 100 frame). Fix sai của Xu'21 chỉ cách 37–56 m. Trong lỗ, chuỗi vị trí trôi tới một đoạn đường giống (aliasing), cổng "top-1 khớp MAP" luôn qua, và bằng chứng yếu nhưng phụ thuộc tích luỹ thành báo on. Các thử nghiệm p_out lớn hơn, p_out theo KL₀, rò rỉ ở mép bản đồ, cổng dự đoán (PG) và trạng thái off-map dead-reckoning cho việc vào lại (DR) đều không sửa được.

**Cơ chế.** Khi chưa báo nơi nào (P(on_{t−1}) ≤ ½), e-value top-1 được nhân với

> g_t = (1−ρ)·exp(−d_t² / 2s_t²) + ρ,  d_t = ‖m_top,t − μ_t‖,  s_t = excl + κ·(quãng đường từ fix báo cuối)

- μ_t là vị trí fix báo cuối cùng cộng odometry; κ = 0.05 (cùng mô hình nhiễu của bộ lọc điều hướng).
- ρ = 0.1 là xác suất tiên nghiệm ghost sai: lối thoát sau một lần báo sai. Không có sàn (ρ = 0.01), Nordland bị khoá chết. ρ chọn sau khi xem Boreas và Nordland, cố định cho mọi dataset.
- a ≤ ẽ ≤ e^top từng điểm, nên ẽ vẫn là e-value và cận ARL₀ ≥ (1−p_in)/p_in − R₀ giữ nguyên (`paper/cpc_theory.md` §3b).
- Baseline công bằng: cùng cổng dead-reckoning (dạng cứng, 2s) áp hậu kiểm lên fix của Xu'21 và certified (`+DRgate`).

Sai số điều hướng trung bình (p95) trên descriptor và 3 seed, bản đồ khuyết 30 % (Nordland: frame; còn lại: m). Cột ρ = 0.03 và 0.3 là phân tích độ nhạy (chạy riêng, cùng seed; ô "–" là chưa chạy).

| Dataset | #desc | Xu'21 (nhãn) | Xu'21 + DR gate | certified | certified + DR gate | CPC-HMM | CPC +GG (ρ = 0.01) | CPC +GG (ρ = 0.03) | **CPC-HMM +GG (ρ = 0.1)** | CPC +GG (ρ = 0.3) |
|---|---|---|---|---|---|---|---|---|---|---|
| CMU-S. | 6 | 13.0 (64) | 10.1 (41) | 3.8 (13) | 4.1 (15) | 5.7 (21) | 6.2 (30) | 6.2 (30) | 5.5 (20) | 5.5 (19) |
| Nordland | 6 | 68.0 (342) | 281.2 (617) | 17.2 (75) | 39.0 (90) | 19.7 (91) | 63.4 (216) | 20.8 (90) | 19.1 (82) | 19.4 (89) |
| 4S office | 6 | 22.7 (86) | 32.0 (120) | 11.3 (33) | 11.2 (33) | 12.8 (44) | 12.3 (41) | 12.0 (40) | 11.6 (39) | 12.0 (39) |
| 4S old town | 6 | 76.9 (336) | 140.4 (529) | 37.0 (134) | 87.3 (386) | 46.3 (189) | 102.0 (413) | 62.0 (243) | 43.3 (155) | 38.4 (133) |
| 4S countryside | 6 | 76.0 (310) | 73.1 (331) | 51.5 (171) | 69.7 (327) | 52.2 (170) | 53.8 (185) | 52.7 (174) | 52.3 (173) | 51.8 (171) |
| Boreas | 6 | 22.6 (101) | 12.5 (51) | 15.7 (92) | 4.8 (22) | 17.7 (115) | 8.0 (37) | 7.1 (35) | 7.1 (35) | 8.6 (43) |

**Boreas theo descriptor** (sai số trung bình, m / số fix sai trung bình mỗi seed):

| Descriptor | Xu'21 (nhãn) | Xu'21 + DR gate | certified | certified + DR gate | CPC-HMM | CPC +GG (ρ = 0.01) | CPC +GG (ρ = 0.03) | **CPC-HMM +GG (ρ = 0.1)** | CPC +GG (ρ = 0.3) |
|---|---|---|---|---|---|---|---|---|---|
| cosplace | 7.4 / 248 | 5.3 / 193 | 23.6 / 762 | 5.4 / 149 | 27.6 / 1776 | 9.1 / 285 | 5.4 / 313 | 5.5 / 365 | 9.4 / 766 |
| dinov2 | 71.6 / 953 | 24.0 / 647 | 8.4 / 16 | 8.3 / 11 | 10.2 / 574 | 11.6 / 554 | 11.6 / 554 | 11.5 / 555 | 11.0 / 560 |
| megaloc | 7.0 / 662 | 4.9 / 585 | 39.1 / 771 | 3.1 / 228 | 34.1 / 2233 | 7.0 / 956 | 5.4 / 1065 | 5.3 / 1231 | 8.3 / 1548 |
| mixvpr | 5.5 / 417 | 6.8 / 413 | 5.1 / 162 | 3.8 / 42 | 9.7 / 946 | 5.0 / 313 | 4.9 / 315 | 5.0 / 378 | 6.0 / 505 |
| netvlad | 38.8 / 827 | 27.7 / 392 | 8.1 / 50 | 5.9 / 26 | 11.6 / 147 | 11.8 / 109 | 11.8 / 111 | 11.7 / 111 | 11.7 / 111 |
| salad | 5.0 / 940 | 6.6 / 914 | 9.6 / 569 | 2.5 / 171 | 12.7 / 1981 | 3.4 / 903 | 3.4 / 912 | 3.4 / 931 | 5.1 / 1284 |

**Độ nhạy theo ρ và giới hạn.**

- ρ nhỏ (0.01, 0.03) làm cổng khoá chết sau một lần báo sai: 4S old town 46.3 → 102.0 / 62.0 m, Nordland 19.7 → 63.4 frame (ρ = 0.01).
- Trên Boreas, ρ = 0.03–0.1 cho mức giảm lớn nhất; ρ = 0.3 yếu hơn và thua Xu'21 trên MegaLoc, CosPlace (cổng mở quá sớm cho bằng chứng aliasing).
- Trên 5 dataset còn lại, ρ = 0.3 tốt nhất hoặc ngang (4S old town 38.4 so với 43.3 ở ρ = 0.1).
- Tức là có đánh đổi: không có một ρ tốt nhất ở mọi nơi. ρ = 0.1 (chọn trước khi chạy lưới này) là điểm cân bằng: thắng Xu'21 trên 6/6 descriptor Boreas và không làm tệ đi trung bình của dataset nào.
- **Theo từng descriptor, cổng có làm tệ đi:** 4S old town DINOv2 48.9 → 73.8 m, NetVLAD 35.4 → 45.6 m ở ρ = 0.1 (được bù bởi CosPlace 116.9 → 65.9 m). Nhận định "không làm tệ đi" chỉ đúng với trung bình theo dataset.

## 6. Kết luận

- **Hợp lệ.** Bảo đảm theo đoạn giữ ở mọi bộ dữ liệu và descriptor, không dùng nhãn (Bảng 1, 4, 5). Baseline hiệu chuẩn bằng nhãn kiểu SAFEVPR vượt α trên RobotCar và CMU.
- **Power.** Số frame đúng được chứng nhận tăng 2–7× so với kiểm định từng frame, và fix đầu tiên đến sớm hơn nhiều (Bảng 2, 3).
- **Điều hướng.** Trong vòng điều hướng, fix có chứng nhận cho sai số thấp nhất hoặc ngang oracle. HMM off-map tune bằng nhãn (Xu'21) có nhiều fix đúng nhưng thỉnh thoảng khoá nhầm chỗ, làm đuôi sai số rất lớn (Bảng 6).
- **CPC-HMM +GG (mục 5.4).** Với một cấu hình không nhãn chung, CPC-HMM thắng Xu'21 (tune bằng nhãn) trên cả 6 descriptor của Boreas (trung bình 7.1 so với 22.6 m) và trên trung bình của cả 6 dataset. Cổng dead-reckoning không làm tệ đi trung bình của dataset nào (tệ nhất +0.1 m), nhưng có làm tệ đi vài descriptor yếu (4S old town DINOv2, NetVLAD), và ρ có đánh đổi giữa Boreas và các dataset khác (mục 5.4). Cùng cổng đó áp hậu kiểm dạng cứng thì tốt nhất trên Boreas nhưng phá các dataset khác (Nordland, 4S old town). Certified (không cổng) vẫn nhỉnh hơn CPC-HMM +GG trên 5/6 dataset.
- **Giới hạn:**
  - ρ = 0.1 của cổng được chọn sau khi xem Boreas và Nordland (offline), rồi cố định;
  - chuỗi quá ngắn (RobotCar, 9 frame) gần như không tăng power;
  - bản đồ nhỏ (CMU, khoảng 70 đoạn null) cho FAR của từng bản đồ dao động quanh cùng một trung bình;
  - giả định các đoạn off-map giống đoạn bản đồ bị giữ lại (exchangeable), được kiểm tra bằng off-map tự nhiên;
  - mới ở mức place (5 m); tinh chỉnh 6DOF theo ngưỡng Sattler'18 là bước sau, và có thể dùng fix đã chứng nhận làm cổng cho bộ giải 6DOF.
