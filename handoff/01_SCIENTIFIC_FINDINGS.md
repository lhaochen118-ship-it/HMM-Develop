# 01 — Scientific Findings (hướng HMM-navigation)

*Cập nhật 2026-11-02 (branch `hmm-navigation-5`, §N0000000 mới nhất). Tài liệu chỉ nói về **kết quả khoa học**: đóng góp, ý nghĩa, kết quả
tích cực và tiêu cực, kèm bằng chứng và điều kiện kiểm chứng. Vận hành ở `02`, trạng thái và việc tiếp theo ở `03`.
**Đọc §N trước** (trạng thái khoa học mới nhất, 2026-10-30/31); §0–§5 là nền tảng từ 2026-10-29, vẫn đúng, trừ chỗ §N
ghi đè. Nguồn số liệu: `RESEARCH_LOG.md` Entry 22–25, `paper/oc_tables.md`, `paper/BAO_CAO_PhanBien.pdf`,
`analysis/results/oc_*_entry25.tgz`.*

## 0. Đọc cho ý tưởng 2 (branch `hmm-2nd-idea`)

Các mục dưới đây là phát hiện của ý tưởng 1 và các hướng trước (SelfCal, CPC-HMM, CMS). Tóm tắt chuyển giao + số liệu cần đánh bại:
`07_IDEA1_SUMMARY.md`. Phát hiện của ý tưởng 2 ghi thành mục mới ở đầu file này.

## 00. Phát hiện mới nhất có ích cho thiết kế ý tưởng 2 (từ Entry 38–39 của ý tưởng 1)

- **Metric:** ngưỡng nhị phân off_d (40 m) phạt fix "gần đúng" (sai 40–50 m ở mép lỗ) như fix sai hẳn: 91–97 % báo sai ở mép là loại này; tính
  off-map từ off_d + 5 m thì phần dư biến mất. Ý tưởng 2 nên báo cáo thêm sai số liên tục (phân phối sai số fix, sai số điều hướng) và độ nhạy
  theo biên định nghĩa, để không tối ưu theo một tạo tác của metric.
- **Nguồn sai số điều hướng thật:** fix sai > 100 m, một nửa xảy ra khi robot vẫn trên bản đồ (sai nơi) — phép thử hình dạng chọn tay (SH) chặn được;
  bất kỳ giải pháp mới nào cũng phải kiểm loại lỗi "trên bản đồ nhưng sai nơi", không chỉ "ngoài bản đồ".
- **Hình dạng lỗ ảo (ống hay khối) gần như không đổi kết quả hiệu chuẩn** (Entry 38): đừng đầu tư vào hình học lỗ.
- **Hệ số 1/π:** khi hiệu chuẩn từ mô phỏng trên chính luồng, phần mô phỏng xuất phát từ trạng thái đã sai (π ≈ 0.55–0.70) làm cận lỏng ra a/π.
- **Bố cục lỗ mới (seed 10–12):** kết quả xác nhận ở `07_IDEA1_SUMMARY.md` §6 (bổ sung khi xong).

## N000000000. Vòng 12 (2026-11-03, Entry 38) — đọc trước §N00000000

- **Thử:** họ lỗ ảo hình khối (lưới ngẫu nhiên mỗi lần chạy ảo) + luật giao CST-JSU (Mệnh đề 20: hợp lệ nếu lỗ thật giống MỘT họ). Báo cáo
  `paper/BAO_CAO_E38.pdf`.
- **Kết quả (đăng ký trước):** H38a đạt (6/6 giữ ra mới seed 3–5, 7/7, Oxford); H38c đạt (recall trong 0.017 của SH); **H38b không đạt** (4/7, 4/6):
  lỗ khối gần như không đổi tỷ lệ báo ở mép ⇒ hình dạng lỗ không phải nguyên nhân chính; H38d không đạt (old town +12.8 m).
- **Phụ:** CST-JSU [both] (nhân quả) ≤ 0.07 mọi lớp vị trí trên 6/6 giữ ra mới (giá recall −0.02…−0.034) — ứng viên cần xác nhận trên bố cục lỗ mới.
- **Khuyến nghị không đổi:** SH ∧ CST-JS (thực dụng), CST-F (chứng nhận), N = 40.

## N00000000. Vòng 11 (2026-11-03, branch `hmm-navigation-5`, Entry 37) — đọc trước §N0000000

- **Đóng góp:** phẫu thuật tiến cả **bằng chứng hiện diện** (mọi thống kê của hệ thống tính lại trên bản đồ của từng lần chạy ảo) + null chính
  xác cho đầu chuỗi (khởi đầu ảo đủ chân trời, ngưỡng theo vị trí kể từ đầu chuỗi, κ′ cho cửa sổ ngắn) ⇒ luật **CST-JS**
  (`CMS-CPC/H+CSTJS+G+NGRr`), Mệnh đề 19 (`paper/cms_theory.md` §4g). Báo cáo `paper/BAO_CAO_E37.pdf`.
- **Tích cực (đăng ký trước):** H37a — segFAR TB ≤ 0.05 trên 7/7 + Oxford, **và trên tập giữ ra seed 6–9 (144 run) kể cả CMU (0.019;
  CST-J\* vòng 10: 0.053, run tệ nhất 0.237)**; H37c — recall trong 0.006 của SH trên 7/7 (cao hơn 6/7), +0.15 so với CST-F trên CMU;
  H37e — Oxford 0.738 vs SH 0.729 (giữ ra 0.711 vs 0.698); H37f — N = 40 tăng recall gộp 6/6 trên 5 descriptor mới; H37g — St Lucia 6
  descriptor hợp lệ, recall = SH, cao hơn SafeVPR'26 (ViT-L/14, có nhãn) ở 6/6 descriptor.
- **Tiêu cực:** H37b — kiểm toán theo vị trí 4/7: đoạn **mép** của lỗ thật Boreas 0.084, old town 0.109 (CST-J\*: 0.152 / 0.178), đầu chuỗi
  office 0.119 (84 đoạn) ⇒ CST-JS **chưa** là bảo đảm theo từng vị trí. Nguyên nhân: lỗ thật là khối bản đồ, lỗ ảo là phần Voronoi của
  đường tin ⇒ (S3-JF) sai ở mép. H37d chỉ đạt 5/7 (old town +14.5 m, Boreas +2.3 m so với SH).
- **Cơ chế đã kiểm (ablation):** CST-JSL (cùng cấu trúc, hiện diện = phẫu thuật đầy đủ vòng 10) vỡ trên giữ ra (CMU 0.051) ⇒ hiện diện tiến
  là thứ sửa tính hợp lệ; CST-JS0 (không chứng nhận cửa sổ ngắn) mất 0.13 recall CMU ⇒ null đầu chuỗi là thứ giữ recall.
- **H37h (độ bền tỷ lệ lỗ):** CST-JS hợp lệ 6/6 ở 10 % và 50 % lỗ, recall ≈ SH; CST-J\* vỡ ở 10 % (CMU 0.086); sai số điều hướng ở mép old town tăng theo tỷ lệ lỗ.
- **Khuyến nghị:** SH ∧ CST-JS (thực dụng: mọi lớp vị trí ≤ 0.07); CST-F (cận chứng nhận theo đoạn); N = 40.
- **Hạ tầng:** phép thử tuyến trên GPU trùng tuyệt đối numpy (L4), nhanh 1.3–1.8× dưới tải; 13 phiên L4 ~45 phút cho 300 run + 274 run N = 40.

## N0000000. Vòng 10 (2026-11-02, branch `hmm-navigation-5`, Entry 36) — đọc trước §N000000

**Báo cáo:** `paper/BAO_CAO_E36.pdf` (bảng `paper/e36_tables.md`); lý thuyết `paper/cms_theory.md` §4f (Mệnh đề 16–18); nhật ký Entry 36
(đăng ký trước, sửa đổi, sai lệch, kết quả); kết quả thô `analysis/results/e36/`.

1. **Mệnh đề 14 (CST) bị dữ liệu bác bỏ ở mọi độ sâu.** Kiểm toán trực tiếp (`analysis/cst_audit.py`): đoạn off-map thật qua CST 5–32 %
   (mục tiêu ≤ 5 %; Oxford 0.321, Nordland 0.302), không chỉ ở mép. Nguyên nhân: null track = chuỗi winner phản thực **từng frame** (không
   mạch lạc) và cửa sổ hình dạng bị cắt ở đầu chuỗi (43 % frame CMU). Chi phí điều hướng của CST đến từ fix sai **sâu** (Boreas NetVLAD:
   269/345 ở độ sâu ≥ 80 frame, sai 419 m). Mất recall Oxford (H35d) = CST chặt hơn SH, không phải lọt ở mép.
2. **Phẫu thuật TIẾN (CST-F, `analysis/cms_fwd.py`):** lối thoát ảo mỗi 1 excl; xoá vùng sau τ (Voronoi, ρ = off_d); chạy **chính chuỗi vị
   trí của hệ thống** (bản sao chính xác, khớp 99.95–100 %) tiến trên bản đồ đã cắt; khởi đầu ảo cho cửa sổ bị cắt; ngưỡng = min theo bin vị
   trí. Kết quả (104 run + Oxford 30 + St Lucia 5): tỷ lệ qua thật 0.004–0.047 trên 9/9 nhóm (kể cả mép), segFAR ≤ 0.004, không run nào > α,
   sai số điều hướng thấp nhất (Boreas 3.8 m vs SH 4.7, CST 16.3). **Giá:** recall −0.011…−0.161 (CMU, đầu chuỗi), Oxford 0.550 vs 0.729.
3. **CST-J (hiệu chuẩn cả quyết định trên mô phỏng tiến) và SH ∧ CST-J\* (thăm dò):** SH ∧ CST-J\* có recall = SH trên 7/7 và Oxford
   (0.729 = 0.729; SH ∧ CST 0.694) ⇒ **tiêu chí recall Oxford đạt**; xác nhận giữ ra 6/6. Nhưng CST-J/CST-J\* một mình vượt α trên CMU giữ
   ra (0.065–0.068): bảo đảm của CST-J chỉ xấp xỉ (bằng chứng hiện diện trong mô phỏng = phẫu thuật đầy đủ).
4. **N = 40 xác nhận (CosPlace, seed 1–9, 48 run):** hợp lệ 6/6, recall ≥ N = 20 trên 5/6 (countryside +0.069) ⇒ khuyến nghị N = 40.
5. **Vector hoá:** 3.9 ms/frame (1 lõi), trùng cache Kaggle ⇒ ngưỡng < 10 ms đạt. Null tiến 4–31 ms/frame.
6. **St Lucia (dataset mới, CosPlace) + SafeVPR'26 so sánh trực tiếp:** 30 % lỗ, 25 điều kiện giữ ra: SafeVPR'26 (nhãn) recall 0.462/0.557
   (α 0.05/0.10, FDR 0.008/0.020); của ta (không nhãn) 0.590–0.623, FDR ≤ 0.010. Không lỗ: mọi phương pháp bão hoà. Trên St Lucia null bản
   đồ cũ CPC-SC-T½ có recall cao hơn CMS (0.920 vs 0.820).
7. **Khuyến nghị:** CMS-CPC/H+CSTF+G+NGRr (N = 40) khi cần chứng nhận; SH ∧ CST-J\* khi ưu tiên recall. Novelty (mô phỏng tiến sự thất bại
   của chính hệ thống từ lối thoát ảo) chưa qua gate tài liệu (Gate 14 cần làm).

## N000000. Vòng 9 (2026-11-01 → 02, branch `hmm-navigation-5`, vòng lặp tự động 9 giờ) — đọc trước §N00000

**Báo cáo:** `paper/BAO_CAO_E32.pdf` (E32–E34 + Oxford); bản nháp bài báo `paper/cms_paper_draft.md`; hình
`paper/fig_validity_recall.png`; lý thuyết `paper/cms_theory.md` §4e (Mệnh đề 14, Hệ quả 15); nhật ký Entry 32–35.

1. **Độ bền (E32, 366 run × 14 biến thể + 42 run × 5 cách dựng null):** 12/14 hằng số và mọi cách dựng null (N, ρ) giữ hợp lệ 7/7 và
   ưu thế recall 7/7. Hằng số mong manh duy nhất: dung sai SH (× 2 vỡ α ở CMU, 4S countryside). N = 40 tăng recall 0.015–0.027 (seed 0).
   Thời gian ~20 ms/frame (thời gian thực 10 Hz trên 1 nhân; ngưỡng đặt trước < 10 ms / < 1 ms không đạt).
2. **NCLT, mỗi phiên làm bản đồ (9 bản đồ, off-map tự nhiên sát bản đồ):** hợp lệ trên mọi bản đồ, recall > CPC-SC-T½+SH 9/9.
3. **Đối thủ mới đọc toàn văn (E33):** SU'25, SUE'24, Carson'23 vi phạm α hoặc mất 40–70 % recall (H33a 7/7). SHcf (phân vị frame) không
   đủ (H33b không đạt).
4. **Oxford RobotCar (dataset uy tín mới, 60 run; dump `nhatlong1103/oxford-robotcar-vpr-dump`):** null bản đồ suy biến 36/60 run
   (bản đồ nhỏ, Hệ quả 9); CMS hợp lệ ở mọi run (0.719–0.753 recall, 0 % run vượt α). Khi null bản đồ còn chạy, ưu thế recall nhỏ
   (CPCW +0.008), sai số thấp hơn 19/24. Mọi baseline có nhãn vượt α.
5. **Novelty mới (E34): phẫu thuật cũng hiệu chuẩn lối THOÁT.** Lỗi còn lại là *duy trì* chuỗi báo sau khi rời bản đồ; quỹ đạo phản
   thực là null của "quỹ đạo ma" ⇒ phép thử hình dạng phản thực theo đoạn CST (Mệnh đề 14: báo sai theo đoạn sâu ≤ a_sh/π, giao biến
   cố). 366 run: hợp lệ 7/7, recall ≥ SH 6/7, a_sh × 2 vẫn hợp lệ. **Nhưng** sai số điều hướng tăng ở Boreas (+9 m) và old town
   (+13.6 m): fix sai ở mép chuyến off-map (ngoài mệnh đề) ⇒ CST một mình không thay SH.
6. **E35 (SH ∧ CST):** báo cáo chỉ khi **cả** SH **và** CST qua. CST mang bảo đảm (mọi báo cáo phải qua nó), SH chỉ bỏ báo cáo nên cận giữ với **mọi** dung sai SH. 228 run (seed 0–2): hợp lệ 7/7 với SH mặc định **và** SH × 2 (SH × 2 một mình vỡ α: countryside 0.100, CPCW office 0.066); ở SH mặc định recall trong 0.01 so với SH trên 6/7 (countryside −0.014), sai số trong 1 m trên 7/7 ⇒ **luật khuyến nghị mới: CMS-CPC/H+SH+CST+G+NGRr** (tính hợp lệ chỉ dựa vào phẫu thuật phản thực). Oxford (60 run): SH ∧ CST hợp lệ mọi run nhưng recall −0.029 so với SH (H35d không đạt) ⇒ "không mất gì" chỉ đúng trên 7 dataset chính. Xác nhận trên seed 3–9 giữ ra (252 run × 2): hợp lệ 6/6 với SH mặc định và SH × 2, recall trong 0.01 trên 5/6, sai số trong 1 m 6/6 (H35c đạt).
7. **Lỗi quy trình đã sửa:** cache thống kê phản thực local là bản xấp xỉ cũ ⇒ E34 lần đầu và các run thiết kế vô hiệu; đã chạy lại
   trên cache chính xác (tái lập Kaggle tới 4 chữ số). Cache local hiện tại: `$S/cmscache → cmsx` (= `nhatlong1103/hmm-cms-cache-exact`).

## N00000. Vòng 8 (2026-11-01, branch `hmm-navigation-5`) — đọc trước §N0000

**Báo cáo:** `paper/BAO_CAO_E30.pdf`; lý thuyết `paper/cms_theory.md` §4c–4d; nhật ký Entry 30–31; novelty Gate 14.

1. **Đề xuất giữ nguyên: CMS-CPC/H+SH+G+NGRr** (cổng mở khoá giới hạn tốc độ = code vòng 7). LODO 7/7 trên mọi luật không nhãn của
   vòng này. Bản "mở cả chuỗi" (+NGR, đăng ký trước) kém hơn ở Boreas (+2.0 đến +2.9 m) và CMU, chỉ hơn ở 4S countryside.
2. **Nhân quả:** `[both]` (giao luật hiệu chuẩn theo phiên và theo phiên khác) hơn CPC-SC-T½+SH recall 7/7 và sai số 7/7, hợp lệ 7/7 ở
   α = 0.05 và 0.01; `[online]` (phiên khác + phần đã qua) hợp lệ nhưng mất recall ở Nordland.
3. **Độ bền bộ lọc:** F1 (nhiễu ×4), F2 (+σ fix 10 m), F3 (khởi tạo không nhãn): đề xuất hơn luật cũ 7/7 recall và 7/7 sai số ở cả ba;
   cổng không có ích dưới F3 (giả định bộ lọc đã định vị).
4. **Off-map tự nhiên (phiên toàn off-map, π = 0):** mọi biến thể CMS hợp lệ ở α = 0.05 (0/36 run vượt), recall cảnh A 0.70–0.72 so với
   0.59 (6/6 cặp); bản chuyển đạo vượt α = 0.01 ở 1–2/36 run (đúng Mệnh đề 8), bản nhân quả không. Baseline có nhãn vượt α ở 11–28 % run.
5. **HMM liên hợp (Entry 31):** biên OFF của HMM = chuỗi hiện diện đã hiệu chuẩn (Mệnh đề 13, kiểm số học) ⇒ có thể trình bày phương
   pháp như một HMM có trạng thái off-map hiệu chuẩn; 114 run: recall trong ±0.01 so với chuỗi vị trí gốc ở 6/7 (Nordland −0.02 đến
   −0.03 do emission dựng lại từ top-100), ghép nối không giảm sai số nhất quán so với cùng chuỗi không OFF (3/7) ⇒ trình bày phương
   pháp như một HMM có trạng thái off-map hiệu chuẩn, cài đặt khuyến nghị vẫn là bản phân rã /H.

## N0000. Vòng 7 (2026-11-01, branch `hmm-navigation-5`) — đọc trước §N000

**Báo cáo:** `paper/BAO_CAO_E29.pdf`; kiểm toán `paper/AUDIT_E29.md`; lý thuyết `paper/cms_theory.md` §4b; nhật ký Entry 29.

1. **Phương pháp đề xuất cuối: CMS-CPC/H+SH+G+NGR** (LODO chọn 7/7 fold ở α = 0.05 và bản α = 0.01 của nó 7/7 ở α = 0.01). Thành phần
   mới: **cổng innovation phản thực +NGR** (`analysis/navrisk.py`): bán kính τ = phân vị 0.05 của độ dời của winner phản thực, mở khoá
   khi H báo cáo liên tiếp có innovation đồng nhất; chỉ bỏ báo cáo. Bản bảo đảm chặt: **CMS-CPCW/H+SH+NGR** (Định lý 6′).
2. **Kết quả (366 run, null chính xác):** so với CPC-SC-T½+SH, luật đề xuất có recall cao hơn 7/7 và sai số thấp hơn 7/7 (CI bootstrap
   cụm: 6/7 và 6/7 có ý nghĩa, không dataset nào kém hơn), segFAR ≤ 0.009; ví dụ countryside 0.491 / 34.3 m so với 0.334 / 51.3 m.
   Cổng giảm sai số của CMS 6/7 (Boreas −5.8 m, Nordland −7.3 m) với mất recall ≤ 0.011. Ablation: không mở khoá / cổng dead-reckoning
   cổ điển khoá chết trên VIO và NCLT. Lỗ 10/50 %: recall cao hơn 6/6.
3. **Kiểm toán:** không rò nhãn; định lý cũ kiểm lại đúng; sửa (i) ngưỡng khởi phát của chuỗi đầy đủ bộ nhớ (→ CMS-CPCW, Định lý 6′),
   (ii) null phản thực cắt cụt (→ `cms_exact.py`; kết quả chênh ≤ 0.005); bổ sung CI bootstrap cụm (`paired_stats.py`).

## N000. Vòng 6 (2026-11-01, branch `hmm-navigation-5`) — đọc trước §N00

**Báo cáo:** `paper/BAO_CAO_E28.pdf`; lý thuyết `paper/cms_theory.md`; nhật ký `RESEARCH_LOG.md` Entry 28; novelty Gate 12.
Dataset mới: `nhatlong1103/hmm-cms-cache` (ρ = off_d), `hmm-cms-cache-r1`, `hmm-e28-results`.

1. **Phương pháp mới — CMS (Counterfactual Map Surgery).** Null hiệu chuẩn sinh từ **chính luồng query**: mỗi frame tính lại
   bằng chứng (chi phí tuyến TAO'26 + độ khác biệt không gian, từ top-100) trên bản đồ đã cắt hành lang bán kính ρ = off_d quanh
   niềm tin của hệ thống (anchor của giả thuyết tuyến thắng, 20 frame). Ngưỡng = phân vị conformal của luồng phản thực theo đoạn
   H frame, Mondrian theo điều kiện. Luật chính CMS-CPC/H+SH (chuỗi hiện diện với e-value hạng phản thực, vị trí = MAP của HMM,
   dừng hình dạng SH); biến thể +G (cổng đồng thuận TAO–MAP), CMS-T (phép thử tuyến trần), CMS-W (chuỗi bộ nhớ hữu hạn), [loco]
   (nhân quả: chỉ phiên khác).
2. **Lý thuyết:** Định lý 6 (tự-nhiễm: khởi phát sai ≤ α(n+1)/(πn+1)), Mệnh đề 8 (hướng nhiễm: niềm tin sai bảo thủ, frame
   off-map trả 1/π), Hệ quả 9 (α = 0.01 và PAC khả thi). Kiểm chứng: thực tế/α = 0.48–1.14, ≤ cận 7/7.
3. **Kết quả (366 run):** ở α = 0.01 CMS-CPC/H+SH so với CPC-SC-T½+SH (α = 0.05): recall cao hơn 6/7, sai số thấp hơn 5/7, segFAR
   trung bình ≤ 0.01 trên 7/7; LODO chọn CMS-CPC/H+SH+G(α = 0.01) ở 7/7 fold. Đường cong: hơn luật cũ 5/7, Claxton'24/TAO'26
   (nhãn) 6/7, SafeVPR'26 5/5 (CMU còn thua 0.013). Cùng điểm số TAO: null phản thực recall 0.28–0.82 so với null bản đồ 0.05–0.66.
   Lỗ 10 %/50 %: recall cao hơn CPC-SC+CS 6/6.
4. **Âm / mở:** ở α = 0.05 sai số điều hướng kém hơn 4/7 (dùng hết ngân sách; LODO α = 0.05 vẫn chọn luật cũ); CMU sát/ vượt α
   (α = 0.01: 0.0097; lỗ 50 %: 0.029–0.053); S1 chỉ đúng trung bình theo bố cục lỗ (tỷ lệ thực tế của CMS-T theo run tới 0.34 trên
   CMU); ρ đăng ký trước (off_d + excl) sai chiều (đã sửa trước đánh giá, ghi nhật ký); CMS-CPC không dừng vi phạm. Mức: cơ chế
   mới (Gate 12: chưa thấy tiền lệ), bằng chứng mạnh hơn rõ; **không tuyên bố A\***.

## N00. Vòng 5 (2026-10-31, branch `hmm-navigation-4`) — đọc trước §N0

**Báo cáo:** `paper/BAO_CAO_E27.pdf`; nhật ký `RESEARCH_LOG.md` Entry 27. Dataset public mới: `nhatlong1103/hmm-xnull`,
`hmm-route-cache`, `hmm-image-baselines`.

1. **Null khớp điều kiện (17 traversal Boreas chưa dùng):** 300–360 chunk/seed (null bản đồ ~10); recall +0.007…+0.008 ở mọi
   luật, segFAR như cũ. Sự dè dặt của điểm mặc định chủ yếu là **cấu trúc** (κ chỉ cho chuỗi hiện diện; bước dừng loại tiếp),
   không phải do null cùng điều kiện.
2. **Công suất tuyến w₃ = ½ (CPC-SC-T½):** đường cong ≥ vòng 4 trên 7/7, pAUC > CPC-SC+CS 7/7; CPC-SC-T½+CS tăng recall mặc
   định 7/7 với run tệ nhất ≤ 0.046. Biến thể chỉ-tuyến / min (thăm dò) không tổng quát → loại. CMU vẫn thua Claxton'24/TAO'26.
3. **SafeVPR'26 và VPR-auditing'26 ngoài Boreas (NCLT, 4Seasons):** CPC-SC-T½+SH cao hơn SafeVPR tại FL ≤ 0.01 trên 4/5;
   VLM 7B nhận 8–18 % frame off-map, sai số 23–102 m.

## N0. Vòng 4 (2026-10-31, branch `hmm-navigation-4`) — đọc trước §N

**Báo cáo:** `paper/BAO_CAO_E26.pdf`; nhật ký `RESEARCH_LOG.md` Entry 26; lý thuyết `paper/cpc_theory.md` §3e–§3f; novelty
`LITERATURE_GATE.md` Gate 11; baseline 2026 `literature/BASELINES_2026.md`.

1. **Chẩn đoán phụ thuộc:** p-value top-1 của frame off-map hợp lệ biên ở phần trong đoạn off-map; vi phạm ở ~50 frame quanh
   mép bản đồ (nhìn chồng lấn) và ở R neo odometry của đoạn dài; null bản đồ chỉ có 8–10 chunk ngắn (~10 đơn vị hoán đổi).
2. **Lý thuyết:** Mệnh đề 5 (không giả định phụ thuộc thì không tích luỹ được bằng chứng); Định lý 4 (GPC: chứng chỉ đúng
   với mọi phụ thuộc, nhưng recall chỉ 10–40 % của CPC-SC+CS); Định lý 5 (khởi phát cửa sổ hữu hạn + dừng/reset hình học:
   tỷ lệ khởi phát sai mỗi đoạn ≤ α với mọi phụ thuộc giữa các đoạn; kiểm chứng: trung bình 0.001–0.006, run tệ nhất của
   CPC-SC-T+SH ≤ 0.039).
3. **Phương pháp mới (không nhãn):** bằng chứng kiểm định tuyến (chi phí TAO'26 trên 100 giả thuyết, 20 frame) **hiệu chuẩn
   bằng null bản đồ** làm thành phần thứ ba của chuỗi hiện diện (CPC-SC-T), cộng dừng hình dạng SH (Procrustes). CPC-SC-T+CS:
   cải thiện Pareto so với CPC-SC+CS (recall 7/7, sai số ≤ 7/7). CPC-SC-T+SH: recall +0.009…+0.053 trên 7/7, hơn Xu'21 về
   recall 5/7; ở FL ≤ 1 % hơn Xu'21 7/7, Claxton'24 và TAO'26 6/7 (trừ CMU).
4. **Baseline 2026 trên cùng giao thức:** TAO'26 xếp hạng mạnh trên CMU nhưng ngưỡng 3σ vi phạm (segFAR 0.24–0.74); TRAIL'26
   ≈ top-1 MegaLoc, ngưỡng có nhãn vi phạm (0.15–0.29); VPR-auditing'26 (Qwen2.5-VL-7B) nhận 30–36 % frame off-map, sai số
   150 m. Với riêng MegaLoc, Claxton'24/TAO'26 xếp hạng tốt hơn trên 4/7.
5. **Âm / mở:** điểm mặc định còn dè dặt vì null **cùng điều kiện ảnh** (hiệu chuẩn chung, bỏ sàn κ: +0.003…+0.011); LODO không
   phân biệt các biến thể theo sai số; CMU với descriptor mạnh vẫn thua về xếp hạng. Mức: A vững hơn, A\* chưa.

## N. Trạng thái mới nhất (2026-10-30 → 2026-10-31)

### N.1 Phương pháp chính hiện tại: CPC-SC+CS (thay CPC-HMM +TCEmin)

`analysis/cpc_sc.py` (cũng là luật `CPC-SC+CS (ours)` trong `nav_rules.py`). Ba thành phần, mọi hằng số theo đơn vị bài
toán (excl, H, α), một cấu hình cho mọi dataset:

1. **Chuỗi hiện diện CPC-HMM** (không TCE): LR_t = ½(ẽ^top_t + (e^R_t)^{1/H}), e = a·p^{a−1} (a: Beta-EM theo traversal),
   ẽ^top có cổng top-1 = MAP; p_in = p_out = 0.01.
2. **SC — ngưỡng khởi phát hiệu chuẩn theo đoạn:** κ = phân vị conformal (1−α) của max log-odds trên các đoạn H frame
   của null tự-phát-lại của bản đồ (chuỗi khởi đầu ở odds 1). Báo từ khi ℓ_t > κ, duy trì khi ℓ_t > 0.
   *Định lý (khởi phát):* dưới exchangeability của đoạn off-map với đoạn null, P(khởi phát báo trong đoạn | chưa báo khi
   vào đoạn) ≤ α, mọi phụ thuộc trong đoạn. Thực nghiệm Boreas: tỷ lệ đoạn có khởi phát sai 0.010–0.041.
3. **CS — quy tắc dừng nhất quán odometry:** dừng nếu ∃k, quãng odometry ≤ 3·excl, | ‖m_t − m_{t−k}‖ − ‖o_t − o_{t−k}‖ | >
   excl. *Bổ đề 7:* chỉ bỏ bớt báo cáo nên segFAR/FL không tăng (không áp cho ARL₀ đếm khởi phát). *Mệnh đề 4:* nếu MAP
   kẹt trong bán kính δ quanh nơi rời bản đồ và excl + in_d + ε + δ < off_d thì không có báo cáo ở frame off-map.

Lý thuyết đầy đủ: `paper/cpc_theory.md` §3c (TCE) và §3d (đường cong, CS, CPC-SC).

### N.2 Chẩn đoán dẫn tới phương pháp (Entry 25, `analysis/recall_diag.py`)

- Recall mất ở **chuỗi hiện diện**, không ở chuỗi vị trí: Boreas NetVLAD chuỗi vị trí đúng 85 % frame on-map, chỉ báo
  30 %; Boreas DINOv2 83 % frame on-map nằm trong đoạn không bao giờ được báo dù chuỗi vị trí đúng 86 % ở đó.
- **Phép min TCE** là nguyên nhân chính (NCLT DINOv2 recall 0.16 TCEmin vs 0.50 CPC-HMM).
- **So với CPC-HMM, TCEmin là điểm vận hành thận trọng hơn trên đường cong kém hơn** (NCLT NetVLAD, cùng recall: sai số
  12.9 vs 6.3 m) → phản biện "chỉ thận trọng hơn" đúng với phương pháp cũ.
- Vi phạm segFAR của CPC-HMM không TCE đến từ **báo cáo kéo dài** (chuỗi vị trí không có trạng thái off-map: MAP kẹt ở
  mép hoặc nhảy sang nơi giống), không phải từ khởi phát.
- **Tính nhất quán odometry trên quãng dịch chuyển là bằng chứng hiện diện mạnh:** ở 4S countryside, mọi luật "+CS" đạt
  recall tốt nhất tại FL ≤ 0.01 khi ngưỡng P(on) chỉ ≈ 0.02 (CS gần như tự loại hết báo sai). Ngược lại phép thử một bước
  (PCR, cổng dự đoán kiểu IPDA) **tự xác nhận**: dưới H0 nơi dự đoán cũng là ô top-1 ở 62 % frame (CMU CosPlace).

### N.3 Kết quả (7 dataset, 6 descriptor; bản đồ khuyết 30 %; NCLT off-map tự nhiên)

**Điểm mặc định, 10 seed (366 run)** — recall / segFAR / sai số (m):

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.68 / 0.043 / 25.3 | 0.53 / 0.021 / 13.7 | 0.69 / 0.227 / 18.1 | 0.74 / 0.038 / 59.3 | 0.72 / 0.215 / 21.2 | 0.62 / 0.101 / 70.9 | 0.25 / 0.088 / 81.0 |
| Claxton'24 (nhãn) | 0.74 / 0.116 / 36.9 | 0.66 / 0.203 / 32.3 | 0.87 / 0.166 / 14.3 | 0.52 / 0.263 / 88.0 | 0.80 / 0.152 / 18.7 | 0.72 / 0.166 / 90.4 | 0.60 / 0.213 / 42.9 |
| TCEmin (cũ) | 0.66 / 0.008 / 6.4 | 0.49 / 0.000 / 3.7 | 0.75 / 0.018 / 3.9 | 0.57 / 0.002 / 13.0 | 0.70 / 0.013 / 12.5 | 0.59 / 0.008 / 33.7 | 0.21 / 0.010 / 59.1 |
| **CPC-SC+CS** | 0.66 / 0.001 / 5.1 | 0.54 / 0.000 / 4.6 | 0.73 / 0.002 / 3.8 | 0.64 / 0.000 / 9.6 | 0.71 / 0.000 / 11.6 | 0.60 / 0.000 / 30.8 | 0.30 / 0.000 / 53.1 |
| Oracle | 0.88 / – / 2.1 | 0.72 / – / 2.2 | 0.94 / – / 3.0 | 0.67 / – / 4.8 | 0.91 / – / 8.3 | 0.84 / – / 19.4 | 0.73 / – / 16.5 |

**Recall ở cùng FL ≤ 0.01 (đường cong vận hành, 3 seed):**

| Luật | Boreas | NCLT | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|---|---|
| Xu'21 (nhãn) | 0.562 | 0.526 | 0.592 | 0.624 | 0.537 | 0.555 | 0.181 |
| Claxton'24 (nhãn) | 0.687 | 0.574 | **0.793** | 0.439 | 0.749 | 0.644 | 0.420 |
| SafeVPR (nhãn) | 0.486 | – | – | – | – | – | – |
| TCEmin (cũ) | 0.692 | **0.590** | 0.713 | 0.619 | 0.733 | 0.616 | 0.245 |
| **CPC-SC+CS** | **0.766** | 0.586 | 0.705 | **0.780** | **0.771** | **0.664** | **0.545** |

- Ở cùng FL ≤ 1 %: hơn Xu'21 7/7, hơn Claxton'24 6/7 (trừ CMU). Đặt tại đúng FL của Xu'21 (Kalman chạy thật,
  `oc_matched.py`): recall cao hơn 5/7, sai số thấp hơn 6/7.
- segFAR tệ nhất trong từng run: 0.021 (mọi 366 run < α = 0.05); TCEmin tới 0.171, Xu'21 tới 1.0.
- So với TCEmin: recall cao hơn 5/7 (CMU −0.02), segFAR ≤ 7/7, sai số thấp hơn 6/7 (NCLT +0.9 m).
- **Độ bền tỷ lệ lỗ bản đồ** (cùng hằng số): 10 % và 50 % → segFAR ≤ 0.012 mọi nơi; sai số thấp hơn Xu'21 ở mọi dataset
  (10 %: 1.2–4.5×, 50 %: 2.4–8.9×).
- **Chọn leave-one-dataset-out** (15 biến thể không nhãn): CPC-SC+CS ở 6/7 fold, regret 0–3.5 m (TCEmin trước đây: tới
  30 m). Giao thức **đăng ký trước**: Boreas/NCLT phát triển, 5 tập còn lại giữ lại.
- Độ nhạy: span CS 2/4·excl đổi recall ±0.02–0.04, segFAR ≤ 0.014; ngưỡng 0.75/1.25·excl ảnh hưởng nhỏ; α = 0.1 như 0.05.

### N.4 Kết quả âm và hạn chế mới (đã xác minh)

1. **CMU (descriptor mạnh, dữ liệu dễ):** Claxton'24 (nhãn) và cả max-sim thô xếp hạng tốt hơn mọi chuỗi hiện diện.
2. **Vùng FL cao (3–8 %):** Claxton'24 recall cao hơn trên 5/7 (segFAR của nó 0.11–0.27).
3. **Điểm mặc định còn dè dặt so với chính đường cong** (countryside recall 0.30 ở FL 0 vs 0.55 ở FL 0.01). Hiệu chuẩn
   chung (hiện diện ∧ CS) trên null không nới được: null tự-phát-lại qua CS nhiều gấp 2.6× off-map thật (0.229 vs 0.088).
4. **Recall mặc định thấp hơn Xu'21 trên 4/7** (Nordland −0.10, còn lại ≤ 0.02).
5. **α = 0.01 không khả thi** khi null có < 99 đoạn (CMU, 4S office: κ = ∞, recall 0).
6. **Bảo đảm dưới phụ thuộc thời gian vẫn chưa có:** W-CPC (bộ nhớ hữu hạn + hiệu chuẩn theo đoạn) vi phạm trên Boreas
   (segFAR 0.030, tệ nhất 0.099) như certified; nguyên nhân: null tự-phát-lại của bản đồ (block ngắn, cùng điều kiện ảnh)
   biểu diễn thiếu phụ thuộc của đoạn off-map dài.
7. Đã thử và loại: e-value hai nhóm (hedge, +0.006 recall), trung bình e-process, TCE trên một thành phần, hysteresis
   TCEmin→CPC, CPC-SC không CS, PCR (kèm lỗi thang đo khi che block của null), cổng độ tin chuỗi vị trí (conf quá tự tin),
   hiệu chuẩn chung CS.
8. NCLT: CS xoá frame đúng; CPC-HMM không CS có đường cong tốt nhất; sai số nhạy với vài fix sai (EKF có hướng).

### N.5 Kết quả 2026-10-30 (Entry 22–24, tóm tắt)

- **TCE / TCEmin** (e-value hiệu chuẩn theo chuyển tiếp, min với e-value biên): segFAR ≤ 0.025 trên 7/7, nhưng recall
  thấp (§N.2).
- **NCLT** (8 phiên, off-map tự nhiên) được thêm như tập giữ lại; mọi luật không nhãn thắng baseline có nhãn về segFAR.
- **Cổng dead-reckoning +GG** tốt trên Boreas nhưng khoá chết trên 4S old town/countryside và NCLT → chỉ là module tuỳ chọn.

### N.6 Novelty (Gate 9–10, `LITERATURE_GATE.md`)

- CS: cơ chế đã biết (RRR, PCM/Olson, SeqSLAM, Claxton'24) — vai trò và chẩn đoán là mới. SC: cùng lập luận exchangeability
  như certified (conformal theo quỹ đạo/block). Đánh giá theo đường cong: giao thức, không phải phương pháp.
- **Mức hiện tại: A (RA-L/ICRA/IROS) khả thi; A\* chưa.** Thiếu: bảo đảm dưới phụ thuộc; so sánh TRAIL'26 / TAO'26 /
  VPR-auditing'26; chạy robot thật vòng kín.

## 0. Bài toán

**Bối cảnh.** Robot dùng camera đơn chạy theo chuỗi frame có odometry, trên một bản đồ ảnh **có lỗ**: có đoạn đường
không có trong bản đồ (off-map). Mỗi frame có similarity tới N ảnh bản đồ (global descriptor).

**Câu hỏi.** Khi nào được tin một "fix" vị trí, để đưa vào bộ lọc điều hướng, sao cho:

1. tỷ lệ fix sai được kiểm soát, **không cần nhãn** của điều kiện mới (đêm, tuyết, mùa);
2. mạnh hơn kiểm định từng frame;
3. đúng cả khi các frame phụ thuộc nhau mạnh.

**Đánh giá.**

- Trong suốt dự án, 30 % block của bản đồ bị bỏ để tạo off-map (thêm 10 % và 50 % cho độ bền).
- Dữ liệu: 7 dataset (RobotCar-Seasons, Extended-CMU, Nordland, 4Seasons ×3 cảnh, Boreas), 6 descriptor (MegaLoc,
  SALAD, MixVPR, CosPlace, NetVLAD, DINOv2), 2–3 seed.
- Odometry thật trên 4Seasons (VIO) và Boreas (bánh xe + gyro); mô phỏng ở các tập còn lại.

## 1. Đóng góp A — Certified sequential localization (hướng chính)

**Phương pháp** (`analysis/cert_seq.py`).

1. p-value SelfCal-AA từng frame, hiệu chuẩn bằng chính bản đồ (leave-block-out, thống kê bất biến affine), cross-fit.
2. Bằng chứng chuỗi neo odometry:

   > R_t = ℓ_t + Σ_{j<H} ℓ_{t−j} · 1[‖(x_t − x_{t−j}) − (o_t − o_{t−j})‖ ≤ ρ_o],  ℓ = −log p

   ANCHR tự fit góc lệch odometry→bản đồ trong mỗi cửa sổ.
3. Hiệu chuẩn theo **đoạn**: ngưỡng là phân vị conformal của max R trên các đoạn H frame của traversal bản đồ bị giữ lại.

**Định lý.** Giả sử các đoạn off-map hoán đổi được (exchangeable) với các đoạn bản đồ giữ lại. Khi đó:

> P(có ít nhất một fix sai trong một đoạn off-map dài H) ≤ α

với mọi kiểu phụ thuộc bên trong đoạn. Đây là lý do cách hiệu chuẩn theo cửa sổ trước đó (exp11/seq_odo) thất bại,
còn cách này đúng.

**Bằng chứng** (α = 0.05; H = 10, RobotCar H = 5; `paper/cert_tables.md`):

| Dataset | FAR theo đoạn, ANCH (tệ nhất) | Baseline hiệu chuẩn bằng nhãn (tệ nhất) | Power ANCH / per-frame / dùng nhãn |
|---|---|---|---|
| RobotCar-S. | 0.016 (0.067) | 0.044 (**0.125**) | 0.68 / 0.77 / 0.77 |
| CMU-S. | 0.022 (0.052) | 0.044 (**0.089**) | 0.82 / 0.62 / 0.87 |
| Nordland | 0.020 (0.033) | 0.016 | 0.86 / 0.44 / 0.87 |
| 4S office | 0.020 (0.049) | 0.022 | 0.83 / 0.31 / 0.85 |
| 4S old town | 0.014 (0.022) | 0.010 | 0.77 / 0.43 / 0.86 |
| 4S countryside | 0.015 (0.025) | 0.025 | 0.37 / 0.19 / 0.49 |
| Boreas | 0.006 (0.017) | 0.026 (**0.062**) | 0.71 / 0.35 / 0.79 |

- **Off-map tự nhiên** (query của cảnh hoặc dataset khác, `cert_natural.py`): FAR ≤ 0.016.
- **α = 0.01 và 0.1** đều bám mục tiêu.
- **Độ trễ tới fix đầu tiên** giảm 5–20×.

**Ý nghĩa.** Đây là bảo đảm không cần nhãn đầu tiên ở mức đoạn (excursion) cho định vị theo chuỗi. Baseline dùng nhãn
của điều kiện dễ (kiểu SAFEVPR, Quantile Transfer) vượt α ở 3/7 dataset.

**Hạn chế.**

- Power luôn thấp hơn baseline dùng nhãn. Đó là cái giá của tính hợp lệ.
- RobotCar có snippet 9 frame, quá ngắn để tích luỹ bằng chứng (0.68 so với 0.77 của per-frame).
- Bản đồ nhỏ (CMU, khoảng 70 đoạn null) khiến FAR của từng bản đồ dao động.
- Giả định exchangeability chỉ được kiểm bằng thực nghiệm.

## 2. Đóng góp B — Chẩn đoán vì sao HMM thua baseline

**Thiết lập** (`analysis/hmm_diag.py`, 36 cấu hình): HMM chuẩn (lọc tiến, chuyển trạng thái theo odometry, emission
exp(s/T)), có hoặc không có trạng thái off-map của Xu et al. RA-L'21.

| Mã | Phát hiện | Số liệu |
|---|---|---|
| D5 | Posterior **bất biến chính xác** khi cộng một hằng số vào mọi similarity của từng frame | thay đổi ≤ 4·10⁻⁶ |
| D1 | Độ tin cậy của HMM tách on/off kém hơn max-sim thô | R@FL5 0.44 so với 0.55 (CMU 0.43 so với 0.74) |
| D2 | Quá tự tin | conf 0.91 so với acc 0.77, ECE 0.14 |
| D3 | Khoá nhầm chỗ | 16 % frame sai mà vẫn tin > 0.9, gây 41 % tổng sai số |
| D4 | Bằng chứng phụ thuộc | tự tương quan trễ 1 là 0.8–0.99, tức phóng đại (1+r)/(1−r) = 8–136× |

**Nguyên nhân gốc:**

1. **Mù với sự vắng mặt.** Softmax chỉ mang bằng chứng tương đối. Câu hỏi "có trong bản đồ không" lại cần
   LR(j : ∅) = f₁(s_j)/f₀(s_j), tức mức tuyệt đối. Vì vậy (T, k) của Xu'21 tune bằng nhãn trên điều kiện dễ cho FL 0.97
   trên CMU.
2. **Đếm thừa bằng chứng phụ thuộc** (likelihood hợp thành), gây quá tự tin và khoá nhầm.
3. **Vòng khoá nhầm:** bằng chứng tính từ niềm tin của HMM tự xác nhận khi đã khoá nhầm.
4. **Bội số:** p-value của thống kê max đã trả giá cho N nơi, nên không nhân vào từng trạng thái được.

## 3. Đóng góp C — CPC-HMM (module sửa HMM)

**Mô hình** (`analysis/hmm_fix.py`, `fac_anchT_mix`; luật điều hướng trong `nav_demo.py`; lý thuyết trong
`paper/cpc_theory.md`).

- **Chuỗi vị trí:** HMM không có trạng thái off-map, với emission (s − s_max)/(τ·σ_far,t). τ là thang Gumbel của null
  bản đồ, nên không phải tune.
- **Chuỗi hiện diện on/off:**

  > P(on_t) ∝ [(1−p_out)·P(on_{t−1}) + p_in·P(off_{t−1})] · LR_t,  LR_t = ½(ẽ^top_t + (e^R_t)^(1/H))

  - e = a·p^(a−1), với a fit bằng EM theo từng traversal (không nhãn).
  - Cổng: top-1 phải khớp MAP của chuỗi vị trí.
  - e^R là e-value của R_t, hiệu chuẩn trên traversal của bản đồ.
- **Quyết định:** báo nơi MAP khi P(on) > ½.

**Lý thuyết** (`paper/cpc_theory.md`):

- **Bổ đề 1:** e-value có thể dự đoán.
- **Bổ đề 2:** cổng, luỹ thừa và trung bình đều giữ tính e-value.
- **Định lý 1:** odds bị chặn bởi thống kê Shiryaev–Roberts, nên **ARL₀ ≥ (1−p_in)/p_in − R₀**, với điều kiện
  p_out ≥ p_in.
- **Định lý 2:** độ trễ vào lại ≈ log((1−p)/p)/KL₁.

**Kiểm chứng ARL₀** (số frame off-map trên mỗi lần bắt đầu báo sai, trung vị; cận lý thuyết 98):

| | CMU | Nordland | 4S office | 4S old town | 4S countryside |
|---|---|---|---|---|---|
| **CPC-HMM** | 995 | 3930 | 2840 | 762 | 895 |
| Xu'21 (nhãn) | **41** | 720 | 651 | 665 | 1424 |
| CPC, p_in = 0.05 (cận 18) | 337 | 1965 | 1893 | 318 | 832 |

**Kết quả CPC-HMM so với Xu'21** (bản đồ khuyết 30 %; ô ghi recall / FL / sai số điều hướng trung bình):

| Dataset | CPC-HMM (không nhãn) | Xu'21 (T, k tune bằng nhãn) | Kết luận |
|---|---|---|---|
| CMU | 0.77 / 0.034 / 6.8 m | 0.71 / 0.363 / 46.0 m | **thắng** |
| Nordland | 0.71 / 0.008 / 20.1 fr | 0.74 / 0.013 / 54.7 fr | **thắng** |
| 4S office | 0.78 / 0.004 / 10.9 m | 0.77 / 0.041 / 17.7 m | **thắng** |
| 4S old town | 0.64 / 0.040 / 45.6 m | 0.60 / 0.091 / 100.9 m | **thắng** |
| 4S countryside | 0.37 / 0.068 / 56.0 m | 0.28 / 0.029 / 94.4 m | thắng điều hướng, FL cao hơn |
| RobotCar | 0.68 / 0.060 / 2.1 m | 0.58 / 0.045 / 1.3 m | **thua** (snippet 9 frame) |
| Boreas (odometry đã sửa) | sai số điều hướng 21.0 m (4 desc.) | 6.2 m | **thua khoảng 3×** |

**Điều hướng khép kín** (`nav_demo.py`, 3 seed, sai số trung bình):

| | CMU | Nordland | 4S office | 4S old town | 4S countryside | Boreas* |
|---|---|---|---|---|---|---|
| CPC-HMM | 5.7 | 17.9 | 12.8 | 36.0 | 54.0 | 21.0 |
| Certified | 3.8 | 17.0 | 11.3 | 37.0 | 52.8 | 19.4 |
| Xu'21 (nhãn) | 14.2 | 70.7 | 22.7 | 62.4 | 76.8 | **6.2** |
| Per-frame SelfCal | 5.3 | 36.3 | 11.6 | 45.2 | 65.7 | 16.2 |

\*Boreas: MegaLoc, SALAD, MixVPR và CosPlace sau khi sửa odometry. NetVLAD và DINOv2 đang chạy.

**Độ bền theo tỷ lệ lỗ bản đồ** (sai số điều hướng của `hmm_fix`, CPC so với Xu'21):

- **Khuyết 50 %:** CPC thắng ở mọi dataset trừ RobotCar.
  - CMU 28.0 so với 55.0; Nordland 23.8 so với 169; 4S office 26.3 so với 79.1.
  - **Boreas 13.7 so với 40.8**.
- **Khuyết 10 %:** CPC thắng trên CMU, Nordland, 4S office và countryside, nhưng thua trên 4S old town (44.0 so với
  30.1).

**Đóng góp mới so với tài liệu** (Gate 7 trong `LITERATURE_GATE.md`):

- **Mới:**
  - chẩn đoán bất biến dịch chuyển;
  - chuỗi tồn tại kiểu IPDA được nuôi bằng e-value hiệu chuẩn bằng bản đồ;
  - cổng độc lập niềm tin;
  - phép chặn chuỗi on/off của HMM bằng một e-detector.
- **Không mới:** từng khối riêng (IPDA/Bernoulli existence, e-detectors của Shin–Ramdas–Rinaldo, p-to-e calibrator,
  HMM-VPR).
- **Mức hiện tại:** RA-L/ICRA nếu sửa được Boreas. Nên trình bày như module của hướng certified.

## 4. Kết quả tiêu cực và hạn chế (kèm nguyên nhân đã xác minh)

1. **HMM không tăng recall trung bình** trên các benchmark này: CMU 90.7 → 92.5 % R@5 m. Không có chỗ cho một paper
   "HMM tăng độ chính xác".
2. **Calibrate theo cửa sổ thất bại** (Entry 18): cửa sổ trong một block 300 m phụ thuộc nhau, và số mẫu hiệu dụng của
   null quá nhỏ. Đã giải quyết bằng hiệu chuẩn theo đoạn.
3. **Lỗi dữ liệu Boreas:** bộ đếm xung bánh xe đứt ở 4/13 chuyến, tạo một bước nhảy 8.7 km. Lỗi này làm chuỗi vị trí mất
   dấu (đúng 2 % so với top-1 đúng 99 %). Đã sửa trong `odometry_wheel`; mọi kết quả Boreas trước 2026-10-29 14:00 UTC
   không dùng được.
4. **Boreas, sau khi sửa odometry, CPC-HMM vẫn thua Xu'21** về điều hướng: FL 0.07–0.085 so với 0.018. Hai nguyên nhân
   đã đo:
   - **Độ trễ khi rời bản đồ** chiếm phần lớn FL. Chuỗi ở biên trên cần khoảng log((1−p_out)/p_out)/|KL₀| frame để
     xuống "off". Giảm p (tăng ARL₀) làm FL **tăng**.
     - Tách p_in/p_out (p_in = 0.01, p_out = 0.2) cho FL Boreas MegaLoc 0.029 → 0.007, recall 0.983 → 0.956 (offline).
     - Nhưng Nordland và 4S countryside mất nhiều recall (p_out = 0.05: Nordland 0.74 → 0.58).
     - Lưới điều hướng `CPC-HMM p_out=*` đang chạy.
   - **e^R vi phạm D_R:** P(p^R ≤ 0.01 | off) = 0.059 trên 4S countryside, P(p^R ≤ 0.05 | off) = 0.075 trên Boreas
     MegaLoc. Trong khi đó p^top vẫn super-uniform ở mọi dataset.
     - Null dùng odometry không nhiễu (Bổ đề 3, Anderson) **không** sửa được.
     - Nguyên nhân còn lại: aliasing kết hợp, top-1 trượt đều theo odometry trên đoạn đường giống, xảy ra sâu bên trong
       đoạn off-map dài.
5. **Thống kê dùng niềm tin HMM** (`fac_pc`, `fac_mix`): FL 0.08–0.14, do khoá nhầm.
6. **Mô hình hợp nhất trạng thái** (e-value vào từng nơi): đếm 1/N hai lần (`abs_naive`, recall 0.26) hoặc FL ≈ 0.9
   (`abs`).
7. **Giảm theo ESS** cho chuỗi vị trí: hết khoá nhầm nhưng mất khả năng xếp hạng.
8. **CPC-HMM thiếu tự tin** (ECE 0.08–0.28, overconf âm): an toàn nhưng chưa hiệu chuẩn.
9. **Độ trễ vào lại của CPC-HMM** chậm hơn Xu'21 trên Nordland (79 so với 36 frame). Nhanh hơn trên CMU (3 so với 31).

## 5. Điều kiện kiểm chứng (để tái tạo)

- **Bản đồ:** bỏ 30 % block (CFG block 300 m; Nordland theo frame), seed 0–2. Off-map khi khoảng cách tới bản đồ còn
  lại > off_d; on-map khi ≤ in_d; fix đúng khi sai số ≤ excl (25 m) hoặc tol.
- **Điều hướng:** Kalman vị trí (σ fix 5 m), odometry trôi (mô phỏng: 3 % scale, heading random walk 0.3°/bước) hoặc
  thật (4S VIO, Boreas bánh xe + gyro).
- **Baseline Xu'21:** emission exp(s/T), off-map exp(s₍ₖ₎/T), p_out = 0.01, p_in = 0.05; (T, k) ∈ {0.01, 0.02, 0.05} ×
  {5, 10, 20} chọn bằng nhãn trên 2 điều kiện dễ nhất với FL ≤ α.
- **Baseline khác:** per-frame SelfCal (p ≤ α), ngưỡng max-sim hiệu chuẩn bằng nhãn, accept-all, oracle.
- **Bổ sung 2026-10-31:**
  - Baseline có nhãn tái hiện từ paper (không có code gốc): Claxton'24 = MLP (32, 16) trên 6 đặc trưng profile
    similarity, huấn luyện bằng nhãn trên 2 điều kiện dễ nhất (`bsel`), chấp nhận khi P > 0.5; SafeVPR = điểm MNN patch
    DINOv2 trên top-20 + Mondrian LTT (FDR α = 0.05, δ = 0.1), chỉ có trên Boreas (`nhatlong1103/vpr-safevpr-scores`).
  - Đường cong: 48 ngưỡng (phân vị của điểm từng luật) + ngưỡng mặc định; Kalman ở 14 ngưỡng (`oc_curves.py`); so khớp
    chính xác: 200 ngưỡng, Kalman tại đúng ngưỡng khớp (`oc_matched.py`). Nhãn chỉ dùng để đánh giá.
  - 10 seed cho điểm mặc định (seed 0–9; NCLT 1 seed vì không có lỗ tổng hợp); đường cong và so khớp dùng seed 0–2.
  - Độ bền: `nav_demo.py --drop 0.1 / 0.5` (cùng mọi hằng số). NCLT: bản đồ 2012-01-08, 8 phiên query, excl 10 m, EKF có
    trạng thái lệch hướng.
  - Mọi số trong §N tái tạo từ cache công khai `nhatlong1103/hmm-navcache-v2` (10 seed) và `hmm-navcache-holes` bằng
    `oc_curves.py --variants [--defaults-only] [--cs-sens]`, `oc_matched.py`, `lodo_select.py`, `paper/build_oc_report.py`.
