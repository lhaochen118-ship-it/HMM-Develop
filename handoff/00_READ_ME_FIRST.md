# 00 — READ ME FIRST (khung chat mới)

Repo `lhaochen118-ship-it/hmm-develop`, **branch làm việc: `claude/selfcal-aa`** (ổn định; không ghi đè kết quả AA).
Branch thí nghiệm mở rộng: `claude/selfcal-seq`. Không tạo PR.

## 1. Thứ tự đọc (mỗi file một vai trò, không trùng lặp)

| # | File | Đọc để biết | Thời lượng |
|---|---|---|---|
| 1 | `handoff/03_HANDOFF_NEW_CHAT.pdf` | Mục tiêu, trạng thái, quyết định đã chốt, mọi thứ nằm ở đâu, việc tiếp theo | 5 phút, **bắt buộc** |
| 2 | `handoff/01_SCIENTIFIC_FINDINGS.pdf` | Đóng góp, lý thuyết, kết quả tích cực/tiêu cực, điều kiện kiểm chứng | 10 phút, **bắt buộc** |
| 3 | `handoff/02_ENGINEERING_OPS_NOTES.pdf` | Cách chạy trên Kaggle (16 T4), pipeline, lỗi đã gặp, bài học | khi cần chạy thí nghiệm |
| 4 | `handoff/ENVIRONMENT_SUMMARY.pdf` | Dataset dump public, cấu trúc thư mục, 8 tài khoản Kaggle | khi cần dữ liệu hoặc tài khoản |
| 5 | `handoff/04_RESEARCH_WORKFLOW.pdf` | Quy trình nghiên cứu và trạng thái từng phase | tham khảo |
| 6 | `LITERATURE_GATE.md` | Các lần kiểm tra novelty trước đó (Gate 1–4) | **bắt buộc cho việc §3** |
| 7 | `paper/selfcal_paper.md` (hoặc `paper/SelfCal_paper_full.pdf`) | Bản thảo paper đầy đủ | khi viết hoặc so sánh |
| — | `RESEARCH_LOG.md` | Nhật ký thí nghiệm chi tiết (Entry 11–17) | chỉ khi cần tra lại |

Chưa cần đọc code. Khi cần thì đọc `analysis/selfcal.py` (method) và `analysis/eval_all.py` (so sánh).

## 2. Môi trường tối thiểu

- Token Kaggle: `~/.kaggle/tok_<username>` cho 8 acc, `~/.kaggle/access_token` là acc 1. Nếu container mới thì tạo
  lại từ tin nhắn của user (danh sách username ở `ENVIRONMENT_SUMMARY.pdf` §3). Không ghi vào `~/.bashrc`.
- Cài đặt: `pip install kaggle markdown xhtml2pdf` (numpy, scipy, torch đã có).
- Mọi tính toán nặng chạy trên Kaggle qua `automation/fanout.py`.

## 3. VIỆC TIẾP THEO (thực hiện trong khung chat mới): đánh giá lại novelty của SelfCal-AA và SelfCal-Gap

**Mục tiêu:**

- Xác định SelfCal-AA và SelfCal-Gap (phiên bản cuối có Mondrian strata, domain gate và chế độ Gap) **có đủ novel
  không**, **trùng ý tưởng với paper nào**, và đóng góp nào cần đóng khung lại.
- **Chỉ đọc paper** (alphaXiv: `discover_papers`, `get_paper_content`, `answer_pdf_queries`). **Không đọc repo code**,
  để tiết kiệm token.

**Đầu vào cần nắm trước:**

- Định nghĩa method: `01_SCIENTIFIC_FINDINGS.pdf` §2.
- Các paper đã so ở Gate 1–4 (`LITERATURE_GATE.md`): RSF, Hussaini'26, Trinh & Lyons'25, Schubert'21, Scheirer'11,
  SAFEVPR'26, Quantile Transfer'26, Bates'23, Barber'23, TFA'26, MPF'19, SeqSLAM, PA ratio, Miller'25 RS/SD/SU,
  Radovanović'10, Jégou & Chum'12, Xu'21, Vysotska'25, Lu & Tanaka'26.
- Không cần đọc lại các paper này trừ khi cần kiểm tra một điểm cụ thể.

**Cần tìm và so sánh thêm (trọng tâm là các thành phần mới từ sau Gate 4):**

1. *Mondrian / conditional conformal theo một biến phụ (nuisance) của query* trong retrieval, VPR, re-ID và OOD
   detection. Ví dụ: conformal theo bin độ khó, "difficulty-aware" hoặc "normalized" conformal, class-conditional
   conformal cho open-set recognition.
2. *Kiểm định giao–hợp (intersection–union) hoặc nhiều điều kiện* để bền với domain shift trong conformal / OOD
   (ví dụ "valid under either assumption").
3. *Gap tới vùng xa đã chuẩn hoá* (z_gap) trong VPR và loop-closure verification: ratio test có loại vùng lân cận,
   "distinctiveness", spatially-aware margin, uniqueness score.
4. *Dùng chính database hoặc bản đồ làm tập hiệu chuẩn hay tập null* trong retrieval, kể cả các paper image
   retrieval, face/person re-ID, LiDAR place recognition (ví dụ leave-one-out gallery, self-retrieval calibration).
5. *Kiểm soát FAR không cần nhãn dưới distribution shift* cho localization hoặc loop closure, kể cả các paper
   2025–2026 sau Gate 4.
6. *Kiểm tra lại các paper "gần nhất" đã biết*: có version mới (2026) nào của SAFEVPR, TFA, Trinh & Lyons đã thêm thứ
   giống strata, gate hoặc map-null chưa.

**Cách làm:**

- Mỗi mảng làm 2–3 truy vấn alphaXiv.
- Đọc kỹ 8–15 paper gần nhất (full text hoặc truy vấn PDF có mục tiêu).
- Lập ma trận chồng lấn theo **từng thành phần**: map pseudo-queries, z_far/z_gap bất biến affine, centring,
  min-p tự hiệu chuẩn, aliasing guard, Mondrian strata, domain gate, chế độ Gap, T1–T6, giao thức đánh giá
  (LOBO, domain lạ, 4 dataset × 6 descriptor).

**Đầu ra:**

1. Ghi **Gate 5** vào `LITERATURE_GATE.md` gồm: ma trận chồng lấn; paper nào trùng một phần; chỗ nào novel thật;
   cách đóng khung lại claim nếu cần; đánh giá tiềm năng A/A\*.
2. Cập nhật mục *Related work* trong `paper/selfcal_paper.md` với các trích dẫn mới (chỉ phần related work và
   claim; không đổi kết quả).
3. Báo user bằng tiếng Việt: kết luận novel hay không, trùng ở đâu, và đề xuất bước tiếp theo.
4. Commit và push lên `claude/selfcal-aa`.
