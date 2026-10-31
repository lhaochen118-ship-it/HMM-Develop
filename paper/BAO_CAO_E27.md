# Báo cáo vòng 5: null khớp điều kiện, xếp hạng với descriptor mạnh, SafeVPR / VPR-auditing ngoài Boreas

*Branch `hmm-navigation-4`, 2026-10-31. Nhật ký `RESEARCH_LOG.md` Entry 27 (đăng ký trước ở đầu entry). Vòng trước:
`paper/BAO_CAO_E26.pdf`. Dataset public mới của `nhatlong1103`: `hmm-xnull` (null chéo traversal Boreas), `hmm-route-cache`
(chi phí tuyến theo frame của mọi run), `hmm-image-baselines` (điểm SafeVPR và phán quyết VLM).*

## 1. Ba việc của vòng này

1. **Null khớp điều kiện (Boreas).** 17 traversal Boreas không phải bản đồ cũng không phải query (ngày, thời tiết, ánh sáng
   khác) được dùng như dữ liệu phía bản đồ: mỗi frame thành pseudo-query leave-block-out (che block gần nhất, chỉ giữ khi cách
   bản đồ còn lại > off_d), với odometry bánh xe + gyro thật của chính traversal đó; cùng phép thử SelfCal nửa bản đồ, cùng
   null của R, top-100 khi đã che block (cho chi phí tuyến). Mỗi seed có **~80k frame giả-off-map trong 300–360 chunk**
   (null bản đồ: ~10 chunk). Ngưỡng khởi phát κ được hiệu chuẩn trên các chunk này thay cho null tự-phát-lại.
2. **Xếp hạng với descriptor mạnh (CMU).** Công suất của thành phần tuyến trong CPC-SC-T: (e^T)^{1/H} (vòng 4) so với
   (e^T)^{1/2} và (e^T)^1 (đăng ký trước); hai cách kết hợp thăm dò, thiết kế sau khi xem CMU: min(ẽ^top, e^T) (Bổ đề 6) và
   chỉ e^T. Mọi biến thể vẫn được hiệu chuẩn theo đoạn trên null, nên tính hợp lệ không đổi.
3. **SafeVPR'26 và VPR-auditing'26 trên NCLT và 4Seasons** (trước đây chỉ Boreas), cùng giao thức; resolver ảnh chung
   `analysis/vpr_images.py`.

## 2. Tối ưu tính toán

- GPU: SafeVPR chạy 4 dataset song song, mỗi GPU L4 một dataset (DINOv2-B fp16, token bản đồ nằm trên GPU: tới 4.5 GB);
  VLM 4 tiến trình × 1 bản Qwen2.5-VL-7B bf16/GPU, batch 16, một lượt forward mỗi cặp; null chéo traversal dùng backend torch
  của SelfCal trên GPU, mỗi job một descriptor × 5 seed (nạp 17 traversal một lần, đọc song song 16 luồng).
- CPU: 78–96 kernel CPU song song (5 phiên/acc, dồn hết slot của một acc trước); cache chi phí tuyến (`hmm-route-cache`)
  tránh tính lại TAO cho mọi lô sau (Boreas: ~10 phút/run).
- Lịch: dồn theo thứ tự acc (2 phiên GPU + 5 phiên CPU của một acc rồi mới sang acc tiếp); hàng đợi L4 vẫn tắc nhiều lần
  (huỷ/đẩy lại tự động; acc chưa nhận luật L4 bị bỏ qua tự động).

## 4. Kết quả

### Bảng 1. Điểm mặc định: recall / segFAR trung bình / segFAR run tệ nhất / sai số (m); 10 seed (NCLT 1); SafeVPR seed 0–2

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.684 / 0.043 / 0.567 / 25.3 | 0.526 / 0.021 / 0.065 / 13.7 | 0.686 / 0.227 / 1.000 / 18.1 | 0.740 / 0.038 / 0.113 / 59.3 | 0.724 / 0.215 / 0.997 / 21.2 | 0.625 / 0.101 / 1.000 / 70.9 | 0.254 / 0.088 / 0.983 / 81.0 |
| Claxton'24 (nhãn) | 0.741 / 0.116 / 0.674 / 36.9 | 0.660 / 0.203 / 0.428 / 32.3 | 0.874 / 0.167 / 0.818 / 14.4 | 0.520 / 0.262 / 0.442 / 88.0 | 0.799 / 0.156 / 0.589 / 18.9 | 0.724 / 0.165 / 0.544 / 89.8 | 0.598 / 0.215 / 0.493 / 43.2 |
| SafeVPR'26 (nhãn) | – | 0.324 / 0.038 / 0.225 / 14.7 | – | – | 0.732 / 0.041 / 0.221 / 11.6 | 0.660 / 0.021 / 0.053 / 31.9 | 0.111 / 0.004 / 0.034 / 74.6 |
| TAO'26 (nhãn) | 0.801 / 0.240 / 0.830 / 46.2 | 0.756 / 0.707 / 1.000 / 57.6 | 0.930 / 0.370 / 1.000 / 38.4 | 0.805 / 0.579 / 1.000 / 187.9 | 0.935 / 0.740 / 1.000 / 54.0 | 0.839 / 0.557 / 1.000 / 168.4 | 0.769 / 0.732 / 1.000 / 95.1 |
| CPC-SC+CS (vòng 3) | 0.661 / 0.001 / 0.021 / 5.1 | 0.537 / 0.000 / 0.000 / 4.6 | 0.731 / 0.002 / 0.019 / 3.8 | 0.644 / 0.000 / 0.003 / 9.6 | 0.709 / 0.000 / 0.000 / 11.6 | 0.600 / 0.000 / 0.010 / 30.8 | 0.297 / 0.000 / 0.007 / 53.1 |
| CPC-SC-T+SH (vòng 4) | 0.670 / 0.002 / 0.028 / 5.6 | 0.590 / 0.001 / 0.003 / 4.8 | 0.773 / 0.010 / 0.060 / 4.4 | 0.692 / 0.000 / 0.006 / 9.5 | 0.739 / 0.000 / 0.003 / 11.3 | 0.642 / 0.007 / 0.034 / 29.7 | 0.324 / 0.000 / 0.007 / 51.0 |
| **CPC-SC-T½+SH** | 0.666 / 0.002 / 0.023 / 5.7 | 0.588 / 0.001 / 0.003 / 4.9 | 0.789 / 0.018 / 0.188 / 5.2 | 0.713 / 0.001 / 0.010 / 9.5 | 0.738 / 0.000 / 0.003 / 11.4 | 0.640 / 0.007 / 0.034 / 29.8 | 0.334 / 0.000 / 0.015 / 51.3 |
| CPC-SC-T½+CS | 0.662 / 0.001 / 0.020 / 5.1 | 0.550 / 0.000 / 0.000 / 4.3 | 0.762 / 0.004 / 0.046 / 4.3 | 0.691 / 0.000 / 0.006 / 9.5 | 0.718 / 0.000 / 0.000 / 11.7 | 0.613 / 0.001 / 0.012 / 30.5 | 0.320 / 0.000 / 0.007 / 52.9 |
| CPC-SC-Tmin+SH (thăm dò) | 0.640 / 0.000 / 0.006 / 5.2 | 0.531 / 0.000 / 0.000 / 4.8 | 0.731 / 0.006 / 0.056 / 3.7 | 0.614 / 0.000 / 0.003 / 10.4 | 0.698 / 0.000 / 0.003 / 12.3 | 0.595 / 0.003 / 0.028 / 33.1 | 0.289 / 0.000 / 0.000 / 53.8 |
| CPC-SC-Tonly+SH (thăm dò) | 0.600 / 0.001 / 0.010 / 6.5 | 0.510 / 0.007 / 0.036 / 20.6 | 0.693 / 0.017 / 0.192 / 5.6 | 0.581 / 0.005 / 0.025 / 15.2 | 0.667 / 0.000 / 0.005 / 15.4 | 0.587 / 0.005 / 0.028 / 33.8 | 0.147 / 0.000 / 0.011 / 91.1 |
| Oracle | 0.88 / – / – / 2.1 | 0.72 / – / – / 2.2 | 0.94 / – / – / 3.0 | 0.67 / – / – / 4.8 | 0.91 / – / – / 8.3 | 0.84 / – / – / 19.4 | 0.73 / – / – / 16.5 |

### Bảng 2. Đường cong: recall tại FL ≤ 0.01 / pAUC (FL ∈ [0, 0.05]); seed 0–2

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.562 / 0.602 | 0.526 / 0.563 | 0.592 / 0.638 | 0.624 / 0.688 | 0.537 / 0.599 | 0.555 / 0.615 | 0.181 / 0.237 |
| Claxton'24 (nhãn) | 0.687 / 0.706 | 0.574 / 0.592 | 0.793 / 0.812 | 0.439 / 0.466 | 0.749 / 0.765 | 0.644 / 0.672 | 0.420 / 0.470 |
| SafeVPR'26 (nhãn) | 0.486 / 0.551 | 0.397 / 0.444 | – | – | 0.757 / 0.786 | 0.698 / 0.733 | 0.252 / 0.329 |
| TAO'26 (nhãn) | 0.640 / 0.659 | 0.520 / 0.543 | 0.792 / 0.806 | 0.418 / 0.493 | 0.683 / 0.705 | 0.631 / 0.654 | 0.239 / 0.296 |
| CPC-SC+CS (vòng 3) | 0.766 / 0.777 | 0.586 / 0.588 | 0.705 / 0.724 | 0.780 / 0.787 | 0.771 / 0.771 | 0.664 / 0.657 | 0.545 / 0.543 |
| CPC-SC-T+SH (vòng 4) | 0.761 / 0.777 | 0.610 / 0.627 | 0.722 / 0.741 | 0.794 / 0.812 | 0.812 / 0.809 | 0.676 / 0.693 | 0.525 / 0.569 |
| **CPC-SC-T½+SH** | 0.770 / 0.780 | 0.612 / 0.624 | 0.744 / 0.759 | 0.794 / 0.814 | 0.812 / 0.810 | 0.680 / 0.693 | 0.528 / 0.571 |
| CPC-SC-T½+CS | 0.775 / 0.785 | 0.582 / 0.589 | 0.736 / 0.746 | 0.786 / 0.795 | 0.772 / 0.772 | 0.665 / 0.659 | 0.547 / 0.545 |
| CPC-SC-Tmin+SH (thăm dò) | 0.763 / 0.777 | 0.570 / 0.605 | 0.693 / 0.715 | 0.764 / 0.788 | 0.812 / 0.809 | 0.669 / 0.687 | 0.514 / 0.563 |
| CPC-SC-Tonly+SH (thăm dò) | 0.764 / 0.784 | 0.534 / 0.563 | 0.658 / 0.698 | 0.706 / 0.757 | 0.812 / 0.809 | 0.661 / 0.686 | 0.531 / 0.584 |

### Bảng 3. Boreas: null chéo traversal (X) so với null bản đồ — mặc định (10 seed)

| Luật | Boreas |
|---|---|
| CPC-SC+CS (null bản đồ) | 0.661 / 0.001 / 0.021 / 5.1 |
| CPC-SC(X)+CS | 0.669 / 0.002 / 0.021 / 5.0 |
| CPC-SC(X)+SH | 0.673 / 0.003 / 0.026 / 5.4 |
| CPC-SC-T+CS (null bản đồ) | 0.666 / 0.001 / 0.023 / 5.1 |
| CPC-SC-T(X)+CS | 0.673 / 0.002 / 0.023 / 5.1 |
| CPC-SC-T+SH (null bản đồ) | 0.670 / 0.002 / 0.028 / 5.6 |
| CPC-SC-T(X)+SH | 0.677 / 0.003 / 0.029 / 5.6 |

### Bảng 3b. Boreas: đường cong (seed 0–2)

| Luật | Boreas |
|---|---|
| CPC-SC+CS (null bản đồ) | 0.766 / 0.777 |
| CPC-SC(X)+CS | 0.769 / 0.777 |
| CPC-SC(X)+SH | 0.761 / 0.773 |
| CPC-SC-T+CS (null bản đồ) | 0.770 / 0.782 |
| CPC-SC-T(X)+CS | 0.772 / 0.783 |
| CPC-SC-T+SH (null bản đồ) | 0.761 / 0.777 |
| CPC-SC-T(X)+SH | 0.766 / 0.779 |

### Bảng 4. VPR-auditing'26 (Qwen2.5-VL-7B offline) trên các frame được audit (mỗi 5 frame), seed 0

| Dataset · descriptor | Luật | P | C | FAR | S | recall | FL | sai số (m) |
|---|---|---|---|---|---|---|---|---|
| Boreas · megaloc | VPR-auditing'26 | 0.796 | 0.592 | 0.371 | 0.662 | 0.691 | 0.359 | 149.5 |
| Boreas · megaloc | Claxton'24 (nhãn) | 0.987 | 0.635 | 0.025 | 0.830 | 0.919 | 0.000 | 3.4 |
| Boreas · megaloc | CPC-SC+CS | 0.988 | 0.650 | 0.023 | 0.840 | 0.943 | 0.003 | 3.0 |
| Boreas · netvlad | VPR-auditing'26 | 0.747 | 0.499 | 0.240 | 0.644 | 0.547 | 0.304 | 151.5 |
| Boreas · netvlad | Claxton'24 (nhãn) | 0.847 | 0.423 | 0.123 | 0.641 | 0.526 | 0.084 | 154.8 |
| Boreas · netvlad | CPC-SC+CS | 0.991 | 0.240 | 0.005 | 0.486 | 0.349 | 0.000 | 7.5 |
| 4S countryside · megaloc | VPR-auditing'26 | 0.761 | 0.293 | 0.177 | 0.505 | 0.344 | 0.150 | 70.1 |
| 4S countryside · megaloc | Claxton'24 (nhãn) | 0.910 | 0.610 | 0.139 | 0.769 | 0.856 | 0.059 | 33.0 |
| 4S countryside · megaloc | CPC-SC+CS | 0.990 | 0.368 | 0.010 | 0.633 | 0.561 | 0.000 | 43.4 |
| 4S countryside · netvlad | VPR-auditing'26 | 0.502 | 0.285 | 0.211 | 0.443 | 0.221 | 0.183 | 88.4 |
| 4S countryside · netvlad | Claxton'24 (nhãn) | 0.778 | 0.209 | 0.069 | 0.420 | 0.250 | 0.019 | 102.4 |
| 4S countryside · netvlad | CPC-SC+CS | 0.959 | 0.031 | 0.002 | 0.086 | 0.045 | 0.000 | 99.8 |
| 4S office · megaloc | VPR-auditing'26 | 0.932 | 0.612 | 0.166 | 0.768 | 0.758 | 0.119 | 23.0 |
| 4S office · megaloc | Claxton'24 (nhãn) | 0.980 | 0.742 | 0.061 | 0.874 | 0.966 | 0.000 | 10.9 |
| 4S office · megaloc | CPC-SC+CS | 0.986 | 0.719 | 0.040 | 0.871 | 0.943 | 0.000 | 11.2 |
| 4S office · netvlad | VPR-auditing'26 | 0.880 | 0.546 | 0.152 | 0.723 | 0.638 | 0.175 | 29.4 |
| 4S office · netvlad | Claxton'24 (nhãn) | 0.914 | 0.491 | 0.098 | 0.708 | 0.597 | 0.079 | 25.1 |
| 4S office · netvlad | CPC-SC+CS | 0.990 | 0.330 | 0.009 | 0.594 | 0.435 | 0.000 | 18.7 |
| 4S old town · megaloc | VPR-auditing'26 | 0.833 | 0.367 | 0.144 | 0.589 | 0.524 | 0.111 | 77.2 |
| 4S old town · megaloc | Claxton'24 (nhãn) | 0.928 | 0.554 | 0.094 | 0.752 | 0.882 | 0.000 | 28.2 |
| 4S old town · megaloc | CPC-SC+CS | 0.940 | 0.559 | 0.080 | 0.762 | 0.902 | 0.000 | 29.3 |
| 4S old town · netvlad | VPR-auditing'26 | 0.778 | 0.349 | 0.126 | 0.567 | 0.466 | 0.146 | 101.6 |
| 4S old town · netvlad | Claxton'24 (nhãn) | 0.820 | 0.381 | 0.111 | 0.604 | 0.537 | 0.077 | 236.1 |
| 4S old town · netvlad | CPC-SC+CS | 0.993 | 0.217 | 0.003 | 0.454 | 0.370 | 0.000 | 48.3 |
| NCLT · megaloc | VPR-auditing'26 | 0.755 | 0.723 | 0.457 | 0.660 | 0.712 | 0.114 | 25.3 |
| NCLT · megaloc | Claxton'24 (nhãn) | 0.855 | 0.691 | 0.258 | 0.757 | 0.770 | 0.003 | 4.8 |
| NCLT · megaloc | CPC-SC+CS | 0.940 | 0.538 | 0.085 | 0.747 | 0.659 | 0.000 | 4.9 |
| NCLT · netvlad | VPR-auditing'26 | 0.673 | 0.610 | 0.354 | 0.642 | 0.536 | 0.083 | 65.5 |
| NCLT · netvlad | Claxton'24 (nhãn) | 0.754 | 0.464 | 0.202 | 0.634 | 0.457 | 0.076 | 63.9 |
| NCLT · netvlad | CPC-SC+CS | 0.984 | 0.265 | 0.009 | 0.517 | 0.340 | 0.000 | 4.4 |

### Bảng 5. Chọn biến thể leave-one-dataset-out (tiêu chí đăng ký trước)

| held-out | chosen on the others | held-out err | recall | segFAR | best label-free on held-out | regret (m) |
|---|---|---|---|---|---|---|
| 4s:countryside | CPC-W+CS+SH | 54.5 | 0.276 | 0.000 | CPC-SC-T+SH (51.0) | 3.5 |
| 4s:office_loop | CPC-W+CS+SH | 11.6 | 0.692 | 0.000 | CPC-SC+SH (11.3) | 0.3 |
| 4s:old_town | CPC-W+CS+SH | 32.7 | 0.586 | 0.000 | CPC-SC-T+SH (29.7) | 2.9 |
| boreas | CPC-W+CS+SH | 5.3 | 0.655 | 0.001 | CPC-SC-Tmin+CS (5.0) | 0.3 |
| cmu | CPC-SC-T0.5+CS | 4.3 | 0.762 | 0.004 | CPC-SC-Tmin+CS (3.5) | 0.8 |
| nclt | CPC-SC-T+CS | 4.6 | 0.552 | 0.000 | TCEmin (3.7) | 1.0 |
| nord | CPC-W+CS+SH | 9.2 | 0.650 | 0.000 | CPC-W+CS+SH (9.2) | 0.0 |



## 5. Đọc kết quả

1. **Null khớp điều kiện:** trên Boreas, κ từ null chéo traversal chỉ tăng recall +0.007 (CPC-SC-T(X)+CS 0.643 so với
   0.636), segFAR vẫn ≤ α (run tệ nhất 0.023); đường cong gần như không đổi. Giả thuyết "điểm mặc định dè dặt vì null cùng
   điều kiện ảnh" chỉ được ủng hộ **yếu**: phân phối p-value của pseudo-query khác điều kiện gần với null bản đồ
   (P(p ≤ 0.05) 0.010–0.035 so với 0.004–0.079). Sự dè dặt chủ yếu là **cấu trúc**: κ bảo đảm P(khởi phát trong đoạn) ≤ α cho
   riêng chuỗi hiện diện, sau đó dừng CS/SH loại thêm phần lớn báo sai (tỷ lệ thực tế 0.001–0.006 ≪ α). Hiệu chuẩn chung
   (hiện diện ∧ dừng) trên null chéo traversal cần chạy chuỗi vị trí trên các pseudo-query: việc tiếp theo.
2. **Công suất tuyến:** w₃ = ½ (đăng ký trước) cho recall tại FL ≤ 0.01 ≥ w₃ = 1/H trên 7/7 (CMU +0.022, Boreas +0.009)
   và pAUC cao hơn CPC-SC+CS trên 7/7; so với Claxton'24 (nhãn) cao hơn 6/7, với SafeVPR'26 (nhãn) 4/5, với TAO'26 6/7. Chọn
   leave-one-dataset-out theo sai số (đăng ký trước) không phân biệt rõ các biến thể (regret ≤ 3.5 m). Ở điểm mặc định, CPC-SC-T½+CS tăng recall trên 7/7 so với CPC-SC+CS với run tệ nhất
   ≤ 0.046 < α; CPC-SC-T½+SH cho recall cao nhất trên CMU (0.789) nhưng một run CMU có segFAR 0.188 > α (dừng SH kém chặt
   hơn CS trên CMU).
3. **CMU vẫn là điểm yếu xếp hạng:** biến thể thăm dò chỉ dùng bằng chứng tuyến thu hẹp khoảng cách với descriptor mạnh
   (CosPlace 0.819, MegaLoc 0.866 tại FL ≤ 0.01, seed 0) nhưng **không tổng quát**: trung bình 6 descriptor × 3 seed trên CMU
   chỉ 0.658 (Tonly) / 0.693 (Tmin), thấp hơn 0.744 của CPC-SC-T½+SH, và kém trên NCLT / Nordland; nên bị loại. Khoảng cách
   với Claxton'24 (nhãn) / TAO'26 (0.79) vẫn còn. Chẩn đoán: vị trí không phải vấn đề (MAP đúng
   98–99 %), mà là bằng chứng hiện diện ở frame off-map gần mép bản đồ.
4. **SafeVPR'26 ngoài Boreas:** có nhãn, segFAR trung bình 0.004–0.041 nhưng run tệ nhất tới 0.22; tại FL ≤ 0.01 thấp hơn
   CPC-SC-T½+SH trên 4/5 dataset có SafeVPR (Boreas, NCLT, office, countryside; thua old town 0.698 so với 0.680).
5. **VPR-auditing'26 ngoài Boreas:** với ảnh ban ngày (4Seasons) Qwen2.5-VL-7B tốt hơn trên Boreas (P 0.76–0.93) nhưng vẫn
   chấp nhận 11–18 % frame off-map, sai số điều hướng 23–102 m; CPC-SC+CS trên cùng frame có FAR 0.002–0.085 và S cao hơn ở
   mọi cấu hình MegaLoc. Với descriptor yếu (NetVLAD), VLM có S cao hơn nhờ độ phủ, nhưng FAR 0.13–0.35.

## 6. Hạn chế và việc tiếp theo

- Null khớp điều kiện mới có cho Boreas (dataset khác không có traversal dư); hiệu chuẩn chung với bước dừng trên null này còn
  mở. Các biến thể "min" / "only" là thăm dò (thiết kế sau khi xem CMU), chỉ được chọn nếu leave-one-dataset-out chọn.
- CMU với descriptor mạnh: khoảng cách 0.07–0.10 recall so với Claxton'24 / TAO'26 vẫn còn.
- Không tuyên bố mức A\*; mức A (RA-L/ICRA/IROS) được củng cố bằng so sánh đầy đủ hơn.
