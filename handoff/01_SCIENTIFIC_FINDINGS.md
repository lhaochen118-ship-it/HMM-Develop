# 01 — Scientific Findings (ý tưởng 2, branch `hmm-2nd-idea`)

*Cập nhật 2026-11-07.*
- **Phạm vi:** đóng góp, ý nghĩa khoa học, kết quả tích cực, kết quả tiêu cực / hạn chế, bằng chứng và điều kiện kiểm chứng. Không chứa vận
  hành (→ `02`) hay kế hoạch (→ `03`).
- Nguồn: `RESEARCH_LOG.md` (Entry 10–28), `paper/owf_theory.md` (Mệnh đề 1–7, §11–12 kiểm toán), `paper/OWF_paper_draft.md`.
- Bản trước (đầy đủ các phiên 2026-11-04 → 06): `history/01_SCIENTIFIC_FINDINGS_through_2026-11-06.md`. Ý tưởng 1: `07_IDEA1_SUMMARY.md`.

## 0. Một trang

**Bài toán.** Robot có camera + odometry tự định vị trên một bản đồ ảnh có lỗ (vùng chưa vẽ). Mỗi frame phải quyết định có báo một fix vị trí
cho bộ lọc điều hướng hay không. Mục tiêu:
- recall cao (nhiều fix đúng trên bản đồ);
- segFAR ≤ α = 0.05 trên từng run (tỉ lệ đoạn ngoài bản đồ có báo sai);
- sai số điều hướng thấp;
- không dùng nhãn khi triển khai, một cấu hình cho mọi dataset.

**Luật cuối: OWF-HWA-S5-NT-HQ.** Gồm:
1. Bộ lọc thế giới mở (OWF): niềm tin trên lưới mét phủ cả vùng có bản đồ lẫn vùng trống, cộng một trạng thái xa Ω.
2. Ngân hàng tự hiệu chỉnh odometry, chọn theo evidence.
3. Không dịch chuyển tức thời (NT).
4. Bằng chứng tuyệt đối hiệu chỉnh hồi cứu cho ô trống (HQ).
5. Lớp quyết định: nhánh HSI-VNc (tự giám sát hồi cứu + conformal, dạng nhân quả của HSI-VN) hợp với các bậc tin cậy cực đoan của OWF.

**Bằng chứng chính.** Ba nhóm seed tươi (64–72; 432 run; 8 dataset × 6 descriptor; quyết định đăng ký trước mỗi lần):
- recall 0.926–0.933 (mã đã kiểm toán hai lần);
- 3/432 run vượt α; với phủ quyết thế giới mở: 0/432;
- hơn HSI-VNc (nhánh học đứng riêng) +0.117 … +0.133;
- vượt oracle một-frame (~0.85);
- ba phương pháp ngoài có ngưỡng chỉnh bằng nhãn (TAO'26, Xu'21, Claxton'24) vượt α trên 56–90 % số run.

Mọi con số đã được **chạy lại bằng mã đã kiểm toán hai lần** (Entry 27, §3.6; Entry 28, §3.7).

**Giới hạn chính:**
- lớp quyết định vẫn là tổ hợp kỹ thuật;
- đầu chuỗi CMU và đầu phiên ở điều kiện chưa thấy vẫn mất recall;
- lỗ được mô phỏng (trừ NCLT, 4Seasons chéo cảnh, VPR-Space);
- HQ trùng nguyên lý với CMS của ý tưởng 1.

## 1. Đóng góp và ý nghĩa

| # | Đóng góp | Ý nghĩa khoa học | Mức mới (trung thực) |
|---|---|---|---|
| C1 | **Bộ lọc thế giới mở** (Entry 10): lưới mét phủ cả vùng trống + Ω; chuyển động bảo toàn khối lượng; hiện diện trên bản đồ là hàm của vị trí; emission là tỉ số hợp lý với ô trống làm null tự nhiên | "Ra khỏi bản đồ" được *dự đoán* bằng dead-reckoning theo độ phủ đã biết của bản đồ, thay vì *phát hiện* bằng phép thử. Đây là gốc của cả recall lẫn hợp lệ | Gate 18: không thấy công trình có cả (i) không gian trống trong trạng thái mét lẫn (ii) hiện diện theo vị trí cho định vị bằng ảnh. Emission thuộc họ chuẩn |
| C2 | **Tự hiệu chỉnh odometry** trực tuyến: ngân hàng q × tỉ lệ, theo bộ lọc có evidence tích luỹ lớn nhất | Hấp thụ sai số tỉ lệ 3–7 % của VIO mà không cần nhãn | Chọn mô hình theo evidence là chuẩn; mới ở chỗ áp dụng |
| C3 | **Bí danh odometry không thấy được** (Mệnh đề 6, Entry 21–22) | Một bản sao dịch dọc đường thẳng của quỹ đạo thật khớp yếu nhưng nhất quán chuyển động. Với emission chuẩn hoá z theo frame (điểm giao ≈ 0.5 SD), nó tích luỹ không giới hạn. Đây là nguồn của phần lớn run vượt α của mọi luật trước | Phân tích mới cho bài toán này. Hiện tượng aliasing nói chung đã biết |
| C4 | **Bằng chứng tuyệt đối hiệu chỉnh hồi cứu cho ô trống (HQ)** (Mệnh đề 7, Entry 23, 27) | Ô trống nhận log f_off(x) − log f_on(x), với x = max độ tương đồng trừ trung vị hồ sơ. Hai mật độ học không nhãn từ các fix tự tin của lượt 1 (f_off = max ngoài 1.6 excl quanh fix: "bí danh khi chỗ đúng vắng mặt"). Hiệu chỉnh trong chính phiên (nhân quả); đúng chỗ không nổi bật thì tự trung tính | **Trùng nguyên lý với CMS / trạng thái OFF có hiệu chỉnh của ý tưởng 1** (Entry 28, 31: xoá hành lang quanh niềm tin để lấy null ngoài bản đồ theo điều kiện). Khác ở thống kê, ước lượng (mật độ thay vì conformal) và chỗ đặt (ô trống của lưới mét) |
| C5 | **Không dịch chuyển tức thời** (Mệnh đề 5, Entry 19) | Hạt giống re-entry rải lên mọi ảnh bị aliasing nhất quán khuếch đại. Ω hấp thụ thì bỏ được kênh này | Nhỏ. Ablation: thêm rất ít khi đã có HQ |
| C6 | **Lý thuyết** (`owf_theory.md`) | Mệnh đề 1 (không kéo ròng), 2 (cận Ville dưới (E1); (E1′) khi có HQ), 2′ (độ phóng đại K đo được), 3 (hiện diện theo vị trí), 4 (conformal hồi cứu; âm), 5, 6, 7 | Công cụ (Ville, e-value) cũng dùng ở ý tưởng 1 |
| C7 | **Giao thức đánh giá** | Đăng ký trước; nhóm seed tươi dùng một lần; kiểm toán theo vị trí; SOTA ngoài trên cùng run; kiểm thử tính nhân quả | Thực hành, không phải đóng góp phương pháp |

## 2. Kết quả tích cực (bằng chứng)

### 2.1 Luật cuối trên ba nhóm seed tươi (đăng ký trước; mã đã kiểm toán, Entry 27)

Mỗi nhóm 144 run (8 dataset × 6 descriptor × 3 seed), quyết định đăng ký trước; số dưới đây là số **chạy lại bằng mã đã kiểm toán hai lần**
(`--lu hsq2`, Entry 27; nhánh HSI nhân quả `HSI-VNc`, Entry 28).

| Nhóm | Entry | Luật cuối: recall / TB segFAR / run > α / điều hướng (m) | + phủ quyết ½ | So sánh cặp | Quyết định |
|---|---|---|---|---|---|
| 64–66 | 23 | 0.933 / 0.0058 / 3 / 14.88 | 0.924 / 0.0026 / **0** / 15.34 | vs luật cũ S5 (cùng nhánh HSI-VNc): −0.0035 [−0.0068, −0.0006], TB segFAR 0.0076 → 0.0058, run > α 4 → 3 | thay luật cũ (V1–V3 đạt) |
| 67–69 | 24 | 0.928 / 0.0029 / **0** / 12.58 | 0.920 / 0.0007 / **0** / 12.93 | vs HSI-VNc độc lập: +0.133 [+0.115, +0.151] | xác nhận (C1–C4, S1–S2 đạt) |
| 70–72 | 26 | 0.926 / 0.0034 / **0** / 14.01 | 0.919 / 0.0013 / **0** / 14.62 | vs HSI-VNc độc lập: +0.117 [+0.100, +0.133] | xác nhận (C1–C4, S1–S2 đạt) |

Tổng: **3/432 run > α (0.7 %)**, cả 3 ở CMU seed 64–66; với phủ quyết **0/432**. Luật cũ OWF-HWA-S5 cùng nhánh HSI-VNc trên 64–72:
6/432 (64–66: 4; 67–69: 1; 70–72: 1).

### 2.2 So với phương pháp ngoài trên cùng run (seed 67–72, 288 run)

| | Ours | + phủ quyết | HSI-VN | TAO'26 | Xu'21 | Claxton'24 | oracle một-frame |
|---|---|---|---|---|---|---|---|
| recall (67–69 / 70–72) | 0.928 / 0.926 | 0.920 / 0.919 | 0.795 / 0.810 | 0.834 / 0.839 | 0.692 / 0.696 | 0.738 / 0.739 | 0.847 / 0.848 |
| run > α (trên 144) | 0 / 0 | 0 / 0 | 0 / 0 | 130 / 126 | 81 / 83 | 104 / 101 | 0 / 0 |
| điều hướng (m) | 12.6 / 14.0 | 12.9 / 14.6 | 14.5 / 15.4 | 110 / 115 | 51 / 57 | 44 / 49 | 10.6 / 11.7 |

Đối thủ ngoài dùng ngưỡng chỉnh bằng NHÃN như trong bài báo gốc. Ba cột đầu là số chạy lại bằng mã đã kiểm toán hai lần (cột HSI-VN nay là
HSI-VNc độc lập); đối thủ không dùng HQ / HSI nên không đổi.

### 2.3 Tổng quát trên các tập không dùng để chỉnh (cùng run; recall / TB segFAR tệ nhất / run > α; ba cột đầu chạy lại bằng mã đã kiểm toán hai lần, mọi cột dùng HSI-VNc)

| Tập | Ours | Luật cũ (S5) | HSI-VNc | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|---|---|
| lỗ 10 % (108) | **0.932 / 0.004 / 0** | 0.933 / 0.008 / 1 | 0.777 / 0.003 / 0 | 0.843 / 0.775 / 92 | 0.646 / 0.145 / 35 | 0.737 / 0.517 / 86 | 0.827 |
| lỗ 50 % (108) | **0.872 / 0.028 / 4** | 0.894 / 0.030 / 4 | 0.751 / 0.027 / 4 | 0.842 / 0.754 / 93 | 0.609 / 0.381 / 30 | 0.678 / 0.133 / 60 | 0.829 |
| off-map tự nhiên (36) | **0.945 / 0.004 / 0** | 0.954 / 0.012 / 1 | 0.756 / 0.011 / 0 | 0.578 / 0.075 / 4 | 0.581 / 0.037 / 10 | 0.678 / 0.020 / 5 | 0.822 |
| NCLT (6) | **0.769 / 0.001 / 0** | 0.780 / 0.003 / 0 | — | 0.756 / 0.713 / 6 | 0.526 / 0.021 / 1 | 0.663 / 0.213 / 5 | 0.724 |

### 2.4 Ablation (tập A, 399 run cùng run; recall / TB segFAR / run > α / điều hướng m)

| S5 (luật cũ) | + NT | + HQ | + NT + HQ (cuối) |
|---|---|---|---|
| 0.933 / 0.0045 / 1 / 12.7 | 0.932 / 0.0040 / 2 / 12.4 | 0.930 / 0.0034 / 0 / 12.9 (mã hsq) | 0.929 / 0.0034 / 0 / 13.0 (chạy lại hsq2 + HSI-VNc: 0.9287 / 0.0032 / 0 / 13.5) |

HQ mang gần hết lợi ích hợp lệ. CMU: 0.852 / 0.0095 → 0.863 / 0.0066. Nordland: segFAR 0.0069 → 0.0026.

Chạy lại với nhánh HSI-VNc ở CẢ HAI cột (Entry 28): S5 0.9328 / 0.0040 / 0 / 12.4 → luật cuối 0.9287 / 0.0032 / 0 / 13.5 (Δrecall −0.0041
[−0.0061, −0.0022]). CMU 0.848 / 0.0092 → 0.859 / 0.0062; Nordland segFAR 0.0069 → 0.0026. **Điều hướng tập A tệ hơn 1.2 m**, chủ yếu old town
(20.9 → 29.1 m) và Boreas (5.3 → 6.6 m): giá của HQ ở đầu phiên điều kiện chưa thấy, nay rõ hơn (trước kiểm toán lần hai: +0.35 m).

### 2.5 Cơ chế đã xác nhận

- **Bí danh dịch chuyển.** Run vượt α của CMU seed 60 và 61 đến từ bản sao lệch 204 m và 673 m, không đổi qua 10–17 lượt đi; hai
  descriptor độc lập chọn cùng chỗ. Cos 0.34–0.45 so với 0.69–0.77 ở đúng chỗ (`paper/figures/owf_shifted_alias.png`).
- Trên CMU s60 CosPlace, z trung vị của bí danh (4.09) cao hơn phân vị 5 % của khớp đúng (3.90). Độ tương đồng thô thì tách được (0.44 so với
  0.54).
- Mẫu "bí danh hồi cứu" (trung vị 0.469) khớp bí danh thật trong lỗ (0.445). AUC khớp đúng vs bí danh: theo cos 0.92–0.96, theo z 0.86–0.88.

## 3. Kết quả tiêu cực và hạn chế (đều có số đo)

### 3.1 Ý tưởng bị loại ở phát triển hoặc kiểm tra

| Entry | Ý tưởng | Kết quả |
|---|---|---|
| 16 | Ngưỡng conformal hồi cứu thay các bậc cố định (Mệnh đề 4) | recall −0.017 … −0.027, 23–46 run > α |
| 19 | NT riêng (kiểm tra 58–60) | không qua quy tắc: cả luật cũ cũng có 6/144 run > α |
| 20 | ℓ = chiều dài tương quan thị giác của bản đồ | recall −0.029, 13 run > α |
| 21 | Phủ quyết HSI bằng mN của OWF (kiểm tra 61–63) | hợp lệ tốt hơn, điều hướng +0.9 m: trượt |
| 22 | Điểm giao cố định μ₁/2 | CMU ÷ 4.6 báo sai, nhưng recall −0.030, Nordland tệ hơn |
| 23 dev | HQ hiệu chỉnh từ phiên khác (hs / hsm / hsmp), KDE 2-D theo điều kiện (hsc), dự phòng theo điều kiện (hsr) | sập phiên đêm old town (0.72 → 0.11–0.66) |
| 24 dev | Co rút Bayes (hsb), chọn hiệu chỉnh theo evidence (hsqsel), nới bậc ngưỡng | không cải thiện |
| 25 | Phủ quyết theo khối lượng trong 1.6 excl | phẳng |

### 3.2 Hạn chế của luật cuối

- **Lớp quyết định là tổ hợp kỹ thuật** (HSI-VN ∪ ba bậc cố định). Hợp lệ được chứng minh thực nghiệm, không bằng một định lý theo run.
  Mệnh đề 2 cần (E1′), và (E1′) không được kiểm.
- **Đầu chuỗi CMU:** trong 2 excl đầu luật báo 53–82 % số frame trên bản đồ, top-1 đúng 95–97 %. Nguyên nhân là đếm bằng chứng theo quãng đường
  (ℓ cố định).
- **Điều hướng trên tập A tệ hơn luật cũ 1.2 m** (13.5 so với 12.4; old town 29.1 so với 20.9 m) khi cả hai dùng nhánh HSI-VNc (Entry 28). Trên seed
  tươi luật cuối vẫn tốt hơn hoặc ngang (V3 đạt cả ba nhóm).
- **Đầu phiên ở điều kiện chưa thấy** (đêm): trước khi phiên có 100 mẫu riêng, HQ dùng phân bố của các phiên khác. Old town −0.012 … −0.018,
  countryside −0.006 … −0.024 so với luật cũ.
- **Hiệu chỉnh xuyên phiên:** dự phòng dùng các phiên khác của cùng run (một đội xe đã đi bản đồ). Biến thể nghiêm ngặt chỉ dùng phiên trước:
  §3.6.
- **VPR-Space** (phiên ngắn, đơn lẻ): HQ trung tính đúng thiết kế; lớp quyết định quá bảo thủ (0.28 so với oracle 0.56).
- **Lỗ mô phỏng** (xoá 30 % ô 300 m), trừ NCLT, 4Seasons chéo cảnh, VPR-Space. Chỉ dùng descriptor toàn cục, không 6DOF.
- **Hằng số 1.6 excl** của HQ trùng off_d của giao thức trên dữ liệu đường phố. Chưa đo độ nhạy.

### 3.3 – 3.5 (giữ chỗ cho các kiểm toán sau)

### 3.6 Kiểm toán 2026-11-07 (Entry 27)

- **Rò rỉ tương lai trong mã HQ đã kiểm tra** (`--lu hsq`):
  - sàn KDE lấy biên từ cả 50 frame của khối;
  - mẫu được thưa theo tổng số frame tự tin của cả phiên.
- `analysis/tests/test_hq_causality.py`: hsq đổi tới 0.67 log-LR ở quá khứ khi đổi tương lai; mã sửa `--lu hsq2` đổi 0.
- Trên 3 run thiết kế, quyết định của hsq và hsq2 trùng ở mọi frame.
- **Chạy lại toàn bộ** (432 run tươi + 399 run tập A, cùng run). Mã hsq2 so với mã đã kiểm tra:
  - Δrecall theo nhóm −0.0001 / −0.0001 / −0.0004 (tập A −0.0002); chênh recall theo run tối đa 0.008;
  - số run > α không đổi (4 / 0 / 0; phủ quyết 0 / 0 / 0);
  - mọi quyết định đăng ký trước của Entry 23, 24, 26 vẫn đúng khi áp lại nguyên văn.
- **Biến thể nghiêm ngặt** `hsq2s` (dự phòng chỉ từ phiên trước):
  - 67–72: ngang hsq2 (C1–C4, S1–S2 đạt; Δrecall −0.0004 / −0.0007);
  - 64–66: CMU segFAR tệ nhất 0.0254 → 0.0366 (luật cũ 0.0364), 5 run > α, phủ quyết 4 run → V1 của Entry 23 trượt.
  - ⇒ **lợi ích hợp lệ của HQ ở CMU dựa một phần vào hiệu chỉnh xuyên phiên** (transductive trong một đợt triển khai). Phải báo cùng giả định.
- **Lý thuyết:** Mệnh đề 2 khi có HQ cần (E1′) (`owf_theory.md` §11 (iii)); Mệnh đề 7(a) thêm điều kiện niềm tin khuếch tán.
- **Tổng quát** chạy lại bằng hsq2 (nhánh HSI-VN cũ): lỗ 10 % 0.932 / 0.005 / 0, lỗ 50 % 0.873 / 0.030 / 4, off-map tự nhiên 0.943 / 0.003 / 0, NCLT 0.770 / 0.002 / 0 (recall / TB segFAR tệ nhất / run > α) — trùng mã hsq ở ba tập đầu (37/108, 31/108, 16/36 run trùng khít, số gộp như nhau), NCLT 0.768 / 0.001 → 0.770 / 0.002.
- Bảng đầy đủ: `RESEARCH_LOG.md` Entry 27, `analysis/results/owf/s1106/e27_*`.

### 3.7 Kiểm toán lần hai 2026-11-07 (Entry 28)

- **Nhánh HSI-VN có nhìn trước trong nhãn hồi cứu** (dùng trong mọi luật union từ Entry 11):
  - s0 / κ của cầu nối là trung vị trên cả đợt triển khai;
  - nhãn khoảng trống được chốt trước khi đoạn phải dùng để khớp được xác minh;
  - bước odometry để đổi cửa sổ mét sang frame lấy từ cả đợt.
- **Sửa:** biến thể `HSI-VNc`. Kiểm thử đầu-cuối `analysis/tests/test_hsi_causality.py` (thay dữ liệu sau mốc R bằng rác, đếm quyết định trước
  R bị đổi): HSI-VN đổi 3–2839, HSI-VNc đổi 0.
- **Chạy lại nhánh HSI** cho mọi tập (frame OWF giữ nguyên):
  - Δrecall của luật cuối so với Entry 27: +0.0005 / +0.0007 / +0.0008 (seed tươi), +0.0002 (tập A), −0.0005 … +0.0019 (tổng quát);
  - run > α: 4 → **3/432**; phủ quyết 0/432; mọi quyết định đăng ký trước vẫn đúng;
  - đường cơ sở HSI-VNc độc lập: 0.795 / 0.810 (trước 0.791 / 0.809).
- Biến thể nghiêm ngặt với HSI-VNc: 5/432 run > α, phủ quyết 4/432, chỉ ở CMU 64–66 (như Entry 27). Luật cũ S5 cùng nhánh HSI-VNc trên 64–72: 6/432.
- Các phần kiểm lại và đúng: bộ lọc + engine GPU, lớp quyết định, `est_c`, đặc trưng HSI, metric, đối thủ. Lý thuyết: sửa phát biểu N (Mệnh đề
  2) và λ_seed (Mệnh đề 5), nêu thiên lệch của mẫu f_off (Mệnh đề 7).
- **Quy ước phải ghi trong paper:** điều hướng khởi tạo bằng vị trí thật; sai số điều hướng vô nghĩa trên tập off-map tự nhiên (hai hệ toạ độ)
  nên không báo.

## 4. Điều kiện kiểm chứng

- **Mã:** commit cuối của `hmm-2nd-idea`. Lệnh luật cuối: `02_ENGINEERING_OPS_NOTES.md` §6.
- **Dữ liệu:** kho seed công khai `namhunhh/hmm-navcache-r61`, `r67` (tươi), `nhatlong1103/hmm-navcache-v2` + `hmm-e37-caches` (tập A),
  `hmm-navcache-holes`, `hmm-natural-cache`.
- **Metric:** `nav_demo.rule_metrics` (recall, segFAR theo đoạn H frame, FL); điều hướng `nav_demo.track`.
- **Giả định:**
  - odometry có nhiễu trong ngân hàng;
  - bản đồ có toạ độ;
  - các phiên của một run cùng một bản đồ (cho dự phòng HQ);
  - lỗ đủ xa (off_d) để đánh giá "ngoài bản đồ".
- **Hằng số chung cho mọi dataset:** bậc 1 − 10⁻⁵ / 16 excl, 1 − 10⁻⁸ / 2 excl, 1 − 3·10⁻⁴ / 0.5 excl + đồng thuận; HQ 1.6 excl, ε = 1 %, 100
  mẫu, khối 50; ℓ = 0.4 excl; ngân hàng q ∈ {0.005, 0.02} excl × tỉ lệ {0.94 … 1.06}.
- **Kết quả thô:** `analysis/results/owf/s1105/`, `s1106/` (bảng `.md`, JSON `.tgz`, script đánh giá).
