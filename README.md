# HMM-Develop — HMM cho Monocular Sequence-based Visual Localization

Nghiên cứu khả năng và giới hạn của Hidden Markov Models (lọc Bayes rời rạc trên bản đồ topo) cho định vị thị giác theo chuỗi
ảnh từ camera đơn, cho cả Visual Place Recognition và 6DoF localization.

## Bắt đầu từ đâu
| Bạn là | Đọc |
|---|---|
| AI agent bắt đầu một phiên | `research/STATE.md` → giai đoạn hiện tại trong `docs/MASTER_RESEARCH_PLAN.md` §6 → `research/HYPOTHESES.md` → `research/DASHBOARD.md` |
| Người muốn hiểu hướng nghiên cứu | `docs/MASTER_RESEARCH_PLAN.md` §1 (tóm tắt), §2 (kiểm toán), §5 (giả thuyết) |
| Người muốn chạy thí nghiệm cũ | `HANDOFF_CCBF.md` (Kaggle, notebook build từ `nb_src/`, `nb2_src/`) |

## Cấu trúc
| Đường dẫn | Nội dung |
|---|---|
| `docs/MASTER_RESEARCH_PLAN.md` | Kế hoạch nghiên cứu tổng (7 giai đoạn, giả thuyết, gates, Research OS) |
| `research/` | Trạng thái sống, registry thí nghiệm, findings, quyết định, issues, pilots |
| `automation/` | Build notebook, chạy Kaggle, `log_run.py` (registry) |
| `nb_src/`, `nb2_src/`, `diag_src/` | Nguồn cell của các notebook CCBF (legacy v1) |
| `CCBF_methodology.md` | Methodology + lý thuyết của CCBF (legacy, tái sử dụng một phần) |

## Quy tắc
- Mọi run (kể cả thất bại) được ghi: `python automation/log_run.py add <record.json>`; sau đó `python automation/log_run.py dashboard`.
- Không con số nào vào findings/paper mà không có `run_id`. Mức bằng chứng: V/S/P/R (xem plan §0.3).
- Không commit token Kaggle hay dữ liệu thô; feature bank lớn để trên Kaggle Datasets.
