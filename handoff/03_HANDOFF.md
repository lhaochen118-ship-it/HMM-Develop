# 03 — Handoff (branch `hmm-2nd-idea`)

*Cập nhật 2026-11-07.*
- **Phạm vi:** mục tiêu, tiến độ, quyết định đã thống nhất, vị trí mã / dữ liệu / kết quả, sổ dùng nhóm seed, việc tiếp theo. Không lặp kết quả
  (→ `01`) hay vận hành (→ `02`).
- Bản trước: `history/03_HANDOFF_through_2026-11-06.md`.

## 1. Mục tiêu nghiên cứu

Một lời giải đạt chuẩn paper A\* cho bài toán: robot camera đơn + odometry định vị theo chuỗi trên bản đồ ảnh có lỗ, quyết định báo / không báo fix
với segFAR ≤ α = 0.05 trên từng run, recall cao, sai số điều hướng thấp, không nhãn, một cấu hình cho mọi dataset. Lời giải phải khác hẳn ý tưởng 1
(phẫu thuật bản đồ phản thực, branch `hmm-navigation-5`). Yêu cầu gốc: `HMM_Navigation_Yeu_Cau_Nghien_Cuu_Cap_Nhat.docx`.

## 2. Tiến độ

| Giai đoạn | Entry | Kết quả |
|---|---|---|
| Ý tưởng 1 (branch `hmm-navigation-5`) | idea-1 Entry 12–39 | baseline SH / CST-JS; `07_IDEA1_SUMMARY.md` |
| Ý tưởng 2a: HSI (tự giám sát hồi cứu + conformal) | 1–9 | HSI-VN; nay là nhánh học của lớp quyết định |
| Ý tưởng 2b: bộ lọc thế giới mở (OWF) | 10 | recall cao nhất, đuôi hợp lệ ở CMU / Nordland |
| AUTOLOOP: OWF-H → OWF-HWA-S5 | 11–15 | union HSI ∪ bậc; ngân hàng tỉ lệ 5 mức; 5 luật qua kiểm tra tươi |
| Engine GPU, tổng quát, SOTA | 16–18 | xác nhận OWF-HWA-S5 (Entry 17); VPR-Space |
| NT, phủ quyết, bí danh dịch chuyển | 19–22 | Mệnh đề 5, 6; hai luật không qua quy tắc |
| **HQ: bằng chứng tuyệt đối hiệu chỉnh hồi cứu** | **23** | **OWF-HWA-S5-NT-HQ thay luật cũ (seed 64–66)** |
| Xác nhận độc lập + SOTA | 24, 26 | xác nhận trên 67–69 và 70–72; điểm an toàn (+ phủ quyết) xác nhận |
| Ablation, mN16, tổng quát, VPR-Space | 25, 26 | HQ mang gần hết lợi ích |
| **Kiểm toán** | **27** | sửa 2 rò rỉ nhân quả (`--lu hsq2`), chạy lại mọi số; biến thể nghiêm ngặt `hsq2s` |

## 3. Quyết định đã thống nhất

- **Luật khuyến nghị: OWF-HWA-S5-NT-HQ với mã đã kiểm toán (`--pin 0 --lu hsq2`).** Lệnh: `02` §6.
- **Điểm vận hành an toàn:** thêm `OWF_VETO=0.5` (HSI chỉ báo khi khối lượng gần bản đồ của OWF ≥ ½). Dùng khi ưu tiên hợp lệ tuyệt đối.
- Giao thức không đổi:
  - 8 dataset × 6 descriptor;
  - segFAR theo đoạn H frame, α = 0.05;
  - recall trong excl;
  - điều hướng Kalman;
  - kiểm toán theo vị trí.
- Quy trình:
  - đăng ký trước mọi quyết định;
  - mỗi nhóm seed tươi dùng một lần;
  - phát triển chỉ trên tập A;
  - mọi thành phần mới phải có lý do / mệnh đề, một cấu hình chung;
  - kiểm thử tính nhân quả cho mọi ước lượng dùng dữ liệu phiên.
- Tài nguyên:
  - dùng mọi tài khoản theo thứ tự lấp;
  - một monitor;
  - token chỉ ở `~/.kaggle/tok_*`;
  - không tạo PR; chỉ push `hmm-2nd-idea`.

## 4. Vị trí

| Thứ | Ở đâu |
|---|---|
| Mã phương pháp | `analysis/owf.py` (lọc, HQ: `hindsight_lu_causal2`), `owf_torch.py` (GPU), `owf_hsi_job.py`, `owf_hybrid.py`, `owf_union.py`, `hsi.py` |
| Đối thủ / giao thức | `analysis/sota_job.py`, `nav_demo.py`, `position_audit.py`, `vprlib.py`, `sc_eval.py`, `hcal_board.py` |
| Kiểm thử | `analysis/tests/test_hq_causality.py` |
| Vận hành Kaggle | `automation/owf_wave.py`, `fanout.py`, `central_monitor.py`, `fetch_done.py`, `publish_dataset.py` |
| Kết quả | `analysis/results/owf/s1105/` (Entry 16–18), `analysis/results/owf/s1106/` (Entry 19–27: bảng `.md`, JSON `.tgz`, script đánh giá) |
| Lý thuyết / paper / báo cáo | `paper/owf_theory.md`, `paper/OWF_paper_draft.md`, `paper/BAO_CAO_S1106.pdf`, `paper/figures/owf_shifted_alias.png` |
| Nhật ký / novelty | `RESEARCH_LOG.md` (mới nhất ở trên), `LITERATURE_GATE.md` (Gate 17–18) |
| Dataset công khai | `ENVIRONMENT_SUMMARY.md` §0.2 |
| Cách đọc repo | `06_NEXT_CHAT_GUIDE.md` |

## 5. Sổ dùng nhóm seed (mỗi nhóm một quyết định)

| Nhóm | Dataset | Dùng cho | Trạng thái |
|---|---|---|---|
| 10–12, 13–15, 16–18 | tái sinh / `caotienminh1/hmm-navcache-f13`, `f16` | Entry 7–9 (HSI) | đã dùng |
| 19–21, 22–24 | `caotienminh1/hmm-navcache-r19` (chỉ 6 dataset) | — | trống (bố cục cũ, không có Oxford / St Lucia) |
| 25–27 | `caotienminh1/hmm-navcache-r19` | Entry 10 | đã dùng |
| 40–54 | `synchan5704/hmm-navcache-r40`, `r49` | Entry 11–15 | đã dùng |
| 55–57, 58–60 | `namhunhh/hmm-navcache-r55` | Entry 17, 19 | đã dùng |
| 61–63, 64–66 | `namhunhh/hmm-navcache-r61` | Entry 21, 23 | đã dùng |
| 67–69, 70–72 | `namhunhh/hmm-navcache-r67` | Entry 24, 26 | đã dùng (cả chạy lại kiểm toán Entry 27) |
| **73–75, 76–78** | `namhunhh/hmm-navcache-r73` | — | **trống** |

## 6. Việc tiếp theo (theo ưu tiên)

1. **Literature gate cho HQ và vị trí so với ý tưởng 1** (`LITERATURE_GATE.md`, chỉ đọc paper).
   - HQ trùng nguyên lý "xoá hành lang quanh niềm tin để lấy null ngoài bản đồ theo điều kiện" với CMS (idea-1 Entry 28) và trạng thái OFF có
     hiệu chỉnh (idea-1 Entry 31).
   - Paper phải trình bày đúng: điểm mới là đặt bằng chứng đó vào ô trống của một trạng thái thế giới mở mét, với ước lượng mật độ không
     cần mô phỏng tiến.
   - Quét hệ thống: MCL / grid localisation có vùng chưa vẽ hoặc trạng thái lost; topometric; open-set VPR; change detection.
2. **Một luật quyết định thống nhất** thay union HSI ∪ ba bậc (điểm yếu novelty lớn nhất: tổ hợp kỹ thuật). Ứng viên có nguyên tắc:
   - ngưỡng posterior suy từ cận Ville với ngân sách phóng đại K ước lượng từ chính bản đồ (Mệnh đề 2′);
   - e-process trên (E1′).
   Kiểm trên tập A trước. Entry 16 (conformal hồi cứu) là bằng chứng âm cần tránh lặp.
3. **Đầu chuỗi CMU** (31 % frame trên bản đồ; luật 53–82 %, top-1 95–97 %). Thay ℓ cố định bằng một mô hình tương quan bằng chứng giữa frame
   liền kề, ước lượng trực tuyến. Đã loại: 1 − r², L_vis.
4. **Đầu phiên ở điều kiện chưa thấy** (đêm): dự phòng HQ có điều kiện. Đã loại: co rút Bayes, chọn theo evidence, theo trung vị hồ sơ.
5. **Độ nhạy hằng số** HQ (1.6 excl; 100 mẫu; khối 50) trên tập A. Hiện chưa đo.
5b. **Giảm phụ thuộc xuyên phiên** của HQ: biến thể nghiêm ngặt `hsq2s` mất lợi ích CMU trên 64–66 (Entry 27). Ứng viên: hiệu chỉnh từ chính
   bản đồ (truy vấn ảnh bản đồ với nhau, loại 1.6 excl) cho f_off trước khi phiên có mẫu riêng — không cần phiên khác.
6. **Dữ liệu lỗ thật** (thay đổi bản đồ theo thời gian) để giảm phụ thuộc vào lỗ mô phỏng.
7. **Viết paper** từ `paper/OWF_paper_draft.md`: câu chuyện "thế giới mở + bằng chứng tuyệt đối hiệu chỉnh hồi cứu"; bảng sinh từ
   `analysis/results/owf/s1106/`.

Mỗi quyết định mới: đăng ký trước, rồi một nhóm từ kho r73 (73–75, rồi 76–78). Khi hết: sinh kho mới bằng
`owf_wave.py --set fresh:79-84` (CPU, ~1.5 giờ).
