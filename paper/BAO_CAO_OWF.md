# Báo cáo Entry 10 — Bộ lọc thế giới mở (OWF): hiện diện suy từ vị trí, không phải từ phép thử

*Branch `hmm-2nd-idea`, 2026-11-04. Ý tưởng 2b. Mã: `analysis/owf.py`; lý thuyết: `paper/owf_theory.md`; nhật ký và đăng ký trước:
`RESEARCH_LOG.md` Entry 10; novelty: `LITERATURE_GATE.md` Gate 18. Bảng sinh bằng `analysis/owf_summary.py` từ JSON mỗi run
(`analysis/results/owf/`).*

## 1. Tóm tắt

**Vấn đề.** Định vị chuỗi bằng HMM trên bản đồ ảnh có lỗ: mỗi frame phải quyết định báo hay không báo một fix, với số đoạn off-map bị báo
sai ≤ α = 0.05, không nhãn. Hai lời giải trước (ý tưởng 1: phẫu thuật bản đồ phản thực; ý tưởng 2a HSI: tự giám sát hồi cứu + conformal) giữ
NGUYÊN bộ lọc vị trí topo và chỉ đổi lớp quyết định. Chẩn đoán: chuỗi vị trí topo đúng ở 0.78–0.95 frame on-map nhưng lớp quyết định chỉ báo
0.51–0.80; nguyên nhân là nhân chuyển trạng thái chuẩn hoá trên các nút bản đồ — robot đi vào lỗ không có chỗ trong không gian trạng thái.

**Phương pháp.** Bộ lọc thế giới mở (OWF): vị trí trên lưới mét phủ cả vùng có và không có bản đồ, chuyển trạng thái bảo toàn khối lượng, emission
là tỉ số hợp lý tự chuẩn hoá (LR = 1 ở ô trống), hiện diện là hàm của vị trí, quyết định đọc thẳng từ hậu nghiệm; không học, không dữ liệu hiệu
chuẩn, không phẫu thuật bản đồ. Lý thuyết: cận Ville cho báo sai trong một đoạn off-map, không có số hạng mép.

**Kết quả (đăng ký trước).** Tập A 404 run: recall 0.863 (HSI-VN 0.791, SH 0.726), TB segFAR ≤ 0.05 trên 9/9 dataset, kiểm toán vị trí đạt mọi lớp
(mép ≤ 0.003). Tập quyết định mới seed 25–27 (108 run): recall +0.076 so với HSI-VN (CI 95 % [+0.054, +0.099]), hợp lệ. **Nhưng** sai số điều hướng
kém hơn HSI-VN trên 4/6 dataset (tiêu chí D3 trượt) và 4.7 % run vượt α (CMU, Nordland) ⇒ theo quy tắc đã đăng ký, HSI-VN vẫn là luật khuyến
nghị; OWF là luật hợp lệ có recall cao nhất và là bộ ước lượng tốt hơn (MAP đúng 0.87–1.00).

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

| Dataset | runs | OWF recall / segFAR | runs > α | SH recall / segFAR | CST-JS | HSI-VN recall / segFAR | Δ vs SH (wins) | Δ vs HSI-VN (wins) | err OWF / SH / HSI-VN (m) | OWF tại segFAR của SH | start / edge / deep | ms/frame (Kaggle) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Boreas | 54 | 0.954 / 0.0012 | 0 | 0.771 / 0.0023 | 0.776 | 0.893 / 0.0015 | +0.182 (54/54) | +0.060 (43/54) | **3.1** / 4.5 / 7.0 | 0.919 | 0.002 / 0.000 / 0.001 | 30.0 |
| NCLT | 5 | 0.689 / 0.0013 | 0 | 0.601 / 0.0020 | 0.622 | 0.570 / 0.0007 | +0.088 (5/5) | +0.119 (5/5) | **4.0** / 4.6 / 4.4 | 0.786 | 0.000 / 0.000 / 0.002 | 27.8 |
| CMU | 54 | 0.758 / 0.0307 | 14 | 0.834 / 0.0092 | 0.815 | 0.756 / 0.0042 | −0.076 (8/54) | +0.002 (26/54) | 6.2 / 4.0 / **3.6** | 0.609 | 0.037 / – / – | 21.0 |
| Nordland | 54 | 0.938 / 0.0215 | 5 | 0.766 / 0.0000 | 0.779 | 0.784 / 0.0001 | +0.171 (54/54) | +0.154 (54/54) | 15.4 / 6.2 / **5.8** | 0.562 | 0.002 / 0.003 / 0.023 | 6.1 |
| office | 54 | 0.925 / 0.0000 | 0 | 0.798 / 0.0003 | 0.810 | 0.870 / 0.0000 | +0.127 (52/54) | +0.054 (41/54) | 10.3 / 9.7 / **9.0** | 0.981 | 0.000 / 0.000 / 0.000 | 12.7 |
| old town | 54 | 0.893 / 0.0007 | 0 | 0.701 / 0.0058 | 0.709 | 0.723 / 0.0014 | +0.192 (54/54) | +0.169 (54/54) | **21.6** / 26.1 / 33.0 | 0.949 | 0.005 / 0.000 / 0.000 | 28.0 |
| countryside | 54 | 0.632 / 0.0006 | 0 | 0.483 / 0.0006 | 0.494 | 0.657 / 0.0067 | +0.149 (49/54) | −0.025 (25/54) | 45.6 / 33.8 / **26.7** | 0.733 | 0.000 / 0.000 / 0.001 | 36.4 |
| Oxford | 45 | 0.898 / 0.0007 | 0 | 0.719 / 0.0039 | 0.729 | 0.805 / 0.0089 | +0.179 (45/45) | +0.093 (45/45) | **17.6** / 21.9 / 21.1 | 0.960 | 0.006 / 0.002 / 0.000 | 23.6 |
| St Lucia | 30 | 0.975 / 0.0000 | 0 | 0.761 / 0.0006 | 0.763 | 0.915 / 0.0013 | +0.214 (30/30) | +0.060 (30/30) | **16.6** / 25.5 / 18.5 | 0.996 | 0.000 / 0.000 / 0.000 | 20.6 |

Gộp 404 run: recall OWF **0.863**, SH 0.726, HSI-VN 0.791 (OWF − HSI-VN +0.072, CI 95 % [+0.061, +0.083]); run > α: OWF 19/404 (CMU 14,
Nordland 5; tệ nhất 0.140), HSI-VN 0, SH 2; sai số điều hướng gộp OWF 16.9 m, SH 15.7, HSI-VN 15.1.
**Giả thuyết:** H1 **đạt** (TB ≤ 0.05 trên 9/9; CMU 0.031); H2 **đạt** 8/9 (CMU −0.076); H2b **đạt**; H3 **đạt** (mọi lớp ≤ 0.07: mép ≤ 0.003
mọi dataset — ý tưởng 1 không đạt ở đây; CMU start 0.037, Nordland deep 0.023); H4 **không đạt** (3/7: Boreas, NCLT, old town); H5 **không đạt**
(6–36 ms/frame trên phiên CPU Kaggle 4 job / 4 vCPU; cục bộ 2–14 ms); H6 **không đạt** (7/9: Nordland và CMU — SH ở segFAR ≈ 0 ở đó, đường cong
OWF tại segFAR đó thấp hơn); H7 (ε = 0.01) **không đạt** (hợp lệ 7/9: CMU 0.059, Nordland 0.060; recall > SH 8/9); H8 **đạt** 8/9 (countryside
−0.025); H9 **đạt** 5/9 (Boreas, NCLT, old town, Oxford, St Lucia).
**Đọc:** OWF đổi recall lấy đuôi: trung bình hợp lệ trên mọi dataset và recall cao nhất trên 8/9 (gộp +0.072 so với HSI-VN, +0.137 so với SH),
nhưng (a) 4.7 % run vượt α, tập trung ở CMU (khởi đầu toàn cục trên chuỗi ngắn) và Nordland (chuỗi bắt đầu trong lỗ, aliasing đường ray)
— đúng chỗ yếu Mệnh đề 2 dự báo (O₀ ≈ 1 ở đầu chuỗi); (b) sai số điều hướng kém hơn trên Nordland / CMU (vài fix sai xa sau khi hậu nghiệm nhảy)
và countryside (fix thô, VIO trôi). Kết luận nhất quán với tập B.

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

**Ablation (phụ; seed 1–2 × CosPlace + MegaLoc × 7 dataset, NCLT seed 0 — 26 run mỗi biến thể; ghi 11:26 UTC).**

| Biến thể | recall | segFAR TB | run > α | sai số (m) | OWF đầy đủ, cùng run |
|---|---|---|---|---|---|
| thế giới ĐÓNG (ô trống / Ω có LR ≈ 0: bản tương tự topo với cùng emission và chuyển động) | 0.847 | **0.297** | **26/26** | 50.2 | 0.882 / 0.0026 / 12.7 |
| không trọng số theo quãng đường (ℓ = 0) | 0.917 | **0.606** | **26/26** | 75.5 | |
| q cố định 0.02 excl (không chọn trực tuyến) | 0.862 | 0.0026 | 0 | 11.9 | |
| kidnap 1e-4 | 0.848 | 0.0101 | 2 | 13.4 | |

**Đọc:** (1) không gian trạng thái mở là thứ tạo ra tính hợp lệ: cùng emission, cùng chuyển động, chỉ bỏ ô trống ⇒ mọi run vượt α (segFAR 0.21–0.45
theo dataset) — xác nhận chẩn đoán của §1; (2) trọng số theo quãng đường là bắt buộc (aliasing đếm mỗi frame); (3) chọn q trực tuyến thêm
+0.020 recall (sai số +0.8 m); (4) kidnap ≈ 0 thêm +0.034 recall và bỏ 2 run vi phạm.

**Độ bền tỉ lệ lỗ (phụ; `hmm-navcache-holes` seed 0–2 × 6 dataset × 6 desc, 216 run; ghi 11:39 UTC).**

| lỗ | Dataset | runs | OWF recall / segFAR | run > α | SH | HSI-VN | err OWF / SH / HSI-VN (m) |
|---|---|---|---|---|---|---|---|
| 10 % | boreas | 18 | 0.976 / 0.0007 | 0 | 0.812 / 0.0000 | 0.913 / 0.0006 | 2.1 / 3.2 / 6.2 |
| 10 % | cmu | 18 | 0.768 / 0.0502 | 6 | 0.838 / 0.0158 | 0.597 / 0.0000 | 5.4 / 3.7 / 2.8 |
| 10 % | nord | 18 | 0.951 / 0.0129 | 1 | 0.774 / 0.0000 | 0.829 / 0.0000 | 4.5 / 5.5 / 3.8 |
| 10 % | 4s:office_loop | 18 | 0.951 / 0.0000 | 0 | 0.812 / 0.0008 | 0.867 / 0.0000 | 8.2 / 7.4 / 6.7 |
| 10 % | 4s:old_town | 18 | 0.927 / 0.0000 | 0 | 0.736 / 0.0040 | 0.729 / 0.0000 | 17.2 / 21.5 / 32.4 |
| 10 % | 4s:countryside | 18 | 0.662 / 0.0007 | 0 | 0.519 / 0.0000 | 0.696 / 0.0016 | 45.3 / 32.5 / 19.1 |
| 50 % | boreas | 18 | 0.923 / 0.0000 | 0 | 0.730 / 0.0017 | 0.881 / 0.0001 | 3.2 / 5.2 / 4.6 |
| 50 % | cmu | 18 | 0.652 / 0.0184 | 3 | 0.743 / 0.0269 | 0.770 / 0.0296 | 8.8 / 9.9 / 9.9 |
| 50 % | nord | 18 | 0.921 / 0.0187 | 0 | 0.766 / 0.0002 | 0.685 / 0.0001 | 40.5 / 9.6 / 8.9 |
| 50 % | 4s:office_loop | 18 | 0.877 / 0.0000 | 0 | 0.783 / 0.0009 | 0.860 / 0.0008 | 14.6 / 13.6 / 13.7 |
| 50 % | 4s:old_town | 18 | 0.861 / 0.0000 | 0 | 0.696 / 0.0033 | 0.720 / 0.0011 | 34.0 / 36.9 / 60.2 |
| 50 % | 4s:countryside | 18 | 0.531 / 0.0021 | 0 | 0.457 / 0.0044 | 0.608 / 0.0049 | 56.3 / 41.9 / 35.6 |

Gộp: lỗ 10 % recall OWF 0.872 / SH 0.748 / HSI-VN 0.772, 7/108 run > α (CMU 6 — TB CMU **0.0502**, vượt α ngay ở mức trung bình; Nordland 1); lỗ
50 % 0.794 / 0.696 / 0.754, 3/108 run > α (CMU). Mép: 0.000–0.003 ở mọi tỉ lệ. Điều hướng: Nordland lỗ 50 % 40.5 m (SH 9.6, HSI-VN 8.9) — cùng
cơ chế fix sai xa sau bước nhảy; Boreas và old town vẫn tốt nhất. ⇒ cùng bức tranh: recall cao nhất ở mọi tỉ lệ, đuôi hợp lệ CMU và điều hướng
Nordland / countryside là điểm yếu.

## 7. Kết quả âm, hạn chế, việc tiếp theo

**Kết quả âm (có số đo).** (a) Sai số điều hướng (D3, H4): Nordland 15.4 m vs SH 6.2 / HSI-VN 5.8; countryside 45.6 vs 33.8 / 26.7; CMU 6.2 vs 4.0 /
3.6 (tập A). Nguyên nhân: vài fix sai xa sau khi hậu nghiệm nhảy sang một đoạn giống (Nordland 0.6 %, CMU 0.8 % các báo) và fix thô dưới VIO trôi
(countryside: 23 % báo có sai số 10–25 m, 7.8 % > excl). (b) Đuôi hợp lệ: 19/404 run > α (CMU 14, Nordland 5) — đầu chuỗi là trường hợp yếu của
Mệnh đề 2 (O₀ ≈ 1); HSI-VN 0/404. (c) CMU recall 0.758 < SH 0.834. (d) countryside recall < HSI-VN (−0.025). (e) ε = 0.01 vượt α trên CMU /
Nordland. (f) Chi phí 6–36 ms/frame trên phiên CPU Kaggle (mục tiêu 15 ms không đạt; cục bộ 2–14 ms).

**Hạn chế của lý thuyết.** Giả định (E1) (LR có trọng số là e-value có điều kiện ngoài bản đồ) bị vi phạm bởi aliasing mạch lạc; trọng số theo
quãng đường chỉ là hiệu chỉnh thô; ε = α/50 được chọn để hấp thụ hệ số thổi phồng — không phải bảo đảm chặt. Lưới mét cần odometry trong hệ toạ
độ bản đồ (như mọi luật của giao thức: hướng ban đầu hiệu chỉnh trên 50 frame đầu).

**Việc tiếp theo.** (1) Sửa điều hướng: cổng nhảy dead-reckoning giữa hai lần báo (chẩn đoán trên tập A: Nordland 15.4 → ~5 m, recall −0.01;
không đổi CMU; xấu đi countryside 45 → 51–57 m) ⇒ cần một tiêu chí chọn theo độ trôi; báo theo khối lượng trong bán kính nhỏ hơn excl; phương sai
trôi lớn hơn khi bằng chứng yếu. (2) Khởi đầu toàn cục an toàn hơn (CMU, chuỗi bắt đầu trong lỗ). (3) Ghép OWF (bộ ước lượng) với lớp quyết
định HSI (HSI cần chuỗi vị trí đúng; OWF cho chuỗi vị trí đúng hơn). (4) Mọi quyết định mới cần tập mới: nhóm dự trữ 19–21 / 22–24 (của phiên
HSI) hoặc sinh seed 28–30 bằng `hsi_fresh.py --keep`.
