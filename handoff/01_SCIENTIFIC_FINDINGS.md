# 01 — Scientific Findings (hướng HMM-navigation)

*Cập nhật 2026-10-29. Branch `hmm-navigation` → bàn giao sang `hmm-navigation-2`. Tài liệu chỉ nói về **kết quả khoa
học**: đóng góp, ý nghĩa, kết quả tích cực và tiêu cực, kèm bằng chứng và điều kiện kiểm chứng. Vận hành ở `02`, trạng
thái và việc tiếp theo ở `03`. Số liệu đọc từ `analysis/results/*.json`, bảng sinh bằng `paper/build_cert_tables.py`
và `paper/build_report.py`.*

## 0. Bài toán

**Bối cảnh.** Robot dùng camera đơn chạy theo chuỗi frame có odometry, trên một bản đồ ảnh **có lỗ**: có đoạn đường
không có trong bản đồ (off-map). Mỗi frame có similarity tới N ảnh bản đồ (global descriptor).

**Câu hỏi.** Khi nào được tin một "fix" vị trí, để đưa vào bộ lọc điều hướng, sao cho:

1. tỷ lệ fix sai được kiểm soát, **không cần nhãn** của điều kiện mới (đêm, tuyết, mùa);
2. mạnh hơn kiểm định từng frame;
3. đúng cả khi các frame phụ thuộc nhau mạnh.

**Đánh giá.**

- Trong suốt dự án, 30 % block của bản đồ bị bỏ để tạo off-map (thêm 10 % và 50 % cho độ bền).
- Dữ liệu: 7 dataset (RobotCar-Seasons, Extended-CMU, Nordland, 4Seasons ×3 cảnh, Boreas), 6 descriptor (MegaLoc,
  SALAD, MixVPR, CosPlace, NetVLAD, DINOv2), 2–3 seed.
- Odometry thật trên 4Seasons (VIO) và Boreas (bánh xe + gyro); mô phỏng ở các tập còn lại.

## 1. Đóng góp A — Certified sequential localization (hướng chính)

**Phương pháp** (`analysis/cert_seq.py`).

1. p-value SelfCal-AA từng frame, hiệu chuẩn bằng chính bản đồ (leave-block-out, thống kê bất biến affine), cross-fit.
2. Bằng chứng chuỗi neo odometry:

   > R_t = ℓ_t + Σ_{j<H} ℓ_{t−j} · 1[‖(x_t − x_{t−j}) − (o_t − o_{t−j})‖ ≤ ρ_o],  ℓ = −log p

   ANCHR tự fit góc lệch odometry→bản đồ trong mỗi cửa sổ.
3. Hiệu chuẩn theo **đoạn**: ngưỡng là phân vị conformal của max R trên các đoạn H frame của traversal bản đồ bị giữ lại.

**Định lý.** Giả sử các đoạn off-map hoán đổi được (exchangeable) với các đoạn bản đồ giữ lại. Khi đó:

> P(có ít nhất một fix sai trong một đoạn off-map dài H) ≤ α

với mọi kiểu phụ thuộc bên trong đoạn. Đây là lý do cách hiệu chuẩn theo cửa sổ trước đó (exp11/seq_odo) thất bại,
còn cách này đúng.

**Bằng chứng** (α = 0.05; H = 10, RobotCar H = 5; `paper/cert_tables.md`):

| Dataset | FAR theo đoạn, ANCH (tệ nhất) | Baseline hiệu chuẩn bằng nhãn (tệ nhất) | Power ANCH / per-frame / dùng nhãn |
|---|---|---|---|
| RobotCar-S. | 0.016 (0.067) | 0.044 (**0.125**) | 0.68 / 0.77 / 0.77 |
| CMU-S. | 0.022 (0.052) | 0.044 (**0.089**) | 0.82 / 0.62 / 0.87 |
| Nordland | 0.020 (0.033) | 0.016 | 0.86 / 0.44 / 0.87 |
| 4S office | 0.020 (0.049) | 0.022 | 0.83 / 0.31 / 0.85 |
| 4S old town | 0.014 (0.022) | 0.010 | 0.77 / 0.43 / 0.86 |
| 4S countryside | 0.015 (0.025) | 0.025 | 0.37 / 0.19 / 0.49 |
| Boreas | 0.006 (0.017) | 0.026 (**0.062**) | 0.71 / 0.35 / 0.79 |

- **Off-map tự nhiên** (query của cảnh hoặc dataset khác, `cert_natural.py`): FAR ≤ 0.016.
- **α = 0.01 và 0.1** đều bám mục tiêu.
- **Độ trễ tới fix đầu tiên** giảm 5–20×.

**Ý nghĩa.** Đây là bảo đảm không cần nhãn đầu tiên ở mức đoạn (excursion) cho định vị theo chuỗi. Baseline dùng nhãn
của điều kiện dễ (kiểu SAFEVPR, Quantile Transfer) vượt α ở 3/7 dataset.

**Hạn chế.**

- Power luôn thấp hơn baseline dùng nhãn. Đó là cái giá của tính hợp lệ.
- RobotCar có snippet 9 frame, quá ngắn để tích luỹ bằng chứng (0.68 so với 0.77 của per-frame).
- Bản đồ nhỏ (CMU, khoảng 70 đoạn null) khiến FAR của từng bản đồ dao động.
- Giả định exchangeability chỉ được kiểm bằng thực nghiệm.

## 2. Đóng góp B — Chẩn đoán vì sao HMM thua baseline

**Thiết lập** (`analysis/hmm_diag.py`, 36 cấu hình): HMM chuẩn (lọc tiến, chuyển trạng thái theo odometry, emission
exp(s/T)), có hoặc không có trạng thái off-map của Xu et al. RA-L'21.

| Mã | Phát hiện | Số liệu |
|---|---|---|
| D5 | Posterior **bất biến chính xác** khi cộng một hằng số vào mọi similarity của từng frame | thay đổi ≤ 4·10⁻⁶ |
| D1 | Độ tin cậy của HMM tách on/off kém hơn max-sim thô | R@FL5 0.44 so với 0.55 (CMU 0.43 so với 0.74) |
| D2 | Quá tự tin | conf 0.91 so với acc 0.77, ECE 0.14 |
| D3 | Khoá nhầm chỗ | 16 % frame sai mà vẫn tin > 0.9, gây 41 % tổng sai số |
| D4 | Bằng chứng phụ thuộc | tự tương quan trễ 1 là 0.8–0.99, tức phóng đại (1+r)/(1−r) = 8–136× |

**Nguyên nhân gốc:**

1. **Mù với sự vắng mặt.** Softmax chỉ mang bằng chứng tương đối. Câu hỏi "có trong bản đồ không" lại cần
   LR(j : ∅) = f₁(s_j)/f₀(s_j), tức mức tuyệt đối. Vì vậy (T, k) của Xu'21 tune bằng nhãn trên điều kiện dễ cho FL 0.97
   trên CMU.
2. **Đếm thừa bằng chứng phụ thuộc** (likelihood hợp thành), gây quá tự tin và khoá nhầm.
3. **Vòng khoá nhầm:** bằng chứng tính từ niềm tin của HMM tự xác nhận khi đã khoá nhầm.
4. **Bội số:** p-value của thống kê max đã trả giá cho N nơi, nên không nhân vào từng trạng thái được.

## 3. Đóng góp C — CPC-HMM (module sửa HMM)

**Mô hình** (`analysis/hmm_fix.py`, `fac_anchT_mix`; luật điều hướng trong `nav_demo.py`; lý thuyết trong
`paper/cpc_theory.md`).

- **Chuỗi vị trí:** HMM không có trạng thái off-map, với emission (s − s_max)/(τ·σ_far,t). τ là thang Gumbel của null
  bản đồ, nên không phải tune.
- **Chuỗi hiện diện on/off:**

  > P(on_t) ∝ [(1−p_out)·P(on_{t−1}) + p_in·P(off_{t−1})] · LR_t,  LR_t = ½(ẽ^top_t + (e^R_t)^(1/H))

  - e = a·p^(a−1), với a fit bằng EM theo từng traversal (không nhãn).
  - Cổng: top-1 phải khớp MAP của chuỗi vị trí.
  - e^R là e-value của R_t, hiệu chuẩn trên traversal của bản đồ.
- **Quyết định:** báo nơi MAP khi P(on) > ½.

**Lý thuyết** (`paper/cpc_theory.md`):

- **Bổ đề 1:** e-value có thể dự đoán.
- **Bổ đề 2:** cổng, luỹ thừa và trung bình đều giữ tính e-value.
- **Định lý 1:** odds bị chặn bởi thống kê Shiryaev–Roberts, nên **ARL₀ ≥ (1−p_in)/p_in − R₀**, với điều kiện
  p_out ≥ p_in.
- **Định lý 2:** độ trễ vào lại ≈ log((1−p)/p)/KL₁.

**Kiểm chứng ARL₀** (số frame off-map trên mỗi lần bắt đầu báo sai, trung vị; cận lý thuyết 98):

| | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|
| **CPC-HMM** | 995 | 3930 | 2840 | 762 | 895 |
| Xu'21 (nhãn) | **41** | 720 | 651 | 665 | 1424 |
| CPC, p_in = 0.05 (cận 18) | 337 | 1965 | 1893 | 318 | 832 |

**Kết quả CPC-HMM so với Xu'21** (bản đồ khuyết 30 %; ô ghi recall / FL / sai số điều hướng trung bình):

| Dataset | CPC-HMM (không nhãn) | Xu'21 (T, k tune bằng nhãn) | Kết luận |
|---|---|---|---|
| CMU | 0.77 / 0.034 / 6.8 m | 0.71 / 0.363 / 46.0 m | **thắng** |
| Nordland | 0.71 / 0.008 / 20.1 fr | 0.74 / 0.013 / 54.7 fr | **thắng** |
| 4S office | 0.78 / 0.004 / 10.9 m | 0.77 / 0.041 / 17.7 m | **thắng** |
| 4S old town | 0.64 / 0.040 / 45.6 m | 0.60 / 0.091 / 100.9 m | **thắng** |
| 4S countryside | 0.37 / 0.068 / 56.0 m | 0.28 / 0.029 / 94.4 m | thắng điều hướng, FL cao hơn |
| RobotCar | 0.68 / 0.060 / 2.1 m | 0.58 / 0.045 / 1.3 m | **thua** (snippet 9 frame) |
| Boreas (odometry đã sửa) | sai số điều hướng 21.0 m (4 desc.) | 6.2 m | **thua khoảng 3×** |

**Điều hướng khép kín** (`nav_demo.py`, 3 seed, sai số trung bình):

| | CMU | Nordland | 4S office | 4S old town | 4S countryside | Boreas* |
|---|---|---|---|---|---|---|
| CPC-HMM | 5.7 | 17.9 | 12.8 | 36.0 | 54.0 | 21.0 |
| Certified | 3.8 | 17.0 | 11.3 | 37.0 | 52.8 | 19.4 |
| Xu'21 (nhãn) | 14.2 | 70.7 | 22.7 | 62.4 | 76.8 | **6.2** |
| Per-frame SelfCal | 5.3 | 36.3 | 11.6 | 45.2 | 65.7 | 16.2 |

\*Boreas: MegaLoc, SALAD, MixVPR và CosPlace sau khi sửa odometry. NetVLAD và DINOv2 đang chạy.

**Độ bền theo tỷ lệ lỗ bản đồ** (sai số điều hướng của `hmm_fix`, CPC so với Xu'21):

- **Khuyết 50 %:** CPC thắng ở mọi dataset trừ RobotCar.
  - CMU 28.0 so với 55.0; Nordland 23.8 so với 169; 4S office 26.3 so với 79.1.
  - **Boreas 13.7 so với 40.8**.
- **Khuyết 10 %:** CPC thắng trên CMU, Nordland, 4S office và countryside, nhưng thua trên 4S old town (44.0 so với
  30.1).

**Đóng góp mới so với tài liệu** (Gate 7 trong `LITERATURE_GATE.md`):

- **Mới:**
  - chẩn đoán bất biến dịch chuyển;
  - chuỗi tồn tại kiểu IPDA được nuôi bằng e-value hiệu chuẩn bằng bản đồ;
  - cổng độc lập niềm tin;
  - phép chặn chuỗi on/off của HMM bằng một e-detector.
- **Không mới:** từng khối riêng (IPDA/Bernoulli existence, e-detectors của Shin–Ramdas–Rinaldo, p-to-e calibrator,
  HMM-VPR).
- **Mức hiện tại:** RA-L/ICRA nếu sửa được Boreas. Nên trình bày như module của hướng certified.

## 4. Kết quả tiêu cực và hạn chế (kèm nguyên nhân đã xác minh)

1. **HMM không tăng recall trung bình** trên các benchmark này: CMU 90.7 → 92.5 % R@5 m. Không có chỗ cho một paper
   "HMM tăng độ chính xác".
2. **Calibrate theo cửa sổ thất bại** (Entry 18): cửa sổ trong một block 300 m phụ thuộc nhau, và số mẫu hiệu dụng của
   null quá nhỏ. Đã giải quyết bằng hiệu chuẩn theo đoạn.
3. **Lỗi dữ liệu Boreas:** bộ đếm xung bánh xe đứt ở 4/13 chuyến, tạo một bước nhảy 8.7 km. Lỗi này làm chuỗi vị trí mất
   dấu (đúng 2 % so với top-1 đúng 99 %). Đã sửa trong `odometry_wheel`; mọi kết quả Boreas trước 2026-10-29 14:00 UTC
   không dùng được.
4. **Boreas, sau khi sửa odometry, CPC-HMM vẫn thua Xu'21** về điều hướng: FL 0.07–0.085 so với 0.018. Hai nguyên nhân
   đã đo:
   - **Độ trễ khi rời bản đồ** chiếm phần lớn FL. Chuỗi ở biên trên cần khoảng log((1−p_out)/p_out)/|KL₀| frame để
     xuống "off". Giảm p (tăng ARL₀) làm FL **tăng**.
     - Tách p_in/p_out (p_in = 0.01, p_out = 0.2) cho FL Boreas MegaLoc 0.029 → 0.007, recall 0.983 → 0.956 (offline).
     - Nhưng Nordland và 4S countryside mất nhiều recall (p_out = 0.05: Nordland 0.74 → 0.58).
     - Lưới điều hướng `CPC-HMM p_out=*` đang chạy.
   - **e^R vi phạm D_R:** P(p^R ≤ 0.01 | off) = 0.059 trên 4S countryside, P(p^R ≤ 0.05 | off) = 0.075 trên Boreas
     MegaLoc. Trong khi đó p^top vẫn super-uniform ở mọi dataset.
     - Null dùng odometry không nhiễu (Bổ đề 3, Anderson) **không** sửa được.
     - Nguyên nhân còn lại: aliasing kết hợp, top-1 trượt đều theo odometry trên đoạn đường giống, xảy ra sâu bên trong
       đoạn off-map dài.
5. **Thống kê dùng niềm tin HMM** (`fac_pc`, `fac_mix`): FL 0.08–0.14, do khoá nhầm.
6. **Mô hình hợp nhất trạng thái** (e-value vào từng nơi): đếm 1/N hai lần (`abs_naive`, recall 0.26) hoặc FL ≈ 0.9
   (`abs`).
7. **Giảm theo ESS** cho chuỗi vị trí: hết khoá nhầm nhưng mất khả năng xếp hạng.
8. **CPC-HMM thiếu tự tin** (ECE 0.08–0.28, overconf âm): an toàn nhưng chưa hiệu chuẩn.
9. **Độ trễ vào lại của CPC-HMM** chậm hơn Xu'21 trên Nordland (79 so với 36 frame). Nhanh hơn trên CMU (3 so với 31).

## 5. Điều kiện kiểm chứng (để tái tạo)

- **Bản đồ:** bỏ 30 % block (CFG block 300 m; Nordland theo frame), seed 0–2. Off-map khi khoảng cách tới bản đồ còn
  lại > off_d; on-map khi ≤ in_d; fix đúng khi sai số ≤ excl (25 m) hoặc tol.
- **Điều hướng:** Kalman vị trí (σ fix 5 m), odometry trôi (mô phỏng: 3 % scale, heading random walk 0.3°/bước) hoặc
  thật (4S VIO, Boreas bánh xe + gyro).
- **Baseline Xu'21:** emission exp(s/T), off-map exp(s₍ₖ₎/T), p_out = 0.01, p_in = 0.05; (T, k) ∈ {0.01, 0.02, 0.05} ×
  {5, 10, 20} chọn bằng nhãn trên 2 điều kiện dễ nhất với FL ≤ α.
- **Baseline khác:** per-frame SelfCal (p ≤ α), ngưỡng max-sim hiệu chuẩn bằng nhãn, accept-all, oracle.
