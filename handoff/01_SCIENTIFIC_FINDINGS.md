# DIVE-HMM → CRSG — Scientific Findings & Contributions (Handoff)

> **Superseded (2026-10-28):** CRSG was dropped after the literature gate. The current contribution is SelfCal; see `handoff/03_HANDOFF_NEW_CHAT.md`, `RESEARCH_LOG.md` Entries 11–13 and `paper/selfcal_paper.md`. The negative findings below (CCBF inert, temperature scaling) are still valid.

*Chi tiết toàn bộ phát hiện khoa học positive + negative của phiên làm việc. Mọi con số đã verify trên Kaggle
(T4/khi ghi rõ). Đọc kèm `RESEARCH_LOG.md` (nhật ký 10 entry) và `PAPER_DRAFT.md` (bản thảo) trong repo.*

Project domain: **Visual Place Recognition (VPR) / topological localization dưới appearance change** (mùa, thời
tiết, ngày/đêm). Descriptor chính: **SALAD** (DINOv2 ViT-B/14 backbone, dim 8448), frozen, không fine-tune.
Datasets: RobotCar-Seasons v2, Extended-CMU-Seasons, Nordland (4 mùa).

---

## 0. Tóm tắt một dòng

Ý tưởng kế thừa (**CCBF** — bộ lọc Bayes factored place×condition với temperature theo điều kiện) **thất bại/trơ**.
Qua vòng lặp Generate→Critique→Pivot, đóng góp mới được tìm ra và kiểm chứng là **CRSG (Calibrated
Retrieval-Score Geometry)**: một calibrator per-frame 2–3 tham số trên *hình học của vector điểm retrieval*
(margin top1−top2, NN-distance, score entropy) → một **reliability score** calibrated cho cả confidence lẫn
open-set abstention. Kèm theo là một **reality-check**: các phương pháp phức tạp (sequential filtering,
condition-aware calibration) chỉ thắng trên benchmark lý tưởng (Nordland) và **thất bại trên dữ liệu thực tế**
(RobotCar, CMU), nơi CRSG thống trị.

---

## 1. Bối cảnh & research gap (positive framing)

- VPR được benchmark gần như hoàn toàn bằng **recall@K**, vốn đang **bão hòa**: SALAD đạt R@1 ≈ 0.94–0.98 trên
  RobotCar ở ngưỡng 5 m cho **mọi** điều kiện kể cả night.
- Thứ mà triển khai thực tế (robotics/AV/loop-closure) cần là **độ tin cậy (reliability)**: (a) confidence có
  **calibrate** không, (b) biết khi nào **lạc khỏi bản đồ / off-map** (open-set abstention).
- Trục reliability này **ít được nghiên cứu**; các công cụ sẵn có (temperature scaling, SUE — Zaffar'24) **yếu**.
- **Gap đã verify:** confidence retrieval bị **miscalibrated nghiêm trọng** ngay cả khi recall ~bão hòa; và
  miscalibration **phụ thuộc điều kiện theo HÌNH DẠNG phân phối điểm** (night bị nén), chứ không chỉ theo scale —
  nên một scalar temperature (global hay per-condition) không sửa được.

---

## 2. Các phát hiện NEGATIVE (đã kiểm chứng — có giá trị khoa học)

### 2.1 CCBF / condition-aware temperature là **INERT** (2 dataset)
- Fit temperature per-condition τ_c (cơ chế lõi của CCBF): các τ_c **gần như y hệt nhau**.
  - Nordland: τ spread = **1.22×** (spring/summer/fall 0.0309, winter 0.0253).
  - RobotCar: τ spread = **1.49×** (hầu hết ~0.0253; night 0.0208; overcast-summer 0.0309).
- Per-condition τ cải thiện pooled ECE so với global τ ≈ **0%** (cả hai dataset).
- **Nhưng appearance gap là THẬT:** trên RobotCar, night/night-rain có match–nonmatch margin (~0.088) chỉ bằng
  **một nửa** day (~0.17); night match-score 0.384 vs day 0.58. Vấn đề: một **scalar** τ không biến gap thật này
  thành lợi ích calibration. → **Condition-conditional temperature là sai knob.**
- Ý nghĩa: cảnh báo trực tiếp với các hướng "thêm condition-awareness" bằng temperature — chúng không giúp khi
  descriptor SOTA đã khá robust về điều kiện.

### 2.2 Sequential Bayesian filtering là **REGIME-SPECIFIC** (không generalize)
- Trên **Nordland (dày đặc, frame-aligned 1:1, idealized)**: filter **xuất sắc** — ECE single→filter
  0.076→0.028; AURC ≈ oracle (0.019 vs 0.018 @scale); off-map AUROC 0.99 (≫ SUE 0.94). Đây là "sân nhà".
- Trên **RobotCar (thưa, thực tế)**: filter **không sửa được calibration** (ECE 0.472→0.439), và **thua SUE ở
  off-map** (0.888 vs 0.950) — ngược hẳn Nordland.
- Trên **CMU (thực tế, đa route)**: filter off-map **sụp đổ** (AUROC **0.228**, tệ hơn random); ECE 0.32,
  conf-AUROC 0.65 — thất bại rõ.
- Đã **loại trừ artifact setup**: traversal RobotCar có velocity ~1 (median Δ=1, 97–99% bước ∈[0,3]); motion model
  khớp. Filter fail là **thật**.
- **Cơ chế (NB8):** calibrate posterior của filter (CRSG-filter) sửa được ECE nhưng **không** tái tạo
  discrimination (AURC 0.137 ≈ filter thô ≫ CRSG-single 0.090). → Tín hiệu discrimination nằm ở **margin
  single-image**, và filter **phá hủy** nó trên dữ liệu thưa; không calibration nào hồi phục được. "Calibrate the
  belief" không phải free lunch — phải calibrate đúng belief mang discrimination.
- Ý nghĩa: **đánh giá reliability chỉ trên Nordland là gây hiểu lầm**; đây là reality-check cross-benchmark.

### 2.3 Một "negative phụ" đáng giữ
- softmax-max trên ~180–200 ứng viên gần hòa **không phải tín hiệu correctness** → ECE single-image thảm
  (RobotCar ~0.47–0.55; CMU tới 0.65 ở tol=2m). Temperature scaling chỉ giảm nhẹ, không sửa được bản chất.

---

## 3. Phát hiện POSITIVE — CRSG (đóng góp chính, đã verify)

**Phương pháp.** Với vector similarity s ∈ ℝ^M (query vs map), tính per-frame **geometry features**:
margin **gap12 = s₍₁₎−s₍₂₎**, **NN-distance** √(2−2·max s) (≡ SUE), **score entropy** (và maxsim). Fit một
**logistic calibrator** g(·) (2–3 feature) dự đoán correctness (fit trên held-out). g(s) là **một reliability
score calibrated** dùng cho: (i) confidence, (ii) selective prediction / abstention, (iii) open-set detection
(reliability thấp ⇒ off-map). Không cần temporal stream, không cần condition label, descriptor-agnostic.

**Insight:** softmax-max không monotone với correctness khi có nhiều near-tie; **margin thì có**, và NN-distance
bắt được OOD. Một calibrator 2–3 tham số là đủ.

### 3.1 Calibration + discrimination (pooled cross-fit)

RobotCar hard conditions, tol=2m (acc 0.765):

| method | ECE | AURC ↓ | conf-AUROC ↑ |
|---|---|---|---|
| softmax (uncal) | 0.485 | 0.133 | 0.749 |
| temperature scaling | 0.303 | 0.135 | 0.736 |
| sequential fixed filter | 0.301 | 0.132 | 0.677 |
| CCBF | 0.269 | 0.130 | 0.671 |
| **CRSG (ours)** | **0.069** | **0.090** | **0.801** |
| oracle AURC | — | 0.030 | — |

CRSG cho **discrimination tốt nhất (AURC, conf-AUROC) ở MỌI tolerance** {0.5,1,2,5}m, và ECE gần tốt nhất, đập
softmax/temperature/filter/CCBF. Các phương pháp sequential/condition **không** cho discrimination gain so với
softmax.

### 3.2 Open-set / off-map (reliability thống nhất)
- RobotCar: CRSG 0.949 ≈ SUE 0.948 > filter-null 0.898.
- CMU: SUE 0.895, CRSG 0.861, **filter-null 0.228 (sụp)**.
- Nordland: **filter-null 0.992** > SUE 0.935 > CRSG 0.804 (filter thắng trên dữ liệu dày đặc).

### 3.3 Cross-dataset (regime-dependence — bức tranh trung thực)

| dataset (regime) | tol | CRSG | filter | ghi chú |
|---|---|---|---|---|
| RobotCar (thưa, thực tế) | 2m | **thống trị** | fail | CRSG best ECE/AURC/conf-AUROC |
| CMU (thưa, thực tế, 4 route) | 2m | **thống trị** | fail (ECE 0.32) | xác nhận ở scale N=7395 |
| Nordland (dày, lý tưởng) | 0 fr | competitive | **best AURC+off-map** | filter sân nhà; CRSG beat softmax/temp, best conf-AUROC |

→ **CRSG là method robust-across-regime, stream-free**; filter là regime-specific.

### 3.4 Descriptor-agnostic (SALAD vs DINOv2)
- CRSG **sửa calibration cho cả hai** descriptor (ECE 0.03–0.06 vs softmax/temperature 0.2–0.7) và **thắng
  off-map cho cả hai** (DINOv2: CRSG 0.861 ≫ SUE 0.746 — descriptor yếu làm SUE thô kém, CRSG multi-feature vẫn
  robust).
- **Nuance trung thực:** lợi thế **discrimination** của CRSG so với softmax ranking **lớn hơn với descriptor
  mạnh** (rõ với SALAD, ~ngang với DINOv2). → Claim "calibration + open-set" là descriptor-agnostic; claim
  "discrimination dominance" phát biểu cho descriptor mạnh.

### 3.5 Conformal risk control (chiều sâu lý thuyết)
Selective predictor trên CRSG score với guarantee finite-sample (RCPS/Hoeffding UCB, δ=0.1), RobotCar tol=2m:
- **C1 — risk control + coverage:** ở target α=0.10, **CRSG certify coverage 61.5%** (realized risk 0.11) trong
  khi **softmax certify 0%** (phải abstain toàn bộ) → CRSG là conformity score mạnh hơn hẳn.
- **C2 — shift phá guarantee:** fit benign → deploy night, realized risk vượt target (α=0.20 → 0.304) — cảnh báo
  khi calibrate reliability trên dữ liệu dễ.
- **C3 — Mondrian khôi phục:** per-condition thresholds đưa worst-condition risk **0.221 → 0.000** (≤ target).

### 3.6 Full-scale validation (RTX-intended, chạy T4 vì RTX bận)
- **Nordland 3000/mùa (N=9000):** nhất quán bản 800/mùa — CRSG đập softmax/temperature, conf-AUROC tốt nhất
  0.957; filter giữ lợi thế AURC (0.011) + off-map (0.981) trên dữ liệu dày.
- **CMU 4 route (N=7395):** CRSG đập baseline calibrated-maxsim (AURC 0.143 vs 0.159; conf-AUROC 0.759 vs 0.732;
  tol=5m conf-AUROC 0.854 vs 0.788); filter fail (ECE 0.321, conf-AUROC 0.647).

---

## 4. Contribution statement (cho paper)

1. Một **reliability evaluation protocol** cho VPR (calibration + selective risk via AURC + open-set, swept over
   tolerance) phơi bày vấn đề bị che bởi recall ở ngưỡng lỏng, và phát hiện **reliability của VPR là
   regime-dependent**.
2. Một chứng minh cross-benchmark nghiêm túc rằng **condition-aware calibration là inert** và **sequential
   filtering là regime-specific** (near-oracle trên Nordland, sụp trên RobotCar+CMU), kèm **cơ chế** (filter phá
   hủy margin single-image; calibrate posterior không tái tạo được discrimination).
3. **CRSG** — calibrator per-frame tầm thường, descriptor-agnostic, stream-free trên retrieval-score geometry, là
   **default robust-across-regime**: thắng softmax & temperature trên cả 3 dataset, thống trị 2 dataset thực tế,
   competitive trên Nordland.
4. **Conformal risk control** trên CRSG score: guarantee selective-prediction finite-sample, conformity score
   mạnh hơn softmax, chứng minh marginal guarantee vỡ dưới appearance shift, và khắc phục bằng Mondrian.

---

## 5. Đánh giá A* thẳng thắn (positive + negative)

**Điểm mạnh:** 3 dataset + 2 descriptor + lý thuyết (conformal) + reality-check bất ngờ (simple đập complex) +
negative results trung thực. Nội dung khoa học đã ở tầm A*.

**Rủi ro/điểm yếu còn lại (cần giải quyết để chắc A*):**
- Đánh giá dùng **pose-GT tự dựng + train split** (RobotCar train.txt, CMU date-poses, Nordland frame-aligned),
  **chưa phải protocol benchmark chính thức** (RobotCar-Seasons test split + ngưỡng 0.25m/0.5m/5m). Reviewer
  top-tier sẽ muốn số chuẩn. **Đây là lỗ hổng credibility lớn nhất.**
- Mới 2 descriptor (SALAD, DINOv2) — cần thêm (BoQ/MixVPR) để claim descriptor-agnostic mạnh hơn.
- Chưa có figures (reliability diagram, risk–coverage curve) và chưa viết full paper.
- CRSG rất đơn giản → trọng tâm phải là *reality-check + simple-beats-complex + guarantees*, không phải độ phức
  tạp phương pháp.
