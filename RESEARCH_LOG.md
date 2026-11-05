# Research Log — ý tưởng 2 (branch `hmm-2nd-idea`)

*Nhật ký thí nghiệm của lời giải mới. Entry mới đặt trên cùng. Mỗi entry: bối cảnh, giả thuyết, đăng ký trước (commit trước khi xem kết quả),
thí nghiệm, kết quả (kể cả âm), kết luận. Nhật ký của ý tưởng 1 (Entry 0–39): `history/RESEARCH_LOG_idea1.md`; tóm tắt:
`handoff/07_IDEA1_SUMMARY.md`.*

**Độ bền tỉ lệ lỗ (phụ, không quyết định; `hmm-navcache-holes` seed 0–2 × 6 dataset × 6 desc, 216 run; ghi 11:39 UTC).**

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

**Ablation (phụ, không quyết định; seed 1–2 × CosPlace + MegaLoc × 7 dataset, NCLT seed 0 — 26 run mỗi biến thể; ghi 11:26 UTC).**

| Biến thể | recall | segFAR TB | run > α | sai số (m) | OWF đầy đủ, cùng run |
|---|---|---|---|---|---|
| thế giới ĐÓNG (ô trống / Ω có LR ≈ 0: bản tương tự topo với cùng emission và chuyển động) | 0.847 | **0.297** | **26/26** | 50.2 | 0.882 / 0.0026 / 12.7 |
| không trọng số theo quãng đường (ℓ = 0) | 0.917 | **0.606** | **26/26** | 75.5 | |
| q cố định 0.02 excl (không chọn trực tuyến) | 0.862 | 0.0026 | 0 | 11.9 | |
| kidnap 1e-4 | 0.848 | 0.0101 | 2 | 13.4 | |

**Đọc:** (1) không gian trạng thái mở là thứ tạo ra tính hợp lệ: cùng emission, cùng chuyển động, chỉ bỏ ô trống ⇒ mọi run vượt α (segFAR 0.21–0.45
theo dataset) — xác nhận chẩn đoán của §1; (2) trọng số theo quãng đường là bắt buộc (aliasing đếm mỗi frame); (3) chọn q trực tuyến thêm
+0.020 recall (sai số +0.8 m); (4) kidnap ≈ 0 thêm +0.034 recall và bỏ 2 run vi phạm.

**Kết quả tập A (404 run chưa từng xem với OWF: seed 1–9 × 6 desc × 6 dataset có lỗ, NCLT × 5 desc, Oxford 45, St Lucia 30; đợt `owfa` +
probe `owfp-1`; ghi 11:02 UTC).** ε = 1e-3; SH / CST-JS / HSI-VN trên CÙNG run.

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

**Kết quả tập quyết định B (seed 25–27, 108 run, đợt `owfb` + `hsib`; ghi 10:43 UTC, trước khi đọc tập A).**

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
*Chẩn đoán sau khi xem (không quyết định gì; ε = 1e-3, tập B, nhãn chỉ để chẩn đoán):* tỉ lệ báo sai trên bản đồ (err > excl) trong các báo:
countryside 7.8 % (và 23 % báo có sai số 10–25 m: fix "đúng" nhưng thô), Nordland 0.47 % với 0.59 % báo xa > 20 frame (km), CMU 0.84 % báo xa
> 100 m; Boreas / office / old town ≤ 0.2 %. ⇒ sai số điều hướng do (i) một ít fix sai XA sau khi hậu nghiệm nhảy sang một đoạn giống (Nordland,
CMU — chính là chỗ HSI có cổng nhất quán ngắn hạn) và (ii) hậu nghiệm quá tự tin trên countryside (VIO trôi, đường lặp). Hướng sửa (cổng
nhất quán theo dead-reckoning giữa hai lần báo, tính quá tự tin theo độ trôi) phải kiểm trên tập MỚI (không còn nhóm dự trữ sau 25–27).

## Entry 16 — Hindsight-calibrated OWF decision (OWF-HC): KẾT QUẢ PHÁT TRIỂN ÂM, không đăng ký kiểm tra (2026-11-05 16:38 UTC)

**Bối cảnh.** Luật đương nhiệm OWF-HWA-S5 (Entry 15) hợp OWF-H với ba bậc ngưỡng CỐ ĐỊNH m(1e-5, 16) | m(1e-8, 2) | t(3e-4, 0.5), chọn trên
seed phát triển. Tài liệu 08 ghi đây là phần heuristic của hệ. Giả thuyết của Entry 16: thay các hằng số đó bằng ngưỡng do chính lần triển khai
hiệu chuẩn — split conformal theo tầng quãng đường từ đầu chuỗi, trên các đoạn null hồi cứu của chính run, hiệu chuẩn chung với nhánh OWF-H
(`paper/owf_theory.md` §6, Mệnh đề 4: bảo đảm hữu hạn mẫu, không cần giả định (E1) của Mệnh đề 2). Gate 19 (`LITERATURE_GATE.md`).

**Chẩn đoán trước khi thiết kế (`analysis/owf_alias_diag.py`, run thiết kế seed 1).** Trên Nordland, các giả thuyết tự tin nhưng sai của OWF
nằm SÂU trong lỗ: quãng đường từ đầu chuỗi ≥ 32 excl, 82 % frame off-map. Chúng kéo dài trung vị 2.3 excl (p90 16 excl) và đạt khối lượng
1 − 1e-10. Đây là aliasing liên tiếp: (E1) bị vi phạm, không chỉ ở đầu chuỗi.

**Hạ tầng (mới trong phiên).** Engine GPU cho OWF (`owf_torch.py`, `owf.py --engine torch`): 2.7–3.4 ms/frame cho ngân hàng 10 bộ lọc trên một
L4, so với 29 ms/frame của numpy. Quyết định trùng numpy ở mọi ngưỡng. Đợt `inc` (6 phiên 4×L4, 657 run, 35 phút, 0 lỗi): luật đương nhiệm trên
tập phát triển A (399 run: 6 dataset có lỗ × 6 descriptor × seed 1–9, Oxford 45, St Lucia 30) + NCLT 6 + các tập tổng quát (lỗ 10 %, 50 %,
off-map tự nhiên). `hsi_eval --frames` lưu thêm null hồi cứu / thời điểm khả dụng / đơn vị hiệu chuẩn để nghiên cứu quyết định ngoại tuyến.

**Đánh giá phát triển (tập A, 399 run, `analysis/owf_hcal.py` + `hcal_board.py`; cầu hồi cứu dựng từ chuỗi tô-pô độc lập với OWF; null =
có thể off-map ∪ ảnh OWF có thể sai ∪ chưa từng xác minh).** Ô = recall / TB segFAR / run > α / sai số điều hướng (m):

| Biến thể | gộp 399 run | Δ recall vs INC (CI 95 %) | tệ nhất (TB segFAR) |
|---|---|---|---|
| INC (OWF-HWA-S5) | **0.933 / 0.0045 / 1 / 12.7** | — | 0.0095 (CMU) |
| H (chỉ nhánh OWF-H) | 0.885 / 0.0026 / 0 / 13.7 | −0.047 | 0.0077 |
| HC3 (3 tầng 0/2/16 excl) | 0.912 / 0.0158 / 41 / 17.0 | −0.021 [−0.024, −0.018] | 0.035 (Nordland) |
| HC5 (5 tầng) | 0.911 / 0.0148 / 34 / 16.9 | −0.022 | 0.035 |
| HC3a / HC5a (+ đồng thuận ba nguồn) | 0.907 / 0.906, 31 / 23 run > α | −0.026 / −0.027 | 0.032 / 0.031 |
| HC3v (null không gồm frame chưa xác minh) | 0.914 / 0.0192 / 46 / 17.2 | −0.019 | 0.036 |
| HC1 (một tầng) | 0.916 / 0.0144 / 31 / 16.6 | −0.017 | 0.035 |
| C3 / C5 (nhánh OWF hiệu chuẩn, không H) | 0.684 / 0.675, 42 / 35 run > α | −0.25 | 0.039 |

Thiết kế cục bộ trước đó cũng loại tầng theo "tuổi bằng chứng" (quãng đường từ lần khối lượng < 0.5 gần nhất). Lý do: gần như mọi đoạn null
rơi vào tầng tuổi 0, nên các tầng tự tin không có đoạn hiệu chuẩn.

**Kết luận: hướng bị loại (không đăng ký kiểm tra, không dùng nhóm seed mới).** Mọi biến thể HC đều thua INC trên cả ba trục: recall thấp hơn
0.017–0.027, 23–46 run > α (so với 1), sai số điều hướng tăng 2–4.6 m. Cơ chế:
- (i) Split conformal ở mức α chặn KỲ VỌNG tỉ lệ đoạn null có báo, nên segFAR từng run dao động quanh α và nhiều run vượt α. INC vận hành
  thấp hơn α khoảng 10 lần, và chính các ngưỡng cực đoan cố định tạo ra khoảng an toàn đó.
- (ii) Các đợt aliasing liên tiếp chỉ là thiểu số trong các đoạn null, nên phân vị 95 % bỏ qua chúng (CMU 15 run, Nordland 14 run > α).

Bài học cho lý thuyết: bảo đảm biên theo đoạn (Mệnh đề 4) KHÔNG kiểm soát đuôi theo run. Muốn kiểm soát đuôi theo run cần mức hiệu chuẩn
thấp hơn nhiều, và cái giá recall khi đó còn lớn hơn. Mệnh đề 4 giữ trong `owf_theory.md` §6 kèm kết quả âm này.

**Tính tổng quát của luật đương nhiệm (mô tả; các tập này không dùng để chỉnh luật).** Ô = recall INC vs H / TB segFAR tệ nhất / run > α
INC, H:
- Lỗ 10 % (108 run): 0.933 vs 0.865 / 0.0077 / 1, 0.
- Lỗ 50 % (108 run): 0.894 vs 0.833 / 0.032 (CMU) / 4, 4 (đều CMU, cùng run).
- Off-map tự nhiên 4Seasons chéo cảnh (36 run): 0.952 vs 0.889 / 0.0104 / 2, 2.
- NCLT (6 run): 0.781 vs 0.753 / 0.0049 / 0, 0.

Đuôi hợp lệ còn lại đến từ nhánh H, không từ các bậc. So sánh: HSI-VN trên lỗ 10 % / 50 % đạt 0.772 / 0.754, SH (ý tưởng 1) 0.748 / 0.696.

**Chẩn đoán khoảng trống recall (tập A, nhãn chỉ để chẩn đoán).**
- CMU không có chuỗi nào dài quá 16 excl. Ảnh MAP của OWF đúng 0.95–0.99 frame on-map ở MỌI khoảng cách từ đầu chuỗi, kể cả 0.964 trong
  0.5 excl đầu. INC chỉ báo 0.53–0.94. Frame đúng bị bỏ = 0.125 tổng số frame on-map, tức toàn bộ khoảng cách recall của CMU nằm ở quyết định
  đầu chuỗi.
- Ở đầu chuỗi CMU (< 2 excl), điểm OWF ≥ 2 (khối lượng ≥ 0.99) kèm đồng thuận ba nguồn báo 0.587 frame đúng, 0/8129 frame sai on-map và
  0.04 % frame off-map. Điểm ≥ 3 cho 0.489 / 0 / 0 trên 49 410 frame off-map.
- Countryside: khoảng trống nằm ở chuỗi dài (≥ 16 excl): OWF đúng 0.912, báo 0.844 (khối lượng bị VIO trôi làm loãng).

## Entry 15 — Ngân hàng tỉ lệ odometry rộng hơn (0.94–1.06) — đăng ký trước (2026-11-04 22:19 UTC; AUTOLOOP vòng 7)

**KẾT QUẢ TẬP KIỂM TRA (seed 52–54, 144 run mới, đợt `t52`; ghi 2026-11-05 00:25 UTC). Quyết định: OWF-HWA-S5 THAY OWF-HWA-S làm luật khuyến
nghị.** Ô = recall / TB segFAR / run > α / sai số (m).

| Dataset | OWF-HWA-S5 (C) | OWF-HWA-S (R*) | HSI-VN |
|---|---|---|---|
| Boreas | 0.976 / 0.0024 / 0 / 4.0 | 0.977 / 0.0026 / 0 / 4.0 | 0.890 / 0.0001 / 0 / 5.8 |
| CMU | 0.862 / 0.0114 / 1 / 4.3 | 0.861 / 0.0114 / 1 / 4.3 | 0.799 / 0.0114 / 1 / 4.4 |
| Nordland | 0.969 / 0.0062 / 0 / 6.3 | 0.970 / 0.0061 / 0 / 6.3 | 0.823 / 0.0000 / 0 / 3.6 |
| office | 0.970 / 0.0000 / 0 / 8.5 | 0.969 / 0.0000 / 0 / 9.0 | 0.876 / 0.0000 / 0 / 8.5 |
| old town | 0.959 / 0.0027 / 0 / 22.1 | 0.950 / 0.0037 / 0 / 24.6 | 0.766 / 0.0012 / 0 / 31.4 |
| countryside | **0.873** / 0.0019 / 0 / 24.0 | 0.847 / 0.0019 / 0 / 24.7 | 0.693 / 0.0026 / 0 / 24.3 |
| Oxford | 0.944 / 0.0065 / 0 / 18.3 | 0.944 / 0.0066 / 0 / 18.3 | 0.812 / 0.0076 / 0 / 21.6 |
| St Lucia | 0.977 / 0.0021 / 0 / 13.8 | 0.976 / 0.0023 / 0 / 13.7 | 0.928 / 0.0022 / 0 / 15.0 |
| **Gộp (144)** | **0.941 / 1 run / 12.67 m** | 0.937 / 1 / 13.11 | 0.823 / 1 / 14.32 |

- **M1 đạt:** TB segFAR tệ nhất 0.0114 (CMU). 1/144 run > α: cùng một run CMU ở mọi luật, kể cả HSI-VN.
- **M2 đạt:** chênh C − R* **+0.0045**, CI 95 % [+0.0024, +0.0070]; thắng 80 / hoà 5 / thua 59.
- **M3 đạt:** 12.67 vs 13.11 m.

Gain tập trung đúng ở các dataset VIO lệch tỉ lệ: countryside +0.026, old town +0.009 (sai số 22.1 vs 24.6 m). Các dataset khác ±0.001.
Bảng điểm đầy đủ (cả OWF-H-S5, OWF-HW-S5): `analysis/results/owf/owfhwas5_test_s52_54_json.tgz`.

**Chẩn đoán (dữ liệu phát triển, cache seed 1).** So độ dài từng bước odometry với GNSS:
- 4Seasons (VIO): lệch tỉ lệ ngoài ngân hàng ±3 % của Entry 13. Countryside: trung vị 1.040, P10–P90 1.03–1.07. Office: 1.037. Old town:
  0.943, P10–P90 0.93–1.01.
- Boreas: 1.001.
- Oxford (mô phỏng): 0.97–1.04.
- Trôi hướng VIO: nhỏ (|trôi| trung vị < 0.6°/km), nên KHÔNG cần ngân hàng hướng.

**Phát triển.** Cục bộ, countryside cosplace s1 (OWF riêng): recall 0.568 → 0.603, chuỗi đúng 0.786 → 0.817, sai số 42.8 → 40.8 m. Đợt `devW`
(6 phiên, 149 run phát triển × {3 tỉ lệ, 5 tỉ lệ}, kèm mặt nạ HSI); khi đăng ký mới có 68 run đủ cặp. Luật đầy đủ (OWF-H + hợp hai bậc + bậc đồng
thuận) với ngân hàng 5 tỉ lệ so với 3 tỉ lệ:
- recall **+0.0058**, CI [+0.0020, +0.0103]; thắng 45 / thua 23;
- 0 run > α ở cả hai;
- sai số 12.77 vs 13.63 m.

Theo dataset: countryside 0.759 → 0.793, old town 0.910 → 0.928 (22.5 vs 27.5 m), office 0.958 → 0.965; Boreas / CMU / Nordland / Oxford /
St Lucia ±0.002; NCLT −0.016 (2 run).

**Luật đăng ký: OWF-HWA-S5** = OWF-HWA-S (Entry 14) với ngân hàng `--scales 0.94,0.97,1.0,1.03,1.06` (10 bộ lọc: 2 q × 5 tỉ lệ) thay cho
`0.97,1.0,1.03`. Mọi phần khác giữ nguyên: OWF-H `xms0.9_16` + HSI-VN; `owf_union.py --variants "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"`.

**Tập kiểm tra mới:** seed 52–54 của `synchan5704/hmm-navcache-r49` (144 run, chưa dùng). R* = OWF-HWA-S (Entry 14 đạt). R* và C chạy trong CÙNG
đợt `t52`, trên CÙNG run: tag `r52S` (3 tỉ lệ) và `r52S5` (5 tỉ lệ), cả hai kèm mặt nạ HSI.
- **M1 (hợp lệ):** TB segFAR ≤ 0.05 trên 8/8 dataset và ≤ 2/144 run > α.
- **M2 (recall):** chênh gộp C − R* ≥ +0.003 với cận dưới CI 95 % bootstrap (theo run) > 0.
- **M3 (điều hướng):** sai số gộp ≤ R* + 0.5 m.

**Quy tắc:** M1 ∧ M2 ∧ M3 ⇒ OWF-HWA-S5 là luật khuyến nghị mới. *Phụ (báo cáo):* recall theo dataset (countryside / old town / office), HSI-VN
trên cùng run.

## Entry 14 — Bậc đồng thuận ba nguồn cho đầu chuỗi (OWF ∧ chuỗi tô-pô ∧ truy hồi top-1) — đăng ký trước (2026-11-04 19:05 UTC; AUTOLOOP vòng 6)

**KẾT QUẢ TẬP KIỂM TRA (seed 49–51, 144 run mới, đợt `t49`; ghi 22:18 UTC). Quyết định: OWF-HWA-S THAY OWF-HW-S làm luật khuyến nghị.**
R* = OWF-HW-S (Entry 13 đạt) ⇒ C = **OWF-HWA-S** = OWF-HW-S ∨ t(3e-4, 0.5) trên khung OWF ngân hàng tỉ lệ. Ô = recall / TB segFAR / run > α / sai số (m).

| Dataset | OWF-HWA-S (C) | OWF-HW-S (R*) | OWF-HU | HSI-VN |
|---|---|---|---|---|
| Boreas | 0.975 / 0.0012 / 0 / 3.4 | 0.972 / 0.0010 / 0 / 3.3 | 0.973 / 0.0011 / 0 / 3.3 | 0.898 / 0.0009 / 0 / 5.2 |
| CMU | **0.874** / 0.0080 / 0 / 3.8 | 0.832 / 0.0066 / 0 / 3.7 | 0.808 / 0.0066 / 0 / 3.8 | 0.808 / 0.0066 / 0 / 3.4 |
| Nordland | 0.975 / 0.0080 / 0 / 9.6 | 0.972 / 0.0060 / 0 / 9.6 | 0.962 / 0.0058 / 1 / 10.5 | 0.813 / 0.0000 / 0 / 4.2 |
| office | 0.967 / 0.0006 / 0 / 8.1 | 0.956 / 0.0006 / 0 / 8.1 | 0.950 / 0.0010 / 0 / 8.8 | 0.857 / 0.0006 / 0 / 7.7 |
| old town | 0.939 / 0.0003 / 0 / 26.6 | 0.926 / 0.0003 / 0 / 27.5 | 0.900 / 0.0005 / 0 / 29.4 | 0.737 / 0.0024 / 0 / 32.0 |
| countryside | 0.838 / 0.0006 / 0 / 21.7 | 0.831 / 0.0006 / 0 / 21.7 | 0.771 / 0.0000 / 0 / 25.1 | 0.644 / 0.0002 / 0 / 20.0 |
| Oxford | 0.921 / 0.0066 / 0 / 17.0 | 0.909 / 0.0066 / 0 / 17.1 | 0.896 / 0.0068 / 0 / 17.5 | 0.761 / 0.0071 / 0 / 22.0 |
| St Lucia | 0.975 / 0.0019 / 0 / 18.9 | 0.970 / 0.0019 / 0 / 19.1 | 0.966 / 0.0016 / 0 / 19.1 | 0.912 / 0.0013 / 0 / 20.4 |
| **Gộp (144)** | **0.933 / 0 run / 13.64 m** | 0.921 / 0 / 13.78 | 0.903 / 1 / 14.68 | 0.804 / 0 / 14.34 |

- **L1 đạt:** TB segFAR tệ nhất 0.0080 (CMU, Nordland), 0/144 run > α.
- **L2 đạt:** chênh C − R* **+0.0118**, CI 95 % [+0.0096, +0.0141]; thắng **144/144** run.
- **L3 đạt:** 13.64 vs 13.78 m.

Gain lớn nhất ở CMU (+0.042, đúng đích chẩn đoán); recall tăng trên cả 8/8 dataset. Bậc đồng thuận trên OWF thường cũng tăng như vậy (OWF-HWA
0.9205 vs OWF-HW 0.9078; báo cáo phụ). Bảng điểm đầy đủ: `analysis/results/owf/owfhwas_test_s49_51_json.tgz`.

**Chẩn đoán (tập A, 404 run, nhãn chỉ để chẩn đoán).** Với luật hợp hai bậc W(1e-5, 16, 1e-8, 2), chuỗi vị trí lai (OWF-H) đúng trên 0.959 khung
trong bản đồ nhưng chỉ báo đúng 0.899. Trên CMU khoảng cách lớn nhất: chuỗi đúng 0.964, báo 0.794, và TOÀN BỘ phần thiếu (0.176) nằm ở đoạn
đường < 16·excl từ đầu chuỗi. Lý do: mỗi run CMU có ~130 chuỗi ngắn (~7.5·excl ≈ 190 m), nên chuỗi OWF-H và bậc U không bao giờ được dùng,
còn HSI-VN thận trọng ở đầu chuỗi. Countryside: 0.073 khung có OWF tự tin nhưng sai trong khi chuỗi tô-pô đúng.

**Cơ chế.** Ba bộ ước lượng có kiểu lỗi khác nhau:
- OWF: thế giới mở, metric, có trạng thái ngoài bản đồ.
- Chuỗi tô-pô `est_c`: HMM thế giới đóng, bị ép chọn một nút.
- Truy hồi top-1: một khung, không có động học.

Ngoài bản đồ, cả ba cùng chỉ về một ảnh sai VÀ OWF đặt khối lượng đĩa ≥ 1 − ε là hiếm. Vì thế điều kiện đồng thuận thay được phần lớn yêu cầu
"đã đi đủ xa" của bậc U/W. Riêng bậc đồng thuận (không hợp với OWF-H) trên 149 run `devS`: TB segFAR ≤ 0.003 trên mọi dataset, 0 run > α, với cả
OWF thường lẫn OWF ngân hàng tỉ lệ.

**Phát triển (tập A, 404 run, `owf_union.py` dạng tổng quát).** Bậc t(ε, D) = khối lượng OWF ≥ 1 − ε, đường đi ≥ D·excl, và ảnh OWF nằm trong
excl của CẢ `est_c` lẫn top-1. Luật = W(1e-5, 16, 1e-8, 2) ∨ t(ε, D):

| Bậc thêm | Score (recall gộp) | run > α | segFAR dataset tệ nhất | sai số (m) | CMU | countryside | NCLT |
|---|---|---|---|---|---|---|---|
| — (W) | 0.8990 | 0 | 0.0079 | 13.73 | 0.794 | 0.770 | 0.786 |
| t(1e-6, 0) | 0.9030 | 0 | 0.0079 | 13.73 | 0.818 | 0.772 | 0.786 |
| t(1e-4, 0.5) | 0.9107 | 0 | 0.0082 | 13.70 | 0.842 | 0.778 | 0.795 |
| **t(3e-4, 0.5)** | **0.9136** | **0** | 0.0082 | 13.73 | 0.848 | 0.780 | 0.800 |
| t(1e-3, 0) | 0.9168 | 1 | 0.0095 | 13.77 | 0.856 | 0.783 | 0.807 |
| t(1e-2, 0.5) | 0.9229 | 6 | 0.0179 | 13.95 | 0.871 | 0.788 | 0.820 |

Kết quả phát triển, theo từng phần:
- *Bền vững (persistence):* đòi đồng thuận liên tục L khung KHÔNG tốt hơn biên ε. Ví dụ p(1e-3, 0, 3) cho 0.9127 / 0 run;
  p(1e-2, 0.5, 5) cho 0.9149 / 1 run.
- *Đồng thuận hai nguồn (bỏ top-1):* kém an toàn hơn. a(1e-3, 2) trên CMU có 4 run > α.
- *Chọn điểm:* điểm có Score phát triển lớn nhất mà 0 run > α là **ε = 3e-4, D = 0.5**.
- *Theo dataset:* recall tăng trên 9/9 dataset; CMU 0.794 → 0.848, vượt SH 0.834.

**Luật đăng ký: C = R* ∨ t(3e-4, 0.5).** R* là luật khuyến nghị sau Entry 13: OWF-HW-S nếu Entry 13 đạt, ngược lại OWF-HU. Bậc đồng thuận dùng
khối lượng / ảnh của CÙNG bộ lọc OWF mà R* dùng; báo thêm lấy ảnh OWF làm fix. Tên:
- OWF-HWA-S (nếu R* = OWF-HW-S);
- OWF-HUA (nếu R* = OWF-HU).

Lệnh: `owf_union.py … --variants "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"`, hoặc `"H|m(1e-5,16)|t(3e-4,0.5)"` cho OWF-HUA.

**Tập kiểm tra mới:** seed 49–51 của kho mới `fr49` (seed 49–54; 8 dataset có lỗ × 6 descriptor = 144 run; sinh bằng `hsi_fresh.py --keep`, chưa
dùng cho bất kỳ quyết định nào). Chạy đợt `t49` = OWF thường và OWF ngân hàng tỉ lệ → OWF-H (HSI-VN, `--hsiframes`), rồi hợp ngoại tuyến. R* và
C tính trên CÙNG 144 run.
- **L1 (hợp lệ):** TB segFAR ≤ 0.05 trên 8/8 dataset và ≤ 2/144 run > α.
- **L2 (recall):** chênh gộp C − R* ≥ +0.005 với cận dưới CI 95 % bootstrap (theo run) > 0.
- **L3 (điều hướng):** sai số gộp ≤ R* + 0.5 m.

**Quy tắc:** L1 ∧ L2 ∧ L3 ⇒ C là luật khuyến nghị mới. *Phụ (báo cáo, không quyết định):* recall CMU của C và R*, HSI-VN trên cùng run.

## Entry 13 — OWF-HW-S: ngân hàng tỉ lệ odometry + luật hợp hai bậc — đăng ký trước (2026-11-04 18:00 UTC; AUTOLOOP vòng 3 + 5)

**KẾT QUẢ TẬP KIỂM TRA (seed 46–48, 144 run mới, đợt `t46`; ghi 19:18 UTC). Quyết định: OWF-HW-S THAY OWF-HU làm luật khuyến nghị.**
R* = OWF-HU (Entry 12 đạt). Ô = recall / TB segFAR / run > α / sai số điều hướng (m).

| Dataset | OWF-HW-S | OWF-HU (R*) | OWF-HW | OWF-H-S | HSI-VN |
|---|---|---|---|---|---|
| Boreas | 0.970 / 0.0013 / 0 / 4.1 | 0.971 / 0.0010 / 0 / 3.9 | 0.972 / 0.0010 / 0 / 3.8 | 0.964 / 0.0005 / 0 / 4.2 | 0.883 / 0.0002 / 0 / 6.3 |
| CMU | 0.679 / 0.0014 / 0 / 2.9 | 0.603 / 0.0014 / 0 / 3.0 | 0.676 / 0.0014 / 0 / 2.9 | 0.603 / 0.0014 / 0 / 3.0 | 0.603 / 0.0014 / 0 / 3.0 |
| Nordland | 0.963 / 0.0006 / 0 / 3.6 | 0.948 / 0.0003 / 0 / 3.6 | 0.955 / 0.0003 / 0 / 3.7 | 0.919 / 0.0000 / 0 / 3.7 | 0.799 / 0.0000 / 0 / 4.3 |
| office | 0.957 / 0.0008 / 0 / 9.1 | 0.945 / 0.0012 / 0 / 10.0 | 0.946 / 0.0012 / 0 / 10.0 | 0.944 / 0.0008 / 0 / 9.2 | 0.852 / 0.0010 / 0 / 8.8 |
| old town | 0.934 / 0.0003 / 0 / 21.2 | 0.915 / 0.0003 / 0 / 23.6 | 0.916 / 0.0003 / 0 / 23.6 | 0.882 / 0.0003 / 0 / 26.6 | 0.757 / 0.0008 / 0 / 31.3 |
| countryside | 0.807 / 0.0013 / 0 / 25.7 | 0.746 / 0.0016 / 0 / 28.8 | 0.750 / 0.0016 / 0 / 28.8 | 0.783 / 0.0013 / 0 / 26.3 | 0.693 / 0.0016 / 0 / 22.4 |
| Oxford | 0.940 / 0.0044 / 0 / 18.3 | 0.932 / 0.0045 / 0 / 18.6 | 0.933 / 0.0045 / 0 / 18.6 | 0.930 / 0.0044 / 0 / 18.4 | 0.817 / 0.0043 / 0 / 21.4 |
| St Lucia | 0.966 / 0.0069 / 1 / 17.3 | 0.961 / 0.0076 / 1 / 17.5 | 0.961 / 0.0076 / 1 / 17.5 | 0.942 / 0.0069 / 1 / 18.6 | 0.887 / 0.0076 / 1 / 20.3 |
| **Gộp (144)** | **0.902 / 1 run / 12.75 m** | 0.878 / 1 / 13.61 | 0.889 / 1 / 13.60 | 0.871 / 1 / 13.74 | 0.786 / 1 / 14.72 |

- **K1 đạt:** TB segFAR tệ nhất 0.0069 (St Lucia), 1/144 run > α (cùng một run St Lucia như mọi luật, kể cả HSI-VN).
- **K2 đạt:** chênh OWF-HW-S − OWF-HU **+0.0244**, CI 95 % [+0.0185, +0.0307]; thắng 124 / hoà 1 / thua 19.
- **K3 đạt:** 12.75 m vs 13.61 m.

Tách đóng góp trên cùng run:
- *Hợp hai bậc* (OWF-HW − OWF-HU): +0.0110 [+0.0066, +0.0160], 112 thắng / 0 thua; gần như toàn bộ từ CMU (0.603 → 0.676).
- *Ngân hàng tỉ lệ* (OWF-HW-S − OWF-HW): +0.0134 [+0.0095, +0.0179]; countryside +0.057, old town +0.018, Nordland / office +0.01.

Điểm yếu còn lại: CMU (0.68; chuỗi ngắn), là đích của Entry 14. Bảng điểm: `analysis/results/owf/owfhws_test_s46_48_json.tgz`.

**Phát triển (không quyết định; nhãn chỉ để đánh giá).**
(a) *Ngân hàng tỉ lệ odometry* (`owf.py --qx 0.005,0.02 --scales 0.97,1.0,1.03`: 6 bộ lọc, chọn trực tuyến theo evidence; VIO 4Seasons dài hơn GNSS
1–12 %, odometry mô phỏng sai tỉ lệ ~3 %), đợt `devS` (149 run: seed 1–3 của 6 dataset có lỗ, NCLT, Oxford / St Lucia seed 0–2), cùng run:

| Luật | recall gộp | run > α | sai số (m) | countryside recall / sai số |
|---|---|---|---|---|
| OWF-H-S | 0.876 | 0 | 15.15 | 0.787 / 27.4 |
| OWF-H | 0.866 | 0 | 15.72 | 0.730 / 30.5 |
| OWF-S | 0.871 | 2 | 15.67 | 0.661 / 45.3 |
| OWF | 0.856 | 1 | 16.23 | 0.605 / 48.3 |
| HSI-VN | 0.786 | 0 | 16.81 | 0.646 / 28.9 |

(b) *Luật hợp hai bậc* trên tập A (404 run, `owf_union.py`, OWF thường): W(1e-5, 16, 1e-8, 2) = OWF-H ∨ (khối lượng ≥ 1 − 1e-5 sau 16·excl) ∨
(khối lượng ≥ 1 − 1e-8 sau 2·excl): Score **0.899**, 0 run > α, 13.73 m; CMU 0.794 (OWF-H 0.756, SH 0.834). W(…, 1e-7, 2) 0.900; W(…, 1e-9, 2) 0.898;
W(…, 1e-8, 4) 0.896 — bậc sớm cực chặt mở được đầu chuỗi CMU mà không vi phạm.

**Luật đăng ký: OWF-HW-S** = OWF với ngân hàng tỉ lệ (`--qx 0.005,0.02 --scales 0.97,1.0,1.03`, phần còn lại như Entry 10) → OWF-H (`--mode
xms0.9_16`, HSI-VN) → hợp hai bậc W(1e-5, 16, 1e-8, 2) với khối lượng / ảnh của OWF-S.
**Tập kiểm tra mới:** seed 46–48 của `hmm-navcache-r40` (144 run). Luật đương nhiệm R* = luật khuyến nghị sau Entry 12 (OWF-HU nếu Entry 12 đạt,
ngược lại OWF-H), tính trên CÙNG 144 run (OWF thường + OWF-H + mặt nạ, trong cùng đợt `t46`).
- **K1 (hợp lệ):** TB segFAR ≤ 0.05 trên 8/8 dataset và ≤ 2/144 run > α.
- **K2 (recall):** chênh gộp OWF-HW-S − R* ≥ +0.01 với cận dưới CI 95 % bootstrap > 0.
- **K3 (điều hướng):** sai số gộp ≤ R* + 0.5 m.
**Quy tắc:** K1 ∧ K2 ∧ K3 ⇒ OWF-HW-S là luật khuyến nghị mới. *Phụ (báo cáo):* OWF-HW (OWF thường + hợp hai bậc), OWF-H-S, HSI-VN.

## Entry 12 — OWF-HU: hợp của OWF-H với các báo OWF cực tự tin đã ổn định — đăng ký trước (2026-11-04 17:32 UTC; AUTOLOOP vòng 4)

**KẾT QUẢ TẬP KIỂM TRA (seed 43–45, 144 run mới, đợt `t43`; ghi 18:49 UTC). Quyết định: OWF-HU THAY OWF-H làm luật khuyến nghị.**

| Dataset | OWF-HU recall / segFAR / run > α / sai số | OWF-H | HSI-VN |
|---|---|---|---|
| Boreas | 0.970 / 0.0008 / 0 / 3.5 | 0.964 / 0.0006 / 0 / 3.5 | 0.889 / 0.0011 / 0 / 6.6 |
| CMU | 0.736 / 0.0052 / 0 / 3.6 | 0.736 / 0.0052 / 0 / 3.6 | 0.736 / 0.0052 / 0 / 3.5 |
| Nordland | 0.957 / 0.0031 / 0 / 4.3 | 0.911 / 0.0000 / 0 / 3.7 | 0.796 / 0.0003 / 0 / 6.2 |
| office | 0.942 / 0.0008 / 0 / 11.6 | 0.932 / 0.0008 / 0 / 11.7 | 0.872 / 0.0008 / 0 / 10.5 |
| old town | 0.911 / 0.0004 / 0 / 22.6 | 0.861 / 0.0004 / 0 / 27.7 | 0.746 / 0.0007 / 0 / 28.8 |
| countryside | 0.750 / 0.0044 / 0 / 36.2 | 0.740 / 0.0044 / 0 / 36.7 | 0.666 / 0.0014 / 0 / 29.5 |
| Oxford | 0.941 / 0.0057 / 0 / 20.5 | 0.935 / 0.0057 / 0 / 20.6 | 0.829 / 0.0075 / 0 / 22.8 |
| St Lucia | 0.963 / 0.0092 / 1 / 17.3 | 0.947 / 0.0092 / 1 / 18.3 | 0.905 / 0.0084 / 1 / 19.6 |

Gộp: OWF-HU **0.896**, OWF-H 0.878, HSI-VN 0.805; OWF-HU − OWF-H **+0.018** (CI 95 % [+0.014, +0.022]); run > α 1/144 cả ba luật (cùng một run St
Lucia); sai số gộp **14.94** / 15.73 / 15.92 m. **G1, G2, G3 đạt** ⇒ **OWF-HU là luật khuyến nghị**. Kiểm nhất quán: biến thể "H" của `owf_union.py`
trùng tuyệt đối OWF-H của `hsi_eval.py` (|Δ recall| max 0.0). Phụ (phát triển, tập A): hợp hai bậc trên nền HSI-VMN — Score 0.892, 0 run > α,
sai số **12.66 m** (điểm vận hành điều hướng tốt nhất đã đo).


**Bối cảnh.** Entry 11: OWF-H là luật khuyến nghị (tập mới 40–42: 0.885, 1/144 run > α, 14.46 m). Trên Nordland / old town / St Lucia, OWF một mình
báo được nhiều fix đúng hơn OWF-H (tập 40–42: 0.947 / 0.901 / 0.984 vs 0.919 / 0.852 / 0.970).
**Phát triển (tập A, 404 run, ngoại tuyến `analysis/owf_union.py` từ mặt nạ báo của OWF-H — đợt `hybE` — và frame OWF; biến thể "H" tái tạo
đúng OWF-H 0.8697):**

| Luật | Score (recall gộp) | run > α | sai số (m) |
|---|---|---|---|
| U(1e-3, 16) | 0.901 | 5 (Nordland) | 14.74 |
| U(1e-4, 16) | 0.896 | 2 | 13.97 |
| U(1e-4, 32) | 0.895 | 2 | 13.99 |
| **U(1e-5, 16)** | **0.892** | **0** | **13.74** |
| U(1e-5, 32) | 0.891 | 0 | 13.75 |
| OWF-H | 0.870 | 0 | 14.58 |

**Luật đăng ký: OWF-HU = U(1e-5, 16):** báo tại t nếu OWF-H báo, HOẶC (khối lượng đĩa OWF ≥ 1 − 1e-5 VÀ quãng đường từ đầu chuỗi ≥ 16·excl); vị trí
fix = của OWF-H nếu nó báo, ngược lại ảnh của OWF. Lý do cơ chế: sau vùng đầu chuỗi (nơi Mệnh đề 2 yếu) hậu nghiệm OWF ở mức 1 − 1e-5 hầu như
không sai (tập A: 0 run vi phạm); HSI chặn bớt các báo này vì null hồi cứu bảo thủ.
**Tập kiểm tra mới:** seed 43–45 của `hmm-navcache-r40` (144 run, 8 dataset × 6 desc × 3 seed); OWF, OWF-H (+ mặt nạ báo) chạy trong cùng job
(đợt `t43`); HSI-VN trên cùng cache (đợt `fr40`).
- **G1 (hợp lệ):** TB segFAR ≤ 0.05 trên 8/8 dataset và ≤ 2/144 run > α.
- **G2 (recall):** chênh gộp OWF-HU − OWF-H ≥ +0.01 với cận dưới CI 95 % bootstrap > 0.
- **G3 (điều hướng):** sai số gộp ≤ OWF-H + 0.5 m.
**Quy tắc:** G1 ∧ G2 ∧ G3 ⇒ OWF-HU thay OWF-H làm luật khuyến nghị; ngược lại OWF-H giữ nguyên. Ghi kèm so sánh với HSI-VN trên cùng run.

## Entry 11 — OWF-H: bộ ước lượng thế giới mở + lớp quyết định HSI, giao chuỗi khi đã "ổn định" — đăng ký trước (2026-11-04 15:40 UTC; AUTOLOOP vòng 1)

**KẾT QUẢ TẬP KIỂM TRA (seed 40–42, 144 run mới, đợt `t40`; ghi 17:31 UTC). Quyết định: OWF-H THAY HSI-VN làm luật khuyến nghị.**

| Dataset | runs | OWF-H recall / segFAR / run > α | HSI-VN | Δ recall (wins) | sai số OWF-H / HSI-VN (m) | OWF một mình (recall / segFAR / > α / err) | OWF-H-VMN (recall / err) | HSI-VMN |
|---|---|---|---|---|---|---|---|---|
| Boreas | 18 | 0.970 / 0.0006 / 0 | 0.890 / 0.0004 / 0 | +0.081 (16/18) | **2.8** / 7.5 | 0.958 / 0.0035 / 0 / 3.6 | 0.964 / 2.6 | 0.883 / 7.4 |
| CMU | 18 | 0.756 / 0.0072 / 0 | 0.756 / 0.0072 / 0 | +0.000 (0/18) | 3.3 / 3.3 | 0.727 / 0.0245 / 4 / 4.8 | 0.739 / 3.3 | 0.739 / 3.3 |
| Nordland | 18 | 0.919 / 0.0000 / 0 | 0.807 / 0.0000 / 0 | +0.112 (18/18) | **2.8** / 3.1 | 0.947 / 0.0265 / 1 / 18.0 | 0.909 / 2.8 | 0.799 / 3.1 |
| office | 18 | 0.933 / 0.0004 / 0 | 0.864 / 0.0004 / 0 | +0.069 (17/18) | 10.4 / **9.4** | 0.918 / 0.0000 / 0 / 10.5 | 0.915 / 10.2 | 0.844 / 9.1 |
| old town | 18 | 0.852 / 0.0022 / 0 | 0.747 / 0.0038 / 0 | +0.105 (15/18) | **31.1** / 36.8 | 0.901 / 0.0000 / 0 / 21.1 | 0.841 / 26.3 | 0.736 / 27.2 |
| countryside | 18 | 0.755 / 0.0007 / 0 | 0.677 / 0.0004 / 0 | +0.077 (10/18) | 30.4 / **23.6** | 0.651 / 0.0000 / 0 / 44.9 | 0.745 / 30.3 | 0.668 / 23.5 |
| Oxford | 18 | 0.924 / 0.0082 / 1 | 0.820 / 0.0082 / 1 | +0.104 (18/18) | **22.7** / 25.6 | 0.905 / 0.0005 / 0 / 20.5 | 0.918 / 22.3 | 0.814 / 25.4 |
| St Lucia | 18 | 0.970 / 0.0000 / 0 | 0.929 / 0.0000 / 0 | +0.040 (15/18) | **12.2** / 13.4 | 0.984 / 0.0000 / 0 / 11.9 | 0.967 / 12.2 | 0.927 / 13.3 |

Gộp: recall OWF-H **0.885** vs HSI-VN 0.811 (**+0.074**, CI 95 % [+0.060, +0.088]); run > α 1/144 vs 1/144 (cùng một run Oxford); sai số gộp
**14.46 vs 15.35 m**. **F1 đạt** (8/8, 1 ≤ 2 run), **F2 đạt**, **F3 đạt** (gộp −0.9 m; trong +1 m trên 6/8 — trượt countryside +6.8 m và office
+1.0 m). ⇒ theo quy tắc đã đăng ký: **OWF-H là luật khuyến nghị mới**; HSI-VN là tham chiếu. CMU không đổi (vùng đầu chuỗi phủ gần hết chuỗi CMU);
countryside là chỗ điều hướng còn kém.
*Phát triển thêm sau khi chốt (vòng 2 / 4 trên tập A, không thuộc quyết định này):* lân cận (t, D) phẳng (Score 0.866–0.871, mọi biến thể hợp lệ);
đặc trưng độ tin OWF cho HSI (`xmsc`) +0.0006; luật HỢP U(ε2, D2) = OWF-H ∨ (khối lượng OWF ≥ 1 − ε2 và ≥ D2·excl từ đầu chuỗi): U(1e-5, 16)
Score 0.892 (0 run > α, sai số 13.74 m), U(1e-4, 16) 0.896 (2 run), U(1e-3, 16) 0.901 (5 run) — ứng viên Entry 12.


**Bối cảnh.** Entry 10: OWF có recall cao nhất nhưng 19/404 run > α và điều hướng kém; HSI-VN hợp lệ từng run nhưng dùng chuỗi vị trí topo kém hơn.
AUTOLOOP (`handoff/AUTOLOOP.md`): Score = recall gộp với ràng buộc V1 (TB mọi dataset ≤ 0.05), V2 (≤ 2 % run > α), N1 (sai số gộp ≤ HSI-VN + 0.5 m).

**Phát triển (tập A của Entry 10 = 404 run seed 1–9 / NCLT / Oxford / St Lucia; nhãn chỉ để đánh giá; ngoại tuyến từ frame OWF đã lưu).**
- 13 biến thể lớp quyết định của chính OWF (`analysis/owf_decide.py`: lịch ε khởi đầu, tuổi track, cổng nhảy): không biến thể nào đạt V2 (11–19
  run > α) hay N1 (16.7–17.1 m).
- Ghép OWF → HSI (`analysis/owf_hybrid.py`: thay chuỗi `est_c` mà HSI đọc bằng ảnh fix của OWF, rồi chạy HSI-VN NGUYÊN BẢN):
  thay toàn bộ (`x`): CMU s1 segFAR 0.089 — chứng chỉ hình học của HSI (chuỗi khớp odometry) bị lừa vì quỹ đạo OWF được dead-reckon nên luôn
  khớp odometry, kể cả khi sai. Thay khi khối lượng OWF ≥ t (`xm`): hyb50 0.886 / 26 run > α, hyb90 0.880 / 18 run > α — mọi vi phạm ở CMU (đầu
  chuỗi ngắn). Thay khi tự tin VÀ đã đi ≥ D·excl từ đầu chuỗi (`xms<t>_<D>`, chỉ dùng chuỗi topo tự do khi mới bắt đầu):

| Biến thể (HSI-VN trên chuỗi ghép) | recall gộp | run > α | sai số (m) | Score |
|---|---|---|---|---|
| xms0.9_4 | 0.875 | 14 | 14.95 | – (V2) |
| xms0.9_8 | 0.872 | 9 | 14.67 | – (V2) |
| **xms0.9_16** | **0.870** | **0** | **14.58** | **0.870** |
| xms0.5_8 | 0.878 | 9 | 15.11 | – (V2) |
| xma0.9_8 (tuổi track thay quãng đường đầu chuỗi) | 0.850 | 0 | 14.91 | 0.850 |
| HSI-VN (tham chiếu) | 0.791 | 0 | 15.15 | 0.791 |
| HSI-VMN | 0.781 | 0 | 13.65 | 0.781 |

  Theo dataset (xms0.9_16 vs HSI-VN, recall / sai số): Boreas 0.962 / 4.3 vs 0.893 / 7.0; NCLT 0.768 / 5.5 vs 0.570 / 4.4; CMU 0.756 / 3.6 vs 0.756 /
  3.6 (đầu chuỗi chiếm gần hết chuỗi CMU ⇒ gần như HSI-VN); Nordland 0.887 / 4.8 vs 0.784 / 5.8; office 0.936 / 10.0 vs 0.870 / 9.0; old town
  0.842 / 31.9 vs 0.723 / 33.0; countryside 0.750 / 29.2 vs 0.657 / 26.7; Oxford 0.924 / 18.2 vs 0.805 / 21.1; St Lucia 0.959 / 17.2 vs 0.915 / 18.5.
  (Chọn D = 16 và t = 0.9 trên tập A ⇒ cần tập mới.)

**Luật đăng ký: OWF-H** = OWF (cấu hình Entry 10, không đổi) → `owf_hybrid.py --mode xms0.9_16` → HSI-VN (không đổi). Lý do cơ chế: lớp quyết
định HSI tự hiệu chuẩn trên excursion thật nhưng chứng chỉ của nó cần một chuỗi TỰ DO ở đầu chuỗi; OWF cho vị trí đúng hơn hẳn khi đã ổn định.

**Tập kiểm tra (mới, sinh trong AUTOLOOP sau mọi lựa chọn trên):** seed 40–42 của kho riêng `hmm-navcache-r40` (đợt `fr40`), 8 dataset có lỗ
(Boreas, CMU, Nordland, office, old town, countryside, Oxford, St Lucia) × 6 descriptor × 3 seed = 144 run; HSI-VN trên CÙNG cache (đợt `fr40`).
- **F1 (hợp lệ):** segFAR TB ≤ 0.05 trên 8/8 dataset và ≤ 2/144 run > α.
- **F2 (recall):** chênh recall gộp cặp OWF-H − HSI-VN > 0, cận dưới CI 95 % bootstrap (theo run) > 0.
- **F3 (điều hướng):** sai số gộp ≤ HSI-VN + 0.5 m và theo dataset ≤ HSI-VN + 1 m trên ≥ 6/8.
**Quy tắc quyết định:** F1 ∧ F2 ∧ F3 ⇒ OWF-H thay HSI-VN làm luật khuyến nghị. Ngược lại HSI-VN giữ nguyên; ghi tiêu chí trượt.
*Phụ (không quyết định):* OWF một mình và HSI-VMN trên OWF-H (`xms0.9_16:HSI-VN,HSI-VMN`) trên cùng run.

## Entry 10 — the open-world filter (OWF, idea 2b): presence by position, not by test — đăng ký trước (2026-11-04 09:13 UTC)

**Context.** Same problem and protocol (`handoff/07_IDEA1_SUMMARY.md` §1: maps with 30 % of the 300 m cells removed, label-free per-frame
report / no-report, recall at segFAR <= alpha = 0.05, navigation error, position audit). Baselines: idea 1 (SH, CST-JS, CST-F: topological
place filter + decision calibrated on counterfactual nulls) and idea 2a HSI-VN (Entries 1–9: same topological filter + report score learned
from hindsight geometric labels, conformal threshold on real excursions; recommended rule at the head of this branch).
**Provenance (read first).** This entry was developed in a chat whose checkout started at the branch-creation commit `7502e2c` (the clone did
not contain Entries 1–9); the HSI line was found only when pushing, and this entry was then rebased on top of it (Entry 10, Gate 18). The
design (section 5) used only seed 0 and idea-1 baselines; no HSI result influenced it. Seeds 1–9 are HSI's development data but were never
looked at for OWF; the project rule (`03_HANDOFF` §3.3: every new decision on an unused reserve group) is followed with seeds 25–27 (the last reserve group; 19–21 and 22–24 are left to the HSI line, whose chat was still active on this branch at 09:02 UTC).

### 1. Where the topological filter loses recall (measured before any design; navcache-v2, seeds 0–2, all 6 descriptors; labels only to evaluate)

| Dataset | chain MAP within excl (on-map frames) | top-1 within excl | SH recall |
|---|---|---|---|
| Boreas | 0.931 | 0.885 | 0.779 |
| NCLT | 0.775 | 0.724 | 0.612 |
| CMU | 0.940 | 0.914 | 0.764 |
| Nordland | 0.928 | 0.661 | 0.752 |
| office | 0.946 | 0.910 | 0.795 |
| old town | 0.874 | 0.837 | 0.687 |
| countryside | 0.800 | 0.733 | 0.513 |

The place chain (DiagFilter MAP, the `est_c` that idea 1 and HSI both use) is right on 0.78–0.95 of the on-map frames; the decision reports
0.51–0.80 of them (HSI-VN, development: 0.65–0.92). Label-ORACLE
thresholds on per-frame scores (posterior mass, log-odds, max-sim, Xu'21 off-map posterior) give only 0.10–0.77 at segFAR = 0.05. Frames
within 40 frames of a map entry or of the sequence start are 2–5 % of the on-map frames (CMU 24 %, short sequences), so the loss is in long
on-map stretches with weak appearance evidence. Structural cause: in a topological HMM the transition kernel is renormalised over the
remaining map nodes, so the belief of a robot that drives into a hole has nowhere to go but map nodes; the decision layer must then tell
"on the map with weak evidence" from "in a hole" statistically (all of idea 1's calibration machinery), and fails at hole edges.

### 2. Method — open-world filter (`analysis/owf.py`)

- **State.** Robot position on a metric grid (cell g = excl / 5; Nordland 1 frame) covering the map's bounding box grown by a band B
  (= the config's block, 300 m; Nordland 200 frames; NCLT 100 m), cells farther than B from every map image excluded, plus one
  position-less far state Omega. A cell is *mapped* when it holds >= 1 map image. **Presence on the map is a function of the position**
  (no presence chain, no off-map node).
- **Motion (mass-conserving).** x_t = x_{t-1} + u_t + w_t, u_t the odometry increment (real VIO / wheel+gyro / FOG, or simulated, exactly as
  every idea-1 rule and the Kalman evaluation use); per-axis process variance q |u_t| + drift^2 (2 L_s |u_t| + |u_t|^2), L_s = odometry path
  since the last confident frame (largest disc mass >= 0.5), drift = 0.02 (systematic drift grows linearly with the path since the last fix).
  The belief array is shifted only by whole cells (sub-cell odometry kept as a phase phi; world position of cell c = origin + g c + phi), so
  deterministic motion adds no numerical diffusion; the noise is an exact Gaussian blur applied when the accumulated variance >= (g/2)^2.
  Mass that leaves the band goes to Omega; Omega re-enters at rate p_in = 0.01 / frame through the prior. Kidnap (teleport) rate
  p_kid = 1e-12 (a car does not teleport; every teleported unit of mass is a seed for an alias).
- **Emission (likelihood ratios against one reference p0 = "the view is unrelated to this map image").** Unmapped cells and Omega: LR = 1.
  Map image i: z_i = robust z-score of the frame's similarity to i within the frame's own profile over the whole map (median, 1.4826 MAD);
  log L_i = beta z_i - log mean_j exp(beta z_j) (exponential tilt, beta = 1) so that mean_j L_j = 1 exactly: the frame's own profile is its
  null, and a diffuse belief over the map gains or loses nothing on average (Proposition 1). Mapped cell: L_c = mean_{i in c} L_i.
  Evidence per distance: log L is weighted by w_t = min(1, |u_t| / ell), ell = 0.4 excl (consecutive frames ~1 m apart see the same scene;
  without it aliasing is counted once per frame — the first design run reported 80 % of the off-map frames).
- **Prior.** p_map0 = 0.5 spread over the map images, p_Omega0 = 0.1, the rest uniform over the band.
- **Odometry noise, self-calibrated online.** Three filters q in {0.005, 0.02, 0.08} excl run in parallel; at every frame the decision is
  read from the filter with the largest cumulative log evidence sum_{s<=t} log p(z_s | z_<s) (causal model selection; the evidence is the
  normaliser of each update).
- **Decision.** The excl-disc with the largest posterior mass around one of the 12 heaviest mapped cells; the reported fix x_hat is the map
  image nearest to the posterior MEAN inside that disc (MMSE snapped onto the map; design §5); report x_hat iff the disc mass >= 1 - eps. **Default eps = 1e-3**; the operating curve sweeps eps in {0.2 … 1e-5}.
- **Cost.** One forward pass per filter; 2–13 ms/frame for the three filters on one shared CPU core (design runs), no map surgery, no
  forward simulation, no calibration data, no labels.

### 3. Theory (to be written out in the report)

*Notation.* N = cells within excl of a map image, U = the other band cells + Omega (all with LR = 1); a report needs posterior mass >= 1 - eps
on an excl-disc around a map image, hence P_t(N) >= 1 - eps. Unnormalised filter pi~_t = motion(pi~_{t-1}) * L_t (motion conserves mass).
- **Proposition 1 (no net pull of a diffuse belief).** If the predicted belief restricted to the map images is uniform, sum_i pred(i) L_i =
  pred(map) exactly at every frame (mean_j L_j = 1), whatever the frame: the mapped odds of a robot with no positional knowledge move only
  through the shape of the profile, never through its level (contrast: topological HMMs renormalise onto the nodes).
- **Proposition 2 (false reports in an off-map stretch; Ville).** Let a stretch start at t0 with mapped odds O_0 = P(N) / P(U) and let lambda
  be the share of the U mass that motion and seeds (kidnap, Omega re-entry) move into N during the stretch. If (E1) the weighted LR of every
  cell of N has conditional mean <= 1 given the past while the robot is off the map, then T_t = pi~_t(N) + pi~_t(U) is a nonnegative
  supermartingale and P(any report in the stretch) <= eps (1 + O_0) / ((1 - eps)(1 - lambda)). For a robot tracked into a hole (its mass
  dead-reckoned into U, O_0 ~ 0, lambda ~ motion tail + p_kid T) the bound is ~eps: **no edge term** (contrast idea 1, Entry 37 H37b). At
  a sequence start O_0 = p_map0 / (1 - p_map0) ~ 1 and lambda can be large (diffuse U mass flows into N), so the start is the weak case.
- **(E1) is violated by coherent aliasing** (consecutive off-map frames match the same look-alike stretch). The audit (observed segFAR /
  bound, per position class) measures the inflation; the default eps = 1e-3 = alpha / 50 assumes an inflation <= 50 (design: Nordland
  needs ~eps <= 0.01).

### 4. Pre-registration (committed before any held-out OWF result is read; nothing below has been computed on these sets)

**Set A — development-wide evaluation (all hypotheses H1–H9).** (a) seeds 1–9 x 6 descriptors x 6 holed datasets (Boreas, CMU, Nordland,
office, old town, countryside; `hmm-navcache-v2`) = 324 runs; (b) NCLT (natural off-map, 1 layout) x the 5 descriptors not used in design;
(c) Oxford RobotCar (45 runs, `hmm-e37-caches`) and St Lucia (30 runs). Total 404 runs (the six jobs of the probe kernel `owfp-1`, started
before this commit and not read, belong to this set). Baselines on the SAME runs: SH = CMS-CPC/H+SH+G+NGRr, CST-JS, CST-F (idea-1 defaults,
`analysis/results/baselines_idea1/`, Entry 38 files for seeds 0–9, Entry 37 for St Lucia) and HSI-VN / HSI-VMN (`analysis/results/hsi/
hsi_results_json.tgz`, main). One configuration for every dataset and descriptor (section 2); `analysis/owf_summary.py` computes every number.
- **H1 (validity):** at eps = 1e-3 the mean segFAR <= 0.05 on every one of the 9 datasets.
- **H2 (recall vs idea 1):** at eps = 1e-3 the paired mean recall > SH's on >= 7 / 9 datasets; **H2b:** > CST-JS's on >= 7 / 9.
- **H3 (per position):** report rate of the real off-map segments <= 0.07 in every position class (start / edge / deep,
  `position_audit.seg_classes`) with >= 50 segments, on every dataset.
- **H4 (navigation):** mean navigation error (Kalman with the reported fixes, `nav_demo.track`) <= SH's on >= 6 of the 7 main datasets.
- **H5 (cost):** <= 15 ms/frame (three filters, one CPU core) on every dataset.
- **H6 (matched operating point):** OWF recall on its eps curve at the run's SH segFAR >= SH recall on >= 8 / 9 datasets.
- **H7 (secondary operating point eps = 0.01):** mean segFAR <= 0.05 on >= 8 / 9 datasets and recall > SH on >= 8 / 9.
- **H8 (recall vs HSI-VN):** at eps = 1e-3 the paired mean recall > HSI-VN's on >= 7 / 9 datasets.
- **H9 (navigation vs HSI-VN):** mean navigation error <= HSI-VN's on >= 5 / 9 datasets.

**Set B — decision set: reserve seeds 25–27** (`caotienminh1/hmm-navcache-r19`, 6 holed datasets x 6 descriptors x 3 seeds = 108 runs;
recorded in `03_HANDOFF` §5). OWF (eps = 1e-3) and HSI-VN / HSI-VMN (`hsi_eval.py`, unchanged code of the branch head)
run on the same caches in the same wave; no SH (needs the idea-1 GPU pipeline).
- **D1 (validity):** OWF mean segFAR <= 0.05 on 6 / 6 datasets and <= 5 % of the 108 runs above alpha.
- **D2 (recall):** pooled paired recall difference OWF − HSI-VN > 0 with the lower end of the 95 % bootstrap CI (runs resampled) > 0.
- **D3 (navigation):** OWF mean navigation error <= HSI-VN's + 1 m on >= 4 / 6 datasets.
**Decision rule.** D1 ∧ D2 ∧ D3 ⇒ OWF becomes the recommended label-free rule of the branch (HSI-VN stays as the reference). Otherwise HSI-VN
stays recommended and OWF is reported with the failing criteria; any change after this point needs a new reserve set (none left after 25–27: generate seeds 28–30 with `hsi_fresh.py --keep`).
*Secondary (no decision): ablations on seeds 1–2, cosplace + megaloc, 7 datasets — closed world (unmapped LR ~ 0: the topological
analogue), no distance weighting (ell = 0), fixed q = 0.02 excl, kidnap 1e-4; hole ratio 10 % / 50 % (`hmm-navcache-holes`, seeds 0–2,
6 datasets x 6 descriptors); per-descriptor segFAR; worst run.*

### 5. Design results (seed 0; tuned on these — not evidence)

Design path (all on seed 0, cosplace unless stated; `owf.py` options in brackets): first run without distance weighting: FL 0.80 on CMU
(aliasing counted per frame) -> ell = 0.4 excl; start prior uniform over the band too slow on CMU -> p_map0 = 0.5; Boreas false reports
deep in holes from a look-alike 170 m behind the hole entry, seeded by the kidnap rate 1e-4 -> p_kid 1e-12 (Boreas segFAR 0.086 -> 0.023 at
eps 0.05, NCLT 0.091 -> 0.000); band x2 / x4 and p_in 1e-3 change nothing on Nordland (its failures: sequences that START in a 400-frame
hole, coherent railway aliasing); ell = 1.0 excl valid everywhere but loses recall (CMU 0.69, countryside 0.47) -> kept 0.4; fixed q in
{0.005, 0.02} excl each fails somewhere -> online evidence selection over {0.005, 0.02, 0.08} excl (Nordland segFAR 0.064 -> 0.010 at
eps 1e-3); profile-correlation weighting (1 - r^2) rejected (r = 0.98–0.998 everywhere: far stronger than ell, kills countryside).
Final configuration (section 2), eps curve; SH / CST-JS = idea-1 defaults on the SAME runs (Entry 38 files):

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

Design reading: at eps = 1e-3 every design run is valid (worst 0.015) and above SH on 12 / 15 runs; it is below SH where SH is already high
and the OWF start / re-entry delay dominates (CMU short sequences: cosplace -0.031, megaloc -0.014; countryside cosplace -0.106). Position
classes: no reported EDGE segment in any design run (Boreas 0/39, NCLT 0/26, Nordland 0/12, old town 0/9, office 0/10, countryside 0/9);
the remaining false reports are starts (CMU at eps >= 0.05) and Nordland sequences that start inside a hole. The idea-1 weaknesses
named in `07` §4 — edge reports, recall capped by the decision, cost — are the ones the design addresses.
Fix position (design, eps = 1e-3, cosplace s0): the image nearest to the posterior mean of the disc vs the highest-LR image of the best
cell — same recall, navigation error old town 21.1 vs 21.8 m, CMU 2.7 vs 2.9 m ⇒ posterior mean (`--xhat mean`, default).
Probe kernel (`owfp-1`, Set-A jobs, started before this commit): only its timing / memory / mount checks are read before the wave;
its six results are part of Set A and are evaluated with it.

**Kết quả giữ ra Entry 5 (đợt `hsi9`, 441 + 216 lỗ + 36 tự nhiên run; nguồn cache đã kiểm; 2026-11-03 19:30 UTC).** Gộp 413 run (recall / segFAR TB /
run > α / sai số): HSI-rot-m-sc 0.772 / 0.0026 / 0 / 15.0; **HSI-V 0.786 / 0.0040 / 0 / 15.3**; HSI-VM 0.775 / 0.0026 / 0 / **13.6**; HSI-Vc 0.775 / 0.0030 /
0 / 15.4; HSI-Gdrop 0.784 / 0.0036 / 0 / 14.9; geo-rm (chỉ chứng chỉ) 0.684 / 0.0007 / 0 / 16.2; SH 0.731 / 0.0029 / 2 / 15.6. Theo dataset (HSI-V vs
HSI-rot-m-sc): NCLT 0.645 vs 0.577 (+0.068; SH 0.690), CMU 0.676 vs 0.652 (+0.024), Oxford 0.807 vs 0.764, countryside 0.666 vs 0.642, St Lucia 0.916 vs
0.905; các dataset khác ±0.005. HSI-V so với SH: **H1–H5 đạt** (0/413; ≥ SH trên 7/9, gộp +0.054; DINOv2 + NetVLAD +0.110; điều hướng 7/9; vị trí 9/9).
**H9 không đạt** — gộp +0.014 ≥ 0.01 và NCLT +0.068 đạt, nhưng CMU +0.024 < +0.03. **H10 đạt** (geo-rm 0/413 run > 0.05; cũng 0/108 lỗ 10 %, 0/108 lỗ 50 %,
0/36 tự nhiên — giả định ε_G nhỏ của Mệnh đề 6 đứng vững). **H11 đạt** (HSI-V: lỗ 10 % 0/108, lỗ 50 % 5/108 = 4.6 % — đều ở CMU, HSI-rot-m-sc 4/108;
tự nhiên 0/36). Lỗ 50 %: HSI-V recall 0.752 vs 0.744 nhưng sai số old town 62.8 vs 56.7 m; HSI-VM 0.740, sai số 19.6 vs 22.6 m.
**Quyết định (theo quy tắc đăng ký trước):** H9 trượt ⇒ **HSI-rot-m-sc vẫn là luật khuyến nghị**; HSI-V báo cáo như biến thể hợp lệ có recall cao
nhất (+0.014 gộp, NCLT +0.068, 0 vi phạm) — cơ chế (cầu hồi cứu neo bằng chứng chỉ) được xác nhận bởi H10 và ablation (Vc giữ chứng chỉ trong α:
+0.003; Gdrop bỏ chứng chỉ khỏi α nhưng cầu cũ: +0.012). HSI-VM là điểm vận hành ưu tiên điều hướng (−1.4 m, recall +0.003). Tập xác nhận mới
(seed 10–12) đang chạy (đợt `hsi10`): C1 áp cho HSI-rot-m-sc, C2 kiểm dấu lợi ích của HSI-V trên dữ liệu chưa từng thấy.

## Quét α và tham chiếu Claxton'24 (mô tả, không quyết định luật; đợt `hsi8`, 413 run giữ ra, 2026-11-03 19:00 UTC)

Luật HSI-rot-m-sc ở α ∈ {0.01, 0.02, 0.05, 0.1, 0.2} (`paper/tables/hsi_alpha.md`, `paper/figures/hsi_alpha.png`). segFAR thực (TB các TB dataset /
dataset tệ nhất / run > α / run > 0.05 / recall gộp / sai số): α 0.01 — 0.0008 / 0.0030 / 6 / 0 / 0.707 / 16.5; 0.02 — 0.0013 / 0.0035 / 4 / 0 / 0.733 /
15.9; 0.05 — 0.0023 / 0.0060 / 0 / 0 / 0.772 / 15.0; 0.1 — 0.0046 / 0.0143 / 0 / 0 / 0.799 / 15.0; 0.2 — 0.0083 / 0.0437 / 0 / 0 / 0.811 / 16.0.
**Đọc:** bảo đảm đúng ở mọi mức (TB ≪ α) nhưng bảo thủ 5–25× — hệ quả dự kiến của null là TẬP CHA của off-map (có thể off-map ∪ fix sai ∪ chưa
xác minh, Mệnh đề 4 (i)); ở α nhỏ (0.01) vài run vượt do số đoạn hiệu chuẩn ít (ngưỡng conformal rời rạc). Recall tăng đều theo α (0.707 → 0.811;
oracle 0.845). Tham chiếu **Claxton'24** (MLP giám sát bằng nhãn của 2 điều kiện dễ nhất, kiểu RA-L'24): recall 0.729 nhưng **287/413 run vượt
α**, sai số 46 m — một bộ giám sát học có nhãn không được hiệu chuẩn cho off-map không thay được hiệu chuẩn trên excursion thật; Xu'21: 202/413.

## Entry 9 — nhân bản Entry 8 trên tập mới seed 16–18 — đăng ký trước (2026-11-04 04:30 UTC)

*Viết khi tập seed 16–18 ĐANG được sinh (đợt `hsi17`), chưa có kết quả nào trên đó. Đây là lần kiểm CUỐI CÙNG của giả thuyết HSI-VN: dù kết quả thế
nào, sẽ không kiểm lại trên tập khác.*
**Lý do:** trên seed 13–15, HSI-VN đạt T1, T2, T4 và trượt T3 ở tiêu chí cơ chế (khoá 7 → 4, cần ≤ 3.5). Nhân bản với CÙNG quy tắc, không nới.
**Đăng ký trước (seed 16–18, 6 dataset × 6 descriptor = 108 run, so với HSI-rot-m-sc trên cùng run):** T1–T4 y hệt Entry 8 (`analysis/hsi_entry8_test.py`).
**Quyết định:** T1 ∧ T2 ∧ T3 ∧ T4 cho HSI-VN ⇒ HSI-VN thay HSI-rot-m-sc làm luật khuyến nghị (bằng chứng: phát triển 413 run + seed 13–15 + seed 16–18);
nếu không ⇒ HSI-rot-m-sc giữ nguyên, HSI-VN báo cáo như điểm vận hành trội Pareto nhưng chưa đạt tiêu chí cơ chế. Thứ cấp (báo cáo, không quyết
định): gộp hai tập mới (216 run).
*Ghi chú (Entry 8 phụ):* hạ ngưỡng nhãn tối thiểu của lần học đầu (50 → 20) không đổi kết quả trên 5 run CMU phát triển — khởi động lạnh bị giới hạn
bởi độ trễ có nhãn hồi cứu, không bởi ngưỡng.

**Kết quả KIỂM TRA Entry 9 (seed 16–18, 108 run chưa từng thấy, đợt `hsi19`, cache `caotienminh1/hmm-navcache-f16` đã kiểm 108/108; 2026-11-04
06:15 UTC).** Gộp (recall / segFAR TB / run > α / sai số): HSI-rot-m-sc 0.750 / 0.0015 / 0 / 14.5; HSI-V 0.759 / 0.0021 / 1 / 13.9; HSI-N 0.754 / 0.0007 / 0 / 13.8;
**HSI-VN 0.763 / 0.0014 / 0 / 14.0**; HSI-VMN 0.750 / 0.0007 / 0 / 11.9; geo-rm 0.660 / 0.0000 / 0 / 14.3; Xu'21 0.632 / 0.158 / **49** / 49.9; Claxton'24 0.710 /
0.207 / **81** / 45.0; oracle 0.829. CMU: HSI-rot-m-sc 0.574, **HSI-VN 0.624**.
- HSI-VN: **T1 đạt** (0/108; TB dataset tối đa 0.0059), **T2 đạt** (+0.0138, bootstrap 95 % [+0.0083, +0.0200], thắng 65/108), **T3 đạt** (CMU +0.050; khoá 11 → 5
  ≤ 5.5), **T4 đạt** (−0.49 m) ⇒ **TẤT CẢ ĐẠT**.
- HSI-VMN: T1, T4 đạt (−2.60 m), T2 không (+0.0003), T3 không (khoá 11 → 8).
- Gộp hai tập mới (seed 13–18, 216 run, thứ cấp): HSI-VN 0/216 run > α; recall +0.0150 (bootstrap 95 % [+0.0103, +0.0201], thắng 129/216); CMU +0.055,
  khoá 18 → 9; điều hướng −0.53 m. HSI-VMN: +0.0027, −2.59 m.
**Quyết định (theo quy tắc đăng ký trước):** **HSI-VN thay HSI-rot-m-sc làm luật khuyến nghị của ý tưởng 2** (bằng chứng: 413 run phát triển, seed
13–15 đạt 3/4 tiêu chí, seed 16–18 đạt 4/4). HSI-VMN là điểm vận hành ưu tiên điều hướng (−2.6 m, recall như HSI-rot-m-sc). Giả thuyết HSI-VN đã
kiểm lần cuối như đã cam kết; mọi thay đổi sau này cần một tập mới (seed 19+).

## Entry 8 — vách khoá hiệu chuẩn và căn chỉnh Neyman–Pearson (HSI-VN) — đăng ký trước (2026-11-04 03:38 UTC)

*Từ đây: seed 0–9 (413 run) = dữ liệu PHÁT TRIỂN (được chẩn đoán); seed 10–12 đã dùng cho C1–C4 / Entry 7; **seed 13–15 = tập KIỂM TRA**, sinh bởi
đợt `hsi13` (cache giữ lại, xuất bản công khai sau khi sinh), chưa có kết quả nào của bất kỳ luật nào trên đó. Viết TRƯỚC khi tập kiểm tra sinh xong.*
**Chẩn đoán (phát triển; `paper/hsi_theory.md` Mệnh đề 7):** CMU có hai chế độ theo seed — ở 27/60 run (HSI-rot-m-sc) nhánh học TẮT HẲN (frac_c <
0.1, recall ~0.52–0.66; SH 0.87–0.98), ở các run khác HSI thắng SH. Cơ chế: ngưỡng conformal = phân vị của max điểm theo đoạn; điểm GBM bão hoà;
khi tỉ lệ q đoạn null có frame được phép báo vượt α, θ nhảy từ −∞ lên ≈ 1 (vách). Đoạn đặt ngưỡng đều là frame CHƯA TỪNG XÁC MINH — đầu các
chuỗi bắt đầu trong lỗ (nới đầu chuỗi của Entry 3) và vài chuỗi ngắn hoàn toàn đúng — mà mô hình (học trên nhãn đúng/sai CÓ nhãn) chưa từng thấy
là âm. Thử và loại: đặc trưng hubness theo nơi (bản đồ tự học điểm mù — 1 % nơi hút 36–46 % fix sai, nhưng không mở khoá), chứng chỉ cửa sổ ngắn
"học từ chuỗi dài" (ước lượng thầy đánh giá thấp lỗi thật: 0.005 vs 0.097), chứng chỉ tự đồng dạng bản đồ (K = 0 gần như không bao giờ ở ℓ ≤ 30 m),
Mondrian theo trạng thái bằng chứng (mở khoá nhưng mất ở run không khoá). **Thay đổi (một cờ, `train_null=True`):** huấn luyện (c) với dương =
frame đã xác minh, âm = TOÀN BỘ null hồi cứu (gồm frame chưa xác minh), chỉ trên đơn vị huấn luyện ⇒ điểm ước lượng tỉ số hợp lý so với chính
phân phối null dùng để hiệu chuẩn (Neyman–Pearson), bảo đảm split conformal giữ nguyên.
**Phát triển (413 run seed 0–9; recall / segFAR TB / run > α / sai số):** HSI-rot-m-sc 0.772 / 0.0026 / 0 / 15.0; HSI-V 0.786 / 0.0040 / 0 / 15.3; **HSI-VN
0.796 / 0.0029 / 0 / 15.1** (CMU 0.761 vs 0.652; run CMU bị khoá 27 → 1 / 60); HSI-VMN 0.786 / 0.0017 / 0 / 13.6 (CMU 0.753); HSI-N (không V) 0.784 /
0.0021 / 0 / 15.3 (CMU 0.741); SH 0.731 / 0.0029 / 2 / 15.6 (CMU 0.835). Tập thiết kế: HSI-VN 0.720, segFAR max 0.014 (HSI-V 0.044).
**Đăng ký trước (tập kiểm tra seed 13–15, 6 dataset × 6 descriptor = 108 run, so với HSI-rot-m-sc trên cùng run):** luật ứng viên chính **HSI-VN**;
phụ **HSI-VMN**; ablation HSI-V, HSI-VM, HSI-N; chẩn đoán geo-rm, Xu'21, Claxton'24, oracle.
- **T1 (hợp lệ):** ≤ 5 % run segFAR > 0.05 và segFAR TB ≤ 0.05 trên 6/6 dataset.
- **T2 (recall):** recall gộp HSI-VN − HSI-rot-m-sc ≥ +0.01 (kèm bootstrap 95 %).
- **T3 (cơ chế, CMU):** recall CMU HSI-VN − HSI-rot-m-sc ≥ +0.03 VÀ số run CMU bị khoá (frac_c < 0.1) của HSI-VN ≤ một nửa của HSI-rot-m-sc.
- **T4 (điều hướng):** sai số gộp HSI-VN ≤ HSI-rot-m-sc + 0.5 m.
**Quyết định:** T1 ∧ T2 ∧ T3 ∧ T4 ⇒ HSI-VN thay HSI-rot-m-sc làm luật khuyến nghị; nếu HSI-VN chỉ trượt T4 mà HSI-VMN đạt cả bốn (T2, T3 tính cho
HSI-VMN) ⇒ HSI-VMN; còn lại giữ HSI-rot-m-sc. Kết quả báo cáo dù thuận hay nghịch.

**Kết quả KIỂM TRA Entry 8 (seed 13–15, 108 run chưa từng thấy, đợt `hsi16`, cache `caotienminh1/hmm-navcache-f13` đã kiểm 108/108; 2026-11-04
04:27 UTC).** Gộp (recall / segFAR TB / run > α / sai số): HSI-rot-m-sc 0.752 / 0.0012 / 0 / 16.4; HSI-V 0.756 / 0.0011 / 0 / 16.3; **HSI-VN 0.768 / 0.0012 / 0 /
15.8**; HSI-VMN 0.757 / 0.0007 / 0 / 13.8; HSI-N 0.760 / 0.0008 / 0 / 16.0; geo-rm 0.676 / 0.0001 / 0 / 16.2; Xu'21 0.634 / 0.133 / **44** / 57.4; Claxton'24 0.717 /
0.197 / **77** / 51.9; oracle 0.829. CMU: HSI-rot-m-sc 0.612, HSI-V 0.598, **HSI-VN 0.671**, HSI-VMN 0.662.
- HSI-VN: **T1 đạt** (0/108; TB dataset tối đa 0.0031), **T2 đạt** (+0.0162, bootstrap 95 % [+0.0094, +0.0241], thắng 64/108), **T3 không đạt** — CMU +0.059 (≥ 0.03
  đạt) nhưng số run CMU bị khoá 7 → 4 (cần ≤ 3.5), **T4 đạt** (−0.58 m).
- HSI-VMN: T1 đạt, T2 không đạt (+0.0051, [−0.0017, +0.0134]), T3 không đạt (CMU +0.050; khoá 7 → 5), T4 đạt (−2.57 m).
**Quyết định (theo quy tắc đăng ký trước):** giữ **HSI-rot-m-sc** làm luật khuyến nghị chính thức. Ghi nhận trung thực: trên dữ liệu mới, HSI-VN
**trội Pareto** so với HSI-rot-m-sc ở cả ba thước đo kết quả đã đăng ký (hợp lệ như nhau 0/108, recall +0.016 với CI dương, điều hướng −0.58 m), chỉ
trượt tiêu chí cơ chế (giảm một nửa số run bị khoá); lợi ích CMU lặp lại (+0.059, dev +0.106). Khoá còn lại ở CMU = nhiễm null bởi chuỗi ngắn hoàn
toàn đúng (Mệnh đề 7 (iii)) — giới hạn thông tin, không phải lỗi cài đặt.
**Quét α của HSI-VN (phát triển, đợt `hsi18`, mô tả):** segFAR TB các TB dataset / dataset tệ nhất / run > α / recall: α 0.01 — 0.0011 / 0.0038 / 9 / 0.727;
0.02 — 0.0014 / 0.0055 / 1 / 0.758; 0.05 — 0.0027 / 0.0089 / 0 / 0.796; 0.1 — 0.0035 / 0.0099 / 0 / 0.808; 0.2 — 0.0046 / 0.0202 / 0 / 0.812. Ở mọi α, recall
HSI-VN > HSI-rot-m-sc cùng α (0.707 / 0.733 / 0.772 / 0.799 / 0.811).
**Bền (phát triển, mọi run; đợt `hsi15`):** lỗ 10 % — HSI-VN 0/108 run > α, recall 0.772 (HSI-rot-m-sc 0.755); lỗ 50 % — 4/108 (HSI-rot-m-sc 4/108, đều CMU),
recall 0.754 vs 0.744, sai số 22.2 vs 22.6 m; off-map tự nhiên 4Seasons — 0/36 (HSI-rot-m-sc 1/36), segFAR TB 0.0037 vs 0.0097.

## Kết quả tập xác nhận mới (seed 10–12, 108 run; đợt `hsi10` + `hsi12`, kéo về 2026-11-04 02:09 UTC) — C1–C4, Entry 7

Cache sinh lại hai lần độc lập (hai đợt) cho kết quả HSI-rot-m-sc giống hệt nhau trên 108/108 run (tất định). Không có SH (cần GPU). Gộp 108 run
(recall / segFAR TB / run > 0.05 / sai số m): **HSI-rot-m-sc 0.784 / 0.0029 / 0 / 13.9**; HSI-V 0.792 / 0.0028 / 0 / 13.8; HSI-VM-nosc 0.792 / 0.0056 / 0 / 13.2;
HSI-VM 0.782 / 0.0026 / 0 / 12.8; HSI-M 0.776 / 0.0028 / 0 / 13.0; HSI-V-sc5 0.795 / 0.0073 / 1 / 16.4; HSI-V-nosc 0.804 / 0.0083 / 1 / 17.1; chỉ chứng chỉ
(geo-rm) 0.675 / 0.0001 / 0 / 15.6; tham chiếu có nhãn: Xu'21 0.609 / 0.150 / **33** / 48.3, Claxton'24 0.716 / 0.196 / **75** / 45.6; oracle 0.833.
- **C1 đạt:** luật được chọn (HSI-rot-m-sc) 0/108 run > 0.05, segFAR TB dataset ≤ 0.012 (6/6).
- **C2 không đạt (cùng dấu, nhỏ hơn ngưỡng):** HSI-V − HSI-rot-m-sc = +0.0074 (bootstrap 95 % [+0.0026, +0.0127], thắng 64/108) < +0.01. Lợi ích của
  cầu neo bằng chứng chỉ lặp lại về dấu và có ý nghĩa thống kê nhưng nhỏ hơn trên tập giữ ra (+0.014).
- **C3 đạt:** chứng chỉ một mình 0/108 run > 0.05 (tổng cộng 0/773 run trên mọi tập).
- **C4:** Entry 6 giữ HSI-rot-m-sc ⇒ C4 trùng C1 (đạt). Biến thể bỏ cổng (sc5, nosc) lặp lại cái giá điều hướng trên dữ liệu mới (+2.5 / +3.2 m).
- **Entry 7 (HSI-VM-nosc):** E1 đạt (0/108; TB dataset ≤ 0.017), **E2 không đạt** (+0.0080, bootstrap 95 % [−0.0020, +0.0182] < +0.01), E3 đạt (−0.66 m).
  **Quyết định:** giữ HSI-rot-m-sc.
**Kết luận cuối của vòng tự động:** luật khuyến nghị của ý tưởng 2 là **HSI-rot-m-sc** — hợp lệ ở 0/413 run giữ ra và 0/108 run mới, +0.041 recall so
với ý tưởng 1 (SH) trên giữ ra. Các cải tiến sau đó (Entry 4–7) đều hợp lệ và lặp lại về dấu trên dữ liệu mới, nhưng lợi ích (≤ +0.008 recall, hoặc
−1 m điều hướng với HSI-VM) không vượt các ngưỡng đã đăng ký trước ⇒ báo cáo như các điểm vận hành thay thế (recall: HSI-V; điều hướng: HSI-VM),
không thay luật.

## Entry 7 — HSI-VM-nosc, quyết định CHỈ trên tập xác nhận mới — đăng ký trước (2026-11-04 02:05 UTC)

*Viết sau kết quả giữ ra của Entry 6 (bên dưới) và TRƯỚC khi xem bất kỳ kết quả nào của tập mới seed 10–12 (đợt `hsi10`, `hsi12` chưa được kéo về).*
**Bối cảnh:** trên tập giữ ra (đã dùng 6 vòng), biến thể ablation HSI-VM-nosc (cầu neo bằng chứng chỉ + Mondrian theo chế độ + KHÔNG cổng nhất
quán ngắn hạn) có recall 0.794 (+0.022), 1/413 run > α, sai số điều hướng 13.9 m (−1.1 m) — tốt nhất cả ba trục; lỗ 10 % 0/108, lỗ 50 % 4/108 (sai số
20.6 vs 22.6 m), tự nhiên 1/36. Giả thuyết này sinh ra từ tập giữ ra nên chỉ được kiểm trên dữ liệu chưa thấy.
**Đăng ký trước (tập mới seed 10–12, 108 run, đợt `hsi12`, so với HSI-rot-m-sc trên cùng run):** **E1** ≤ 5 % run segFAR > 0.05 và segFAR TB ≤ 0.05
trên 6/6 dataset; **E2** recall gộp ≥ HSI-rot-m-sc + 0.01; **E3** sai số điều hướng gộp ≤ HSI-rot-m-sc + 0.5 m. **Quyết định:** E1 ∧ E2 ∧ E3 ⇒
HSI-VM-nosc thay HSI-rot-m-sc làm luật khuyến nghị (bằng chứng: giữ ra + tập mới); nếu không ⇒ giữ HSI-rot-m-sc.

## Entry 6 — khi null đã sạch, bỏ phần lớn cổng heuristic (HSI-V-sc5) — đăng ký trước (2026-11-03 19:45 UTC)

*Viết TRƯỚC khi xem bất kỳ kết quả nào của tập xác nhận mới (đợt `hsi10` đang chạy) và của Entry 6.*
**Chẩn đoán (tập thiết kế, HSI-V):** frame đúng bị bỏ lỡ = 0.138 frame on-map, trong đó **nhất quán ngắn hạn (cổng sc 5/10/20 m) chiếm 0.089**,
khởi động lạnh 0.021, sàn MAP 0.013, ngưỡng conformal chỉ 0.010 (ở 3/4 run kiểm tra, θ = −∞: < α đoạn null có frame được phép báo). Cổng sc được
đặt ở Entry 1 vì hiệu chuẩn không đủ tin (ablation Entry 1: bỏ sc ⇒ 13/413 run vi phạm với null cũ). Với null sạch của Entry 5 (cầu neo bằng chứng
chỉ), hiệu chuẩn có thể gánh phần an toàn đó. NCLT: frame đúng trượt sc nằm ngay sau lúc chuỗi bắt lại đúng chỗ (cửa sổ 20 m vắt qua cú nhảy).
**Tập thiết kế (28 run; recall / chênh SH / thắng / sai số chênh SH / segFAR max):** HSI-V 0.719 / +0.069 / 24 / −0.01 / 0.044; **HSI-V-sc5 (chỉ độ trễ
5 m) 0.736 / +0.085 / 26 / −1.26 m / 0.044**; HSI-V-nosc (bỏ sc) 0.750 / +0.100 / 26 / −0.61 / 0.039 — nhưng Nordland MegaLoc sai số 0.6 → 22.4 (vài fix
sai xa); HSI-VM-nosc 0.736 / +0.086 / 24 / −0.90 / 0.031; HSI-VJd (sc tính từ lần nhảy cuối, chỉ khi khớp DR của tham chiếu) 0.725 / +0.074 / 24 / −0.11.
**Đăng ký trước.** Luật ứng viên chính **HSI-V-sc5**; phụ **HSI-V-nosc**; ablation HSI-VJd, HSI-VM-nosc. Cùng 413 run giữ ra + lỗ 10 % / 50 % + tự nhiên;
H1–H5 như §1.3; **H12:** recall gộp ≥ HSI-rot-m-sc + 0.02 VÀ sai số điều hướng gộp ≤ HSI-rot-m-sc + 0.5 m; **H11** (lỗ / tự nhiên ≤ 10 % run > α mỗi
tập). **Quyết định:** H1 ∧ H2 ∧ H11 ∧ H12 cho HSI-V-sc5 ⇒ HSI-V-sc5 thay HSI-rot-m-sc làm luật khuyến nghị; nếu HSI-V-sc5 trượt mà HSI-V-nosc đạt
cả bốn ⇒ HSI-V-nosc. **Xác nhận (C4, tập mới seed 10–12, 108 run, cùng bố cục lỗ với C1–C3):** luật được chọn có ≤ 5 % run > 0.05 và recall gộp ≥
HSI-rot-m-sc + 0.01 trên tập mới; báo cáo dù thuận hay nghịch.

**Kết quả giữ ra Entry 6 (đợt `hsi11`, 441 + 216 + 36 run; nguồn cache đã kiểm; kéo về 2026-11-03 20:50, phân tích 2026-11-04 02:08 UTC).** Gộp 413
run (recall / segFAR TB / run > α / sai số): HSI-rot-m-sc 0.772 / 0.0026 / 0 / 15.0; HSI-V 0.786 / 0.0040 / 0 / 15.3; **HSI-V-sc5 0.794 / 0.0075 / 9 / 16.7**;
HSI-V-nosc 0.805 / 0.0077 / 9 / 17.5; HSI-VJd 0.789 / 0.0040 / 0 / 15.3; HSI-VM-nosc 0.794 / 0.0043 / 1 / **13.9**; SH 0.731 / 0.0029 / 2 / 15.6. HSI-V-sc5:
H1 đạt (9/413 = 2.2 % ≤ 10 %; TB dataset ≤ 0.012), H11 đạt (lỗ 10 % 2/108, 50 % 6/108, tự nhiên 3/36), **H12 không đạt** (recall +0.022 đạt nhưng
sai số +1.7 m > +0.5: old town 31.6 → 45.0 m, Boreas 6.9 → 8.9 m). HSI-V-nosc: H12 không đạt (+2.5 m), H11 không đạt (tự nhiên 5/36).
**Quyết định:** HSI-rot-m-sc vẫn là luật khuyến nghị. **Bài học:** tập thiết kế (28 run) không lộ cái giá điều hướng — cổng nhất quán ngắn hạn
chủ yếu chặn fix SAI XA trong bản đồ (ảnh hưởng điều hướng, không ảnh hưởng segFAR); bỏ cổng cần một cơ chế khác giữ an toàn điều hướng
(Mondrian theo chế độ làm được điều đó trên giữ ra: HSI-VM-nosc — kiểm ở Entry 7 trên dữ liệu mới).

## Entry 5 — chứng nhận rồi hiệu chuẩn: chứng chỉ hình học làm điểm neo hồi cứu (HSI-V) — đăng ký trước (2026-11-03 18:45 UTC)

*Viết TRƯỚC khi xem bất kỳ kết quả giữ ra nào của Entry 4 (đợt `hsi7` đang chạy) và của Entry 5.*
**Chẩn đoán (tập thiết kế seed 0; nhãn chỉ để chẩn đoán; `paper/hsi_theory.md` Mệnh đề 6):** frame đúng bị bỏ lỡ chủ yếu vì điểm (c) > 0.5 nhưng
dưới ngưỡng conformal (CMU 0.29, NCLT 0.16–0.18 frame on-map). Hiệu chuẩn với null oracle (off-map thật) nâng CMU NetVLAD 0.391 → 0.569 ⇒ null
hồi cứu bị nhiễm. Nguồn nhiễm: (i) NCLT chỉ 6–13 % frame được xác minh hồi cứu (độ chính xác 1.000) trong khi chứng chỉ hình học G = (a|b) phủ
28–42 % (độ chính xác ≥ 0.997) ⇒ cầu dead-reckoning dài, sai 30–180 m ⇒ 20 % frame null là fix đúng, và G báo ĐÚNG ở 52 % số đó; 18 % đoạn null
hiệu chuẩn có G báo > α ⇒ ngưỡng (c) = +∞; (ii) CMU 48 % frame thuộc chuỗi không có đoạn xác minh nào. Tỉ lệ G báo trong null ∩ off-map thật =
0.000 (Boreas, CMU, NCLT).
**Thay đổi (một tham số, `anchors="ver+geo"`):** điểm neo của cầu hồi cứu = đoạn xác minh hồi cứu ∪ frame có chứng chỉ G (nhân quả). Hệ quả:
cầu ngắn hơn, nhãn huấn luyện + null sạch hơn; G không còn trong null nên không bị tính vào α (bảo đảm thành ε_G + α, Mệnh đề 6).
**Tập thiết kế (28 run, recall TB / chênh với SH / thắng / sai số chênh / segFAR max):** HSI-rot-m-sc 0.702 / +0.051 / 21 / −0.31 m / 0.035;
**HSI-V 0.719 / +0.069 / 24 / −0.01 m / 0.044** (CMU 0.702 vs 0.659, NCLT 0.546 vs 0.481; CMU sai số 9.0 vs 7.0 m — thêm báo ở đầu chuỗi);
HSI-VM (+ Mondrian theo chế độ) 0.707 / +0.057 / 23 / −0.36 / 0.037 (Boreas sai số 7.1 → 3.9 m); HSI-Gdrop (G không tính vào α, cầu cũ) 0.714 /
+0.063 / 23 / −0.67 / 0.035; HSI-Vc (cầu ver ∪ G nhưng G bị phán xét bằng cầu cũ) giữ lợi ích CMU, mất lợi ích NCLT; leave-one-run-out kém hơn
mọi biến thể (chuỗi CMU ngắn không có đoạn neo lân cận).
**Đăng ký trước.** Luật ứng viên chính **HSI-V**; phụ **HSI-VM**; ablation HSI-Vc, HSI-Gdrop; chẩn đoán **geo-rm** (chỉ G, hình học rot-m) để đo
ε_G trực tiếp. Cùng tập giữ ra (413 run) + lỗ 10 % / 50 % (seed 0–2, 6 dataset × 6 descriptor) + off-map tự nhiên 4Seasons chéo cảnh (36 run),
cùng tham chiếu SH / CST-JS, cùng H1–H5 (§1.3). Thêm:
- **H9 (lợi ích):** recall gộp mọi run giữ ra của HSI-V ≥ HSI-rot-m-sc + 0.01, VÀ trên CMU và NCLT, mỗi dataset ≥ HSI-rot-m-sc + 0.03.
- **H10 (chứng chỉ):** geo-rm có segFAR > 0.05 trên ≤ 2 % run giữ ra (ε_G nhỏ là giả định của Mệnh đề 6).
- **H11 (bền):** HSI-V hợp lệ (H1) ở lỗ 10 %, 50 % và off-map tự nhiên (tỉ lệ run > 0.05 ≤ 10 % mỗi tập).
**Quyết định:** H1 ∧ H2 ∧ H9 ∧ H10 ⇒ HSI-V thay HSI-rot-m-sc làm luật khuyến nghị (HSI-VM thay nếu nó đạt H1 ∧ H2 ∧ H9 mà HSI-V trượt H1);
H10 trượt ⇒ giữ HSI-rot-m-sc (bảo đảm hợp), báo cáo HSI-V như điểm vận hành recall cao hơn với giả định chứng chỉ; H9 trượt ⇒ HSI-V là ablation.

**Bổ sung đăng ký trước — TẬP XÁC NHẬN MỚI (2026-11-03 19:10 UTC, trước mọi kết quả giữ ra của Entry 5).** Tập giữ ra 413 run đã được dùng
cho 5 vòng quyết định ⇒ nguy cơ quá khớp thích nghi. Tập mới chưa từng tồn tại: bố cục lỗ **seed 10–12** (sinh lại bằng `nav_demo --cache
--cache-only --seed0 10` từ dump descriptor công khai; mã tái tạo đúng từng bit cache công khai seed 0 — đã kiểm Nordland DINOv2), 6 dataset có
lỗ × 6 descriptor = **108 run**; không có SH (luật ý tưởng 1 cần GPU) ⇒ chỉ so các luật của ý tưởng 2 + tham chiếu trong cache (Xu'21, Claxton'24,
oracle). Đánh giá: HSI-rot-m-sc, HSI-M, HSI-V, HSI-VM, HSI-Gdrop, geo-rm. **Giả thuyết xác nhận:** **C1** luật được chọn bởi quyết định Entry 5
(HSI-V hoặc HSI-rot-m-sc) có ≤ 5 % run segFAR > 0.05 và segFAR TB ≤ 0.05 trên 6/6 dataset; **C2** recall gộp HSI-V − HSI-rot-m-sc ≥ +0.01 (dấu
của H9 lặp lại trên dữ liệu mới); **C3** geo-rm ≤ 2 % run > 0.05. Kết quả xác nhận được báo cáo dù thuận hay nghịch; nếu C2 trái dấu với H9
thì báo cáo lợi ích của HSI-V là không ổn định.

## Entry 4 — hiệu chuẩn Mondrian theo chế độ quyết định (HSI-M) — đăng ký trước (2026-11-03 18:05 UTC)

**Bối cảnh (từ kết quả giữ ra của Entry 3, chỉ CMU được dùng để chẩn đoán):** nới đầu chuỗi đưa các đoạn null đầu chuỗi (37/130 chuỗi CMU bắt đầu
off-map) vào cùng một ngân sách conformal ⇒ ngưỡng chung tăng, (c) báo ít hơn ở phần đang bám (frac_c trung vị 0.19 → 0.12), CMU giữ ra 0.692 →
0.652. **Thay đổi:** ngưỡng conformal riêng cho từng chế độ (k = 1: chuỗi chưa có tham chiếu tin cậy — đầu chuỗi / mất dấu; k = 0: đã có), mỗi
đoạn null cắt tại chỗ đổi chế độ; bảo đảm trở thành P(báo trong một đoạn null mới của chế độ k) ≤ α cho TỪNG k (Mệnh đề 4 áp riêng mỗi lớp) —
khớp với tinh thần kiểm toán theo vị trí (đầu chuỗi có ngưỡng riêng). Tập thiết kế: HSI-M +0.044 so với SH (20/28), sai số −0.9 m (20/28), max
segFAR 0.035; HSI-M-nos (không nới đầu chuỗi) +0.038.
**Đăng ký trước:** luật ứng viên **HSI-M**; phụ HSI-M-nos. Cùng tập giữ ra, tham chiếu, H1–H5. **H8:** recall CMU của HSI-M ≥ HSI-rot-m-sc + 0.03 VÀ
recall gộp mọi run giữ ra ≥ HSI-rot-m-sc − 0.005. **Quyết định:** H1 ∧ H2 ∧ H8 ⇒ HSI-M thay HSI-rot-m-sc; nếu không, giữ HSI-rot-m-sc và báo cáo
HSI-M như ablation (đổi recall lấy điều hướng / bảo đảm theo chế độ).

**Kết quả giữ ra Entry 4 (đợt `hsi7`, 441 run, 413 giữ ra; nguồn cache đã kiểm: 366 `hmm-navcache-v2` + 75 `hmm-e37-caches`; 2026-11-03 18:40 UTC).**
Recall / segFAR TB / run > α / sai số (TB theo run, gộp 413): HSI-rot-m-sc 0.772 / 0.0026 / 0 / 15.0 m; **HSI-M 0.764 / 0.0019 / 0 / 13.9 m**; HSI-M-nos
0.770 / 0.0026 / 0 / 13.9 m; SH 0.731 / 0.0029 / 2 / 15.6 m. CMU: HSI-M 0.654 (+0.002 so với HSI-rot-m-sc), HSI-M-nos 0.695 (+0.043). **H8 không đạt**
(CMU +0.002 < +0.03; gộp −0.008 < −0.005). H1 đạt (0/413), H2 đạt (≥ SH trên 7/9; gộp +0.033), H4 đạt (7/9; kém old town +2.8 m, NCLT +1.3 m).
Mondrian theo chế độ cải thiện điều hướng rõ (Boreas 6.9 → 4.4 m, old town 31.6 → 28.7, countryside 26.8 → 24.8) và giảm segFAR, đổi lại −0.008 recall.
**Quyết định (theo quy tắc đăng ký trước):** giữ HSI-rot-m-sc; HSI-M báo cáo như điểm vận hành ưu tiên điều hướng (bảo đảm theo chế độ). Quan sát
hậu nghiệm (không dùng để quyết định): HSI-M-nos đạt điều kiện số của H8 (CMU +0.043, gộp −0.002) với sai số 13.9 m.
Bền (mọi run, 3 seed × 36): lỗ 10 % — HSI-M 0/108 run > α, recall 0.747 (HSI-rot-m-sc 0.755, 0/108), sai số 11.2 vs 12.1 m; lỗ 50 % — 4/108 (cùng 4 run
CMU như HSI-rot-m-sc), recall 0.734 vs 0.744, sai số 19.5 vs 22.6 m (old town 56.7 → 40.6 m); off-map tự nhiên 4Seasons — 0/36 (HSI-rot-m-sc 1/36),
recall 0.742 vs 0.743.

## Entry 3 — đầu chuỗi và biên null (HSI-rot-m-sc) — đăng ký trước (2026-11-03 17:00 UTC, chưa xem kết quả giữ ra nào của Entry 1–2)

**Chẩn đoán trên tập thiết kế (seed 0) với HSI-rot-m:** (i) CMU: 97–100 % frame on-map bị bỏ lỡ (chuỗi đúng) nằm TRƯỚC điểm neo đầu tiên của
chuỗi, 72–82 % trong 50 frame đầu — chuỗi CMU ngắn (trung vị 186 frame), 37/130 chuỗi bắt đầu off-map; (c) không được báo ở đó vì đòi hỏi nhất
quán ngắn hạn 20 m; (ii) NCLT: ngưỡng hợp của (c) = +∞ vì null "có thể off-map" (biên 2σ với off_d chỉ 20 m) chứa nhiều frame thật ra ở vùng
giữa (in_d < d ≤ off_d) nơi hình học báo đúng ⇒ phần hình học chiếm > α đoạn null.
**Thay đổi:** (1) `start_relax`: trong max(độ trễ nhất quán ngắn) frame đầu của chuỗi, (c) được phép không cần nhất quán ngắn hạn (vẫn: sàn MAP
0.5, hiệu chuẩn biên chung); (2) `null_cap=0.25`: biên của null "có thể off-map" = min(2σ, off_d/4). Tập thiết kế: HSI-rot-m-sc +0.051 recall so
với SH (thắng 21/28), sai số −0.3 m (tốt hơn 19/28), segFAR TB 0.004 (max 0.035); CMU 0.659 vs SH 0.652.
**Đăng ký trước:** luật ứng viên **HSI-rot-m-sc**, cùng tập giữ ra / tham chiếu / H1–H5 như Entry 1; **H7:** HSI-rot-m-sc ≥ HSI-rot-m (Entry 2)
về recall TB trên ≥ 6/9 dataset mà không có dataset nào segFAR TB > 0.05. **Quyết định:** H1 ∧ H2 ∧ H7 ⇒ thay HSI-rot-m làm luật khuyến nghị.

**Kết quả giữ ra Entry 3 (đợt `hsi4`, 441 run, 413 giữ ra; 2026-11-03 17:50 UTC).** HSI-rot-m-sc: H1 **đạt** (0/413 run > 0.05; segFAR TB
dataset tối đa 0.006), H2 **đạt** (≥ SH trên 7/9 dataset; gộp +0.041), H3 **đạt** (DINOv2 + NetVLAD +0.096), H4 **đạt** (6/9), H5 **đạt** (9/9),
**H7 đạt** (≥ HSI-rot-m trên 8/9 dataset — CMU giảm: 0.652 vs 0.692). Recall HSI-rot-m-sc / SH: Boreas 0.892 / 0.777, office 0.872 / 0.803,
countryside 0.642 / 0.492, St Lucia 0.905 / 0.761, Oxford 0.764 / 0.719, old town 0.735 / 0.708, Nordland 0.785 / 0.770, CMU 0.652 / 0.835,
NCLT 0.577 / 0.690. Sai số điều hướng: tốt hơn SH ở countryside (−6.7 m), St Lucia (−6.7), Nordland (−1.0), office (−0.7), Oxford (−0.4), CMU
(−0.1); kém hơn ở old town (+5.7), Boreas (+2.5), NCLT (+1.9). **Quyết định (theo quy tắc đăng ký trước):** HSI-rot-m-sc là luật khuyến nghị của
ý tưởng 2; ghi rõ cái giá ở CMU (đầu chuỗi được nới làm tăng ngưỡng hiệu chuẩn chung) và sai số Boreas.

## Entry 2 — cửa sổ theo mét quãng đường + bù hướng có giới hạn (HSI-rot-m) — đăng ký trước (2026-11-03 16:40 UTC)

**Bối cảnh.** Viết TRƯỚC khi xem bất kỳ kết quả giữ ra nào của Entry 1 (đợt `hsi1` đang chạy). Hai lỗi đơn vị/giả định của cấu hình Entry 1 nhìn
thấy trên tập thiết kế (seed 0, 28 run): (i) mọi cửa sổ (độ trễ neo 10–80, span 20, W 40, P_over 80, khối hiệu chuẩn 300) tính bằng FRAME —
đúng ~1 m/frame nhưng Oxford / St Lucia có ~10 m/frame (cửa sổ 80 frame = 800 m > một lỗ 300 m); (ii) phép thử nhất quán giả định hướng
odometry đúng — sai với Segway NCLT (trôi 10–25°/phiên) và VIO 4Seasons.
**Thay đổi (một cấu hình chung):** mọi cửa sổ đổi sang mét quãng đường (giá trị cũ × 1 m, đổi ra frame bằng trung vị bước odometry của chính
lần chạy, không nhãn; không mịn hơn 1 m/frame) — `metric_windows=True`; phép thử nhất quán sau phép quay tốt nhất của cửa sổ, |góc| ≤ 20°
(`rot_max=0.35`). Tập thiết kế: HSI-rot-m +0.037 recall so với SH (thắng 17/28), segFAR TB 0.004 (max 0.037), sai số +0.6 m (tốt hơn 16/28);
HSI-m +0.026 (17/28), max 0.033.
**Đăng ký trước.** Luật ứng viên chính: **HSI-rot-m**; phụ: HSI-m. Cùng tập giữ ra, cùng tham chiếu, cùng H1–H5 như Entry 1 (§1.3). Thêm
**H6:** HSI-rot-m ≥ HSI (Entry 1) về recall TB trên ≥ 6/9 dataset, và Oxford + St Lucia (10 m/frame) mỗi dataset recall HSI-rot-m ≥ HSI + 0.05.
**Quyết định:** nếu H1 ∧ H2 đạt cho HSI-rot-m thì nó thay HSI làm luật khuyến nghị; nếu không, giữ quyết định của Entry 1.

**Kết quả giữ ra Entry 2 (đợt `hsi2`, 441 run, 413 run giữ ra có SH trên cùng run; nhãn chỉ để đánh giá; 2026-11-03 17:10 UTC).**
H1 **đạt** (segFAR TB ≤ 0.05 trên 9/9 dataset; 0/413 run > 0.05 — SH: 2); H2 **đạt** (HSI-rot-m ≥ SH trên 6/9 dataset; gộp +0.039);
H3 **đạt** (DINOv2 + NetVLAD: +0.089, 133 run); H4 **đạt** (sai số trong +1 m của SH trên 7/9); H5 **đạt** (mọi lớp vị trí ≤ 0.07 trên 9/9 — điều
ý tưởng 1 chưa đạt; lớp tệ nhất: St Lucia start 0.058 trên 120 đoạn). H6 chờ đợt `hsi1`.
Theo dataset (recall HSI-rot-m / SH, thắng / tổng): Boreas 0.889 / 0.777 (56/56), office 0.867 / 0.803 (54/56), countryside 0.638 / 0.492
(56/56; sai số −6.1 m), St Lucia 0.904 / 0.761 (30/30; −6.7 m), Oxford 0.758 / 0.719 (33/45), old town 0.710 / 0.708 (29/56; sai số +4.6 m),
Nordland 0.769 / 0.770 (22/56), **CMU 0.692 / 0.835 (0/56)**, NCLT 0.577 / 0.690 (0/2). Theo descriptor: DINOv2 +0.116, NetVLAD +0.059, MixVPR
+0.027, CosPlace +0.023, SALAD +0.015, MegaLoc −0.007. Tham chiếu: Xu'21 (nhãn) recall 0.689 nhưng 202/413 run vượt α.
**Kết luận Entry 2:** HSI-rot-m là luật khuyến nghị (H1 ∧ H2); điểm yếu còn lại là đầu chuỗi ngắn (CMU) và NCLT — đúng mục tiêu của Entry 3
(đăng ký trước 17:00, đợt `hsi4` đang chạy).

## Entry 1 — HSI: tự giám sát hồi cứu bằng hình học (robot học khi nào tin "mắt" từ phán quyết hồi cứu của "chân") (2026-11-03)

### 1.1 Chẩn đoán dẫn tới ý tưởng (nhãn chỉ dùng để chẩn đoán; tập thiết kế = seed 0 của 7 dataset × 4 descriptor CosPlace/NetVLAD/MegaLoc/DINOv2 = 28 run)

- **D1 — mất recall nằm ở quyết định báo, không ở bộ lọc vị trí.** Chuỗi vị trí (MAP, `est_c`) đúng ở 54–99.8 % frame on-map; luật tốt nhất của ý
  tưởng 1 (SH = CMS-CPC/H+SH+G+NGRr) báo 14–96 %. Ví dụ CMU CosPlace: chuỗi đúng 0.981, SH 0.814.
- **D2 — thông tin có sẵn, thiếu cách học không nhãn.** Một bộ phân loại có giám sát (GBM trên đặc trưng nhân quả: thống kê ngoại hình, dư
  chuỗi–odometry ở nhiều độ trễ; huấn luyện trên nửa điều kiện, thử trên nửa kia, ngưỡng oracle) đạt recall ở segFAR ≤ 0.05 cao hơn SH
  +0.12…+0.31 (7 run thử). Thống kê bất biến affine của ý tưởng 1 làm mất thông tin: AUROC on/off của p SelfCal 0.65 so với s1−mean 0.95
  (countryside CosPlace).
- **D3 — tự nhất quán hình học là chứng chỉ gần tuyệt đối và không phụ thuộc điều kiện ảnh.** "Điểm neo" = độ dời của chuỗi vị trí khớp
  odometry ở mọi độ trễ 10/20/40/80 frame (không có ngưỡng ngoại hình nào): P(chuỗi đúng | neo) ≥ 0.993 trên 28/28 run, kể cả DINOv2/NetVLAD.
  Luật chỉ báo ở điểm neo đã đạt recall cao hơn SH ở Boreas DINOv2 (0.71 vs 0.55) — nhưng chậm (cửa sổ 80 frame).
- **D4 — nhãn hồi cứu tự sinh.** Giữa hai đoạn chuỗi đã xác minh, odometry (khớp cứng hai phía) cho vị trí hồi cứu của mọi frame ⇒ nhãn
  "fix đúng / sai / off-map" theo vùng phủ đã biết của bản đồ: độ chính xác nhãn off-map 1.000 (Boreas, office, countryside, Nordland, CMU),
  0.88–0.93 (old town, NCLT: odometry trôi); nhãn "fix đúng" ≥ 0.99 mọi nơi.
- **D5 — sai số điều hướng do vài fix sai rất xa (> 100 m)**, kể cả từ neo trên một tuyến SAI nhất quán (aliasing có cấu trúc): bỏ 458/40 727 fix
  đó thì sai số Boreas DINOv2 26.3 → 3.7 m ⇒ các tham chiếu phải nhất quán lẫn nhau qua dead-reckoning.

### 1.2 Phương pháp HSI (`analysis/hsi.py`, `online_v2`; cấu hình đóng băng `analysis/hsi_eval.py` VARIANTS["HSI"])

Một cấu hình cho mọi dataset/descriptor; hằng số theo đơn vị giao thức (excl, off_d, H) hoặc frame; không nhãn, không can thiệp bản đồ.

- **(a) Điểm neo tin cậy:** neo nhân quả (khớp độ dời ở mọi độ trễ {10,20,40,80}, dung sai 0.4·excl·(1+k/40)); neo trở thành THAM CHIẾU (phép
  biến đổi cứng odometry→bản đồ, Kabsch trên 40 frame cuối) nếu khớp dead-reckoning của tham chiếu trước (dung sai + 2κ·quãng đường), hoặc sau
  80 frame neo liên tục khi mâu thuẫn (tham chiếu cũ sai). κ cập nhật không nhãn từ các lần khớp.
- **(b) Đồng thuận dead-reckoning:** báo nếu |fix − x_DR| + 2σ ≤ excl và d(x_DR, bản đồ) + 2σ ≤ off_d (σ = s0 + κ·quãng từ tham chiếu).
- **(c) Điểm số học hồi cứu:** GBM (`HistGradientBoosting`) dự đoán nhãn hồi cứu từ ~33 đặc trưng nhân quả (ngoại hình tuyệt đối/tương đối,
  dư chuỗi–odometry ở 6 độ trễ, dead-reckoning từ neo/tham chiếu); học lại khi nhãn tăng 10 %, theo thứ tự triển khai (phiên theo ngày rồi
  chuỗi); nhãn chỉ dùng khi đã "chốt" (`avail`). (c) chỉ báo khi chuỗi nhất quán ngắn hạn (độ trễ 5/10/20), không mâu thuẫn xa với tham chiếu
  (|fix − x_DR| − 2σ ≤ off_d), P̂(đúng) > 0.5 và vượt ngưỡng conformal.
- **Hiệu chuẩn (biên, toàn luật):** đơn vị = đoạn H frame của tập null hồi cứu (có thể off-map ∪ fix chắc chắn sai ∪ chưa từng được xác
  minh) thuộc các khối 300 frame giữ ra (một nửa, ngẫu nhiên tất định), gộp mọi phiên đã qua; điểm đoạn = max trên frame của (+∞ nếu (a|b)
  báo, P̂ nếu (c) được phép, −∞ còn lại); ngưỡng = phân vị conformal (1−α), α = 0.05 ⇒ P(có báo trong một đoạn null mới) ≤ α dưới hoán
  đổi được giữa đoạn null hồi cứu và đoạn sai thật (nhãn đúng).

### 1.3 Đăng ký trước (viết và commit TRƯỚC khi chạy bất kỳ seed nào ngoài seed 0 của 28 run thiết kế)

**Tập giữ ra (chưa từng nhìn):** seed 1–9 của 6 dataset có lỗ × 6 descriptor (kể cả SALAD, MixVPR chưa xem lần nào); seed 0 của SALAD/MixVPR;
NCLT SALAD/MixVPR; Oxford RobotCar (seed 0–9 / 0–4, 6 descriptor); St Lucia (seed 0–4, 6 descriptor). Tham chiếu = SH và CST-JS của ý tưởng 1
trên cùng (dataset, descriptor, seed) (`analysis/results/baselines_idea1/` e37 + e38). α = 0.05, H = 10.

- **H1 (hợp lệ):** segFAR trung bình của HSI ≤ 0.05 trên 9/9 dataset; tỷ lệ run giữ ra có segFAR > 0.05 ≤ 10 %.
- **H2 (recall):** recall TB của HSI ≥ SH trên ≥ 5/9 dataset, và chênh lệch gộp mọi run giữ ra ≥ 0.
- **H3 (descriptor yếu):** trên các run DINOv2 + NetVLAD giữ ra, recall HSI − SH ≥ +0.05 (trung bình).
- **H4 (điều hướng):** sai số điều hướng TB của HSI trong +1 m của SH trên ≥ 5/9 dataset.
- **H5 (kiểm toán vị trí):** tỷ lệ báo của đoạn off-map thật ≤ 0.07 ở mọi lớp (start / edge / deep) có ≥ 50 đoạn trên ≥ 7/9 dataset.
- **Ablation (mỗi cái đổi một thành phần, báo cáo, không quyết định luật):** HSI-adapt (dung sai tự hiệu chuẩn chỉ nới), HSI-sess (hiệu chuẩn
  theo phiên), HSI-regime (hiệu chuẩn có điều kiện), HSI-nosc, HSI-nounl, HSI-nogate, HSI-rigid, HSI-nofloor, geo (chỉ (a|b)), anc (chỉ neo).
- **Quyết định:** H1 ∧ H2 ⇒ HSI là luật khuyến nghị của ý tưởng 2; nếu H1 đạt mà H2 không ⇒ báo cáo HSI như luật hợp lệ bổ trợ (thắng ở đâu,
  thua ở đâu) và quay lại thiết kế; nếu H1 không đạt ⇒ chẩn đoán vị trí/điều kiện vi phạm trước khi sửa.

**Bổ sung trước khi chạy đợt giữ ra (16:30 UTC, chưa có kết quả giữ ra nào):** thêm ứng viên phụ **HSI-rot** (= HSI + phép thử nhất quán sau
phép quay tốt nhất của cửa sổ, giới hạn |góc| ≤ 20°: chịu được lệch hướng của odometry thật như NCLT/VIO, vẫn loại tuyến cần quay lớn). Tập
thiết kế: +0.007 so với SH (thắng 14/28), segFAR TB 0.003 (max 0.037), NCLT +0.048 so với HSI. Báo cáo như ứng viên phụ (không thay luật chính
trong Entry 1); nếu nó hơn HSI trên tập giữ ra thì là ứng viên cho Entry 2 (cần xác nhận trên dữ liệu mới).

**Đã biết từ tập thiết kế (seed 0, 28 run; để đọc kết quả trung thực):** HSI recall TB +0.001 so với SH (thắng 15/28), segFAR TB 0.002 (max
0.033), sai số +0.9 m (tốt hơn 16/28); thắng Boreas (+0.107), countryside (+0.105), Nordland (+0.063); thua NCLT (−0.175), old town (−0.062),
CMU (−0.037). HSI-adapt: +0.025 recall (18/28) nhưng 1 run vượt α (CMU DINOv2 0.060).

**Kết quả giữ ra Entry 1 (đợt `hsi1`, 441 run × 12 biến thể; 413 giữ ra).** HSI (cấu hình đóng băng, cửa sổ theo frame): H1 **đạt** (1/413 run
> 0.05), **H2 không đạt** (≥ SH trên 3/9 dataset; gộp −0.069), **H3 không đạt** (−0.032), H4 đạt (5/9), H5 đạt (9/9). Thất bại tập trung ở đúng
hai dataset 10 m/frame (Oxford 0.285 vs SH 0.719; St Lucia 0.447 vs 0.761) — lý do đã được nêu và sửa trong Entry 2 (đăng ký trước kết quả này),
cộng old town (0.598 vs 0.708) và CMU (0.682 vs 0.835). **Ablation (giữ ra, TB theo dataset; recall / segFAR / số run > 0.05 / sai số):** HSI
0.626 / 0.0016 / 1 / 20.1; hiệu chuẩn có điều kiện (regime) 0.534 / 0.0002 / 0 — hiệu chuẩn biên chung mang lại +0.09 recall; theo phiên (sess)
0.582 / 0.0007 / 0 — gộp phiên +0.044; bỏ nhất quán ngắn (nosc) 0.640 / 0.0042 / **13** — cần cho tính hợp lệ; bỏ null chưa xác minh (nounl) 0.630 /
0.0025 / **7** — cần cho tính hợp lệ; dung sai tự hiệu chuẩn (adapt) 0.651 / 0.0043 / 7; bỏ sàn MAP 0.630 / 0.0032 / 1; bỏ cổng DR 0.631 /
0.0031 / 1; cầu cứng (rigid) 0.635 / 0.0018 / 0; chỉ hình học (geo) 0.564 / 0.0026 / 6; chỉ neo nhân quả (anc) 0.547 / 0.0147 / **40** (tham chiếu
tin cậy giảm vi phạm 40 → 6); cửa sổ theo mét (HSI-m) 0.746 / 0.0027 / 1; + bù hướng (HSI-rot-m) 0.756 / 0.0027 / 0. Tham chiếu: SH 0.728 / 0.0025 /
2 / 14.9; Xu'21 (nhãn) 0.689 / 0.190 / 202; oracle top-1 0.842. HSI-rot (ứng viên phụ, cửa sổ frame) 0.632 — bù hướng chỉ có ích khi đã sửa đơn vị.
**Kết luận Entry 1:** cấu hình frame bị bác trên tập giữ ra (H2, H3); các thành phần then chốt được xác nhận bằng ablation (hiệu chuẩn biên
chung, gộp phiên, nhất quán ngắn, null chưa xác minh, tham chiếu tin cậy).
