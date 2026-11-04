# AUTOLOOP — vòng nghiên cứu tự động 12 giờ (2026-11-04 14:15 UTC → 2026-11-05 ~02:15 UTC)

*Yêu cầu user (2026-11-04 14:13 UTC): "Làm tiếp. Thực hiện 1 quy trình tự động giải quyết vấn đề, không ngừng tìm ra giải pháp mới, sáng tạo, giải
quyết hiệu quả vấn đề (chứng minh bằng score cao trên các datasets). Tự chạy tiếp 12 tiếng." File này là trạng thái của vòng lặp: mọi lần thức
dậy (tin nhắn hẹn giờ, khởi động lại container) đọc file này trước, làm tiếp từ "Trạng thái hiện tại", và cập nhật nó sau mỗi bước.*

## 1. Mục tiêu và điểm số

Luật báo fix không nhãn trên bản đồ có lỗ (giao thức `07_IDEA1_SUMMARY.md` §1). **Score của một luật trên một tập run** = recall gộp (TB các run), chỉ
tính khi đạt **ràng buộc**: (V1) segFAR TB ≤ 0.05 trên MỌI dataset; (V2) ≤ 2 % run có segFAR > α; (N1) sai số điều hướng gộp ≤ của HSI-VN + 0.5 m
trên cùng run. Luật tham chiếu: **HSI-VN** (khuyến nghị hiện tại; 0 run > α, recall gộp tập A 0.791, sai số 15.1 m), **OWF** (Entry 10: recall
0.863 nhưng V2 trượt 19/404, N1 trượt 16.9 m), SH (ý tưởng 1).

## 2. Quy trình một vòng (bắt buộc, theo `04_RESEARCH_WORKFLOW.md`)

1. Chẩn đoán điểm yếu của luật tốt nhất trên dữ liệu PHÁT TRIỂN (seed 0–9, tập A của Entry 10; nhãn chỉ để chẩn đoán).
2. Đề xuất ≥ 2 biến thể có lý do cơ chế; ưu tiên biến thể đánh giá được ngoại tuyến từ đầu ra đã có (frame npz, cache) — rẻ.
3. Đánh giá phát triển (cục bộ nếu được; Kaggle CPU nếu cần chạy lại bộ lọc). Chọn ứng viên theo Score trên tập A.
4. **Đăng ký trước** trong `RESEARCH_LOG.md` (tiêu chí = Score + ràng buộc, quy tắc quyết định), commit + push TRƯỚC khi chạy tập mới.
5. Kiểm trên **một nhóm seed mới chưa dùng** của kho riêng (mục 3), cùng run với HSI-VN; ghi kết quả + quyết định; cập nhật handoff (00, 01, 03
   §5–6, 06) và file này; commit + push.
6. Lặp lại với điểm yếu tiếp theo. Không kiểm lại cùng một giả thuyết trên tập đã dùng.

## 3. Kho tập mới riêng của vòng này

Seed 40–48 (3 nhóm: 40–42, 43–45, 46–48), 8 dataset có lỗ (Boreas, CMU, Nordland, office, old town, countryside, Oxford, St Lucia) × 6 descriptor,
sinh bằng `hsi_fresh.py --keep navcache_r40` (kèm HSI-VN / HSI-VMN / HSI-rot-m-sc / oracle trên cùng cache) — đợt `fr40`. Kho dự trữ 19–21 /
22–24 của `caotienminh1/hmm-navcache-r19` để dành cho phiên HSI (25–27 đã dùng ở Entry 10).

## 4. Hướng đã lên lịch (thứ tự ưu tiên; cập nhật khi có số)

1. **Ghép OWF + HSI** (bộ ước lượng OWF, lớp quyết định HSI): thay `est_c` của cache bằng quỹ đạo OWF (+ `conf_c`/`lo_c` = khối lượng đĩa OWF)
   rồi chạy HSI-VN nguyên bản. Kỳ vọng: giữ 0 vi phạm và điều hướng của HSI, recall tăng vì chuỗi vị trí đúng hơn (0.87–1.00 vs 0.78–0.95).
2. **Lớp quyết định an toàn cho OWF:** lịch ε theo quãng đường từ đầu chuỗi / từ lần mất định vị (Mệnh đề 2: O₀ ≈ 1 ở đầu chuỗi), cổng nhảy theo
   độ bất định dead-reckoning của chính bộ lọc, đĩa bán kính nhỏ cho fix chính xác (điều hướng).
3. **Bộ ước lượng OWF tốt hơn:** mô hình trôi hướng / tỉ lệ (countryside VIO), BMA thay vì chọn một q.
4. Nếu còn thời gian: giao (OWF ∧ HSI) / hợp có hiệu chuẩn; NCLT thêm cấu hình.

## 5. Trạng thái hiện tại (cập nhật mỗi bước)

- 14:15 UTC: bắt đầu. Kế hoạch ghi; hẹn giờ tự đánh thức mỗi ~2 giờ (send_later), lần cuối ~02:15 UTC = tổng kết.
- 14:23 UTC: đợt `fr40` (34 kernel CPU, 432 job `hsi_fresh.py --keep navcache_r40`, seed 40–48 × 8 dataset × 6 desc, kèm HSI-VN / HSI-VMN /
  HSI-rot-m-sc / oracle) đã đẩy; monitor `runs/f_state.json` (scratchpad).
- 14:50 UTC: **vòng 1, phát triển (tập A, 404 run, ngoại tuyến):** 13 biến thể lớp quyết định của OWF (`analysis/owf_decide.py`: lịch ε khởi
  đầu, tuổi track, cổng nhảy) — KHÔNG biến thể nào đạt V2 (11–19 run > α) hay N1 (16.7–17.1 m vs HSI-VN 15.2) ⇒ lớp quyết định của OWF một
  mình không đủ. Ghép OWF→HSI thô (`owf_hybrid.py --mode x`) làm vỡ HSI (CMU s1 segFAR 0.089: chứng chỉ hình học của HSI bị lừa bởi quỹ đạo
  dead-reckoning của OWF); ghép CÓ ĐIỀU KIỆN (`--mode xm0.5`: chỉ thay chuỗi khi khối lượng OWF ≥ 0.5) trên CMU s1: recall 0.830 / segFAR 0.005
  (HSI-VN 0.572 / 0, OWF 0.812 / 0.008). Đợt phát triển đầy đủ `hybA` (2 phiên L4, 130 job: xm0.5 HSI-VN+VMN, xm0.9 HSI-VN; frame OWF tập A
  publish `synchan5704/hmm-owf-frames-a`) đã đẩy 14:59.
- 15:45 UTC: **vòng 1 chọn được OWF-H** (`--mode xms0.9_16`: chuỗi OWF chỉ giao cho HSI-VN khi khối lượng ≥ 0.9 và đã đi ≥ 16·excl từ đầu
  chuỗi): Score phát triển 0.870 (0 run > α, sai số 14.58 m) vs HSI-VN 0.791. **Entry 11 đăng ký trước** (F1–F3 trên seed 40–42, 144 run) đã push.
  Đợt phát triển vòng 2 `hybC` (L4: đặc trưng độ tin OWF cho HSI `xmsc`, quét t / D) đã đẩy 15:48. Kho `fr40`: 7/34 kernel xong, cache kéo dần
  bằng `automation/fetch_done.py` vào scratchpad `r40/`.
- 16:55 UTC: kho `fr40` xong (432 cache, publish `synchan5704/hmm-navcache-r40`, kèm HSI-VN / VMN / rot-m-sc / oracle trên cùng cache). Đợt kiểm
  tra Entry 11 `t40` (32 kernel CPU, 144 run seed 40–42: OWF → OWF-H HSI-VN + VMN) đã đẩy 16:41. Vòng 2 phát triển: lân cận (t, D) phẳng — Score
  0.866–0.871 với t ∈ {0.8, 0.9, 0.95}, D ∈ {12, 16, 24}, tất cả hợp lệ (bền); đặc trưng độ tin OWF cho HSI (`xmsc`) +0.0006 (bỏ); OWF-H-VMN
  0.860 / 13.63 m trội HSI-VMN (0.781 / 13.65). Vòng 3 phát triển (`devS`, 4 phiên L4, 149 run): ngân hàng tỉ lệ odometry `--scales 0.97,1.0,1.03`
  × `--qx 0.005,0.02` (thiết kế countryside s0: recall 0.554 → 0.603, MAP đúng 0.812 → 0.834) + OWF-H trên đó.
- 17:30 UTC: **Entry 11 ĐẠT trên seed 40–42** (144 run): OWF-H 0.885 vs HSI-VN 0.811 (+0.074, CI [+0.060, +0.088]), 1/144 run > α, sai số 14.46 vs
  15.35 m ⇒ **OWF-H là luật khuyến nghị**. Handoff 00 / 01 / 03 cập nhật.
- 17:40 UTC: **Entry 12 đăng ký trước** (OWF-HU = OWF-H ∨ báo OWF ≥ 1 − 1e-5 sau 16·excl; phát triển Score 0.892, 0 run > α, 13.74 m); đợt kiểm tra
  `t43` (seed 43–45, 32 kernel CPU) đã đẩy. `devS` (ngân hàng tỉ lệ odometry, L4) đang chạy. Bảng điểm (tập mới, recall gộp / run > α / sai số):
  HSI-VN 0.811 / 1 / 15.35 → OWF-H 0.885 / 1 / 14.46 (seed 40–42).
