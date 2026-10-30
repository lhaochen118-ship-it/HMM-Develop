# 03 — Handoff (khung chat mới, branch `hmm-navigation-2`)

*2026-10-29. Chỉ ghi mục tiêu, trạng thái, quyết định đã chốt, vị trí mọi thứ và việc tiếp theo. Nội dung khoa học chi
tiết ở `01_SCIENTIFIC_FINDINGS`; kinh nghiệm vận hành ở `02_ENGINEERING_OPS_NOTES` (§8).*

## 1. Mục tiêu nghiên cứu

- **Đề bài gốc:** HMM cho định vị theo chuỗi (sequence-based visual localization) với camera đơn cho robot navigation,
  trên nền Sattler et al. CVPR'18.
- **Mục tiêu:** đóng góp đủ mạnh cho venue A\*.
- **Hướng đang theo:**
  1. **Certified sequential localization** (hướng chính, đã vững): bảo đảm FAR theo đoạn off-map, không cần nhãn.
  2. **CPC-HMM** (module): sửa các điểm yếu cấu trúc của HMM. Thắng HMM Xu'21 trên 5/7 dataset, thua trên **Boreas**
     và **RobotCar**.

## 2. Trạng thái hiện tại (một dòng mỗi mục)

- **Certified:** hợp lệ trên 7/7 dataset, power gấp 1.3–2.7× per-frame. Báo cáo ngắn ở `paper/BAO_CAO_CertSeq.pdf`
  (cần rebuild).
- **CPC-HMM:**
  - lý thuyết (ARL₀, Shiryaev–Roberts, Anderson) ở `paper/cpc_theory.md`;
  - ARL₀ thực nghiệm 762–3930, vượt cận 98;
  - novelty ở `LITERATURE_GATE.md` Gate 7.
- **Boreas:**
  - Đã sửa lỗi odometry (bước nhảy 8.7 km).
  - Còn thua Xu'21 khoảng 3× về sai số điều hướng (21.0 m so với 6.2 m), do độ trễ khi rời bản đồ và e^R vi phạm D_R.
  - Ngược lại, khi bản đồ khuyết 50 % thì CPC thắng: 13.7 m so với 40.8 m.
- **Đang chạy trên Kaggle:** xem `handoff/RUNNING_KERNELS.md`.
  - navF/navFc/navG: điều hướng đầy đủ có biến thể `CPC-HMM p_out=*`.
  - fix7: `hmm_fix` 7 dataset, gồm quét p_out, a_t dự đoán được và KL.
  - bfix: Boreas `hmm_fix` + `cert_seq` với odometry đã sửa.
  - fix6: `hmm_fix` với null cũ, bị fix7 thay thế.

### Cập nhật 2026-10-30 (khung chat `hmm-navigation-2`)

- **Bước 1 đã xong:** CPC-HMM + cổng dead-reckoning (`+GG`, ρ = 0.1) thắng Xu'21 trên 6/6 descriptor Boreas (trung bình
  7.1 so với 22.6 m) và trên trung bình cả 6 dataset; không làm CPC-HMM tệ đi ở dataset nào. Chi tiết: `RESEARCH_LOG.md`
  Entry 22, `paper/cpc_theory.md` §3b, báo cáo `paper/BAO_CAO_CertSeq.pdf` §5.4, Gate 8.
- **Đã thử và loại:** p_out cố định hoặc theo KL₀; rò rỉ ở mép bản đồ; cổng dự đoán (PG); vào lại theo dead-reckoning (DR).
- **Việc tiếp theo gợi ý:**
  1. chạy lại `hmm_fix.py` với +GG để có ARL₀, recall, ECE (chưa có);
  2. RobotCar trong lưới điều hướng (snippet 9 frame);
  3. độ bền theo tỷ lệ lỗ 10 % / 50 % cho +GG (`nav_demo` chưa có `--drop`);
  4. benchmark chuỗi dài mới (NCLT, Oxford RobotCar gốc) nếu muốn chứng minh tổng quát hơn;
  5. kiểm thêm các giá trị ρ (0.03, 0.3) để báo độ nhạy.
- **Kaggle:** `nhatlong1103` và `huyenco` hết quota GPU tuần (30 h) lúc 2026-10-29 tối; dùng CPU cho 2 acc này.

## 3. Quyết định đã chốt (không bàn lại trừ khi user yêu cầu)

1. **Không viết paper.** Chỉ báo cáo PDF ngắn **tiếng Việt**: method + công thức, bảng kết quả, so sánh baseline mới
   nhất, **không hình**. Chỉ viết khi có phương pháp novel và thực nghiệm ủng hộ mạnh.
2. **Không làm phương pháp nào phụ thuộc nhãn** của điều kiện deploy. Baseline dùng nhãn chỉ để so sánh.
3. **Không bỏ phương pháp chỉ vì yếu trên chuỗi ngắn** (RobotCar). Bổ sung benchmark chuỗi dài thay vì bỏ.
4. **Tài nguyên:**
   - Dùng **hết GPU** (8 acc × 2 T4; GPU của `mucnokieu` hay bị người khác chiếm). RTX PRO 6000 chỉ cho việc rất lớn.
   - Hết GPU: job **rất nhẹ** (dưới khoảng 30 phút trên CPU, ví dụ nav_demo CMU/4S/Nordland, phân tích offline) thì chạy CPU (5 phiên mỗi acc); job **nặng** (Boreas nav_demo/hmm_fix, dump descriptor) thì **đợi GPU trống**, không đẩy sang CPU (user chốt 2026-10-30).
   - Kernel kẹt hàng đợi quá 10 phút thì huỷ và chạy lại, tối đa 4 lần, rồi mới tìm lỗi.
5. **Dữ liệu mới:**
   - Upload lên acc `nhatlong1103`, để **public**.
   - Cập nhật `ENVIRONMENT_SUMMARY` (tên, link, cấu trúc).
   - Xoá bản cũ đã có bản thay. Môi trường chặn lệnh xoá hàng loạt, nên xoá từng lệnh hoặc nhờ user.
6. **User không quan tâm bảo mật**, nhưng token **không** được commit (repo public). Token đặt ở `~/.kaggle/tok_<acc>`.
7. **Định kỳ kiểm tra tiến trình treo** và tự chạy lại. Cái gì không tự ngắt được thì báo user.
8. **Git:**
   - Làm và push trên branch được giao (`hmm-navigation-2`); không tạo PR.
   - Commit có trailer `Co-Authored-By` / `Claude-Session`, không ghi model ID.

## 4. Vị trí mọi thứ

| Cái gì | Ở đâu |
|---|---|
| Dataset, dump, acc Kaggle | `handoff/ENVIRONMENT_SUMMARY.md` (§1, §1b 4Seasons, §1c Boreas, §3 acc) |
| Code phương pháp | `analysis/cert_seq.py` (certified), `analysis/hmm_fix.py` (CPC-HMM + ablation + Xu'21), `analysis/nav_demo.py` (điều hướng), `analysis/hmm_diag.py` (chẩn đoán), `analysis/selfcal.py` (p-value), `analysis/vprlib.py` (loader) |
| Hạ tầng Kaggle | `automation/fanout.py`, `make_eval_kernel.py`, `run_kernel.py`, `reattach.py`, `resume.py`, `pull_kernels.py` |
| Kết quả | `analysis/results/{cert,nav,natural,hmmdiag,hmmfix,hmmfix_d10,hmmfix_d50}_*.json` |
| Báo cáo và bảng | `paper/BAO_CAO_CertSeq.{md,pdf}` (`build_report.py`), `paper/cert_tables.md` (`build_cert_tables.py`) |
| Lý thuyết CPC-HMM | `paper/cpc_theory.md` |
| Nhật ký và novelty | `RESEARCH_LOG.md` (Entry 18–21), `LITERATURE_GATE.md` (Gate 6–7), `DATA_AUDIT.md` |
| Kernel đang chạy | `handoff/RUNNING_KERNELS.md` (kéo bằng `python3 automation/pull_kernels.py`) |
| Script chẩn đoán offline | `analysis/navdiag.py`, `analysis/presence_variants.py`: đọc `navframes_*.npz` từ `nav_demo --dump`. File npz nằm trong output kernel (bfix, enull, cdiag, bdiag), không có trong git |

## 5. Việc tiếp theo (theo thứ tự ưu tiên của user)

### Bước 0 — Khởi động (khoảng 15 phút)

1. Tạo `~/.kaggle/tok_<acc>` từ tin nhắn user (thứ tự acc ở `ENVIRONMENT_SUMMARY` §3).
2. `pip install kaggle markdown xhtml2pdf`.
3. `python3 automation/pull_kernels.py /tmp/kpull`: kéo kết quả các kernel đã xong. Kernel chưa xong thì kéo lại sau.
4. Tổng hợp:
   - `nav_*`: luật `CPC-HMM p_out=0.05/0.1/0.2` so với Xu'21, per-frame, certified;
   - `hmmfix_*` của fix7: `cpc_pout*`, `cpc_p*`, `cpc_pred`, `KL`, `ARL0`.
5. Ghi Entry 22 vào `RESEARCH_LOG.md`.

### Bước 1 — Chạy tiếp hướng CPC-HMM (đang làm dở)

- **Mục tiêu:** CPC-HMM không thua Xu'21 trên Boreas, mà không làm hỏng các dataset khác. Dùng **một** cấu hình chung,
  chọn bằng lý thuyết hoặc không nhãn, không tune theo từng dataset.
- **Ứng viên đã có cơ sở:**
  1. **p_out không nhãn:**
     - độ trễ khi rời bản đồ ≈ log((1−p_out)/p_out)/|KL₀|;
     - KL₀ = E₀[log LR] ước lượng được trên các pseudo-query của null bản đồ (là mẫu H0);
     - chọn p_out sao cho độ trễ ≤ L frame (ví dụ 3);
     - so tỷ lệ rơi on-map ước lượng từ Beta(a,1) đã fit.
  2. **Sửa e^R (D_R):**
     - Dựng null R trên **đoạn giữ lại dài** (nhiều block liên tiếp), để mô phỏng aliasing kết hợp trong đoạn off-map
       dài.
     - Hoặc bỏ e^R, chỉ dùng e^top (vốn hợp lệ ở mọi dataset), rồi bù power bằng chuỗi vị trí.
     - Kiểm bằng P(p^R ≤ u | off) ≤ u, dùng `presence_variants.py` trên npz.
  3. **Theo dõi:** độ trễ vào lại (Nordland chậm hơn Xu'21), và việc CPC-HMM thiếu tự tin (ECE).
- **Tiêu chí dừng:** sau 2–3 vòng mà Boreas vẫn thua Xu'21 (sai số điều hướng trung bình qua 6 descriptor) thì sang
  Bước 2.

### Bước 2 — Đi sâu vào nơi HMM thua baseline

- Phân tích theo bản chất toán, thuật toán, mô hình và bài toán tại **chính các chỗ thua**:
  - Boreas: Xu'21 mạnh vì odometry gần hoàn hảo và tuyến lặp lại;
  - RobotCar: snippet 9 frame;
  - 4S countryside: bằng chứng yếu, ARL₀ và FL cao.
- Đề xuất **một** module, công thức, cơ chế hoặc kỹ thuật cho HMM. Gợi ý chưa kiểm novelty:
  - tái khởi động có hiệu chuẩn (sensor resetting) cho chuỗi vị trí, có trọng số theo local fdr của top-1;
  - p_out thích nghi theo KL ước lượng online;
  - emission có tính tới phụ thuộc (ESS chỉ cho tầng hiện diện).
- Mỗi đề xuất phải qua gate novelty (`LITERATURE_GATE.md`).

### Bước 3 — Nếu vấn đề nằm ở bản chất dataset

Nếu dataset không phù hợp với phương pháp (ví dụ snippet quá ngắn, hoặc tuyến lặp lại với odometry gần như GT khiến
HMM thường đã đủ mạnh): bỏ qua dataset đó và tìm **benchmark mới uy tín, phù hợp hơn**. Yêu cầu: chuỗi dài, odometry
thật, nhiều điều kiện, có GT pose. Ứng viên cần kiểm tra license và cách tải:

| Dataset | Ghi chú |
|---|---|
| NCLT (Michigan) | 27 phiên trong 15 tháng, odometry bánh xe + IMU, GT RTK/SLAM |
| Oxford RobotCar gốc | Chuỗi dài, VO + INS; RobotCar-Seasons chỉ là tập con ngắn |
| Oxford Radar RobotCar | |
| St Lucia | |
| SFU Mountain | |
| KITTI / KITTI-360 | Có vòng lặp, odometry |

Thêm dataset theo quy trình §3.5 (upload `nhatlong1103`, public, cập nhật `ENVIRONMENT_SUMMARY`).

### Bước 4 — Báo cáo

Khi có kết quả mạnh: rebuild `paper/BAO_CAO_CertSeq.pdf` (`paper/build_report.py` đã có mục 5 về HMM và CPC-HMM; cần
thêm luật p_out mới nếu được chọn), rồi commit và push.

## 6. Lưu ý chuyển giao

- Trigger kiểm tra hằng giờ của khung chat cũ **đã tắt**. Khung chat mới tự đặt lịch kiểm tra nếu cần.
- Scratchpad của khung chat cũ (thư mục `runs/` với kernel dir và npz) **không** sang được khung chat mới. Mọi thứ cần
  kéo lại đều nằm trên Kaggle theo `RUNNING_KERNELS.md`.
