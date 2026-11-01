# CMS — Phẫu thuật bản đồ phản thực: tự hiệu chuẩn quyết định định vị trên chính luồng triển khai

*Entry 28–29, branch `hmm-navigation-5` (§4b: hiệu chỉnh sau tự kiểm toán). Code: `analysis/cms.py` (thống kê + luật), `analysis/cms_dump.py` (Kaggle),
`analysis/oc_curves.py --cms`. Ký hiệu như `paper/cpc_theory.md` §0.*

## 1. Vì sao cần một null mới

Mọi bảo đảm không nhãn trước đây (SelfCal, certified, CPC-SC, CPC-SC-T, Định lý 1–5) lấy null từ **chính bản đồ**: frame
bản đồ, với block của nó bị che, đóng vai query off-map. Null này có ba khiếm khuyết đã đo được:

1. **Sai điều kiện:** ảnh của null có điều kiện của bản đồ (ví dụ trời nắng), không phải điều kiện triển khai (đêm, tuyết).
2. **Sai nhiễu và sai phụ thuộc:** odometry của null là pose bản đồ chính xác; đoạn null ngắn (~100 frame), chỉ ~10 chunk
   độc lập, không có đoạn off-map dài (Entry 26: vi phạm nằm ở mép bản đồ và ở đoạn dài).
3. **Quá ít đơn vị:** với n ≈ 10–70 đoạn null, α = 0.01 không khả thi (κ = ∞ trên CMU, 4S office) và bảo đảm có điều kiện
   theo hiệu chuẩn (PAC) không thể có (Hệ quả §3e).

Hệ quả thực nghiệm: tỷ lệ khởi phát sai thực tế 0.001–0.006 ≪ α = 0.05 — ngân sách rủi ro bị bỏ phí, điểm mặc định dè dặt.

## 2. Cấu trúc: phẫu thuật bản đồ quanh niềm tin của chính hệ thống

Cho bản đồ M (vị trí m_j, descriptor), luồng query (ảnh I_t, odometry o_t), một thống kê bằng chứng bộ nhớ hữu hạn
T_t = τ(W_t; M) trên cửa sổ W_t (N = 20 frame gần nhất), lớn = nhiều bằng chứng có mặt. Hệ thống có một **niềm tin** b_t:
các anchor a_{t,1..N} của giả thuyết tuyến thắng (vị trí bản đồ mà hệ thống tin là robot đã đi qua trong cửa sổ).

**Phẫu thuật.** B_t = ∪_k B(a_{t,k}, ρ), ρ = off_d (xem ghi chú về ρ bên dưới). Thống kê phản thực T^cf_t = τ(W_t; M \ B_t), tính **y hệt** T_t:
giả thuyết trong B_t bị bỏ, tra cứu ngoại hình của entry bị che rơi về similarity thứ K, vệt anchor đi vào B_t rời khỏi
chunk tuyến từ điểm đó (đúng như một lỗ thật: chunk tuyến kết thúc ở lỗ).

**Quan sát then chốt.** Nếu niềm tin gần đúng (|a_{t,k} − x_{t−k}| = e nhỏ), mọi frame của cửa sổ cách bản đồ còn lại
≈ ρ − e ≈ off_d: trên bản đồ đã phẫu thuật, cửa sổ là một cửa sổ off-map **nằm đúng ở biên định nghĩa off-map** — trường hợp
khó nhất (giống bản đồ nhất) theo S2 — với ảnh, điều kiện, nhiễu odometry và phụ thuộc thời gian **của chính query**.

*Ghi chú về ρ (sai lệch so với đăng ký trước, RESEARCH_LOG Entry 28).* Bản đăng ký trước dùng ρ = off_d + excl với lập luận
"niềm tin sai tới excl thì frame phản thực vẫn > off_d". Lập luận này sai chiều: với niềm tin gần chính xác, frame phản thực
nằm cách bản đồ ≈ off_d + excl, **xa hơn** các frame off-map thật ở 40–65 m, nên null phản thực ít giống bản đồ hơn thật ⇒
chống-bảo-thủ (chẩn đoán có nhãn: vi phạm theo seed, ví dụ CMU seed 5–9). Theo S2 lựa chọn bảo thủ là null **ở biên**: ρ = off_d;
niềm tin lệch e chỉ đưa frame phản thực vào vùng off_d − e (giống bản đồ hơn) ⇒ bảo thủ. Nếu niềm tin sai, nơi thật còn nguyên sau phẫu
thuật và T^cf lớn (phía bảo thủ). Null = {T^cf_t} của luồng: hàng trăm–hàng nghìn đoạn mỗi điều kiện.

Hai thống kê dùng trong Entry 28 (chỉ cần danh sách top-100, nên phẫu thuật là phép che chỉ số):
chi phí tuyến C_t (TAO'26, thấp = có mặt) và độ khác biệt z_t = (s1 − s_far)/std_t (s_far: entry tốt nhất cách top-1
> excl; phép thử tỷ lệ không gian, bất biến affine).

## 3. Giả định

- **(S1) Bất biến phẫu thuật.** Với cửa sổ mà mọi frame cách bản đồ M' ≥ off_d, phân phối của τ(W; M') cho điều kiện c chỉ
  phụ thuộc c và hồ sơ khoảng cách D = (d(x_i, M'))_i, không phụ thuộc vùng nào của bản đồ bị thiếu.
- **(S2) Đơn điệu.** Phân phối đó giảm ngẫu nhiên theo D (xa bản đồ hơn ⇒ ít bằng chứng có mặt hơn).
- **(S3) Hoán đổi theo đoạn, trong cùng luồng.** Với cùng điều kiện, vector thống kê trên một đoạn H frame của một chuyến
  off-map thật hoán đổi được với vector trên một đoạn phản thực có niềm tin đúng, **sau khi** điều chỉnh khoảng cách theo S2.
  Không giả định gì về phụ thuộc bên trong đoạn hay giữa các đoạn.

So với null bản đồ: S3 chỉ so hai mẫu **của cùng một luồng** (cùng camera, cùng điều kiện, cùng odometry), thay vì so query
đêm với ảnh bản đồ ban ngày có odometry hoàn hảo.

## 4. Định lý 6 (hợp lệ dưới tự-nhiễm)

Trong một điều kiện có n đoạn phản thực, gọi π là tỷ lệ đoạn phản thực đến từ cửa sổ on-map có niềm tin đúng ("đoạn tốt").
Ngưỡng khởi phát κ = phân vị conformal (1 − α) của max_{t∈G} T^cf_t trên các đoạn G. Với một đoạn off-map thật G₀ có độ sâu
≥ N − 1 frame trong chuyến off-map:

> P( ∃ t ∈ G₀ : T_t > κ ) ≤ α (n + 1) / (π n + 1) ≈ α / π,

với mọi phụ thuộc bên trong đoạn và giữa các đoạn (luật bộ nhớ hữu hạn CMS-T; với chuỗi hiện diện là phát biểu cho khởi
phát trong đoạn vào khi chưa báo, như CPC-SC).

*Chứng minh.* Đoạn tốt: theo S1–S2, max T^cf trên đoạn tốt (khoảng cách ≈ off_d, biên khó nhất) trội ngẫu nhiên so với
max T trên đoạn off-map thật (khoảng cách ≥ off_d), và theo S3 ta có thể ghép (coupling) X₀ := max_{G₀} T ≤ X' với X' hoán
đổi được với πn đoạn tốt. Trường hợp xấu nhất cho κ là mọi (1 − π)n đoạn còn lại đều nằm dưới κ: khi đó κ ≥ thống kê thứ
r = ⌈(1 − α)(n + 1)⌉ − (1 − π)n của πn đoạn tốt. Tính chất hạng của phần tử hoán đổi được cho
P(X' > κ) ≤ (πn + 1 − r)/(πn + 1) ≤ α(n + 1)/(πn + 1). ∎

**Mệnh đề 8 (hướng của nhiễm).** (i) Frame on-map có niềm tin **sai**: nơi thật sống sót sau phẫu thuật ⇒ T^cf lớn ⇒ đẩy κ
lên (bảo thủ). (ii) Frame off-map: phẫu thuật chỉ làm bản đồ thưa hơn ⇒ khoảng cách tăng ⇒ theo S2, T^cf nhỏ hơn bằng chứng
off-map thật ⇒ đây là nhiễm duy nhất phía không bảo thủ, và Định lý 6 trả giá nó bằng hệ số 1/π. (iii) Frame on-map có niềm
tin đúng nhưng nhìn thấy bản đồ ngoài ρ (chồng lấn tầm nhìn): giống hệt frame off-map thật gần mép lỗ ⇒ không thiên lệch.
So với Bashari–Sesia–Romano (ICML'25, conformal outlier detection với tập tham chiếu bị nhiễm): ở đó nhiễm làm phép thử bảo
thủ; ở đây null được **sinh ra** (không phải thu thập), nên ta phân tích được chính xác hướng của từng loại nhiễm.

**Hệ quả 9 (α nhỏ và bảo đảm PAC trở nên khả thi).** (a) Luồng cho n ≈ T/H đoạn mỗi điều kiện (CMU ~190, 4Seasons 300–450,
Boreas ~580, NCLT ~480), nên α = 0.01 khả thi ở mọi dataset (cần n ≥ 2/α − 1; điều kiện nhỏ hơn được gộp — Mondrian có dự
phòng, quy tắc đặt trước). (b) Bảo đảm có điều kiện theo hiệu chuẩn (Vovk 2012): chọn κ là đoạn max lớn thứ k với k lớn nhất
thoả P(Bin(n, α) ≤ k − 1) ≤ δ thì P( tỷ lệ khởi phát sai > α/π | hiệu chuẩn ) ≤ δ (biến thể `-PAC`, δ = 0.1). Với null
bản đồ (n ≈ 10) điều này bất khả.

**Mệnh đề 10 (hợp hai phép thử).** CMS-U báo khi phép thử tuyến (CMS-T) **hoặc** khởi phát chuỗi hiện diện vượt ngưỡng,
mỗi cái hiệu chuẩn ở α/2: tỷ lệ khởi phát sai ≤ α/π (cận hợp).

**Duy trì và dừng.** Chuỗi hiện diện duy trì báo khi log-odds > 0 nên một chuỗi báo có thể được mang từ bản đồ vào lỗ;
Định lý 6 chỉ nói về khởi phát. Như CPC-SC (Bổ đề 7, Mệnh đề 4, Định lý 5): dừng hình dạng SH trên quỹ đạo MAP của HMM chỉ
loại báo cáo (không làm tăng segFAR/FL) và cắt chuỗi báo ở mép bản đồ dưới giả định NC. CMS-CPC **không** dừng là đối chứng
chẩn đoán (dự đoán: vi phạm segFAR).


## 4b. Hiệu chỉnh sau tự kiểm toán (Entry 29)

**(i) Khởi phát của chuỗi đầy đủ bộ nhớ (lỗ hổng, kế thừa từ CPC-SC vòng 3).** κ được hiệu chuẩn trên các đoạn phản thực với
chuỗi **khởi động lại ở odds 1** (log-odds 0), với lập luận "odds 1 là mức cao nhất mà một chuỗi chưa báo có thể giữ". Lập luận
này **sai** khi κ > 0 (thực tế κ ≈ 2.4–4.7): với trễ Schmitt (khởi phát > κ, duy trì > 0), một chuỗi chưa từng khởi phát có thể
vào đoạn với log-odds bất kỳ trong (0, κ]; bước dự đoán g(ℓ) = logit(σ(ℓ)(1 − p) + (1 − σ(ℓ))p) tăng theo ℓ, nên từ trạng thái
đó chuỗi vượt κ dễ hơn chuỗi khởi động ở 0 ⇒ phân vị hiệu chuẩn không trội tỷ lệ khởi phát thật. Phát biểu "P(khởi phát trong
đoạn) ≤ α" của CPC-SC và của CMS-CPC vì vậy **chỉ là xấp xỉ** (thực nghiệm: tỷ lệ thực tế vẫn ≤ α ở 7/7, nhưng không phải định lý).

*Sửa (CMS-CPCW).* Khởi phát bằng log-odds **cửa sổ hữu hạn** w_t (chuỗi khởi động lại ở odds 1 tại t − W + 1, W = H): w_t chỉ phụ
thuộc W frame cuối, **không phụ thuộc trạng thái lúc vào đoạn**; κ_W = phân vị conformal của max w trên các đoạn phản thực (cùng
w). Duy trì vẫn bằng chuỗi đầy đủ (ℓ_t > 0) và dừng SH.

**Định lý 6′ (khởi phát cửa sổ hữu hạn).** Dưới S1–S3 (S3 áp cho vector (w_t) của các đoạn H frame nằm sâu ≥ W − 1 frame trong
chuyến off-map) và với π, n như Định lý 6: P(∃ t ∈ G₀: w_t > κ_W) ≤ α(n+1)/(πn+1), mọi phụ thuộc trong và giữa các đoạn; mọi báo
cáo off-map của CMS-CPCW thuộc một chuỗi báo có khởi phát trong chuyến off-map (Định lý 5 (a), dưới NC và dừng SH) ⇒ tỷ lệ khởi phát
sai mỗi đoạn ≤ α/π (tuyến tính của kỳ vọng). *Chứng minh:* như Định lý 6, thay max T bằng max w; w của đoạn không phụ thuộc quá
khứ trước t − W + 1. ∎

**(ii) Phát biểu chính xác của S3 và của tập "đoạn tốt".** Tập đoạn tốt (niềm tin đúng) là ngẫu nhiên và phụ thuộc dữ liệu. Giả
định cần là: có ghép X₀ ≤ X′ sao cho (X′, các max của đoạn tốt) hoán đổi được **có điều kiện trên nhãn tốt/xấu** của các đoạn
phản thực. Định lý 6 không khẳng định gì cho đoạn ở độ sâu < N − 1 (cửa sổ còn chồng lên bản đồ ở đầu chuyến off-map); segFAR
thực nghiệm tính mọi đoạn.

**(iii) Null phản thực chính xác.** Bản Entry 28 xoá entry trong hành lang khỏi top-100 đã lưu: còn 100 − n_mask giả thuyết và
giá trị dự phòng là similarity thứ 100 của bản đồ đầy đủ — không đúng thống kê trên M \ B_t. `analysis/cms_exact.py` dùng top-300
và lấy đúng 100 entry chưa che đầu tiên cho giả thuyết, tra cứu và dự phòng (= top-100 của M \ B_t khi n_mask ≤ 200; không có
danh sách nào bị thiếu trên dữ liệu thử). Kiểm: chi phí tuyến phản thực đổi ít (trung vị +0.004 trên thang ~1.3, hai chiều), độ
khác biệt phản thực bản cũ chống-bảo-thủ (trung vị 0.264 so với 0.287).

**(iv) Cổng innovation phản thực (+NGR, `analysis/navrisk.py`) — rủi ro điều hướng.** Bằng chứng hiện diện kiểm soát *có hay
không* một fix sai, không kiểm soát *tác hại*: một fix sai dịch ước lượng của bộ lọc K·ν (ν = innovation). Winner phản thực j_cf là
fix sai theo cấu trúc; d_cf = |m(j_cf) − m(j)| là innovation nó gây ra cho một bộ lọc bám đúng niềm tin. Cổng τ = phân vị β của
d_cf (β = 0.05).
*Mệnh đề 11.* (a) +NGR chỉ bỏ báo cáo ⇒ mọi cận theo đoạn của luật nền (segFAR, FL, Định lý 6/6′) giữ nguyên (Bổ đề 7).
(b) (Gần đúng, không phải định lý.) Dưới S1–S3 áp cho d_cf, nếu ước lượng của bộ lọc lệch niềm tin không quá e thì
|ν − d| ≤ e cho fix sai tương ứng, nên một fix sai ở biên off-map lọt cổng với xác suất ≤ P(d_cf ≤ τ + e) ≈ β/π + P(τ < d_cf ≤ τ + e)
(d_cf đo so với niềm tin, ν đo so với bộ lọc).
*Lưu ý (kiểm toán).* Giả thuyết phản thực nằm ngoài hành lang bán kính ρ quanh mọi anchor, nên d_cf ≥ ρ theo cấu trúc và
τ ≥ ρ = off_d (đo được: 40.5–44 m ở các dataset đô thị, 29–30 frame ở Nordland với ρ = 10): cổng về bản chất là cổng innovation
bán kính cỡ off_d (đơn vị bài toán), phần phản thực chỉ hiệu chỉnh phần trên ρ theo từng điều kiện. Không tuyên bố novelty cho
riêng cổng (Gate 13).
(c) Mở khoá theo chuỗi (R = H báo cáo liên tiếp có innovation đồng nhất, độ phân tán ≤ excl/2) tránh khoá chết khi bộ lọc trôi;
giá: một chuỗi báo sai trượt song song đều với bộ lọc có thể lọt — đúng loại báo sai mà dừng SH cũng không bắt.

## 4c. Hiệu chuẩn nhân quả và cổng điều hướng (Entry 30)

**Vấn đề.** Nhóm hiệu chuẩn `cond` dùng toàn bộ luồng phản thực của chính phiên (kể cả frame tương lai) — chuyển đạo. Nặng hơn:
một phiên **hoàn toàn off-map** (robot ở vùng chưa có bản đồ suốt phiên) có π = 0 trong nhóm của nó ⇒ cận α(n+1)/(πn+1) của
Định lý 6 vô nghĩa, và theo Mệnh đề 8 (ii) nhiễm của frame off-map là phía không bảo thủ.

**Ba nhóm nhân quả** (cùng thống kê, cùng luật CMS-CPCW / CMS-CPC+G, chỉ khác tập hiệu chuẩn của κ và của phép biến đổi e-value):
- `[loco]`: chỉ các phiên khác (phiên trước của robot). π = tỷ lệ đoạn tốt trong các phiên khác.
- `[online]`: các phiên khác cộng các đoạn H frame **đã kết thúc** của phiên hiện tại (cập nhật cuối mỗi khối H); phép biến đổi
  p → e và a của Beta-EM cố định từ các phiên khác. Ngưỡng dùng trong một đoạn G₀ chỉ phụ thuộc dữ liệu trước G₀.
- `[both]`: báo iff luật `cond` **và** luật `[loco]` cùng báo.

**Định lý 6″ (hiệu chuẩn tuần tự).** Với `[online]`, gọi P(G₀) là tập đoạn phản thực có trước G₀ (n đoạn, tỷ lệ tốt π). Dưới
S1–S3 áp cho G₀ và các đoạn tốt của P(G₀) (hoán đổi có điều kiện trên nhãn tốt/xấu), với G₀ thẳng hàng với lưới khối H:
P(∃ t ∈ G₀: w_t > κ_W(P(G₀))) ≤ α(n+1)/(πn+1). *Chứng minh:* có điều kiện trên P(G₀), ngưỡng cố định trên G₀; lập luận hạng
của Định lý 6′ áp nguyên. Với G₀ không thẳng hàng, ngưỡng đổi tối đa một lần trong G₀ ⇒ cận hợp cho hệ số ≤ 2. ∎
Hệ quả: tỷ lệ khởi phát sai ≤ α/π với π của **các phiên khác cộng phần đã qua**, không còn π = 0 cho phiên toàn off-map
(miễn là các phiên khác có phần on-map — đúng với mọi robot đã từng chạy trên bản đồ của nó).

**Mệnh đề 12 (giao hai luật).** Với mọi đoạn off-map G₀: P([both] báo trong G₀) ≤ min(P(cond báo trong G₀), P(loco báo trong G₀)),
nên segFAR kỳ vọng của `[both]` ≤ min của hai luật: `[both]` hợp lệ nếu **một trong hai** null hợp lệ (π của phiên hoặc π của
các phiên khác lớn). Giá: recall ≤ min của hai luật. *Chứng minh:* tập báo của `[both]` là giao hai tập báo. ∎

**Cổng +NGR — hai biến thể mở khoá và một sửa (Entry 30).** (a) Code Entry 29 kiểm lại độ đồng nhất sau mỗi fix được nhận; bước
nhảy innovation do chính cập nhật của bộ lọc làm chuỗi "mất đồng nhất" ⇒ chuỗi đã mở chỉ được nhận **một fix mỗi R frame** (khác mô
tả "mở cho cả chuỗi"). Hai biến thể được giữ: `+NGR` (vòng 8) mở **đến hết chuỗi**; `+NGRr` mở **giới hạn tốc độ** (= code vòng 7):
một chuỗi báo sai trượt song song đều với bộ lọc — đúng loại mà mở khoá không phân biệt được với trôi — chỉ kéo bộ lọc tối đa
K·ν mỗi R frame, nên tác hại của nó bị chặn theo tốc độ; đổi lại, phục hồi sau trôi lớn chậm hơn R lần. LODO chọn giữa hai biến
thể (không chọn theo bảng). (b) Bán kính max(τ, 3√P⁻): khi bộ lọc chưa định vị (P⁻ lớn, ví dụ khởi tạo không nhãn), innovation của fix đúng
có thể lớn cỡ √P⁻; khi bộ lọc đã định vị (√P ≈ 0.6 m ≪ τ) sàn này không hoạt động. Cả hai chỉ bỏ báo cáo ít hơn, vẫn là
"chỉ bỏ báo cáo" so với luật nền ⇒ Mệnh đề 11 (a) giữ nguyên.

**Benchmark off-map tự nhiên (4sx).** Bản đồ = bản ghi tham chiếu của cảnh 4Seasons A (không có lỗ), truy vấn = các bản ghi khác
của A rồi **mọi** bản ghi của cảnh B (thành phố khác: mọi frame off-map, ảnh và VIO thật). Đây là trường hợp π = 0 cho `cond` ở
mọi phiên B, nơi Định lý 6″ / Mệnh đề 12 là bảo đảm còn lại.

## 5. Điểm mới so với tài liệu (tóm tắt; Gate 12 trong `LITERATURE_GATE.md`)

- Null bản đồ (SelfCal, certified, CPC-SC; SAFEVPR'26 và Quantile Transfer dùng nhãn trên traversal hiệu chuẩn): null đến
  từ dữ liệu khác điều kiện. **CMS:** null là **can thiệp (do-operation) lên biểu diễn môi trường tại chính niềm tin của
  mô hình**, áp lên luồng triển khai — không cần nhãn, không cần traversal hiệu chuẩn.
- Tỷ lệ uniqueness của SeqSLAM / phép thử tỷ lệ không gian: là **điểm số**, không có hiệu chuẩn; CMS dùng phẫu thuật để
  **hiệu chuẩn** bất kỳ điểm số nào (ở đây chi phí tuyến TAO'26, vốn không có ngưỡng không nhãn).
- Knockoffs (Barber–Candès) tạo bản sao null giữ cấu trúc phụ thuộc của biến; CMS tạo bản sao null của **bằng chứng** giữ
  cấu trúc phụ thuộc thời gian của luồng, bằng cách xoá tín hiệu (nơi thật) khỏi bản đồ thay vì mô phỏng biến.
- Conformal trực tuyến / rolling conformal (Barber et al.): cần quan sát kết quả (nhãn) trên luồng; CMS tự sinh mẫu null.
