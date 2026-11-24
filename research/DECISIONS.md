# DECISIONS — nhật ký quyết định (ADR)

Mẫu: **D# — tiêu đề** · Ngày · Bối cảnh · Phương án · Quyết định · Lý do · Điều kiện xem lại.

### D1 — Chuyển từ "CCBF là đóng góp chính" sang "chẩn đoán → sửa gốc → mở rộng" với HMM làm trung tâm
- **Ngày:** 2026-11-24. **Bối cảnh:** CCBF ≈ fixed trên Nordland (F2, F3); kiểm toán phát hiện A1–A4 làm thí nghiệm không có
  khả năng kiểm định cơ chế; người dùng mở rộng mục tiêu sang kiểm chứng tổng quát HMM cho localization (VPR + 6DoF).
- **Phương án:** (a) tiếp tục tune CCBF; (b) bỏ HMM; (c) kế hoạch 7 giai đoạn hướng giả thuyết với CCBF thành module có điều kiện.
- **Quyết định:** (c). **Lý do:** (a) là tuning không có giả thuyết; (b) chưa có bằng chứng; (c) giữ giá trị đã có và kiểm định công bằng.
- **Xem lại khi:** Gate G2 hoặc G3 có kết quả.

### D2 — Giữ CCBF như module M4 có điều kiện, quyết định tại Gate G3 (RobotCar ngày/đêm, giao thức đã sửa A3/A4)
- **Ngày:** 2026-11-24. **Xem lại khi:** T3.2 xong.

### D3 — Không dùng ECE làm metric hiệu chỉnh chính; NLL là chính, ECE/Brier/confident-wrong là phụ
- **Ngày:** 2026-11-24. **Lý do:** F7 (pilot P0). **Xem lại khi:** không.

### D4 — "Trích một lần, thí nghiệm nhiều lần": feature bank trên Kaggle Datasets, thí nghiệm HMM chạy CPU
- **Ngày:** 2026-11-24. **Lý do:** trích descriptor là chi phí chính (≈20 ảnh/s T4 [R]); HMM trên cache tốn phút.

### D-prereg — (chờ T1.5) commit hash của bản đăng ký trước giả thuyết
