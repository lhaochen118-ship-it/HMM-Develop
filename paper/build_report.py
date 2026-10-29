#!/usr/bin/env python3
"""Short report (Vietnamese, no figures): method + formulas + result tables vs the latest baselines.
Numbers are read from analysis/results/{cert,nav,natural}_*.json. Usage: build_report.py -> paper/BAO_CAO_CertSeq.{md,pdf}"""
import os, json, glob, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "analysis", "results"); OUT = os.path.join(ROOT, "paper", "BAO_CAO_CertSeq.md")
DS = [("rc", "RobotCar-S."), ("cmu", "CMU-S."), ("nord", "Nordland"), ("4s:office_loop", "4S office"), ("4s:old_town", "4S old town"),
      ("4s:countryside", "4S countryside"), ("boreas", "Boreas")]
H0 = {"rc": 5}


def cert_rows():
    out = []
    for f in glob.glob(os.path.join(R, "cert_*.json")):
        if "_rho" in f or "_noise" in f: continue
        r = json.load(open(f))
        for run in r["runs"]:
            for row in run["rows"]:
                row = dict(row); row["ds"], row["desc"] = r["ds"], r["desc"]; row.setdefault("alpha", 0.05); out.append(row)
    return out


def sel(rs, ds, kind, a=0.05, H=None):
    return [r for r in rs if r["ds"] == ds and r["kind"] == kind and r["alpha"] == a and r["H"] == (H or H0.get(ds, 10))]


def main():
    rs = cert_rows(); dss = [(d, n) for d, n in DS if any(r["ds"] == d for r in rs)]
    nav = [json.load(open(f)) for f in glob.glob(os.path.join(R, "nav_*.json"))]
    nat = [json.load(open(f)) for f in glob.glob(os.path.join(R, "natural_*.json"))]
    L = []
    A = L.append
    A("# Báo cáo: Định vị theo chuỗi có chứng nhận (Certified Sequential Localization)")
    A("")
    A("*Hướng HMM / sequence-based visual localization cho robot dùng camera đơn. Branch `hmm-navigation`, 2026-10-29. "
      "Số liệu sinh tự động từ `analysis/results/` (`paper/build_report.py`); chi tiết thí nghiệm ở `RESEARCH_LOG.md` Entry 18–19.*")
    A("")
    A("## 1. Bài toán và khoảng trống")
    A("")
    A("Robot có bản đồ là một lần chạy trước (ảnh, global descriptor, pose). Khi đi lại, mỗi frame được đối chiếu với bản đồ, "
      "và odometry nối các frame lại với nhau. Với descriptor nền tảng (MegaLoc, SALAD), tỷ lệ tìm đúng nơi đã khoảng 90–98 % "
      "trên RobotCar và CMU (`DATA_AUDIT.md`). HMM thông thường chỉ thêm khoảng 2 điểm.")
    A("")
    A("Thứ còn thiếu là **tính toàn vẹn**: robot đi ra ngoài vùng có bản đồ (rẽ khác, bản đồ thiếu đoạn, cảnh đã đổi) mà bộ "
      "định vị vẫn báo một vị trí. Các phương pháp hiện có đều không chặn được sự kiện này:")
    A("")
    A("- **Kiểm định từng frame** (SelfCal'26, SUE'24) chỉ chặn xác suất sai *của mỗi frame*, không chặn xác suất sai *của cả "
      "đoạn đi lệch*.")
    A("- **HMM có trạng thái off-map** (Xu et al. RA-L'21) và **sequence verifier** (SAFEVPR'26, SMR'25) chọn ngưỡng bằng "
      "nhãn. Ngưỡng tune ở điều kiện dễ không chuyển được sang đêm hay tuyết.")
    A("- **Hiệu chuẩn theo cửa sổ** (window conformal) không hợp lệ: các frame liên tiếp phụ thuộc mạnh, và mức phụ thuộc đổi "
      "theo điều kiện (Entry 18).")
    A("")
    A("**Mục tiêu.** Với mọi đoạn off-map dài H frame: **P(chấp nhận sai ít nhất một lần trong đoạn) ≤ α**. Không dùng nhãn, "
      "áp dụng cho mọi descriptor, đúng với mọi kiểu phụ thuộc thời gian bên trong đoạn.")
    A("")
    A("## 2. Phương pháp")
    A("")
    A("**(a) Bằng chứng từng frame.** ℓ_t = −log p_t, với p_t là p-value SelfCal-AA của match top-1 của frame t:")
    A("")
    A("- tính từ thống kê bất biến affine so với các vùng xa, cộng một cổng max-similarity;")
    A("- hiệu chuẩn trên các pseudo-query leave-block-out của chính bản đồ;")
    A("- cross-fit: test từng frame chỉ được fit trên các block chẵn của bản đồ.")
    A("")
    A("**(b) Bằng chứng chuỗi neo theo odometry (ANCH).** Gọi x_t là vị trí trên bản đồ của top-1 tại frame t và o_t là "
      "odometry tích luỹ. Khi đó")
    A("")
    A("> R_t = ℓ_t + Σ_{j=1..H−1} ℓ_{t−j} · 1[ ‖(x_t − x_{t−j}) − (o_t − o_{t−j})‖ ≤ ρ_o ]")
    A("")
    A("- **Diễn giải HMM:** R_t là điểm Viterbi (max-product) của đường đi kết thúc ở x_t và dịch chuyển theo odometry; "
      "transition bị gate cứng, emission chịu được outlier.")
    A("- **Tham số:** ρ_o là dung sai vật lý của odometry (5 m; Nordland 1 frame).")
    A("- **Vì sao cần odometry:** không có nó (RUN, exp11), một alias đứng yên (tuyết hay đêm làm nhiều frame liền khớp cùng "
      "một chỗ sai) vẫn được tính là nhất quán. Đó là nguyên nhân làm vỡ tính hợp lệ.")
    A("- **ANCHR (không cần hướng):** góc quay giữa odometry và bản đồ là ẩn số. Nó được ước lượng trong mỗi cửa sổ bằng "
      "cách tối đa tổng ℓ của các inlier (RANSAC một tham số). Phù hợp robot camera đơn chưa có fix đầu tiên.")
    A("")
    A("**(c) Hiệu chuẩn mức đoạn bằng chính bản đồ.**")
    A("")
    A("- **Null:** mỗi đoạn H frame liên tiếp của traversal bản đồ nằm trong một block lẻ được giữ lại. Đoạn đó được truy vấn "
      "với bản đồ đã bỏ block ấy, nên off-map theo cấu trúc; odometry mô phỏng từ pose bản đồ. Điểm null của đoạn là "
      "S = max_{t∈đoạn} R_t.")
    A("- **Ngưỡng:** với n đoạn null, τ = S_(k), trong đó k = ⌈(1−α)(n+1)⌉.")
    A("- **Quyết định:** khi triển khai, chấp nhận frame t (báo vị trí x_t) nếu và chỉ nếu R_t > τ.")
    A("- **Chi phí:** tính null một lần cho mỗi bản đồ; mỗi frame chỉ cần retrieval top-1 cộng O(H).")
    A("")
    A("**Định lý 1 (bảo đảm theo đoạn).** Nếu điểm null S_1..S_n và điểm S* = max_{t∈E} R_t của một đoạn off-map E là "
      "exchangeable, thì")
    A("")
    A("> P(∃ t ∈ E : R_t > τ) = P(S* > S_(k)) ≤ α")
    A("")
    A("Định lý không giả định gì về sự phụ thuộc giữa các frame trong đoạn, vì đơn vị exchangeable là cả đoạn. "
      "Chứng minh: rank của S* phân phối đều trên {1..n+1}.")
    A("")
    A("- **Hệ quả 1 (đổi điều kiện).** Nếu S* bị một bản sao exchangeable trội ngẫu nhiên (thay đổi ngoại cảnh làm frame "
      "off-map *kém giống* bản đồ hơn), bảo đảm vẫn giữ. Thống kê AA đã được kiểm chứng có tính trội này; cổng odometry "
      "không phụ thuộc ngoại cảnh.")
    A("- **Hệ quả 2.** Một đoạn dài E frame có P ≤ ⌈E/H⌉·α.")
    A("")
    A("## 3. Thiết lập thí nghiệm")
    A("")
    A("| Dataset | Đặc điểm | Odometry |")
    A("|---|---|---|")
    A("| RobotCar-Seasons v2, Extended CMU-Seasons | benchmark của Sattler'18 | mô phỏng (nhiễu tỷ lệ 3 %, nhiễu bước 5 %) |")
    A("| Nordland | 3 mùa so với mùa hè | mô phỏng |")
    A("| 4Seasons | 3 cảnh, 18 recording | VIO thật |")
    A("| Boreas | 1 tuyến 8 km, 31 lần chạy trong 1 năm | bánh xe + gyro thật |")
    A("")
    A("- **Descriptor:** MegaLoc, SALAD, MixVPR, CosPlace, NetVLAD, DINOv2.")
    A("- **Đoạn off-map:** leave-block-out (block 300 m; Nordland 200 frame) với 3 lưới block ngẫu nhiên, cộng thêm off-map "
      "tự nhiên (query của cảnh hoặc dataset khác).")
    A("- **Tham số:** α = 0.05 nếu không ghi khác; H = 10 (RobotCar H = 5, vì query của nó chỉ là các đoạn 9 frame).")
    A("")
    A("**Baseline:**")
    A("")
    A("| Baseline | Nguồn | Mô tả |")
    A("|---|---|---|")
    A("| per-frame SelfCal | SelfCal'26, label-free | kiểm định từng frame |")
    A("| RUN | exp11, kiểu sequence-matching / SeqSLAM run | run nhất quán, không odometry |")
    A("| label-calibrated | kiểu SAFEVPR'26 / Quantile-Transfer IROS'26 | cùng thống kê ANCH, ngưỡng conformal từ các đoạn off-map *có nhãn* của 2 điều kiện dễ nhất |")
    A("| HMM off-map | Xu et al. RA-L'21 | emission exp(s/T); off-map emission = match thứ k; T và k tune bằng nhãn với ràng buộc FAR ≤ α |")
    A("| accept-all | – | nhận mọi match |")
    A("| oracle | – | chỉ nhận match đúng |")
    A("")
    A("## 4. Kết quả")
    A("")
    # Table 1 validity
    A("### Bảng 1 — Tính hợp lệ: FAR theo đoạn (α = 0.05)")
    A("")
    A("Mỗi ô ghi trung bình trên 6 descriptor × 3 lưới block, kèm (giá trị lớn nhất) và [điều kiện tệ nhất, trung bình]. "
      "Phương pháp hợp lệ khi giá trị trung bình ≤ 0.05.")
    A("")
    A("| Phương pháp | " + " | ".join(n for _, n in dss) + " |"); A("|---|" + "---|" * len(dss))
    for k, name in [("FRAME", "per-frame SelfCal"), ("RUN", "RUN (không odometry)"), ("LABEL", "label-calibrated (SAFEVPR-style)"),
                    ("ANCH", "**ANCH (ours)**"), ("ANCHR", "**ANCHR (ours, không cần hướng)**")]:
        cells = []
        for d, _ in dss:
            s = sel(rs, d, "ANCH" if k == "LABEL" else k)
            if k == "LABEL":
                s = [r for r in s if "label" in r]
                if not s: cells.append("–"); continue
                far = [r["label"]["FAR"] for r in s]; wc = [max(r["label"]["cond"].values()) for r in s if r["label"]["cond"]]
            else:
                if not s: cells.append("–"); continue
                far = [r["FAR_iso"] for r in s]; wc = [max(r["cond_iso"].values()) for r in s if r["cond_iso"]]
            cells.append(f"{np.mean(far):.3f} ({np.max(far):.2f}) [{np.mean(wc):.2f}]")
        A(f"| {name} | " + " | ".join(cells) + " |")
    A("")
    # Table 2 power
    A("### Bảng 2 — Power")
    A("")
    A("Mỗi ô ghi: tỷ lệ frame on-map có match đúng được chứng nhận / độ trễ trung vị (số frame) tới fix đúng đầu tiên. "
      "Riêng hàng label-calibrated chỉ ghi tỷ lệ.")
    A("")
    A("| Phương pháp | " + " | ".join(n for _, n in dss) + " |"); A("|---|" + "---|" * len(dss))
    for k, name in [("FRAME", "per-frame SelfCal"), ("RUN", "RUN (không odometry)"), ("LABEL", "label-calibrated (cần nhãn)"),
                    ("ANCH", "**ANCH (ours)**"), ("ANCHR", "**ANCHR (ours)**")]:
        cells = []
        for d, _ in dss:
            s = sel(rs, d, "ANCH" if k == "LABEL" else k)
            if k == "LABEL":
                s = [r for r in s if "label" in r]; cells.append(f"{np.mean([r['label']['TPR'] for r in s]):.2f}" if s else "–"); continue
            cells.append(f"{np.mean([r['TPR'] for r in s]):.2f} / {np.median([r['latency_med'] for r in s]):.0f}" if s else "–")
        A(f"| {name} | " + " | ".join(cells) + " |")
    A("")
    # Table 3 per descriptor
    A("### Bảng 3 — Power theo descriptor: ANCH so với per-frame SelfCal")
    A("")
    descs = ["megaloc", "salad", "mixvpr", "cosplace", "netvlad", "dinov2"]
    A("| Dataset | " + " | ".join(descs) + " |"); A("|---|" + "---|" * len(descs))
    for d, n in dss:
        cells = []
        for de in descs:
            a = [r["TPR"] for r in sel(rs, d, "ANCH") if r["desc"] == de]; b = [r["TPR"] for r in sel(rs, d, "FRAME") if r["desc"] == de]
            cells.append(f"{np.mean(a):.2f} / {np.mean(b):.2f}" if a and b else "–")
        A(f"| {n} | " + " | ".join(cells) + " |")
    A("")
    # Table 4 alpha sweep
    A("### Bảng 4 — FAR theo đoạn của ANCH khi đổi α và H")
    A("")
    A("Mỗi ô là trung bình trên descriptor và lưới block. n = số đoạn null.")
    A("")
    A("| Dataset | H | α = 0.01 | α = 0.05 | α = 0.10 | n |"); A("|---|---|---|---|---|---|")
    for d, n in dss:
        for H in sorted({r["H"] for r in rs if r["ds"] == d}):
            c = []
            for a in (0.01, 0.05, 0.1):
                v = [r["FAR_iso"] for r in sel(rs, d, "ANCH", a, H)]; c.append(f"{np.mean(v):.3f}" if v else "–")
            ns = [r["n_null_seg"] for r in sel(rs, d, "ANCH", 0.05, H)]
            A(f"| {n} | {H} | " + " | ".join(c) + f" | {np.mean(ns):.0f} |" if ns else f"| {n} | {H} | " + " | ".join(c) + " | – |")
    A("")
    A("Ô '–' ở α = 0.01 nghĩa là bản đồ có dưới 100 đoạn null, nên không đặt được ngưỡng.")
    A("")
    # Table 5 natural
    if nat:
        A("### Bảng 5 — Off-map tự nhiên: query của cảnh hoặc dataset khác chạy trên bản đồ (FAR theo đoạn, α = 0.05, H = 10)")
        A("")
        A("Mỗi ô là trung bình trên các nguồn query và descriptor, kèm (giá trị lớn nhất).")
        A("")
        A("| Bản đồ | per-frame | ANCH | ANCHR | nguồn query |"); A("|---|---|---|---|---|")
        for m in sorted({n["map"] for n in nat}):
            cells = []
            for k in ("FRAME", "ANCH", "ANCHR"):
                v = [r["FAR"]["0.05"] for n in nat if n["map"] == m for r in n["rows"] if r["kind"] == k and r["H"] == 10 and r["n_seg"] > 0]
                cells.append(f"{np.mean(v):.3f} ({np.max(v):.3f})" if v else "–")
            src = sorted({r["src"] for n in nat if n["map"] == m for r in n["rows"]})
            A(f"| {dict(DS).get(m, m)} | " + " | ".join(cells) + f" | {', '.join(dict(DS).get(s, s) for s in src)} |")
        A("")
    # Table 6 navigation
    if nav:
        rules = ["accept all", "label threshold", "SelfCal frame", "HMM off-map (labels)", "certified (ours)", "oracle"]
        rn = {"accept all": "accept-all", "label threshold": "ngưỡng max-sim (nhãn)", "SelfCal frame": "per-frame SelfCal",
              "HMM off-map (labels)": "HMM off-map Xu'21 (nhãn)", "certified (ours)": "**ours**", "oracle": "oracle"}
        A("### Bảng 6 — Điều hướng khép kín, bản đồ khuyết 30 % block")
        A("")
        A("Kalman filter chạy odometry trôi và nhận các fix được chấp nhận (σ = 5 m). Mỗi ô ghi sai số vị trí trung bình "
          "(phân vị 95) trên descriptor và seed. Nordland tính bằng frame, các dataset khác tính bằng mét.")
        A("")
        A("| Dataset | " + " | ".join(rn[k] for k in rules) + " |"); A("|---|" + "---|" * len(rules))
        for d, n in DS:
            ns = [x for x in nav if x["ds"] == d]
            if not ns: continue
            cells = []
            for k in rules:
                v = [run["rules"][k] for x in ns for run in x["runs"] if k in run["rules"]]
                cells.append(f"{np.mean([y['err_mean'] for y in v]):.1f} ({np.mean([y['err_p95'] for y in v]):.0f})" if v else "–")
            A(f"| {n} | " + " | ".join(cells) + " |")
        A("")
    A("## 5. Kết luận")
    A("")
    A("- **Hợp lệ.** Bảo đảm theo đoạn giữ ở mọi bộ dữ liệu và descriptor, không dùng nhãn (Bảng 1, 4, 5). Baseline hiệu "
      "chuẩn bằng nhãn kiểu SAFEVPR vượt α trên RobotCar và CMU.")
    A("- **Power.** Số frame đúng được chứng nhận tăng 2–7× so với kiểm định từng frame, và fix đầu tiên đến sớm hơn nhiều "
      "(Bảng 2, 3).")
    A("- **Điều hướng.** Trong vòng điều hướng, fix có chứng nhận cho sai số thấp nhất hoặc ngang oracle. HMM off-map tune "
      "bằng nhãn (Xu'21) có nhiều fix đúng nhưng thỉnh thoảng khoá nhầm chỗ, làm đuôi sai số rất lớn (Bảng 6).")
    A("- **Giới hạn:**")
    A("  - chuỗi quá ngắn (RobotCar, 9 frame) gần như không tăng power;")
    A("  - bản đồ nhỏ (CMU, khoảng 70 đoạn null) cho FAR của từng bản đồ dao động quanh cùng một trung bình;")
    A("  - giả định các đoạn off-map giống đoạn bản đồ bị giữ lại (exchangeable), được kiểm tra bằng off-map tự nhiên;")
    A("  - mới ở mức place (5 m); tinh chỉnh 6DOF theo ngưỡng Sattler'18 là bước sau, và có thể dùng fix đã chứng nhận làm "
      "cổng cho bộ giải 6DOF.")
    open(OUT, "w").write("\n".join(L) + "\n")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "automation", "md2pdf.py"), OUT, OUT[:-3] + ".pdf"], capture_output=True, text=True)
    print((r.stdout + r.stderr)[-300:]); print("written", OUT)


if __name__ == "__main__":
    main()
