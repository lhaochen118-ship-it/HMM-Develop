# Engineering & Operations Lessons — phiên 27/11/2026

## Tài nguyên đã dùng
- GPU: ~2.3 T4-giờ trên tài khoản `nhatlong1103` (k01 Nordland video-rate ~60 phút; k02 4Seasons office_loop ~12 phút;
  k03 4Seasons countryside ~40 phút; k04 4Seasons old_town ~35 phút). Không dùng tài khoản khác, không dùng nguồn competition để mở tier GPU.
- CPU: toàn bộ HMM/thống kê chạy cục bộ (4 vCPU) từ feature bank đã cache (~4 GB), 121 lần chạy được ghi registry.

## Bài học kỹ thuật
1. **Tái sử dụng feature bank trước khi trích xuất lại**: các dump nb15a–d (6 descriptor × Nordland/RobotCar/CMU) có sẵn
   trên Kaggle tiết kiệm ~6–8 GPU-giờ; tải về ~17 MB/s.
2. **Chỉ dùng GPU cho descriptor; HMM chạy CPU** — mọi thí nghiệm sau đó lặp nhanh (2–10 phút/cấu hình đầy đủ).
3. **Test vét cạn trước khi tin filter** (`tests/test_hmm_core.py`) — bắt được mọi sai lệch bảo toàn khối lượng; mở rộng
   test khi thêm emission vận tốc.
4. **Lỗi của chính phiên này** (ghi trong ISSUES.md, đã sửa/đánh dấu):
   A21 SeqSLAM contrast enhancement phá peak trên bản đồ dày; A22 lấy mẫu hard-negative không trọng số làm lệch LLR;
   A23 sai đơn vị vị trí khi stride>1; A24 oracle-motion NaN trên nordseg; A25 lưới kernel cố định không phủ tốc độ
   4Seasons (baseline bị thiệt) → mọi ô E18 được chạy lại cùng giao thức; A26 tốc độ phải đo theo tọa độ bản đồ (lần sửa đầu dùng nearest-node gây nhảy trên vòng lặp → sụp đổ LV; đã thay bằng tỉ lệ arc-length cục bộ). Bài học: **mọi baseline phải được hưởng cùng
   thông tin dữ liệu (data-driven grid) như phương pháp đề xuất**.
5. Hiệu năng Python: `p[has]` trong vòng lặp gây O(T²M); SeqSLAM phải vector hóa (khớp vòng lặp tham chiếu trong test).
6. Kernel Kaggle: kiểm tra mọi biến dùng ở cuối script (k02 lỗi ở dòng ghi report sau khi trích xuất xong — dữ liệu vẫn
   dùng được); dùng `--file-pattern` để chỉ tải log/meta khi khảo sát.
7. Hàng đợi `research/run_queue.sh` + registry JSONL: chạy song song an toàn; bảng/hình sinh tự động từ registry
   (`make_tables.py`, `make_figure*.py`) — không gõ tay số liệu.
8. Thời gian thực: tiến độ nhanh hơn ước lượng; luôn kiểm tra `date -u` thay vì ước đoán.

## Quy tắc bắt buộc — không tái phạm (cập nhật 28/11, mỗi lỗi ↔ một biện pháp kiểm tra)

| # | Lỗi đã mắc | Quy tắc / biện pháp tự động |
|---|---|---|
| R1 | A21–A26: siêu tham số/đơn vị sai làm baseline hoặc phương pháp bị thiệt | Mọi lưới siêu tham số phủ dải dữ liệu thực (data-driven grid); đơn vị vị trí/tốc độ kiểm tra bằng assert trên calibration |
| R2 | A27/A28: sai quy ước toạ độ / kích thước ảnh đầu vào | Kernel GPU luôn có self-check (Sampson px, kích thước ảnh = mặc định repo gốc) in ra log trước khi chạy dài |
| R3 | A29: OpenCV ném lỗi trên cặp suy biến làm chết cả chunk | Mọi lời gọi RANSAC/PnP bọc try/except → 0 inlier; unit bị lỗi được trả lại hàng đợi (runner L4x4) |
| R4 | A30: container khởi động lại giết job CPU cục bộ | Job > 10 phút KHÔNG chạy cục bộ: đẩy lên phiên CPU Kaggle (`kaggle/cpu/build_cpu.py`); job cục bộ phải resumable |
| R5 | A31: script Kaggle > ~1 MB bị từ chối | Payload lớn → dataset (`build.py --payload-dataset`) |
| R6 | Upload dataset bằng symlink → zip rỗng (22 B) | Không dùng symlink khi upload (dùng hardlink `cp -al`); sau upload kiểm tra size > 0 bằng `datasets list` |
| R7 | `kag.sh` timeout 120 s cắt upload/tải lớn | Lệnh dài đặt `KAG_TIMEOUT` (upload/tải ≥ 1800 s) |
| R8 | Kernel nguồn ở trạng thái ERROR không mount được (k02) | Chỉ dùng output kernel COMPLETE làm nguồn; dữ liệu quan trọng → dataset |
| R9 | Smoke test trên T4 kẹt hàng đợi > 25 phút | Smoke chạy thẳng trên phần cứng đích, tập con nhỏ (`--smoke`) |
| R10 | Gắn dataset ảnh khổng lồ làm phiên chậm 17 phút | Chỉ gắn dataset phiên thật sự cần |
| R11 | I30: trọng số chọn ở biên lưới (2 lần) | Mọi tham số chọn trên calibration phải báo cờ `edge` nếu nằm ở biên lưới; biên → mở rộng lưới MỘT lần, ghi rõ, đánh dấu run cũ superseded |
| R12 | I30: thành phần geometry bị β tempering của HMM làm yếu đi | Bằng chứng ngoài appearance đưa vào emission phải ghi rõ có/không bị temper (thang đo của trọng số) |
| R13 | A32: HMM tệ hơn ảnh đơn khi descriptor quá yếu trên đồ thị không gian (MSLS-sf DINOv2) | Bộ chọn trên calibration phải có lựa chọn suy biến an toàn (leak lớn ≈ ảnh đơn); thay đổi này áp dụng đồng loạt và chạy lại toàn bộ |
| R15 | Hai job Boreas (48k query × 6.5k node) song song trong một phiên CPU 30 GB → OOM kill (rc −9) | Job bộ nhớ lớn (Boreas, MSLS-SeqVLAD) chạy 1 job/phiên; runner ghi rc −9 thành lỗi rõ ràng |
| R14 | Monitor/poller lặp lại sự kiện cũ; merge thủ công quên commit | Đánh dấu `.merged`; `collect.sh` tự merge + commit + push |

## Bảo mật
Token Kaggle chỉ nằm trong scratchpad của phiên (quyền 600), không commit, không in ra log.
