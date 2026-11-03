# 03 — Handoff (branch `hmm-2nd-idea`)

*2026-11-03. Trạng thái, cái đã giữ / bỏ khi tách branch, và việc tiếp theo. Bản handoff đầy đủ của ý tưởng 1:
`git show hmm-navigation-5:handoff/03_HANDOFF.md`.*

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
