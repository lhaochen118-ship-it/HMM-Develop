# Báo cáo vòng 8: hiệu chuẩn nhân quả, độ bền bộ lọc, off-map tự nhiên và HMM liên hợp

*Branch `hmm-navigation-5`, 2026-11-01. Nhật ký `RESEARCH_LOG.md` Entry 30–31 (đăng ký trước, push trước đánh giá). Lý thuyết:
`paper/cms_theory.md` §4c–4d. Vòng trước: `paper/BAO_CAO_E29.pdf`.*

**Tóm tắt.**

1. **Phương pháp đề xuất giữ nguyên và được củng cố: CMS-CPC/H+SH+G+NGRr** (= luật vòng 7, cổng điều hướng mở khoá *giới hạn
   tốc độ*). LODO trên mọi luật không nhãn của vòng này (gồm cả hai biến thể cổng và mọi nhóm hiệu chuẩn) chọn nó ở **7/7 fold**
   (α = 0.05; ở α = 0.01 bản α = 0.01 của nó 6/7).
2. **Bản triển khai được (nhân quả, không nhìn tương lai của phiên): CMS-CPCW/H+SH[both]+NGRr** hơn luật tốt nhất trước CMS
   (CPC-SC-T½+SH) cả **recall 7/7 và sai số điều hướng 7/7** trên 366 run (CI bootstrap cụm: recall 6/7, sai số 7/7), segFAR trung bình
   ≤ 0.008; bản nhân quả hợp lệ ở 7/7 dataset cả α = 0.05 lẫn 0.01 (Định lý 6″, Mệnh đề 12).
3. **Độ bền bộ lọc:** dưới cả ba bộ lọc thay thế (nhiễu quá trình ×4; thêm σ fix 10 m; khởi tạo không nhãn), phương pháp đề xuất hơn
   CPC-SC-T½+SH về recall 7/7 và sai số 7/7 ở cả ba (CI: recall 6/7 mỗi cấu hình; sai số 5/7, 7/7, 6/7).
4. **Off-map tự nhiên** (4Seasons chéo cảnh, 36 run, phiên hoàn toàn off-map): mọi biến thể CMS hợp lệ ở α = 0.05 (không run nào vượt
   α), recall cảnh A cao hơn luật cũ **6/6 cặp** (0.71 so với 0.59 gộp) và sai số thấp hơn (18.8 so với 26.0 m); baseline có nhãn
   vượt α ở 11–28 % run. Bản chuyển đạo vượt α = 0.01 ở 2/36 run — đúng chế độ hỏng π = 0 lý thuyết dự báo, bản nhân quả thì không.
5. **Hai phát hiện về cổng** (báo cáo thẳng): code vòng 7 khác mô tả (mở khoá giới hạn tốc độ thay vì mở cả chuỗi); bản sửa "mở cả
   chuỗi" đăng ký trước hoá ra **kém hơn** (Boreas +2.0 đến +2.9 m, CI > 0) ⇒ giữ cả hai, LODO chọn bản giới hạn tốc độ.
6. **HMM là trung tâm (Entry 31):** HMM liên hợp vị trí–hiện diện với trạng thái OFF có emission hiệu chuẩn phản thực; biên OFF của nó
   **trùng chính xác** chuỗi hiện diện đã hiệu chuẩn (Mệnh đề 13), nên mọi định lý là phát biểu về chính HMM. Đánh giá 114 run: HMM liên hợp có recall trong ±0.01 so với chuỗi vị trí gốc
   ở 6/7 dataset (Nordland −0.02 đến −0.03, do emission dựng lại từ top-100), sai số giảm ở 4S countryside (−3.5 m, CI < 0); so với
   cùng chuỗi không có OFF, ghép nối **không** giảm sai số nhất quán (3/7). Kết luận: công thức HMM là chính xác và dùng được để trình
   bày phương pháp, nhưng bản phân rã (/H) vẫn là cài đặt khuyến nghị; HMM liên hợp vẫn hơn luật cũ 7/7 recall và 7/7 sai số.

## 1. Câu hỏi của vòng này (không có robot thật, chỉ benchmark trên dataset)

| # | Vấn đề còn lại sau vòng 7 | Ảnh hưởng | Thí nghiệm |
|---|---|---|---|
| 1 | Hiệu chuẩn CMS theo phiên là **chuyển đạo** (dùng cả frame tương lai của phiên) | Không triển khai được nguyên dạng; reviewer sẽ hỏi | Nhóm `[online]` (phiên khác + phần đã qua của phiên), `[both]` (giao phiên ∧ phiên khác) |
| 2 | Cổng điều hướng và sai số gắn với **một** cấu hình Kalman khởi tạo ở pose thật | Kết luận về sai số có thể phụ thuộc bộ lọc | F1 nhiễu quá trình ×4, F2 = F1 + σ fix 10 m, F3 khởi tạo không nhãn (top-1 frame đầu) |
| 3 | Off-map hầu hết là **lỗ tổng hợp** (trừ NCLT); phiên **hoàn toàn off-map** có π = 0 | Bảo đảm của nhóm `cond` vô nghĩa ở phiên đó | Benchmark 4Seasons chéo cảnh: bản đồ cảnh A, truy vấn cảnh B (mọi frame off-map, ảnh và VIO thật) |
| 4 | Chốt luật chính | — | CMS-CPCW/H+SH+NGR (định lý chặt) và CMS-CPC/H+SH+G+NGR (recall), khoảng tin cậy ghép cặp, LODO |

## 2. Phương pháp và sửa lỗi của vòng này

**Hiệu chuẩn nhân quả (`analysis/cms.py: online_parts`).** `[online]`: tại frame t, ngưỡng khởi phát là phân vị (1 − α) của max
log-odds trên các đoạn phản thực của **các phiên khác** cộng các đoạn H frame **đã kết thúc trước t** của phiên hiện tại; phép biến đổi
p → e và a của Beta-EM cố định từ các phiên khác. Định lý 6″: tỷ lệ khởi phát sai mỗi đoạn ≤ α(n+1)/(πn+1) với π của tập hiệu chuẩn
có trước đoạn đó — một phiên hoàn toàn off-map vẫn được bảo đảm nhờ phần on-map của các phiên khác. `[both]`: báo khi luật theo phiên
**và** luật theo phiên khác cùng báo; Mệnh đề 12: segFAR ≤ min của hai luật (hợp lệ nếu một trong hai null hợp lệ).

**Cổng +NGR: một chỗ code khác mô tả, một sửa, hai biến thể (tìm ra khi thiết kế F3, Nordland CosPlace s0).**
(a) Mở khoá kiểm lại độ đồng nhất của innovation sau mỗi fix được nhận — chính bước cập nhật của bộ lọc làm innovation nhảy ⇒ chuỗi
đã mở chỉ được nhận **một fix mỗi R = 10 frame** (khác mô tả "mở cho cả chuỗi" của vòng 7). Đăng ký trước: sửa thành mở đến hết chuỗi
(`+NGR`). Giữa đánh giá (202/366 run, ghi nhật ký trước mọi phân tích khác) thấy sửa này **lẫn lộn** với khởi tạo pose thật: Boreas
+1.3 đến +2.6 m (một chuỗi báo sai đồng nhất lọt hết khi đã mở), CMU +0.5 m, còn Nordland / 4S thấp hơn. Hành vi vòng 7 hoá ra là một
thiết kế hợp lệ — **mở giới hạn tốc độ**, chặn tác hại của chuỗi báo sai đồng nhất — nên giữ cả hai (`+NGRr` = vòng 7 + sàn bất định),
tính lại mọi run cho `+NGRr`, và để LODO chọn. (b) Bán kính cổng max(τ, 3√P⁻): khi bộ lọc chưa định vị (P⁻ lớn), fix đúng có
innovation cỡ √P⁻; với khởi tạo pose thật sàn này gần như không hoạt động (`+NGRr` trùng tuyệt đối với +NGR vòng 7 trên 360/366 run;
6 run NCLT lệch ≤ 0.001 recall).

**Benchmark off-map tự nhiên (`analysis/natural_eval.py`).** 6 cặp có thứ tự của {office loop, old town, countryside} × 6 descriptor =
36 run. Bản đồ = bản ghi tham chiếu của A (không lỗ); truy vấn = các bản ghi còn lại của A rồi mọi bản ghi của B. Recall tính trên A,
segFAR trên các đoạn off-map (gần như toàn bộ là B), sai số điều hướng chỉ tính trên A (toạ độ của B không liên quan bản đồ). Baseline
có nhãn được huấn luyện trên bản ghi A dễ nhất **và một bản ghi B có nhãn** (có lợi cho baseline).

## 3. Tối ưu tính toán

- Ba đợt Kaggle, lấp đầy từng acc trước khi sang acc khác (2 phiên L4×4 + 5 phiên CPU mỗi acc, 10 acc):
  - Đợt 1: 20 phiên L4 (đánh giá chính 366 run + F3) và 50 phiên CPU (F1, F2: 732 job).
  - Đợt 2: 48 phiên CPU (36 job benchmark tự nhiên, mỗi job một pipeline đầy đủ ~21 phút; 72 job bản đồ khuyết).
  - Đợt 3: 20 phiên L4 + 50 phiên CPU (biến thể cổng giới hạn tốc độ cho mọi cấu hình).
- Chính sách L4 của user (kẹt > 5 phút thì huỷ + đẩy lại, tối đa 5 lần, sau đó 2×T4): 7/20 phiên được đẩy lại 1–3 lần, không phiên nào
  phải xuống T4.
- Tái dùng: thống kê phản thực chính xác của 216 run bản đồ khuyết và cache của benchmark tự nhiên được đóng gói thành dataset Kaggle
  (`hmm-holes-cms-exact`, `hmm-natural-cache`), các lần chạy lại chỉ còn phần quyết định (CPU, vài phút).
- Kiểm tái lập: các luật không cổng của vòng này trùng **tuyệt đối** với vòng 7 trên mọi run (366/366); `+NGRr` trùng tuyệt đối với
  +NGR của vòng 7 trên 360/366 run — 6 run NCLT (bộ lọc EKF có trạng thái hướng, √P lớn hơn) lệch ≤ 0.001 recall / ≤ 0.09 m do sàn bất
  định 3√P⁻.

{{TABLES}}

## 5. Đọc kết quả

**Hiệu chuẩn nhân quả (Bảng 1–4).** Bản chuyển đạo (`cond`) vẫn có recall cao nhất trên benchmark chính (dữ liệu của phiên giúp
khớp điều kiện). Trong các bản nhân quả, `[both]` (giao phiên ∧ phiên khác) tốt nhất và ổn định nhất: hơn CPC-SC-T½+SH 7/7 cả hai
chỉ số. `[online]` (phiên khác + phần đã qua của phiên) mất recall ở Nordland (0.695 so với 0.713): ở đầu mỗi phiên tập hiệu chuẩn
chưa có gì của điều kiện hiện tại, và Nordland có điều kiện mùa khác hẳn nhau. Giá của tính nhân quả so với bản chuyển đạo: 0.01–0.05
recall, sai số gần như không đổi (nhờ cổng).

**Hai biến thể cổng (Bảng 4).** Mở cả chuỗi (+NGR) để lọt các chuỗi báo sai đồng nhất: Boreas +2.0 đến +2.9 m, CMU +0.5 m (CI > 0);
chỉ có lợi ở 4S countryside (−0.5 đến −1.0 m, VIO trôi). Mở giới hạn tốc độ (+NGRr) chặn tác hại của chuỗi sai đồng nhất ở K·ν mỗi
R frame. LODO chọn +NGRr 7/7.

**Độ bền bộ lọc (Bảng 5–6).** Kết luận chính không phụ thuộc bộ lọc: dưới F1, F2, F3 phương pháp đề xuất hơn luật cũ 7/7 cả recall lẫn
sai số. Cổng giảm sai số 7/7 dưới F1/F2 nhưng **không** giúp dưới F3 (2/7): khi bộ lọc khởi tạo sai, innovation của fix đúng lớn và
cổng (giả định bộ lọc đã định vị) giữ lại chúng — sàn 3√P⁻ chỉ mở cổng trong vài bước đầu khi P còn lớn. Đây là giới hạn đúng như
thiết kế của cổng, không phải của CMS (bản không cổng vẫn hơn luật cũ dưới F3).

**Off-map tự nhiên (Bảng 7–8).** Đây là phép thử quan trọng nhất về tính hợp lệ: phiên của cảnh B hoàn toàn off-map nên nhóm `cond` có
π = 0 trong phiên đó. Thực tế ở α = 0.05 mọi biến thể vẫn hợp lệ (segFAR tệ nhất 0.044 với CMS-CPC/H+SH+G không cổng, 0.013 với cổng +NGRr):
nhiễm của frame off-map yếu vì xoá một hành lang chỉ bỏ một phần nhỏ các khớp giả. Ở α = 0.01 bản `cond` vượt α ở 2/36 run không cổng, 1/36 với +NGRr (đúng dự báo
của Mệnh đề 8), các bản nhân quả không run nào. Recall cảnh A: CMS 0.67–0.72 so với 0.59 của luật cũ (6/6 cặp). Baseline có nhãn (được xem
một bản ghi có nhãn của cảnh B): Claxton'24 recall cao hơn ở hai cặp countryside nhưng vượt α ở 14 % run; Xu'21 28 %; TAO'26 11 %.
⇒ **Khuyến nghị triển khai:** `[online]` hoặc `[both]` (không bao giờ vượt α ở đây), mất ≈ 0.01–0.05 recall so với bản chuyển đạo.

**HMM liên hợp (Entry 31; lý thuyết §4d; Bảng 11–12).** Ba nhận xét. (i) **Quyết định không đổi**: biên OFF của HMM liên hợp trùng
chính xác chuỗi hiện diện đã hiệu chuẩn (Mệnh đề 13), nên segFAR/FL và mọi định lý giữ nguyên — đây là lý do lý thuyết để gọi phương
pháp là "HMM có trạng thái off-map hiệu chuẩn phản thực". (ii) **Ghép nối chỉ đổi vị trí báo cáo**: cập nhật "tôi" ngăn frame off-map
kéo niềm tin vị trí về nơi giống ảnh, nhưng trên dữ liệu thật chuỗi vị trí gốc hiếm khi bị khoá (độ đúng vị trí on-map 0.95), và SH +
cổng đồng thuận đã loại phần lớn fix sai do khoá ⇒ lợi ích nhỏ và không nhất quán (Boreas −2.6 m, old town / countryside +1.3 đến
+2.8 m so với /R). (iii) Khoảng cách /R–/H (≈ 0.02 ở Nordland) là do emission dựng lại từ top-100 thay vì toàn bộ ma trận similarity;
cài đặt liên hợp với emission đầy đủ cần chạy lại bước dựng cache trên GPU (chưa làm).

## 6. Hạn chế và việc tiếp theo

- Benchmark tự nhiên chỉ dùng 3 cảnh 4Seasons (6 cặp); cảnh B khác thành phố nhưng cùng loại ảnh (camera, mùa). Off-map "gần" (đi lạc
  sang phố bên cạnh bản đồ) vẫn chỉ có ở lỗ tổng hợp và NCLT.
- Sai số điều hướng tuyệt đối vẫn phụ thuộc bộ lọc đánh giá; F1–F3 cho thấy **so sánh** giữa các luật bền, không phải mức tuyệt đối.
- Cổng +NGRr giả định bộ lọc đã định vị (F3); chọn giữa hai biến thể mở khoá dựa trên LODO, không có định lý về tác hại.
- `[online]` cần các phiên trước có phần on-map; với robot ở phiên đầu tiên (chưa có phiên nào khác) chỉ còn bản chuyển đạo hoặc null
  bản đồ.
- HMM liên hợp (/J) dùng emission dựng lại từ top-100 (mất ≈ 0.02 recall ở Nordland so với chuỗi gốc); bản đầy đủ cần ma trận
  similarity của từng run (chạy lại `nav_demo` trên GPU).
- Việc tiếp theo: dữ liệu MarsLab (khi có máy RTX ghi rosbag) cho off-map tự nhiên kiểu "đi ra ngoài vùng bản đồ" và vòng kín
  điều khiển.
