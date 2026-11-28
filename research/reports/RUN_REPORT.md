# Báo cáo các lần chạy & kết quả (sinh tự động từ registry và log Kaggle)

## A. Các kernel Kaggle (GPU dùng để trích xuất descriptor / hình học; thời lượng đo từ log của kernel)

| Kernel | Mục đích | Thiết bị | Thời lượng | Trạng thái |
|---|---|---|---|---|
| hmm-k01-nordseg | Nordland video-rate 2×2500 frame × 4 mùa × SALAD/MegaLoc/NetVLAD/CosPlace | T4 | 51.3 | OK |
| hmm-k02-4s-stopgo | 4Seasons office_loop (map 1 m, query 2 Hz) × SALAD/NetVLAD/CosPlace | T4 | 15.9 | OK (lỗi ghi report ở dòng cuối, dữ liệu đủ) |
| hmm-k03-4s-scene2 | 4Seasons countryside × 4 descriptor | T4 | 40.7 | OK |
| hmm-k04-4s-scene3 | 4Seasons old_town (dừng thật, có đêm) × 4 descriptor | T4 | 27.2 | OK |
| hmm-k05-pnp v1 | M5 6DoF RobotCar (SuperPoint+LightGlue+PnP) | T4 | ≈27 | INVALID (A27: sai hệ tọa độ NVM) |
| hmm-k06-nvmdiag | Chẩn đoán hệ tọa độ NVM (CPU) | CPU | 0.8 | OK |
| hmm-k05-pnp v2 | M5 6DoF RobotCar, ứng viên ảnh đơn vs HMM | T4 | 19.5 | OK |
| hmm-k07-jist v1/v2 | JIST Nordland/RobotCar/CMU ở 384×384 (v1 lỗi thứ tự pip) | T4 (xin L4, bị hạ xuống T4) | 31.4 (+v1 chưa đo) | SUPERSEDED (sai kích thước ảnh) |
| hmm-k07-jist v3 | JIST Nordland/RobotCar/CMU ở 480×640 (mặc định JIST) | T4 | 18.4 | OK |
| hmm-k08-jist4s v1/v2 | JIST 4Seasons trên CPU (384 / 480×640) | CPU | – | SUPERSEDED |
| hmm-k08-jist4s v3 | JIST 4Seasons 3 tuyến ở 480×640 | T4 | 13.4 | OK |

Tổng GPU T4 đã dùng ≈ 4.1 giờ (k01–k08, gồm các lần bị thay thế), chỉ trên tài khoản `nhatlong1103`. Không lần nào được cấp L4 (yêu cầu `NvidiaL4` bị hạ xuống T4).

## B. Các lần chạy CPU cục bộ (HMM, thống kê) — theo nhóm thí nghiệm

| Thí nghiệm | Nội dung | Số lần chạy | Tổng phút CPU | Invalid |
|---|---|---|---|---|
| E01 | Thang HMM (single/SeqSLAM/HMM τ,β,LLR) | 16 | 46.9 | 0 |
| E08 | Time-warp ban đầu | 1 | 5.6 | 0 |
| E18 | IA-HMM đầy đủ (bảng chính, seed, video-rate, 4Seasons) | 108 | 655.5 | 0 |
| E12 | Off-map (lỗ bản đồ) | 2 | 3.4 | 0 |
| PC | Theo điều kiện + 6DoF thô | 4 | 3.1 | 0 |
| E32 | Fixed-lag smoothing | 3 | 2.1 | 0 |
| E15 | Trọng số theo thông tin vs β cố định / keyframe | 10 | 8.7 | 0 |
| E21 | Chuyển giao CMU↔RobotCar | 4 | 3.0 | 0 |
| T4.1 | Taxonomy lỗi | 4 | 2.1 | 0 |
| E23 | Runtime | 1 | 0.0 | 0 |
| E30 | Pose 6DoF (nội suy + PnP) | 9 | 23.0 | 0 |
| E18b | Prior vận tốc (chẩn đoán) | 3 | 18.0 | 0 |
| B10 | Baseline JIST (học chuỗi) | 7 | 5.8 | 1 |

Tổng: 172 lần chạy ghi trong registry. Hàng invalid/superseded được giữ để truy vết (ISSUES A21–A27).

## C. Baseline học chuỗi JIST (Berton et al., RA-L 2024; trọng số chính thức, ResNet-18 + SeqGeM, ảnh 480×640)

L ∈ {3,5,10} và stride database ∈ {1,2,3,5} chọn trên calibration (cùng quy tắc với SeqSLAM). R@1 trên test sequences:

| Dataset | JIST ảnh đơn | JIST chuỗi (SeqGeM) | JIST chuỗi + HMM | **IA-HMM trên descriptor JIST** | IA-HMM tốt nhất (descriptor khác) |
|---|---|---|---|---|---|
| Nordland | 0.723 | 0.780 (L=5, k=1) | 0.986 | **0.987** | 0.991 (salad) |
| Extended CMU | 0.927 | 0.923 (L=3, k=1) | 0.939 | **0.950** | 0.955 (salad) |
| RobotCar v2 | 0.900 | 0.882 (L=3, k=2) | 0.899 | **0.918** | 0.991 (salad) |
| 4Seasons office_loop | 0.850 | 0.756 (L=3, k=3) | 0.783 | **0.918** | 0.971 (salad) |
| 4Seasons countryside | 0.665 | 0.472 (L=3, k=5) | 0.475 | **0.796** | 0.890 (megaloc) |
| 4Seasons old_town | 0.603 | 0.544 (L=3, k=3) | 0.559 | **0.677** | 0.899 (salad) |
| Nordland time-warp s1 | 0.766 | – | – | **0.915** | – |
## D. Bảng kết quả chính — R@1 (giao thức khóa, test sequences)

Tổng hợp 31 ô (seed 0/1 như trong bảng): IA-HMM ≥ ảnh đơn 31/31; so với SeqSLAM tuned 25 thắng / 5 hòa (±0.5 điểm) / 1 thua; so với HMM kernel cố định 14 / 14 / 3.

| Dataset (NetVLAD / CosPlace / SALAD / MegaLoc) | Single | SeqSLAM (tuned) | HMM kernel cố định | **IA-HMM (dev-sel.)** |
|---|---|---|---|---|
| Nordland đồng bộ | 0.364 / 0.652 / 0.811 / 0.821 | 0.889 / 0.966 / 0.970 / 0.960 | 0.983 / 0.989 / 0.990 / 0.989 | **0.983 / 0.982 / 0.991 / 0.989** |
| Nordland time-warp s1 | 0.430 / 0.695 / 0.808 / 0.832 | 0.580 / 0.658 / 0.671 / 0.669 | 0.563 / 0.826 / 0.869 / 0.882 | **0.827 / 0.915 / 0.901 / 0.917** |
| Extended CMU (11 slice) | 0.701 / 0.908 / 0.943 / 0.932 | 0.770 / 0.921 / 0.954 / 0.947 | 0.820 / 0.931 / 0.955 / 0.941 | **0.820 / 0.931 / 0.955 / 0.941** |
| RobotCar Seasons v2 | 0.708 / 0.834 / 0.987 / 0.974 | 0.777 / 0.858 / 0.989 / 0.984 | 0.785 / 0.868 / 0.991 / 0.987 | **0.776 / 0.859 / 0.991 / 0.985** |
| 4Seasons office_loop (thật) | 0.512 / 0.814 / 0.932 / — | 0.703 / 0.883 / 0.956 / — | 0.791 / 0.853 / 0.969 / — | **0.847 / 0.923 / 0.971 / —** |
| 4Seasons countryside (thật) | 0.278 / 0.575 / 0.659 / 0.724 | 0.336 / 0.614 / 0.731 / 0.788 | 0.468 / 0.663 / 0.855 / 0.824 | **0.513 / 0.682 / 0.855 / 0.890** |
| 4Seasons old_town (thật) | 0.413 / 0.536 / 0.832 / 0.794 | 0.422 / 0.544 / 0.840 / 0.815 | 0.516 / 0.594 / 0.868 / 0.838 | **0.516 / 0.611 / 0.899 / 0.879** |
| Nordland video-rate (k01) | 0.379 / — / 0.815 / — | 0.753 / — / 0.895 / — | 0.936 / — / 0.953 / — | **0.936 / — / 0.953 / —** |
| Nordland video-rate time-warp | 0.418 / — / 0.839 / — | 0.601 / — / 0.873 / — | 0.652 / — / 0.905 / — | **0.794 / — / 0.915 / —** |

## E. 6DoF có hướng dẫn bởi HMM (RobotCar, k=3 ứng viên, SuperPoint+LightGlue+PnP)

| Descriptor / tập | Ngưỡng | Ứng viên ảnh đơn | Ứng viên HMM | CI hiệu (bootstrap theo chuỗi) |
|---|---|---|---|---|
| netvlad / all | 0.25m | 0.248 | 0.250 | [-0.015, +0.020] |
| netvlad / night | 0.25m | 0.037 | 0.037 | [-0.013, +0.013] |
| netvlad / all | 0.5m | 0.476 | 0.497 | [+0.002, +0.044] |
| netvlad / night | 0.5m | 0.121 | 0.154 | [-0.013, +0.090] |
| netvlad / all | 5.0m | 0.728 | 0.768 | [+0.015, +0.068] |
| netvlad / night | 5.0m | 0.221 | 0.282 | [-0.018, +0.144] |
| salad / all | 0.25m | 0.278 | 0.276 | [-0.012, +0.008] |
| salad / night | 0.25m | 0.114 | 0.107 | [-0.032, +0.017] |
| salad / all | 0.5m | 0.560 | 0.563 | [-0.005, +0.012] |
| salad / night | 0.5m | 0.399 | 0.393 | [-0.031, +0.019] |
| salad / all | 5.0m | 0.908 | 0.906 | [-0.007, +0.001] |
| salad / night | 5.0m | 0.862 | 0.859 | [-0.020, +0.009] |

## F. Kiểm định bội (Holm, α=0.05)

- fixed_vs_single: 40 tests · Holm-significant: 36 (improvements 36, degradations 0)
- devsel_vs_fixed: 29 tests · Holm-significant: 10 (improvements 10, degradations 0)
- LVME_vs_fixed: 39 tests · Holm-significant: 14 (improvements 9, degradations 5)

## G. Đang chờ / chưa chạy

| Việc | Trạng thái | Cần gì |
|---|---|---|
| Kernel Kaggle | không có kernel nào đang chạy | – |
| Phản hồi hình học (số inlier) vào HMM (I30) | chưa chạy | GPU ~30 phút (RobotCar), kết quả k05 dùng lại được |
| 6DoF trên CMU/4Seasons | chưa chạy | tam giác hóa mô hình 3D từ pose reference (GPU ~1 h/dataset) |
| HSMM dwell / bin vận tốc học được (F16) | chưa chạy | CPU |
| Dataset thứ 5 (MSLS sequences) | chưa chạy | quyền truy cập MSLS trên Kaggle + GPU trích xuất |
| SeqVLAD / CaseVPR (baseline học chuỗi khác) | chưa chạy | trọng số công khai (cần xác minh nguồn) |
