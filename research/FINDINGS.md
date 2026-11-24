# FINDINGS — sổ phát hiện

Mỗi finding: ID, phát biểu, **mức bằng chứng** ([V]/[S]/[P]/[R]), run_ids, phạm vi/giới hạn. Không có run_id → không phải finding.

| ID | Phát biểu | Mức | Runs | Phạm vi / giới hạn |
|---|---|---|---|---|
| F1 | SALAD (dino_salad.ckpt) nạp đúng từ bundle (missing=0/unexpected=0, 8448-d); single-image R@1 0.617 trên Nordland Short summer→winter (600 frame) | R | L001_NB1v3 | Không có log trong repo |
| F2 | Trên Nordland 4 mùa (800 frame/mùa, ref=summer): filter v=1 tăng R@1 0.819→0.889 và giảm ECE 0.076→0.028; CCBF ≈ filter | R | L002_NB2 | Oracle motion (A1), stride≈45 (A2), fit lệch cặp (A3), rò rỉ centroid (A4) ⇒ cận trên |
| F3 | τ theo mùa gần như bằng nhau với SALAD trên Nordland (0.0309 ×3, 0.0253 winter) ⇒ tiền đề CCBF yếu trên Nordland | R | L002_NB2 | τ_fall/τ_winter fit trên cặp sai (A3) |
| F4 | (Synthetic) nhiễu similarity tương quan dọc đường chéo làm HMM ngây thơ giảm acc 0.91→0.18–0.21 và confident-wrong 0.2%→18% khi ρ: 0→0.85 | P | R20261124-001_P0, -002_P0 | Mô hình Gaussian, đồng nhất |
| F5 | (Synthetic) ρ ước lượng không nhãn (che top-k, tương quan đường chéo lag-1) sai số ≤ 0.02 | P | R20261124-001_P0, -002_P0 | Chưa thử trên dữ liệu thật |
| F6 | (Synthetic) β tối ưu theo NLL khớp 1/VIF(ρ̂, L_eff) với L_eff∈[2,8]; công thức tiệm cận (1−ρ)/(1+ρ) over-temper | P | R20261124-001_P0, -002_P0 | L_eff fit trên calib |
| F7 | (Synthetic, phương pháp luận) ECE có thể "đẹp" do hai sai lệch ngược chiều triệt tiêu (ρ=0.5: ECE 0.03 nhưng NLL/acc tệ) ⇒ không dùng ECE một mình | P | R20261124-001_P0, -002_P0 | Áp dụng cho mọi đánh giá hiệu chỉnh |
| F8 | (Synthetic) whitening đường chéo đơn giản (xấp xỉ AR-HMM) tệ hơn tempering về acc | P | R20261124-001_P0, -002_P0 | AR-HMM đúng cần pair-state |
| F9 | (Synthetic) L_eff giảm đơn điệu khi motion kernel rộng ra (std 0.5→6–8; 1→3–4; 2→2–3) ⇒ L_eff là bộ nhớ của bộ lọc; dự đoán về leak **không** được ủng hộ | P | R20261124-003_P0b, -004_P0b | Gaussian, đồng nhất |
| F10 | (Synthetic) Motion prior càng sắc, tác hại của bằng chứng tương quan và lợi ích tempering càng lớn (NLL 1.52→0.69 ở std 0.5 vs 2.94→2.40 ở std 2) ⇒ dự đoán tương tác M2×M3 (H18) | P | R20261124-003_P0b, -004_P0b | Cần kiểm trên dữ liệu thật |
