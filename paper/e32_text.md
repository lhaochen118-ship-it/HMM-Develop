# Báo cáo vòng 9: độ nhạy, thời gian chạy, off-map tự nhiên sát bản đồ, đối thủ mới, hiệu chuẩn lối thoát (CST) và Oxford RobotCar

*Branch `hmm-navigation-5`, 2026-11-01. Nhật ký `RESEARCH_LOG.md` Entry 32–34 (đăng ký trước, push trước đánh giá). Tài liệu:
`literature/RELATED_WORK_E32.md`, `LITERATURE_GATE.md` Gate 15. Vòng trước: `paper/BAO_CAO_E30.pdf`.*

**Tóm tắt.**

- **Độ nhạy (366 run × 14 biến thể).** 12/14 hằng số chọn tay đổi recall ≤ 0.03 và giữ segFAR ≤ α trên 7/7 dataset, recall
  vẫn > CPC-SC-T½+SH trên 7/7. Ngoại lệ duy nhất: **dung sai hình dạng SH** (× 2 làm vỡ α ở CMU 0.071 và 4S countryside 0.100;
  × 0.5 mất recall). Dựng null phản thực (N, ρ; 42 run mỗi biến thể): hợp lệ 7/7 với mọi biến thể; cửa sổ niềm tin N = 40 tăng
  recall 0.015–0.027.
- **Thời gian chạy:** ~20 ms/frame (top-300 GPU 0.01–0.05 ms, thống kê phản thực 10–17.5 ms, lớp quyết định 1.7–2.8 ms) ⇒ thời gian
  thực 10 Hz trên một nhân CPU. Ngưỡng đăng ký trước (< 10 ms và < 1 ms) **không đạt**; báo cáo trung thực.
- **Off-map tự nhiên sát bản đồ (NCLT, mỗi phiên làm bản đồ, 9 bản đồ, 48 run):** luật đề xuất hợp lệ trên mọi bản đồ (segFAR gộp
  0.007, 0 % run > α) và recall cao hơn CPC-SC-T½+SH trên 9/9 bản đồ; các biến thể nhân quả cũng 9/9.
- **Đối thủ mới đọc toàn văn (E33, 366 run):** SU'25, SUE'24 (cả bản hiệu chuẩn theo đoạn có nhãn, có lợi nhất cho họ) và
  Carson'23 hoặc vi phạm α (segFAR 0.19–0.99) hoặc hợp lệ nhưng recall 0.09–0.39 so với 0.49–0.82 của ta: H33a đạt 7/7.
  Dung sai SH hiệu chuẩn theo phân vị frame (SHcf) hợp lệ 7/7 nhưng recall chỉ sát SH trên 4/7: H33b không đạt.
- **Cơ chế mới (E34) — phẫu thuật cũng hiệu chuẩn lối THOÁT:** chẩn đoán cho thấy lỗi còn lại của phương pháp không nằm ở khởi phát
  (đã có Định lý 6) mà ở **duy trì** chuỗi báo khi robot rời bản đồ. Phép thử hình dạng phản thực theo đoạn (CST, Mệnh đề 14,
  Hệ quả 15) cho bảo đảm đầu-cuối theo đoạn mà không còn hằng số dung sai. Kết quả 366 run: CST hợp lệ 7/7, recall trong ±0.02 so với SH chọn tay trên 7/7 (cao hơn trên 6/7, +0.003 đến +0.022), bản nhân quả hợp lệ 7/7; nhân đôi mức a_sh **vẫn hợp lệ 7/7** trong khi nhân đôi dung sai SH làm vỡ α ở 2/7. Cái giá: 6 % run vượt α (SH: 0.5 %) và — kiểm định cặp — sai số điều hướng **tăng** có ý nghĩa ở Boreas (+9.0 m) và 4S old town (+13.6 m): CST cho lọt vài fix sai ở mép chuyến off-map (ngoài Mệnh đề 14) mà SH chặn. Entry 35 (đang chạy) thử SH ∧ CST: bảo đảm từ CST, bảo vệ từ SH.
- **Dataset uy tín mới: Oxford RobotCar** (PointNetVLAD split, 43 lượt chạy, 34 039 frame, 6 descriptor, 30 % lỗ bản đồ). Baseline null-bản-đồ (CPC-SC) **suy biến ở 36/60 run** (bản đồ ~670 frame sau khi khoét lỗ không đủ đoạn null để có phân vị α hữu hạn — đúng Hệ quả 9); CMS hiệu chuẩn được ở **mọi** run (null từ luồng truy vấn): recall 0.719 / segFAR 0.003 / 0 % run vượt α (CPCW: 0.753 / 0.006). Trên 24 run null bản đồ còn chạy được, CMS-CPCW ngang recall (+0.008) với sai số thấp hơn ở 19/24; mọi baseline có nhãn vượt α (Xu'21 100 % run, TAO'26 93 %, Claxton'24 72 %).

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

- **Một bộ theo dõi duy nhất.** ~80 tiến trình theo dõi song song (mỗi kernel một tiến trình) làm Kaggle chặn API **theo IP**
  (mọi acc, kể cả acc mới). Thay bằng `automation/central_monitor.py`: một hàng đợi API (≥ 60–90 s giữa hai lệnh, nghỉ 30 phút khi
  bị chặn, gom lệnh theo acc, `--pull-first` cho kernel chắc chắn đã xong), có xếp lịch: kernel mới vào acc đầu tiên còn slot đúng
  loại (2 GPU / 5 CPU), tối đa 8 acc, bớt 1 acc mỗi lần bị chặn; reset hàng đợi 8/10 phút × 5, L4 kẹt ⇒ kiểm lỗi code (NEEDS_FIX)
  hoặc tự chuyển 2 × T4. Ba kernel GPU "mất tích" (lần đẩy lại bị từ chối vì acc cũ đã đủ 2 phiên GPU) được phát hiện và chạy lại.
- **Đánh giá lớp quyết định chạy local.** Mọi cache (navcache, top-K, thống kê phản thực, route) của 366 run có sẵn ở máy, nên các
  thí nghiệm chỉ đổi lớp quyết định (E34: 366 run) chạy trên 4 nhân CPU local, ~45–110 s/run, **không tốn API hay phiên Kaggle**.
- **Oxford chạy local** từ dump (2.1 GB) kéo về từ kernel tạo dump: tránh việc đăng / tải lại qua API.
- **Bài học:** tải đầu ra kernel có hàng nghìn file (ảnh) tốn một request mỗi file và gây chặn API — đầu ra lớn phải đóng gói tar.

## 4. Bảng kết quả

![Validity vs recall](fig_validity_recall.png)

*Hình 1. Mặt phẳng hợp lệ–recall (trung bình theo dataset). Vùng xanh: segFAR ≤ α. CMS (xanh dương) hợp lệ và có recall cao nhất trong các luật hợp lệ trên cả 8 dataset; baseline có nhãn (cam) vượt α hoặc mất 40–70 % recall; null bản đồ (xanh lá) suy biến trên Oxford.*

{{TABLES}}

### Đối thủ mới (Entry 33, 366 run)

{{TABLES33}}

### Phép thử hình dạng phản thực CST và Oxford RobotCar (Entry 34)

{{TABLES34}}

## 5. Đọc kết quả

1. **Phương pháp không phụ thuộc vào việc chọn hằng số — trừ đúng một chỗ.** Mười hai hằng số của lớp quyết định và hai tham số
   dựng null đều có thể đổi trong khoảng ×0.5–×2 mà bảo đảm và ưu thế giữ nguyên. Chỗ duy nhất nhạy là dung sai hình dạng SH, và
   chẩn đoán E34 giải thích vì sao: SH là cơ chế **duy nhất** chặn lỗi duy trì (chuỗi báo mang từ bản đồ vào vùng off-map, 13–62 %
   báo sai off-map khi bỏ SH, phần lớn ở độ sâu ≥ 20 frame), một phần mà Định lý 6/6′/6″ không phủ.
2. **Ưu thế không đến từ việc chọn dataset.** Trên off-map tự nhiên sát bản đồ (NCLT, 9 bản đồ) và trên 7 dataset với 6 descriptor,
   luật đề xuất là luật duy nhất vừa hợp lệ vừa có recall cao nhất trong các luật hợp lệ; mọi baseline có nhãn mới đọc (SU'25,
   SUE'24, Carson'23) hoặc vi phạm α hoặc mất 40–70 % recall.
3. **Điều chưa đạt.** H32b (ngưỡng thời gian đặt trước) và H33b (SHcf) không đạt; cả hai được ghi như kết quả âm.
4. **Novelty vòng này: phẫu thuật bản đồ hiệu chuẩn cả lối thoát.** Chẩn đoán (cache chính xác) cho thấy lỗi còn lại của phương
   pháp là *duy trì* chuỗi báo sau khi rời bản đồ, không phải khởi phát. Quỹ đạo phản thực MP[j_cf] sai theo cấu trúc, tức là null
   của "quỹ đạo ma" sau khi thoát. Phân vị conformal dưới của residual hình dạng tối thiểu theo đoạn cho một phép dừng có bảo đảm
   (Mệnh đề 14, Hệ quả 15). Báo sai cần **cả** chuỗi báo **và** qua CST (giao biến cố), nên tỷ lệ báo sai theo đoạn sâu ≤ a_sh/π.
   Kết quả 366 run xác nhận: hợp lệ 7/7, recall giữ nguyên hoặc tăng nhẹ (CI > 0 trên 5/7), và mức a_sh hành xử như một *mức*
   (×2 vẫn hợp lệ) chứ không như một *dung sai* (×2 vỡ). **Nhưng** CST làm tăng sai số điều hướng ở Boreas (+9.0 m) và old town
   (+13.6 m): bảo đảm theo đoạn (segFAR) không đồng nghĩa với an toàn điều hướng — vài fix sai ở mép chuyến off-map đủ làm lệch bộ
   lọc. Vì vậy CST một mình **không** thay được SH trong luật khuyến nghị; xem Entry 35 (SH ∧ CST).
5. **Oxford RobotCar minh hoạ đúng luận điểm cốt lõi của bài.** Null lấy từ bản đồ cần bản đồ đủ lớn; với bản đồ nhỏ nó suy biến
   (36/60 run không báo gì). Null phản thực lấy từ luồng triển khai nên luôn đủ mẫu. Khi null bản đồ còn chạy được, ưu thế recall
   của CMS trên Oxford nhỏ (+0.008 cho CPCW, −0.026 cho luật có +G). Ưu thế thật là độ bền và sai số thấp hơn.
6. **Một lỗi quy trình đã được bắt và sửa.** Lần chạy E34 đầu tiên trên máy local dùng nhầm cache thống kê phản thực xấp xỉ (Entry 28).
   Lỗi được phát hiện vì luật SH cho số khác Kaggle. Toàn bộ E34 đã chạy lại trên cache chính xác, và cache này tái lập kết quả
   Kaggle tới 4 chữ số. Kết quả trên cache sai không được dùng.

## 6. Việc tiếp theo

1. **Phẫu thuật "tiến" cho đoạn ở mép chuyến off-map** (độ sâu < N): chỉ xoá anchor sau một thời điểm thoát ảo t₀ để có null cho
   cửa sổ chồng một phần lên bản đồ ⇒ đóng khoảng trống cuối của Mệnh đề 14 (CMU s0: 94/126 báo sai còn lại của CST nằm trong 20
   frame đầu chuyến off-map). Cần top-300 (Kaggle GPU) và ~1× chi phí thống kê hiện tại.
2. **Cửa sổ niềm tin N = 40** tăng recall 0.015–0.027 trên seed 0 mà không đổi tính hợp lệ (E32): kiểm xác nhận trên seed 1–9
   (giữ ra, không dùng để chọn) trước khi đổi mặc định.
3. **Vector hoá thống kê phản thực** (vòng lặp Python, 10–17 ms/frame) ⇒ < 1 ms/frame; điều kiện để chạy phẫu thuật tiến ở quy mô 366 run.
4. **Bài báo:** bản nháp `paper/cms_paper_draft.md` (tiếng Anh) đã có cấu trúc, định lý, bảng chính, hình `paper/fig_validity_recall.png`;
   còn thiếu: chứng minh đầy đủ ở phụ lục, so sánh trực tiếp với SafeVPR'26 trên cùng split (họ dùng Oxford/NCLT/St Lucia), St Lucia.
