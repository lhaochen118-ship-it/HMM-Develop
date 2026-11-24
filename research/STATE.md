# STATE — trạng thái sống của nghiên cứu (agent đọc file này ĐẦU TIÊN mỗi phiên)

*Cập nhật lần cuối: 2026-11-24 — phiên lập kế hoạch (Master Research Plan v1.0).*

## Vị trí hiện tại
- **Giai đoạn:** chuyển từ "CCBF v1 (legacy)" sang **GĐ1 + GĐ2 chạy song song** theo `docs/MASTER_RESEARCH_PLAN.md`.
- **Gates:** G1 ⏳ chưa · G2 ⏳ · G3 ⏳ (RobotCar CCBF — chưa chạy) · G4 ⏳ · G5 ⏳ · G6 ⏳
- **Đã xong trong phiên này:** kiểm toán repo (`ISSUES.md` A1–A13); registry + `automation/log_run.py`; đăng ký run cũ
  (`L001_NB1v3`, `L002_NB2`, mức R); pilot P0 synthetic (`R20261124-001_P0`, `-002_P0`); kế hoạch v1.0.

## 3 việc tiếp theo (theo thứ tự ưu tiên)
1. **T2.1 + T2.2 cho RobotCar Seasons v2** (sửa A9, dựng chuỗi theo timestamp, map từ NVM) → mở khoá T3.2 (Gate G3, CCBF).
2. **T2.7** package `hmmloc` tối thiểu: forward vector hoá (torch) + test tương đương với filter numpy cũ.
3. **T1.3 novelty check cho M2** (tempering/phụ thuộc) — rủi ro novelty đã biết: HM4 (σ bandwidth), Multi-Process Fusion
   (thừa nhận phụ thuộc), Hussaini et al. 2025 (receptiveness), Carson et al. (quality weighting).

## Blockers / cần con người
- Weights descriptor bổ sung (BoQ, MegaLoc, CosPlace/EigenPlaces, NetVLAD) chưa có trong bundle → cần kernel có internet
  hoặc người tải (§11 của plan).
- Tài khoản visuallocalization.net (nộp test RobotCar/CMU) — chưa có.
- Oxford RobotCar: trang dataset báo rút dataset ngày 2026-10-22 (sub-agent đọc, **chưa xác minh**) → không đặt kết luận chính lên đó.
- RobotCar Seasons v2: query chỉ là ~460 đoạn ~9 frame → dùng cho G3/6DoF chuỗi ngắn, không cho H5/H6b.

## Câu hỏi mở cho người nghiên cứu
- Ưu tiên venue (CVPR/NeurIPS vs RA-L/ICRA) — ảnh hưởng mức đầu tư vào M5 (6DoF) so với C2 (lý thuyết).
- Có muốn thêm MSLS / Oxford RobotCar raw (cần đăng ký) không?
