# Báo cáo vòng 7: hiệu chuẩn rủi ro điều hướng và tự kiểm toán toàn bộ

*Branch `hmm-navigation-5`, 2026-11-01. Nhật ký `RESEARCH_LOG.md` Entry 29 (đăng ký trước, push trước đánh giá). Kiểm toán chi
tiết: `paper/AUDIT_E29.md`. Lý thuyết: `paper/cms_theory.md` §4b. Novelty: `LITERATURE_GATE.md` Gate 13. Vòng trước:
`paper/BAO_CAO_E28.pdf`.*

**Tóm tắt.**

1. **Phương pháp đề xuất cuối: CMS-CPC/H+SH+G+NGR** = CMS (null hiệu chuẩn sinh từ chính luồng triển khai bằng phẫu thuật bản đồ
   quanh niềm tin của hệ thống, null **chính xác** top-100 của bản đồ đã phẫu thuật) + chuỗi hiện diện HMM + dừng hình dạng + cổng
   đồng thuận + **cổng innovation phản thực** (hiệu chuẩn rủi ro điều hướng, không nhãn). Leave-one-dataset-out chọn luật này ở
   **7/7 fold** (α = 0.05; ở α = 0.01 chọn bản α = 0.01 của nó, cũng 7/7).
2. So với phương pháp tốt nhất trước đó (CPC-SC-T½+SH), trên cùng 366 run: **recall cao hơn 7/7 dataset và sai số điều hướng thấp hơn
   7/7** (ví dụ 4S countryside 0.491 / 34.3 m so với 0.334 / 51.3 m; Boreas 0.775 / 4.5 m so với 0.666 / 5.7 m), segFAR ≤ 0.009;
   bootstrap cụm theo seed: recall cao hơn có ý nghĩa 6/7, sai số thấp hơn có ý nghĩa 6/7, không dataset nào kém hơn.
3. Bản bảo đảm chặt **CMS-CPCW/H+SH+NGR** (Định lý 6′: khởi phát bằng chuỗi cửa sổ hữu hạn): cũng hơn luật cũ 7/7 về recall và 7/7
   về sai số. Đường cong: recall tại FL ≤ 0.01 của CMS-CPC/H+SH+NGR cao hơn luật cũ **7/7**.
4. Tự kiểm toán: không có rò nhãn; các định lý cũ đã kiểm lại; sửa hai lỗi thật (ngưỡng khởi phát của chuỗi đầy đủ bộ nhớ → CMS-CPCW;
   null phản thực cắt cụt → bản chính xác, kết quả gần như không đổi) và bổ sung khoảng tin cậy.

## 1. Tự kiểm toán: các vấn đề tìm thấy và cách sửa

| Mục | Vấn đề | Mức | Sửa |
|---|---|---|---|
| Định lý | Ngưỡng khởi phát của chuỗi đầy đủ bộ nhớ (CPC-SC vòng 3, CMS-CPC vòng 6) hiệu chuẩn trên chuỗi khởi động ở odds 1 với lập luận "odds 1 là mức cao nhất của chuỗi chưa báo" — sai khi κ > 0 (κ ≈ 2.4–4.7) | Nghiêm trọng (lý thuyết) | Định lý 6′ + luật **CMS-CPCW**: khởi phát bằng chuỗi cửa sổ hữu hạn |
| Code | Null phản thực bị cắt cụt ở top-100 (giả thuyết hạng > 100 bị thiếu, giá trị dự phòng sai) | Trung bình | `cms_exact.py`: top-300 trên GPU, đúng top-100 của bản đồ đã phẫu thuật; tính lại 366 + 216 run |
| Thống kê | Vòng 6 báo trung bình và số dataset thắng; các run (seed × descriptor) không độc lập | Bổ sung | Bootstrap cụm theo seed + sign test (`paired_stats.py`), Bảng 5 |
| Dữ liệu | Baseline có nhãn đánh giá cả trên điều kiện huấn luyện (`bsel`); CMS chuyển đạo theo phiên; thiết kế dùng vài run giữ lại | Trung bình | Ghi rõ (so sánh với baseline là bảo thủ); bản nhân quả `[loco]`; LODO |
| Định lý | S3 cần điều kiện trên nhãn "đoạn tốt"; Định lý 6 không phủ đoạn ở đầu chuyến off-map | Trung bình | Phát biểu lại (§4b(ii)) |
| Đánh giá | Bộ lọc Kalman của đánh giá quá tự tin (√P ≈ 0.6 m, độ lợi ≈ 0.014); odometry căn bằng GT ở đầu chuỗi; với dataset mô phỏng bộ lọc dùng odometry khác luật quyết định | Nhẹ–trung bình | Ghi rõ; chung cho mọi luật |
| Novelty | "no prior instance found" sau vài truy vấn | Nhẹ | Tìm rộng hơn (Gate 13); hạ chữ; cổng +NGR không tuyên bố mới |
| Đã kiểm, đúng | Bổ đề 1–2, Định lý 1 (Shiryaev–Roberts), Định lý 5, PAC (Hệ quả 9), chỉ số conformal, Procrustes, TAO, metric segFAR/FL/recall, không rò nhãn trong `cms.py` / `cms_exact.py` / `navrisk.py` | — | — |

## 2. Phương pháp mới của vòng này

**Hiệu chuẩn rủi ro điều hướng: cổng innovation phản thực (+NGR, `analysis/navrisk.py`).** Chẩn đoán (nhãn chỉ để phân loại):
fix đúng được chấp nhận có innovation nhỏ (trung vị 0.5–8 m), fix sai gây hại có innovation lớn (phân vị 90 % là 42–856 m); một
fix sai dịch ước lượng của bộ lọc K·ν. Winner phản thực j_cf của CMS là một fix sai theo cấu trúc; d_cf = |m(j_cf) − m(j)| là
innovation mà nó gây ra. Cổng: báo cáo t chỉ khi luật nền báo cáo **và** ν_t = |fix_t − x̂_t⁻| ≤ τ, τ = phân vị β = 0.05 của d_cf
trong nhóm hiệu chuẩn; mở khoá cho một chuỗi khi luật nền đã báo R = H frame liền và các vector innovation đồng nhất (phân tán
≤ excl/2: bộ lọc bị lệch khỏi một quỹ đạo nhất quán — trường hợp trôi). Cổng chỉ **bỏ** báo cáo ⇒ giữ mọi cận theo đoạn.

**Khởi phát chặt (CMS-CPCW).** Khởi phát khi log-odds của chuỗi cửa sổ W = H frame (khởi động lại ở odds 1) vượt κ_W (phân vị trên
các đoạn phản thực của cùng chuỗi cửa sổ); duy trì bằng chuỗi đầy đủ (log-odds > 0) và dừng SH. Định lý 6′: tỷ lệ khởi phát sai mỗi
đoạn ≤ α(n+1)/(πn+1), mọi phụ thuộc, không phụ thuộc trạng thái lúc vào đoạn.

**Null phản thực chính xác (`analysis/cms_exact.py`).** Mỗi frame giữ top-300; bản đồ đã phẫu thuật dùng đúng 100 entry chưa che
đầu tiên cho giả thuyết, tra cứu ngoại hình và giá trị dự phòng.

## 3. Tối ưu tính toán

- Thống kê chính xác: 366 job `cms_exact.py` (top-300 trên GPU + thống kê trên CPU) cân bằng tải LPT trên 10 phiên L4×4 (40 job song
  song mỗi phiên, 4 GPU chia vòng); độ bền lỗ 10/50 %: 216 job trên 10 phiên L4 của 5 acc khác, chạy đồng thời (20 phiên L4).
- Đánh giá cuối (đường cong + mặc định, 2 mức α, nhân quả, cổng điều hướng, ablation) trên các phiên L4 được giải phóng.
- Không sửa code trong lúc tạo kernel (mỗi lần sửa buộc upload lại code cho acc kế tiếp).

{{TABLES}}

## 5. Đọc kết quả

1. **Cổng điều hướng làm đúng việc (Bảng 1, 5).** So với chính CMS-CPC/H+SH không cổng: sai số giảm có ý nghĩa trên 6/7 (Boreas
   −5.8 m, Nordland −7.3 m, NCLT −3.2 m, CMU −2.7 m), segFAR giảm 7/7, recall chỉ mất ≤ 0.011. Đây là vấn đề còn lại của vòng 6
   (ở α = 0.05 CMS kém luật cũ về sai số 4/7): nay CMS ở α = 0.05 tốt hơn luật cũ cả về recall lẫn sai số.
2. **Ablation cổng.** Không mở khoá (+NG) khoá chết trên VIO trôi (old town recall 0.485 / 73.8 m, countryside 0.313 / 72.7 m); cổng
   dead-reckoning cổ điển (+DRG) khoá chết trên NCLT (56.3 m) và old town (68.9 m): cơ chế mở khoá theo innovation đồng nhất là cần
   thiết. Cổng gắn vào luật cũ (CPC-SC-T½+SH+NGR) chỉ cải thiện ít — lợi ích đến từ việc kết hợp CMS (recall cao) với cổng (sai số thấp).
3. **Luật được chọn (Bảng 1, 6, 7).** CMS-CPC/H+SH+G+NGR: Boreas 0.775 / 0.003 / 4.5 m, NCLT 0.612 / 0.002 / 4.3, CMU 0.822 / 0.009 / 4.0,
   Nordland 0.765 / 0.000 / 5.6, office 0.800 / 0.000 / 9.7, old town 0.703 / 0.006 / 26.1, countryside 0.491 / 0.001 / 34.3; LODO chọn
   nó 7/7 fold ở α = 0.05 (regret 0–2.5 m) và bản α = 0.01 của nó 7/7 fold ở α = 0.01 (regret 0–2.4 m). So với Claxton'24 (có nhãn):
   sai số thấp hơn 7/7 (−8.5 … −83.3 m) với segFAR thấp hơn 0.11–0.27.
4. **Bảo đảm chặt không làm mất kết quả (Bảng 1, 4).** CMS-CPCW/H+SH+NGR (Định lý 6′) đạt recall 0.468–0.826 và sai số thấp hơn luật cũ
   7/7; tỷ lệ khởi phát sai mỗi đoạn 0.03–0.09·α.
5. **Đường cong (Bảng 3).** CMS-CPC/H+SH+NGR: recall tại FL ≤ 0.01 hơn luật cũ 7/7 (Boreas 0.809 so với 0.770, NCLT 0.632 so với 0.612,
   CMU 0.783 so với 0.744, Nordland 0.815 so với 0.794, countryside 0.605 so với 0.528), hơn Claxton'24 / TAO'26 (có nhãn) 6/7.
6. **Null chính xác (Bảng 6).** Kết quả của bản cắt cụt và bản chính xác chênh ≤ 0.005 recall: số liệu vòng 6 vẫn đúng; Định lý 6 kiểm
   lại với null chính xác: tỷ lệ thực tế / α = 0.46–1.18, dưới cận 7/7 (Bảng 9).
7. **Độ bền tỷ lệ lỗ (Bảng 8).** Khuyết 10 %: recall của CMS-CPC/H+SH+NGR cao hơn CPC-SC+CS 6/6, segFAR ≤ 0.009, sai số thấp hơn 4/6
   (countryside 28.3 so với 49.4 m); khuyết 50 %: recall cao hơn 6/6, cổng đưa CMU từ 0.052 về 0.027 (< α), sai số thấp hơn 4/6.

## 6. Hạn chế và việc tiếp theo

- Sai số tuyệt đối phụ thuộc bộ lọc Kalman của đánh giá (chung cho mọi luật, khởi tạo tại pose thật, odometry căn ở đầu chuỗi).
- Bảo đảm segFAR của CMS-CPC (khởi phát chuỗi đầy đủ) là thực nghiệm; bản chứng minh chặt là CMS-CPCW (recall thấp hơn ≤ 0.045).
- Cổng +NGR có bán kính ≈ off_d (đơn vị bài toán), hiệu chỉnh theo điều kiện; phát biểu rủi ro của nó là gần đúng (Mệnh đề 11).
- Hiệu chuẩn chuyển đạo theo phiên; bản nhân quả `[loco]` có số liệu trong Bảng 1–2.
- Việc tiếp theo: robot thật vòng kín; benchmark off-map tự nhiên ngoài NCLT; nộp bài (novelty: Gate 12–13).
