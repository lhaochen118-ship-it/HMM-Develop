# CMS — Phẫu thuật bản đồ phản thực: tự hiệu chuẩn quyết định định vị trên chính luồng triển khai

*Entry 28, branch `hmm-navigation-5`. Code: `analysis/cms.py` (thống kê + luật), `analysis/cms_dump.py` (Kaggle),
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

**Phẫu thuật.** B_t = ∪_k B(a_{t,k}, ρ), ρ = off_d + excl. Thống kê phản thực T^cf_t = τ(W_t; M \ B_t), tính **y hệt** T_t:
giả thuyết trong B_t bị bỏ, tra cứu ngoại hình của entry bị che rơi về similarity thứ K, vệt anchor đi vào B_t rời khỏi
chunk tuyến từ điểm đó (đúng như một lỗ thật: chunk tuyến kết thúc ở lỗ).

**Quan sát then chốt.** Nếu niềm tin đúng (|a_{t,k} − x_{t−k}| ≤ excl với mọi k), mọi frame của cửa sổ cách bản đồ còn lại
> ρ − excl = off_d: trên bản đồ đã phẫu thuật, cửa sổ là một cửa sổ **off-map hợp lệ theo đúng định nghĩa đánh giá**, với
ảnh, điều kiện, nhiễu odometry và phụ thuộc thời gian **của chính query**. Nếu niềm tin sai, nơi thật còn nguyên sau phẫu
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

## 5. Điểm mới so với tài liệu (tóm tắt; Gate 12 trong `LITERATURE_GATE.md`)

- Null bản đồ (SelfCal, certified, CPC-SC; SAFEVPR'26 và Quantile Transfer dùng nhãn trên traversal hiệu chuẩn): null đến
  từ dữ liệu khác điều kiện. **CMS:** null là **can thiệp (do-operation) lên biểu diễn môi trường tại chính niềm tin của
  mô hình**, áp lên luồng triển khai — không cần nhãn, không cần traversal hiệu chuẩn.
- Tỷ lệ uniqueness của SeqSLAM / phép thử tỷ lệ không gian: là **điểm số**, không có hiệu chuẩn; CMS dùng phẫu thuật để
  **hiệu chuẩn** bất kỳ điểm số nào (ở đây chi phí tuyến TAO'26, vốn không có ngưỡng không nhãn).
- Knockoffs (Barber–Candès) tạo bản sao null giữ cấu trúc phụ thuộc của biến; CMS tạo bản sao null của **bằng chứng** giữ
  cấu trúc phụ thuộc thời gian của luồng, bằng cách xoá tín hiệu (nơi thật) khỏi bản đồ thay vì mô phỏng biến.
- Conformal trực tuyến / rolling conformal (Barber et al.): cần quan sát kết quả (nhãn) trên luồng; CMS tự sinh mẫu null.
