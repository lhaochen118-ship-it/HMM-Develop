# BÁO CÁO — Ý tưởng 2: HSI, tự giám sát hồi cứu bằng hình học cho định vị chuỗi trên bản đồ có lỗ

*Branch `hmm-2nd-idea`, 2026-11-03/04. Nhật ký: `RESEARCH_LOG.md` Entry 1–3; lý thuyết: `paper/hsi_theory.md`; novelty: `LITERATURE_GATE.md`
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

**Kết quả (413 run giữ ra, 9 dataset × 6 descriptor, so với ý tưởng 1 trên CÙNG run; luật HSI-rot-m-sc, Entry 3, đăng ký trước):**
hợp lệ ở **413/413 run** (segFAR ≤ 0.05; SH của ý tưởng 1: 411/413), **kiểm toán theo vị trí (start / edge / deep) ≤ 0.07 trên 9/9 dataset** — điều ý
tưởng 1 chưa đạt; recall gộp **+0.041** so với SH, cao hơn trên 7/9 dataset (Boreas +0.115, countryside +0.149, St Lucia +0.144, office +0.069,
Oxford +0.045, old town +0.027, Nordland +0.016), descriptor yếu DINOv2 +0.123, NetVLAD +0.068; sai số điều hướng ≤ SH trên 6/9 dataset
(countryside −6.7 m, St Lucia −6.7 m). Bền với tỷ lệ lỗ 10 % (0/84 run vượt α) và 50 % (4/84; SH 3/84), và với off-map tự nhiên (4Seasons chéo
cảnh: 1/36). **Điểm yếu:** CMU (0.652 vs 0.835: chuỗi ngắn, khởi động lạnh, ngân sách hiệu chuẩn chung bị đầu chuỗi chiếm), NCLT (2 run giữ ra:
0.577 vs 0.690), sai số điều hướng old town (+5.7 m) và Boreas (+2.5 m).

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

Lý thuyết (Mệnh đề 1–5, `paper/hsi_theory.md`): neo chứng nhận sai số hằng trên cửa sổ; tham chiếu tin cậy loại tuyến dịch cứng; sai số vị trí
hồi cứu theo cầu Brown; hiệu chuẩn biên cho P(báo trong một đoạn null mới) ≤ α dưới hoán đổi; sàn MAP chặn ngưỡng suy biến.

## 5. Kết quả trên tập giữ ra

Tập giữ ra = mọi run ngoài tập thiết kế (seed 0 × 7 dataset × 4 descriptor): seed 1–9, SALAD/MixVPR, Oxford, St Lucia — 413 run có SH của ý tưởng
1 trên cùng (dataset, descriptor, seed). Ba vòng, mỗi vòng đăng ký trước khi xem bất kỳ kết quả giữ ra nào (`RESEARCH_LOG.md`):

| Vòng | Luật | H1 hợp lệ | H2 recall ≥ SH | H3 descriptor yếu | H4 điều hướng | H5 vị trí | Kết luận |
|---|---|---|---|---|---|---|---|
| Entry 1 | HSI (cửa sổ theo frame) | đạt (1/413 > α) | **không** (3/9; −0.069) | **không** (−0.032) | đạt (5/9) | đạt (9/9) | bác: Oxford/St Lucia (10 m/frame) sụp |
| Entry 2 | HSI-rot-m (cửa sổ theo mét + bù hướng) | đạt (0/413) | đạt (6/9; +0.039) | đạt (+0.089) | đạt (7/9) | đạt (9/9) | luật khuyến nghị (vòng 2) |
| Entry 3 | HSI-rot-m-sc (+ đầu chuỗi, biên null) | đạt (0/413) | đạt (7/9; +0.041) | đạt (+0.096) | đạt (6/9) | đạt (9/9) | **luật khuyến nghị** (H7: ≥ Entry 2 trên 8/9) |

**Ablation (giữ ra; recall / segFAR / số run > α / sai số điều hướng TB):** hiệu chuẩn biên chung thay vì có điều kiện +0.09 recall; gộp phiên thay
vì theo phiên +0.044; bỏ nhất quán ngắn hạn → 13 run vi phạm; bỏ null "chưa từng xác minh" → 7 run vi phạm; chỉ neo nhân quả → 40 run vi phạm,
thêm tham chiếu tin cậy (chỉ hình học) → 6; cửa sổ theo mét +0.12 (Oxford, St Lucia); bù hướng +0.01. Bảng đầy đủ ở Bảng A.

**Độ bền.** Lỗ 10 %: HSI-rot-m-sc 0/84 run vượt α, recall ≥ SH trên 5/6 dataset (gộp +0.005; CMU 0.539 vs 0.845); lỗ 50 %: 4/84 run vượt (SH 3/84),
≥ SH trên 4/6 (gộp +0.048; Nordland −0.10), sai số old town +20.6 m. Off-map tự nhiên (4Seasons, cảnh B hoàn toàn ngoài bản đồ, ảnh + VIO thật,
36 run): recall cảnh A 0.743, segFAR 0.010 (1/36 run 0.053); Xu'21 (nhãn) 0.581 với 10/36 run vượt α. Chi phí: 10–90 s mỗi run (Boreas 74 k
frame) trên một lõi CPU ⇒ ~1 ms/frame cho cả đặc trưng, học lại GBM và đánh giá; ý tưởng 1 cần 18–45 ms/frame trên GPU cho mô phỏng tiến.

### Bảng A — luật khuyến nghị HSI-rot-m-sc (Entry 3), tập giữ ra; Ablation: mọi biến thể

runs: 441 (held-out 413, with idea-1 SH on the same run 413)

## Held-out runs: mean recall / segFAR / navigation error per dataset

| dataset | n | HSI rec / seg / err | geo rec / seg / err | SH rec / seg / err | CST-JS rec / seg / err | oracle rec / seg / err | HSI−SH rec (wins) | HSI−SH err (better) |
|---|---|---|---|---|---|---|---|---|
| boreas | 56 | 0.892 / 0.001 / 6.9 | 0.832 / 0.001 / 5.9 | 0.777 / 0.002 / 4.5 | 0.781 / 0.011 / 8.5 | 0.882 / 0.000 / 2.1 | +0.115 (56/56) | +2.5 (33/56) |
| nclt | 2 | 0.577 / 0.000 / 5.1 | 0.565 / 0.000 / 3.9 | 0.690 / 0.000 / 3.2 | 0.711 / 0.002 / 3.4 | 0.784 / 0.000 / 2.2 | -0.113 (0/2) | +1.9 (0/2) |
| cmu | 56 | 0.652 / 0.006 / 3.8 | 0.450 / 0.005 / 3.6 | 0.835 / 0.009 / 3.9 | 0.816 / 0.019 / 3.8 | 0.945 / 0.000 / 2.9 | -0.183 (10/56) | -0.1 (38/56) |
| nord | 56 | 0.785 / 0.000 / 5.0 | 0.679 / 0.000 / 5.9 | 0.770 / 0.000 / 6.0 | 0.783 / 0.001 / 6.1 | 0.676 / 0.000 / 5.1 | +0.016 (23/56) | -1.0 (22/56) |
| 4s_office_loop | 56 | 0.872 / 0.000 / 9.0 | 0.697 / 0.001 / 11.6 | 0.803 / 0.000 / 9.7 | 0.815 / 0.008 / 9.7 | 0.914 / 0.000 / 8.3 | +0.069 (54/56) | -0.7 (47/56) |
| 4s_old_town | 56 | 0.735 / 0.001 / 31.6 | 0.594 / 0.003 / 47.2 | 0.708 / 0.006 / 25.9 | 0.715 / 0.012 / 39.6 | 0.844 / 0.000 / 19.3 | +0.027 (39/56) | +5.7 (25/56) |
| 4s_countryside | 56 | 0.642 / 0.005 / 26.8 | 0.595 / 0.011 / 27.8 | 0.492 / 0.001 / 33.5 | 0.503 / 0.005 / 32.9 | 0.739 / 0.000 / 16.0 | +0.149 (56/56) | -6.7 (52/56) |
| oxford | 45 | 0.764 / 0.006 / 21.4 | 0.338 / 0.002 / 35.3 | 0.719 / 0.004 / 21.9 | 0.729 / 0.021 / 22.0 | 0.899 / 0.000 / 15.9 | +0.045 (34/45) | -0.4 (35/45) |
| stlucia | 30 | 0.905 / 0.002 / 18.8 | 0.332 / 0.000 / 44.9 | 0.761 / 0.001 / 25.5 | 0.763 / 0.021 / 25.6 | 0.896 / 0.000 / 17.3 | +0.144 (30/30) | -6.7 (30/30) |

## Pre-registered hypotheses (Entry 1) on the held-out runs

- **H1 (validity):** mean segFAR <= 0.05 on 9/9 datasets; runs > 0.05: 0/413 (0.0%) -> **supported**
- **H2 (recall):** HSI >= SH on 7/9 datasets; pooled mean difference +0.0410 -> **supported**
- **H3 (weak descriptors):** DINOv2 + NetVLAD held-out runs: mean HSI − SH = +0.0964 over 133 runs -> **supported**
- **H4 (navigation):** mean error within +1 m of SH on 6/9 datasets -> **supported**
- **H5 (position audit):** every class <= 0.07 (classes with >= 50 segments) on 9/9 datasets -> **supported**
  - boreas: start 0.019 (n=4632), edge 0.001 (n=3954), deep 0.000 (n=86096)
  - nclt: start 0.000 (n=186), edge 0.000 (n=52), deep 0.000 (n=374)
  - cmu: start 0.007 (n=24472), edge 0.000 (n=0), deep 0.000 (n=0)
  - nord: start 0.000 (n=496), edge 0.000 (n=798), deep 0.000 (n=20102)
  - 4s_office_loop: start 0.000 (n=504), edge 0.000 (n=806), deep 0.000 (n=14580)
  - 4s_old_town: start 0.002 (n=1756), edge 0.003 (n=612), deep 0.000 (n=10238)
  - 4s_countryside: start 0.023 (n=1152), edge 0.007 (n=684), deep 0.004 (n=13560)
  - oxford: start 0.030 (n=2634), edge 0.007 (n=8799), deep 0.004 (n=34788)
  - stlucia: start 0.058 (n=120), edge 0.000 (n=1794), deep 0.000 (n=2556)

## Held-out, per descriptor (mean over datasets and seeds)

| descriptor | n | HSI rec | SH rec | HSI−SH | wins | HSI seg | HSI err | SH err |
|---|---|---|---|---|---|---|---|---|
| cosplace | 64 | 0.792 | 0.775 | +0.017 | 45 | 0.003 | 13.5 | 14.1 |
| netvlad | 64 | 0.616 | 0.548 | +0.068 | 54 | 0.002 | 24.5 | 21.6 |
| megaloc | 64 | 0.881 | 0.884 | -0.004 | 42 | 0.001 | 10.7 | 11.0 |
| dinov2 | 69 | 0.617 | 0.494 | +0.123 | 57 | 0.005 | 18.3 | 23.1 |
| salad | 76 | 0.863 | 0.845 | +0.018 | 48 | 0.002 | 11.5 | 12.0 |
| mixvpr | 76 | 0.846 | 0.822 | +0.024 | 56 | 0.002 | 12.3 | 12.3 |

## Ablations (held-out runs; mean over datasets of the per-dataset means)

| variant | recall | segFAR | runs seg>0.05 | nav err | worst-class rate |
|---|---|---|---|---|---|
| HSI | 0.758 | 0.0023 | 0 | 14.3 | 0.058 |
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
| HSI-sess | 0.582 | 0.0007 | 0 | 21.7 | 0.006 |
| Xu21 | 0.689 | 0.1903 | 202 | 47.5 | 0.710 |
| anc | 0.547 | 0.0147 | 40 | 22.2 | 0.175 |
| geo | 0.564 | 0.0026 | 6 | 20.7 | 0.039 |
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
| HSI-sess | 0.582 | 0.0007 | 0 | 21.7 | 0.006 |
| Xu21 | 0.689 | 0.1903 | 202 | 47.5 | 0.710 |
| anc | 0.547 | 0.0147 | 40 | 22.2 | 0.175 |
| geo | 0.564 | 0.0026 | 6 | 20.7 | 0.039 |
| oracle | 0.842 | 0.0000 | 0 | 9.9 | 0.000 |
| top1 | 0.842 | 1.0000 | 413 | 162.0 | 1.000 |
| (idea 1) SH | 0.728 | 0.0025 | 2 | 14.9 | – |


## 6. Novelty, hạn chế, việc tiếp theo

**Novelty (Gate 17).** Gần nhất: Lajoie & Beltrame RA-L'23 (nhãn tự giám sát từ pose-graph để fine-tune VPR + ước lượng bất định — cần
loop closure, không có trạng thái off-map, không có quyết định online có bảo đảm); TF-VPR, Carson'23, Claxton'24; ACI với phản hồi trễ. Mới: (i)
nhãn của lớp OFF-MAP (lớp không bao giờ có nhãn khi triển khai) từ dead-reckoning + vùng phủ bản đồ; (ii) nhãn sinh và dùng online, nhân quả, trong
cùng một lần triển khai để học và hiệu chuẩn quyết định báo; (iii) hiệu chuẩn biên của luật hợp gồm chứng chỉ hình học không cần hiệu chuẩn và
điểm số học được, trên excursion thật (mép, đầu chuỗi có sẵn); (iv) chứng chỉ hình học bất biến điều kiện ảnh. Từng khối riêng có tiền lệ.

**So với ý tưởng 1.** Ý tưởng 1 can thiệp lên bản đồ để sinh null và hiệu chuẩn một thống kê cố định (bất biến affine — bỏ thông tin); hệ số 1/π và
lỗ ảo khác lỗ thật ở mép làm bảo đảm theo vị trí không đạt. HSI quan sát excursion thật qua hình học hồi cứu, học hàm điểm dùng cả similarity tuyệt
đối, và đạt kiểm toán vị trí 9/9 với recall cao hơn — nhưng phải "học dần": phiên đầu tiên của một lần triển khai chỉ có chứng chỉ hình học (khởi
động lạnh), và mỗi phiên chỉ có 5–7 lỗ thật nên hiệu chuẩn phải gộp phiên (hoán đổi giữa điều kiện chỉ xấp xỉ).

**Hạn chế đã đo.** (1) CMU: chuỗi rất ngắn (trung vị 186 frame) và nhiều chuỗi bắt đầu off-map; ngưỡng chung bị các đoạn đầu chuỗi chiếm ⇒ hướng
sửa: hiệu chuẩn Mondrian theo chế độ quyết định (đã/ chưa có tham chiếu tin cậy). (2) NCLT: off-map tự nhiên sát bản đồ (off_d 20 m) — vị trí hồi
cứu ±3–5 m làm null mơ hồ. (3) Sai số điều hướng old town (VIO trôi 6 %/100 m; khoảng trống fix dài ở đầu phiên). (4) Bảo đảm dựa trên hoán đổi giữa
đoạn null hồi cứu và đoạn sai thật; nhãn hồi cứu sai (tuyến dịch cứng được xác minh) làm thiếu null — đo được hiếm (≤ 0.7 % neo sai).

**Việc tiếp theo.** Entry 4: Mondrian theo chế độ; mô hình ưu tiên (prior) mang từ các lần triển khai trước để giảm khởi động lạnh; bộ dữ liệu
không gian (VPR-Space, gợi ý của user) cần pose + thứ tự chuỗi để áp giao thức bản đồ có lỗ; kiểm chứng robot thật vòng kín.

## 7. Tái lập

- Dữ liệu: cache công khai `nhatlong1103/hmm-navcache-v2` (7 dataset × 6 descriptor × 10 seed), `nhatlong1103/hmm-e37-caches` (Oxford, St Lucia).
- Một run: `python3 analysis/hsi_eval.py <cache_dir> <ds> <desc> <seeds> --variants HSI,HSI-rot-m,geo`.
- Đợt Kaggle: `automation/hsi_wave.py` → `automation/fanout.py --groups --build-only --cpu --nodumps --ds nhatlong1103/hmm-navcache-v2,nhatlong1103/hmm-e37-caches --par 4`
  → `automation/central_monitor.py`; gom: `automation/hsi_collect.py`; bảng: `analysis/hsi_summary.py`; báo cáo: `paper/build_hsi_report.py`.
- Chi phí: ~2–25 s mỗi run mỗi biến thể trên 1 lõi CPU (không cần GPU); đợt 12 biến thể × 441 run ≈ 17 phút trên 10 phiên CPU Kaggle.
