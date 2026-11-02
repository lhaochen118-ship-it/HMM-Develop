# Báo cáo vòng 10 (Entry 36): phẫu thuật bản đồ phản thực TIẾN — null của chính quỹ đạo ma của hệ thống

*Branch `hmm-navigation-5`, 2026-11-02. Nhật ký: `RESEARCH_LOG.md` Entry 36 (đăng ký trước, sửa đổi, sai lệch). Lý thuyết:
`paper/cms_theory.md` §4f (Mệnh đề 16–18). Code: `analysis/cms_vec.py`, `cms_fwd.py`, `cst_audit.py`, `e36_run.py`, `n40_run.py`,
`safevpr26.py`, `safevpr26_eval.py`; bảng: `paper/build_e36_report.py` → `paper/e36_tables.md`. Phiên này không có token Kaggle: mọi
tính toán chạy trên 4 lõi CPU của phiên, từ cache công khai.*

## 1. Bốn việc được giao và kết luận ngắn

| Việc | Kết quả |
|---|---|
| 1. Phẫu thuật "tiến" cho đoạn mép chuyến off-map | **Làm xong, rộng hơn yêu cầu.** Kiểm toán cho thấy CST lọt fix sai ở **mọi** độ sâu (đoạn off-map thật qua CST 5–32 %, mục tiêu ≤ 5 %), không chỉ ở mép. Phẫu thuật tiến (chạy chính chuỗi vị trí của hệ thống tiến từ lối thoát ảo trên bản đồ đã cắt) cho **CST-F**: tỷ lệ qua 0.4–4.7 % trên 9/9 nhóm dữ liệu (kể cả mép, Oxford, St Lucia), segFAR ≤ 0.004, xoá chi phí điều hướng của CST (Boreas −12.5 m, old town −13.0 m); giá: recall −0.01 đến −0.18. |
| Tiêu chí recall trên Oxford | **SH ∧ CST-J\*** (hiệu chuẩn cả quyết định trên mô phỏng tiến, thăm dò): recall = SH trên 7/7 dataset và Oxford (0.729 = 0.729; SH ∧ CST 0.694), xác nhận trên tập giữ ra (6/6). Bảo đảm của CST-J chỉ xấp xỉ: CST-J một mình vượt α trên CMU giữ ra (0.065–0.068). CST-F không đạt tiêu chí Oxford (0.550). |
| SHcf | Thay bằng CST-F/CST-J: dung sai giờ được hiệu chuẩn trên **quỹ đạo ma của chính hệ thống** thay vì phân vị từng frame của winner phản thực. |
| 2. Cửa sổ niềm tin N = 40 trên seed 1–9 | **Xác nhận (CosPlace, 48 run):** segFAR ≤ 0.011 trên 6/6, recall ≥ N = 20 trên 5/6 (countryside +0.069, CMU −0.003) ⇒ khuyến nghị N = 40; các descriptor khác còn mở. |
| 3. Vector hoá thống kê phản thực | **Xong.** 3.9 ms/frame trên 1 lõi (vòng lặp 9.4 ms; Kaggle 10.3–17.5 ms), trùng tuyệt đối với cache đã công bố ⇒ ngưỡng đặt trước < 10 ms đạt. |
| 4. St Lucia + SafeVPR'26 | **Xong (CosPlace).** St Lucia (10 lượt chạy, HF mirror) thêm vào pipeline. So sánh trực tiếp theo thước đo của SafeVPR (FDR / TPR): không lỗ — bão hoà; 30 % lỗ — SafeVPR'26 (nhãn) recall 0.462 / 0.557 ở α = 0.05 / 0.10, của ta (không nhãn) 0.590–0.623 với FDR ≤ 0.010. Trên St Lucia, null bản đồ cũ (CPC-SC-T½) có recall cao hơn CMS. |

## 2. Vector hoá thống kê phản thực

`analysis/cms_vec.py` làm đúng phép tính của `cms_exact.cms_stats_exact` nhưng theo lô frame: nhóm cửa sổ theo độ dài, Procrustes theo
lô, tra cứu ngoại hình bằng searchsorted trên các hàng nối đuôi (có hiệu chỉnh chính xác một bước), phép thử hành lang hai tầng (phủ
anchor + dải mơ hồ) và **tính thành viên hành lang trên các hàng bản đồ** thay vì trên từng mục của danh sách dài. Kiểm tra: trùng tuyệt
đối với vòng lặp (8/8 đầu ra, sai khác tối đa 0); trùng với cache Kaggle đã công bố: chi phí tuyến và độ khác biệt (thật và phản thực)
100 %, winner 99.8 % (hoà điểm của danh sách fp16). Phát hiện kèm: đường CPU của `topk_long` dùng độ lệch chuẩn lệch (N), đường GPU
dùng không lệch (N − 1) → z lệch hằng số √(N/(N−1)); đã sửa. Thời gian (1 lõi): 3.9 ms/frame (N = 20) so với 9.4 ms của vòng lặp
trên cùng lõi và 10.3–17.5 ms đo trên Kaggle → **ngưỡng đặt trước < 10 ms/frame của Entry 32 nay đạt**. N = 40: 6.6 ms/frame (trước
khi tính thành viên theo hàng bản đồ: 16 ms).

## 3. Chẩn đoán: giả định của Mệnh đề 14 sai ở mọi độ sâu, không chỉ ở mép

`analysis/cst_audit.py` đo trực tiếp đại lượng mà Mệnh đề 14 chặn, P(∃ t ∈ G₀: r_t ≤ ε), trên các đoạn off-map **thật** (nhãn chỉ để
đánh giá). Nếu (S3-T) đúng thì tỷ lệ này ≤ a/π ≈ 0.05.

Bảng kiểm toán ở đầu mục 5 (dòng "CST" so với "CST-F").

Hai nguyên nhân: (i) null track của CST là chuỗi winner phản thực **của từng frame**, mỗi frame một phẫu thuật riêng và một bộ ước lượng
khác (phép thử tuyến) — các winner liên tiếp là những nơi không liên quan, nên null kém mạch lạc hơn nhiều so với quỹ đạo ma mà chuỗi vị
trí thật sự đi theo sau khi rời bản đồ (dính mép lỗ, khoá vào đường song song hay nơi giống nhau ở xa: CMU, sai 1.1 km với residual
6–15 m); (ii) cửa sổ hình dạng bị cắt ở đầu chuỗi (43 % frame của CMU: 130 chuỗi ngắn, robot bắt đầu trong lỗ). Các luật CST vẫn hợp lệ
ở Entry 34 chỉ vì khởi phát của chuỗi hiện diện cũng phải xảy ra. Thiệt hại điều hướng của CST (Entry 35: Boreas +9 m, old town +13.6 m)
đến chủ yếu từ các fix sai **sâu** trong chuyến (Boreas NetVLAD s7: 269/345 ở độ sâu ≥ 80 frame, sai trung vị 419 m), không phải ở mép.
Mất recall trên Oxford (H35d) là chuyện khác: CST **chặt hơn** SH trên Oxford.

## 4. Phương pháp: phẫu thuật tiến và hiệu chuẩn đầu-cuối

**Lối thoát ảo.** Tại frame τ (mỗi 1 excl quãng đường), xoá vùng bản đồ robot đi qua sau τ: V_τ = { m : d(m, X⁺) ≤ ρ, d(m, X⁺) < d(m, X⁻) }
(X⁺ / X⁻: vị trí tin sau / trước τ trong off_d + 20 excl quãng đường; cắt Voronoi giữ bản đồ trước điểm thoát; ρ = off_d), rồi chạy
**chính chuỗi vị trí của hệ thống** (bản sao chính xác của `DiagFilter`, emission tính lại trên bản đồ đã phẫu thuật; khớp MAP thật
99.95–100 %) tiến từ niềm tin của nó tại τ. **Khởi đầu ảo:** chuỗi khởi động lại đều tại τ, bỏ hành lang ρ quanh 3 excl đường tiếp theo,
cửa sổ cắt tại τ (đúng tình huống robot bắt đầu trong lỗ).

**Ba luật hiệu chuẩn từ các lần chạy ảo** (đoạn ảo cắt như đoạn thật; ngưỡng = min theo bin vị trí trong chuyến, mỗi bin ≥ 2/a đoạn):
- **CST-F** (Mệnh đề 16–17): ε = phân vị a của cực tiểu residual của quỹ đạo ghép (thật đến τ, ma sau τ) trên đoạn ảo. Mọi báo cáo phải qua
  ⇒ tỷ lệ báo sai theo đoạn ≤ a/π **chỉ nhờ phép thử hình dạng**, mọi vị trí (kể cả mép), mọi chuỗi hiện diện, mọi dung sai SH.
- **CST-J** (Mệnh đề 18): mô phỏng **cả quyết định** dọc lần chạy ảo — chuỗi hiện diện tiếp tục từ trạng thái thật tại τ với log-LR phản thực,
  cổng +G trên quỹ đạo ma, residual — và chọn dung sai lớn nhất sao cho tỷ lệ báo của đoạn ảo ≤ a (có thể = ∞).
- **CST-J\*** (thăm dò, tìm thấy giữa đánh giá): như CST-J, nhưng frame có cửa sổ < 1 excl được phép báo và điều này được tính trong chính mô
  phỏng (khởi đầu ảo báo trên cửa sổ ngắn = báo sai).
SH, +G, +NGRr chỉ bỏ báo cáo nên giữ nguyên các cận (Bổ đề 7): **SH ∧ CST-J(\*)** hợp lệ với mọi dung sai SH.

## 5. Kết quả

### Kiểm toán (S3-T) / (S3-F): tỷ lệ đoạn off-map THẬT qua phép thử hình dạng (mục tiêu ≤ a = 0.05; nhãn chỉ để đánh giá)

| Dataset | run | CST: tất cả / mép / sâu | CST-F: tất cả / mép / sâu | CST-F: cửa sổ đủ / bị cắt | ε CST / ε CST-F / oracle |
|---|---|---|---|---|---|
| Boreas | 8 | 0.182 / 0.397 / 0.178 | **0.025** / 0.005 / 0.027 | 0.025 / 0.000 | 18.5 / 8.3 / 12.2 |
| NCLT | 5 | 0.187 / 0.142 / 0.192 | **0.025** / 0.018 / 0.028 | 0.024 / 0.033 | 6.1 / 3.7 / 4.3 |
| CMU | 18 | 0.067 / 0.111 / 0.056 | **0.019** / 0.011 / 0.015 | 0.020 / 0.016 | 14.0 / 9.0 / 13.7 |
| Nordland | 18 | 0.302 / 0.372 / 0.302 | **0.036** / 0.011 / 0.039 | 0.036 / 0.028 | 3.6 / 1.5 / 1.7 |
| 4S office | 18 | 0.099 / 0.236 / 0.089 | **0.004** / 0.000 / 0.004 | 0.004 / nan | 14.5 / 9.3 / 15.5 |
| 4S old town | 18 | 0.147 / 0.445 / 0.117 | **0.019** / 0.055 / 0.016 | 0.018 / 0.042 | 23.6 / 9.2 / 14.0 |
| 4S countryside | 18 | 0.051 / 0.083 / 0.051 | **0.015** / 0.014 / 0.016 | 0.015 / nan | 12.2 / 9.2 / 13.0 |
| Oxford | 30 | 0.321 / 0.320 / 0.346 | **0.033** / 0.022 / 0.038 | 0.033 / 0.025 | 13.6 / 4.8 / 6.2 |
| St Lucia | 5 | 0.219 / 0.144 / 0.292 | **0.047** / 0.015 / 0.060 | 0.048 / 0.000 | 10.4 / 2.3 / 3.4 |

### Entry 36 — CST-F (seed 0–2, 104 run, α = 0.05): recall / segFAR TB / tệ nhất / sai số điều hướng (m)

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.710 / 0.007 / 0.023 / 7.9 | 0.588 / 0.001 / 0.003 / 4.9 | 0.713 / 0.004 / 0.021 / 4.0 | 0.711 / 0.000 / 0.003 / 11.5 | 0.736 / 0.000 / 0.003 / 11.9 | 0.616 / 0.006 / 0.023 / 32.0 | 0.340 / 0.000 / 0.000 / 52.0 |
| CMS-CPC/ H+SH+G+NGRr (SH chọn tay) | 0.815 / 0.006 / 0.022 / 4.7 | 0.612 / 0.002 / 0.007 / 4.3 | 0.764 / 0.003 / 0.014 / 3.9 | 0.752 / 0.000 / 0.000 / 6.9 | 0.795 / 0.000 / 0.006 / 10.1 | 0.687 / 0.003 / 0.010 / 27.5 | 0.513 / 0.001 / 0.006 / 33.9 |
| SH ∧ CST (Entry 35) | 0.815 / 0.006 / 0.022 / 4.6 | 0.608 / 0.002 / 0.007 / 4.3 | 0.762 / 0.003 / 0.014 / 3.9 | 0.752 / 0.000 / 0.000 / 6.9 | 0.792 / 0.000 / 0.006 / 10.2 | 0.686 / 0.003 / 0.010 / 27.5 | 0.499 / 0.000 / 0.000 / 34.8 |
| CST (Entry 34) | 0.822 / 0.019 / 0.058 / 16.3 | 0.617 / 0.002 / 0.010 / 4.9 | 0.769 / 0.008 / 0.041 / 4.0 | 0.764 / 0.001 / 0.005 / 6.9 | 0.805 / 0.013 / 0.072 / 10.5 | 0.715 / 0.017 / 0.057 / 41.5 | 0.510 / 0.002 / 0.033 / 32.5 |
| **CMS-CPC/ H+CSTF+G+NGRr (CST-F, đề xuất)** | 0.804 / 0.004 / 0.013 / 3.8 | 0.581 / 0.000 / 0.000 / 3.3 | 0.603 / 0.000 / 0.003 / 3.1 | 0.726 / 0.000 / 0.000 / 7.0 | 0.771 / 0.000 / 0.006 / 10.2 | 0.637 / 0.002 / 0.008 / 28.5 | 0.477 / 0.000 / 0.000 / 39.2 |
| SH ∧ CST-F | 0.804 / 0.004 / 0.013 / 4.0 | 0.581 / 0.000 / 0.000 / 3.3 | 0.603 / 0.000 / 0.000 / 3.1 | 0.726 / 0.000 / 0.000 / 7.0 | 0.771 / 0.000 / 0.006 / 10.2 | 0.637 / 0.002 / 0.008 / 28.5 | 0.477 / 0.000 / 0.000 / 39.2 |
| CMS-CPCW/ H+CSTF+NGRr | 0.795 / 0.004 / 0.012 / 4.2 | 0.573 / 0.000 / 0.000 / 3.4 | 0.600 / 0.000 / 0.003 / 3.1 | 0.717 / 0.000 / 0.000 / 6.9 | 0.765 / 0.000 / 0.003 / 10.2 | 0.632 / 0.002 / 0.008 / 28.6 | 0.454 / 0.000 / 0.002 / 44.2 |
| CST-F [both] (nhân quả) | 0.782 / 0.004 / 0.013 / 4.2 | 0.572 / 0.000 / 0.000 / 3.4 | 0.592 / 0.000 / 0.000 / 3.0 | 0.697 / 0.000 / 0.000 / 7.5 | 0.746 / 0.000 / 0.000 / 10.5 | 0.606 / 0.000 / 0.000 / 30.5 | 0.424 / 0.000 / 0.000 / 45.5 |
| CMS-CPCW/ H+CSTF[both]+NGRr (nhân quả) | 0.772 / 0.004 / 0.012 / 4.4 | 0.562 / 0.000 / 0.000 / 3.6 | 0.588 / 0.000 / 0.000 / 3.1 | 0.665 / 0.000 / 0.000 / 9.5 | 0.734 / 0.000 / 0.000 / 10.8 | 0.597 / 0.000 / 0.003 / 31.2 | 0.390 / 0.000 / 0.000 / 49.6 |
| CST-F không cổng +NGRr | 0.804 / 0.007 / 0.020 / 8.0 | 0.581 / 0.002 / 0.010 / 4.5 | 0.603 / 0.002 / 0.027 / 3.1 | 0.729 / 0.001 / 0.003 / 5.9 | 0.773 / 0.001 / 0.015 / 10.3 | 0.650 / 0.002 / 0.009 / 44.0 | 0.491 / 0.000 / 0.000 / 35.1 |
| CST-J (mô phỏng cả quyết định) | 0.824 / 0.030 / 0.064 / 11.6 | 0.640 / 0.005 / 0.010 / 5.5 | 0.644 / 0.027 / 0.095 / 3.6 | 0.781 / 0.006 / 0.013 / 6.9 | 0.811 / 0.027 / 0.068 / 10.8 | 0.717 / 0.022 / 0.063 / 39.4 | 0.541 / 0.021 / 0.051 / 32.5 |
| SH ∧ CST-J | 0.809 / 0.006 / 0.021 / 4.4 | 0.612 / 0.002 / 0.007 / 4.3 | 0.615 / 0.003 / 0.014 / 3.2 | 0.752 / 0.000 / 0.000 / 6.9 | 0.784 / 0.000 / 0.006 / 10.1 | 0.684 / 0.003 / 0.010 / 27.5 | 0.509 / 0.001 / 0.006 / 35.4 |
| CST-J\* (thăm dò) | 0.829 / 0.030 / 0.064 / 11.7 | 0.640 / 0.005 / 0.010 / 5.5 | 0.792 / 0.027 / 0.095 / 4.2 | 0.781 / 0.006 / 0.013 / 6.9 | 0.821 / 0.027 / 0.068 / 10.8 | 0.720 / 0.022 / 0.063 / 39.4 | 0.544 / 0.021 / 0.051 / 32.5 |
| **SH ∧ CST-J\*** (thăm dò) | 0.814 / 0.006 / 0.021 / 4.8 | 0.612 / 0.002 / 0.007 / 4.3 | 0.764 / 0.003 / 0.014 / 3.9 | 0.752 / 0.000 / 0.000 / 6.9 | 0.794 / 0.000 / 0.006 / 10.1 | 0.686 / 0.003 / 0.010 / 27.5 | 0.511 / 0.001 / 0.006 / 35.4 |
| CST-J [both] (nhân quả) | 0.801 / 0.027 / 0.061 / 7.8 | 0.628 / 0.003 / 0.010 / 4.5 | 0.623 / 0.020 / 0.093 / 3.3 | 0.747 / 0.005 / 0.013 / 7.4 | 0.776 / 0.016 / 0.059 / 10.7 | 0.698 / 0.016 / 0.054 / 28.7 | 0.478 / 0.011 / 0.045 / 40.0 |

**Kiểm giả thuyết (đăng ký trước, Entry 36):**

- H36a: tỷ lệ qua của CST-F ≤ 0.07 trên 7/7 (cần ≥ 6/7); thấp hơn CST trên 7/7 (cần 7/7)
- H36b: segFAR TB của CST-F ≤ 0.05 trên 7/7
- H36c: sai số điều hướng CST-F − SH ≤ 1 m trên 6/7 (cần ≥ 6/7): Boreas -0.9, NCLT -1.0, CMU -0.9, Nordland +0.1, 4S office +0.1, 4S old town +1.0, 4S countryside +5.3
- H36d: recall CST-F − SH ≥ −0.03 trên 3/7 (cần ≥ 4/7): Boreas -0.011, NCLT -0.032, CMU -0.161, Nordland -0.027, 4S office -0.024, 4S old town -0.050, 4S countryside -0.036
- So với CST (Entry 34) về sai số điều hướng: Boreas -12.5 m, NCLT -1.6 m, CMU -1.0 m, Nordland +0.1 m, 4S office -0.3 m, 4S old town -13.0 m, 4S countryside +6.7 m

Tỷ lệ run có segFAR > α / segFAR tệ nhất (mọi dataset):

| Luật | run > α | tệ nhất | số run |
|---|---|---|---|
| CMS-CPC/H+SH+G+NGRr (SH chọn tay) | 0.000 | 0.022 | 104 |
| SH ∧ CST (Entry 35) | 0.000 | 0.022 | 104 |
| CST (Entry 34) | 0.029 | 0.072 | 104 |
| **CMS-CPC/H+CSTF+G+NGRr (CST-F, đề xuất)** | 0.000 | 0.013 | 104 |
| SH ∧ CST-F | 0.000 | 0.013 | 104 |
| CMS-CPCW/H+CSTF+NGRr | 0.000 | 0.012 | 104 |
| CST-F [both] (nhân quả) | 0.000 | 0.013 | 104 |

### Oxford RobotCar (30 run, 30 % lỗ): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | Oxford RobotCar |
|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.468 / 0.011 / 0.042 / 37.5 |
| CMS-CPC/ H+SH+G+NGRr (SH chọn tay) | 0.729 / 0.004 / 0.011 / 21.8 |
| SH ∧ CST (Entry 35) | 0.694 / 0.002 / 0.009 / 22.1 |
| CST (Entry 34) | 0.700 / 0.013 / 0.051 / 22.2 |
| **CMS-CPC/ H+CSTF+G+NGRr (CST-F, đề xuất)** | 0.550 / 0.001 / 0.003 / 23.8 |
| SH ∧ CST-F | 0.550 / 0.001 / 0.003 / 23.8 |
| CMS-CPCW/ H+CSTF+NGRr | 0.564 / 0.001 / 0.003 / 23.4 |
| CST-F [both] (nhân quả) | 0.532 / 0.001 / 0.003 / 24.9 |
| CMS-CPCW/ H+CSTF[both]+NGRr (nhân quả) | 0.541 / 0.001 / 0.003 / 24.6 |
| CST-F không cổng +NGRr | 0.556 / 0.002 / 0.005 / 23.3 |
| CST-J (mô phỏng cả quyết định) | 0.755 / 0.041 / 0.069 / 22.2 |
| SH ∧ CST-J | 0.728 / 0.004 / 0.011 / 21.8 |
| CST-J\* (thăm dò) | 0.756 / 0.041 / 0.069 / 22.2 |
| **SH ∧ CST-J\*** (thăm dò) | 0.729 / 0.004 / 0.011 / 21.8 |
| CST-J [both] (nhân quả) | 0.740 / 0.040 / 0.068 / 23.2 |

- CMS-CPC/H+SH+G+NGRr (SH chọn tay): run segFAR > α = 0.00, tệ nhất 0.011 (30 run)
- SH ∧ CST (Entry 35): run segFAR > α = 0.00, tệ nhất 0.009 (30 run)
- CST (Entry 34): run segFAR > α = 0.03, tệ nhất 0.051 (30 run)
- **CMS-CPC/H+CSTF+G+NGRr (CST-F, đề xuất)**: run segFAR > α = 0.00, tệ nhất 0.003 (30 run)
- SH ∧ CST-F: run segFAR > α = 0.00, tệ nhất 0.003 (30 run)

### St Lucia (5 run, 30 % lỗ): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | St Lucia |
|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.920 / 0.021 / 0.037 / 18.4 |
| CMS-CPC/ H+SH+G+NGRr (SH chọn tay) | 0.820 / 0.000 / 0.000 / 23.1 |
| SH ∧ CST (Entry 35) | 0.818 / 0.000 / 0.000 / 23.2 |
| CST (Entry 34) | 0.818 / 0.000 / 0.000 / 23.2 |
| **CMS-CPC/ H+CSTF+G+NGRr (CST-F, đề xuất)** | 0.622 / 0.000 / 0.000 / 26.0 |
| SH ∧ CST-F | 0.622 / 0.000 / 0.000 / 26.0 |
| CMS-CPCW/ H+CSTF+NGRr | 0.645 / 0.000 / 0.000 / 23.9 |
| CST-F [both] (nhân quả) | 0.586 / 0.000 / 0.000 / 26.5 |
| CMS-CPCW/ H+CSTF[both]+NGRr (nhân quả) | 0.603 / 0.000 / 0.000 / 25.4 |
| CST-F không cổng +NGRr | 0.633 / 0.003 / 0.013 / 22.7 |
| CST-J (mô phỏng cả quyết định) | 0.818 / 0.050 / 0.087 / 23.1 |
| SH ∧ CST-J | 0.818 / 0.000 / 0.000 / 23.1 |
| CST-J\* (thăm dò) | 0.818 / 0.050 / 0.087 / 23.1 |
| **SH ∧ CST-J\*** (thăm dò) | 0.818 / 0.000 / 0.000 / 23.1 |
| CST-J [both] (nhân quả) | 0.816 / 0.047 / 0.087 / 23.2 |

- CMS-CPC/H+SH+G+NGRr (SH chọn tay): run segFAR > α = 0.00, tệ nhất 0.000 (5 run)
- SH ∧ CST (Entry 35): run segFAR > α = 0.00, tệ nhất 0.000 (5 run)
- CST (Entry 34): run segFAR > α = 0.00, tệ nhất 0.000 (5 run)
- **CMS-CPC/H+CSTF+G+NGRr (CST-F, đề xuất)**: run segFAR > α = 0.00, tệ nhất 0.000 (5 run)
- SH ∧ CST-F: run segFAR > α = 0.00, tệ nhất 0.000 (5 run)

### Xác nhận giữ ra của CST-J\* (5 dataset có lỗ, seed 3–5 × CosPlace / NetVLAD / MegaLoc (45 run)): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|
| SH | 0.847 / 0.019 / 0.050 / 4.6 | 0.756 / 0.000 / 0.000 / 3.6 | 0.828 / 0.000 / 0.000 / 9.5 | 0.710 / 0.005 / 0.018 / 26.8 | 0.538 / 0.000 / 0.002 / 35.1 |
| SH ∧ CST | 0.845 / 0.010 / 0.023 / 4.4 | 0.756 / 0.000 / 0.000 / 3.6 | 0.827 / 0.000 / 0.000 / 9.5 | 0.710 / 0.005 / 0.018 / 26.8 | 0.523 / 0.000 / 0.002 / 35.8 |
| CST-F | 0.671 / 0.001 / 0.005 / 3.1 | 0.733 / 0.000 / 0.000 / 3.7 | 0.810 / 0.000 / 0.003 / 9.5 | 0.693 / 0.003 / 0.010 / 28.8 | 0.496 / 0.000 / 0.000 / 38.3 |
| CST-J | 0.707 / 0.065 / 0.125 / 5.9 | 0.783 / 0.010 / 0.026 / 3.7 | 0.836 / 0.031 / 0.063 / 10.8 | 0.741 / 0.037 / 0.091 / 42.6 | 0.573 / 0.045 / 0.169 / 32.4 |
| SH ∧ CST-J | 0.680 / 0.016 / 0.042 / 3.9 | 0.756 / 0.000 / 0.000 / 3.6 | 0.817 / 0.000 / 0.000 / 9.4 | 0.708 / 0.005 / 0.018 / 26.7 | 0.535 / 0.000 / 0.002 / 35.2 |
| CST-J\* | 0.874 / 0.068 / 0.135 / 6.3 | 0.783 / 0.010 / 0.026 / 3.7 | 0.847 / 0.031 / 0.063 / 10.8 | 0.742 / 0.038 / 0.096 / 42.7 | 0.575 / 0.045 / 0.169 / 32.4 |
| **SH ∧ CST-J\*** | 0.847 / 0.019 / 0.050 / 4.6 | 0.756 / 0.000 / 0.000 / 3.6 | 0.828 / 0.000 / 0.000 / 9.5 | 0.710 / 0.005 / 0.018 / 26.8 | 0.538 / 0.000 / 0.002 / 35.2 |

- H36h: SH ∧ CST-J\* recall trong 0.01 của SH trên 5/5, sai số trong 1 m trên 5/5, segFAR ≤ 0.05 trên 5/5; CST-J\* một mình segFAR ≤ 0.05 trên 4/5

### Xác nhận giữ ra của CST-J\* (Oxford, seed 5–9 × CosPlace / NetVLAD / MegaLoc (15 run)): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | Oxford RobotCar |
|---|---|
| SH | 0.720 / 0.002 / 0.004 / 21.1 |
| SH ∧ CST | 0.710 / 0.002 / 0.004 / 21.2 |
| CST-F | 0.538 / 0.000 / 0.001 / 23.6 |
| CST-J | 0.739 / 0.025 / 0.043 / 21.3 |
| SH ∧ CST-J | 0.719 / 0.002 / 0.004 / 21.1 |
| CST-J\* | 0.740 / 0.025 / 0.043 / 21.3 |
| **SH ∧ CST-J\*** | 0.719 / 0.002 / 0.004 / 21.1 |

- H36h: SH ∧ CST-J\* recall trong 0.01 của SH trên 1/1, sai số trong 1 m trên 1/1, segFAR ≤ 0.05 trên 1/1; CST-J\* một mình segFAR ≤ 0.05 trên 1/1

### Cửa sổ niềm tin N = 40 so với N = 20 (seed 1–9, cùng run): recall / segFAR TB / sai số (m)

| Luật | N | Boreas | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| CMS-CPC/H+SH+G+NGRr | 20 | 0.818 / 0.007 / 4.1 | 0.907 / 0.013 / 3.7 | 0.840 / 0.000 / 4.8 | 0.857 / 0.000 / 9.0 | 0.655 / 0.006 / 29.1 | 0.553 / 0.000 / 23.5 |
| CMS-CPC/H+SH+G+NGRr | 40 | 0.820 / 0.008 / 4.0 | 0.904 / 0.011 / 3.8 | 0.852 / 0.000 / 4.9 | 0.861 / 0.000 / 9.0 | 0.659 / 0.008 / 29.8 | 0.622 / 0.000 / 22.1 |
| CMS-CPCW/H+SH+NGRr | 20 | 0.816 / 0.007 / 9.3 | 0.911 / 0.008 / 3.5 | 0.843 / 0.000 / 5.0 | 0.856 / 0.000 / 9.0 | 0.658 / 0.006 / 30.3 | 0.518 / 0.000 / 25.9 |
| CMS-CPCW/H+SH+NGRr | 40 | 0.818 / 0.008 / 7.1 | 0.914 / 0.011 / 3.8 | 0.852 / 0.001 / 5.1 | 0.862 / 0.000 / 8.9 | 0.663 / 0.008 / 29.3 | 0.597 / 0.000 / 22.7 |

- H36f: N = 40 segFAR ≤ 0.05 trên 6/6 (cần 6/6); recall ≥ N = 20 trên 5/6 (cần ≥ 5/6): Boreas +0.002, CMU -0.003, Nordland +0.012, 4S office +0.004, 4S old town +0.004, 4S countryside +0.069

### So sánh trực tiếp với SafeVPR'26 trên St Lucia (thước đo của SafeVPR: FDR của tập được chấp nhận, TPR; mỗi lượt truy vấn là một điều kiện giữ ra)

St Lucia, CosPlace, 10 m frames, map 100909_0845, 5 query traversals x 5 hole layouts (30 % map blocks removed) = 25 held-out conditions; SafeVPR'26 calibrated with labels on the other 4 traversals (Mondrian LTT, B = 5, M = 5, delta = 0.05), our rules label-free; FDR = wrong accepted / accepted (tolerance 25 m), TPR = correct accepted / correct candidates, recall = correct accepted / all query frames

| Giao thức | Phương pháp | α | hợp lệ (FDR ≤ α) | FDR TB | TPR TB | recall TB | nhãn |
|---|---|---|---|---|---|---|---|
| 30 % lỗ | SafeVPR'26 (MNN DINOv2-B/14, Mondrian LTT, labels) | 0.05 | 25/25 | 0.0083 | 0.655 | 0.462 | calibration traversals |
| 30 % lỗ | SafeVPR'26 (MNN DINOv2-B/14, Mondrian LTT, labels) | 0.1 | 25/25 | 0.0198 | 0.795 | 0.557 | calibration traversals |
| 30 % lỗ | CMS-CPC/H+SH+G+NGRr | – | 25/25 | 0.0017 | 0.821 | 0.592 | none |
| 30 % lỗ | CMS-CPC/H+SH+CSTJs+G+NGRr | – | 25/25 | 0.0017 | 0.818 | 0.590 | none |
| 30 % lỗ | CMS-CPC/H+CSTJs+G+NGRr | – | 25/25 | 0.0065 | 0.819 | 0.591 | none |
| 30 % lỗ | CMS-CPC/H+CSTF+G+NGRr | – | 25/25 | 0.0000 | 0.611 | 0.442 | none |
| 30 % lỗ | CPC-SC-T0.5+SH | – | 25/25 | 0.0108 | 0.928 | 0.669 | none |
| 30 % lỗ | CMS-CPCW/H+SH+NGRr | – | 25/25 | 0.0104 | 0.864 | 0.623 | none |
| không lỗ | SafeVPR'26 (MNN DINOv2-B/14, Mondrian LTT, labels) | 0.05 | 5/5 | 0.0001 | 1.000 | 0.994 | calibration traversals |
| không lỗ | SafeVPR'26 (MNN DINOv2-B/14, Mondrian LTT, labels) | 0.1 | 5/5 | 0.0001 | 1.000 | 0.994 | calibration traversals |
| không lỗ | CMS-CPC/H+SH+G+NGRr | – | 5/5 | 0.0000 | 0.999 | 0.999 | none |
| không lỗ | CMS-CPC/H+SH+CSTJs+G+NGRr | – | 5/5 | 0.0000 | 0.995 | 0.995 | none |
| không lỗ | CMS-CPC/H+CSTJs+G+NGRr | – | 5/5 | 0.0000 | 0.995 | 0.995 | none |
| không lỗ | CMS-CPC/H+CSTF+G+NGRr | – | 5/5 | 0.0000 | 0.807 | 0.807 | none |
| không lỗ | CPC-SC-T0.5+SH | – | 5/5 | 0.0000 | 1.000 | 0.999 | none |



## 6. Thảo luận, hạn chế, việc tiếp theo

- **Điều phẫu thuật tiến chứng minh được:** null của *chính quỹ đạo ma của hệ thống* (một can thiệp tại lối thoát ảo, rồi để hệ thống tự lan
  truyền) làm phép thử hình dạng hợp lệ **một mình** ở mọi vị trí trong chuyến off-map — điều Mệnh đề 14 tuyên bố nhưng dữ liệu bác bỏ. Không
  còn hằng số dung sai chọn tay trong điều kiện hợp lệ; sai số điều hướng thấp nhất trong mọi luật trên Boreas, NCLT, CMU.
- **Giá và giới hạn:** (i) CST-F chặt khi residual của quỹ đạo đúng và ma chồng lấn (Oxford: frame 10 m, cửa sổ 75 m ~8 điểm; St Lucia) và ở
  đầu chuỗi (CMU: 130 chuỗi ngắn, cửa sổ < 1 excl không chứng nhận được) ⇒ H36d không đạt. (ii) CST-J (mô phỏng cả quyết định) giữ recall
  nhưng dùng bằng chứng hiện diện của phẫu thuật đầy đủ trong mô phỏng ⇒ xấp xỉ, vượt α trên CMU giữ ra. Hướng sửa: phẫu thuật tiến cả
  thống kê hiện diện (phép thử tuyến trên bản đồ tiến cho từng lần chạy ảo; ~20 × chi phí hiện tại) và null chính xác cho đầu chuỗi.
- **Sai lệch do tài nguyên:** không có token Kaggle ⇒ mọi thứ chạy trên 4 lõi CPU; Boreas 8/18 run, N = 40 chỉ CosPlace (Boreas seed 1–3),
  St Lucia chỉ CosPlace; verifier SafeVPR dùng DINOv2 ViT-B/14 (bài báo dùng ViT-L/14) và không biết đúng cặp lượt chạy St Lucia của họ.
  Mọi sai lệch ghi trước khi có kết quả tương ứng (`RESEARCH_LOG.md` Entry 36).
- **Khuyến nghị:** **CMS-CPC/H+CSTF+G+NGRr** (N = 40) khi cần bảo đảm theo đoạn có chứng nhận; **SH ∧ CST-J\*** khi ưu tiên recall
  (bằng SH, đạt tiêu chí Oxford; bảo đảm xấp xỉ). Novelty: mô phỏng phản thực **tiến** sự thất bại của chính hệ thống từ lối thoát ảo để hiệu
  chuẩn quyết định của nó — cần gate tài liệu (Gate 14) trước khi tuyên bố. Không tuyên bố đạt A\* hay vượt SOTA ngoài các so sánh trong báo cáo.
