# 03 — Handoff (branch `hmm-2nd-idea`)

*Cập nhật 2026-11-04. Phạm vi: mục tiêu, tiến độ, quyết định đã thống nhất, vị trí mã / dữ liệu / kết quả, việc tiếp theo. Bằng chứng và số liệu
chi tiết → `01_SCIENTIFIC_FINDINGS`; cách chạy và bài học vận hành → `02_ENGINEERING_OPS_NOTES`; tài khoản, dataset → `ENVIRONMENT_SUMMARY`.*

## 1. Mục tiêu nghiên cứu

Lời giải A\* thứ hai (khác hẳn ý tưởng 1 — phẫu thuật bản đồ phản thực, branch `hmm-navigation-5`) cho bài toán: robot camera đơn + odometry
định vị theo chuỗi (HMM) trên bản đồ ảnh có lỗ, quyết định báo / không báo fix với bảo đảm segFAR ≤ α, recall cao, sai số điều hướng thấp, kiểm
toán theo vị trí đạt. Yêu cầu gốc: `HMM_Navigation_Yeu_Cau_Nghien_Cuu_Cap_Nhat.docx` (novelty A\*, thực nghiệm mạnh, tối ưu tài nguyên Kaggle).

## 2. Tiến độ (một dòng mỗi mốc)

| Mốc | Trạng thái |
|---|---|
| Phương pháp HSI (tự giám sát hồi cứu + hiệu chuẩn conformal trên excursion thật) | xong, `analysis/hsi.py` |
| 9 vòng đăng ký trước (Entry 1–9) | xong; quyết định cuối ở Entry 9 |
| Ba tập kiểm tra mới (seed 10–12, 13–15, 16–18) | đã dùng |
| Kho dự trữ seed 19–27 (3 tập × 108 run) | sinh bởi đợt `hsi20`, publish `caotienminh1/hmm-navcache-r19`; **chưa dùng** |
| Báo cáo `paper/BAO_CAO_HSI.pdf` (15 trang, abstract tiếng Anh) + lý thuyết Mệnh đề 1–7 | xong |
| Paper hoàn chỉnh | chưa viết (chỉ báo cáo + abstract nháp) |
| **Entry 10 — OWF (ý tưởng 2b, bộ lọc thế giới mở)** | xong: Gate 18, đăng ký trước, tập A 404 run + tập quyết định seed 25–27; D3 (điều hướng) trượt ⇒ HSI-VN giữ nguyên; `paper/BAO_CAO_OWF.pdf` |

## 3. Quyết định đã thống nhất

1. **Luật khuyến nghị: HSI-VN** (`VARIANTS["HSI-VN"]`: HSI-rot-m-sc + `anchors="ver+geo"` + `train_null=True`). **Điểm vận hành điều hướng:
   HSI-VMN** (+ `mondrian="ref"`). Luật trước HSI-rot-m-sc chỉ còn làm tham chiếu.
2. Một cấu hình chung cho mọi dataset; α = 0.05, H = 10; không tinh chỉnh theo dataset.
3. Mọi quyết định mới: đăng ký trước trong `RESEARCH_LOG.md` (commit trước khi có kết quả) và kiểm trên **một nhóm 3 seed CHƯA DÙNG của kho dự
   trữ** (19–21, rồi 22–24, rồi 25–27); ghi nhóm đã dùng vào bảng §5. Không kiểm lại cùng một giả thuyết trên tập khác sau khi đã cam kết "lần cuối".
4. Seed 0–9 là dữ liệu phát triển (được chẩn đoán tuỳ ý); tập thiết kế 28 run chỉ để đo nhanh — không đủ để kết luận về điều hướng.
5. Tiêu chí quyết định đặt theo thước đo kết quả (hợp lệ, recall, điều hướng); tiêu chí cơ chế chỉ để báo cáo (bài học Entry 8).
6. Token Kaggle không bao giờ vào repo / dataset / báo cáo; repo public. Phiên chat mới cần user cung cấp lại token (7 acc đang dùng, xem
   `ENVIRONMENT_SUMMARY.md` §0).
7. **OWF (Entry 10)** là luật hợp lệ có recall cao nhất (tập A gộp 0.863 vs HSI-VN 0.791; tập mới seed 25–27 +0.076) nhưng KHÔNG thay HSI-VN: sai số
   điều hướng kém hơn trên 4/6 dataset (Nordland, CMU, countryside, office) và 19/404 run > α (CMU, Nordland). Dùng OWF khi ưu tiên recall / tốc độ
   bắt lại sau lỗ; HSI-VN khi ưu tiên hợp lệ từng run và điều hướng.
8. Mỗi phiên chat dùng code dataset Kaggle riêng (`export VPR_CODE_DS=...`); kiểm `git log HEAD..origin/hmm-2nd-idea` trước khi bắt đầu (hai phiên đã
   chạy song song trên branch này ngày 2026-11-04).

## 4. Vị trí

| Thứ | Ở đâu |
|---|---|
| Phương pháp | `analysis/hsi.py` (`online_v2` + cờ: `anchors`, `train_null`, `mondrian`, `sc_mode`, `place_feats`, `geo_budget`, `null_oracle` (chẩn đoán), `min_lab`) |
| Biến thể có tên | `analysis/hsi_eval.py` `VARIANTS` |
| Đánh giá / so sánh / tiêu chí | `analysis/hsi_eval.py`, `hsi_compare.py`, `hsi_summary.py`, `hsi_entry8_test.py`, `hsi_alpha.py`, `hsi_lockfig.py`, `hsi_fresh.py` |
| Kaggle | `automation/` (`hsi_wave.py`, `fanout.py`, `central_monitor.py`, `hsi_collect.py`, `fetch_outputs.py`, `publish_dataset.py`, `make_eval_kernel.py`) |
| Nhật ký / lý thuyết / novelty | `RESEARCH_LOG.md` (Entry 1–9 HSI, Entry 10 OWF), `paper/hsi_theory.md`, `paper/owf_theory.md`, `LITERATURE_GATE.md` Gate 17, 18 |
| OWF (Entry 10) | `analysis/owf.py` (phương pháp + chạy một run), `analysis/owf_summary.py` (so sánh / giả thuyết / D1–D3), `automation/owf_wave.py`, `owf_collect.py`; kết quả `analysis/results/owf/*.tgz`; báo cáo `paper/BAO_CAO_OWF.(md|pdf)` |
| Báo cáo | `paper/BAO_CAO_HSI.pdf` (dựng: `paper/build_hsi_report.py`, văn bản `paper/hsi_report_text.md`, bảng `paper/tables/`, hình `paper/figures/`) |
| Kết quả thô | `analysis/results/hsi/hsi_results_json.tgz` (main / holes_d10 / holes_d50 / natural / fresh_s10_12 / test_s13_15 / test_s16_18), `hsi_frames_*.tgz`; baseline ý tưởng 1 `analysis/results/baselines_idea1/e37|e38/oc_*.tgz` |
| Cache | xem `ENVIRONMENT_SUMMARY.md` §1d, §1g (public trên Kaggle) |

## 5. Sổ dùng tập kiểm tra

| Tập | Dataset | Dùng cho | Trạng thái |
|---|---|---|---|
| seed 10–12 | (không publish; tái sinh tất định bằng `hsi_fresh.py`) | C1–C4, Entry 7 | đã dùng |
| seed 13–15 | `caotienminh1/hmm-navcache-f13` | Entry 8 | đã dùng |
| seed 16–18 | `caotienminh1/hmm-navcache-f16` | Entry 9 | đã dùng |
| seed 19–21 | `caotienminh1/hmm-navcache-r19` | — | **trống** |
| seed 22–24 | `caotienminh1/hmm-navcache-r19` | — | **trống** |
| seed 25–27 | `caotienminh1/hmm-navcache-r19` | Entry 10 (OWF vs HSI-VN: D1 đạt, D2 đạt +0.076, D3 trượt ⇒ HSI-VN giữ nguyên) | đã dùng |

## 6. Việc tiếp theo (khung chat mới)

**Việc 0 — OWF (Entry 10):** sửa sai số điều hướng mà không mất recall. Đã đo (chẩn đoán, tập A): (a) cổng nhảy dead-reckoning giữa hai lần
báo — Nordland 15.4 → ~5 m, recall −0.01; CMU không đổi; countryside xấu đi (45 → 51–57 m: chặn fix đúng sau khi VIO trôi); (b) countryside: 23 %
fix sai số 10–25 m và 7.8 % fix > excl ⇒ hậu nghiệm quá tự tin dưới VIO trôi ⇒ báo theo khối lượng trong bán kính nhỏ hơn, hoặc phương sai trôi
lớn hơn khi bằng chứng yếu; (c) đuôi hợp lệ ở đầu chuỗi (CMU 14/54 run > α; Nordland: chuỗi bắt đầu trong lỗ). Ghép OWF với lớp quyết định HSI
(HSI dùng chuỗi vị trí; OWF đặt MAP đúng 0.87–1.00 vs 0.78–0.95 của chuỗi topo). Cần tập mới: 19–21 / 22–24 hoặc sinh seed 28–30.

**Việc 1 — đào sâu bản chất để giải quyết ba điểm yếu** (chẩn đoán trên seed 0–9; quyết định trên kho dự trữ):

- *CMU (0.76 vs SH 0.835, oracle 0.945).* Khoá còn lại do chuỗi ngắn hoàn toàn đúng nhưng không thể chứng nhận. Câu hỏi mở: có thông tin nào
  (ngoài hình học ngắn — đã chứng minh vô ích ở 20–40 m — và hubness — không mở khoá) phân biệt chuỗi ngắn đúng với excursion off-map aliasing?
  Gợi ý chưa thử: tính duy nhất của giải thích ở mức chuỗi (lợi thế của SH, nhưng phải KHÁC phẫu thuật bản đồ của ý tưởng 1), học có điều kiện
  theo phiên / điều kiện ảnh, hiệu chuẩn có trọng số theo xác suất off-map ước lượng cho phần null chưa xác minh. Dữ liệu chẩn đoán đã có: 5
  cache CMU phát triển bị khoá / không khoá (SALAD s2, s4; CosPlace s1, s2, s4 — tải lại từ `hmm-navcache-v2`).
- *NCLT (2 run).* Mở rộng đánh giá: cache NCLT chỉ có seed 0 (off-map tự nhiên, không có lỗ tổng hợp); cần sinh thêm cấu hình (vd. lỗ tổng hợp
  trên bản đồ NCLT, hoặc đổi phiên làm bản đồ) bằng `nav_demo.py` với dump `nhatlong1103/nclt-vpr-dump` (`--ds` thêm dataset này).
- *Sai số điều hướng old town (32.5 m vs SH 25.9, oracle 19.3).* Không do fix sai xa; do thời điểm báo dưới VIO trôi (khoảng trống sau khi quay lại
  bản đồ). HSI-VMN giảm còn 29.0. Hướng: quyết định có xét giá trị điều hướng của một báo (độ trôi tích luỹ từ fix cuối) trong giới hạn α.

**Việc 2 — áp dụng lên 16 bộ của VPR-Space** (https://github.com/rfechner/VPR-Space; Fechner & Neubert 2026, arXiv:2610.35642):

- Đã biết (từ `dataset.py` của repo): 16 cặp `db--query` — MadMax ×6 (A0–A2, A2–A4, C0–C1, E0–E1, F0–F3, G0–G2), S3LI-Etna ×2 (crater–crater_inout,
  traverse_1–loops), LunarLoc ×2 (9–10, 15–17), SPICE ×8 (dawn / noon / night, phơi sáng `spad@5.0us`, `@2500.0us`). Bố cục:
  `images/<trajectory>/*.png` (thứ tự theo tên), `poses/<trajectory>.npy`, ground truth `vpr_gt/VPR-GT-RPE-0/<setup>.npz` với `gt_soft`, `gt_hard`.
  Tải: GitHub Releases, nhiều phần `vpr-space.tar.*` (`cat vpr-space.tar.* | tar xvf -`). Giấy phép MIT (cần xác nhận phạm vi dữ liệu).
- Chưa biết: kích thước, định dạng pose (4×4 hay 7 số), pose có phải quỹ đạo liên tục đủ để tạo odometry không, ý nghĩa chính xác `gt_soft/hard`.
- Kế hoạch: (1) kernel CPU có internet tải + giải nén, giữ trong output; (2) kernel GPU (cùng acc, mount output đó) trích 6 descriptor thành dump
  định dạng `vpr-descriptor-dumps` + `meta/` (xem `make_dump_*.py`, `nb15_src/`); (3) viết loader `vprlib.load_vprspace`, odometry từ pose có
  nhiễu tổng hợp như các dataset khác; (4) định nghĩa giao thức: bản đồ = db, truy vấn = query, off-map = vùng query ngoài phủ của db (từ pose) và /
  hoặc lỗ tổng hợp; (5) sinh cache `nav_demo --cache-only`, đánh giá HSI-VN / HSI-rot-m-sc / geo-rm / Xu'21 / oracle (không có SH nếu không có GPU).
  Ước GPU-giờ trước bước (2) và báo user nếu cần thêm acc GPU.

**Việc phụ:** viết paper từ báo cáo (abstract nháp có sẵn ở `paper/hsi_report_text.md` §1b).
