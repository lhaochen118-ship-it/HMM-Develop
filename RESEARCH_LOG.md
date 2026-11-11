# Research Log — ý tưởng 2 (branch `hmm-2nd-idea`)

*Nhật ký thí nghiệm của lời giải mới. Entry mới đặt trên cùng. Mỗi entry: bối cảnh, giả thuyết, đăng ký trước (commit trước khi xem kết quả),
thí nghiệm, kết quả (kể cả âm), kết luận. Nhật ký của ý tưởng 1 (Entry 0–39): `history/RESEARCH_LOG_idea1.md`; tóm tắt:
`handoff/07_IDEA1_SUMMARY.md`.*

*2026-11-11: Entry 1–22 (HSI, OWF, AUTOLOOP, NT, phủ quyết, bí danh dịch chuyển) và các bảng kết quả của Entry 10 (trước đây
nằm nhầm ở đầu log) đã chuyển sang `history/RESEARCH_LOG_idea2_entries01-22.md`, nội dung giữ nguyên.*

## Entry 29 — Kiểm toán lần ba: điểm vận hành của baseline ngoài; giả định heading của odometry mô phỏng (ĐĂNG KÝ TRƯỚC, 2026-11-11)

**Bối cảnh.** Người dùng yêu cầu kiểm tra mã có lỗi làm sai score không. Chi tiết: `handoff/09_KIEM_TOAN_2026-11-11.md`.
- Không tìm thấy lỗi mã nào ở luật cuối.
  - Engine GPU so với numpy trên dữ liệu tổng hợp: quyết định khác nhau ở 0 frame tại ba ngưỡng.
  - Thử nghiệm đầu-cuối mới của OWF + HQ: tương lai của một phiên không đổi quá khứ của nó.
  - `tests/test_hq_causality.py`: PASS.
- Có lỗi ở **điểm vận hành của baseline**: Xu'21 chỉnh cho FL theo frame, Claxton'24 dùng P > 0.5, TAO'26 dùng cận inlier 3σ, trong khi giao
  thức chấm segFAR theo đoạn.
- Có một **giả định giao thức** có lợi cho OWF: odometry mô phỏng dùng heading thật.

**Đăng ký trước (commit trước khi chạy bất kỳ kernel nào của entry này).** Không quyết định gì về phương pháp; chỉ đo lại phép so sánh.

**E29a — baseline ở mục tiêu đúng.**
- Dữ liệu: seed 67–72 (288 run, cùng run của C3 Entry 24 / 26) với `baseline_recal.py` và `sota_job.py --scores`.
- Báo cho TAO'26 / Xu'21 / Claxton'24 ba điểm `@pub` / `@seg` / `@orc`: recall, TB segFAR, run > α, điều hướng.
- Luật cuối lấy từ `un2_t67Q2.json` (không chạy lại).
- Đọc:
  - (i) `@seg` hợp lệ (TB segFAR tệ nhất theo dataset ≤ α và ≤ 2 run > α): so recall cặp với luật cuối, CI bootstrap như C3.
  - (ii) `@orc` là cận trên. Nếu luật cuối có recall ≥ `@orc` của một baseline (CI dưới > 0), ghi "vượt cả ngưỡng oracle của baseline đó".
    Ngược lại, ghi đúng khoảng cách.
  - (iii) Thay câu "vượt α trên 56–90 % run" trong paper bằng bảng ba điểm vận hành, dù kết quả thế nào.

**E29b — ablation trôi heading** (tập A; không dùng nhóm seed tươi).
- Cấu hình: `ODO_YAWRW` ∈ {0, 0.13, 0.3} độ/√m; CMU, Oxford, St Lucia; trước hết CosPlace + MegaLoc, seed 1–3.
- Đo luật cuối (lệnh `02` §6), HSI-VNc độc lập và TAO dưới cùng odometry.
- Đọc:
  - Ở 0.13 (mức trôi `nav_demo.track` tự mô phỏng): nếu recall luật cuối giảm ≤ 0.02 và không có run > α, ghi "bền với trôi heading ở mức
    của bộ lọc điều hướng".
  - Ngược lại: chạy đủ 129 run, ghi là hạn chế. Ứng viên sửa có lý do: thêm chiều heading-offset vào ngân hàng tự hiệu chỉnh, chọn theo
    evidence như q / tỉ lệ (dev trước, rồi một nhóm r73).
- 0.3 là mức thử sức, chỉ mô tả.

**Kết quả E29 (ghi 2026-11-11 10:07 UTC; kernel L4 trên `duylnng` / `caotienminh1`; không dùng nhóm seed tươi).**
Bảng đầy đủ: `analysis/results/owf/s1111/` (`e29a_board_s67_72.md`, `e29b_subset18.md`, `e29b_full129.md`, JSON trong các `.tgz`).

*E29a — 288 run seed 67–72.* Ô = recall / TB segFAR / run > α / điều hướng (m). Luật cuối lấy từ `un2_t67Q2.json`, không chạy lại.
- `@pub` tái lập đúng số cũ (Claxton 0.738 / 205, Xu'21 0.694 / 164, TAO 0.836 / 256).
- Ba cột Claxton / Xu'21 tính cục bộ và trong kernel cho số trùng nhau.

| Luật | Điểm gốc (@pub) | @seg (segFAR trên 2 điều kiện dễ) | @orc (oracle theo run, cận trên) | luật cuối − @orc |
|---|---|---|---|---|
| luật cuối | 0.927 / 0.0031 / 0 / 13.3 | | | |
| Claxton'24 | 0.738 / 0.193 / 205 / 46.6 | 0.684 / 0.073 / 142 / 30.3 | 0.670 / 0.048 / 0 / 28.1 | +0.257 [+0.229, +0.284] |
| Xu'21 | 0.694 / 0.256 / 164 / 53.8 | 0.642 / 0.051 / 106 / 44.6 | 0.651 / 0.048 / 0 / 44.5 | +0.276 [+0.248, +0.307] |
| TAO'26 | 0.836 / 0.663 / 256 / 112.2 | 0.629 / 0.040 / 53 / 37.3 | 0.651 / 0.048 / 0 / 37.1 | +0.276 [+0.250, +0.303] |

Đọc theo đăng ký:
- (i) không `@seg` nào hợp lệ. Hiệu chỉnh nhãn trên điều kiện dễ không chuyển sang điều kiện khó.
- (ii) luật cuối vượt cả ngưỡng oracle của từng baseline, CI dưới > 0.
- (iii) đã thay câu "vượt α trên 56–90 % run" trong paper / handoff bằng bảng ba điểm vận hành.
- TAO tái hiện vẫn có recall < top-1 ở 5/8 dataset (ghi chú, chưa sửa).

*E29b — trôi heading* (tập A, CMU / Oxford / St Lucia; mức 0 tham chiếu = `un2_aQ2.json` của Entry 28).
- Chạy lại 18 run ở mức 0: recall chênh tối đa 0.004 / run, trung bình −0.0002. Do phép cộng nguyên tử trên GPU, không phải lỗi.
- 18 run × 3 mức, recall / TB segFAR / run > α / điều hướng:
  - luật cuối: 0.960 / 0.0018 / 0 / 11.4 → 0.917 / 0.0025 / 0 / 16.3 → 0.766 / 0.0034 / 0 / 35.0;
  - HSI-VNc: 0.864 → 0.800 → 0.653;
  - TAO'26 không đổi (khớp phép quay trên cửa sổ 20 frame).
- Mức 0.13 giảm −0.042 > 0.02, nên theo quy tắc chạy đủ 129 run:

| Tập | luật cuối, trôi 0 | luật cuối, trôi 0.13 | Δrecall [CI 95 %] | HSI-VNc 0 → 0.13 |
|---|---|---|---|---|
| CMU (54) | 0.859 / 0.0062 / 0 / 3.7 | 0.859 / 0.0056 / 0 / 3.6 | −0.0003 [−0.0013, +0.0009] | 0.752 → 0.751 |
| Oxford (45) | 0.942 / 0.0093 / 0 / 18.3 | 0.903 / 0.0087 / 0 / 19.4 | −0.040 [−0.048, −0.032] | 0.805 → 0.795 |
| St Lucia (30) | 0.985 / 0.0016 / 0 / 16.3 | 0.840 / 0.0019 / 0 / 26.4 | −0.145 [−0.179, −0.111] | 0.914 → 0.748 |
| tất cả (129) | 0.918 / 0.0062 / 0 / 11.7 | 0.870 / 0.0058 / 0 / 14.4 | −0.048 [−0.062, −0.035] | 0.808 → 0.766 |

**Kết luận E29b.**
- Không bền với trôi heading ở mức của bộ lọc điều hướng: ghi là hạn chế. Tính hợp lệ giữ nguyên (0/129 run > α; phủ quyết TB segFAR 0.0022).
- Mất mát tăng theo độ dài chuỗi: CMU (chuỗi ngắn) không đổi, St Lucia (chuỗi dài) mất nhiều nhất. HSI-VNc mất tương tự, dù chuỗi tô-pô
  `est_c` của nó vẫn tính bằng odometry sạch.
- Khi trôi, luật cuối vẫn hơn Claxton'24 @orc (0.783) +0.086 [+0.060, +0.114] và Xu'21 @orc (0.729, odometry KHÔNG trôi) +0.141
  [+0.104, +0.179]. Riêng St Lucia: Xu'21 @orc 0.859 > 0.840.
- Việc tiếp theo có lý do: thêm chiều lệch heading vào ngân hàng tự hiệu chỉnh, chọn theo evidence như q / tỉ lệ (giả thuyết, chưa kiểm:
  lệch heading làm giảm evidence tích luỹ nên chọn được theo lml). Phát triển trên tập A ở `ODO_YAWRW=0.13`, rồi đăng ký và kiểm trên r73.

## Entry 28 — Kiểm toán lần hai: nhánh HSI-VN có nhìn trước trong nhãn hồi cứu; sửa (HSI-VNc), kiểm thử đầu-cuối, chạy lại (2026-11-07 07:00 UTC)

**Bối cảnh.** Người dùng yêu cầu chạy lại bước tự kiểm tra một lần nữa. Lần này soát cả những phần Entry 27 chỉ kiểm sơ: nhánh HSI-VN, lớp
quyết định, chuỗi tô-pô `est_c`, đặc trưng của HSI, engine GPU, metric, điều hướng, đối thủ, và lại toàn bộ Mệnh đề 1–7.

**Sai tìm thấy (nhánh HSI-VN, dùng trong mọi luật union từ Entry 11):** vòng lặp trực tuyến chỉ dùng nhãn đã chốt (`avail < T`), nhưng
chính nhãn được tạo bằng đại lượng của cả đợt triển khai:
- (L1) `hindsight_bridge`: s0 (nhiễu khớp) và κ (độ trôi) là trung vị trên MỌI đoạn đã xác minh / mọi lần khép cầu, kể cả tương lai;
  chúng quyết định biên độ nhãn, tập null hiệu chỉnh và phép thử khép cầu;
- (L2) khoảng trống khép bởi đoạn phải r1 được chốt tại r1[0] + span, nhưng phép khớp phải dùng r1[:W] (chỉ xác minh xong ở r1[W−1] + span);
- (L3) bước odometry để đổi cửa sổ mét sang frame là trung vị trên cả đợt.

**Sửa:** biến thể `HSI-VNc` (cờ `causal_bridge`, `causal_step`; mặc định giữ hành vi cũ để tái lập): nhãn chốt ở hạng A chỉ dùng phần dư
khớp và lần khép cầu đã có ở A; khoảng trống chốt ở r1[min(W, |r1|) − 1] + span; bước odometry từ 20 bước đầu của đợt.

**Kiểm thử đầu-cuối** `analysis/tests/test_hsi_causality.py`: cắt ở hạng R, thay mọi dữ liệu sau R (chuỗi tô-pô, odometry, đặc trưng
ảnh) bằng rác, đếm quyết định trước R bị đổi.

| Run thiết kế | cắt | HSI-VN: quyết định quá khứ đổi | HSI-VNc |
|---|---|---|---|
| CMU s64 CosPlace | 0.2 / 0.5 / 0.8 | 1837 / 2839 / 988 | 0 / 0 / 0 |
| Nordland s65 | 0.2 / 0.5 / 0.8 | 730 / 197 / 3 | 0 / 0 / 0 |
| old town s67 | 0.2 / 0.5 / 0.8 | 586 / 508 / 165 | 0 / 0 / 0 |

Nhiễu loạn cực đoan nên con số phóng đại; trên dữ liệu thật ba run thiết kế: recall HSI-VN → HSI-VNc 0.866 → 0.870, 0.921 → 0.921,
0.909 → 0.921; segFAR 0 ở cả hai.

**Các phần kiểm lại và đúng:** bộ lọc OWF + engine GPU (chỉ tiến; chọn ngân hàng theo evidence tích luỹ); lớp quyết định (quãng đường từ
đầu, persistence, đồng thuận ba nguồn); `est_c` (DiagFilter tiến); đặc trưng HSI (`running` chỉ nhìn lùi); metric; đối thủ ngoài (chỉnh bằng
nhãn trên điều kiện dễ của cùng run, như mô tả). Mệnh đề 1, 2, 2′, 3, 5, 6, 7: chứng minh đúng; sửa hai phát biểu (N gồm nửa đường chéo ô;
λ_seed là tỉ lệ) và nêu một thiên lệch (mẫu f_off loại một đĩa 1.6 excl) — `paper/owf_theory.md` §1, §8, §10, §12.

**Chạy lại nhánh HSI bằng HSI-VNc** trên frame OWF có sẵn (mã hsq2 của Entry 27; cục bộ, 4 lõi). Quy tắc của Entry 23 / 24 / 26 áp lại
nguyên văn (`analysis/results/owf/s1106/e28_eval2.py`); đường cơ sở HSI cho C2 / C4 cũng là HSI-VNc độc lập. Ô = recall / TB segFAR /
run > α / tệ nhất / điều hướng (m):

| Nhóm | Luật cuối (hsq2 + HSI-VNc) | + phủ quyết ½ | Δrecall so với HSI-VN (Entry 27) | Quyết định |
|---|---|---|---|---|
| 64–66 | 0.9327 / 0.0058 / 3 / 0.0255 / 14.88 | 0.9237 / 0.0026 / **0** / 15.34 | +0.0005 [−0.0005, +0.0014] | Entry 23: V1, V2, V3 ĐẠT so với luật cũ cùng nhánh HSI-VNc (0.9362 / 0.0076 / 4 / 15.15) |
| 67–69 | 0.9275 / 0.0029 / **0** / 0.0096 / 12.58 | 0.9204 / 0.0007 / **0** / 12.93 | +0.0007 [−0.0002, +0.0015] | Entry 24: C1–C4, S1, S2 ĐẠT |
| 70–72 | 0.9263 / 0.0034 / **0** / 0.0087 / 14.01 | 0.9188 / 0.0013 / **0** / 14.62 | +0.0008 [−0.0001, +0.0017] | Entry 26: C1–C4, S1, S2 ĐẠT |

- Tổng 432 run tươi: **3/432 run > α** (trước: 4); phủ quyết **0/432**.
- Đường cơ sở HSI-VNc độc lập (67–69 / 70–72): 0.795 / 0.810, 0 run > α, điều hướng 14.5 / 15.4 m. Luật cuối hơn nó +0.133 [+0.115, +0.151]
  và +0.117 [+0.100, +0.133].
- Entry 23 so với luật cũ cùng nhánh HSI-VNc: run > α 4 → 3, TB segFAR 0.0076 → 0.0058, recall −0.0035 [−0.0068, −0.0006], điều hướng
  15.15 → 14.88 m.

**Tập A và tổng quát (luật cuối, HSI-VNc so với HSI-VN của Entry 27, cùng run).** Ô = recall / TB segFAR tệ nhất / run > α:

| Tập | HSI-VNc | HSI-VN (Entry 27) | Δrecall [CI 95 %] |
|---|---|---|---|
| tập A (399) | 0.9287 / 0.0093 / 0 (TB 0.0032; điều hướng 13.54 m) | 0.9285 / 0.0089 / 0 (TB 0.0034; 13.01 m) | +0.0002 [−0.0005, +0.0008] |
| lỗ 10 % (108) | 0.932 / 0.004 / 0 | 0.932 / 0.005 / 0 | +0.0002 [−0.0006, +0.0009] |
| lỗ 50 % (108) | 0.872 / 0.028 / 4 | 0.873 / 0.030 / 4 | −0.0003 [−0.0021, +0.0013] |
| off-map tự nhiên (36) | 0.945 / 0.004 / 0 | 0.943 / 0.003 / 0 | +0.0019 [+0.0004, +0.0036] |
| NCLT (6) | 0.769 / 0.001 / 0 | 0.770 / 0.002 / 0 | −0.0005 [−0.0015, +0.0004] |

- Tập A theo dataset: thay đổi ≤ 0.003 recall; CMU 0.862 → 0.859, countryside segFAR 0.0049 → 0.0024. Điều hướng tập A +0.5 m (13.0 → 13.5).
- **Mọi cột so sánh cũng dùng HSI-VNc** (đợt P4): tổng quát — luật cuối / luật cũ S5 / HSI-VNc đứng riêng: lỗ 10 % 0.932 / 0.004 / 0 | 0.933 / 0.008 / 1 |
  0.777 / 0.003 / 0; lỗ 50 % 0.872 / 0.028 / 4 | 0.894 / 0.030 / 4 | 0.751 / 0.027 / 4; tự nhiên 0.945 / 0.004 / 0 | 0.954 / 0.012 / 1 | 0.756 / 0.011 / 0;
  NCLT 0.769 / 0.001 / 0 | 0.780 / 0.003 / 0.
- Tập A, S5 + HSI-VNc → luật cuối: TB segFAR 0.0040 → 0.0032, run > α 0 → 0, recall −0.0041 [−0.0061, −0.0022], **điều hướng 12.4 → 13.5 m**
  (old town 20.9 → 29.1, Boreas 5.3 → 6.6, CMU 4.3 → 3.7, Nordland 6.2 → 5.0). Khoảng cách điều hướng lớn hơn trước kiểm toán (+0.35 m): phải
  báo như hạn chế (đầu phiên điều kiện chưa thấy).
- **Quy ước đánh giá (không phải lỗi phương pháp):** trên tập off-map tự nhiên (hai cảnh 4Seasons, hệ toạ độ khác nhau), một fix sai trong
  cảnh lạ kéo bộ lọc Kalman đi hàng chục km, nên sai số điều hướng vô nghĩa ở tập này (trung vị ~10⁵ m với CẢ hai phiên bản; các run có
  segFAR 0 cho 25–96 m). Con số này chưa từng được báo; chỉ báo recall / segFAR cho tập này.

**Biến thể nghiêm ngặt (hsq2s) với HSI-VNc** (cùng run): 64–66 0.932 / 0.0075 / 5 run > α / tệ nhất 0.036 (phủ quyết 4); 67–69 0.927 / 0 run > α;
70–72 0.926 / 0 run > α. Tổng 5/432 (phủ quyết 4/432) — như Entry 27: phụ thuộc hiệu chỉnh xuyên phiên ở CMU 64–66 không đổi.

**Tham chiếu luật cũ S5 với cùng nhánh HSI-VNc:** 64–66 0.936 / 0.0076 / 4; 67–69 0.931 / 0.0033 / 1; 70–72 0.931 / 0.0049 / 1 → 6/432 run > α
(luật cuối 3/432). V1–V3 của Entry 23 cũng đạt trên 67–69 và 70–72.

**Kết luận.** Luật khuyến nghị giữ nguyên về cấu trúc; mã khuyến nghị nay là `--pin 0 --lu hsq2` + nhánh `HSI-VNc`. Mọi quyết định đăng ký
trước của Entry 23, 24, 26 vẫn đúng khi tính lại bằng mã nhân quả ở cả hai nhánh. Kết quả: `analysis/results/owf/s1106/e28_*`.

## Entry 27 — Kiểm toán mã, công thức và lý thuyết; sửa hai rò rỉ nhân quả của HQ; chạy lại mọi kết quả (2026-11-07 04:05 UTC)

**Bối cảnh.** Người dùng yêu cầu tự kiểm tra mã, công thức, định lý trước mọi bước khác, sửa và chạy lại đến khi đúng hết.

**Phạm vi kiểm toán:**
- metric (`nav_demo.rule_metrics`: recall, segFAR theo đoạn H frame, dải mơ hồ) — khớp mô tả; không sửa;
- bộ lọc OWF (`owf.py`, `owf_torch.py`): bảo toàn khối lượng, Ω hấp thụ khi `--pin 0`, chọn ngân hàng theo evidence nhân quả — không sửa;
- lớp quyết định (`owf_union.py`): ngưỡng, thời gian tích luỹ, phủ quyết — không sửa;
- HQ (`--lu hsq`, Mệnh đề 7): **hai rò rỉ tương lai** (dưới);
- lý thuyết (`paper/owf_theory.md`): Mệnh đề 2 chưa phủ trường hợp ô trống có LR ≠ 1; Mệnh đề 7(a) cần giả thiết niềm tin khuếch tán. Đã sửa (§10, §11).

**Hai rò rỉ trong mã HQ đã kiểm tra (`--lu hsq`, dùng ở Entry 23, 24, 26):**
1. Sàn nhiễm 1 % của KDE chia cho biên độ lấy trên mẫu VÀ 50 frame của khối đang đánh giá → LR của frame t phụ thuộc tới 49 frame sau.
2. Mẫu lượt 1 được thưa với bước ⌊(số frame tự tin của cả phiên) / 3000⌋ → mẫu quá khứ nào được dùng phụ thuộc tương lai của phiên.

**Sửa:** `--lu hsq2` (`hindsight_lu_causal2`): sàn chỉ từ mẫu; dùng mọi frame tự tin. Biến thể nghiêm ngặt `--lu hsq2s`: dự phòng chỉ từ các
phiên TRƯỚC (phiên đầu không có dự phòng), để tách giả định "xuyên phiên" (một đội xe đã đi bản đồ; không phải rò rỉ trong phiên).

**Kiểm thử** `analysis/tests/test_hq_causality.py` (đổi tương lai của một phiên, so log-LR quá khứ): hsq đổi tới 0.673 (rò rỉ xác nhận);
hsq2 và hsq2s đổi 0 → PASS.

**Chạy lại (đợt `rq`, `rqdev`, `t70ref`; mã hsq2 / hsq2s, cùng run, cùng giao thức).** Quy tắc quyết định của Entry 23, 24, 26 áp lại nguyên
văn (script `analysis/results/owf/s1106/e27_rq_eval.py`).

| Nhóm | Mã | R_new recall / TB segFAR / run > α / tệ nhất / điều hướng | C10 (+ phủ quyết ½) | Δrecall so với hsq [CI 95 %] | Quyết định |
|---|---|---|---|---|---|
| 64–66 | hsq2 | 0.9323 / 0.0059 / 4 / 0.0254 / 14.56 | 0.9235 / 0.0024 / **0** | −0.0001 [−0.0002, +0.0001] | Entry 23: V1, V2, V3 ĐẠT (giữ nguyên) |
| 64–66 | hsq2s | 0.9321 / 0.0071 / 5 / 0.0366 / 14.80 | 0.9231 / 0.0044 / 4 | −0.0002 [−0.0007, +0.0002] | V1 TRƯỢT (5 vs 4 run > α) |
| 67–69 | hsq2 | 0.9268 / 0.0029 / 0 / 0.0085 / 12.53 | 0.9201 / 0.0009 / 0 | −0.0001 [−0.0003, +0.0001] | Entry 24: C1–C4 ĐẠT; S1, S2 ĐẠT |
| 67–69 | hsq2s | 0.9266 / 0.0032 / 0 / 0.0080 / 12.54 | 0.9197 / 0.0011 / 0 | −0.0004 [−0.0010, +0.0003] | C1–C4, S1, S2 ĐẠT |
| 70–72 | hsq2 | 0.9255 / 0.0035 / 0 / 0.0092 / 13.97 | 0.9181 / 0.0013 / 0 | −0.0004 [−0.0005, −0.0002] | Entry 26: C1–C4 ĐẠT; S1, S2 ĐẠT |
| 70–72 | hsq2s | 0.9252 / 0.0041 / 0 / 0.0121 / 14.06 | 0.9184 / 0.0020 / 0 | −0.0007 [−0.0013, −0.0001] | C1–C4, S1, S2 ĐẠT |
| tập A (399) | hsq2 | 0.9285 / 0.0034 / 0 / — / 13.01 | — | −0.0002 [−0.0003, −0.0000] | (phát triển) |

- Tổng 432 run tươi, hsq2: **4/432 run > α** (cả 4 ở CMU seed 64–66, như trước); C10: **0/432**.
- Tham chiếu luật cũ S5 trên 70–72 (đợt `t70ref`, báo muộn ở Entry 26): 0.931 / 0.0053 / 1 run > α / 14.19 m. Luật cuối so với nó: run > α 1 → 0, TB
  segFAR 0.0053 → 0.0035, recall −0.0053 [−0.0088, −0.0022], điều hướng 14.19 → 13.97 m (V1–V3 của Entry 23 cũng đạt trên nhóm này).
  Luật cũ trên 6 nhóm tươi 55–72: 15/864 run > α (1.7 %); luật cuối trên 64–72: 4/432 (0.9 %).
- So với HSI-VN (67–72): +0.136 [+0.118, +0.154] và +0.117 [+0.101, +0.134]. Đối thủ ngoài không đổi (không dùng HQ).
- Tập A, hsq2 so với S5: TB segFAR 0.0045 → 0.0034, run > α 1 → 0, recall −0.004; CMU 0.852 / 0.0095 → 0.862 / 0.0066; Nordland segFAR
  0.0069 → 0.0026 (như Entry 23 dev).
- Số run trùng khít với hsq: 33 / 39 / 35 trên 144 (tươi), 96 / 399 (tập A); chênh tuyệt đối recall theo run tối đa 0.008.

**Phát hiện từ biến thể nghiêm ngặt hsq2s.**
- Khác hsq2 chỉ đáng kể ở CMU seed 64–66: segFAR tệ nhất 0.0254 → 0.0366 (luật cũ S5: 0.0364), 5 run > α; C10 4 run > α.
- ⇒ Lợi ích hợp lệ của HQ ở CMU **dựa một phần vào hiệu chỉnh xuyên phiên** (transductive, cùng môi trường). Trên 67–72 hsq2s ngang hsq2.
- Paper phải nêu rõ giả định triển khai (một đội xe / nhiều phiên trên cùng bản đồ) và báo cả hai biến thể.

**Lý thuyết đã sửa (`paper/owf_theory.md`):**
- §10 Mệnh đề 7(a): thêm điều kiện "niềm tin khuếch tán".
- §11 (mới): (i) hai rò rỉ và kiểm thử; (ii) giả định xuyên phiên; (iii) Mệnh đề 2 khi có HQ cần (E1′): E[(L_t(c) Λ_t)^{w_t} | 𝓕] ≤ 1 với
  Λ_t = f_on/f_off; Λ_t là e-value dưới mật độ ngoài bản đồ thật; (iv) hằng số 1.6 excl trùng off_d của giao thức trên dữ liệu đường phố,
  chưa đo độ nhạy.

**Tổng quát (lỗ 10 / 50 %, off-map tự nhiên, NCLT) chạy lại bằng hsq2:** lỗ 10 % 0.932 / 0.005 / 0, lỗ 50 % 0.873 / 0.030 / 4, off-map tự nhiên 0.943 / 0.003 / 0, NCLT 0.770 / 0.002 / 0 (recall / TB segFAR tệ nhất / run > α) — trùng mã hsq ở ba tập đầu (37/108, 31/108, 16/36 run trùng khít, số gộp như nhau), NCLT 0.768 / 0.001 → 0.770 / 0.002.

**Kết luận.** Luật khuyến nghị giữ nguyên: OWF-HWA-S5-NT-HQ, nay là **mã đã kiểm toán `--pin 0 --lu hsq2`**. Mọi quyết định đăng ký trước của
Entry 23, 24, 26 vẫn đúng khi tính lại. Hạn chế mới phải báo: phần lợi ích CMU phụ thuộc hiệu chỉnh xuyên phiên. Kết quả lưu ở
`analysis/results/owf/s1106/e27_*`.

## Entry 26 — Xác nhận độc lập lần ba của OWF-HWA-S5-NT-HQ trên seed 70–72 — đăng ký trước (2026-11-06 16:28 UTC)

**KẾT QUẢ (seed 70–72, 144 run; đợt `test70b`; ghi 16:56 UTC). Quyết định: R_new XÁC NHẬN lần ba (C1–C4 đạt); điểm an toàn C10 XÁC NHẬN (S1 ∧
S2).** Ô = recall / TB segFAR / run > α / sai số (m):

| Dataset | R_new | C10 | HSI-VN | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|---|---|
| Boreas | 0.964 / 0.0011 / 0 / 4.2 | 0.951 / 0.0009 / 0 / 3.4 | 0.891 | 0.805 / 0.239 / 8 | 0.718 / 0.103 / 10 | 0.735 / 0.126 / 8 | 0.874 |
| CMU | 0.854 / 0.0092 / 0 / 4.4 | 0.842 / 0.0042 / 0 / 3.4 | 0.767 | 0.924 / 0.420 / 14 | 0.634 / 0.345 / 10 | 0.859 / 0.195 / 11 | 0.935 |
| Nordland | 0.974 / 0.0036 / 0 / 3.3 | 0.973 / 0.0036 / 0 / 3.3 | 0.792 | 0.812 / 0.654 / 18 | 0.744 / 0.032 / 6 | 0.521 / 0.295 / 18 | 0.667 |
| office | 0.969 / 0.0002 / 0 / 8.1 | 0.967 / 0.0002 / 0 / 8.1 | 0.864 | 0.930 / 0.737 / 18 | 0.783 / 0.285 / 10 | 0.795 / 0.183 / 12 | 0.904 |
| old town | 0.943 / 0.0002 / 0 / 19.5 | 0.937 / 0.0000 / 0 / 17.9 | 0.764 | 0.846 / 0.511 / 14 | 0.616 / 0.092 / 6 | 0.736 / 0.166 / 11 | 0.850 |
| countryside | 0.782 / 0.0025 / 0 / 29.7 | 0.762 / 0.0007 / 0 / 39.0 | 0.664 | 0.791 / 0.711 / 18 | 0.263 / 0.033 / 6 | 0.621 / 0.149 / 16 | 0.758 |
| Oxford | 0.937 / 0.0063 / 0 / 21.9 | 0.934 / 0.0003 / 0 / 21.1 | 0.813 | 0.792 / 0.996 / 18 | 0.903 / 0.826 / 18 | 0.814 / 0.183 / 14 | 0.902 |
| St Lucia | 0.984 / 0.0040 / 0 / 20.5 | 0.984 / 0.0014 / 0 / 20.1 | 0.915 | 0.812 / 0.999 / 18 | 0.907 / 0.340 / 17 | 0.833 / 0.189 / 11 | 0.893 |
| **Gộp** | **0.926 / 0.0034 / 0 / 13.95** | 0.919 / **0.0014 / 0** / 14.55 | 0.809 / 0.0026 / 0 / 15.24 | 0.839 / 0.658 / **126** | 0.696 / 0.257 / **83** | 0.739 / 0.186 / **101** | 0.848 |

Tiêu chí:
- C1 đạt: TB tệ nhất 0.0092 (CMU); 0/144 run > α.
- C2 đạt: +0.117 [+0.101, +0.134].
- C3 đạt: cả ba đối thủ ngoài không hợp lệ, recall thấp hơn (+0.087 / +0.230 / +0.187).
- C4 đạt: 13.95 so với 15.24 m.
- C10: S1 đạt (0 run > α); S2 đạt (−0.0072 [−0.0103, −0.0046]).
- Tham chiếu R_old (3 kernel S5) rơi vào tài khoản T4 chậm, nên báo sau, không ảnh hưởng quyết định.

**Ablation (mô tả, tập A, 399 run cùng run; ghi 17:11 UTC; đợt `ablhn` + `ablhm`, S5 + HQ không có NT).** Ô = recall / TB segFAR / run > α / sai số (m):

| | S5 | S5 + NT | S5 + HQ | S5 + NT + HQ (luật cuối) |
|---|---|---|---|---|
| gộp | 0.933 / 0.0045 / 1 / 12.7 | 0.932 / 0.0040 / 2 / 12.4 | 0.930 / 0.0034 / 0 / 12.9 | 0.929 / 0.0034 / 0 / 13.0 |
| CMU | 0.852 / 0.0095 / 1 / 4.4 | 0.852 / 0.0096 / 2 / 4.4 | 0.862 / 0.0066 / 0 / 3.8 | 0.863 / 0.0066 / 0 / 3.8 |
| Nordland | 0.968 / 0.0069 / 0 / 6.2 | 0.967 / 0.0053 / 0 / 5.0 | 0.972 / 0.0028 / 0 / 4.9 | 0.970 / 0.0026 / 0 / 4.7 |

- HQ mang gần hết lợi ích hợp lệ: TB segFAR −24 %, run > α 1 → 0, CMU và Nordland tốt hơn.
- NT thêm rất ít khi đã có HQ: Nordland segFAR 0.0028 → 0.0026, điều hướng 4.9 → 4.7 m; recall −0.0012.
- HQ cũng giảm phụ thuộc vào kênh re-entry: bằng chứng tuyệt đối đã ngăn hạt giống trên bí danh phát triển.

**Tổng trên ba nhóm seed tươi của luật cuối (64–72, 432 run, mỗi nhóm đăng ký trước):**
- R_new: recall gộp 0.932 / 0.927 / 0.926; **4/432 run > α (0.9 %)**, cả 4 ở CMU seed 64–66 (3 từ nhánh HSI).
- C10: 0.924 / 0.920 / 0.919; **0/432 run > α**.
- Luật cũ OWF-HWA-S5 trên 5 nhóm tươi 55–69: 1 + 6 + 2 + 4 + 1 = 14/720 run > α (1.9 %).

**Mục đích.** Thêm một nhóm seed tươi (nhóm cuối của `namhunhh/hmm-navcache-r67`, chưa dùng) để ước lượng tỉ lệ run > α của luật cuối trên
432 run tươi (64–72) thay vì 288. Cấu hình y hệt Entry 24: R_new = OWF-HWA-S5-NT-HQ; R_old = OWF-HWA-S5; C10 = R_new + phủ quyết ½. Tất cả
trên CÙNG đợt `test70b`; SOTA ngoài trên cùng run (`sota_job.py`); HSI-VN từ output `fr67-*`.

**Tiêu chí:** C1–C4 như Entry 24 (áp cho R_new), S1–S2 như Entry 24 (áp cho C10). Không có quyết định đổi luật. Đây là xác nhận; nếu C1 trượt,
ghi rõ nguồn của các run > α.

## Entry 25 — Phủ quyết theo khối lượng trong 1.6 excl (mN16) thay cho excl: KẾT QUẢ PHÁT TRIỂN PHẲNG, không đăng ký (2026-11-06 16:09 UTC)

**Ý tưởng.** Phủ quyết của C10 dùng mN = khối lượng trong excl quanh ảnh bản đồ. "Ngoài bản đồ" theo giao thức (và theo bán kính bí danh của
HQ) là xa hơn 1.6 excl. Giả thuyết: VIO trôi ngang (countryside) đặt khối lượng giữa excl và 1.6 excl, nên phủ quyết bỏ nhầm fix HSI đúng.
`owf_torch.py` xuất thêm `mN16`; `OWF_VETO_KEY=mN16 owf_union.py`.

**Phát triển:** đợt `devh16` (8 phiên L4, tập A, 399 run). Khung NT-HQ trùng hệt đợt `devhq` (tất định).

| | R_new | phủ quyết mN | phủ quyết mN16 | mN16, phủ quyết mọi báo |
|---|---|---|---|---|
| recall gộp | 0.929 | 0.923 | 0.923 | 0.923 |
| TB segFAR | 0.0034 | 0.0013 | 0.0014 | 0.0014 |
| run > α | 0 | 0 | 0 | 0 |
| countryside recall / điều hướng (m) | 0.833 / 25.7 | 0.816 / 31.2 | 0.817 / 30.9 | 0.817 / 30.9 |

**Đọc.**
- Khác biệt không đáng kể (+0.0003 recall). Chi phí ở countryside không do bán kính: ở đó hậu nghiệm OWF thật sự nằm xa bản đồ (VIO trôi,
  khớp yếu).
- Phủ quyết mọi báo, gồm cả các bậc OWF, giống hệt chỉ phủ quyết H: trên tập A, các bậc OWF của NT-HQ không báo khi mN16 < ½.
- Không đăng ký. Seed 70–72 vẫn trống (kernel `test70-*` đã dựng sẵn nhưng không push).

**VPR-Space với luật mới (mô tả; 96 run, 16 setup × 6 descriptor; chạy cục bộ).** Ô = recall / TB segFAR tệ nhất / run > α:
- OWF-HWA-S5: 0.292 / 0.0001 / 0;
- NT: 0.282 / 0.0001 / 0;
- **NT-HQ: 0.281 / 0.0001 / 0**; NT-HQ + phủ quyết: 0.281;
- TAO'26: 0.629 / 0.244 / 24; Xu'21: 0.498 / 0.008 / 5; Claxton'24: 0.441 / 0.013 / 8; oracle: 0.562.

HQ không tác dụng ở đây, đúng như thiết kế: mỗi setup chỉ có một phiên truy vấn ngắn (54–1683 frame), không có phiên khác để hiệu chỉnh, và
phiên tự thân hiếm khi đủ 100 mẫu, nên lu = 0. Khoảng cách tới oracle vẫn do lớp quyết định quá bảo thủ trên triển khai ngắn (Entry 18).

**Chẩn đoán phụ: khoảng trống recall của CMU so với oracle một-frame** (NT-HQ, tập A, 54 run; recall theo quãng đường từ đầu chuỗi):

| quãng đường (excl) | tỉ lệ frame trên bản đồ | luật | top-1 đúng | OWF ≥ 0.99 và đúng | nhánh H |
|---|---|---|---|---|---|
| [0, 0.5) | 0.08 | 0.53 | 0.97 | 0.42 | 0.53 |
| [0.5, 1) | 0.08 | 0.78 | 0.97 | 0.71 | 0.61 |
| [1, 2) | 0.15 | 0.82 | 0.95 | 0.81 | 0.60 |
| [2, 4) | 0.25 | 0.89 | 0.95 | 0.90 | 0.75 |
| [4, 8) | 0.36 | 0.94 | 0.94 | 0.96 | 0.89 |

- Chuỗi CMU ngắn và đa số bắt đầu trên bản đồ. Khoảng trống so với oracle (~0.12) nằm gần hết trong 2 excl đầu.
- Nguyên nhân là tốc độ đếm bằng chứng theo quãng đường (ℓ = 0.4 excl; frame CMU cách ~2.4 m). Đây là sự thận trọng có nguyên tắc: bỏ ℓ thì
  mọi run vượt α (Entry 10); trọng số tương quan hồ sơ 1 − r² đã bị loại trước đó.
- Lấp khoảng này cần một mô hình tương quan bằng chứng tốt hơn. Để mở.

## Entry 24 — Xác nhận độc lập OWF-HWA-S5-NT-HQ trên nhóm seed mới 67–69, SOTA ngoài trên CÙNG run, và điểm vận hành an toàn — đăng ký trước (2026-11-06 14:41 UTC)

**KẾT QUẢ (seed 67–69, 144 run; đợt `test67`, 9 phiên L4; ghi 15:25 UTC). Quyết định: R_new = OWF-HWA-S5-NT-HQ XÁC NHẬN (C1–C4 đều đạt).
Điểm vận hành an toàn C10 XÁC NHẬN (S1 ∧ S2).** Ô = recall / TB segFAR / run > α / sai số (m), trên CÙNG run:

| Dataset | R_new | R_old (S5) | C10 (+ phủ quyết) | HSI-VN | TAO'26 | Xu'21 | Claxton'24 | oracle |
|---|---|---|---|---|---|---|---|---|
| Boreas | 0.973 / 0.0012 / 0 / 5.3 | 0.980 / 0.0009 / 0 / 4.1 | 0.968 / 0.0007 / 0 / 2.9 | 0.905 | 0.802 / 0.325 / 10 | 0.702 / 0.071 / 4 | 0.748 / 0.177 / 11 | 0.881 |
| CMU | 0.803 / 0.0048 / 0 / 3.1 | 0.788 / 0.0076 / 1 / 3.2 | 0.795 / 0.0021 / 0 / 2.9 | 0.651 | 0.913 / 0.372 / 16 | 0.778 / 0.584 / 15 | 0.847 / 0.198 / 15 | 0.924 |
| Nordland | 0.969 / 0.0029 / 0 / 3.0 | 0.968 / 0.0039 / 0 / 3.2 | 0.968 / 0.0029 / 0 / 3.0 | 0.798 | 0.812 / 0.675 / 18 | 0.749 / 0.030 / 4 | 0.532 / 0.283 / 18 | 0.678 |
| office | 0.960 / 0.0011 / 0 / 9.9 | 0.967 / 0.0009 / 0 / 9.5 | 0.959 / 0.0000 / 0 / 9.7 | 0.858 | 0.933 / 0.729 / 18 | 0.638 / 0.239 / 9 | 0.786 / 0.147 / 9 | 0.908 |
| old town | 0.944 / 0.0004 / 0 / 20.2 | 0.956 / 0.0000 / 0 / 18.3 | 0.937 / 0.0000 / 0 / 17.8 | 0.718 | 0.839 / 0.512 / 14 | 0.600 / 0.033 / 4 | 0.731 / 0.175 / 11 | 0.844 |
| countryside | 0.834 / 0.0037 / 0 / 23.3 | 0.858 / 0.0034 / 0 / 22.7 | 0.808 / 0.0002 / 0 / 32.9 | 0.672 | 0.785 / 0.750 / 18 | 0.304 / 0.236 / 11 | 0.620 / 0.269 / 18 | 0.750 |
| Oxford | 0.950 / 0.0084 / 0 / 21.0 | 0.953 / 0.0086 / 0 / 20.8 | 0.945 / 0.0010 / 0 / 20.1 | 0.828 | 0.792 / 0.992 / 18 | 0.867 / 0.521 / 18 | 0.808 / 0.164 / 11 | 0.901 |
| St Lucia | 0.983 / 0.0026 / 0 / 14.6 | 0.978 / 0.0026 / 0 / 14.8 | 0.983 / 0.0000 / 0 / 14.1 | 0.897 | 0.792 / 0.990 / 18 | 0.900 / 0.334 / 16 | 0.830 / 0.186 / 11 | 0.891 |
| **Gộp** | **0.927 / 0.0031 / 0 / 12.55** | 0.931 / 0.0035 / 1 / 12.07 | 0.920 / **0.0009 / 0** / 12.93 | 0.791 / 0.0030 / 0 / 15.5 | 0.834 / 0.668 / **130** | 0.692 / 0.256 / **81** | 0.738 / 0.200 / **104** | 0.847 |

Tiêu chí:
- **C1 đạt:** TB segFAR tệ nhất 0.0084 (Oxford); **0/144 run > α**.
- **C2 đạt:** R_new − HSI-VN = **+0.136**, CI [+0.118, +0.155].
- **C3 đạt:** TAO'26, Xu'21, Claxton'24 đều KHÔNG hợp lệ (130 / 81 / 104 run > α). Recall của R_new còn cao hơn chúng +0.093 / +0.235 / +0.189,
  CI đều > 0.
- **C4 đạt:** 12.55 so với 15.48 m.
- Nhắc lại Entry 23 (R_new so với R_old): run > α 0 so với 1; TB segFAR 0.0031 so với 0.0035; recall −0.0040 [−0.0073, −0.0009]; điều hướng
  +0.48 m (countryside / Boreas / old town).
- **C10:** S1 đạt (0 run > α, TB tệ nhất 0.0029, gộp 0.0009); S2 đạt (−0.0066 [−0.0089, −0.0046]).

**Đọc.**
- (i) R_new vượt oracle một-frame (0.847) thêm +0.080 recall với 0 run > α.
- (ii) Mọi đối thủ ngoài đều vượt α trên phần lớn run, dù ngưỡng của họ được chỉnh bằng NHÃN.
- (iii) Cái giá so với luật cũ nằm đúng chỗ đã biết: đầu phiên khác điều kiện, gồm countryside −0.024 và old town −0.012.
- (iv) Trên hai nhóm seed mới (64–69, 288 run), R_new có 4 run > α (64–66, CMU, 3 từ nhánh HSI) và 0 run > α (67–69). C10 có 0 + 0.

**Phát triển phụ đã xem trước kết quả này (không đổi luật):**
- `--lu hsb` (co rút Bayes): đêm old town 0.632, không tốt hơn hsq.
- `--lu hsqsel` (lấy tập (trung tính, hsq) làm một chiều của ngân hàng, chọn theo evidence): evidence vẫn chọn hsq ở phiên đêm
  (lsel = 1.0), không đổi kết quả. Cùng kiểu thất bại với ngân hàng β (Entry 16): evidence thưởng cho mô hình linh hoạt hơn.

**Bối cảnh.** Entry 23 đưa OWF-HWA-S5-NT-HQ (R_new) lên luật khuyến nghị trên seed 64–66. Một nhóm seed mới nữa là cần để xác nhận độc
lập, như Entry 17 đã làm cho luật trước.
- Kho: `namhunhh/hmm-navcache-r67` (seed 67–72, 288 cache, sinh bằng 20 kernel CPU `fr67-*`).
- Seed 67–69 chưa dùng.
- Thêm đối thủ ngoài trên CÙNG run (`sota_job.py`): TAO'26, Xu'21, Claxton'24, top-1, oracle một-frame. HSI-VN lấy từ output `fr67-*`.

**Phát triển trước khi đăng ký (chỉ mô tả, đã xem):**
- Nới bậc ngưỡng trên khung NT-HQ của tập A (399 run): +0.0008 … +0.0043 recall, nhưng run > α tăng tới 3. Lớp quyết định vẫn bão hoà, nên
  không đổi luật.
- Co rút Bayes cho hiệu chỉnh đầu phiên (`--lu hsb`): không cứu được đầu phiên đêm old town (0.632 so với 0.664 của hsq). Không dùng.

**Luật kiểm tra:** R_new = OWF-HWA-S5-NT-HQ, đúng cấu hình Entry 23. Tham chiếu: R_old = OWF-HWA-S5. Tất cả trong CÙNG đợt `test67` trên CÙNG 144 run.

**Tiêu chí (như Entry 17, áp cho R_new):**
- **C1 (hợp lệ tuyệt đối):** TB segFAR ≤ α trên 8/8 dataset và ≤ 2/144 run > α.
- **C2:** recall R_new − HSI-VN ≥ +0.08 với cận dưới CI 95 % > 0.
- **C3:** mỗi đối thủ ngoài (TAO'26, Xu'21, Claxton'24) hoặc không hợp lệ, hoặc recall thấp hơn R_new với cận dưới CI > 0.
- **C4:** sai số điều hướng R_new ≤ HSI-VN.

**Nhắc lại Entry 23 (V1–V3 so với R_old):** báo cáo; không đổi quyết định đã có.

**Điểm vận hành an toàn C10 = R_new + phủ quyết ½ (báo cáo, quyết định riêng):**
- S1: ≤ 2/144 run > α và TB ≤ α trên 8/8 dataset.
- S2: recall C10 − R_new ≥ −0.015.
- S1 ∧ S2 ⇒ C10 được ghi là "điểm vận hành an toàn đã xác nhận" bên cạnh R_new.

**Quy tắc:** C1 ∧ C2 ∧ C3 ∧ C4 ⇒ R_new XÁC NHẬN. Nếu C1 trượt thì ghi rõ dataset / nguồn của các run > α.

## Entry 23 — Bằng chứng TUYỆT ĐỐI cho ô trống, hiệu chỉnh hồi cứu theo phiên (OWF-NT-HQ, Mệnh đề 7) — đăng ký trước (2026-11-06 08:27 UTC)

**KẾT QUẢ (seed 64–66, 144 run; đợt `test64`, 8 phiên L4; ghi 08:54 UTC). Theo quy tắc đăng ký trước: V1 ∧ V2 ∧ V3 ĐẠT ⇒ C9 =
OWF-HWA-S5-NT-HQ THAY R* — LUẬT KHUYẾN NGHỊ MỚI.** Ô = recall / TB segFAR / run > α / sai số (m), trên CÙNG run:

| Dataset | R* = OWF-HWA-S5 | **C9 = OWF-HWA-S5-NT-HQ** | C10 = C9 + phủ quyết (báo cáo) |
|---|---|---|---|
| CMU | 0.856 / 0.0364 / 4 / 8.5 | **0.865 / 0.0254 / 4 / 7.1** | 0.856 / 0.0129 / 0 / 5.3 |
| Nordland | 0.968 / 0.0064 / 0 / 7.5 | **0.972 / 0.0036 / 0 / 4.1** | 0.971 / 0.0036 / 0 / 4.1 |
| St Lucia | 0.979 / 0.0010 / 0 / 18.0 | 0.985 / 0.0010 / 0 / 17.9 | 0.984 / 0.0007 / 0 / 17.7 |
| office | 0.977 / 0.0004 / 0 / 7.5 | 0.975 / 0.0006 / 0 / 7.7 | 0.972 / 0.0000 / 0 / 7.7 |
| old town | 0.938 / 0.0010 / 0 / 22.8 | 0.920 / 0.0008 / 0 / 24.1 | 0.912 / 0.0002 / 0 / 23.8 |
| countryside | 0.853 / 0.0048 / 0 / 25.9 | 0.847 / 0.0041 / 0 / 25.7 | 0.823 / 0.0008 / 0 / 35.2 |
| Boreas | 0.973 / 0.0007 / 0 / 4.3 | 0.960 / 0.0010 / 0 / 5.5 | 0.940 / 0.0006 / 0 / 3.8 |
| Oxford | 0.944 / 0.0087 / 0 / 22.8 | 0.935 / 0.0093 / 0 / 24.0 | 0.932 / 0.0006 / 0 / 21.5 |
| **Gộp** | 0.936 / 0.0074 / 4 / 14.67 | **0.932 / 0.0057 / 4 / 14.51** | 0.924 / **0.0024 / 0** / 14.90 |

C9:
- **V1 đạt:** run > α 4 = 4; TB segFAR 0.0074 → 0.0057.
- **V2 đạt:** −0.0037 [−0.0071, −0.0008] (thắng 76 / thua 68).
- **V3 đạt:** 14.51 so với 14.67 m (tốt hơn).
- V4 trượt, giống R*: 4 run CMU > α.

C10 (chỉ báo cáo):
- V1 đạt, AN TOÀN HƠN: **0/144 run > α**, TB segFAR 0.0024.
- V2 trượt (−0.0123).
- V3 đạt (14.90).
- V4 ĐẠT.

*Ghi chú vận hành:* `e23_eval.sh` sao từ Entry 21 nên in V1–V3 cho biến thể có phủ quyết và N1′–N3 cho C9, và dòng DECISION của nó ("R* KEPT")
sai luật. Quyết định trên được tính lại đúng luật đã commit (V1–V3 trên C9) từ CÙNG các số (`analysis/results/owf/s1106/e23_decision.txt`).

**Tổng quát của C9 (mô tả, không quyết định; đợt `genhq`, các tập chưa từng dùng để chỉnh; R* = OWF-HWA-S5 trên CÙNG run).** Ô = recall
/ TB segFAR / run > α:

| Tập | R* | C9 | chênh recall (CI 95 %) |
|---|---|---|---|
| lỗ 10 % (108) | 0.933 / 0.0022 / 1 | 0.932 / 0.0019 / **0** | −0.001 [−0.004, +0.002] |
| lỗ 50 % (108) | 0.894 / 0.0091 / 4 | 0.873 / 0.0071 / 4 | −0.021 [−0.031, −0.013] |
| off-map tự nhiên (36) | 0.952 / 0.0104 / 2 | 0.943 / **0.0025 / 0** | −0.009 [−0.014, −0.005] |
| NCLT (6) | 0.781 / 0.0049 / 0 | 0.768 / 0.0011 / 0 | −0.013 [−0.028, +0.004] |

- Hợp lệ tốt hơn ở MỌI tập: tổng run > α 7 → 4; 4 run còn lại đều là CMU ở lỗ 50 %.
- Lỗ 10 %, CMU: 0.796 / 0.0077 / 1 → 0.814 / 0.0034 / 0.
- Điều hướng: lỗ 50 % Nordland 21.7 → 13.2 m; NCLT 5.8 → 4.7 m.
- Recall giảm rõ nhất ở lỗ 50 % (−0.021): ít frame trên bản đồ, nên phiên đủ 100 mẫu riêng muộn hơn.

**Đọc trung thực.**
- (i) Thay đổi ở bộ ước lượng sửa đúng chỗ đã chẩn đoán. CMU segFAR −30 % VỚI recall +0.009 và điều hướng −1.4 m; Nordland segFAR −44 %,
  điều hướng 7.5 → 4.1 m.
- (ii) Recall giảm ở old town / Boreas / Oxford (−0.009 … −0.018). Đó là đầu các phiên có điều kiện khác, đúng như phát triển dự báo.
- (iii) 4 run CMU > α còn lại (cả R* lẫn C9) có 3 đến từ nhánh HSI (H(R*) 3 run > α). Phủ quyết bằng mN của C9 (C10) xoá cả 4, đổi lại
  −0.012 recall.
- (iv) Đây là lần đầu từ Entry 15 một luật mới thay luật khuyến nghị theo quy tắc đăng ký trước. Nhóm 64–66 đã dùng; kho r61 hết.

**Ý tưởng (`paper/owf_theory.md` §10, viết trước khi đọc đợt phát triển).** Entry 22 cho thấy chuẩn hoá z theo frame bỏ mất thông tin tách
khớp đúng khỏi bí danh. Thông tin đó nằm ở độ tương đồng tuyệt đối. Quan sát x_t = max_i s_ti − median_i s_ti:
- trên bản đồ, x_t là max của (đúng chỗ, bí danh tốt nhất), mật độ f_on;
- ngoài bản đồ, x_t là bí danh tốt nhất khi đúng chỗ vắng mặt, mật độ f_off.

Ô trống và Ω nhận log-LR log f_off(x_t) − log f_on(x_t). Mật độ ước lượng KHÔNG nhãn từ lượt 1 (bộ lọc cũ), tại các fix tự tin
(khối lượng ≥ 1 − 1e-3):
- f_on: max của frame;
- f_off: max trên các ảnh xa hơn 1.6 excl khỏi fix (bí danh cùng điều kiện, cùng descriptor, cùng bản đồ);
- KDE + 1 % nhiễm đều.

**Nhân quả:** lượt 1 là nhân quả và không phụ thuộc lượt 2. Frame t của một phiên dùng mẫu của chính phiên ở các frame < t khi đã có
≥ 100 mỗi loại; trước đó dùng các phiên khác của run (`owf.py --pin 0 --lu hsq`).
- Kiểm offline (CMU s60): trung vị bí danh hồi cứu 0.469 khớp bí danh thật trong lỗ 0.445; AUC khớp đúng vs bí danh theo cos 0.92–0.96, theo
  z 0.86–0.88.
- Các biến thể đã loại trên run thiết kế:
  - hs (cos đúng chỗ, LOSO) và hsmp (gộp): sập phiên đêm old town (0.72 → 0.11 … 0.32);
  - hsc (KDE 2-D theo trung vị hồ sơ): không đỡ;
  - hsr (dự phòng theo điều kiện khớp): không đổi.

**Phát triển: đợt `devhq`** (8 phiên L4, 405 run; mọi JSON có `lu.mode = hsq`), so với R* trên CÙNG 399 run. Ô = recall / TB segFAR / run > α
/ sai số (m):

| Dataset | R* (S5) | C9 = NT + HQ | C10 = C9 + phủ quyết ½ |
|---|---|---|---|
| CMU | 0.852 / 0.0095 / 1 / 4.4 | **0.863 / 0.0066 / 0 / 3.8** | 0.854 / 0.0037 / 0 / 3.3 |
| Nordland | 0.968 / 0.0069 / 0 / 6.2 | **0.970 / 0.0026 / 0 / 4.7** | 0.969 / 0.0026 / 0 / 4.7 |
| St Lucia | 0.980 / 0.0013 | 0.986 / 0.0013 | 0.985 / 0.0008 |
| office | 0.969 / 0.0001 | 0.970 / 0.0002 | 0.969 / 0.0001 |
| old town | 0.946 / 0.0010 / 0 / 20.1 | 0.932 / 0.0007 / 0 / 23.3 | 0.927 / 0.0001 / 0 / 19.7 |
| countryside | 0.852 / 0.0056 / 0 / 25.4 | 0.833 / 0.0049 / 0 / 25.7 | 0.816 / 0.0005 / 0 / 31.2 |
| Boreas | 0.971 / 0.0027 / 0 / 4.7 | 0.962 / 0.0022 / 0 / 5.7 | 0.952 / 0.0009 / 0 / 3.5 |
| Oxford | 0.949 / 0.0078 | 0.943 / 0.0089 | 0.940 / 0.0013 |
| **gộp** | 0.933 / 0.0045 / 1 / 12.7 | 0.929 / **0.0034 / 0** / 13.0 | 0.923 / **0.0013 / 0** / 12.8 |

Chênh recall so với R*:
- C9: −0.0040 [−0.0061, −0.0022] (thắng 219 / thua 178), điều hướng +0.37 m;
- C10: −0.0100 [−0.0126, −0.0075], điều hướng +0.10 m.

Đọc:
- Lần đầu tiên một thay đổi ở bộ ước lượng tăng recall VÀ giảm báo sai trên CMU và Nordland, đúng hai nơi có đuôi hợp lệ.
- Cái giá nằm ở đầu các phiên có điều kiện khác hẳn các phiên còn lại (đêm 4Seasons, trước khi phiên có 100 mẫu riêng).

**Luật đăng ký: OWF-HWA-S5-NT-HQ (C9).** OWF-HWA-S5 với `--pin 0 --lu hsq`. Union / OWF-H giữ nguyên. Hằng số mới, đều chung cho mọi dataset:
- 1.6 excl (bán kính "chỗ khác", như giao thức τ của VPR-Space);
- ε = 1 % nhiễm;
- 100 mẫu tối thiểu;
- khối 50 frame.

**Tập kiểm tra mới:** seed 64–66 của `namhunhh/hmm-navcache-r61` (144 run, chưa dùng). R* và C9 trong CÙNG đợt (`test64`). C10 tính từ khung của
C9 bằng `OWF_VETO=0.5`. Tiêu chí giống hệt V1–V3 đã đăng ký ở Entry 21 cho một ứng viên ưu tiên hợp lệ:
- **V1 (hợp lệ, tương đối):** run > α của C9 ≤ của R*, VÀ TB segFAR gộp của C9 ≤ của R*.
- **V2 (giá recall có giới hạn):** chênh gộp ≥ −0.006, VÀ cận dưới CI 95 % ≥ −0.010.
- **V3 (điều hướng):** sai số gộp của C9 ≤ R* + 0.5 m.
- **V4 (báo cáo):** mục tiêu tuyệt đối (TB ≤ α trên 8/8 dataset, ≤ 2/144 run > α). Báo cáo thêm CMU / Nordland segFAR.

**Quy tắc:** V1 ∧ V2 ∧ V3 ⇒ C9 thay R* (luật khuyến nghị mới). Nếu thêm run > α giảm ngặt, ghi "an toàn hơn". Nếu chênh recall có CI > 0,
ghi "tốt hơn". C10 chỉ báo cáo (cùng tiêu chí), không quyết định.

