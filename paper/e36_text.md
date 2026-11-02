# Báo cáo vòng 10 (Entry 36): phẫu thuật bản đồ phản thực TIẾN — null của chính quỹ đạo ma của hệ thống

*Branch `hmm-navigation-5`, 2026-11-02. Nhật ký: `RESEARCH_LOG.md` Entry 36 (đăng ký trước, sửa đổi, sai lệch). Lý thuyết:
`paper/cms_theory.md` §4f (Mệnh đề 16–18). Code: `analysis/cms_vec.py`, `cms_fwd.py`, `cst_audit.py`, `e36_run.py`, `n40_run.py`,
`safevpr26.py`, `safevpr26_eval.py`; bảng: `paper/build_e36_report.py` → `paper/e36_tables.md`. Phiên này không có token Kaggle: mọi
tính toán chạy trên 4 lõi CPU của phiên, từ cache công khai.*

## 1. Bốn việc được giao và kết luận ngắn

{{SUMMARY}}

## 2. Vector hoá thống kê phản thực

`analysis/cms_vec.py` làm đúng phép tính của `cms_exact.cms_stats_exact` nhưng theo lô frame: nhóm cửa sổ theo độ dài, Procrustes theo
lô, tra cứu ngoại hình bằng searchsorted trên các hàng nối đuôi (có hiệu chỉnh chính xác một bước), phép thử hành lang hai tầng (phủ
anchor + dải mơ hồ) và **tính thành viên hành lang trên các hàng bản đồ** thay vì trên từng mục của danh sách dài. Kiểm tra: trùng tuyệt
đối với vòng lặp (8/8 đầu ra, sai khác tối đa 0); trùng với cache Kaggle đã công bố: chi phí tuyến và độ khác biệt (thật và phản thực)
100 %, winner 99.8 % (hoà điểm của danh sách fp16). Phát hiện kèm: đường CPU của `topk_long` dùng độ lệch chuẩn lệch (N), đường GPU
dùng không lệch (N − 1) → z lệch hằng số √(N/(N−1)); đã sửa. Thời gian (1 lõi): 3.9 ms/frame (N = 20) so với 9.4 ms của vòng lặp
trên cùng lõi và 10.3–17.5 ms đo trên Kaggle → **ngưỡng đặt trước < 10 ms/frame của Entry 32 nay đạt**. N = 40: 6.6 ms/frame (trước
khi tính thành viên theo hàng bản đồ: 16 ms).

## 3. Chẩn đoán: giả định của Mệnh đề 14 sai ở mọi độ sâu, không chỉ ở mép

`analysis/cst_audit.py` đo trực tiếp đại lượng mà Mệnh đề 14 chặn, P(∃ t ∈ G₀: r_t ≤ ε), trên các đoạn off-map **thật** (nhãn chỉ để
đánh giá). Nếu (S3-T) đúng thì tỷ lệ này ≤ a/π ≈ 0.05.

{{AUDIT}}

Hai nguyên nhân: (i) null track của CST là chuỗi winner phản thực **của từng frame**, mỗi frame một phẫu thuật riêng và một bộ ước lượng
khác (phép thử tuyến) — các winner liên tiếp là những nơi không liên quan, nên null kém mạch lạc hơn nhiều so với quỹ đạo ma mà chuỗi vị
trí thật sự đi theo sau khi rời bản đồ (dính mép lỗ, khoá vào đường song song hay nơi giống nhau ở xa: CMU, sai 1.1 km với residual
6–15 m); (ii) cửa sổ hình dạng bị cắt ở đầu chuỗi (43 % frame của CMU: 130 chuỗi ngắn, robot bắt đầu trong lỗ). Các luật CST vẫn hợp lệ
ở Entry 34 chỉ vì khởi phát của chuỗi hiện diện cũng phải xảy ra. Thiệt hại điều hướng của CST (Entry 35: Boreas +9 m, old town +13.6 m)
đến chủ yếu từ các fix sai **sâu** trong chuyến (Boreas NetVLAD s7: 269/345 ở độ sâu ≥ 80 frame, sai trung vị 419 m), không phải ở mép.
Mất recall trên Oxford (H35d) là chuyện khác: CST **chặt hơn** SH trên Oxford.

## 4. Phương pháp: phẫu thuật tiến và hiệu chuẩn đầu-cuối

**Lối thoát ảo.** Tại frame τ (mỗi 1 excl quãng đường), xoá vùng bản đồ robot đi qua sau τ: V_τ = { m : d(m, X⁺) ≤ ρ, d(m, X⁺) < d(m, X⁻) }
(X⁺ / X⁻: vị trí tin sau / trước τ trong off_d + 20 excl quãng đường; cắt Voronoi giữ bản đồ trước điểm thoát; ρ = off_d), rồi chạy
**chính chuỗi vị trí của hệ thống** (bản sao chính xác của `DiagFilter`, emission tính lại trên bản đồ đã phẫu thuật; khớp MAP thật
99.95–100 %) tiến từ niềm tin của nó tại τ. **Khởi đầu ảo:** chuỗi khởi động lại đều tại τ, bỏ hành lang ρ quanh 3 excl đường tiếp theo,
cửa sổ cắt tại τ (đúng tình huống robot bắt đầu trong lỗ).

**Ba luật hiệu chuẩn từ các lần chạy ảo** (đoạn ảo cắt như đoạn thật; ngưỡng = min theo bin vị trí trong chuyến, mỗi bin ≥ 2/a đoạn):
- **CST-F** (Mệnh đề 16–17): ε = phân vị a của cực tiểu residual của quỹ đạo ghép (thật đến τ, ma sau τ) trên đoạn ảo. Mọi báo cáo phải qua
  ⇒ tỷ lệ báo sai theo đoạn ≤ a/π **chỉ nhờ phép thử hình dạng**, mọi vị trí (kể cả mép), mọi chuỗi hiện diện, mọi dung sai SH.
- **CST-J** (Mệnh đề 18): mô phỏng **cả quyết định** dọc lần chạy ảo — chuỗi hiện diện tiếp tục từ trạng thái thật tại τ với log-LR phản thực,
  cổng +G trên quỹ đạo ma, residual — và chọn dung sai lớn nhất sao cho tỷ lệ báo của đoạn ảo ≤ a (có thể = ∞).
- **CST-J\*** (thăm dò, tìm thấy giữa đánh giá): như CST-J, nhưng frame có cửa sổ < 1 excl được phép báo và điều này được tính trong chính mô
  phỏng (khởi đầu ảo báo trên cửa sổ ngắn = báo sai).
SH, +G, +NGRr chỉ bỏ báo cáo nên giữ nguyên các cận (Bổ đề 7): **SH ∧ CST-J(\*)** hợp lệ với mọi dung sai SH.

## 5. Kết quả

{{TABLES}}

## 6. Thảo luận, hạn chế, việc tiếp theo

{{DISCUSSION}}
