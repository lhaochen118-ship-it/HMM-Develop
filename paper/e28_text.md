# Báo cáo vòng 6: Phẫu thuật bản đồ phản thực (CMS) — tự hiệu chuẩn quyết định định vị trên chính luồng triển khai

*Branch `hmm-navigation-5`, 2026-11-01. Nhật ký `RESEARCH_LOG.md` Entry 28 (đăng ký trước ở đầu entry, đã push trước khi
chạy đánh giá đầy đủ). Lý thuyết `paper/cms_theory.md`; novelty `LITERATURE_GATE.md` Gate 12. Vòng trước:
`paper/BAO_CAO_E27.pdf`.*

## 1. Vấn đề còn lại và ý tưởng

Mọi luật không nhãn trước đây (certified, CPC-SC, CPC-SC-T) hiệu chuẩn ngưỡng trên **null tự-phát-lại của bản đồ**: frame
bản đồ, che block của chính nó, làm query off-map. Null này khác điều kiện ảnh của query, dùng odometry hoàn hảo, và chỉ có
~10 chunk độc lập. Hệ quả đã đo ở vòng 3–5: tỷ lệ khởi phát sai thực tế 0.001–0.006 ≪ α (ngân sách rủi ro bị bỏ phí), α = 0.01
không khả thi trên CMU và 4S office (κ = ∞), không có bảo đảm có điều kiện theo hiệu chuẩn.

**CMS (Counterfactual Map Surgery).** Null được sinh từ **chính luồng query**: với mỗi frame t, tính lại thống kê bằng chứng
trên bản đồ đã **cắt bỏ hành lang bán kính ρ = off_d + excl quanh niềm tin của chính hệ thống** (các anchor của giả thuyết tuyến
thắng trên N = 20 frame gần nhất). Nếu niềm tin đúng, cả cửa sổ cách bản đồ còn lại > off_d: thống kê phản thực là một mẫu
**off-map hợp lệ** với đúng điều kiện ảnh, nhiễu odometry và phụ thuộc thời gian của query. Nếu niềm tin sai, nơi thật còn
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
  acc kế), 3 tiến trình/kernel; kết quả công khai `nhatlong1103/hmm-cms-cache`. Đánh giá (đường cong + điểm mặc định, 2 mức α)
  cũng chia theo (dataset, descriptor, seed) trên các kernel CPU; chi phí tuyến thật dùng lại `hmm-route-cache`.

{{TABLES}}

## 5. Đọc kết quả

{{READING}}

## 6. Hạn chế và việc tiếp theo

{{LIMITS}}
