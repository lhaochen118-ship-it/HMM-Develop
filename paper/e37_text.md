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

{{TABLES}}

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
