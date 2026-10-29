# 00 — READ ME FIRST: hướng HMM-navigation (khung chat mới)

*Cập nhật 2026-10-29. Repo `lhaochen118-ship-it/hmm-develop`, **branch làm việc: `hmm-navigation`**. Không tạo PR.
Tài liệu này hướng dẫn đọc repo và liệt kê việc tiếp theo cho đề bài mới.*

## 1. Đề bài

> **Idea:** dùng Hidden Markov Model làm localization theo chuỗi (sequence-based) cho robot navigation với camera
> monocular. **Topic:** visual localization. **Cơ sở:** Sattler et al., *Benchmarking 6DOF Outdoor Visual Localization
> in Changing Conditions*, CVPR 2018
> (https://openaccess.thecvf.com/content_cvpr_2018/papers/Sattler_Benchmarking_6DOF_Outdoor_CVPR_2018_paper.pdf).
> **Mục tiêu:** research paper hạng A\*.

Các bước user gợi ý (theo thứ tự):

1. Verify lại các dataset đã có xem đã chính xác chưa.
2. Bổ sung dataset nếu cần.
3. Dựa trên idea, xây dựng ý tưởng đủ novel cho paper A\*.
4. Chạy code thực nghiệm → đánh giá → chạy code → … (vòng lặp của `04_RESEARCH_WORKFLOW`).

## 2. Thứ tự đọc

| # | File | Đọc để biết | Khi nào |
|---|---|---|---|
| 1 | File này | Đề bài, repo có gì, việc tiếp theo | **bắt buộc** |
| 2 | `handoff/04_RESEARCH_WORKFLOW.md` (+ bản gốc `handoff/RESEARCH_WORKFLOW_original.pdf`) | Quy trình nghiên cứu, phase, nguyên tắc | **bắt buộc** |
| 3 | `handoff/ENVIRONMENT_SUMMARY.md` | Dataset trên Kaggle, dump descriptor, cấu trúc thư mục, 8 tài khoản | **bắt buộc cho bước 1–2** |
| 4 | `handoff/02_ENGINEERING_OPS_NOTES.md` | Cách chạy trên Kaggle (16 T4), lỗi đã gặp, điểm dễ sai của loader | trước khi chạy code |
| 5 | `literature/VISUAL_LOCALIZATION_REVIEW.md` | Tổng quan visual localization, HMM/sequence VPR (§6) | trước khi làm idea |
| 6 | `LITERATURE_GATE.md` | Các lần kiểm tra novelty trước (Gate 1–5); Gate 3 liệt kê paper HMM/sequence | trước khi chốt idea |
| 7 | `RESEARCH_LOG.md` | Nhật ký thí nghiệm hướng cũ (CCBF/HMM filter, SelfCal) | chỉ khi cần tra |
| — | `KAGGLE_TOKENS.md` (nếu có) | Token API của 8 acc | khi container mới |

## 3. Repo có gì (sau khi dọn)

| Path | Nội dung | Dùng lại cho HMM thế nào |
|---|---|---|
| `analysis/vprlib.py` | Loader `LOADERS[rc|cmu|nord|msls|nordw]` cho dump descriptor, `Episode`, metric, `map_cells`, `correct`, `top1_errors`, **`frame_order`** (sequence id + chỉ số trong chuỗi cho query/map; port từ branch seq) | Dữ liệu đầu vào của HMM: vector similarity query→map, pose, thứ tự frame |
| `analysis/selfcal.py`, `analysis/sc_eval.py` | Phương pháp SelfCal (p-value off-map không cần nhãn, hiệu chuẩn bằng bản đồ) và `CFG` cho từng dataset (cell, excl, block, ngưỡng đúng/sai) | Ứng viên làm **emission đã hiệu chuẩn** hoặc **trạng thái off-map** trong HMM (xem §5) |
| `automation/` | `fanout.py` (chia job ra 8 acc × 2 T4), `make_eval_kernel.py` (upload `analysis/*.py` + chạy job), `run_kernel.py`, `build_nb.py`/`make_meta.py`/`vpr_extra.py` (tạo dump mới), `md2pdf.py` | Hạ tầng chạy thí nghiệm, giữ nguyên |
| `nb15_src/` | Nguồn notebook tạo dump descriptor | Khi cần dump dataset/descriptor mới |
| `literature/` | Review visual localization | Nền cho literature gate |
| `LITERATURE_GATE.md`, `RESEARCH_LOG.md` | Lịch sử novelty và thí nghiệm | Tránh lặp lại hướng đã thất bại |

**Đã xoá khỏi branch này** (vẫn còn nguyên ở branch khác, lấy lại bằng `git checkout <branch> -- <path>`):

- Paper SelfCal, bảng, hình, kết quả JSON, script thí nghiệm `eval_all.py`, `exp2`–`exp10`, `figures2.py`,
  handoff 01/03 của SelfCal → branch `claude/selfcal-aa`.
- Sequence SelfCal `exp11_sequence.py`, demo định vị Kalman + odometry `exp12_deploy.py`, kết quả `seq_*`,
  `deploy_*` → branch `claude/selfcal-seq`. **`exp12_deploy.py` là baseline định vị theo chuỗi rất nên xem lại**
  (nó cần `selfcal.py` của branch seq).
- Notebook và tài liệu hướng HMM/CCBF đầu tiên (`CCBF_methodology.md`, `HANDOFF_CCBF.md`, NB1–NB14) → branch `main`.

## 4. Bài học từ các hướng trước liên quan trực tiếp tới HMM

1. **CCBF (HMM/Bayes filter trên (place, condition) với temperature theo điều kiện):** tốt trên Nordland (ECE
   0.076 → 0.028; off-map AUROC 0.99) nhưng **sụp trên RobotCar/CMU** (off-map AUROC 0.23). Temperature theo điều kiện
   gần như không khác nhau (≈ 1.2–1.5×). ⇒ Một HMM chỉ dựa vào similarity thô **không** tổng quát qua dataset; cần
   xử lý off-map và độ tin cậy emission một cách có nguyên tắc.
2. **Sequence SelfCal (cửa sổ L frame):** power tăng mạnh nhưng **validity theo cửa sổ thất bại** trên Nordland
   (MegaLoc vi phạm 2–3/3 mùa khi L ≥ 3), vì các query off-map liên tiếp phụ thuộc nhau theo điều kiện. ⇒ Mọi bảo
   đảm theo chuỗi phải tính tới phụ thuộc thời gian.
3. **Demo định vị (exp12, branch seq):** bản đồ mất 30 % block, Kalman filter + odometry trôi; chấp nhận fix bằng
   SelfCal-AA từng frame thắng ngưỡng có nhãn ở cả 12 cặp descriptor × dataset (lỗi thấp hơn 1.3–12.6×; CMU
   3.6–9.3 m so với oracle 2.8–3.2 m). ⇒ Đã có baseline định vị theo chuỗi để so.
4. **Label calibrated trên điều kiện dễ không chuyển sang điều kiện khó** (đêm, tuyết): đúng cho mọi ngưỡng/score.
5. **MSLS:** power thấp với mọi phương pháp không nhãn; bản đồ dị biệt là ca khó.
6. Kết luận chỉ từ ≥ 10 seed; mọi lựa chọn sau-khi-xem-dữ-liệu phải kiểm định trên dữ liệu mới.

## 5. Việc tiếp theo (thực hiện theo thứ tự)

### Bước 1 — Verify dataset đã có

Dữ liệu hiện có mô tả trong `ENVIRONMENT_SUMMARY.md`. Cần kiểm tra (viết kết quả vào `DATA_AUDIT.md` mới):

- **RobotCar-Seasons v2** (`nhatlong1103/robotcar-seasons-v2`, dump `rc_*`): số ảnh reference/query đúng như bản
  chính thức; camera nào (rear/left/right); quy ước pose (camera→world hay world→camera; tâm camera `C = −Rᵀt`);
  ground truth chỉ có cho **1,906 query train** công khai, test phải nộp lên server visuallocalization.net; timestamp
  trong tên ảnh có tạo được chuỗi liên tục (`vprlib.frame_order`) với bước ~1 m; có odometry (VO/INS) không — **HMM
  cần mô hình chuyển trạng thái, nên odometry là thiếu sót quan trọng nhất cần kiểm tra**.
- **Extended-CMU-Seasons** (`extended-cmu-seasons(-2)`, dump `cmu_s*`): slice nào có GT query thật (bản extended chỉ
  công bố GT cho một số slice); chỉ dùng camera c0; thư mục lồng `sliceN/sliceN/`; kiểm tra pose query không bị 0/NaN.
- **Nordland** (dump `nord_*`): chỉ có chỉ số frame (không có 6DOF); căn khung 1:1 giữa 4 mùa; subsample 4,500/35,768.
- **MSLS-val** (dump `msls_*`): GPS UTM + compass, có sequence key; bỏ panorama.
- **4Seasons** (`nhatlong1103/4seasons` + `-poses`): có pose và VO, chưa dump — ứng viên tốt cho odometry thật.
- Đối chiếu số lượng, phân bố khoảng cách giữa frame liên tiếp, và tỷ lệ query có match đúng (Recall@1) với số
  công bố.

### Bước 2 — Bổ sung dataset nếu cần

Bám paper cơ sở Sattler'18 (Aachen Day-Night, RobotCar Seasons, CMU Seasons; metric % query trong (0.25 m, 2°),
(0.5 m, 5°), (5 m, 10°)):

- Aachen Day-Night **chưa có** nhưng là ảnh đơn, không có chuỗi → ít giá trị cho HMM; chỉ cần nếu muốn so 6DOF đầy đủ.
- Với HMM theo chuỗi cần: chuỗi query có thứ tự + odometry hoặc pose tương đối. Ứng viên: 4Seasons (VO thật),
  Oxford RobotCar gốc (VO/INS), NCLT, St Lucia.
- Nếu làm 6DOF (không chỉ place-level) cần local features + mô hình 3D (RobotCar-Seasons có `3D-models/all.nvm`);
  dump hiện tại **chỉ có global descriptor**, nên cần notebook dump mới (local features, ví dụ SuperPoint + LightGlue)
  qua `nb15_src/` + `automation/build_nb.py`.

### Bước 3 — Literature gate (Gate 6) và ý tưởng novel

- Ghi Gate 6 vào `LITERATURE_GATE.md`. Chỉ đọc paper (alphaXiv). Nhóm cần so: HMM cho VPR/localization
  (Hansen & Browning'14, Xu et al. RA-L'21 có trạng thái off-map, SeqSLAM, Vysotska, Route-MHT, Hussaini'25/'26,
  SAFEVPR, Toft'20 *Long-term visual localization revisited* có đánh giá chuỗi), particle/topometric filters,
  sequence 6DOF localization.
- Hướng có thể khai thác (gợi ý, chưa kiểm tra novelty): HMM có **trạng thái off-map với emission được hiệu chuẩn
  bằng chính bản đồ** (dùng lại SelfCal), bảo đảm FAR theo chuỗi bền với phụ thuộc thời gian (khắc phục bài học 2),
  kết hợp place-level HMM với tinh chỉnh 6DOF, đánh giá trên giao thức Sattler'18.

### Bước 4 — Thực nghiệm

- Thử nhỏ ở local (< 2 phút), rồi chạy đầy đủ trên Kaggle bằng `automation/fanout.py` (dùng hết 16 T4 trước).
- Kết quả mới đặt ở `analysis/results/` (thư mục đang trống), log ở `RESEARCH_LOG.md` (Entry 18 trở đi).

## 6. Môi trường tối thiểu (container mới)

- `pip install kaggle markdown xhtml2pdf` (numpy, scipy, torch có sẵn).
- Token: `~/.kaggle/tok_<username>` cho 8 acc, `~/.kaggle/access_token` = acc 1 (`nhatlong1103`). Tạo lại từ
  `KAGGLE_TOKENS.md` hoặc tin nhắn của user. Không ghi vào `~/.bashrc`.
- Mọi tính toán nặng chạy trên Kaggle.
