# Báo cáo Entry 10 — Bộ lọc thế giới mở (OWF): hiện diện suy từ vị trí, không phải từ phép thử

*Branch `hmm-2nd-idea`, 2026-11-04. Ý tưởng 2b. Mã: `analysis/owf.py`; lý thuyết: `paper/owf_theory.md`; nhật ký và đăng ký trước:
`RESEARCH_LOG.md` Entry 10; novelty: `LITERATURE_GATE.md` Gate 18. Bảng sinh bằng `analysis/owf_summary.py` từ JSON mỗi run
(`analysis/results/owf/`).*

## 1. Tóm tắt

@@ABSTRACT@@

## 2. Bài toán, giao thức và các đối thủ

Robot camera đơn + odometry đi trên bản đồ ảnh có lỗ (30 % ô 300 m bị xoá; Nordland khối 200 frame; NCLT off-map tự nhiên). Mỗi frame: báo
hay không báo một fix vị trí cho bộ lọc điều hướng Kalman. Thước đo: recall (frame on-map được báo fix trong excl / frame on-map), segFAR
(tỉ lệ đoạn off-map H = 10 frame có ≥ 1 báo; mục tiêu ≤ α = 0.05), sai số điều hướng TB, kiểm toán theo vị trí (start / edge / deep ≤ 0.07),
không nhãn khi triển khai. Đối thủ trên CÙNG run (cùng lỗ, odometry, truy vấn): ý tưởng 1 — SH (CMS-CPC/H+SH+G+NGRr), CST-JS, CST-F (phẫu
thuật bản đồ phản thực, hiệu chuẩn trên null sinh từ luồng); ý tưởng 2a — HSI-VN (tự giám sát hồi cứu bằng hình học + conformal trên
excursion thật). Cả ba đều dùng CHUNG bộ lọc vị trí topo (DiagFilter, `est_c`) và chỉ khác ở lớp quyết định.

## 3. Chẩn đoán dẫn tới ý tưởng

Trên `hmm-navcache-v2` (seed 0–2, cả 6 descriptor; nhãn chỉ để chẩn đoán), MAP của chuỗi vị trí topo nằm trong excl ở 0.78–0.95 frame
on-map, nhưng luật tốt nhất của ý tưởng 1 chỉ báo 0.51–0.80 và HSI-VN (phát triển) 0.65–0.92:

| Dataset | MAP chuỗi đúng | top-1 đúng | SH recall |
|---|---|---|---|
| Boreas | 0.931 | 0.885 | 0.779 |
| NCLT | 0.775 | 0.724 | 0.612 |
| CMU | 0.940 | 0.914 | 0.764 |
| Nordland | 0.928 | 0.661 | 0.752 |
| office | 0.946 | 0.910 | 0.795 |
| old town | 0.874 | 0.837 | 0.687 |
| countryside | 0.800 | 0.733 | 0.513 |

Ngưỡng ORACLE theo nhãn trên điểm từng frame (khối lượng hậu nghiệm, log-odds, max-sim, hậu nghiệm off-map của Xu'21) chỉ đạt 0.10–0.77 ở
segFAR = 0.05; frame trong 40 frame sau khi vào bản đồ hoặc đầu chuỗi chỉ chiếm 2–5 % (CMU 24 %). Vậy recall mất ở các đoạn on-map dài có bằng
chứng ảnh yếu. **Nguyên nhân cấu trúc:** trong HMM topo, nhân chuyển trạng thái được chuẩn hoá lại trên các nút bản đồ còn lại, nên niềm tin
của robot đi vào lỗ không có chỗ nào để ở ngoài các nút bản đồ; lớp quyết định phải phân biệt *thống kê* "trên bản đồ, bằng chứng yếu" với
"trong lỗ" — toàn bộ cơ chế hiệu chuẩn của ý tưởng 1 và lớp học của HSI dành cho việc này, và cả hai đều yếu ở mép lỗ / đầu chuỗi.

## 4. Phương pháp

- **Trạng thái:** vị trí robot trên lưới mét (ô g = excl / 5; Nordland 1 frame) phủ hộp bao của bản đồ nới thêm một dải B (= khối cấu hình:
  300 m; Nordland 200 frame; NCLT 100 m) + một trạng thái xa Ω không vị trí. Ô *có bản đồ* khi chứa ≥ 1 ảnh. **Hiện diện trên bản đồ là hàm
  của vị trí** — không có chuỗi hiện diện, không có nút off-map.
- **Chuyển trạng thái bảo toàn khối lượng:** dịch theo odometry (chỉ dịch nguyên ô, phần lẻ giữ ở pha φ ⇒ không khuếch tán số), mờ Gauss
  phương sai q|u| + drift²(2L_s|u| + |u|²) (trôi hệ thống tăng tuyến tính từ lần định vị chắc chắn gần nhất); khối lượng đi vào lỗ ở lại
  trong lỗ và được dead-reckon qua lỗ; ra ngoài dải ⇒ Ω (quay lại với tốc độ 0.01/frame theo prior); xác suất "bắt cóc" 1e-12.
- **Emission là tỉ số hợp lý so với một tham chiếu chung:** ô không có bản đồ và Ω: LR = 1. Ảnh i: z_i = điểm z bền của độ tương đồng
  trong chính profile của frame trên toàn bản đồ; log L_i = z_i − log mean_j exp(z_j) ⇒ trung bình LR trên bản đồ đúng bằng 1 (profile
  của frame là null của nó). Bằng chứng tính theo quãng đường: trọng số min(1, |u|/ℓ), ℓ = 0.4 excl.
- **Prior:** 0.5 trên các ảnh bản đồ, 0.1 cho Ω, phần còn lại đều trên dải.
- **Tự hiệu chuẩn nhiễu odometry trực tuyến:** ba bộ lọc q ∈ {0.005, 0.02, 0.08}·excl chạy song song, mỗi frame dùng bộ có log-evidence tích
  luỹ lớn nhất (nhân quả).
- **Quyết định:** đĩa bán kính excl quanh một trong 12 ô có bản đồ nặng nhất có khối lượng hậu nghiệm lớn nhất; fix = ảnh bản đồ gần trung
  bình hậu nghiệm trong đĩa; báo khi khối lượng đĩa ≥ 1 − ε, ε = 1e-3 (đường cong quét ε).
- **Chi phí:** một lượt lọc tiến mỗi bộ lọc; không mô phỏng, không phẫu thuật bản đồ, không học, không dữ liệu hiệu chuẩn, không nhãn.

## 5. Lý thuyết (tóm tắt; chứng minh ở `paper/owf_theory.md`)

- **Mệnh đề 1 (không kéo ròng một niềm tin khuếch tán):** nếu niềm tin dự đoán trên các ảnh là đều, tổng khối lượng có bản đồ sau cập nhật
  giữ nguyên với MỌI frame (trung bình LR = 1): robot chưa biết mình ở đâu chỉ đổi khối lượng có bản đồ qua HÌNH DẠNG profile, không qua mức.
- **Mệnh đề 2 (báo sai trong một đoạn off-map, Ville):** nếu LR có trọng số của mọi ô gần bản đồ là e-value có điều kiện khi robot ở nơi khác
  (E1), thì P(có báo trong đoạn) ≤ ε(1 + O₀)/((1 − ε)(1 − λ)), O₀ = tỉ số khối lượng gần bản đồ / xa bản đồ đầu đoạn, λ = phần khối lượng xa
  bản đồ bị chuyển động và hạt giống (bắt cóc, Ω) đưa vào gần bản đồ. Robot được bám vào lỗ: O₀ ≈ 0 ⇒ cận ≈ ε, **không có số hạng mép**.
  Đầu chuỗi: O₀ ≈ 1, λ có thể lớn ⇒ trường hợp yếu.
- **Mệnh đề 3 (hiện diện theo vị trí):** không có bằng chứng ảnh, khối lượng gần bản đồ của robot đã định vị khi ra khỏi bản đồ bị chặn bởi
  xác suất sai số dead-reckoning vượt off_d − excl − r: rời bản đồ được quyết định bằng dead-reckoning so với vùng phủ đã biết, không bằng
  phép thử ảnh.
- (E1) bị vi phạm bởi aliasing mạch lạc (các frame off-map liên tiếp khớp cùng một đoạn giống); trọng số theo quãng đường là hiệu chỉnh thô;
  ε = α/50 để hấp thụ hệ số thổi phồng, đo bằng kiểm toán theo vị trí.

## 6. Kết quả

### 6.1 Thiết kế (seed 0; không phải bằng chứng)

Cấu hình cuối (§4), seed 0, SH / CST-JS của ý tưởng 1 trên cùng run:
| Dataset | desc | chain MAP correct | OWF eps 0.05 (recall / segFAR) | eps 0.01 | **eps 1e-3 (default)** | SH | CST-JS | ms/frame (3 filters) |
|---|---|---|---|---|---|---|---|---|
| Boreas | cosplace | 0.993 | 0.978 / 0.038 | 0.973 / 0.018 | **0.967 / 0.009** | 0.874 / 0.018 | 0.875 / 0.020 | 9.7 |
| NCLT | cosplace | 0.924 | 0.841 / 0.010 | 0.791 / 0.000 | **0.715 / 0.000** | 0.670 / 0.000 | 0.685 / 0.000 | 10.0 |
| CMU | cosplace | 0.951 | 0.868 / 0.149 | 0.831 / 0.008 | **0.783 / 0.000** | 0.814 / 0.014 | 0.801 / 0.015 | 9.7 |
| CMU | megaloc | 0.963 | 0.909 / 0.004 | 0.884 / 0.000 | **0.853 / 0.000** | 0.867 / 0.014 | 0.867 / 0.029 | 10.0 |
| CMU | netvlad | 0.916 | 0.752 / 0.010 | 0.696 / 0.004 | **0.625 / 0.000** | 0.428 / 0.000 | 0.463 / 0.010 | 9.7 |
| Nordland | cosplace | 0.992 | 0.984 / 0.145 | 0.975 / 0.028 | **0.960 / 0.010** | 0.826 / 0.000 | 0.835 / 0.000 | 2.1 |
| Nordland | netvlad | 0.989 | 0.976 / 0.112 | 0.966 / 0.046 | **0.952 / 0.015** | 0.542 / 0.000 | 0.565 / 0.000 | 2.2 |
| office | cosplace | 0.998 | 0.983 / 0.000 | 0.975 / 0.000 | **0.963 / 0.000** | 0.883 / 0.000 | 0.883 / 0.004 | 4.9 |
| office | netvlad | 0.996 | 0.962 / 0.000 | 0.945 / 0.000 | **0.897 / 0.000** | 0.645 / 0.000 | 0.649 / 0.004 | 5.7 |
| old town | cosplace | 0.976 | 0.954 / 0.000 | 0.948 / 0.000 | **0.936 / 0.000** | 0.701 / 0.003 | 0.711 / 0.003 | 10.5 |
| old town | megaloc | 0.997 | 0.982 / 0.000 | 0.979 / 0.000 | **0.972 / 0.000** | 0.938 / 0.006 | 0.937 / 0.006 | 11.3 |
| old town | netvlad | 0.921 | 0.855 / 0.000 | 0.828 / 0.000 | **0.792 / 0.000** | 0.514 / 0.003 | 0.526 / 0.009 | 10.4 |
| countryside | cosplace | 0.786 | 0.684 / 0.006 | 0.611 / 0.000 | **0.553 / 0.000** | 0.659 / 0.000 | 0.664 / 0.000 | 12.7 |
| countryside | megaloc | 0.959 | 0.927 / 0.050 | 0.907 / 0.006 | **0.883 / 0.000** | 0.854 / 0.000 | 0.865 / 0.006 | 14.3 |
| countryside | netvlad | 0.777 | 0.594 / 0.000 | 0.518 / 0.000 | **0.459 / 0.000** | 0.226 / 0.000 | 0.258 / 0.000 | 11.4 |

Nhận xét thiết kế: ở ε = 1e-3 mọi run hợp lệ (tệ nhất 0.015), cao hơn SH ở 12/15; thấp hơn SH khi SH đã cao và độ trễ khởi đầu của OWF chiếm ưu
thế (chuỗi CMU ngắn; countryside CosPlace). Không đoạn MÉP nào bị báo trong mọi run thiết kế.

### 6.2 Tập A — 404 run phát triển chưa từng xem với OWF (seed 1–9, NCLT, Oxford, St Lucia)

@@SETA@@

### 6.3 Tập B — tập quyết định: kho dự trữ seed 25–27 (108 run), OWF vs HSI-VN trên cùng cache

| Dataset | runs | OWF recall | OWF segFAR | runs > α | HSI-VN recall | HSI-VN segFAR | Δ recall (wins) | OWF err (m) | HSI-VN err (m) | start / edge / deep (OWF) |
|---|---|---|---|---|---|---|---|---|---|---|
| Boreas | 18 | 0.961 | 0.0034 | 0 | 0.887 | 0.0001 | +0.074 (16/18) | **3.0** | 6.6 | 0.014 / 0.000 / 0.002 |
| CMU | 18 | 0.735 | 0.0237 | 3 | 0.695 | 0.0181 | +0.040 (11/18) | 5.9 | **4.7** | 0.033 / – / – |
| Nordland | 18 | 0.956 | 0.0158 | 0 | 0.799 | 0.0003 | +0.157 (18/18) | 8.0 | **5.6** | 0.000 / 0.009 / 0.017 |
| office | 18 | 0.912 | 0.0000 | 0 | 0.853 | 0.0008 | +0.059 (15/18) | 9.9 | **8.3** | 0.000 / 0.000 / 0.000 |
| old town | 18 | 0.906 | 0.0000 | 0 | 0.764 | 0.0021 | +0.141 (18/18) | **22.7** | 39.2 | 0.000 / 0.000 / 0.000 |
| countryside | 18 | 0.647 | 0.0025 | 0 | 0.661 | 0.0026 | −0.015 (8/18) | 46.7 | **28.2** | 0.037 / 0.000 / 0.000 |

**D1 đạt** (mọi dataset ≤ 0.05; 3/108 = 2.8 % run > α, đều CMU, tệ nhất 0.128). **D2 đạt:** recall gộp OWF − HSI-VN = **+0.076** (CI 95 % bootstrap
[+0.054, +0.099]); thắng 5/6 dataset (Nordland +0.157, old town +0.141, Boreas +0.074, office +0.059, CMU +0.040), countryside −0.015.
**D3 không đạt** (2/6: Boreas 3.0 vs 6.6 m, old town 22.7 vs 39.2 m; thua CMU +1.2, Nordland +2.4, office +1.6, countryside +18.5 m).
Kiểm toán vị trí: mép ≤ 0.009 mọi dataset; start CMU 0.033, countryside 0.037; tất cả ≤ 0.07.
**Quyết định (theo quy tắc đăng ký trước): D3 trượt ⇒ HSI-VN vẫn là luật khuyến nghị.** OWF được ghi nhận là luật hợp lệ có recall cao nhất
(+0.076 so với HSI-VN trên dữ liệu mới), không đổi được sai số điều hướng.

**Chẩn đoán sau khi xem** (không quyết định gì; nhãn chỉ để chẩn đoán): trong các báo của OWF ở ε = 1e-3, tỉ lệ fix sai trên bản đồ (err > excl):
countryside 7.8 % và 23 % fix có sai số 10–25 m ("đúng" theo excl nhưng thô); Nordland 0.47 % với 0.59 % fix sai xa > 20 frame (hàng km); CMU
0.84 % fix xa > 100 m; Boreas / office / old town ≤ 0.2 %. Sai số điều hướng của OWF vì vậy đến từ (i) một ít fix sai XA sau khi hậu nghiệm nhảy
sang một đoạn giống (Nordland, CMU — chỗ HSI có cổng nhất quán ngắn hạn) và (ii) hậu nghiệm quá tự tin trên countryside (VIO trôi, đường lặp).

### 6.4 Ablation, độ bền tỉ lệ lỗ

@@ABL@@

## 7. Kết quả âm, hạn chế, việc tiếp theo

@@NEG@@
