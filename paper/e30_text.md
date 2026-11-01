# Báo cáo vòng 8: hiệu chuẩn nhân quả, độ bền bộ lọc và benchmark off-map tự nhiên

*Branch `hmm-navigation-5`, 2026-11-01. Nhật ký `RESEARCH_LOG.md` Entry 30 (đăng ký trước, push trước đánh giá). Lý thuyết:
`paper/cms_theory.md` §4c. Vòng trước: `paper/BAO_CAO_E29.pdf`.*

**Tóm tắt.**

{{SUMMARY}}

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
innovation cỡ √P⁻; với khởi tạo pose thật sàn này không hoạt động (`+NGRr` trùng khớp tuyệt đối với +NGR của vòng 7 trên mọi run kiểm).

**Benchmark off-map tự nhiên (`analysis/natural_eval.py`).** 6 cặp có thứ tự của {office loop, old town, countryside} × 6 descriptor =
36 run. Bản đồ = bản ghi tham chiếu của A (không lỗ); truy vấn = các bản ghi còn lại của A rồi mọi bản ghi của B. Recall tính trên A,
segFAR trên các đoạn off-map (gần như toàn bộ là B), sai số điều hướng chỉ tính trên A (toạ độ của B không liên quan bản đồ). Baseline
có nhãn được huấn luyện trên bản ghi A dễ nhất **và một bản ghi B có nhãn** (có lợi cho baseline).

## 3. Tối ưu tính toán

{{OPS}}

{{TABLES}}

## 5. Đọc kết quả

{{READ}}

## 6. Hạn chế và việc tiếp theo

{{LIMITS}}
