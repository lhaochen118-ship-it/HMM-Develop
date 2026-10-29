# 04 — Research Workflow (cập nhật 2026-10-29)

*Cập nhật cuối ngày 2026-10-29 (branch `hmm-navigation-2`). Quy trình chuẩn của dự án (giữ tinh thần bản gốc `RESEARCH_WORKFLOW_original.pdf`) và trạng thái hiện tại của từng
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

## Trạng thái theo phase (hướng HMM-navigation, cuối ngày 2026-10-29)

| Phase | Trạng thái |
|---|---|
| 1 | **Xong.** Gate 6 (certified sequential) và Gate 7 (CPC-HMM: IPDA, e-detectors, SAFEVPR, Xu'21) trong `LITERATURE_GATE.md`. |
| 2 | **Hai ý tưởng đã chốt.** (A) Certified sequential localization: bảo đảm theo đoạn off-map, không nhãn. (B) CPC-HMM: chuỗi vị trí bất biến affine + chuỗi hiện diện nuôi bằng e-value hiệu chuẩn bằng bản đồ. |
| 3 | **Có phương pháp và lý thuyết đầy đủ.** Định lý theo đoạn cho A; ARL₀ (Shiryaev–Roberts), độ trễ, Anderson cho B (`paper/cpc_theory.md`). |
| 4 | **Có 7 dataset × 6 descriptor.** RobotCar, CMU, Nordland, 4Seasons ×3 (VIO thật), Boreas (bánh xe + gyro thật; đã sửa lỗi bộ đếm). Có thể thêm benchmark chuỗi dài nếu cần (NCLT, Oxford RobotCar gốc). |
| 5 | **Đang lặp ở vòng CPC-HMM.** Thắng Xu'21 trên 5/7; thua Boreas (khuyết 30 %) và RobotCar. Đang chạy lưới tách p_in/p_out và fix7. |
| 6 | **Báo cáo ngắn** `paper/BAO_CAO_CertSeq.pdf` (tiếng Việt, không hình). Không viết paper. Bàn giao 00–04 + `RUNNING_KERNELS.md`. |

Lịch sử hướng trước (CCBF → CRSG → SelfCal): xem `RESEARCH_LOG.md` (Entry ≤ 17) và branch `claude/selfcal-aa`.

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
