# Báo cáo AUTOLOOP — 12 giờ tự động cải tiến luật báo fix trên bản đồ có lỗ

*Branch `hmm-2nd-idea`, 2026-11-04 14:15 → 2026-11-05 02:15 UTC. Trạng thái vòng lặp: `handoff/AUTOLOOP.md`; đăng ký trước + kết quả:
`RESEARCH_LOG.md` Entry 11–15; bảng điểm: `analysis/autoloop_board.py`; JSON mỗi run: `analysis/results/owf/`.*

## 1. Mục tiêu và điểm số

Bài toán (giao thức `handoff/07_IDEA1_SUMMARY.md` §1): định vị chuỗi trên bản đồ ảnh có 30 % ô 300 m bị xoá. Ở mỗi khung, hệ thống phải quyết định
báo hay không báo một fix, không có nhãn.

**Score** của một luật trên một tập run là recall gộp (trung bình các run). Score chỉ được tính khi đạt cả ba ràng buộc:
- **V1:** TB segFAR ≤ 0.05 trên MỌI dataset.
- **V2:** ≤ 2 % run có segFAR > α.
- **N1:** sai số điều hướng gộp ≤ HSI-VN + 0.5 m trên cùng run.

Điểm xuất phát:
- **HSI-VN** (ý tưởng 2a): luật khuyến nghị lúc bắt đầu.
- **OWF** (Entry 10, bộ lọc thế giới mở): recall cao hơn nhưng trượt V2 / N1.

**Quy trình mỗi vòng:**
1. Chẩn đoán trên dữ liệu phát triển (seed 0–9; nhãn chỉ để chẩn đoán).
2. Đề xuất biến thể có lý do cơ chế; đánh giá phát triển (ngoại tuyến nếu được).
3. **Đăng ký trước** trong `RESEARCH_LOG.md`, commit + push TRƯỚC khi chạy tập kiểm tra.
4. Kiểm trên **một nhóm 3 seed MỚI chưa dùng** (144 run: 8 dataset có lỗ × 6 descriptor), so với luật đương nhiệm trên CÙNG run.

Không nhóm seed nào được dùng cho hai quyết định.

## 2. Lời giải hiện tại (luật khuyến nghị): OWF-HWA-S

```
ảnh truy vấn + odometry
   │
   ├─► OWF, ngân hàng tỉ lệ odometry {0.97, 1, 1.03} × q {0.005, 0.02}·excl, chọn trực tuyến theo evidence      (owf.py --scales)
   │      → khối lượng đĩa excl m_t, ảnh bản đồ x̂_t
   │
   ├─► chuỗi lai: x̂_t nếu m_t ≥ 0.9 VÀ đường đi từ đầu chuỗi ≥ 16·excl, ngược lại chuỗi tô-pô est_c          (owf_hybrid.py --mode xms0.9_16)
   │      → HSI-VN nguyên bản trên chuỗi lai (tự giám sát hồi cứu + conformal theo run)  = OWF-H
   │
   └─► báo tại t nếu MỘT trong bốn điều kiện                                                                     (owf_union.py)
          (1) OWF-H báo;
          (2) m_t ≥ 1 − 1e-5 và đường đi ≥ 16·excl;
          (3) m_t ≥ 1 − 1e-8 và đường đi ≥ 2·excl;
          (4) x̂_t trùng (≤ excl) với CẢ est_c lẫn truy hồi top-1, m_t ≥ 1 − 3e-4 và đường đi ≥ 0.5·excl  (bậc đồng thuận)
       fix = ảnh của OWF-H khi (1), ảnh OWF x̂_t khi (2)–(4)
```

## 3. Bảng điểm trên các nhóm seed mới (đăng ký trước)

Ô = recall gộp / số run > α (trên 144) / sai số điều hướng gộp (m). Mọi luật có số trong bảng đều đạt V1 trên nhóm của nó. Mỗi nhóm seed chỉ dùng
cho MỘT quyết định (cột in đậm là luật được kiểm ở nhóm đó).

| Nhóm mới | HSI-VN | OWF-H (E11) | OWF-HU (E12) | OWF-HW-S (E13) | OWF-HWA-S (E14) | Quyết định |
|---|---|---|---|---|---|---|
| seed 40–42 | 0.811 / 1 / 15.35 | **0.885** / 1 / 14.46 | | | | E11 đạt: +0.074 [+0.060, +0.088] |
| seed 43–45 | 0.805 / 1 / 15.92 | 0.878 / 1 / 15.73 | **0.896** / 1 / 14.94 | | | E12 đạt: +0.018 [+0.014, +0.022] |
| seed 46–48 | 0.786 / 1 / 14.72 | 0.860 / 1 / 14.62 | 0.878 / 1 / 13.61 | **0.902** / 1 / 12.75 | | E13 đạt: +0.024 [+0.019, +0.031] |
| seed 49–51 | 0.804 / 0 / 14.34 | 0.882 / 0 / 15.37 | 0.903 / 1 / 14.68 | 0.921 / 0 / 13.78 | **0.933** / 0 / 13.64 | E14 đạt: +0.012 [+0.010, +0.014] |

Trên nhóm 49–51, luật hiện tại so với HSI-VN có recall **+0.129** (0.933 vs 0.804), không run nào vượt α, và sai số điều hướng thấp hơn 0.7 m.
Theo dataset (recall / sai số):

| Dataset | OWF-HWA-S | HSI-VN | Δ recall |
|---|---|---|---|
| Boreas | 0.975 / 3.4 m | 0.898 / 5.2 m | +0.077 |
| CMU | 0.874 / 3.8 m | 0.808 / 3.4 m | +0.066 |
| Nordland | 0.975 / 9.6 m | 0.813 / 4.2 m | +0.162 |
| office | 0.967 / 8.1 m | 0.857 / 7.7 m | +0.110 |
| old town | 0.939 / 26.6 m | 0.737 / 32.0 m | +0.202 |
| countryside | 0.838 / 21.7 m | 0.644 / 20.0 m | +0.194 |
| Oxford | 0.921 / 17.0 m | 0.761 / 22.0 m | +0.160 |
| St Lucia | 0.975 / 18.9 m | 0.912 / 20.4 m | +0.063 |

Cả bốn quyết định đều đạt trên nhóm seed mới của mình. Mỗi bước nâng recall trên cùng run, không tăng số run vi phạm, và sai số điều hướng
không tệ hơn.

## 4. Các phát hiện cơ chế

1. **Chứng chỉ hình học của HSI bị quỹ đạo dead-reckoning lừa (E11).** Ghép thẳng chuỗi OWF vào HSI làm vỡ HSI (CMU segFAR 0.089). Lý do: chuỗi
   OWF luôn khớp odometry, kể cả khi sai, trong khi chứng chỉ của HSI giả định chuỗi được ước lượng tự do. Sửa: chỉ giao chuỗi OWF khi OWF tự tin
   VÀ đã ổn định (đã đi ≥ 16·excl). Kết quả: bộ ước lượng tốt hơn (OWF) cộng với hiệu chuẩn theo run (HSI).
2. **Khối lượng thế giới mở cực cao an toàn khi đã ổn định (E12–E13).** Trên Nordland / old town, OWF báo được nhiều fix đúng mà HSI bỏ qua. Với
   ngưỡng 1 − 1e-5 sau 16·excl, và 1 − 1e-8 sau 2·excl cho chuỗi ngắn, không thêm run vi phạm nào.
3. **Odometry thật lệch tỉ lệ (E13).** VIO 4Seasons dài hơn GNSS 3–7 % (countryside 1.04, office 1.04, old town 0.94); odometry mô phỏng lệch ~3 %.
   Ngân hàng tỉ lệ chọn theo evidence cho countryside +0.057 recall.
4. **CMU là bài toán đầu chuỗi; đồng thuận ba nguồn mở được nó (E14).** Mỗi run CMU có ~130 chuỗi ngắn ~7.5·excl. Chuỗi lai đúng trên 0.96
   khung nhưng đầu chuỗi không được báo (phát triển: 0.79). OWF (thế giới mở, metric), chuỗi tô-pô (thế giới đóng) và truy hồi top-1 (một khung) có
   kiểu lỗi khác nhau, nên khi cả ba trùng một ảnh, yêu cầu "đã đi đủ xa" gần như không cần nữa. Riêng bậc này có TB segFAR ≤ 0.003 trên mọi dataset
   phát triển. Kết quả tập mới: CMU 0.832 → 0.874, và thắng 144/144 run.

## 5. Kết quả tiêu cực (đã thử, bỏ)

- *Lớp quyết định riêng cho OWF (13 biến thể):* lịch ε theo quãng đường, tuổi track, cổng nhảy. Không biến thể nào đạt V2 (11–19 run > α) hay N1.
- *Đưa độ tin OWF làm đặc trưng cho HSI* (`xmsc`): +0.0006, bỏ.
- *Lân cận (t, D) của chuỗi lai:* phẳng (0.866–0.871), tức bền nhưng không còn chỗ tăng.
- *Bầu chọn chuỗi bằng truy hồi top-1:* giảm độ đúng của chuỗi (0.959 → 0.947), vì top-1 chỉ đúng 0.84.
- *Đòi đồng thuận liên tục L khung:* không tốt hơn biên ε.
- *Trôi hướng VIO:* nhỏ (< 0.6°/km), nên không cần ngân hàng hướng.
- *Thêm bậc sau Entry 14 (phát triển, tập A):* gần bão hoà. Bậc đầu chuỗi (đồng thuận + khối lượng ≥ 0.5 khi đường đi < 0.5·excl) và bậc đồng thuận
  lỏng có bền vững (ε = 3e-3 / 1e-2, L = 3 / 5) chỉ thêm +0.001–0.004 nhưng làm xuất hiện 1–2 run > α. Phần còn thiếu nằm ở BỘ ƯỚC LƯỢNG
  (countryside: chuỗi đúng ~0.84–0.87), không ở lớp quyết định.

<!-- ENTRY15 -->

## 6. Hạn chế và việc tiếp theo

- CMU vẫn là dataset yếu nhất (0.68 trên seed 46–48).
- Countryside: chuỗi tốt nhất chỉ đúng 0.87 khung; sai số điều hướng 25.7 m (HSI-VN 22.4).
- Các nhóm seed khác nhau về độ khó (HSI-VN 0.786–0.811), nên mọi so sánh đều làm trên CÙNG run.
- Mọi kết quả là trên lỗ mô phỏng (30 % ô 300 m) của 8 dataset; NCLT (off-map tự nhiên) không có trong kho mới.
