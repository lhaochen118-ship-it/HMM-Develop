# 01 — Scientific Findings: QCC Benchmark I (invsqrt)

*Cập nhật 2026-10-31. Cuộc thi Kaggle "Google Quantum AI — Verifiable Quantum Circuit Compilation", bài 1. Tài liệu
này chỉ nói về **kết quả khoa học**: mô hình bài toán, giải phẫu lời giải tốt nhất hiện có, các giả thuyết đã kiểm
chứng (dương và âm tính), bằng chứng và cách kiểm chứng lại. Vận hành ở `02`, trạng thái và việc tiếp theo ở `03`.*

## 1. Bài toán và mô hình chi phí

**Hợp đồng.** Circuit kickmix trên thanh ghi `x` 22 qubit thực hiện |x⟩|0⟩ → e^{2πi/√x}|x⟩|0⟩ với mọi
x ∈ [1, 3 133 452] = [1, 3(2^10−2)^2]. Mỗi x được thử 64 lần (200 540 928 shot), kết quả đo HMR được seed từ
SHA-256 của file circuit cộng salt bí mật. Mỗi shot phải: khôi phục `x`, đưa mọi qubit nháp về |0⟩, và có sai số
pha ≤ tol(x) = 2^−24/√x vòng (sai số tương đối hằng 2^−24).

**Chi phí** S = Q × C:

- Q = tổng số qubit.
- C = (số Toffoli thực thi trung bình mỗi shot) + T/4. CCX, CCZ, CSWAP mỗi cái tính 1 Toffoli. Cổng nằm trong
  khối điều kiện cổ điển chỉ được đếm khi điều kiện đúng.
- Mỗi rotation Z_POW không phải Clifford/T tốn 0.56·log2(1/ε) + 5.3 T, với ε = π·margin / n_rot và
  margin = min_x (tol(x) − |err(x)|).
- Tham chiếu của ban tổ chức: S_ref = 2 076 774.23 (Q = 260, C = 7 988).

**Điểm leaderboard** = trung bình nhân 3 tỉ lệ S_ref/S. Vì vậy cải thiện x% ở bài 1 làm điểm tổng tăng khoảng x/3 %.

**Hệ quả quan trọng của mô hình (rút ra trong quá trình làm):**

1. **Bit cổ điển là đồng xu ngẫu nhiên.** HMR đo theo cơ sở X nên kết quả luôn đều 50/50, độc lập với x. Không
   thể rẽ nhánh theo x; chỉ có thể thực thi có điều kiện theo đồng xu (kỳ vọng ½), đó là cách các sửa pha
   "measurement-conditioned" trở nên rẻ.
2. **Xoá một dây bằng HMR.** Xoá dây giữ f(x) cần áp pha (−1)^{b·f}. Nếu f là hàm bậc ≤ 2 (trên GF(2)) của các
   dây còn sống thì sửa pha là CZ/Z (Clifford, miễn phí); mỗi đơn thức bậc 3 cần một CCZ, kỳ vọng ½ Toffoli.
   Đây là cơ chế làm uncompute rẻ.
3. **Mỗi rotation ≈ 7.2 Toffoli-eq** (khoảng 28.8 T ở ε ≈ 2^−42). Các trọng số pha 2^−1, 2^−2, 2^−3 vòng là
   Clifford/T. Đầu ra nhị phân phủ dải trọng số 2^−4 … 2^−36 vòng nên **cần tối thiểu 33 rotation**.
4. **Ở Q ≈ 62, mỗi qubit đáng ≈ 26 Toffoli** (1.6% cost). Thêm qubit để bớt Toffoli hầu như luôn lỗ.

## 2. Giải phẫu lời giải public tốt nhất

Circuit `6dbb98b34c3b` (dòng busyaprime → mrmeows → yoyobar → Ozer):

| Đại lượng | Giá trị |
|---|---|
| Cost | 100 940.56 (tỉ lệ 20.57) |
| Q | 62 |
| Toffoli trung bình mỗi shot | 1 331.48 |
| Toffoli tĩnh | 1 501 |
| T | 7.0 |
| Rotation | 41 |
| Margin | 3.1765e−12 vòng |
| Worst err/tol | 0.99932 tại x = 161 |

Mọi số liệu trong bảng đều do simulator của chúng tôi đo lại và khớp verifier chính thức tới từng chữ số.

**Thuật toán.**

1. **Chuẩn hoá.** Chuỗi AND tiền tố "cặp bit 0 dẫn đầu" cho s ∈ [0, 10]. Các bit nhị phân của s lấy bằng XOR các
   cờ tiền tố, nên miễn phí. Sau đó dịch x tại chỗ một lượng 2s bằng các tầng CSWAP.
2. **Tra bảng.** Lookup theo 10 bit cao của u = x·4^s, dạng ANF với đơn thức chia sẻ: khoảng 35 dây hệ số là hàm
   của u>>12. Có khoảng 38 dây đơn thức sống cùng lúc, chính chúng tạo ra đỉnh Q = 62.
3. **Hai luồng pha.**
   - Luồng A: các "tap" seed, 15 rotation, trọng số 2^−18 … 2^−4.
   - Luồng B: hiệu chỉnh độ chính xác cao, 26 rotation, trọng số 2^−36 … 2^−11.
   - Trong mỗi luồng, bit được tính tuần tự, xoay (rotate), rồi xoá bằng HMR. Mỗi bit được định tuyến theo s bằng
     khoảng 2 CSWAP.
4. **Uncompute.** Đảo phép tính số học, rồi đảo chuẩn hoá.

**Ngân sách Toffoli (thực thi trung bình, theo cửa sổ lệnh):**

| Lệnh | Toffoli | Nội dung |
|---|---:|---|
| 0–1k | 92 | chuẩn hoá thuận |
| 1k–15k | ~160 | lookup ANF |
| 15k–16k | 72 | luồng A |
| 16k–21k | ~51 | — |
| 21k–26k | ~436 | số học chính + luồng B |
| 28k–37k | ~446 | uncompute số học |
| 44k–48k | ~74 | chuẩn hoá nghịch |

Rotation chiếm khoảng 295 Toffoli-eq (18% của C).

**Cấu trúc rotation.**

- 8 trọng số (2^−18 … 2^−11) có mặt ở cả hai luồng.
- 14 rotation chỉ kích hoạt khi x nhỏ: x ≤ 2^20, 2^18, …, 252. Lý do là mỗi luồng phải phủ cả dải dịch s.
- Tổng 41 = 33 (sàn) + 8 (trùng).

## 3. Kết quả tích cực

| # | Kết quả | Bằng chứng |
|---|---|---|
| P1 | Simulator bit-sliced `ksim` tái hiện chính xác verifier chính thức (Toffoli, T, rotation, margin, err/tol, khôi phục x, scratch sạch) trên toàn miền 3.1M x | Toffoli 1 331.48, margin 3.1765e−12, err/tol 0.99932 trùng với output `verify_submission_invsqrt.py` |
| P2 | Pipeline nộp bài và chấm điểm đã hiệu chuẩn: baseline (3 circuit public tốt nhất) đạt **public LB 23.13505**, đúng (20.57 · 60.6 · 9.93)^{1/3} | Kaggle submission 57812055 |
| P3 | Verifier chạy trên Kaggle với kickmix PyPI 1.0.0 cho cost 100 940.5617, trùng manifest | `results.json` của kernel `yuan1103/qcc-v-base`, 200M shot |
| P4 | Bản đồ ngân sách trên, định vị chỗ còn dư: vùng số học/uncompute (lệnh 19k–31k) chỉ dùng trung bình ~56/62 qubit; các đỉnh 62 ở đó là xung ngắn, trừ hai vùng 17–18k và 33–34k | profile chiếm dụng từ `ksim` (track_life) |

## 4. Kết quả âm tính (giả thuyết đã bác bỏ)

| # | Giả thuyết | Kết quả | Lợi ích tiềm năng |
|---|---|---|---|
| N1 | Tối ưu lại 41 góc quay để tăng margin | LP chính xác (cutting-plane trên toàn miền) cho margin 3.17654e−12 → 3.17655e−12. Góc đã LP-tối ưu. Margin bị ghim bởi ~52 giá trị x rải ở mọi s (619 x nằm trong 2× min) | ≤ 0.35% mỗi lần tăng gấp đôi margin |
| N2 | Peephole: CCX là hàm affine của các dây sống; CCZ/CSWAP luôn 0 | 42 CCZ (theo a·b) và 48 CCZ (theo a·b·c) không bao giờ tác động, nhưng đều nằm trong nhánh đo hiếm: −0.125 / −0.63 Toffoli mỗi shot | −0.04% (không nộp) |
| N3 | Bớt qubit bằng gán lại nhãn | 62 qubit đồng thời khác 0 trong 15 720 lệnh | 0 |
| N4 | Bớt qubit (62→61) bằng xoá/tính lại dây rảnh | Phủ tham lam vùng đỉnh cần 5 khoảng rảnh (q23 ×3, q43, q32). Ở điểm xoá/tính lại, không giá trị nào là hàm bậc ≤ 2 của dây sống, cũng không phải hàm của ≤ 3 dây | 1.6% |
| N5 | "Đỗ tạm" bit x (q0–q13 rảnh suốt vùng đỉnh) | Không bit nào là hàm bậc 2 của các dây khác | 1.6% |
| N6 | Gộp hai luồng pha (41 → 33 rotation) | Các bit seed của luồng A không còn tái dựng được (bậc 2) ở thời điểm luồng B (mrmeows cũng xác nhận). Gộp phải tra bảng lại (~186 Toffoli) | −3.4% nếu gộp miễn phí |
| N7 | Thay một khối như oracle pha | Không có ranh giới sạch: khối [19.5k, 37.5k) và [240, 44k) đều đổi trạng thái dây và có pha phụ thuộc đồng xu (sửa pha bị hoãn ra ngoài khối) | — |
| N8 | Thiết kế mới từ đầu kiểu "chuẩn hoá → seed 256 mục → hiệu chỉnh bậc 3 → một luồng" | Ước lượng giấy ~1 700 Toffoli-eq ở 62–70 qubit, kém 1 628 @ 62 | — |

**Phân tích lý thuyết đi kèm N8.**

- Các phương án "bảng lớn hơn / bậc thấp hơn / NR thay đa thức / Booth radix-4 / dịch đầu ra bằng hệ số tiền nhân
  2^s" đều cho tổng gần như ngang nhau, tức không gian thiết kế phẳng quanh điểm của lineage.
- Phần "dấu phẩy động" là chi phí nội tại: chuẩn hoá vào/ra ~170–230, định tuyến luồng, 14 rotation hiếm ~100
  Toffoli-eq.
- Nhân hai số lượng tử tốn ~2 AND mỗi tích riêng phần (sinh AND + nén). Ở chế độ ít qubit, uncompute ≈ compute.

## 5. Đòn bẩy còn mở (chưa kiểm chứng bằng circuit)

**Uncompute số học (~446 Toffoli, 27% C).**

- Bộ cộng in-place chỉ đảo được bằng phép trừ.
- Nếu giữ các bit carry sống tới lúc xoá, tổng là hàm tuyến tính của toán hạng và carry. Khi đó mọi dây xoá được
  bằng HMR + CZ (miễn phí), tức uncompute ≈ 0 Toffoli cho bộ cộng đó, đổi lại mất n qubit carry trong suốt khoảng
  sống.
- Vùng số học có dư 4–8 qubit (P4), nên có thể áp dụng cho một phần các bộ cộng mà không tăng Q, với điều kiện làm
  phẳng các xung đỉnh.
- Ước lượng lạc quan: uncompute còn ~200 → C ≈ 1 380 → cost ≈ 86k (tỉ lệ ~24, điểm tổng +5–6%).
- Chưa kiểm chứng. Cần dựng lại toàn bộ khối số học bằng generator riêng, vì không có ranh giới sạch (N7).

## 6. Điều kiện kiểm chứng lại

- Circuit: `circuits/invsqrt/6dbb98b34c3b.kmb` trong dataset `manwithacat/vqcc-apache-public-circuits`.
- P1, N1–N5:

```bash
python qcc/refit_angles.py best.kmx
python qcc/peephole.py best.kmx
python qcc/probes/ccz_fast.py DIR
python qcc/probes/xbits_run.py DIR
```

- Toàn miền x với seed HMR 3–23. Kết quả "luôn bằng 0" được kiểm trên 3–4 seed.
- Số liệu chính thức chỉ công nhận khi chạy verifier gốc (`--shots-per-x 64`, 200M shot).
- Điểm LB phụ thuộc salt bí mật. Với bài 1 cost gần như tất định: chỉ số Toffoli trung bình dao động rất nhỏ theo
  seed đồng xu.
