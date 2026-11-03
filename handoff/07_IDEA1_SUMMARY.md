# 07 — Ý tưởng 1 (branch `hmm-navigation-5`): tóm tắt để đánh bại, không để làm tiếp

*2026-11-03. Đây là bản tóm tắt của toàn bộ hướng nghiên cứu thứ nhất (Entry 18–39 trong `history/RESEARCH_LOG_idea1.md`). Code của nó đã
được gỡ khỏi branch này; khôi phục khi cần chạy lại làm baseline: `git checkout hmm-navigation-5 -- analysis/<file>.py` (cả các module
phụ thuộc: `cms*.py`, `cpc*.py`, `navrisk.py`, `oc_curves.py`, `e37_*.py`). Số liệu thô của baseline: `analysis/results/baselines_idea1/`.*

## 1. Bài toán và giao thức đánh giá (giữ nguyên cho ý tưởng 2)

- Robot camera đơn + odometry đi trên bản đồ ảnh **có lỗ** (30 % ô 300 m của bản đồ bị xoá; Nordland: 200 frame; NCLT: off-map tự nhiên).
  Mỗi frame: có báo một "fix" vị trí cho bộ lọc điều hướng hay không. Mục tiêu: nhiều fix đúng (recall), ít fix sai khi robot ở ngoài bản
  đồ, **không dùng nhãn** khi triển khai.
- Dữ liệu: 7 dataset (Boreas, NCLT, CMU, Nordland, 4Seasons office / old town / countryside) × 6 descriptor (CosPlace, NetVLAD, MegaLoc,
  SALAD, MixVPR, DINOv2) × 10 seed lỗ (+ seed 10–12 cho bố cục mới), Oxford RobotCar (seed 0–9), St Lucia (6 descriptor, seed 0–4).
  Cache công khai: `ENVIRONMENT_SUMMARY.md` §1d–1g.
- Thước đo (`nav_demo.rule_metrics`, `oc_summary`, `e26_summary`): recall (frame đúng trong bán kính in_d được báo / frame on-map), **segFAR**
  (tỷ lệ đoạn off-map H frame có ≥ 1 báo; mục tiêu ≤ α = 0.05), FL (tỷ lệ frame off-map có báo), sai số điều hướng TB (Kalman với các fix).
  Kiểm toán theo vị trí (`analysis/position_audit.py`): đoạn đầu chuỗi / mép / sâu, mục tiêu ≤ 0.07.
- Quy trình: đăng ký trước (commit trước khi xem), tập giữ ra, leave-one-dataset-out, đường cong vận hành + so khớp, 10 seed, lỗ 10/30/50 %.

## 2. Dòng phát triển của ý tưởng 1 (mỗi bước một câu)

1. SelfCal (Entry 12–17): p-value hiệu chuẩn bằng bản đồ (null leave-block-out) cho từng frame.
2. CPC-HMM / CPC-SC+CS (Entry 20–25): chuỗi hiện diện kiểu HMM bằng e-value + quy tắc dừng nhất quán odometry.
3. **CMS — Counterfactual Map Surgery** (Entry 28–31): null hiệu chuẩn sinh từ chính luồng query bằng cách xoá hành lang ρ = off_d quanh niềm
   tin của hệ thống; luật CMS-CPC/H+SH+G+NGRr (SH = dung sai hình dạng chọn tay 12.5 m, G = cổng đồng thuận, NGRr = cổng rủi ro điều hướng).
4. CST (Entry 34–35): phép thử hình dạng phản thực; SH ∧ CST.
5. Phẫu thuật TIẾN (Entry 36): lối thoát ảo, chạy chính bộ lọc của hệ thống tiến trên bản đồ đã xoá → CST-F (có chứng nhận), CST-J (mô phỏng cả quyết định).
6. Entry 37: phẫu thuật tiến cả bằng chứng hiện diện + null đầu chuỗi chính xác → CST-JS; Entry 38: lỗ ảo hình khối → CST-JSU.

## 3. Số liệu tốt nhất cần đánh bại (α = 0.05; recall / segFAR TB)

| Luật | Boreas | NCLT | CMU | Nordland | office | old town | countryside | Oxford | St Lucia |
|---|---|---|---|---|---|---|---|---|---|
| **SH** (CMS-CPC/H+SH+G+NGRr, seed 0–2) | 0.779 / 0.004 | 0.612 / 0.002 | 0.764 / 0.003 | 0.752 / 0.000 | 0.795 / 0.000 | 0.687 / 0.003 | 0.513 / 0.001 | 0.729 / 0.004 | 0.761 / 0.001 |
| CST-JS (không hằng số chọn tay) | 0.782 / 0.009 | 0.632 / 0.003 | 0.758 / 0.011 | 0.767 / 0.001 | 0.807 / 0.007 | 0.696 / 0.010 | 0.523 / 0.003 | 0.738 / 0.023 | 0.763 / 0.021 |
| CST-F (cận chứng nhận theo đoạn) | 0.764 / 0.002 | 0.581 / 0.000 | 0.603 / 0.000 | 0.726 / 0.000 | 0.771 / 0.000 | 0.637 / 0.002 | 0.477 / 0.000 | 0.550 / 0.001 | 0.513 / 0.000 |

Sai số điều hướng TB của SH (m): Boreas 4.5, NCLT 4.3, CMU 3.9, Nordland 6.9, office 10.1, old town 27.5, countryside 33.9.
Baseline có nhãn (cùng giao thức, `01_SCIENTIFIC_FINDINGS.md` §N…): Xu'21, Claxton'24 vượt α nhiều (segFAR 0.02–0.26); TAO'26 ngưỡng 3σ
vỡ (0.24–0.74); SafeVPR'26 (St Lucia, ViT-L/14, có nhãn) recall 0.20–0.54 ở α = 0.05 — thấp hơn SH ở 6/6 descriptor.
N = 40 (cửa sổ niềm tin) tăng recall 0.01–0.03 so với N = 20 trên mọi dataset.

## 4. Giới hạn đã biết của ý tưởng 1 (cơ hội cho ý tưởng 2)

- Recall bị chặn bởi bộ lọc vị trí và descriptor: countryside 0.51, NCLT 0.61, old town 0.69; DINOv2/NetVLAD thấp (0.2–0.6).
- Old town: báo sai ở **mép lỗ** sang nơi giống nhau ở xa (~1 km) → sai số điều hướng +13–15 m với luật không có SH.
- Bảo đảm theo từng vị trí (mép, đầu chuỗi) chưa đạt: tỷ lệ báo ở mép Boreas 0.08, old town 0.11; lỗ ảo hình khối không sửa được (Entry 38).
- Chi phí hiệu chuẩn lớn: mô phỏng tiến ~18–45 ms/frame/lõi (đã gộp lô GPU), cần chạy trên cả luồng của phiên.
- Mọi luật đều quyết định "báo / không báo" trên fix của một bộ lọc có sẵn; không học, không dùng hình học 6DOF / local feature (dump chỉ có
  global descriptor; ảnh gốc có cho Boreas, 4Seasons, NCLT, St Lucia — xem `ENVIRONMENT_SUMMARY.md`).
- Novelty (Gate 9–16): ý tưởng 1 được đánh giá "A khả thi, A\\* chưa chắc"; mô phỏng tiến bản thân nó mới (Gate 16) nhưng phức tạp.

## 5. Bài học khoa học chuyển giao được

- Phép thử một bước tự xác nhận; nhất quán odometry trên quãng dịch chuyển phân biệt rất mạnh; null tự phát lại của bản đồ thiếu phụ thuộc
  thời gian của đoạn off-map dài; null sinh từ chính luồng (can thiệp lên bản đồ) khớp điều kiện ảnh tốt hơn null bản đồ.
- Mọi bảo đảm thực nghiệm phải được kiểm theo **vị trí** (mép, đầu chuỗi), không chỉ trung bình.
- Lỗi dữ liệu thật (Boreas dmi, 4/13 chuỗi) đã làm hỏng một vòng: luôn chẩn đoán từng frame trước khi kết luận.
