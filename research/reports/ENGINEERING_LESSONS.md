# Engineering & Operations Lessons — phiên 27/11/2026

## Tài nguyên đã dùng
- GPU: ~1.7 T4-giờ trên tài khoản `nhatlong1103` (k01 Nordland video-rate ~60 phút; k02 4Seasons office_loop ~12 phút;
  k03 4Seasons countryside ~40 phút). Không dùng tài khoản khác, không dùng nguồn competition để mở tier GPU.
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
   4Seasons (baseline bị thiệt) → mọi ô E18 được chạy lại cùng giao thức. Bài học: **mọi baseline phải được hưởng cùng
   thông tin dữ liệu (data-driven grid) như phương pháp đề xuất**.
5. Hiệu năng Python: `p[has]` trong vòng lặp gây O(T²M); SeqSLAM phải vector hóa (khớp vòng lặp tham chiếu trong test).
6. Kernel Kaggle: kiểm tra mọi biến dùng ở cuối script (k02 lỗi ở dòng ghi report sau khi trích xuất xong — dữ liệu vẫn
   dùng được); dùng `--file-pattern` để chỉ tải log/meta khi khảo sát.
7. Hàng đợi `research/run_queue.sh` + registry JSONL: chạy song song an toàn; bảng/hình sinh tự động từ registry
   (`make_tables.py`, `make_figure*.py`) — không gõ tay số liệu.
8. Thời gian thực: tiến độ nhanh hơn ước lượng; luôn kiểm tra `date -u` thay vì ước đoán.

## Bảo mật
Token Kaggle chỉ nằm trong scratchpad của phiên (quyền 600), không commit, không in ra log.
