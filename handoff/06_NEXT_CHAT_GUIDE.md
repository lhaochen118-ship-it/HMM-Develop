# 06 — Hướng dẫn cho khung chat mới: đọc repository và việc tiếp theo

*2026-11-04, branch `hmm-2nd-idea` (repo `lhaochen118-ship-it/hmm-develop`, public). Không tạo PR. Thay cho `history/05_NEW_CHAT_GUIDE_idea2-start.md`.*

## 1. Đọc theo thứ tự (≈ 30 phút)

1. `handoff/03_HANDOFF.pdf` — mục tiêu, quyết định đã chốt, vị trí mọi thứ, sổ dùng tập kiểm tra, **việc tiếp theo** (§6).
2. `handoff/01_SCIENTIFIC_FINDINGS.pdf` — đóng góp, số liệu, kết quả âm (để không lặp lại hướng đã bác).
3. `handoff/02_ENGINEERING_OPS_NOTES.pdf` — công cụ, cách chạy một đợt Kaggle, lỗi đã gặp.
4. `handoff/ENVIRONMENT_SUMMARY.pdf` §0 — tài khoản, dataset công khai, gói cần cài.
5. `paper/BAO_CAO_HSI.pdf` (15 trang) — câu chuyện đầy đủ, bảng, hình; `paper/hsi_theory.md` — Mệnh đề 1–7.
6. Khi cần chi tiết một vòng: `RESEARCH_LOG.md` (Entry mới ở trên cùng; Entry 1–9 = HSI, Entry 10 = OWF).
6b. Ý tưởng 2b (OWF): `paper/BAO_CAO_OWF.pdf`, `paper/owf_theory.md` (Mệnh đề 1–3), `LITERATURE_GATE.md` Gate 18.
6c. **Luật khuyến nghị hiện tại và cách tới đó:** `paper/BAO_CAO_AUTOLOOP.pdf` (vòng lặp 12 giờ, Entry 11–15), `handoff/AUTOLOOP.md` (nhật ký
    trạng thái), `RESEARCH_LOG.md` Entry 11–15.
7. Yêu cầu gốc của user: `HMM_Navigation_Yeu_Cau_Nghien_Cuu_Cap_Nhat.docx`; quy trình: `handoff/04_RESEARCH_WORKFLOW.pdf`.

## 2. Bản đồ repository (chỉ phần dùng cho ý tưởng 2)

```
analysis/hsi.py            phương pháp (online_v2 + các cờ), chứng chỉ hình học, cầu hồi cứu, hiệu chuẩn conformal
analysis/hsi_eval.py       VARIANTS (HSI-VN = luật khuyến nghị) + đánh giá một (dataset, descriptor, seeds)
analysis/hsi_compare.py    bảng so sánh biến thể theo dataset (+ SH với --base)
analysis/hsi_summary.py    H1–H5 so với SH;  hsi_entry8_test.py  tiêu chí T1–T4;  hsi_alpha.py  quét α
analysis/hsi_fresh.py      sinh tập kiểm tra mới (bố cục lỗ mới) từ dump descriptor rồi đánh giá
analysis/nav_demo.py       HMM + giao thức + cache (dùng chung với ý tưởng 1);  vprlib.py  loader dataset
automation/                hsi_wave.py, fanout.py, central_monitor.py, hsi_collect.py, fetch_outputs.py, publish_dataset.py, md2pdf.py
paper/                     BAO_CAO_HSI.(md|pdf), hsi_report_text.md, build_hsi_report.py, hsi_theory.md, tables/, figures/
analysis/results/hsi/      kết quả thô (JSON mỗi run + mặt nạ báo theo frame), baselines_idea1/ (SH, CST-JS của ý tưởng 1)
analysis/owf.py            ý tưởng 2b: bộ lọc thế giới mở (OpenWorldFilter + main: một run từ navcache + dump)
analysis/owf_summary.py    so sánh cặp với SH / CST-JS / HSI-VN, kiểm toán vị trí, giả thuyết H1–H9, tiêu chí D1–D3 (--decide)
automation/owf_wave.py     nhóm job (main / abl / holes / design / r19 / r19hsi), owf_collect.py  gom JSON theo tập
analysis/results/owf/      JSON mỗi run của Entry 10 (tập A, tập B + HSI-VN cùng run, ablation, lỗ) và Entry 11–15 (tgz phát triển / kiểm tra)
analysis/owf_hybrid.py     chuỗi lai OWF → HSI (thay est_c của cache khi OWF tự tin + ổn định; --mode xms0.9_16) rồi chạy hsi_eval (--hsiframes: mặt nạ)
analysis/owf_hsi_job.py    một job của tập mới: owf.py (khung) → owf_hybrid.py trong cùng kernel
analysis/owf_union.py      lớp quyết định ngoại tuyến: H ∨ m(e,D) ∨ t(e,D) (đồng thuận ba nguồn) từ khung OWF + mặt nạ HSI + navcache
analysis/owf_decide.py     biến thể quyết định riêng của OWF (âm tính: không đạt V2 / N1); owf_score.py, autoloop_board.py  bảng Score V1/V2/N1
automation/owf_wave.py     + fresh:A-B (kho seed mới), fresh_owf:A-B --pool --bank/--banks --hsiframes (đợt kiểm tra); fetch_done.py (kéo dần cache)
RESEARCH_LOG.md, LITERATURE_GATE.md (Gate 17 HSI, Gate 18 OWF), handoff/, history/ (tài liệu cũ, ý tưởng 1)
```

## 3. Khởi động phiên mới (≈ 10 phút)

```bash
pip install -q kaggle markdown xhtml2pdf scipy scikit-learn matplotlib pypdf
```

- Xin user token Kaggle của 7 acc (`quynhle07, nguyenhoa99, quynhtran35, yuan1103, caotienminh1`, + `synchan5704, yeshenhi` từ Entry 10); lưu
  `~/.kaggle/tok_<acc>` (chmod 600). Không ghi token ở bất kỳ đâu khác.
- **Kiểm tra trước khi làm gì:** `git fetch origin hmm-2nd-idea && git log HEAD..origin/hmm-2nd-idea` — Entry 10 được làm từ một checkout CŨ (không
  thấy Entry 1–9) và hai phiên chat đã chạy song song trên cùng branch / cùng acc. Đặt `export VPR_CODE_DS=<tên riêng>` cho mọi kernel của mình
  (code dataset riêng, `make_eval_kernel.py`) để không ghi đè code của phiên khác.
- Tái tạo số liệu chính không cần Kaggle: giải nén `analysis/results/hsi/hsi_results_json.tgz` và `analysis/results/baselines_idea1/e37/oc_e37.tgz`,
  `e38/oc_e38.tgz` vào scratchpad rồi chạy, ví dụ
  `python3 analysis/hsi_compare.py <x>/main HSI-VN,HSI-rot-m-sc --base <x>/oc37 <x>/oc38` và
  `python3 analysis/hsi_entry8_test.py <x>/test_s16_18 HSI-VN` (phải ra "ALL PASS").
- Dữ liệu thiết kế cục bộ (28 cache seed 0, ~300 MB) cho thử nghiệm nhanh: tải từ `nhatlong1103/hmm-navcache-v2` bằng
  `kaggle datasets download nhatlong1103/hmm-navcache-v2 -f <tên file> -p <dir>` (KHÔNG để `-f` rỗng — sẽ kéo cả 1.3 GB).

## 4. Cách làm một vòng nghiên cứu (đã kiểm chứng)

1. Chẩn đoán cơ chế trên dữ liệu thiết kế / phát triển bằng script nhỏ (`analysis/`, cục bộ, vài phút).
2. Hiện thực thành MỘT cờ mới trong `online_v2` (mặc định = hành vi cũ) + biến thể có tên trong `VARIANTS`; kiểm hồi quy (biến thể cũ cho đúng
   số cũ) và smoke test trên 2–4 run thiết kế.
3. Đợt phát triển trên seed 0–9 (`hsi_wave.py` → `fanout.py --build-only --cpu --nodumps` → `central_monitor.py`), 15–40 phút.
4. Viết đăng ký trước vào `RESEARCH_LOG.md` (tiêu chí theo thước đo kết quả, quy tắc quyết định), commit + push.
5. Đánh giá trên **một nhóm seed chưa dùng** của `caotienminh1/hmm-navcache-r19` (19–21, 22–24 còn trống; 25–27 đã dùng ở Entry 10) (token `DIR:navcache_`, `--nodumps --ds caotienminh1/hmm-navcache-r19`,
   seeds `19-21` …), ghi kết quả + quyết định, cập nhật `03_HANDOFF.md` §5, báo cáo (`paper/build_hsi_report.py`), commit + push.

## 5. Việc tiếp theo

Chi tiết trong `03_HANDOFF.md` §6. Luật khuyến nghị: **OWF-HWA-S5** (Entry 15; seed 52–54: 0.941 vs HSI-VN 0.823). Kho seed
mới đã dùng hết (40–54); quyết định tiếp theo cần sinh kho mới bằng `owf_wave.py --set fresh:55-60` (34 kernel CPU, ~2.5 giờ).

1. **Countryside:** chuỗi tốt nhất chỉ đúng ~0.87 khung (VIO trôi); sai số điều hướng 21.7 m (HSI-VN 20.0). Hướng tiếp: ước lượng tỉ lệ liên tục
   (trạng thái tỉ lệ trong bộ lọc thay cho lưới), mô hình trôi tỉ lệ theo thời gian.
2. **Nordland điều hướng:** 9.6 m vs HSI-VN 4.2 m trên seed 49–51. Các báo OWF tự tin nhưng lệch vài chục mét kéo bộ Kalman; thử báo với bán kính
   đĩa nhỏ hơn cho fix điều hướng (điểm vận hành riêng, như HSI-VMN).
3. **Điểm vận hành điều hướng:** luật hợp hai bậc trên mặt nạ HSI-VMN (phát triển 0.892 / 12.66 m) chưa được kiểm trên tập mới.
4. **NCLT:** không có trong kho mới (off-map tự nhiên); cần cấu hình đánh giá riêng.
5. **Áp dụng lên 16 bộ VPR-Space** (https://github.com/rfechner/VPR-Space): tải release → trích 6 descriptor (GPU, ước GPU-giờ trước) → loader +
   odometry từ pose → giao thức bản đồ = db, truy vấn = query → cache → đánh giá luật khuyến nghị.
