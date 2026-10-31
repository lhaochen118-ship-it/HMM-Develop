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

{{TABLES}}

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
