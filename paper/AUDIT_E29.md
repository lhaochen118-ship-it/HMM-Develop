# Tự kiểm toán toàn bộ nghiên cứu (Entry 29, branch `hmm-navigation-5`)

*2026-11-01. Mục tiêu: bảo đảm không có lỗi logic, lỗi code hay rò nhãn dẫn tới score sai; sửa mọi lỗi thật và tính lại. Phạm vi: code của phương pháp và đánh giá, công thức, định lý, quy trình chia dữ liệu / hiệu chuẩn / huấn luyện
baseline, thống kê, kiến thức AI/ML được dùng, tuyên bố novelty. Mỗi mục: phát hiện → mức độ → xử lý → ảnh hưởng tới kết quả.
Mức độ: **Nghiêm trọng** (làm sai kết luận), **Trung bình** (sai một phát biểu / thiên lệch có hướng), **Nhẹ** (cần ghi rõ).*

## A. Code

| # | Phát hiện | Mức | Xử lý | Ảnh hưởng |
|---|---|---|---|---|
| A1 | **Null phản thực bị cắt cụt** (Entry 28, `cms.cms_stats`): xoá entry trong hành lang khỏi top-100 đã lưu ⇒ chỉ còn 100 − n_mask giả thuyết (n_mask trung vị 39–62) và giá trị dự phòng là similarity thứ 100 của bản đồ *đầy đủ*; thống kê trên M \ B_t thật dùng top-100 của M \ B_t. Winner phản thực thường ở hạng 58–72 (7–21 % ở 10 hạng cuối) ⇒ hạng > 100 có thể thắng | Trung bình | `analysis/cms_exact.py`: top-300 (GPU), lấy đúng 100 entry chưa che đầu tiên cho giả thuyết, tra cứu và dự phòng; tính lại 366 run + các run lỗ 10/50 % | Chi phí tuyến phản thực: trung vị +0.004 (thang ~1.3, hai chiều); độ khác biệt phản thực bản cũ **chống-bảo-thủ** (trung vị 0.264 so với 0.287) |
| A2 | Frame có toàn bộ top-100 bị che: bản cũ đánh dấu thiếu | Nhẹ | Bản chính xác không còn danh sách thiếu (0 % trên dữ liệu thử) | — |
| A3 | Similarity fp16 (cache top-K) và fp32 (bản chính xác) | Nhẹ | Ghi rõ | Chi phí thật lệch ≤ 3·10⁻⁴; winner trùng 99.5 % |
| A4 | Đường cong vận hành dùng điểm số tức thời (`score > t`, không trễ) trong khi điểm mặc định của các luật chuỗi dùng trễ Schmitt ⇒ điểm mặc định **không nằm trên** đường cong của chính nó | Nhẹ (quy ước kế thừa từ vòng 3) | Ghi rõ trong báo cáo | So sánh đường cong vẫn công bằng giữa các luật (cùng quy ước) |
| A5 | **Odometry:** luật quyết định dùng `o_q`; với dataset odometry mô phỏng (CMU, Nordland), bộ lọc điều hướng của đánh giá tự mô phỏng một odometry *khác* (trôi hướng 0.3°/bước). Odometry thật được căn yaw / scale bằng GT trên 20–50 frame đầu; bộ lọc khởi tạo ở vị trí thật | Nhẹ (chung cho mọi phương pháp) | Ghi rõ là giả định "biết pose ban đầu"; cổng +NGR dùng đúng trạng thái của bộ lọc đánh giá | Không thiên vị giữa các luật |
| A6 | **Bộ lọc đánh giá quá tự tin:** √P ≈ 0.6 m trong khi innovation của fix đúng có trung vị 0.5–8 m ⇒ độ lợi K ≈ 0.014 | Trung bình (độ lớn tuyệt đối của sai số điều hướng phụ thuộc bộ lọc này) | Ghi rõ; so sánh tương đối giữa các luật vẫn trên cùng bộ lọc; giải thích vì sao cổng χ² cổ điển khoá chết | Số sai số tuyệt đối nên đọc như chỉ số tương đối |
| A7 | Rò nhãn trong phương pháp: `cms.py`, `cms_exact.py` không dùng `q_pos`, `inm`, `offm`, `good`, `bsel`; `navrisk.py` dùng `q_pos` chỉ để khởi tạo và (dataset mô phỏng) sinh odometry của bộ lọc, đúng như bộ lọc đánh giá | — | Đã kiểm bằng grep | Không có rò nhãn |
| A8 | Tên log quá dài, sửa `analysis/*.py` khi đang tạo kernel (upload lại) | Vận hành | Đã sửa / ghi vào `02` §000 | — |
| A9 | Nhóm hiệu chuẩn của cổng +NGR phụ thuộc biến toàn cục `ALPHA_MIN` còn lại từ lần gọi luật trước (thứ tự gọi) | Nhẹ | `navrisk.gate_tau` cố định ngưỡng Mondrian (α = 0.05) | Kết quả cổng tất định, không phụ thuộc thứ tự |

## B. Công thức và định lý

| # | Phát hiện | Mức | Xử lý |
|---|---|---|---|
| B1 | **Khởi phát của chuỗi đầy đủ bộ nhớ (CPC-SC vòng 3, CMS-CPC vòng 6):** κ hiệu chuẩn trên chuỗi khởi động ở odds 1 với lập luận "odds 1 là mức cao nhất của chuỗi chưa báo" — **sai khi κ > 0** (κ ≈ 2.4–4.7): chuỗi chưa khởi phát có thể vào đoạn với log-odds trong (0, κ], bước dự đoán đơn điệu tăng ⇒ vượt κ dễ hơn | **Nghiêm trọng về lý thuyết** (phát biểu "P(khởi phát) ≤ α" của CPC-SC / CMS-CPC chỉ còn là xấp xỉ thực nghiệm) | Định lý 6′ + luật **CMS-CPCW** (khởi phát bằng chuỗi cửa sổ hữu hạn, độc lập trạng thái lúc vào đoạn) — `paper/cms_theory.md` §4b(i) |
| B2 | Định lý 6: tập "đoạn tốt" phụ thuộc dữ liệu; cần hoán đổi được **có điều kiện trên nhãn tốt/xấu**; không phủ các đoạn ở độ sâu < N − 1 | Trung bình (phát biểu chưa chặt) | Phát biểu lại S3, §4b(ii) |
| B3 | Bổ đề 1, 2 (cổng ẽ ≤ e từng điểm; luỹ thừa Jensen; trung bình), Định lý 1 (chặn chuỗi hiện diện bởi Shiryaev–Roberts: O′ ≤ c + O, R_t ≤ (1 + R_{t−1})LR_t, optional stopping), Định lý 5, PAC (Hệ quả 9: P(F̄(κ) > α) = P(Bin(n, α) ≤ k − 1)), chỉ số conformal của κ (⌊α(n+1)⌋, ⌈(1−α)(n+1)⌉) | — | Kiểm lại từng bước: **đúng** (Định lý 1 vẫn cần e-value hợp lệ có điều kiện, đã nêu là vi phạm thực nghiệm ở Boreas/4S) |
| B4 | Mệnh đề 8 (hướng nhiễm) dựa trên S2 (đơn điệu theo khoảng cách) — giả định, kiểm bằng thực nghiệm (Bảng 10: đuôi phản thực thấp hơn đuôi off-map 7/7) | Nhẹ | Ghi rõ là giả định |
| B5 | Lập luận ρ = off_d + excl (đăng ký trước, Entry 28) sai chiều | Đã sửa ở Entry 28 (ρ = off_d), có ghi nhật ký trước đánh giá | — |
| B6 | Cổng +NGR: phát biểu về rủi ro chỉ gần đúng (d_cf đo so với niềm tin, innovation so với bộ lọc) | Nhẹ | Mệnh đề 11: phần chặt là "chỉ bỏ báo cáo ⇒ giữ mọi cận theo đoạn"; phần định lượng ghi là gần đúng |

## C. Chia dữ liệu, hiệu chuẩn, huấn luyện

| # | Phát hiện | Mức | Xử lý / ảnh hưởng |
|---|---|---|---|
| C1 | Baseline có nhãn (Claxton'24 MLP, Xu'21 (T, k), TAO'26 3σ, SafeVPR'26 LTT) được huấn luyện / tinh chỉnh trên 2 điều kiện dễ nhất (`bsel`) và **đánh giá trên mọi điều kiện, kể cả `bsel`** | Trung bình (thiên vị **có lợi cho baseline**) | Mọi so sánh "hơn baseline có nhãn" là bảo thủ; ghi rõ |
| C2 | CMS hiệu chuẩn **chuyển đạo theo phiên** (dùng phản thực của cả phiên, kể cả frame tương lai); Beta-EM a cũng theo cả phiên (kế thừa) | Trung bình | Báo cáo song song bản nhân quả `[loco]` (chỉ phiên khác) |
| C3 | Thiết kế dùng một số run của tập giữ lại (4 run ở Entry 28, 6 run ở Entry 29) | Trung bình (thiên lệch chọn lựa) | Ghi trong đăng ký trước; đo bằng LODO |
| C4 | 64 họ luật được đánh giá (so sánh bội) | Trung bình | Báo cáo luật đăng ký trước và luật LODO chọn; không chọn theo bảng |
| C5 | NCLT chỉ 1 seed (6 run); độ bền lỗ chỉ 3 seed | Nhẹ | Ghi rõ |
| C6 | **Thống kê:** vòng 6 báo trung bình và số dataset thắng; bổ sung khoảng tin cậy. Các run (seed × descriptor) không độc lập (cùng ảnh, cùng bố cục lỗ) ⇒ dùng bootstrap cụm theo seed | Bổ sung | `analysis/paired_stats.py` (bootstrap cụm + sign test theo seed); bảng ghép cặp trong `BAO_CAO_E29` |

## D. Kiến thức AI / ML

| # | Phát hiện | Xử lý |
|---|---|---|
| D1 | Gọi κ là "phân vị conformal" của null phản thực: null không hoán đổi được với điểm kiểm tra theo cấu trúc; hợp lệ dựa trên S1–S3 (giống "surrogate null"), không chỉ trên hoán đổi conformal | Sửa cách gọi trong lý thuyết: "phân vị của null phản thực" |
| D2 | e-value a·p^(a−1) với a ước lượng trên chính dữ liệu (Beta-uniform mixture, Pounds–Morris 2003): không còn là e-value đúng nghĩa; hợp lệ của luật đến từ hiệu chuẩn κ trên cùng phép biến đổi | Ghi rõ |
| D3 | TAO'26, TRAIL'26, VPR-auditing'26 tái hiện từ bài báo (không có code gốc): số liệu baseline có thể khác bản gốc | Đã ghi từ vòng 4; giữ |
| D4 | Bộ lọc Kalman vô hướng cho 2-D, nhiễu quá trình (0.05·L)² ngẫu nhiên trong khi trôi thật có hệ thống | Xem A6 |

## E. Tuyên bố novelty

| # | Phát hiện | Xử lý |
|---|---|---|
| E1 | Gate 12 ghi "no prior instance found" sau vài truy vấn | Sửa thành "không tìm thấy trong các truy vấn đã làm (liệt kê)"; cần tìm kỹ hơn trước khi nộp |
| E2 | "Hiệu chuẩn chặt ≈ α" là của phép thử trần CMS-T; luật đề xuất (có dừng SH) dùng 0.04–0.97·α | Viết rõ trong báo cáo |

## F. Kết quả sau khi sửa

Xem `paper/BAO_CAO_E29.pdf` (bảng tính lại bằng null phản thực chính xác, luật CMS-CPCW, cổng điều hướng +NGR, khoảng tin cậy).
