# 08 — Tài liệu chuyển giao theo `HMM_Navigation_Yeu_Cau_Nghien_Cuu_Cap_Nhat.docx`

*2026-11-05, branch `hmm-2nd-idea` (repo `lhaochen118-ship-it/hmm-develop`). Tài liệu đi theo đúng 5 mục của file yêu cầu. Với mỗi mục, tài liệu
ghi: đã làm gì, bằng chứng nằm ở đâu, và điều gì CHƯA đạt. Chi tiết nằm trong các file được dẫn:
- số liệu: `01_SCIENTIFIC_FINDINGS`;
- vận hành: `02_ENGINEERING_OPS_NOTES`;
- quyết định, sổ dùng tập kiểm tra: `03_HANDOFF`;
- cách bắt đầu phiên mới: `06_NEXT_CHAT_GUIDE`.*

## 1. Mục tiêu nghiên cứu (yêu cầu §1: nâng cao novelty)

**Bài toán.** Robot camera đơn + odometry định vị theo chuỗi (HMM) trên bản đồ ảnh có lỗ (30 % ô 300 m bị xoá). Ở mỗi khung, hệ thống quyết định
báo hay không báo một fix vị trí, không có nhãn. Ràng buộc: tỉ lệ đoạn off-map bị báo sai segFAR ≤ α = 0.05; recall cao; sai số điều hướng thấp.

**Ba hướng của branch này.** Mỗi hướng có cơ chế riêng, khác ý tưởng 1 (phẫu thuật bản đồ phản thực, branch `hmm-navigation-5`):

| Hướng | Cơ chế mới | Lý thuyết | Gate novelty |
|---|---|---|---|
| 2a — HSI (Entry 1–9) | Tự giám sát HỒI CỨU: dùng tính nhất quán hình học của chuỗi đã đi để gán nhãn cho quá khứ, rồi hiệu chuẩn conformal trên các excursion thật của chính run | `paper/hsi_theory.md` Mệnh đề 1–7 | `LITERATURE_GATE.md` Gate 17 |
| 2b — OWF (Entry 10) | Bộ lọc THẾ GIỚI MỞ: trạng thái là vị trí metric phủ cả vùng có và không có bản đồ; hiện diện trên bản đồ là HÀM của vị trí, không phải một phép thử | `paper/owf_theory.md` Mệnh đề 1–3 (cận Ville cho báo sai trong đoạn off-map, không có số hạng mép) | Gate 18 |
| Ghép 2a + 2b (Entry 11–15, AUTOLOOP) | Bộ ước lượng OWF + lớp quyết định HSI. Phát hiện: chứng chỉ hình học của HSI bị quỹ đạo dead-reckoning lừa. Thêm bậc đồng thuận ba nguồn và ngân hàng tỉ lệ odometry chọn theo evidence | lập luận cơ chế trong `RESEARCH_LOG.md` Entry 11–15; chưa có mệnh đề hình thức | chưa chạy gate riêng |

**Đánh giá trung thực về novelty.** HSI và OWF mỗi hướng có một nguyên lý riêng, có lý thuyết, đã qua gate tài liệu. Các bước AUTOLOOP (Entry 11–15)
cải thiện số liệu rõ rệt, nhưng phần lớn là KỸ THUẬT GHÉP: luật hợp nhiều bậc, ngưỡng theo quãng đường, lưới tỉ lệ. Một reviewer A\* có thể xem
chúng là heuristic. Nếu viết paper, đóng góp chính nên là OWF (hoặc HSI); OWF-HWA-S5 là hệ hoàn chỉnh dùng trong thực nghiệm. **Chưa đủ bằng chứng
để tuyên bố đạt mức A\*.** Chưa so với SOTA ngoài hai đối thủ nội bộ (SH / CST-JS của ý tưởng 1, HSI-VN). Paper hoàn chỉnh chưa viết.

## 2. Nguyên tắc nghiên cứu (yêu cầu §2)

| Nguyên tắc | Cách đã thực hiện |
|---|---|
| Kết quả tái lập được | JSON mỗi run + khung / mặt nạ báo theo frame trong `analysis/results/{hsi,owf}/` (tgz). Bảng điểm sinh lại bằng `analysis/autoloop_board.py`, `owf_union.py`, `owf_summary.py`, `hsi_compare.py` |
| Không mặc định là mới / vượt trội | Mọi quyết định được **đăng ký trước** trong `RESEARCH_LOG.md` (commit + push TRƯỚC khi chạy), rồi kiểm trên **một nhóm seed mới chưa dùng**; mỗi nhóm chỉ dùng cho một quyết định. Kết quả âm được ghi lại (ví dụ Entry 10: D3 trượt nên HSI-VN được giữ) |
| Tổng quát, không chỉnh riêng cho dataset | MỘT cấu hình chung cho 8–9 dataset × 6 descriptor. Ngưỡng tính theo đơn vị excl và evidence trực tuyến. Không có tham số theo dataset |

## 3. Quy trình nghiên cứu tự động, lặp (yêu cầu §3, Bước 1–6)

Đã chạy 15 vòng (Entry 1–15). Vòng lặp tự động 12 giờ cuối (AUTOLOOP, 2026-11-04 14:15 → 2026-11-05 00:30 UTC) được ghi trong
`handoff/AUTOLOOP.md` và `paper/BAO_CAO_AUTOLOOP.pdf`.

| Bước | Ví dụ cụ thể (AUTOLOOP) |
|---|---|
| 1. Phân tích bản chất | Chẩn đoán oracle trên dữ liệu phát triển: chuỗi vị trí đúng ở 0.96 khung on-map nhưng chỉ báo đúng 0.90. Thiếu hụt nằm ở đầu chuỗi CMU (~130 chuỗi ngắn mỗi run) và ở tỉ lệ VIO của 4Seasons (lệch 3–7 % so với GNSS) |
| 2. Giả thuyết | Ba nguồn có kiểu lỗi khác nhau (OWF thế giới mở, chuỗi tô-pô thế giới đóng, truy hồi một khung): khi cả ba trùng thì an toàn. Ngân hàng tỉ lệ chọn theo evidence sẽ tự bỏ các tỉ lệ thừa |
| 3. Triển khai | `analysis/owf.py` (`--scales`), `owf_hybrid.py`, `owf_union.py` (grammar `H\|m(e,D)\|t(e,D)`), `owf_hsi_job.py`. Đợt Kaggle tự động: `owf_wave.py` → `fanout.py --build-only` → `central_monitor.py` |
| 4. Đánh giá | 5 nhóm seed mới × 144 run (8 dataset có lỗ × 6 descriptor), so cặp trên CÙNG run với luật đương nhiệm và HSI-VN, có CI bootstrap |
| 5. Phân tích | Tách đóng góp từng thành phần (ví dụ Entry 13: hợp hai bậc +0.011, ngân hàng tỉ lệ +0.013). Ghi các hướng loại bỏ (xem dưới) |
| 6. Lặp lại | 5 vòng liên tiếp; cả 5 luật đăng ký trước đều đạt |

**Bảng điểm (recall gộp / số run > α / sai số điều hướng; 144 run mỗi nhóm):**

| Nhóm seed mới | HSI-VN (xuất phát) | Luật được kiểm | Luật đương nhiệm | Chênh, CI 95 % |
|---|---|---|---|---|
| 40–42 | 0.811 / 1 / 15.35 m | OWF-H 0.885 / 1 / 14.46 | HSI-VN | +0.074 [+0.060, +0.088] |
| 43–45 | 0.805 / 1 / 15.92 | OWF-HU 0.896 / 1 / 14.94 | OWF-H 0.878 | +0.018 [+0.014, +0.022] |
| 46–48 | 0.786 / 1 / 14.72 | OWF-HW-S 0.902 / 1 / 12.75 | OWF-HU 0.878 | +0.024 [+0.019, +0.031] |
| 49–51 | 0.804 / 0 / 14.34 | OWF-HWA-S 0.933 / 0 / 13.64 | OWF-HW-S 0.921 | +0.012 [+0.010, +0.014] |
| 52–54 | 0.823 / 1 / 14.32 | **OWF-HWA-S5 0.941 / 1 / 12.67** | OWF-HWA-S 0.937 | +0.0045 [+0.0024, +0.0070] |

Theo dataset, trên nhóm 52–54, luật cuối so với HSI-VN:

| Dataset | Δ recall |
|---|---|
| old town | +0.193 |
| countryside | +0.180 |
| Nordland | +0.146 |
| Oxford | +0.132 |
| office | +0.094 |
| Boreas | +0.086 |
| CMU | +0.063 |
| St Lucia | +0.049 |

**Hướng đã loại (kết quả âm, có số):**
- lớp quyết định riêng cho OWF (13 biến thể; trượt V2 / N1);
- ghép thẳng OWF → HSI (vỡ CMU, segFAR 0.089);
- đặc trưng độ tin OWF cho HSI (+0.0006);
- bầu chọn chuỗi bằng truy hồi top-1 (giảm độ đúng của chuỗi);
- đồng thuận hai nguồn (kém an toàn);
- ngân hàng hướng (trôi hướng VIO < 0.6°/km);
- thêm bậc sau Entry 14 (+0.001–0.004 nhưng có run vượt α).

## 4. Tài nguyên Kaggle (yêu cầu §4)

**Cấu hình (§4.1).**
- Token chỉ nằm trong `~/.kaggle/tok_<username>` (chmod 600) của container; KHÔNG có trong repo, dataset hay báo cáo.
- Mỗi lệnh dùng `KAGGLE_API_TOKEN=$(cat ~/.kaggle/tok_<acc>)`.
- Phiên mới: xin lại token từ người dùng.

**Tình trạng 22 tài khoản (kiểm lúc 2026-11-05 ~02:10 UTC).** Phép kiểm: đẩy một kernel nhỏ yêu cầu L4, in tên GPU, rồi xoá. Quota GPU là 30 giờ / tuần
và hồi lại khi Kaggle đặt lại tuần.

| Tình trạng | Tài khoản (username Kaggle) |
|---|---|
| Còn quota, có L4 | quynhtran35, yuan1103, phatle1578, nguyenmanh0404 (NguyenManh) |
| Còn quota, CHỈ T4 (yêu cầu L4 thì nhận máy không GPU) | yeshenhi, mxuanquy |
| Hết quota GPU tuần | nhatlong1103, quynhle07, caotienminh1 (= CaoTienMinh, cùng token), nguyenhoa99, synchan5704, anderson1202, loinguyentran, mucnokieu, huyenco, nguynduylm, phuongnehe, thnliu, linhmai24, lelynhan, duylnng (Duylan), hai1108 (HaiDinh) |

Phiên CPU (5 / tài khoản) không tính quota GPU. Mọi đợt OWF / HSI của AUTOLOOP chạy được trên CPU (mã thuần numpy, 4 job / phiên).

**Quản lý phiên (§4.2).** `automation/central_monitor.py` là một monitor nối tiếp cho mọi kernel:
- tự đẩy kernel vào slot trống, lấp đầy một tài khoản trước khi sang tài khoản kế (theo `automation/active_accounts.txt`);
- quá 8 phút (L4 / CPU) hoặc 10 phút (T4) còn QUEUED thì xoá + đẩy lại, tối đa 5 lần, rồi L4 → 2×T4;
- tự kéo kết quả, đánh dấu NEEDS_FIX khi job lỗi;
- trạng thái lưu trong file JSON, nên chạy lại được sau khi container khởi động lại (đã xảy ra lúc 00:05 UTC, không mất kernel nào).

**GPU / song song (§4.3).** Các đợt dùng mã CPU, vì OWF và HSI là bộ lọc numpy không cần GPU. Phiên L4 được dùng như máy nhiều lõi:
- `--par 46`: ~48 job chạy song song trên một phiên L4;
- phiên CPU: 4 job song song.

GPU chỉ cần khi trích descriptor mới (ví dụ VPR-Space); khi đó dùng 4×L4 / phiên như yêu cầu.

**Dữ liệu và tái sử dụng (§4.4).** Code dataset riêng mỗi phiên (`VPR_CODE_DS=dive-vpr-owf`). Cache dùng lại đã publish công khai:

| Dataset | Nội dung |
|---|---|
| `nhatlong1103/hmm-navcache-v2` | cache thiết kế / phát triển |
| `caotienminh1/hmm-navcache-r19` | seed 19–27 |
| `synchan5704/hmm-navcache-r40` | seed 40–48 |
| `synchan5704/hmm-navcache-r49` | seed 49–54 |

Kết quả mỗi đợt nằm ở `analysis/results/owf/*.tgz`. Tránh chạy trùng: luật quyết định mới được đánh giá NGOẠI TUYẾN từ khung OWF + mặt nạ HSI đã lưu, trong vài
phút thay vì một đợt Kaggle.

**Tối ưu làm việc (§4.5).**
- Monitor nối tiếp + vòng chờ nền (thông báo khi xong, không kiểm thủ công).
- Lịch tự đánh thức mỗi 2 giờ trong AUTOLOOP.
- Đọc paper / văn bản thay vì cả repo mã.

## 5. Kết quả so với tiêu chuẩn kỳ vọng (yêu cầu §5) — cập nhật 2026-11-05 chiều cho hai dòng SOTA và tổng quát; xem `paper/BAO_CAO_S1105.pdf`

| Tiêu chuẩn | Trạng thái | Bằng chứng / còn thiếu |
|---|---|---|
| Đóng góp khoa học rõ, novelty thuyết phục, tiềm năng A\* | **một phần** | HSI, OWF: cơ chế mới + gate tài liệu. Hệ ghép cuối mang tính kỹ thuật. Chưa có paper, chưa có đánh giá novelty độc lập |
| Hiệu quả cải thiện đáng kể, so với baseline / SOTA | **đạt** (cập nhật 2026-11-05 chiều) | Entry 17, đăng ký trước, seed mới 55–57, CÙNG 144 run: OWF-HWA-S5 0.937 / 1 run > α so với HSI-VN 0.806, TAO'26 0.846 (129 run > α), Xu'21 0.691 (75), Claxton'24 0.732 (99), oracle một-frame 0.847. Trên lỗ 10/50 %, off-map tự nhiên, NCLT, các đối thủ ngoài cũng không hợp lệ hoặc recall thấp hơn (`analysis/results/owf/s1105/`) |
| Bảo đảm lý thuyết có giả định, phạm vi | **một phần** | HSI Mệnh đề 1–7; OWF Mệnh đề 1–3 (cận Ville; đầu chuỗi là trường hợp yếu). Các bậc của luật hợp chưa có mệnh đề |
| Tổng quát trên nhiều dataset, không chỉnh riêng | **đạt (trong phạm vi đã thử)** | Một cấu hình cho 8 dataset × 6 descriptor. Thêm 2026-11-05 trên các tập không dùng để chỉnh luật: lỗ 10 % 0.933, lỗ 50 % 0.894, off-map tự nhiên 0.952, NCLT 0.781; đều hợp lệ trung bình. VPR-Space (ngoài Trái Đất, Entry 18): bộ ước lượng tổng quát tốt, nhưng lớp quyết định CỐ ĐỊNH quá bảo thủ trên chuỗi ngắn: 0.29 so với oracle một-frame 0.56, dù hợp lệ. Hạn chế đã ghi |
| Mã, cấu hình, log, kết quả lưu có hệ thống | **đạt** | `analysis/`, `automation/`, `analysis/results/`, `RESEARCH_LOG.md` (đăng ký trước + kết quả), `handoff/AUTOLOOP.md` (nhật ký từng bước) |
| Báo cáo giả thuyết, kết quả, hạn chế, hướng tiếp | **đạt** | `paper/BAO_CAO_HSI.pdf`, `paper/BAO_CAO_OWF.pdf`, `paper/BAO_CAO_AUTOLOOP.pdf`; mục dưới |

**Cập nhật 2026-11-06 (Entry 19–22, `paper/BAO_CAO_S1106.pdf`).**
- Hiệu quả: luật đương nhiệm được kiểm thêm trên hai nhóm seed mới (58–60, 61–63). Trên 3 nhóm, 432 run: recall 0.927–0.937, 9/432 run > α
  (2.1 %), TB segFAR 0.0063. Tiêu chuẩn "≤ 2 % run > α" đạt trên 2/3 nhóm.
- Lý thuyết: thêm Mệnh đề 5 (không dịch chuyển tức thời; kiểm trên seed mới) và Mệnh đề 6 (điểm giao của emission, bí danh odometry
  không thấy được). Mệnh đề 6 viết trước đợt phát triển; dự báo đúng cả cơ chế lẫn cái giá.
- **Entry 23 (đăng ký trước, seed 64–66): OWF-HWA-S5-NT-HQ thay luật khuyến nghị.** Hợp lệ tốt hơn (TB segFAR −23 %), điều hướng tốt
  hơn, recall −0.004. Cơ chế có mệnh đề riêng (Mệnh đề 7, viết trước đợt phát triển). Biến thể + phủ quyết ½: 0/144 run > α.
- **Entry 24 (seed 67–69): xác nhận độc lập luật mới.** 0/144 run > α; +0.136 so với HSI-VN; ba SOTA ngoài trên cùng run đều không hợp lệ
  (130 / 81 / 104 run > α) và có recall thấp hơn.
- Quy trình (yêu cầu §3): 6 vòng trong phiên (Entry 19–24). Hai vòng đăng ký trước, kiểm trên seed mới, quyết định theo quy tắc (giữ R*). Hai vòng âm ở
  phát triển nên không đốt seed mới. Nhóm 64–66 dùng cho Entry 23 (luật mới qua). Kho r67 đang sinh.
- Kaggle (yêu cầu §4): 4 tài khoản × 2 phiên 4×L4 + CPU. Kho seed `namhunhh/hmm-navcache-r61` (20 kernel CPU). Monitor trung tâm khởi động
  lại được sau khi container reset.

**Hạn chế còn tồn tại.**
- (mới) Bí danh odometry không thấy được trên CMU: nguồn 7/9 run > α trên 432 run mới. Cần emission hiệu chỉnh tuyệt đối theo điều kiện.
- Sai số điều hướng Nordland kém HSI-VN (6.3–9.6 vs 3.6–4.2 m): ~5 % báo thêm của OWF lệch quá excl.
- Countryside: chuỗi đúng chỉ ~0.87 khung (VIO trôi).
- CMU vẫn yếu nhất (0.86); một run CMU vượt α ở mọi luật trên seed 52–54.
- Lỗ là mô phỏng (30 % ô 300 m).
- Kho seed mới 40–54 đã dùng hết.

**Hướng tiếp theo (thứ tự ưu tiên).**
1. Sinh kho seed 55+ (`owf_wave.py --set fresh:55-60`, CPU) trước mọi quyết định mới.
2. Điểm vận hành điều hướng: trọng số fix theo hiệp phương sai OWF, hoặc cổng đổi mới trong bộ Kalman (áp cho mọi luật).
3. Trạng thái tỉ lệ liên tục trong OWF cho VIO.
4. So sánh với SOTA ngoài trên cùng giao thức; đánh giá trên NCLT và 16 bộ VPR-Space.
5. Viết paper quanh OWF: phát biểu thành mệnh đề cho bậc đồng thuận ba nguồn, hoặc giữ nó là phần hệ thống.
