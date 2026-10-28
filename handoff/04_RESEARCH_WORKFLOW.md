# 04 — Research Workflow (cập nhật 2026-10-28)

*Quy trình chuẩn của dự án (giữ tinh thần bản gốc "Research Workflow") và trạng thái hiện tại của từng phase. Không
lặp chi tiết khoa học (`01`), vận hành (`02`) hay việc tiếp theo cụ thể (`03`).*

## Mục tiêu

Paper hạng A\* (ICRA/RA-L/IROS/CVPR/NeurIPS...). Mỗi phase lặp vòng **Generate → Critique → Verify → Improve →
Re-evaluate** cho đến khi đủ tốt. Đích cuối: gap rõ ràng, đóng góp novel, nền lý thuyết vững, bằng chứng thực nghiệm
thuyết phục, câu chuyện ở mức paper.

## Các phase

1. **Literature và gap.** Hiểu SOTA, tìm gap có giá trị, **kiểm tra trùng ý tưởng** (chỉ đọc paper, không đọc code
   repo). Mỗi ý tưởng mới phải qua một "gate" novelty, ghi vào `LITERATURE_GATE.md`.
2. **Ý tưởng.** Ưu tiên ý tưởng đơn giản nhưng có insight mạnh; mỗi thành phần phải có lý do. Tự chấm novelty,
   soundness, hiệu quả kỳ vọng và tiềm năng A\*. Chưa đủ thì quay lại.
3. **Phương pháp hoàn chỉnh.** Bài toán, input/output, toán, lý thuyết, baseline, metric, ablation, độ bền, chi phí,
   điểm mạnh/yếu. Qua A\* Quality Gate.
4. **Dữ liệu và môi trường.** Dataset, split, trọng số, package. Nhóm A: tự tải. Nhóm B: user tải rồi upload Kaggle.
   Dump descriptor để tách tính toán nặng khỏi phân tích.
5. **Hiện thực và kiểm chứng.** Chia nhỏ; kiểm tra shape, dtype, numerics, path. Thử nhỏ ở local trước rồi mới chạy
   full trên Kaggle (16 T4). Đối chiếu từng bit sau mỗi refactor.
6. **Viết paper và bàn giao.** Bảng sinh tự động từ `analysis/results/`. Tài liệu bàn giao 00–04 cùng
   environment summary.

## Trạng thái theo phase

| Phase | Trạng thái |
|---|---|
| 1 | Xong cho SelfCal: Gate 2–4 kết luận chưa thấy paper nào làm trùng toàn bộ. **Cần Gate 5** cho SelfCal-AA/Gap phiên bản cuối (strata, gate, Gap). |
| 2 | Đã pivot: CCBF → CRSG → SelfCal. Đã chốt SelfCal-AA và Gap. Seq bị loại khỏi claim. |
| 3 | Xong: method, T1–T6, baseline, ablation. Còn thiếu kiểm định độc lập các siêu tham số chọn sau-khi-xem-dữ-liệu. |
| 4 | Xong cho 4 dataset × 6 descriptor (dump public). BoQ chưa có trọng số. 4Seasons poses sẵn sàng nhưng chưa dump. |
| 5 | Xong: mọi kết quả đã chạy trên Kaggle và tái lập được. Seq/demo nằm trên branch seq. |
| 6 | Bản nháp paper hoàn chỉnh ở dạng markdown/PDF. Chưa có template LaTeX. Đã có tài liệu bàn giao. |

## Nguyên tắc làm việc (rút ra từ dự án)

- Một thí nghiệm quyết định mỗi lần, nhưng khi đã chắc thì chạy song song tối đa trên mọi GPU.
- Mọi biến thể chọn sau khi xem dữ liệu phải được ghi rõ và kiểm định trên dữ liệu mới.
- Branch ổn định không bị ghi đè; mở rộng làm trên branch riêng; kết quả mới để ở thư mục riêng.
- Báo cáo kết quả tiêu cực trung thực: chúng là phát hiện, không phải thứ cần giấu.
