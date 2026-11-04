# HSI — lý thuyết (ý tưởng 2, Entry 1)

*Ký hiệu.* Vị trí thật x_t; vị trí bản đồ P = {p_j}; fix của chuỗi vị trí f_t = p_{est_t}; odometry o_t (trong hệ của chuỗi) với
o_t − o_s = R_q (x_t − x_s) + ε_{s,t}, |ε_{s,t}| ≤ κ ℓ(s,t) + σ_o (trôi tỉ lệ quãng đường ℓ, R_q phép quay chưa biết của chuỗi q).
Off-map: d(x_t, P) > off_d; fix đúng: |f_t − x_t| ≤ excl. Đoạn null = đoạn H frame mà mọi frame có fix sai hoặc robot off-map.

## Mệnh đề 1 (điều mà tự nhất quán hình học chứng nhận)

Nếu với mọi cặp (i, j) trong cửa sổ W, |(f_j − f_i) − (o_j − o_i)| ≤ τ_{j−i} (R_q = I), thì sai số e_t = f_t − x_t thoả
|e_j − e_i| ≤ τ_{j−i} + κ ℓ(i,j) + σ_o: sai số của chuỗi gần như **hằng** trên cửa sổ. Do đó "neo" ⟹ (fix đúng) ∨ (chuỗi bám một tuyến
**dịch cứng** c = e ≈ const với |c| > excl). Trường hợp sau đòi hỏi bản đồ có một tuyến đồng dạng (song song, cùng độ dài, cùng các khúc
quay) với quãng đường của robot ở độ lệch c, VÀ ngoại hình ưu tiên tuyến đó ở mọi frame của cửa sổ. *Hệ quả:* nếu quãng đường trong cửa sổ không
có vị trí đặt thay thế nào trên bản đồ (tập C(W) = {c ≠ 0 : d(x_i + c, P) ≤ τ ∀ i} rỗng) thì neo ⟹ fix đúng, **bất kể điều kiện ảnh**: chứng
chỉ không dùng giá trị similarity. Thực nghiệm (tập thiết kế, 28 run): P(fix đúng | neo) ≥ 0.993; vài neo sai còn lại đúng là các tuyến
dịch cứng xa hàng trăm mét (aliasing có cấu trúc) ⇒ Mệnh đề 2.

## Mệnh đề 2 (tham chiếu tin cậy loại tuyến dịch cứng)

Giả sử tham chiếu hiện tại đúng (sai số ≤ s_0) và odometry trôi ≤ κ. Một neo mới ở quãng ℓ sau tham chiếu được chấp nhận khi
|f_t − x̂_DR(t)| ≤ τ + 2κ̂ℓ. Một neo trên tuyến dịch cứng c thoả |f_t − x̂_DR(t)| ≥ |c| − s_0 − κℓ, nên bị loại khi |c| > τ + s_0 + (2κ̂ + κ)ℓ.
Tuyến sai chỉ lọt khi (i) chưa có tham chiếu (đầu chuỗi), hoặc (ii) nó chiếm ≥ P_over frame neo liên tục (luật ghi đè, cần cho trường hợp
tham chiếu cũ sai). Hai trường hợp này là nguồn còn lại của fix sai xa (D5).

## Mệnh đề 3 (độ chính xác của vị trí hồi cứu — cầu Brown)

Giữa hai đoạn đã xác minh ở hai phía (khoảng cách quãng d_l, d_r tới chúng), dead reckoning tiến từ phía trái và lùi từ phía phải, trộn
theo w = d_l/(d_l + d_r), có sai số ≤ s_0 + κ d_l d_r/(d_l + d_r) với trôi tuyến tính (tỉ lệ / hướng không đổi trong khoảng); với trôi kiểu
bước ngẫu nhiên, phương sai cầu Brown ∝ d_l d_r/(d_l + d_r). Nhãn hồi cứu với biên z σ_t (σ_t = s_0 + κ̂ d_l d_r/(d_l + d_r), κ̂ ước lượng từ
sai số dự đoán một phía của các khoảng đã đóng, không nhãn) là đúng khi sai số thật ≤ z σ_t. Kiểm chứng (tập thiết kế): độ chính xác nhãn
off-map 1.000 (Boreas, office, countryside, Nordland), 0.88–0.93 (old town, NCLT: odometry thật trôi); nhãn "fix đúng" ≥ 0.99.

## Mệnh đề 4 (hiệu chuẩn biên của luật hợp; hợp lệ dưới hoán đổi)

Luật báo R_t = A_t ∨ B_t ∨ (C_t ∧ g_t > θ), với A, B (hình học) và miền C xác định nhân quả. Với mỗi đoạn null hồi cứu giữ ra u, đặt
S_u = max_{t∈u} s_t, s_t = +∞ nếu A_t ∨ B_t, g_t nếu C_t, −∞ còn lại; θ = phân vị ⌈(1−α)(n+1)⌉ của {S_u}. Nếu đoạn null mới U* hoán đổi được
với n đoạn hiệu chuẩn (cùng phân phối, điều kiện cùng mô hình đã học) thì P(R báo trong U*) = P(S_{U*} > θ) ≤ α. Không cần giả định gì về phụ
thuộc BÊN TRONG đoạn. Hiệu chuẩn có điều kiện (chỉ các đoạn trong miền C) là bảo thủ hơn và lãng phí ngân sách (ablation HSI-regime).
*Giới hạn:* (i) hoán đổi giữa đoạn null hồi cứu và đoạn sai thật cần nhãn đúng: nhãn thiếu ở các chuỗi chưa từng xác minh → được đưa vào null
(bảo thủ); nhãn sai (tuyến dịch cứng được xác minh) làm thiếu null → slack ≤ tỉ lệ đoạn bị gán nhầm; (ii) giữa các phiên (điều kiện) khác nhau
hoán đổi chỉ xấp xỉ — gộp phiên (`pooled`) là lựa chọn mặc định vì số excursion thật mỗi phiên quá ít (5–7 lỗ / phiên).

## Mệnh đề 5 (sàn MAP)

Báo khi ĝ_t = P̂(fix đúng | đặc trưng) > 1/2 là luật Bayes cho tổn thất 0–1 cân bằng; kết hợp ngưỡng conformal (max(θ, 1/2)) không làm hỏng
Mệnh đề 4 (miền báo nhỏ hơn) và chặn trường hợp ngưỡng conformal suy biến (θ = −∞ khi phần lớn đoạn null không có frame đủ điều kiện) — nguồn
của fix sai xa ở đầu phiên trong thiết kế (Nordland DINOv2: 11 fix sai > 20 frame, sai số điều hướng 17.5 → 0.7).

## Mệnh đề 6 (chứng nhận rồi hiệu chuẩn — Entry 5)

Gọi G_t = A_t ∨ B_t (chứng chỉ hình học) và N là tập null hồi cứu. Với mọi đoạn off-map thật U:
P(R báo trong U) ≤ P(G báo trong U) + P(C báo trong U) ≤ ε_G + α_C, với ε_G = xác suất chứng chỉ sai trên một đoạn off-map (Mệnh đề 1–2: cần
một tuyến SAI vừa khớp odometry ở mọi độ trễ 10–80 m vừa khớp dead-reckoning của tham chiếu trước) và α_C là mức conformal của nhánh học
(Mệnh đề 4, áp cho điểm s_t = g_t nếu C_t, −∞ còn lại). Hiệu chuẩn hợp (Mệnh đề 4) thay ε_G bằng ước lượng thực nghiệm trên N — đúng khi N
sạch, nhưng **khi N bị nhiễm các frame đúng (cầu hồi cứu dài trôi xa), chứng chỉ báo ĐÚNG ở các frame đó lại bị tính là vi phạm**: tập thiết
kế, tỉ lệ G báo trong N ∩ off-map thật = 0.000 (Boreas, CMU, NCLT), trong N ∩ fix đúng = 0.52–0.58 (NCLT, Boreas); NCLT: 18 % đoạn null có G
báo > α ⇒ ngưỡng của (c) = +∞. Lý do nhiễm: chỉ 6–13 % frame NCLT được xác minh hồi cứu (độ chính xác 1.000) trong khi chứng chỉ phủ 28–42 %
(độ chính xác ≥ 0.997) ⇒ cầu Brown nối các đoạn xác minh thưa dài hàng trăm mét, sai số cầu 30–180 m vượt z σ.
**Hệ quả / thiết kế:** dùng G làm điểm neo hồi cứu cùng với các đoạn xác minh (ver ∪ G): cầu ngắn hơn (Mệnh đề 3: σ ∝ d_l d_r/(d_l + d_r)) ⇒
nhãn huấn luyện và null sạch hơn; G không còn trong N nên không tự chứng nhận mà cũng không bị tính trùng — bảo đảm trở thành ε_G + α. ε_G
không hiệu chuẩn được bằng dữ liệu không nhãn mà là tính chất của phép thử hình học; nó được kiểm chứng trực tiếp trên tập giữ ra (biến thể
geo-rm, Entry 5). Hai cách "giữ G trong hiệu chuẩn" đã thử trên tập thiết kế đều thua: (i) phán xét G bằng cầu không dùng G (HSI-Vc) — nhiễm
như cũ; (ii) phán xét mỗi đoạn neo bằng các đoạn neo lân cận (leave-one-run-out) — chuỗi ngắn (CMU) không có lân cận ⇒ G thành "chưa xác minh".

## Mệnh đề 7 (vách khoá hiệu chuẩn và căn chỉnh Neyman–Pearson — Entry 8)

Ngưỡng hợp θ = phân vị ⌈(1−α)(n+1)⌉ của S_u = max_{t∈u} s_t trên n đoạn null. Gọi q = tỉ lệ đoạn null có ít nhất một frame được phép báo
(s_t > −∞). (i) Nếu q < α thì θ = −∞ (mọi frame trong chế độ (c) đều báo); nếu q ≥ α thì θ nằm trong phân phối điểm của các đoạn "trúng". Khi điểm
bão hoà (GBM: P̂ ≈ 1 trên phần lớn frame được phép), θ ≈ 1 và nhánh học TẮT HẲN ⇒ hiệu năng là một hàm bậc thang của q: một vài chuỗi ngắn
(CMU CosPlace s4: 6 chuỗi, 1.1 % frame) đủ đẩy q qua α và khoá toàn bộ lần triển khai (recall 0.88 → 0.59). (ii) Điểm tối ưu cho phép thử
conformal là tỉ số hợp lý Λ(x) = p₊(x)/p₀(x) giữa phân phối dương và **phân phối null dùng để hiệu chuẩn** p₀ (bổ đề Neyman–Pearson; với max
theo đoạn: xấp xỉ). Mô hình học trên nhãn hồi cứu (đúng vs sai CÓ nhãn) ước lượng p₊/p_sai, KHÔNG phải p₊/p₀: p₀ còn gồm frame chưa từng xác minh
(đầu chuỗi trong lỗ, chuỗi ngắn), mô hình chưa thấy chúng là âm nên chấm điểm cao ⇒ q bị thổi lên. **Căn chỉnh:** học dương (đã xác minh) vs null
(gồm cả chưa xác minh), chỉ trên các đơn vị huấn luyện (tách khỏi đơn vị hiệu chuẩn ⇒ Mệnh đề 4 giữ nguyên). Đo được (CMU, phát triển): SALAD s4
0.520 → 0.914 (segFAR 0.000), CosPlace s4 0.590 → 0.873; tập thiết kế: recall không đổi, segFAR max 0.044 → 0.014. (iii) Giới hạn: khi null
bị nhiễm bởi frame ĐÚNG mà đặc trưng không phân biệt được với dương (chuỗi ngắn hoàn toàn đúng nhưng không thể chứng nhận, CosPlace s1), không
thông tin nào gỡ được khoá mà vẫn giữ bảo đảm; và ở thang 20–40 m hình học không giúp (K(p, ℓ) = 0 gần như không xảy ra — mọi đoạn đường ngắn
đều có bản sao đồng dạng trong bản đồ), nên chứng nhận sớm hơn bằng hình học là bất khả.

## Vì sao khác ý tưởng 1

Ý tưởng 1 sinh null bằng **can thiệp** lên bản đồ (phẫu thuật phản thực quanh niềm tin của hệ thống) và hiệu chuẩn một thống kê hiện diện cố
định; giới hạn của nó: hệ số 1/π (mô phỏng xuất phát từ trạng thái đã sai), lỗ ảo khác lỗ thật ở mép, thống kê bất biến affine bỏ thông tin.
HSI không can thiệp: nó **quan sát** các excursion thật của chính lần triển khai qua hình học hồi cứu, **học** hàm điểm (dùng cả similarity
tuyệt đối — thông tin mạnh nhất, AUROC 0.95–0.99 với descriptor tốt) và hiệu chuẩn trên excursion thật (mép và đầu chuỗi có sẵn trong tập
hiệu chuẩn). Thành phần hình học (A, B) không cần hiệu chuẩn và gần như không có báo sai.
