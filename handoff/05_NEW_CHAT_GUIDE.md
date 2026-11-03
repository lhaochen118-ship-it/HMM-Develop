# 05 — Hướng dẫn cho khung chat mới (branch `hmm-2nd-idea`): tự chạy một vòng lặp ý tưởng mới

*2026-11-03. Repo `lhaochen118-ship-it/hmm-develop`, branch `hmm-2nd-idea` (tách từ `hmm-navigation-5` sau Entry 38). Không tạo PR.*

## 1. Nhiệm vụ của branch này

Cùng bài toán: **định vị thị giác cho robot bằng HMM trên chuỗi ảnh từ camera đơn** (nền tảng: Sattler et al., "Benchmarking 6DOF Outdoor
Visual Localization in Changing Conditions", CVPR 2018), khai thác thông tin thời gian khi robot di chuyển. Nhưng phải nghiên cứu một
**lời giải A\* HOÀN TOÀN MỚI**, khác hẳn ý tưởng 1 (phẫu thuật bản đồ phản thực + hiệu chuẩn quyết định báo/không báo, xem
`07_IDEA1_SUMMARY.md`). Ý tưởng 1 là **baseline cần đánh bại**, không phải thứ để làm tiếp.

Gợi ý vùng chưa khai thác (không bắt buộc; phải qua gate novelty): HMM ở mức 6DOF / hình học (Sattler'18 là benchmark 6DOF; dump hiện chỉ
có global descriptor — ảnh gốc có cho Boreas, 4Seasons, NCLT, St Lucia, RobotCar); trạng thái ẩn giàu hơn vị trí rời rạc (vị trí + hướng +
điều kiện ảnh); học emission / transition không nhãn từ chính luồng; HMM trên đồ thị bản đồ với lỗ là trạng thái tường minh; suy luận chuỗi
dài với độ phức tạp tuyến tính trên GPU; đánh giá đầu-cuối bằng sai số định vị 6DOF chứ không chỉ "fix đúng".

## 2. Thứ tự đọc (≈ 40 phút)

| # | File | Đọc để biết |
|---|---|---|
| 1 | `handoff/04_RESEARCH_WORKFLOW.md` (+ `RESEARCH_WORKFLOW_original.pdf`) | Quy trình phase, nguyên tắc nghiên cứu |
| 2 | `handoff/07_IDEA1_SUMMARY.md` | Bài toán, giao thức, số liệu cần đánh bại, giới hạn của ý tưởng 1 |
| 3 | `handoff/01_SCIENTIFIC_FINDINGS.md` | Phát hiện khoa học tích lũy (kết quả tích cực/tiêu cực) — §N mới nhất trước |
| 4 | `LITERATURE_GATE.md`, `literature/` | Related work đã đọc, kết luận novelty; ý tưởng mới phải qua gate mới |
| 5 | `handoff/02_ENGINEERING_OPS_NOTES.md` §00 (nguyên tắc tối ưu) rồi §0… | Kaggle, lỗi đã gặp, cách chạy nhanh |
| 6 | `handoff/ENVIRONMENT_SUMMARY.md` | Dataset, cache công khai, tài khoản, hạn mức GPU |
| 7 | `DATA_AUDIT.md`, `history/RESEARCH_LOG_idea1.md` (khi cần chi tiết) | Kiểm dữ liệu; nhật ký đầy đủ của ý tưởng 1 |

## 3. Vòng lặp phải tự thực hiện (theo `04_RESEARCH_WORKFLOW.md`)

1. **Literature + gap** — đọc paper (không đọc code repo của người khác), ghi gate mới vào `LITERATURE_GATE.md` (Gate 17…). Kiểm trùng ý tưởng.
2. **Ý tưởng** — 2–3 ứng viên, tự chấm novelty / soundness / hiệu quả / tiềm năng A\*; chọn một, ghi lý do. Phải khác bản chất ý tưởng 1.
3. **Phương pháp hoàn chỉnh** — toán, giả định, định lý nếu có, baseline (gồm SH / CST-JS của ý tưởng 1), metric, ablation, chi phí.
4. **Đăng ký trước** trong `RESEARCH_LOG.md` (mới, Entry 1…) — commit TRƯỚC khi xem kết quả đánh giá; tách tập thiết kế / giữ ra.
5. **Hiện thực + kiểm** — smoke test cục bộ đầu-cuối, kernel thăm dò thật trên Kaggle, rồi mới chạy cả đợt (xem §5).
6. **Đánh giá + cải tiến** — đường cong, kiểm toán theo vị trí, LODO, giữ ra; báo cáo kết quả âm trung thực; lặp lại 2–6.
7. **Bàn giao** — báo cáo `paper/BAO_CAO_*.md/.pdf` (tiếng Việt, `automation/md2pdf.py`), cập nhật handoff 00–07, ENVIRONMENT_SUMMARY.

## 4. Bản đồ code giữ lại (nền chung, không thuộc ý tưởng 1)

| Nhóm | File | Vai trò |
|---|---|---|
| Dữ liệu | `analysis/vprlib.py` | Loader mọi dataset (`LOADERS`, `load_boreas`, `load_4seasons`, `load_nclt`, `load_oxford`, `load_stlucia`), `frame_order`, `map_cells` |
| | `analysis/topk_dump.py` | `load(dump, ds, desc)`, top-K ứng viên (GPU) |
| | `analysis/sc_eval.py` | `CFG` theo dataset (cell, excl, block, off_d, in_d) |
| Giao thức | `analysis/nav_demo.py` | Sinh bản đồ có lỗ (seed), odometry thật/mô phỏng, chuỗi vị trí HMM, metric `rule_metrics`, baseline có nhãn (Xu'21, Claxton'24, …); `--cache` ghi `navcache_*.npz` |
| | `analysis/nav_rules.py`, `oc_summary.py`, `e26_summary.py`, `position_audit.py` | Đánh giá luật từ cache, đường cong, bảng, kiểm toán theo vị trí |
| HMM / hình học | `analysis/hmm_diag.py` (DiagFilter), `hmm_fix.py`, `hmm_eval.py`, `cert_seq.py` (odometry bánh xe / VIO), `geo_cons.py` (Procrustes), `cpc_geo.py`, `cpc_sc.py`, `selfcal.py` (null bản đồ, dùng bởi `nav_demo`) | Thành phần dùng chung |
| Baseline 2026 | `analysis/tao.py` (TAO'26), `trail.py` (TRAIL'26), `safevpr26.py` + `safevpr26_eval.py` + `safevpr_mnn.py` (SafeVPR'26), `vlm_audit.py` + `vlm_eval.py` (VPR-auditing'26), `vpr_images.py` | Đặc tả: `literature/BASELINES_2026.md` |
| Kaggle | `automation/make_eval_kernel.py` (runner song song, token `DUMP` / `DIR:<prefix>[@<thư mục>]`), `fanout.py`, `central_monitor.py`, `e37_collect.py`, `publish_dataset.py`, `anon_download.py`, `make_stlucia_kernel.py` (mẫu kernel trích descriptor + ViT-L), `make_dump_*.py`, `extract_desc_cpu.py`, `vpr_extra.py`, `nb15_src/` | Chạy, theo dõi, đăng dữ liệu |
| Khác | `analysis/envrun.py` (job với biến môi trường / thư mục riêng), `automation/md2pdf.py` | |

## 5. Nguyên tắc tối ưu tài nguyên (BẮT BUỘC; chi tiết và số đo ở `02` §00)

1. **Đo trước khi chạy lớn:** một kernel thăm dò với job THẬT của đợt, đủ tải (46 job / phiên L4), in ms/frame, RAM đỉnh, VRAM đỉnh;
   so GPU với numpy trên cùng job (kết quả phải trùng tuyệt đối nếu cùng phép tính).
2. **Phiên L4×4** = 4 GPU × 23 GB, 48 vCPU, 197 GB RAM. CPU thường là nút cổ chai; GPU chỉ có lợi khi lời gọi **lớn** (gộp lô qua nhiều
   đơn vị: đo được 1.94×); nhiều lời gọi nhỏ từ 12 tiến trình/GPU bị chia thời gian (MPS chỉ cứu được 1.3×). Lô GPU ~1 GB/tiến trình,
   tự chia đôi khi hết VRAM.
3. **Hạn mức:** 30 GPU-giờ/tuần/acc; L4×4 tính 4 GPU-giờ mỗi giờ. Lập ngân sách GPU-giờ trước mỗi đợt; phiên CPU (5/acc, 4 vCPU, không tốn
   hạn mức) cho các đơn vị nhỏ. Hết acc L4 thì báo user xin thêm.
4. **Đóng gói:** đơn vị = mọi job phụ thuộc nhau (vd. các phần của một run + job đánh giá) trong cùng kernel; LPT theo chi phí đo; job
   chuẩn bị đầu tiên, job chờ cuối cùng (FIFO ⇒ không deadlock); gộp các giai đoạn trong kernel để tránh vòng đẩy/kéo.
5. **API Kaggle:** một `central_monitor.py` duy nhất (khoảng cách ≥ 20 s); không `pkill -f` (giết theo PID tiến trình python); tải nguyên
   dataset bằng một lệnh; code dataset của acc phải "ready" trước khi đẩy.
6. **Bộ nhớ:** descriptor lưu fp16, đổi kiểu theo chuỗi; job Boreas 8448 chiều ~3 GB (top-K / thống kê chính xác ~6 GB).
7. **Đĩa phiên 30 GB:** giải nén đầu ra một lần, chép phần cần, xoá tar ngay.
8. **Smoke test đầu-cuối mọi cờ mới** cục bộ (dữ liệu nhỏ) và một kernel `--test` trên Kaggle trước khi chạy đợt.

## 6. Khởi động nhanh

```bash
pip install kaggle scipy scikit-learn markdown xhtml2pdf opencv-python-headless
```

Token: user gửi danh sách; lưu `~/.kaggle/tokens_raw`, `~/.kaggle/tok_<acc>` (chmod 600), `~/.kaggle/access_token` = `nhatlong1103`
(không ghi vào git). Kiểm: `KAGGLE_API_TOKEN=$(cat ~/.kaggle/tok_<acc>) kaggle config view`.

```bash
kaggle datasets download nhatlong1103/hmm-navcache-v2 -p <scratch>/navcache --unzip
```

Sinh cache cho bố cục lỗ mới (seed s) của một run: `python3 analysis/nav_demo.py <dump> <ds> <desc> 1 --cache --cache-only --seed0 <s>`.
Chạy một job trên Kaggle: `python3 automation/make_eval_kernel.py <dir> <slug> "<script> DUMP <args>" "" --owner <acc> --l4 --par 46`, theo
dõi bằng `automation/central_monitor.py <state.json> --gap 20 <dir>`.
