# KẾ HOẠCH VẬN HÀNH, NGHIÊN CỨU VÀ CHUYỂN GIAO

*Phiên bản 1.1 — viết lại từ bản nháp "Prompt_Agent_Research_improve.docx" (v1.0 dựa trên "Prompt_Agent_Research.docx"; v1.1
bỏ phần cuộc thi Zalo DataMate, thay bằng quy trình chung cho nhánh đề tài mới). Tài liệu này quy định **cách agent làm việc**
(tài nguyên, quy trình, kiểm soát chất lượng, bàn giao). **Nội dung khoa học** (giả thuyết, giai đoạn, metric) nằm ở
`docs/MASTER_RESEARCH_PLAN.md`; hai tài liệu không lặp lại nhau.*

---

## 0. Những điểm đã sửa so với bản nháp (đọc trước)

| # | Vấn đề trong bản nháp | Cách xử lý trong bản này |
|---|---|---|
| 1 | Ngưỡng "không có output" mâu thuẫn: 5 phút (L4/CPU) ở §2 và §5, trong khi tài liệu trước dùng 8 phút | Thống nhất một bảng ngưỡng duy nhất (§3.3), có phân biệt *đang xếp hàng* với *đang chạy mà im lặng* |
| 2 | Metadata L4 tự mâu thuẫn: `"accelerator": "nvidiaL4"` nhưng `"isGpuEnabled": false`; `sourceId: 149921` ở một chỗ, `COMPETITION_SLUG` ở chỗ khác | Một mẫu `kernel-metadata.json` duy nhất, có trường bắt buộc điền và bước kiểm tra GPU thực tế khi kernel khởi động (§3.4) |
| 3 | Mục "4.1/4.2" không có mục 4 cha; GPU nằm ở §3, metadata ở §4 | Gộp thành một chương tài nguyên tính toán (§3) |
| 4 | "Không cần tiết kiệm GPU" mâu thuẫn với "kiểm tra giờ GPU còn lại trước khi chạy" | Quy tắc rõ: **tối ưu thời gian ra kết quả** trong giới hạn quota; luôn ước lượng trước khi chạy (§3.5) |
| 5 | Đề xuất FSDP cho mọi nhánh | FSDP chỉ có ích khi *mô hình* không vừa một GPU. Phần lớn việc của đề tài (trích descriptor, matching, HMM) là suy luận → **chia dữ liệu theo GPU** nhanh và đơn giản hơn (§3.2) |
| 6 | Dùng Kaggle Dataset *public* cho mọi thứ | Dataset bên thứ ba (RobotCar, CMU, Nordland, …) có license hạn chế phân phối lại → để **private** và chia sẻ cho các tài khoản; chỉ code/kết quả tự tạo mới để public (§4.1) |
| 7 | Mục 9.3 và 10 đều "sao chép nhánh hiện tại" nhưng không nói làm trước hay sau dọn dẹp/bàn giao | Quy định rõ: dọn dẹp → bộ bàn giao → mới tạo nhánh (§7.3, §8) |
| 8 | Mục tiêu nghiên cứu nói về robot nhưng không nêu yêu cầu tổng quát hoá ở phần mục tiêu, chỉ ở phần quy trình | Đưa yêu cầu "phương pháp tổng quát" lên §1 |

---

## 1. Mục tiêu và phạm vi

**Đề tài chính:** định vị thị giác cho robot (visual localization) bằng Hidden Markov Model trên chuỗi ảnh từ một camera đơn
(monocular, sequence-based), khai thác thông tin thời gian để định vị ổn định và đáng tin cậy hơn so với từng ảnh độc lập.

**Tài liệu nền tảng:** Sattler et al., *Benchmarking 6DOF Outdoor Visual Localization in Changing Conditions*, CVPR 2018.

**Yêu cầu đối với phương pháp:** tổng quát, áp dụng được cho nhiều dataset và descriptor; **không** chỉnh cứng cho một dataset.
Ưu tiên cơ chế/công thức mới có cơ sở toán học hơn là lắp ghép module có sẵn; mục tiêu là đủ novelty và bằng chứng
thực nghiệm cho venue A/A*. Không được tuyên bố novelty hay SOTA khi chưa có bằng chứng.

**Đề tài khác:** thực hiện trên nhánh riêng theo quy trình chung ở §8.

---

## 2. Thiết lập tài khoản và bảo mật

1. Cấu hình Kaggle CLI cho từng tài khoản bằng `KAGGLE_API_TOKEN` hoặc `~/.kaggle/access_token` (quyền 600). Kiểm tra
   kết nối bằng `kaggle competitions list`.
2. Lưu danh sách token **ngoài repo** (ví dụ `~/.kaggle/accounts.json`, quyền 600). Không đưa token vào prompt, mã nguồn,
   notebook, log, commit hay báo cáo. Script chỉ đọc token từ file/biến môi trường.
3. Lập `Process/accounts_status.md` (không chứa token) ghi: tên tài khoản, quota GPU còn lại, số phiên đang chạy, ngày reset.

---

## 3. Tài nguyên tính toán

### 3.1 Hạn mức (theo cấu hình người dùng cung cấp — kiểm chứng lại khi phiên đầu chạy)
| Loại | Mỗi tài khoản | Cấu hình phiên |
|---|---|---|
| GPU commit | tối đa 2 phiên đồng thời | 4 × NVIDIA L4 (24 GB/GPU; 96 GB **phân tán**, không phải một khối liền) — dự phòng: 2 × T4 |
| CPU commit | tối đa 5 phiên đồng thời | CPU |

### 3.2 Chiến lược dùng GPU
- **Quy tắc chọn kiểu song song:**
  | Loại việc | Cách làm |
  |---|---|
  | Suy luận/trích đặc trưng, matching, đánh giá | Chia dữ liệu thành shard; **mỗi GPU một tiến trình độc lập**, gộp kết quả cuối |
  | Nhiều cấu hình thử nghiệm nhỏ (vừa 24 GB) | **Mỗi GPU một thử nghiệm** → 4 thử nghiệm/phiên, 8/tài khoản |
  | Huấn luyện mô hình vừa một GPU | DDP trên 4 GPU |
  | Huấn luyện mô hình không vừa một GPU | FSDP (hoặc model sharding) |
- Dùng BF16/FP16, batch size lớn nhất không OOM (dò tự động, chừa ~10% VRAM), DataLoader nhiều worker, `pin_memory`.
  Mục tiêu là throughput cao và GPU không nhàn rỗi; dùng gần hết VRAM chỉ là phương tiện, không phải mục tiêu.
- Đầu mỗi kernel in tên GPU, số GPU, VRAM; nếu cấu hình nhận được khác cấu hình yêu cầu → ghi log và tự điều chỉnh
  số shard (không chạy giả định 4 GPU trên máy 2 GPU).
- Lấp đầy slot theo thứ tự: dùng hết 2 phiên GPU của một tài khoản rồi mới sang tài khoản tiếp theo.
- Việc dài: lưu checkpoint/kết quả từng shard thường xuyên để có thể **tiếp tục ở tài khoản khác** khi hết quota hoặc lỗi.

### 3.3 Giám sát phiên và xử lý treo (một bảng thống nhất)
| Tình trạng | Ngưỡng | Hành động |
|---|---|---|
| Phiên ở trạng thái chờ/khởi tạo, không có output | T4: 10 phút · L4: 8 phút · CPU: 5 phút | Huỷ, tạo lại phiên; tối đa 4 lần |
| Đã chạy nhưng không in thêm output | > 2 × thời gian giữa hai lần log dự kiến | Kiểm tra log một phần; nếu treo thật → huỷ, sửa, chạy lại |
| Thất bại sau 4 lần tạo lại | – | Kiểm tra log, quota, metadata, lỗi code; L4 không cấp được → chuyển 2 × T4 |
| Không huỷ được bằng mọi cách | – | Báo người dùng huỷ thủ công (kèm tên tài khoản và kernel) |
| Hết GPU ở mọi tài khoản | – | Việc nhẹ chạy CPU; việc nặng xếp hàng chờ GPU |

Mọi kernel phải in log tiến độ đều đặn (ví dụ mỗi 1–2 phút) để phân biệt "đang chạy" với "treo".

### 3.4 Mẫu `kernel-metadata.json` cho L4 (một mẫu duy nhất)
```json
{
  "id": "<username>/<kernel-slug>",
  "title": "<kernel-slug>",
  "code_file": "<notebook>.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": true,
  "enable_gpu": true,
  "enable_internet": false,
  "machine_shape": "NvidiaL4",
  "competition_sources": ["<COMPETITION_SLUG>"],
  "dataset_sources": ["<owner>/<dataset>", "..."],
  "kernel_sources": [],
  "model_sources": []
}
```
- `<COMPETITION_SLUG>` là slug của cuộc thi cấp quyền L4 (bản nháp có `sourceId: 149921` — cần xác định slug tương ứng
  một lần và ghi vào `Process/accounts_status.md`).
- Phần `"kaggle": {...}` trong metadata của notebook (trường `accelerator`, `isGpuEnabled`) phải **khớp** với file trên:
  `"accelerator": "nvidiaL4"`, `"isGpuEnabled": true`, `"isInternetEnabled": false`.
- Xác nhận bằng dòng in tên GPU ở cell đầu tiên; nếu nhận T4 thì cấu hình chưa có hiệu lực.
- Dự phòng T4: bỏ `machine_shape` và `competition_sources`.

### 3.5 Kiểm tra trước khi chạy (bắt buộc)
1. **Ước lượng thời gian:** chạy thử trên tập con nhỏ (≤ 10 phút), đo throughput, ngoại suy thời gian toàn bộ.
2. **So với quota còn lại.** Nếu không đủ: tối ưu (batch, precision, chia shard thêm GPU/tài khoản, cache đặc trưng, bỏ bước
   thừa) → nếu vẫn không đủ: chia thành nhiều lần chạy có checkpoint qua nhiều tài khoản → nếu vẫn không khả thi: **không chạy**,
   ghi lý do và đề xuất phương án khác.
3. **Review code trước khi đẩy lên:** kiểm tra công thức, shape/dtype/device, đường dẫn, xử lý NaN, lưu kết quả từng phần;
   chạy unit test cục bộ (CPU) cho phần logic. Mục tiêu: không để lỗi xuất hiện giữa lần chạy dài.

---

## 4. Tối ưu quy trình

### 4.1 Tài sản dùng chung
- Thư viện/weights cần chạy offline: tải trước, đóng gói thành Kaggle Dataset (`bundle`) gắn vào mọi kernel.
- **Phạm vi công khai:** code và kết quả tự tạo → có thể public. Dữ liệu và weights của bên thứ ba → giữ private và chia sẻ cho các
  tài khoản cần dùng, trừ khi license cho phép phân phối lại.
- Kết quả tính toán đắt (descriptor, ma trận similarity, VO, kết quả matching) lưu thành "feature bank" có version để không
  phải tính lại; code đặt trên nhánh GitHub hiện tại.

### 4.2 Thông báo tự động (tiết kiệm token của agent)
- Mỗi lần push kernel đều chạy kèm script nền theo dõi trạng thái (`automation/kaggle_run.py` / `poll_pull.py`). Script tự
  tải output khi xong, trích `metrics.json` và ghi bản ghi vào registry (`automation/log_run.py`).
- Agent nhận thông báo khi tiến trình nền kết thúc, **không** tự kiểm tra lặp lại thủ công.

### 4.3 Tra cứu tài liệu
Ưu tiên đọc paper, tài liệu chính thức và README; chỉ đọc mã nguồn repository khi cần chi tiết triển khai cụ thể.

---

## 5. Quy trình nghiên cứu

Mỗi vòng lặp xử lý **một** giả thuyết:

1. **Hiểu vấn đề:** phân tích bản chất toán học, mô hình, thuật toán và nguyên nhân thất bại hiện tại.
2. **Tham khảo:** paper/tài liệu liên quan; kiểm tra trùng lặp (§6).
3. **Đề xuất:** giải pháp nhắm vào nguyên nhân gốc, kèm giả thuyết và dự đoán định lượng viết trước khi chạy.
4. **Thiết kế thí nghiệm:** dataset, split chống rò rỉ, baseline, metric, tiêu chí ủng hộ/bác bỏ.
5. **Triển khai và kiểm tra** (§3.5), chạy smoke test rồi chạy thật qua Kaggle CLI.
6. **Phân tích:** so với dự đoán; tìm nguyên nhân khi lệch.
7. **Quyết định:** giữ, cải tiến hoặc loại bỏ — ghi vào `research/DECISIONS.md`.

Ghi nhận: mọi run (kể cả thất bại) vào `research/registry/runs.jsonl`; findings, giả thuyết, quyết định trong `research/`.
Không con số nào được báo cáo mà không có `run_id`.

---

## 6. Khảo sát Related Work và kiểm tra trùng lặp

1. Khảo sát nghiên cứu về HMM/Bayes filter trong sequence-based visual localization và robot navigation (giai đoạn này
   chỉ đọc paper).
2. Với mỗi công trình ghi: bài toán, phương pháp, đóng góp, kết quả tích cực, hạn chế/kết quả tiêu cực, khoảng trống còn lại.
3. Lập bảng so sánh các phương pháp, làm rõ điểm giống/khác với hướng của dự án.
4. Kiểm tra method/contribution hiện tại đã xuất hiện chưa; nếu trùng → điều chỉnh hướng **trước** khi đầu tư thực nghiệm lớn.
5. Ghi toàn bộ vào `research_log.md` (mục Related Work), kèm trạng thái kiểm chứng trích dẫn.

---

## 7. Dọn dẹp, bàn giao và nhánh tiếp nối

### 7.1 Dọn dẹp nhánh
Xoá bản nháp, log và tệp lỗi thời chắc chắn không còn dùng. **Không xoá** mã nguồn, cấu hình, kết quả, registry và tài liệu
quan trọng. Danh sách tệp bị xoá ghi trong commit message.

### 7.2 Bộ bàn giao (cho khung chat mới)
| Tệp | Nội dung | Không chứa |
|---|---|---|
| **PDF 1 — Scientific Findings** | Đóng góp, ý nghĩa khoa học, kết quả tích cực/tiêu cực, bằng chứng (`run_id`) và điều kiện kiểm chứng | Chi tiết vận hành |
| **PDF 2 — Engineering & Operations Lessons** | Kinh nghiệm code, môi trường, quản lý Kaggle, tổ chức thử nghiệm, lỗi đã gặp và cách sửa | Kết quả khoa học |
| **PDF 3 — Handoff** | Mục tiêu, tiến độ, quyết định đã chốt, vị trí code/dữ liệu/kết quả, việc tiếp theo | Chi tiết của PDF 1–2 |
| `Process/` | Tất cả tệp có thể chuyển giao: code, script automation, file theo dõi tiến độ, cấu hình, registry, kết quả nhỏ | Token, dữ liệu thô, file lớn (để trên Kaggle Dataset, ghi đường dẫn) |
| `READ_ME_FIRST.md` | Thứ tự đọc repository và danh sách việc tiếp theo | – |
| Cập nhật | `Research Workflow.pdf` và `environment_summary.pdf` theo trạng thái mới nhất | – |

Chỉ những gì không chuyển giao được (phiên Kaggle đang chạy, token, môi trường cục bộ) mới để khung chat mới dựng lại; ghi rõ
trong PDF 3 cách dựng lại.

### 7.3 Nhánh tiếp nối cùng đề tài
Tạo nhánh mới từ nhánh hiện tại (sau 7.1–7.2), commit `READ_ME_FIRST.md` trên nhánh đó.

---

## 8. Nhánh cho đề tài khác

1. **Thời điểm:** sau khi đã dọn dẹp (§7.1) và lập bộ bàn giao (§7.2), để nhánh mới kế thừa trạng thái gọn và mới nhất.
2. **Tạo nhánh** từ nhánh hiện tại, đặt tên theo đề tài mới.
3. **Lược bỏ** mọi tệp đặc thù đề tài HMM (notebook, nguồn cell, kết quả, findings, pilot, tài liệu khoa học).
4. **Giữ lại** tài nguyên dùng chung: tài liệu vận hành này, `automation/` (build notebook, chạy/theo dõi Kaggle, `log_run.py`),
   `research/templates/`, khung thư mục `research/` (STATE, HYPOTHESES, FINDINGS, DECISIONS, ISSUES — để trống), quy ước
   registry.
5. **Viết README** giải thích cấu trúc repository, đề tài mới, đầu vào cần có (dữ liệu, luật/đánh giá, ràng buộc tài nguyên) và
   việc đầu tiên cần làm.
6. **Kiểm tra** nhánh mới không còn tham chiếu tới tệp đã xoá (link trong README, đường dẫn trong script) và không chứa token.

Nhánh đề tài mới áp dụng cùng §2–§6 và §9 của tài liệu này.

---

## 9. Điều kiện viết báo cáo
Chưa viết paper hay tài liệu lý thuyết dài. Chỉ khi có phương pháp thực sự mới **và** bằng chứng thực nghiệm đủ mạnh (đạt các
gate trong `docs/MASTER_RESEARCH_PLAN.md`), lập một báo cáo PDF ngắn: phương pháp, công thức chính, bảng kết quả và so sánh với
các baseline mới nhất phù hợp.

---

## 10. Thứ tự thực hiện

1. §2 Thiết lập tài khoản → §3.4 xác minh cấu hình L4 bằng một kernel chẩn đoán ngắn.
2. §6 Related Work + kiểm tra trùng lặp (song song với dựng feature bank §4.1).
3. §5 Vòng lặp nghiên cứu theo các giai đoạn của Master Research Plan.
4. §7 Dọn dẹp và bàn giao khi kết thúc khung chat → tạo nhánh tiếp nối cùng đề tài.
5. §8 Nhánh đề tài khác — khi có yêu cầu.
