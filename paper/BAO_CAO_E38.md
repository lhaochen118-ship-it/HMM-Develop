# Báo cáo vòng 12 (Entry 38): lỗ ảo hình khối cho mép lỗ thật — và tăng tốc phép mô phỏng tiến trên GPU

*Branch `hmm-navigation-5`, 2026-11-03. Nhật ký: `RESEARCH_LOG.md` Entry 38 (đăng ký trước — commit trước mọi kết quả — kết quả, kết luận).
Lý thuyết: `paper/cms_theory.md` §4h (Mệnh đề 20). Code: `analysis/cms_fwd.py` (BlockGrid, BlockHoleMask, `fwd_null(shape="block")`,
`FwdStats.multi_stats`, MultiMask), `cms.py` (CST-JSB, CST-JSU), `e37_eval.py --block / --corr`, `oc_curves.py --fwdb`, `mps_probe.py`;
`automation/e37_wave.py --e38`; bảng `paper/build_e38_report.py` → `paper/e38_tables.md`. Nhãn chỉ dùng để đánh giá.*

## 1. Câu hỏi và kết luận ngắn

Entry 37: luật CST-JS hợp lệ ở mức segFAR (kể cả tập giữ ra), nhưng **đoạn MÉP của lỗ thật** bị báo sai quá ngưỡng trên Boreas (0.084) và old town
(0.109). Giả thuyết: lỗ thật là ô vuông của bản đồ (mất cả phố song song/cắt ngang), lỗ ảo là ống hẹp ρ dọc đường tin ⇒ thêm **họ lỗ ảo hình khối**.

| Giả thuyết (đăng ký trước) | Kết quả |
|---|---|
| H38a — CST-JSU hợp lệ (segFAR ≤ 0.05) | **Đạt:** 6/6 tập giữ ra mới (seed 3–5, 99 run), 7/7 tập E37, Oxford 0.021 |
| H38b — mọi lớp vị trí ≤ 0.07 | **Không đạt:** 4/7 (tập E37), 4/6 (giữ ra mới). Lỗ khối gần như không đổi tỷ lệ ở mép (Boreas 0.084 → 0.076, old town 0.109 → 0.106) |
| H38c — recall trong 0.03 của SH | **Đạt:** 6/6; +0.167 so với CST-F trên CMU |
| H38d — sai số điều hướng trong 1 m của SH | **Không đạt:** 4/6 (old town +12.8 m, Boreas +1.9 m) |
| H38e — Oxford | **Đạt:** hợp lệ, recall 0.728 vs SH 0.719 |

**Kết luận:** hình dạng lỗ **không** phải nguyên nhân chính của phần dư ở mép (giả thuyết cơ chế của Entry 37 bị bác bỏ với cách dựng này). Theo luật
quyết định, CST-JSU không được đề cử; khuyến nghị của Entry 37 giữ nguyên (SH ∧ CST-JS thực dụng, CST-F chứng nhận). **Quan sát phụ (luật thứ cấp
đã đăng ký):** bản nhân quả **CST-JSU [both]** đạt ≤ 0.07 ở mọi lớp vị trí trên **6/6** tập giữ ra mới (mép Boreas 0.055, old town 0.046), giá
recall −0.02 đến −0.034 so với SH — ứng viên để xác nhận trên các bố cục lỗ mới (đăng ký trước riêng).

## 2. Phương pháp

Mỗi lần chạy ảo có một lưới vuông ngẫu nhiên riêng (cạnh = block của cấu hình × {½, 1, 2}, xoay U[0, π/2), dịch U[0, 1) ô); lối thoát xoá **cả các ô**
chứa nơi trong bán kính ρ của đường tin sau lối thoát (rồi cắt Voronoi với đường trước lối thoát); khởi đầu xoá các ô quanh đường tin của nó.
Mọi phần còn lại như CST-JS. **CST-JSU** báo khi qua ngưỡng của cả hai họ: theo Mệnh đề 20, bảo đảm giữ nguyên nếu lỗ thật giống **một** trong hai họ.
Kiểm: numpy = torch (mọi khoá), đường `--corr` (dùng null hành lang đã công bố) cho kết quả trùng tính lại.

## 3. Kết quả

### Tập giữ ra MỚI (seed 3–5; 99 run, chưa từng dùng cho luật Entry 37/38): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | Boreas | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.778 / 0.003 / 0.017 / 5.0 | 0.850 / 0.011 / 0.030 / 4.1 | 0.771 / 0.000 / 0.000 / 3.5 | 0.818 / 0.000 / 0.003 / 9.7 | 0.716 / 0.005 / 0.018 / 24.8 | 0.509 / 0.001 / 0.010 / 36.5 |
| CST-F (Entry 36, chứng nhận) | 0.768 / 0.001 / 0.009 / 3.4 | 0.665 / 0.000 / 0.000 / 3.0 | 0.746 / 0.000 / 0.000 / 3.6 | 0.796 / 0.000 / 0.003 / 9.8 | 0.693 / 0.001 / 0.010 / 26.4 | 0.474 / 0.000 / 0.000 / 39.6 |
| CST-JS (Entry 37, lỗ ảo hành lang) | 0.781 / 0.008 / 0.019 / 6.9 | 0.838 / 0.025 / 0.053 / 4.0 | 0.785 / 0.002 / 0.010 / 3.5 | 0.830 / 0.010 / 0.058 / 9.9 | 0.721 / 0.011 / 0.036 / 38.9 | 0.520 / 0.005 / 0.019 / 35.1 |
| SH ∧ CST-JS (Entry 37, thực dụng) | 0.778 / 0.003 / 0.016 / 4.1 | 0.833 / 0.009 / 0.022 / 3.7 | 0.771 / 0.000 / 0.000 / 3.5 | 0.816 / 0.000 / 0.003 / 9.7 | 0.714 / 0.003 / 0.015 / 24.8 | 0.507 / 0.001 / 0.010 / 37.0 |
| CST-JSB (lỗ ảo khối) | 0.782 / 0.008 / 0.019 / 7.1 | 0.841 / 0.026 / 0.052 / 4.1 | 0.784 / 0.002 / 0.010 / 3.6 | 0.821 / 0.007 / 0.036 / 9.7 | 0.720 / 0.012 / 0.036 / 41.8 | 0.521 / 0.006 / 0.016 / 34.9 |
| **CST-JSU: hành lang ∧ khối (Entry 38, luật chính)** | 0.781 / 0.008 / 0.019 / 6.9 | 0.832 / 0.023 / 0.050 / 3.9 | 0.784 / 0.002 / 0.010 / 3.6 | 0.820 / 0.006 / 0.036 / 9.7 | 0.719 / 0.011 / 0.036 / 37.6 | 0.519 / 0.005 / 0.014 / 35.5 |
| SH ∧ CST-JSU | 0.778 / 0.003 / 0.016 / 4.1 | 0.828 / 0.009 / 0.020 / 3.6 | 0.771 / 0.000 / 0.000 / 3.5 | 0.813 / 0.000 / 0.003 / 9.7 | 0.714 / 0.003 / 0.015 / 24.8 | 0.507 / 0.001 / 0.010 / 37.0 |
| CST-JSU [both] (nhân quả) | 0.756 / 0.006 / 0.018 / 6.3 | 0.819 / 0.017 / 0.033 / 3.7 | 0.748 / 0.001 / 0.008 / 4.5 | 0.790 / 0.001 / 0.008 / 10.0 | 0.701 / 0.003 / 0.015 / 25.6 | 0.475 / 0.002 / 0.007 / 39.6 |
| CST-JSB [both] | 0.757 / 0.007 / 0.018 / 6.4 | 0.828 / 0.020 / 0.037 / 3.9 | 0.748 / 0.001 / 0.008 / 4.5 | 0.791 / 0.003 / 0.025 / 10.1 | 0.702 / 0.004 / 0.015 / 25.5 | 0.477 / 0.003 / 0.016 / 38.7 |

| Luật | run > α | tệ nhất | số run |
|---|---|---|---|
| SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay) | 0.000 | 0.030 | 99 |
| CST-F (Entry 36, chứng nhận) | 0.000 | 0.010 | 99 |
| CST-JS (Entry 37, lỗ ảo hành lang) | 0.020 | 0.058 | 99 |
| SH ∧ CST-JS (Entry 37, thực dụng) | 0.000 | 0.022 | 99 |
| CST-JSB (lỗ ảo khối) | 0.010 | 0.052 | 99 |
| **CST-JSU: hành lang ∧ khối (Entry 38, luật chính)** | 0.000 | 0.050 | 99 |
| SH ∧ CST-JSU | 0.000 | 0.020 | 99 |
| CST-JSU [both] (nhân quả) | 0.000 | 0.033 | 99 |
| CST-JSB [both] | 0.000 | 0.037 | 99 |

### Tập của Entry 37 (seed 0–2 + 6–9, NCLT 0; 258 run; nơi thất bại ở mép được phát hiện): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.774 / 0.002 / 0.022 / 4.3 | 0.612 / 0.002 / 0.007 / 4.3 | 0.811 / 0.007 / 0.038 / 3.8 | 0.763 / 0.000 / 0.000 / 6.5 | 0.792 / 0.000 / 0.006 / 9.7 | 0.697 / 0.006 / 0.051 / 26.6 | 0.483 / 0.000 / 0.006 / 33.4 |
| CST-F (Entry 36, chứng nhận) | 0.762 / 0.001 / 0.013 / 3.4 | 0.581 / 0.000 / 0.000 / 3.3 | 0.642 / 0.000 / 0.004 / 3.1 | 0.733 / 0.000 / 0.000 / 6.6 | 0.768 / 0.000 / 0.006 / 9.7 | 0.663 / 0.002 / 0.023 / 27.7 | 0.447 / 0.000 / 0.000 / 38.1 |
| CST-JS (Entry 37, lỗ ảo hành lang) | 0.779 / 0.012 / 0.074 / 9.2 | 0.632 / 0.003 / 0.010 / 4.7 | 0.790 / 0.016 / 0.051 / 3.6 | 0.776 / 0.001 / 0.005 / 6.6 | 0.804 / 0.007 / 0.041 / 9.7 | 0.706 / 0.012 / 0.074 / 40.1 | 0.493 / 0.004 / 0.024 / 33.1 |
| SH ∧ CST-JS (Entry 37, thực dụng) | 0.774 / 0.002 / 0.021 / 3.8 | 0.612 / 0.002 / 0.007 / 4.3 | 0.782 / 0.005 / 0.034 / 3.4 | 0.763 / 0.000 / 0.000 / 6.5 | 0.790 / 0.000 / 0.006 / 9.7 | 0.696 / 0.004 / 0.023 / 26.7 | 0.481 / 0.000 / 0.006 / 34.7 |
| CST-JSB (lỗ ảo khối) | 0.779 / 0.012 / 0.068 / 8.3 | 0.632 / 0.003 / 0.010 / 4.7 | 0.804 / 0.014 / 0.051 / 3.7 | 0.775 / 0.001 / 0.005 / 6.5 | 0.799 / 0.006 / 0.027 / 9.7 | 0.706 / 0.013 / 0.085 / 37.6 | 0.496 / 0.004 / 0.024 / 31.5 |
| **CST-JSU: hành lang ∧ khối (Entry 38, luật chính)** | 0.778 / 0.011 / 0.063 / 8.1 | 0.632 / 0.003 / 0.010 / 4.7 | 0.784 / 0.013 / 0.051 / 3.5 | 0.775 / 0.001 / 0.005 / 6.5 | 0.798 / 0.006 / 0.027 / 9.7 | 0.705 / 0.012 / 0.085 / 37.4 | 0.492 / 0.003 / 0.024 / 33.6 |
| SH ∧ CST-JSU | 0.774 / 0.002 / 0.021 / 3.8 | 0.612 / 0.002 / 0.007 / 4.3 | 0.778 / 0.005 / 0.034 / 3.4 | 0.763 / 0.000 / 0.000 / 6.5 | 0.788 / 0.000 / 0.006 / 9.7 | 0.696 / 0.004 / 0.023 / 26.7 | 0.481 / 0.000 / 0.006 / 34.6 |
| CST-JSU [both] (nhân quả) | 0.752 / 0.009 / 0.057 / 7.0 | 0.622 / 0.001 / 0.007 / 4.7 | 0.768 / 0.009 / 0.038 / 3.4 | 0.744 / 0.001 / 0.003 / 7.1 | 0.768 / 0.002 / 0.009 / 9.9 | 0.690 / 0.004 / 0.023 / 27.2 | 0.440 / 0.002 / 0.014 / 38.6 |
| CST-JSB [both] | 0.753 / 0.009 / 0.060 / 7.1 | 0.622 / 0.001 / 0.007 / 4.6 | 0.787 / 0.010 / 0.038 / 3.5 | 0.744 / 0.001 / 0.003 / 7.1 | 0.768 / 0.002 / 0.009 / 9.9 | 0.691 / 0.005 / 0.034 / 27.3 | 0.449 / 0.002 / 0.014 / 36.8 |

| Luật | run > α | tệ nhất | số run |
|---|---|---|---|
| SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay) | 0.004 | 0.051 | 258 |
| CST-F (Entry 36, chứng nhận) | 0.000 | 0.023 | 258 |
| CST-JS (Entry 37, lỗ ảo hành lang) | 0.019 | 0.074 | 258 |
| SH ∧ CST-JS (Entry 37, thực dụng) | 0.000 | 0.034 | 258 |
| CST-JSB (lỗ ảo khối) | 0.019 | 0.085 | 258 |
| **CST-JSU: hành lang ∧ khối (Entry 38, luật chính)** | 0.016 | 0.085 | 258 |
| SH ∧ CST-JSU | 0.000 | 0.034 | 258 |
| CST-JSU [both] (nhân quả) | 0.004 | 0.057 | 258 |
| CST-JSB [both] | 0.004 | 0.060 | 258 |

### Oxford RobotCar (Entry 37 run, 45 run): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | Oxford RobotCar |
|---|---|
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.719 / 0.004 / 0.011 / 21.9 |
| CST-F (Entry 36, chứng nhận) | 0.537 / 0.001 / 0.003 / 24.0 |
| CST-JS (Entry 37, lỗ ảo hành lang) | 0.729 / 0.021 / 0.041 / 22.0 |
| SH ∧ CST-JS (Entry 37, thực dụng) | 0.716 / 0.004 / 0.011 / 22.0 |
| CST-JSB (lỗ ảo khối) | 0.730 / 0.021 / 0.040 / 21.9 |
| **CST-JSU: hành lang ∧ khối (Entry 38, luật chính)** | 0.728 / 0.021 / 0.040 / 22.0 |
| SH ∧ CST-JSU | 0.716 / 0.004 / 0.011 / 22.0 |
| CST-JSU [both] (nhân quả) | 0.716 / 0.019 / 0.040 / 22.7 |
| CST-JSB [both] | 0.717 / 0.019 / 0.040 / 22.7 |

### Kiểm toán theo vị trí, tập E37: tỷ lệ đoạn off-map THẬT có báo (start / mép / sâu; nhãn chỉ để đánh giá)

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| số đoạn | 3234/3114/70122 | 558/156/1122 | 17742/0/0 | 420/576/15294 | 84/636/10278 | 1644/432/8118 | 720/504/9912 |
| CST-JSU | 0.031 / 0.076 / 0.007 | 0.005 / 0.006 / 0.001 | 0.012 / – / – | 0.000 / 0.024 / 0.000 | 0.119 / 0.039 / 0.003 | 0.012 / 0.106 / 0.006 | 0.007 / 0.034 / 0.001 |
| CST-JSB | 0.033 / 0.083 / 0.008 | 0.005 / 0.006 / 0.001 | 0.013 / – / – | 0.000 / 0.024 / 0.000 | 0.119 / 0.042 / 0.004 | 0.016 / 0.109 / 0.006 | 0.007 / 0.034 / 0.001 |
| SH ∧ CST-JSU | 0.009 / 0.001 / 0.002 | 0.004 / 0.006 / 0.000 | 0.005 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.001 / 0.060 / 0.001 | 0.000 / 0.002 / 0.000 |
| CST-JSU [both] | 0.026 / 0.070 / 0.005 | 0.004 / 0.000 / 0.000 | 0.009 / – / – | 0.000 / 0.017 / 0.000 | 0.119 / 0.008 / 0.000 | 0.003 / 0.067 / 0.001 | 0.001 / 0.020 / 0.000 |
| CST-JS | 0.034 / 0.084 / 0.008 | 0.005 / 0.006 / 0.001 | 0.016 / – / – | 0.000 / 0.026 / 0.000 | 0.119 / 0.042 / 0.004 | 0.014 / 0.109 / 0.006 | 0.007 / 0.046 / 0.002 |
| SH ∧ CST-JS | 0.009 / 0.001 / 0.002 | 0.004 / 0.006 / 0.000 | 0.005 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.002 / 0.060 / 0.001 | 0.000 / 0.002 / 0.000 |
| CST-F | 0.000 / 0.001 / 0.001 | 0.000 / 0.000 / 0.000 | 0.000 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.000 / 0.032 / 0.001 | 0.000 / 0.000 / 0.000 |
| SH | 0.012 / 0.001 / 0.002 | 0.004 / 0.006 / 0.000 | 0.006 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.006 / 0.069 / 0.001 | 0.000 / 0.002 / 0.000 |

- ≤ 0.07 ở mọi lớp có ≥ 50 đoạn: CST-JSU 4/7 (cần ≥ 6/7), CST-JSB 4/7, CST-JS 4/7

### Kiểm toán theo vị trí, tập giữ ra mới: tỷ lệ đoạn off-map THẬT có báo (start / mép / sâu; nhãn chỉ để đánh giá)

| Luật | Boreas | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| số đoạn | 1398/996/24666 | 4401/0/0 | 216/270/6192 | 420/210/5382 | 552/216/2952 | 504/216/5472 |
| CST-JSU | 0.029 / 0.065 / 0.005 | 0.025 / – / – | 0.000 / 0.030 / 0.001 | 0.002 / 0.100 / 0.004 | 0.009 / 0.093 / 0.005 | 0.002 / 0.051 / 0.003 |
| CST-JSB | 0.032 / 0.072 / 0.005 | 0.029 / – / – | 0.000 / 0.030 / 0.001 | 0.002 / 0.110 / 0.004 | 0.011 / 0.093 / 0.006 | 0.002 / 0.060 / 0.003 |
| SH ∧ CST-JSU | 0.009 / 0.000 / 0.003 | 0.010 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.005 / 0.042 / 0.000 | 0.002 / 0.000 / 0.001 |
| CST-JSU [both] | 0.028 / 0.055 / 0.004 | 0.019 / – / – | 0.000 / 0.015 / 0.001 | 0.000 / 0.029 / 0.000 | 0.000 / 0.046 / 0.000 | 0.000 / 0.019 / 0.002 |
| CST-JS | 0.031 / 0.065 / 0.005 | 0.027 / – / – | 0.000 / 0.030 / 0.001 | 0.005 / 0.110 / 0.007 | 0.009 / 0.093 / 0.005 | 0.002 / 0.060 / 0.003 |
| SH ∧ CST-JS | 0.009 / 0.000 / 0.003 | 0.010 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.005 / 0.042 / 0.000 | 0.002 / 0.000 / 0.001 |
| CST-F | 0.000 / 0.000 / 0.001 | 0.000 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.005 / 0.000 | 0.000 / 0.023 / 0.000 | 0.000 / 0.000 / 0.000 |
| SH | 0.011 / 0.000 / 0.003 | 0.013 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.007 / 0.060 / 0.000 | 0.002 / 0.000 / 0.001 |

- ≤ 0.07 ở mọi lớp có ≥ 50 đoạn: CST-JSU 4/6 (cần ≥ 5/6), CST-JSB 3/6, CST-JS 4/6

**Kiểm giả thuyết (đăng ký trước, Entry 38):**

- H38a: CST-JSU segFAR TB ≤ 0.05 trên 6/6 (giữ ra mới) và 7/7 (tập E37), Oxford 0.021: Boreas 0.008, CMU 0.023, Nordland 0.002, 4S office 0.006, 4S old town 0.011, 4S countryside 0.005
- H38c: recall CST-JSU − SH ≥ −0.03 trên 6/6 (cần ≥ 4/6): Boreas +0.003, CMU -0.017, Nordland +0.013, 4S office +0.001, 4S old town +0.003, 4S countryside +0.010; CMU CST-JSU − CST-F = +0.167 (cần ≥ +0.05)
- H38d: sai số CST-JSU − SH ≤ 1 m trên 4/6 (cần ≥ 5/6): Boreas +1.9, CMU -0.2, Nordland +0.0, 4S office -0.0, 4S old town +12.8, 4S countryside -1.0; old town tập E37: CST-JSU +10.8 m (CST-JS +13.5)
- H38e: Oxford CST-JSU segFAR 0.021, recall 0.728 vs SH 0.719
- H38b (Kiểm toán theo vị trí, tập E37): CST-JSU ≤ 0.07 ở mọi lớp ≥ 50 đoạn trên 4/7 (cần ≥ 6/7)
- H38b (Kiểm toán theo vị trí, tập giữ ra mới): CST-JSU ≤ 0.07 ở mọi lớp ≥ 50 đoạn trên 4/6 (cần ≥ 5/6)


## 4. Tối ưu tài nguyên (đo trên L4, cùng 48 job null tiến CMU, 46 song song)

| Cấu hình | ms / frame | so với cũ |
|---|---|---|
| Code cũ (mỗi lần chạy ảo một lời gọi GPU nhỏ, 12 tiến trình chia thời gian một GPU) | 35.5 | 1.00× |
| Code cũ + CUDA MPS | 27.6 | 1.29× (wall 1.34×) |
| **Gộp lô phép thử tuyến qua mọi lần chạy ảo của một chuỗi** (`FwdStats.multi_stats`) | **18.3** | **1.94×** |
| Gộp lô + MPS | 19.5 | — (MPS không thêm khi đã gộp lô) |

Đầu ra của bản gộp lô **trùng tuyệt đối** bản cũ (hai họ lỗ, numpy và torch). Lô 2 048 hàng dùng ~2 GB VRAM mỗi tiến trình (12 tiến trình trên 23 GB:
một số job hết VRAM) ⇒ mặc định 1 024 hàng, tự chia đôi khi hết bộ nhớ. Trước đây VRAM chỉ dùng ~11 %; với lô 1 024 hàng ước ~50 % (12 tiến trình × ~1 GB; chưa đo lại trên L4). **Hạn mức:** một phiên L4×4 tính
4 GPU-giờ mỗi giờ; mỗi acc 30 GPU-giờ/tuần (~7.5 giờ L4) — `nhatlong1103` đã hết trong vòng này. Phiên CPU (5/acc, 4 vCPU) không tốn hạn mức GPU:
đã dùng 12 phiên CPU cho các run nhỏ.

## 5. Việc tiếp theo

1. Xác nhận CST-JSU [both] trên **bố cục lỗ mới** (seed mới của bộ sinh lỗ: `nav_demo.py --cache` seed ≥ 10), đăng ký trước riêng.
2. Kiểm hai giải thích còn lại cho phần dư ở mép: hệ số 1/π của Mệnh đề 19 (đo π), và biên định nghĩa off_d (robot chỉ vừa qua 40 m).
3. Các đợt sau dùng code gộp lô (≈ 2× mỗi GPU-giờ) và phiên CPU cho run nhỏ.
