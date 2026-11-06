# 01 — Scientific Findings (ý tưởng 2: HSI, branch `hmm-2nd-idea`)

*Cập nhật 2026-11-06 (trước: 2026-11-04). Phạm vi: đóng góp, ý nghĩa khoa học, kết quả tích cực, kết quả tiêu cực / hạn chế, bằng chứng và điều kiện kiểm chứng.
Không chứa vận hành (→ `02`) hay kế hoạch (→ `03`). Nguồn đầy đủ: `RESEARCH_LOG.md` Entry 1–9; lý thuyết `paper/hsi_theory.md` Mệnh đề 1–7;
báo cáo `paper/BAO_CAO_HSI.pdf`. Phát hiện của ý tưởng 1 và của các hướng trước: `history/01_SCIENTIFIC_FINDINGS_idea1_and_idea2-early.md`,
tóm tắt `07_IDEA1_SUMMARY.md`.*

## 0000000. Phiên 2026-11-06 — Entry 19–22: hợp lệ của luật đương nhiệm trên 3 nhóm mới, bí danh odometry không thấy được

**Luật đương nhiệm OWF-HWA-S5 trên ba nhóm seed mới (55–57, 58–60, 61–63; 432 run, đều đăng ký trước):**

| Nhóm | recall | TB segFAR | run > α | sai số (m) |
|---|---|---|---|---|
| 55–57 | 0.937 | 0.0045 | 1 | 12.5 |
| 58–60 | 0.934 | 0.0101 | 6 | 16.3 |
| 61–63 | 0.927 | 0.0043 | 2 | 12.9 |

Tổng 9/432 = 2.1 % run > α. 7 trong 9 là CMU, đến từ hai bố cục lỗ: seed 60 (nhánh HSI) và seed 61 (bậc đồng thuận OWF).

**Phát hiện (tích cực, cơ chế): bí danh mà odometry không thấy được** (`paper/owf_theory.md` §9, Mệnh đề 6).
- Truy từ các run > α: cả hai bố cục lỗ đều phủ một đoạn đường mà ở chỗ khác trên bản đồ có một "bản sao dịch chuyển".
  - Seed 60: lệch 204 m dọc chính con đường (slice 11–12).
  - Seed 61: lệch 673 m (slice 22 ↔ 24).
  - Độ lệch không đổi qua 10–17 lượt đi; hai descriptor độc lập chọn cùng chỗ (lệch nhau trung vị 4.9 m).
- Khớp yếu theo giá trị tuyệt đối: cos 0.34–0.45, so với 0.69–0.77 ở đúng chỗ.
- Nhưng dịch dọc một đường thẳng không quan sát được bằng odometry. Emission chuẩn hoá theo hồ sơ của frame có điểm giao ≈ 0.5 SD, nên bản
  sao tích luỹ không giới hạn.

**Bằng chứng nhân quả:** nâng điểm giao lên μ₁/2 (`--lu half`) chia 4.6 lần báo sai CMU của OWF đơn lẻ trên tập A. Run thiết kế CMU s60:
17 → 0 đoạn, sai số 6.8 → 2.7 m.

**Kết quả tiêu cực (đều có số đo):**
- NT (Entry 19, seed 58–60). Mệnh đề 5 đúng: Nordland điều hướng 19.1 → 13.5 m, TB segFAR 0.0101 → 0.0091. Nhưng không qua N1, vì cả R*
  cũng có 6/144 run > α. Trên seed 61–63 trượt N3 0.07 m.
- ℓ = L_vis (Entry 20, phát triển): −0.029 recall, 13 run > α. Tương quan bản đồ–bản đồ không phải tương quan bằng chứng truy vấn–bản đồ.
- OWF phủ quyết nhánh HSI (Entry 21, seed 61–63): TB segFAR −23 %, recall −0.005, điều hướng +0.9 m (countryside).
- Điểm giao μ₁/2 (Entry 22, phát triển): recall −0.030, Nordland tệ hơn. Một hằng số mỗi run sai mô hình khi điều kiện thay đổi.
- Phủ quyết chéo: hợp lệ nhất từng đo (TB segFAR 0.0012–0.0018), nhưng recall giảm 2.6–4.5 pp.
- Tự kiểm toán theo thời gian, luật toàn vẹn cục bộ, hiệu chỉnh tỉ lệ cho điều hướng: âm (ghi chú trong Entry 19).

**Ý nghĩa.** Thông tin loại được bí danh dịch chuyển nằm ở độ tương đồng TUYỆT ĐỐI (CMU: cos ở đúng chỗ, phân vị 5 % = 0.54, so với trung vị bí danh 0.44). Chuẩn
hoá z theo frame đã bỏ đi thông tin đó. Bước tiếp theo có nguyên tắc là một emission hiệu chỉnh tuyệt đối theo điều kiện.

## 000000. Phiên 2026-11-05 chiều — Entry 16 (âm), tính tổng quát của OWF-HWA-S5, chẩn đoán khoảng trống, engine GPU

**Engine GPU (công cụ, không phải đóng góp khoa học).** `owf.py --engine torch`: 2.7–3.4 ms/frame cho ngân hàng 10 bộ lọc trên một L4, so với
29 ms/frame numpy. Quyết định trùng numpy ở mọi ngưỡng. Nhờ vậy một đợt 657 run (OWF + OWF-H) chỉ mất 35 phút trên 6 phiên 4×L4.

**Entry 16 — âm: hiệu chuẩn conformal OWF trên null hồi cứu của chính run không thay được các bậc cố định.** Phát triển, tập A, 399 run:

| Biến thể | Recall | Run > α | Sai số điều hướng |
|---|---|---|---|
| INC (OWF-HWA-S5) | 0.933 | 1 | 12.7 m |
| HC (tốt nhất) | 0.906–0.916 | 23–46 | 14.7–17.2 m |

Cơ chế: split conformal ở mức α chỉ chặn KỲ VỌNG tỉ lệ đoạn null có báo. segFAR từng run vì thế dao động quanh α, trong khi INC vận hành
thấp hơn α khoảng 10 lần. Ngoài ra các đợt aliasing liên tiếp là thiểu số trong các đoạn null. Hệ quả cho lý thuyết: Mệnh đề 4 (bảo đảm biên
theo đoạn, `owf_theory.md` §6) đúng nhưng KHÔNG kiểm soát đuôi theo run.

Hai thử nghiệm nhỏ cùng hướng cũng âm:
- tầng theo tuổi bằng chứng làm cạn dữ liệu hiệu chuẩn;
- β (nhiệt độ emission) chọn theo evidence: evidence chọn β = 1.4, log-evidence tăng 3300, nhưng trên Nordland s1 segFAR tăng 0.038 → 0.064
  và sai số điều hướng tăng 15 → 51 m. LR sắc hơn làm aliasing tệ hơn.

Các biến thể bậc (bỏ điều kiện quãng đường, 2 hằng số thay cho 6) cho recall ±0.005 và thêm run vượt α. Lớp quyết định đã bão hoà.

**Chẩn đoán aliasing.** Trên Nordland, giả thuyết tự tin nhưng sai nằm sâu trong lỗ (≥ 32 excl từ đầu chuỗi, 82 % frame off-map), kéo dài
trung vị 2.3 excl và đạt khối lượng 1 − 1e-10. Đây là bằng chứng trực tiếp rằng giả định (E1) của Mệnh đề 2 bị vi phạm. Nó giải thích vì sao
cần ngưỡng cực đoan cố định.

**Tính tổng quát của OWF-HWA-S5** (các tập không dùng để chỉnh luật; H = nhánh OWF-H trên cùng run):

| Tập | Recall INC vs H | TB segFAR tệ nhất | Run > α (INC / H) |
|---|---|---|---|
| lỗ 10 % (108 run) | 0.933 vs 0.865 | 0.0077 | 1 / 0 |
| lỗ 50 % (108 run) | 0.894 vs 0.833 | 0.032 (CMU) | 4 / 4 (CMU, cùng run) |
| off-map tự nhiên 4Seasons (36 run) | 0.952 vs 0.889 | 0.0104 | 2 / 2 |
| NCLT (6 run) | 0.781 vs 0.753 | 0.0049 | 0 / 0 |

Đuôi hợp lệ còn lại thuộc nhánh HSI, không thuộc các bậc OWF. Tham chiếu: HSI-VN đạt 0.772 / 0.754 ở lỗ 10 % / 50 %, SH (ý tưởng 1)
0.748 / 0.696.

**Entry 17 — XÁC NHẬN trên seed mới 55–57 (đăng ký trước; 144 run, cùng run cho mọi luật).** Ô = recall / run > α / sai số (m):
- OWF-HWA-S5: **0.937 / 1 / 12.5**;
- HSI-VN: 0.806 / 0 / 15.0;
- TAO'26: 0.846 / 129 / 123.5;
- Xu'21: 0.691 / 75 / 57.5;
- Claxton'24: 0.732 / 99 / 48.4;
- oracle một-frame: 0.847.

C1–C4 đều đạt. Luật vượt oracle một-frame trên 7/8 dataset (Nordland 0.970 vs 0.675). Ngoại lệ là CMU: 0.841 vs 0.929.

**Độ phóng đại (E1) đo được** (`owf_theory.md` §7, Mệnh đề 2′): K̂(ε) = segFAR(ε) / (2ε) của OWF đơn lẻ ≤ 1 trên 4Seasons và St Lucia, tức cận
Ville đúng như phát biểu. Trên CMU / Nordland, K̂ tăng tới 10³–4·10⁴ khi ε giảm (aliasing đuôi nặng). Điều này giải thích vì sao cần bậc cực
đoan và nhánh HSI.

**VPR-Space (Entry 18, mô tả; 16 setup ngoài Trái Đất × 6 descriptor, off-map tự nhiên, giao thức theo thang τ của benchmark).**
- OWF-HWA-S5 hợp lệ (0/96 run > α) nhưng recall 0.292, thấp hơn oracle một-frame 0.562.
- Đối thủ: TAO'26 0.629 (24 run > α); Xu'21 / Claxton'24 (chỉnh bằng nhãn trên chính chuỗi) 0.498 / 0.441.
- Bộ ước lượng OWF tổng quát tốt: MAP đúng 0.70–1.00 frame on-map, vượt xa top-1 một-frame.
- Lớp quyết định thì không: HSI không khởi động trên chuỗi 54–1683 frame, các bậc cần ≥ 2–16 excl.
- OWF đơn lẻ không báo sai ở MỌI ε (0.733 ở ε = 0.2): K ≈ 0 ở đây, so với 10³–10⁴ trên CMU/Nordland, nên ε cố định không hợp cả hai.
- Không chọn ε sau khi xem số liệu. Hướng tiếp: cận K theo bản đồ (`03` §6a).

**Khoảng trống recall còn lại (tập A, nhãn chỉ để chẩn đoán).**
- CMU: ảnh MAP của OWF đúng 0.95–0.99 frame on-map ở mọi khoảng cách từ đầu chuỗi, nhưng chỉ 0.53–0.94 được báo. Phần bị bỏ = 0.125
  frame on-map, tức toàn bộ khoảng cách recall của CMU. Mọi chuỗi CMU đều < 16 excl.
- Countryside: khoảng trống nằm ở chuỗi dài (OWF đúng 0.912, báo 0.844). Các frame đúng bị bỏ có khối lượng trung vị chỉ 0.70, nên nút thắt
  là độ sắc của bộ ước lượng dưới VIO trôi, không phải lớp quyết định.
- Báo vị trí trung bình hậu nghiệm thay cho ảnh bản đồ không giảm sai số điều hướng: sai số fix trung vị chỉ 2.3–2.5 m; sai số điều hướng
  đến từ khoảng dead-reckoning trong lỗ.

## 00000. AUTOLOOP Entry 15 — ngân hàng tỉ lệ 5 mức (OWF-HWA-S5, luật khuyến nghị hiện tại)

**Chẩn đoán.** Đo độ dài bước odometry so với GNSS: VIO 4Seasons lệch tỉ lệ ngoài ±3 %. Countryside 1.04 (P10–P90 1.03–1.07), office 1.04, old town
0.94. Trôi hướng nhỏ (< 0.6°/km), nên không cần ngân hàng hướng.

**Thay đổi.** Lưới tỉ lệ {0.94, 0.97, 1, 1.03, 1.06} thay cho {0.97, 1, 1.03}; chọn trực tuyến theo evidence như cũ.

**Kết quả (đăng ký trước, seed 52–54).** 0.941 vs OWF-HWA-S 0.937 (+0.0045, CI [+0.0024, +0.0070]), 1/144 run > α (cùng run CMU với mọi luật kể cả
HSI-VN), 12.67 vs 13.11 m. Gain nằm đúng ở các dataset VIO: countryside +0.026, old town +0.009 (22.1 vs 24.6 m); các dataset khác ±0.001.

**Tổng kết vòng lặp.** Trên nhóm cuối (seed 52–54), luật hiện tại so với HSI-VN (luật khuyến nghị lúc bắt đầu vòng lặp): recall **0.941 vs 0.823
(+0.118)**, cùng số run > α, sai số điều hướng 12.67 vs 14.32 m. Theo dataset: old town +0.193, countryside +0.180, Nordland +0.146, Oxford +0.132,
office +0.094, Boreas +0.086, CMU +0.063, St Lucia +0.049. Hạn chế: điều hướng Nordland (6.3 vs 3.6 m) và countryside (24.0 vs 24.3 m) không tốt hơn
HSI-VN; chưa kiểm trên NCLT (off-map tự nhiên).

## 0000. AUTOLOOP Entry 14 — bậc đồng thuận ba nguồn (OWF-HWA-S, luật khuyến nghị hiện tại)

**Chẩn đoán.** Trên tập A, chuỗi lai đúng 0.959 khung trong bản đồ nhưng chỉ báo đúng 0.899. CMU có ~130 chuỗi ngắn ~7.5·excl mỗi run, nên mọi khung
thiếu đều ở đầu chuỗi, nơi không bậc nào có hiệu lực.

**Cơ chế.** Ba bộ ước lượng có kiểu lỗi khác nhau:
- OWF: thế giới mở, metric.
- Chuỗi tô-pô: HMM thế giới đóng, bị ép chọn một nút.
- Truy hồi top-1: một khung.

Khi ngoài bản đồ, cả ba chỉ cùng một ảnh sai VÀ OWF tự tin là hiếm. Riêng bậc này có TB segFAR ≤ 0.003 trên mọi dataset phát triển. Đòi đồng
thuận chỉ hai nguồn (bỏ top-1) thì kém an toàn hơn; đòi đồng thuận liên tục L khung không cải thiện biên ε.

**Kết quả (đăng ký trước, seed 49–51).** 0.933 vs OWF-HW-S 0.921 (+0.012, CI [+0.010, +0.014]), thắng 144/144 run, 0 run > α, 13.64 vs 13.78 m.
CMU 0.832 → 0.874; tăng trên cả 8/8 dataset.

## 000. AUTOLOOP Entry 12–13 — OWF-HU, rồi OWF-HW-S (luật khuyến nghị hiện tại)

**Entry 12 — OWF-HU** = OWF-H ∨ (khối lượng OWF ≥ 1 − 1e-5 và đã đi ≥ 16·excl). Cơ chế: trên Nordland và old town, bộ lọc thế giới mở báo được nhiều
fix đúng hơn lớp quyết định HSI. Khi đã ổn định, khối lượng đĩa cực cao là đủ an toàn. Tập mới seed 43–45: 0.896 vs OWF-H 0.878 (+0.018, CI
[+0.014, +0.022]), 1/144 run > α, 14.94 vs 15.73 m.

**Entry 13 — OWF-HW-S.** Hai thay đổi, cả hai đều có lý do cơ chế:
- *Ngân hàng tỉ lệ odometry:* VIO của 4Seasons lệch tỉ lệ 3–7 % so với GNSS (countryside 1.04, old town 0.94); odometry mô phỏng lệch ~3 %.
  Sáu bộ lọc (q × tỉ lệ) được chọn trực tuyến theo evidence tích luỹ.
- *Bậc sớm cực chặt:* (≥ 1 − 1e-8 sau 2·excl) mở được đầu các chuỗi ngắn của CMU.

Tập mới seed 46–48: **0.902** vs OWF-HU 0.878 (+0.024, CI [+0.019, +0.031]), 1/144 run > α, 12.75 vs 13.61 m. Tách đóng góp trên cùng run:
- hợp hai bậc +0.011 (CMU 0.603 → 0.676);
- ngân hàng tỉ lệ +0.013 (countryside +0.057, old town +0.018).

**Hạn chế còn lại.** CMU (0.68 trên seed 46–48): mỗi run có ~130 chuỗi ngắn ~7.5·excl, và chẩn đoán oracle cho thấy chuỗi lai đúng trên 0.96 khung
nhưng đầu chuỗi chưa được báo. Countryside: chuỗi tốt nhất chỉ đúng 0.87 (VIO trôi). Nhóm seed 46–48 có recall thấp hơn hai nhóm trước ở MỌI luật
(HSI-VN 0.786), nên chỉ so sánh trong cùng nhóm.

## 00. Entry 11 — OWF-H (luật khuyến nghị mới)

**Đóng góp.** Ghép bộ ƯỚC LƯỢNG OWF (vị trí đúng hơn: MAP trong excl ở 0.87–1.00 frame on-map) với lớp QUYẾT ĐỊNH HSI (tự hiệu chuẩn trên
excursion thật, hợp lệ từng run). Phát hiện cơ chế: ghép thẳng làm vỡ HSI (CMU segFAR 0.089) vì chứng chỉ hình học của HSI ("chuỗi khớp
odometry") bị lừa bởi quỹ đạo dead-reckoning của OWF — luôn khớp odometry kể cả khi sai; sửa: chỉ giao chuỗi OWF khi OWF tự tin (≥ 0.9) VÀ đã
ổn định (≥ 16·excl từ đầu chuỗi), còn lại giữ chuỗi topo tự do. Lân cận (t, D) phẳng (phát triển: Score 0.866–0.871, mọi biến thể hợp lệ).
**Kết quả (đăng ký trước, tập mới seed 40–42, 144 run):** recall 0.885 vs HSI-VN 0.811 (+0.074, CI [+0.060, +0.088]); thắng 7/8 dataset (Nordland
+0.112, old town +0.105, Oxford +0.104, Boreas +0.081, countryside +0.077, office +0.069, St Lucia +0.040; CMU hoà); 1/144 run > α (cùng run với
HSI-VN); điều hướng gộp 14.46 vs 15.35 m (Boreas 2.8 vs 7.5). **Hạn chế:** CMU không cải thiện (đầu chuỗi phủ gần hết chuỗi ngắn); điều hướng
countryside 30.4 vs 23.6 m.

## 0. Entry 10 — ý tưởng 2b: bộ lọc thế giới mở (OWF) — đọc trước §1 nếu cần số mới nhất

**Đóng góp.** Đổi BỘ ƯỚC LƯỢNG chứ không đổi lớp quyết định: trạng thái là vị trí trên lưới mét phủ cả vùng có bản đồ và vùng trống (+ trạng thái
xa Ω); chuyển trạng thái bảo toàn khối lượng (khối lượng đi vào lỗ được dead-reckon qua lỗ thay vì bị dồn về các nút bản đồ); emission là tỉ số
hợp lý tự chuẩn hoá (LR = 1 ở ô trống); hiện diện là HÀM của vị trí; báo khi khối lượng hậu nghiệm trong đĩa excl ≥ 1 − 1e-3. Lý thuyết
(`paper/owf_theory.md`): Mệnh đề 1 (niềm tin khuếch tán không bị kéo về bản đồ), Mệnh đề 2 (cận Ville cho báo sai trong một đoạn off-map —
không có số hạng mép; đầu chuỗi là trường hợp yếu), Mệnh đề 3 (rời bản đồ quyết định bằng dead-reckoning so với vùng phủ). Chẩn đoán dẫn tới ý
tưởng: chuỗi vị trí topo đúng ở 0.78–0.95 frame on-map nhưng lớp quyết định (SH) chỉ báo 0.51–0.80.

**Tích cực (đăng ký trước, Entry 10).** Tập A (404 run chưa từng xem với OWF): recall gộp **0.863** vs HSI-VN 0.791 vs SH 0.726; cao hơn HSI-VN
trên 8/9 dataset (gộp +0.072, CI [+0.061, +0.083]) và hơn SH 8/9; TB segFAR ≤ 0.05 trên 9/9; **kiểm toán vị trí đạt mọi lớp, mép ≤ 0.003 mọi
dataset** (ý tưởng 1: 0.08–0.11 ở Boreas / old town). Sai số điều hướng tốt nhất trên Boreas (3.1 m vs SH 4.5, HSI-VN 7.0), old town (21.6 vs 26.1
/ 33.0), Oxford, St Lucia, NCLT. Tập quyết định mới (seed 25–27, 108 run): D1 hợp lệ đạt (3/108 run > α), D2 recall +0.076 so với HSI-VN (CI
[+0.054, +0.099]).

**Tiêu cực.** (a) **D3 trượt** — sai số điều hướng ≤ HSI-VN + 1 m chỉ 2/6 dataset ⇒ HSI-VN giữ nguyên là luật khuyến nghị. Nguyên nhân (chẩn
đoán): vài fix sai XA sau khi hậu nghiệm nhảy sang một đoạn giống (Nordland 0.6 % fix, CMU 0.8 %) và fix thô / quá tự tin dưới VIO trôi
(countryside: 7.8 % fix > excl, 23 % fix 10–25 m). (b) Đuôi hợp lệ: 19/404 run > α (CMU 14 — khởi đầu toàn cục trên chuỗi ngắn; Nordland 5 —
chuỗi bắt đầu trong lỗ), HSI-VN 0. (c) CMU recall 0.758 < SH 0.834 (= HSI-VN 0.756). (d) countryside recall < HSI-VN (−0.025). (e) ε = 0.01 không
an toàn (CMU, Nordland 0.06). (f) Chi phí 6–36 ms/frame trên Kaggle CPU (3 bộ lọc), vượt mục tiêu 15 ms.
**Cơ chế (ablation, 26 run mỗi biến thể):** bỏ ô trống (thế giới đóng — bản tương tự topo với cùng emission / chuyển động) ⇒ 26/26 run vượt α
(segFAR 0.297); bỏ trọng số theo quãng đường ⇒ 26/26 (0.606); chọn q trực tuyến +0.020 recall; kidnap ≈ 0 +0.034 recall. **Độ bền tỉ lệ lỗ**
(216 run): lỗ 10 % recall 0.872 (SH 0.748, HSI-VN 0.772), 7/108 run > α (CMU TB 0.0502 — vượt α); lỗ 50 % 0.794 (0.696, 0.754), 3/108; Nordland
lỗ 50 % sai số 40.5 m.
**Đã thử và bác trong thiết kế (seed 0):** không trọng số bằng chứng theo quãng đường (FL 0.80); prior đều trên dải (khởi đầu chậm); kidnap 1e-4
(hạt giống của bóng ma 170 m ở Boreas); trọng số theo tương quan profile (r = 0.98–0.998 ⇒ quá mạnh); dải ×2 / ×4 (vô ích); q cố định (mỗi giá trị
hỏng một nơi). Sau tập A (chẩn đoán): cổng nhảy dead-reckoning — Nordland tốt hẳn, CMU không đổi, countryside xấu đi.

## 1. Bài toán và giao thức (để đọc số liệu đúng)

Robot camera đơn + odometry định vị trên bản đồ ảnh bằng một bộ lọc chuỗi vị trí HMM (MAP `est_c`, dùng chung cho mọi luật). Mỗi frame: báo
hay không báo fix cho bộ lọc điều hướng Kalman. Bản đồ có lỗ: 30 % ô 300 m bị xoá (tập lỗ 10 % / 50 % để thử độ bền); NCLT và 4Seasons chéo cảnh
có off-map tự nhiên. Thước đo: **recall** (frame on-map báo fix đúng trong excl / frame on-map), **segFAR** (tỉ lệ đoạn off-map H = 10 frame có ≥ 1
báo; mục tiêu ≤ α = 0.05), **FL**, **sai số điều hướng TB** (m), **kiểm toán theo vị trí** (lớp start / edge / deep ≤ 0.07). Không dùng nhãn khi
triển khai. Tham chiếu: SH và CST-JS của ý tưởng 1 (phẫu thuật bản đồ phản thực) trên CÙNG (dataset, descriptor, seed); Xu'21 và Claxton'24
(dùng nhãn); oracle (chỉ báo khi top-1 đúng). 9 dataset (Boreas, CMU, Nordland, 4Seasons office/old town/countryside, NCLT, Oxford, St Lucia) ×
6 descriptor (CosPlace, NetVLAD, MegaLoc, DINOv2, SALAD, MixVPR).

## 2. Đóng góp

| # | Đóng góp | Nội dung | Bằng chứng chính |
|---|---|---|---|
| C1 | **Chứng chỉ hình học bất biến điều kiện ảnh** | chuỗi vị trí khớp odometry ở mọi độ trễ 10–80 m (sau phép quay tốt nhất ≤ 20°, cửa sổ theo mét) + tham chiếu tin cậy nhất quán qua dead-reckoning (loại tuyến dịch cứng) | P(fix đúng \| neo) ≥ 0.993 (28/28 run thiết kế); chứng chỉ một mình **0/773 run vi phạm** trên mọi tập |
| C2 | **Nhãn hồi cứu tự sinh, kể cả lớp off-map** | cầu dead-reckoning hai phía (trộn, bất định kiểu cầu Brown, κ và s0 ước lượng không nhãn) giữa các đoạn đã xác minh + vùng phủ đã biết của bản đồ | nhãn off-map chính xác 1.000 khi odometry tốt, 0.88–0.93 với VIO / Segway trôi; nhãn đúng ≥ 0.99 |
| C3 | **Hiệu chuẩn conformal trên excursion THẬT của chính lần triển khai** | điểm học (GBM online) + ngưỡng split conformal trên đoạn null hồi cứu giữ ra ⇒ P(báo trong một đoạn null mới) ≤ α (Mệnh đề 4) | hợp lệ ở mọi tập; quét α: segFAR thực ≤ α ở mọi mức |
| C4 | **Chứng nhận rồi hiệu chuẩn** (Mệnh đề 6) | frame có chứng chỉ neo cầu hồi cứu và không bị tính vào α; nếu không, cầu dài trôi xa làm null nhiễm fix đúng và chứng chỉ báo đúng ở đó bị tính là vi phạm | NCLT: 6–13 % frame xác minh hồi cứu vs 28–42 % có chứng chỉ; chứng chỉ báo trong null ∩ off-map thật = 0.000, trong null ∩ fix đúng = 0.52–0.58; NCLT +0.068 |
| C5 | **Vách khoá hiệu chuẩn và căn chỉnh Neyman–Pearson** (Mệnh đề 7) | ngưỡng = phân vị của max điểm theo đoạn, điểm bão hoà ⇒ nhánh học TẮT HẲN khi > α đoạn null có một frame được phép báo; sửa: học điểm với âm = chính null hiệu chuẩn (đơn vị huấn luyện) | run CMU bị khoá 27 → 1 / 60 (phát triển); tập mới: 18 → 9 / 36, recall +0.015 (CI [+0.010, +0.020]) |
| C6 | **Đánh giá có đăng ký trước trên dữ liệu chưa từng thấy** | 9 vòng, mỗi vòng commit tiêu chí trước khi xem; ba tập kiểm tra sinh SAU quyết định (seed 10–12, 13–15, 16–18) | quyết định cuối (HSI-VN) dựa trên tập seed 16–18 đạt 4/4 tiêu chí |

**Ý nghĩa.** (i) Một robot có thể tự gán nhãn quá khứ của mình — kể cả lớp off-map, lớp không bao giờ có nhãn khi triển khai — chỉ bằng hình
học và odometry, rồi dùng nhãn đó để học và hiệu chuẩn quyết định tin thị giác, không cần nhãn, không can thiệp bản đồ, ~1 ms/frame trên 1 lõi
CPU. (ii) Hai nguyên lý tổng quát cho giám sát toàn vẹn tự giám sát: phần đã có chứng chỉ không được phán xét bằng nhãn kém tin cậy hơn chính nó
(C4); điểm học được phải được huấn luyện chống lại đúng phân phối null dùng để hiệu chuẩn, nếu không hiệu chuẩn có thể sụp kiểu bậc thang (C5).
(iii) Novelty (Gate 17, `LITERATURE_GATE.md`): gần nhất Lajoie & Beltrame RA-L'23, TF-VPR, Carson'23, Claxton'24, ACI với phản hồi trễ; mới là
nhãn off-map hồi cứu, dùng online trong cùng lần triển khai, hiệu chuẩn trên excursion thật, C4 và C5.

## 3. Kết quả tích cực

**Luật khuyến nghị HSI-VN** (`analysis/hsi_eval.py` VARIANTS["HSI-VN"]).

Phát triển — 413 run seed 0–9 (recall / segFAR TB / run > α / sai số m):

| dataset | n | HSI-VN | HSI-rot-m-sc (luật trước) | HSI-VMN | SH (ý tưởng 1) | oracle |
|---|---|---|---|---|---|---|
| countryside | 56 | 0.665 / 0.0066 / 0 / 26.6 | 0.642 / 0.0050 / 0 / 26.8 | 0.655 / 0.0019 / 0 / 23.5 | 0.492 / 0.0006 / 0 / 33.5 | 0.739 |
| office | 56 | 0.873 / 0.0000 / 0 / 8.9 | 0.872 / 0.0001 / 0 / 9.0 | 0.854 / 0.0000 / 0 / 8.9 | 0.803 / 0.0003 / 0 / 9.7 | 0.914 |
| old town | 56 | 0.731 / 0.0014 / 0 / 32.5 | 0.735 / 0.0008 / 0 / 31.6 | 0.720 / 0.0004 / 0 / 29.0 | 0.708 / 0.0057 / 1 / 25.9 | 0.844 |
| Boreas | 56 | 0.896 / 0.0014 / 0 / 6.8 | 0.892 / 0.0014 / 0 / 6.9 | 0.885 / 0.0002 / 0 / 3.9 | 0.777 / 0.0023 / 0 / 4.5 | 0.882 |
| CMU | 56 | 0.761 / 0.0043 / 0 / 3.6 | 0.652 / 0.0060 / 0 / 3.8 | 0.753 / 0.0040 / 0 / 3.5 | 0.835 / 0.0092 / 1 / 3.9 | 0.945 |
| NCLT | 2 | 0.645 / 0 / 0 / 3.2 | 0.577 / 0 / 0 / 5.1 | 0.634 / 0 / 0 / 3.2 | 0.690 / 0 / 0 / 3.2 | 0.784 |
| Nordland | 56 | 0.786 / 0.0001 / 0 / 5.6 | 0.785 / 0.0000 / 0 / 5.0 | 0.777 / 0.0000 / 0 / 5.0 | 0.770 / 0.0000 / 0 / 6.0 | 0.676 |
| Oxford | 45 | 0.805 / 0.0089 / 0 / 21.1 | 0.764 / 0.0059 / 0 / 21.4 | 0.799 / 0.0068 / 0 / 20.4 | 0.719 / 0.0039 / 0 / 21.9 | 0.899 |
| St Lucia | 30 | 0.915 / 0.0013 / 0 / 18.5 | 0.905 / 0.0018 / 0 / 18.8 | 0.912 / 0.0011 / 0 / 18.4 | 0.761 / 0.0006 / 0 / 25.5 | 0.896 |
| **gộp** | 413 | **0.796** / 0.0029 / **0** / 15.1 | 0.772 / 0.0026 / 0 / 15.0 | 0.786 / 0.0017 / 0 / **13.6** | 0.731 / 0.0029 / 2 / 15.6 | 0.845 |

Theo giả thuyết H1–H5 so với SH (`analysis/hsi_summary.py`): H1 hợp lệ 0/413; H2 ≥ SH trên 7/9 dataset, gộp **+0.065**; H3 DINOv2 + NetVLAD
**+0.118**; H4 điều hướng trong +1 m của SH trên 7/9; H5 kiểm toán theo vị trí ≤ 0.07 trên 9/9 (ý tưởng 1 không đạt). Tham chiếu có nhãn: Xu'21
202/413 run vượt α, Claxton'24 287/413.

**Tập kiểm tra mới** (sinh sau quyết định; không có SH vì cần GPU; so với luật trước HSI-rot-m-sc trên cùng run):

| tập | HSI-VN vi phạm | Δ recall (CI 95 %) | Δ CMU | run CMU khoá | Δ sai số | Xu'21 / Claxton'24 vượt α |
|---|---|---|---|---|---|---|
| seed 13–15 (Entry 8) | 0/108 | +0.016 [+0.009, +0.024] | +0.059 | 7 → 4 | −0.58 m | 44 / 77 trên 108 |
| seed 16–18 (Entry 9) | 0/108 | +0.014 [+0.008, +0.020] | +0.050 | 11 → 5 | −0.49 m | 49 / 81 trên 108 |
| gộp 216 run | 0/216 | +0.015 [+0.010, +0.020] | +0.055 | 18 → 9 | −0.53 m | — |

**Bền** (phát triển, mọi run): lỗ 10 % — 0/108, recall 0.772 (luật trước 0.755); lỗ 50 % — 4/108 (đều CMU, bằng luật trước), 0.754 vs 0.744;
off-map tự nhiên 4Seasons chéo cảnh — 0/36 (luật trước 1/36). **Quét α** (`paper/figures/hsi_alpha_vn.png`): segFAR thực TB 0.0011 / 0.0014 /
0.0027 / 0.0035 / 0.0046 ở α = 0.01 / 0.02 / 0.05 / 0.1 / 0.2; recall HSI-VN cao hơn luật trước ở MỌI α (0.727 / 0.758 / 0.796 / 0.808 / 0.812 vs
0.707 / 0.733 / 0.772 / 0.799 / 0.811). **Chi phí:** ~1 ms/frame trên 1 lõi CPU (đặc trưng + học lại GBM + hiệu chuẩn); ý tưởng 1 cần 18–45
ms/frame trên GPU.

## 4. Kết quả tiêu cực và hạn chế (đều có số đo)

**Điểm yếu còn lại.** (a) **CMU** 0.761 vs SH 0.835 (oracle 0.945). Chuỗi CMU ngắn (trung vị 194 m), quãng tới chứng chỉ đầu tiên trung vị
~110 m; phần khoá còn lại do vài chuỗi ngắn (16–71 m) HOÀN TOÀN đúng nhưng không thể chứng nhận nằm trong null — đặc trưng không phân biệt được
chúng với dương ⇒ giới hạn thông tin của khung hiện tại. Khởi động lạnh: 3–4 % frame CMU trước lần học đầu, bị giới hạn bởi độ trễ có nhãn hồi
cứu (hạ ngưỡng nhãn tối thiểu 50 → 20 không đổi gì). (b) **NCLT** chỉ 2 run giữ ra (một bản đồ, 8 phiên; mỗi descriptor seed 0). (c) **Sai số
điều hướng old town** 32.5 m vs SH 25.9 (oracle 19.3): KHÔNG có fix sai xa nào; nguyên nhân là thời điểm báo (VIO trôi ~6 %/100 m, khoảng trống
sau khi quay lại bản đồ) — HSI-VMN giảm còn 29.0. (d) **Null bảo thủ 5–25×** (là tập cha của off-map) — đúng nhưng tốn recall.

**Hướng đã thử và bác (bằng chứng):**

| hướng | kết quả đo | lý do bác |
|---|---|---|
| cấu hình cửa sổ theo frame (Entry 1) | Oxford 0.285, St Lucia 0.447 vs SH 0.72 / 0.76 | 10 m/frame ⇒ cửa sổ quá dài; sửa bằng cửa sổ theo mét (Entry 2) |
| Mondrian theo chế độ tham chiếu (Entry 4, HSI-M) | recall −0.008, sai số −1.1 m | trượt H8; giữ làm điểm vận hành điều hướng |
| bỏ / thu cổng nhất quán ngắn hạn (Entry 6) | recall +0.02…+0.03 nhưng sai số +1.7…+3.2 m (old town 45 m), 9/413 run > α | cổng chặn fix sai xa trong bản đồ; tập thiết kế 28 run không lộ cái giá |
| phán xét chứng chỉ bằng cầu không dùng nó / leave-one-run-out (Entry 5) | mất lợi ích NCLT / chuỗi CMU ngắn không có đoạn neo lân cận | |
| tách ngân sách α cho hình học (split budget) | NCLT 0.551 → 0.524 | null "chắc chắn" vẫn nhiễm 10 % fix đúng |
| đặc trưng hubness theo nơi (Entry 8) | 1 % nơi hút 36–46 % fix sai (R² theo nơi 0.48–0.77) nhưng recall gần như không đổi, không mở khoá | ngưỡng không phải nút thắt ở chỗ đặc trưng giúp được |
| chứng chỉ cửa sổ ngắn "học từ chuỗi dài" | lỗi thật ở L = 20 m: 2–50 % (countryside tệ nhất); ước lượng thầy 0.005 vs thật 0.097 (CMU SALAD s4) | thầy thiên lệch về vùng dễ ⇒ không an toàn |
| chứng chỉ tự đồng dạng của bản đồ K(p, ℓ) | K = 0 gần như không xảy ra ở ℓ ≤ 30 m | ở thang 20–40 m đường gần thẳng, hình học không mang thông tin |
| Mondrian theo trạng thái bằng chứng (đầu chuỗi) | mở khoá SALAD s4 nhưng SALAD s2 0.921 → 0.798 | gộp hay tách ngân sách không trội nhau |
| hiệu chuẩn chụm lỗi ngắn (< H) | fix sai xa nằm trong chuỗi sai dài 14–760 frame, đã thuộc null | giả thuyết sai |
| quét α như "bảo đảm chặt" | bảo đảm đúng nhưng bảo thủ; α = 0.01 có 6–9 / 413 run > 0.01 | rời rạc khi ít đoạn hiệu chuẩn |

**Giả định của bảo đảm.** Hoán đổi giữa đoạn null hồi cứu và đoạn off-map thật (null là tập cha ⇒ bảo thủ khi nhãn đúng); gộp phiên ⇒ hoán đổi
giữa điều kiện chỉ xấp xỉ; ε_G (sai của chứng chỉ) không hiệu chuẩn được mà là tính chất phép thử hình học — đo trực tiếp bằng biến thể geo-rm
(0/773).

## 5. Điều kiện kiểm chứng (để tái tạo đúng số)

- **Dữ liệu:** cache `nav_demo --cache` công khai: `nhatlong1103/hmm-navcache-v2` (7 dataset × 6 descriptor × seed 0–9, NCLT seed 0),
  `nhatlong1103/hmm-e37-caches` (Oxford, St Lucia), `nhatlong1103/hmm-navcache-holes` (`d10/`, `d50/`, seed 0–2), `nhatlong1103/hmm-natural-cache`
  (4Seasons chéo cảnh), `caotienminh1/hmm-navcache-f13` (seed 13–15), `caotienminh1/hmm-navcache-f16` (seed 16–18); kho dự trữ seed 19–27
  (`caotienminh1/hmm-navcache-r19`, chưa dùng). Mã tái tạo đúng từng bit cache công khai (đã kiểm Nordland DINOv2 seed 0); hai lần sinh độc lập
  seed 10–12 cho kết quả giống hệt.
- **Phân chia:** thiết kế = seed 0 × {CosPlace, NetVLAD, MegaLoc, DINOv2} của 7 dataset (28 run); phát triển = seed 0–9 (413 run có SH); tập kiểm tra
  = seed 10–12 (đã dùng C1–C4, Entry 7), 13–15 (Entry 8), 16–18 (Entry 9). α = 0.05, H = 10, một cấu hình chung cho mọi dataset.
- **Kết quả thô:** `analysis/results/hsi/hsi_results_json.tgz` (JSON mỗi run: main, holes_d10, holes_d50, natural, fresh_s10_12, test_s13_15,
  test_s16_18), mặt nạ báo theo frame `hsi_frames_*.tgz`; baseline ý tưởng 1 `analysis/results/baselines_idea1/e37|e38/oc_*.tgz`.
- **Lệnh:** một run `python3 analysis/hsi_eval.py <cache_dir> <ds> <desc> <seeds> --variants HSI-VN,HSI-rot-m-sc,geo-rm`; so sánh
  `analysis/hsi_compare.py`; tiêu chí đăng ký trước `analysis/hsi_entry8_test.py`; H1–H5 `analysis/hsi_summary.py`; quét α `analysis/hsi_alpha.py`.
