"""RUN_REPORT.md: what ran (Kaggle + local CPU, with durations), what is pending, and result tables — all from registry/logs."""
import json, os, collections, subprocess
ROOT = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "registry", "runs.jsonl"))]
def latest(exp, ds, desc, seed=None):
    c = [r for r in rows if r.get("experiment_id") == exp and r.get("dataset") == ds and r.get("descriptor") == desc
         and (seed is None or r.get("seed") == seed) and r.get("status") == "ok"]
    return json.load(open(os.path.join(ROOT, "..", c[-1]["artifacts"], "metrics.json"))) if c else None
L = ["# Báo cáo các lần chạy & kết quả (sinh tự động từ registry và log Kaggle)\n",
     "## A. Các kernel Kaggle (GPU dùng để trích xuất descriptor / hình học; thời lượng đo từ log của kernel)\n",
     "| Kernel | Mục đích | Thiết bị | Thời lượng | Trạng thái |", "|---|---|---|---|---|"]
KAGGLE = [  # (kernel, purpose, device, minutes, status) — minutes from kernel log timestamps (max record time)
    ("hmm-k01-nordseg", "Nordland video-rate 2×2500 frame × 4 mùa × SALAD/MegaLoc/NetVLAD/CosPlace", "T4", "51.3", "OK"),
    ("hmm-k02-4s-stopgo", "4Seasons office_loop (map 1 m, query 2 Hz) × SALAD/NetVLAD/CosPlace", "T4", "15.9", "OK (lỗi ghi report ở dòng cuối, dữ liệu đủ)"),
    ("hmm-k03-4s-scene2", "4Seasons countryside × 4 descriptor", "T4", "40.7", "OK"),
    ("hmm-k04-4s-scene3", "4Seasons old_town (dừng thật, có đêm) × 4 descriptor", "T4", "27.2", "OK"),
    ("hmm-k05-pnp v1", "M5 6DoF RobotCar (SuperPoint+LightGlue+PnP)", "T4", "≈27", "INVALID (A27: sai hệ tọa độ NVM)"),
    ("hmm-k06-nvmdiag", "Chẩn đoán hệ tọa độ NVM (CPU)", "CPU", "0.8", "OK"),
    ("hmm-k05-pnp v2", "M5 6DoF RobotCar, ứng viên ảnh đơn vs HMM", "T4", "19.5", "OK"),
    ("hmm-k07-jist v1/v2", "JIST Nordland/RobotCar/CMU ở 384×384 (v1 lỗi thứ tự pip)", "T4 (xin L4, bị hạ xuống T4)", "31.4 (+v1 chưa đo)", "SUPERSEDED (sai kích thước ảnh)"),
    ("hmm-k07-jist v3", "JIST Nordland/RobotCar/CMU ở 480×640 (mặc định JIST)", "T4", "18.4", "OK"),
    ("hmm-k08-jist4s v1/v2", "JIST 4Seasons trên CPU (384 / 480×640)", "CPU", "–", "SUPERSEDED"),
    ("hmm-k08-jist4s v3", "JIST 4Seasons 3 tuyến ở 480×640", "T4", "13.4", "OK"),
]
for k in KAGGLE: L.append("| " + " | ".join(k) + " |")
L.append("\nTổng GPU T4 đã dùng ≈ 4.1 giờ (k01–k08, gồm các lần bị thay thế), chỉ trên tài khoản `nhatlong1103`. "
         "Không lần nào được cấp L4 (yêu cầu `NvidiaL4` bị hạ xuống T4).\n")
L += ["## B. Các lần chạy CPU cục bộ (HMM, thống kê) — theo nhóm thí nghiệm\n", "| Thí nghiệm | Nội dung | Số lần chạy | Tổng phút CPU | Invalid |", "|---|---|---|---|---|"]
DESC = {"E01": "Thang HMM (single/SeqSLAM/HMM τ,β,LLR)", "E18": "IA-HMM đầy đủ (bảng chính, seed, video-rate, 4Seasons)",
        "E18b": "Prior vận tốc (chẩn đoán)", "E15": "Trọng số theo thông tin vs β cố định / keyframe", "E08": "Time-warp ban đầu",
        "E12": "Off-map (lỗ bản đồ)", "E32": "Fixed-lag smoothing", "E21": "Chuyển giao CMU↔RobotCar", "T4.1": "Taxonomy lỗi",
        "PC": "Theo điều kiện + 6DoF thô", "E23": "Runtime", "E30": "Pose 6DoF (nội suy + PnP)", "B10": "Baseline JIST (học chuỗi)"}
g = collections.OrderedDict()
for r in rows:
    k = r.get("experiment_id", "?"); m = (r.get("compute") or {}).get("minutes")
    d = g.setdefault(k, [0, 0.0, 0]); d[0] += 1; d[1] += float(m) if isinstance(m, (int, float)) else 0; d[2] += r.get("status") == "invalid"
for k, (n, mi, inv) in g.items(): L.append(f"| {k} | {DESC.get(k, '')} | {n} | {mi:.1f} | {inv} |")
L.append(f"\nTổng: {len(rows)} lần chạy ghi trong registry. Hàng invalid/superseded được giữ để truy vết (ISSUES A21–A27).\n")
# JIST comparison
L += ["## C. Baseline học chuỗi JIST (Berton et al., RA-L 2024; trọng số chính thức, ResNet-18 + SeqGeM, ảnh 480×640)\n",
      "L ∈ {3,5,10} và stride database ∈ {1,2,3,5} chọn trên calibration (cùng quy tắc với SeqSLAM). R@1 trên test sequences:\n",
      "| Dataset | JIST ảnh đơn | JIST chuỗi (SeqGeM) | JIST chuỗi + HMM | **IA-HMM trên descriptor JIST** | IA-HMM tốt nhất (descriptor khác) |", "|---|---|---|---|---|---|"]
NAMES = {"nord": "Nordland", "cmu": "Extended CMU", "rc": "RobotCar v2", "4s": "4Seasons office_loop", "4s2": "4Seasons countryside", "4s3": "4Seasons old_town"}
for ds, nm in NAMES.items():
    b = latest("B10", ds, "jist"); e = latest("E18", ds, "jist", 0)
    if not b or not e: continue
    bb = b["results"]; ee = e["results"]
    best = max(((d, latest("E18", ds, d, 0)) for d in ("netvlad", "cosplace", "salad", "megaloc")), key=lambda x: x[1]["results"]["OURS_devselected"]["R@1"] if x[1] else -1)
    bstr = f"{best[1]['results']['OURS_devselected']['R@1']:.3f} ({best[0]})" if best[1] else "–"
    L.append(f"| {nm} | {bb['single_jist']['R@1']:.3f} | {bb['JIST_seq']['R@1']:.3f} (L={b['sel'][1]}, k={b['sel'][2]}) | {bb['JIST_seq+HMM']['R@1']:.3f} | **{ee['OURS_devselected']['R@1']:.3f}** | {bstr} |")
e = latest("E18", "nord-tw", "jist", 1)
if e: L.append(f"| Nordland time-warp s1 | {e['results']['single']['R@1']:.3f} | – | – | **{e['results']['OURS_devselected']['R@1']:.3f}** | – |")
L.append("")
open(os.path.join(ROOT, "reports", "RUN_REPORT.md"), "w").write("\n".join(L)); print("\n".join(L))
# D. main table (same generator as REPORT_v1), E. 6DoF, F. Holm, G. pending
import re
rep = open(os.path.join(ROOT, "reports", "REPORT_v1.md")).read()
m = re.search(r"<!--MAIN_TABLE-->\n(.*?)\n<!--/MAIN_TABLE-->", rep, flags=re.S)
L2 = ["## D. Bảng kết quả chính — R@1 (giao thức khóa, test sequences)\n", m.group(1) if m else "(xem REPORT_v1.md)", ""]
pnp = [r for r in rows if r.get("experiment_id") == "E30" and r.get("dataset") == "rc" and "pnp" in r.get("run_id", "")]
if pnp:
    mm = json.load(open(os.path.join(ROOT, "..", pnp[-1]["artifacts"], "metrics.json")))
    L2 += ["## E. 6DoF có hướng dẫn bởi HMM (RobotCar, k=3 ứng viên, SuperPoint+LightGlue+PnP)\n",
           "| Descriptor / tập | Ngưỡng | Ứng viên ảnh đơn | Ứng viên HMM | CI hiệu (bootstrap theo chuỗi) |", "|---|---|---|---|---|"]
    for k, v in mm.items():
        d, tag, thr = k.split("_")
        L2.append(f"| {d} / {tag} | {thr} | {v['single']:.3f} | {v['hmm']:.3f} | [{v['diff_CI'][0]:+.3f}, {v['diff_CI'][1]:+.3f}] |")
    L2.append("")
holm = open(os.path.join(ROOT, "reports", "HOLM.md")).read()
L2 += ["## F. Kiểm định bội (Holm, α=0.05)\n"] + [l.replace("## ", "- ") for l in holm.splitlines() if l.startswith("## ")] + [""]
L2 += ["## G. Đang chờ / chưa chạy\n",
       "| Việc | Trạng thái | Cần gì |", "|---|---|---|",
       "| Kernel Kaggle | không có kernel nào đang chạy | – |",
       "| Phản hồi hình học (số inlier) vào HMM (I30) | chưa chạy | GPU ~30 phút (RobotCar), kết quả k05 dùng lại được |",
       "| 6DoF trên CMU/4Seasons | chưa chạy | tam giác hóa mô hình 3D từ pose reference (GPU ~1 h/dataset) |",
       "| HSMM dwell / bin vận tốc học được (F16) | chưa chạy | CPU |",
       "| Dataset thứ 5 (MSLS sequences) | chưa chạy | quyền truy cập MSLS trên Kaggle + GPU trích xuất |",
       "| SeqVLAD / CaseVPR (baseline học chuỗi khác) | chưa chạy | trọng số công khai (cần xác minh nguồn) |", ""]
open(os.path.join(ROOT, "reports", "RUN_REPORT.md"), "a").write("\n".join(L2)); print("appended", len(L2))
