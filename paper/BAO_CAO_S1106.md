# Báo cáo phiên 2026-11-06 → 07 — Entry 19–28: không dịch chuyển tức thời, phủ quyết thế giới mở, bí danh mà odometry không thấy được, bằng chứng tuyệt đối hiệu chỉnh hồi cứu, kiểm toán

*Branch `hmm-2nd-idea`. Nhật ký đầy đủ: `RESEARCH_LOG.md` Entry 19–28. Lý thuyết: `paper/owf_theory.md` §8 (Mệnh đề 5), §9 (Mệnh đề 6), §10 (Mệnh đề 7), §11–12 (kiểm toán). Số liệu
thô: `analysis/results/owf/s1106/`. Báo cáo không tuyên bố novelty hay vượt SOTA ngoài những gì các bảng dưới chứng minh trên đúng giao thức này.*

## 1. Tóm tắt

0. **LUẬT KHUYẾN NGHỊ MỚI: OWF-HWA-S5-NT-HQ (Entry 23, đăng ký trước, seed 64–66).** Thay OWF-HWA-S5 theo đúng quy tắc (V1–V3 đạt):
   - TB segFAR 0.0074 → 0.0059; recall −0.0038 [−0.0071, −0.0010]; điều hướng 14.67 → 14.56 m (số chạy lại bằng mã đã kiểm toán, §4f).
   - CMU: recall +0.009, segFAR −30 %, điều hướng 8.5 → 7.1 m. Nordland: segFAR −44 %, điều hướng 7.5 → 4.1 m.
   - Biến thể có phủ quyết (C10, chỉ báo cáo): 0/144 run > α, TB segFAR 0.0024, recall −0.012.
   - Cơ chế: bằng chứng tuyệt đối cho ô trống, hiệu chỉnh hồi cứu không nhãn, nhân quả trong phiên (Mệnh đề 7).
   - **Entry 27 (kiểm toán, 2026-11-07):** sửa hai rò rỉ nhân quả trong mã HQ (`--lu hsq2`), chạy lại 432 + 399 + 258 run: mọi quyết định giữ nguyên (§4f).
   - **Entry 28 (kiểm toán lần hai):** nhánh HSI-VN nhìn trước trong nhãn hồi cứu → sửa `HSI-VNc`, kiểm thử đầu-cuối; chạy lại nhánh HSI mọi tập:
     mọi quyết định giữ nguyên, run > α 4 → 3/432 (§4g).
   - **Entry 24 xác nhận độc lập trên seed 67–69:** 0/144 run > α, +0.136 so với HSI-VN; TAO'26 / Xu'21 / Claxton'24 không hợp lệ.
1. **Luật cũ OWF-HWA-S5** đã được kiểm trên ba nhóm seed mới, đều đăng ký trước, mỗi nhóm 144 run (8 dataset × 6 descriptor):

   | Nhóm | Recall | TB segFAR | Run > α | Sai số điều hướng (m) |
   |---|---|---|---|---|
   | 55–57 (Entry 17) | 0.937 | 0.0045 | 1 | 12.5 |
   | 58–60 (Entry 19) | 0.934 | 0.0101 | 6 | 16.3 |
   | 61–63 (Entry 21) | 0.927 | 0.0043 | 2 | 12.9 |

   Tổng 9/432 run vượt α (2.1 %). 7 trong 9 là CMU, đến từ đúng hai bố cục lỗ.
2. **Entry 19 (đăng ký trước, seed 58–60): không dịch chuyển tức thời (NT, Mệnh đề 5).** Recall bằng (−0.001); TB segFAR 0.0101 → 0.0091;
   Nordland điều hướng 19.1 → 13.5 m. Không qua quy tắc, vì tiêu chí tuyệt đối "≤ 2/144 run > α" trượt với CẢ R* lẫn ứng viên (6 run mỗi bên).
3. **Entry 21 (đăng ký trước, seed 61–63): OWF phủ quyết nhánh HSI khi khối lượng gần bản đồ mN < ½.**
   - Hợp lệ tốt hơn: TB segFAR 0.0043 → 0.0033; Oxford 0.0068 → 0.0010.
   - Recall −0.005.
   - Điều hướng +0.9 m (countryside 26 → 35 m): trượt V3, R* giữ nguyên.
   - NT trên cùng nhóm: trượt N3 0.07 m.
4. **Phát hiện chính: bí danh mà odometry không thấy được.** Truy ngược các run vượt α: cả hai bố cục lỗ CMU đều phủ một đoạn đường mà ở chỗ
   khác trên bản đồ có một "bản sao dịch chuyển".
   - Độ lệch không đổi: (−188, −78) m ở seed 60 và (−652, +166) m ở seed 61, qua 10–17 lượt đi.
   - Hai descriptor độc lập chọn cùng chỗ.
   - Khớp yếu theo giá trị tuyệt đối (cos 0.34–0.45 so với 0.69–0.77 ở đúng chỗ), nhưng nhất quán với chuyển động.

   Mệnh đề 6: với emission chuẩn hoá theo hồ sơ của frame, ảnh được tăng khối lượng khi z > ≈ 0.5 SD. Vì vậy bản sao tích luỹ bằng chứng không
   giới hạn.
5. **Entry 22 (âm ở phát triển): điểm giao Gaussian-shift μ₁/2 cho ô trống.** Cơ chế được xác nhận: báo sai CMU của OWF đơn lẻ ÷ 4.6; run
   thiết kế CMU s60 từ 17 → 0 đoạn sai, sai số 6.8 → 2.7 m. Nhưng một điểm giao chung cho cả run làm recall hệ đầy đủ giảm 3 pp và Nordland tệ
   hơn. Loại ở phát triển; seed 64–66 để dành, rồi dùng cho Entry 23.
6. **Entry 20 (âm ở phát triển): độ dài bằng chứng ℓ = chiều dài tương quan thị giác của bản đồ.** Recall −0.029, 13 run > α.

## 2. Entry 19 — không dịch chuyển tức thời (Mệnh đề 5)

Bộ lọc cũ đưa khối lượng của trạng thái xa Ω quay lại lưới theo prior khởi đầu: mỗi frame, mọi ảnh bản đồ nhận một hạt giống nhỏ. Một đợt
aliasing liên tiếp (độ phóng đại K tới 10¹⁰, Mệnh đề 2′) biến hạt giống thành chắc chắn. NT làm Ω hấp thụ (`owf.py --pin 0`), tương đương
re-entry qua rìa band. Trên run thiết kế Nordland, số báo sai ở 1 − 1e-8 giảm 22 → 0.

| Seed 58–60, 144 run | R* | NT |
|---|---|---|
| recall gộp | 0.934 | 0.933 |
| TB segFAR | 0.0101 | 0.0091 |
| run > α | 6 | 6 |
| điều hướng (m) | 16.3 | 15.6 |

Cả R* cũng có đúng 6 run > α: 4 CMU (seed 60, từ nhánh HSI), 1 countryside, 1 St Lucia. Tiêu chí N1 lẽ ra phải tương đối với một thay đổi chỉ
chạm bộ ước lượng. Quy tắc không được sửa sau khi xem kết quả; Entry 21 viết N1 tương đối trước khi xem nhóm mới.

## 3. Entry 21 — bộ lọc thế giới mở phủ quyết nhánh thế giới đóng

Nhánh HSI không có trạng thái "ngoài bản đồ"; OWF thì có. Luật C2: HSI chỉ được báo nơi OWF cho rằng robot ở gần bản đồ nhiều khả năng hơn là
không (mN ≥ ½, quyết định Bayes dưới mất mát 0–1).

Phát triển, tập A, 399 run, so với R* trên cùng run:
- recall −0.0044;
- TB segFAR 0.0045 → 0.0025;
- run > α 1 → 0.

| Seed 61–63, 144 run | R* | C1 = NT | C2 = NT + phủ quyết |
|---|---|---|---|
| recall | 0.927 | 0.926 | 0.922 |
| TB segFAR | 0.0043 | 0.0043 | **0.0033** |
| run > α | 2 | 2 | 2 |
| điều hướng (m) | 12.9 | 13.0 | 13.8 |
| countryside điều hướng (m) | 26.0 | 25.8 | **34.6** |

Đọc:
- Ở countryside, VIO trôi làm hậu nghiệm OWF loang (mN thấp), nên phủ quyết bỏ cả các fix HSI đúng.
- 2 run CMU > α không đến từ HSI (H(R*) = 0 run > α), nên phủ quyết không chạm được chúng.
- Hai run đó đến từ bậc đồng thuận ba nguồn, ở đầu chuỗi trong lỗ: OWF, chuỗi tô-pô và top-1 cùng chỉ vào một bản sao dịch chuyển.

## 4. Bí danh mà odometry không thấy được (Mệnh đề 6)

![Bí danh dịch chuyển trên CMU](figures/owf_shifted_alias.png)

*Trái: CMU seed 60 (CosPlace).*
- Xám: ảnh bản đồ của run.
- Xanh: truy vấn trong lỗ bị báo sai.
- Đỏ: ảnh được báo.

*Giữa / phải: z và độ tương đồng thô.*
- Xanh lá: z / cos của đúng chỗ, bản đồ đầy đủ (seed 58).
- Đỏ: z / cos của khớp tốt nhất trong lỗ (bí danh).
- Theo z hai phân bố chồng nhau; theo cos thì tách được.

Lập luận:
- Bản sao là quỹ đạo thật dịch dọc chính con đường. Odometry không phân biệt được hai quỹ đạo, nên tỉ số hậu nghiệm chỉ do emission quyết
  định.
- Emission hiện tại cho ảnh i log-LR β z_i − A_t, với A_t = log mean_j exp(β z_j). Với β = 1, điểm giao so với ô trống là z ≈ 0.5.
- Bí danh có z trung vị ≈ 4.1 mỗi frame, nên tích luỹ khoảng e^3.6 mỗi frame. Không ngưỡng quyết định nào cứu được, vì khối lượng của bản sao hội tụ về 1.
- Mô hình dịch Gaussian (khớp đúng ~ N(μ₁, 1)), làm mềm về cùng độ dốc, cho điểm giao μ₁/2.

| CMU, 399 run phát triển | R* | NT | NT + LU (μ₁/2) |
|---|---|---|---|
| OWF đơn lẻ, ε = 1e-3: TB segFAR | — | 0.036 | **0.008** |
| OWF đơn lẻ: recall | — | 0.767 | 0.691 |
| hệ đầy đủ: run > α | 1 | 2 | 0 |
| hệ đầy đủ: điều hướng (m) | 4.4 | 4.4 | 3.9 |

Cái giá, đã dự báo trong §9 trước đợt phát triển:
- Các frame trên bản đồ có z thật < μ₁/2 (mùa đông, quay đầu, che khuất) đẩy khối lượng ra ngoài bản đồ.
- Recall office / old town / Boreas giảm 11–12 pp (OWF đơn lẻ).
- Nordland báo sai TĂNG (0.018 → 0.046): hậu nghiệm mất vết, rồi bắt lại ở chỗ giống.
- Hệ đầy đủ: recall −0.030, điều hướng +3.4 m.

Mô hình có phương sai (σ₁ ≈ 2–3) hạ điểm giao về ≈ 2, thấp hơn z của bí danh. Vậy trong không gian z, khớp đúng yếu và bí danh chồng nhau.
Thông tin tách được nằm ở độ tương đồng tuyệt đối (cos ở đúng chỗ, phân vị 5 % = 0.54, so với trung vị bí danh 0.44), và chuẩn hoá z theo frame đã bỏ nó đi.

Phủ quyết bằng bộ lọc LU (quyết định vững trên hai mô hình emission, Entry 22b):
- hợp lệ nhất từng đo trên tập A: TB segFAR 0.0012–0.0018, 0 run > α;
- nhưng recall giảm 2.6–4.5 pp.

## 4b. Entry 23 — bằng chứng tuyệt đối cho ô trống, hiệu chỉnh hồi cứu theo phiên (Mệnh đề 7)

Entry 22 cho thấy thông tin tách khớp đúng khỏi bí danh nằm ở độ tương đồng tuyệt đối, không ở z. Mô hình quan sát đúng là trên **max của
frame** x_t = max s − median s:
- trên bản đồ, x_t = max(đúng chỗ, bí danh tốt nhất), mật độ f_on;
- ngoài bản đồ, x_t = bí danh tốt nhất khi đúng chỗ vắng mặt, mật độ f_off.

Ô trống nhận log-LR log f_off(x_t) − log f_on(x_t).

Hai mật độ ước lượng **không nhãn** từ các fix tự tin của lượt 1 (bộ lọc cũ):
- f_on: max của frame;
- f_off: max trên ảnh xa hơn 1.6 excl khỏi fix.

Đây là "bí danh khi đúng chỗ bị loại", cùng điều kiện, cùng descriptor, cùng bản đồ. Trên CMU s60, trung vị bí danh hồi cứu 0.469 khớp bí danh
thật trong lỗ 0.445.

**Nhân quả:** lượt 1 không phụ thuộc lượt 2. Frame t dùng mẫu của chính phiên ở frame < t khi đã đủ 100 mẫu, trước đó dùng các phiên khác.

Tính chất (Mệnh đề 7):
- ngoài bản đồ, giả thuyết "trên bản đồ" mất bằng chứng với tốc độ KL(f_off ‖ f_on);
- ở điều kiện mà đúng chỗ không nổi bật (đêm, đoạn lặp dài), f_on ≈ f_off nên LR ≈ 1 và bộ lọc tự lùi về bộ lọc cũ.

Bài học từ các biến thể thất bại trên run thiết kế: hiệu chỉnh từ phiên khác (leave-one-session-out) làm sập phiên đêm old town (0.72 →
0.11–0.32), vì cos đúng chỗ ban đêm (0.20 trên nền) thấp hơn bí danh ban ngày (0.30). Chỉ hiệu chỉnh trong chính phiên mới đúng điều kiện.

**Phát triển (tập A, 399 run, cùng run với R*):**

| | R* | C9 = NT + HQ | C10 = C9 + phủ quyết |
|---|---|---|---|
| recall gộp | 0.933 | 0.929 | 0.923 |
| TB segFAR | 0.0045 | **0.0034** | **0.0013** |
| run > α | 1 | **0** | **0** |
| điều hướng (m) | 12.7 | 13.0 | 12.8 |
| CMU recall / segFAR | 0.852 / 0.0095 | **0.863 / 0.0066** | 0.854 / 0.0037 |
| Nordland recall / segFAR | 0.968 / 0.0069 | **0.970 / 0.0026** | 0.969 / 0.0026 |

Cái giá nằm ở đầu các phiên có điều kiện khác hẳn (đêm 4Seasons), trước khi phiên đủ mẫu riêng: old town −1.4 pp, countryside −1.9 pp.

## 4c. Entry 23 — kiểm tra trên seed 64–66 (đăng ký trước)

| Seed 64–66, 144 run | R* = OWF-HWA-S5 | **C9 = OWF-HWA-S5-NT-HQ** | C10 = C9 + phủ quyết |
|---|---|---|---|
| recall gộp | 0.936 | 0.932 | 0.924 |
| TB segFAR | 0.0074 | **0.0057** | **0.0024** |
| run > α | 4 | 4 | **0** |
| điều hướng (m) | 14.67 | **14.51** | 14.90 |
| CMU recall / segFAR / điều hướng | 0.856 / 0.0364 / 8.5 | **0.865 / 0.0254 / 7.1** | 0.856 / 0.0129 / 5.3 |
| Nordland segFAR / điều hướng | 0.0064 / 7.5 | **0.0036 / 4.1** | 0.0036 / 4.1 |

**Quyết định theo quy tắc: C9 thay R*.**
- V1: 4 = 4 run > α; segFAR thấp hơn.
- V2: −0.0037, CI dưới −0.0071 ≥ −0.010.
- V3: điều hướng tốt hơn.

Script đánh giá in nhầm luật (sao từ Entry 21). Quyết định được tính lại đúng luật đã commit từ cùng các số
(`analysis/results/owf/s1106/e23_decision.txt`).

**Tổng quát của C9 (mô tả, không quyết định; đợt `genhq`, các tập chưa từng dùng để chỉnh; R* = OWF-HWA-S5 trên CÙNG run).** Ô = recall
/ TB segFAR / run > α:

| Tập | R* | C9 | chênh recall (CI 95 %) |
|---|---|---|---|
| lỗ 10 % (108) | 0.933 / 0.0022 / 1 | 0.932 / 0.0019 / **0** | −0.001 [−0.004, +0.002] |
| lỗ 50 % (108) | 0.894 / 0.0091 / 4 | 0.873 / 0.0071 / 4 | −0.021 [−0.031, −0.013] |
| off-map tự nhiên (36) | 0.952 / 0.0104 / 2 | 0.943 / **0.0025 / 0** | −0.009 [−0.014, −0.005] |
| NCLT (6) | 0.781 / 0.0049 / 0 | 0.768 / 0.0011 / 0 | −0.013 [−0.028, +0.004] |

- Hợp lệ tốt hơn ở MỌI tập: tổng run > α 7 → 4; 4 run còn lại đều là CMU ở lỗ 50 %.
- Lỗ 10 %, CMU: 0.796 / 0.0077 / 1 → 0.814 / 0.0034 / 0.
- Điều hướng: lỗ 50 % Nordland 21.7 → 13.2 m; NCLT 5.8 → 4.7 m.
- Recall giảm rõ nhất ở lỗ 50 % (−0.021): ít frame trên bản đồ, nên phiên đủ 100 mẫu riêng muộn hơn.

Còn lại:
- 4 run CMU > α (cả hai luật), 3 trong đó từ nhánh HSI. C10 xoá cả 4, đổi lại −0.012 recall.
- Recall giảm ở đầu các phiên khác điều kiện (old town −0.018, Boreas −0.013).

## 4d. Entry 24 — xác nhận độc lập trên seed 67–69, kèm SOTA ngoài trên cùng run (đăng ký trước)

| Seed 67–69, 144 run | **OWF-HWA-S5-NT-HQ** | + phủ quyết (an toàn) | luật cũ | HSI-VN | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|---|---|---|
| recall | **0.927** | 0.920 | 0.931 | 0.791 | 0.834 | 0.692 | 0.738 | 0.847 |
| run > α | **0** | **0** | 1 | 0 | 130 | 81 | 104 | 0 |
| TB segFAR gộp | 0.0031 | **0.0009** | 0.0035 | 0.0030 | 0.668 | 0.256 | 0.200 | 0 |
| điều hướng (m) | 12.6 | 12.9 | 12.1 | 15.5 | 109.5 | 51.0 | 44.3 | 10.6 |

**Quyết định: XÁC NHẬN (C1–C4).** Điểm vận hành an toàn cũng được xác nhận (S1 ∧ S2).
- Luật mới vượt oracle một-frame +0.080 recall với 0 run > α.
- Ba đối thủ ngoài (ngưỡng chỉnh bằng NHÃN) vượt α trên 56–90 % run.

Hai thử nghiệm phát triển phụ không thành công, đều cho đầu phiên đêm:
- co rút Bayes;
- chọn hiệu chỉnh theo evidence: evidence lại thưởng cho mô hình linh hoạt hơn, như ngân hàng β ở Entry 16.

## 4d-bis. Entry 26 — xác nhận lần ba trên seed 70–72

R_new: 0.926 recall, **0/144 run > α**, điều hướng 13.95 m (HSI-VN 15.24 m). TAO'26 / Xu'21 / Claxton'24 vượt α ở 126 / 83 / 101 run.

**Tổng 432 run tươi (64–72):**
- R_new: 4 run > α (0.9 %).
- Điểm an toàn: 0 run > α.
- Luật cũ: 14/720 run > α (1.9 %) trên 55–69.

## 4e. Tổng quát của luật mới so với SOTA ngoài (cùng run), Entry 25, VPR-Space, chẩn đoán đầu chuỗi CMU

| Set | Ours (OWF-HWA-S5-NT-HQ) | OWF-HWA-S5 | HSI-VN | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|---|---|
| holes 10 % (108) | **0.932 / 0.005 / 0** | 0.933 / 0.008 / 1 | 0.772 / 0.002 / 0 | 0.843 / 0.775 / 92 | 0.646 / 0.145 / 35 | 0.737 / 0.517 / 86 | 0.827 |
| holes 50 % (108) | **0.873 / 0.030 / 4** | 0.894 / 0.032 / 4 | 0.754 / 0.030 / 4 | 0.842 / 0.754 / 93 | 0.609 / 0.381 / 30 | 0.678 / 0.133 / 60 | 0.829 |
| natural off-map (36) | **0.943 / 0.003 / 0** | 0.952 / 0.010 / 2 | 0.742 / 0.004 / 0 | 0.578 / 0.075 / 4 | 0.581 / 0.037 / 10 | 0.678 / 0.020 / 5 | 0.822 |
| NCLT (6) | **0.768 / 0.001 / 0** | 0.781 / 0.005 / 0 | — | 0.756 / 0.713 / 6 | 0.526 / 0.021 / 1 | 0.663 / 0.213 / 5 | 0.724 |

cell = pooled recall / worst-dataset mean segFAR / runs > alpha

- Luật mới hợp lệ nhất trên mọi tập. 4 run > α còn lại đều là CMU ở lỗ 50 %, nơi mọi luật không nhãn đều có 4.
- **VPR-Space (96 run):** 0.281, 0 run > α, không đổi so với luật cũ. Mỗi setup chỉ có một phiên ngắn, nên bằng chứng tuyệt đối tự về trung
  tính, đúng như thiết kế. Khoảng cách tới oracle (0.56) vẫn do lớp quyết định.
- **Entry 25 (phẳng):** phủ quyết theo khối lượng trong 1.6 excl so với trong excl: +0.0003 recall. Chi phí countryside không do bán kính.
- **Đầu chuỗi CMU:** 31 % số frame trên bản đồ nằm trong 2 excl đầu. Ở đó luật báo 53–82 %, trong khi top-1 đúng 95–97 %. Nguyên nhân là đếm
  bằng chứng theo quãng đường (cần thiết, Entry 10). Đây là hướng có khoảng trống lớn nhất còn lại.

## 4f. Entry 27 — kiểm toán mã, công thức, lý thuyết (2026-11-07)

**Đã kiểm:** metric, bộ lọc OWF, ngân hàng, lớp quyết định, HQ, Mệnh đề 1–7.

**Sai tìm thấy và đã sửa:**
1. Mã HQ đã kiểm tra (`--lu hsq`) có **hai rò rỉ tương lai**: sàn KDE lấy biên từ cả khối 50 frame; mẫu được thưa theo tổng số frame tự tin của
   cả phiên. Kiểm thử `analysis/tests/test_hq_causality.py`: hsq đổi tới 0.67 log-LR ở quá khứ khi đổi tương lai; mã sửa `hsq2` đổi 0.
2. Mệnh đề 2 giả định LR = 1 trên ô trống; với HQ cần điều kiện (E1′) (`owf_theory.md` §11 (iii)). Mệnh đề 7(a) thêm "niềm tin khuếch tán".
3. Mô tả "nhân quả theo phiên" chưa chính xác: dự phòng dùng các phiên khác của cùng run (giả định đội xe, transductive). Thêm biến thể
   nghiêm ngặt `hsq2s` (chỉ phiên trước).

**Chạy lại** (cùng run, quy tắc đăng ký trước áp lại nguyên văn). Ô = recall / TB segFAR / run > α / điều hướng (m):

| Nhóm | hsq2 (mã khuyến nghị) | + phủ quyết ½ | hsq2s (nghiêm ngặt) | Quyết định |
|---|---|---|---|---|
| 64–66 | 0.932 / 0.0059 / 4 / 14.56 | 0.924 / 0.0024 / 0 / 14.91 | 0.932 / 0.0071 / 5 / 14.80 | Entry 23 giữ (V1–V3 đạt); hsq2s trượt V1 |
| 67–69 | 0.927 / 0.0029 / 0 / 12.53 | 0.920 / 0.0009 / 0 / 12.93 | 0.927 / 0.0032 / 0 / 12.54 | Entry 24 giữ (C1–C4, S1–S2) |
| 70–72 | 0.926 / 0.0035 / 0 / 13.97 | 0.918 / 0.0013 / 0 / 14.56 | 0.925 / 0.0041 / 0 / 14.06 | Entry 26 giữ (C1–C4, S1–S2) |
| tập A (399) | 0.929 / 0.0034 / 0 / 13.01 | — | — | (phát triển) |

- hsq2 so với hsq: Δrecall ≤ 0.0004 mỗi nhóm; run > α không đổi; tổng quát trùng (NCLT 0.768 → 0.770).
- hsq2s chỉ khác ở CMU 64–66 (segFAR tệ nhất 0.025 → 0.037, ngang luật cũ 0.036): **một phần lợi ích CMU của HQ đến từ hiệu chỉnh xuyên
  phiên**. Đây là hạn chế phải báo trong paper.

## 4g. Entry 28 — kiểm toán lần hai (2026-11-07)

**Sai tìm thấy:** nhánh HSI-VN (nhánh học của mọi luật union) tạo nhãn hồi cứu bằng đại lượng của cả đợt triển khai:
- s0 / κ của cầu nối là trung vị toàn đợt;
- nhãn khoảng trống chốt trước khi đoạn phải dùng để khớp được xác minh;
- bước odometry trung vị toàn đợt.

Vòng lặp trực tuyến chỉ dùng nhãn đã chốt, nên lỗi này không lộ khi kiểm từng hàm. Nó chỉ lộ khi kiểm **đầu-cuối**
(`analysis/tests/test_hsi_causality.py`): thay dữ liệu sau mốc R bằng rác thì HSI-VN đổi 3–2839 quyết định trước R, còn bản sửa `HSI-VNc`
đổi 0.

**Chạy lại nhánh HSI** (frame OWF giữ nguyên; luật cũ và đường cơ sở HSI đứng riêng cũng dùng HSI-VNc). Ô = recall / TB segFAR / run > α / điều hướng (m):

| Nhóm | Luật cuối | + phủ quyết ½ | Quyết định |
|---|---|---|---|
| 64–66 | 0.933 / 0.0058 / 3 / 14.88 | 0.924 / 0.0026 / 0 / 15.34 | Entry 23 giữ (vs luật cũ 0.936 / 0.0076 / 4 / 15.15) |
| 67–69 | 0.928 / 0.0029 / 0 / 12.58 | 0.920 / 0.0007 / 0 / 12.93 | Entry 24 giữ (+0.133 vs HSI-VNc) |
| 70–72 | 0.926 / 0.0034 / 0 / 14.01 | 0.919 / 0.0013 / 0 / 14.62 | Entry 26 giữ (+0.117 vs HSI-VNc) |
| tập A (399) | 0.929 / 0.0032 / 0 / 13.54 | — | (phát triển) |

Tổng quát (mọi cột dùng HSI-VNc; recall / TB segFAR tệ nhất / run > α):

| Tập | Luật cuối | Luật cũ S5 | HSI-VNc đứng riêng |
|---|---|---|---|
| lỗ 10 % (108) | 0.932 / 0.004 / 0 | 0.933 / 0.008 / 1 | 0.777 / 0.003 / 0 |
| lỗ 50 % (108) | 0.872 / 0.028 / 4 | 0.894 / 0.030 / 4 | 0.751 / 0.027 / 4 |
| off-map tự nhiên (36) | 0.945 / 0.004 / 0 | 0.954 / 0.012 / 1 | 0.756 / 0.011 / 0 |
| NCLT (6) | 0.769 / 0.001 / 0 | 0.780 / 0.003 / 0 | — |

Tập A với HSI-VNc ở cả hai luật: S5 0.933 / 0.0040 / 0 / 12.4 m → luật cuối 0.929 / 0.0032 / 0 / 13.5 m. **Điều hướng tập A tệ hơn 1.2 m**
(old town 20.9 → 29.1 m): giá của HQ ở đầu phiên điều kiện chưa thấy, nay rõ hơn trước. Biến thể nghiêm ngặt: 5/432 (phủ quyết 4/432),
như Entry 27.

**Đã kiểm lại và đúng:** bộ lọc OWF + engine GPU, lớp quyết định, chuỗi tô-pô, đặc trưng HSI, metric, đối thủ ngoài, Mệnh đề 1–7 (sửa hai
phát biểu, nêu một thiên lệch). Quy ước cần ghi: điều hướng khởi tạo bằng vị trí thật; không báo sai số điều hướng trên tập off-map tự nhiên.

## 5. Vận hành

- Kho seed mới `namhunhh/hmm-navcache-r61` (seed 61–66, 288 cache, 20 kernel CPU).
- Ba đợt kiểm tra / phát triển trên GPU (6 phiên 4×L4 mỗi đợt, 20–35 phút):
  - `test61`: R*, NT;
  - `devlu`: NT + LU;
  - `genlu`: tổng quát, mô tả.
- `hieuho669` dùng được L4 từ 06:23 UTC.
- Container khởi động lại một lần; monitor trung tâm chạy lại từ state file, không mất kernel.

## 6. Hạn chế và việc tiếp theo

- Bí danh odometry không thấy được (CMU) là nguồn đuôi hợp lệ. Entry 23 giảm nó ở bộ ước lượng (CMU segFAR −30 %). Phủ quyết bằng mN của
  C9 xoá hết trên seed 64–66, với giá −0.012 recall.
- Đầu phiên có điều kiện chưa từng thấy (đêm): trước 100 mẫu riêng, phiên dùng phân bố của phiên khác. Cần dự phòng có điều kiện tốt hơn
  (thử theo trung vị hồ sơ: không đủ).
- **Ưu tiên 1:** sinh kho seed mới (r61 đã dùng hết) rồi kiểm C10 (C9 + phủ quyết ½) như một điểm vận hành "an toàn" riêng. Trên seed
  64–66 nó đạt 0/144 run > α.
- **Ưu tiên 2:** dự phòng đầu phiên cho điều kiện chưa từng thấy. Ví dụ trộn Bayes giữa "trung tính" và "phân bố phiên khác", trọng số theo
  khả năng dự đoán x_t của chính phiên.
- **Ưu tiên 3:** tổng quát của C9 trên lỗ 10/50 %, off-map tự nhiên, NCLT. Đợt `genhq` đã chạy; xem RESEARCH_LOG nếu kịp đọc.
- VPR-Space: lớp quyết định quá bảo thủ trên triển khai ngắn (Entry 18). Vẫn mở.

## 7. So sánh novelty với ý tưởng 1 (branch `hmm-navigation-5`), không tính dataset / giao thức

Bài toán, giao thức và metric giống hệt nhau (hạ tầng chung, không tính vào novelty). So sánh từng thành phần của luật cuối với thứ gần nhất
trong ý tưởng 1. Trọng số là mức đóng góp của thành phần vào novelty của luật cuối (đánh giá chủ quan).

| Thành phần luật cuối | Trọng số | Thứ gần nhất trong ý tưởng 1 | Mức trùng |
|---|---|---|---|
| Bộ lọc thế giới mở: vùng trống trong trạng thái mét, hiện diện theo vị trí, bảo toàn khối lượng, dead-reckoning qua lỗ | 30 % | trạng thái OFF không có vị trí (Entry 31); "ghost" dead-reckoning làm cổng (Gate 8); lỗ ảo trong phẫu thuật tiến (CST-F) | ~20 % |
| HQ: bằng chứng tuyệt đối cho ô trống, null "bí danh khi chỗ đúng vắng mặt" lấy bằng cách loại vùng quanh fix tự tin, hiệu chỉnh theo phiên | 25 % | **CMS** (Entry 28: xoá hành lang ρ quanh niềm tin để lấy null ngoài bản đồ theo điều kiện truy vấn, Mondrian theo điều kiện); **HMM có trạng thái OFF với emission hiệu chỉnh bằng CMS** (Entry 31) | **~65 %** |
| Lớp quyết định HSI-VN ∪ bậc OWF ∪ đồng thuận ba nguồn | 20 % | SelfCal / CPC (presence có hiệu chỉnh conformal / e-value), cổng đồng thuận G, phép thử hình dạng SH / CST | ~40 % |
| Lý thuyết (Ville / e-value, Mệnh đề 1–7) | 15 % | Định lý 6 / 6′ / 6″ (chuỗi hiện diện e-value + Ville), Mệnh đề 13 | ~35 % (công cụ chung; Mệnh đề 3, 5, 6, 7 mới) |
| Ngân hàng tự hiệu chỉnh odometry | 5 % | không có | 0 % |
| Không dịch chuyển tức thời | 5 % | biến thể "reset" / "temper" của re-entry (Entry 31) | ~20 % |

**Mức trùng gộp ≈ 0.30·0.20 + 0.25·0.65 + 0.20·0.40 + 0.15·0.35 + 0.05·0 + 0.05·0.20 ≈ 0.37, tức khoảng 35–40 %.**

- Phần khác biệt chính là bộ ước lượng thế giới mở (ý tưởng 1 giữ HMM tô-pô, kiểm hiện diện bằng phép thử).
- Phần trùng nhiều nhất là HQ: cùng nguyên lý "null ngoài bản đồ từ chính luồng truy vấn bằng cách loại vùng quanh niềm tin, theo điều kiện".
  Khác ở ba điểm:
  - thống kê (max − trung vị so với route cost / độ đặc trưng không gian);
  - ước lượng (mật độ KDE từ các fix tự tin của lượt 1, không phẫu thuật lại bản đồ mỗi frame, không conformal);
  - chỗ đặt (LR của ô trống trong lưới mét, thay vì trạng thái OFF không vị trí).
- Paper phải ghi rõ quan hệ này.

## 8. Tóm tắt phương pháp dễ hiểu

- **Bài toán.** Robot có camera và đo quãng đường (odometry). Nó so ảnh đang thấy với một bản đồ ảnh có toạ độ, nhưng bản đồ có những chỗ trống
  chưa từng chụp. Mỗi khoảnh khắc, robot phải quyết định có tin vị trí tìm được để báo cho bộ dẫn đường hay không. Báo sai khi đang ở chỗ trống
  thì rất có hại.
- **Ý chính 1: thế giới mở.** Thay vì chỉ hỏi "mình đang ở ảnh bản đồ nào", robot giữ một bản đồ xác suất về vị trí trên lưới mét phủ cả chỗ có
  ảnh lẫn chỗ trống. Khi robot lái vào chỗ trống, đo quãng đường tự đẩy xác suất vào vùng trống. Robot biết mình "ra khỏi bản đồ" nhờ tính
  toán vị trí, không cần một phép thử riêng.
- **Ý chính 2: tự hiệu chỉnh đo quãng đường.** Chạy song song 10 bộ lọc với các giả thuyết khác nhau về nhiễu và tỉ lệ sai của odometry, rồi theo
  bộ lọc giải thích dữ liệu tốt nhất.
- **Ý chính 3: bằng chứng tuyệt đối có hiệu chỉnh (HQ).** Có những con đường thẳng mà một đoạn ở chỗ khác trông hơi giống. Odometry không
  phân biệt được hai đoạn vì chúng chỉ lệch nhau theo chiều đường. Vì thế robot học hai phân bố từ chính lần chạy thứ nhất, ở những chỗ nó đã
  chắc chắn:
  - "ảnh giống nhất trông thế nào khi đúng chỗ";
  - "ảnh giống nhất trông thế nào khi chỗ đúng bị loại đi", tức bí danh.

  Khi khớp tốt nhất chỉ ở mức bí danh, xác suất được dồn về vùng trống thay vì về chỗ giống.
- **Quyết định.** Báo khi nhánh học hồi cứu (HSI) báo, hoặc khi bộ lọc chắc chắn ở mức cực cao. Chế độ an toàn: nhánh học chỉ được báo khi bộ
  lọc thế giới mở cũng cho rằng robot ở gần bản đồ.

## 9. Hướng hoàn thiện / cải tiến

1. **Luật quyết định thống nhất** thay union HSI ∪ bậc: ngưỡng posterior suy từ cận Ville với ngân sách phóng đại K ước lượng từ bản đồ, hoặc
   e-process trên (E1′). Đây là việc quan trọng nhất cho novelty.
2. **Mô hình tương quan bằng chứng** giữa frame liền kề thay ℓ cố định, để lấp khoảng trống đầu chuỗi CMU (53–82 % so với top-1 95–97 %).
3. **Hiệu chỉnh HQ có điều kiện và trực tuyến thật sự:** chọn phiên tham chiếu cùng môi trường / điều kiện (embedding điều kiện từ descriptor),
   hoặc ước lượng f_off từ chính bản đồ (ảnh bản đồ truy vấn bản đồ, loại 1.6 excl) trước khi phiên có mẫu riêng, để biến thể nghiêm ngặt
   giữ được lợi ích trên CMU (Entry 27).
4. **Kiểm chứng hình học** (local feature / 6DOF) cho các fix có bí danh, trên dataset có ảnh gốc (Boreas, 4Seasons, NCLT, St Lucia).
5. **Lỗ thật** (bản đồ cũ, môi trường đổi) và đánh giá độ nhạy hằng số HQ (1.6 excl, 100 mẫu).
6. **VPR-Space:** lớp quyết định thích nghi với triển khai ngắn.
7. **Gate tài liệu hệ thống** cho OWF + HQ (MCL với vùng chưa vẽ, topometric, open-set VPR, change detection) và định vị rõ so với CMS.

