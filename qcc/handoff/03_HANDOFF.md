# 03 — Handoff: QCC Benchmark I (invsqrt)

*Cập nhật 2026-10-31. Repo `lhaochen118-ship-it/hmm-develop`, branch **`hmm-navigation-2`**, thư mục **`qcc/`**.
Không tạo PR. Branch này còn được phiên HMM-navigation dùng song song: luôn `git fetch && git rebase
origin/hmm-navigation-2` trước khi push, và **không sửa `handoff/` gốc** (của dự án HMM). Kết quả khoa học ở `01`,
kinh nghiệm vận hành ở `02`.*

## 1. Mục tiêu

- Giải bài 1 (invsqrt) của cuộc thi Kaggle `google-verifiable-quantum-circuit-compilation` (hạn chót 2027-01-20;
  mốc Mid-Competition Prize 2026-11-20).
- Vòng lặp người dùng yêu cầu: tham khảo → hiểu bản chất → ý tưởng → thử nghiệm → chạy qua Kaggle CLI → **chấm bằng
  score chính thức** → giữ hoặc bỏ.
- Tự quyết định, không hỏi lại. Tối ưu điểm càng nhiều càng tốt; ưu tiên tốc độ nhưng không hy sinh độ chính xác.

## 2. Tiến độ

| Hạng mục | Trạng thái |
|---|---|
| Đọc đề, paper, verifier; tải tuyến đầu public | Xong |
| Simulator, LP góc quay, peephole, các probe dư thừa | Xong (`qcc/`) |
| Hạ tầng verify trên Kaggle + pipeline nộp/chờ điểm | Xong, đã hiệu chuẩn |
| Nộp baseline (3 circuit public tốt nhất) | **LB 23.13505** (lượt nộp duy nhất, 2026-10-30) |
| Cải tiến bài 1 | **Chưa có.** Mọi hướng nhanh âm tính (`01` §4). Đòn bẩy còn mở: uncompute số học (`01` §5) |

## 3. Quyết định đã chốt

- Nộp bài **chỉ từ `nhatlong1103`**. Chạy tính toán Kaggle trên **`yuan1103`** (được phiên HMM để dành cho
  người dùng).
- Mỗi lượt nộp dùng **circuit public tốt nhất cho dqi và dfthcsos**, chỉ thay invsqrt khi có bản tốt hơn đã PASS
  verifier gốc đủ 200M shot.
- Chỉ nộp khi cải tiến đáng kể (cost bài 1 giảm ≳ 0.5%). Các gain −0.04% (`01` N2) không nộp.
- Không commit dữ liệu cuộc thi, token hay file `.kmb` (đã có trong `.gitignore`).
- Phạm vi người dùng giao là bài 1. Chuyển sang bài 3 cần người dùng đồng ý (đã đề xuất, chưa có trả lời).

## 4. Vị trí mọi thứ

| Thứ | Ở đâu |
|---|---|
| Mã | `qcc/*.py`, `qcc/probes/`, `qcc/wait_scores.sh`; bảng công cụ `qcc/README.md`. Nhật ký thí nghiệm mới ghi vào `01` (kết quả) hoặc tạo `qcc/LOG.md` |
| Circuit public | Dataset `manwithacat/vqcc-apache-public-circuits`: `manifest.csv`, `circuits/invsqrt/<sha12>.kmb`, `circuits/dqi/2ed7ccf189f1.kmb`, `circuits/chemistry/0d46767d0211/` |
| Write-up lineage invsqrt | Dataset `mrmeows/qcc-1375-open-circuits` (`README.md`, `sources/invsqrt_*/`) |
| Dữ liệu cuộc thi | `kaggle competitions download google-verifiable-quantum-circuit-compilation -f <file>`: `verifiable_circuit_compilation.pdf`, `verifiers/invsqrt/*.py`, `kickmix/kickmix.so`, `sample_submission/*` |
| Kernel đã chạy | `yuan1103/qcc-v-base` (verify baseline, PASS) |
| Lượt nộp | 57812055 (baseline, 23.13505) |
| Scratchpad cũ | `/tmp/claude-0/.../scratchpad/qc/` (dữ liệu tải về, `best_pub.kmx`, cache). Sẽ mất khi container bị thu hồi; tải lại bằng các lệnh ở §5 |

## 5. Khởi động khung chat mới

1. **Token.** Xin người dùng 2 token (thứ tự: `nhatlong1103`, `yuan1103`), lưu vào `~/.kaggle/tok_<user>` và
   `~/.kaggle/access_token`, chmod 600.
2. **Cài gói.**

```bash
pip install kaggle scipy kickmix==1.0.0
```

3. **Lấy circuit tốt nhất và đổi sang kmx.**

```bash
kaggle datasets download manwithacat/vqcc-apache-public-circuits -f circuits/invsqrt/6dbb98b34c3b.kmb -p D/
```

```bash
python3 -c "import kickmix as km; km.Circuit.from_file('D/circuits/invsqrt/6dbb98b34c3b.kmb').to_file('D/best_pub.kmx', format='kmx')"
```

4. **Lấy verifier gốc** (cho `kaggle_verify.py` và verify local).

```bash
kaggle competitions download google-verifiable-quantum-circuit-compilation -f verifiers/invsqrt/verify_submission_invsqrt.py -p D/
```

5. **Kiểm tra nhanh.**

```bash
python3 qcc/refit_angles.py D/best_pub.kmx
```

   Kết quả phải ra margin 3.1765e−12, đúng như ở `01` §3.

6. **Kiểm tra tuyến đầu public mới.** Tải lại `manifest.csv` mỗi phiên: tuyến đầu đổi hằng ngày (ngày 30/10 invsqrt
   đi từ 102k xuống 100.9k).

## 6. Việc tiếp theo (theo ưu tiên)

1. **Hỏi người dùng về phạm vi.**
   - (a) Ở lại bài 1 với dự án generator mới (bước 2), hay
   - (b) chuyển sang bài 3 (chemistry, ×9.93; tác giả public chỉ ra ~10% còn lại nếu fit lại được bộ word 7-bit qua
     ngưỡng 20 mHa).
   - Khoảng cách tới top LB 26.76 (≈ +55% tích ba tỉ lệ) gần như chắc chắn không nằm ở bài 1.

2. **Nếu ở lại bài 1: generator riêng tấn công phần uncompute** (`01` §5). Thứ tự gợi ý:
   1. Viết builder kmx gọn (cấp phát/giải phóng qubit, AND + xoá HMR có sửa Clifford, bộ cộng Gidney, CSWAP, Z_POW),
      kiểm bằng `ksim`.
   2. Tái hiện trước phần đầu circuit của lineage (chuẩn hoá + lookup ANF 10 bit) ở mức chức năng: dùng `ksim`
      trích bảng chân trị 35 dây hệ số (hàm của u>>12) tại lệnh ~21000.
   3. Fit lại phần pha còn thiếu sau luồng A, theo dạng A(i) + B(i)·δ + C(i)·δ² trên 1 024 đoạn, rồi hồi quy xem
      35 dây hệ số mã hoá B, C ra sao.
   4. Xây khối số học mới: giữ carry trong 4–8 qubit dư để xoá bằng phép đo, làm phẳng các xung đỉnh.
   5. LP refit góc quay (`refit_angles.py`), chạy verifier gốc, rồi nộp.
   - Mốc dừng: nếu sau bước 4 mô hình chi phí không dưới ~1 500 Toffoli-eq ở Q ≤ 62 thì dừng hướng này.

3. **Song song, rẻ:** theo dõi manifest. Khi có circuit public tốt hơn cho bất kỳ bài nào, ghép lại portfolio và
   nộp lại bằng `make_submission.py` (tốn 1 lượt/ngày).
