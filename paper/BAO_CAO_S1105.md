# Báo cáo phiên 2026-11-05 (chiều) — engine GPU, Entry 16 (âm), tính tổng quát và so sánh SOTA của OWF-HWA-S5, Entry 17

*Branch `hmm-2nd-idea`. Nhật ký đầy đủ: `RESEARCH_LOG.md` Entry 16–17. Số liệu thô: `analysis/results/owf/s1105/`. Không tuyên bố novelty A\* hay vượt SOTA
ngoài những gì các bảng dưới chứng minh trên đúng giao thức này.*

## 1. Tóm tắt

1. **Engine GPU cho bộ lọc thế giới mở** (`analysis/owf_torch.py`, `owf.py --engine torch`). Cả ngân hàng bộ lọc (q × tỉ lệ odometry) chạy
   trong một tensor float64 trên một L4. Tốc độ 2.7–3.4 ms/frame cho 10 bộ lọc, so với 29 ms/frame numpy, tức nhanh khoảng 10×. Quyết định
   trùng bản numpy ở mọi ngưỡng. Nhờ vậy cả tập phát triển + các tập tổng quát (657 run) chạy trong 35 phút trên 6 phiên 4×L4, với GPU thật
   sự được dùng (6 job / GPU) thay vì dùng phiên L4 như máy CPU.
2. **Entry 16 (âm, dừng ở phát triển).** Thay các bậc ngưỡng cố định của luật khuyến nghị bằng ngưỡng conformal mà mỗi lần triển khai tự
   hiệu chuẩn trên null hồi cứu của chính nó (Mệnh đề 4) cho kết quả KÉM HƠN trên cả ba trục (tập A 399 run): recall −0.017 … −0.027,
   23–46 run vượt α so với 1, sai số điều hướng +2 … +4.6 m. Nguyên nhân: bảo đảm biên ở mức α không kiểm soát đuôi theo run, còn luật
   khuyến nghị vận hành thấp hơn α khoảng 10 lần. Hai biến thể nhỏ (tầng theo tuổi bằng chứng, β chọn theo evidence) cũng âm.
3. **Tính tổng quát của OWF-HWA-S5** trên các tập chưa từng dùng để chỉnh luật: lỗ 10 %, lỗ 50 %, off-map tự nhiên 4Seasons chéo cảnh,
   NCLT. Luật hợp lệ trung bình trên mọi dataset; recall 0.78–0.95.
4. **So sánh SOTA ngoài trên cùng run** (TAO'26, Xu'21, Claxton'24; ngưỡng chỉnh bằng NHÃN như trong các bài báo). TAO'26 và Claxton'24 vượt
   α trên phần lớn run; Xu'21 hợp lệ hơn nhưng recall thấp hơn 0.29. OWF-HWA-S5 là luật duy nhất vừa hợp lệ vừa có recall cao, và vượt cả
   oracle một-frame (chỉ báo khi top-1 đúng) 0.06–0.13.
5. **Entry 17 (đăng ký trước 16:42 UTC), XÁC NHẬN.** Trên nhóm seed mới 55–57:
   - OWF-HWA-S5: 0.937, 1/144 run > α, 12.5 m;
   - HSI-VN: 0.806;
   - TAO'26 / Xu'21 / Claxton'24: vượt α trên 129 / 75 / 99 run.

## 2. Engine GPU

Mọi bước của bộ lọc là phép toán phần tử / gather / tích chập nhỏ trên tensor (bộ lọc × lưới). Các phép đó là:
- dịch nguyên ô (zero-fill);
- làm mờ Gauss bằng hai tích chập 1-D zero-padded, cùng kernel chuẩn hoá như `scipy.ndimage.gaussian_filter(mode="constant",
  truncate=3)`;
- mặt nạ band, kidnap / Ω;
- cập nhật LR bằng scatter-add;
- khối lượng đĩa excl quanh 12 ô nặng nhất.

Phần chỉ phụ thuộc odometry được tính trước trên CPU: pha, số ô dịch, thời điểm làm mờ, trọng số bằng chứng. Dtype float32 của log-LR được
giữ đúng như bản numpy.

Kiểm tương đương:
- Nordland (1-D), old town, CMU (2-D): vị trí báo trùng; quyết định trùng ở 1−0.2 … 1−1e-8; đường cong vận hành CMU trùng.
- |Δ khối lượng| ≤ 1e-4 (1-D) và ≤ 7e-7 (2-D), do khác biệt 1-ulp của `exp` float32 giữa numpy và torch.

## 3. Entry 16 — vì sao hiệu chuẩn conformal không thay được các bậc cố định

**Chẩn đoán.** Trên Nordland, giả thuyết tự tin nhưng sai của OWF nằm sâu trong lỗ: ≥ 32 excl từ đầu chuỗi, 82 % frame off-map, kéo dài
trung vị 2.3 excl, đạt khối lượng 1 − 1e-10. Đây là aliasing liên tiếp, vi phạm giả định e-value (E1) của cận Ville (Mệnh đề 2).

**Thiết kế (Mệnh đề 4, `owf_theory.md` §6).**
- Điểm = −log10(1 − khối lượng đĩa OWF).
- Ngưỡng theo tầng quãng đường từ đầu chuỗi = phân vị conformal (1 − α) của cực đại điểm trên các đoạn null hồi cứu (H = 10 frame) giữ ra.
  Hiệu chuẩn chung với nhánh OWF-H.
- Cầu hồi cứu dựng từ chuỗi tô-pô, độc lập với OWF, để tránh việc track của chính OWF tự chứng nhận nó.

**Kết quả phát triển (tập A, 399 run).** Ô = recall / TB segFAR / run > α / sai số điều hướng (m):

| Biến thể | Gộp |
|---|---|
| INC (OWF-HWA-S5) | **0.933 / 0.0045 / 1 / 12.7** |
| HC3 | 0.912 / 0.0158 / 41 / 17.0 |
| HC5a | 0.906 / 0.0172 / 23 / 14.7 |
| HC1 | 0.916 / 0.0144 / 31 / 16.6 |
| C3 (không có nhánh OWF-H) | 0.684 / 0.0151 / 42 / 27.0 |

**Bài học.**
- Bảo đảm biên theo đoạn ở mức α đúng, nhưng không kiểm soát đuôi theo run.
- Các đợt aliasing là thiểu số trong null, nên phân vị bỏ qua chúng.
- Muốn kiểm soát đuôi theo run phải hiệu chuẩn ở mức thấp hơn nhiều, và khi đó recall còn mất nhiều hơn.
- Biến thể bậc (bỏ điều kiện quãng đường; 2 hằng số thay cho 6): recall ±0.005 và thêm run vượt α. Lớp quyết định đã bão hoà.

## 4. Tính tổng quát và SOTA ngoài trên cùng run

Ô = recall gộp / TB segFAR / số run > α.

| Tập | OWF-HWA-S5 | HSI-VN | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|---|
| lỗ 10 % (108) | **0.933** / 0.002 / 1 | 0.772 / 0.000 / 0 | 0.843 / 0.554 / 92 | 0.646 / 0.077 / 35 | 0.737 / 0.288 / 86 | 0.827 |
| lỗ 50 % (108) | **0.894** / 0.009 / 4 | 0.754 / 0.006 / 4 | 0.842 / 0.535 / 93 | 0.609 / 0.129 / 30 | 0.678 / 0.090 / 60 | 0.829 |
| off-map tự nhiên (36) | **0.952** / 0.010 / 2 | 0.742 / 0.004 / 0 | 0.578 / 0.075 / 4 | 0.581 / 0.037 / 10 | 0.678 / 0.020 / 5 | 0.822 |
| NCLT (6) | **0.781** / 0.005 / 0 | — | 0.756 / 0.713 / 6 | 0.526 / 0.021 / 1 | 0.663 / 0.213 / 5 | 0.724 |

Các run vượt α của OWF-HWA-S5 (CMU khi lỗ 50 %; 2 run off-map tự nhiên) đều trùng với nhánh HSI của nó (OWF-H). Bảng đầy đủ theo dataset:
`analysis/results/owf/s1105/sota_*.md`.

**Khoảng trống còn lại (chẩn đoán, tập A).**
- CMU: OWF đúng 0.95–0.99 frame on-map ở mọi khoảng cách từ đầu chuỗi, nhưng chỉ 0.53–0.94 được báo. Phần bị bỏ = 0.125, nằm ở quyết định
  đầu chuỗi.
- Countryside: khoảng trống nằm ở chuỗi dài; khối lượng trung vị của frame đúng bị bỏ chỉ 0.70, tức bộ ước lượng chưa đủ sắc dưới VIO trôi.
- Sai số điều hướng đến từ dead-reckoning trong lỗ, không từ độ chính xác fix (trung vị 2.3–2.5 m).

**VPR-Space (Entry 18, mô tả; 16 setup ngoài Trái Đất × 6 descriptor, off-map tự nhiên, giao thức theo thang τ của benchmark).**
- OWF-HWA-S5 hợp lệ (0/96 run > α) nhưng recall 0.292, thấp hơn oracle một-frame 0.562.
- Đối thủ: TAO'26 0.629 (24 run > α); Xu'21 / Claxton'24 (chỉnh bằng nhãn trên chính chuỗi) 0.498 / 0.441.
- Bộ ước lượng OWF tổng quát tốt: MAP đúng 0.70–1.00 frame on-map, vượt xa top-1 một-frame.
- Lớp quyết định thì không: HSI không khởi động trên chuỗi 54–1683 frame, các bậc cần ≥ 2–16 excl.
- OWF đơn lẻ không báo sai ở MỌI ε (0.733 ở ε = 0.2): K ≈ 0 ở đây, so với 10³–10⁴ trên CMU/Nordland, nên ε cố định không hợp cả hai.
- Không chọn ε sau khi xem số liệu. Hướng tiếp: cận K theo bản đồ (`03` §6a).

## 5. Entry 17 — xác nhận trên seed 55–57 (đăng ký trước 16:42 UTC)

**XÁC NHẬN: C1–C4 đều đạt** (144 run mới; mọi luật chạy trên CÙNG run). Ô = recall gộp / TB segFAR tệ nhất / run > α / sai số điều hướng (m):

| Luật | Gộp 144 run |
|---|---|
| **OWF-HWA-S5** | **0.937** / 0.013 / **1** / **12.5** |
| HSI-VN | 0.806 / 0.008 / 0 / 15.0 |
| TAO'26 | 0.846 / 0.996 / 129 / 123.5 |
| Xu'21 | 0.691 / 0.600 / 75 / 57.5 |
| Claxton'24 | 0.732 / 0.268 / 99 / 48.4 |
| oracle một-frame | 0.847 / 0 / 0 / 10.9 |

- C2: +0.131 so với HSI-VN, CI [+0.114, +0.150].
- C3: cả ba đối thủ ngoài đều không hợp lệ.
- C4: 12.5 vs 15.0 m.
- Recall vượt oracle một-frame +0.090. Ngoại lệ CMU: 0.841 vs oracle 0.929, khoảng trống đầu chuỗi.
- Bảng theo dataset: `analysis/results/owf/s1105/e17_board_s55_57.md`.

## 6. Hạn chế và việc tiếp theo

- Phần quyết định của hệ vẫn là bậc ngưỡng cố định, có biện minh thực nghiệm (bền trên lỗ 10/50 %, off-map tự nhiên) nhưng chưa có mệnh đề
  kiểm soát đuôi theo run.
- Nhánh HSI là nguồn của đuôi hợp lệ còn lại (CMU khi lỗ 50 %).
- VPR-Space (16 cặp ngoài Trái Đất) chưa chạy. Repo `rfechner/vpr-space` đọc được (danh sách setup trong `dataset.py`); proxy của phiên chặn
  API release. Kernel CPU có internet (`dinhthinh/vprspace-fetch`) liệt kê release v0.1.0: 11 phần `vpr-space.tar.0000–0010`, tổng 20.3 GB,
  lớn hơn đĩa làm việc của một kernel (20.9 GB) nếu vừa lưu vừa giải nén. Hướng khả thi:
  - stream `curl … | tar x` lọc theo từng quỹ đạo trong kernel CPU có internet, thu nhỏ ảnh vào output (< 19 GB);
  - kernel L4 cùng tài khoản mount output đó (`kernel_sources`), trích 6 descriptor.
- Paper: bản nháp tiếng Anh `paper/OWF_paper_draft.md`; phần kết quả lấy từ các entry đăng ký trước.
