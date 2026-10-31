# Báo cáo: "Phương pháp chỉ đang thận trọng hơn?" — chẩn đoán, phương pháp CPC-SC+CS và đánh giá theo đường cong vận hành

*Branch `hmm-navigation-3`, 2026-10-31. Nhật ký chi tiết: `RESEARCH_LOG.md` Entry 25. Lý thuyết: `paper/cpc_theory.md` §3d.
Mã: `analysis/cpc_sc.py` (luật đề xuất), `oc_curves.py`, `oc_matched.py`, `lodo_select.py`, `recall_diag.py`.*

## 1. Câu hỏi phản biện

Phương pháp trước (CPC-HMM +TCEmin, Entry 24) có sai số điều hướng thấp nhưng recall cũng thấp. Phản biện: "mô hình chỉ
thận trọng hơn, nên ít sai nhưng cũng bắt ít mẫu đúng; không có bằng chứng nó tốt hơn". Câu hỏi đúng về mặt phương pháp
luận: mỗi luật chấp nhận là "báo khi điểm s_t vượt ngưỡng θ"; điểm mặc định chỉ là **một điểm** trên đường cong
(recall(θ), FL(θ), segFAR(θ)). Luật tốt hơn phải có đường cong **cao hơn** (nhiều fix đúng hơn ở cùng mức báo sai), không
chỉ có θ cao hơn.

## 2. Chẩn đoán (kết luận: phản biện đúng một phần với phương pháp cũ)

- **Recall mất ở chuỗi hiện diện, không ở chuỗi vị trí.** Với descriptor yếu, chuỗi vị trí vẫn đúng chỗ phần lớn thời
  gian nhưng chuỗi hiện diện không bật: Boreas NetVLAD, chuỗi vị trí đúng 85 % frame on-map, chỉ báo 30 %; Boreas DINOv2,
  83 % frame on-map nằm trong các đoạn **không bao giờ được báo** dù chuỗi vị trí đúng 86 % ở đó.
- **Phép min với TCE là nguyên nhân chính.** NCLT DINOv2: recall 0.16 (TCEmin) so với 0.50 (CPC-HMM không TCE).
- **So với CPC-HMM, TCEmin đúng là "chỉ thận trọng hơn"**: ở cùng recall, TCEmin có sai số cao hơn (NCLT NetVLAD 12.9 so
  với 6.3 m) và pAUC thấp hơn (0.490 so với 0.525).
- **Nhưng CPC-HMM không TCE thì vi phạm segFAR** (0.04–0.07 trên 4/7 dataset), và chẩn đoán cho thấy phần vi phạm đến từ
  báo cáo **kéo dài**: chuỗi vị trí không có trạng thái off-map, nên khi robot rời bản đồ, MAP bị buộc kẹt ở mép bản đồ hoặc
  nhảy sang nơi giống, trong khi chuỗi hiện diện vẫn tin là on. Phần **khởi phát** sai thì kiểm soát được (tỷ lệ đoạn có
  khởi phát sai 0.010–0.041 ≤ α khi hiệu chuẩn theo đoạn).

## 3. Phương pháp đề xuất: CPC-SC+CS (tổng quát, không nhãn, không tune theo dataset)

Ký hiệu: m_t nơi được báo (MAP của chuỗi vị trí), o_t odometry, p_t p-value SelfCal của top-1, p^R_t p-value của thống kê
neo odometry R_t, excl dung sai định vị, H độ dài đoạn, α mức FAR theo đoạn.

1. **Chuỗi hiện diện CPC-HMM** (giữ xếp hạng tốt, bỏ TCE):
   LR_t = ½ (ẽ^top_t + (e^R_t)^{1/H}),  e = a·p^{a−1} (a fit Beta-EM theo traversal, không nhãn), ẽ^top có cổng top-1 = MAP;
   log-odds ℓ_t = logit[(1−p_out)·P(on_{t−1}) + p_in·P(off_{t−1})] + log LR_t, p_in = p_out = 0.01.
2. **Ngưỡng khởi phát hiệu chuẩn theo đoạn (SC):** κ = phân vị conformal (1−α) của max ℓ trên các đoạn H frame của null
   tự-phát-lại của bản đồ (block giữ lại, chuỗi khởi đầu ở odds 1). Báo từ frame ℓ_t > κ, duy trì khi ℓ_t > 0.
   *Định lý (khởi phát):* nếu các đoạn off-map của query hoán đổi được với đoạn null thì một đoạn được đi vào khi chưa báo
   có khởi phát báo với xác suất ≤ α, với mọi phụ thuộc trong đoạn (log-odds đơn điệu theo odds ban đầu).
3. **Quy tắc dừng nhất quán odometry (CS):** dừng báo ở t nếu tồn tại độ trễ k với quãng odometry ≤ 3·excl sao cho
   | ‖m_t − m_{t−k}‖ − ‖o_t − o_{t−k}‖ | > excl  (chỉ độ lớn, bất biến với trôi hướng).
   *Bổ đề 7:* CS chỉ bỏ bớt báo cáo nên giữ các bảo đảm dạng "có báo cáo trong đoạn" (segFAR, FL) của luật gốc (không áp
   dụng cho ARL₀ đếm theo khởi phát). *Mệnh đề 4:* nếu MAP kẹt trong bán kính δ quanh
   nơi rời bản đồ và excl + in_d + ε + δ < off_d thì không có báo cáo ở frame off-map (ε: sai số độ lớn odometry trên 3·excl).

Mọi hằng số tính theo đơn vị của bài toán (excl, H, α); cùng một giá trị cho 7 dataset, 6 descriptor. Kiểm tra nhất quán với
odometry đã có tiền lệ (RRR, Latif et al. 2013; SeqSLAM), nên CS không mới tự thân; phần đóng góp là chẩn đoán đúng nguồn
vi phạm, vai trò trong khung có bảo đảm, và bằng chứng đường cong.

## 4. Giao thức đánh giá (chống thiên lệch chọn lựa)

- 7 dataset (Boreas, NCLT, CMU, Nordland, 4Seasons office/old town/countryside), 6 descriptor; bản đồ khuyết 30 % block
  (NCLT: off-map tự nhiên). Điểm mặc định: 10 seed; đường cong và so khớp: seed 0–2. Độ bền: bản đồ khuyết 10 % và 50 %
  với **cùng** hằng số.
- **Đăng ký trước** (ghi vào nhật ký trước khi xem): Boreas + NCLT là tập phát triển; 5 tập còn lại là tập giữ lại.
- **Chọn leave-one-dataset-out** trong 15 biến thể không nhãn: CPC-SC+CS được chọn ở 6/7 fold (CMU: CPC-HMM+CS), regret
  0–3.5 m (phương pháp cũ: tới 30 m).
- **Đường cong vận hành**: quét ngưỡng của từng luật (baseline dùng nhãn: Xu'21, Claxton'24, SafeVPR, ngưỡng max-sim;
  không nhãn: certified, per-frame SelfCal, các biến thể CPC); nhãn chỉ dùng để đánh giá. **So khớp chính xác**: đặt luật
  đề xuất tại đúng FL / recall của điểm mặc định từng baseline, chạy Kalman thật tại ngưỡng đó.

## 5. Kết quả

{{TABLES}}

## 6. Trả lời phản biện

1. **Không chỉ thận trọng hơn.** Ở cùng mức báo sai FL ≤ 1 %, CPC-SC+CS bắt được nhiều fix đúng hơn Xu'21 trên 7/7
   dataset và hơn Claxton'24 (dùng nhãn) trên 6/7; đặt tại đúng FL của Xu'21, recall cao hơn trên 5/7 và sai số thấp hơn
   trên 6/7. Ở điểm mặc định (10 seed, 366 run), so với phương pháp cũ (TCEmin): recall cao hơn trên 5/7 (NCLT +0.05,
   Nordland +0.07, countryside +0.09, office/old town +0.01), bằng trên Boreas, thấp hơn 0.02 trên CMU; segFAR thấp hơn
   hoặc bằng trên 7/7; sai số thấp hơn trên 6/7 (NCLT +0.9 m). segFAR tệ nhất trong **từng run** là 0.021 (mọi run dưới
   α = 0.05), trong khi TCEmin tới 0.171 và Xu'21 tới 1.0; so với Xu'21 sai số thấp hơn 1.5–6.2× trên 7/7.
2. **Tổng quát, không tune theo dataset:** cùng một bộ hằng số (đơn vị excl, H, α) cho 7 dataset, 6 descriptor, 3 tỷ lệ
   lỗ bản đồ (10/30/50 %) và off-map tự nhiên (NCLT); segFAR trung bình ≤ 0.012 ở mọi cấu hình; chọn leave-one-dataset-out
   ổn định (6/7 fold).
3. **Phản biện đúng một phần với phương pháp cũ**: so với CPC-HMM, TCEmin là điểm thận trọng hơn trên một đường cong kém
   hơn; phép min với TCE đã được thay bằng hiệu chuẩn ngưỡng khởi phát và quy tắc dừng CS.

## 7. Hạn chế (giữ nguyên, không che)

- **Ở điểm mặc định, recall vẫn thấp hơn Xu'21 trên 4/7 dataset** (Nordland −0.10, Boreas/old town −0.02, office −0.01),
  dù sai số thấp hơn 1.5–6.2× và Xu'21 vi phạm segFAR; ở cùng FL thì đường cong của đề xuất cao hơn (mục 6).
- **CMU (descriptor mạnh, dữ liệu dễ):** Claxton'24 và cả điểm max-sim thô xếp hạng tốt hơn mọi chuỗi hiện diện; ở FL
  của Xu'21 recall của đề xuất thấp hơn 0.04.
- **Vùng FL cao (3–8 %):** Claxton'24 có recall cao hơn trên 5/7 dataset — nhưng ở đó segFAR của nó 0.11–0.27.
- **NCLT:** CS xoá frame đúng; CPC-HMM không CS có đường cong tốt nhất; sai số điều hướng nhạy với vài fix sai do EKF có
  trạng thái hướng.
- **Điểm mặc định còn dè dặt so với chính đường cong của nó** (countryside: recall 0.30 ở FL 0.000, 0.55 ở FL 0.01).
  Hiệu chuẩn chung (hiện diện ∧ CS) trên null tự-phát-lại không nới được ngưỡng vì null qua CS nhiều gấp 2.6× off-map thật.
- **α nhỏ cần đủ đoạn null:** α = 0.01 cần ≥ 99 đoạn; CMU/4S office có ít hơn nên κ = ∞ (recall 0).
- Đã thử và loại (kết quả âm, chi tiết trong nhật ký): e-value hai nhóm (hedge), trung bình e-process, TCE trên một thành
  phần, hysteresis TCEmin/CPC, CPC-SC không CS, W-CPC (bộ nhớ hữu hạn), PCR (cổng dự đoán kiểu IPDA: tự xác nhận, LR ≈ 1.5),
  cổng độ tin chuỗi vị trí, hiệu chuẩn chung CS.
