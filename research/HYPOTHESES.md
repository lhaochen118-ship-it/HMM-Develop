# HYPOTHESES — bảng giả thuyết (đăng ký trước)

Định nghĩa đầy đủ, dự đoán định lượng và tiêu chí bác bỏ: `docs/MASTER_RESEARCH_PLAN.md` §5.4.
**Quy tắc:** ngưỡng chỉ được sửa trước commit pre-registration (T1.5); sau đó mọi thay đổi ghi lý do và đánh dấu *post-hoc*.

| ID | Tóm tắt | Trạng thái | Mức | Bằng chứng (run_ids) | Ghi chú |
|---|---|---|---|---|---|
| H1 | HMM đặc tả tốt > single-image (không oracle) | mở | R | L002 | L002 dùng oracle motion (A1) → chỉ là cận trên |
| H2 | Lợi ích dạng chữ U ngược theo acc single-image | mở | H | – | Cần thang descriptor (T4.3) |
| H3 | Đồng bộ khung Nordland thổi phồng lợi ích | mở | H | – | T3.1 |
| H4 | Lỗi còn lại chủ yếu aliasing lock-in + outage | mở | H | – | T4.1 |
| H5 | Bằng chứng tương quan → quá tự tin, tăng theo frame rate | mở | P | R20261124-001_P0, -002_P0 | Synthetic ủng hộ mạnh |
| H6a | β* = (1−ρ)/(1+ρ) | **bác bỏ (synthetic)** | P | R20261124-001_P0, -002_P0 | Over-temper |
| H6b | β* ≈ 1/VIF(ρ̂, L_eff) | mở | P | R20261124-001_P0, -002_P0, -003_P0b, -004_P0b | Khớp NLL-fit ±0.03; L_eff giảm khi motion std tăng (P0b) |
| H7 | LLR density-ratio + null theo place > softmax-τ | mở | H | – | |
| H8 | Tiền đề CCBF: dị biệt điều kiện (RobotCar) | mở — **Gate G3** | R | L002 (âm trên Nordland) | A3/A4 làm L002 không công bằng |
| H9 | Hiệu chỉnh hubness giảm lock-in | mở | H | – | |
| H10 | Nguyên nhân emission > transition | mở | H | – | |
| H11 | HMM điều phối verification cải thiện 6DoF đêm | mở | H | – | |
| H12 | Emission hình học loại bỏ lock-in | mở | H | – | |
| H13 | Tổng quát hoá chéo dataset | mở | H | – | |
| H14 | Thời gian thực | mở | H | – | |
| H15 | SPRT đạt tỉ lệ lỗi mục tiêu | mở | H | – | |
| H16 | ACI conformal đạt coverage dưới drift | mở | H | – | Prior art: Su et al. 2024; Silva et al. 2026 |
| H17 | Trạng thái động học khôi phục lợi ích oracle | mở | H | – | |
| H18 | Tương tác M2×M3: transition càng chính xác, lợi ích của hiệu chỉnh phụ thuộc càng lớn | mở | P | R20261124-003_P0b, -004_P0b | Kiểm ở ablation T6.3 |
