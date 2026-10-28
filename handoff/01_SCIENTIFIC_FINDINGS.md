# 01 — Scientific Findings: SelfCal (self-calibrating maps for VPR)

*Cập nhật 2026-10-28. Tài liệu này chỉ nói về **khoa học**: đóng góp, ý nghĩa, kết quả tích cực/tiêu cực, bằng chứng
và điều kiện kiểm chứng. Vận hành/kỹ thuật xem `02_ENGINEERING_OPS_NOTES.pdf`; trạng thái và việc tiếp theo xem
`03_HANDOFF_NEW_CHAT.pdf`. Mọi con số ở α = 0.05 nếu không ghi khác. Kết quả gốc: `analysis/results/*.json` (bảng:
`python3 paper/build_tables.py` → `paper/tables.md`).*

## 1. Vấn đề và khoảng trống nghiên cứu

- VPR luôn trả về một top-1. Robot (loop closure, relocalisation) phải quyết định **có tin match đó không**.
- Hai kiểu lỗi chính:
    - query ở chỗ **không có trong bản đồ** (off-map);
    - match nhầm sang một nơi **trông giống** (aliasing).
- Mọi luật chấp nhận hiện có đều cần dữ liệu có nhãn để hiệu chuẩn: threshold, PA ratio, SUE, integrity MLP, conformal
  (SAFEVPR), Quantile Transfer. Khi điều kiện ánh sáng, thời tiết, mùa lúc deploy khác lúc hiệu chuẩn, bảo đảm FAR
  (false-accept rate) bị phá vỡ. Đây là khoảng trống mà SelfCal lấp.

## 2. Đóng góp (claim chính, có bằng chứng)

**C1. Bản đồ là tập hiệu chuẩn miễn phí (map pseudo-queries).**

- Bỏ lần lượt từng block 300 m của bản đồ (leave-one-block-out). Mỗi ảnh bản đồ trong block đó trở thành một query
  **off-map theo cấu trúc**, cho ra hàng nghìn mẫu null có nhãn mà không cần người gán nhãn.
- p-value conformal tính trên tập null này.

**C2. Thống kê bất biến affine theo từng query, so với các vùng xa của bản đồ.**

- Gom ảnh bản đồ thành các ô 10 m, lấy similarity lớn nhất trong mỗi ô. Bỏ các ô cách top-1 dưới 25 m. Với các ô
  còn lại, tính μ_far và σ_far.
- z_far = (s₁ − μ_far)/σ_far và z_gap = (s₁ − max ô xa)/σ_far.
- Descriptor được trừ trung bình của bản đồ (map centring) để giảm hubness.
- Thay đổi ngoại hình chủ yếu làm méo điểm similarity theo dạng affine, và chỉ làm query không liên quan **kém giống**
  bản đồ hơn. Vì vậy hiệu chuẩn trên chính bản đồ sẽ lệch về phía an toàn (dominance).

**C3. Luật quyết định SelfCal-AA**, gồm:

- min-p tự hiệu chuẩn của (max-sim, z_far);
- aliasing guard z_gap: chấp nhận khi max(p_comb, p_zgap) ≤ α;
- **Mondrian strata** theo σ_far (B = 10 bin, tự giảm để mỗi bin có ≥ 50 mẫu null);
- **domain gate**: p_maxsim thô ≤ 0.8.

**C3'. SelfCal-Gap**, chế độ power cao.

- Chỉ dùng p_zgap, vẫn cùng strata và gate.
- Thêm vào sau khi phân tích MSLS (xem §4.2; chọn sau khi đã xem dữ liệu).

**C4. Lý thuyết** (`paper/selfcal_paper.md` §5):

| Định lý | Nội dung |
|---|---|
| T1 | Hợp lệ dưới exchangeability; với Mondrian thì hợp lệ có điều kiện theo từng stratum |
| T2 | Nếu thống kê off-map bị null của bản đồ dominate thì FAR ≤ α |
| T3 | FAR − α ≤ Δ⁺ (khoảng cách Kolmogorov một phía) |
| T4 | Kết hợp min-p tái hiệu chuẩn vẫn hợp lệ |
| T5 | BH kiểm soát FDR (PRDS) |
| T6 | Domain gate theo intersection–union: FAR ≤ min(α + Δ⁺, ε_c), tức hợp lệ nếu appearance shift **hoặc** domain shift được giải thích. Cùng lập luận: AA hợp lệ nếu **một trong hai** nhánh (comb hoặc z_gap) bị dominate; Gap cần chính z_gap bị dominate. |

**C5. Đánh giá rộng.**

- 4 benchmark: RobotCar-Seasons v2 (bản đồ chính thức), Extended-CMU (11 slice gộp), Nordland, MSLS-val (CPH+SF).
- 6 descriptor: NetVLAD, CosPlace, MixVPR, DINOv2, SALAD, MegaLoc.
- Tổng cộng 24 setting, 192 điều kiện deploy, thêm 120 cặp domain lạ.

## 3. Kết quả tích cực (bằng chứng)

**3.1 Bảng chính** (`paper/tables.md` Table 2a; Gap ở `analysis/results/gap/`):

| method | nhãn | điều kiện vi phạm (binomial, Bonferroni) | TPR TB | aliasing chấp nhận (median) | FAR tệ nhất |
|---|---|---|---|---|---|
| **SelfCal-AA** | không | **0/192** | 0.646 | 0.011 | **0.048** |
| **SelfCal-Gap** | không | **0/192** | **0.746** | 0.021 | 0.073 |
| SUE (Zaffar'24) | benign | 16/192 | 0.661 | 0.070 | 0.163 |
| CRSG (learned calibrator) | benign | 32/192 | 0.757 | 0.169 | 0.356 |
| Threshold benign → all | benign | 36/192 | 0.652 | 0.218 | 0.281 |
| Conformal LOCO (SAFEVPR protocol) | điều kiện khác | 51/192 (24/24 setting) | 0.699 | 0.217 | 0.419 |
| Quantile Transfer | benign | 79/192 | 0.769 | 0.405 | 0.483 |
| Gaussian z-norm / EVT spacing | không | 164 / 18 | — | — | 1.000 / 0.109 |
| Oracle (nhãn mọi điều kiện) | tất cả | 0/192 | 0.706 | — | 0.050 |

- **Riêng RobotCar, CMU, Nordland:** AA đạt 0.708 so với oracle 0.721; Gap đạt 0.793, cao hơn oracle.
- **Ablation:**
    - bỏ strata: 0.612 (FAR tệ nhất 0.140);
    - bỏ gate: power gần như không đổi, nhưng rò rỉ domain quay lại;
    - bỏ aliasing guard: 5 vi phạm và aliasing tăng lên 0.072;
    - bỏ centring trên Nordland: TPR 0.742 → 0.568 (SALAD).

**3.2 Domain lạ (natural off-map, exp9).**

- Query từ dataset hoặc thành phố khác, chiếu lên mỗi bản đồ: 0/120 ô vượt α, FAR lớn nhất 0.007.
- Không có gate thì luật cũ rò tới 0.143 (CosPlace, bản đồ CMU).
- Với Gap, FAR lớn nhất là 0.011 (exp10).

**3.3 Vì sao hoạt động (exp6).**

- Survival function của mọi điều kiện RobotCar đều nằm dưới null của bản đồ.
- Δ⁺ với null bản đồ ≤ 0.052, so với 0.255 nếu dùng null benign có nhãn (Table 3).

**3.4 Batch / FDR (exp3).**

- BH ở q = 0.1 giữ gross FDR ≤ 0.04 trên RobotCar, CMU và Nordland.
- Power 0.97–0.99 (RobotCar), 0.87–0.89 (CMU), 0.68–0.74 (Nordland).

**3.5 Bền vững.**

- Nordland lấy mùa đông làm bản đồ: 0/3 vi phạm.
- Bản đồ RobotCar chỉ 25% / 50%: 0/9 vi phạm.
- Hyper-parameter ×0.5–2: TPR đổi ≤ 0.06, FAR tệ nhất ≤ 0.073.

**3.6 Downstream** (branch `claude/selfcal-seq`, exp12, Table 8).

- Thiết lập: bản đồ mất 30% block, Kalman filter với odometry trôi, 10 seed, 12 cặp descriptor × dataset.
- SelfCal-AA từng frame thắng threshold có nhãn ở **cả 12 cặp**:
    - lỗi định vị thấp hơn 1.3–12.6×;
    - fix sai ít hơn 1.5–27×;
    - CMU đạt 3.6–9.3 m, so với oracle 2.8–3.2 m.

## 4. Kết quả tiêu cực và hạn chế (cũng là phát hiện)

1. **Power trên MSLS thấp với AA:** 0.460 so với oracle 0.661. Nguyên nhân đã xác định: dominance của **z_far**
   **thất bại** trên MSLS (z_far một mình cho FAR tệ nhất 0.40–0.88). Gap nâng lên 0.603.
2. **SelfCal-Gap có biên an toàn mỏng hơn:** FAR điểm tệ nhất 0.073, có 5/30 ô vượt 0.05 (không có ý nghĩa thống
   kê). Biến thể này được chọn **sau khi xem dữ liệu**, cần kiểm định độc lập (dataset mới).
3. **DINOv2 CLS+mean bảo thủ:** TPR 0.04–0.38 so với oracle 0.32–0.70. Descriptor này mã hoá điều kiện quá mạnh.
   Dual centring chỉ giúp 0.33 → 0.41 nên không áp dụng.
4. **Aliasing guard chỉ có bằng chứng thực nghiệm**, không có định lý. Bảo đảm chỉ áp dụng cho off-map.
5. **Độ phân giải p-value:** mỗi stratum cần ≥ 1/α mẫu null. CMU có 75 mẫu/stratum nên không dùng được α = 0.01.
6. **Confidence không nhãn (two-groups)** kém trên CMU/Nordland (ECE khoảng 0.09 / 0.13). Nên dùng p-value.
7. **Bản đồ 50% RobotCar:** TPR tụt còn 0.843 (25% đạt 0.964). Chưa giải thích được.
8. **SelfCal theo chuỗi (Seq, branch seq, exp11): KHÔNG giữ được validity.**
    - Thiết kế: cửa sổ L frame hiệu chuẩn bằng chuỗi giả từ bản đồ, cross-fit, thống kê run-evidence.
    - Power tăng mạnh, ví dụ Nordland DINOv2 0.26 → 0.62.
    - Nhưng MegaLoc trên Nordland vi phạm 2–3/3 mùa khi L ≥ 3. Lý do: phụ thuộc thời gian của các lần truy vấn
     off-map thay đổi theo điều kiện (tuyết làm khớp sai nhất quán), nên exchangeability của cửa sổ là giả định
     mạnh hơn của frame.
    - Trong demo định vị, Seq còn **kém** bản từng frame.
    - Trung bình e-value thì hợp lệ với mọi phụ thuộc, nhưng quá yếu.
9. **Lịch sử (đã loại):**
    - CCBF (temperature theo điều kiện): trơ, τ chỉ chênh khoảng 1.2–1.5×.
    - Lọc tuần tự (sequence filter): chỉ tốt trên Nordland, sụp trên CMU (off-map AUROC 0.23).
    - CRSG: bị các paper đã có đi trước (PA ratio, RS/SD/SU, integrity MLP, SAFEVPR). Xem `LITERATURE_GATE.md` Gate 1.

## 5. Điều kiện kiểm chứng (để đọc số liệu đúng)

- **Off-map:**
    - Leave-one-300 m-block-out; query cách phần bản đồ còn lại > 40 m (Nordland: 200 / 10 frame).
    - Số mẫu off-map: RobotCar 1,386, CMU 14,117, Nordland 12,180, MSLS 8,491.
- **Đúng (correct):**
    - RobotCar và CMU: 5 m, 10°. Nordland: 2 frame. MSLS: 25 m.
    - In-map ≤ 5 m (MSLS 10 m). Aliasing: top-1 > 25 m (Nordland 5 frame).
- **Vi phạm:** binomial một phía, Bonferroni theo số điều kiện, mỗi điều kiện cần ≥ 20 mẫu off-map.
- **Baseline có nhãn:** hiệu chuẩn trên 2 điều kiện benign nhất (recall cao nhất). Oracle = threshold max-sim hiệu
  chuẩn bằng nhãn của từng điều kiện.
- **RobotCar:** ground truth chỉ có cho train split công khai (test bị giữ kín). Dùng ngưỡng chính thức trên 1,906
  query train.
- **Đã kiểm chứng tái lập:**
    - Backend GPU và numpy cho cùng kết quả.
    - AA mặc định trùng từng bit sau khi thêm mode Gap (95,770 query).
    - 1,275 dòng AA của lần chạy v3 khớp tuyệt đối với kết quả trên branch AA.
