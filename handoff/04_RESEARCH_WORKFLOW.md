# 04 — Research Workflow (cập nhật 2026-10-31)

*Cập nhật 2026-10-31 (branch `hmm-navigation-3`). Quy trình chuẩn của dự án (giữ tinh thần bản gốc `RESEARCH_WORKFLOW_original.pdf`) và trạng thái hiện tại của từng
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

## Trạng thái theo phase (hướng HMM-navigation, 2026-10-31)

| Phase | Trạng thái |
|---|---|
| 1 | **Xong đến Gate 10.** Gate 9 (A/A\* readiness), Gate 10 (CPC-SC+CS: CS là cơ chế đã biết, SC cùng lập luận với certified). Related work: `literature/VISUAL_LOCALIZATION_REVIEW.md` §5, §6, §6b. **Cần mở lại** cho hướng mới (bảo đảm dưới phụ thuộc, null tự sinh, hình học bản đồ) và cho TRAIL'26 / TAO'26 / VPR-auditing'26. |
| 2 | **Ý tưởng hiện có:** (A) certified sequential; (C) CPC-HMM; (D) CPC-SC+CS (Entry 25). **Chưa đủ A\*:** cần một ý tưởng mới có insight lý thuyết (xem `03` §5 Bước 1). |
| 3 | Lý thuyết: định lý theo đoạn (A), ARL₀/Shiryaev–Roberts (C), TCE (§3c), Bổ đề 7 + Mệnh đề 4 + định lý khởi phát (§3d). **Thiếu:** bảo đảm cho quyết định HMM dưới phụ thuộc thời gian. |
| 4 | **7 dataset × 6 descriptor** (RobotCar ngoài lưới điều hướng; CMU, Nordland, 4S ×3, Boreas, NCLT 8 phiên). Cache công khai 10 seed + tỷ lệ lỗ 10/50 %. Ảnh gốc có cho baseline cần ảnh (TRAIL, VPR-auditing). |
| 5 | **Vòng Entry 25 xong:** đường cong vận hành, so khớp chính xác, đăng ký trước + LODO, độ nhạy, tỷ lệ lỗ, 10 seed. Baseline có nhãn đã có: Xu'21, Claxton'24, SafeVPR (Boreas), max-sim. **Thiếu:** TRAIL'26, TAO'26, VPR-auditing'26. |
| 6 | Báo cáo ngắn `paper/BAO_CAO_PhanBien.pdf`. Bàn giao 01–05 + `ENVIRONMENT_SUMMARY`. Không viết paper. |

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
- **Đánh giá theo đường cong** (recall ở FL/segFAR khớp, so khớp chính xác tại điểm của baseline) trước khi kết luận một
  luật tốt hơn hay chỉ dè dặt hơn; điểm mặc định chỉ là một điểm trên đường cong.
- **Đăng ký trước** ứng viên/tiêu chí/tập giữ lại (commit trước khi xem), rồi chọn bằng leave-one-dataset-out.
- **Smoke-test đầu-cuối mọi cờ CLI mới** trên dữ liệu nhỏ cục bộ trước khi chạy hàng loạt trên Kaggle.
