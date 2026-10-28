# 03 — Handoff (cho khung chat mới)

*Cập nhật 2026-10-28. Chỉ ghi mục tiêu, trạng thái, quyết định đã chốt, vị trí mọi thứ và việc tiếp theo. Chi tiết
khoa học ở `01_SCIENTIFIC_FINDINGS.pdf`, chi tiết vận hành ở `02_ENGINEERING_OPS_NOTES.pdf`, tài khoản và dữ liệu ở
`ENVIRONMENT_SUMMARY.pdf`. Thứ tự đọc: `00_READ_ME_FIRST.md`.*

## 1. Mục tiêu

Viết một research paper hạng A/A\* (RA-L/IROS/ICRA trở lên) về **độ tin cậy của Visual Place Recognition**: chấp nhận
hay từ chối match top-1, với **kiểm soát false-accept rate không cần nhãn** và bền vững với thay đổi ngoại hình và
domain. Quy trình làm việc: `04_RESEARCH_WORKFLOW.pdf`.

## 2. Trạng thái hiện tại

- **Phương pháp:** SelfCal ("your map is its own calibration set"), có hai chế độ trên cùng một hạ tầng:
    - **SelfCal-AA:** bền vững nhất, là method chính.
    - **SelfCal-Gap:** power cao.
- **Kết quả:** đủ cho 4 dataset × 6 descriptor, cùng ablation, domain lạ, FDR, map-size và Nordland lấy mùa đông làm
  bản đồ.
- **Paper:** `paper/selfcal_paper.md`, bản build là `paper/SelfCal_paper_full.pdf` (đã có Gap).
  `paper/SelfCal_paper_AA_only.pdf` là bản chỉ-AA, giữ lại để đối chiếu.
- **Mức đánh giá hiện tại:** A (RA-L/IROS khá). Để lên A\* còn thiếu:
    - kiểm định độc lập cho các lựa chọn sau-khi-xem-dữ-liệu;
    - power trên bản đồ lớn và dị biệt (MSLS);
    - phần sequence có bảo đảm;
    - và **kiểm tra novelty lần cuối** (việc đầu tiên của chat mới).

## 3. Quyết định đã chốt (không mở lại nếu không có bằng chứng mới)

1. Bỏ CCBF/HMM-temperature và CRSG (trơ hoặc bị đi trước). Hướng chính là SelfCal.
2. Luật được chọn:
    - SelfCal-AA = Mondrian strata theo σ_far (B = 10, ≥ 50 mẫu/stratum) + domain gate (p_maxsim ≤ 0.8) + max(p_comb,
     p_zgap).
    - SelfCal-Gap = p_zgap trong cùng strata và gate.
3. Báo cáo **cả hai** chế độ, khuyến nghị AA khi cần giả định yếu nhất.
4. SelfCal theo chuỗi (Seq) **không** đưa vào claim chính, vì validity theo cửa sổ thất bại trên Nordland. Chỉ là
   hướng mở.
5. Branch:
    - `claude/selfcal-aa`: ổn định, đã có Gap, **không ghi đè kết quả AA**.
    - `claude/selfcal-seq`: thí nghiệm mở rộng (Seq exp11, demo định vị exp12, cache thống kê, tìm biến thể).
    - `claude/elegant-brown-xvnecd`: lịch sử cũ.
    - Không tạo PR.
6. Toàn bộ tính toán nặng chạy trên Kaggle, 16 slot T4 (8 acc).

## 4. Mọi thứ nằm ở đâu

| Thứ | Vị trí |
|---|---|
| Descriptor dumps (4.4 GB, public) | Kaggle `nhatlong1103/vpr-descriptor-dumps` (cấu trúc: `ENVIRONMENT_SUMMARY.pdf`) |
| Ảnh gốc, trọng số, notebook tạo dump | `ENVIRONMENT_SUMMARY.pdf` §2; notebook nguồn `nb15_src/` (build bằng `automation/build_nb.py`) |
| Method | `analysis/selfcal.py` (`SelfCalTest`, `SelfCalAA`), `analysis/vprlib.py`, `analysis/sc_eval.py` |
| So sánh chính / các nghiên cứu phụ | `analysis/eval_all.py`; `exp3_fdr`, `exp5_ablation`, `exp6_dominance`, `exp7_mapsize`, `exp9_natural`, `exp10_shiftfix` |
| Kết quả | `analysis/results/*.json` (AA và baseline); `analysis/results/gap/*.json` (Gap) |
| Bảng / hình / paper | `paper/build_tables.py` → `paper/tables.md`; `analysis/figures2.py` → `analysis/figs/`; `paper/build_paper.py` |
| Kaggle ops | `automation/fanout.py`, `make_eval_kernel.py`, `run_kernel.py`; token `~/.kaggle/tok_<user>` |
| Nhật ký và novelty | `RESEARCH_LOG.md` (Entry 11–17), `LITERATURE_GATE.md` (Gate 1–4), `literature/VISUAL_LOCALIZATION_REVIEW.pdf` |
| Seq / demo định vị | branch `claude/selfcal-seq`: `analysis/exp11_sequence.py`, `exp12_deploy.py`, `results/seq_*`, `deploy_*` |

**Tái lập nhanh:**

```
python3 automation/fanout.py /tmp/w v3 "eval_all.py rc salad;..."
python3 paper/build_paper.py
```

Lệnh thứ nhất chạy thí nghiệm và tự gom kết quả. Lệnh thứ hai dựng lại bảng và PDF.

## 5. Việc tiếp theo (theo thứ tự)

1. **[Chat mới, làm đầu tiên] Đánh giá lại novelty của SelfCal-AA và SelfCal-Gap.** So với các paper, **chỉ đọc
   paper, không đọc repo code**. Hướng dẫn chi tiết và danh sách so sánh ở `00_READ_ME_FIRST.md` §3. Ghi kết quả vào
   `LITERATURE_GATE.md` (Gate 5) và báo user kết luận novel / trùng ở đâu.
2. **Kiểm định độc lập các lựa chọn sau-khi-xem-dữ-liệu** (gate 0.8, B = 10, chế độ Gap) trên dataset mới chưa dùng
   để chọn. Ứng viên: Pitts30k / SF-XL / Tokyo24-7 / 4Seasons (poses đã có `nhatlong1103/4seasons-poses`). Cần chạy
   notebook dump mới.
3. **Power trên MSLS:** null theo thành phố hoặc theo hướng nhìn, hoặc chọn biến strata tốt hơn. Dùng cache exp10
   (`--stats`) để thử rẻ.
4. **Sequence có bảo đảm:** cần thống kê bền với phụ thuộc theo thời gian (Seq hiện tại không hợp lệ trên Nordland).
5. **Chuẩn bị nộp:** chuyển sang template LaTeX của venue, thêm hình định tính (ví dụ ảnh bị chấp nhận hoặc từ chối
   do aliasing).
