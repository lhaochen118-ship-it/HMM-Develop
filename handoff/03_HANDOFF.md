# 03 — Handoff (cho khung chat mới, từ branch `hmm-navigation-3`)

*2026-10-31. Chỉ ghi mục tiêu, tiến độ, quyết định đã chốt, vị trí mọi thứ và việc tiếp theo. Chi tiết khoa học ở
`01_SCIENTIFIC_FINDINGS` (§N trước), vận hành ở `02_ENGINEERING_OPS_NOTES` (§0 trước). Cách đọc repo:
`05_NEW_CHAT_GUIDE.md`. Bản cũ của tài liệu này: `git show 29970dd:handoff/03_HANDOFF.md`.*

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
