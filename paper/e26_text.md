# Báo cáo vòng 4: bảo đảm khi các frame phụ thuộc nhau, kiểm định tuyến hiệu chuẩn bằng bản đồ, so sánh TAO'26 / TRAIL'26 / VPR-auditing'26

*Branch `hmm-navigation-4`, 2026-10-31. Nhật ký: `RESEARCH_LOG.md` Entry 26. Lý thuyết: `paper/cpc_theory.md` §3e–§3f.
Novelty: `LITERATURE_GATE.md` Gate 11. Baseline tái hiện từ paper: `literature/BASELINES_2026.md`. Mọi số liệu tái tạo
được từ dataset public `nhatlong1103/hmm-navcache-v2` và `nhatlong1103/hmm-topk`.*

## 1. Câu hỏi của vòng này

1. Định lý khởi phát của CPC-SC dựa trên giả định các đoạn off-map hoán đổi được với đoạn null của bản đồ; các frame phụ
   thuộc nhau mạnh. Có bảo đảm nào đúng khi các frame phụ thuộc, mà không quá bảo thủ?
2. Phương pháp có đứng vững trước các công trình 2026 gần nhất (TAO'26, TRAIL'26, VPR-auditing'26) trên cùng giao thức?
3. Có cơ chế mới nào nâng điểm số mà vẫn không dùng nhãn?

## 2. Chẩn đoán: giả định hỏng ở đâu (nhãn chỉ dùng để chẩn đoán)

- p-value SelfCal của top-1 ở frame off-map **siêu đều ở phần trong** đoạn off-map: P(p ≤ 0.05) = 0.000–0.006 khi cách
  cả hai mép ≥ 50 frame (Boreas, CMU, 4S countryside).
- Vi phạm nằm ở **mép bản đồ** (~50 frame quanh mép): CMU MegaLoc P(p ≤ 0.05) = 0.12–0.16, vì ảnh ở mép bản đồ nhìn thấy cùng
  cảnh (top-1 cách 40–100 m): giới hạn phân giải của bằng chứng ngoại hình.
- Thống kê R neo odometry dưới đều ở **đoạn off-map dài** (Boreas CosPlace 0.19–0.23 ở độ sâu 0–100 frame), nơi null của bản
  đồ không có mẫu: null chỉ có **8–10 chunk dài 84–135 frame**. Số đơn vị hoán đổi được hiệu dụng ≈ 10.
- Kết luận: vấn đề không phải phụ thuộc *bên trong* một đoạn (định lý theo đoạn đã cho phép phụ thuộc tuỳ ý trong đoạn) mà
  là (i) trạng thái mang qua giữa các đoạn của một chuỗi có bộ nhớ vô hạn, (ii) tính đại diện của null (mép, đoạn dài, ít
  đơn vị), (iii) null cùng điều kiện ảnh.

## 3. Lý thuyết mới (chi tiết và chứng minh: `cpc_theory.md` §3e)

**Mệnh đề 5 (cái giá của phụ thuộc).** Nếu chỉ biết mỗi frame hợp lệ *biên* và phân phối chung tuỳ ý, thì mọi phép thử
mức α trên n frame, tại phân phối "n bản sao của một frame" (gần với thực tế: tự tương quan trễ 1 là 0.8–0.99), chỉ còn là
phép thử một frame. Mọi bảo đảm có **tích luỹ** bằng chứng đều cần một giả định về phụ thuộc.

**Định lý 4 (GPC: chứng chỉ đúng với mọi phụ thuộc).** Đặt cửa sổ odometry D = 6·excl lên traversal của bản đồ bằng
Procrustes 2-D (chỉ hình học, không ảnh); báo nếu một cách đặt có ≥ φK frame có top-1 trùng điểm đặt và p ≤ u\* =
αφ/min(1, Q_t), với Q_t là độ phủ hình học của các cách đặt. Khi đó P(báo sai tại t) ≤ α với **mọi** phân phối chung theo
thời gian (Markov trên số đếm + độ phủ), nên E[FL] ≤ α. Thực nghiệm: FL = 0 ở mọi nơi, nhưng recall chỉ 10–40 % của CPC-SC+CS
(xem bảng): đúng như Mệnh đề 5.

**Định lý 5 (khởi phát cửa sổ hữu hạn + bền vững hình học).** Khởi phát dùng thống kê chỉ phụ thuộc W = H frame cuối, hiệu
chuẩn bằng phân vị conformal theo đoạn trên null; dừng (và reset) khi chuỗi vị trí không còn nhất quán với odometry (CS:
độ lớn; SH: hình dạng, phần dư Procrustes ≤ excl/2 trên 3·excl). Dưới hoán đổi được **chỉ trong từng cửa sổ H frame** và
giả định không có đường bản đồ nối tiếp khớp hình dạng ở mép (NC): tỷ lệ khởi phát sai mỗi đoạn off-map ≤ α, **với mọi
phụ thuộc giữa các đoạn** (tuyến tính của kỳ vọng). Không cần e-value hợp lệ có điều kiện (Định lý 1, 3) và không cần đoạn
off-map dài hoán đổi được với đoạn null ngắn.

**Hệ quả (giới hạn của bản đồ).** Bảo đảm có điều kiện theo hiệu chuẩn (theo từng lần triển khai) cần ≳ log(1/δ)/α đơn
vị độc lập; bản đồ cho ~10, nên chỉ bảo đảm biên là khả thi: đúng với dao động theo run quan sát được.

## 4. Cơ chế mới: kiểm định tuyến hiệu chuẩn bằng bản đồ (`cpc_theory.md` §3f)

Chi phí TAO C_t: với 100 giả thuyết của frame t, neo truy ngược trên tuyến bản đồ theo quãng odometry của 20 frame gần nhất,
khớp cứng 2-D, phần dư Huber cắt 75 % + 2·(1 − similarity) dọc tuyến. Chúng tôi **chạy cùng thống kê trên null tự-phát-lại
của bản đồ** (ảnh của block giữ lại, che block của chính nó, odometry chính xác của bản đồ):

- **TAO-SC:** báo khi C_t dưới phân vị dưới conformal mức α của min-chi-phí theo đoạn của null: không nhãn, bộ nhớ hữu hạn,
  nên Định lý 5 áp dụng.
- **CPC-SC-T:** p-value hạng của C_t trong null làm thành phần thứ ba của chuỗi hiện diện CPC-SC,
  LR_t = ⅓(ẽ^top_t + (e^R_t)^{1/H} + (e^T_t)^{1/H}), κ hiệu chuẩn theo đoạn với cùng ba thành phần.

{{TABLES}}

## 6. Đọc kết quả

1. **Cải thiện đo được, không nhãn.** CPC-SC-T+CS (CPC-SC+CS thêm bằng chứng kiểm định tuyến) là cải thiện Pareto so với
   phương pháp vòng 3 tại điểm mặc định: recall cao hơn 7/7 dataset (+0.005…+0.032), segFAR như cũ (run tệ nhất ≤ 0.023
   < α), sai số bằng hoặc thấp hơn 7/7. CPC-SC-T+SH cho recall cao nhất (+0.009…+0.053 trên 7/7; NCLT +0.05, CMU +0.04,
   Nordland +0.05, old town +0.04), segFAR trung bình ≤ 0.010 (run tệ nhất 0.060 trên CMU), sai số thấp hơn trên 4/7; recall
   cao hơn Xu'21 (có nhãn) trên 5/7 (vòng 3: 3/7) với sai số thấp hơn 2.4–6×. Trên đường cong (FL ≤ 0.01) CPC-SC-T+SH
   hơn CPC-SC+CS 5/7, pAUC 6/7; hơn Xu'21 7/7, Claxton'24 và TAO'26 6/7 (trừ CMU).
2. **Chọn biến thể theo leave-one-dataset-out** (tiêu chí đăng ký trước: sai số chuẩn hoá thấp nhất với segFAR ≤ α trên các
   dataset khác) không phân biệt rõ: CPC-W+CS+SH được chọn 5/7 fold, regret 0–3.5 m; các biến thể khác nhau chủ yếu ở
   recall, không ở sai số. Họ CPC-SC-T được thiết kế sau khi xem CMU CosPlace seed 0–1 (tập giữ lại): đã ghi rõ.
3. **TAO'26** xếp hạng rất tốt trên CMU (recall 0.79 tại FL ≤ 0.01, ngang Claxton'24) nhưng ngưỡng 3σ của paper không chuyển
   được sang điều kiện khác (segFAR 0.24–0.74, sai số 38–188 m). Hiệu chuẩn không nhãn của chúng tôi (TAO-SC) giữ đúng đường
   cong của TAO nhưng điểm mặc định kém ổn định (CMU run tệ nhất 0.76): min-chi-phí theo đoạn với ~70 đoạn null dao động mạnh.
   Đưa chi phí TAO vào chuỗi hiện diện (CPC-SC-T) ổn định hơn nhiều.
4. **TRAIL'26** (MegaLoc, huấn luyện trên 6 dataset còn lại): vị trí đúng ≈ top-1 MegaLoc (khác ≤ 0.01, trừ Nordland −0.08);
   ngưỡng hiệu chuẩn bằng nhãn trên điều kiện dễ vi phạm nặng (segFAR 0.15–0.29); đường cong ở FL ≤ 0.01 thấp nhất trong các
   luật học được (Boreas 0.56, countryside 0.16).
5. **VPR-auditing'26** (Qwen2.5-VL-7B mở, offline): trên Boreas FAR 0.24–0.37 và nhận 30–36 % frame off-map, sai số điều hướng
   150 m; CPC-SC+CS trên cùng frame thắng cả theo metric S của paper với MegaLoc (0.840 so với 0.662). Mô hình mở 7B yếu hơn
   GPT-4.1 / Gemini trong paper (S 0.60 so với 0.76–0.78), nên đây là cận dưới của họ phương pháp VLM.
6. **Chỉ MegaLoc (descriptor mạnh nhất):** Claxton'24 (có nhãn) và TAO'26 xếp hạng tốt hơn CPC-SC-T+SH trên Boreas, NCLT, CMU,
   4S office; CPC-SC-T+SH thắng trên Nordland, old town, countryside. Lợi thế của phương pháp là tính hợp lệ không nhãn và độ
   bền trên mọi descriptor, không phải xếp hạng tốt nhất với descriptor mạnh.

## 7. Hạn chế và kết quả âm (đã xác minh)

1. **Điểm mặc định vẫn dè dặt** so với chính đường cong. Nguyên nhân đã đo: null của bản đồ là **cùng điều kiện ảnh**, cho
   bằng chứng mạnh hơn query khác điều kiện, nên κ cao. Hiệu chuẩn chung (hiện diện ∧ hình học) và bỏ sàn κ ≥ 0 chỉ thêm
   +0.003…+0.011 recall (`cpc_geo.scj_kappa`). Null khớp điều kiện (ví dụ pseudo-query từ traversal khác của bản đồ nhiều
   phiên) là việc mở.
2. **CMU với descriptor mạnh** vẫn là điểm yếu xếp hạng (mục 6.6). **Luật cửa sổ hữu hạn (CPC-W):** trung bình ngang CPC-SC+CS, nhưng run tệ nhất trên CMU có tỷ lệ khởi phát sai 0.07–0.11
   > α (bản đồ nhỏ, ~70 đoạn null): bảo đảm là biên theo hiệu chuẩn.
3. **GPC** hợp lệ dưới mọi phụ thuộc nhưng power thấp (recall 0.04–0.28 ở α = 0.05).
4. **Dừng hình dạng SH** chỉ là cải thiện nhỏ (pAUC tăng 6/7 dataset, recall tại FL ≤ 0.01 lẫn lộn).
5. **TRAIL'26** được tái hiện với biến thể transition d_g (bản CNN trên tương quan DINOv2 cục bộ cần ảnh mọi ứng viên);
   **VPR-auditing'26** chỉ chạy trên Boreas (2 descriptor, mỗi 5 frame) vì chi phí VLM (≈ 3 cặp/giây/GPU L4).
6. Hàng đợi GPU của Kaggle (L4 lẫn T4) tắc nhiều lần trong vòng này; các job nhẹ được chuyển sang T4/CPU theo quy tắc.

## 8. Novelty và mức sẵn sàng (Gate 11)

- Mới: chẩn đoán vị trí vi phạm giả định null; Mệnh đề 5 + Định lý 4 (cận dưới/trên của cái giá phụ thuộc); Định lý 5
  (tỷ lệ khởi phát sai ≤ α với phụ thuộc tuỳ ý giữa các đoạn); hiệu chuẩn không nhãn bằng null bản đồ cho kiểm định tuyến đa
  giả thuyết (TAO'26 không có ngưỡng không nhãn); so sánh trực tiếp đầu tiên với ba baseline 2026 trên giao thức bản đồ có lỗ.
- Không mới: các khối công cụ (conformal theo đoạn, e-value, Procrustes, Markov, kiểm nhất quán odometry).
- **Mức: A (RA-L/ICRA/IROS) vững hơn; A\* chưa** — còn thiếu null khớp điều kiện (điểm mặc định dè dặt), chạy robot thật
  vòng kín, và SafeVPR/VLM trên nhiều benchmark hơn.
