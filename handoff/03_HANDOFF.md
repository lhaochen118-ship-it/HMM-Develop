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
| **Entry 19–23 (phiên 2026-11-06)** | xong: NT (E19), NT-V (E21) không qua quy tắc; L_vis (E20), μ₁/2 (E22) âm ở phát triển; **E23 OWF-HWA-S5-NT-HQ thay R* (seed 64–66)** |
| **Entry 10 — OWF (ý tưởng 2b, bộ lọc thế giới mở)** | xong: Gate 18, đăng ký trước, tập A 404 run + tập quyết định seed 25–27; D3 (điều hướng) trượt ⇒ HSI-VN giữ nguyên; `paper/BAO_CAO_OWF.pdf` |

## 3. Quyết định đã thống nhất

0. **Luật khuyến nghị (Entry 15, 2026-11-05 00:25 UTC): OWF-HWA-S5** = OWF-HWA-S với ngân hàng tỉ lệ 5 mức
   (`owf.py --qx 0.005,0.02 --scales 0.94,0.97,1.0,1.03,1.06`). Seed 52–54: 0.941 vs OWF-HWA-S 0.937 vs HSI-VN 0.823, 1/144 run > α (cùng run với
   HSI-VN), 12.67 m.
   *Luật trước đó (Entry 14, 2026-11-04 22:18 UTC): OWF-HWA-S* = OWF-HW-S ∨ bậc đồng thuận ba nguồn
   (`owf_union.py --variants "H|m(1e-5,16)|m(1e-8,2)|t(3e-4,0.5)"`). Seed 49–51: 0.933 vs 0.921 vs HSI-VN 0.804, 0 run > α, 13.64 m.
   *Luật trước đó (Entry 13, 2026-11-04 19:18 UTC): OWF-HW-S.* Các bước:
   - OWF ngân hàng tỉ lệ (`owf.py --qx 0.005,0.02 --scales 0.97,1.0,1.03`);
   - OWF-H (`owf_hybrid.py --mode xms0.9_16 --hsiframes`);
   - hợp hai bậc (`owf_union.py --variants "W(1e-5,16,1e-8,2)"`).

   Seed 46–48: 0.902 vs OWF-HU 0.878 vs HSI-VN 0.786, 1/144 run > α, sai số 12.75 m. Trước đó, Entry 12 (OWF-HU, seed 43–45: 0.896) và
   Entry 11 (OWF-H). Chi tiết: `RESEARCH_LOG.md` Entry 11–13, `handoff/AUTOLOOP.md`.
   *Luật trước đó, Entry 11, 2026-11-04 17:30 UTC: OWF-H* — OWF (Entry 10) → `owf_hybrid.py --mode xms0.9_16` → HSI-VN; tập mới seed
   40–42: recall 0.885 vs HSI-VN 0.811, 1/144 run > α, sai số 14.46 vs 15.35 m (`RESEARCH_LOG.md` Entry 11). Mục 1 bên dưới là luật trước đó.
1. **Luật khuyến nghị (đến Entry 10): HSI-VN** (`VARIANTS["HSI-VN"]`: HSI-rot-m-sc + `anchors="ver+geo"` + `train_null=True`). **Điểm vận hành điều hướng:
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
| seed 40–42 | `synchan5704/hmm-navcache-r40` (AUTOLOOP) | Entry 11 (OWF-H: F1–F3 đạt) | đã dùng |
| seed 43–45 | `synchan5704/hmm-navcache-r40` | Entry 12 (OWF-HU: G1–G3 đạt) | đã dùng |
| seed 46–48 | `synchan5704/hmm-navcache-r40` | Entry 13 (OWF-HW-S: K1–K3 đạt) | đã dùng |
| seed 49–51 | `synchan5704/hmm-navcache-r49` (kho `fr49`) | Entry 14 (OWF-HWA-S: L1–L3 đạt) | đã dùng |
| seed 52–54 | `synchan5704/hmm-navcache-r49` | Entry 15 (OWF-HWA-S5: M1–M3 đạt) | đã dùng |
| seed 55–57 | `namhunhh/hmm-navcache-r55` (kho `fr55`, 2026-11-05) | Entry 17 (xác nhận OWF-HWA-S5 + SOTA ngoài trên cùng run) | đã dùng |
| seed 58–60 | `namhunhh/hmm-navcache-r55` | Entry 19 (OWF-HWA-S5-NT: N1 trượt — cả R* cũng có 6/144 run > α; R* giữ nguyên) | đã dùng |
| seed 61–63 | `namhunhh/hmm-navcache-r61` (kho `fr61`, 2026-11-06) | Entry 21 (NT-V: V3 điều hướng trượt; NT: N3 trượt 0.07 m; R* giữ nguyên) | đã dùng |
| seed 64–66 | `namhunhh/hmm-navcache-r61` | Entry 23 (OWF-HWA-S5-NT-HQ: V1–V3 đạt ⇒ thay R*) | đã dùng |
| seed 67–69 | `namhunhh/hmm-navcache-r67` (kho `fr67`) | Entry 24 (xác nhận OWF-HWA-S5-NT-HQ + SOTA ngoài trên cùng run; điểm an toàn C10) | đã dùng |
| seed 70–72 | `namhunhh/hmm-navcache-r67` | — | **trống** |
| seed 25–27 | `caotienminh1/hmm-navcache-r19` | Entry 10 (OWF vs HSI-VN: D1 đạt, D2 đạt +0.076, D3 trượt ⇒ HSI-VN giữ nguyên) | đã dùng |

## 6b. Việc tiếp theo — cập nhật phiên 2026-11-06 (đọc trước §6a)

**Đã chốt trong phiên (Entry 19–23, `RESEARCH_LOG.md`; báo cáo `paper/BAO_CAO_S1106.pdf`).**
- **Luật khuyến nghị MỚI: OWF-HWA-S5-NT-HQ** (Entry 23, seed 64–66, V1–V3 đạt): TB segFAR 0.0074 → 0.0057, recall −0.0037, điều hướng
  14.67 → 14.51 m. Biến thể + phủ quyết ½: 0/144 run > α.
- Luật cũ OWF-HWA-S5. Trên ba nhóm seed mới 55–63 (432 run): recall 0.927–0.937, TB segFAR gộp 0.0063, 9/432 run > α
  (2.1 %). 7 trong 9 run là CMU, đến từ hai bố cục lỗ (seed 60, seed 61).
- Entry 19 (NT, không dịch chuyển tức thời) và Entry 21 (NT-V, OWF phủ quyết nhánh HSI) đều không qua quy tắc đăng ký. NT: recall bằng, TB
  segFAR thấp hơn, điều hướng ±. NT-V: hợp lệ tốt hơn, nhưng điều hướng countryside tệ hơn.
- Entry 20 (ℓ = L_vis) và Entry 22 (điểm giao μ₁/2 cho ô trống; phủ quyết chéo) âm ở phát triển.
- **Phát hiện chính:** bí danh mà odometry không thấy được. Bản sao dịch dọc một đường thẳng khớp yếu (cos 0.34–0.45 so với 0.69–0.77)
  nhưng nhất quán chuyển động. Mọi bộ lọc chuẩn hoá z theo frame đều đi theo nó (Mệnh đề 6, `paper/owf_theory.md` §9). Trên CMU có hai
  bản sao như vậy: lệch 204 m (slice 11–12) và 673 m (slice 22 ↔ 24), không đổi qua 10–17 lượt đi.

**Cập nhật 16:15 UTC (sau Entry 24–25):**
- OWF-HWA-S5-NT-HQ đã XÁC NHẬN độc lập trên seed 67–69 (Entry 24), kèm SOTA ngoài trên cùng run và điểm vận hành an toàn (+ phủ quyết ½).
- Entry 25 (phủ quyết theo mN16) phẳng.
- Kho seed: `hmm-navcache-r67` còn 70–72; kho 73–78 (`fr73-*`, 24 kernel CPU, đẩy 15:31 UTC) đang sinh. Khi xong: kéo
  `results.tar` / navcache rồi publish `hmm-navcache-r73`.
- Hướng có khoảng trống lớn nhất còn lại là **đầu chuỗi CMU**: 31 % số frame trên bản đồ nằm trong 2 excl đầu; ở đó luật báo 53–82 %,
  trong khi top-1 đúng 95–97 % (RESEARCH_LOG Entry 25). Cần một mô hình tương quan bằng chứng giữa các frame liền kề tốt hơn ℓ cố định.
  Trọng số tương quan hồ sơ 1 − r² và L_vis đã bị loại.
- Hướng thứ hai: chi phí đầu phiên ở điều kiện chưa thấy (đêm) của HQ. Co rút Bayes và chọn theo evidence đều đã thử, không thành công.

**Theo thứ tự ưu tiên (cập nhật 08:55 UTC, sau Entry 23):**
0. **Kho seed mới 67–72:** 20 kernel CPU `fr67-*` đã được đẩy lúc 08:58 UTC (xem `ENVIRONMENT_SUMMARY.md` §000 để kéo / publish
   `hmm-navcache-r67`). Kho r61 đã dùng hết. Rồi:
   - (a) kiểm OWF-HWA-S5-NT-HQ + phủ quyết ½ như điểm vận hành "an toàn";
   - (b) dự phòng đầu phiên cho điều kiện chưa thấy (đêm);
   - (c) đọc đợt tổng quát `genhq` (lỗ 10/50 %, tự nhiên, NCLT; script `ghq_cmp.sh` trong scratchpad, có bản sao ở
     `analysis/results/owf/s1106/`).
1. *(đã làm ở Entry 23)* **Emission hiệu chỉnh tuyệt đối theo điều kiện** (con đường duy nhất đã thấy để loại bí danh dịch chuyển mà không mất recall).
   - Điểm giao một-hằng-số-mỗi-run (`--lu half`) chứng minh cơ chế: CMU ÷ 4.6 báo sai. Nhưng nó sai mô hình khi điều kiện thay đổi.
   - Ứng viên: μ₁ ước lượng nhân quả theo từng chuỗi; hoặc LR trên độ tương đồng thô, hiệu chỉnh bằng phân bố "khớp đúng" của chính hậu
     nghiệm (hindsight) và phân bố "bí danh" của bản đồ (cặp ảnh xa nhau).
   - Kiểm trên tập A trước (`devlu` là mốc so sánh: `analysis/results/owf/s1106/e22_*`), rồi mới dùng seed 64–66.
2. **Seed 64–66 của `namhunhh/hmm-navcache-r61` còn trống.** Kernel `test64-*` (R* + NT-LU) đã dựng nhưng không push. Phải dựng lại với ứng
   viên mới.
3. Nếu ưu tiên hợp lệ hơn recall: C5 / C6 (phủ quyết bằng bộ lọc LU) là các luật hợp lệ nhất từng đo trên tập A (TB segFAR 0.0012–0.0018,
   0 run > α), đổi lại −2.6 … −4.5 pp recall. Có thể đăng ký như một điểm vận hành "an toàn" riêng.
4. VPR-Space: lớp quyết định quá bảo thủ trên triển khai ngắn (Entry 18). Vẫn mở.

## 6a. Việc tiếp theo — cập nhật phiên 2026-11-05 chiều (đọc trước §6 cũ)

**Đã chốt trong phiên.** Luật khuyến nghị vẫn là OWF-HWA-S5. Lớp quyết định và ngân hàng ước lượng đều đã bão hoà trong họ thiết kế hiện tại.
Bằng chứng: Entry 16, gồm ngưỡng conformal hồi cứu, biến thể bậc, β-bank, ngân hàng ±15 % — tất cả âm hoặc phẳng trên 399 run phát triển.
Bằng chứng mới cho paper:
- tổng quát trên lỗ 10/50 %, off-map tự nhiên, NCLT;
- SOTA ngoài trên cùng run;
- độ phóng đại đo được của giả định (E1) (`owf_theory.md` §7);
- Entry 17 trên seed 55–57.

**Theo thứ tự ưu tiên:**
1. **VPR-Space (tổng quát sang miền ngoài Trái Đất).**
   - Bước 1 đang / đã chạy: kernel CPU có internet `dinhthinh/vprspace-frames` stream release v0.1.0 (11 phần, 20.3 GB) qua `tar`, thu nhỏ
     frame về JPEG ≤ 322 px, giữ `poses/` + `vpr_gt/` trong output.
   - Bước 2: kernel L4 CÙNG tài khoản (`kernel_sources = dinhthinh/vprspace-frames`, không đi qua monitor vì monitor có thể chuyển tài
     khoản). Ghép các cell `nb15_src` 10/20/25 + vòng trích như `automation/make_stlucia_kernel.py`; weights từ `nhatlong1103/bundle`,
     `nhatlong1103/vpr-descriptor-weights`.
   - Bước 3: `vprlib.load_vprspace(dump, desc, setup)` (16 setup trong `rfechner/vpr-space/dataset.py`, db = bản đồ, query = truy vấn), odometry
     mô phỏng từ pose như các dataset khác, `nav_demo --cache-only` có lỗ, rồi đánh giá OWF-HWA-S5 + SOTA bằng các job hiện có.
2. **Cận cho ngân sách phóng đại K từ chính bản đồ (Mệnh đề 2′).** Đây là con đường duy nhất thấy được tới bảo đảm theo run cho các bậc cố
   định: đo mức hai nơi của bản đồ giống nhau mạnh và lâu tới đâu.
   - Cảnh báo novelty: tự phát lại bản đồ là lãnh thổ của ý tưởng 1 (SelfCal / CMS). Cần gate riêng trước khi làm.
3. **Đầu chuỗi CMU.** Khoảng trống 0.125: OWF đúng 0.95–0.99 nhưng không báo. Ở mức frame, điểm ≥ 2 + đồng thuận tách gần hoàn hảo, nhưng ở
   mức đoạn mọi nới lỏng đều thêm run vượt α. Cần một cơ chế mới, không phải hằng số mới.
4. **Seed 58–60 của `namhunhh/hmm-navcache-r55` còn trống:** dành cho quyết định đầu tiên có ứng viên vượt luật đương nhiệm trên tập A.

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
