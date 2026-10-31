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

**Kết quả của PG và DR (navH/navHc): trung tính.** Boreas CosPlace 27.6 → 24.3 m; 4S countryside 52.2 → 51.9 m. Lý do:
trong lỗ bản đồ, P(on) dao động ở vài phần trăm, vẫn ≫ p_in. Vì vậy b^pred vẫn do K∗b_{t−1} chi phối: chuỗi vị trí giữ
bộ nhớ và tự trôi tới Y; khối lượng vào lại không bao giờ có tác dụng.

**3. Cổng dead-reckoning (GG), phiên bản giữ lại.** Khi chưa báo nơi nào (P(on_{t−1}) ≤ ½) và đã có fix trước đó:

> g_t = 1[‖m_top − m_x̂‖ ≤ excl] · [ (1−ρ)·exp(−d_t²/2s_t²) + ρ ],  d_t = ‖m_top,t − μ_t‖

- μ_t là vị trí fix báo cuối cùng, cộng dồn odometry; s_t = excl + κ·(quãng đường từ fix đó), κ = 0.05.
- Chuỗi vị trí giữ nguyên như CPC-HMM; chỉ cổng thay đổi.
- Bổ đề 4 áp dụng (g_t ∈ [0, 1]), nên ARL₀ giữ nguyên.
- **Sàn ρ** là xác suất tiên nghiệm rằng chính ghost sai. Nếu không có sàn (hoặc ρ = 0.01), một lần báo sai sẽ neo ghost
  sai và chặn mọi fix đúng về sau. Trên Nordland CosPlace, recall giảm 0.74 → 0.31. Với ρ = 0.1 thì recall giữ 0.73,
  và mức giảm fix sai trên Boreas vẫn còn (thử offline). ρ được chọn sau khi xem Boreas và Nordland, cố định cho mọi
  dataset; ρ = 0.01 được báo cáo như ablation.
- Giới hạn cổng theo quãng đường (chỉ áp trong 10–20·excl) bị loại: mất phần lớn mức giảm trên Boreas, vì nhiều lần báo
  sai bắt đầu > 200 m sau fix đúng cuối.

**Baseline công bằng.** Cùng cổng dead-reckoning, dạng cứng (giữ fix mở đầu chuỗi nếu cách ghost ≤ 2s), áp hậu kiểm lên
fix của Xu'21, SelfCal và certified (`+DRgate`). Dạng cứng không có lối thoát nên khoá chết trên Nordland: Xu'21+DRgate
có 0 fix đúng.

**Liên hệ tài liệu.** "Gate" theo mật độ dự đoán và "coasting" (dự đoán track khi không có đo) là khái niệm chuẩn của
IPDA/tracking. Điểm mới ở đây: (i) gate tác động lên một e-value hiệu chuẩn bằng bản đồ và chứng minh được là vẫn giữ
tính e-value, nên giữ bảo đảm ARL₀; (ii) trạng thái off-map của HMM-VPR mang vị trí dead-reckoning thay vì không có vị
trí (Xu'21, Hansen–Browning'14).

## 3c. E-value hiệu chuẩn theo chuyển tiếp (TCE) và cận FAR theo đoạn cho chính HMM

*Code: `analysis/nav_demo.py`, hàm `tce`; luật `CPC-HMM +TCE`, `+TCEmin`, `+TCEmin+GG`.*

**Vấn đề.** Định lý 1 cần e-value **hợp lệ có điều kiện**: E_{H0}[e_t | F_{t−1}] ≤ 1. Với p-value phụ thuộc mạnh theo thời
gian (tự tương quan 0.8–0.99, Mệnh đề 2), điều này sai. Một đoạn aliasing có p ≈ 0.15 liên tiếp cho e ≈ 1.1 ở mọi frame,
nên E[e_t | p_{t−1} ≈ 0.15] > 1 và chuỗi hiện diện báo on sai (nguồn FL trên Boreas, mục 3b).

**Cấu trúc TCE (Mondrian theo trạng thái trước).**

- **Null replay:** traversal của chính bản đồ, ở các block giữ lại (off-map theo cấu trúc), cho dãy (p_s, p^R_s) theo thời
  gian.
- **Ô trạng thái:** Z_s = (bin(log p_{s−1}), bin(log p^R_{s−1})), là F_{s−1}-đo được. Frame đầu của mỗi đoạn có ô "start".
- **p-value có điều kiện của query:**

  > u_t = (1 + #{s : Z_s = Z_t, p_s ≤ p_t}) / (1 + n_{Z_t}),  tương tự cho p^R.

  Ô thưa (dưới 30 cặp) lùi về ô chỉ theo p, rồi về pool biên.
- **e-value:** e_t = a·u_t^(a−1), với a fit bằng EM theo traversal.

**Giả định T (chuyển tiếp exchangeable).** Với frame off-map t và mọi ô z, có điều kiện Z_t = z, p_t exchangeable với
các p_s của null có Z_s = z; và Z_t là thống kê đủ của F_{t−1} cho p_t (Markov bậc nhất trên trạng thái bằng chứng).

**Bổ đề 5.** Dưới T, P(u_t ≤ x | F_{t−1}) ≤ x với mọi x, nên e_t = a·u_t^(a−1) là e-value có điều kiện.
*Chứng minh.* Exchangeability trong ô cho siêu đều của p-value conformal Mondrian có điều kiện Z_t (Vovk, Mondrian
conformal); Markov-đủ nâng lên điều kiện F_{t−1}. Phần còn lại như Bổ đề 1. ∎

**Thực nghiệm: T có thể sai theo hướng dễ dãi.** Replay của bản đồ (cùng điều kiện ảnh) có quỹ đạo p mượt hơn query
khác điều kiện. Vì vậy một cú giảm p ở query trông "bất ngờ" so với null. Ví dụ CMU CosPlace: TCE cho segFAR 0.156,
ARL₀ 101 (CPC: 0.069, 418).

**Bổ đề 6 (min-combination, hợp lệ dưới hợp các giả định).** Nếu e¹_t là e-value có điều kiện dưới giả định D (CPC, biên)
và e²_t dưới T (TCE), thì e_t = min(e¹_t, e²_t) là e-value có điều kiện dưới **D hoặc T**.
*Chứng minh.* min(e¹, e²) ≤ eⁱ từng điểm với i = 1, 2; nếu giả định i đúng thì E[min | F] ≤ E[eⁱ | F] ≤ 1. ∎
Áp từng thành phần (e^top, a, e^R) rồi gộp như cũ (Bổ đề 2). Biến thể `+TCEmin` dùng cấu trúc này: nó chặn được tích luỹ
aliasing (TCE nhỏ) và không dễ dãi khi T sai (biên chặn trên).

**Định lý 3 (cận FAR theo đoạn cho quyết định của HMM).** Dưới giả định của Định lý 1 (LR_t là e-value có điều kiện;
p_out ≥ p_in), xét một đoạn off-map dài L bắt đầu với R₀ = O₀/c, c = p_in/(1−p_in). Khi đó:

> P(HMM báo nơi ít nhất một lần trong đoạn) ≤ c·(R₀ + L) = p_in/(1−p_in) · (R₀ + L)

*Chứng minh.* Theo bước 1–3 của Định lý 1, R_t ≤ S_t với S_t = (S_{t−1} + 1)·LR_t, S_0 = R₀. Đặt M_t = S_t + (L − t) với
t ≤ L. Ta có E[M_t | F_{t−1}] ≤ (S_{t−1} + 1) + L − t = M_{t−1}, nên M là siêu martingale không âm. Theo bất đẳng thức
Ville: P(max_{t≤L} M_t ≥ 1/c) ≤ c·M_0 = c·(R₀ + L). Vì S_t ≤ M_t và "báo nơi" ⇔ R_t > 1/c ⇒ S_t > 1/c, ta có điều phải
chứng minh. ∎

*Hệ quả.* Chọn p_in = α/(R₀ + L + α) cho FAR ≤ α trên mọi đoạn off-map dài L: chính HMM có **bảo đảm mức đoạn kiểu
certified**, cùng lúc với ARL₀ (Định lý 1). Với p_in = 0.01, L = H = 10, R₀ ≈ 1 thì cận là 0.11. Đây là cận bảo thủ;
segFAR thực nghiệm của TCEmin là 0.000–0.015 (Nordland, CMU).

**Ý nghĩa.** Ba mảnh (null replay của bản đồ, e-value hiệu chuẩn theo chuyển tiếp, min-combination) biến HMM thành một
e-detector có bảo đảm dưới phụ thuộc thời gian, ở cả mức ARL₀ và mức đoạn, không cần nhãn. Tài liệu gần nhất là
conformal e-testing (Vovk 2020) và conformal e-process cho change detection (2026); cả hai giả định quan sát độc lập.

## 3d. "Chỉ thận trọng hơn?" — đánh giá theo đường cong vận hành và quy tắc dừng nhất quán odometry (CS)

*Code: `analysis/oc_curves.py`, `analysis/oc_summary.py` (đường cong), hàm `consistency_ok` (CS), `sc_evidence` (CPC-SC).
Nhật ký: `RESEARCH_LOG.md` Entry 25.*

**Vì sao điểm mặc định không đủ.** Mỗi luật chấp nhận là "báo khi điểm số s_t vượt ngưỡng θ". Điểm mặc định chỉ là một
điểm trên đường cong (recall(θ), FL(θ), segFAR(θ), sai số(θ)). Hai luật cùng đường cong nhưng khác θ thì luật có θ cao hơn
"ít sai hơn nhưng bắt ít hơn" mà không tốt hơn. Vì các tập báo cáo {s_t > θ} lồng nhau, recall, FL và segFAR đơn điệu theo
θ, nên so sánh được ở **recall khớp** (FL, segFAR, sai số khi mọi luật cùng recall với một luật tham chiếu) và ở **báo sai
khớp** (recall khi FL = 0.005/0.01/0.02, segFAR = 0.01/0.025/0.05), cùng pAUC = recall trung bình trên FL ∈ [0, 0.05].
Đây là cách cộng đồng VPR/loop closure so các bộ phát hiện có điểm vận hành khác nhau (đường PR, recall ở 100 %
precision; Lowry et al. 2016) và là đường risk–coverage của selective prediction (Geifman & El-Yaniv 2017). Nhãn chỉ dùng
để đánh giá.

**Quy tắc dừng CS.** Gọi m_t là nơi được báo (MAP của chuỗi vị trí), o_t là odometry. Dừng báo ở frame t nếu tồn tại độ trễ k
với quãng đường odometry giữa t−k và t không quá 3·excl sao cho

> | ‖m_t − m_{t−k}‖ − ‖o_t − o_{t−k}‖ | > excl.

Chỉ dùng độ lớn, nên bất biến với trôi hướng của odometry (NCLT trôi 10–25°).

- **Bổ đề 7 (lọc đơn điệu giữ bảo đảm dạng "có báo cáo").** Nếu luật A có segFAR ≤ α (hoặc FL ≤ f) thì luật A ∧ CS cũng
  vậy, vì tập báo cáo của A ∧ CS là tập con của A trên mọi đoạn. *Chứng minh:* {báo trong đoạn | A ∧ CS} ⊆ {báo trong đoạn |
  A}. ∎ *Lưu ý:* không áp dụng cho ARL₀ tính theo số lần khởi phát — bỏ một báo cáo giữa một chuỗi báo sai có thể tách nó
  thành hai khởi phát.
- **Mệnh đề 4 (trễ khi rời bản đồ khi MAP kẹt ở mép).** Giả sử nơi báo luôn là một nơi của bản đồ; robot rời bản đồ sau
  frame τ (cách bản đồ ≤ in_d); sau đó MAP kẹt trong bán kính δ quanh m_τ (δ = khoảng cách giữa hai nơi liền kề của bản đồ,
  vài mét); sai số độ lớn của odometry trên quãng ≤ 3·excl không quá ε; và robot ra tới khoảng cách off_d trước khi đi quá
  3·excl kể từ τ. Nếu excl + in_d + ε + δ < off_d thì không có báo cáo nào ở frame cách bản đồ hơn off_d (frame off-map) cho
  tới khi MAP rời khỏi bán kính δ đó. *Chứng minh:* tại frame off-map t, dist(x_t, bản đồ) ≤ ‖x_t − x_τ‖ + in_d nên
  ‖x_t − x_τ‖ > off_d − in_d, do đó ‖o_t − o_τ‖ > off_d − in_d − ε > excl + δ ≥ excl + ‖m_t − m_τ‖; độ trễ k = t − τ nằm
  trong cửa sổ theo giả định nên CS dừng báo. Ở các frame sau, các độ trễ có quãng odometry trong (excl + δ, 3·excl] vẫn vi
  phạm chừng nào MAP còn kẹt. ∎ Biên δ, ε: Boreas/CMU/4S cần ε + δ < 10 m (40 − 25 − 5), NCLT < 7 m, Nordland < 4.5 frame.
- **Không bảo đảm** cho aliasing kết hợp song song (MAP trượt trên một đường giống, cùng tốc độ odometry): trường hợp này
  vẫn do bằng chứng hiện diện xử lý (TCEmin hoặc ngưỡng khởi phát hiệu chuẩn theo đoạn).

**CPC-SC (ngưỡng khởi phát hiệu chuẩn theo đoạn).** Chuỗi CPC-HMM giữ nguyên (xếp hạng tốt hơn TCEmin), chỉ hiệu chuẩn
ngưỡng *khởi phát* κ = phân vị conformal (1−α) của max log-odds trên các đoạn H frame của null tự-phát-lại của bản đồ,
chuỗi khởi đầu ở odds 1 (log-odds đơn điệu theo odds ban đầu). Query dùng cùng thống kê với null (p-value SelfCal nửa bản
đồ p_q, p^R, cùng calibrator của điều kiện), nên dưới exchangeability của các đoạn off-map với đoạn null: một đoạn được
đi vào khi không báo chứa khởi phát báo với xác suất ≤ α, với mọi phụ thuộc trong đoạn (như certified). Thực nghiệm (Boreas
seed 0–2): tỷ lệ đoạn có khởi phát sai 0.010–0.041 ≤ α, đúng như định lý; vi phạm segFAR còn lại đến từ báo cáo **kéo
dài** (carried), đúng phần CS xử lý.

**Định vị.** Kiểm tra nhất quán với odometry để loại loop closure sai đã có (RRR, Latif et al. IJRR 2013; ràng buộc chuỗi
vận tốc của SeqSLAM, Milford & Wyeth 2012), nên CS **không mới** tự thân. Phần đóng góp là vai trò của nó trong khung có bảo
đảm (Bổ đề 7, Mệnh đề 4) và chẩn đoán cho thấy nó nhắm đúng nguồn vi phạm còn lại.


## 3e. Bảo đảm khi các frame phụ thuộc nhau (Entry 26, branch `hmm-navigation-4`)

*Code: `analysis/dep_diag.py` (chẩn đoán), `analysis/gpc.py` (chứng chỉ không phụ thuộc giả định phụ thuộc),
`analysis/cpc_geo.py` (khởi phát cửa sổ hữu hạn, dừng hình dạng, reset), `analysis/geo_cons.py`.*

**Chẩn đoán (nhãn chỉ dùng ở đây).** (i) p-value SelfCal top-1 của frame off-map **siêu đều biên ở phần trong** của
đoạn off-map (P(p ≤ 0.05) = 0.000–0.006 khi cách cả hai mép ≥ 50 frame), nhưng **dưới đều trong ~50 frame quanh mép bản
đồ** (CMU MegaLoc 0.12–0.16): vùng nhìn chồng lấn, top-1 là ảnh ở mép cách 40–100 m. (ii) p-value của R neo odometry dưới
đều ở **đoạn off-map dài** (Boreas CosPlace 0.19–0.23 ở độ sâu 0–100) — nơi null của bản đồ **không có mẫu**: null chỉ có
8–10 chunk, dài trung bình 84–135 frame. Vậy số đơn vị hoán đổi được hiệu dụng của null ≈ 10, và giả định "đoạn off-map
hoán đổi được với đoạn null" hỏng ở cả mép lẫn đoạn dài; phụ thuộc *bên trong* đoạn không phải vấn đề chính.

**Mệnh đề 5 (không tích luỹ được khi không giả định gì về phụ thuộc).** Gọi e_1..e_n là bằng chứng của n frame, mỗi
e_i hợp lệ *biên* dưới H0 (E e_i ≤ 1, hay p_i siêu đều), còn phân phối chung tuỳ ý. Mọi phép thử φ(e_1..e_n) có
P_{H0}(φ = 1) ≤ α với **mọi** phân phối chung như vậy thì, tại phân phối "n bản sao" e_1 = … = e_n = e, có
P(e ∈ A) ≤ α với A = {x : φ(x, …, x) = 1}: φ chỉ còn là phép thử một frame mức α. *Chứng minh:* phân phối bản sao là
một phân phối chung hợp lệ với cùng biên. ∎ Vì frame liền nhau gần như trùng nhau (tự tương quan trễ 1 là 0.8–0.99),
trường hợp này không phải giả tưởng: **mọi bảo đảm có tích luỹ bằng chứng theo thời gian đều cần một giả định về phụ
thuộc** (hoán đổi đơn vị, mixing, Markov). Đây là "cái giá của phụ thuộc"; cùng tinh thần với kết quả của Vovk–Wang (2021):
dưới phụ thuộc tuỳ ý, trung bình cộng là cách gộp e-value chấp nhận được duy nhất (không vượt được e-value lớn nhất).

**Định lý 4 (chứng chỉ đặt-quỹ-đạo hình học GPC: đúng với mọi phụ thuộc).** Cửa sổ odometry D = 6 excl gần nhất được đặt
lên mọi đoạn traversal của bản đồ bằng Procrustes 2-D (sai số ≤ excl/4); tập cách đặt 𝒫_t chỉ phụ thuộc odometry và hình
học bản đồ. Báo t nếu ∃P ∈ 𝒫_t: ≥ φK frame của cửa sổ có top-1 trùng điểm đặt (bán kính excl) **và** p ≤ u\*,
u\* = αφ / min(1, Q_t), Q_t = trung bình theo vị trí trong cửa sổ của phần bản đồ mà hợp các bóng excl quanh các điểm đặt phủ.
*Phát biểu:* dưới (D) p siêu đều từng frame và (GAI) P(top-1 ∈ B(p) | ảnh) ≤ q(p) (cách đặt không mang thông tin về ảnh),
P(báo sai tại t) ≤ α **với mọi phân phối chung theo thời gian**; do đó E[FL] ≤ α (tuyến tính của kỳ vọng). Không có GAI,
cận suy giảm thành α / min(1, Q_t). *Chứng minh:* mỗi frame cộng tối đa 1 vào số đếm của một cách đặt bất kỳ, nên
max_P N_P ≤ Σ_k 1[top-1 ∈ U_k] 1[p_k ≤ u\*]; lấy kỳ vọng (GAI rồi D) và Markov. ∎ *Thực nghiệm (CMU, seed 0):* FL = 0 ở mọi α,
nhưng recall chỉ 0.04–0.20 ở α = 0.05 (CPC-SC+CS 0.72–0.84): đúng Mệnh đề 5 — bảo đảm không cần giả định phụ thuộc thì
phải trả bằng power. Q_t trung vị 0.64 (CMU): phần lớn cửa sổ 150 m là gần thẳng, hình học chỉ giảm bội số ở chỗ rẽ.

**Định lý 5 (khởi phát cửa sổ hữu hạn + bền vững hình học: tỷ lệ khởi phát sai ≤ α, mọi phụ thuộc giữa các đoạn).** Luật
CPC-W: khởi phát tại t nếu log-odds cửa sổ w_t (chuỗi hiện diện khởi động lại ở odds 1 tại t − W + 1, W = H) > κ_W và ok_t
và không đang báo; duy trì khi log-odds đầy đủ ℓ_t > 0 và ok_t; ok = CS ∧ SH (SH: phần dư Procrustes của chuỗi MAP với
odometry trên 3 excl ≤ excl/2); ok sai thì **reset** (cần khởi phát mới). κ_W = phân vị conformal (1 − α) của max w trên
các đoạn H frame của null bản đồ. Giả định: (WX) với mỗi đoạn off-map G gồm H frame nằm sâu ≥ W − 1 frame trong đoạn
off-map, vector (w_t)_{t∈G} hoán đổi được với các vector của đoạn null — **chỉ trong từng đoạn**, không giả định gì giữa các
đoạn; (NC) bản đồ không chứa đường nào bắt đầu trong bán kính excl quanh vị trí on-map cuối của robot và khớp hình dạng
odometry cho tới khi robot cách bản đồ off_d; (TR) chuỗi vị trí đúng (trong excl + δ) ở frame on-map cuối.
*Phát biểu:* (a) mọi báo cáo ở frame off-map thuộc một chuỗi báo có khởi phát nằm trong đoạn off-map ở độ sâu ≥ W − 1;
(b) P(có khởi phát trong G) ≤ α cho từng G; (c) E[#đoạn có khởi phát sai] ≤ α · E[#đoạn], tức tỷ lệ khởi phát sai mỗi
đoạn ≤ α (ARL₀ ≥ H/α theo kỳ vọng) **với mọi phụ thuộc giữa các đoạn và bên trong mỗi đoạn**.
*Chứng minh:* (a) chuỗi báo mang từ bản đồ vào phải qua ok ở frame off-map đầu tiên, khi robot đã đi ≥ off_d − in_d từ vị
trí on-map cuối; nếu MAP đứng yên hay nhảy, CS/SH sai (Mệnh đề 4); nếu MAP trượt nhất quán thì đó là một đường liên tục
khớp hình dạng, trái với NC. Khởi phát ở độ sâu < W − 1 cũng phải qua ok tại các frame đó: cùng lập luận. (b) khởi phát
trong G kéo theo max_{t∈G} w_t > κ_W; w_t chỉ phụ thuộc W frame cuối, nằm hoàn toàn trong đoạn off-map; xác suất ≤ α theo
WX và tính chất phân vị conformal. (c) tuyến tính của kỳ vọng. ∎
*Khác với Định lý 1 và 3:* không cần e-value hợp lệ có điều kiện (bị vi phạm trên Boreas/4S) và không cần đoạn off-map dài
hoán đổi được với đoạn null ngắn; chỉ cần hoán đổi ở mức cửa sổ H frame. Bảo đảm là về **tỷ lệ khởi phát** (không phải
P(≥ 1 báo cáo trong đoạn), vốn phụ thuộc độ dài chuỗi báo sau khởi phát).
*Thực nghiệm (366 run, 10 seed):* tỷ lệ khởi phát sai trung bình mỗi đoạn 0.001–0.006 trên 7/7 dataset cho mọi luật CPC (α
= 0.05); tệ nhất từng run ≤ 0.013 với CPC-SC+CS, nhưng CPC-W tới 0.071–0.114 trên CMU (bản đồ nhỏ, ~70 đoạn null: phân vị
conformal dao động theo run — bảo đảm là biên theo hiệu chuẩn, không theo từng run).

**Hệ quả (giới hạn của hiệu chuẩn bằng bản đồ).** Với n đơn vị hoán đổi được, bảo đảm có điều kiện theo hiệu chuẩn
P(rủi ro > α + ε | hiệu chuẩn) ≤ δ cần n ≳ log(1/δ)/α đơn vị độc lập; bản đồ cho ~10 chunk null độc lập, nên chỉ bảo đảm
biên là khả thi — đúng với dao động theo run quan sát được (worst-run > α trên CMU dù trung bình ≪ α).

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
