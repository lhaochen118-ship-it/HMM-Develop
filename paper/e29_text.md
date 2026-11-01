# Báo cáo vòng 7: hiệu chuẩn rủi ro điều hướng và tự kiểm toán toàn bộ

*Branch `hmm-navigation-5`, 2026-11-01. Nhật ký `RESEARCH_LOG.md` Entry 29 (đăng ký trước, push trước đánh giá). Kiểm toán chi
tiết: `paper/AUDIT_E29.md`. Lý thuyết: `paper/cms_theory.md` §4b. Novelty: `LITERATURE_GATE.md` Gate 13. Vòng trước:
`paper/BAO_CAO_E28.pdf`.*

{{SUMMARY}}

## 1. Tự kiểm toán: các vấn đề tìm thấy và cách sửa

| Mục | Vấn đề | Mức | Sửa |
|---|---|---|---|
| Định lý | Ngưỡng khởi phát của chuỗi đầy đủ bộ nhớ (CPC-SC vòng 3, CMS-CPC vòng 6) hiệu chuẩn trên chuỗi khởi động ở odds 1 với lập luận "odds 1 là mức cao nhất của chuỗi chưa báo" — sai khi κ > 0 (κ ≈ 2.4–4.7) | Nghiêm trọng (lý thuyết) | Định lý 6′ + luật **CMS-CPCW**: khởi phát bằng chuỗi cửa sổ hữu hạn |
| Code | Null phản thực bị cắt cụt ở top-100 (giả thuyết hạng > 100 bị thiếu, giá trị dự phòng sai) | Trung bình | `cms_exact.py`: top-300 trên GPU, đúng top-100 của bản đồ đã phẫu thuật; tính lại 366 + 216 run |
| Thống kê | Vòng 6 chỉ báo trung bình và số dataset thắng; các run không độc lập | Nghiêm trọng (diễn giải) | Bootstrap cụm theo seed + sign test (`paired_stats.py`); tuyên bố vòng 6 được hạ xuống (recall có ý nghĩa 4/7, sai số 2/7) |
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

{{READING}}

## 6. Hạn chế và việc tiếp theo

{{LIMITS}}
