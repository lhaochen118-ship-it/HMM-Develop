# MASTER RESEARCH PLAN v3 — HMM cho Monocular Sequence-based Visual Localization

*Bản vận hành (operative) dành cho AI Research/Coding Agent. Kế thừa và **không thay thế** hai tài liệu gốc của người
dùng: "HMM_Master_Research_Plan_Integrated.pdf" (v2.0, 38 trang) và "HMM_Operations_Plan_v1.3_Idea_Bank.pdf"
(34 trang). Mọi ID (T*, E*, H*, M*, A*, G*, I*) giữ nguyên nghĩa của v2.0/v1.3; v3 chỉ thêm H20+, E32+, A21+,
và đặc tả phương pháp trung tâm. Trạng thái thực tế luôn nằm ở `research/STATE.md` + `research/registry/runs.jsonl`,
không nằm trong tài liệu này.*

---

## 0. Cách đọc và quy tắc ưu tiên

| Tài liệu | Vai trò |
|---|---|
| `AGENTS.md` | thứ tự đọc, chính sách bằng chứng, quy tắc an toàn |
| `research/STATE.md` | phase, gate, 3 việc tiếp theo, blocker, kernel đang chạy |
| `research/MASTER_PLAN.md` (file này) | khoa học: câu hỏi, giả thuyết, phương pháp, giao thức, gate |
| `research/PROTOCOL.md` | giao thức đã **khóa** (split, metric, quy tắc chọn tham số) |
| `research/HYPOTHESES.md`, `FINDINGS.md`, `DECISIONS.md`, `ISSUES.md` | sổ giả thuyết / phát hiện / quyết định / lỗi |
| `research/registry/runs.jsonl`, `research/runs/<run_id>/` | nguồn duy nhất cho mọi con số |

Xung đột: luật/licence/chính sách nền tảng > chỉ dẫn hiện hành của người dùng > PROTOCOL đã khóa > file này > mặc định vận hành.
Ràng buộc người dùng (27/11/2026): **HMM phải là trung tâm**. Mọi cơ chế mới phải là một thành phần *của* một HMM
(emission, transition, state space, inference) — không được là một cơ chế khác "giống HMM".

---

## 1. Tóm tắt điều hành

**Câu hỏi trung tâm.** Khi nào và vì sao thông tin thời gian, khai thác bằng một HMM đúng nghĩa (state ẩn = vị trí trên
bản đồ, emission = bằng chứng thị giác, transition = chuyển động), giúp định vị thị giác đơn mắt; và làm thế nào để HMM
giữ được lợi ích đó khi các giả định cổ điển (quan sát độc lập có điều kiện, vận tốc biết trước, bản đồ đầy đủ,
likelihood đúng) bị vi phạm?

**Luận điểm khoa học đề xuất (chưa phải kết luận).** Thất bại/hạn chế của HMM trong VPR chủ yếu *không* nằm ở cấu trúc
Markov mà ở **ba lỗi đặc tả emission/transition có thể sửa trong khuôn khổ HMM**:
(i) emission là *potential* (s/τ) chứ không phải likelihood ratio đã hiệu chỉnh → null/off-map và confidence sai;
(ii) quan sát liên tiếp **phụ thuộc** (video-rate, dừng xe) → đếm trùng bằng chứng, khóa sai tự tin;
(iii) prior chuyển động **ngầm oracle** (v=1 trên Nordland đồng bộ) → lợi ích bị thổi phồng, sụp đổ khi tốc độ thay đổi.
Phương pháp trung tâm **IA-HMM (Information-Aware, calibrated HMM)** sửa cả ba mà vẫn là HMM:
emission = LLR hiệu chỉnh có null chính xác (M1), trọng số bằng chứng từng frame suy ra từ emission AR(1)
(M2, *mới*), transition trên đồ thị bản đồ theo arc-length mét + vận tốc ẩn (M3), suy luận forward / fixed-lag /
Viterbi chính xác trên state rời rạc.

**Bằng chứng hiện có (27/11/2026, mức [S], chi tiết `reports/REPORT_v1.md`, `FINDINGS.md` F01–F12):**
- H1 [S+]: HMM ≥ ảnh đơn ở 16/16 ô (Nordland, Nordland time-warp, CMU, RobotCar × NetVLAD/CosPlace/SALAD/MegaLoc);
  lớn nhất khi ảnh đơn yếu (Nordland winter NetVLAD 0.120→0.954).
- H22 [S+]: IA-HMM ≥ SeqSLAM tuned ở 12/16 ô, ngang (≤0.6 điểm) ở 4 ô; dưới vận tốc thay đổi SeqSLAM < ảnh đơn.
- H3 [S+]: prior v=1 đồng bộ thổi phồng lợi ích (−65% khi time-warp); H17 [S+/partial]: LV+ME+IA phục hồi 61–84% oracle.
- H5/H6 [S+]: β* giảm theo frame-rate (0.1 ở stride 1); β=1 ở video-rate gây CW@0.9 = 18%.
- H20: IA đơn lẻ [S−] trên CMU; có lợi ở video-rate Nordland (NLL −17…−35%) và khi kết hợp state vận tốc (time-warp).
- H7 [S−]: null LLR hiệu chỉnh không vượt null quantile đã tune; lọc thời gian là thứ làm off-map tốt (AUROC 0.88→0.99).
- H13 [S+]: chuyển siêu tham số CMU↔RobotCar giữ 60–110% lợi ích.

---

## 2. Đặc tả bài toán và mô hình toán học

### 2.1 Hai tầng: VPR vs 6DoF
- **VPR/topological**: state z_t ∈ {1..M} ∪ {∅}; đầu ra: belief b_t, top-k, xác suất off-map, confidence theo tolerance.
- **6DoF**: T_t ∈ SE(3). Phân rã p(T_t | I_{1:t}) = Σ_j p(T_t | z_t=j, I_t) · b_t(j): HMM chọn/khóa *vùng* bản đồ,
  hình học (PnP / pose của reference) cho pose. HMM **không** thay thế hình học; nó (a) giảm sai retrieval (lỗi chiếm ưu
  thế ở ngưỡng (5 m,10°) đêm), (b) cung cấp confidence/abstain, (c) chọn ứng viên cho verification dưới ngân sách cố định (M5).

### 2.2 HMM chuẩn của dự án
- Bản đồ: M ảnh reference, descriptor r_j (chuẩn hoá L2), pose C_j,R_j. Chuỗi bản đồ có thứ tự (traversal tham chiếu),
  vị trí arc-length s_j = Σ‖C_{i+1}−C_i‖ (bước nhảy >30 m bị cắt = discontinuity). Nordland: s_j = chỉ số frame.
- State: z_t = (j, k) với k ∈ {1..K} bin vận tốc (K=1 nếu không dùng), cộng state null ∅.
- Transition (bảo toàn khối lượng; A_k hàng-ngẫu nhiên trên on-map):
  b̃(j,k') = (1−η)[Σ_{i,k}(1−e)P(k'|k)A_{k'}(i,j)b(i,k) + (1−ρ)r_j P₀(k')b(∅)] + η·u_j P₀(k')·(on-map mass);
  b̃(∅) = e·Σb(i,k) + ρ·b(∅);  A_k(i,j) ∝ N(s_j − s_i; v_k, σ_k²) cắt ở ±4σ, chuẩn hoá theo hàng (biên).
- Emission: l_t(j) = log p(o_t|z=j) − log p(o_t|z=∅) (log-likelihood ratio so với giả thuyết "mọi reference đều
  non-match") ⇒ **l_t(∅)=0 chính xác**. Update: b_t ∝ b̃_t · exp(β_t l_t).
- Kiểm chứng: `tests/test_hmm_core.py` so filter với liệt kê vét cạn mọi quỹ đạo (G0 PASS).

### 2.3 Vì sao HMM có thể thất bại (chuỗi nhân quả cần kiểm chứng)
1. **Information vs mismatch** (v2.0 §4.2): R_seq − R_img = −I(Z_t;H_t|O_t) + ε_seq − ε_img. Lịch sử luôn có
   thông tin ≥0; thuật toán chỉ thua ảnh đơn khi sai số mô hình ε_seq lớn hơn.
2. **Phụ thuộc quan sát**: với residual AR(1) tương quan ρ, mỗi frame mới chỉ mang (1−ρ)/(1+ρ) thông tin Fisher của
   một frame độc lập. HMM ngây thơ dùng β=1 ⇒ log-odds tăng nhanh gấp (1+ρ)/(1−ρ) lần ⇒ over-confidence, lock-in.
3. **Motion mismatch**: kernel hẹp sai vận tốc ⇒ true state bị đẩy ra ngoài support; kernel quá rộng ⇒ mất thông tin.
4. **Emission sai dạng**: s/τ tối ưu NLL ảnh đơn không phải LLR; null heuristic (quantile) không cùng thang.
5. **Aliasing có cấu trúc**: hai quỹ đạo có cùng likelihood + prior ⇒ không thuật toán nào phân biệt (giới hạn thông tin).

---

## 3. Kế thừa và kiểm toán (Phase 1 đã thực hiện phần lớn)
- Kế thừa: feature bank 6 descriptor (SALAD, MegaLoc, MixVPR, CosPlace, NetVLAD, DINOv2) đã dump trên Kaggle
  (kernels `dive-vpr-nb15a..d-dump`, `hmm-d4s-0`): Nordland 4 mùa (4500 frame/mùa), RobotCar v2 (6954 ref + 1906 query
  có pose), CMU 11 slice, 4Seasons 3 recording ⇒ **tiết kiệm ~6–8 GPU-giờ**.
- Mới: `kaggle/k01_nordseg` (Nordland stride-1, 2 block × 2500 frame × 4 mùa × {SALAD, MegaLoc, NetVLAD, CosPlace}).
- Lỗi legacy A01–A20 và lỗi mới A21–A22: `ISSUES.md` (trạng thái FIXED/OPEN, có test).
- CCBF (M4): **park** — bằng chứng legacy (τ theo mùa gần bằng nhau) cho thấy không có headroom; chỉ mở lại nếu G3
  (oracle condition giảm NLL ≥10%) đạt trên RobotCar.

---

## 4. Phương pháp trung tâm: IA-HMM (module, cơ sở, giả thuyết, kill criteria)

> Nguyên tắc: mỗi module là một **thành phần của HMM** và có thể tắt độc lập để ablation (factorial M1×M2×M3).

### M1 — Emission là likelihood ratio đã hiệu chỉnh, null chính xác
- Mô hình: logit p(match | x_tj) = wᵀx_tj + b với x = [s, z-score theo frame, (tùy chọn) hiệu chỉnh hubness CSLS
  s − ½μ_j]. LLR = logit − log(π/(1−π)), π = tỉ lệ match quần thể.
- Ước lượng: mẫu Horvitz–Thompson (mọi positive; n_hard negative điểm cao nhất trọng số 1; n_rand negative ngẫu nhiên
  trọng số n_rest/n_rand) ⇒ ước lượng không chệch của logit quần thể (sửa A22).
- Vì sao vẫn là HMM: chỉ thay hàm emission; null có l(∅)=0 đúng nghĩa xác suất (mọi reference là non-match).
- Giả thuyết H7; kill nếu NLL cải thiện <3% trên ≥2 dataset ⇒ giữ softmax-τ (đơn giản hơn).

### M2 — Information-aware evidence weighting (đóng góp mới, H20)
- Mô hình emission có điều kiện AR(1): p(o_t | z_t, o_{t−1}). Với LLR Gaussian, thông tin Fisher của o_t|o_{t−1}
  = (1−ρ_t)/(1+ρ_t) lần thông tin frame độc lập ⇒ dùng power-likelihood β_t = β₀(1−ρ_t)/(1+ρ_t) trong update HMM.
- ρ_t **không cần nhãn**: u_t = min(1, (1 − q_t·q_{t−1})/κ) (tỉ lệ thay đổi ngoại quan "mới"), ρ_t = 1 − u_t
  ⇒ β_t = β₀ u_t/(2−u_t). Dừng xe (q_t = q_{t−1}) ⇒ β_t → 0 (frame trùng không thêm bằng chứng); frame độc lập ⇒ β₀/1.
- Tham số: β₀ và κ (κ chọn trong lưới quantile của phân phối thay đổi trên calibration — không cần nhãn cho κ).
- So sánh bắt buộc (cùng emission, cùng kernel): β=1; β cố định tối ưu dev; keyframing (bỏ update khi thay đổi < ngưỡng);
  β=1/VIF(ρ̂) (H6b). Novelty threat: tempering/coarsening (Bissiri 2016, Miller & Dunson 2019), keyframes, acoustic scale
  ASR ⇒ novelty nằm ở *ước lượng ρ_t không nhãn, từng frame, từ luồng descriptor, có dẫn xuất AR(1)*.
- Kill: NLL gain <2% hoặc R@1 giảm >1 điểm so với β cố định trên ≥2 dataset video-rate.

### M3 — Transition trên đồ thị bản đồ (mét) + vận tốc ẩn
- Kernel theo arc-length mét (không theo chỉ số ảnh): bất biến với mật độ bản đồ. State (j,k) với bin vận tốc
  {0, .5, 1, 1.5, 2, 3}×đơn vị/frame, P(k'|k) sticky; HSMM dwell khi dừng (I15-C) nếu cần.
- Tùy chọn: cạnh "junction" nối các node gần nhau về không gian nhưng xa trong thứ tự (vòng lặp/giao lộ, I17).
- Kiểm chứng chính: time-warp (dừng-đi, chậm, nhanh) trên Nordland; so oracle per-step kernel (chẩn đoán).
- Kill: latent velocity không vượt kernel rộng cố định (cùng budget) trên ≥2 dataset ⇒ dùng kernel rộng.

### M4 — CCBF (condition-aware): parked (xem §3).
### M5 — HMM-guided 6DoF: dùng posterior top-k làm ứng viên cho LightGlue+PnP dưới ngân sách matching cố định; pose
  ước lượng = pose của reference/hình học; báo (0.25 m,2°)/(0.5 m,5°)/(5 m,10°). Chỉ sau G4.
### M6 — Open-world: null + exit/re-entry + recovery leak η; đo off-map AUROC, FPR@95TPR, thời gian phục hồi.
### Suy luận: forward (online), fixed-lag ℓ (H21, latency ℓ frame), Viterbi (offline). Cùng mô hình, khác truy vấn.

---

## 5. Giả thuyết và tiêu chí (xem `HYPOTHESES.md` — ngưỡng đã khóa)
Ưu tiên kiểm chứng: H1 (khả thi), H22 (HMM vs SeqSLAM), H23/H2 (theo độ mạnh descriptor), H20 (IA), H3/H17 (time-warp,
vận tốc), H7 (LLR), H21 (fixed-lag), H19 (recovery/off-map), H13 (cross-dataset).

---

## 6. Datasets, giao thức, metric
Xem `PROTOCOL.md` (đã khóa). Tóm tắt vai trò:

| Dataset | Đặc điểm | Vai trò khoa học |
|---|---|---|
| Nordland 4 mùa (stride≈8) | 728 km, đồng bộ frame, mùa đông khó | H1/H2/H23, time-warp (H3/H17), off-map holes |
| Nordland video-rate (k01) | stride 1, có đoạn dừng ga | H5/H20 (phụ thuộc), stride sweep |
| RobotCar Seasons v2 | 9 điều kiện, đêm, chuỗi ngắn ~8 frame | điều kiện khó, 6DoF thô, cold-start |
| Extended CMU Seasons | 11 slice, 12 ngày, 14 Hz, xe dừng/chạy | H20 (video-rate thật), H1, cross-condition |
| 4Seasons (dump có sẵn) | VIO/RTK, 3 recording | M3 VO (sau), H17 |

Baselines: B01 single (softmax-τ hiệu chỉnh), B04 SeqSLAM causal (L, enhancement chọn trên dev), B06/HMM-0R
(τ-emission, β=1), B08 HMM+null; ablation thang HMM-0R → +M1 → +M2 → +M3 → fixed-lag.

---

## 7. Kế hoạch triển khai theo giai đoạn (task cards)

Ký hiệu: Done = điều kiện hoàn thành; Go/Kill = điều kiện tiếp tục/bỏ; Compute ước lượng.

### Giai đoạn 1 — Khảo sát, audit, lý thuyết (CPU)
| Task | Mục tiêu / bước | Input → Output | Done | Compute/Risk |
|---|---|---|---|---|
| T1.1 | đóng băng snapshot, audit A01–A22 | repo f376568 → `ISSUES.md` | mỗi issue có trạng thái + test | CPU; rủi ro: lỗi ẩn → thêm test |
| T1.2 | literature theo §11 (≥3 đối thủ gần nhất/module) | web, PDF v2.0 Phụ lục C → `LITERATURE.md` | mỗi ref có trạng thái ✓/○/⚠ | không bịa ref; ⚠ không dùng làm bằng chứng |
| T1.3 | novelty matrix M1–M3 vs prior art | → `NOVELTY.md` | mỗi claim có đối chứng | va chạm novelty ⇒ thu hẹp claim |
| T1.4 | lý thuyết: dẫn xuất β_t từ AR(1), điều kiện, giới hạn | → `THEORY.md` + test synthetic | dẫn xuất kiểm bằng mô phỏng | claim chỉ dưới giả định nêu rõ |

### Giai đoạn 2 — Hạ tầng benchmark (CPU + GPU nhỏ)
| Task | Mục tiêu | Output | Done |
|---|---|---|---|
| T2.2 | adapter Nordland/RobotCar/CMU từ dump (✔ `hmmloc/data.py`) | Episode | GT sanity: q→ref median 0.54 m (RC) |
| T2.3 | feature bank (✔ reuse nb15a–d; ✔ k01 nordseg) | `.npy` fp16 + meta | checksum/shape, R@1 khớp log dump |
| T2.4 | metrics + bootstrap theo sequence (✔ `metrics.py`) | | test |
| T2.5 | biến thể có kiểm soát: time-warp (✔), holes/detour, kidnap | `data.timewarp`, … | seeded |
| T2.6 | PROTOCOL khóa (✔) | `PROTOCOL.md` | trước khi xem test |
| T2.7 | sửa HMM core (✔), test vét cạn (✔) | `hmm.py`, tests | **G0 PASS** |

### Giai đoạn 3 — Khả thi HMM (CPU)
| Task | Thí nghiệm | Done / Gate |
|---|---|---|
| T3.3 | E01 thang HMM × 3 dataset × ≥4 descriptor (`hmmloc/exp/e01_ladder.py`) | bảng + CI ⇒ **G2** (ΔR@1>0 CI trên ≥2/4 dataset) |
| T3.1 | E08 time-warp (`e03_timewarp.py`), oracle motion | H3, H17 |
| T3.4 | E06/E07 stride/duplicate trên nordseg; ρ̂, β* | H5, H6b |
| T3.5 | SeqSLAM tuned (✔ trong E01) | H22 |
| T3.6 | holes/detour/kidnap/off-map (M6) | H19 |
| T3.7 | runtime M∈{1k,10k,30k} | H14 |

### Giai đoạn 4 — Chẩn đoán nguyên nhân (CPU)
T4.1 taxonomy lỗi (outage: true rank>K; aliasing lock-in; motion lag; cold-start; confident-wrong) trên các run E01.
T4.3 can thiệp: oracle-emission swap / oracle-transition swap (2×2, I01); descriptor ladder (I02); duplicate injection (I03).
Gate **G4**: ≥1 nguyên nhân có can thiệp hỗ trợ trên ≥2 dataset.

### Giai đoạn 5 — IA-HMM (CPU)
T5.1 M1 (E25), T5.2 M2 (E15 = `e02_infoaware.py`), T5.3 M3 (E08/E18), factorial M1×M2×M3 (E28), fixed-lag (H21).
Chọn cấu hình cuối theo dev; khóa trước khi chạy test cuối.

### Giai đoạn 6 — Tổng quát hoá & thống kê
Leave-one-dataset-out cho siêu tham số (H13); robust (fps, map holes, corruption); seeds; Holm cho họ H1/H20/H22.
Gate **G5**: lợi ích so với baseline mạnh nhất cùng ngân sách, CI, ablation, runtime.

### Giai đoạn 7 — Hoàn thiện
Báo cáo khoa học, bảng sinh từ registry, gói tái lập (`README_REPRO.md`), giới hạn và hướng tiếp (6DoF M5, VO M3).

---

## 8. Ma trận thí nghiệm (v3 bổ sung)
| E | Nội dung | Script | H |
|---|---|---|---|
| E01 | thang HMM (single, SeqSLAM, HMM τ, +β, +LLR, +z, +vận tốc) | `e01_ladder.py` | H1,H7,H22,H23 |
| E08 | time-warp + oracle motion | `e03_timewarp.py` | H3,H17,H20 |
| E15 | IA-HMM vs β cố định vs keyframe | `e02_infoaware.py` | H20,H6b |
| E32 | fixed-lag ℓ∈{0,2,5,10} | (Bench.run lag=) | H21 |
| E33 | stride sweep nordseg {1,2,5,10} × IA | `e02_infoaware.py nordseg{s}` | H5,H20 |

## 9. Decision gates (giữ G0–G6 của v2.0)
G0 correctness ✔ (tests). G1 benchmark trust: R@1 ảnh đơn khớp log dump (✔ CMU/RobotCar/Nordland). G2 khả thi.
G3 condition (CCBF) — parked. G4 nguyên nhân gốc. G5 phương pháp cuối. G6 công bố (cần người dùng duyệt).

## 10. Vận hành (Research OS + Kaggle)
- Vòng lặp: giả thuyết → (khóa tiêu chí) → thí nghiệm nhỏ nhất → registry → phân tích → quyết định (`DECISIONS.md`).
- Trigger tự điều chỉnh (v2.0 §10.6): "too good" ⇒ audit leakage; 3 vòng inconclusive ⇒ đổi chẩn đoán; bug ⇒ A##,
  invalid run, rerun.
- GPU: chỉ trích xuất descriptor (Kaggle T4, `kaggle/`), không dùng nguồn competition để mở tier GPU; token chỉ ở
  scratchpad, không commit. HMM chạy CPU từ feature bank.
- Mỗi phiên kết thúc: cập nhật STATE/FINDINGS/DECISIONS/ISSUES, commit + push nhánh làm việc.

## 11. Tài liệu (bản đồ rút gọn; chi tiết và trạng thái xác minh ở `LITERATURE.md`)
Nền tảng: Sattler CVPR'18; Toft TPAMI'22. Sequence không xác suất: SeqSLAM (Milford & Wyeth ICRA'12), SMART,
network flow (Naseer AAAI'14), Vysotska & Stachniss RA-L'16. HMM/Bayes VPR: FAB-MAP (Cummins & Newman IJRR'08),
CAT-SLAM, Hansen & Browning IROS'14 (HMM + velocity), Doan et al. ICCV'19 / HM⁴ RA-L'21, Xu et al. RA-L'21
(topometric, new place), Jaenal et al. IJRR'23 (SMC topometric). Learned sequence: SeqNet, SeqMatchNet, JIST, CaseVPR.
Descriptors: NetVLAD, CosPlace, MixVPR, SALAD, MegaLoc. Uncertainty: SUE (Zaffar CVPR'24), STUN, BTL, Carson RA-L'22.
Generalised Bayes/tempering: Bissiri et al. JRSS-B'16; Miller & Dunson JASA'19. HMM lý thuyết: Rabiner'89; Cappé et al.'05;
HSMM (Yu'10); AR-HMM. Đánh dấu ⚠ cho các preprint 2026 chưa xác minh (TRAIL, UniPR-3D, SG2Loc, Adapt-STformer).
