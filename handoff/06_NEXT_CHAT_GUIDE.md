# 06 — Hướng dẫn cho khung chat mới: đọc repository và việc tiếp theo

*2026-11-04, branch `hmm-2nd-idea` (repo `lhaochen118-ship-it/hmm-develop`, public). Không tạo PR. Thay cho `history/05_NEW_CHAT_GUIDE_idea2-start.md`.*

## 1. Đọc theo thứ tự (≈ 30 phút)

1. `handoff/03_HANDOFF.pdf` — mục tiêu, quyết định đã chốt, vị trí mọi thứ, sổ dùng tập kiểm tra, **việc tiếp theo** (§6).
2. `handoff/01_SCIENTIFIC_FINDINGS.pdf` — đóng góp, số liệu, kết quả âm (để không lặp lại hướng đã bác).
3. `handoff/02_ENGINEERING_OPS_NOTES.pdf` — công cụ, cách chạy một đợt Kaggle, lỗi đã gặp.
4. `handoff/ENVIRONMENT_SUMMARY.pdf` §0 — tài khoản, dataset công khai, gói cần cài.
5. `paper/BAO_CAO_HSI.pdf` (15 trang) — câu chuyện đầy đủ, bảng, hình; `paper/hsi_theory.md` — Mệnh đề 1–7.
6. Khi cần chi tiết một vòng: `RESEARCH_LOG.md` (Entry mới ở trên cùng; Entry 1–9 của ý tưởng 2).
7. Yêu cầu gốc của user: `HMM_Navigation_Yeu_Cau_Nghien_Cuu_Cap_Nhat.docx`; quy trình: `handoff/04_RESEARCH_WORKFLOW.pdf`.

## 2. Bản đồ repository (chỉ phần dùng cho ý tưởng 2)

```
analysis/hsi.py            phương pháp (online_v2 + các cờ), chứng chỉ hình học, cầu hồi cứu, hiệu chuẩn conformal
analysis/hsi_eval.py       VARIANTS (HSI-VN = luật khuyến nghị) + đánh giá một (dataset, descriptor, seeds)
analysis/hsi_compare.py    bảng so sánh biến thể theo dataset (+ SH với --base)
analysis/hsi_summary.py    H1–H5 so với SH;  hsi_entry8_test.py  tiêu chí T1–T4;  hsi_alpha.py  quét α
analysis/hsi_fresh.py      sinh tập kiểm tra mới (bố cục lỗ mới) từ dump descriptor rồi đánh giá
analysis/nav_demo.py       HMM + giao thức + cache (dùng chung với ý tưởng 1);  vprlib.py  loader dataset
automation/                hsi_wave.py, fanout.py, central_monitor.py, hsi_collect.py, fetch_outputs.py, publish_dataset.py, md2pdf.py
paper/                     BAO_CAO_HSI.(md|pdf), hsi_report_text.md, build_hsi_report.py, hsi_theory.md, tables/, figures/
analysis/results/hsi/      kết quả thô (JSON mỗi run + mặt nạ báo theo frame), baselines_idea1/ (SH, CST-JS của ý tưởng 1)
RESEARCH_LOG.md, LITERATURE_GATE.md (Gate 17), handoff/, history/ (tài liệu cũ, ý tưởng 1)
```

## 3. Khởi động phiên mới (≈ 10 phút)

```bash
pip install -q kaggle markdown xhtml2pdf scipy scikit-learn matplotlib pypdf
```

- Xin user token Kaggle của 5 acc (`quynhle07, nguyenhoa99, quynhtran35, yuan1103, caotienminh1`); lưu `~/.kaggle/tok_<acc>` (chmod 600). Không ghi
  token ở bất kỳ đâu khác.
- Tái tạo số liệu chính không cần Kaggle: giải nén `analysis/results/hsi/hsi_results_json.tgz` và `analysis/results/baselines_idea1/e37/oc_e37.tgz`,
  `e38/oc_e38.tgz` vào scratchpad rồi chạy, ví dụ
  `python3 analysis/hsi_compare.py <x>/main HSI-VN,HSI-rot-m-sc --base <x>/oc37 <x>/oc38` và
  `python3 analysis/hsi_entry8_test.py <x>/test_s16_18 HSI-VN` (phải ra "ALL PASS").
- Dữ liệu thiết kế cục bộ (28 cache seed 0, ~300 MB) cho thử nghiệm nhanh: tải từ `nhatlong1103/hmm-navcache-v2` bằng
  `kaggle datasets download nhatlong1103/hmm-navcache-v2 -f <tên file> -p <dir>` (KHÔNG để `-f` rỗng — sẽ kéo cả 1.3 GB).

## 4. Cách làm một vòng nghiên cứu (đã kiểm chứng)

1. Chẩn đoán cơ chế trên dữ liệu thiết kế / phát triển bằng script nhỏ (`analysis/`, cục bộ, vài phút).
2. Hiện thực thành MỘT cờ mới trong `online_v2` (mặc định = hành vi cũ) + biến thể có tên trong `VARIANTS`; kiểm hồi quy (biến thể cũ cho đúng
   số cũ) và smoke test trên 2–4 run thiết kế.
3. Đợt phát triển trên seed 0–9 (`hsi_wave.py` → `fanout.py --build-only --cpu --nodumps` → `central_monitor.py`), 15–40 phút.
4. Viết đăng ký trước vào `RESEARCH_LOG.md` (tiêu chí theo thước đo kết quả, quy tắc quyết định), commit + push.
5. Đánh giá trên **một nhóm seed chưa dùng** của `caotienminh1/hmm-navcache-r19` (token `DIR:navcache_`, `--nodumps --ds caotienminh1/hmm-navcache-r19`,
   seeds `19-21` …), ghi kết quả + quyết định, cập nhật `03_HANDOFF.md` §5, báo cáo (`paper/build_hsi_report.py`), commit + push.

## 5. Việc tiếp theo

Chi tiết trong `03_HANDOFF.md` §6. Tóm tắt:

1. **Đào sâu ba điểm yếu:** CMU (0.76 vs SH 0.835 — khoá còn lại do chuỗi ngắn đúng nhưng không thể chứng nhận), NCLT (mới 2 run — cần thêm cấu
   hình đánh giá), sai số điều hướng old town (do thời điểm báo dưới VIO trôi, không do fix sai xa).
2. **Áp dụng lên 16 bộ VPR-Space** (https://github.com/rfechner/VPR-Space): tải release → trích 6 descriptor (GPU, ước GPU-giờ trước) → loader +
   odometry từ pose → giao thức bản đồ = db, truy vấn = query → cache → đánh giá HSI-VN.
