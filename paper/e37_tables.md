### Entry 37 — tập chính (seed 0–2, NCLT seed 0; 12 run, α = 0.05): recall / segFAR TB / tệ nhất / sai số điều hướng (m)

| Luật | CMU |
|---|---|
| CPC-SC-T½+SH (null bản đồ) | 0.709 / 0.004 / 0.014 / 4.5 |
| SH: CMS-CPC/ H+SH+G+NGRr (dung sai chọn tay) | 0.755 / 0.005 / 0.014 / 4.3 |
| SH ∧ CST (Entry 35) | 0.754 / 0.004 / 0.014 / 4.2 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.604 / 0.000 / 0.000 / 3.1 |
| CST-J (Entry 36) | 0.642 / 0.028 / 0.095 / 3.6 |
| CST-J\* (Entry 36, thăm dò) | 0.782 / 0.027 / 0.095 / 4.5 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.755 / 0.005 / 0.014 / 4.3 |
| **CST-JS: CMS-CPC/ H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.749 / 0.013 / 0.050 / 3.9 |
| SH ∧ CST-JS | 0.740 / 0.004 / 0.014 / 3.7 |
| CST-JS [both] (nhân quả) | 0.729 / 0.011 / 0.039 / 3.6 |
| SH ∧ CST-JS [both] | 0.724 / 0.004 / 0.014 / 3.6 |
| CST-JS0 (cửa sổ ngắn không chứng nhận) | 0.622 / 0.012 / 0.044 / 3.3 |
| CST-JSL (hiện diện = phẫu thuật đầy đủ E36) | 0.775 / 0.027 / 0.095 / 4.2 |
| CST-JF0 (khởi đầu min theo bin) | 0.609 / 0.004 / 0.023 / 3.2 |
| CST-JS không +NGRr | 0.749 / 0.014 / 0.052 / 5.6 |

Tỷ lệ run có segFAR > α / segFAR tệ nhất:

| Luật | run > α | tệ nhất | số run |
|---|---|---|---|
| SH: CMS-CPC/H+SH+G+NGRr (dung sai chọn tay) | 0.000 | 0.014 | 12 |
| SH ∧ CST (Entry 35) | 0.000 | 0.014 | 12 |
| CST-F (Entry 36, đề xuất có chứng nhận) | 0.000 | 0.000 | 12 |
| CST-J (Entry 36) | 0.250 | 0.095 | 12 |
| CST-J\* (Entry 36, thăm dò) | 0.250 | 0.095 | 12 |
| SH ∧ CST-J\* (Entry 36, thực dụng) | 0.000 | 0.014 | 12 |
| **CST-JS: CMS-CPC/H+CSTJS+G+NGRr (Entry 37, luật chính)** | 0.083 | 0.050 | 12 |
| SH ∧ CST-JS | 0.000 | 0.014 | 12 |
| CST-JS [both] (nhân quả) | 0.000 | 0.039 | 12 |
| SH ∧ CST-JS [both] | 0.000 | 0.014 | 12 |

**Kiểm giả thuyết (đăng ký trước, Entry 37):**

- H37a: segFAR TB của CST-JS ≤ 0.05 trên 1/1 (tập chính), Oxford [] (chính, giữ ra), giữ ra 0/6: CMU 0.013
- H37c: recall CST-JS − CST-F trên CMU (chính, giữ ra) = +0.145 (cần ≥ +0.05); CST-JS − SH ≥ −0.03 trên 1/1 (cần ≥ 4/7): CMU -0.007
- H37d: sai số điều hướng CST-JS − SH ≤ 1 m trên 1/1 (cần ≥ 5/7): CMU -0.4
