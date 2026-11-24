# Tổng quan Visual Localization (VPR, 6-DoF localization, reliability, HMM/sequence)

*Phiên bản 2026-10-28, bổ sung 2026-10-30 (§6b, §8). Chỉ đọc paper, không đọc repo code. Mục đích: (1) nắm phương pháp, benchmark và đóng góp ±
của các paper chính; (2) tránh trùng ý tưởng khi Claude đề xuất hướng mới. Phần HMM/sequence là **§6**.*

**Ký hiệu nguồn:**
- **[F]** đọc full text trong phiên này. Số liệu lấy trực tiếp từ bảng của paper.
- **[R]** đọc report/abstract.
- **[T]** số liệu lấy từ **bảng so sánh của một paper khác** đã đọc [F] (ghi rõ nguồn). Đây là số do paper đó báo
  cáo, có thể khác số của paper gốc do protocol khác.
- **[C]** chỉ biết qua trích dẫn. Phải verify trước khi dùng.

**Metric:**
- **R@k**: tỉ lệ query có ảnh đúng trong top-k. Ngưỡng 25 m cho dataset đô thị; ±2 frame (Nordland) hoặc 1:1 tuỳ protocol.
- **(m, °)**: tỉ lệ query có pose trong ngưỡng.
- **cm/°**: median error.
- **R@99%P**: recall tại precision 99 %.
- **FAR**: false-accept rate.

---

## 1. Bản đồ lĩnh vực

| Nhánh | Đầu vào → đầu ra | Paper đại diện | Benchmark chính |
|---|---|---|---|
| **VPR / image retrieval** (global descriptor) | ảnh → top-k ảnh map (vị trí thô) | NetVLAD, GeM, CosPlace, EigenPlaces, MixVPR, AnyLoc, SALAD, BoQ, CricaVPR, CliqueMining, MegaLoc | Pitts30k/250k, MSLS, Tokyo 24/7, Nordland, SPED, SF-XL, AmsterTime, Eynsham, SVOX, Baidu |
| **Two-stage VPR** (re-ranking local) | + so khớp local để sắp lại top-k | Patch-NetVLAD, TransVPR, R2Former, SelaVPR, SP-SuperGlue, DELG | MSLS, Pitts30k, Tokyo 24/7 |
| **Structure-based 6-DoF** | ảnh → pose 6-DoF qua 2D-3D | Active Search, CSL, HF-Net/hloc, InLoc, PixLoc | Aachen Day-Night, RobotCar Seasons, CMU Seasons, Cambridge, 7-Scenes, LaMAR |
| **Absolute pose regression (APR)** | ảnh → pose (mạng nhớ scene) | PoseNet, MapNet, MS-Transformer, LENS, PMNet, DFNet | Cambridge, 7-Scenes, RobotCar |
| **Scene coordinate regression (SCR)** | ảnh → toạ độ 3D mỗi pixel → PnP | DSAC*, SANet, SRC, ACE, (GLACE) | 7/12-Scenes, Cambridge, Wayspots |
| **Relative pose regression / feed-forward 3D** | cặp ảnh → pose tương đối | Map-free, ExReNet, DUSt3R, MASt3R, Reloc3r | ScanNet1500, RealEstate10K, CO3D, 7-Scenes, Cambridge |
| **Reliability / uncertainty / acceptance** | match → chấp nhận hay không | PA, SUE, RS/SD/SU, Quantile Transfer, SAFEVPR, VLM auditing, SMR, Trinh & Lyons | Pitts, MSLS, Nordland, RobotCar… |
| **Sequence / HMM / filter** (§6) | chuỗi ảnh (+odometry) → belief/pose | SeqSLAM, HMM (Hansen'14, Doan'19), MPF, Xu'20/'21, TRAIL | Nordland, RobotCar, St Lucia, MSLS, 4Seasons |

---

## 2. VPR một giai đoạn (global descriptor)

### 2.1 Phương pháp, đóng góp

| Paper | Proposed method | (+) Đóng góp | (−) Hạn chế |
|---|---|---|---|
| **NetVLAD** (Arandjelović, CVPR'16) [T] | VLAD khả vi (soft-assign cluster) trên feature VGG16. Weakly-supervised triplet trên Pitts. | Chuẩn de-facto 2016–2021. Vẫn dùng trong hloc/COLMAP. | Descriptor 32k-d. Yếu với đêm (SF-XL night R@1 6.7) và mùa (Nordland* 32.6). |
| **GeM / AP-GeM** (Radenović'18; Revaud'19) [T] | Generalized-mean pooling, loss listwise AP. | Đơn giản, gọn. | Kém NetVLAD trên VPR đô thị (MSLS-val 56.0, Pitts250k 80.0). |
| **CosPlace** (Berton, CVPR'22) [T] | Huấn luyện kiểu classification trên các nhóm place không chồng lấn của SF-XL (41 M ảnh). GeM 2048-d. | Scale được tới hàng chục triệu ảnh. Bản ResNet-18 chỉ 11 M param. | Kém trên Baidu indoor (R@1 52.0) và landmark. |
| **EigenPlaces** (Berton, ICCV'23) [T] | Sampling theo hướng nhìn chính (eigen) để học viewpoint-robust. | Pitts30k 92.5, Tokyo 93.0, AmsterTime 48.9 (R50). | Đêm/occlusion vẫn yếu (SF-XL night 23.6). |
| **Conv-AP / GSV-Cities** (Ali-bey'22) [T] | Dataset GSV-Cities (530k ảnh, 62k place) + multi-similarity loss. | Chuẩn hoá training, nhanh. | Nordland* 38.2. |
| **MixVPR** (Ali-bey, WACV'23) [T] | Feature-mixer MLP trên feature map ResNet-50. | One-stage mạnh thời CNN (Pitts250k 94.2–94.3). | SVOX night 64.4, Nordland* 58.4. |
| **AnyLoc** (Keetha, RA-L'23) [R][T] | DINOv2 **không fine-tune**, VLAD hard-assign trên feature dense (layer 31 value), vocabulary theo domain. | Universal: tốt indoor/aerial/underwater/subT. Training-free. | Descriptor 49k-d (không chạy được SF-XL vì RAM). Urban kém fine-tuned: MSLS-val 58.7, Nordland* 16.1 (theo bảng SALAD). |
| **SALAD** (Izquierdo & Civera, CVPR'24) [F] | DINOv2-B fine-tune 4 block cuối. Gán feature → cluster bằng **optimal transport (Sinkhorn) + dustbin**. Descriptor 8192+256. Train 30 phút. | MSLS-challenge 75.0, Nordland 76.0, SPED 92.1 (R@1). One-stage vượt mọi two-stage (R2Former 73.0 MSLS-ch). Latency 2.4 ms. | Chậm hơn ResNet. Phụ thuộc backbone độ phân giải cao (ResNet-SALAD chỉ 57.4 MSLS-ch). |
| **BoQ** (Ali-bey, CVPR'24) [F] | Bag of **learnable queries** + cross-attention lên feature (ResNet-50 hoặc DINOv2). | R50 4096-d: Pitts250k 95.0, MSLS-val 91.1, SPED 85.4, Nordland* 69.5. **SVOX night 87.1** (MixVPR 64.4). Hơn two-stage, nhanh hơn R2Former 30×. | Không re-ranking. Bản DINOv2 cần GPU lớn. Còn yếu với ảnh lịch sử (AmsterTime 52.2). |
| **CricaVPR** (Lu, CVPR'24) [T] | Cross-image correlation-aware representation (attention giữa các ảnh trong batch). | MSLS-val 76.7, Pitts30k 90.0. | Thua SALAD trên hầu hết bộ theo bảng MegaLoc. |
| **CliqueMining** (Izquierdo, ECCV'24) [T] | Mining hard negative theo clique trên MSLS. Kiến trúc SALAD. | **MSLS-val 91.6** (cao nhất), Tokyo 96.8. | Kém MegaLoc ở Baidu, SF-XL v1. |
| **MegaLoc** (Berton & Masone, 2025) [F] | DINOv2-B + SALAD. Huấn luyện **trộn 5 dataset** (SF-XL, GSV-Cities, MSLS, MegaScenes, ScanNet), 6 sub-batch, mỗi sub-batch một multi-similarity loss. Backward riêng từng loss (VRAM 360 → 60 GB). | SOTA trên đa số VPR. Baidu indoor 87.7 (SALAD 72.7). R-Oxford E 91.0 (SALAD 55.2). SOTA LaMAR. | "Không có technical novelty" (tự nhận). Thua CliqueMining trên MSLS. Không hợp rừng/hang (AnyLoc tốt hơn) và embedded (228 M param). |

### 2.2 Benchmark R@1 / R@10 (nguồn: bảng 1 MegaLoc [F])

| Method | dim | Baidu | Eynsham | MSLS-val | Pitts250k | Pitts30k | SF-XL v1 | SF-XL night | SF-XL occl. | Tokyo 24/7 |
|---|---|---|---|---|---|---|---|---|---|---|
| NetVLAD | 4096 | 69.0/95.0 | 77.7/90.5 | 54.5/70.4 | 85.9/95.0 | 85.0/94.4 | 40.1/57.7 | 6.7/14.2 | 9.2/22.4 | 69.8/82.9 |
| AP-GeM | 2048 | 59.8/90.8 | 68.3/84.0 | 56.0/72.9 | 80.0/93.5 | 80.7/94.1 | 37.9/54.1 | 7.5/16.7 | 5.3/14.5 | 57.5/77.5 |
| CosPlace | 2048 | 52.0/80.4 | 90.0/94.9 | 85.0/92.6 | 92.3/98.4 | 90.9/96.7 | 76.6/85.5 | 23.6/32.8 | 30.3/44.7 | 87.3/95.6 |
| MixVPR | 4096 | 71.9/94.7 | 89.6/94.4 | 83.2/91.9 | 94.3/98.9 | 91.6/96.4 | 72.5/80.9 | 19.5/30.5 | 30.3/38.2 | 87.0/94.0 |
| EigenPlaces | 2048 | 69.1/91.9 | 90.7/95.4 | 85.9/93.1 | 94.1/98.7 | 92.5/97.6 | 84.0/90.7 | 23.6/34.5 | 32.9/52.6 | 93.0/97.5 |
| AnyLoc | 49152 | 75.6/95.2 | 85.0/94.1 | 58.7/74.5 | 89.4/98.0 | 86.3/96.7 | – | – | – | 87.6/97.5 |
| SALAD | 8448 | 72.7/93.6 | 91.6/95.9 | 88.2/95.0 | 95.0/99.2 | 92.3/97.4 | 88.7/94.4 | 46.1/62.4 | 50.0/68.4 | 94.6/98.1 |
| CricaVPR | 10752 | 65.6/93.2 | 88.0/94.3 | 76.7/87.2 | 92.6/98.3 | 90.0/96.7 | 62.6/78.9 | 25.8/40.6 | 27.6/47.4 | 82.9/93.7 |
| CliqueMining | 8448 | 72.9/92.7 | 91.9/96.2 | **91.6**/95.9 | 95.3/99.2 | 92.6/97.8 | 85.5/92.6 | 46.1/60.9 | 44.7/64.5 | **96.8**/97.8 |
| MegaLoc | 8448 | **87.7**/98.0 | **92.6**/96.8 | 91.0/95.8 | **96.4**/99.3 | **94.1**/98.2 | **95.3**/98.0 | **52.8**/73.8 | **51.3**/75.0 | 96.5/99.4 |

### 2.3 Benchmark mùa / thời tiết / đêm (nguồn: BoQ [F] bảng 2–3, SALAD [F] bảng 1)

| Method (backbone) | Nordland* R@1 | Nordland** R@1 | SPED R@1 | MSLS-ch R@1 | SVOX night | SVOX snow | AmsterTime | St Lucia |
|---|---|---|---|---|---|---|---|---|
| NetVLAD (VGG16) | 32.6 | 13.1 | 78.7 | 35.1 | 8.0 | 54.4 | 16.3 | 64.6 |
| CosPlace (R50) | 54.4 | 71.9 | 75.3 | 67.2 | 50.7 | 92.0 | 47.7 | 99.6 |
| MixVPR (R50) | 58.4 | 76.2 | 85.2 | 64.0 | 64.4 | 96.8 | 40.2 | 99.6 |
| EigenPlaces (R50) | 54.2 | 71.2 | 82.4 | 67.4 | 58.9 | 93.1 | 48.9 | 99.6 |
| BoQ (R50) | 69.5–70.7 | 83.1 | 85.4–86.5 | – | **87.1** | **98.7** | **52.2** | 100 |
| SALAD (DINOv2) | **76.0** | – | **92.1** | **75.0** | – | – | – | – |
| AnyLoc (DINOv2, theo SALAD) | 16.1 | – | 85.3 | 42.2 | – | – | – | – |

*Nordland\* = 2760 query/27.6k ref (protocol MixVPR). Nordland\*\* = 27.6k/27.6k. Các paper dùng split khác nhau, nên
chỉ so trong cùng một cột.*

**Nhận xét chung VPR:**
- (+) Từ 2023, backbone DINOv2 fine-tune cộng aggregation (SALAD/BoQ/MegaLoc) đã bão hoà các benchmark đô thị (R@1 > 90).
- (−) Khó còn lại là đêm (SF-XL night ≈ 50), occlusion, ảnh lịch sử (AmsterTime ≈ 50), indoor ngoài phân phối và rừng.
- (−) **Không paper nào trong nhánh này cho cơ chế accept/reject có đảm bảo.** Tất cả chỉ báo R@k, giả định query
  luôn có ảnh đúng trong DB.

## 3. VPR hai giai đoạn (re-ranking)

| Paper | Method | Benchmark (R@1; nguồn) | (+) | (−) |
|---|---|---|---|---|
| **Patch-NetVLAD** (Hausler, CVPR'21) [T] | NetVLAD trên patch đa tỉ lệ để re-rank. | MSLS-val 79.5, MSLS-ch 48.1, Pitts30k 88.7, Tokyo 86.0 (SelaVPR T2) | Không cần train thêm, tốt cho viewpoint. | 1.3 s extract và 7.4 s re-rank/query. Bộ nhớ 908 GB trên MSLS (SALAD T2). |
| **SP-SuperGlue** [T] | SuperPoint + SuperGlue matching top-100. | MSLS-val 78.1, Pitts30k 87.2, Tokyo 88.2 | Geometric verification mạnh. | 7.5 s/query. |
| **DELG** (Cao, ECCV'20) [T] | Global + local trong một mạng. | MSLS-val 83.2, Pitts30k 89.9 | | 35 s re-rank. |
| **TransVPR** (Wang, CVPR'22) [T] | Attention đa tầng, re-rank bằng token. | MSLS-val 86.8, MSLS-ch 63.9 | Nhanh hơn Patch-NetVLAD. | 3.2 s re-rank. |
| **R2Former** (Zhu, CVPR'23) [T] | Transformer hợp nhất retrieval + re-ranking. | MSLS-val 89.7, MSLS-ch 73.0, Pitts30k 91.1, Tokyo 88.6 | Re-rank nhanh nhất (0.2–0.4 s). | Bị SALAD/BoQ one-stage vượt. |
| **SelaVPR** (Lu, ICLR'24) [F] | DINOv2 đóng băng + **adapter** (global + local), re-rank bằng mutual-NN dense local feature, loss local khả vi. | Tokyo **94.0**, MSLS-val 90.8, MSLS-ch 73.5, Pitts30k 92.8 | Chỉ 53 M param tunable, train 0.3 h. Re-rank 0.08 s. | Vẫn hai giai đoạn. Cần fine-tune MSLS rồi Pitts riêng cho từng benchmark. |

## 4. Localization 6-DoF

### 4.1 Structure-based / hierarchical

| Paper | Method | (+) | (−) |
|---|---|---|---|
| **Benchmarking 6DOF localization in changing conditions** (Sattler et al., CVPR'18) [F] | Tạo **Aachen Day-Night, RobotCar Seasons, CMU Seasons** với GT 6-DoF và ngưỡng (.25 m, 2°)/(.5 m, 5°)/(5 m, 10°). Đánh giá AS, CSL, DenseVLAD, NetVLAD, FAB-MAP, LocalSfM, DenseSfM. | Benchmark chuẩn của ngành. Kết luận long-term localization "far from solved", đề xuất sequence-based. | Test GT bị giữ kín (submit online). |
| **Active Search (AS)** / **CSL** [T] | Matching 2D-3D trực tiếp với SIFT, ưu tiên hoá. | Rất chính xác ban ngày (Aachen day 57.3/83.7/96.6). | Sụp ban đêm (RobotCar night 0.5/1.1/3.4). |
| **DenseVLAD / NetVLAD (retrieval → pose ảnh DB)** [T] | Lấy pose của ảnh top-1. | Bền ban đêm ở ngưỡng thô (RobotCar night 5 m: 15–20 %). | Không chính xác ở ngưỡng mịn (Aachen .25 m ≈ 0). |
| **HF-Net / hloc** (Sarlin, CVPR'19) [F] | **Coarse-to-fine:** NetVLAD retrieval top-k, rồi SuperPoint local matching trong các cụm covisible, rồi PnP. HF-Net là một CNN chưng cất ra cả global + local. | NV+SP: Aachen night 40.8/56.1/74.5, CMU urban 91.7/94.6/97.7. Real-time (HF-Net). Thành pipeline chuẩn (hloc). | RobotCar night vẫn thấp (6.6/17.1/32.2). Phụ thuộc retrieval đúng. |
| **AS+GC(seq)** (trong Sattler'18) [F] | Active Search + ràng buộc **sequence/multi-camera**. | CMU 86–92 % (.25 m). Chứng minh sequence giúp rất nhiều. | Cần chuỗi + rig đã biết. |
| **InLoc, PixLoc, LaMAR** [C][T] | Dense matching indoor; featuremetric alignment; benchmark AR. | MegaLoc dùng LaMAR: HGE phone (5°, 1 m) 92.9, LIN 94.9. | Map lớn, nặng. |

**Benchmark RobotCar Seasons (%, .25/.5/5 m; nguồn HF-Net T3 [F]):**

| Method | dusk | sun | night | night-rain |
|---|---|---|---|---|
| Active Search | 44.7/74.6/95.9 | 25.0/46.5/69.1 | 0.5/1.1/3.4 | 1.4/3.0/5.2 |
| NetVLAD | 7.4/29.7/92.9 | 5.7/16.5/86.7 | 0.2/1.8/15.5 | 0.5/2.7/16.4 |
| NV+SP (hloc) | 54.8/83.0/96.2 | 51.7/73.9/92.4 | 6.6/17.1/32.2 | 5.2/17.0/26.6 |
| HF-Net | 53.9/81.5/94.2 | 48.5/69.1/85.7 | 2.7/6.6/15.8 | 4.7/16.8/21.8 |

*Đối chiếu với SelfCal: trên tập train công khai RobotCar, SALAD top-1 đạt khoảng 0.9 ở (5 m, 10°) kể cả ban đêm.
Retrieval hiện đại đã vượt xa NetVLAD 2019 ở ngưỡng thô.*

### 4.2 Absolute pose regression (APR) và scene-coordinate regression (SCR)

| Paper | Method | Benchmark | (+) | (−) |
|---|---|---|---|---|
| **PoseNet** (Kendall'15, '17) [T] | CNN hồi quy trực tiếp pose. | Cambridge median 267 cm / 3.0° (ACE T2) | Rất nhanh, map nhỏ. | Kém một bậc độ lớn. Sattler'19 chỉ ra APR gần với retrieval nội suy. |
| **MapNet / MS-Transformer / LENS / PMNet / DFNet+NeFeS** [T] | APR có ràng buộc hình học, NeRF-augmentation. | 7-Scenes DFNet+NeFeS 0.02 m/0.79°; Cambridge PMNet 0.31 m/0.79° (Reloc3r T4–5) | Cải thiện mạnh nhờ synthetic view. | Train nhiều ngày/scene. Không tổng quát scene mới. |
| **DSAC\*** (Brachmann, TPAMI'21) [T] | Hồi quy toạ độ 3D, RANSAC khả vi. | 7-Scenes 98.2 % (5 cm, 5°), Cambridge 21 cm / 0.3° (có depth) | Chính xác nhất cho SCR. | Map 15 h/scene. |
| **ACE** (Brachmann, CVPR'23) [F] | Backbone dùng chung + **head MLP riêng scene**. Train trên hàng nghìn viewpoint cùng lúc; curriculum loss reprojection. | **Map 5 phút**, 4 MB. 7-Scenes 97.1 %, Cambridge 25 cm / 0.4°. Ensemble "Poker" 17 cm / 0.3°. | Nhanh hơn DSAC\* 300×, không cần depth. | Kém AS/hloc ở Cambridge (11–14 cm). Mỗi scene vẫn phải map. |
| **Reloc3r** (2025) [F] | Relative-pose regression từ DUSt3R, train 8 M cặp ảnh, cộng motion averaging từ top-10 NetVLAD. | 7-Scenes 0.04 m / 1.02°; Cambridge 0.55 m / 0.56° **trên scene chưa thấy**. ScanNet1500 AUC@5 34.8. 25 ms. | Tổng quát scene mới, real-time. | Cambridge vẫn kém SCR/structure (dm vs cm). Phụ thuộc retrieval NetVLAD. |
| **Map-free relocalization, ExReNet, DUSt3R, MASt3R** [T] | Pose từ một ảnh tham chiếu hoặc point-map feed-forward. | MASt3R ScanNet1500 AUC@5 28.0. Map-free 7-Scenes 0.13 m / 3.7°. | Không cần map 3D. | Độ chính xác metric/scale còn kém. |

## 5. Reliability, uncertainty, chấp nhận match (liên quan trực tiếp SelfCal)

| Paper | Method | Benchmark | (+) | (−) |
|---|---|---|---|---|
| **PA ratio** (Hausler'21), L2 distance [T] | Tỉ lệ khoảng cách top-1/top-2. | Zaffar'24 AUC-PR: L2 0.69, PA 0.68 (trung bình 6 bộ). | Rẻ. | Overconfident với aliasing. Cần ngưỡng có nhãn. |
| **BTL, STUN** (DUE) [T] | Học phân phối descriptor (aleatoric). | AUC-PR 0.28 / 0.54 | | Cần train lại, kém L2. |
| **SUE** (Zaffar, CVPR'24) [F] | Phương sai không gian có trọng số exp(−λd) của top-K pose (K=10, λ=350). | AUC-PR TB 0.77 (Pitts 0.94, MSLS 0.77, Nordland 0.26). GV-DELF 0.93. | Dùng pose của map. Training-free. | Cần ngưỡng có nhãn. Benchmark nội bộ: vi phạm FAR trên RobotCar (1/9 điều kiện), TPR CMU 0.52. |
| **RS / SD / SU** (Miller, Milford et al., RA-L'26) [R] | RS = TB s_i/s_1; SD = median/best; SU = trung bình hai cái. | AUC-PR SU 0.92 (9 VPR × 6 dataset). SuperPoint-GV 0.95. <0.03 ms. | Training-free, nhanh. | Chỉ là score, không có đảm bảo. Vẫn phải chọn ngưỡng. |
| **Quantile Transfer** (Rajani, Milford, Fischer, 2026) [Gate 2] | Ánh xạ ngưỡng qua quantile batch. | – | Label-free khi deploy. | Benchmark nội bộ: vi phạm 64/138 điều kiện. |
| **SAFEVPR** (2026) [Gate 1] | Conformal (LTT/Mondrian) trên patch-score cho sequence VPR. | – | Đảm bảo conformal. | Cần nhãn calibration. LOCO vi phạm 38/138 (nội bộ). |
| **VPR Auditing bằng VLM** (Waheed, Milford et al., 2026) [F] | GPT-4.1 / Gemini / Qwen-VL xác minh cặp (query, top-1), không ngưỡng. | R@1 +13.6 điểm trung bình. FAR 0.12–0.30, precision > 0.95, coverage > 0.75 (6 dataset, 5 VPR). | Không cần ngưỡng/nhãn. Đề xuất bộ metric precision–coverage–FAR. | Chậm, phụ thuộc API đóng. FAR vẫn 0.6 trên Pitts250k. Không có đảm bảo. |
| **Trinh & Lyons** (2025) [F] | Ngưỡng theo place từ negative similarity (GMM). | GardensPoint R@1 61.7→93.3 (EigenPlaces), Nordland mini 69.0→76.7. | Tự động. | Dataset nhỏ. Không có off-map, không đảm bảo. |
| **TFA** (2026) [R] | Dùng ảnh DB làm pseudo-query (leave-self-out) để hiệu chỉnh aggregation (training-free). | MSLS-val +17.4 R@1 so với AnyLoc. | Database-only calibration. | Mục tiêu là retrieval, không phải accept/reject. |
| **KappaPlace, LocalScore (biometrics)** [R] | Uncertainty hyperspherical có học; mật độ k-NN gallery cho open-set. | LocalScore: FNIR@FPIR 53→40 %. | | Cần train / domain khác. |

**Khoảng trống chung:** chưa có phương pháp nào kiểm soát FAR (off-map/aliasing) **không cần nhãn** và **bền dưới
appearance shift** với đảm bảo thống kê. Đây là vị trí của SelfCal (xem `LITERATURE_GATE.md` Gate 1–4).

---

## 6. Sequence-based / HMM / Bayes filter cho visual localization – navigation

### 6.1 Tóm tắt chung
1. **Cách chuẩn hoá bài toán:**
   - state rời rạc = index ảnh map, hoặc pose liên tục;
   - observation = similarity của descriptor;
   - transition = band vận tốc hoặc odometry;
   - suy luận bằng forward filter, Viterbi, forward–backward hoặc MCL.
2. **Các hướng đã khai thác:**
   - chuẩn hoá emission;
   - odometry 1/3-dof;
   - smoothing ngược;
   - trạng thái off-map;
   - map tăng trưởng/nén;
   - độ dài sequence động;
   - học sequence descriptor;
   - introspection;
   - CRF trên database không thứ tự.
3. **Accept/reject** dựa trên ngưỡng heuristic (τ, MaxAP ≥ γ, R@99%P tune bằng nhãn). **Không** paper nào cho đảm bảo
   FAR/FDR dưới shift.
4. **Kinh nghiệm nội bộ (CCBF):** temperature/likelihood theo điều kiện **trơ** với HMM filter khi descriptor mạnh.

### 6.2 Sequence matching (không xác suất)

| Paper | Method | Benchmark | (+) | (−) |
|---|---|---|---|---|
| **SeqSLAM** (Milford & Wyeth, ICRA'12) [C] | SAD trên ảnh downsample + patch-norm. Tìm đường thẳng trong ma trận khác biệt. | MPF'19: Nordland R@100%P 70 %. Xu'20 (SeqM, NetVLAD) R@99%P: rain 83.1, dusk 31.1, night 6.2. | Day↔night, mùa với feature yếu. | Vận tốc hằng, route lặp, latency = độ dài sequence. |
| **Network flows** (Naseer AAAI'14, T-RO'18), **Lazy DA** (Vysotska RA-L'16) [C] | Min-cost flow / đồ thị lazy, có node non-match. | Xu'20 (Graph, NetVLAD) R@99%P: rain 88.3, dusk 14.0, night 6.0. | Vận tốc thay đổi, online. | Ngưỡng non-match tay. |
| **Adaptive thresholding for sequence PR** (Vysotska, ICRA'25) [C], **Beyond ANN** (Schubert, ICRA'21) [C] | Ngưỡng tự động từ dữ liệu batch/sequence. | – | Online, không nhãn. | Heuristic, không đảm bảo. |
| **Carson et al.** (ICRA'23) [F] | Unsupervised: argmin khoảng cách trùng argmax gradient (±1 frame) thì coi là "tốt", hạ khoảng cách rồi SeqSLAM. | AUC@20%recall TB 0.77→0.84 (15 cặp dataset×VPR: GardensPoint, Nordland, 4Seasons, RobotCar). | Training-free, <20 ms. | Recall bị cắt. Có trường hợp xấu đi (4Seasons). |
| **SMR predictor** (Hussaini, Fischer, Milford, 2025) [F] | MLP 4 lớp dự đoán sequence matching sẽ giữ/sửa/làm hỏng match. | Giảm AOC 26 % trung bình. Nordland −37.8 %, RobotCar −19 %, SFU −21.7 % (7 VPR). | Agnostic descriptor (cả SALAD). | Supervised theo dataset. F1 0.37–0.54. Restore thất bại. |

### 6.3 HMM / discrete Bayes filter / MCL

| Paper | Method | Benchmark | (+) | (−) |
|---|---|---|---|---|
| **Hansen & Browning** (IROS'14) [C] | HMM + Viterbi thay đường thẳng SeqSLAM. | – | Vận tốc phi tuyến. | Giữ cả ma trận similarity, không scale. |
| **MPF** (Hausler, RA-L'19) [F] | 4 xử lý ảnh (SAD, HOG, CNN, CNN-argmax). Emission = Σ log obs chuẩn hoá. Viterbi bỏ prior. Sequence động 5–20 frame theo quality (best vs next-best ngoài cửa sổ). | F1 TB 0.96 (NetVLAD 0.78, SeqSLAM 0.49). R@100%P: Nordland 92 %, RobotCar day→night 44 %, St Lucia 47 %. | Fusion trên một camera, latency giảm. | Giả định độc lập. Chuẩn hoá ad-hoc. Feature cũ. |
| **Doan et al.** (ICCV'19) [F] | HMM trên đồ thị map. Emission từ L-NN k-means tree (SIFT-VLAD). Accept nếu MaxAP ≥ γ = 0.3. **Cull/combine node** để map không phình. | RobotCar 6 sequence: mean err 6.6–30 m / median 5.7–13 m (tốt hơn MapNet, VidLoc). Suy luận ~4 ms. Update < 5 phút (MapNet 6 h). | Map tăng trưởng liên tục, không cần GNSS/VO. | Ngưỡng γ heuristic. Không đo FAR off-map. |
| **Doan et al.** (DICTA'19) [F] | HMM band v_max + MCVL (particle 6-DoF). | RobotCar 1 km/10 km và GTA-V synthetic: vượt PoseNet/MapNet (% trong ngưỡng). | Filter + retrieval thắng pose regression. | Không off-map, tham số tay. |
| **Xu, Sünderhauf, Milford** (RA-L'20) [F] | Discrete Bayes filter (λ theo quantile khoảng cách frame đầu) + MCL 6-DoF với VO. Phát hiện hội tụ (khối belief quanh MAP > τ). | RobotCar R@99%P (5 m, 30°), NetVLAD: Single 65.8/4.0/1.2 (rain/dusk/night) → Topological 91.7/92.0/57.6 → MCL 97.2/80.0/55.8. | Latency tự scale theo aliasing (6–18 bước). | MCL cần pose RTK. τ chọn bằng PR có nhãn. |
| **Xu, Fischer, Sünderhauf, Milford** (RA-L'21) [F] | Topometric filter, odometry 3-dof (Mahalanobis tới đoạn quỹ đạo). **Off-map state**: E_{i→O} = min χ²₃, emission O = match thứ k. Forward–backward. | R@99%P loop closure (HF-Net/NetVLAD): dusk 0.92/0.88, night 0.86/0.96, rain-detour 0.97/0.96, sun-detour 0.96/0.98 (No-Off 0.69/0.75 ở detour). Global loc. hội tụ trong 17–52 m. ~100 ms/bước. | Off-map đầu tiên cho VPR appearance-invariant. | Emission off-map heuristic. Tham số tune trên nhãn. Chỉ RobotCar. |
| **Stenborg et al.** (3DV'20) [C] | Filter odometry 1-D + smoothing lọc retrieval cho 6-DoF. | (Xu'21 Stenborg20 R@99%P night 0.57/0.89) | Smoothing giúp hierarchical. | Giả định không detour. |
| **CAT-SLAM, FAB-MAP** (2008–2012) [C] | Particle/Bayes trên BoW với new-place model. | Sattler'18: FAB-MAP gần 0 % trên RobotCar/CMU. | New-place awareness sớm. | Không chịu appearance change. |

### 6.4 Learned sequence / CRF / multi-hypothesis (2020–2026)

| Paper | Method | Benchmark | (+) | (−) |
|---|---|---|---|---|
| **SeqNet / SeqMatchNet** (Garg & Milford, 2021) [C], **SeqVLAD** (Mereu'22), **JIST** (Berton'24), **DeepSeqSLAM** (2020) [R] | Học sequence descriptor / sequence-matching contrastive. | (MSLS / Nordland seq, không trích số) | SOTA recall sequence-VPR. | Không off-map/confidence. Cần train. |
| **TRAIL** (Kloepfer & Wenzel, 2026) [R] | CRF chuỗi trên top-K (MegaLoc đóng băng). Emission MLP, transition CNN trên tương quan local DINOv2, dustbin state. **DB không thứ tự.** | R@1/5/10 (T = độ dài chuỗi): MSLS 55.1→56.5/65.2/66.7; Nordland 73.8→75.3/81.3/78.1; 4Seasons 69.4→71.0/78.2/79.0 (PairVPR 4Seasons 92.1). Chi phí bằng 1/7–1/9 re-ranker. | Task mới (sequence query, map không có route). | Cần train. Dustbin không calibrate. |
| **TAO / Route-MHT** (Lu & Tanaka, 2026, thermal) [R] | K = 100 nhánh hypothesis, SE(2) Procrustes batched SVD, ràng buộc vận tốc. | Map-out FPR 32.6 % → 4.9–11.9 %. Kidnapped recovery 4–5 frame. OOD AUC ở 5 m chỉ 0.54–0.57. | Fail-safe macro, O(KN). | Cần odometry, thermal. Không có đảm bảo. |

### 6.5 Ý tưởng đã bị chiếm (checklist chống trùng)
1. HMM/Viterbi thay SeqSLAM (Hansen'14). Band transition (Doan'19, Xu'20).
2. Emission exp(−λd) với λ theo quantile (Xu'20). Log-sum nhiều descriptor (MPF'19).
3. Odometry 1/3-dof trong transition. Forward–backward smoothing (Stenborg'20, Xu'21).
4. **Off-map/new-place state** (Xu'21, FAB-MAP/CAT-SLAM). Dustbin trong CRF (TRAIL'26).
5. Sequence length động (MPF'19). Latency tự scale theo convergence (Xu'20).
6. Map tăng trưởng, cull/combine (Doan'19). Multi-experience (Churchill & Newman'13).
7. Learned sequence descriptor (SeqNet, SeqVLAD, JIST). CRF học được (TRAIL'26).
8. Introspection cho sequence (SMR'25). Unsupervised consensus (Carson'23). Ngưỡng tự động (Vysotska'25,
   Schubert'21, Trinh'25, Mount'20).
9. Multi-hypothesis Procrustes cho map-out (TAO'26). Protocol xoá đoạn map khi đánh giá (TAO'26).
10. Temperature/likelihood theo điều kiện (CCBF nội bộ, negative).

### 6.6 Khoảng trống còn mở
- **Đảm bảo thống kê cho quyết định sequence/HMM** (P(accept | off-map) ≤ α, không nhãn, dưới shift). Hướng gợi ý:
  calibrate statistic cửa sổ trên pseudo-sequence của map (held-out traversal), hoặc e-process/anytime-valid test.
  Chưa thấy paper nào làm.
- **Off-map state được calibrate:** thay heuristic "match thứ k" (Xu'21) bằng likelihood ratio ước lượng từ map null.
  Phải đo FAR, không chỉ R@99%P.
- **Domain shift:** statistic chuẩn hoá theo spread có thể anti-conservative với query ngoại miền (thí nghiệm nội bộ
  Entry 14). MPF và Xu'20 dùng score chuẩn hoá nhưng chưa ai đo hiện tượng này.

---

## 6b. Bổ sung 2026-10-30: integrity, kiểm tra nhất quán odometry, thống kê tuần tự hợp lệ

*Tìm qua web search (abstract/tóm tắt, chưa đọc full text) để đối chiếu novelty của 3 đóng góp của dự án (§8).*

### 6b.1 Integrity / verification cho VPR và định vị bằng camera

| Paper | Method | Benchmark | (+) | (−) |
|---|---|---|---|---|
| **Claxton, Malone, Carson, Ford, Bolton, Shames, Milford** (RA-L'24) [R] | Integrity monitor MLP (thay SVM của các bản trước) dự đoán match VPR có tin được không. Hai cách dùng: loại match đơn lẻ; **"history of queries": chiếu tiến từ match đã xác minh gần nhất bằng odometry**. | Robot thật: lỗi along-track tới goal 9.8 → 3.1 m; lỗi định vị 2.0 → 0.5 m, precision 97 → 99 %. | Đóng vòng điều hướng thật. Không cần train lại theo môi trường. | Monitor học được, không có đảm bảo FAR. **Trùng ý tưởng với cổng dead-reckoning (GG) của dự án.** |
| **SAFEVPR** (Sier et al., arXiv 2605.28048, 2026) [R] | Score patch MNN trên DINOv2 + Mondrian conformal Learn-Then-Test để chọn ngưỡng accept theo FDR. | 23 setup cross-condition (Oxford RobotCar, NCLT, St Lucia), 3 backbone: hợp lệ cả 23 ở α = 0.10, FDR chấp nhận TB 0.014, TPR 0.75. | Có đảm bảo conformal (FDR), dùng cho sequence VPR. | Cần nhãn calibration; đảm bảo dựa trên exchangeability, nên khi đổi điều kiện chỉ còn hợp lệ thực nghiệm. Kiểm soát FDR của match được nhận, không phải FAR theo đoạn off-map. |
| **Gupta & Gao** (NAVIGATION'21, "Data-driven protection levels for camera and 3D map-based safe urban localization") [R] | DNN chấm điểm các state ứng viên bằng cách so ảnh với map LiDAR 3D; mô hình lỗi Gaussian mixture → protection level. | Đô thị, GNSS-denied. | Khái niệm protection level từ hàng không, áp cho camera + map. | Map LiDAR; protection level dựa mô hình lỗi học được. |
| **Mohanty, Gupta, Gao** (2021, Particle RAIM cho GNSS-camera) [R] | Particle filter + RAIM; phân phối vị trí từ camera qua map-matching để mô hình lỗi thị giác. | Mô phỏng + dữ liệu thật. | Xác suất false alarm / missed detection nhỏ hơn baseline. | Kết quả thực nghiệm, không phải đảm bảo. |
| **Zhu et al.** (2020, review integrity monitoring cho định vị thị giác) [R] | Tổng quan. | – | Nêu thiếu khung integrity trưởng thành là rào cản lớn nhất cho lái xe tự động. | – |
| **Miller et al.** (arXiv 2510.13464, 2025, "Through the Lens of Doubt") [R] | 3 metric uncertainty không huấn luyện từ similarity của VPR bất kỳ (= RS/SD/SU ở §5). | – | Rẻ, dùng cho loop closure. | Không đảm bảo. |
| **Sferrazza et al.** (2025, "To Match or Not to Match") [R] | Số inlier khớp hình học làm proxy uncertainty để quyết định có re-rank không. | – | | Không đảm bảo. |

### 6b.2 Kiểm tra nhất quán với odometry / robust back-end (gần với cổng GG)

| Paper | Ý chính | Liên hệ với dự án |
|---|---|---|
| **Olson** (2006 CSW, RSS'08) [R] | Ma trận nhất quán cặp đôi giữa các ứng viên loop closure, chọn tập con nhất quán lớn nhất. | Kiểm nhất quán với odometry để loại match aliasing. |
| **PCM** (Mangelson et al., ICRA'18), **group-k** (Forsgren et al., 2022) [R] | Pairwise Consistency Maximization → bài toán max-clique, giải realtime; group-k cho trường hợp cặp đôi chưa đủ. | Cùng mục tiêu loại loop closure sai bằng nhất quán hình học. |
| **Switchable constraints, DCS** [C] | Tắt / giảm trọng số ràng buộc có residual lớn. | Cổng mềm theo residual, tương tự g_t = exp(−d²/2s²). |
| **Tanaka** (2016, multi-model hypothesize-and-verify) [R] | Kiểm giả thuyết loop closure với VO / stereo SLAM. | |
| **Innovation gating (χ²) trong EKF** [C] | Bỏ đo có Mahalanobis lớn. | Chính là baseline `+DRgate`; khoá chết khi neo sai (Nordland). |
| **Murphy et al.** (arXiv 1809.09755, 2018, "Map matching when the map is wrong") [R] | Hợp nhất HMM map matching với free-space tracking: xe có thể ở trên **hoặc ngoài** mạng đường, vẫn có vị trí. | **Trạng thái off-map có vị trí** (ý DR của dự án) đã có trong map matching GPS. |
| **Newson & Krumm** (SIGSPATIAL'09) [R] | HMM map matching chuẩn. | Nền của các HMM VPR. |
| **Sensor resetting** (Lenser & Veloso, ICRA'00), **multi-observation SRL** (Coltin & Veloso, 2013), augmented MCL [R] | Bơm giả thuyết từ cảm biến khi robot bị lạc (kidnapped). | Tương đương sàn ρ của cổng GG (lối thoát khi neo sai). |

### 6b.3 Thống kê tuần tự hợp lệ, conformal dưới phụ thuộc và shift

| Paper | Ý chính | Liên hệ |
|---|---|---|
| **E-detectors** (Shin, Ramdas, Rinaldo, NEJSDS 2024) [R] | Tổng các e-process khởi động ở mọi thời điểm (kiểu Shiryaev–Roberts / CUSUM); cận ARL không tiệm cận, delay gần tối ưu. | Định lý ARL₀ của CPC-HMM dựa trực tiếp vào đây. |
| **Conformal test martingales** (Vovk et al., 2021; Fedorova et al. ICML'12) [R] | Đặt cược trên conformal p-value để kiểm exchangeability online / phát hiện change-point. | Họ hàng của chuỗi hiện diện dùng e-value từ p-value conformal. |
| **Detecting object tracking failure via sequential hypothesis testing** (Monroy Muñoz, Verma, Timans, arXiv 2602.12983, 2026) [R] | E-process trên chỉ số chất lượng của tracker để báo tracker hỏng, kiểm soát tỷ lệ báo sai. | **Rất gần** ý "e-process phát hiện mất định vị" của CPC-HMM, nhưng cho tracking đối tượng. |
| **Testing for outliers with conformal p-values** (Bates, Candès, Lei, Romano, Sesia, AoS) [R] | p-value conformal cho phát hiện ngoại lai; bản calibration-conditional. | Cơ sở của p-value SelfCal hiệu chuẩn bằng bản đồ. |
| **Conformal prediction beyond exchangeability** (Barber, Candès, Ramdas, Tibshirani, AoS 2023) [R] | Weighted quantile; cận mất coverage theo TV khi vi phạm exchangeability. | Có thể dùng để định lượng mất mát khi đoạn off-map không exchangeable với đoạn bản đồ. |
| **Exact and robust conformal inference with dependent data** (Chernozhukov, Wüthrich, Zhu, COLT'18) [R] | Hoán vị theo block giữ cấu trúc phụ thuộc; hợp lệ xấp xỉ cho quá trình mixing. | **Gần** cách hiệu chuẩn theo đoạn của certified. |
| **Conformal cho nhiều quỹ đạo exchangeable** (Stankeviciute et al. NeurIPS'21; Lindemann et al.; Zhou, Lindemann, Sesia arXiv 2402.09623) [R] | Coi mỗi quỹ đạo là một đơn vị exchangeable; Bonferroni theo bước (bảo thủ). | **Gần** ý "mỗi đoạn H frame là một đơn vị exchangeable, hiệu chuẩn max theo đoạn". |
| **Scan statistic** (Walther & Perry, JRSS-B 2022) [R] | Hiệu chuẩn max qua cửa sổ trượt, critical value phụ thuộc kích thước, Bonferroni scan. | Thống kê max R theo đoạn của certified là một scan statistic. |
| **Conformal không nhãn dưới shift**: Yilmaz & Heckel (2022), Kasa et al. (ECP/EACP, 2024), Correia & Louizos (NeurIPS'25, OT) [R] | Hiệu chỉnh ngưỡng conformal từ dữ liệu test không nhãn. | Chỉ đảm bảo dưới mô hình shift hạn chế; **không có đảm bảo tổng quát** khi không có nhãn. Dự án tránh vấn đề này bằng cách hiệu chuẩn trên chính bản đồ. |
| **Provably guaranteed polytopic UQ for SLAM** (arXiv 2605.28172, 2026) [R] | Conformal hiệu chuẩn bất định đo cho SLAM; tập rỗng → loại loop closure sai. | Conformal trong SLAM, khác mục tiêu (bất định pose, không phải FAR off-map). |
| **Tempering the Bayes filter** (arXiv 2512.02823, 2025) [R] | Tempering likelihood / posterior của Bayes filter; tempered Kalman. | Liên quan Mệnh đề 2 (đếm thừa bằng chứng phụ thuộc); không có quy tắc chọn lũy thừa theo tương quan. |

### 6b.4 Existence / track presence

| Paper | Ý chính | Liên hệ |
|---|---|---|
| **IPDA, Bernoulli filter** (Musicki et al.; Ristic et al.) [R] | Ước lượng đồng thời trạng thái và xác suất tồn tại của mục tiêu. | Chuỗi hiện diện của CPC-HMM là chuỗi tồn tại kiểu IPDA. |
| **Gies et al.** (arXiv 2003.10316, 2020) [R] | LMB filter + bản đồ số → "extended existence probability" để xác minh đối tượng. | Gần nhất với "existence + map", nhưng cho phát hiện đối tượng. |

### 6b.5 Bổ sung checklist chống trùng (nối §6.5)
11. Monitor integrity cho VPR + **chiếu tiến bằng odometry từ match đã xác minh** (Claxton RA-L'24).
12. Kiểm nhất quán loop closure với odometry (Olson'06/'08, PCM'18, group-k); innovation gating χ².
13. Trạng thái "ngoài mạng" **có vị trí** trong HMM map matching (Murphy'18).
14. E-process phát hiện tracker hỏng với đảm bảo tỷ lệ báo sai (arXiv 2602.12983, 2026).
15. Conformal LTT/FDR cho sequence VPR (SAFEVPR'26, có nhãn).
16. Coi quỹ đạo/đoạn là đơn vị exchangeable cho conformal (Stankeviciute'21, Lindemann, Zhou'24); block conformal
    (Chernozhukov'18); scan statistic (Walther & Perry'22).

---

## 7. Datasets tham chiếu nhanh

| Dataset | Loại | Quy mô | Thách thức | Dùng bởi |
|---|---|---|---|---|
| Pitts30k / Pitts250k | đô thị, Street View | 10k/84k DB, 6.8k/8.2k query | viewpoint, aliasing | hầu hết VPR |
| MSLS val / challenge | dashcam 30 thành phố | 18.9k DB / 740 query (val) | mùa, ngày/đêm, cũ/mới | VPR, TRAIL, **SelfCal (CPH+SF)** |
| Tokyo 24/7 | đô thị | 76k / 315 | ngày/đêm | VPR |
| Nordland | tàu hoả 4 mùa | 27.6k frame/mùa | mùa, aliasing tự nhiên | VPR, HMM, **SelfCal** |
| SPED, St Lucia, Eynsham, AmsterTime, SVOX, SF-XL, Baidu | đa dạng | – | webcam, ngoại ô, lịch sử, thời tiết, quy mô thành phố, indoor | VPR |
| Aachen Day-Night | thành phố cổ | 4.3k ảnh, 922 query | ngày/đêm 6-DoF | structure-based |
| RobotCar Seasons | Oxford | 20.9k ref, 11.9k query | 9 điều kiện 6-DoF | structure-based, **SelfCal** |
| (Extended) CMU Seasons | Pittsburgh | 7.2k ref, 75k query | mùa, tán lá | structure-based, **SelfCal** |
| Cambridge Landmarks, 7/12-Scenes | outdoor/indoor nhỏ | 5 / 7 scene | pose cm | APR, SCR, Reloc3r |
| LaMAR | AR indoor/outdoor | 3 địa điểm | phone/HoloLens | MegaLoc, hloc |
| 4Seasons | lái xe Munich, 30 recording | 7 scene | mùa, xám | TRAIL, Carson'23; **poses đã upload Kaggle** |

---

## 8. Định vị 3 đóng góp của dự án so với tài liệu (2026-10-30)

| Đóng góp | Phần đã có trong tài liệu | Phần mới (theo những gì đã tìm) | Mức novelty |
|---|---|---|---|
| **A. Certified sequential localization** (FAR theo đoạn off-map ≤ α, không nhãn, hiệu chuẩn bằng traversal bị giữ lại của chính bản đồ) | Conformal với đơn vị exchangeable là quỹ đạo (Stankeviciute, Lindemann); block conformal (Chernozhukov); scan statistic; conformal outlier p-value (Bates); conformal FDR cho sequence VPR **có nhãn** (SAFEVPR). | Dùng **bản đồ làm nguồn null** (không nhãn của điều kiện deploy), đảm bảo **mức đoạn** cho định vị chuỗi, thống kê neo odometry. Chưa thấy paper VPR/localization nào làm. | Trung bình–khá. Công cụ thống kê đã biết; cách đặt bài toán và giao thức là mới. |
| **C. CPC-HMM** (chuỗi hiện diện kiểu IPDA nuôi bằng e-value hiệu chuẩn bằng bản đồ; ARL₀ ≥ (1−p)/p − R₀) | E-detectors (Shin et al.); conformal test martingales; IPDA/Bernoulli; off-map state (Xu'21), dustbin (TRAIL'26); e-process cho tracking failure (2026). | Áp e-detector cho chuỗi on/off **lặp lại** của HMM VPR (domination bởi SR), e-value không nhãn từ bản đồ, cổng khớp MAP giữ tính e-value. | Trung bình. Định lý ngắn, ghép từ khối có sẵn. |
| **C+. Cổng dead-reckoning (+GG)** | Claxton RA-L'24 (chiếu tiến bằng odometry); PCM/Olson; χ² gating; Murphy'18 (off-road có vị trí); sensor resetting (sàn ρ). | Cổng nhân lên một e-value nên **giữ ARL₀**; sàn ρ làm lối thoát; chẩn đoán "fix sai ở xa do chuỗi vị trí trôi trong lỗ bản đồ". | Thấp–trung bình (gia tăng). |

**Kết luận novelty:** không có đóng góp nào bị chiếm hoàn toàn, nhưng cả ba đều là **ghép công cụ đã biết** vào một bài
toán mới. Điểm mạnh nhất là A (đảm bảo không nhãn ở mức đoạn, thắng các baseline dùng nhãn về tính hợp lệ). Đánh giá chi
tiết khả năng vào venue A/A* ở `LITERATURE_GATE.md` Gate 9.

