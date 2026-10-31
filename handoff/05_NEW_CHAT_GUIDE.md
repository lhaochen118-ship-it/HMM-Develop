# 05 — Hướng dẫn cho khung chat mới: đọc repo thế nào, làm gì tiếp

*2026-10-31, cập nhật từ branch `hmm-navigation-4` (vòng 4). Repo `lhaochen118-ship-it/hmm-develop`. Không tạo PR.*

**Vòng 4 (đọc trước):** `paper/BAO_CAO_E26.pdf`, `handoff/01_SCIENTIFIC_FINDINGS.md` §N0, `RESEARCH_LOG.md` Entry 26, `paper/cpc_theory.md` §3e–§3f, `LITERATURE_GATE.md` Gate 11, `literature/BASELINES_2026.md`, `handoff/02_ENGINEERING_OPS_NOTES.md` §00. Phương pháp tốt nhất hiện tại: **CPC-SC-T+SH** / **CPC-SC-T+CS** (họ luật trong `analysis/oc_curves.py --topk --mapdump`, `analysis/cpc_geo.py`, `analysis/tao.py`). Dữ liệu mới: `nhatlong1103/hmm-topk`. Tải dataset public không cần token: `automation/anon_download.py`.

## 1. Bối cảnh trong 5 dòng

- Bài toán: robot camera đơn + odometry chạy trên bản đồ ảnh **có lỗ** (đoạn đường không có trong bản đồ). Mỗi frame cần
  quyết định có báo một "fix" vị trí cho bộ lọc điều hướng hay không, sao cho báo sai ít (không dùng nhãn) mà bắt được
  nhiều fix đúng.
- Phương pháp hiện tại: **CPC-SC+CS** (`analysis/cpc_sc.py`) — chuỗi hiện diện kiểu HMM bằng e-value hiệu chuẩn bằng bản
  đồ + ngưỡng khởi phát hiệu chuẩn theo đoạn + quy tắc dừng nhất quán odometry.
- Đã chứng minh không chỉ "thận trọng hơn": ở FL ≤ 1 % recall cao hơn Xu'21 7/7 dataset, Claxton'24 6/7.
- Mức novelty: A khả thi, **A\* chưa**.
- Việc của khung chat mới: lời giải mới đủ novel cho A\*, bảo đảm dưới phụ thuộc thời gian, so sánh TRAIL'26 / TAO'26 /
  VPR-auditing'26.

## 2. Thứ tự đọc (≈ 45 phút)

| # | File | Đọc để biết | Phần nên đọc |
|---|---|---|---|
| 1 | `handoff/03_HANDOFF.md` | Mục tiêu, quyết định đã chốt, vị trí mọi thứ, **việc tiếp theo** | Toàn bộ |
| 2 | `handoff/01_SCIENTIFIC_FINDINGS.md` | Phương pháp, số liệu, kết quả âm, novelty | §N trước; §0–§3 khi cần nền |
| 3 | `paper/BAO_CAO_PhanBien.pdf` | Báo cáo ngắn mới nhất (công thức + bảng) | Toàn bộ (6 trang) |
| 4 | `paper/cpc_theory.md` | Lý thuyết: vì sao HMM yếu, CPC-HMM, ARL₀, TCE, CS, CPC-SC | §1, §3c, §3d |
| 5 | `handoff/02_ENGINEERING_OPS_NOTES.md` | Chạy Kaggle, lỗi đã gặp, bài học | §0 trước, rồi §8 |
| 6 | `handoff/ENVIRONMENT_SUMMARY.md` | Dataset, cache công khai, acc Kaggle | §1d, §3 |
| 7 | `LITERATURE_GATE.md` | Kết luận novelty | Gate 9, Gate 10 |
| 8 | `literature/VISUAL_LOCALIZATION_REVIEW.md` | Tóm tắt method + score của related work | §5, §6, §6b, §8 |
| 9 | `RESEARCH_LOG.md` | Nhật ký thí nghiệm, kể cả kết quả âm | Entry 25 (mới nhất) |
| — | `handoff/04_RESEARCH_WORKFLOW.md` | Quy trình theo phase, nguyên tắc | Khi lập kế hoạch |

## 3. Bản đồ code

| Nhóm | File | Vai trò |
|---|---|---|
| Phương pháp | `analysis/cpc_sc.py` | CPC-SC+CS (luật đề xuất) |
| Sinh dữ liệu (Kaggle) | `analysis/nav_demo.py` | Mọi thống kê nặng + baseline; `--cache` ghi `navcache_*.npz` |
| Đánh giá từ cache | `nav_rules.py`, `oc_curves.py`, `oc_matched.py`, `oc_summary.py`, `lodo_select.py`, `recall_diag.py` | Luật, đường cong, so khớp, chọn biến thể |
| Nền | `vprlib.py` (loader), `selfcal.py` (p-value bản đồ), `cert_seq.py` (certified, odometry), `hmm_diag.py` (chuỗi vị trí), `hmm_fix.py` | Thống kê và bộ lọc |
| Kaggle | `automation/fanout.py`, `make_eval_kernel.py`, `run_kernel.py`, `reattach.py`, `publish_dataset.py` | Chia job ra acc, theo dõi, kéo kết quả |
| Báo cáo | `paper/build_oc_report.py`, `paper/phanbien_text.md`, `automation/md2pdf.py` | Bảng tự sinh + PDF |
| Không liên quan | `qcc/` | Dự án khác (Kaggle QCC), bỏ qua |

## 4. Khởi động nhanh

```bash
pip install kaggle markdown xhtml2pdf scipy scikit-learn
```

Token: lưu danh sách user gửi vào `~/.kaggle/tokens_raw` (chmod 600); với mỗi token, lấy tên acc bằng
`KAGGLE_API_TOKEN=<tok> kaggle config view` rồi ghi `~/.kaggle/tok_<acc>` (chmod 600); `~/.kaggle/access_token` là của
`nhatlong1103`.

Tái tạo bảng của khung chat trước từ cache công khai (không cần GPU):

```bash
kaggle datasets download nhatlong1103/hmm-navcache-v2 -p <scratch>/navcache --unzip
```

```bash
python3 analysis/oc_curves.py <scratch>/navcache cmu megaloc,salad --variants --defaults-only --jobs 4
```

Thêm một luật mới: viết hàm trong `analysis/cpc_sc.py` (hoặc module mới), thêm một family trong `oc_curves.families`,
chạy `oc_curves.py` trên cache. Chỉ chạy lại `nav_demo.py` trên Kaggle khi cần thống kê chưa có trong cache (ví dụ top-K
chỉ số cho TAO'26).

## 4b. Tái tạo bảng vòng 4 (CPU, không cần GPU)

```bash
python3 automation/anon_download.py nhatlong1103/hmm-navcache-v2 <scratch>/navcache --jobs 12
```

```bash
python3 automation/anon_download.py nhatlong1103/hmm-topk <scratch>/topk --jobs 12
```

```bash
python3 analysis/oc_curves.py <scratch>/navcache cmu cosplace --topk <scratch>/topk --mapdump <dump_dir> --fams TAO26,TAO-SC,CPC-SC-T,CPC-SC-T+CS,CPC-SC-T+SH --seeds 0,1,2 --jobs 3
```

(`<dump_dir>`: descriptor dumps, `analysis/topk_dump.py` / `vprlib` layout; trên Kaggle dùng token `DUMP`, `CACHE`, `TOPK`.)
Bảng báo cáo: `paper/build_e26_report.py` (đầu vào: thư mục `oc_*.json`; kết quả thô nén ở `analysis/results/e26/`).

## 5. Việc tiếp theo (tóm tắt; chi tiết ở `03` §5)

**Sau vòng 5 (ưu tiên):** (1) hiệu chuẩn **chung** (hiện diện ∧ dừng CS/SH) trên null chéo traversal — cần chạy chuỗi vị trí
trên các pseudo-query (`hmm-xnull` đã có top-100 khi che block); đây là nguồn dè dặt chính còn lại; (2) CMU / descriptor mạnh:
khoảng cách ~0.05 với Claxton'24/TAO'26 vẫn còn (biến thể chỉ-tuyến không tổng quát); (3) robot thật vòng kín. Báo cáo mới
nhất: `paper/BAO_CAO_E27.pdf`.

**Sau vòng 4 (đã làm ở vòng 5: mục 1 phần null X, mục 2 một phần, mục 3):** (1) null **khớp điều kiện ảnh** để điểm mặc định bớt dè dặt (ví dụ pseudo-query từ traversal khác
của bản đồ nhiều phiên; Boreas có 17 traversal chưa dùng); (2) CMU / descriptor mạnh: Claxton'24 và TAO'26 xếp hạng tốt hơn —
thử chi phí tuyến với trọng số hình học/ngoại hình hiệu chuẩn trên null, hoặc K lớn hơn; (3) VLM-auditing và SafeVPR trên
NCLT / 4Seasons (ảnh có sẵn: `nclt-cam5-*`, `4seasons`); (4) chạy robot thật vòng kín. Các mục cũ bên dưới vẫn đúng.


1. **Lời giải mới cho A\*, tổng quát:** đào sâu ba sự thật thực nghiệm — phép thử một bước tự xác nhận; nhất quán odometry
   trên quãng dịch chuyển phân biệt mạnh; null tự-phát-lại của bản đồ thiếu phụ thuộc của đoạn off-map dài. Hướng gợi ý:
   bảo đảm dựa trên hình học bản đồ, null tự sinh từ chính query (dịch vòng odometry so với ảnh), khối theo quãng đường
   với cận mixing. Mỗi ý tưởng qua gate novelty trước khi làm.
2. **Bảo đảm cho quyết định HMM dưới phụ thuộc thời gian**, kiểm trên Boreas và NCLT.
3. **Baseline:** TRAIL'26, TAO'26, VPR-auditing'26 (tái hiện từ paper); mở rộng cache lưu top-K chỉ số; VLM mở chạy
   offline trên L4.
4. Giữ giao thức: đăng ký trước, tập giữ lại, leave-one-dataset-out, đường cong + so khớp chính xác, 10 seed, tỷ lệ lỗ
   10/30/50 %, một cấu hình cho mọi dataset.
5. Kết thúc: báo cáo PDF ngắn tiếng Việt nếu kết quả mạnh; cập nhật `handoff/01–05` và `ENVIRONMENT_SUMMARY` (md + pdf).
