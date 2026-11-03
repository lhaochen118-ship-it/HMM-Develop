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

## Vì sao khác ý tưởng 1

Ý tưởng 1 sinh null bằng **can thiệp** lên bản đồ (phẫu thuật phản thực quanh niềm tin của hệ thống) và hiệu chuẩn một thống kê hiện diện cố
định; giới hạn của nó: hệ số 1/π (mô phỏng xuất phát từ trạng thái đã sai), lỗ ảo khác lỗ thật ở mép, thống kê bất biến affine bỏ thông tin.
HSI không can thiệp: nó **quan sát** các excursion thật của chính lần triển khai qua hình học hồi cứu, **học** hàm điểm (dùng cả similarity
tuyệt đối — thông tin mạnh nhất, AUROC 0.95–0.99 với descriptor tốt) và hiệu chuẩn trên excursion thật (mép và đầu chuỗi có sẵn trong tập
hiệu chuẩn). Thành phần hình học (A, B) không cần hiệu chuẩn và gần như không có báo sai.
