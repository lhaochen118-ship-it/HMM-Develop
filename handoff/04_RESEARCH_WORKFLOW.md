# 04 — Research Workflow (cập nhật 2026-11-07)

*Cập nhật 2026-11-07 (branch `hmm-2nd-idea`; bản trước: `history/04_RESEARCH_WORKFLOW_through_2026-11-06.md`). Quy trình chuẩn của dự án (giữ tinh thần bản gốc `RESEARCH_WORKFLOW_original.pdf`) và trạng thái hiện tại của từng
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

## Trạng thái theo phase — ý tưởng 2b (OWF, luật cuối OWF-HWA-S5-NT-HQ), 2026-11-07

| Phase | Trạng thái |
|---|---|
| 1 | Gate 17 (HSI), Gate 18 (OWF): không thấy công trình có (i) không gian trống trong trạng thái mét + (ii) hiện diện là hàm của vị trí. **Còn thiếu:** gate cho HQ. HQ trùng nguyên lý với CMS / trạng thái OFF có hiệu chỉnh của chính ý tưởng 1 (Entry 28, 31), cần nêu rõ. Còn thiếu một vòng quét hệ thống (MCL với vùng chưa vẽ, topometric, open-set VPR) |
| 2 | Ý tưởng chốt: bộ lọc thế giới mở + tự hiệu chỉnh odometry + không dịch chuyển tức thời + bằng chứng tuyệt đối hiệu chỉnh hồi cứu (HQ) |
| 3 | Lý thuyết `paper/owf_theory.md`: Mệnh đề 1–7, kiểm toán §11 ((E1′) cho Mệnh đề 2 khi có HQ). Thiếu: bảo đảm theo run cho lớp quyết định (union HSI ∪ bậc cố định vẫn là kỹ thuật) |
| 4 | 8 dataset × 6 descriptor; lỗ 10/30/50 %; off-map tự nhiên (4Seasons chéo cảnh, NCLT); VPR-Space (ngoài Trái Đất); các kho seed tươi r55–r73 |
| 5 | Đăng ký trước Entry 19–26. Luật cuối thay luật cũ ở Entry 23 và được xác nhận ở Entry 24, 26. Entry 27 (kiểm toán): sửa hai rò rỉ nhân quả, chạy lại mọi số trên mã đã sửa |
| 6 | Bản thảo `paper/OWF_paper_draft.md` (abstract, phương pháp, thực nghiệm, hạn chế); báo cáo `paper/BAO_CAO_S1106.pdf`; bàn giao 00–08. **Chưa viết paper hoàn chỉnh** |

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
- **Kiểm thử tính nhân quả** (bổ sung 2026-11-07) cho mọi ước lượng dùng dữ liệu của chính phiên: đổi tương lai, quá khứ phải không đổi. Mắt
  không thấy rò rỉ; kiểm thử thì thấy.
- **Script đánh giá viết từ văn bản đăng ký**, in tên luật và tiêu chí. Không sao chép script của entry trước mà không đổi luật.
- **Trước khi tuyên bố novelty: so sánh với các nhánh cũ của chính dự án.** HQ trùng nguyên lý với CMS của ý tưởng 1.

