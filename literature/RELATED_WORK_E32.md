# Related work và định vị novelty (Entry 32, 2026-11-01)

*Tìm có hệ thống theo 6 nhánh (20 truy vấn web, chế độ standard/extended; danh sách truy vấn ở `LITERATURE_GATE.md` Gate 15).
Mỗi dòng: công trình — nó làm gì — cần nhãn? — bảo đảm? — xử lý phụ thuộc thời gian / off-map? — quan hệ với phương pháp của ta.
Đây là tìm qua máy tìm kiếm, **chưa** thay được việc đọc kỹ proceedings ICRA/IROS/RSS/RA-L/T-RO 2024–2026 trước khi nộp.*

## 1. Kiểm tra tính toàn vẹn (integrity) của VPR / định vị thị giác

| Công trình | Làm gì | Nhãn | Bảo đảm | Off-map / phụ thuộc | Quan hệ |
|---|---|---|---|---|---|
| Carson, Ford, Milford, RA-L 2022 "Predicting to improve" (doi 10.1109/LRA.2022.3191205) | SVM dự đoán từng frame VPR có trong dung sai không | Có (theo môi trường) | Không | Không | Tiền thân của Claxton'24 |
| Carson et al., ICRA 2023 (unsupervised quality prediction, arXiv 2307.01464) | Dự đoán không giám sát match trong dung sai + trọng số chuỗi | Không | Không | Một phần (chuỗi) | Gần nhất về "không nhãn", nhưng không có bảo đảm FAR |
| Claxton et al., 2024 (arXiv 2407.08162) | MLP integrity monitor | Có | Không (tác giả tự nêu) | Không | **Baseline Claxton'24** |
| Hussaini, Fischer, Milford, IROS 2025 (arXiv 2503.06840) | Dự đoán khi nào sequence matching có ích (SMR) | Có | Không | Chuỗi | Bổ trợ; có thể làm baseline phụ |
| SafeVPR 2026 (arXiv 2605.28048) | Xác minh conformal (Mondrian LTT) cho sequence VPR | Có (tập hiệu chuẩn) | Có, khi hoán đổi được | Tác giả nêu: vỡ khi lệch điều kiện | **Baseline SafeVPR'26**; ta bỏ nhãn bằng null phản thực |
| SwPC 2025 (arXiv 2501.04947) | Conformal cho VPR ngôn ngữ–thị giác trong nhà | Có | Coverage | Không | Xa |
| Audit VPR cho smart city, Smart Cities 2025 (doi 10.3390/smartcities9100163) | Đánh giá VPR như dịch vụ định vị | — | Không | — | Trích dẫn Claxton/SafeVPR là chuẩn an toàn |
| Zhu et al., NAVI 2022 "Integrity of Visual Navigation" | Khảo sát integrity thị giác | — | — | — | Khung khái niệm (integrity risk) |
| Gupta & Gao, NAVI 2021 (arXiv 2101.06379); Li & Waslander 2019 (arXiv 1909.08537); Zheng et al. T-ITS 2025 (arXiv 2211.15127) | Protection level cho định vị camera + bản đồ 3-D | Mô hình lỗi | Có (mô hình) | Không | Hướng PL; cổng +NGR của ta là phiên bản rời rạc thô |

## 2. Off-map / nơi mới / open-set

| Công trình | Làm gì | Nhãn | Bảo đảm | Quan hệ |
|---|---|---|---|---|
| Xu et al., RA-L 2021 (arXiv 2107.07707, 2105.03091) | Bộ lọc topometric với trạng thái **off-map** | Ngưỡng/nhiệt độ chỉnh tay hoặc theo nhãn | Không | **Baseline Xu'21**; ta hiệu chuẩn trạng thái OFF bằng null phản thực (Mệnh đề 13) |
| Multi-Process Fusion (arXiv 1903.03305) | HMM qua chuỗi ảnh, điểm chất lượng phân biệt cảnh quen / mới | Không | Không | Ý tưởng "novel scene" không hiệu chuẩn |
| HMM place recognition LiDAR, Sensors 2024 | HMM nhiều frame trên bản đồ trước | — | Không | Không xử lý ngoài bản đồ |
| Open-set recognition (Bendale & Boult 2016; PROSER CVPR 2021; calibration OSR 2022, arXiv 2205.07160) | Từ chối lớp lạ bằng ngưỡng / EVT | Có | Không | Tác giả OSR nêu hiệu chuẩn open-set "chưa được nghiên cứu" |
| Lee & Pollefeys, ICRA 2014 | Ngưỡng xác minh vòng lặp không nhãn: hỗn hợp số inlier | Không | Không | Gần nhất về **ngưỡng không nhãn**; tác giả nêu suy biến khi ít/không có vòng lặp — đúng trường hợp null phản thực xử lý |
| Self-supervised domain calibration (arXiv 2203.04446) | Gán nhãn match bằng pose graph SLAM | Tự giám sát | Không | Cần SLAM nhất quán |
| ROVER (arXiv 2508.13488) | Loại vòng lặp sai bằng quỹ đạo lịch sử | Không | Không | Tương tự +SH / +NGR (dùng odometry) |

## 3. Phát hiện thay đổi tuần tự với e-value / conformal

| Công trình | Làm gì | Quan hệ |
|---|---|---|
| Shin, Ramdas, Rinaldo, "E-detectors" (arXiv 2203.03532, NEJSDS 2023) | Phát hiện thay đổi phi tham số từ tổng e-process, cận ARL không tiệm cận; tổng quát hoá Shiryaev–Roberts / CUSUM | Nền của chuỗi hiện diện (Định lý 1: chặn Shiryaev–Roberts). **Cần lớp trước/sau thay đổi định trước**, ta thay bằng null sinh từ luồng |
| Vovk, conformal e-prediction cho change detection (arXiv 2006.02329) | Conformal Shiryaev–Roberts / CUSUM phát hiện vi phạm IID | Gần về hình thức; null là hoán đổi của chính dữ liệu, không phải null "off-map" được tạo ra |
| Multi-stream e-detectors (arXiv 2501.04130) | Nhiều luồng | Có thể dùng cho nhiều robot |
| E-value monitor cho định vị particle filter (arXiv 2604.26479, 2026) | Martingale kiểm tra tự tin quá mức theo hướng trôi, báo khi vượt 1/α | **Gần nhất về e-process cho định vị robot**; kiểm hiệu chuẩn của bộ lọc, không kiểm "đang trên bản đồ" và không có null không nhãn |
| E-process cho lỗi bám đối tượng (arXiv 2602.12983) | Phát hiện tracker trôi sang mục tiêu sai | Tương tự ở mức hình thức |
| Duenas Arana et al. 2019 (recursive integrity monitoring, landmark EKF) | Kiểm χ² tuần tự trên innovation | Baseline cổ điển cho cổng +DRG / +NGR |
| Kim et al. 2018 (Sensors, self-diagnosis of localization status) | Phân loại thành công/thất bại định vị LiDAR | Có nhãn |
| Game-theoretic / anytime-valid inference (arXiv 2210.01948) | Khung e-process | Nền lý thuyết |

## 4. Conformal dưới phụ thuộc thời gian

| Công trình | Làm gì | Quan hệ |
|---|---|---|
| Review split-conformal dưới β-mixing (Stocker et al. 2025) | Cận hữu hạn mẫu dưới phụ thuộc yếu | Ta tránh giả định mixing bằng hiệu chuẩn theo **đoạn** H frame (max trên đoạn) — mọi phụ thuộc trong đoạn |
| Block / guard-band conformal (arXiv 2606.30500; Bian et al. 2024 Markovian CP) | Tách khối hiệu chuẩn bằng khoảng đệm | Gần ý tưởng đoạn; ta thêm null sinh ra (không phải dữ liệu đã có nhãn) |
| Adaptive conformal anomaly detection cho chuỗi thời gian (ICLR 2026; RESS 2026 sliding calibration) | Giữ FAR khi dữ liệu trôi | Gần `[online]`; không có null off-map sinh ra |
| Adaptive conformal với particle filter dưới HMM (arXiv 2411.01558); conformalized Kalman filter (arXiv 2609.27506); online localized CP (arXiv 2605.05497) | Coverage cho trạng thái ẩn | Coverage vị trí, không phải phát hiện off-map với cận khởi phát sai |
| Zheng & Proutière, ICML 2024 "Conformal predictions under Markovian data" (arXiv 2407.15277) | Khoảng cách coverage ~ √(t_mix ln n / n); K-split CP (tỉa tập hiệu chuẩn) | Ta hiệu chuẩn trên **max theo đoạn**, không cần t_mix; nên so sánh trong bài |
| Nettasinghe et al. 2024 (PNNL) — conformal cho HMM qua định lý de Finetti cho chuỗi Markov | Khối hoán đổi được trong HMM | Gần về "hoán đổi theo khối"; không có null off-map sinh ra |

## 5. Ngưỡng / hiệu chuẩn VPR không nhãn khác

| Công trình | Làm gì | Quan hệ |
|---|---|---|
| Threshold transfer theo phân vị (arXiv 2602.04401) | Chọn ngưỡng từ traversal hiệu chuẩn có tương ứng | Cần tương ứng (nhãn) |
| KappaPlace (arXiv 2605.19435), training-free calibration (arXiv 2609.25937) | Độ bất định / hiệu chuẩn hình học retrieval | Điểm tin cậy, không có bảo đảm FAR |

## 6. Định vị novelty (kết luận Gate 15)

**Không tìm thấy** (trong các truy vấn đã làm) công trình nào:
1. tạo null của bằng chứng "đang trên bản đồ" bằng **phẫu thuật bản đồ quanh niềm tin của chính hệ thống** trên luồng triển khai
   (gần nhất: Lee & Pollefeys 2014 — hỗn hợp không nhãn, không có null; SafeVPR — conformal có nhãn);
2. cho cận **khởi phát sai theo đoạn** không nhãn, mọi phụ thuộc trong đoạn, với tự-nhiễm định lượng α(n+1)/(πn+1)
   (gần nhất: e-detectors — cần lớp trước/sau định trước; conformal dưới mixing — cần giả định mixing);
3. hiệu chuẩn **trạng thái off-map của HMM** sao cho biên OFF có bảo đảm (gần nhất: Xu'21 — trạng thái off-map chỉnh tay/nhãn).

**Đã có (không tuyên bố):** HMM với trạng thái off-map (Xu'21); conformal accept/reject cho VPR (SafeVPR); e-detector /
Shiryaev–Roberts (Shin et al.); cổng innovation / protection level (GNSS RAIM, Gupta & Gao); dự đoán integrity có nhãn (Carson,
Claxton). Bài viết nên đặt đóng góp là **(1)–(3)**, phần còn lại là thành phần đã biết.

**Việc còn thiếu trước khi nộp:** đọc toàn văn SafeVPR, E-detectors, Vovk 2006.02329, Lee & Pollefeys 2014, arXiv 2604.26479
(e-value monitor cho particle filter — cần so sánh trực tiếp), Zheng & Proutière 2024; quét danh mục RA-L
2024–2026 và RSS 2025–2026 với từ khoá "self-calibrat*", "label-free", "integrity"; kiểm Bian et al. 2024 (Markovian CP).

## 7. Đối thủ SOTA — đọc toàn văn (Entry 33, 2026-11-01)

*Đọc PDF (trích bằng `pdftotext` khi PDF > 10 MB) hoặc bản HTML của arXiv; không đọc code. Mục đích: còn phương pháp nào cạnh
tranh trực tiếp với phương pháp đề xuất (quyết định báo fix theo từng frame, không nhãn, bản đồ có lỗ, có odometry)?*

| Công trình | Đọc gì | Quyết định | Nhãn | Bảo đảm | Off-map | Chuỗi / odometry | Dataset | Kết luận cho ta |
|---|---|---|---|---|---|---|---|---|
| **SafeVPR**, arXiv 2605.28048 (05/2026) | HTML đến §V-B + tóm tắt | nhận/loại top-1 của **mỗi chuỗi 10 frame** | **Có** (điều kiện khác, Mondrian LTT, B = 5 bin) | FDR ≤ α với xác suất 1 − δ **khi hoán đổi được**; tác giả: "không tuyên bố bảo đảm dưới lệch điều kiện" | Không | chuỗi (khớp chéo), không odometry | Oxford RobotCar (4 traversal), NCLT (3), St Lucia (1 cặp) | Đã là baseline (SafeVPR'26). Số của họ: α = 0.10, 23/23 setup hợp lệ, TPR 0.75 |
| **Through the Lens of Doubt** (Miller et al.), arXiv 2510.13464 (10/2025) | HTML đầy đủ | điểm bất định (RS = TB s_i/s_1, SD = s_median/s_1, SU = ½(RS + SD)) | Không (điểm); **không có ngưỡng** | Không | Không | ảnh đơn | Pitts250k, St Lucia, Nordland, AmsterTime, Eynsham, Tokyo 24/7 | **Thống kê mạnh nhất trong nhóm rẻ** (AUC-PR 0.92 so với SUE 0.71, L2 0.83; GV SuperPoint 0.95 nhưng 84 ms). Thêm làm baseline (ngưỡng hiệu chuẩn có nhãn) **và** thử làm thống kê bên trong CMS |
| **SUE** (Zaffar et al., CVPR 2024) | PDF CVF đầy đủ | độ phân tán không gian của top-10 vị trí, trọng số e^{−λd} | Không (λ chỉnh trên Pittsburgh) | Không (AUC-PR, không ngưỡng) | Không | ảnh đơn | Pitts, SF, St Lucia, Eynsham, MSLS, Nordland | Thống kê; AUC-PR TB 0.77 (Nordland 0.26). Thêm làm baseline thống kê |
| **To Match or Not to Match** (Sferrazza et al.), arXiv 2504.06116 | HTML §1–4.2 + bảng 3 | −số inlier RANSAC với top-1 | Không (logistic hiệu chuẩn trên MSLS Val) | Không | Không | ảnh đơn | 10 bộ (MSLS, Pitts30k, SF-XL, SVOX, Tokyo…) | Cần ảnh + matcher; hơn L2 chỉ ≈ 1.6 AUPRC — không ưu tiên |
| **Carson, Ford, Milford, ICRA 2023** (arXiv 2307.01464) | HTML | nhận match khi \|argmax gradient − argmin khoảng cách\| ≤ 1 (theo thứ tự tuyến của bản đồ) | **Không**, không chỉnh | Không | Không | chuỗi có trọng số, không odometry | Gardens Point, Nordland, 4Seasons office, Oxford RobotCar | **Luật không nhãn**, thêm làm baseline (cần vector khoảng cách đầy đủ theo thứ tự bản đồ) |
| **SMR** (Hussaini, Fischer, Milford, IROS 2025) | HTML | MLP 4 lớp: khớp chuỗi có giúp không | Có, mỗi dataset | Không | Không | chuỗi (SeqSLAM), không odometry | Nordland, Oxford RobotCar, SFU Mountain | Có nhãn và huấn luyện lại mỗi dataset; không xét off-map — không thêm |
| **Valentin 2026** "Recipes for calibration checks", arXiv 2604.26479 | PDF (pdftotext) | kiểm độ hiệu chuẩn của particle filter (e-value một phía, Ville) | **Cần ground truth** | type-I (anytime) cho kiểm hiệu chuẩn | Không | mô phỏng 2-D có beacon | — | Không phải đối thủ: kiểm độ tin của bộ lọc bằng nhãn |

**Kết luận.** Không có phương pháp nào trong nhóm đọc được giải đúng bài toán của ta (quyết định từng frame, không nhãn, bản đồ có
lỗ / off-map, có bảo đảm). Đối thủ cần đưa thêm vào thí nghiệm: **SU'25** và **SUE'24** (thống kê mạnh, ngưỡng hiệu chuẩn có nhãn
theo cùng giao thức các baseline có nhãn), **Carson'23** (luật không nhãn). Hướng cải tiến rút ra: CMS hiệu chuẩn được **bất kỳ**
thống kê nào ⇒ thử SU làm thành phần thứ ba của e-value (không nhãn, có bảo đảm). Dataset uy tín dùng chung với SafeVPR:
Oxford RobotCar, NCLT (đã có), St Lucia.
