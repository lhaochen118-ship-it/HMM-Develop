# CPC-HMM: lý thuyết, lập luận và công thức

*Module của hướng certified sequential localization. Code: `analysis/hmm_fix.py` (`fac_anchT_mix`, `cpc_p*`, `cpc_pred`),
`analysis/nav_demo.py` (luật "CPC-HMM (ours)").*

## 0. Bài toán và ký hiệu

- Bản đồ: N ảnh với vị trí m_j. Query tại frame t có similarity s_t ∈ R^N và odometry u_t.
- Trạng thái ẩn gồm hai phần:
  - x_t ∈ {1..N}: nơi trên bản đồ;
  - z_t ∈ {on, off}: robot có đang ở trong vùng có bản đồ không.
- Giả thuyết: H0 (frame off-map, z_t = off) và H1 (frame on-map).
- F_{t−1}: toàn bộ dữ liệu đến frame t−1.
- **e-value có điều kiện:** e_t ≥ 0 với E_{H0}[e_t | F_{t−1}] ≤ 1.

## 1. Vì sao HMM yếu

**Mệnh đề 1 (bất biến dịch chuyển).**

- *Phát biểu.* Xét emission exp(s_tj/T) và trạng thái off-map với emission exp(s₍ₖ₎,t/T) (Xu'21). Posterior lọc tiến
  P(x_t, z_t | F_t) không đổi khi s_t → s_t + c_t·1, với mọi dãy c_t.
- *Chứng minh.* Mọi emission của frame t cùng nhân với hằng số exp(c_t/T). Hằng số này triệt tiêu khi chuẩn hoá.
- *Hệ quả.*
  - Quyết định on/off chỉ phụ thuộc vào hình dạng của s_t − max s_t.
  - Tỷ số on/off Λ_t = Σ_j b_t(j)·exp((s_tj − s₍ₖ₎)/T) có E_{H0}[Λ_t] phụ thuộc vào T, k và điều kiện ảnh.
  - Không có (T, k) nào làm Λ_t thành e-value ở mọi điều kiện. Tune bằng nhãn trên điều kiện dễ không chuyển được sang
    điều kiện khó: trên CMU, FL = 0.97.

**Mệnh đề 2 (đếm thừa bằng chứng phụ thuộc).**

- *Phát biểu.* Giả sử bằng chứng là quá trình AR(1) Gauss với hệ số r. Log-LR đúng của n frame tăng theo
  n·(1−r)/(1+r)·μ²/σ², còn HMM, vì nhân emission như độc lập, tính n·μ²/σ².
- *Hệ quả.* Log-odds của HMM bị phóng đại (1+r)/(1−r) lần. Với r đo được là 0.8–0.99, hệ số này là 9–200×. Kết quả là
  posterior quá tự tin và khoá nhầm chỗ.

**Mệnh đề 3 (bội số).**

- p-value của thống kê max đã trả giá cho N nơi.
- Phân rã nhất quán là P(z_t = on, x_t = j | s_t) = P(on | p_t) · P(j | s_t, on).
- Đưa e-value vào từng trạng thái nơi chốn thì trả 1/N hai lần.

**Hệ quả 4 (khoá nhầm do bằng chứng phụ thuộc niềm tin).** Nếu bằng chứng hiện diện được tính tại nơi MAP x̂_t, thì
x̂_t là lựa chọn phụ thuộc dữ liệu. Khi đó E_{H0}[e(x̂_t)] > 1, nên chuỗi hiện diện tự xác nhận khi đã khoá nhầm.

## 2. Mô hình CPC-HMM

**Chuỗi vị trí ("ở đâu"):** HMM không có trạng thái off-map, chuyển trạng thái theo odometry.

> b_t(j) ∝ e_t(j) · Σ_i b_{t−1}(i) · K(m_j − m_i − u_t),  log e_t(j) = (s_tj − max_i s_ti) / (τ · σ_far,t)

- τ là thang Gumbel của null bản đồ.
- σ_far,t là độ trải các cực đại vùng xa của frame t.
- Không có tham số nào phải tune bằng nhãn.

**Bằng chứng hiện diện:** chỉ tính từ top-1 và odometry, không từ niềm tin của HMM.

- e-value của frame, với p_t là p-value SelfCal-AA của top-1 (hiệu chuẩn bằng bản đồ):

  > e^top_t = a_t · p_t^(a_t − 1)

- e-value của chuỗi neo odometry. R_t là thống kê ANCH trong cửa sổ H, và p^R_t là p-value của nó so với null R trên
  traversal của bản đồ:

  > e^R_t = a′_t · (p^R_t)^(a′_t − 1)

- Cổng khớp:

  > ẽ^top_t = e^top_t · 1[‖m_top − m_x̂‖ ≤ ρ] + a_t · 1[ngược lại]

- Gộp:

  > LR_t = ½ · ( ẽ^top_t + (e^R_t)^(1/H) )

**Chuỗi hiện diện**, với p_in = p_out = p:

> P(on_t) ∝ [ (1−p)·P(on_{t−1}) + p·P(off_{t−1}) ] · LR_t

Báo nơi x̂_t khi P(on_t) > ½.

## 3. Bảo đảm

**Giả định D (map-null dominance).** Với frame off-map t và điều kiện trên F_{t−1}, thống kê SelfCal-AA của query bị trội
ngẫu nhiên bởi thống kê của pseudo-query leave-block-out của bản đồ. Khi đó P(p_t ≤ u | F_{t−1}) ≤ u, tức p_t
super-uniform có điều kiện.

- Giả định D là cùng giả định đã làm cho FAR theo đoạn hợp lệ trong cert_seq. Nó đã được kiểm trên 192 điều kiện và trên
  off-map tự nhiên.
- Giả định tương tự cho p^R_t (D_R).

**Bổ đề 1 (e-value có thể dự đoán).** Nếu a_t ∈ (0, 1] chỉ phụ thuộc F_{t−1} và p_t super-uniform có điều kiện, thì
E[e^top_t | F_{t−1}] ≤ 1.

- *Chứng minh.* Hàm g(p) = a·p^(a−1) giảm theo p. Với p super-uniform, E[g(p)] ≤ ∫₀¹ a·p^(a−1) dp = 1.
- Ước lượng a bằng EM trên toàn bộ traversal dùng cả dữ liệu tương lai. Bản `cpc_pred` dùng a_t fit lại mỗi 25 frame
  trên các frame quá khứ, nên đúng điều kiện của bổ đề.

**Bổ đề 2 (cổng, luỹ thừa, trung bình).**

- *Cổng.* Vì p ≤ 1 và a ≤ 1, ta có a·p^(a−1) ≥ a. Do đó ẽ^top_t ≤ e^top_t từng điểm, vẫn là e-value.
- *Luỹ thừa.* Với w ∈ (0, 1], Jensen cho E[e^w] ≤ (E[e])^w ≤ 1.
- *Trung bình.* ½(e₁ + e₂) là e-value với mọi kiểu phụ thuộc giữa e₁ và e₂.
- Vì vậy LR_t là e-value có điều kiện dưới D và D_R.

**Bổ đề 3 (null bảo thủ theo odometry, cho D_R).**

- *Phát biểu.* Kiểm khớp của ANCH tại trễ j là 1[‖Δx − Δo‖ ≤ ρ_o]. Giả sử odometry thật là Δo = Δg + ε, với ε độc lập,
  đối xứng và đơn đỉnh (log-concave). Khi đó, với mọi phân phối đối xứng đơn đỉnh của a = Δx − Δg:

  > P(‖a − ε‖ ≤ ρ_o) ≤ P(‖a‖ ≤ ρ_o)

- *Chứng minh.* Hệ quả của bất đẳng thức Anderson: hình cầu là tập lồi đối xứng, và tích chập với một phân phối đối xứng
  đơn đỉnh không làm tăng xác suất của tập đó.
- *Hệ quả.* Null R tính trên traversal của bản đồ với odometry không nhiễu (Δo = Δg) trội ngẫu nhiên hơn R của query
  off-map với mọi odometry thật. Vì vậy p^R super-uniform, tức D_R đúng một cách bảo thủ.
- *Thực nghiệm.* Null dùng odometry mô phỏng có nhiễu (3 % scale, 5 % step) cho p^R sub-uniform khi odometry thật chính
  xác hơn mô phỏng:
  - 4S countryside: P(p^R ≤ 0.01 | off) = 0.059;
  - Boreas MegaLoc: P(p^R ≤ 0.05 | off) = 0.075.

  Trong khi đó p^top vẫn super-uniform ở mọi dataset. Đây là nguyên nhân CPC-HMM báo on sai 7–8.5 % trên Boreas.

**Định lý 1 (ARL₀ của chuỗi hiện diện).**

- *Phát biểu.* Giả sử LR_t là e-value có điều kiện dưới H0 và p_in ≤ p_out. Gọi τ₀ là thời điểm báo on sai đầu tiên
  trong một đoạn off-map. Khi đó:

  > E[τ₀] ≥ (1 − p_in)/p_in − R₀,  với R₀ = O₀·(1 − p_in)/p_in

  Ở đây O₀ là odds của on lúc bắt đầu đoạn. Với p = 0.01 và chuỗi ở biên dưới, R₀ ≈ 1, nên ARL₀ ≥ 98 frame.
- *Chứng minh.*
  1. Bước dự đoán cho O′ = (p_in + (1−p_out)·O)/((1−p_in) + p_out·O) ≤ c + O, với c = p_in/(1−p_in), vì p_out ≥ p_in.
  2. Do đó R_t := O_t/c ≤ (R_{t−1} + 1)·LR_t.
  3. Vế phải là thống kê Shiryaev–Roberts S_t = (S_{t−1} + 1)·LR_t. Bằng quy nạp, R_t ≤ S_t.
  4. Nếu LR_t là e-value có điều kiện thì S_t − t là siêu martingale. Áp dụng optional stopping tại
     σ = inf{t : S_t ≥ 1/c} cho E[σ] ≥ E[S_σ] − S₀ ≥ 1/c − S₀.
  5. "Báo on" là O_t > 1, tương đương R_t > 1/c, kéo theo S_t > 1/c. Vậy τ₀ ≥ σ. ∎
- *Lưu ý.* Bước 3–4 chính là e-detector Shiryaev–Roberts của Shin–Ramdas–Rinaldo. Phần của ta là bước 1–2 (chuỗi on/off
  của HMM bị chặn trên bởi một e-detector) và việc cung cấp e-value không nhãn.

**Định lý 2 (bộ nhớ bị chặn và độ trễ vào lại).**

- Sau bước dự đoán, log-odds nằm trong [−b, b] với b = log((1−p)/p) ≈ 4.6. Vì vậy bằng chứng đếm thừa (Mệnh đề 2) không
  thể đẩy niềm tin on lên quá b + ℓ_t.
- Khi robot vào lại bản đồ, chuỗi xuất phát từ khoảng −b. Theo Wald, độ trễ trung bình đến khi P(on) > ½ là:

  > E_{H1}[δ] ≈ b / KL₁,  với KL₁ := E_{H1}[log LR_t] > 0

- Tương tự, sau khi rời bản đồ, độ trễ đến khi ngừng báo là khoảng b / |KL₀|, với KL₀ := E_{H0}[log LR_t] < 0 theo Jensen.

**Hệ quả 3 (chọn p).** Muốn ARL₀ ≥ L thì đặt p = 1/(1+L). Khi đó độ trễ ≈ log L / KL₁. Đây là đánh đổi bậc tối ưu
log ARL₀ / KL của Lorden cho bài toán phát hiện thay đổi.

**Nhận xét (phụ thuộc giữa các frame).**

- Bổ đề 1 cần tính hợp lệ có điều kiện. Nếu chỉ có tính hợp lệ biên thì vẫn có E_{H0}[Σ log LR_t] ≤ 0 với mọi kiểu
  phụ thuộc (tuyến tính của kỳ vọng và Jensen), tức độ trôi không dương. Nhưng cận ARL₀ có thể sai khi các frame off-map
  liên tiếp gần như trùng nhau.
- Hai biện pháp:
  - luỹ thừa e^R theo 1/H, vì mỗi frame nằm trong H cửa sổ;
  - a_t có thể dự đoán (`cpc_pred`).
- ARL₀ được kiểm bằng thực nghiệm trên mọi dataset (§5).

## 3b. Mở rộng: cổng dự đoán (PG) và trạng thái off-map dead-reckoning (DR)

*Code: `analysis/nav_demo.py`, hàm `cpc_joint`; luật `CPC-HMM +PG`, `+DR`, `+PG+DR`.*

**Chẩn đoán dẫn tới mở rộng** (Boreas, `navframes_*.npz`, 2026-10-29):

- FL của CPC-HMM trên Boreas **không** chủ yếu là độ trễ khi rời bản đồ. 47–72 % frame FL (MegaLoc, SALAD) nằm > 100
  frame sau frame on-map cuối, trong đoạn off-map dài > 100 frame. Một rò rỉ p_out = 0.6 đặt đúng tại mép bản đồ (oracle) không đổi FL.
- Fix sai của CPC-HMM ở rất xa: trung vị 111–182 m, p90 tới 954 m. Fix sai của Xu'21 chỉ cách 37–56 m (vùng xám ở mép).
  Sai số điều hướng do vài chuỗi fix sai liên tiếp, nhất quán với odometry, ở một đoạn đường aliasing cách xa.
- Cơ chế: trong lỗ bản đồ, chuỗi vị trí (không có trạng thái off-map) buộc phải đặt khối lượng lên bản đồ, nên trôi tới
  đoạn aliasing Y. Cổng "top-1 khớp MAP hậu nghiệm" khi đó luôn đúng (MAP đã chạy theo top-1), và bằng chứng yếu nhưng
  phụ thuộc (p ≈ 0.15 nhiều frame liền) tích luỹ thành báo on.
- Trạng thái off-map của Xu'21 **không có vị trí**: vào lại bản đồ phân bố đều, nên cũng không ngăn được nhảy xa.

**Mô hình.** Chạy chung hai chuỗi; b_t = P(x_t | on_t).

1. *Trạng thái off-map dead-reckoning (DR).* Ghost G_t = N(μ_t, s_t²): μ là vị trí fix báo cuối cùng, cộng dồn odometry
   khi đang off; s_t = s₀ + κ·(quãng đường từ fix cuối), với s₀ = excl và κ = 0.05 (cùng mô hình nhiễu của bộ lọc điều
   hướng). Không có tham số tune bằng nhãn. Dự đoán chuỗi vị trí, có điều kiện on:

   > b_t^pred ∝ P(on_{t−1})(1−p_out) · K∗b_{t−1} + P(off_{t−1}) · p_in · G_t

   (DR tắt: G_t đều trên bản đồ, như Xu'21.)
2. *Cổng dự đoán (PG).* g_t = Σ_{j: ‖m_j − m_top,t‖ ≤ excl} b_t^pred(j), tức xác suất dự đoán (trước khi thấy ảnh t, ngoài
   vị trí top-1) rằng robot ở nơi top-1. Bằng chứng frame:

   > ẽ^top_t = a_t + g_t · (e^top_t − a_t)

**Bổ đề 4 (PG giữ tính e-value).** Vì e^top ≥ a (p ≤ 1, a ≤ 1) và g_t ∈ [0, 1], ta có a ≤ ẽ^top_t ≤ e^top_t từng
điểm. Do đó E_{H0}[ẽ^top_t | F_{t−1}] ≤ E_{H0}[e^top_t | F_{t−1}] ≤ 1 dưới D, với **mọi** g_t, kể cả g_t phụ thuộc vào
frame t qua m_top. Bổ đề 2 (luỹ thừa, trung bình) áp dụng nguyên vẹn.

**Hệ quả 5.** Định lý 1 (ARL₀ ≥ (1−p_in)/p_in − R₀) giữ nguyên cho +PG, +DR, +PG+DR: DR chỉ đổi phân phối của chuỗi
vị trí, không đổi LR_t ngoài qua g_t, và chuỗi hiện diện giữ p_out ≥ p_in.

**Vì sao giảm fix sai xa.** Khi robot ở sâu trong lỗ, P(off) cao nên b^pred bị chi phối bởi G_t (gần vị trí
dead-reckoning thật). Nơi aliasing Y cách xa ghost có g_t ≈ 0, nên ẽ^top = a < 1: bằng chứng âm, chuỗi hiện diện ở off.
Khi robot ra khỏi lỗ đúng chỗ ghost dự đoán, g_t ≈ 1 ngay, nên độ trễ vào lại không tăng. Nếu ghost sai (khoá nhầm
trước khi rời bản đồ), s_t tăng tuyến tính theo quãng đường, nên G_t loang dần và tái định vị toàn cục vẫn khả thi.

**Liên hệ tài liệu.** "Gate" theo mật độ dự đoán và "coasting" (dự đoán track khi không có đo) là khái niệm chuẩn của
IPDA/tracking. Điểm mới ở đây: (i) gate tác động lên một e-value hiệu chuẩn bằng bản đồ và chứng minh được là vẫn giữ
tính e-value, nên giữ bảo đảm ARL₀; (ii) trạng thái off-map của HMM-VPR mang vị trí dead-reckoning thay vì không có vị
trí (Xu'21, Hansen–Browning'14).

## 4. Định vị so với công trình gần nhất

| | Bằng chứng on/off | Cần mô hình hoặc nhãn | Bảo đảm |
|---|---|---|---|
| Xu'21 (HMM + off-map) | exp(s₍ₖ₎/T), tương đối, bất biến dịch chuyển | T, k tune bằng nhãn | không; E₀ phụ thuộc điều kiện |
| IPDA / Bernoulli filter | LR = 1 − P_D·P_G + P_D·P_G·Σℓ_i/λ | P_D, mật độ clutter λ, likelihood đo | đúng nếu mô hình đúng |
| E-detectors (Shin et al.) | e-process do người dùng cung cấp | mẫu trước thay đổi hoặc lớp phân phối | ARL₀ ≥ ngưỡng, một lần thay đổi |
| **CPC-HMM** | e-value từ p-value hiệu chuẩn bằng bản đồ + odometry neo | không nhãn, không mô hình clutter | ARL₀ ≥ (1−p)/p − R₀ trên mỗi đoạn off-map, dưới D |

**Khác biệt cốt lõi:**

1. Chuỗi tồn tại kiểu IPDA, nhưng likelihood dựa mô hình được thay bằng e-value hiệu chuẩn bằng chính bản đồ. Vì vậy
   không cần P_D hay mật độ clutter.
2. E-detector được áp dụng cho chuỗi on/off lặp lại của HMM, nhờ biên ±b. Chuỗi tự "khởi động lại" sau mỗi đoạn
   on-map, thay vì phát hiện một thay đổi duy nhất.
3. Cổng khớp MAP nối chuỗi hiện diện với chuỗi vị trí mà vẫn giữ tính e-value (Bổ đề 2). Điều này phá vòng khoá nhầm
   (Hệ quả 4).

## 5. Kiểm chứng (đang chạy)

- **ARL₀ và độ trễ vào lại** trên 7 dataset (`hmm_fix.py`, metric `ARL0`, `reentry_delay`).
- **Quét p ∈ {0.001, 0.003, 0.01, 0.03, 0.1}** (`cpc_p*`): kiểm ARL₀ ≥ (1−p)/p − 1 và độ trễ ≈ log((1−p)/p)/KL₁, với KL₁
  đo được (`KL_on`).
- **a_t có thể dự đoán** (`cpc_pred`) so với a fit trên toàn traversal (`fac_anchT_mix`).
- **Boreas** (benchmark dài, odometry bánh xe thật): chẩn đoán từng frame (`nav_demo --dump`).
