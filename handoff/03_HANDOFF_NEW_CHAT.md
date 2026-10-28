# Handoff — Context & How to Continue (for a FRESH chat window)

*Tài liệu này để khung chat mới nắm ngữ cảnh + tiến độ và tiếp tục được ngay. KHÔNG trùng nội dung với:
`handoff/01_SCIENTIFIC_FINDINGS.pdf` (khoa học) và `handoff/02_ENGINEERING_OPS_NOTES.pdf` (code/vận hành). Đọc 2
file đó + `RESEARCH_LOG.md` + `PAPER_DRAFT.md` + `RESULTS.md` trước khi hành động.*

Ngày chuyển giao: 2026-10-28. Repo: `lhaochen118-ship-it/hmm-develop`, branch **`claude/elegant-brown-xvnecd`**
(mọi commit nằm ở đây). Kaggle user: **`nhatlong1103`**.

---

## 1. Dự án đang ở đâu (1 đoạn)

Khởi đầu là ý tưởng **CCBF** (bộ lọc Bayes place×condition + temperature theo điều kiện). Qua ~9 thí nghiệm trên
Kaggle, CCBF bị chứng minh **trơ**, pivot sang đóng góp mới **CRSG** (calibrated retrieval-score geometry) —
đã verify trên **3 dataset (RobotCar, CMU, Nordland) + 2 descriptor (SALAD, DINOv2) + conformal guarantees +
full-scale**. Bản thảo paper + bảng kết quả + nhật ký đã viết và push. **Gói contribution core coi như xong.**
Việc còn lại là các đòn bẩy nặng để chắc A* (xem §4).

## 2. Bản đồ repo (những gì cần biết)

| File / thư mục | Nội dung |
|---|---|
| `PAPER_DRAFT.md` | Bản thảo paper: abstract, setup, §3 why remedies fail, §4 CRSG method, §5 results (5.1–5.6), contributions, limitations. **Điểm khởi đầu để viết full paper.** |
| `RESULTS.md` | Bảng master: 3 dataset × method × metric (reliability + off-map + conformal + scale). |
| `RESEARCH_LOG.md` | Nhật ký honest 10 entry (Entry 1→10, newest-at-top). Toàn bộ reasoning + số liệu từng thí nghiệm. |
| `handoff/01..03` | 3 file chuyển giao (khoa học / vận hành / cái này). |
| `CCBF_methodology.md` | Method+Theory CŨ của CCBF (4 định lý). CCBF đã bị bỏ — giữ làm tham chiếu, phần lý thuyết temperature không còn là contribution. |
| `DIVE_HMM_CCBF_NB3..14.ipynb` + `nbX_src/` | Notebook + source build-from-src (xem bảng §3). |
| `automation/` | `build_nb.py`, `run_stall.py` (T4 runner), `run_rtx2.py` (RTX runner có delete-restart), `make_meta.py` (T4/RTX metadata), `md2pdf.py`. |
| `HANDOFF_CCBF.md/.pdf` | Handoff CŨ (thời CCBF) — đã lỗi thời về khoa học; giữ cho lịch sử. |

## 3. Các notebook & kernel đã có (Kaggle slug `nhatlong1103/<slug>`)

| NB | Kernel slug | Mục đích | Trạng thái/kết quả |
|---|---|---|---|
| NB3 | dive-hmm-ccbf-nb3 | RobotCar per-condition τ diagnostic | DONE — τ inert (pivot) |
| NB4 | dive-hmm-ccbf-nb4 | RobotCar reliability gating | DONE — filter/CCBF fail |
| NB5 | dive-hmm-ccbf-nb5 | Diagnose + instantaneous calibration probe | DONE — breakthrough (margin) |
| NB6 | dive-hmm-ccbf-nb6 | CRSG validation (tolerance sweep) RobotCar | DONE — CRSG dominates |
| NB7 | dive-hmm-ccbf-nb7 | Cross-dataset Nordland | DONE — regime-dependence |
| NB8 | dive-hmm-ccbf-nb8 | Unified "calibrate the belief" | DONE — calibration can't rescue filter |
| NB9 | dive-hmm-ccbf-nb9 | Descriptor-agnostic (DINOv2) | DONE — calibration/off-map agnostic |
| NB11 | dive-hmm-ccbf-nb11 | CMU single-slice | DONE — CRSG dominates |
| NB12 | dive-hmm-ccbf-nb12 | Conformal risk control | DONE — C1/C2/C3 |
| NB13 | dive-hmm-ccbf-nb13 | Nordland large-scale (3000/mùa, T4) | DONE — scale consistent |
| NB14 | dive-hmm-ccbf-nb14 | CMU multi-slice large-scale (T4) | DONE — scale consistent |
| (probe) | dive-hmm-cmu-probe | CMU structure probe | DONE |

Mỗi NB build từ `nbX_src/` bằng `python automation/build_nb.py <out.ipynb> ../nbX_src`. Chạy bằng
`automation/run_stall.py` (T4) hoặc `run_rtx2.py` (RTX). CRSG core nằm ở `nb6_src/50_method.src`; conformal ở
`nb12_src/50_conformal.src`; CMU multi-slice ở `nb14_src/40_cmu_multi.src`.

## 4. VIỆC TIẾP THEO (user chỉ định, theo thứ tự)

### Bước 0 (GATE) — Kiểm tra trùng lặp với literature
Trước khi đầu tư thêm: **kiểm tra contribution CRSG + reality-check có trùng ý tưởng paper nào không.**
- Từ khóa tìm: "visual place recognition uncertainty / calibration", "selective prediction VPR", "retrieval
  score margin confidence", "conformal prediction place recognition / retrieval", "out-of-distribution VPR /
  off-map detection", "SUE place recognition uncertainty (Zaffar 2024)", "when does sequence help VPR".
- Cần phân biệt rõ CRSG với: SUE (Zaffar CVPR'24 — chỉ NN-distance), temperature scaling, SeqSLAM/HMM-VPR,
  learned uncertainty heads (BTL, STUN), conformal prediction cho image retrieval.
- **Nếu trùng mạnh** → quay lại Phase 2 (sinh ý tưởng), dùng các asset đã có (reliability protocol, regime-
  dependence finding) làm điểm tựa.
- **Nếu không trùng** → tiến hành các bước dưới.

### Bước 1 — Benchmark RobotCar-Seasons CHÍNH THỨC (ưu tiên cao nhất cho credibility)
- Dùng **test split chuẩn** (`robotcar_v2_test.txt`) + **ngưỡng chuẩn 0.25m/0.5m/5m** (+ góc 2°/5°/10° nếu khai
  thác được rotation từ quaternion/pose). Hiện tại đang dùng pose-GT tự dựng từ train.txt → cần thay bằng protocol
  chính thức để reviewer tin.
- Lưu ý: cần poses cho `overcast-reference` (map) — lấy từ `3D-models/all.nvm` hoặc `.db` (chưa làm). Hoặc dùng
  đúng submission format của benchmark RobotCar-Seasons.

### Bước 2 — Thêm descriptor (BoQ / MixVPR) — **quy trình user yêu cầu**
- CRSG mới test SALAD + DINOv2 (cùng backbone DINOv2). Thêm descriptor **khác hẳn** (BoQ, MixVPR) để claim
  descriptor-agnostic mạnh.
- **Quy trình bắt buộc (user chỉ định):** descriptor cần tải → **tải về MÁY CỦA USER** (cung cấp lệnh/script hoặc
  dùng cơ chế download-to-user-machine) → **upload lên thành Kaggle dataset** → **tự import vào notebook** và chạy.
  (Khung chat mới cần hỏi/hướng dẫn user hoặc dùng công cụ phù hợp để đưa file về máy user rồi lên Kaggle.)
- Trọng số BoQ/MixVPR không có trong `bundle` hiện tại → phải thêm.

### Bước 3 — Figures + viết full paper
- Figures cần: reliability diagrams, risk–coverage curves, ECE-vs-tolerance, bảng cross-dataset. Notebook nên
  lưu PNG vào `/kaggle/working` rồi pull về (hiện các NB chỉ in số, chưa lưu hình).
- Viết full paper từ `PAPER_DRAFT.md` (đã có khung + số thật).

## 5. Khôi phục vận hành nhanh (khung chat mới làm ngay khi bắt đầu)
1. Cài deps + token Kaggle (xem `handoff/02` §6). Verify: `kaggle kernels list --mine | head`.
2. Branch đang là `claude/elegant-brown-xvnecd`; `git pull` để chắc chắn mới nhất.
3. Đọc `RESEARCH_LOG.md` (10 entry) + `PAPER_DRAFT.md` + 2 file handoff khoa học/vận hành.
4. Làm **Bước 0 (literature gate)** trước khi code thêm.

## 6. Nguyên tắc giữ nguyên (từ user)
- Tự chủ, **không hỏi quyết định** trừ khi thật sự cần; cứ chạy.
- **Trung thực khoa học**: báo số đúng như nó là, kể cả negative; không oversell.
- GPU RTX PRO 6000 cho large-scale; **nhưng** ưu tiên T4 nếu RTX bận (đã chứng minh T4 nhanh + chắc cho cỡ dữ
  liệu hiện tại). Stall RTX 15 phút → delete + restart, tối đa 4 lần, rồi check lỗi.
- Mỗi push: test local synthetic trước; build bằng `build_nb.py`; commit + push lên branch.
