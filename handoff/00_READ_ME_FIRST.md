# 00 — READ ME FIRST (branch `hmm-2nd-idea`)

*2026-11-04. Repo `lhaochen118-ship-it/hmm-develop` (public). Không tạo PR. Branch dành cho **ý tưởng 2 (HSI)**: lời giải A\* khác hẳn ý tưởng 1
(phẫu thuật bản đồ phản thực, branch `hmm-navigation-5`) cho cùng bài toán định vị chuỗi trên bản đồ ảnh có lỗ.*

**Luật khuyến nghị: HSI-VN** — 0 vi phạm trên 413 run phát triển + 216 run của hai tập kiểm tra mới; +0.065 recall so với ý tưởng 1 (SH).

**LUẬT KHUYẾN NGHỊ (từ 2026-11-04 19:18 UTC, Entry 13): OWF-HW-S.** Quy trình gồm ba bước:
1. OWF với ngân hàng tỉ lệ odometry (`owf.py --qx 0.005,0.02 --scales 0.97,1.0,1.03`).
2. OWF-H: chuỗi OWF giao cho HSI-VN khi khối lượng ≥ 0.9 và đã đi ≥ 16·excl (`owf_hybrid.py --mode xms0.9_16`).
3. Hợp hai bậc với các báo OWF cực tự tin: `owf_union.py --variants "W(1e-5,16,1e-8,2)"`.

Vòng lặp tự động 12 giờ (`handoff/AUTOLOOP.md`). Mỗi luật được đăng ký trước, rồi kiểm trên một nhóm seed MỚI. Bảng dưới là recall gộp / số run
> α / sai số điều hướng; mọi luật đều hợp lệ trên mọi dataset:

| Nhóm mới (144 run) | HSI-VN | OWF-H (Entry 11) | OWF-HU (Entry 12) | OWF-HW-S (Entry 13) |
|---|---|---|---|---|
| seed 40–42 | 0.811 / 1 / 15.35 | **0.885** / 1 / 14.46 | | |
| seed 43–45 | 0.805 / 1 / 15.92 | 0.878 / 1 / 15.73 | **0.896** / 1 / 14.94 | |
| seed 46–48 | 0.786 / 1 / 14.72 | 0.860 / 1 / 14.62 | 0.878 / 1 / 13.61 | **0.902** / 1 / 12.75 |

Đang chạy: Entry 14, bậc đồng thuận ba nguồn cho đầu chuỗi (CMU), kiểm trên seed 49–51.

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
| `../paper/BAO_CAO_HSI.pdf` | báo cáo đầy đủ của ý tưởng 2a (HSI) |
| `../paper/BAO_CAO_OWF.pdf`, `../paper/owf_theory.md` | báo cáo + lý thuyết của ý tưởng 2b (OWF, Entry 10) |
| `../history/` | tài liệu cũ (phát hiện / vận hành của ý tưởng 1, hướng dẫn đầu ý tưởng 2) |
