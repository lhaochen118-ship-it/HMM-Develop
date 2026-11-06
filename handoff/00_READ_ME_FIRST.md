# 00 — READ ME FIRST (branch `hmm-2nd-idea`)

*2026-11-06 (trước: 2026-11-04). Repo `lhaochen118-ship-it/hmm-develop` (public). Không tạo PR. Branch dành cho **ý tưởng 2 (HSI)**: lời giải A\* khác hẳn ý tưởng 1
(phẫu thuật bản đồ phản thực, branch `hmm-navigation-5`) cho cùng bài toán định vị chuỗi trên bản đồ ảnh có lỗ.*

**Luật khuyến nghị: HSI-VN** — 0 vi phạm trên 413 run phát triển + 216 run của hai tập kiểm tra mới; +0.065 recall so với ý tưởng 1 (SH).

**Phiên 2026-11-06 (Entry 19–22, `paper/BAO_CAO_S1106.pdf`).** Luật khuyến nghị vẫn là **OWF-HWA-S5**.
- Ba nhóm seed mới 55–63 (432 run): recall 0.927–0.937, 9/432 run > α (7 là CMU, từ hai bố cục lỗ).
- Hai ứng viên đăng ký trước không qua quy tắc. NT (không dịch chuyển tức thời): recall bằng, điều hướng ±. NT-V (OWF phủ quyết HSI): hợp lệ
  tốt hơn, điều hướng countryside tệ hơn.
- Hai ý tưởng âm ở phát triển: ℓ = L_vis; điểm giao μ₁/2.
- Phát hiện: **bí danh odometry không thấy được** (bản sao dịch dọc đường thẳng; Mệnh đề 6, `paper/owf_theory.md` §9) là nguồn đuôi hợp
  lệ còn lại.
- Kho seed mới `namhunhh/hmm-navcache-r61`; seed 64–66 còn trống.
- Việc tiếp theo: `03_HANDOFF.md` §6b.

**Phiên 2026-11-05 chiều (Entry 16–17, `paper/BAO_CAO_S1105.pdf`).**
- Engine GPU cho OWF: 10× nhanh hơn, quyết định trùng bản numpy.
- Entry 16: mọi hướng "nguyên tắc hoá" lớp quyết định / ước lượng đều âm hoặc phẳng trên 399 run phát triển. Các hướng đó gồm ngưỡng conformal
  hồi cứu, β theo evidence, ngân hàng tỉ lệ ±15 %.
- **Entry 17 XÁC NHẬN OWF-HWA-S5 trên seed mới 55–57:** 0.937, 1/144 run > α, 12.5 m, so với HSI-VN 0.806. SOTA ngoài trên cùng run
  (TAO'26, Xu'21, Claxton'24) đều vượt α trên 75–129 / 144 run.
- Tổng quát: lỗ 10/50 %, off-map tự nhiên, NCLT đều hợp lệ trung bình.
- Kho seed mới: `namhunhh/hmm-navcache-r55`; seed 58–60 còn trống.
- Việc tiếp theo: `03_HANDOFF.md` §6a.

**LUẬT KHUYẾN NGHỊ (từ 2026-11-05 00:25 UTC, Entry 15): OWF-HWA-S5.** Quy trình gồm bốn bước:
1. OWF với ngân hàng tỉ lệ odometry 5 mức (`owf.py --qx 0.005,0.02 --scales 0.94,0.97,1.0,1.03,1.06`; 10 bộ lọc, chọn trực tuyến theo evidence).
2. OWF-H: chuỗi OWF giao cho HSI-VN khi khối lượng ≥ 0.9 và đã đi ≥ 16·excl (`owf_hybrid.py --mode xms0.9_16 --hsiframes`).
3. Hợp với các báo OWF cực tự tin: ≥ 1 − 1e-5 sau 16·excl, hoặc ≥ 1 − 1e-8 sau 2·excl.
4. Bậc đồng thuận ba nguồn: ảnh OWF trùng chuỗi tô-pô VÀ truy hồi top-1, kèm khối lượng ≥ 1 − 3e-4 sau 0.5·excl.

Bước 3–4 là một lệnh: `owf_union.py --variants "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"`. Một job Kaggle cho bước 1–2: `owf_hsi_job.py`.

**Vòng lặp tự động 12 giờ** (`handoff/AUTOLOOP.md`, báo cáo `paper/BAO_CAO_AUTOLOOP.pdf`): 5 luật đăng ký trước, cả 5 đều ĐẠT trên nhóm seed mới
của mình. Bảng dưới là recall gộp / số run > α / sai số điều hướng (m) trên 144 run mỗi nhóm; mọi luật đều hợp lệ trên mọi dataset:

| Nhóm mới | HSI-VN | OWF-H (E11) | OWF-HU (E12) | OWF-HW-S (E13) | OWF-HWA-S (E14) | OWF-HWA-S5 (E15) |
|---|---|---|---|---|---|---|
| seed 40–42 | 0.811 / 1 / 15.35 | **0.885** / 1 / 14.46 | | | | |
| seed 43–45 | 0.805 / 1 / 15.92 | 0.878 / 1 / 15.73 | **0.896** / 1 / 14.94 | | | |
| seed 46–48 | 0.786 / 1 / 14.72 | 0.860 / 1 / 14.62 | 0.878 / 1 / 13.61 | **0.902** / 1 / 12.75 | | |
| seed 49–51 | 0.804 / 0 / 14.34 | 0.882 / 0 / 15.37 | 0.903 / 1 / 14.68 | 0.921 / 0 / 13.78 | **0.933** / 0 / 13.64 | |
| seed 52–54 | 0.823 / 1 / 14.32 | | | | 0.937 / 1 / 13.11 | **0.941** / 1 / 12.67 |

**Entry 10 — ý tưởng 2b, bộ lọc thế giới mở (OWF, `analysis/owf.py`):** lưới mét phủ cả vùng có bản đồ và vùng trống, hiện diện suy từ vị trí.
Hợp lệ (TB), recall cao nhất: tập A 404 run 0.863 (HSI-VN 0.791, SH 0.726), tập quyết định mới seed 25–27: +0.076 so với HSI-VN (CI [+0.054,
+0.099]) — nhưng sai số điều hướng kém HSI-VN ở 4/6 dataset và 4.7 % run vượt α (CMU, Nordland) ⇒ **theo quy tắc đăng ký trước HSI-VN vẫn là luật
khuyến nghị**; OWF là luật hợp lệ có recall cao nhất. Báo cáo: `paper/BAO_CAO_OWF.pdf`; nhật ký `RESEARCH_LOG.md` Entry 10; Gate 18.

**Bắt đầu: `06_NEXT_CHAT_GUIDE.md`** (thứ tự đọc, bản đồ repo, khởi động phiên, cách làm một vòng, việc tiếp theo).

| File | Phạm vi (không trùng nhau) |
|---|---|
| `06_NEXT_CHAT_GUIDE.md` | cách đọc repo, khởi động phiên mới, quy trình một vòng, tóm tắt việc tiếp theo |
| `01_SCIENTIFIC_FINDINGS.md` (.pdf) | đóng góp, ý nghĩa, kết quả tích cực / tiêu cực, bằng chứng, điều kiện kiểm chứng |
| `02_ENGINEERING_OPS_NOTES.md` (.pdf) | lập trình, môi trường, Kaggle, tổ chức thử nghiệm, lỗi và cách sửa, bài học |
| `03_HANDOFF.md` (.pdf) | mục tiêu, tiến độ, quyết định, vị trí mã / dữ liệu / kết quả, sổ dùng tập kiểm tra, việc tiếp theo chi tiết |
| `04_RESEARCH_WORKFLOW.md` (.pdf) + `RESEARCH_WORKFLOW_original.pdf` | quy trình theo phase, trạng thái phase, nguyên tắc |
| `ENVIRONMENT_SUMMARY.md` (.pdf) | tài khoản, dataset công khai, container (§0 = hiện hành) |
| `07_IDEA1_SUMMARY.md` (.pdf) | ý tưởng 1: giao thức, baseline cần đánh bại, bài học |
| `08_CHUYEN_GIAO_THEO_YEU_CAU.md` (.pdf) | chuyển giao theo 5 mục của file yêu cầu docx: đã làm gì, bằng chứng, chưa đạt gì; tình trạng 22 tài khoản Kaggle |
| `../paper/BAO_CAO_HSI.pdf` | báo cáo đầy đủ của ý tưởng 2a (HSI) |
| `../paper/BAO_CAO_OWF.pdf`, `../paper/owf_theory.md` | báo cáo + lý thuyết của ý tưởng 2b (OWF, Entry 10) |
| `../history/` | tài liệu cũ (phát hiện / vận hành của ý tưởng 1, hướng dẫn đầu ý tưởng 2) |
