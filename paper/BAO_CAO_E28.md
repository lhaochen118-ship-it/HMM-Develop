# Báo cáo vòng 6: Phẫu thuật bản đồ phản thực (CMS) — tự hiệu chuẩn quyết định định vị trên chính luồng triển khai

*Branch `hmm-navigation-5`, 2026-11-01. Nhật ký `RESEARCH_LOG.md` Entry 28 (đăng ký trước ở đầu entry, đã push trước khi
chạy đánh giá đầy đủ). Lý thuyết `paper/cms_theory.md`; novelty `LITERATURE_GATE.md` Gate 12. Vòng trước:
`paper/BAO_CAO_E27.pdf`.*

**Tóm tắt.** (1) Cơ chế mới: null hiệu chuẩn được **sinh từ chính luồng triển khai** bằng phẫu thuật bản đồ quanh niềm tin của hệ
thống — khớp điều kiện ảnh, nhiễu odometry và phụ thuộc thời gian, không nhãn, hàng trăm đơn vị hoán đổi thay vì ~10.
(2) Định lý 6: tỷ lệ khởi phát sai ≤ α(n+1)/(πn+1); kiểm chứng 7/7 dataset, tỷ lệ thực tế ≈ α (0.48–1.14·α) thay vì ≪ α.
(3) **Đề xuất cuối: CMS-CPC/H+SH ở α = 0.01** (chặt gấp 5 lần luật cũ): recall cao hơn luật tốt nhất cũ CPC-SC-T½+SH (chạy ở
α = 0.05) trên 6/7 dataset, sai số điều hướng thấp hơn 5/7, segFAR trung bình ≤ 0.01 trên 7/7; biến thể +G được LODO chọn ở 7/7 fold.
Xếp hạng (recall tại FL ≤ 0.01) cao hơn luật cũ 5/7, hơn Claxton'24 / TAO'26 (có nhãn) 6/7, SafeVPR'26 5/5. (4) Hạn chế: ở
α = 0.05 sai số điều hướng kém hơn 4/7 (dùng hết ngân sách rủi ro); CMU sát ngưỡng; S1 chỉ đúng trung bình theo bố cục lỗ.

## 1. Vấn đề còn lại và ý tưởng

Mọi luật không nhãn trước đây (certified, CPC-SC, CPC-SC-T) hiệu chuẩn ngưỡng trên **null tự-phát-lại của bản đồ**: frame
bản đồ, che block của chính nó, làm query off-map. Null này khác điều kiện ảnh của query, dùng odometry hoàn hảo, và chỉ có
~10 chunk độc lập. Hệ quả đã đo ở vòng 3–5: tỷ lệ khởi phát sai thực tế 0.001–0.006 ≪ α (ngân sách rủi ro bị bỏ phí), α = 0.01
không khả thi trên CMU và 4S office (κ = ∞), không có bảo đảm có điều kiện theo hiệu chuẩn.

**CMS (Counterfactual Map Surgery).** Null được sinh từ **chính luồng query**: với mỗi frame t, tính lại thống kê bằng chứng
trên bản đồ đã **cắt bỏ hành lang bán kính ρ = off_d quanh niềm tin của chính hệ thống** (các anchor của giả thuyết tuyến
thắng trên N = 20 frame gần nhất). Nếu niềm tin đúng, cả cửa sổ nằm ở biên off-map (≈ off_d tới bản đồ còn lại): thống kê phản thực là một mẫu
**off-map ở biên** (khó nhất) với đúng điều kiện ảnh, nhiễu odometry và phụ thuộc thời gian của query. Nếu niềm tin sai, nơi thật còn
nguyên (phía bảo thủ). Ngưỡng = phân vị conformal của luồng phản thực theo đoạn H frame, theo từng điều kiện (Mondrian;
điều kiện có < 2/α đoạn được gộp). Không nhãn, không traversal hiệu chuẩn, không mô hình tham số.

## 2. Phương pháp và công thức

Thống kê (tính **y hệt** trên bản đồ thật và bản đồ đã phẫu thuật, chỉ từ danh sách top-100 mỗi frame):

- **Chi phí tuyến** C_t (TAO'26): với mỗi giả thuyết j trong top-K, truy ngược anchor trên tuyến bản đồ theo quãng odometry
  của N = 20 frame, khớp cứng 2-D; C_t(j) = trung bình cắt 75 % của Huber₈(phần dư)/8² + 2 · trung bình(1 − s_i(j)); C_t = min_j.
  Phẫu thuật: bỏ giả thuyết trong hành lang B_t, tra cứu ngoại hình bị che rơi về similarity thứ K, vệt anchor đi vào B_t
  rời chunk tuyến từ đó (như lỗ thật).
- **Độ khác biệt** z_t = (s₁ − s_far)/std_t, s_far = entry tốt nhất cách top-1 > excl.
- **p-value phản thực:** p_t = (1 + #{t' cùng điều kiện : T^cf_{t'} ≥ T_t}) / (1 + n) (với C: ≤); e_t = a · p_t^(a−1), a = Beta-EM.

Luật (mọi hằng số theo đơn vị bài toán; một cấu hình cho mọi dataset/descriptor):

- **CMS-T:** báo khi C_t < κ_T, κ_T = phần tử nhỏ thứ ⌊α(n+1)⌋ của min C^cf trên các đoạn H frame phản thực (bộ nhớ hữu hạn,
  không trễ: Định lý 6 áp dụng trực tiếp, mọi phụ thuộc giữa các đoạn).
- **CMS-CPC/H+SH (đề xuất chính, đăng ký trước):** chuỗi hiện diện P(on_t) ∝ [(1−p)P(on_{t−1}) + p P(off_{t−1})] · LR_t,
  p = 0.01, LR_t = ½(e^z_t + (e^C_t)^{1/2}); khởi phát khi log-odds > κ (phân vị conformal (1 − α) của max log-odds khởi động
  lại trên các đoạn phản thực, chuỗi phản thực dùng hạng leave-one-out), duy trì khi log-odds > 0; vị trí báo = MAP của chuỗi
  vị trí HMM; dừng hình dạng SH (phần dư Procrustes của quỹ đạo MAP so với odometry trên 3·excl > excl/2).
- **CMS-U/H+SH:** hợp CMS-T và khởi phát CMS-CPC, mỗi cái ở α/2. **-PAC:** ngưỡng có điều kiện theo hiệu chuẩn (δ = 0.1).

## 3. Bảo đảm (chi tiết và chứng minh: `paper/cms_theory.md`)

- **Định lý 6 (hợp lệ dưới tự-nhiễm).** Dưới S1 (bất biến phẫu thuật), S2 (bằng chứng giảm theo khoảng cách tới bản đồ),
  S3 (hoán đổi theo đoạn **trong cùng luồng**): P(khởi phát sai trong một đoạn off-map) ≤ α(n + 1)/(πn + 1) ≈ α/π, π = tỷ lệ
  đoạn phản thực có niềm tin đúng; mọi phụ thuộc trong đoạn và giữa các đoạn.
- **Mệnh đề 8 (hướng của nhiễm).** Niềm tin sai → bảo thủ; frame off-map → trả bằng hệ số 1/π; chồng lấn tầm nhìn → không
  thiên lệch.
- **Hệ quả 9.** α = 0.01 khả thi ở mọi dataset (hàng trăm đoạn mỗi điều kiện thay vì ~10); bảo đảm PAC
  P(tỷ lệ > α/π | hiệu chuẩn) ≤ δ.
- Dừng SH chỉ bỏ báo cáo (Bổ đề 7), cắt chuỗi báo ở mép bản đồ (Mệnh đề 4, Định lý 5).

## 3b. Tối ưu tính toán

- Thống kê CMS chỉ cần top-100 (`hmm-topk`): phẫu thuật = che chỉ số, không cần descriptor hay GPU. Tính thật và phản thực
  trong **một lượt** (các giả thuyết, anchor, Procrustes dùng chung; chỉ phần tra cứu ngoại hình chạy lại có mặt nạ).
- 366 run chia **cân bằng tải theo số frame** (LPT) thành 50 kernel CPU (10 acc × 5 phiên, lấp đầy từng acc trước khi sang
  acc kế), 3 tiến trình/kernel, ~25 phút cho mỗi bán kính ρ; kết quả công khai `nhatlong1103/hmm-cms-cache` (ρ = off_d) và
  `hmm-cms-cache-r1`. Đánh giá (64 họ luật, đường cong seed 0–2 + điểm mặc định 10 seed, 2 mức α, 2 bán kính, chuyển đạo và nhân quả)
  chạy trên 8 phiên L4×4 dùng như máy 48 lõi (40 job song song/phiên): ~12 phút; độ bền lỗ 10/50 % (top-100 trên GPU + CMS + đánh giá,
  216 job) trên 12 phiên L4. Chi phí tuyến thật dùng lại `hmm-route-cache`. Một lô dự phòng 25 kernel CPU được huỷ khi L4 xong trước.

## 4. Kết quả

### Bảng 1. Điểm mặc định, α = 0.05: recall / segFAR trung bình / segFAR run tệ nhất / sai số điều hướng (m); 10 seed (NCLT 1), 6 descriptor

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.684 / 0.043 / 0.567 / 25.3 | 0.526 / 0.021 / 0.065 / 13.7 | 0.686 / 0.227 / 1.000 / 18.1 | 0.740 / 0.038 / 0.113 / 59.3 | 0.724 / 0.215 / 0.997 / 21.2 | 0.625 / 0.101 / 1.000 / 70.9 | 0.254 / 0.088 / 0.983 / 81.0 |
| Claxton'24 (nhãn) | 0.741 / 0.116 / 0.619 / 37.3 | 0.663 / 0.213 / 0.425 / 33.2 | 0.874 / 0.166 / 0.809 / 14.4 | 0.522 / 0.267 / 0.447 / 88.9 | 0.798 / 0.152 / 0.589 / 18.7 | 0.724 / 0.166 / 0.544 / 90.3 | 0.597 / 0.213 / 0.498 / 42.9 |
| SafeVPR'26 (nhãn) | – | 0.324 / 0.038 / 0.225 / 14.7 | – | – | 0.711 / 0.037 / 0.221 / 11.6 | 0.668 / 0.033 / 0.158 / 32.6 | 0.105 / 0.005 / 0.056 / 75.2 |
| TAO'26 (nhãn) | 0.801 / 0.240 / 0.830 / 46.2 | 0.756 / 0.707 / 1.000 / 57.6 | 0.930 / 0.370 / 1.000 / 38.4 | 0.805 / 0.579 / 1.000 / 187.9 | 0.935 / 0.740 / 1.000 / 54.0 | 0.839 / 0.557 / 1.000 / 168.4 | 0.769 / 0.732 / 1.000 / 95.1 |
| Certified (null bản đồ) | 0.651 / 0.022 / 0.109 / 8.5 | 0.476 / 0.001 / 0.003 / 3.7 | 0.692 / 0.025 / 0.232 / 4.2 | 0.576 / 0.025 / 0.099 / 12.7 | 0.661 / 0.016 / 0.132 / 11.2 | 0.540 / 0.015 / 0.086 / 33.1 | 0.203 / 0.013 / 0.122 / 52.5 |
| TAO-SC (null bản đồ) | 0.584 / 0.011 / 0.107 / 10.1 | 0.400 / 0.000 / 0.000 / 11.4 | 0.659 / 0.066 / 0.764 / 7.1 | 0.348 / 0.012 / 0.056 / 63.8 | 0.630 / 0.011 / 0.081 / 18.7 | 0.547 / 0.008 / 0.098 / 37.5 | 0.048 / 0.003 / 0.200 / 102.3 |
| CPC-SC+CS (vòng 3) | 0.661 / 0.001 / 0.021 / 5.1 | 0.537 / 0.000 / 0.000 / 4.6 | 0.731 / 0.002 / 0.019 / 3.8 | 0.644 / 0.000 / 0.003 / 9.6 | 0.709 / 0.000 / 0.000 / 11.6 | 0.600 / 0.000 / 0.010 / 30.8 | 0.297 / 0.000 / 0.007 / 53.1 |
| CPC-SC-T½+SH (vòng 5, tốt nhất cũ) | 0.666 / 0.002 / 0.023 / 5.7 | 0.588 / 0.001 / 0.003 / 4.9 | 0.789 / 0.018 / 0.188 / 5.2 | 0.713 / 0.001 / 0.010 / 9.5 | 0.738 / 0.000 / 0.003 / 11.4 | 0.640 / 0.007 / 0.034 / 29.8 | 0.334 / 0.000 / 0.015 / 51.3 |
| CMS-T (tuyến, winner TAO) | 0.735 / 0.036 / 0.178 / 29.6 | 0.574 / 0.048 / 0.183 / 26.2 | 0.782 / 0.055 / 0.343 / 7.2 | 0.484 / 0.024 / 0.082 / 61.7 | 0.819 / 0.044 / 0.118 / 14.2 | 0.708 / 0.040 / 0.111 / 70.8 | 0.284 / 0.044 / 0.179 / 71.7 |
| CMS-T/ H (tuyến, vị trí HMM) | 0.735 / 0.036 / 0.178 / 30.0 | 0.577 / 0.048 / 0.183 / 25.7 | 0.783 / 0.055 / 0.343 / 6.9 | 0.501 / 0.024 / 0.082 / 50.4 | 0.819 / 0.044 / 0.118 / 13.2 | 0.706 / 0.040 / 0.111 / 76.2 | 0.292 / 0.044 / 0.179 / 66.6 |
| CMS-T/ H+SH | 0.683 / 0.000 / 0.003 / 8.1 | 0.531 / 0.010 / 0.059 / 10.9 | 0.732 / 0.010 / 0.079 / 4.9 | 0.485 / 0.003 / 0.022 / 14.2 | 0.747 / 0.001 / 0.018 / 10.4 | 0.634 / 0.003 / 0.023 / 29.6 | 0.255 / 0.001 / 0.013 / 47.1 |
| CMS-W/ H+SH (chuỗi bộ nhớ hữu hạn) | 0.707 / 0.003 / 0.022 / 8.1 | 0.550 / 0.004 / 0.026 / 5.4 | 0.779 / 0.010 / 0.058 / 4.9 | 0.553 / 0.002 / 0.012 / 10.1 | 0.759 / 0.001 / 0.009 / 10.1 | 0.657 / 0.004 / 0.034 / 28.0 | 0.317 / 0.001 / 0.010 / 40.8 |
| **CMS-CPC/ H+SH (đề xuất, đăng ký trước)** | 0.780 / 0.006 / 0.030 / 11.2 | 0.629 / 0.013 / 0.062 / 8.4 | 0.834 / 0.019 / 0.075 / 7.2 | 0.798 / 0.009 / 0.046 / 12.8 | 0.804 / 0.002 / 0.018 / 9.8 | 0.718 / 0.011 / 0.062 / 27.6 | 0.523 / 0.003 / 0.026 / 34.1 |
| **CMS-CPC/ H+SH+G (chọn bởi LODO)** | 0.775 / 0.005 / 0.030 / 11.3 | 0.614 / 0.008 / 0.046 / 6.7 | 0.823 / 0.018 / 0.071 / 6.7 | 0.766 / 0.003 / 0.020 / 7.3 | 0.800 / 0.002 / 0.018 / 9.9 | 0.713 / 0.008 / 0.062 / 26.8 | 0.504 / 0.002 / 0.026 / 33.7 |
| CMS-U/ H+SH (hợp, α/2 mỗi nhánh) | 0.771 / 0.005 / 0.029 / 11.1 | 0.622 / 0.015 / 0.075 / 7.9 | 0.831 / 0.017 / 0.081 / 6.3 | 0.783 / 0.007 / 0.038 / 12.1 | 0.803 / 0.002 / 0.018 / 9.8 | 0.713 / 0.010 / 0.051 / 27.6 | 0.507 / 0.003 / 0.024 / 35.2 |
| CMS-CPC/ H+SH [nhân quả: chỉ phiên khác] | 0.768 / 0.007 / 0.034 / 9.7 | 0.625 / 0.011 / 0.056 / 8.5 | 0.830 / 0.017 / 0.070 / 7.0 | 0.781 / 0.018 / 0.085 / 18.7 | 0.781 / 0.001 / 0.024 / 10.0 | 0.715 / 0.012 / 0.062 / 29.6 | 0.514 / 0.006 / 0.040 / 36.8 |
| CMS-CPC/ H+SH {ρ = off_d + excl, đăng ký trước} | 0.783 / 0.007 / 0.031 / 12.0 | 0.635 / 0.016 / 0.062 / 9.1 | 0.841 / 0.025 / 0.091 / 8.8 | 0.799 / 0.009 / 0.046 / 12.9 | 0.808 / 0.002 / 0.027 / 9.8 | 0.722 / 0.014 / 0.062 / 28.3 | 0.547 / 0.004 / 0.030 / 32.5 |
| CMS-F-PAC (δ = 0.1) | 0.744 / 0.038 / 0.137 / 24.3 | 0.567 / 0.014 / 0.065 / 13.8 | 0.805 / 0.035 / 0.145 / 5.4 | 0.499 / 0.017 / 0.047 / 28.8 | 0.816 / 0.041 / 0.118 / 14.0 | 0.696 / 0.038 / 0.091 / 63.7 | 0.352 / 0.044 / 0.169 / 63.1 |
| CMS-CPC không dừng (chẩn đoán) | 0.852 / 0.118 / 0.296 / 51.6 | 0.689 / 0.075 / 0.245 / 25.0 | 0.900 / 0.128 / 0.453 / 13.2 | 0.808 / 0.083 / 0.244 / 94.1 | 0.905 / 0.139 / 0.324 / 27.2 | 0.821 / 0.137 / 0.310 / 103.2 | 0.604 / 0.196 / 0.444 / 67.8 |
| Oracle | 0.88 / – / – / 2.1 | 0.72 / – / – / 2.2 | 0.94 / – / – / 3.0 | 0.67 / – / – / 4.8 | 0.91 / – / – / 8.3 | 0.84 / – / – / 19.4 | 0.73 / – / – / 16.5 |

### Bảng 2. Điểm mặc định, α = 0.01 (cùng định dạng)

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| CPC-SC+CS, α = 0.01 (null bản đồ) | 0.644 / 0.001 / 0.011 / 5.1 | 0.488 / 0.000 / 0.000 / 4.1 | 0.000 / 0.000 / 0.000 / 4.0 | 0.630 / 0.000 / 0.003 / 9.7 | 0.000 / 0.000 / 0.000 / 37.4 | 0.180 / 0.000 / 0.000 / 78.4 | 0.204 / 0.000 / 0.000 / 67.0 |
| CMS-T (tuyến, winner TAO) | 0.673 / 0.008 / 0.081 / 17.0 | 0.499 / 0.011 / 0.052 / 20.4 | 0.660 / 0.015 / 0.095 / 4.2 | 0.104 / 0.005 / 0.026 / 78.9 | 0.763 / 0.012 / 0.033 / 12.0 | 0.606 / 0.010 / 0.050 / 59.9 | 0.155 / 0.016 / 0.097 / 89.9 |
| CMS-T/ H (tuyến, vị trí HMM) | 0.673 / 0.008 / 0.081 / 16.6 | 0.500 / 0.011 / 0.052 / 21.9 | 0.660 / 0.015 / 0.095 / 4.0 | 0.112 / 0.005 / 0.026 / 72.6 | 0.763 / 0.012 / 0.033 / 11.1 | 0.605 / 0.010 / 0.050 / 62.6 | 0.158 / 0.016 / 0.097 / 87.3 |
| CMS-T/ H+SH | 0.632 / 0.000 / 0.001 / 4.3 | 0.471 / 0.004 / 0.026 / 11.1 | 0.624 / 0.002 / 0.022 / 3.7 | 0.109 / 0.001 / 0.009 / 33.9 | 0.706 / 0.000 / 0.005 / 10.9 | 0.555 / 0.002 / 0.023 / 32.1 | 0.142 / 0.001 / 0.010 / 63.1 |
| CMS-W/ H+SH (chuỗi bộ nhớ hữu hạn) | 0.577 / 0.000 / 0.009 / 4.2 | 0.370 / 0.000 / 0.000 / 4.9 | 0.660 / 0.002 / 0.022 / 3.6 | 0.115 / 0.000 / 0.003 / 18.5 | 0.393 / 0.000 / 0.003 / 14.6 | 0.441 / 0.001 / 0.017 / 32.6 | 0.127 / 0.000 / 0.010 / 66.2 |
| **CMS-CPC/ H+SH (đề xuất, đăng ký trước)** | 0.750 / 0.002 / 0.020 / 6.9 | 0.595 / 0.002 / 0.007 / 4.7 | 0.795 / 0.010 / 0.046 / 4.3 | 0.723 / 0.005 / 0.038 / 10.3 | 0.734 / 0.000 / 0.007 / 10.5 | 0.700 / 0.008 / 0.051 / 28.1 | 0.410 / 0.001 / 0.012 / 44.7 |
| **CMS-CPC/ H+SH+G (chọn bởi LODO)** | 0.747 / 0.002 / 0.020 / 5.7 | 0.582 / 0.001 / 0.003 / 4.6 | 0.787 / 0.010 / 0.046 / 4.1 | 0.696 / 0.002 / 0.015 / 7.5 | 0.730 / 0.000 / 0.004 / 10.6 | 0.695 / 0.006 / 0.051 / 27.5 | 0.397 / 0.001 / 0.010 / 44.0 |
| CMS-U/ H+SH (hợp, α/2 mỗi nhánh) | 0.740 / 0.001 / 0.011 / 4.7 | 0.587 / 0.007 / 0.033 / 9.5 | 0.792 / 0.010 / 0.058 / 4.3 | 0.656 / 0.004 / 0.018 / 15.0 | 0.731 / 0.000 / 0.007 / 11.1 | 0.672 / 0.008 / 0.051 / 28.9 | 0.375 / 0.002 / 0.012 / 55.0 |
| CMS-CPC/ H+SH [nhân quả: chỉ phiên khác] | 0.729 / 0.003 / 0.021 / 7.3 | 0.590 / 0.004 / 0.020 / 5.6 | 0.797 / 0.010 / 0.051 / 4.5 | 0.685 / 0.005 / 0.031 / 14.0 | 0.760 / 0.001 / 0.011 / 10.4 | 0.695 / 0.009 / 0.051 / 27.3 | 0.425 / 0.003 / 0.040 / 55.2 |
| CMS-CPC/ H+SH {ρ = off_d + excl, đăng ký trước} | 0.754 / 0.003 / 0.021 / 7.5 | 0.609 / 0.004 / 0.016 / 5.0 | 0.805 / 0.013 / 0.052 / 5.0 | 0.729 / 0.004 / 0.038 / 10.4 | 0.739 / 0.000 / 0.007 / 10.4 | 0.709 / 0.010 / 0.051 / 27.5 | 0.475 / 0.002 / 0.023 / 43.1 |
| CMS-F-PAC (δ = 0.1) | 0.667 / 0.005 / 0.050 / 8.0 | 0.413 / 0.003 / 0.020 / 9.5 | 0.668 / 0.008 / 0.058 / 3.7 | 0.179 / 0.003 / 0.013 / 26.3 | 0.706 / 0.007 / 0.036 / 11.0 | 0.549 / 0.006 / 0.029 / 48.5 | 0.152 / 0.009 / 0.043 / 70.8 |
| CMS-CPC không dừng (chẩn đoán) | 0.811 / 0.057 / 0.130 / 35.3 | 0.636 / 0.031 / 0.062 / 19.5 | 0.853 / 0.072 / 0.347 / 6.6 | 0.730 / 0.054 / 0.210 / 69.8 | 0.817 / 0.084 / 0.267 / 24.0 | 0.784 / 0.083 / 0.170 / 89.6 | 0.452 / 0.109 / 0.317 / 83.7 |
| Oracle | 0.88 / – / – / 2.1 | 0.72 / – / – / 2.2 | 0.94 / – / – / 3.0 | 0.67 / – / – / 4.8 | 0.91 / – / – / 8.3 | 0.84 / – / – / 19.4 | 0.73 / – / – / 16.5 |

### Bảng 3. Đường cong vận hành: recall tại FL ≤ 0.01 / pAUC (FL ∈ [0, 0.05]); seed 0–2

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.562 / 0.602 | 0.526 / 0.563 | 0.592 / 0.638 | 0.624 / 0.688 | 0.537 / 0.599 | 0.555 / 0.615 | 0.181 / 0.237 |
| Claxton'24 (nhãn) | 0.686 / 0.705 | 0.571 / 0.592 | 0.791 / 0.812 | 0.438 / 0.466 | 0.749 / 0.765 | 0.645 / 0.672 | 0.423 / 0.472 |
| SafeVPR'26 (nhãn) | 0.486 / 0.551 | 0.397 / 0.444 | – | – | 0.757 / 0.786 | 0.698 / 0.733 | 0.252 / 0.329 |
| TAO'26 (nhãn) | 0.640 / 0.659 | 0.520 / 0.543 | 0.792 / 0.806 | 0.418 / 0.493 | 0.683 / 0.705 | 0.631 / 0.654 | 0.239 / 0.296 |
| Certified (null bản đồ) | 0.674 / 0.685 | 0.588 / 0.608 | 0.729 / 0.750 | 0.573 / 0.579 | 0.731 / 0.752 | 0.595 / 0.628 | 0.262 / 0.294 |
| TAO-SC (null bản đồ) | 0.641 / 0.659 | 0.520 / 0.543 | 0.791 / 0.805 | 0.418 / 0.493 | 0.683 / 0.705 | 0.632 / 0.655 | 0.239 / 0.296 |
| CPC-SC+CS (vòng 3) | 0.766 / 0.777 | 0.586 / 0.588 | 0.705 / 0.724 | 0.780 / 0.787 | 0.771 / 0.771 | 0.664 / 0.657 | 0.545 / 0.543 |
| CPC-SC-T½+SH (vòng 5, tốt nhất cũ) | 0.770 / 0.780 | 0.612 / 0.624 | 0.744 / 0.759 | 0.794 / 0.814 | 0.812 / 0.810 | 0.680 / 0.693 | 0.528 / 0.571 |
| CMS-T (tuyến, winner TAO) | 0.694 / 0.720 | 0.530 / 0.559 | 0.782 / 0.796 | 0.445 / 0.543 | 0.774 / 0.801 | 0.662 / 0.688 | 0.257 / 0.312 |
| CMS-T/ H (tuyến, vị trí HMM) | 0.694 / 0.720 | 0.533 / 0.562 | 0.786 / 0.800 | 0.458 / 0.558 | 0.774 / 0.801 | 0.661 / 0.687 | 0.266 / 0.324 |
| CMS-T/ H+SH | 0.766 / 0.788 | 0.568 / 0.586 | 0.736 / 0.750 | 0.755 / 0.777 | 0.814 / 0.811 | 0.701 / 0.706 | 0.565 / 0.592 |
| CMS-W/ H+SH (chuỗi bộ nhớ hữu hạn) | 0.790 / 0.802 | 0.597 / 0.621 | 0.770 / 0.778 | 0.783 / 0.806 | 0.815 / 0.812 | 0.707 / 0.709 | 0.606 / 0.613 |
| **CMS-CPC/ H+SH (đề xuất, đăng ký trước)** | 0.796 / 0.806 | 0.592 / 0.624 | 0.778 / 0.785 | 0.790 / 0.813 | 0.815 / 0.812 | 0.714 / 0.712 | 0.616 / 0.618 |
| **CMS-CPC/ H+SH+G (chọn bởi LODO)** | 0.800 / 0.800 | 0.598 / 0.618 | 0.765 / 0.770 | 0.792 / 0.789 | 0.805 / 0.803 | 0.709 / 0.706 | 0.589 / 0.585 |
| CMS-U/ H+SH (hợp, α/2 mỗi nhánh) | 0.771 / 0.792 | 0.592 / 0.605 | 0.753 / 0.761 | 0.757 / 0.781 | 0.814 / 0.812 | 0.706 / 0.707 | 0.592 / 0.607 |
| CMS-F-PAC (δ = 0.1) | 0.736 / 0.759 | 0.582 / 0.608 | 0.797 / 0.815 | 0.551 / 0.595 | 0.789 / 0.804 | 0.671 / 0.699 | 0.307 / 0.383 |
| CMS-CPC không dừng (chẩn đoán) | 0.723 / 0.757 | 0.594 / 0.623 | 0.756 / 0.788 | 0.622 / 0.672 | 0.759 / 0.789 | 0.574 / 0.658 | 0.276 / 0.358 |
| **CMS-CPC/ H+SH, α = 0.01** | 0.799 / 0.805 | 0.597 / 0.625 | 0.775 / 0.784 | 0.785 / 0.810 | 0.813 / 0.810 | 0.713 / 0.710 | 0.615 / 0.618 |
| **CMS-CPC/ H+SH+G, α = 0.01** | 0.801 / 0.797 | 0.603 / 0.620 | 0.763 / 0.769 | 0.792 / 0.787 | 0.801 / 0.798 | 0.709 / 0.705 | 0.589 / 0.585 |

### Bảng 4. Cùng một điểm số (chi phí tuyến TAO'26), ba cách đặt ngưỡng: recall / segFAR / run tệ nhất / sai số

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| ngưỡng nhãn 3σ (TAO'26) | 0.801 / 0.240 / 0.830 / 46.2 | 0.756 / 0.707 / 1.000 / 57.6 | 0.930 / 0.370 / 1.000 / 38.4 | 0.805 / 0.579 / 1.000 / 187.9 | 0.935 / 0.740 / 1.000 / 54.0 | 0.839 / 0.557 / 1.000 / 168.4 | 0.769 / 0.732 / 1.000 / 95.1 |
| null bản đồ (TAO-SC) | 0.584 / 0.011 / 0.107 / 10.1 | 0.400 / 0.000 / 0.000 / 11.4 | 0.659 / 0.066 / 0.764 / 7.1 | 0.348 / 0.012 / 0.056 / 63.8 | 0.630 / 0.011 / 0.081 / 18.7 | 0.547 / 0.008 / 0.098 / 37.5 | 0.048 / 0.003 / 0.200 / 102.3 |
| null phản thực (CMS-T), α = 0.05 | 0.735 / 0.036 / 0.178 / 29.6 | 0.574 / 0.048 / 0.183 / 26.2 | 0.782 / 0.055 / 0.343 / 7.2 | 0.484 / 0.024 / 0.082 / 61.7 | 0.819 / 0.044 / 0.118 / 14.2 | 0.708 / 0.040 / 0.111 / 70.8 | 0.284 / 0.044 / 0.179 / 71.7 |
| null phản thực (CMS-T), α = 0.01 | 0.673 / 0.008 / 0.081 / 17.0 | 0.499 / 0.011 / 0.052 / 20.4 | 0.660 / 0.015 / 0.095 / 4.2 | 0.104 / 0.005 / 0.026 / 78.9 | 0.763 / 0.012 / 0.033 / 12.0 | 0.606 / 0.010 / 0.050 / 59.9 | 0.155 / 0.016 / 0.097 / 89.9 |

### Bảng 5. Độ chặt của bảo đảm: tỷ lệ khởi phát sai mỗi đoạn off-map / α và segFAR / α (1 = dùng đúng ngân sách)

| Luật | α | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|---|
| CPC-SC+CS | 0.05 | 0.02 / 0.03 | 0.06 / 0.00 | 0.06 / 0.04 | 0.05 / 0.00 | 0.08 / 0.00 | 0.09 / 0.01 | 0.08 / 0.00 |
| CPC-SC-T½+SH | 0.05 | 0.03 / 0.04 | 0.06 / 0.01 | 0.22 / 0.35 | 0.05 / 0.01 | 0.08 / 0.00 | 0.10 / 0.14 | 0.09 / 0.01 |
| TAO-SC | 0.05 | 0.10 / 0.23 | 0.06 / 0.00 | 0.31 / 1.32 | 0.17 / 0.24 | 0.11 / 0.21 | 0.11 / 0.16 | 0.09 / 0.07 |
| CMS-T | 0.05 | 0.32 / 0.71 | 0.53 / 0.96 | 0.38 / 1.09 | 0.27 / 0.48 | 0.38 / 0.87 | 0.41 / 0.79 | 0.23 / 0.88 |
| CMS-CPC/H+SH | 0.05 | 0.07 / 0.12 | 0.20 / 0.26 | 0.24 / 0.37 | 0.14 / 0.17 | 0.10 / 0.04 | 0.13 / 0.21 | 0.11 / 0.07 |
| CMS-T | 0.01 | 0.40 / 0.79 | 0.82 / 1.09 | 0.74 / 1.50 | 0.36 / 0.50 | 0.60 / 1.18 | 0.71 / 0.96 | 0.70 / 1.55 |
| CMS-CPC/H+SH | 0.01 | 0.14 / 0.21 | 0.36 / 0.22 | 0.59 / 0.97 | 0.46 / 0.46 | 0.40 / 0.05 | 0.56 / 0.85 | 0.46 / 0.14 |
| CMS-CPC/H+SH+G | 0.01 | 0.14 / 0.18 | 0.31 / 0.11 | 0.60 / 0.95 | 0.40 / 0.19 | 0.38 / 0.02 | 0.55 / 0.60 | 0.44 / 0.08 |

### Bảng 6. Số dataset (trên 7) mà luật đề xuất hơn CPC-SC-T½+SH

| So sánh | recall mặc định cao hơn | sai số thấp hơn | recall tại FL ≤ 0.01 cao hơn |
|---|---|---|---|
| CMS-CPC/H+SH α = 0.05 | 7 | 3 | 5 |
| CMS-CPC/H+SH+G α = 0.05 | 7 | 4 | 4 |
| CMS-CPC/H+SH α = 0.01 | 6 | 5 | 5 |
| CMS-CPC/H+SH+G α = 0.01 | 3 | 6 | 4 |
| CMS-T α = 0.01 | 2 | 1 | 1 |

### Bảng 7a. Chọn luật leave-one-dataset-out (α = 0.05, tiêu chí đăng ký trước)

| held-out | chosen on the others | held-out err | recall | segFAR | best label-free on held-out | regret (m) |
|---|---|---|---|---|---|---|
| 4s:countryside | CPC-SC-T0.5+CS | 52.9 | 0.320 | 0.000 | CMS-CPC/H+SH+G (33.7) | 19.2 |
| 4s:office_loop | CPC-SC-T0.5+CS | 11.7 | 0.718 | 0.000 | CMS-U/H+SH (9.8) | 2.0 |
| 4s:old_town | CPC-SC-T0.5+CS | 30.5 | 0.613 | 0.001 | CMS-CPC/H+SH+G (26.8) | 3.6 |
| boreas | CPC-SC-T0.5+CS | 5.1 | 0.662 | 0.001 | CMS-F+SH (4.5) | 0.6 |
| cmu | CPC-SC-T0.5+CS | 4.3 | 0.762 | 0.004 | CPC-SC+CS (3.8) | 0.5 |
| nclt | CMS-F+SH | 7.8 | 0.512 | 0.004 | certified (3.7) | 4.1 |
| nord | CPC-SC+CS | 9.6 | 0.644 | 0.000 | CMS-CPC/H+SH+G (7.3) | 2.3 |


### Bảng 7b. Chọn luật leave-one-dataset-out (α = 0.01)

| held-out | chosen on the others | held-out err | recall | segFAR | best label-free on held-out | regret (m) |
|---|---|---|---|---|---|---|
| 4s:countryside | CMS-CPC/H+SH+G(a=0.01) | 44.0 | 0.397 | 0.001 | CMS-CPC/H+SH+G(a=0.01) (44.0) | 0.0 |
| 4s:office_loop | CMS-CPC/H+SH+G(a=0.01) | 10.6 | 0.730 | 0.000 | CMS-CPC/H+SH(a=0.01) (10.5) | 0.1 |
| 4s:old_town | CMS-CPC/H+SH+G(a=0.01) | 27.5 | 0.695 | 0.006 | CMS-CPC/H+SH+G(a=0.01) (27.5) | 0.0 |
| boreas | CMS-CPC/H+SH+G(a=0.01) | 5.7 | 0.747 | 0.002 | CMS-F+SH(a=0.01) (4.0) | 1.8 |
| cmu | CMS-CPC/H+SH+G(a=0.01) | 4.1 | 0.787 | 0.010 | CMS-F+SH(a=0.01) (3.5) | 0.6 |
| nclt | CMS-CPC/H+SH+G(a=0.01) | 4.6 | 0.582 | 0.001 | CPC-SC+CS(alpha=0.01) (4.1) | 0.5 |
| nord | CMS-CPC/H+SH+G(a=0.01) | 7.5 | 0.696 | 0.002 | CMS-CPC/H+SH+G(a=0.01) (7.5) | 0.0 |


### Bảng 9a. Bản đồ khuyết 10 % (cùng mọi hằng số), 3 seed × 6 descriptor: recall / segFAR / run tệ nhất / sai số

| Luật | Boreas | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.769 / 0.076 / 0.894 / 19.9 | 0.705 / 0.047 / 0.160 / 5.6 | 0.746 / 0.027 / 0.093 / 29.3 | 0.728 / 0.145 / 0.958 / 12.4 | 0.647 / 0.072 / 0.649 / 37.5 | 0.278 / 0.093 / 0.976 / 60.1 |
| Claxton'24 (nhãn) | 0.787 / 0.218 / 0.956 / 33.8 | 0.892 / 0.266 / 0.752 / 10.5 | 0.553 / 0.517 / 0.719 / 66.7 | 0.813 / 0.211 / 0.679 / 17.4 | 0.754 / 0.257 / 0.680 / 85.2 | 0.624 / 0.260 / 0.380 / 37.6 |
| TAO'26 (nhãn) | 0.783 / 0.286 / 0.812 / 20.4 | 0.926 / 0.433 / 1.000 / 16.5 | 0.808 / 0.639 / 1.000 / 71.0 | 0.934 / 0.709 / 1.000 / 31.6 | 0.840 / 0.536 / 1.000 / 115.5 | 0.781 / 0.771 / 1.000 / 69.0 |
| CPC-SC+CS (null bản đồ) | 0.689 / 0.000 / 0.000 / 4.4 | 0.758 / 0.001 / 0.006 / 3.0 | 0.647 / 0.000 / 0.000 / 10.7 | 0.719 / 0.000 / 0.000 / 9.5 | 0.639 / 0.000 / 0.000 / 26.0 | 0.305 / 0.000 / 0.000 / 50.4 |
| CMS-T/ H+SH | 0.713 / 0.000 / 0.005 / 7.6 | 0.753 / 0.025 / 0.073 / 4.7 | 0.399 / 0.001 / 0.009 / 9.3 | 0.754 / 0.000 / 0.000 / 8.2 | 0.657 / 0.002 / 0.009 / 23.7 | 0.254 / 0.001 / 0.015 / 52.7 |
| CMS-W/ H+SH | 0.739 / 0.000 / 0.005 / 7.0 | 0.802 / 0.021 / 0.079 / 4.1 | 0.509 / 0.000 / 0.000 / 7.0 | 0.773 / 0.001 / 0.007 / 7.9 | 0.680 / 0.001 / 0.018 / 22.3 | 0.331 / 0.002 / 0.023 / 40.6 |
| CMS-CPC/ H+SH | 0.817 / 0.001 / 0.007 / 8.7 | 0.848 / 0.031 / 0.097 / 5.1 | 0.811 / 0.002 / 0.019 / 4.5 | 0.816 / 0.003 / 0.028 / 7.4 | 0.747 / 0.006 / 0.035 / 22.5 | 0.552 / 0.003 / 0.035 / 27.5 |
| CMS-T/ H+SH, α = 0.01 | 0.658 / 0.000 / 0.000 / 3.3 | 0.665 / 0.013 / 0.048 / 3.8 | 0.063 / 0.000 / 0.000 / 28.6 | 0.716 / 0.000 / 0.000 / 9.0 | 0.582 / 0.001 / 0.009 / 26.7 | 0.142 / 0.001 / 0.012 / 63.5 |
| CMS-CPC/ H+SH, α = 0.01 | 0.783 / 0.000 / 0.002 / 5.1 | 0.814 / 0.017 / 0.097 / 3.9 | 0.751 / 0.001 / 0.009 / 6.0 | 0.805 / 0.000 / 0.007 / 7.5 | 0.726 / 0.005 / 0.018 / 24.1 | 0.420 / 0.002 / 0.023 / 40.4 |
| Oracle | 0.88 / – / – / 1.8 | 0.94 / – / – / 2.7 | 0.66 / – / – / 4.3 | 0.90 / – / – / 6.3 | 0.84 / – / – / 15.9 | 0.74 / – / – / 14.2 |

### Bảng 9b. Bản đồ khuyết 50 % (cùng mọi hằng số), 3 seed × 6 descriptor: recall / segFAR / run tệ nhất / sai số

| Luật | Boreas | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.715 / 0.027 / 0.071 / 32.1 | 0.568 / 0.080 / 0.986 / 21.9 | 0.754 / 0.037 / 0.094 / 121.5 | 0.786 / 0.381 / 1.000 / 56.0 | 0.559 / 0.029 / 0.047 / 98.8 | 0.272 / 0.221 / 0.968 / 156.2 |
| Claxton'24 (nhãn) | 0.715 / 0.064 / 0.203 / 34.5 | 0.796 / 0.070 / 0.210 / 16.2 | 0.508 / 0.133 / 0.231 / 89.0 | 0.769 / 0.087 / 0.285 / 24.9 | 0.715 / 0.090 / 0.291 / 134.2 | 0.568 / 0.099 / 0.208 / 47.9 |
| TAO'26 (nhãn) | 0.810 / 0.257 / 0.768 / 61.4 | 0.888 / 0.397 / 0.982 / 99.8 | 0.780 / 0.406 / 0.994 / 270.8 | 0.931 / 0.723 / 1.000 / 101.9 | 0.842 / 0.549 / 1.000 / 301.6 | 0.759 / 0.632 / 1.000 / 177.7 |
| CPC-SC+CS (null bản đồ) | 0.600 / 0.000 / 0.007 / 5.8 | 0.609 / 0.012 / 0.090 / 6.9 | 0.669 / 0.000 / 0.001 / 13.7 | 0.697 / 0.000 / 0.000 / 15.5 | 0.572 / 0.000 / 0.000 / 41.0 | 0.250 / 0.001 / 0.011 / 59.5 |
| CMS-T/ H+SH | 0.644 / 0.002 / 0.007 / 8.8 | 0.674 / 0.015 / 0.065 / 10.4 | 0.614 / 0.003 / 0.010 / 21.7 | 0.739 / 0.001 / 0.007 / 14.7 | 0.630 / 0.004 / 0.014 / 45.2 | 0.295 / 0.000 / 0.003 / 54.8 |
| CMS-W/ H+SH | 0.667 / 0.001 / 0.007 / 6.7 | 0.697 / 0.034 / 0.142 / 15.8 | 0.645 / 0.001 / 0.004 / 13.4 | 0.750 / 0.001 / 0.005 / 14.2 | 0.656 / 0.003 / 0.010 / 41.2 | 0.326 / 0.006 / 0.017 / 45.9 |
| CMS-CPC/ H+SH | 0.736 / 0.005 / 0.016 / 11.5 | 0.759 / 0.053 / 0.187 / 26.7 | 0.799 / 0.011 / 0.049 / 25.0 | 0.791 / 0.003 / 0.016 / 14.9 | 0.717 / 0.011 / 0.024 / 48.3 | 0.492 / 0.010 / 0.026 / 45.8 |
| CMS-T/ H+SH, α = 0.01 | 0.592 / 0.000 / 0.001 / 5.0 | 0.564 / 0.004 / 0.031 / 5.0 | 0.231 / 0.000 / 0.004 / 40.9 | 0.699 / 0.000 / 0.002 / 14.8 | 0.547 / 0.001 / 0.007 / 45.2 | 0.192 / 0.000 / 0.000 / 67.1 |
| CMS-CPC/ H+SH, α = 0.01 | 0.712 / 0.001 / 0.006 / 7.6 | 0.707 / 0.029 / 0.150 / 12.9 | 0.745 / 0.005 / 0.022 / 16.0 | 0.714 / 0.002 / 0.016 / 14.8 | 0.692 / 0.010 / 0.024 / 45.6 | 0.408 / 0.005 / 0.017 / 52.2 |
| Oracle | 0.89 / – / – / 2.5 | 0.90 / – / – / 3.3 | 0.69 / – / – / 8.0 | 0.91 / – / – / 12.0 | 0.85 / – / – / 31.8 | 0.73 / – / – / 23.6 |

### Bảng 10. Kiểm chứng Định lý 6 (nhãn chỉ để kiểm): CMS-T, α = 0.05, theo điều kiện × run

| dataset | conditions x runs | pi (mean) | bound alpha(n+1)/(pi n+1) | realized false onset (CMS-T) | realized / alpha | CF good median / off median | CF good q05 / off q05 |
|---|---|---|---|---|---|---|---|
| 4s_countryside | 180 | 0.50 | 0.119 | 0.042 | 0.84 | 1.009 / 1.047 | 0.769 / 0.817 |
| 4s_office_loop | 300 | 0.65 | 0.080 | 0.037 | 0.74 | 1.305 / 1.329 | 1.165 / 1.210 |
| 4s_old_town | 180 | 0.52 | 0.166 | 0.039 | 0.78 | 1.360 / 1.383 | 1.212 / 1.262 |
| boreas | 780 | 0.62 | 0.125 | 0.034 | 0.68 | 1.183 / 1.243 | 1.030 / 1.079 |
| cmu | 660 | 0.62 | 0.082 | 0.051 | 1.03 | 1.308 / 1.350 | 1.089 / 1.150 |
| nclt | 48 | 0.49 | 0.107 | 0.057 | 1.14 | 1.237 / 1.215 | 1.026 / 1.066 |
| nord | 180 | 0.53 | 0.120 | 0.024 | 0.48 | 1.180 / 1.198 | 0.983 / 1.025 |




## 5. Đọc kết quả

1. **Hiệu chuẩn chặt và hợp lệ (Bảng 5, 10).** Với ρ = off_d, phép thử tuyến trần CMS-T dùng gần đúng ngân sách rủi ro: tỷ lệ
   khởi phát sai thực tế / α = 0.48–1.14 trên 7 dataset (Bảng 10), luôn ≤ cận α(n+1)/(πn+1) của Định lý 6 (7/7), và đuôi null
   phản thực luôn thấp hơn đuôi off-map thật (chi phí q05 0.77–1.21 so với 0.82–1.26: phía bảo thủ của S2). Luật null bản đồ
   CPC-SC+CS chỉ dùng 0.00–0.09 ngân sách. Luật đề xuất CMS-CPC/H+SH có segFAR trung bình ≤ α trên 7/7 ở cả hai mức α (0.04–0.37·α
   ở α = 0.05; 0.05–0.97·α ở α = 0.01).
2. **α = 0.01 khả thi ở mọi nơi (Bảng 2).** Null bản đồ ở α = 0.01 (CPC-SC+CS) cho recall 0.000 trên CMU và 4S office, 0.180 trên
   old town (κ = ∞ hoặc quá cao: < 99 đoạn null). Null phản thực có ~190–590 đoạn mỗi điều kiện.
3. **Điểm mặc định (Bảng 1, 2, 6).** Ở α = 0.05, CMS-CPC/H+SH có recall cao hơn CPC-SC-T½+SH (tốt nhất cũ) trên **7/7**
   (+0.041 NCLT … +0.189 4S countryside), segFAR trung bình 0.002–0.019, run tệ nhất 0.018–0.075 (cũ: tới 0.188 trên CMU); sai số
   điều hướng thấp hơn trên 3/7 (countryside 34.1 so với 51.3 m) nhưng cao hơn trên Boreas (11.2 so với 5.7 m), NCLT, CMU,
   Nordland — cái giá của việc dùng ngân sách rủi ro với bộ lọc Kalman không có cổng ngoại lai. Ở **α = 0.01 (chặt gấp 5 lần)**,
   CMS-CPC/H+SH vẫn có recall cao hơn luật cũ (chạy ở α = 0.05) trên **6/7** (Boreas 0.750 so với 0.666, old town 0.700 so với
   0.640, countryside 0.410 so với 0.334; office −0.004), sai số thấp hơn trên **5/7**, segFAR trung bình ≤ 0.010 trên 7/7.
4. **Chọn luật leave-one-dataset-out (Bảng 7, tiêu chí đăng ký trước).** Ở α = 0.01, CMS-CPC/H+SH+G (thêm cổng đồng thuận vị
   trí tuyến TAO – MAP của HMM) được chọn ở **7/7 fold**, regret 0.0–1.8 m; luật này có sai số thấp hơn CPC-SC-T½+SH trên 6/7
   (Boreas bằng nhau, 5.7 m). Ở α = 0.05 tiêu chí sai số vẫn chọn các luật cũ dè dặt (CPC-SC-T½+CS ở 5/7 fold): khi ngân sách
   là 0.05, dùng hết ngân sách làm tăng sai số điều hướng — khuyến nghị dùng CMS ở α = 0.01.
5. **Đường cong (Bảng 3).** Chuẩn hoá theo null phản thực của từng điều kiện còn cải thiện **xếp hạng**: CMS-CPC/H+SH có recall
   tại FL ≤ 0.01 ≥ CPC-SC-T½+SH trên 5/7 (Boreas 0.796 so với 0.770, CMU 0.778 so với 0.744, old town 0.714 so với 0.680,
   countryside 0.616 so với 0.528; NCLT 0.592 so với 0.612, Nordland 0.790 so với 0.794), pAUC ≥ trên 6/7 (một hoà). So với
   baseline có nhãn: hơn Claxton'24 6/7 và TAO'26 6/7 (chỉ thua CMU 0.778 so với 0.791 / 0.792: khoảng cách giảm từ 0.047 còn 0.013),
   hơn SafeVPR'26 5/5.
6. **Cùng điểm số, ba null (Bảng 4).** Với đúng chi phí tuyến của TAO'26: ngưỡng nhãn 3σ vi phạm (segFAR 0.24–0.74); null bản đồ
   (TAO-SC) quá dè dặt (recall 0.048–0.659); null phản thực (CMS-T, α = 0.05) cho recall 0.284–0.819 (cao hơn TAO-SC 7/7) với
   segFAR 0.024–0.055 — khác biệt chỉ do nguồn null.
7. **Nhân quả (không nhìn trước phiên hiện tại).** Hiệu chuẩn chỉ bằng luồng phản thực của các phiên khác (`[loco]`): ở α = 0.01
   segFAR ≤ 0.010 trên 7/7, recall vẫn cao hơn luật cũ trên 6/7 (Nordland 0.685 so với 0.713), chênh −0.04…+0.03 so với bản chuyển đạo.
8. **Độ bền tỷ lệ lỗ (Bảng 9).** Cùng mọi hằng số, bản đồ khuyết 10 %: recall của CMS-CPC/H+SH cao hơn CPC-SC+CS trên 6/6 ở cả hai α
   (ví dụ countryside 0.552 so với 0.305, sai số 27.5 so với 50.4 m), segFAR trung bình ≤ 0.031 (α = 0.05) và ≤ 0.005 trên 5/6 ở
   α = 0.01 (CMU 0.017); khuyết 50 %: recall cao hơn 6/6 nhưng CMU vượt α (0.053 / 0.029) và sai số cao hơn ở 4/6.
9. **Bán kính đăng ký trước ρ = off_d + excl ({r1}).** Chuỗi + dừng vẫn hợp lệ trung bình ở α = 0.05 (≤ 0.025), nhưng phép thử
   trần chống-bảo-thủ theo seed (chẩn đoán trước khi đánh giá đầy đủ) và CMU vượt α = 0.01 (0.013): xác nhận lựa chọn ρ = off_d
   của lý thuyết (S2).
10. **Đối chứng chẩn đoán.** CMS-CPC không dừng vi phạm (segFAR 0.075–0.196): Định lý 6 chỉ nói về khởi phát; dừng hình dạng SH
    trên quỹ đạo HMM là cần thiết để cắt chuỗi báo mang ra khỏi bản đồ (đúng dự đoán đăng ký trước).

## 6. Hạn chế và việc tiếp theo

- **Sai số điều hướng ở α = 0.05** cao hơn luật cũ trên 4/7: CMS dùng ngân sách rủi ro (FL tới ~0.01) và Kalman không có cổng
  ngoại lai nhạy với vài fix sai. Khuyến nghị α = 0.01; hướng tiếp: hiệu chuẩn trực tiếp rủi ro điều hướng (không chỉ segFAR).
- **CMU** (11 điều kiện × ~190 đoạn, phải gộp Mondrian ở α = 0.01) sát ngưỡng ở α = 0.01 (0.0097) và vượt α khi khuyết 50 %.
- **S1 chỉ đúng trung bình:** tỷ lệ thực tế của phép thử trần thay đổi mạnh theo bố cục lỗ (CMU: phân vị 90 % theo run 0.146 ở
  α = 0.05). Bảo đảm là biên (trung bình theo bố cục), không theo từng run; bảo đảm PAC không sửa được lệch phân phối này.
- **Sai lệch đăng ký trước:** ρ đổi từ off_d + excl sang off_d sau chẩn đoán có nhãn (ghi vào nhật ký trước khi đánh giá đầy đủ);
  biến thể +G được chọn bởi LODO (nằm trong tập ứng viên đăng ký trước); bốn run seed 0 dùng khi thiết kế được đánh dấu ở Entry 28.
- Hiệu chuẩn chính là **chuyển đạo theo phiên** (dùng phản thực của cả phiên); bản nhân quả `[loco]` kém hơn 0–0.04 recall.
- Chưa chạy robot thật vòng kín; off-map tự nhiên chỉ có NCLT. **Không tuyên bố mức A\***: cơ chế mới (Gate 12) và bằng chứng
  mạnh hơn rõ rệt (recall 6–7/7 ở bảo đảm chặt hơn 5 lần, xếp hạng 5/7, LODO ổn định 7/7), nhưng cần thêm lý thuyết cho S1
  (khi nào phẫu thuật tái tạo đúng luật off-map), vòng kín và benchmark off-map tự nhiên.
