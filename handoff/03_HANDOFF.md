# 03 — Handoff (branch `hmm-2nd-idea`)

*2026-11-03. Trạng thái, cái đã giữ / bỏ khi tách branch, và việc tiếp theo. Bản handoff đầy đủ của ý tưởng 1:
`git show hmm-navigation-5:handoff/03_HANDOFF.md`.*


## 0. Trạng thái ý tưởng 2 (cập nhật 2026-11-04 04:45 UTC, vòng tự động thứ hai của phiên `session_01Xy89bX34L6MPEcAxmjRJWt`)

- **Phương pháp:** HSI (`analysis/hsi.py` `online_v2`, biến thể trong `analysis/hsi_eval.py` VARIANTS). Lý thuyết `paper/hsi_theory.md` Mệnh đề 1–7;
  nhật ký `RESEARCH_LOG.md` Entry 1–9; báo cáo `paper/BAO_CAO_HSI.pdf` (14 trang).
- **Luật khuyến nghị chính thức: HSI-rot-m-sc** (Entry 3). **Ứng viên mạnh nhất: HSI-VN** (Entry 8: chứng chỉ neo cầu hồi cứu + căn chỉnh
  Neyman–Pearson `train_null=True`) — trội Pareto trên tập kiểm tra seed 13–15 (0/108 vi phạm, recall +0.016, điều hướng −0.58 m) nhưng trượt tiêu
  chí cơ chế T3; **Entry 9** (nhân bản đúng quy tắc trên seed 16–18) quyết định cuối cùng. HSI-VMN = điểm vận hành ưu tiên điều hướng.
- **Phân chia dữ liệu:** seed 0 × 4 descriptor = thiết kế; seed 0–9 (413 run) = phát triển; seed 10–12 = xác nhận cũ (đã dùng); seed 13–15 =
  kiểm tra Entry 8 (`caotienminh1/hmm-navcache-f13`, public); seed 16–18 = kiểm tra Entry 9 (`caotienminh1/hmm-navcache-f16`, sinh bởi đợt
  `hsi17`). Mọi quyết định mới cần một tập mới nữa (seed 19+).
- **Công cụ mới:** `analysis/hsi_fresh.py --keep` (sinh cache bố cục lỗ mới, giữ trong output kernel), `automation/fetch_outputs.py` (kéo file từ
  kernel nhiều tài khoản), `automation/publish_dataset.py --owner`, `central_monitor.py --pull-pattern` (chỉ kéo results.tar + log),
  `analysis/hsi_entry8_test.py` (T1–T4), `analysis/hsi_compare.py`, `analysis/hsi_alpha.py`.
- **Hướng đã thử và loại (đều đo trước khi chạy lớn):** đặc trưng hubness theo nơi, chứng chỉ cửa sổ ngắn "học từ chuỗi dài" (thầy đánh giá thấp lỗi
  thật), chứng chỉ tự đồng dạng bản đồ (K = 0 gần như không có ở ℓ ≤ 30 m), Mondrian theo trạng thái bằng chứng, bỏ cổng nhất quán (điều hướng),
  hiệu chuẩn chụm lỗi ngắn (fix sai xa nằm trong chuỗi sai dài, không phải chụm ngắn), hạ ngưỡng nhãn tối thiểu.

## 1. Trạng thái

- Branch tách từ `hmm-navigation-5` (sau Entry 38 + đăng ký trước Entry 39). Chưa có ý tưởng 2: phase 1 (literature + gap) bắt đầu từ đầu.
- `RESEARCH_LOG.md` mới (trống, Entry 1 cho ý tưởng 2); nhật ký cũ: `history/RESEARCH_LOG_idea1.md`.
- Entry 39 của ý tưởng 1 (xác nhận CST-JSU [both] trên bố cục lỗ mới, chẩn đoán mép) chạy tiếp trên branch `hmm-navigation-5`; kết quả
  của nó (nếu đổi baseline) xem `git show hmm-navigation-5:RESEARCH_LOG.md`.

## 2. Đã giữ

- Code nền: loader dữ liệu, sinh lỗ + odometry + HMM + metric (`nav_demo.py` và các module nó cần), đánh giá từ cache, kiểm toán theo vị
  trí, baseline 2026 của người khác (TAO'26, TRAIL'26, SafeVPR'26, VPR-auditing'26). Danh sách: `05_NEW_CHAT_GUIDE.md` §4.
- Toàn bộ công cụ Kaggle / vận hành (`automation/`), mã trích descriptor (`nb15_src/`, `make_dump_*.py`, `make_stlucia_kernel.py`).
- Tài liệu: phát hiện khoa học (01), vận hành (02), quy trình (04 + bản gốc), môi trường, `LITERATURE_GATE.md`, `literature/`,
  `DATA_AUDIT.md`, yêu cầu nghiên cứu `HMM_Navigation_Yeu_Cau_Nghien_Cuu_Cap_Nhat.docx`.
- Số liệu baseline của ý tưởng 1: `analysis/results/baselines_idea1/` (oc JSON của Entry 37 — 342 run, lỗ 10/50 %, N = 40 — và
  Entry 38 — 402 run; kiểm toán theo vị trí; so sánh SafeVPR'26 trên St Lucia).

## 3. Đã bỏ (khôi phục bằng `git checkout hmm-navigation-5 -- <path>`)

- 46 module của ý tưởng 1: `cms*.py`, `cms_fwd.py`, `cst_audit.py`, `navrisk.py`, `oc_curves.py`, `e36_*`, `e37_*` (trừ `e37_collect.py`),
  `holes_*`, `natural_*`, `xnull.py`, … (danh sách đầy đủ trong commit tách branch).
- `paper/` (báo cáo và lý thuyết của ý tưởng 1: `BAO_CAO_E26…E38`, `cms_theory.md`, `cpc_theory.md`), kết quả cũ trong `analysis/results/`,
  `qcc/` (dự án khác), handoff 06 / RUNNING_KERNELS, `automation/e37_wave.py`, `cms_jobs.py`.
- Để chạy lại luật SH / CST-JS làm baseline trên dữ liệu mới: khôi phục `analysis/{cms,cms_exact,cms_vec,cms_fwd,cms_torch,navrisk,oc_curves,
  e37_fwd,e37_prep,e37_eval}.py` và `automation/e37_wave.py` từ `hmm-navigation-5` (null công khai: `hmm-fwd-null-e37`, `hmm-fwd-null-e38`).

## 4. Việc tiếp theo

Theo `05_NEW_CHAT_GUIDE.md` §3: gate novelty mới → 2–3 ứng viên → chọn → phương pháp → đăng ký trước → hiện thực + kernel thăm dò → đánh
giá trên giao thức chung (§1 của `07`) → lặp. Hạn mức GPU tuần của các acc đã dùng nhiều trong vòng 11–12 (nhatlong1103 hết đến khi reset):
ước lượng GPU-giờ trước mỗi đợt, báo user nếu cần thêm acc L4.
