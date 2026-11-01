# Related work và định vị novelty (Entry 32, 2026-11-01)

*Tìm có hệ thống theo 6 nhánh (17 truy vấn web, chế độ standard/extended; danh sách truy vấn ở `LITERATURE_GATE.md` Gate 15).
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
| Game-theoretic / anytime-valid inference (arXiv 2210.01948) | Khung e-process | Nền lý thuyết |

## 4. Conformal dưới phụ thuộc thời gian

| Công trình | Làm gì | Quan hệ |
|---|---|---|
| Review split-conformal dưới β-mixing (Stocker et al. 2025) | Cận hữu hạn mẫu dưới phụ thuộc yếu | Ta tránh giả định mixing bằng hiệu chuẩn theo **đoạn** H frame (max trên đoạn) — mọi phụ thuộc trong đoạn |
| Block / guard-band conformal (arXiv 2606.30500; Bian et al. 2024 Markovian CP) | Tách khối hiệu chuẩn bằng khoảng đệm | Gần ý tưởng đoạn; ta thêm null sinh ra (không phải dữ liệu đã có nhãn) |
| Adaptive conformal anomaly detection cho chuỗi thời gian (ICLR 2026; RESS 2026 sliding calibration) | Giữ FAR khi dữ liệu trôi | Gần `[online]`; không có null off-map sinh ra |
| Adaptive conformal với particle filter dưới HMM (arXiv 2411.01558); conformalized Kalman filter (arXiv 2609.27506); online localized CP (arXiv 2605.05497) | Coverage cho trạng thái ẩn | Coverage vị trí, không phải phát hiện off-map với cận khởi phát sai |

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

**Việc còn thiếu trước khi nộp:** đọc toàn văn SafeVPR, E-detectors, Vovk 2006.02329, Lee & Pollefeys 2014; quét danh mục RA-L
2024–2026 và RSS 2025–2026 với từ khoá "self-calibrat*", "label-free", "integrity"; kiểm Bian et al. 2024 (Markovian CP).
