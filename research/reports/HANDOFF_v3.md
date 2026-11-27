# HANDOFF v3 — tiếp tục nghiên cứu IA-HMM

**Nhánh:** `claude/nice-fermi-l7bzd6` · **Đọc theo thứ tự:** `AGENTS.md` → `research/STATE.md` → `research/MASTER_PLAN.md`
→ `research/reports/REPORT_v1.md` → `research/FINDINGS.md` · **Tái lập:** `README_REPRO.md`.

## Trạng thái
- Gates: G0 ✅ G1 ✅ G2 ✅ [S] G4 ✅ [S] (phụ thuộc quan sát + oracle motion là nguyên nhân gốc có can thiệp hỗ trợ trên ≥2
  dataset) · G5 một phần · G3 parked · G6 cần người dùng duyệt.
- Phương pháp: IA-HMM = HMM (node, vận tốc) + emission thị giác tempered + emission vận tốc từ thay đổi descriptor +
  trọng số bằng chứng AR(1) + chọn mô hình bằng NLL calibration.
- Kết quả (bảng chính 31 ô, sinh từ registry): ≥ ảnh đơn 31/31; vs SeqSLAM 25/5/1; vs HMM kernel cố định 14/14/3; 3 tuyến 4Seasons thật (old_town có dừng xe thật + đêm: emission vận tốc thắng kernel cố định, CI không chứa 0 cho 3/4 descriptor).

## Dữ liệu / kernel (owner nhatlong1103)
`dive-vpr-nb15a..d-dump`, `hmm-k01-nordseg`, `hmm-k02-4s-stopgo`, `hmm-k03-4s-scene2` → tải bằng
`kaggle kernels output <id> -p $HMMLOC_FB/<slug>`.

## 3 việc tiếp theo (ưu tiên)
1. **M5 6DoF**: ứng viên top-k từ posterior → SuperPoint+LightGlue → PnP (bundle có sẵn), ngân sách matching cố định,
   so HLoc retrieval-top-k; ngưỡng (0.25 m,2°)/(0.5 m,5°).
2. **Baseline learned-sequence** (JIST/SeqVLAD): cần trọng số (không có trên Kaggle) — blocker, cần người dùng cho phép
   tải từ GitHub release trong kernel có internet.
3. **Tổng quát hóa**: MSLS sequences, Oxford RobotCar full (chuỗi dài, dừng thật); Holm correction cho họ H1/H17/H20/H22;
   HSMM dwell cho dừng xe thật; sparse candidate cho LV ở bản đồ ≥30k (runtime 22 ms/frame hiện tại).

## Câu hỏi cần người dùng quyết định
- Có dùng các tài khoản Kaggle khác không (cần xác nhận chủ tài khoản đồng ý và phù hợp điều khoản Kaggle)?
- Venue/claim chính (VPR probabilistic vs robotics system) — sau M5.
