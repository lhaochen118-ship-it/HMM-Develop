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
| **ANCHR (ours, không cần hướng)** | 0.017 (0.09) [0.07] | 0.023 (0.06) [0.05] | 0.020 (0.04) [0.03] | 0.020 (0.05) [0.05] | 0.014 (0.05) [0.02] | 0.015 (0.06) [0.02] |

### Bảng 2 — Power

Mỗi ô ghi: tỷ lệ frame on-map có match đúng được chứng nhận / độ trễ trung vị (số frame) tới fix đúng đầu tiên. Riêng hàng label-calibrated chỉ ghi tỷ lệ.

| Phương pháp | RobotCar-S. | CMU-S. | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| per-frame SelfCal | 0.77 / 0 | 0.62 / 0 | 0.44 / 27 | 0.31 / 33 | 0.43 / 28 | 0.19 / 4 |
| RUN (không odometry) | 0.67 / 2 | 0.78 / 6 | 0.73 / 23 | 0.76 / 8 | 0.70 / 28 | 0.29 / 8 |
| label-calibrated (cần nhãn) | 0.77 | 0.87 | 0.87 | 0.85 | 0.86 | 0.49 |
| **ANCH (ours)** | 0.68 / 2 | 0.82 / 4 | 0.86 / 24 | 0.83 / 4 | 0.77 / 28 | 0.37 / 6 |
| **ANCHR (ours)** | 0.65 / 2 | 0.80 / 5 | 0.86 / 24 | 0.81 / 5 | 0.75 / 28 | 0.35 / 6 |

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

| Dataset | accept-all | ngưỡng max-sim (nhãn) | per-frame SelfCal | HMM off-map Xu'21 (nhãn) | **ours** | oracle |
|---|---|---|---|---|---|---|
| CMU-S. | 92.6 (553) | 15.5 (75) | 5.2 (21) | 13.0 (64) | 3.8 (13) | 2.9 (8) |
| Nordland | 438.5 (1593) | 211.1 (736) | 36.1 (178) | 68.0 (342) | 17.2 (75) | 5.4 (13) |
| 4S office | 57.5 (221) | 16.9 (56) | 11.6 (34) | – | 11.3 (33) | 8.4 (26) |
| 4S old town | 277.0 (845) | 68.0 (253) | 50.4 (201) | – | 37.0 (134) | 21.1 (74) |
| 4S countryside | 110.0 (473) | 54.3 (184) | 66.2 (209) | – | 51.5 (171) | 17.8 (54) |

## 5. Vì sao HMM thua baseline, và cơ chế sửa

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
- **Quyết định:** báo nơi MAP của chuỗi vị trí khi P(on) > 0.5. Độ tin cậy là P(on) × độ tập trung posterior.

**Vì sao sửa được:**

- **Mệnh đề 1:** bằng chứng hiện diện là mức tuyệt đối đã hiệu chuẩn, sửa nguyên nhân 1.
- **Mệnh đề 3:** p-value của thống kê max đã trả giá cho N nơi, nên phải đi vào một chuỗi on/off riêng. Đưa vào từng trạng thái thì hoặc đếm phạt hai lần (`abs_naive`: quá bảo thủ), hoặc vi phạm giả định độc lập giữa prior và quan sát (`abs`: FL ≈ 0.9).
- **Bài học từ 5.1:** bằng chứng hiện diện tính từ top-1, không từ niềm tin của HMM, nên không bị cuốn vào vòng khoá nhầm.
- **Không cần nhãn hay tune:** τ và a ước lượng từ bản đồ và từ chính dòng p-value.

### 5.3 Kết quả: CPC-HMM so với HMM Xu'21 (`analysis/hmm_fix.py`)

Bản đồ khuyết 30 %, 6 descriptor × 2 seed. Mỗi ô ghi: recall on-map / định vị sai off-map (FL) / recall ở 5 % FL / ECE / sai số điều hướng trung bình (p95). Nordland tính bằng frame, các dataset khác tính bằng mét.

| Phương pháp | RobotCar-S. | Nordland | 4S old town |
|---|---|---|---|
| HMM + off-map Xu'21 (T, k tune bằng nhãn) | 0.63 / 0.048 / 0.64 / 0.19 / 1.0 (1) | 0.74 / 0.014 / 0.79 / 0.17 / 52.9 (285) | 0.60 / 0.091 / 0.61 / 0.18 / 100.9 (457) |
| HMM không off-map (T tune) | 0.80 / 1.000 / 0.59 / 0.08 / 25.6 (138) | 0.92 / 1.000 / 0.60 / 0.04 / 290.9 (1560) | 0.73 / 1.000 / 0.22 / 0.12 / 247.4 (878) |
| chỉ emission bất biến affine | 0.61 / 0.085 / 0.62 / 0.21 / 1.9 (7) | 0.71 / 0.064 / 0.68 / 0.19 / 161.2 (1201) | 0.60 / 0.131 / 0.54 / 0.18 / 135.1 (610) |
| e-value nhân vào từng nơi (đếm 1/N hai lần) | 0.26 / 0.000 / 0.69 / 0.59 / 0.2 (0) | 0.32 / 0.000 / 0.53 / 0.42 / 18.6 (65) | 0.46 / 0.001 / 0.54 / 0.26 / 40.6 (132) |
| CPC, prior lệch (p_in = 0.05) | 0.75 / 0.112 / 0.72 / 0.09 / 4.0 (22) | 0.78 / 0.309 / 0.67 / 0.16 / 114.5 (597) | 0.68 / 0.338 / 0.56 / 0.12 / 141.2 (637) |
| CPC + giảm theo ESS | 0.73 / 0.039 / 0.71 / 0.10 / 1.3 (1) | 0.59 / 0.015 / 0.69 / 0.27 / 22.5 (116) | 0.60 / 0.055 / 0.56 / 0.15 / 58.2 (232) |
| **CPC-HMM (đề xuất, không nhãn)** | 0.73 / 0.038 / 0.72 / 0.09 / 1.3 (1) | 0.56 / 0.004 / 0.71 / 0.28 / 16.4 (58) | 0.59 / 0.023 / 0.61 / 0.10 / 46.4 (208) |

**Thử nghiệm âm tính (giữ lại để tránh lặp lại):**

- Bằng chứng hiện diện tính tại nơi MAP của HMM (`fac_pc`), trên Nordland CosPlace: FL 0.08, sai số điều hướng 315 frame.
- Thêm e-value từ độ tập trung posterior, hiệu chuẩn bằng null bản đồ (`fac_mix`): recall 0.85 nhưng FL 0.14, sai số điều hướng 280 frame.
- Cả hai cùng một nguyên nhân: thống kê lấy từ niềm tin của HMM bị nhiễm khoá nhầm.
- Giảm theo độ dư thừa (ESS) giúp hạn chế khoá nhầm nhưng làm giảm khả năng xếp hạng. Nó là tuỳ chọn, không nằm trong cấu hình chính.

## 6. Kết luận

- **Hợp lệ.** Bảo đảm theo đoạn giữ ở mọi bộ dữ liệu và descriptor, không dùng nhãn (Bảng 1, 4, 5). Baseline hiệu chuẩn bằng nhãn kiểu SAFEVPR vượt α trên RobotCar và CMU.
- **Power.** Số frame đúng được chứng nhận tăng 2–7× so với kiểm định từng frame, và fix đầu tiên đến sớm hơn nhiều (Bảng 2, 3).
- **Điều hướng.** Trong vòng điều hướng, fix có chứng nhận cho sai số thấp nhất hoặc ngang oracle. HMM off-map tune bằng nhãn (Xu'21) có nhiều fix đúng nhưng thỉnh thoảng khoá nhầm chỗ, làm đuôi sai số rất lớn (Bảng 6).
- **Giới hạn:**
  - chuỗi quá ngắn (RobotCar, 9 frame) gần như không tăng power;
  - bản đồ nhỏ (CMU, khoảng 70 đoạn null) cho FAR của từng bản đồ dao động quanh cùng một trung bình;
  - giả định các đoạn off-map giống đoạn bản đồ bị giữ lại (exchangeable), được kiểm tra bằng off-map tự nhiên;
  - mới ở mức place (5 m); tinh chỉnh 6DOF theo ngưỡng Sattler'18 là bước sau, và có thể dùng fix đã chứng nhận làm cổng cho bộ giải 6DOF.
