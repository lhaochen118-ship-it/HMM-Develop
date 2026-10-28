# Research Workflow — Updated (2026-10-28)

> **Status update (2026-10-28):** Phases 1–4 were redone for the SelfCal direction (gate → idea → Kaggle verification → paper). Current state and next steps: `handoff/03_HANDOFF_NEW_CHAT.md`.

*Bản cập nhật của "Research Workflow" gốc, bổ sung TRẠNG THÁI HIỆN TẠI và VIỆC TIẾP THEO theo tiến độ dự án
DIVE-HMM → CRSG. Phần quy trình (Phase 1–5) giữ nguyên tinh thần bản gốc; phần cuối là mapping tiến độ + next steps.*

## Mục tiêu (giữ nguyên)
Xây dựng research paper chất lượng A* (ICLR/ICML/ICRA/NeurIPS/CVPR...). Quy trình chia Phase; mỗi Phase tự đánh
giá và lặp **Generate → Critique → Verify → Improve → Re-evaluate** đến khi đủ tốt. Mục tiêu cuối: Research Gap rõ
→ Novel Contribution mạnh → Technical Foundation vững → Experimental Evidence thuyết phục → Paper-level Story.

## Các Phase (tóm tắt, giữ nguyên tinh thần)
- **Phase 1 — Literature Review & Research Gap:** hiểu SOTA; tìm gap có giá trị; **kiểm tra kỹ để tránh trùng ý
  tưởng** (giảm novelty).
- **Phase 2 — Novel Idea Generation (quan trọng nhất):** ưu tiên **ý tưởng đơn giản nhưng insight mạnh + novelty
  rõ**, không ghép module cồng kềnh. Mỗi thành phần phải có lý do. Tự đánh giá Novelty / Technical Soundness /
  Expected Effectiveness / A* Potential; chưa đủ mạnh thì quay lại 2.1.
- **Phase 3 — Phương pháp hoàn chỉnh:** problem formulation, I/O, kiến trúc, math, train/inference, dataset,
  baseline, metrics, ablation, robustness, complexity, strengths/weaknesses. A* Quality Gate.
- **Phase 4 — Dataset/Environment/Assets:** liệt kê dataset, split, pretrained, checkpoint, weights, packages,
  CUDA/PyTorch, repos. **Nhóm A** (tự tải được → đóng gói .zip gửi user) / **Nhóm B** (không tải được → cung cấp
  script để user tải về máy → user upload lên Kaggle).
- **Phase 5 — Implementation & Debugging:** chia nhỏ Phase 0→10; sau mỗi phase kiểm shape/dtype/device/numerics/
  paths/deps; **small-scale pipeline test** trước; chỉ chạy **full-scale** khi small-scale ổn.
- **Môi trường cố định:** Kaggle Notebook, **GPU RTX PRO 6000 (96GB)**, một `.ipynb`, dataset/checkpoint upload lên
  Kaggle Dataset trước; tối ưu VRAM nhưng không đổi correctness.

---

## ✅ TRẠNG THÁI HIỆN TẠI (mapping vào các Phase)

- **Phase 1 (Gap):** ĐÃ XÁC ĐỊNH — VPR recall bão hòa; trục **reliability** (calibration + open-set abstention) ít
  nghiên cứu; temperature/SUE yếu; miscalibration phụ thuộc *hình dạng* phân phối điểm (scalar τ không sửa được).
  **Còn thiếu:** literature check chính thức xem CRSG/reality-check có trùng paper nào không (xem Next §A).
- **Phase 2 (Idea):** ĐÃ PIVOT. Ý tưởng gốc **CCBF** (condition-temperature) bị chứng minh **inert** → loại. Ý
  tưởng mới **CRSG** (calibrated retrieval-score geometry) — đơn giản, insight mạnh, đạt tinh thần "simple but
  strong". (Chi tiết: `handoff/01_SCIENTIFIC_FINDINGS.pdf`.)
- **Phase 3 (Method):** ĐÃ CÓ khung đầy đủ trong `PAPER_DRAFT.md` (problem, method, baselines, metrics
  ECE/AURC/conf-AUROC/open-set, conformal, ablations, limitations).
- **Phase 4 (Assets):** Datasets đã attach (RobotCar/CMU/Nordland/bundle). **Còn thiếu:** descriptor BoQ/MixVPR
  (Nhóm B — cần tải về máy user rồi upload Kaggle). Xem `environment_summary` cập nhật.
- **Phase 5 (Impl):** ĐÃ chạy small-scale → full-scale cho CRSG trên 3 dataset + 2 descriptor + conformal + scale.
  Verify đầy đủ. (NB3–NB14, xem `handoff/03`.)

**A* Quality Gate hiện tại:** nội dung khoa học đạt tầm A*; rủi ro còn lại là **benchmark chính thức** (đang dùng
pose-GT tự dựng) và **bề rộng descriptor** + figures/full paper.

---

## ▶ VIỆC TIẾP THEO (thứ tự ưu tiên — user chỉ định)

**§A. GATE — Literature overlap check (làm TRƯỚC).** Kiểm tra CRSG + reality-check có trùng ý tưởng paper nào
không (VPR uncertainty/calibration, selective prediction, conformal retrieval, SUE, SeqSLAM/HMM-VPR, learned
uncertainty heads). Nếu trùng mạnh → quay lại Phase 2. Nếu không → tiếp §B–§D.

**§B. Benchmark RobotCar-Seasons CHÍNH THỨC (credibility cao nhất).** Chuyển từ pose-GT tự dựng sang **test split
+ ngưỡng chuẩn (0.25m/0.5m/5m, 2°/5°/10°)**; lấy reference poses từ `3D-models/all.nvm`/`.db`. Mục tiêu: số liệu
reviewer-grade.

**§C. Thêm descriptor BoQ/MixVPR (Nhóm B).** Theo đúng quy trình user: **tải trọng số về MÁY USER → user/agent
upload lên Kaggle Dataset → import vào notebook → chạy** CRSG suite. Củng cố claim descriptor-agnostic.

**§D. Figures + full paper.** Reliability diagrams, risk–coverage curves, ECE-vs-tolerance; lưu PNG từ notebook
(`/kaggle/working`) rồi pull. Viết full paper từ `PAPER_DRAFT.md`.

**Nguyên tắc vận hành khi large-scale:** RTX PRO 6000 cho dữ liệu rất lớn; nhưng đã chứng minh **T4 nhanh + chắc**
cho cỡ hiện tại (≤ vài chục nghìn ảnh, chạy song song 2 kernel). Stall RTX 15 phút (0 output) → `kaggle kernels
delete -y` session cũ → tạo mới; tối đa 4 lần; vẫn fail thì kiểm tra lỗi. (Chi tiết: `handoff/02`.)
