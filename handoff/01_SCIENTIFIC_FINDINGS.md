# 01 — Scientific Findings (ý tưởng 2: HSI, branch `hmm-2nd-idea`)

*Cập nhật 2026-11-04. Phạm vi: đóng góp, ý nghĩa khoa học, kết quả tích cực, kết quả tiêu cực / hạn chế, bằng chứng và điều kiện kiểm chứng.
Không chứa vận hành (→ `02`) hay kế hoạch (→ `03`). Nguồn đầy đủ: `RESEARCH_LOG.md` Entry 1–9; lý thuyết `paper/hsi_theory.md` Mệnh đề 1–7;
báo cáo `paper/BAO_CAO_HSI.pdf`. Phát hiện của ý tưởng 1 và của các hướng trước: `history/01_SCIENTIFIC_FINDINGS_idea1_and_idea2-early.md`,
tóm tắt `07_IDEA1_SUMMARY.md`.*

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
