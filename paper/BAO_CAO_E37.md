# Báo cáo vòng 11 (Entry 37): phẫu thuật tiến cả BẰNG CHỨNG HIỆN DIỆN, null chính xác cho đầu chuỗi (CST-JS), N = 40 mọi descriptor, St Lucia 6 descriptor

*Branch `hmm-navigation-5`, 2026-11-03. Nhật ký: `RESEARCH_LOG.md` Entry 37 (đăng ký trước — commit trước mọi đánh giá — kết quả, kết luận).
Lý thuyết: `paper/cms_theory.md` §4g (Mệnh đề 19). Novelty: `LITERATURE_GATE.md` Gate 16. Code: `analysis/cms_fwd.py` (FwdStats, joint_crit,
eps_start_pos), `cms_torch.py` (GPU), `cms.py` (luật CST-JS), `e37_fwd.py`, `e37_eval.py`, `e37_audit.py`, `e37_safevpr.py`;
`automation/e37_wave.py`, `make_stlucia_kernel.py`; bảng `paper/build_e37_report.py` → `paper/e37_tables.md`. Nhãn chỉ dùng để đánh giá.*

## 1. Việc được giao và kết luận ngắn

| Việc | Kết quả |
|---|---|
| (1) Phẫu thuật tiến cả bằng chứng hiện diện, để hiệu chuẩn đầu-cuối thành bảo đảm thật | **Hợp lệ ở mức segFAR trên tập giữ ra** (seed 6–9, 144 run, kể cả CMU: 0.019; CST-J\* của vòng 10 vỡ ở đây: 0.053, run tệ nhất 0.237). Recall bằng luật SH chọn tay (trong 0.006, cao hơn trên 6/7), +0.15 so với CST-F trên CMU. **Nhưng kiểm toán theo vị trí không đạt**: đoạn MÉP của lỗ thật trên Boreas (0.084) và old town (0.109) vượt 0.07 ⇒ theo luật quyết định đăng ký trước, CST-JS **chưa** là bảo đảm theo từng vị trí. |
| (2) Null chính xác cho đầu chuỗi (vấn đề CMU) | **Giải quyết:** khởi đầu ảo đủ chân trời + ngưỡng theo vị trí kể từ đầu chuỗi + ngưỡng log-odds κ′ cho cửa sổ ngắn; đoạn đầu chuỗi CMU có báo 0.016, recall CMU 0.758 (CST-F 0.603, SH 0.764). |
| (3a) Boreas đủ 18 run | Xong (tập chính 18 run + giữ ra 24 run). |
| (3b) N = 40 cho mọi descriptor | **H37f đạt:** recall gộp N = 40 > N = 20 trên 6/6 dataset, segFAR ≤ 0.015 mọi (dataset, descriptor). |
| (3c) St Lucia 6 descriptor | **H37g đạt:** CST-JS hợp lệ 6/6 descriptor; so trực tiếp SafeVPR'26 với verifier ViT-L/14 như bài báo: ta (không nhãn) recall cao hơn ở 6/6 descriptor, FDR thấp hơn. |

**Khuyến nghị:** **SH ∧ CST-JS** là luật thực dụng (mọi lớp vị trí ≤ 0.07, recall trong 0.016 của SH); **CST-F** khi cần cận chứng nhận theo
đoạn; **CST-JS** một mình là luật không nhãn, không hằng số chọn tay, bảo đảm ở mức trung bình. N = 40 giữ làm cửa sổ niềm tin mặc định.

## 2. Phương pháp (tóm tắt; chi tiết `cms_theory.md` §4g)

**Vì sao CST-J vỡ trên CMU.** Ở CST-J (vòng 10), log-LR hiện diện của frame ảo lấy từ phẫu thuật ĐẦY ĐỦ tại chính frame đó, không phải từ
bản đồ của lần chạy ảo. Đo trên run thiết kế: hệ thống thật báo ở **22.4 %** đoạn ảo vị trí 0 khi mọi thống kê được tính lại trên bản đồ của
lần chạy ảo, so với 4.5 % với hiện diện phẫu thuật đầy đủ ⇒ CST-J đánh giá thấp rủi ro ở mép ~5 lần.

**Phẫu thuật tiến của hiện diện.** Với mỗi lần chạy ảo (lối thoát hoặc khởi đầu), mỗi frame của nó được tính lại **đúng phép tính của hệ
thống** (chi phí tuyến, winner, độ khác biệt) trên bản đồ đã xoá: giả thuyết = top-K của bản đồ còn lại, bảng tra cứu của mọi frame trong cửa
sổ trên cùng bản đồ, vệt anchor rời chunk khi vào vùng bị xoá; đổi sang log-LR bằng phép biến đổi của chính hệ thống; cổng dùng winner tiến.
Với bản đồ nguyên vẹn trùng cache công bố (100 % / 100 % / 99.8 %).

**Null đầu chuỗi.** Khởi đầu ảo đủ chân trời (hành lang ρ quanh cả đường tin off_d + 20 excl), chuỗi chạy lại từ niềm tin đều, mọi cửa sổ cắt
tại điểm bắt đầu. Ngưỡng theo vị trí kể từ đầu chuỗi (biết không cần nhãn); bin có cửa sổ ngắn chia ngân sách a/2 (dung sai) + a/2 (κ′).
**Mệnh đề 19:** dưới (S3-JF) và (S3-S), mọi đoạn off-map thật (mép, sâu, đầu chuỗi) bị báo với xác suất ≤ a(n_b+1)/(π_b n_b+1).

**Chi phí và hạ tầng.** ~45 lần chạy ảo sống mỗi frame; phép thử tuyến chạy trên GPU (torch float64) **trùng tuyệt đối với numpy trên L4**,
nhanh hơn 1.3–1.8× dưới tải đầy (46 job/phiên). Đợt Kaggle: 13 phiên L4 (4 GPU, 48 CPU mỗi phiên) trên 7 acc, 2 146 job, 41–46 phút; đánh giá
luật gộp ngay trong kernel (mỗi run là một đơn vị: mọi phần + job đánh giá). St Lucia: một phiên L4 làm cả trích 6 descriptor, patch ViT-L/14,
chuỗi E37 và SafeVPR'26.

## 3. Kết quả

### Entry 37 — tập chính (seed 0–2, NCLT seed 0; 114 run, α = 0.05): recall / segFAR TB / tệ nhất / sai số điều hướng (m)

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.663 / 0.004 / 0.023 / 6.6 | 0.588 / 0.001 / 0.003 / 4.9 | 0.713 / 0.004 / 0.021 / 4.0 | 0.711 / 0.000 / 0.003 / 11.5 | 0.736 / 0.000 / 0.003 / 11.9 | 0.616 / 0.006 / 0.023 / 32.0 | 0.340 / 0.000 / 0.000 / 52.0 |
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.779 / 0.004 / 0.022 / 4.5 | 0.612 / 0.002 / 0.007 / 4.3 | 0.764 / 0.003 / 0.014 / 3.9 | 0.752 / 0.000 / 0.000 / 6.9 | 0.795 / 0.000 / 0.006 / 10.1 | 0.687 / 0.003 / 0.010 / 27.5 | 0.513 / 0.001 / 0.006 / 33.9 |
| SH ∧ CST (Entry 35) | 0.778 / 0.004 / 0.022 / 4.5 | 0.608 / 0.002 / 0.007 / 4.3 | 0.762 / 0.003 / 0.014 / 3.9 | 0.752 / 0.000 / 0.000 / 6.9 | 0.792 / 0.000 / 0.006 / 10.2 | 0.686 / 0.003 / 0.010 / 27.5 | 0.499 / 0.000 / 0.000 / 34.8 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.764 / 0.002 / 0.013 / 3.5 | 0.581 / 0.000 / 0.000 / 3.3 | 0.603 / 0.000 / 0.003 / 3.1 | 0.726 / 0.000 / 0.000 / 7.0 | 0.771 / 0.000 / 0.006 / 10.2 | 0.637 / 0.002 / 0.008 / 28.5 | 0.477 / 0.000 / 0.000 / 39.2 |
| CST-J (Entry 36) | 0.795 / 0.033 / 0.100 / 9.8 | 0.640 / 0.005 / 0.010 / 5.5 | 0.644 / 0.027 / 0.095 / 3.6 | 0.781 / 0.006 / 0.013 / 6.9 | 0.811 / 0.027 / 0.068 / 10.8 | 0.717 / 0.022 / 0.063 / 39.4 | 0.541 / 0.021 / 0.051 / 32.5 |
| CST-J\* (Entry 36, thăm dò) | 0.800 / 0.033 / 0.100 / 9.9 | 0.640 / 0.005 / 0.010 / 5.5 | 0.792 / 0.027 / 0.095 / 4.2 | 0.781 / 0.006 / 0.013 / 6.9 | 0.821 / 0.027 / 0.068 / 10.8 | 0.720 / 0.022 / 0.063 / 39.4 | 0.544 / 0.021 / 0.051 / 32.5 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.778 / 0.004 / 0.021 / 4.5 | 0.612 / 0.002 / 0.007 / 4.3 | 0.764 / 0.003 / 0.014 / 3.9 | 0.752 / 0.000 / 0.000 / 6.9 | 0.794 / 0.000 / 0.006 / 10.1 | 0.686 / 0.003 / 0.010 / 27.5 | 0.511 / 0.001 / 0.006 / 35.4 |
| **CST-JS: CMS-CPC/ H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.782 / 0.009 / 0.027 / 6.8 | 0.632 / 0.003 / 0.010 / 4.7 | 0.758 / 0.011 / 0.050 / 3.6 | 0.767 / 0.001 / 0.005 / 7.3 | 0.807 / 0.007 / 0.041 / 10.2 | 0.696 / 0.010 / 0.029 / 42.0 | 0.523 / 0.003 / 0.018 / 34.5 |
| SH ∧ CST-JS | 0.778 / 0.004 / 0.021 / 4.0 | 0.612 / 0.002 / 0.007 / 4.3 | 0.748 / 0.003 / 0.014 / 3.5 | 0.752 / 0.000 / 0.000 / 6.9 | 0.793 / 0.000 / 0.006 / 10.1 | 0.685 / 0.003 / 0.010 / 27.5 | 0.509 / 0.001 / 0.006 / 36.2 |
| CST-JS [both] (nhân quả) | 0.756 / 0.007 / 0.027 / 5.2 | 0.622 / 0.001 / 0.007 / 4.7 | 0.737 / 0.008 / 0.039 / 3.4 | 0.736 / 0.001 / 0.003 / 7.4 | 0.772 / 0.002 / 0.009 / 10.4 | 0.678 / 0.004 / 0.011 / 28.6 | 0.457 / 0.000 / 0.004 / 42.5 |
| SH ∧ CST-JS [both] | 0.753 / 0.003 / 0.020 / 4.1 | 0.604 / 0.001 / 0.007 / 4.3 | 0.732 / 0.003 / 0.014 / 3.4 | 0.723 / 0.000 / 0.000 / 7.4 | 0.768 / 0.000 / 0.000 / 10.4 | 0.673 / 0.003 / 0.008 / 28.5 | 0.451 / 0.000 / 0.000 / 42.9 |
| CST-JS0 (cửa sổ ngắn không chứng nhận) | 0.777 / 0.009 / 0.027 / 6.8 | 0.632 / 0.003 / 0.010 / 4.7 | 0.625 / 0.010 / 0.044 / 3.3 | 0.767 / 0.001 / 0.005 / 7.3 | 0.798 / 0.007 / 0.041 / 10.2 | 0.693 / 0.010 / 0.029 / 42.0 | 0.521 / 0.003 / 0.018 / 34.5 |
| CST-JSL (hiện diện = phẫu thuật đầy đủ E36) | 0.800 / 0.033 / 0.100 / 9.9 | 0.640 / 0.005 / 0.010 / 5.5 | 0.784 / 0.027 / 0.095 / 3.9 | 0.781 / 0.006 / 0.013 / 6.9 | 0.821 / 0.027 / 0.068 / 10.8 | 0.720 / 0.022 / 0.063 / 39.4 | 0.544 / 0.021 / 0.051 / 32.5 |
| CST-JF0 (khởi đầu min theo bin) | 0.777 / 0.008 / 0.026 / 6.8 | 0.632 / 0.002 / 0.007 / 4.7 | 0.612 / 0.004 / 0.023 / 3.2 | 0.767 / 0.001 / 0.005 / 7.3 | 0.795 / 0.007 / 0.041 / 10.1 | 0.692 / 0.010 / 0.029 / 42.2 | 0.518 / 0.003 / 0.018 / 34.5 |
| CST-JS không +NGRr | 0.782 / 0.018 / 0.047 / 14.1 | 0.635 / 0.020 / 0.075 / 10.7 | 0.759 / 0.015 / 0.052 / 5.0 | 0.771 / 0.010 / 0.034 / 12.1 | 0.809 / 0.016 / 0.072 / 12.0 | 0.712 / 0.019 / 0.051 / 76.6 | 0.535 / 0.006 / 0.029 / 30.6 |

Tỷ lệ run có segFAR > α / segFAR tệ nhất:

| Luật | run > α | tệ nhất | số run |
|---|---|---|---|
| SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay) | 0.000 | 0.022 | 114 |
| SH ∧ CST (Entry 35) | 0.000 | 0.022 | 114 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.000 | 0.013 | 114 |
| CST-J (Entry 36) | 0.123 | 0.100 | 114 |
| CST-J\* (Entry 36, thăm dò) | 0.123 | 0.100 | 114 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.000 | 0.021 | 114 |
| **CST-JS: CMS-CPC/H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.009 | 0.050 | 114 |
| SH ∧ CST-JS | 0.000 | 0.021 | 114 |
| CST-JS [both] (nhân quả) | 0.000 | 0.039 | 114 |
| SH ∧ CST-JS [both] | 0.000 | 0.020 | 114 |

### Tập giữ ra (seed 6–9; 144 run, chưa từng dùng cho luật CST nào): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | Boreas | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.674 / 0.000 / 0.007 / 5.1 | 0.827 / 0.022 / 0.124 / 6.1 | 0.713 / 0.000 / 0.005 / 9.9 | 0.729 / 0.000 / 0.003 / 10.7 | 0.648 / 0.008 / 0.034 / 28.9 | 0.316 / 0.000 / 0.005 / 49.3 |
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.771 / 0.001 / 0.011 / 4.2 | 0.846 / 0.009 / 0.038 / 3.8 | 0.770 / 0.000 / 0.000 / 6.2 | 0.790 / 0.000 / 0.006 / 9.3 | 0.706 / 0.008 / 0.051 / 26.0 | 0.461 / 0.000 / 0.004 / 33.0 |
| SH ∧ CST (Entry 35) | 0.771 / 0.001 / 0.011 / 4.2 | 0.842 / 0.006 / 0.034 / 3.7 | 0.770 / 0.000 / 0.000 / 6.2 | 0.787 / 0.000 / 0.006 / 9.3 | 0.705 / 0.008 / 0.051 / 26.0 | 0.446 / 0.000 / 0.004 / 33.6 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.760 / 0.000 / 0.002 / 3.3 | 0.671 / 0.000 / 0.004 / 3.2 | 0.738 / 0.000 / 0.000 / 6.2 | 0.766 / 0.000 / 0.006 / 9.3 | 0.683 / 0.003 / 0.023 / 27.1 | 0.425 / 0.000 / 0.000 / 37.4 |
| CST-J (Entry 36) | 0.788 / 0.026 / 0.084 / 12.1 | 0.697 / 0.052 / 0.237 / 4.1 | 0.792 / 0.005 / 0.021 / 6.1 | 0.808 / 0.038 / 0.081 / 10.1 | 0.737 / 0.035 / 0.114 / 42.4 | 0.482 / 0.029 / 0.157 / 31.0 |
| CST-J\* (Entry 36, thăm dò) | 0.792 / 0.026 / 0.085 / 12.2 | 0.862 / 0.053 / 0.237 / 4.5 | 0.792 / 0.005 / 0.021 / 6.1 | 0.818 / 0.038 / 0.081 / 10.1 | 0.738 / 0.036 / 0.114 / 42.4 | 0.485 / 0.029 / 0.157 / 31.0 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.771 / 0.001 / 0.011 / 4.2 | 0.846 / 0.009 / 0.038 / 3.8 | 0.770 / 0.000 / 0.000 / 6.2 | 0.789 / 0.000 / 0.006 / 9.3 | 0.705 / 0.008 / 0.051 / 26.0 | 0.461 / 0.000 / 0.004 / 33.3 |
| **CST-JS: CMS-CPC/ H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.777 / 0.014 / 0.074 / 11.0 | 0.813 / 0.019 / 0.051 / 3.6 | 0.782 / 0.001 / 0.003 / 6.2 | 0.801 / 0.007 / 0.041 / 9.3 | 0.714 / 0.014 / 0.074 / 38.7 | 0.471 / 0.005 / 0.024 / 32.0 |
| SH ∧ CST-JS | 0.770 / 0.001 / 0.010 / 3.7 | 0.807 / 0.007 / 0.034 / 3.4 | 0.770 / 0.000 / 0.000 / 6.2 | 0.787 / 0.000 / 0.006 / 9.3 | 0.704 / 0.005 / 0.023 / 26.0 | 0.460 / 0.000 / 0.004 / 33.5 |
| CST-JS [both] (nhân quả) | 0.750 / 0.011 / 0.068 / 8.7 | 0.797 / 0.014 / 0.038 / 3.4 | 0.751 / 0.001 / 0.003 / 6.9 | 0.767 / 0.002 / 0.009 / 9.5 | 0.700 / 0.004 / 0.023 / 26.3 | 0.428 / 0.002 / 0.014 / 35.5 |
| SH ∧ CST-JS [both] | 0.745 / 0.001 / 0.010 / 4.1 | 0.793 / 0.007 / 0.034 / 3.3 | 0.740 / 0.000 / 0.000 / 6.9 | 0.762 / 0.000 / 0.000 / 9.5 | 0.695 / 0.004 / 0.023 / 26.5 | 0.420 / 0.000 / 0.000 / 36.3 |
| CST-JS0 (cửa sổ ngắn không chứng nhận) | 0.773 / 0.014 / 0.074 / 10.9 | 0.686 / 0.018 / 0.051 / 3.5 | 0.782 / 0.001 / 0.003 / 6.1 | 0.792 / 0.007 / 0.041 / 9.3 | 0.713 / 0.014 / 0.074 / 38.7 | 0.468 / 0.005 / 0.024 / 32.0 |
| CST-JSL (hiện diện = phẫu thuật đầy đủ E36) | 0.792 / 0.026 / 0.085 / 12.1 | 0.854 / 0.051 / 0.237 / 4.1 | 0.792 / 0.005 / 0.021 / 6.1 | 0.818 / 0.038 / 0.081 / 10.1 | 0.738 / 0.034 / 0.114 / 42.4 | 0.485 / 0.029 / 0.157 / 31.0 |
| CST-JF0 (khởi đầu min theo bin) | 0.773 / 0.014 / 0.074 / 10.9 | 0.662 / 0.002 / 0.013 / 3.2 | 0.782 / 0.001 / 0.003 / 6.1 | 0.789 / 0.007 / 0.041 / 9.3 | 0.712 / 0.014 / 0.074 / 38.6 | 0.467 / 0.005 / 0.024 / 31.7 |
| CST-JS không +NGRr | 0.777 / 0.026 / 0.136 / 18.9 | 0.813 / 0.037 / 0.093 / 4.7 | 0.784 / 0.009 / 0.032 / 12.5 | 0.802 / 0.015 / 0.072 / 10.9 | 0.726 / 0.026 / 0.125 / 66.2 | 0.482 / 0.010 / 0.055 / 32.9 |

| Luật | run > α | tệ nhất | số run |
|---|---|---|---|
| SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay) | 0.007 | 0.051 | 144 |
| SH ∧ CST (Entry 35) | 0.007 | 0.051 | 144 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.000 | 0.023 | 144 |
| CST-J (Entry 36) | 0.208 | 0.237 | 144 |
| CST-J\* (Entry 36, thăm dò) | 0.222 | 0.237 | 144 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.007 | 0.051 | 144 |
| **CST-JS: CMS-CPC/H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.028 | 0.074 | 144 |
| SH ∧ CST-JS | 0.000 | 0.034 | 144 |
| CST-JS [both] (nhân quả) | 0.007 | 0.068 | 144 |
| SH ∧ CST-JS [both] | 0.000 | 0.034 | 144 |

### Run thiết kế (CMU seed 3–5 × CosPlace / NetVLAD / MegaLoc; KHÔNG tính cho giả thuyết) (9 run): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | CMU |
|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.811 / 0.030 / 0.188 / 5.9 |
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.847 / 0.019 / 0.050 / 4.6 |
| SH ∧ CST (Entry 35) | 0.845 / 0.010 / 0.023 / 4.4 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.671 / 0.001 / 0.005 / 3.1 |
| CST-J (Entry 36) | 0.707 / 0.065 / 0.125 / 5.9 |
| CST-J\* (Entry 36, thăm dò) | 0.874 / 0.068 / 0.135 / 6.3 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.847 / 0.019 / 0.050 / 4.6 |
| **CST-JS: CMS-CPC/ H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.842 / 0.030 / 0.063 / 4.7 |
| SH ∧ CST-JS | 0.832 / 0.014 / 0.038 / 4.0 |
| CST-JS [both] (nhân quả) | 0.830 / 0.021 / 0.058 / 4.0 |
| SH ∧ CST-JS [both] | 0.825 / 0.013 / 0.038 / 3.8 |
| CST-JS0 (cửa sổ ngắn không chứng nhận) | 0.689 / 0.028 / 0.060 / 4.4 |
| CST-JSL (hiện diện = phẫu thuật đầy đủ E36) | 0.869 / 0.062 / 0.121 / 5.8 |
| CST-JF0 (khởi đầu min theo bin) | 0.684 / 0.021 / 0.060 / 4.0 |
| CST-JS không +NGRr | 0.842 / 0.044 / 0.130 / 7.7 |

- SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay): run segFAR > α = 0.11, tệ nhất 0.050 (9 run)
- CST-F (Entry 36, đề xuất có chứng nhận): run segFAR > α = 0.00, tệ nhất 0.005 (9 run)
- SH ∧ CST-J\* (Entry 36, thực dụng): run segFAR > α = 0.11, tệ nhất 0.050 (9 run)
- **CST-JS: CMS-CPC/H+CSTJS+G+NGRr (Entry 37, luật chính)**: run segFAR > α = 0.33, tệ nhất 0.063 (9 run)
- SH ∧ CST-JS: run segFAR > α = 0.00, tệ nhất 0.038 (9 run)

### Oxford RobotCar seed 0–4 × 6 descriptor (30 run): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | Oxford RobotCar |
|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.468 / 0.011 / 0.042 / 37.5 |
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.729 / 0.004 / 0.011 / 21.8 |
| SH ∧ CST (Entry 35) | 0.694 / 0.002 / 0.009 / 22.1 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.550 / 0.001 / 0.003 / 23.8 |
| CST-J (Entry 36) | 0.755 / 0.041 / 0.069 / 22.2 |
| CST-J\* (Entry 36, thăm dò) | 0.756 / 0.041 / 0.069 / 22.2 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.729 / 0.004 / 0.011 / 21.8 |
| **CST-JS: CMS-CPC/ H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.738 / 0.023 / 0.041 / 21.9 |
| SH ∧ CST-JS | 0.725 / 0.004 / 0.011 / 21.9 |
| CST-JS [both] (nhân quả) | 0.725 / 0.021 / 0.040 / 22.8 |
| SH ∧ CST-JS [both] | 0.714 / 0.003 / 0.010 / 22.8 |
| CST-JS0 (cửa sổ ngắn không chứng nhận) | 0.738 / 0.023 / 0.041 / 21.9 |
| CST-JSL (hiện diện = phẫu thuật đầy đủ E36) | 0.756 / 0.041 / 0.069 / 22.2 |
| CST-JF0 (khởi đầu min theo bin) | 0.738 / 0.023 / 0.041 / 21.9 |
| CST-JS không +NGRr | 0.743 / 0.030 / 0.062 / 25.4 |

- SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay): run segFAR > α = 0.00, tệ nhất 0.011 (30 run)
- CST-F (Entry 36, đề xuất có chứng nhận): run segFAR > α = 0.00, tệ nhất 0.003 (30 run)
- SH ∧ CST-J\* (Entry 36, thực dụng): run segFAR > α = 0.00, tệ nhất 0.011 (30 run)
- **CST-JS: CMS-CPC/H+CSTJS+G+NGRr (Entry 37, luật chính)**: run segFAR > α = 0.00, tệ nhất 0.041 (30 run)
- SH ∧ CST-JS: run segFAR > α = 0.00, tệ nhất 0.011 (30 run)

### Oxford RobotCar giữ ra: seed 5–9 × SALAD / MixVPR / DINOv2 (15 run): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | Oxford RobotCar |
|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.152 / 0.004 / 0.036 / 50.0 |
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.698 / 0.003 / 0.009 / 22.0 |
| SH ∧ CST (Entry 35) | 0.664 / 0.002 / 0.005 / 22.2 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.511 / 0.001 / 0.003 / 24.3 |
| CST-J (Entry 36) | 0.727 / 0.038 / 0.072 / 22.7 |
| CST-J\* (Entry 36, thăm dò) | 0.727 / 0.038 / 0.072 / 22.7 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.698 / 0.003 / 0.009 / 22.0 |
| **CST-JS: CMS-CPC/ H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.711 / 0.019 / 0.031 / 22.1 |
| SH ∧ CST-JS | 0.697 / 0.003 / 0.009 / 22.1 |
| CST-JS [both] (nhân quả) | 0.698 / 0.017 / 0.029 / 22.6 |
| SH ∧ CST-JS [both] | 0.686 / 0.003 / 0.006 / 22.6 |
| CST-JS0 (cửa sổ ngắn không chứng nhận) | 0.711 / 0.019 / 0.031 / 22.1 |
| CST-JSL (hiện diện = phẫu thuật đầy đủ E36) | 0.727 / 0.038 / 0.072 / 22.7 |
| CST-JF0 (khởi đầu min theo bin) | 0.710 / 0.019 / 0.032 / 22.1 |
| CST-JS không +NGRr | 0.718 / 0.023 / 0.041 / 22.8 |

- SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay): run segFAR > α = 0.00, tệ nhất 0.009 (15 run)
- CST-F (Entry 36, đề xuất có chứng nhận): run segFAR > α = 0.00, tệ nhất 0.003 (15 run)
- SH ∧ CST-J\* (Entry 36, thực dụng): run segFAR > α = 0.00, tệ nhất 0.009 (15 run)
- **CST-JS: CMS-CPC/H+CSTJS+G+NGRr (Entry 37, luật chính)**: run segFAR > α = 0.00, tệ nhất 0.031 (15 run)
- SH ∧ CST-JS: run segFAR > α = 0.00, tệ nhất 0.009 (15 run)

### St Lucia (6 descriptor × seed 0–4; 30 % lỗ) (30 run): recall / segFAR TB / tệ nhất / sai số (m)

| Luật | St Lucia |
|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.835 / 0.024 / 0.056 / 25.1 |
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.761 / 0.001 / 0.006 / 25.5 |
| SH ∧ CST (Entry 35) | 0.760 / 0.000 / 0.006 / 25.7 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.513 / 0.000 / 0.000 / 30.6 |
| CST-J (Entry 36) | 0.763 / 0.059 / 0.300 / 25.6 |
| CST-J\* (Entry 36, thăm dò) | 0.763 / 0.059 / 0.300 / 25.6 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.759 / 0.001 / 0.006 / 25.5 |
| **CST-JS: CMS-CPC/ H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.763 / 0.021 / 0.073 / 25.6 |
| SH ∧ CST-JS | 0.761 / 0.001 / 0.006 / 25.5 |
| CST-JS [both] (nhân quả) | 0.748 / 0.017 / 0.073 / 26.8 |
| SH ∧ CST-JS [both] | 0.748 / 0.000 / 0.006 / 26.7 |
| CST-JS0 (cửa sổ ngắn không chứng nhận) | 0.762 / 0.021 / 0.073 / 25.6 |
| CST-JSL (hiện diện = phẫu thuật đầy đủ E36) | 0.765 / 0.059 / 0.300 / 25.6 |
| CST-JF0 (khởi đầu min theo bin) | 0.762 / 0.021 / 0.073 / 25.6 |
| CST-JS không +NGRr | 0.775 / 0.041 / 0.100 / 26.5 |

- SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay): run segFAR > α = 0.00, tệ nhất 0.006 (30 run)
- CST-F (Entry 36, đề xuất có chứng nhận): run segFAR > α = 0.00, tệ nhất 0.000 (30 run)
- SH ∧ CST-J\* (Entry 36, thực dụng): run segFAR > α = 0.00, tệ nhất 0.006 (30 run)
- **CST-JS: CMS-CPC/H+CSTJS+G+NGRr (Entry 37, luật chính)**: run segFAR > α = 0.03, tệ nhất 0.073 (30 run)
- SH ∧ CST-JS: run segFAR > α = 0.00, tệ nhất 0.006 (30 run)

### Kiểm toán theo vị trí (H37b): tỷ lệ đoạn off-map THẬT có báo, gộp mọi run main + giữ ra (start / mép / sâu; nhãn chỉ để đánh giá)

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| số đoạn (start / mép / sâu) | 3234/3114/70122 | 558/156/1122 | 17742/0/0 | 420/576/15294 | 84/636/10278 | 1644/432/8118 | 720/504/9912 |
| CST-JS | 0.034 / 0.084 / 0.008 | 0.005 / 0.006 / 0.001 | 0.016 / – / – | 0.000 / 0.026 / 0.000 | 0.119 / 0.042 / 0.004 | 0.014 / 0.109 / 0.006 | 0.007 / 0.046 / 0.002 |
| SH ∧ CST-JS | 0.009 / 0.001 / 0.002 | 0.004 / 0.006 / 0.000 | 0.005 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.002 / 0.060 / 0.001 | 0.000 / 0.002 / 0.000 |
| CST-JS [both] | 0.028 / 0.079 / 0.006 | 0.004 / 0.000 / 0.000 | 0.011 / – / – | 0.000 / 0.019 / 0.000 | 0.119 / 0.013 / 0.001 | 0.004 / 0.069 / 0.001 | 0.001 / 0.020 / 0.000 |
| CST-J\* | 0.086 / 0.152 / 0.021 | 0.005 / 0.006 / 0.004 | 0.039 / – / – | 0.000 / 0.134 / 0.001 | 0.286 / 0.245 / 0.017 | 0.046 / 0.178 / 0.016 | 0.018 / 0.220 / 0.013 |
| SH ∧ CST-J\* | 0.012 / 0.001 / 0.002 | 0.004 / 0.006 / 0.000 | 0.006 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.006 / 0.067 / 0.001 | 0.000 / 0.002 / 0.000 |
| CST-J | 0.083 / 0.152 / 0.021 | 0.005 / 0.006 / 0.004 | 0.038 / – / – | 0.000 / 0.134 / 0.001 | 0.286 / 0.245 / 0.017 | 0.043 / 0.178 / 0.016 | 0.018 / 0.220 / 0.013 |
| CST-F | 0.000 / 0.001 / 0.001 | 0.000 / 0.000 / 0.000 | 0.000 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.000 / 0.032 / 0.001 | 0.000 / 0.000 / 0.000 |
| SH | 0.012 / 0.001 / 0.002 | 0.004 / 0.006 / 0.000 | 0.006 / – / – | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 | 0.006 / 0.069 / 0.001 | 0.000 / 0.002 / 0.000 |

- H37b: CST-JS ≤ 0.07 ở mọi lớp có ≥ 50 đoạn trên 4/7 (cần ≥ 6/7); thấp hơn CST-J\* ở mép trên 5/7 (cần ≥ 5/7)

### Cửa sổ niềm tin N = 40 so với N = 20 (seed 1–9; luật SH CMS-CPC/H+SH+G+NGRr): recall N20 → N40 / segFAR N40

| Descriptor | Boreas | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|
| cosplace | 0.846 → 0.849 / 0.004 | nan → nan / nan | nan → nan / nan | nan → nan / nan | nan → nan / nan | nan → nan / nan |
| dinov2 | 0.476 → 0.521 / 0.001 | 0.658 → 0.696 / 0.008 | 0.586 → 0.615 / 0.000 | 0.548 → 0.587 / 0.001 | 0.429 → 0.458 / 0.004 | 0.107 → 0.120 / 0.002 |
| megaloc | 0.926 → 0.927 / 0.003 | 0.937 → 0.929 / 0.008 | 0.874 → 0.873 / 0.001 | 0.931 → 0.930 / 0.000 | 0.922 → 0.917 / 0.009 | 0.793 → 0.815 / 0.000 |
| mixvpr | 0.867 → 0.869 / 0.002 | 0.923 → 0.920 / 0.005 | 0.876 → 0.878 / 0.000 | 0.889 → 0.892 / 0.000 | 0.760 → 0.776 / 0.010 | 0.674 → 0.715 / 0.000 |
| netvlad | 0.603 → 0.630 / 0.000 | 0.653 → 0.673 / 0.004 | 0.542 → 0.565 / 0.000 | 0.632 → 0.648 / 0.000 | 0.521 → 0.535 / 0.000 | 0.200 → 0.213 / 0.000 |
| salad | 0.918 → 0.921 / 0.002 | 0.927 → 0.925 / 0.005 | 0.879 → 0.889 / 0.000 | 0.928 → 0.928 / 0.000 | 0.920 → 0.913 / 0.015 | 0.573 → 0.649 / 0.000 |
| **gộp** | 0.768 → 0.782 / 0.002 | 0.820 → 0.829 / 0.006 | 0.751 → 0.764 / 0.000 | 0.786 → 0.797 / 0.000 | 0.710 → 0.720 / 0.007 | 0.469 → 0.503 / 0.001 |

### So sánh trực tiếp với SafeVPR'26 trên St Lucia (verifier DINOv2 ViT-L/14 như bài báo; 30 % lỗ; FDR / TPR của tập được chấp nhận)

| Descriptor | Phương pháp | α | hợp lệ | FDR TB | TPR TB | recall TB | nhãn |
|---|---|---|---|---|---|---|---|
| cosplace | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.05 | 25/25 | 0.0094 | 0.733 | 0.514 | calibration traversals |
| cosplace | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.1 | 25/25 | 0.0163 | 0.827 | 0.580 | calibration traversals |
| cosplace | CMS-CPC/H+SH+G+NGRr | – | 25/25 | 0.0018 | 0.820 | 0.591 | none |
| cosplace | CMS-CPC/H+CSTJS+G+NGRr | – | 25/25 | 0.0040 | 0.820 | 0.592 | none |
| cosplace | CMS-CPC/H+SH+CSTJS+G+NGRr | – | 25/25 | 0.0018 | 0.820 | 0.591 | none |
| cosplace | CMS-CPC/H+CSTF+G+NGRr | – | 25/25 | 0.0000 | 0.610 | 0.440 | none |
| cosplace | CMS-CPC/H+CSTJs+G+NGRr | – | 25/25 | 0.0065 | 0.819 | 0.591 | none |
| cosplace | CMS-CPC/H+SH+CSTJs+G+NGRr | – | 25/25 | 0.0018 | 0.817 | 0.589 | none |
| cosplace | CPC-SC-T0.5+SH | – | 25/25 | 0.0109 | 0.928 | 0.668 | none |
| cosplace | CMS-CPCW/H+SH+NGRr | – | 25/25 | 0.0104 | 0.865 | 0.624 | none |
| netvlad | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.05 | 25/25 | 0.0108 | 0.486 | 0.203 | calibration traversals |
| netvlad | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.1 | 25/25 | 0.0140 | 0.514 | 0.212 | calibration traversals |
| netvlad | CMS-CPC/H+SH+G+NGRr | – | 25/25 | 0.0010 | 0.703 | 0.473 | none |
| netvlad | CMS-CPC/H+CSTJS+G+NGRr | – | 25/25 | 0.0028 | 0.708 | 0.476 | none |
| netvlad | CMS-CPC/H+SH+CSTJS+G+NGRr | – | 25/25 | 0.0010 | 0.703 | 0.473 | none |
| netvlad | CMS-CPC/H+CSTF+G+NGRr | – | 25/25 | 0.0000 | 0.417 | 0.279 | none |
| netvlad | CMS-CPC/H+CSTJs+G+NGRr | – | 25/25 | 0.0032 | 0.711 | 0.478 | none |
| netvlad | CMS-CPC/H+SH+CSTJs+G+NGRr | – | 25/25 | 0.0010 | 0.700 | 0.471 | none |
| netvlad | CPC-SC-T0.5+SH | – | 25/25 | 0.0142 | 0.712 | 0.482 | none |
| netvlad | CMS-CPCW/H+SH+NGRr | – | 25/25 | 0.0105 | 0.746 | 0.502 | none |
| megaloc | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.05 | 25/25 | 0.0091 | 0.753 | 0.538 | calibration traversals |
| megaloc | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.1 | 25/25 | 0.0160 | 0.812 | 0.581 | calibration traversals |
| megaloc | CMS-CPC/H+SH+G+NGRr | – | 25/25 | 0.0035 | 0.812 | 0.596 | none |
| megaloc | CMS-CPC/H+CSTJS+G+NGRr | – | 25/25 | 0.0076 | 0.813 | 0.597 | none |
| megaloc | CMS-CPC/H+SH+CSTJS+G+NGRr | – | 25/25 | 0.0035 | 0.812 | 0.596 | none |
| megaloc | CMS-CPC/H+CSTF+G+NGRr | – | 25/25 | 0.0000 | 0.557 | 0.411 | none |
| megaloc | CMS-CPC/H+CSTJs+G+NGRr | – | 25/25 | 0.0102 | 0.813 | 0.596 | none |
| megaloc | CMS-CPC/H+SH+CSTJs+G+NGRr | – | 25/25 | 0.0035 | 0.809 | 0.594 | none |
| megaloc | CPC-SC-T0.5+SH | – | 25/25 | 0.0119 | 0.928 | 0.680 | none |
| megaloc | CMS-CPCW/H+SH+NGRr | – | 25/25 | 0.0113 | 0.862 | 0.632 | none |
| salad | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.05 | 25/25 | 0.0085 | 0.736 | 0.522 | calibration traversals |
| salad | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.1 | 25/25 | 0.0168 | 0.815 | 0.579 | calibration traversals |
| salad | CMS-CPC/H+SH+G+NGRr | – | 25/25 | 0.0029 | 0.814 | 0.593 | none |
| salad | CMS-CPC/H+CSTJS+G+NGRr | – | 25/25 | 0.0063 | 0.815 | 0.594 | none |
| salad | CMS-CPC/H+SH+CSTJS+G+NGRr | – | 25/25 | 0.0029 | 0.814 | 0.593 | none |
| salad | CMS-CPC/H+CSTF+G+NGRr | – | 25/25 | 0.0000 | 0.528 | 0.387 | none |
| salad | CMS-CPC/H+CSTJs+G+NGRr | – | 25/25 | 0.0117 | 0.814 | 0.593 | none |
| salad | CMS-CPC/H+SH+CSTJs+G+NGRr | – | 25/25 | 0.0029 | 0.812 | 0.591 | none |
| salad | CPC-SC-T0.5+SH | – | 25/25 | 0.0108 | 0.929 | 0.676 | none |
| salad | CMS-CPCW/H+SH+NGRr | – | 25/25 | 0.0108 | 0.861 | 0.627 | none |
| mixvpr | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.05 | 25/25 | 0.0079 | 0.753 | 0.532 | calibration traversals |
| mixvpr | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.1 | 25/25 | 0.0158 | 0.828 | 0.585 | calibration traversals |
| mixvpr | CMS-CPC/H+SH+G+NGRr | – | 25/25 | 0.0030 | 0.813 | 0.594 | none |
| mixvpr | CMS-CPC/H+CSTJS+G+NGRr | – | 25/25 | 0.0060 | 0.814 | 0.594 | none |
| mixvpr | CMS-CPC/H+SH+CSTJS+G+NGRr | – | 25/25 | 0.0030 | 0.813 | 0.594 | none |
| mixvpr | CMS-CPC/H+CSTF+G+NGRr | – | 25/25 | 0.0000 | 0.559 | 0.408 | none |
| mixvpr | CMS-CPC/H+CSTJs+G+NGRr | – | 25/25 | 0.0084 | 0.813 | 0.594 | none |
| mixvpr | CMS-CPC/H+SH+CSTJs+G+NGRr | – | 25/25 | 0.0030 | 0.811 | 0.592 | none |
| mixvpr | CPC-SC-T0.5+SH | – | 25/25 | 0.0106 | 0.928 | 0.677 | none |
| mixvpr | CMS-CPCW/H+SH+NGRr | – | 25/25 | 0.0103 | 0.857 | 0.626 | none |
| dinov2 | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.05 | 25/25 | 0.0070 | 0.488 | 0.278 | calibration traversals |
| dinov2 | SafeVPR'26 (MNN DINOv2 ViT-L/14, Mondrian LTT, labels) | 0.1 | 25/25 | 0.0186 | 0.630 | 0.359 | calibration traversals |
| dinov2 | CMS-CPC/H+SH+G+NGRr | – | 25/25 | 0.0018 | 0.707 | 0.444 | none |
| dinov2 | CMS-CPC/H+CSTJS+G+NGRr | – | 25/25 | 0.0042 | 0.709 | 0.446 | none |
| dinov2 | CMS-CPC/H+SH+CSTJS+G+NGRr | – | 25/25 | 0.0018 | 0.707 | 0.444 | none |
| dinov2 | CMS-CPC/H+CSTF+G+NGRr | – | 25/25 | 0.0000 | 0.418 | 0.265 | none |
| dinov2 | CMS-CPC/H+CSTJs+G+NGRr | – | 25/25 | 0.0049 | 0.715 | 0.448 | none |
| dinov2 | CMS-CPC/H+SH+CSTJs+G+NGRr | – | 25/25 | 0.0018 | 0.706 | 0.444 | none |
| dinov2 | CPC-SC-T0.5+SH | – | 24/25 | 0.0195 | 0.704 | 0.449 | none |
| dinov2 | CMS-CPCW/H+SH+NGRr | – | 25/25 | 0.0098 | 0.742 | 0.466 | none |

**Kiểm giả thuyết (đăng ký trước, Entry 37):**

- H37a: segFAR TB của CST-JS ≤ 0.05 trên 7/7 (tập chính), Oxford [np.True_, np.True_] (chính, giữ ra), giữ ra 6/6: Boreas 0.009, NCLT 0.003, CMU 0.011, Nordland 0.001, 4S office 0.007, 4S old town 0.010, 4S countryside 0.003 | giữ ra: Boreas 0.014, CMU 0.019, Nordland 0.001, 4S office 0.007, 4S old town 0.014, 4S countryside 0.005
- H37c: recall CST-JS − CST-F trên CMU (chính, giữ ra) = +0.155, +0.142 (cần ≥ +0.05); CST-JS − SH ≥ −0.03 trên 7/7 (cần ≥ 4/7): Boreas +0.003, NCLT +0.020, CMU -0.006, Nordland +0.015, 4S office +0.013, 4S old town +0.009, 4S countryside +0.010
- H37d: sai số điều hướng CST-JS − SH ≤ 1 m trên 5/7 (cần ≥ 5/7): Boreas +2.3, NCLT +0.4, CMU -0.3, Nordland +0.4, 4S office +0.0, 4S old town +14.5, 4S countryside +0.6
- H37e (Oxford seed 0–4): CST-JS segFAR 0.023, recall 0.738 vs SH 0.729 (Δ +0.009; cần ≥ −0.03)
- H37e (Oxford giữ ra): CST-JS segFAR 0.019, recall 0.711 vs SH 0.698 (Δ +0.012; cần ≥ −0.03)
- H37g (St Lucia): CST-JS segFAR 0.021, recall 0.763 vs SH 0.761
- H37f: N = 40 segFAR TB ≤ 0.05 ở mọi (dataset, descriptor): True; recall gộp N40 ≥ N20 trên 6/6 (cần ≥ 5/6)


## 4. Đọc kết quả

- **Bằng chứng hiện diện tiến là thứ sửa tính hợp lệ.** Cùng cấu trúc CST-JS nhưng hiện diện của vòng 10 (ablation CST-JSL): CMU giữ ra 0.051,
  old town 0.034, office 0.038; với hiện diện tiến: 0.019 / 0.014 / 0.007. Null đầu chuỗi thêm recall ở CMU: bỏ cửa sổ ngắn (CST-JS0) mất
  0.13 recall trên CMU, gần như không đổi ở dataset khác (≤ 0.009).
- **Khoảng trống còn lại là mép lỗ hình khối.** Đoạn sâu: 0.000–0.008 mọi nơi; đoạn đầu chuỗi: ≤ 0.034 trừ office (0.119 trên chỉ 84 đoạn);
  đoạn mép: Boreas 0.084, old town 0.109 (CST-J\* 0.152 / 0.178). Lỗ thật là các khối bản đồ, lỗ ảo là phần Voronoi của đường tin, nên đoạn
  đầu tiên sau lối thoát thật không hoán đổi được với đoạn ảo vị trí 0 trên hai dataset này. Hệ quả điều hướng: old town +14.5 m so với SH
  (H37d chỉ đạt 5/7). SH ∧ CST-JS cắt các báo cáo này (mép old town 0.060, sai số = SH).
- **Oxford:** CST-JS hợp lệ (0.023; giữ ra 0.019) và recall cao hơn SH (+0.009 / +0.012), trong khi CST-F vòng 10 mất 0.18.
- **N = 40** tăng recall trên mọi dataset khi gộp descriptor (lớn nhất countryside +0.034; DINOv2 +0.01–0.05), không đổi tính hợp lệ.
- **St Lucia / SafeVPR'26 (ViT-L/14):** SafeVPR'26 hợp lệ 25/25 nhưng recall 0.20–0.54 ở α = 0.05 (cần nhãn của 4 lượt khác); luật của ta
  0.44–0.60 không nhãn, FDR 0.001–0.008. Thay ViT-B (vòng 10) bằng ViT-L tăng recall của SafeVPR'26 (CosPlace 0.462 → 0.514) nhưng không đổi kết luận.

## 5. Việc tiếp theo

1. Lỗ ảo có **hình học khối của bản đồ triển khai** (cắt theo khối thay vì Voronoi) để đoạn mép hoán đổi được; kiểm lại H37b trên tập giữ ra mới.
2. H37h (độ bền tỷ lệ lỗ 10 % / 50 %, 216 run) — đang chạy khi viết báo cáo; kết quả bổ sung vào `RESEARCH_LOG.md`.
3. Hoàn thiện bài báo: SH ∧ CST-JS + CST-F + N = 40; phụ lục chi phí GPU.
