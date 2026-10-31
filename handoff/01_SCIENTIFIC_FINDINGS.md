# 01 — Scientific Findings (hướng HMM-navigation)

*Cập nhật 2026-10-31 (branch `hmm-navigation-3`). Tài liệu chỉ nói về **kết quả khoa học**: đóng góp, ý nghĩa, kết quả
tích cực và tiêu cực, kèm bằng chứng và điều kiện kiểm chứng. Vận hành ở `02`, trạng thái và việc tiếp theo ở `03`.
**Đọc §N trước** (trạng thái khoa học mới nhất, 2026-10-30/31); §0–§5 là nền tảng từ 2026-10-29, vẫn đúng, trừ chỗ §N
ghi đè. Nguồn số liệu: `RESEARCH_LOG.md` Entry 22–25, `paper/oc_tables.md`, `paper/BAO_CAO_PhanBien.pdf`,
`analysis/results/oc_*_entry25.tgz`.*

## N0. Vòng 4 (2026-10-31, branch `hmm-navigation-4`) — đọc trước §N

**Báo cáo:** `paper/BAO_CAO_E26.pdf`; nhật ký `RESEARCH_LOG.md` Entry 26; lý thuyết `paper/cpc_theory.md` §3e–§3f; novelty
`LITERATURE_GATE.md` Gate 11; baseline 2026 `literature/BASELINES_2026.md`.

1. **Chẩn đoán phụ thuộc:** p-value top-1 của frame off-map hợp lệ biên ở phần trong đoạn off-map; vi phạm ở ~50 frame quanh
   mép bản đồ (nhìn chồng lấn) và ở R neo odometry của đoạn dài; null bản đồ chỉ có 8–10 chunk ngắn (~10 đơn vị hoán đổi).
2. **Lý thuyết:** Mệnh đề 5 (không giả định phụ thuộc thì không tích luỹ được bằng chứng); Định lý 4 (GPC: chứng chỉ đúng
   với mọi phụ thuộc, nhưng recall chỉ 10–40 % của CPC-SC+CS); Định lý 5 (khởi phát cửa sổ hữu hạn + dừng/reset hình học:
   tỷ lệ khởi phát sai mỗi đoạn ≤ α với mọi phụ thuộc giữa các đoạn; kiểm chứng: trung bình 0.001–0.006, run tệ nhất của
   CPC-SC-T+SH ≤ 0.039).
3. **Phương pháp mới (không nhãn):** bằng chứng kiểm định tuyến (chi phí TAO'26 trên 100 giả thuyết, 20 frame) **hiệu chuẩn
   bằng null bản đồ** làm thành phần thứ ba của chuỗi hiện diện (CPC-SC-T), cộng dừng hình dạng SH (Procrustes). CPC-SC-T+CS:
   cải thiện Pareto so với CPC-SC+CS (recall 7/7, sai số ≤ 7/7). CPC-SC-T+SH: recall +0.009…+0.053 trên 7/7, hơn Xu'21 về
   recall 5/7; ở FL ≤ 1 % hơn Xu'21 7/7, Claxton'24 và TAO'26 6/7 (trừ CMU).
4. **Baseline 2026 trên cùng giao thức:** TAO'26 xếp hạng mạnh trên CMU nhưng ngưỡng 3σ vi phạm (segFAR 0.24–0.74); TRAIL'26
   ≈ top-1 MegaLoc, ngưỡng có nhãn vi phạm (0.15–0.29); VPR-auditing'26 (Qwen2.5-VL-7B) nhận 30–36 % frame off-map, sai số
   150 m. Với riêng MegaLoc, Claxton'24/TAO'26 xếp hạng tốt hơn trên 4/7.
5. **Âm / mở:** điểm mặc định còn dè dặt vì null **cùng điều kiện ảnh** (hiệu chuẩn chung, bỏ sàn κ: +0.003…+0.011); LODO không
   phân biệt các biến thể theo sai số; CMU với descriptor mạnh vẫn thua về xếp hạng. Mức: A vững hơn, A\* chưa.

## N. Trạng thái mới nhất (2026-10-30 → 2026-10-31)

### N.1 Phương pháp chính hiện tại: CPC-SC+CS (thay CPC-HMM +TCEmin)

`analysis/cpc_sc.py` (cũng là luật `CPC-SC+CS (ours)` trong `nav_rules.py`). Ba thành phần, mọi hằng số theo đơn vị bài
toán (excl, H, α), một cấu hình cho mọi dataset:

1. **Chuỗi hiện diện CPC-HMM** (không TCE): LR_t = ½(ẽ^top_t + (e^R_t)^{1/H}), e = a·p^{a−1} (a: Beta-EM theo traversal),
   ẽ^top có cổng top-1 = MAP; p_in = p_out = 0.01.
2. **SC — ngưỡng khởi phát hiệu chuẩn theo đoạn:** κ = phân vị conformal (1−α) của max log-odds trên các đoạn H frame
   của null tự-phát-lại của bản đồ (chuỗi khởi đầu ở odds 1). Báo từ khi ℓ_t > κ, duy trì khi ℓ_t > 0.
   *Định lý (khởi phát):* dưới exchangeability của đoạn off-map với đoạn null, P(khởi phát báo trong đoạn | chưa báo khi
   vào đoạn) ≤ α, mọi phụ thuộc trong đoạn. Thực nghiệm Boreas: tỷ lệ đoạn có khởi phát sai 0.010–0.041.
3. **CS — quy tắc dừng nhất quán odometry:** dừng nếu ∃k, quãng odometry ≤ 3·excl, | ‖m_t − m_{t−k}‖ − ‖o_t − o_{t−k}‖ | >
   excl. *Bổ đề 7:* chỉ bỏ bớt báo cáo nên segFAR/FL không tăng (không áp cho ARL₀ đếm khởi phát). *Mệnh đề 4:* nếu MAP
   kẹt trong bán kính δ quanh nơi rời bản đồ và excl + in_d + ε + δ < off_d thì không có báo cáo ở frame off-map.

Lý thuyết đầy đủ: `paper/cpc_theory.md` §3c (TCE) và §3d (đường cong, CS, CPC-SC).

### N.2 Chẩn đoán dẫn tới phương pháp (Entry 25, `analysis/recall_diag.py`)

- Recall mất ở **chuỗi hiện diện**, không ở chuỗi vị trí: Boreas NetVLAD chuỗi vị trí đúng 85 % frame on-map, chỉ báo
  30 %; Boreas DINOv2 83 % frame on-map nằm trong đoạn không bao giờ được báo dù chuỗi vị trí đúng 86 % ở đó.
- **Phép min TCE** là nguyên nhân chính (NCLT DINOv2 recall 0.16 TCEmin vs 0.50 CPC-HMM).
- **So với CPC-HMM, TCEmin là điểm vận hành thận trọng hơn trên đường cong kém hơn** (NCLT NetVLAD, cùng recall: sai số
  12.9 vs 6.3 m) → phản biện "chỉ thận trọng hơn" đúng với phương pháp cũ.
- Vi phạm segFAR của CPC-HMM không TCE đến từ **báo cáo kéo dài** (chuỗi vị trí không có trạng thái off-map: MAP kẹt ở
  mép hoặc nhảy sang nơi giống), không phải từ khởi phát.
- **Tính nhất quán odometry trên quãng dịch chuyển là bằng chứng hiện diện mạnh:** ở 4S countryside, mọi luật "+CS" đạt
  recall tốt nhất tại FL ≤ 0.01 khi ngưỡng P(on) chỉ ≈ 0.02 (CS gần như tự loại hết báo sai). Ngược lại phép thử một bước
  (PCR, cổng dự đoán kiểu IPDA) **tự xác nhận**: dưới H0 nơi dự đoán cũng là ô top-1 ở 62 % frame (CMU CosPlace).

### N.3 Kết quả (7 dataset, 6 descriptor; bản đồ khuyết 30 %; NCLT off-map tự nhiên)

**Điểm mặc định, 10 seed (366 run)** — recall / segFAR / sai số (m):

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.68 / 0.043 / 25.3 | 0.53 / 0.021 / 13.7 | 0.69 / 0.227 / 18.1 | 0.74 / 0.038 / 59.3 | 0.72 / 0.215 / 21.2 | 0.62 / 0.101 / 70.9 | 0.25 / 0.088 / 81.0 |
| Claxton'24 (nhãn) | 0.74 / 0.116 / 36.9 | 0.66 / 0.203 / 32.3 | 0.87 / 0.166 / 14.3 | 0.52 / 0.263 / 88.0 | 0.80 / 0.152 / 18.7 | 0.72 / 0.166 / 90.4 | 0.60 / 0.213 / 42.9 |
| TCEmin (cũ) | 0.66 / 0.008 / 6.4 | 0.49 / 0.000 / 3.7 | 0.75 / 0.018 / 3.9 | 0.57 / 0.002 / 13.0 | 0.70 / 0.013 / 12.5 | 0.59 / 0.008 / 33.7 | 0.21 / 0.010 / 59.1 |
| **CPC-SC+CS** | 0.66 / 0.001 / 5.1 | 0.54 / 0.000 / 4.6 | 0.73 / 0.002 / 3.8 | 0.64 / 0.000 / 9.6 | 0.71 / 0.000 / 11.6 | 0.60 / 0.000 / 30.8 | 0.30 / 0.000 / 53.1 |
| Oracle | 0.88 / – / 2.1 | 0.72 / – / 2.2 | 0.94 / – / 3.0 | 0.67 / – / 4.8 | 0.91 / – / 8.3 | 0.84 / – / 19.4 | 0.73 / – / 16.5 |

**Recall ở cùng FL ≤ 0.01 (đường cong vận hành, 3 seed):**

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.562 | 0.526 | 0.592 | 0.624 | 0.537 | 0.555 | 0.181 |
| Claxton'24 (nhãn) | 0.687 | 0.574 | **0.793** | 0.439 | 0.749 | 0.644 | 0.420 |
| SafeVPR (nhãn) | 0.486 | – | – | – | – | – | – |
| TCEmin (cũ) | 0.692 | **0.590** | 0.713 | 0.619 | 0.733 | 0.616 | 0.245 |
| **CPC-SC+CS** | **0.766** | 0.586 | 0.705 | **0.780** | **0.771** | **0.664** | **0.545** |

- Ở cùng FL ≤ 1 %: hơn Xu'21 7/7, hơn Claxton'24 6/7 (trừ CMU). Đặt tại đúng FL của Xu'21 (Kalman chạy thật,
  `oc_matched.py`): recall cao hơn 5/7, sai số thấp hơn 6/7.
- segFAR tệ nhất trong từng run: 0.021 (mọi 366 run < α = 0.05); TCEmin tới 0.171, Xu'21 tới 1.0.
- So với TCEmin: recall cao hơn 5/7 (CMU −0.02), segFAR ≤ 7/7, sai số thấp hơn 6/7 (NCLT +0.9 m).
- **Độ bền tỷ lệ lỗ bản đồ** (cùng hằng số): 10 % và 50 % → segFAR ≤ 0.012 mọi nơi; sai số thấp hơn Xu'21 ở mọi dataset
  (10 %: 1.2–4.5×, 50 %: 2.4–8.9×).
- **Chọn leave-one-dataset-out** (15 biến thể không nhãn): CPC-SC+CS ở 6/7 fold, regret 0–3.5 m (TCEmin trước đây: tới
  30 m). Giao thức **đăng ký trước**: Boreas/NCLT phát triển, 5 tập còn lại giữ lại.
- Độ nhạy: span CS 2/4·excl đổi recall ±0.02–0.04, segFAR ≤ 0.014; ngưỡng 0.75/1.25·excl ảnh hưởng nhỏ; α = 0.1 như 0.05.

### N.4 Kết quả âm và hạn chế mới (đã xác minh)

1. **CMU (descriptor mạnh, dữ liệu dễ):** Claxton'24 (nhãn) và cả max-sim thô xếp hạng tốt hơn mọi chuỗi hiện diện.
2. **Vùng FL cao (3–8 %):** Claxton'24 recall cao hơn trên 5/7 (segFAR của nó 0.11–0.27).
3. **Điểm mặc định còn dè dặt so với chính đường cong** (countryside recall 0.30 ở FL 0 vs 0.55 ở FL 0.01). Hiệu chuẩn
   chung (hiện diện ∧ CS) trên null không nới được: null tự-phát-lại qua CS nhiều gấp 2.6× off-map thật (0.229 vs 0.088).
4. **Recall mặc định thấp hơn Xu'21 trên 4/7** (Nordland −0.10, còn lại ≤ 0.02).
5. **α = 0.01 không khả thi** khi null có < 99 đoạn (CMU, 4S office: κ = ∞, recall 0).
6. **Bảo đảm dưới phụ thuộc thời gian vẫn chưa có:** W-CPC (bộ nhớ hữu hạn + hiệu chuẩn theo đoạn) vi phạm trên Boreas
   (segFAR 0.030, tệ nhất 0.099) như certified; nguyên nhân: null tự-phát-lại của bản đồ (block ngắn, cùng điều kiện ảnh)
   biểu diễn thiếu phụ thuộc của đoạn off-map dài.
7. Đã thử và loại: e-value hai nhóm (hedge, +0.006 recall), trung bình e-process, TCE trên một thành phần, hysteresis
   TCEmin→CPC, CPC-SC không CS, PCR (kèm lỗi thang đo khi che block của null), cổng độ tin chuỗi vị trí (conf quá tự tin),
   hiệu chuẩn chung CS.
8. NCLT: CS xoá frame đúng; CPC-HMM không CS có đường cong tốt nhất; sai số nhạy với vài fix sai (EKF có hướng).

### N.5 Kết quả 2026-10-30 (Entry 22–24, tóm tắt)

- **TCE / TCEmin** (e-value hiệu chuẩn theo chuyển tiếp, min với e-value biên): segFAR ≤ 0.025 trên 7/7, nhưng recall
  thấp (§N.2).
- **NCLT** (8 phiên, off-map tự nhiên) được thêm như tập giữ lại; mọi luật không nhãn thắng baseline có nhãn về segFAR.
- **Cổng dead-reckoning +GG** tốt trên Boreas nhưng khoá chết trên 4S old town/countryside và NCLT → chỉ là module tuỳ chọn.

### N.6 Novelty (Gate 9–10, `LITERATURE_GATE.md`)

- CS: cơ chế đã biết (RRR, PCM/Olson, SeqSLAM, Claxton'24) — vai trò và chẩn đoán là mới. SC: cùng lập luận exchangeability
  như certified (conformal theo quỹ đạo/block). Đánh giá theo đường cong: giao thức, không phải phương pháp.
- **Mức hiện tại: A (RA-L/ICRA/IROS) khả thi; A\* chưa.** Thiếu: bảo đảm dưới phụ thuộc; so sánh TRAIL'26 / TAO'26 /
  VPR-auditing'26; chạy robot thật vòng kín.

## 0. Bài toán

**Bối cảnh.** Robot dùng camera đơn chạy theo chuỗi frame có odometry, trên một bản đồ ảnh **có lỗ**: có đoạn đường
không có trong bản đồ (off-map). Mỗi frame có similarity tới N ảnh bản đồ (global descriptor).

**Câu hỏi.** Khi nào được tin một "fix" vị trí, để đưa vào bộ lọc điều hướng, sao cho:

1. tỷ lệ fix sai được kiểm soát, **không cần nhãn** của điều kiện mới (đêm, tuyết, mùa);
2. mạnh hơn kiểm định từng frame;
3. đúng cả khi các frame phụ thuộc nhau mạnh.

**Đánh giá.**

- Trong suốt dự án, 30 % block của bản đồ bị bỏ để tạo off-map (thêm 10 % và 50 % cho độ bền).
- Dữ liệu: 7 dataset (RobotCar-Seasons, Extended-CMU, Nordland, 4Seasons ×3 cảnh, Boreas), 6 descriptor (MegaLoc,
  SALAD, MixVPR, CosPlace, NetVLAD, DINOv2), 2–3 seed.
- Odometry thật trên 4Seasons (VIO) và Boreas (bánh xe + gyro); mô phỏng ở các tập còn lại.

## 1. Đóng góp A — Certified sequential localization (hướng chính)

**Phương pháp** (`analysis/cert_seq.py`).

1. p-value SelfCal-AA từng frame, hiệu chuẩn bằng chính bản đồ (leave-block-out, thống kê bất biến affine), cross-fit.
2. Bằng chứng chuỗi neo odometry:

   > R_t = ℓ_t + Σ_{j<H} ℓ_{t−j} · 1[‖(x_t − x_{t−j}) − (o_t − o_{t−j})‖ ≤ ρ_o],  ℓ = −log p

   ANCHR tự fit góc lệch odometry→bản đồ trong mỗi cửa sổ.
3. Hiệu chuẩn theo **đoạn**: ngưỡng là phân vị conformal của max R trên các đoạn H frame của traversal bản đồ bị giữ lại.

**Định lý.** Giả sử các đoạn off-map hoán đổi được (exchangeable) với các đoạn bản đồ giữ lại. Khi đó:

> P(có ít nhất một fix sai trong một đoạn off-map dài H) ≤ α

với mọi kiểu phụ thuộc bên trong đoạn. Đây là lý do cách hiệu chuẩn theo cửa sổ trước đó (exp11/seq_odo) thất bại,
còn cách này đúng.

**Bằng chứng** (α = 0.05; H = 10, RobotCar H = 5; `paper/cert_tables.md`):

| Dataset | FAR theo đoạn, ANCH (tệ nhất) | Baseline hiệu chuẩn bằng nhãn (tệ nhất) | Power ANCH / per-frame / dùng nhãn |
|---|---|---|---|
| RobotCar-S. | 0.016 (0.067) | 0.044 (**0.125**) | 0.68 / 0.77 / 0.77 |
| CMU-S. | 0.022 (0.052) | 0.044 (**0.089**) | 0.82 / 0.62 / 0.87 |
| Nordland | 0.020 (0.033) | 0.016 | 0.86 / 0.44 / 0.87 |
| 4S office | 0.020 (0.049) | 0.022 | 0.83 / 0.31 / 0.85 |
| 4S old town | 0.014 (0.022) | 0.010 | 0.77 / 0.43 / 0.86 |
| 4S countryside | 0.015 (0.025) | 0.025 | 0.37 / 0.19 / 0.49 |
| Boreas | 0.006 (0.017) | 0.026 (**0.062**) | 0.71 / 0.35 / 0.79 |

- **Off-map tự nhiên** (query của cảnh hoặc dataset khác, `cert_natural.py`): FAR ≤ 0.016.
- **α = 0.01 và 0.1** đều bám mục tiêu.
- **Độ trễ tới fix đầu tiên** giảm 5–20×.

**Ý nghĩa.** Đây là bảo đảm không cần nhãn đầu tiên ở mức đoạn (excursion) cho định vị theo chuỗi. Baseline dùng nhãn
của điều kiện dễ (kiểu SAFEVPR, Quantile Transfer) vượt α ở 3/7 dataset.

**Hạn chế.**

- Power luôn thấp hơn baseline dùng nhãn. Đó là cái giá của tính hợp lệ.
- RobotCar có snippet 9 frame, quá ngắn để tích luỹ bằng chứng (0.68 so với 0.77 của per-frame).
- Bản đồ nhỏ (CMU, khoảng 70 đoạn null) khiến FAR của từng bản đồ dao động.
- Giả định exchangeability chỉ được kiểm bằng thực nghiệm.

## 2. Đóng góp B — Chẩn đoán vì sao HMM thua baseline

**Thiết lập** (`analysis/hmm_diag.py`, 36 cấu hình): HMM chuẩn (lọc tiến, chuyển trạng thái theo odometry, emission
exp(s/T)), có hoặc không có trạng thái off-map của Xu et al. RA-L'21.

| Mã | Phát hiện | Số liệu |
|---|---|---|
| D5 | Posterior **bất biến chính xác** khi cộng một hằng số vào mọi similarity của từng frame | thay đổi ≤ 4·10⁻⁶ |
| D1 | Độ tin cậy của HMM tách on/off kém hơn max-sim thô | R@FL5 0.44 so với 0.55 (CMU 0.43 so với 0.74) |
| D2 | Quá tự tin | conf 0.91 so với acc 0.77, ECE 0.14 |
| D3 | Khoá nhầm chỗ | 16 % frame sai mà vẫn tin > 0.9, gây 41 % tổng sai số |
| D4 | Bằng chứng phụ thuộc | tự tương quan trễ 1 là 0.8–0.99, tức phóng đại (1+r)/(1−r) = 8–136× |

**Nguyên nhân gốc:**

1. **Mù với sự vắng mặt.** Softmax chỉ mang bằng chứng tương đối. Câu hỏi "có trong bản đồ không" lại cần
   LR(j : ∅) = f₁(s_j)/f₀(s_j), tức mức tuyệt đối. Vì vậy (T, k) của Xu'21 tune bằng nhãn trên điều kiện dễ cho FL 0.97
   trên CMU.
2. **Đếm thừa bằng chứng phụ thuộc** (likelihood hợp thành), gây quá tự tin và khoá nhầm.
3. **Vòng khoá nhầm:** bằng chứng tính từ niềm tin của HMM tự xác nhận khi đã khoá nhầm.
4. **Bội số:** p-value của thống kê max đã trả giá cho N nơi, nên không nhân vào từng trạng thái được.

## 3. Đóng góp C — CPC-HMM (module sửa HMM)

**Mô hình** (`analysis/hmm_fix.py`, `fac_anchT_mix`; luật điều hướng trong `nav_demo.py`; lý thuyết trong
`paper/cpc_theory.md`).

- **Chuỗi vị trí:** HMM không có trạng thái off-map, với emission (s − s_max)/(τ·σ_far,t). τ là thang Gumbel của null
  bản đồ, nên không phải tune.
- **Chuỗi hiện diện on/off:**

  > P(on_t) ∝ [(1−p_out)·P(on_{t−1}) + p_in·P(off_{t−1})] · LR_t,  LR_t = ½(ẽ^top_t + (e^R_t)^(1/H))

  - e = a·p^(a−1), với a fit bằng EM theo từng traversal (không nhãn).
  - Cổng: top-1 phải khớp MAP của chuỗi vị trí.
  - e^R là e-value của R_t, hiệu chuẩn trên traversal của bản đồ.
- **Quyết định:** báo nơi MAP khi P(on) > ½.

**Lý thuyết** (`paper/cpc_theory.md`):

- **Bổ đề 1:** e-value có thể dự đoán.
- **Bổ đề 2:** cổng, luỹ thừa và trung bình đều giữ tính e-value.
- **Định lý 1:** odds bị chặn bởi thống kê Shiryaev–Roberts, nên **ARL₀ ≥ (1−p_in)/p_in − R₀**, với điều kiện
  p_out ≥ p_in.
- **Định lý 2:** độ trễ vào lại ≈ log((1−p)/p)/KL₁.

**Kiểm chứng ARL₀** (số frame off-map trên mỗi lần bắt đầu báo sai, trung vị; cận lý thuyết 98):

| | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|
| **CPC-HMM** | 995 | 3930 | 2840 | 762 | 895 |
| Xu'21 (nhãn) | **41** | 720 | 651 | 665 | 1424 |
| CPC, p_in = 0.05 (cận 18) | 337 | 1965 | 1893 | 318 | 832 |

**Kết quả CPC-HMM so với Xu'21** (bản đồ khuyết 30 %; ô ghi recall / FL / sai số điều hướng trung bình):

| Dataset | CPC-HMM (không nhãn) | Xu'21 (T, k tune bằng nhãn) | Kết luận |
|---|---|---|---|
| CMU | 0.77 / 0.034 / 6.8 m | 0.71 / 0.363 / 46.0 m | **thắng** |
| Nordland | 0.71 / 0.008 / 20.1 fr | 0.74 / 0.013 / 54.7 fr | **thắng** |
| 4S office | 0.78 / 0.004 / 10.9 m | 0.77 / 0.041 / 17.7 m | **thắng** |
| 4S old town | 0.64 / 0.040 / 45.6 m | 0.60 / 0.091 / 100.9 m | **thắng** |
| 4S countryside | 0.37 / 0.068 / 56.0 m | 0.28 / 0.029 / 94.4 m | thắng điều hướng, FL cao hơn |
| RobotCar | 0.68 / 0.060 / 2.1 m | 0.58 / 0.045 / 1.3 m | **thua** (snippet 9 frame) |
| Boreas (odometry đã sửa) | sai số điều hướng 21.0 m (4 desc.) | 6.2 m | **thua khoảng 3×** |

**Điều hướng khép kín** (`nav_demo.py`, 3 seed, sai số trung bình):

| | CMU | Nordland | 4S office | 4S old town | 4S countryside | Boreas* |
|---|---|---|---|---|---|---|
| CPC-HMM | 5.7 | 17.9 | 12.8 | 36.0 | 54.0 | 21.0 |
| Certified | 3.8 | 17.0 | 11.3 | 37.0 | 52.8 | 19.4 |
| Xu'21 (nhãn) | 14.2 | 70.7 | 22.7 | 62.4 | 76.8 | **6.2** |
| Per-frame SelfCal | 5.3 | 36.3 | 11.6 | 45.2 | 65.7 | 16.2 |

\*Boreas: MegaLoc, SALAD, MixVPR và CosPlace sau khi sửa odometry. NetVLAD và DINOv2 đang chạy.

**Độ bền theo tỷ lệ lỗ bản đồ** (sai số điều hướng của `hmm_fix`, CPC so với Xu'21):

- **Khuyết 50 %:** CPC thắng ở mọi dataset trừ RobotCar.
  - CMU 28.0 so với 55.0; Nordland 23.8 so với 169; 4S office 26.3 so với 79.1.
  - **Boreas 13.7 so với 40.8**.
- **Khuyết 10 %:** CPC thắng trên CMU, Nordland, 4S office và countryside, nhưng thua trên 4S old town (44.0 so với
  30.1).

**Đóng góp mới so với tài liệu** (Gate 7 trong `LITERATURE_GATE.md`):

- **Mới:**
  - chẩn đoán bất biến dịch chuyển;
  - chuỗi tồn tại kiểu IPDA được nuôi bằng e-value hiệu chuẩn bằng bản đồ;
  - cổng độc lập niềm tin;
  - phép chặn chuỗi on/off của HMM bằng một e-detector.
- **Không mới:** từng khối riêng (IPDA/Bernoulli existence, e-detectors của Shin–Ramdas–Rinaldo, p-to-e calibrator,
  HMM-VPR).
- **Mức hiện tại:** RA-L/ICRA nếu sửa được Boreas. Nên trình bày như module của hướng certified.

## 4. Kết quả tiêu cực và hạn chế (kèm nguyên nhân đã xác minh)

1. **HMM không tăng recall trung bình** trên các benchmark này: CMU 90.7 → 92.5 % R@5 m. Không có chỗ cho một paper
   "HMM tăng độ chính xác".
2. **Calibrate theo cửa sổ thất bại** (Entry 18): cửa sổ trong một block 300 m phụ thuộc nhau, và số mẫu hiệu dụng của
   null quá nhỏ. Đã giải quyết bằng hiệu chuẩn theo đoạn.
3. **Lỗi dữ liệu Boreas:** bộ đếm xung bánh xe đứt ở 4/13 chuyến, tạo một bước nhảy 8.7 km. Lỗi này làm chuỗi vị trí mất
   dấu (đúng 2 % so với top-1 đúng 99 %). Đã sửa trong `odometry_wheel`; mọi kết quả Boreas trước 2026-10-29 14:00 UTC
   không dùng được.
4. **Boreas, sau khi sửa odometry, CPC-HMM vẫn thua Xu'21** về điều hướng: FL 0.07–0.085 so với 0.018. Hai nguyên nhân
   đã đo:
   - **Độ trễ khi rời bản đồ** chiếm phần lớn FL. Chuỗi ở biên trên cần khoảng log((1−p_out)/p_out)/|KL₀| frame để
     xuống "off". Giảm p (tăng ARL₀) làm FL **tăng**.
     - Tách p_in/p_out (p_in = 0.01, p_out = 0.2) cho FL Boreas MegaLoc 0.029 → 0.007, recall 0.983 → 0.956 (offline).
     - Nhưng Nordland và 4S countryside mất nhiều recall (p_out = 0.05: Nordland 0.74 → 0.58).
     - Lưới điều hướng `CPC-HMM p_out=*` đang chạy.
   - **e^R vi phạm D_R:** P(p^R ≤ 0.01 | off) = 0.059 trên 4S countryside, P(p^R ≤ 0.05 | off) = 0.075 trên Boreas
     MegaLoc. Trong khi đó p^top vẫn super-uniform ở mọi dataset.
     - Null dùng odometry không nhiễu (Bổ đề 3, Anderson) **không** sửa được.
     - Nguyên nhân còn lại: aliasing kết hợp, top-1 trượt đều theo odometry trên đoạn đường giống, xảy ra sâu bên trong
       đoạn off-map dài.
5. **Thống kê dùng niềm tin HMM** (`fac_pc`, `fac_mix`): FL 0.08–0.14, do khoá nhầm.
6. **Mô hình hợp nhất trạng thái** (e-value vào từng nơi): đếm 1/N hai lần (`abs_naive`, recall 0.26) hoặc FL ≈ 0.9
   (`abs`).
7. **Giảm theo ESS** cho chuỗi vị trí: hết khoá nhầm nhưng mất khả năng xếp hạng.
8. **CPC-HMM thiếu tự tin** (ECE 0.08–0.28, overconf âm): an toàn nhưng chưa hiệu chuẩn.
9. **Độ trễ vào lại của CPC-HMM** chậm hơn Xu'21 trên Nordland (79 so với 36 frame). Nhanh hơn trên CMU (3 so với 31).

## 5. Điều kiện kiểm chứng (để tái tạo)

- **Bản đồ:** bỏ 30 % block (CFG block 300 m; Nordland theo frame), seed 0–2. Off-map khi khoảng cách tới bản đồ còn
  lại > off_d; on-map khi ≤ in_d; fix đúng khi sai số ≤ excl (25 m) hoặc tol.
- **Điều hướng:** Kalman vị trí (σ fix 5 m), odometry trôi (mô phỏng: 3 % scale, heading random walk 0.3°/bước) hoặc
  thật (4S VIO, Boreas bánh xe + gyro).
- **Baseline Xu'21:** emission exp(s/T), off-map exp(s₍ₖ₎/T), p_out = 0.01, p_in = 0.05; (T, k) ∈ {0.01, 0.02, 0.05} ×
  {5, 10, 20} chọn bằng nhãn trên 2 điều kiện dễ nhất với FL ≤ α.
- **Baseline khác:** per-frame SelfCal (p ≤ α), ngưỡng max-sim hiệu chuẩn bằng nhãn, accept-all, oracle.
- **Bổ sung 2026-10-31:**
  - Baseline có nhãn tái hiện từ paper (không có code gốc): Claxton'24 = MLP (32, 16) trên 6 đặc trưng profile
    similarity, huấn luyện bằng nhãn trên 2 điều kiện dễ nhất (`bsel`), chấp nhận khi P > 0.5; SafeVPR = điểm MNN patch
    DINOv2 trên top-20 + Mondrian LTT (FDR α = 0.05, δ = 0.1), chỉ có trên Boreas (`nhatlong1103/vpr-safevpr-scores`).
  - Đường cong: 48 ngưỡng (phân vị của điểm từng luật) + ngưỡng mặc định; Kalman ở 14 ngưỡng (`oc_curves.py`); so khớp
    chính xác: 200 ngưỡng, Kalman tại đúng ngưỡng khớp (`oc_matched.py`). Nhãn chỉ dùng để đánh giá.
  - 10 seed cho điểm mặc định (seed 0–9; NCLT 1 seed vì không có lỗ tổng hợp); đường cong và so khớp dùng seed 0–2.
  - Độ bền: `nav_demo.py --drop 0.1 / 0.5` (cùng mọi hằng số). NCLT: bản đồ 2012-01-08, 8 phiên query, excl 10 m, EKF có
    trạng thái lệch hướng.
  - Mọi số trong §N tái tạo từ cache công khai `nhatlong1103/hmm-navcache-v2` (10 seed) và `hmm-navcache-holes` bằng
    `oc_curves.py --variants [--defaults-only] [--cs-sens]`, `oc_matched.py`, `lodo_select.py`, `paper/build_oc_report.py`.
