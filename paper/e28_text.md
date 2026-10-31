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

{{TABLES}}

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
