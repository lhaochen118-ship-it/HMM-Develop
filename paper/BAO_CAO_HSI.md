# BÁO CÁO — Ý tưởng 2: HSI, tự giám sát hồi cứu bằng hình học cho định vị chuỗi trên bản đồ có lỗ

*Branch `hmm-2nd-idea`, 2026-11-03/04 (cập nhật 2026-11-04 06:20 UTC). Nhật ký: `RESEARCH_LOG.md` Entry 1–9 + hai tập mới; lý thuyết: `paper/hsi_theory.md`; novelty: `LITERATURE_GATE.md`
Gate 17; code: `analysis/hsi.py`, `analysis/hsi_eval.py`, `analysis/hsi_summary.py`; kết quả thô: `analysis/results/hsi/`.*

## 1. Tóm tắt

**Vấn đề.** Ý tưởng 1 hiệu chuẩn quyết định "báo / không báo fix" bằng null phản thực (phẫu thuật bản đồ). Chẩn đoán cho thấy: (i) phần mất
recall nằm ở quyết định báo, không ở bộ lọc vị trí; (ii) thông tin đủ để vượt xa ý tưởng 1 đã có sẵn trong các đặc trưng nhân quả (một bộ phân
loại có giám sát vượt +0.12…+0.31 recall) — cái thiếu là cách học và hiệu chuẩn **không nhãn**.

**Ý tưởng (HSI).** Hai giác quan độc lập kiểm chứng lẫn nhau: chuỗi vị trí (thị giác) đề xuất, odometry xác minh — một chứng chỉ không dùng
giá trị similarity nên không phụ thuộc điều kiện ảnh (P(fix đúng | xác minh) ≥ 0.993). Những gì đã xác minh, và các excursion off-map nằm giữa
chúng (định vị lại bằng dead-reckoning hai phía + vùng phủ đã biết của bản đồ), thành **nhãn hồi cứu tự sinh** để học online khi nào tin thị giác
sớm hơn, và để hiệu chuẩn ngưỡng báo bằng conformal trên các excursion THẬT của chính lần triển khai. Không nhãn, không can thiệp bản đồ, không GPU
(~1 ms/frame trên một lõi CPU, gồm cả học lại).

**Kết quả.** Chín vòng, mỗi vòng đăng ký trước khi xem kết quả; 413 run phát triển (9 dataset × 6 descriptor, so với ý tưởng 1 trên CÙNG run) +
lỗ 10 %/50 % + off-map tự nhiên + **ba tập mới sinh SAU các quyết định** (seed 10–12, 13–15, 16–18; 108 run mỗi tập).
**Luật khuyến nghị: HSI-VN** (Entry 8–9) = HSI + chứng chỉ hình học neo cầu hồi cứu (chứng nhận rồi hiệu chuẩn, Mệnh đề 6) + **căn chỉnh
Neyman–Pearson** (điểm học được huấn luyện chống lại chính null hiệu chuẩn, Mệnh đề 7). Trên 413 run phát triển: hợp lệ 413/413 (SH của ý tưởng 1:
411/413), kiểm toán theo vị trí ≤ 0.07 trên 9/9 dataset, recall **0.796 vs SH 0.731 (+0.065)**, DINOv2 + NetVLAD +0.118. Trên **hai tập kiểm tra
mới** (seed 13–18, 216 run chưa từng thấy) so với luật trước (HSI-rot-m-sc): **0/216 vi phạm**, recall **+0.015** (CI 95 % [+0.010, +0.020]), CMU
+0.055 (số run nhánh học bị khoá 18 → 9), điều hướng −0.53 m; các bộ giám sát có nhãn (Xu'21, Claxton'24) vượt α ở 41–75 % run. Quy tắc đăng ký
trước: seed 13–15 đạt 3/4 tiêu chí (trượt tiêu chí cơ chế), seed 16–18 đạt 4/4 ⇒ HSI-VN thay luật cũ. **Hiệu chuẩn:** quét α ∈ [0.01, 0.2] —
segFAR thực ≪ α, recall HSI-VN cao hơn luật cũ ở mọi α. **Bền:** lỗ 10 % 0/108, lỗ 50 % 4/108 (CMU, như luật cũ), off-map tự nhiên 0/36; chứng chỉ
một mình 0 vi phạm trên mọi tập. **Điều hướng:** HSI-VMN (thêm Mondrian theo chế độ) −2.6 m so với luật cũ với recall như cũ. **Điểm yếu:** CMU
(0.76 vs SH 0.835; phần khoá còn lại do chuỗi ngắn hoàn toàn đúng nhưng không thể chứng nhận — giới hạn thông tin), NCLT (2 run), sai số old town.

## 1b. English abstract (draft for a paper)

*Hindsight Self-supervised Integrity for sequence-based visual localization on maps with holes.* A robot localizing with a camera and odometry
against an image map must decide, frame by frame, whether to trust the place estimate of its sequence filter; reporting while the robot is off the
mapped area corrupts navigation. Prior integrity monitors either need labels from the deployment conditions or simulate the off-map case by editing
the map. We show that the robot can label its own past: chain-to-odometry geometric self-consistency certifies correct fixes independently of image
conditions, and dead-reckoning bridges between certified stretches, checked against the known coverage of the map, label every frame in hindsight —
including the off-map class, which is never labelled at deployment time. These labels train an appearance-based score online and calibrate its
threshold by split conformal prediction on the robot's own real excursions, bounding the per-segment false-report probability. Two structural
findings make the scheme work: (i) *certify-then-calibrate* — certified frames must anchor the hindsight bridges and must not be charged against the
false-alarm budget, otherwise long drifting bridges contaminate the calibration null; (ii) a *calibration lock-out cliff* — with saturated learned
scores, a segment-level conformal threshold jumps from −∞ to ≈1 as soon as more than α of the null segments contain one eligible frame, silencing
the learned branch for a whole deployment; training the score against the calibration null itself (Neyman–Pearson alignment) removes the cliff
(locked runs 27 → 1 of 60 on CMU). On 9 datasets × 6 descriptors (413 held-out runs, synthetic holes of 10/30/50 % and natural off-map) and on two
fresh test sets generated after every design decision was frozen (216 runs), the method is valid in all runs at α = 0.05, passes a
per-position audit that a map-surgery baseline fails, improves recall over it by +0.065, and the Neyman–Pearson alignment adds +0.015 recall
(95 % CI [+0.010, +0.020]) and −0.5 m navigation error on the fresh sets, at ~1 ms per frame on one CPU core.

## 2. Bài toán (giữ nguyên giao thức của ý tưởng 1)

Robot camera đơn + odometry đi trên bản đồ ảnh có lỗ (30 % ô 300 m bị xoá; NCLT off-map tự nhiên). Mỗi frame: báo hay không báo fix vị trí
(nơi MAP của chuỗi vị trí HMM dùng chung) cho bộ lọc điều hướng Kalman. Thước đo: recall (fix đúng trong excl / frame on-map), segFAR (tỷ lệ đoạn
off-map 10 frame có ≥ 1 báo, mục tiêu ≤ α = 0.05), sai số điều hướng TB, kiểm toán theo vị trí (start / edge / deep ≤ 0.07). Không dùng nhãn khi
triển khai. Baseline cần đánh bại: luật SH và CST-JS của ý tưởng 1 (phẫu thuật bản đồ phản thực), trên CÙNG (dataset, descriptor, seed).

## 3. Chẩn đoán dẫn tới ý tưởng (tập thiết kế: seed 0, 7 dataset × 4 descriptor)

| Phát hiện | Số liệu |
|---|---|
| Mất recall nằm ở quyết định báo, không ở bộ lọc vị trí | chuỗi vị trí đúng 54–99.8 % frame on-map; SH báo 14–96 % (CMU CosPlace: 0.981 vs 0.814) |
| Thông tin có sẵn: một GBM có giám sát trên đặc trưng nhân quả vượt SH | +0.12…+0.31 recall ở segFAR ≤ 0.05 (7 run) |
| Thống kê bất biến affine (ý tưởng 1) bỏ thông tin | AUROC on/off: p SelfCal 0.65 vs s1 − mean 0.95 (countryside CosPlace) |
| Tự nhất quán hình học (chuỗi vị trí ↔ odometry, độ trễ 10–80) là chứng chỉ gần tuyệt đối, không phụ thuộc điều kiện ảnh | P(fix đúng \| neo) ≥ 0.993 trên 28/28 run |
| Nhãn hồi cứu từ cầu odometry giữa hai đoạn đã xác minh | nhãn off-map chính xác 1.000 (Boreas, office, countryside, Nordland), 0.88–0.93 (old town, NCLT); nhãn fix đúng ≥ 0.99 |
| Sai số điều hướng do vài fix sai rất xa (> 100 m), kể cả neo trên tuyến sai nhất quán | Boreas DINOv2: bỏ 458/40 727 fix đó, sai số 26.3 → 3.7 m |

## 4. Phương pháp HSI

Ý tưởng cốt lõi: **hai giác quan độc lập kiểm chứng lẫn nhau, và phán quyết hồi cứu của sự kiểm chứng đó dạy robot khi nào tin giác quan nhanh
hơn.** Thị giác (chuỗi vị trí HMM) đề xuất; proprioception (odometry) xác minh — không cần giá trị similarity nào, nên chứng chỉ giữ nguyên ý
nghĩa dưới mọi điều kiện ảnh. Những gì đã được xác minh (và các excursion off-map nằm giữa các đoạn đã xác minh, định vị lại bằng dead
reckoning hai phía) trở thành nhãn tự sinh để học và hiệu chuẩn quyết định nhanh dựa trên ngoại hình.

1. **(a) Điểm neo tin cậy** — chuỗi vị trí khớp odometry ở mọi độ trễ (10/20/40/80 m); tham chiếu = phép biến đổi cứng odometry→bản đồ; neo
   mới chỉ được tin nếu khớp dead-reckoning của tham chiếu trước (loại tuyến dịch cứng — aliasing có cấu trúc) hoặc sau 80 m neo liên tục.
2. **(b) Đồng thuận dead-reckoning** — báo khi fix và vị trí dead-reckoning cùng nằm trong vùng phủ của bản đồ (biên 2σ, σ tăng theo quãng đường,
   tốc độ trôi ước lượng không nhãn từ các lần khớp).
3. **(c) Điểm số học hồi cứu** — GBM dự đoán nhãn hồi cứu "fix đúng" từ ~33 đặc trưng nhân quả; học lại theo thứ tự triển khai, chỉ dùng nhãn
   đã chốt; báo khi chuỗi nhất quán ngắn hạn, không mâu thuẫn xa với tham chiếu, P̂ > 0.5 và vượt ngưỡng conformal.
4. **Hiệu chuẩn biên của cả luật** — phân vị conformal (1 − α) trên các đoạn null hồi cứu giữ ra (có thể off-map ∪ fix chắc chắn sai ∪ chưa từng
   được xác minh) của các excursion THẬT, với điểm đoạn = +∞ nếu (a|b) báo, P̂ nếu (c) được phép, −∞ còn lại (Mệnh đề 4).
5. **Entry 2:** cửa sổ theo mét quãng đường (Oxford / St Lucia có ~10 m/frame) và bù hướng odometry có giới hạn (|góc| ≤ 20°).
6. **Entry 3:** đầu chuỗi được nới (nhất quán ngắn hạn chưa xác định ở đó) và biên null "có thể off-map" ≤ off_d/4.
7. **Entry 4 (ablation):** ngưỡng conformal riêng theo chế độ (đã / chưa có tham chiếu tin cậy) — Mondrian.
8. **Entry 5 — chứng nhận rồi hiệu chuẩn:** frame có chứng chỉ hình học (a|b) cũng là điểm neo của cầu hồi cứu. Chẩn đoán: NCLT chỉ 6–13 % frame
   được xác minh hồi cứu nhưng chứng chỉ phủ 28–42 % (độ chính xác ≥ 0.997) ⇒ cầu dài trôi 30–180 m ⇒ 20 % frame null thật ra là fix đúng, và
   chứng chỉ báo đúng ở một nửa số đó; hiệu chuẩn hợp tính các báo đúng ấy là vi phạm (18 % đoạn null > α ⇒ (c) bị khoá). Tỉ lệ chứng chỉ báo
   trong null ∩ off-map thật = 0.000. Bảo đảm trở thành ε_G + α (Mệnh đề 6), ε_G đo trực tiếp bằng biến thể chỉ-hình-học.

Lý thuyết (Mệnh đề 1–6, `paper/hsi_theory.md`): neo chứng nhận sai số hằng trên cửa sổ; tham chiếu tin cậy loại tuyến dịch cứng; sai số vị trí
hồi cứu theo cầu Brown; hiệu chuẩn biên cho P(báo trong một đoạn null mới) ≤ α dưới hoán đổi; sàn MAP chặn ngưỡng suy biến; chứng nhận rồi
hiệu chuẩn: P(báo trong đoạn off-map) ≤ ε_G + α khi chứng chỉ neo cầu hồi cứu.

## 5. Kết quả trên tập giữ ra

Tập giữ ra = mọi run ngoài tập thiết kế (seed 0 × 7 dataset × 4 descriptor): seed 1–9, SALAD/MixVPR, Oxford, St Lucia — 413 run có SH của ý tưởng
1 trên cùng (dataset, descriptor, seed). Ba vòng, mỗi vòng đăng ký trước khi xem bất kỳ kết quả giữ ra nào (`RESEARCH_LOG.md`):

| Vòng | Luật | H1 hợp lệ | H2 recall ≥ SH | H3 descriptor yếu | H4 điều hướng | H5 vị trí | Kết luận |
|---|---|---|---|---|---|---|---|
| Entry 1 | HSI (cửa sổ theo frame) | đạt (1/413 > α) | **không** (3/9; −0.069) | **không** (−0.032) | đạt (5/9) | đạt (9/9) | bác: Oxford/St Lucia (10 m/frame) sụp |
| Entry 2 | HSI-rot-m (cửa sổ theo mét + bù hướng) | đạt (0/413) | đạt (6/9; +0.039) | đạt (+0.089) | đạt (7/9) | đạt (9/9) | luật khuyến nghị (vòng 2) |
| Entry 3 | HSI-rot-m-sc (+ đầu chuỗi, biên null) | đạt (0/413) | đạt (7/9; +0.041) | đạt (+0.096) | đạt (6/9) | đạt (9/9) | **luật khuyến nghị** (H7: ≥ Entry 2 trên 8/9) |
| Entry 4 | HSI-M (Mondrian theo chế độ) | đạt (0/413) | đạt (7/9; +0.033) | – | đạt (7/9) | đạt (9/9) | ablation (H8 trượt: CMU +0.002); sai số −1.1 m |
| Entry 5 | HSI-V (chứng nhận rồi hiệu chuẩn) | đạt (0/413) | đạt (7/9; +0.054) | đạt (+0.110) | đạt (7/9) | đạt (9/9) | ablation (H9 trượt ở CMU +0.024 < 0.03; H10, H11 đạt) |
| Entry 6 | HSI-V-sc5 (cổng nhất quán chỉ 5 m) | đạt (9/413 > α) | đạt (+0.063) | – | – | – | ablation (H12 trượt: điều hướng +1.7 m) |
| Entry 7 | HSI-VM-nosc (quyết định trên tập mới) | đạt (0/108) | – | – | đạt (−0.7 m) | – | ablation (E2: +0.008 < 0.01) |
| Entry 8 | HSI-VN (căn chỉnh Neyman–Pearson), kiểm tra seed 13–15 | đạt (0/108) | đạt (+0.016) | – | đạt (−0.58 m) | – | trội Pareto; trượt T3 cơ chế (khoá 7 → 4) |
| Entry 9 | nhân bản Entry 8 trên seed 16–18 | đạt (0/108) | đạt (+0.014) | – | đạt (−0.49 m) | – | **đạt 4/4 (T3: khoá 11 → 5) ⇒ HSI-VN là luật khuyến nghị** |

**Ablation (giữ ra; recall / segFAR / số run > α / sai số điều hướng TB):** hiệu chuẩn biên chung thay vì có điều kiện +0.09 recall; gộp phiên thay
vì theo phiên +0.044; bỏ nhất quán ngắn hạn → 13 run vi phạm; bỏ null "chưa từng xác minh" → 7 run vi phạm; chỉ neo nhân quả → 40 run vi phạm,
thêm tham chiếu tin cậy (chỉ hình học) → 6; cửa sổ theo mét +0.12 (Oxford, St Lucia); bù hướng +0.01. Bảng đầy đủ ở Bảng A.

**Độ bền (giữ ra, so với SH trên cùng run — tập con không thuộc tập thiết kế).** Lỗ 10 %: HSI-rot-m-sc 0/84 run vượt α, recall ≥ SH trên 5/6
dataset (gộp +0.005; CMU 0.539 vs 0.845); lỗ 50 %: 4/84 (SH 3/84), ≥ SH trên 4/6 (gộp +0.048; Nordland −0.10), sai số old town +20.6 m. Trên MỌI run
(108 mỗi tỷ lệ lỗ, kể cả seed 0) xem §5.2: lỗ 10 % 0/108, lỗ 50 % 4/108 — đều ở CMU (HSI-V 5/108). Off-map tự nhiên (4Seasons, cảnh B hoàn toàn
ngoài bản đồ, ảnh + VIO thật, 36 run): recall cảnh A 0.743, segFAR 0.010 (1/36 run 0.053); HSI-M / HSI-V / HSI-VM 0/36; Xu'21 (nhãn) 0.581 với
10/36 run vượt α. Chi phí: 10–90 s mỗi run (Boreas 74 k frame) trên một lõi CPU ⇒ ~1 ms/frame cho cả đặc trưng, học lại GBM và đánh giá; ý tưởng
1 cần 18–45 ms/frame trên GPU cho mô phỏng tiến.

### 5.1 So sánh các biến thể (413 run giữ ra; recall / segFAR / số run > 0.05 / sai số điều hướng m)

| dataset | n | HSI-rot-m-sc rec / seg / >α / err | HSI-V rec / seg / >α / err | HSI-VN rec / seg / >α / err | HSI-VMN rec / seg / >α / err | HSI-VM rec / seg / >α / err | geo-rm rec / seg / >α / err | SH rec / seg / >α / err |
|---|---|---|---|---|---|---|---|---|
| 4s:countryside | 56 | 0.642 / 0.0050 / 0 / 26.8 | 0.666 / 0.0084 / 0 / 27.3 | 0.665 / 0.0066 / 0 / 26.6 | 0.655 / 0.0019 / 0 / 23.5 | 0.656 / 0.0025 / 0 / 23.1 | 0.594 / 0.0004 / 0 / 28.3 | 0.492 / 0.0006 / 0 / 33.5 |
| 4s:office_loop | 56 | 0.872 / 0.0001 / 0 / 9.0 | 0.874 / 0.0003 / 0 / 8.9 | 0.873 / 0.0000 / 0 / 8.9 | 0.854 / 0.0000 / 0 / 8.9 | 0.855 / 0.0003 / 0 / 8.9 | 0.786 / 0.0000 / 0 / 9.7 | 0.803 / 0.0003 / 0 / 9.7 |
| 4s:old_town | 56 | 0.735 / 0.0008 / 0 / 31.6 | 0.733 / 0.0013 / 0 / 32.7 | 0.731 / 0.0014 / 0 / 32.5 | 0.720 / 0.0004 / 0 / 29.0 | 0.721 / 0.0004 / 0 / 29.0 | 0.624 / 0.0000 / 0 / 40.9 | 0.708 / 0.0057 / 1 / 25.9 |
| boreas | 56 | 0.892 / 0.0014 / 0 / 6.9 | 0.897 / 0.0014 / 0 / 7.1 | 0.896 / 0.0014 / 0 / 6.8 | 0.885 / 0.0002 / 0 / 3.9 | 0.886 / 0.0003 / 0 / 4.4 | 0.856 / 0.0000 / 0 / 3.3 | 0.777 / 0.0023 / 0 / 4.5 |
| cmu | 56 | 0.652 / 0.0060 / 0 / 3.8 | 0.676 / 0.0061 / 0 / 3.8 | 0.761 / 0.0043 / 0 / 3.6 | 0.753 / 0.0040 / 0 / 3.5 | 0.669 / 0.0057 / 0 / 3.7 | 0.452 / 0.0014 / 0 / 3.3 | 0.835 / 0.0092 / 1 / 3.9 |
| nclt | 2 | 0.577 / 0.0000 / 0 / 5.1 | 0.645 / 0.0000 / 0 / 3.2 | 0.645 / 0.0000 / 0 / 3.2 | 0.634 / 0.0000 / 0 / 3.2 | 0.629 / 0.0000 / 0 / 3.3 | 0.550 / 0.0000 / 0 / 5.2 | 0.690 / 0.0000 / 0 / 3.2 |
| nord | 56 | 0.785 / 0.0000 / 0 / 5.0 | 0.785 / 0.0001 / 0 / 5.6 | 0.786 / 0.0001 / 0 / 5.6 | 0.777 / 0.0000 / 0 / 5.0 | 0.777 / 0.0000 / 0 / 5.0 | 0.668 / 0.0000 / 0 / 6.0 | 0.770 / 0.0000 / 0 / 6.0 |
| oxford | 45 | 0.764 / 0.0059 / 0 / 21.4 | 0.807 / 0.0139 / 0 / 21.2 | 0.805 / 0.0089 / 0 / 21.1 | 0.799 / 0.0068 / 0 / 20.4 | 0.801 / 0.0115 / 0 / 20.3 | 0.722 / 0.0029 / 0 / 21.8 | 0.719 / 0.0039 / 0 / 21.9 |
| stlucia | 30 | 0.905 / 0.0018 / 0 / 18.8 | 0.916 / 0.0013 / 0 / 18.5 | 0.915 / 0.0013 / 0 / 18.5 | 0.912 / 0.0011 / 0 / 18.4 | 0.912 / 0.0011 / 0 / 18.4 | 0.870 / 0.0011 / 0 / 19.8 | 0.761 / 0.0006 / 0 / 25.5 |
| **pooled** | 413 | **0.772** / 0.0026 / 0 / 15.0 | **0.786** / 0.0040 / 0 / 15.3 | **0.796** / 0.0029 / 0 / 15.1 | **0.786** / 0.0017 / 0 / 13.6 | **0.775** / 0.0026 / 0 / 13.6 | **0.684** / 0.0007 / 0 / 16.2 | **0.731** / 0.0029 / 2 / 15.6 |


### 5.2 Độ bền: lỗ 10 %, lỗ 50 %, off-map tự nhiên (mọi run; sai số của 4Seasons chéo cảnh không có nghĩa — gốc toạ độ khác)

Lỗ 10 % (108 run):

| dataset | n | HSI-rot-m-sc rec / seg / >α / err | HSI-V rec / seg / >α / err | HSI-VN rec / seg / >α / err | HSI-VMN rec / seg / >α / err | HSI-VM rec / seg / >α / err | geo-rm rec / seg / >α / err |
|---|---|---|---|---|---|---|---|
| 4s:countryside | 18 | 0.672 / 0.0023 / 0 / 21.0 | 0.697 / 0.0009 / 0 / 18.3 | 0.696 / 0.0016 / 0 / 19.1 | 0.688 / 0.0016 / 0 / 19.1 | 0.689 / 0.0009 / 0 / 18.3 | 0.641 / 0.0000 / 0 / 23.4 |
| 4s:office_loop | 18 | 0.860 / 0.0000 / 0 / 6.8 | 0.867 / 0.0004 / 0 / 6.7 | 0.867 / 0.0000 / 0 / 6.7 | 0.852 / 0.0000 / 0 / 6.8 | 0.853 / 0.0004 / 0 / 6.7 | 0.807 / 0.0000 / 0 / 7.3 |
| 4s:old_town | 18 | 0.735 / 0.0005 / 0 / 32.1 | 0.731 / 0.0005 / 0 / 33.5 | 0.729 / 0.0000 / 0 / 32.4 | 0.714 / 0.0000 / 0 / 29.8 | 0.717 / 0.0000 / 0 / 31.6 | 0.674 / 0.0000 / 0 / 35.6 |
| boreas | 18 | 0.903 / 0.0006 / 0 / 6.0 | 0.913 / 0.0006 / 0 / 5.8 | 0.913 / 0.0006 / 0 / 6.2 | 0.903 / 0.0006 / 0 / 2.8 | 0.903 / 0.0006 / 0 / 2.7 | 0.888 / 0.0006 / 0 / 2.9 |
| cmu | 18 | 0.530 / 0.0007 / 0 / 2.9 | 0.542 / 0.0012 / 0 / 2.9 | 0.597 / 0.0000 / 0 / 2.8 | 0.592 / 0.0000 / 0 / 2.8 | 0.538 / 0.0012 / 0 / 2.9 | 0.469 / 0.0000 / 0 / 2.9 |
| nord | 18 | 0.831 / 0.0000 / 0 / 3.8 | 0.828 / 0.0000 / 0 / 3.8 | 0.829 / 0.0000 / 0 / 3.8 | 0.824 / 0.0000 / 0 / 3.8 | 0.823 / 0.0000 / 0 / 3.8 | 0.762 / 0.0000 / 0 / 4.4 |
| **pooled** | 108 | **0.755** / 0.0007 / 0 / 12.1 | **0.763** / 0.0006 / 0 / 11.8 | **0.772** / 0.0004 / 0 / 11.8 | **0.762** / 0.0004 / 0 / 10.8 | **0.754** / 0.0005 / 0 / 11.0 | **0.707** / 0.0001 / 0 / 12.7 |


Lỗ 50 % (108 run):

| dataset | n | HSI-rot-m-sc rec / seg / >α / err | HSI-V rec / seg / >α / err | HSI-VN rec / seg / >α / err | HSI-VMN rec / seg / >α / err | HSI-VM rec / seg / >α / err | geo-rm rec / seg / >α / err |
|---|---|---|---|---|---|---|---|
| 4s:countryside | 18 | 0.601 / 0.0044 / 0 / 37.9 | 0.610 / 0.0062 / 0 / 38.8 | 0.608 / 0.0049 / 0 / 35.6 | 0.598 / 0.0037 / 0 / 35.5 | 0.600 / 0.0038 / 0 / 36.4 | 0.523 / 0.0007 / 0 / 40.6 |
| 4s:office_loop | 18 | 0.862 / 0.0006 / 0 / 13.5 | 0.862 / 0.0012 / 0 / 13.6 | 0.860 / 0.0008 / 0 / 13.7 | 0.837 / 0.0008 / 0 / 13.7 | 0.839 / 0.0012 / 0 / 13.6 | 0.756 / 0.0002 / 0 / 14.3 |
| 4s:old_town | 18 | 0.719 / 0.0007 / 0 / 56.7 | 0.723 / 0.0019 / 0 / 62.8 | 0.720 / 0.0011 / 0 / 60.2 | 0.705 / 0.0004 / 0 / 41.1 | 0.707 / 0.0005 / 0 / 41.8 | 0.579 / 0.0000 / 0 / 62.5 |
| boreas | 18 | 0.883 / 0.0001 / 0 / 6.6 | 0.882 / 0.0000 / 0 / 5.2 | 0.881 / 0.0001 / 0 / 4.6 | 0.868 / 0.0001 / 0 / 4.6 | 0.869 / 0.0000 / 0 / 4.8 | 0.830 / 0.0000 / 0 / 4.1 |
| cmu | 18 | 0.733 / 0.0318 / 4 / 12.0 | 0.755 / 0.0362 / 5 / 13.2 | 0.770 / 0.0296 / 4 / 9.9 | 0.764 / 0.0284 / 3 / 9.7 | 0.750 / 0.0331 / 4 / 12.2 | 0.352 / 0.0066 / 0 / 5.9 |
| nord | 18 | 0.669 / 0.0000 / 0 / 8.8 | 0.682 / 0.0002 / 0 / 10.9 | 0.685 / 0.0001 / 0 / 8.9 | 0.678 / 0.0001 / 0 / 8.9 | 0.675 / 0.0001 / 0 / 8.9 | 0.532 / 0.0000 / 0 / 10.3 |
| **pooled** | 108 | **0.744** / 0.0063 / 4 / 22.6 | **0.752** / 0.0076 / 5 / 24.1 | **0.754** / 0.0061 / 4 / 22.2 | **0.742** / 0.0056 / 3 / 18.9 | **0.740** / 0.0065 / 4 / 19.6 | **0.595** / 0.0013 / 0 / 23.0 |


Off-map tự nhiên 4Seasons chéo cảnh (36 run):

| dataset | n | HSI-rot-m-sc rec / seg / >α / err | HSI-V rec / seg / >α / err | HSI-VN rec / seg / >α / err | HSI-VMN rec / seg / >α / err | HSI-VM rec / seg / >α / err | geo-rm rec / seg / >α / err |
|---|---|---|---|---|---|---|---|
| 4sx:countrysideoffice_loop | 6 | 0.683 / 0.0090 / 0 / 207477.5 | 0.679 / 0.0118 / 0 / 291190.2 | 0.680 / 0.0051 / 0 / 150900.8 | 0.678 / 0.0020 / 0 / 67952.1 | 0.677 / 0.0092 / 0 / 235086.3 | 0.656 / 0.0001 / 0 / 2834.2 |
| 4sx:countrysideold_town | 6 | 0.683 / 0.0070 / 0 / 193878.9 | 0.681 / 0.0177 / 0 / 370778.3 | 0.680 / 0.0092 / 0 / 231436.9 | 0.678 / 0.0023 / 0 / 73535.2 | 0.678 / 0.0142 / 0 / 287816.2 | 0.656 / 0.0002 / 0 / 9165.4 |
| 4sx:office_loopcountryside | 6 | 0.857 / 0.0039 / 0 / 219710.6 | 0.861 / 0.0037 / 0 / 215421.6 | 0.861 / 0.0015 / 0 / 103714.7 | 0.857 / 0.0008 / 0 / 44502.4 | 0.857 / 0.0028 / 0 / 171098.9 | 0.841 / 0.0000 / 0 / 95.8 |
| 4sx:office_loopold_town | 6 | 0.865 / 0.0166 / 1 / 213423.4 | 0.867 / 0.0119 / 0 / 176347.6 | 0.867 / 0.0017 / 0 / 36276.9 | 0.864 / 0.0002 / 0 / 5247.1 | 0.864 / 0.0101 / 0 / 150285.2 | 0.854 / 0.0000 / 0 / 43.2 |
| 4sx:old_towncountryside | 6 | 0.670 / 0.0043 / 0 / 250406.3 | 0.672 / 0.0048 / 0 / 269752.7 | 0.672 / 0.0015 / 0 / 98336.0 | 0.670 / 0.0005 / 0 / 39093.6 | 0.670 / 0.0037 / 0 / 219336.0 | 0.660 / 0.0000 / 0 / 115.1 |
| 4sx:old_townoffice_loop | 6 | 0.702 / 0.0175 / 0 / 312010.8 | 0.688 / 0.0174 / 0 / 327866.2 | 0.693 / 0.0034 / 0 / 86836.6 | 0.692 / 0.0029 / 0 / 88030.7 | 0.687 / 0.0168 / 0 / 330769.4 | 0.684 / 0.0000 / 0 / 33.4 |
| **pooled** | 36 | **0.743** / 0.0097 / 1 / 232817.9 | **0.741** / 0.0112 / 0 / 275226.1 | **0.742** / 0.0037 / 0 / 117917.0 | **0.740** / 0.0015 / 0 / 53060.2 | **0.739** / 0.0095 / 0 / 232398.7 | **0.725** / 0.0001 / 0 / 2047.8 |


### 5.3 Hiệu chuẩn: quét α (HSI-rot-m-sc ở α khác nhau; 413 run giữ ra)

![alpha](figures/hsi_alpha.png)

| rule | nominal α | runs | segFAR mean of dataset means | max dataset mean | runs > α | runs > 0.05 | pooled recall | nav err (m) |
|---|---|---|---|---|---|---|---|---|
| HSI-sc@0.01 | 0.01 | 413 | 0.0008 | 0.0030 | 6 (1.5%) | 0 | 0.707 | 16.5 |
| HSI-sc@0.02 | 0.02 | 413 | 0.0013 | 0.0035 | 4 (1.0%) | 0 | 0.733 | 15.9 |
| HSI-rot-m-sc | 0.05 | 413 | 0.0023 | 0.0060 | 0 (0.0%) | 0 | 0.772 | 15.0 |
| HSI-sc@0.1 | 0.1 | 413 | 0.0046 | 0.0143 | 0 (0.0%) | 4 | 0.799 | 15.0 |
| HSI-sc@0.2 | 0.2 | 413 | 0.0083 | 0.0437 | 0 (0.0%) | 27 | 0.811 | 16.0 |
| Claxton24 | 0.05 | 413 | 0.1699 | 0.2568 | 287 (69.5%) | 287 | 0.729 | 46.2 |
| Xu21 | 0.05 | 413 | 0.1903 | 0.5679 | 202 (48.9%) | 202 | 0.670 | 51.0 |
| oracle | 0.0 | 413 | 0.0000 | 0.0000 | 0 (0.0%) | 0 | 0.845 | 10.3 |


Bảo đảm đúng ở mọi mức và bảo thủ (null hồi cứu là tập cha của off-map). Claxton'24 (MLP giám sát có nhãn) và Xu'21 (HMM có trạng thái off-map,
chỉnh bằng nhãn) không có cơ chế hiệu chuẩn cho off-map nên vượt α ở 49–70 % run.

### 5.4 Tập xác nhận mới (bố cục lỗ seed 10–12, sinh lại sau khi mọi quyết định đã chốt; 108 run, mọi run)

Sinh bằng `analysis/hsi_fresh.py` (nav_demo `--cache-only` trên dump descriptor công khai; mã tái tạo đúng từng bit cache công khai seed 0; hai lần
sinh độc lập cho kết quả giống hệt). Không có SH (cần GPU). Đăng ký trước: C1 (luật được chọn hợp lệ) **đạt** 0/108; C3 (chứng chỉ) **đạt** 0/108;
C2 (HSI-V ≥ +0.01) **không đạt**: +0.0074, bootstrap 95 % [+0.0026, +0.0127]; Entry 7 (HSI-VM-nosc) E1, E3 đạt, E2 không đạt (+0.0080).

| dataset | n | HSI-rot-m-sc rec / seg / >α / err | HSI-V rec / seg / >α / err | HSI-VM rec / seg / >α / err | HSI-VM-nosc rec / seg / >α / err | geo-rm rec / seg / >α / err | Xu21 rec / seg / >α / err | Claxton24 rec / seg / >α / err | oracle rec / seg / >α / err |
|---|---|---|---|---|---|---|---|---|---|
| 4s:countryside | 18 | 0.655 / 0.0025 / 0 / 21.1 | 0.681 / 0.0007 / 0 / 19.9 | 0.672 / 0.0007 / 0 / 19.8 | 0.687 / 0.0035 / 0 / 19.7 | 0.613 / 0.0000 / 0 / 24.3 | 0.223 / 0.1318 / 7 / 78.4 | 0.619 / 0.3500 / 18 / 39.0 | 0.748 / 0.0000 / 0 / 13.8 |
| 4s:office_loop | 18 | 0.886 / 0.0004 / 0 / 8.1 | 0.887 / 0.0000 / 0 / 8.0 | 0.871 / 0.0000 / 0 / 8.1 | 0.893 / 0.0019 / 0 / 8.0 | 0.821 / 0.0000 / 0 / 8.7 | 0.696 / 0.1354 / 5 / 15.4 | 0.811 / 0.1512 / 9 / 17.7 | 0.912 / 0.0000 / 0 / 7.7 |
| 4s:old_town | 18 | 0.737 / 0.0016 / 0 / 37.7 | 0.725 / 0.0014 / 0 / 38.0 | 0.715 / 0.0010 / 0 / 34.3 | 0.713 / 0.0069 / 0 / 35.7 | 0.632 / 0.0000 / 0 / 47.5 | 0.657 / 0.3313 / 8 / 106.1 | 0.738 / 0.1619 / 10 / 95.3 | 0.853 / 0.0000 / 0 / 21.3 |
| boreas | 18 | 0.888 / 0.0009 / 0 / 7.1 | 0.891 / 0.0010 / 0 / 7.6 | 0.883 / 0.0003 / 0 / 5.5 | 0.893 / 0.0030 / 0 / 6.5 | 0.856 / 0.0000 / 0 / 4.5 | 0.723 / 0.2421 / 7 / 30.0 | 0.746 / 0.1403 / 10 / 28.0 | 0.871 / 0.0000 / 0 / 2.0 |
| cmu | 18 | 0.748 / 0.0120 / 0 / 4.5 | 0.762 / 0.0138 / 0 / 4.8 | 0.758 / 0.0134 / 0 / 4.8 | 0.717 / 0.0172 / 0 / 5.1 | 0.437 / 0.0005 / 0 / 3.1 | 0.622 / 0.0251 / 4 / 5.8 | 0.858 / 0.1262 / 10 / 14.5 | 0.945 / 0.0000 / 0 / 2.9 |
| nord | 18 | 0.792 / 0.0000 / 0 / 4.7 | 0.803 / 0.0000 / 0 / 4.6 | 0.791 / 0.0000 / 0 / 4.6 | 0.851 / 0.0011 / 0 / 4.3 | 0.690 / 0.0000 / 0 / 5.6 | 0.735 / 0.0322 / 2 / 53.8 | 0.524 / 0.2444 / 18 / 79.0 | 0.671 / 0.0000 / 0 / 4.9 |
| **pooled** | 108 | **0.784** / 0.0029 / 0 / 13.9 | **0.792** / 0.0028 / 0 / 13.8 | **0.782** / 0.0026 / 0 / 12.8 | **0.792** / 0.0056 / 0 / 13.2 | **0.675** / 0.0001 / 0 / 15.6 | **0.609** / 0.1497 / 33 / 48.3 | **0.716** / 0.1957 / 75 / 45.6 | **0.833** / 0.0000 / 0 / 8.8 |


### 5.5 Entry 8 — vách khoá hiệu chuẩn và căn chỉnh Neyman–Pearson (HSI-VN)

**Phát hiện.** Ở CMU, nhánh học tắt hẳn ở 27/60 run (HSI-rot-m-sc): ngưỡng conformal là phân vị của max điểm theo đoạn, điểm GBM bão hoà, nên
khi tỉ lệ đoạn null có một frame được phép báo vượt α thì ngưỡng nhảy từ −∞ lên ≈ 1 (Mệnh đề 7). Đoạn gây khoá là frame CHƯA TỪNG XÁC MINH (đầu
chuỗi bắt đầu trong lỗ, chuỗi ngắn) — thứ mô hình học trên nhãn có-nhãn chưa từng thấy là âm. **Sửa (một cờ):** học điểm (c) với âm = toàn bộ null
hồi cứu, trên đơn vị huấn luyện ⇒ điểm ước lượng tỉ số hợp lý so với chính phân phối null dùng để hiệu chuẩn; bảo đảm split conformal giữ nguyên.
Các hướng đã thử và loại (đều đo trước khi chạy lớn): đặc trưng hubness theo nơi, chứng chỉ cửa sổ ngắn "học từ chuỗi dài", chứng chỉ tự đồng
dạng của bản đồ, Mondrian theo trạng thái bằng chứng (`RESEARCH_LOG.md` Entry 8).

![lockout](figures/hsi_lockout.png)

*Hình: 60 run CMU phát triển. Trái — tỉ lệ frame do nhánh học báo; cụm < 0.1 là các run bị khoá (cam). Phải — recall từng run: căn chỉnh
Neyman–Pearson kéo cụm bị khoá lên mà không làm hại các run vốn không khoá.*

Phát triển (seed 0–9, tập con có SH):

| dataset | n | HSI-rot-m-sc rec / seg / >α / err | HSI-V rec / seg / >α / err | HSI-N rec / seg / >α / err | HSI-VN rec / seg / >α / err | HSI-VMN rec / seg / >α / err | SH rec / seg / >α / err |
|---|---|---|---|---|---|---|---|
| 4s:countryside | 56 | 0.642 / 0.0050 / 0 / 26.8 | 0.666 / 0.0084 / 0 / 27.3 | 0.642 / 0.0045 / 0 / 27.8 | 0.665 / 0.0066 / 0 / 26.6 | 0.655 / 0.0019 / 0 / 23.5 | 0.492 / 0.0006 / 0 / 33.5 |
| 4s:office_loop | 56 | 0.872 / 0.0001 / 0 / 9.0 | 0.874 / 0.0003 / 0 / 8.9 | 0.870 / 0.0000 / 0 / 9.0 | 0.873 / 0.0000 / 0 / 8.9 | 0.854 / 0.0000 / 0 / 8.9 | 0.803 / 0.0003 / 0 / 9.7 |
| 4s:old_town | 56 | 0.735 / 0.0008 / 0 / 31.6 | 0.733 / 0.0013 / 0 / 32.7 | 0.733 / 0.0009 / 0 / 33.2 | 0.731 / 0.0014 / 0 / 32.5 | 0.720 / 0.0004 / 0 / 29.0 | 0.708 / 0.0057 / 1 / 25.9 |
| boreas | 56 | 0.892 / 0.0014 / 0 / 6.9 | 0.897 / 0.0014 / 0 / 7.1 | 0.891 / 0.0013 / 0 / 6.6 | 0.896 / 0.0014 / 0 / 6.8 | 0.885 / 0.0002 / 0 / 3.9 | 0.777 / 0.0023 / 0 / 4.5 |
| cmu | 56 | 0.652 / 0.0060 / 0 / 3.8 | 0.676 / 0.0061 / 0 / 3.8 | 0.741 / 0.0039 / 0 / 3.6 | 0.761 / 0.0043 / 0 / 3.6 | 0.753 / 0.0040 / 0 / 3.5 | 0.835 / 0.0092 / 1 / 3.9 |
| nclt | 2 | 0.577 / 0.0000 / 0 / 5.1 | 0.645 / 0.0000 / 0 / 3.2 | 0.575 / 0.0000 / 0 / 5.1 | 0.645 / 0.0000 / 0 / 3.2 | 0.634 / 0.0000 / 0 / 3.2 | 0.690 / 0.0000 / 0 / 3.2 |
| nord | 56 | 0.785 / 0.0000 / 0 / 5.0 | 0.785 / 0.0001 / 0 / 5.6 | 0.786 / 0.0000 / 0 / 5.0 | 0.786 / 0.0001 / 0 / 5.6 | 0.777 / 0.0000 / 0 / 5.0 | 0.770 / 0.0000 / 0 / 6.0 |
| oxford | 45 | 0.764 / 0.0059 / 0 / 21.4 | 0.807 / 0.0139 / 0 / 21.2 | 0.767 / 0.0053 / 0 / 21.5 | 0.805 / 0.0089 / 0 / 21.1 | 0.799 / 0.0068 / 0 / 20.4 | 0.719 / 0.0039 / 0 / 21.9 |
| stlucia | 30 | 0.905 / 0.0018 / 0 / 18.8 | 0.916 / 0.0013 / 0 / 18.5 | 0.905 / 0.0013 / 0 / 18.7 | 0.915 / 0.0013 / 0 / 18.5 | 0.912 / 0.0011 / 0 / 18.4 | 0.761 / 0.0006 / 0 / 25.5 |
| **pooled** | 413 | **0.772** / 0.0026 / 0 / 15.0 | **0.786** / 0.0040 / 0 / 15.3 | **0.784** / 0.0021 / 0 / 15.3 | **0.796** / 0.0029 / 0 / 15.1 | **0.786** / 0.0017 / 0 / 13.6 | **0.731** / 0.0029 / 2 / 15.6 |


Quét α của HSI-VN (phát triển, 413 run): segFAR thực luôn ≪ α; ở mọi mức α HSI-VN có recall cao hơn HSI-rot-m-sc ở cùng α
(0.01: 0.727 vs 0.707; 0.02: 0.758 vs 0.733; 0.05: 0.796 vs 0.772; 0.1: 0.808 vs 0.799; 0.2: 0.812 vs 0.811) — tức căn chỉnh dịch cả đường
cong vận hành, không chỉ một điểm.

![alpha-vn](figures/hsi_alpha_vn.png)

Tập kiểm tra seed 13–15 (sinh sau đăng ký trước Entry 8; 108 run, không có SH):

| dataset | n | HSI-rot-m-sc rec / seg / >α / err | HSI-V rec / seg / >α / err | HSI-N rec / seg / >α / err | HSI-VN rec / seg / >α / err | HSI-VMN rec / seg / >α / err | geo-rm rec / seg / >α / err | Xu21 rec / seg / >α / err | Claxton24 rec / seg / >α / err | oracle rec / seg / >α / err |
|---|---|---|---|---|---|---|---|---|---|---|
| 4s:countryside | 18 | 0.608 / 0.0014 / 0 / 28.5 | 0.640 / 0.0020 / 0 / 26.8 | 0.610 / 0.0006 / 0 / 28.2 | 0.641 / 0.0031 / 0 / 27.3 | 0.630 / 0.0008 / 0 / 26.6 | 0.573 / 0.0000 / 0 / 30.5 | 0.257 / 0.0837 / 5 / 102.6 | 0.593 / 0.1787 / 16 / 49.9 | 0.728 / 0.0000 / 0 / 17.6 |
| 4s:office_loop | 18 | 0.871 / 0.0000 / 0 / 7.2 | 0.878 / 0.0000 / 0 / 7.1 | 0.870 / 0.0000 / 0 / 7.2 | 0.877 / 0.0000 / 0 / 7.1 | 0.860 / 0.0000 / 0 / 7.2 | 0.800 / 0.0000 / 0 / 7.7 | 0.705 / 0.0462 / 7 / 12.7 | 0.808 / 0.1988 / 12 / 19.5 | 0.910 / 0.0000 / 0 / 6.8 |
| 4s:old_town | 18 | 0.719 / 0.0007 / 0 / 46.4 | 0.708 / 0.0003 / 0 / 47.9 | 0.718 / 0.0007 / 0 / 44.5 | 0.713 / 0.0003 / 0 / 44.6 | 0.707 / 0.0003 / 0 / 36.5 | 0.648 / 0.0000 / 0 / 46.2 | 0.697 / 0.3736 / 9 / 110.5 | 0.749 / 0.1575 / 10 / 101.8 | 0.846 / 0.0000 / 0 / 22.9 |
| boreas | 18 | 0.883 / 0.0007 / 0 / 7.7 | 0.888 / 0.0007 / 0 / 7.6 | 0.882 / 0.0007 / 0 / 7.7 | 0.886 / 0.0007 / 0 / 7.5 | 0.875 / 0.0002 / 0 / 4.3 | 0.843 / 0.0002 / 0 / 3.6 | 0.702 / 0.1435 / 7 / 28.0 | 0.730 / 0.1439 / 7 / 33.0 | 0.871 / 0.0000 / 0 / 2.1 |
| cmu | 18 | 0.612 / 0.0047 / 0 / 3.4 | 0.598 / 0.0035 / 0 / 3.3 | 0.661 / 0.0029 / 0 / 3.3 | 0.671 / 0.0030 / 0 / 3.2 | 0.662 / 0.0028 / 0 / 3.2 | 0.479 / 0.0006 / 0 / 2.8 | 0.692 / 0.0985 / 7 / 12.4 | 0.899 / 0.2299 / 14 / 12.4 | 0.948 / 0.0000 / 0 / 2.6 |
| nord | 18 | 0.821 / 0.0000 / 0 / 5.0 | 0.820 / 0.0000 / 0 / 5.1 | 0.821 / 0.0000 / 0 / 5.0 | 0.821 / 0.0000 / 0 / 5.0 | 0.809 / 0.0000 / 0 / 5.0 | 0.713 / 0.0000 / 0 / 6.3 | 0.751 / 0.0537 / 9 / 78.4 | 0.526 / 0.2749 / 18 / 94.9 | 0.671 / 0.0000 / 0 / 5.4 |
| **pooled** | 108 | **0.752** / 0.0012 / 0 / 16.4 | **0.756** / 0.0011 / 0 / 16.3 | **0.760** / 0.0008 / 0 / 16.0 | **0.768** / 0.0012 / 0 / 15.8 | **0.757** / 0.0007 / 0 / 13.8 | **0.676** / 0.0001 / 0 / 16.2 | **0.634** / 0.1332 / 44 / 57.4 | **0.717** / 0.1973 / 77 / 51.9 | **0.829** / 0.0000 / 0 / 9.6 |


Tập kiểm tra seed 16–18 (Entry 9 — nhân bản đúng quy tắc của Entry 8, sinh sau đăng ký trước; 108 run):

| dataset | n | HSI-rot-m-sc rec / seg / >α / err | HSI-V rec / seg / >α / err | HSI-N rec / seg / >α / err | HSI-VN rec / seg / >α / err | HSI-VMN rec / seg / >α / err | geo-rm rec / seg / >α / err | Xu21 rec / seg / >α / err | Claxton24 rec / seg / >α / err | oracle rec / seg / >α / err |
|---|---|---|---|---|---|---|---|---|---|---|
| 4s:countryside | 18 | 0.658 / 0.0035 / 0 / 22.9 | 0.674 / 0.0050 / 0 / 22.2 | 0.659 / 0.0031 / 0 / 22.8 | 0.671 / 0.0059 / 0 / 22.5 | 0.661 / 0.0030 / 0 / 21.8 | 0.610 / 0.0000 / 0 / 25.3 | 0.247 / 0.1433 / 9 / 100.7 | 0.626 / 0.2966 / 18 / 42.5 | 0.761 / 0.0000 / 0 / 15.4 |
| 4s:office_loop | 18 | 0.853 / 0.0000 / 0 / 9.0 | 0.860 / 0.0006 / 0 / 8.8 | 0.851 / 0.0000 / 0 / 9.0 | 0.859 / 0.0000 / 0 / 8.9 | 0.836 / 0.0000 / 0 / 8.9 | 0.750 / 0.0000 / 0 / 9.9 | 0.721 / 0.2941 / 12 / 22.9 | 0.777 / 0.1543 / 12 / 19.7 | 0.906 / 0.0000 / 0 / 8.2 |
| 4s:old_town | 18 | 0.735 / 0.0021 / 0 / 41.2 | 0.734 / 0.0013 / 0 / 38.4 | 0.736 / 0.0008 / 0 / 36.8 | 0.728 / 0.0016 / 0 / 38.9 | 0.720 / 0.0005 / 0 / 28.9 | 0.636 / 0.0000 / 0 / 37.8 | 0.648 / 0.1941 / 9 / 74.6 | 0.734 / 0.1629 / 10 / 93.8 | 0.842 / 0.0000 / 0 / 19.0 |
| boreas | 18 | 0.876 / 0.0005 / 0 / 5.6 | 0.887 / 0.0008 / 0 / 5.6 | 0.875 / 0.0003 / 0 / 5.9 | 0.886 / 0.0006 / 0 / 5.5 | 0.874 / 0.0000 / 0 / 3.5 | 0.847 / 0.0000 / 0 / 3.4 | 0.661 / 0.1917 / 6 / 34.1 | 0.736 / 0.1290 / 8 / 29.5 | 0.872 / 0.0000 / 0 / 2.0 |
| cmu | 18 | 0.574 / 0.0026 / 0 / 2.9 | 0.589 / 0.0050 / 1 / 3.0 | 0.598 / 0.0000 / 0 / 2.8 | 0.624 / 0.0004 / 0 / 2.8 | 0.608 / 0.0004 / 0 / 2.9 | 0.442 / 0.0000 / 0 / 2.9 | 0.769 / 0.0854 / 6 / 7.8 | 0.868 / 0.2420 / 15 / 11.0 | 0.923 / 0.0000 / 0 / 2.6 |
| nord | 18 | 0.803 / 0.0001 / 0 / 5.4 | 0.812 / 0.0000 / 0 / 5.4 | 0.803 / 0.0001 / 0 / 5.4 | 0.813 / 0.0000 / 0 / 5.4 | 0.801 / 0.0000 / 0 / 5.4 | 0.679 / 0.0000 / 0 / 6.7 | 0.747 / 0.0377 / 7 / 59.2 | 0.520 / 0.2573 / 18 / 73.7 | 0.668 / 0.0000 / 0 / 5.9 |
| **pooled** | 108 | **0.750** / 0.0015 / 0 / 14.5 | **0.759** / 0.0021 / 1 / 13.9 | **0.754** / 0.0007 / 0 / 13.8 | **0.763** / 0.0014 / 0 / 14.0 | **0.750** / 0.0007 / 0 / 11.9 | **0.660** / 0.0000 / 0 / 14.3 | **0.632** / 0.1577 / 49 / 49.9 | **0.710** / 0.2070 / 81 / 45.0 | **0.829** / 0.0000 / 0 / 8.9 |


Gộp hai tập kiểm tra mới (seed 13–18, 216 run):

| dataset | n | HSI-rot-m-sc rec / seg / >α / err | HSI-VN rec / seg / >α / err | HSI-VMN rec / seg / >α / err | Xu21 rec / seg / >α / err | Claxton24 rec / seg / >α / err | oracle rec / seg / >α / err |
|---|---|---|---|---|---|---|---|
| 4s:countryside | 36 | 0.633 / 0.0024 / 0 / 25.7 | 0.656 / 0.0045 / 0 / 24.9 | 0.645 / 0.0019 / 0 / 24.2 | 0.252 / 0.1135 / 14 / 101.7 | 0.609 / 0.2376 / 34 / 46.2 | 0.744 / 0.0000 / 0 / 16.5 |
| 4s:office_loop | 36 | 0.862 / 0.0000 / 0 / 8.1 | 0.868 / 0.0000 / 0 / 8.0 | 0.848 / 0.0000 / 0 / 8.0 | 0.713 / 0.1702 / 19 / 17.8 | 0.793 / 0.1765 / 24 / 19.6 | 0.908 / 0.0000 / 0 / 7.5 |
| 4s:old_town | 36 | 0.727 / 0.0014 / 0 / 43.8 | 0.721 / 0.0010 / 0 / 41.8 | 0.713 / 0.0004 / 0 / 32.7 | 0.673 / 0.2839 / 18 / 92.5 | 0.742 / 0.1602 / 20 / 97.8 | 0.844 / 0.0000 / 0 / 21.0 |
| boreas | 36 | 0.879 / 0.0006 / 0 / 6.7 | 0.886 / 0.0007 / 0 / 6.5 | 0.875 / 0.0001 / 0 / 3.9 | 0.682 / 0.1676 / 13 / 31.0 | 0.733 / 0.1364 / 15 / 31.2 | 0.871 / 0.0000 / 0 / 2.1 |
| cmu | 36 | 0.593 / 0.0037 / 0 / 3.1 | 0.648 / 0.0017 / 0 / 3.0 | 0.635 / 0.0016 / 0 / 3.0 | 0.731 / 0.0919 / 13 / 10.1 | 0.884 / 0.2360 / 29 / 11.7 | 0.935 / 0.0000 / 0 / 2.6 |
| nord | 36 | 0.812 / 0.0001 / 0 / 5.2 | 0.817 / 0.0000 / 0 / 5.2 | 0.805 / 0.0000 / 0 / 5.2 | 0.749 / 0.0457 / 16 / 68.8 | 0.523 / 0.2661 / 36 / 84.3 | 0.670 / 0.0000 / 0 / 5.6 |
| **pooled** | 216 | **0.751** / 0.0014 / 0 / 15.4 | **0.766** / 0.0013 / 0 / 14.9 | **0.754** / 0.0007 / 0 / 12.8 | **0.633** / 0.1455 / 93 / 53.7 | **0.714** / 0.2021 / 158 / 48.5 | **0.829** / 0.0000 / 0 / 9.2 |


### Bảng A — luật khuyến nghị HSI-VN (Entry 8–9), seed 0–9 (phát triển, so với SH trên cùng run); Ablation: mọi biến thể

runs: 441 (held-out 413, with idea-1 SH on the same run 413)

## Held-out runs: mean recall / segFAR / navigation error per dataset

| dataset | n | HSI rec / seg / err | geo rec / seg / err | SH rec / seg / err | CST-JS rec / seg / err | oracle rec / seg / err | HSI−SH rec (wins) | HSI−SH err (better) |
|---|---|---|---|---|---|---|---|---|
| boreas | 56 | 0.896 / 0.001 / 6.8 | 0.832 / 0.001 / 5.9 | 0.777 / 0.002 / 4.5 | 0.781 / 0.011 / 8.5 | 0.882 / 0.000 / 2.1 | +0.119 (56/56) | +2.3 (31/56) |
| nclt | 2 | 0.645 / 0.000 / 3.2 | 0.565 / 0.000 / 3.9 | 0.690 / 0.000 / 3.2 | 0.711 / 0.002 / 3.4 | 0.784 / 0.000 / 2.2 | -0.045 (0/2) | +0.0 (1/2) |
| cmu | 56 | 0.761 / 0.004 / 3.6 | 0.450 / 0.005 / 3.6 | 0.835 / 0.009 / 3.9 | 0.816 / 0.019 / 3.8 | 0.945 / 0.000 / 2.9 | -0.074 (11/56) | -0.3 (42/56) |
| nord | 56 | 0.786 / 0.000 / 5.6 | 0.679 / 0.000 / 5.9 | 0.770 / 0.000 / 6.0 | 0.783 / 0.001 / 6.1 | 0.676 / 0.000 / 5.1 | +0.016 (22/56) | -0.4 (23/56) |
| 4s_office_loop | 56 | 0.873 / 0.000 / 8.9 | 0.697 / 0.001 / 11.6 | 0.803 / 0.000 / 9.7 | 0.815 / 0.008 / 9.7 | 0.914 / 0.000 / 8.3 | +0.071 (56/56) | -0.7 (51/56) |
| 4s_old_town | 56 | 0.731 / 0.001 / 32.5 | 0.594 / 0.003 / 47.2 | 0.708 / 0.006 / 25.9 | 0.715 / 0.012 / 39.6 | 0.844 / 0.000 / 19.3 | +0.023 (39/56) | +6.6 (22/56) |
| 4s_countryside | 56 | 0.665 / 0.007 / 26.6 | 0.595 / 0.011 / 27.8 | 0.492 / 0.001 / 33.5 | 0.503 / 0.005 / 32.9 | 0.739 / 0.000 / 16.0 | +0.172 (56/56) | -6.9 (48/56) |
| oxford | 45 | 0.805 / 0.009 / 21.1 | 0.338 / 0.002 / 35.3 | 0.719 / 0.004 / 21.9 | 0.729 / 0.021 / 22.0 | 0.899 / 0.000 / 15.9 | +0.086 (45/45) | -0.8 (36/45) |
| stlucia | 30 | 0.915 / 0.001 / 18.5 | 0.332 / 0.000 / 44.9 | 0.761 / 0.001 / 25.5 | 0.763 / 0.021 / 25.6 | 0.896 / 0.000 / 17.3 | +0.154 (30/30) | -7.0 (30/30) |

## Pre-registered hypotheses (Entry 1) on the held-out runs

- **H1 (validity):** mean segFAR <= 0.05 on 9/9 datasets; runs > 0.05: 0/413 (0.0%) -> **supported**
- **H2 (recall):** HSI >= SH on 7/9 datasets; pooled mean difference +0.0647 -> **supported**
- **H3 (weak descriptors):** DINOv2 + NetVLAD held-out runs: mean HSI − SH = +0.1184 over 133 runs -> **supported**
- **H4 (navigation):** mean error within +1 m of SH on 7/9 datasets -> **supported**
- **H5 (position audit):** every class <= 0.07 (classes with >= 50 segments) on 9/9 datasets -> **supported**
  - boreas: start 0.019 (n=4632), edge 0.001 (n=3954), deep 0.000 (n=86096)
  - nclt: start 0.000 (n=186), edge 0.000 (n=52), deep 0.000 (n=374)
  - cmu: start 0.005 (n=24472), edge 0.000 (n=0), deep 0.000 (n=0)
  - nord: start 0.004 (n=496), edge 0.000 (n=798), deep 0.000 (n=20102)
  - 4s_office_loop: start 0.000 (n=504), edge 0.000 (n=806), deep 0.000 (n=14580)
  - 4s_old_town: start 0.004 (n=1756), edge 0.007 (n=612), deep 0.000 (n=10238)
  - 4s_countryside: start 0.042 (n=1152), edge 0.004 (n=684), deep 0.005 (n=13560)
  - oxford: start 0.043 (n=2634), edge 0.008 (n=8799), deep 0.007 (n=34788)
  - stlucia: start 0.042 (n=120), edge 0.000 (n=1794), deep 0.000 (n=2556)

## Held-out, per descriptor (mean over datasets and seeds)

| descriptor | n | HSI rec | SH rec | HSI−SH | wins | HSI seg | HSI err | SH err |
|---|---|---|---|---|---|---|---|---|
| cosplace | 64 | 0.820 | 0.775 | +0.045 | 49 | 0.003 | 13.3 | 14.1 |
| netvlad | 64 | 0.635 | 0.548 | +0.087 | 54 | 0.003 | 25.5 | 21.6 |
| megaloc | 64 | 0.900 | 0.884 | +0.016 | 39 | 0.002 | 11.0 | 11.0 |
| dinov2 | 69 | 0.641 | 0.494 | +0.148 | 62 | 0.006 | 18.0 | 23.1 |
| salad | 76 | 0.890 | 0.845 | +0.045 | 55 | 0.002 | 11.7 | 12.0 |
| mixvpr | 76 | 0.870 | 0.822 | +0.048 | 56 | 0.002 | 11.9 | 12.3 |

## Ablations (held-out runs; mean over datasets of the per-dataset means)

| variant | recall | segFAR | runs seg>0.05 | nav err | worst-class rate |
|---|---|---|---|---|---|
| HSI | 0.786 | 0.0027 | 0 | 14.1 | 0.043 |
| Claxton24 | 0.737 | 0.1699 | 287 | 43.0 | 0.330 |
| HSI-Gdrop | 0.777 | 0.0033 | 0 | 14.0 | 0.058 |
| HSI-M | 0.751 | 0.0017 | 0 | 13.3 | 0.033 |
| HSI-M-nos | 0.755 | 0.0023 | 0 | 13.3 | 0.033 |
| HSI-N | 0.768 | 0.0019 | 0 | 14.5 | 0.042 |
| HSI-V | 0.778 | 0.0037 | 0 | 14.3 | 0.055 |
| HSI-V-nosc | 0.797 | 0.0071 | 9 | 16.1 | 0.123 |
| HSI-V-sc5 | 0.786 | 0.0070 | 9 | 15.4 | 0.104 |
| HSI-VJd | 0.781 | 0.0036 | 0 | 14.3 | 0.052 |
| HSI-VM | 0.767 | 0.0024 | 0 | 12.9 | 0.033 |
| HSI-VM-nosc | 0.783 | 0.0038 | 1 | 13.3 | 0.070 |
| HSI-VMN | 0.776 | 0.0016 | 0 | 12.9 | 0.033 |
| HSI-VN@0.01 | 0.719 | 0.0011 | 0 | 15.6 | 0.033 |
| HSI-VN@0.02 | 0.750 | 0.0014 | 0 | 14.7 | 0.033 |
| HSI-VN@0.1 | 0.797 | 0.0035 | 0 | 14.1 | 0.049 |
| HSI-VN@0.2 | 0.800 | 0.0046 | 3 | 14.3 | 0.050 |
| HSI-Vc | 0.759 | 0.0027 | 0 | 14.6 | 0.042 |
| HSI-adapt | 0.651 | 0.0043 | 7 | 18.8 | 0.045 |
| HSI-e1 | 0.626 | 0.0016 | 1 | 20.1 | 0.012 |
| HSI-m | 0.746 | 0.0027 | 1 | 14.6 | 0.067 |
| HSI-nofloor | 0.630 | 0.0032 | 1 | 20.1 | 0.023 |
| HSI-nogate | 0.631 | 0.0031 | 1 | 19.9 | 0.012 |
| HSI-nosc | 0.640 | 0.0042 | 13 | 20.9 | 0.127 |
| HSI-nounl | 0.630 | 0.0025 | 7 | 19.9 | 0.018 |
| HSI-regime | 0.534 | 0.0002 | 0 | 23.6 | 0.002 |
| HSI-rigid | 0.635 | 0.0018 | 0 | 19.6 | 0.018 |
| HSI-rot | 0.632 | 0.0017 | 1 | 19.7 | 0.013 |
| HSI-rot-m | 0.756 | 0.0027 | 0 | 14.0 | 0.058 |
| HSI-rot-m-c | 0.761 | 0.0028 | 0 | 13.7 | 0.058 |
| HSI-rot-m-s | 0.753 | 0.0022 | 0 | 14.5 | 0.058 |
| HSI-rot-m-sc | 0.758 | 0.0023 | 0 | 14.3 | 0.058 |
| HSI-sc@0.01 | 0.700 | 0.0008 | 0 | 15.6 | 0.033 |
| HSI-sc@0.02 | 0.722 | 0.0013 | 0 | 15.1 | 0.033 |
| HSI-sc@0.1 | 0.783 | 0.0046 | 4 | 14.2 | 0.071 |
| HSI-sc@0.2 | 0.799 | 0.0083 | 27 | 14.9 | 0.087 |
| HSI-sess | 0.582 | 0.0007 | 0 | 21.7 | 0.006 |
| Xu21 | 0.689 | 0.1903 | 202 | 47.5 | 0.710 |
| anc | 0.547 | 0.0147 | 40 | 22.2 | 0.175 |
| geo | 0.564 | 0.0026 | 6 | 20.7 | 0.039 |
| geo-rm | 0.680 | 0.0007 | 0 | 15.4 | 0.033 |
| oracle | 0.842 | 0.0000 | 0 | 9.9 | 0.000 |
| top1 | 0.842 | 1.0000 | 413 | 162.0 | 1.000 |
| (idea 1) SH | 0.728 | 0.0025 | 2 | 14.9 | – |


### Bảng B — cấu hình Entry 1 (cửa sổ theo frame), để đối chiếu

runs: 441 (held-out 413, with idea-1 SH on the same run 413)

## Held-out runs: mean recall / segFAR / navigation error per dataset

| dataset | n | HSI rec / seg / err | geo rec / seg / err | SH rec / seg / err | CST-JS rec / seg / err | oracle rec / seg / err | HSI−SH rec (wins) | HSI−SH err (better) |
|---|---|---|---|---|---|---|---|---|
| boreas | 56 | 0.884 / 0.001 / 4.9 | 0.832 / 0.001 / 5.9 | 0.777 / 0.002 / 4.5 | 0.781 / 0.011 / 8.5 | 0.882 / 0.000 / 2.1 | +0.108 (56/56) | +0.5 (37/56) |
| nclt | 2 | 0.504 / 0.000 / 7.4 | 0.565 / 0.000 / 3.9 | 0.690 / 0.000 / 3.2 | 0.711 / 0.002 / 3.4 | 0.784 / 0.000 / 2.2 | -0.186 (0/2) | +4.2 (0/2) |
| cmu | 56 | 0.682 / 0.010 / 4.2 | 0.450 / 0.005 / 3.6 | 0.835 / 0.009 / 3.9 | 0.816 / 0.019 / 3.8 | 0.945 / 0.000 / 2.9 | -0.152 (0/56) | +0.3 (33/56) |
| nord | 56 | 0.769 / 0.000 / 5.1 | 0.679 / 0.000 / 5.9 | 0.770 / 0.000 / 6.0 | 0.783 / 0.001 / 6.1 | 0.676 / 0.000 / 5.1 | -0.001 (22/56) | -0.9 (21/56) |
| 4s_office_loop | 56 | 0.824 / 0.000 / 9.4 | 0.697 / 0.001 / 11.6 | 0.803 / 0.000 / 9.7 | 0.815 / 0.008 / 9.7 | 0.914 / 0.000 / 8.3 | +0.022 (46/56) | -0.2 (40/56) |
| 4s_old_town | 56 | 0.598 / 0.000 / 46.0 | 0.594 / 0.003 / 47.2 | 0.708 / 0.006 / 25.9 | 0.715 / 0.012 / 39.6 | 0.844 / 0.000 / 19.3 | -0.110 (3/56) | +20.1 (3/56) |
| 4s_countryside | 56 | 0.639 / 0.003 / 28.4 | 0.595 / 0.011 / 27.8 | 0.492 / 0.001 / 33.5 | 0.503 / 0.005 / 32.9 | 0.739 / 0.000 / 16.0 | +0.147 (56/56) | -5.1 (48/56) |
| oxford | 45 | 0.285 / 0.000 / 37.5 | 0.338 / 0.002 / 35.3 | 0.719 / 0.004 / 21.9 | 0.729 / 0.021 / 22.0 | 0.899 / 0.000 / 15.9 | -0.434 (0/45) | +15.6 (0/45) |
| stlucia | 30 | 0.447 / 0.000 / 37.8 | 0.332 / 0.000 / 44.9 | 0.761 / 0.001 / 25.5 | 0.763 / 0.021 / 25.6 | 0.896 / 0.000 / 17.3 | -0.314 (0/30) | +12.3 (1/30) |

## Pre-registered hypotheses (Entry 1) on the held-out runs

- **H1 (validity):** mean segFAR <= 0.05 on 9/9 datasets; runs > 0.05: 1/413 (0.2%) -> **supported**
- **H2 (recall):** HSI >= SH on 3/9 datasets; pooled mean difference -0.0692 -> **NOT supported**
- **H3 (weak descriptors):** DINOv2 + NetVLAD held-out runs: mean HSI − SH = -0.0317 over 133 runs -> **NOT supported**
- **H4 (navigation):** mean error within +1 m of SH on 5/9 datasets -> **supported**
- **H5 (position audit):** every class <= 0.07 (classes with >= 50 segments) on 9/9 datasets -> **supported**
  - boreas: start 0.008 (n=4632), edge 0.000 (n=3954), deep 0.000 (n=86096)
  - nclt: start 0.000 (n=186), edge 0.000 (n=52), deep 0.000 (n=374)
  - cmu: start 0.012 (n=24472), edge 0.000 (n=0), deep 0.000 (n=0)
  - nord: start 0.000 (n=496), edge 0.000 (n=798), deep 0.000 (n=20102)
  - 4s_office_loop: start 0.004 (n=504), edge 0.000 (n=806), deep 0.000 (n=14580)
  - 4s_old_town: start 0.002 (n=1756), edge 0.000 (n=612), deep 0.000 (n=10238)
  - 4s_countryside: start 0.010 (n=1152), edge 0.003 (n=684), deep 0.002 (n=13560)
  - oxford: start 0.000 (n=2634), edge 0.000 (n=8799), deep 0.000 (n=34788)
  - stlucia: start 0.000 (n=120), edge 0.000 (n=1794), deep 0.000 (n=2556)

## Held-out, per descriptor (mean over datasets and seeds)

| descriptor | n | HSI rec | SH rec | HSI−SH | wins | HSI seg | HSI err | SH err |
|---|---|---|---|---|---|---|---|---|
| cosplace | 64 | 0.707 | 0.775 | -0.068 | 29 | 0.002 | 20.4 | 14.1 |
| netvlad | 64 | 0.491 | 0.548 | -0.058 | 34 | 0.001 | 27.6 | 21.6 |
| megaloc | 64 | 0.783 | 0.884 | -0.101 | 24 | 0.001 | 16.2 | 11.0 |
| dinov2 | 69 | 0.486 | 0.494 | -0.007 | 37 | 0.002 | 24.7 | 23.1 |
| salad | 76 | 0.753 | 0.845 | -0.092 | 28 | 0.003 | 16.9 | 12.0 |
| mixvpr | 76 | 0.736 | 0.822 | -0.086 | 31 | 0.002 | 16.2 | 12.3 |

## Ablations (held-out runs; mean over datasets of the per-dataset means)

| variant | recall | segFAR | runs seg>0.05 | nav err | worst-class rate |
|---|---|---|---|---|---|
| HSI | 0.626 | 0.0016 | 1 | 20.1 | 0.012 |
| Claxton24 | 0.737 | 0.1699 | 287 | 43.0 | 0.330 |
| HSI-Gdrop | 0.777 | 0.0033 | 0 | 14.0 | 0.058 |
| HSI-M | 0.751 | 0.0017 | 0 | 13.3 | 0.033 |
| HSI-M-nos | 0.755 | 0.0023 | 0 | 13.3 | 0.033 |
| HSI-N | 0.768 | 0.0019 | 0 | 14.5 | 0.042 |
| HSI-V | 0.778 | 0.0037 | 0 | 14.3 | 0.055 |
| HSI-V-nosc | 0.797 | 0.0071 | 9 | 16.1 | 0.123 |
| HSI-V-sc5 | 0.786 | 0.0070 | 9 | 15.4 | 0.104 |
| HSI-VJd | 0.781 | 0.0036 | 0 | 14.3 | 0.052 |
| HSI-VM | 0.767 | 0.0024 | 0 | 12.9 | 0.033 |
| HSI-VM-nosc | 0.783 | 0.0038 | 1 | 13.3 | 0.070 |
| HSI-VMN | 0.776 | 0.0016 | 0 | 12.9 | 0.033 |
| HSI-VN | 0.786 | 0.0027 | 0 | 14.1 | 0.043 |
| HSI-VN@0.01 | 0.719 | 0.0011 | 0 | 15.6 | 0.033 |
| HSI-VN@0.02 | 0.750 | 0.0014 | 0 | 14.7 | 0.033 |
| HSI-VN@0.1 | 0.797 | 0.0035 | 0 | 14.1 | 0.049 |
| HSI-VN@0.2 | 0.800 | 0.0046 | 3 | 14.3 | 0.050 |
| HSI-Vc | 0.759 | 0.0027 | 0 | 14.6 | 0.042 |
| HSI-adapt | 0.651 | 0.0043 | 7 | 18.8 | 0.045 |
| HSI-m | 0.746 | 0.0027 | 1 | 14.6 | 0.067 |
| HSI-nofloor | 0.630 | 0.0032 | 1 | 20.1 | 0.023 |
| HSI-nogate | 0.631 | 0.0031 | 1 | 19.9 | 0.012 |
| HSI-nosc | 0.640 | 0.0042 | 13 | 20.9 | 0.127 |
| HSI-nounl | 0.630 | 0.0025 | 7 | 19.9 | 0.018 |
| HSI-regime | 0.534 | 0.0002 | 0 | 23.6 | 0.002 |
| HSI-rigid | 0.635 | 0.0018 | 0 | 19.6 | 0.018 |
| HSI-rot | 0.632 | 0.0017 | 1 | 19.7 | 0.013 |
| HSI-rot-m | 0.756 | 0.0027 | 0 | 14.0 | 0.058 |
| HSI-rot-m-c | 0.761 | 0.0028 | 0 | 13.7 | 0.058 |
| HSI-rot-m-s | 0.753 | 0.0022 | 0 | 14.5 | 0.058 |
| HSI-rot-m-sc | 0.758 | 0.0023 | 0 | 14.3 | 0.058 |
| HSI-sc@0.01 | 0.700 | 0.0008 | 0 | 15.6 | 0.033 |
| HSI-sc@0.02 | 0.722 | 0.0013 | 0 | 15.1 | 0.033 |
| HSI-sc@0.1 | 0.783 | 0.0046 | 4 | 14.2 | 0.071 |
| HSI-sc@0.2 | 0.799 | 0.0083 | 27 | 14.9 | 0.087 |
| HSI-sess | 0.582 | 0.0007 | 0 | 21.7 | 0.006 |
| Xu21 | 0.689 | 0.1903 | 202 | 47.5 | 0.710 |
| anc | 0.547 | 0.0147 | 40 | 22.2 | 0.175 |
| geo | 0.564 | 0.0026 | 6 | 20.7 | 0.039 |
| geo-rm | 0.680 | 0.0007 | 0 | 15.4 | 0.033 |
| oracle | 0.842 | 0.0000 | 0 | 9.9 | 0.000 |
| top1 | 0.842 | 1.0000 | 413 | 162.0 | 1.000 |
| (idea 1) SH | 0.728 | 0.0025 | 2 | 14.9 | – |


## 6. Novelty, hạn chế, việc tiếp theo

**Novelty (Gate 17).** Gần nhất: Lajoie & Beltrame RA-L'23 (nhãn tự giám sát từ pose-graph để fine-tune VPR + ước lượng bất định — cần
loop closure, không có trạng thái off-map, không có quyết định online có bảo đảm); TF-VPR, Carson'23, Claxton'24; ACI với phản hồi trễ. Mới: (i)
nhãn của lớp OFF-MAP (lớp không bao giờ có nhãn khi triển khai) từ dead-reckoning + vùng phủ bản đồ; (ii) nhãn sinh và dùng online, nhân quả, trong
cùng một lần triển khai để học và hiệu chuẩn quyết định báo; (iii) hiệu chuẩn biên của luật hợp gồm chứng chỉ hình học không cần hiệu chuẩn và
điểm số học được, trên excursion thật (mép, đầu chuỗi có sẵn); (iv) chứng chỉ hình học bất biến điều kiện ảnh; (v) chứng nhận rồi hiệu chuẩn — chứng chỉ neo nhãn hồi cứu và không tiêu ngân sách α
(Mệnh đề 6). Từng khối riêng có tiền lệ.

**So với ý tưởng 1.** Ý tưởng 1 can thiệp lên bản đồ để sinh null và hiệu chuẩn một thống kê cố định (bất biến affine — bỏ thông tin); hệ số 1/π và
lỗ ảo khác lỗ thật ở mép làm bảo đảm theo vị trí không đạt. HSI quan sát excursion thật qua hình học hồi cứu, học hàm điểm dùng cả similarity tuyệt
đối, và đạt kiểm toán vị trí 9/9 với recall cao hơn — nhưng phải "học dần": phiên đầu tiên của một lần triển khai chỉ có chứng chỉ hình học (khởi
động lạnh), và mỗi phiên chỉ có 5–7 lỗ thật nên hiệu chuẩn phải gộp phiên (hoán đổi giữa điều kiện chỉ xấp xỉ).

**Phát hiện mới của Entry 5 (Mệnh đề 6).** Hiệu chuẩn hợp tính mọi báo của chứng chỉ trong null hồi cứu là vi phạm; khi null bị nhiễm (cầu
dead-reckoning dài trôi xa — NCLT chỉ 6–13 % frame được xác minh hồi cứu), chứng chỉ báo ĐÚNG ở các frame nhiễm và khoá nhánh học. Dùng chứng chỉ
làm điểm neo hồi cứu sửa cả hai: null sạch hơn và nhánh học được ngân sách. Đo được: chứng chỉ báo trong null ∩ off-map thật = 0.000; một mình
chứng chỉ 0/665 run vi phạm. Đây là một nguyên lý chung cho giám sát toàn vẹn tự giám sát: **chứng nhận rồi hiệu chuẩn** (phần có chứng chỉ không
tiêu ngân sách α và không bị phán xét bằng nhãn kém tin cậy hơn chính nó).

**Hạn chế đã đo.** (1) CMU: chuỗi rất ngắn (trung vị 186 frame), 37/130 chuỗi bắt đầu off-map, 48 % frame thuộc chuỗi không có đoạn nào được
xác minh hồi cứu ⇒ ít nhãn, khởi động lạnh; mọi biến thể vẫn dưới SH (0.65–0.70 vs 0.835). (2) NCLT: chỉ 2 run giữ ra (một bản đồ, off-map tự
nhiên). (3) Sai số điều hướng old town (VIO trôi 6 %/100 m) — HSI-VM giảm nhưng chưa bằng SH. (4) Bảo đảm dựa trên hoán đổi giữa đoạn null hồi
cứu và đoạn off-map thật; null là tập cha nên bảo thủ 5–25× (§5.3) — đúng mà tốn recall. (5) Tập giữ ra đã dùng cho 6 vòng quyết định ⇒ nguy cơ
quá khớp thích nghi; tập xác nhận mới (§5.4) cho thấy lợi ích của các cải tiến sau Entry 3 co lại (+0.014 → +0.007). (6) Tham số mặc định (α, H, độ trễ, 0.5) chung cho
mọi dataset; không tinh chỉnh theo dataset.

**Việc tiếp theo.** Thu hẹp null bằng ước lượng tỉ lệ nhiễm (giảm bảo thủ mà vẫn hợp lệ); mô hình ưu tiên mang từ các lần triển khai trước cho
CMU (khởi động lạnh); bộ dữ liệu không gian (VPR-Space, gợi ý của user) cần pose + thứ tự chuỗi để áp giao thức; kiểm chứng robot thật vòng kín.

## 7. Tái lập

- Dữ liệu: cache công khai `nhatlong1103/hmm-navcache-v2` (7 dataset × 6 descriptor × 10 seed), `nhatlong1103/hmm-e37-caches` (Oxford, St Lucia).
- Một run: `python3 analysis/hsi_eval.py <cache_dir> <ds> <desc> <seeds> --variants HSI-rot-m-sc,HSI-V,HSI-VM,geo-rm`.
- Tập xác nhận mới (bố cục lỗ mới, sinh cache từ dump rồi đánh giá): `python3 analysis/hsi_fresh.py <dump_dir> <ds> <desc> 10 3 --variants ...`.
- So sánh biến thể: `analysis/hsi_compare.py`; quét α + hình: `analysis/hsi_alpha.py --png`.
- Đợt Kaggle: `automation/hsi_wave.py` → `automation/fanout.py --groups --build-only --cpu --nodumps --ds nhatlong1103/hmm-navcache-v2,nhatlong1103/hmm-e37-caches --par 4`
  → `automation/central_monitor.py`; gom: `automation/hsi_collect.py`; bảng: `analysis/hsi_summary.py`; báo cáo: `paper/build_hsi_report.py`.
- Chi phí: ~2–25 s mỗi run mỗi biến thể trên 1 lõi CPU (không cần GPU); đợt 12 biến thể × 441 run ≈ 17 phút trên 10 phiên CPU Kaggle.
