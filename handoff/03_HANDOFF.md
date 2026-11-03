# 03 — Handoff (cho khung chat mới; mới nhất: branch `hmm-navigation-5`, §000)

*2026-10-31. Chỉ ghi mục tiêu, tiến độ, quyết định đã chốt, vị trí mọi thứ và việc tiếp theo. Chi tiết khoa học ở
`01_SCIENTIFIC_FINDINGS` (§N trước), vận hành ở `02_ENGINEERING_OPS_NOTES` (§0 trước). Cách đọc repo:
`05_NEW_CHAT_GUIDE.md`. Bản cũ của tài liệu này: `git show 29970dd:handoff/03_HANDOFF.md`.*

## 0000000000. Vòng 13 (2026-11-03, Entry 39) — trạng thái

- **Xong:** xác nhận CST-JSU [both] trên bố cục lỗ mới (seed 10–12, 108 run; 3 L4 + 36 CPU kernel) + chẩn đoán D39. H39a đạt (hợp lệ 6/6, không
  run nào > α), H39b không đạt (mép old town 0.095, Boreas 0.080), H39c đạt (giá recall −0.01…−0.04), H39d không đạt (4/6). Khuyến nghị cuối
  của ý tưởng 1: **SH ∧ CST-JS** (thực dụng), **CST-F** (chứng nhận), N = 40. Phần dư ở mép = biên định nghĩa off_d + hệ số 1/π.
- **Ý tưởng 1 khép lại ở đây;** nghiên cứu tiếp trên branch `hmm-2nd-idea` (lời giải mới hoàn toàn).
- Còn treo: navcache của 6 run Boreas (kernel `nguyenhoa99/e39g-3`) chưa tải lại được vì giới hạn API; kiểm toán Boreas dùng 12/18 run.

## 000000000. Vòng 12 (2026-11-03, Entry 38) — trạng thái

- **Xong:** lỗ ảo hình khối + CST-JSB/CST-JSU, đăng ký trước, đợt 30 kernel (402 run), kiểm toán, báo cáo `paper/BAO_CAO_E38.pdf`, theory §4h,
  null công khai `nhatlong1103/hmm-fwd-null-e38`. Kết luận: H38b không đạt ⇒ khuyến nghị Entry 37 giữ nguyên. Tăng tốc GPU 1.94× đã đưa vào code.
- **Hạn mức GPU tuần:** `nhatlong1103` hết; các acc khác đã dùng nhiều (ước 15–25 / 30 GPU-giờ). Cần thêm acc L4 nếu chạy đợt lớn trước khi reset.
- **Tiếp theo:** (1) xác nhận CST-JSU [both] trên bố cục lỗ mới (seed ≥ 10 của bộ sinh lỗ; cần navcache + thống kê chính xác + null hai họ);
  (2) đo π và hiệu ứng biên off_d ở mép; (3) bài báo.

## 00000000. Vòng 11 (2026-11-03, branch `hmm-navigation-5`, Entry 37) — trạng thái

- **Làm xong:** Entry 37 đủ: đăng ký trước → đợt Kaggle (13 L4 + St Lucia + thăm dò) → đánh giá gộp trong kernel → kiểm toán theo vị trí →
  báo cáo `paper/BAO_CAO_E37.pdf`, theory §4g, Gate 16. Kết quả và kết luận: `RESEARCH_LOG.md` Entry 37 (H37a,c,d,e,f,g đạt; H37b không đạt).
  Đợt độ bền tỷ lệ lỗ (H37h, 18 kernel `e37k-*` trên 9 acc): **đạt** 6/6 ở 10 % và 50 % lỗ (`analysis/results/e37/oc_holes_e37.tgz`).
- **Dữ liệu mới (public, nhatlong1103):** `stlucia-vpr-frames` (ảnh 10 m), `stlucia-vpr-dump` (6 descriptor), `hmm-fwd-null-e37` (null tiến
  có hiện diện, 342 run), `hmm-cms-cache-n40` (thống kê N = 40, 276 run), `hmm-e37-caches` (navcache/cms/topk/tao của Oxford + St Lucia).
- **Quyết định đã chốt:** luật thực dụng SH ∧ CST-JS; CST-F khi cần chứng nhận; N = 40 mặc định.
- **Việc tiếp theo:** (1) lỗ ảo theo hình học khối của bản đồ triển khai để đóng khoảng trống mép (H37b); (2) kiểm lại trên tập giữ ra mới;
  (3) bài báo.
- **Acc:** 10 acc user cấp (7 + anderson1202, loinguyentran, yeshenhi — yeshenhi chỉ T4); token KHÔNG trong git.

## 0000000. Vòng 10 (2026-11-02, branch `hmm-navigation-5`, Entry 36) — trạng thái

- **Làm xong:** (1) phẫu thuật tiến CST-F + hiệu chuẩn đầu-cuối CST-J/CST-J\* (`analysis/cms_fwd.py`, `oc_curves.py --fwd`, preset `@E36`),
  kiểm toán (S3-T)/(S3-F) (`analysis/cst_audit.py`); (2) N = 40 xác nhận trên CosPlace seed 1–9 (`analysis/n40_run.py`); (3) vector hoá
  (`analysis/cms_vec.py`, mặc định của `cms_exact.stats`); (4) St Lucia (`automation/make_stlucia.py`, `vprlib.load_stlucia`,
  `automation/extract_desc_cpu.py`) + SafeVPR'26 tái hiện (`analysis/safevpr26.py`, `safevpr26_eval.py`). Báo cáo `paper/BAO_CAO_E36.pdf`.
- **Đề xuất hiện tại:** **CMS-CPC/H+CSTF+G+NGRr** với N = 40 (bảo đảm theo đoạn chỉ từ phép thử hình dạng tiến, kiểm toán 9/9; recall
  thấp hơn SH 0.01–0.18) — hoặc **SH ∧ CST-J\*** (recall = SH trên 7/7 + Oxford; bảo đảm xấp xỉ: CST-J vượt α trên CMU giữ ra).
- **Không có token Kaggle trong phiên này:** mọi thứ chạy trên 4 lõi CPU ⇒ Boreas 8/18 run, N = 40 chỉ CosPlace, St Lucia chỉ CosPlace.
  Null tiến (157 MB) và cache St Lucia KHÔNG được đăng Kaggle (cần token); tái tạo bằng `e36_run.py` (tất định).
- **Việc tiếp theo:** (1) phẫu thuật tiến cả **bằng chứng hiện diện** (phép thử tuyến trên bản đồ tiến cho từng lần chạy ảo) để CST-J thành
  bảo đảm thật; (2) null chính xác cho đầu chuỗi (CMU); (3) GPU: Boreas đủ 18 run, N = 40 mọi descriptor, St Lucia 6 descriptor + đăng
  dataset (dump St Lucia, null tiến); (4) Gate 14 (novelty của mô phỏng tiến); (5) hoàn thiện bài báo.

## 000000. Vòng 9 (2026-11-01 → 02, branch `hmm-navigation-5`) — trạng thái

- **Làm xong:** E32 (độ nhạy, thời gian, NCLT mỗi phiên làm bản đồ), E33 (đối thủ mới, SHcf, Oxford RobotCar 60 run), E34 (CST, 366
  run + độ nhạy mức), E35 (SH ∧ CST). Báo cáo `paper/BAO_CAO_E32.pdf`, bản nháp bài báo `paper/cms_paper_draft.md`.
- **Đề xuất hiện tại:** **CMS-CPC/H+SH+CST+G+NGRr** (`oc_curves.py --cst`, họ `CMS-CPC/H+SH+CST+G+NGRr`): tính hợp lệ từ CST (Mệnh đề 14) với mọi dung sai SH, hiệu năng = luật SH chọn tay trên 7 dataset chính (Oxford: recall −0.029, vẫn hợp lệ); bản nhân quả = cùng luật với hiệu chuẩn `[both]`. Luật cũ CMS-CPC/H+SH+G+NGRr vẫn là đối chứng.
- **Kaggle:** luật hiện hành ở `ENVIRONMENT_SUMMARY.md` (tối đa 8 acc cùng lúc, dồn đủ 2 GPU + 5 CPU mỗi acc, bớt 1 acc mỗi lần bị
  chặn API, một tiến trình theo dõi duy nhất `automation/central_monitor.py`). Không còn kernel nào chạy.
- **Kết quả thô:** `analysis/results/e32/`, `e33/` (nb.tgz, oxford.tgz), `e34/e34.tgz`, `e35/`.
- **Việc tiếp theo:** (1) phẫu thuật "tiến" cho đoạn ở mép chuyến off-map (khoảng trống cuối của Mệnh đề 14); (2) xác nhận N = 40
  trên seed 1–9; (3) vector hoá thống kê phản thực; (4) St Lucia + so sánh trực tiếp SafeVPR'26; (5) hoàn thiện bài báo.

## 00000. Vòng 8 (2026-11-01, branch `hmm-navigation-5`) — trạng thái

- **Làm xong (Entry 30):** hiệu chuẩn nhân quả `[online]`, `[both]` (Định lý 6″, Mệnh đề 12); độ bền bộ lọc F1–F3; benchmark off-map tự
  nhiên 4Seasons chéo cảnh (`analysis/natural_eval.py`, 36 run); hai biến thể cổng (`+NGR` mở cả chuỗi, `+NGRr` giới hạn tốc độ = code
  vòng 7) + sàn bất định 3√P⁻; báo cáo `paper/BAO_CAO_E30.pdf`; kết quả `analysis/results/e30/`.
- **Đề xuất hiện tại:** **CMS-CPC/H+SH+G+NGRr** (LODO 7/7); bản triển khai nhân quả **CMS-CPCW/H+SH[both]+NGRr** (hoặc `[online]`).
- **Làm xong (Entry 31):** HMM liên hợp vị trí–hiện diện có trạng thái OFF hiệu chuẩn (`analysis/cms_hmm.py`, họ `/J`, `--joint`,
  preset `@E31J`), 114 run: chính xác về lý thuyết (biên OFF = chuỗi hiện diện, Mệnh đề 13), recall ±0.01 so với /H ở 6/7, không có lợi
  nhất quán ⇒ giữ /H. Kết quả `analysis/results/e31/`. Không còn kernel nào chạy.
- **Dataset mới:** `nhatlong1103/hmm-holes-cms-exact`, `nhatlong1103/hmm-natural-cache` (Kaggle **bỏ dấu "+" khỏi tên file**:
  `natural_regate.py` tự xử lý).
- **Việc tiếp theo:** kết quả E31 vào báo cáo; MarsLab (Isaac Sim 5.1 + ROS 2 Jazzy, cần máy RTX) để có off-map "đi ra ngoài bản đồ"
  và vòng kín; viết bài.

## 0000. Vòng 7 (2026-11-01, branch `hmm-navigation-5`) — trạng thái

- **Làm xong:** cổng rủi ro điều hướng +NGR, null phản thực chính xác (366 + 216 run), CMS-CPCW (khởi phát chặt), tự kiểm toán toàn bộ
  (`paper/AUDIT_E29.md`), thống kê ghép cặp, LODO; báo cáo `paper/BAO_CAO_E29.pdf`.
- **Đề xuất hiện tại:** **CMS-CPC/H+SH+G+NGR** (α = 0.05; LODO 7/7) — hoặc **CMS-CPCW/H+SH+NGR** khi cần định lý chặt.
- **Kaggle:** không còn kernel nào chạy. Chính sách L4 (user, 2026-11-01): QUEUED > 5 phút → huỷ + đẩy lại, tối đa 5 lần, rồi 2×T4
  (`fanout.py` tự làm).
- **Việc tiếp theo:** robot thật vòng kín; benchmark off-map tự nhiên ngoài NCLT; viết bài (novelty: Gate 12–13).

## 000. Vòng 6 (2026-11-01, branch `hmm-navigation-5`) — trạng thái

- **Làm xong:** phương pháp mới CMS (phẫu thuật bản đồ phản thực, `analysis/cms.py`), lý thuyết `paper/cms_theory.md`
  (Định lý 6, Mệnh đề 8, Hệ quả 9), đánh giá 366 run × 64 họ luật ở α = 0.05 và 0.01, nhân quả [loco], hai bán kính ρ, độ bền lỗ
  10/50 %, kiểm Định lý 6, LODO; báo cáo `paper/BAO_CAO_E28.pdf`.
- **Đề xuất hiện tại:** **CMS-CPC/H+SH ở α = 0.01** (đăng ký trước) hoặc **CMS-CPC/H+SH+G ở α = 0.01** (LODO chọn 7/7). Số liệu:
  `01` §N000.
- **Kaggle:** không còn kernel nào chạy (lô dự phòng `evlb-*` đã xoá). 10 acc vòng này (`ENVIRONMENT_SUMMARY` §3).
- **Việc tiếp theo (ưu tiên):** (1) hiệu chuẩn **rủi ro điều hướng** (không chỉ segFAR) để dùng ngân sách α = 0.05 mà không tăng
  sai số Kalman — ví dụ ngưỡng phản thực trên chính đổi mới (innovation) của bộ lọc; (2) lý thuyết/điều kiện cho S1 (khi nào phẫu
  thuật tái tạo đúng luật off-map; có thể dùng hỗn hợp nhiều bán kính ρ ∈ [off_d − excl, off_d] làm null "biên"); (3) CMU/điều kiện
  nhỏ: chia sẻ null phản thực giữa các phiên có trọng số (nhân quả [loco] đã hoạt động); (4) robot thật vòng kín; benchmark off-map
  tự nhiên ngoài NCLT.

## 00. Vòng 5 (2026-10-31) — trạng thái

- Làm xong: null chéo traversal Boreas, công suất tuyến w₃, SafeVPR/VLM trên NCLT + 4Seasons; báo cáo `paper/BAO_CAO_E27.pdf`.
- Đề xuất hiện tại: **CPC-SC-T½+CS** (an toàn: run tệ nhất ≤ 0.046, recall mặc định > CPC-SC+CS 7/7) hoặc **CPC-SC-T½+SH**
  (đường cong tốt nhất; một run CMU vượt α). Không còn kernel nào chạy. `anderson1202` đã có L4×4.

## 0. Vòng 4 (branch `hmm-navigation-4`, 2026-10-31) — trạng thái

- **Làm xong:** chẩn đoán phụ thuộc; lý thuyết §3e (Mệnh đề 5, Định lý 4 GPC, Định lý 5) và §3f; dừng hình dạng SH; họ luật
  kiểm định tuyến hiệu chuẩn bằng bản đồ (TAO-SC, CPC-SC-T); tái hiện và so sánh TAO'26, TRAIL'26, VPR-auditing'26 trên cùng
  giao thức; báo cáo `paper/BAO_CAO_E26.pdf`; dataset public `nhatlong1103/hmm-topk`.
- **Phương pháp đề xuất mới:** CPC-SC-T+SH (recall cao nhất, segFAR trung bình ≤ 0.010) hoặc CPC-SC-T+CS (cải thiện Pareto
  so với CPC-SC+CS, run tệ nhất ≤ 0.023). LODO theo sai số không phân biệt rõ các biến thể: chọn giữa hai luật theo mục tiêu
  (recall hay độ an toàn tệ nhất).
- **Kaggle:** không còn kernel nào chạy (mọi lô đã xong). 19 acc (thêm `quynhtran35`); token ở `~/.kaggle/tokens_raw` và
  `~/.kaggle/tok_<acc>` (không vào git).
- **Mức novelty:** A vững hơn, A\* chưa (Gate 11).

## 1. Mục tiêu nghiên cứu

- **Đề bài gốc:** HMM cho định vị theo chuỗi (sequence-based visual localization) với camera đơn cho robot navigation,
  nền Sattler et al. CVPR'18.
- **Mục tiêu của khung chat tiếp theo (user, 2026-10-31):**
    1. Đào sâu bản chất bài toán (toán, thống kê, mô hình) để tìm **giải pháp mới, tổng quát** (không fix theo dataset), đạt
        **score cao hơn** và **đủ novel cho hội nghị A\***; hạn chế dùng lại ý tưởng/kỹ thuật đã có.
    2. **Bảo đảm cho quyết định HMM khi các frame phụ thuộc nhau** (hiện định lý khởi phát dựa trên exchangeability; mọi cách
        hiệu chuẩn theo đoạn đều thất bại hoặc quá bảo thủ trên Boreas).
    3. **So sánh trực tiếp với TRAIL'26, TAO'26, VPR-auditing'26** (SafeVPR mới chạy trên Boreas).

## 2. Tiến độ (một dòng mỗi mục)

- **Phương pháp hiện tại:** CPC-SC+CS (`analysis/cpc_sc.py`). Trả lời được phản biện "chỉ thận trọng hơn": ở FL ≤ 1 % recall
  cao hơn Xu'21 7/7 và Claxton'24 6/7 dataset; mọi 366 run có segFAR ≤ 0.021. Số liệu: `01` §N.3.
- **Mức novelty:** A (RA-L/ICRA/IROS) khả thi, **A\* chưa** (`LITERATURE_GATE.md` Gate 9–10).
- **Điểm yếu đã biết:** CMU (descriptor mạnh) thua Claxton'24/max-sim về xếp hạng; điểm mặc định dè dặt hơn chính đường
  cong của nó; recall mặc định thấp hơn Xu'21 trên 4/7; chưa có bảo đảm dưới phụ thuộc; α = 0.01 cần ≥ 99 đoạn null.
- **Báo cáo:** `paper/BAO_CAO_PhanBien.pdf` (tiếng Việt, ngắn, không hình); lý thuyết `paper/cpc_theory.md` §3d.
- **Kaggle:** không còn kernel nào chạy; cache công khai đủ để tính lại mọi bảng trong vài phút.

## 3. Quyết định đã chốt (không bàn lại trừ khi user yêu cầu)

1. **Không viết paper.** Chỉ báo cáo PDF ngắn tiếng Việt (method + công thức, bảng, so sánh baseline, không hình), chỉ khi
   có kết quả mạnh.
2. **Không dùng nhãn của điều kiện triển khai** trong phương pháp; baseline dùng nhãn chỉ để so sánh.
3. **Giải pháp phải tổng quát:** một cấu hình cho mọi dataset/descriptor/tỷ lệ lỗ; hằng số theo đơn vị bài toán; mọi lựa
   chọn sau khi xem dữ liệu phải ghi lại và kiểm định trên tập giữ lại (đăng ký trước + leave-one-dataset-out).
4. **Novelty A\*:** mỗi ý tưởng qua gate trong `LITERATURE_GATE.md`; chỉ đọc paper (không đọc code repo của người khác);
   chỉ khẳng định "mới / tốt hơn SOTA" khi có bằng chứng thực nghiệm và đối chiếu phù hợp.
5. **Báo cáo trung thực** cả kết quả âm; tự kiểm mọi con số trước khi ghi.
6. **Tài nguyên (user chốt):**
    - Dùng **tất cả** acc được cung cấp; ưu tiên L4×4 (thiết kế để dùng cả 4 GPU, batch lớn, gần hết 96 GB), không có thì
        T4×2; **mỗi acc dùng đủ 2 phiên GPU trước khi sang acc khác**.
    - Phiên không có output ≈ 10 phút (T4) hoặc ≈ 5 phút (L4/CPU) → huỷ, thử lại tối đa 4 lần, rồi tìm nguyên nhân. Tiến
        trình treo → ngắt; không tự ngắt được → báo user.
    - Hết GPU: tác vụ rất nhẹ sang CPU; tác vụ nặng chờ GPU.
    - Thư viện/tệp phụ trợ cho chạy offline: đưa lên Kaggle Dataset **public** của `nhatlong1103`. Kết quả/code tái sử dụng:
        dataset public `nhatlong1103` hoặc thư mục trên branch.
    - **Theo dõi tự động** (waiter nền / hẹn giờ) thay vì kiểm tra thủ công liên tục; luôn tìm cách chạy song song để giảm
        thời gian mà không giảm độ chính xác.
7. **Bảo mật token:** danh sách gốc ở `~/.kaggle/tokens_raw` (chmod 600), không đưa vào prompt, code, báo cáo hay git.
8. **Git:** làm trên branch được giao; không tạo PR; commit có trailer `Co-Authored-By` / `Claude-Session`, không ghi model ID.

## 4. Vị trí mọi thứ

| Cái gì | Ở đâu |
|---|---|
| Phương pháp đề xuất | `analysis/cpc_sc.py`; luật trong `analysis/nav_rules.py` |
| Sinh cache (nặng, Kaggle) | `analysis/nav_demo.py --cache [--cache-only] [--pred] [--drop f] [--seed0 k]` |
| Đánh giá từ cache (nhẹ) | `analysis/oc_curves.py`, `oc_matched.py`, `oc_summary.py`, `lodo_select.py`, `recall_diag.py`, `nav_rules.py` |
| Cache công khai | `nhatlong1103/hmm-navcache-v2` (7 dataset × 6 desc × 10 seed), `nhatlong1103/hmm-navcache-holes` (`d10/`, `d50/`), `nhatlong1103/hmm-navcache` (cũ) |
| Dump descriptor / ảnh | `ENVIRONMENT_SUMMARY.md` §1–§2 (dump 4 benchmark, 4Seasons, Boreas, NCLT; ảnh Boreas `boreas-vpr-images-1..5`, NCLT `nclt-cam5-*`, …) |
| Kết quả Entry 25 | `analysis/results/oc_curves_entry25.tgz`, `oc_matched_entry25.tgz`, `oc_defaults_s39_holes_entry25.tgz`; bảng `paper/oc_tables.md` |
| Báo cáo | `paper/BAO_CAO_PhanBien.{md,pdf}` (`paper/build_oc_report.py` + `paper/phanbien_text.md`), `paper/BAO_CAO_CertSeq.pdf` (cũ) |
| Lý thuyết | `paper/cpc_theory.md` (§3c TCE, §3d CS/CPC-SC) |
| Nhật ký / novelty / related work | `RESEARCH_LOG.md` (Entry 25 mới nhất), `LITERATURE_GATE.md` (Gate 10), `literature/VISUAL_LOCALIZATION_REVIEW.md` |
| Hạ tầng Kaggle | `automation/fanout.py`, `make_eval_kernel.py`, `run_kernel.py`, `reattach.py`, `resume.py`, `publish_dataset.py` |

## 5. Việc tiếp theo

### Bước 0 — Khởi động (≈ 15 phút)

1. Tạo branch mới theo yêu cầu của user (thường: sao `hmm-navigation-3` thành `hmm-navigation-4`).
2. Token: lưu danh sách user gửi vào `~/.kaggle/tokens_raw`, tạo `tok_<acc>` bằng `kaggle config view` (`02` §0.2).
3. `pip install kaggle markdown xhtml2pdf scipy scikit-learn`; tải `hmm-navcache-v2` về scratchpad (1.3 GB) nếu cần phân
   tích cục bộ.

### Bước 1 — Hiểu sâu và đề xuất lời giải mới (mục tiêu A\*)

Đọc `01` §N.2/§N.4 và `paper/cpc_theory.md` §1, §3c, §3d. Ba sự thật thực nghiệm cần một lý thuyết giải thích:
(a) phép thử một bước tự xác nhận (frame liên tiếp gần như trùng nhau); (b) nhất quán odometry trên **quãng dịch chuyển**
lại phân biệt on/off rất mạnh (TPR 0.83 / FPR 0.09 mỗi frame, CMU CosPlace); (c) null tự-phát-lại của bản đồ đánh giá
thiếu phụ thuộc của đoạn off-map dài (cùng điều kiện ảnh, block ngắn) và lại quá bảo thủ cho CS.

Hướng gợi ý (chưa qua gate novelty, phải kiểm trước khi làm):
- **Bảo đảm dựa trên hình học bản đồ thay vì thống kê ảnh:** báo sai bền vững cần chuỗi vị trí bị buộc trượt trên một
  đường của bản đồ khớp hình dạng quãng odometry trong khi robot ở ngoài bản đồ. Xác suất này bị chặn bởi "phổ mơ hồ
  đường đi" của chính bản đồ (tỷ lệ đoạn đường bản đồ dài L khớp một hình dạng quỹ đạo trong ε dưới chuyển động cứng),
  tính từ pose bản đồ và mô hình sai số odometry, **không phụ thuộc phụ thuộc thời gian của ảnh**.
- **Null tự sinh từ chính query (self-null):** dịch vòng / hoán vị theo khối odometry so với chuỗi ảnh để phá liên kết
  ảnh–chuyển động nhưng giữ nguyên tự tương quan của từng dòng (kiểu kiểm định dịch vòng cho chuỗi thời gian) → null có
  đúng cấu trúc phụ thuộc và điều kiện ảnh của query.
- **Khối theo quãng đường** (không theo frame) với hệ số mixing ước lượng không nhãn, cận mất mát kiểu Barber'23 /
  blocking lemma để có bảo đảm định lượng dưới phụ thuộc.
- **Điểm vận hành không nhãn gần đường cong** (khai thác TPR/FPR của nhất quán quãng dịch chuyển) và **bằng chứng tuyệt đối
  mạnh** cho chế độ descriptor mạnh (CMU).

### Bước 2 — Bảo đảm dưới phụ thuộc (yêu cầu 2)

Mục tiêu: một định lý cho chính quyết định HMM (khởi phát và duy trì) không cần exchangeability của đoạn off-map với
đoạn bản đồ, hoặc có cận mất mát định lượng ước lượng được; kiểm thực nghiệm trên Boreas (nơi certified, W-CPC, CPC-SC
không CS đều vi phạm) và NCLT (off-map tự nhiên).

### Bước 3 — Baseline mới (yêu cầu 3; tái hiện từ paper, không đọc code)

| Baseline | Cần gì | Ghi chú |
|---|---|---|
| TRAIL'26 (CRF trên top-K MegaLoc, transition CNN trên tương quan DINOv2 cục bộ, dustbin) | ảnh + đặc trưng DINOv2 cục bộ; huấn luyện | Nặng nhất; huấn luyện trên dataset khác tập kiểm tra để công bằng |
| TAO'26 / Route-MHT (K = 100 giả thuyết, Procrustes SE(2), ràng buộc vận tốc, quyết định map-out) | top-K chỉ số + similarity mỗi frame, odometry | Cache hiện chỉ có `srt10` (giá trị, không chỉ số) → mở rộng `nav_demo --cache` lưu top-K chỉ số |
| VPR-auditing'26 (VLM xác minh cặp query–top-1) | ảnh query + ảnh bản đồ; VLM mở chạy offline trên L4 (trọng số đưa lên dataset public) | Đắt: lấy mẫu con frame; báo cả precision–coverage–FAR như paper |

Ảnh có sẵn: Boreas (`boreas-vpr-images-1..5`), 4Seasons, NCLT (`nclt-cam5-*`), CMU, RobotCar, Nordland
(`ENVIRONMENT_SUMMARY` §1–§2).

### Bước 4 — Báo cáo và bàn giao

Khi có kết quả mạnh: báo cáo PDF ngắn tiếng Việt; cập nhật 01–05, `ENVIRONMENT_SUMMARY`; commit và push.

## 6. Lưu ý chuyển giao

- Scratchpad của khung chat này (cache tải về, thư mục `runs/`) **không** sang khung mới; mọi thứ cần thiết đã ở git hoặc
  dataset public.
- Không có kernel nào đang chạy. Acc `thnliu`, `linhmai24`, `lelynhan`, `huyenco`, `mucnokieu`, `mxuanquy` có kernel của
  phiên khác (`zc-*`, `vicoqa-*`): không đụng vào.
