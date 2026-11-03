# Research Log — ý tưởng 2 (branch `hmm-2nd-idea`)

*Nhật ký thí nghiệm của lời giải mới. Entry mới đặt trên cùng. Mỗi entry: bối cảnh, giả thuyết, đăng ký trước (commit trước khi xem kết quả),
thí nghiệm, kết quả (kể cả âm), kết luận. Nhật ký của ý tưởng 1 (Entry 0–39): `history/RESEARCH_LOG_idea1.md`; tóm tắt:
`handoff/07_IDEA1_SUMMARY.md`.*

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
