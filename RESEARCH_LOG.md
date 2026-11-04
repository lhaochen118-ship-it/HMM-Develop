# Research Log — ý tưởng 2 (branch `hmm-2nd-idea`)

*Nhật ký thí nghiệm của lời giải mới. Entry mới đặt trên cùng. Mỗi entry: bối cảnh, giả thuyết, đăng ký trước (commit trước khi xem kết quả),
thí nghiệm, kết quả (kể cả âm), kết luận. Nhật ký của ý tưởng 1 (Entry 0–39): `history/RESEARCH_LOG_idea1.md`; tóm tắt:
`handoff/07_IDEA1_SUMMARY.md`.*

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
