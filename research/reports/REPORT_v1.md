# Báo cáo nghiên cứu v1 — HMM cho Monocular Sequence-based Visual Localization

*Ngày 27/11/2026 · nhánh `claude/nice-fermi-l7bzd6` · mọi con số được sinh từ `research/registry/runs.jsonl`
(run ID trong ngoặc). Mức bằng chứng: [S] = dev/limited (giao thức khóa, split theo sequence, CI bootstrap theo
sequence, một lần chạy test cho mỗi cấu hình) — **chưa phải [V]** vì chưa có held-out dataset thứ tư, chưa đa seed
cho mọi ô, và chưa so với learned sequence methods (JIST/SeqVLAD) hay 6DoF hình học.*

## 1. Câu trả lời ngắn cho các câu hỏi nghiên cứu

| Câu hỏi | Trả lời theo bằng chứng hiện có |
|---|---|
| HMM có phù hợp với Visual Localization không? | **Có, ở tầng place/topological** [S]. HMM (state = node bản đồ ± vận tốc, emission = bằng chứng thị giác) cải thiện R@1 so với ảnh đơn trong **16/16** ô dataset×descriptor, cải thiện mạnh nhất khi ảnh đơn yếu (Nordland winter NetVLAD 0.120→0.954). Ở tầng 6DoF chính xác (0.25 m/0.5 m), HMM chỉ chọn đúng vùng; pose mịn cần hình học (M5, chưa làm). |
| Thông tin thời gian có lợi đáng kể không? | Có, nhưng **độ lớn phụ thuộc vào (i) độ mạnh descriptor, (ii) độ dài chuỗi, (iii) mức đúng của mô hình chuyển động**. Từ +0.4 điểm (RobotCar SALAD, đã bão hòa) đến +60 điểm (Nordland NetVLAD). |
| Khi nào HMM tốt / thất bại? | Tốt: chuỗi dài, descriptor yếu–trung bình, thay đổi mùa/ngoại cảnh, vận tốc ổn định hoặc được mô hình hóa. Yếu/thất bại: chuỗi rất ngắn (RobotCar ~8 frame: night NetVLAD chỉ 0.153→0.229), outage (đúng chỗ không có trong top-10 ảnh đơn), motion prior sai (time-warp làm HMM kernel cố định mất 65% lợi ích), bằng chứng phụ thuộc (β=1 ở video-rate: NetVLAD 0.972→0.683, confident-wrong 18%). |
| Nguyên nhân gốc? | Không nằm ở cấu trúc Markov mà ở **đặc tả**: (1) emission hiệu chỉnh cho ảnh đơn quá tự tin trong HMM vì quan sát phụ thuộc (β*≈0.1–0.2 ở frame-rate cao, dose-response theo stride); (2) prior vận tốc ngầm oracle; (3) thiếu thông tin (outage, chuỗi ngắn) — giới hạn thông tin, không sửa được bằng mô hình. |
| Do bản chất HMM, cách mô hình hóa, dữ liệu hay pipeline? | Phần lớn do **cách mô hình hóa** (emission tempering, motion) và **dữ liệu** (đồng bộ Nordland thổi phồng lợi ích; chuỗi RobotCar quá ngắn). Hai lỗi pipeline legacy (bảo toàn khối lượng null A01, null heuristic A08) đã sửa; ba lỗi pipeline của chính phiên này (A22, A23, A24) được phát hiện và ghi lại. |

## 2. Phương pháp: IA-HMM (HMM là trung tâm)
State z_t = (node bản đồ j, bin vận tốc k) ∪ {off-map}. Mọi module là thành phần của HMM:
- **Transition**: kernel Gauss theo arc-length bản đồ (mét hoặc frame), sticky velocity P(k'|k), exit/re-entry null, leak
  phục hồi; bảo toàn khối lượng chính xác (G0: khớp liệt kê vét cạn mọi quỹ đạo, `tests/test_hmm_core.py`).
- **Emission thị giác**: s/τ (τ hiệu chỉnh ảnh đơn trên calibration) hoặc LLR logistic (HT-weighted); null l(∅)=0.
- **Emission vận tốc (ME, mới)**: m_t = log(1 − q_t·q_{t−1}) quan sát bởi state vận tốc, p(m|v_k) Gauss fit trên
  calibration ⇒ HMM *nhìn thấy* dừng xe / tăng tốc mà không cần VO.
- **Trọng số bằng chứng theo thông tin (IA, mới)**: β_t = β₀(1−ρ_t)/(1+ρ_t), ρ_t = 1 − min(1, d_t/κ) — dẫn xuất
  từ emission AR(1) (THEORY.md T1).
- **Chọn mô hình bằng NLL calibration** trong {kernel cố định, LV, LV+ME, LV+ME+IA} ⇒ "IA-HMM (dev-selected)".
- Suy luận: forward (online), fixed-lag, Viterbi — cùng một mô hình.

## 3. Kết quả chính (R@1 trên test sequences; bảng đầy đủ + NLL: `RESULTS_TABLES.md`, hình: `figures/fig1_r1_small_multiples.png`)

| Dataset | Descriptor | Single | SeqSLAM (tuned) | HMM kernel cố định | **IA-HMM (dev-sel.)** |
|---|---|---|---|---|---|
| Nordland (đồng bộ) | NetVLAD / CosPlace / SALAD / MegaLoc | 0.364 / 0.652 / 0.811 / 0.821 | 0.889 / 0.966 / 0.970 / 0.960 | 0.970 / 0.987 / 0.986 / 0.985 | **0.970 / 0.982 / 0.991 / 0.985** |
| Nordland time-warp (s1) | 〃 | 0.430 / 0.695 / 0.808 / 0.832 | 0.580 / 0.658 / 0.671 / 0.669 | 0.563 / 0.826 / 0.869 / 0.882 | **0.827 / 0.915 / 0.901 / 0.917** |
| Extended CMU (11 slice) | 〃 | 0.701 / 0.908 / 0.943 / 0.932 | 0.770 / 0.921 / 0.954 / **0.947** | 0.820 / 0.931 / 0.955 / 0.941 | **0.820 / 0.931 / 0.955** / 0.941 |
| RobotCar Seasons v2 | 〃 | 0.708 / 0.834 / 0.987 / 0.974 | 0.777 / **0.858** / 0.989 / **0.984** | 0.772 / 0.860 / 0.992 / 0.984 | **0.779** / 0.857 / **0.991** / 0.980 |

Runs: E18 `20261127-024…042`. Nordland video-rate (k01, stride 1): IA-HMM(dev-sel.) NetVLAD 0.379→0.936, SALAD
0.815→0.953 (SeqSLAM 0.753/0.895); time-warp video-rate NetVLAD 0.418→**0.794** (fixed 0.652, SeqSLAM 0.601).

**Phân rã đóng góp dưới vận tốc thay đổi** (Nordland time-warp, NetVLAD, seed 1/seed 2): kernel cố định
0.563/0.531 → +vận tốc ẩn 0.712/0.599 → +emission vận tốc 0.805/0.747 → +IA 0.827/0.822 (oracle motion 0.896/0.809).
Mọi bước có CI cặp so với kernel cố định không chứa 0.

## 4. Phát hiện chẩn đoán (Phase 4)
1. **Phụ thuộc quan sát là nguyên nhân chính của overconfidence** (H5/H6 [S+]): β* do calibration chọn = 0.1 ở stride 1,
   0.2 ở Nordland stride 8, 0.2–0.75 trên CMU; β=1 ở video-rate: R@1 NetVLAD 0.683 vs 0.972, CW@0.9 0.18 vs 0.001
   (E15_nordseg1). IA (không nhãn) giảm NLL thêm 17% (NetVLAD) / 35% (SALAD) ở video-rate Nordland (có hầm/ga), nhưng
   **không** giúp trên CMU (không có dừng) ⇒ đúng dự đoán P3 của THEORY.md.
2. **Oracle motion thổi phồng** (H3 [S+]): lợi ích HMM kernel cố định SALAD giảm từ +0.175 (đồng bộ) xuống +0.061
   (time-warp); SeqSLAM tụt dưới ảnh đơn. Vận tốc ẩn + emission vận tốc phục hồi 61–84% lợi ích oracle (H17).
3. **Tương tác M2×M3** (H18 [S+] định tính): IA đơn lẻ trên kernel cố định *làm hại* dưới time-warp (0.783 vs 0.871);
   chỉ có lợi khi state vận tốc biểu diễn được trạng thái dừng.
4. **Taxonomy lỗi** (T4.1): CMU NetVLAD — HMM sửa 2229 lỗi của ảnh đơn, gây 536 lỗi mới; lỗi còn lại: outage 43%,
   near-miss (lệch tolerance) 36%, lock-in 16%, cold-start 4%. CMU SALAD: 83% near-miss (lỗi biên tolerance).
   RobotCar NetVLAD: 58% cold-start (chuỗi ngắn). Nordland NetVLAD: 48% outage.
5. **Off-map** (H19 phần): lọc thời gian nâng AUROC off-map từ 0.880 (SUE) lên 0.979–0.988 (SALAD), 0.58→0.90–0.92
   (NetVLAD); null LLR hiệu chỉnh (M1) **không** vượt null quantile đã tune (H7 [S−]).
6. **Fixed-lag** (H21 partial): lag 10 frame: +4.3 điểm CMU, +1.6 Nordland, n.s. RobotCar.
7. **Chuyển giao giữa dataset** (H13 [S+]): siêu tham số chọn trên CMU áp lên RobotCar giữ 84–110% lợi ích; RobotCar→CMU
   giữ 60% (NetVLAD) / 110% (CosPlace); calibration (ECE) xấu đi khi chuyển τ.
8. **Runtime** (H14): filter 0.05–2 ms/frame cho M≤10k; M=30k: 0.8 ms (K=1), 22.5 ms (K=6, CPU 4 lõi dùng chung) ⇒
   cần sparse candidate cho LV ở bản đồ lớn.

## 5. Kết luận khoa học (mức [S])
- HMM **là** một ý tưởng tốt cho sequence-based VL khi được đặc tả đúng: nó luôn ≥ ảnh đơn và ≥ hoặc ngang SeqSLAM đã
  tune, cho xác suất có hiệu chỉnh (NLL thấp hơn 3–170 lần so với điểm SeqSLAM được softmax hóa — vốn không phải xác suất) và off-map detection tốt.
- Đóng góp có khả năng mới (cần kiểm novelty sâu hơn, NOVELTY.md): **emission vận tốc từ thay đổi descriptor toàn cục**
  kết hợp **trọng số bằng chứng AR(1)** trong cùng một HMM, cho phép HMM chịu được dừng/thay đổi tốc độ không cần VO.
- Không claim: SOTA, 6DoF mịn, bảo đảm lý thuyết ngoài giả định Gaussian AR(1).

## 6. Hạn chế & việc tiếp theo
1. Chưa có baseline learned sequence (JIST/SeqVLAD/CaseVPR) — cần trọng số; chưa có held-out dataset (MSLS/SFU/4Seasons cross-traversal).
2. Time-warp là biến thể tổng hợp trên dữ liệu thật; cần chuỗi stop-and-go thật (4Seasons/Oxford full).
3. LV không thắng trên dữ liệu tốc độ ổn định (CMU) — cần học bin/độ rộng tốt hơn hoặc HSMM.
4. M5 (PnP với ứng viên từ posterior) để chuyển lợi ích place-level sang pose mịn; posterior-weighted pose chỉ +1–2 điểm ở 0.5 m.
5. Đa seed cho mọi ô time-warp; Holm correction cho họ H1/H17/H20/H22; held-out test chính thức (visuallocalization.net) cần người dùng duyệt.
