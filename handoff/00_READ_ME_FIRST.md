# 00 — READ ME FIRST (branch `hmm-2nd-idea`)

*2026-11-03. Repo `lhaochen118-ship-it/hmm-develop`. Không tạo PR. Branch này dành cho **ý tưởng thứ hai**: một lời giải A\* hoàn toàn
mới cho cùng bài toán (HMM, định vị thị giác trên chuỗi ảnh camera đơn; nền tảng Sattler et al. CVPR 2018). Ý tưởng 1 (phẫu thuật bản đồ
phản thực) ở branch `hmm-navigation-5`; ở đây chỉ còn bản tóm tắt + số liệu baseline.*

**Kết quả ý tưởng 2 (HSI): `paper/BAO_CAO_HSI.pdf`, `01_SCIENTIFIC_FINDINGS.md` §I2, `03_HANDOFF.md` §0. Luật khuyến nghị: HSI-VN
(0 vi phạm trên 413 run phát triển + 216 run của hai tập kiểm tra mới; +0.065 recall so với ý tưởng 1).**

**Bắt đầu: `05_NEW_CHAT_GUIDE.md`** (nhiệm vụ, thứ tự đọc, vòng lặp, bản đồ code, nguyên tắc tối ưu).

| File | Nội dung |
|---|---|
| `05_NEW_CHAT_GUIDE.md` | Đọc đầu tiên: nhiệm vụ, vòng lặp nghiên cứu, code giữ lại, nguyên tắc tối ưu tài nguyên |
| `07_IDEA1_SUMMARY.md` | Ý tưởng 1: giao thức, số liệu cần đánh bại, giới hạn, bài học |
| `04_RESEARCH_WORKFLOW.md` (.pdf) + `RESEARCH_WORKFLOW_original.pdf` | Quy trình theo phase, nguyên tắc |
| `01_SCIENTIFIC_FINDINGS.md` (.pdf) | Phát hiện khoa học tích lũy (của ý tưởng 1 và các hướng trước) |
| `02_ENGINEERING_OPS_NOTES.md` (.pdf) | §00 nguyên tắc tối ưu; Kaggle, lỗi đã gặp, bài học |
| `03_HANDOFF.md` (.pdf) | Trạng thái branch, cái gì giữ / bỏ, cách khôi phục code cũ |
| `ENVIRONMENT_SUMMARY.md` (.pdf) | Dataset, cache công khai, tài khoản, hạn mức GPU |
