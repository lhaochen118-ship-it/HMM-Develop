# Báo cáo vòng 12 (Entry 38): lỗ ảo hình khối cho mép lỗ thật — và tăng tốc phép mô phỏng tiến trên GPU

*Branch `hmm-navigation-5`, 2026-11-03. Nhật ký: `RESEARCH_LOG.md` Entry 38 (đăng ký trước — commit trước mọi kết quả — kết quả, kết luận).
Lý thuyết: `paper/cms_theory.md` §4h (Mệnh đề 20). Code: `analysis/cms_fwd.py` (BlockGrid, BlockHoleMask, `fwd_null(shape="block")`,
`FwdStats.multi_stats`, MultiMask), `cms.py` (CST-JSB, CST-JSU), `e37_eval.py --block / --corr`, `oc_curves.py --fwdb`, `mps_probe.py`;
`automation/e37_wave.py --e38`; bảng `paper/build_e38_report.py` → `paper/e38_tables.md`. Nhãn chỉ dùng để đánh giá.*

## 1. Câu hỏi và kết luận ngắn

Entry 37: luật CST-JS hợp lệ ở mức segFAR (kể cả tập giữ ra), nhưng **đoạn MÉP của lỗ thật** bị báo sai quá ngưỡng trên Boreas (0.084) và old town
(0.109). Giả thuyết: lỗ thật là ô vuông của bản đồ (mất cả phố song song/cắt ngang), lỗ ảo là ống hẹp ρ dọc đường tin ⇒ thêm **họ lỗ ảo hình khối**.

| Giả thuyết (đăng ký trước) | Kết quả |
|---|---|
| H38a — CST-JSU hợp lệ (segFAR ≤ 0.05) | **Đạt:** 6/6 tập giữ ra mới (seed 3–5, 99 run), 7/7 tập E37, Oxford 0.021 |
| H38b — mọi lớp vị trí ≤ 0.07 | **Không đạt:** 4/7 (tập E37), 4/6 (giữ ra mới). Lỗ khối gần như không đổi tỷ lệ ở mép (Boreas 0.084 → 0.076, old town 0.109 → 0.106) |
| H38c — recall trong 0.03 của SH | **Đạt:** 6/6; +0.167 so với CST-F trên CMU |
| H38d — sai số điều hướng trong 1 m của SH | **Không đạt:** 4/6 (old town +12.8 m, Boreas +1.9 m) |
| H38e — Oxford | **Đạt:** hợp lệ, recall 0.728 vs SH 0.719 |

**Kết luận:** hình dạng lỗ **không** phải nguyên nhân chính của phần dư ở mép (giả thuyết cơ chế của Entry 37 bị bác bỏ với cách dựng này). Theo luật
quyết định, CST-JSU không được đề cử; khuyến nghị của Entry 37 giữ nguyên (SH ∧ CST-JS thực dụng, CST-F chứng nhận). **Quan sát phụ (luật thứ cấp
đã đăng ký):** bản nhân quả **CST-JSU [both]** đạt ≤ 0.07 ở mọi lớp vị trí trên **6/6** tập giữ ra mới (mép Boreas 0.055, old town 0.046), giá
recall −0.02 đến −0.034 so với SH — ứng viên để xác nhận trên các bố cục lỗ mới (đăng ký trước riêng).

## 2. Phương pháp

Mỗi lần chạy ảo có một lưới vuông ngẫu nhiên riêng (cạnh = block của cấu hình × {½, 1, 2}, xoay U[0, π/2), dịch U[0, 1) ô); lối thoát xoá **cả các ô**
chứa nơi trong bán kính ρ của đường tin sau lối thoát (rồi cắt Voronoi với đường trước lối thoát); khởi đầu xoá các ô quanh đường tin của nó.
Mọi phần còn lại như CST-JS. **CST-JSU** báo khi qua ngưỡng của cả hai họ: theo Mệnh đề 20, bảo đảm giữ nguyên nếu lỗ thật giống **một** trong hai họ.
Kiểm: numpy = torch (mọi khoá), đường `--corr` (dùng null hành lang đã công bố) cho kết quả trùng tính lại.

## 3. Kết quả

{{TABLES}}

## 4. Tối ưu tài nguyên (đo trên L4, cùng 48 job null tiến CMU, 46 song song)

| Cấu hình | ms / frame | so với cũ |
|---|---|---|
| Code cũ (mỗi lần chạy ảo một lời gọi GPU nhỏ, 12 tiến trình chia thời gian một GPU) | 35.5 | 1.00× |
| Code cũ + CUDA MPS | 27.6 | 1.29× (wall 1.34×) |
| **Gộp lô phép thử tuyến qua mọi lần chạy ảo của một chuỗi** (`FwdStats.multi_stats`) | **18.3** | **1.94×** |
| Gộp lô + MPS | 19.5 | — (MPS không thêm khi đã gộp lô) |

Đầu ra của bản gộp lô **trùng tuyệt đối** bản cũ (hai họ lỗ, numpy và torch). Lô 2 048 hàng dùng ~2 GB VRAM mỗi tiến trình (12 tiến trình trên 23 GB:
một số job hết VRAM) ⇒ mặc định 1 024 hàng, tự chia đôi khi hết bộ nhớ. Trước đây VRAM chỉ dùng ~11 %; với lô 1 024 hàng ước ~50 % (12 tiến trình × ~1 GB; chưa đo lại trên L4). **Hạn mức:** một phiên L4×4 tính
4 GPU-giờ mỗi giờ; mỗi acc 30 GPU-giờ/tuần (~7.5 giờ L4) — `nhatlong1103` đã hết trong vòng này. Phiên CPU (5/acc, 4 vCPU) không tốn hạn mức GPU:
đã dùng 12 phiên CPU cho các run nhỏ.

## 5. Việc tiếp theo

1. Xác nhận CST-JSU [both] trên **bố cục lỗ mới** (seed mới của bộ sinh lỗ: `nav_demo.py --cache` seed ≥ 10), đăng ký trước riêng.
2. Kiểm hai giải thích còn lại cho phần dư ở mép: hệ số 1/π của Mệnh đề 19 (đo π), và biên định nghĩa off_d (robot chỉ vừa qua 40 m).
3. Các đợt sau dùng code gộp lô (≈ 2× mỗi GPU-giờ) và phiên CPU cho run nhỏ.
