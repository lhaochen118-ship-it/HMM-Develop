# 00 — READ ME FIRST (khung chat mới, branch `hmm-navigation-2`)

*Cập nhật cuối ngày 2026-10-29. Repo `lhaochen118-ship-it/hmm-develop`. **Branch làm việc: `hmm-navigation-2`**, sao
từ `hmm-navigation` lúc bàn giao. Không tạo PR. File này hướng dẫn đọc repo và nêu việc tiếp theo.*

## 1. Đề bài (giữ nguyên)

**Idea:** HMM cho định vị theo chuỗi (sequence-based visual localization) với camera đơn cho robot navigation.
Cơ sở là Sattler et al., *Benchmarking 6DOF Outdoor Visual Localization in Changing Conditions*, CVPR 2018. Mục tiêu
là đóng góp đủ mạnh cho venue A\*.

User muốn tự động hoá tối đa: tự tìm gap → đề xuất → chạy trên Kaggle → kiểm chứng, không hỏi lại quyết định. **Không
viết paper**; chỉ viết báo cáo PDF ngắn bằng tiếng Việt (method + công thức, bảng, so sánh baseline, không hình), và
chỉ khi có kết quả mạnh.

## 2. Thứ tự đọc

| # | File | Để biết |
|---|---|---|
| 1 | File này | Repo có gì, việc tiếp theo |
| 2 | `handoff/03_HANDOFF.md` | Mục tiêu, trạng thái, quyết định đã chốt, vị trí mọi thứ, **các bước tiếp theo chi tiết** |
| 3 | `handoff/01_SCIENTIFIC_FINDINGS.md` | Đóng góp A (certified) và C (CPC-HMM), chẩn đoán HMM, kết quả thắng và thua kèm số liệu, hạn chế |
| 4 | `handoff/02_ENGINEERING_OPS_NOTES.md` (**§8 trước**) | Chạy Kaggle, trần phiên, container hay khởi động lại, lỗi đã gặp |
| 5 | `handoff/ENVIRONMENT_SUMMARY.md` | Dataset (dump 4 benchmark, 4Seasons, Boreas), acc Kaggle, cách chạy |
| 6 | `handoff/RUNNING_KERNELS.md` | Kernel còn chạy hoặc đã xong của khung chat cũ; kéo bằng `automation/pull_kernels.py` |
| 7 | `paper/cpc_theory.md` | Lý thuyết CPC-HMM (ARL₀, Shiryaev–Roberts, Anderson) |
| 8 | `handoff/04_RESEARCH_WORKFLOW.md` | Quy trình và trạng thái theo phase |
| — | `RESEARCH_LOG.md` (Entry 18–21), `LITERATURE_GATE.md` (Gate 6–7), `DATA_AUDIT.md` | Tra cứu khi cần |

Mỗi file `.md` trong `handoff/` có bản `.pdf` cùng tên.

## 3. Bản đồ repo

| Path | Nội dung |
|---|---|
| `analysis/vprlib.py` | Loader cho rc, cmu, nord, msls, nordw, `load_4seasons`, `load_boreas`; `frame_order`, `map_cells` |
| `analysis/selfcal.py`, `sc_eval.py` | p-value SelfCal-AA hiệu chuẩn bằng bản đồ; `CFG` từng dataset |
| `analysis/cert_seq.py` | **(A) Certified sequential localization**; odometry sim/VIO/bánh xe |
| `analysis/hmm_fix.py` | **(C) CPC-HMM** (`fac_anchT_mix`) + ablation + baseline Xu'21; quét `cpc_p*`, `cpc_pout*`, `cpc_pred` |
| `analysis/nav_demo.py` | Điều hướng khép kín. Luật: accept-all, label threshold, SelfCal frame, HMM Xu'21, CPC-HMM (+ p_out), certified, oracle. `--dump` |
| `analysis/hmm_diag.py` | Chẩn đoán HMM D1–D5 |
| `analysis/navdiag.py`, `presence_variants.py` | Phân tích offline file `navframes_*.npz` |
| `analysis/cert_natural.py`, `hmm_eval.py`, `seq_odo.py`, `audit_data.py` | Off-map tự nhiên, vòng HMM đầu, audit dữ liệu |
| `analysis/results/` | Mọi JSON kết quả. `hmmfix_dXX_*` là độ bền theo tỷ lệ lỗ bản đồ |
| `automation/` | `fanout.py` (chia job ra acc/slot, có failover), `make_eval_kernel.py`, `run_kernel.py`, `reattach.py`, `resume.py`, `pull_kernels.py`, dump 4Seasons/Boreas, `md2pdf.py` |
| `paper/` | `BAO_CAO_CertSeq.{md,pdf}` (`build_report.py`), `cert_tables.md` (`build_cert_tables.py`), `cpc_theory.md`, bản nháp cũ |

## 4. Việc tiếp theo (tóm tắt; chi tiết ở `03_HANDOFF.md` §5)

1. **Khởi động.**
   - Tạo token `~/.kaggle/tok_<acc>`.
   - `python3 automation/pull_kernels.py`: kéo kết quả các run navF/navFc/navG/fix7/bfix.
   - Tổng hợp, rồi ghi Entry 22.
2. **Chạy tiếp CPC-HMM.**
   - Mục tiêu: không còn thua Xu'21 trên Boreas, với **một** cấu hình chung chọn không nhãn.
   - Ứng viên:
     - p_out chọn theo công thức độ trễ khi rời bản đồ, với KL₀ ước lượng trên null bản đồ;
     - sửa e^R (null dựng trên đoạn giữ lại dài), hoặc bỏ e^R.
3. **Nếu làm hoài không cải thiện được CPC-HMM:** với những nơi HMM thua baseline (Boreas, RobotCar, 4S countryside),
   đi sâu vào bản chất toán, thuật toán, mô hình và bài toán để tìm nguyên nhân HMM yếu. Sau đó đề xuất một module,
   công thức, cơ chế hoặc kỹ thuật giúp HMM khắc phục điểm yếu đó, và cho nó qua gate novelty.
4. **Nếu nguyên nhân nằm ở bản chất dataset** (snippet quá ngắn; tuyến lặp lại với odometry gần như GT): bỏ qua dataset
   đó và tìm benchmark mới uy tín, phù hợp hơn (chuỗi dài + odometry thật + nhiều điều kiện, ví dụ NCLT, Oxford RobotCar
   gốc). Upload lên `nhatlong1103`, để public, cập nhật `ENVIRONMENT_SUMMARY`.
5. **Báo cáo.** Khi kết quả mạnh: rebuild `paper/BAO_CAO_CertSeq.pdf`, rồi commit và push lên `hmm-navigation-2`.

## 5. Môi trường tối thiểu (container mới)

- `pip install kaggle markdown xhtml2pdf` (numpy, scipy, torch có sẵn).
- **Token:**
  - Đặt ở `~/.kaggle/tok_<username>` cho 8 acc; `~/.kaggle/access_token` là của `nhatlong1103`.
  - Lấy từ tin nhắn đầu của user; thứ tự token trùng thứ tự acc ở `ENVIRONMENT_SUMMARY.md` §3.
  - Repo **public**, nên không commit token và không ghi vào `~/.bashrc`.
  - Kiểm tra bằng `KAGGLE_API_TOKEN=<tok> kaggle kernels list --mine`.
- **Tính toán nặng chạy trên Kaggle:**
  - Dùng hết 16 T4 trước, rồi đến CPU (5 phiên mỗi acc). GPU của `mucnokieu` hay bận.
  - Kernel kẹt hàng đợi quá 10 phút thì huỷ và push lại (`run_kernel.py` tự làm).
- **Container có thể khởi động lại bất cứ lúc nào:**
  - Ghi tên run vào `runs/active_runs.txt`.
  - Phục hồi bằng `automation/resume.py`.
  - Đặt lượt kiểm tra hẹn giờ để tự gắn lại kernel và kiểm tra treo.
