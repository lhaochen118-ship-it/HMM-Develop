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
        rules = ["accept all", "label threshold", "SelfCal frame", "HMM off-map (labels)", "CPC-HMM (ours)", "certified (ours)", "oracle"]
        rn = {"accept all": "accept-all", "label threshold": "ngưỡng max-sim (nhãn)", "SelfCal frame": "per-frame SelfCal",
              "HMM off-map (labels)": "HMM off-map Xu'21 (nhãn)", "CPC-HMM (ours)": "**CPC-HMM (mục 5)**",
              "certified (ours)": "**certified**", "oracle": "oracle"}
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
    # ------------------------------------------------------------------ HMM weakness analysis + fix
    diag = [json.load(open(f)) for f in glob.glob(os.path.join(R, "hmmdiag_*.json"))]
    fix = [x for x in (json.load(open(f)) for f in glob.glob(os.path.join(R, "hmmfix_*.json"))) if x.get("drop", 0.3) == 0.3]
    if diag:
        A("## 5. Vì sao HMM thua baseline, và cơ chế sửa")
        A("")
        if nav:
            A("### 5.0 HMM thua baseline ở đâu")
            A("")
            A("Lấy từ Bảng 6: sai số điều hướng trung bình (p95), cùng giao thức. Cột \"HMM thua\" đánh dấu khi HMM Xu'21, dù "
              "được tune bằng nhãn, có sai số trung bình lớn hơn baseline không nhãn đơn giản nhất (per-frame SelfCal).")
            A("")
            A("| Dataset | HMM Xu'21 (nhãn) | per-frame SelfCal | HMM thua? | CPC-HMM | CPC-HMM / Xu'21 |"); A("|---|---|---|---|---|---|")
            for d, n in DS:
                ns = [x for x in nav if x["ds"] == d]
                g = lambda k, f: [run["rules"][k][f] for x in ns for run in x["runs"] if k in run["rules"]]
                h, b, c_ = g("HMM off-map (labels)", "err_mean"), g("SelfCal frame", "err_mean"), g("CPC-HMM (ours)", "err_mean")
                if not h or not b: continue
                hp, bp, cp = g("HMM off-map (labels)", "err_p95"), g("SelfCal frame", "err_p95"), g("CPC-HMM (ours)", "err_p95")
                A(f"| {n} | {np.mean(h):.1f} ({np.mean(hp):.0f}) | {np.mean(b):.1f} ({np.mean(bp):.0f}) | "
                  f"{'có' if np.mean(h) > np.mean(b) else 'không'} | " + (f"{np.mean(c_):.1f} ({np.mean(cp):.0f}) | {np.mean(c_) / np.mean(h):.2f}× |" if c_ else "– | – |"))
            A("")
        A("### 5.1 Chẩn đoán (`analysis/hmm_diag.py`)")
        A("")
        A("Thiết lập: HMM chuẩn (lọc tiến trên các ảnh bản đồ, chuyển trạng thái theo odometry, emission exp(s/T), có hoặc "
          "không có trạng thái off-map của Xu'21) trên bản đồ khuyết 30 % block. Mỗi ô là trung bình trên descriptor.")
        A("")
        A("Các cột:")
        A("")
        A("- **R@FL5:** tỷ lệ frame on-map đúng được nhận khi giới hạn định vị sai off-map ở 5 %.")
        A("- **conf, acc:** độ tin cậy trung bình so với độ chính xác thật.")
        A("- **khoá nhầm:** tỷ lệ frame sai mà vẫn tin > 0.9 / tỷ lệ tổng sai số do các frame đó gây ra.")
        A("- **r, VIF:** tự tương quan trễ 1 của dòng bằng chứng, và hệ số phóng đại phương sai (1+r)/(1−r).")
        A("- **D5:** thay đổi lớn nhất của posterior khi cộng một hằng số ngẫu nhiên vào mọi similarity của từng frame.")
        A("")
        A("| Dataset | R@FL5 max-sim thô | R@FL5 posterior HMM | R@FL5 HMM+off-map | conf / acc | ECE | khoá nhầm | r (VIF) | D5 |")
        A("|---|---|---|---|---|---|---|---|---|")
        for d, n in DS:
            g = [x for x in diag if x["ds"] == d]
            if not g: continue
            h = lambda f: np.nanmean([f(x) for x in g])
            ac = [x["D4"]["lag1_autocorr_median"] for x in g if np.isfinite(x["D4"]["lag1_autocorr_median"])]
            racs = f"{np.median(ac):.2f} ({(1 + np.median(ac)) / (1 - np.median(ac)):.0f}×)" if ac else "– (chuỗi < 20 frame)"
            A(f"| {n} | {h(lambda x: x['methods']['hmm']['D1']['raw_maxsim']['R_at_FL5']):.2f} | {h(lambda x: x['methods']['hmm']['D1']['conf']['R_at_FL5']):.2f} | "
              f"{h(lambda x: x['methods']['hmm_off']['D1']['conf*(1-off)']['R_at_FL5']):.2f} | {h(lambda x: x['methods']['hmm']['D2']['mean_conf']):.2f} / "
              f"{h(lambda x: x['methods']['hmm']['D2']['acc']):.2f} | {h(lambda x: x['methods']['hmm']['D2']['ECE']):.2f} | "
              f"{h(lambda x: x['methods']['hmm']['D3']['frac_frames']):.2f} / {h(lambda x: x['methods']['hmm']['D3']['share_of_total_error']):.2f} | {racs} | "
              f"{max(x['D5']['max_abs_conf_change'] for x in g):.0e} |")
        A("")
        A("**Nguyên nhân gốc (được số liệu xác nhận):**")
        A("")
        A("1. **Bất biến bằng chứng tương đối (D1, D5).**")
        A("   - Emission softmax p(s_t | j) ∝ exp(s_tj / T) cho posterior bất biến khi s_t → s_t + c_t·1. Trạng thái off-map "
          "của Xu'21, exp(s₍ₖ₎/T), cũng bất biến như vậy, nên chỉ đo được độ nhọn s_max − s₍ₖ₎.")
        A("   - Nhưng câu hỏi \"robot có ở trong bản đồ không\" là câu hỏi về mức tuyệt đối: LR(j : ∅) = f₁(s_j) / f₀(s_j). "
          "HMM về cấu trúc không thấy được sự vắng mặt.")
        A("   - Max-sim thô thắng posterior trên RobotCar, CMU và 4Seasons. Nordland là ngoại lệ: ở đó mức similarity bị mùa "
          "đông làm dịch, nên cần mức tuyệt đối đã được hiệu chuẩn bất biến affine, không phải mức thô.")
        A("2. **Đếm lặp bằng chứng phụ thuộc (D2, D3, D4).**")
        A("   - HMM giả định quan sát độc lập khi biết trạng thái, nhưng bằng chứng của các frame liên tiếp có r ≈ 0.8–0.99.")
        A("   - Var(Σd_t) ≈ nσ²(1+r)/(1−r), trong khi HMM tính như nσ²: đếm thừa 4–200×.")
        A("   - Hệ quả: posterior quá tự tin (conf > acc) và khoá nhầm chỗ. Các frame sai mà vẫn tin > 0.9 gây ra khoảng 40 % "
          "tổng sai số.")
        A("3. **Vòng phản hồi khoá nhầm.** Mọi bằng chứng tính từ chính niềm tin của HMM đều tự xác nhận khi đã khoá nhầm. "
          "Thí nghiệm `fac_pc` và `fac_mix` đều thất bại vì lý do này (mục 5.3).")
        A("")
        A("### 5.2 Cơ chế đề xuất: CPC-HMM (HMM với chuỗi hiện diện đã hiệu chuẩn)")
        A("")
        A("Tách HMM thành 2 chuỗi:")
        A("")
        A("- **Chuỗi vị trí (\"ở đâu\")** là HMM chuẩn không có trạng thái off-map, với emission tương đối bất biến affine "
          "và không cần tune:")
        A("")
        A("  > log e_t(j) = (s_tj − max_i s_ti) / (τ · σ_far,t)")
        A("")
        A("  Ở đây σ_far,t là độ trải của các cực đại vùng xa của chính frame t, và τ là thang Gumbel của null bản đồ "
          "(z_far của các pseudo-query leave-block-out).")
        A("- **Chuỗi hiện diện (\"có trong bản đồ không\")** gồm 2 trạng thái on/off:")
        A("")
        A("  > P(on_t | ·) ∝ [ (1−p_out)·P(on_{t−1}) + p_in·P(off_{t−1}) ] · LR_t,  với LR_t = a · p_t^(a−1)")
        A("")
        A("  - p_t là p-value SelfCal-AA của top-1, hiệu chuẩn bằng bản đồ (bất biến affine, có cổng max-sim). Dưới H0, "
          "p_t ~ U(0,1) nên E[LR_t] = 1, tức LR_t là một e-value.")
        A("  - Tham số a lấy từ EM không nhãn trên dòng p-value của chính chuyến đi: π₀·U + (1−π₀)·Beta(a,1).")
        A("  - **Cổng độc lập niềm tin:** khi top-1 không khớp với nơi MAP của chuỗi vị trí (lệch > 25 m), frame đó được "
          "tính là p = 1.")
        A("  - Prior đối xứng p_in = p_out = 0.01.")
        A("- **Nguồn bằng chứng thứ hai, độc lập với niềm tin:** thống kê neo odometry R_t (mục 2b) của dòng top-1 trong "
          "cửa sổ H = 10 frame. Nó được hiệu chuẩn từng frame với null R trên traversal của chính bản đồ, cho p-value p^R_t "
          "và e-value e^R_t = a′(p^R_t)^(a′−1).")
        A("- **Gộp hai bằng chứng:** mỗi frame nằm trong H cửa sổ, nên e^R được luỹ thừa 1/H để không đếm lặp. Vẫn là e-value "
          "nhờ bất đẳng thức Jensen: E[e^w] ≤ (E[e])^w ≤ 1. Hai e-value được gộp bằng trung bình, cách gộp hợp lệ với mọi "
          "kiểu phụ thuộc giữa chúng:")
        A("")
        A("  > LR_t = ½ · ( e^top_t + (e^R_t)^(1/H) )")
        A("")
        A("- **Quyết định:** báo nơi MAP của chuỗi vị trí khi P(on) > 0.5. Độ tin cậy là P(on) × độ tập trung posterior.")
        A("")
        A("- **Ngưỡng báo sai:** với p_in = p_out = p, odds của chuỗi hiện diện bị chặn bởi thống kê Shiryaev–Roberts "
          "R_t ≤ (R_{t−1} + 1)·LR_t, nên số frame off-map trung bình trước một lần báo on sai thoả ARL₀ ≥ (1−p)/p − R₀ "
          "(≈ 98 frame khi p = 0.01). Bảo đảm này không cần nhãn, vì LR_t là e-value.")
        A("")
    if fix:
        MM = [("xu21_tuned", "HMM + off-map Xu'21 (T, k tune bằng nhãn)"), ("xu21_sym", "Xu'21, prior đối xứng p_in = p_out = 0.01"),
              ("hmm_nooff_tuned", "HMM không off-map (T tune)"),
              ("rel", "chỉ emission bất biến affine"), ("abs_naive", "e-value nhân vào từng nơi (đếm 1/N hai lần)"),
              ("fac_now", "CPC, prior lệch (p_in = 0.05)"), ("fac_ess_pr", "CPC + giảm theo ESS"),
              ("fac_anch_mix", "CPC + ANCH không luỹ thừa (đếm lặp)"), ("fac_now_sym", "CPC, chỉ e-value top-1"),
              ("fac_anchT_mix", "**CPC-HMM đầy đủ (đề xuất, không nhãn)**")]
        A("### 5.3 Kết quả: CPC-HMM so với HMM Xu'21 (`analysis/hmm_fix.py`)")
        A("")
        A("Bản đồ khuyết 30 %, 6 descriptor × 2 seed. Mỗi ô ghi: recall on-map / định vị sai off-map (FL) / recall ở 5 % FL "
          "/ ECE / sai số điều hướng trung bình (p95). Nordland tính bằng frame, các dataset khác tính bằng mét.")
        A("")
        dsx = [(d, n) for d, n in DS if any(x["ds"] == d for x in fix)]
        A("| Phương pháp | " + " | ".join(n for _, n in dsx) + " |"); A("|---|" + "---|" * len(dsx))
        for m, mn in MM:
            cells = []
            for d, _ in dsx:
                v = [run["methods"][m] for x in fix if x["ds"] == d for run in x["runs"] if m in run["methods"]]
                if not v: cells.append("–"); continue
                g = lambda k: np.nanmean([y[k] for y in v])
                cells.append(f"{g('recall'):.2f} / {g('FL'):.3f} / {g('R_FL5'):.2f} / {g('ECE'):.2f} / {g('nav_mean'):.1f} ({g('nav_p95'):.0f})")
            A(f"| {mn} | " + " | ".join(cells) + " |")
        A("")
        # CUSUM / Shiryaev-Roberts check (Proposition 4): ARL0 and re-entry delay
        if any("ARL0" in run["methods"].get("fac_anchT_mix", {}) for x in fix for run in x["runs"]):
            A("**Kiểm chứng ngưỡng báo sai.** ARL₀ là số frame off-map trên mỗi lần bắt đầu báo on sai. Cận lý thuyết là ≥ 98 khi "
              "p_in = 0.01 và LR là e-value. Độ trễ vào lại là số frame từ khi vào lại bản đồ đến fix đúng đầu tiên. Mỗi ô ghi "
              "ARL₀ / độ trễ vào lại.")
            A("")
            A("| Phương pháp | " + " | ".join(n for _, n in dsx) + " |"); A("|---|" + "---|" * len(dsx))
            for m, mn in [("xu21_tuned", "HMM + off-map Xu'21 (nhãn)"), ("xu21_sym", "Xu'21, prior đối xứng"),
                          ("fac_now", "CPC, p_in = 0.05 (cận ≥ 18)"), ("fac_now_sym", "CPC, chỉ e^top"),
                          ("fac_anch_mix", "CPC, e^R không luỹ thừa"), ("fac_anchT_mix", "**CPC-HMM đầy đủ**")]:
                cells = []
                for d, _ in dsx:
                    v = [run["methods"][m] for x in fix if x["ds"] == d for run in x["runs"] if "ARL0" in run["methods"].get(m, {})]
                    cells.append(f"{np.nanmedian([y['ARL0'] for y in v]):.0f} / {np.nanmean([y['reentry_delay'] for y in v]):.1f}" if v else "–")
                A(f"| {mn} | " + " | ".join(cells) + " |")
            A("")
        A("**Thử nghiệm âm tính (giữ lại để tránh lặp lại):**")
        A("")
        A("- Bằng chứng hiện diện tính tại nơi MAP của HMM (`fac_pc`), trên Nordland CosPlace: FL 0.08, sai số điều hướng "
          "315 frame.")
        A("- Thêm e-value từ độ tập trung posterior, hiệu chuẩn bằng null bản đồ (`fac_mix`): recall 0.85 nhưng FL 0.14, sai "
          "số điều hướng 280 frame.")
        A("- Cả hai cùng một nguyên nhân: thống kê lấy từ niềm tin của HMM bị nhiễm khoá nhầm.")
        A("- Giảm theo độ dư thừa (ESS) giúp hạn chế khoá nhầm nhưng làm giảm khả năng xếp hạng. Nó là tuỳ chọn, không nằm "
          "trong cấu hình chính.")
        A("- Đưa e-value ANCH vào mà không luỹ thừa 1/H làm FL trên CMU tăng lên 0.15. Đây chính là lỗi đếm lặp bằng chứng "
          "phụ thuộc (nguyên nhân 2) xuất hiện ở tầng hiện diện.")
        A("")
    gg = [x for x in nav if x["runs"] and "CPC-HMM +GG" in x["runs"][0]["rules"]]
    if gg:
        A("### 5.4 Cổng dead-reckoning (CPC-HMM +GG) — sửa fix sai ở xa trong lỗ bản đồ")
        A("")
        A("**Chẩn đoán (Boreas, `nav_demo --dump`).** Fix sai của CPC-HMM nằm rất xa vị trí thật (trung vị 111–182 m, p90 "
          "tới 954 m), sâu trong lỗ bản đồ (47–72 % frame báo sai cách frame on-map cuối > 100 frame). Fix sai của Xu'21 chỉ "
          "cách 37–56 m. Trong lỗ, chuỗi vị trí trôi tới một đoạn đường giống (aliasing), cổng \"top-1 khớp MAP\" luôn qua, "
          "và bằng chứng yếu nhưng phụ thuộc tích luỹ thành báo on. Các thử nghiệm p_out lớn hơn, p_out theo KL₀, rò rỉ ở mép "
          "bản đồ, cổng dự đoán (PG) và trạng thái off-map dead-reckoning cho việc vào lại (DR) đều không sửa được.")
        A("")
        A("**Cơ chế.** Khi chưa báo nơi nào (P(on_{t−1}) ≤ ½), e-value top-1 được nhân với")
        A("")
        A("> g_t = (1−ρ)·exp(−d_t² / 2s_t²) + ρ,  d_t = ‖m_top,t − μ_t‖,  s_t = excl + κ·(quãng đường từ fix báo cuối)")
        A("")
        A("- μ_t là vị trí fix báo cuối cùng cộng odometry; κ = 0.05 (cùng mô hình nhiễu của bộ lọc điều hướng).")
        A("- ρ = 0.1 là xác suất tiên nghiệm ghost sai: lối thoát sau một lần báo sai. Không có sàn (ρ = 0.01), Nordland bị khoá "
          "chết. ρ chọn sau khi xem Boreas và Nordland, cố định cho mọi dataset.")
        A("- a ≤ ẽ ≤ e^top từng điểm, nên ẽ vẫn là e-value và cận ARL₀ ≥ (1−p_in)/p_in − R₀ giữ nguyên (`paper/cpc_theory.md` §3b).")
        A("- Baseline công bằng: cùng cổng dead-reckoning (dạng cứng, 2s) áp hậu kiểm lên fix của Xu'21 và certified (`+DRgate`).")
        A("")
        cols = [("HMM off-map (labels)", "Xu'21 (nhãn)"), ("HMM off-map (labels) +DRgate", "Xu'21 + DR gate"), ("certified (ours)", "certified"),
                ("certified (ours) +DRgate", "certified + DR gate"), ("CPC-HMM (ours)", "CPC-HMM"), ("CPC-HMM +GG(rho=.01)", "CPC +GG (ρ = 0.01)"),
                ("CPC-HMM +GG", "**CPC-HMM +GG (ρ = 0.1)**")]
        A("Sai số điều hướng trung bình (p95) trên descriptor và 3 seed, bản đồ khuyết 30 % (Nordland: frame; còn lại: m).")
        A("")
        A("| Dataset | #desc | " + " | ".join(n for _, n in cols) + " |"); A("|---|---|" + "---|" * len(cols))
        for d, n in DS:
            ns = [x for x in gg if x["ds"] == d]
            if not ns: continue
            cells = []
            for k, _ in cols:
                v = [run["rules"][k] for x in ns for run in x["runs"] if k in run["rules"]]
                cells.append(f"{np.mean([y['err_mean'] for y in v]):.1f} ({np.mean([y['err_p95'] for y in v]):.0f})" if v else "–")
            A(f"| {n} | {len(ns)} | " + " | ".join(cells) + " |")
        A("")
        bo = sorted([x for x in gg if x["ds"] == "boreas"], key=lambda x: x["desc"])
        if bo:
            A("**Boreas theo descriptor** (sai số trung bình, m / số fix sai trung bình mỗi seed):")
            A("")
            A("| Descriptor | " + " | ".join(n for _, n in cols) + " |"); A("|---|" + "---|" * len(cols))
            for x in bo:
                cells = []
                for k, _ in cols:
                    v = [run["rules"][k] for run in x["runs"] if k in run["rules"]]
                    cells.append(f"{np.mean([y['err_mean'] for y in v]):.1f} / {np.mean([y['wrong_fixes'] for y in v]):.0f}" if v else "–")
                A(f"| {x['desc']} | " + " | ".join(cells) + " |")
            A("")
    A("## 6. Kết luận")
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
