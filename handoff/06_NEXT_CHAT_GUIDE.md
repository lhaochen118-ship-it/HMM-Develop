# 06 — Hướng dẫn khung chat mới: đọc repository và việc tiếp theo

*2026-11-07, branch `hmm-2nd-idea` (repo `lhaochen118-ship-it/hmm-develop`, public).*
- Không tạo PR. Chỉ commit / push lên `hmm-2nd-idea`.
- Bản trước: `history/06_NEXT_CHAT_GUIDE_through_2026-11-06.md`.

## 1. Bắt đầu nhanh (10 phút)

1. `git fetch origin hmm-2nd-idea && git status`. Nếu local cũ và không có thay đổi riêng: `git reset --hard origin/hmm-2nd-idea`.
2. Cài gói: `pip install kaggle markdown xhtml2pdf scipy matplotlib pypdf torch`.
3. Xin người dùng token Kaggle. Lưu từng token vào `~/.kaggle/tok_<username>` (chmod 600), cập nhật `automation/active_accounts.txt` (tài khoản L4
   trước). Kiểm: `KAGGLE_API_TOKEN=$(cat ~/.kaggle/tok_X) kaggle kernels list --mine --page-size 1`.
4. Đọc theo thứ tự ở §2 (≈ 40 phút). Rồi làm việc ở §4.

## 2. Đọc theo thứ tự

| # | File | Đọc để biết |
|---|---|---|
| 1 | `handoff/00_READ_ME_FIRST.md` | trạng thái một trang, luật khuyến nghị |
| 2 | `handoff/03_HANDOFF.md` (PDF 3) | mục tiêu, tiến độ, quyết định, vị trí mã / dữ liệu / kết quả, sổ dùng seed, việc tiếp theo |
| 3 | `handoff/01_SCIENTIFIC_FINDINGS.md` (PDF 1) | đóng góp, kết quả, hạn chế, bằng chứng |
| 4 | `paper/OWF_paper_draft.md` | câu chuyện paper; §3 phương pháp, §6 thực nghiệm |
| 5 | `paper/owf_theory.md` | Mệnh đề 1–7 và mục kiểm toán §11 |
| 6 | `handoff/02_ENGINEERING_OPS_NOTES.md` (PDF 2) | cách chạy một đợt Kaggle, lỗi đã gặp |
| 7 | `handoff/ENVIRONMENT_SUMMARY.md` §0 | tài khoản, dataset công khai, container |
| 8 | `RESEARCH_LOG.md` Entry 19–27 (mới nhất ở trên cùng) | đăng ký trước + kết quả từng vòng |
| — | `handoff/04_RESEARCH_WORKFLOW.md`, `HMM_Navigation_Yeu_Cau_Nghien_Cuu_Cap_Nhat.docx` | quy trình và nguyên tắc người dùng yêu cầu |
| — | `handoff/07_IDEA1_SUMMARY.md` | ý tưởng 1 (branch `hmm-navigation-5`), baseline và phần trùng lặp |

## 3. Bản đồ repository

| Đường dẫn | Nội dung |
|---|---|
| `analysis/owf.py` | **bộ lọc thế giới mở** (lưới mét + Ω), main chạy một run; `--pin 0` (không dịch chuyển tức thời), `--lu hsq2` (bằng chứng tuyệt đối HQ, mã đã kiểm toán) |
| `analysis/owf_torch.py` | engine GPU: cả ngân hàng bộ lọc trong một tensor; xuất `mN`, `mN16` |
| `analysis/owf_hsi_job.py` | một job Kaggle: OWF rồi OWF-H / HSI-VN (`owf_hybrid.py`) trên cùng run |
| `analysis/owf_union.py` | lớp quyết định cuối: union HSI ∪ các bậc OWF; `OWF_VETO`, `OWF_VETO_KEY`, `OWF_VETO_ALL` |
| `analysis/hsi.py`, `hsi_eval.py` | nhánh HSI (tự giám sát hồi cứu + conformal; ý tưởng 2a) |
| `analysis/sota_job.py`, `tao.py`, `safevpr26*.py` | đối thủ ngoài (TAO'26, Xu'21, Claxton'24, SafeVPR'26), top-1, oracle |
| `analysis/nav_demo.py`, `position_audit.py`, `vprlib.py`, `sc_eval.py` | giao thức: cache, metric, kiểm toán vị trí, loader dataset |
| `analysis/hcal_board.py` | bảng so sánh có CI bootstrap theo run |
| `analysis/tests/test_hq_causality.py` | kiểm thử tính nhân quả của HQ (chạy trước mọi thay đổi HQ) |
| `analysis/fig_shifted_alias.py` | hình bí danh dịch chuyển (Mệnh đề 6) |
| `analysis/results/owf/s1106/` | kết quả Entry 19–27 (bảng `.md`, JSON `.tgz`, script đánh giá) |
| `automation/owf_wave.py`, `fanout.py`, `central_monitor.py`, `fetch_done.py`, `publish_dataset.py`, `md2pdf.py` | vận hành Kaggle (xem PDF 2) |
| `paper/` | bản thảo paper, lý thuyết, báo cáo phiên (`BAO_CAO_S1106.pdf` mới nhất), hình |
| `RESEARCH_LOG.md`, `LITERATURE_GATE.md` | nhật ký đăng ký trước; các gate novelty |
| `history/` | tài liệu cũ (ý tưởng 1, các phiên trước) |

## 4. Việc tiếp theo (chi tiết và lý do ở `03_HANDOFF.md` §6)

1. **Literature gate cho OWF + HQ** (`LITERATURE_GATE.md`, chỉ đọc paper). Cần đối chiếu:
   - MCL / grid localization có trạng thái "ngoài bản đồ" hoặc "lost";
   - topometric localization;
   - open-set VPR;
   - change detection trên bản đồ;
   - CMS / trạng thái OFF có hiệu chỉnh của chính ý tưởng 1 (Entry 28, 31 trong `history/RESEARCH_LOG_idea1.md`).
2. **Một luật quyết định thống nhất** thay union HSI ∪ bậc cố định. Đây là điểm yếu novelty lớn nhất (tổ hợp kỹ thuật).
3. **Đầu chuỗi CMU:** mô hình tương quan bằng chứng giữa các frame liền kề thay ℓ cố định.
4. **Đầu phiên ở điều kiện chưa thấy:** dự phòng có điều kiện cho HQ.
5. **Kiểm tra tiếp:** kho `namhunhh/hmm-navcache-r73` (seed 73–78) chưa dùng. Mỗi quyết định mới: đăng ký trước, rồi dùng một nhóm 3 seed.

## 5. Quy tắc bắt buộc (từ người dùng và từ dự án)

- Đăng ký trước mọi quyết định (commit + push trước khi kernel kiểm tra chạy); mỗi nhóm seed mới chỉ dùng một lần.
- Không ghép heuristic thuần; mọi thành phần cần lý do / mệnh đề; một cấu hình chung cho mọi dataset.
- Không tuyên bố novelty / SOTA khi chưa có bằng chứng.
- Dùng hết tài khoản Kaggle theo thứ tự lấp; một monitor duy nhất; quy tắc kẹt hàng đợi (PDF 2 §1).
- Token không bao giờ vào repo; `git grep KGAT_` trước khi kết thúc.
- Commit message kết thúc bằng các dòng attribution mà hệ thống yêu cầu.
