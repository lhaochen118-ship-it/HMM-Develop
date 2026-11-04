# 04 — Research Workflow (cập nhật 2026-11-04)

*Cập nhật 2026-11-04 (branch `hmm-2nd-idea`). Quy trình chuẩn của dự án (giữ tinh thần bản gốc `RESEARCH_WORKFLOW_original.pdf`) và trạng thái hiện tại của từng
phase. Không lặp chi tiết vận hành (`02`) hay việc tiếp theo cụ thể (`00`).*

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

## Trạng thái theo phase — ý tưởng 2 (HSI, branch `hmm-2nd-idea`, 2026-11-04)

| Phase | Trạng thái |
|---|---|
| 1 | **Xong Gate 17** (`LITERATURE_GATE.md`): gần nhất Lajoie & Beltrame RA-L'23, TF-VPR, Carson'23, Claxton'24, ACI phản hồi trễ. Cần gate mới nếu thêm thành phần (vd. cho VPR-Space hoặc cho lời giải CMU). |
| 2 | **Ý tưởng chốt:** HSI = chứng chỉ hình học + nhãn hồi cứu (kể cả off-map) + conformal trên excursion thật; hai nguyên lý mới: chứng nhận rồi hiệu chuẩn, căn chỉnh Neyman–Pearson. |
| 3 | **Lý thuyết:** Mệnh đề 1–7 (`paper/hsi_theory.md`). Thiếu: bảo đảm có điều kiện theo vị trí (hiện chỉ kiểm toán thực nghiệm), phân tích độ bảo thủ của null tập cha. |
| 4 | 9 dataset × 6 descriptor (cache công khai); lỗ 10/30/50 %; off-map tự nhiên (NCLT, 4Seasons chéo cảnh); ba tập kiểm tra đã dùng + kho dự trữ seed 19–27. **Mở:** NCLT mới 2 run; VPR-Space (16 cặp) chưa có dump. |
| 5 | **Xong 9 vòng đăng ký trước**; luật khuyến nghị HSI-VN đạt 4/4 tiêu chí trên seed 16–18. Ablation đầy đủ, quét α, độ bền, tham chiếu có nhãn. |
| 6 | Báo cáo `paper/BAO_CAO_HSI.pdf` + abstract tiếng Anh nháp; bàn giao 00–04, 06 + `ENVIRONMENT_SUMMARY`. **Chưa viết paper.** |

Trạng thái theo phase của ý tưởng 1 và các hướng trước: `07_IDEA1_SUMMARY.md`, `history/`.

## Nguyên tắc làm việc (rút ra từ dự án)

- Một thí nghiệm quyết định mỗi lần, nhưng khi đã chắc thì chạy song song tối đa trên mọi GPU.
- Mọi biến thể chọn sau khi xem dữ liệu phải được ghi rõ và kiểm định trên dữ liệu mới.
- Branch ổn định không bị ghi đè; mở rộng làm trên branch riêng; kết quả mới để ở thư mục riêng.
- Báo cáo kết quả tiêu cực trung thực: chúng là phát hiện, không phải thứ cần giấu.
- Trước khi kết luận trên dataset mới: kiểm dữ liệu đầu vào (odometry, pose, thứ tự frame) bằng chẩn đoán từng frame.
  Lỗi bộ đếm Boreas đã làm hỏng một vòng chạy.
- Đo vị trí và điều kiện xảy ra lỗi (`--dump` + phân tích offline) **trước** khi đề xuất bản sửa và chạy lại.
- Chọn siêu tham số bằng lý thuyết hoặc dữ liệu không nhãn, một cấu hình chung cho mọi dataset; quét tham số chỉ là
  ablation.
- **Đánh giá theo đường cong** (recall ở FL/segFAR khớp, so khớp chính xác tại điểm của baseline) trước khi kết luận một
  luật tốt hơn hay chỉ dè dặt hơn; điểm mặc định chỉ là một điểm trên đường cong.
- **Đăng ký trước** ứng viên/tiêu chí/tập giữ lại (commit trước khi xem), rồi chọn bằng leave-one-dataset-out.
- **Smoke-test đầu-cuối mọi cờ CLI mới** trên dữ liệu nhỏ cục bộ trước khi chạy hàng loạt trên Kaggle.
- **Tập kiểm tra dùng một lần** (bổ sung 2026-11-04): mỗi quyết định rút một nhóm seed chưa dùng từ kho dự trữ công khai; ghi sổ dùng trong
  `03_HANDOFF.md` §5. Dùng lại một tập cho nhiều quyết định gây quá khớp thích nghi (đo được: lợi ích co một nửa trên dữ liệu mới).
- **Đặt tiêu chí theo thước đo kết quả** (hợp lệ, recall, điều hướng) và báo cáo tiêu chí cơ chế riêng; cam kết trước "lần kiểm cuối" cho mỗi giả
  thuyết để tránh kiểm lại tới khi đạt.
- **Chẩn đoán cơ chế trước khi đề xuất** (vd. vì sao nhánh học tắt hẳn ở CMU): đo trên dữ liệu thiết kế / phát triển bằng script nhỏ, loại ý tưởng
  không có tín hiệu trước khi tốn tài nguyên Kaggle.

