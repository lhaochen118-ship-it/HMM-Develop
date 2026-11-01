# Báo cáo vòng 9: độ nhạy, thời gian chạy, off-map tự nhiên sát bản đồ (NCLT) và định vị novelty

*Branch `hmm-navigation-5`, 2026-11-01. Nhật ký `RESEARCH_LOG.md` Entry 32 (đăng ký trước, push trước đánh giá). Tài liệu:
`literature/RELATED_WORK_E32.md`, `LITERATURE_GATE.md` Gate 15. Vòng trước: `paper/BAO_CAO_E30.pdf`.*

**Tóm tắt.**

{{SUMMARY}}

## 1. Câu hỏi của vòng này

| # | Câu hỏi reviewer sẽ hỏi | Thí nghiệm |
|---|---|---|
| 1 | Kết quả có phụ thuộc các hằng số chọn tay (H, W, trọng số trộn, chuyển trạng thái, bán kính +G, dung sai SH, β, R, N, ρ)? | Đổi từng hằng số quanh mặc định trên 366 run (lớp quyết định) và 42 run (dựng null phản thực) |
| 2 | Chạy thời gian thực được không? | Đo thời gian từng bước trên phiên Kaggle L4 (top-300 GPU, thống kê phản thực và lớp quyết định CPU) |
| 3 | Off-map tự nhiên **sát** bản đồ (đi lệch sang lối bên cạnh) — benchmark tự nhiên của vòng 8 là off-map "xa" (thành phố khác) | NCLT, mỗi phiên làm bản đồ một lần (9 bản đồ × 6 descriptor): 6–13 % frame truy vấn tự nhiên ngoài bản đồ > 20 m |
| 4 | Công trình nào đã làm việc này? | Tìm có hệ thống 20 truy vấn, 6 nhánh |

**Dữ liệu đã kiểm và loại cho câu 3:** MSLS val (Copenhagen, San Francisco): 98.8–99.7 % query có database trong 25 m — gần như
không có off-map tự nhiên; 4Seasons trong cùng cảnh: 0 frame off-map tự nhiên (các bản ghi đi cùng tuyến).

## 2. Định vị novelty (việc 3)

Chi tiết và nguồn: `literature/RELATED_WORK_E32.md`. Tóm tắt:

| Nhánh | Gần nhất | Khác với ta ở đâu |
|---|---|---|
| Integrity VPR | Carson–Ford–Milford RA-L'22 / ICRA'23; Claxton'24; SMR (IROS'25); **SafeVPR'26** | Có nhãn (hoặc không có bảo đảm); SafeVPR có bảo đảm conformal nhưng cần tập hiệu chuẩn có nhãn và tự nêu là vỡ khi lệch điều kiện |
| Off-map / nơi mới | **Xu'21** (trạng thái off-map trong bộ lọc topometric); Multi-Process Fusion; open-set recognition | Trạng thái off-map chỉnh tay / theo nhãn, không bảo đảm; open-set: tác giả nêu hiệu chuẩn "chưa được nghiên cứu" |
| Ngưỡng không nhãn | **Lee & Pollefeys ICRA'14** (hỗn hợp số inlier); self-supervised domain calibration (pose graph) | Không có null, không bảo đảm; suy biến khi ít vòng lặp — đúng trường hợp null phản thực xử lý |
| Phát hiện thay đổi tuần tự | **E-detectors** (Shin–Ramdas–Rinaldo); Vovk conformal change detection; **e-value monitor cho particle filter (arXiv 2604.26479)** | Cần lớp trước/sau định trước hoặc null hoán đổi của chính dữ liệu; monitor 2604.26479 kiểm độ tự tin của bộ lọc, không kiểm "đang trên bản đồ" |
| Conformal dưới phụ thuộc | Zheng–Proutière ICML'24 (Markov, K-split); block / guard-band; β-mixing | Cần giả định mixing; ta dùng max theo đoạn (mọi phụ thuộc trong đoạn) + null sinh ra |
| Integrity / protection level | Gupta–Gao NAVI'21; Li–Waslander'19; Duenas Arana'19 (χ² tuần tự) | Mô hình lỗi; cổng +NGR của ta là bản rời rạc — **không** tuyên bố mới |

**Kết luận Gate 15.** Ba đóng góp không tìm thấy trong các truy vấn đã làm: (1) null của bằng chứng "đang trên bản đồ" sinh từ
luồng triển khai bằng phẫu thuật bản đồ quanh niềm tin của hệ thống; (2) cận khởi phát sai theo đoạn không nhãn, mọi phụ thuộc
trong đoạn, với tự-nhiễm định lượng α(n+1)/(πn+1) và bản nhân quả; (3) trạng thái off-map của HMM được hiệu chuẩn bởi null đó
(Mệnh đề 13). Mọi thành phần còn lại (HMM có off-map, conformal accept/reject, e-detector, cổng innovation) là đã biết và sẽ được
trích dẫn. Trước khi nộp còn phải đọc toàn văn SafeVPR, E-detectors, Vovk 2020, Lee–Pollefeys 2014, arXiv 2604.26479 và quét
proceedings RA-L / RSS / ICRA / IROS 2024–2026.

## 3. Tối ưu tính toán

{{OPS}}

{{TABLES}}

## 5. Đọc kết quả

{{READ}}

## 6. Việc tiếp theo

{{NEXT}}
