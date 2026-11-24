# 00 — READ ME FIRST (branch `hmm-2nd-idea`)

*2026-11-07. Repo `lhaochen118-ship-it/hmm-develop` (public). Không tạo PR; chỉ push `main` (từ 2026-11-24 thay cho `hmm-2nd-idea`; nhánh cũ → tag `archive/*`, xem `history/README.md`). Bản trước:
trong git (`git show cf5abef:history/<file>_through_2026-11-06.md`; đã xoá khỏi cây 2026-11-11).*

**Bài toán.** Robot camera đơn + odometry định vị theo chuỗi trên bản đồ ảnh có lỗ. Mỗi frame quyết định có báo fix hay không. Mục tiêu:
- segFAR ≤ α = 0.05 trên từng run;
- recall cao, sai số điều hướng thấp;
- không nhãn, một cấu hình cho mọi dataset.

**Luật khuyến nghị: OWF-HWA-S5-NT-HQ**, mã đã kiểm toán hai lần: `--pin 0 --lu hsq2` + nhánh HSI nhân quả `HSI-VNc`. Gồm:
- bộ lọc thế giới mở trên lưới mét (vùng có bản đồ + vùng trống + trạng thái xa);
- tự hiệu chỉnh odometry;
- không dịch chuyển tức thời;
- bằng chứng tuyệt đối hiệu chỉnh hồi cứu cho ô trống;
- lớp quyết định HSI-VNc ∪ ba bậc tin cậy OWF.

Điểm vận hành an toàn: thêm `OWF_VETO=0.5`.

**Bằng chứng.** Ba nhóm seed tươi 64–72 (432 run, đăng ký trước):
- recall ≈ 0.93;
- 3/432 run > α; với phủ quyết: 0;
- hơn nhánh HSI-VNc đứng riêng +0.12 … +0.13;
- TAO'26 / Xu'21 / Claxton'24 vượt α trên 57–89 % số run ở điểm vận hành gốc. Điểm vận hành đó KHÔNG nhắm segFAR (Entry 29).
  - Ở ngưỡng oracle theo run (cận trên, nhãn của chính run test), cả ba hợp lệ nhưng recall chỉ 0.65–0.67.
  - Luật cuối hơn +0.26…+0.28 trên cùng 288 run.
- Hạn chế mới (Entry 29b): trôi heading 0.13°/√m làm recall giảm 0.048 trên CMU / Oxford / St Lucia (St Lucia −0.145).
  - Hợp lệ giữ nguyên.
  - Odometry mô phỏng của bốn dataset vốn dùng heading thật.

Kiểm toán 2026-11-07:
- Entry 27: sửa hai rò rỉ nhân quả trong HQ;
- Entry 28: sửa nhìn trước trong nhãn hồi cứu của nhánh HSI (HSI-VNc), thêm kiểm thử nhân quả đầu-cuối.

Mọi số đã chạy lại (432 run tươi + 399 tập A + 258 tổng quát + tham chiếu). Mọi quyết định đăng ký trước giữ nguyên; số trên là số chạy lại
(`01` §2.1, §3.6, §3.7).

**Chưa đạt / đang mở:**
- lớp quyết định vẫn là tổ hợp kỹ thuật;
- HQ trùng nguyên lý với CMS của ý tưởng 1;
- lợi ích CMU của HQ dựa một phần vào hiệu chỉnh từ các phiên khác cùng môi trường (biến thể chỉ-phiên-trước mất nó trên seed 64–66);
- đầu chuỗi CMU và đầu phiên ban đêm mất recall;
- lỗ mô phỏng.

Việc tiếp theo: `03_HANDOFF.md` §6.

| File | Phạm vi (không trùng nhau) |
|---|---|
| `06_NEXT_CHAT_GUIDE.md` | **bắt đầu ở đây**: khởi động phiên, thứ tự đọc, bản đồ repo, tóm tắt việc tiếp theo |
| `01_SCIENTIFIC_FINDINGS.md` (.pdf) — PDF 1 | đóng góp, ý nghĩa, kết quả tích cực / tiêu cực, bằng chứng, điều kiện kiểm chứng |
| `02_ENGINEERING_OPS_NOTES.md` (.pdf) — PDF 2 | lập trình, môi trường, Kaggle, tổ chức thử nghiệm, lỗi và cách sửa, bài học |
| `03_HANDOFF.md` (.pdf) — PDF 3 | mục tiêu, tiến độ, quyết định, vị trí mã / dữ liệu / kết quả, sổ dùng seed, việc tiếp theo |
| `04_RESEARCH_WORKFLOW.md` (.pdf) | quy trình theo phase, trạng thái phase, nguyên tắc |
| `ENVIRONMENT_SUMMARY.md` (.pdf) | tài khoản, dataset công khai, container (§0 = hiện hành) |
| `07_IDEA1_SUMMARY.md` (.pdf) | ý tưởng 1 (baseline, phần trùng lặp) |
| `09_KIEM_TOAN_2026-11-11.md` | kiểm toán lần ba: thuật ngữ (localization, không phải navigation), tên phương pháp (LACUNA), lỗi điểm vận hành baseline, giả định heading, kế hoạch chạy lại (Entry 29) |
| `08_CHUYEN_GIAO_THEO_YEU_CAU.md` (.pdf) | đối chiếu với 5 mục của file yêu cầu docx, tự đánh giá mức A\* |
| `../paper/OWF_paper_draft.md`, `../paper/owf_theory.md`, `../paper/BAO_CAO_S1106.pdf` | bản thảo paper, lý thuyết, báo cáo phiên |
