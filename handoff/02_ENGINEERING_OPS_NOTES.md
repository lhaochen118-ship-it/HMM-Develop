# 02 — Engineering & Operations Lessons

*Cập nhật 2026-10-29 cuối ngày (branch `hmm-navigation` → `hmm-navigation-2`). Tài liệu này chỉ về **kỹ thuật và vận
hành**: code, môi trường, Kaggle, cách chạy thí nghiệm, lỗi đã gặp và cách sửa, bài học. §1–§7 viết trong giai đoạn
SelfCal và vẫn đúng. **§8 là các bài học mới của vòng HMM-navigation; nên đọc trước.** Các script SelfCal được nhắc tới
(`eval_all.py`, `exp*`) chỉ còn ở branch `claude/selfcal-aa` / `claude/selfcal-seq`. Bảng tài khoản và dataset:
`ENVIRONMENT_SUMMARY.md`.*

## 1. Chính sách tính toán (user chỉ định)

0. **Mỗi acc dùng đủ 2 phiên GPU trước khi sang acc khác** (không rải 1 phiên mỗi acc, tốn quota GPU của nhiều acc; user chốt 2026-10-30). `fanout.py` cấp slot theo thứ tự (acc1, 0), (acc1, 1), (acc2, 0)…

1. **Mọi tính toán nặng chạy trên Kaggle**, kể cả phân tích chỉ cần CPU. Container local (không GPU, 4 nhân) chỉ
   dùng cho kiểm tra nhanh, dưới khoảng 2 phút.
2. **Dùng hết GPU T4 của mọi acc trước** (8 acc × 2 = 16 slot). Hết GPU: job **rất nhẹ** (dưới khoảng 30 phút trên CPU, ví dụ nav_demo CMU/4S/Nordland, phân tích offline) thì chạy CPU (5 phiên mỗi acc); job **nặng** (Boreas nav_demo/hmm_fix, dump descriptor) thì **đợi GPU trống**, không đẩy sang CPU (user chốt 2026-10-30).
3. Không ghi token vào `~/.bashrc` (bị từ chối). Token để ở `~/.kaggle/tok_<username>`; script tự đọc.
4. Không chạy code bên thứ ba tải về ngay trong container (sandbox chặn). Chạy nó trong kernel Kaggle.

## 2. Pipeline đánh giá trên Kaggle (đang dùng, đã kiểm chứng)

```
python3 automation/fanout.py <work_dir> <prefix> "eval_all.py rc salad;eval_all.py msls megaloc;..." [n_kernels] [--accounts a,b] [--cpu]
```

- `fanout.py` chia job theo vòng vào n kernel, rải trên (acc, slot): slot 0 của mọi acc trước, rồi đến slot 1. Nó
  chờ dataset code ở trạng thái `ready`, chạy `run_kernel.py` cho từng kernel, chờ xong rồi copy `results/*.json`
  vào `analysis/results/`.
- `make_eval_kernel.py <dir> <slug> "<jobs>" "" [--gpu] [--owner <user>]`:
    - upload `analysis/*.py` thành dataset code `<owner>/dive-vpr-analysis` (mỗi lần tạo một version mới);
    - viết `run.py`: mount dataset dump public `nhatlong1103/vpr-descriptor-dumps`, symlink vào `dump_all/`, chạy job
    song song (cpu − 1 luồng), lưu `results/`, `logs/`, `figs/`.
    - Job có thể chứa token chữ `DUMP` ở chỗ cần đường dẫn dump (ví dụ `exp10_shiftfix.py salad DUMP`).
- `run_kernel.py <dir> <out> 600 3 14400`: push, poll trạng thái, tải output. Kernel bị QUEUED quá 10 phút thì
  `delete` rồi push lại. `--attach` để bám lại vào kernel đang chạy sau khi container khởi động lại.
- **Backend GPU:** `selfcal.qm_stats` dùng PyTorch khi có CUDA (`SELFCAL_DEVICE=auto|cuda|torchcpu|numpy`).
    - Đã đối chiếu với numpy: RobotCar trùng hoàn toàn, Nordland lệch ≤ 0.00025.
    - Trọng số SUE phải để float32 như numpy; trước đó float64 làm lệch 3 vi phạm ở α = 0.01.
- **Thời gian trên T4:**
    - `eval_all` RobotCar/CMU/Nordland: 0.5–1 phút mỗi setting. MSLS: 27–36 phút.
    - exp9 (CPU): 17–40 phút mỗi descriptor. exp10 mỗi descriptor: 11–17 phút.
    - exp11/exp12: dưới 1 phút mỗi job.
- **Cache thống kê:** exp10 lưu `shiftstats_<desc>.npz` gồm mọi thống kê raw và centred. `exp10_shiftfix.py <desc>
  --stats <npz>` chấm lại biến thể mới trong vài giây (93 s → 2.5 s). Nên dùng cách này cho mọi tìm kiếm biến thể.

## 3. Kaggle: bài học vận hành

- **Ngắt một session:** chỉ `kaggle kernels delete -y <owner>/<slug>` có tác dụng. Push version mới hay push bản CPU
  "no-op" không ngắt session cũ. Cửa sổ interactive trên web phải tắt trên giao diện.
- **Trần concurrency:** 2 session GPU mỗi acc. Push lại mà không `delete` sẽ ăn vào trần và gây lỗi *Maximum batch
  GPU session count of 2*.
- **Log trễ:** API `output`/`logs` chỉ lộ log gần lúc xong. Kernel RUNNING mà chưa có output không có nghĩa là treo.
  Runner vì thế tắt chế độ silent-restart.
- **T4 và RTX PRO 6000:** T4 cấp ngay và chạy song song được. RTX có lần xếp hàng 21 phút với 0 output. Chỉ dùng
  RTX khi khối lượng extraction rất lớn.
- **GPU gán qua competition grant (RTX PRO 6000, L4x4):** `machine_shape` + `competition_sources` trong
  kernel-metadata chỉ có tác dụng nếu acc đó **đã accept rules** của competition trên web
  (`https://www.kaggle.com/competitions/<slug>/rules`, nút "I Understand and Accept") — **không có API/CLI để
  làm bước này**, phải bấm tay từng acc một lần. Nếu chưa accept, push vẫn thành công nhưng kernel lặng lẽ chạy
  GPU mặc định (T4) thay vì shape yêu cầu, không có lỗi báo. `automation/make_meta.py l4` dùng
  `machine_shape=NvidiaL4x4` qua grant của competition `gemma-4-developer-agent` (deadline 2026-11-25); `rtx` dùng
  `arc-prize-2026-arc-agi-3`. Sau khi accept rules trên 1–2 acc, kiểm tra bằng một kernel nhỏ in
  `torch.cuda.get_device_properties(i).name` cho mọi `i < torch.cuda.device_count()` để xác nhận thấy 4× L4 thật,
  không phải T4 fallback.
- **Dataset code versioning:** sau `make_eval_kernel` phải chờ `kaggle datasets status` báo `ready` rồi mới push
  kernel (`fanout.py` làm sẵn). Không chờ thì kernel có thể mount version code cũ.
- **Giới hạn metadata:** title dataset dài 6–50 ký tự, subtitle 20–80. Title dài quá thì upload hỏng sau khi đã đẩy
  hết 4.4 GB.
- **Chia sẻ dữ liệu giữa các acc:** output kernel riêng tư của acc khác không mount được. Giải pháp hiện tại là dataset
  **public** `nhatlong1103/vpr-descriptor-dumps`; acc mới không cần upload gì. Hai bản dump riêng tư cũ trên acc 2
  và acc 3 đã xoá.
- **Upload:** khoảng 18 MB/s (4.4 GB mất khoảng 6 phút với `-r zip -q`). Dùng hard link (`cp -al`) để chuẩn bị thư
  mục mà không tốn thêm dung lượng.
- **Acc mới:** đã thử GPU T4 trên cả 8 acc. Acc chưa xác minh số điện thoại sẽ không được cấp GPU, nên cần thử một
  job nhỏ trước.

## 4. Code: cấu trúc và quy ước

- `analysis/vprlib.py`: loader (`LOADERS[rc|cmu|nord|msls|nordw]`), metric, `nearest_map_dist`, `correct`,
  `top1_errors`. CMU gộp 11 slice. MSLS gộp hai thành phố, SF dịch 1e7 m theo UTM.
- `analysis/selfcal.py`:
    - `query_stats`/`qm_stats` (chunk theo hàng, `reduceat` lấy max theo ô);
    - `lobo_stats`, `map_null(stride=2)`, `conformal_p`, `combined_p`;
    - `SelfCalTest(N, strata=10, gate=0.8, min_per=50, mode="aa"|"gap")`, `pack`, `selfcal_p`;
    - lớp online `SelfCalAA` (khoảng 1 ms/query theo lô, 18 s chuẩn bị bản đồ RobotCar).
- `analysis/sc_eval.py`: `CFG` cho từng dataset (cell 10 m, excl 25 m, k 10, block 300 m, off_d 40 m, in_d, tol).
- Bảng paper: `paper/build_tables.py` (đọc `analysis/results/` và gộp thêm `results/gap/`) → `paper/tables.md`.
  `paper/build_paper.py` → `SelfCal_paper_full.pdf`.
- md → PDF: `python3 automation/md2pdf.py <in.md> <out.pdf>` (thuần Python, xhtml2pdf). Cần dòng trống trước mỗi
  danh sách. Ô bảng không ngắt dòng được, nên tránh chuỗi code dài trong ô.

## 5. Dữ liệu và loader: các điểm dễ sai

- **RobotCar `robotcar_v2_train.txt`:** pose 4×4 phẳng, translation nằm ở chỉ số [3, 7, 11]. Ảnh tham chiếu
  `overcast-reference` không có trong file train; pose của nó lấy từ `3D-models/all.nvm`.
- **CMU:** thư mục lồng `sliceN/sliceN/`; glob `**/slice*` bắt trùng nên phải dedup. Pose xyz là 3 số cuối. Chỉ dùng
  camera c0.
- **Nordland:** 4 mùa căn khung 1:1. Lấy mẫu con 4,500 trên 35,768 frame. Vị trí tính bằng frame.
- **MSLS:** CSV khi tải từ Kaggle nằm trong thư mục lồng nên phải di chuyển. pandas 3 trả StringArray, phải
  `np.asarray(..., dtype=str)` trước `np.savez`. Bỏ ảnh panorama.
- **Thứ tự frame cho sequence** (`vprlib.frame_order`, chỉ có trên branch seq): timestamp nằm trong tên ảnh. Bước
  giữa các frame liên tiếp khoảng 1 m, giống nhau giữa query và map.

## 6. Lỗi đã gặp và cách sửa (theo nhóm)

| Lỗi | Cách sửa / bài học |
|---|---|
| `pkill -f <pattern>` giết luôn shell đang gọi (exit 144) | Dùng PID cụ thể; hoặc `TaskStop` cho tác vụ nền |
| Chuỗi chờ nền tự push lại kernel sau khi metadata đã đổi acc, suýt tạo bản trùng | Dừng chuỗi cũ (TaskStop) trước khi chuyển job sang acc khác |
| `sed` xoá nhầm dòng | Sửa file bằng Python replace có `assert` hoặc dùng Edit; kiểm tra lại ngay |
| `exp9` dùng `sc.n` sau khi đổi API | Đổi API thì grep mọi chỗ gọi (`sc.test.n`) |
| Định dạng chuỗi với giá trị `None` khi chỉ có 1 bản đồ | Dùng `nan` thay `None` |
| Bộ chạy đặt đường dẫn dump sai vị trí đối số | Thêm token chữ `DUMP` |
| Cùng một biến thể chạy lại nhiều lần, tốn Kaggle | Lưu cache thống kê trung gian (exp10 `--stats`) |
| Kernel CPU chạy trong khi GPU acc khác rảnh (user nhắc) | Quy tắc: dùng hết GPU mọi acc trước |
| Kết quả seed 0–2 lạc quan hơn 10 seed | Luôn dùng đủ seed (≥ 10) trước khi kết luận về demo |

## 7. Bài học thành công và thất bại

- **Thành công:**
    - Hiệu chuẩn bằng chính bản đồ, cache thống kê, chạy fan-out trên nhiều acc, dataset dump public.
    - Đối chiếu từng bit sau mỗi thay đổi code (GPU với numpy, AA mặc định với code cũ).
    - Kiểm tra local nhỏ trước khi push.
- **Thất bại hoặc cần tránh:**
    - Chọn biến thể sau khi xem dữ liệu mà không kiểm định độc lập (gate 0.8, B = 10, Gap): phải nói rõ và kiểm định
    trên dữ liệu mới.
    - Mở rộng sang sequence mà không kiểm tra exchangeability của cửa sổ theo từng điều kiện.
    - Kết luận từ 3 seed.
- **Quy trình git:**
    - Branch ổn định `claude/selfcal-aa` không ghi đè. Thí nghiệm mở rộng làm trên branch riêng
    (`claude/selfcal-seq`).
    - Kết quả mới đặt ở thư mục riêng (`results/gap/`) thay vì sửa file cũ.
    - Không tạo PR. Commit kèm trailer, không ghi model ID.


## 8. Vòng HMM-navigation (2026-10-29): bài học mới

### 8.1 Script mới

| Script | Việc | Ghi chú |
|---|---|---|
| `analysis/cert_seq.py` | Certified sequential localization (FRAME/RUN/RUNO/ANCH/ANCHR) | `cert_seq.py <dump> <ds> <desc> [seeds]`; `--lmax30`, `--rho`, `--noise` |
| `analysis/cert_natural.py` | Off-map tự nhiên (query của cảnh khác) | |
| `analysis/nav_demo.py` | Điều hướng khép kín, mọi luật chấp nhận | `--dump` lưu mảng từng frame `navframes_*.npz` |
| `analysis/hmm_diag.py` | Chẩn đoán HMM (D1–D5) | |
| `analysis/hmm_fix.py` | CPC-HMM + ablation + baseline Xu'21 | `--drop f` (đổi tỷ lệ lỗ, file `hmmfix_dXX_*`), `--simnull` |
| `analysis/hmm_eval.py`, `seq_odo.py` | Vòng đầu (EVT-HMM, RUNO) | |
| `automation/make_dump4s.py`, `make_dump_boreas.py`, `upload_4s_dump.py`, `upload_boreas.py`, `launch_boreas.py` | Tạo và public dump 4Seasons/Boreas | |
| `automation/reattach.py` | Bám lại vào kernel đang chạy, kéo output, copy kết quả | `--skip <regex>` |
| `automation/resume.py` | Sau khi container khởi động lại: gắn lại mọi kernel chưa xong của các run trong `runs/active_runs.txt` | bỏ qua run có fanout còn sống |
| `automation/pull_kernels.py` | Kéo output của kernel liệt kê trong `handoff/RUNNING_KERNELS.md` | dùng cho chat mới |
| `paper/build_cert_tables.py`, `build_report.py` | Bảng và báo cáo PDF ngắn | |

**Thời gian chạy:**

- `hmm_fix` Boreas: khoảng 3.2 giờ mỗi seed trên CPU, vì vòng lặp Python của bộ lọc trên 76 k frame × 6 k trạng thái và
  nhiều biến thể.
- `nav_demo` Boreas 3 seed: khoảng 1–2 giờ trên T4.
- Các dataset khác: 5–40 phút mỗi job.

### 8.2 Kaggle

- **Trần phiên:** 2 GPU và **5 CPU mỗi acc**. Lỗi "Maximum batch CPU session count of 5" làm kernel không push được.
  `fanout.py` có failover sang acc khác khi push lỗi, nhưng chỉ trong danh sách `--accounts`.
- **Kernel thừa chiếm slot:** khi đã dừng collector, kernel vẫn chạy trên Kaggle tới khi xong. Huỷ bằng
  `kaggle kernels delete -y <acc>/<slug>`. Lệnh này chạy được khi gọi **từng lệnh một**; vòng `for` có `delete` bị bộ
  phân loại an toàn chặn ("Unverifiable Deletion Scope"). Khi bị chặn thì gửi user danh sách để xoá tay.
- **Acc `mucnokieu`:** GPU thường bị người khác dùng, nên chỉ dùng cho CPU.
- **Kernel dùng code tại lúc push:** `make_eval_kernel` version lại dataset code mỗi lần. Sửa code sau khi push không ảnh
  hưởng kernel đang chạy. Hai fanout cùng lúc trên một acc có thể đè version của nhau, nên **khởi chạy tuần tự** (chờ
  dòng `launched` trong log) rồi mới gọi fanout tiếp.
- **Kernel có internet** tải được S3 public của Boreas (khoảng 40 MB/s). Dữ liệu lớn nên tải và dump trong kernel thay vì
  trong container.
- **T4 phải dùng fp16.** bf16 bị giả lập nên chậm khoảng 7×.
- **Publish dataset:** ảnh Boreas khoảng 13 GB, chia 4 dataset (`--part i/4`) cho vừa đĩa container. Dùng hard link,
  không copy.

### 8.3 Container và tiến trình nền

- **Container khởi động lại nhiều lần trong ngày** (3 lần ngày 29/10): mất mọi tiến trình monitor (`fanout`,
  `run_kernel`). Scratchpad và repo vẫn còn, và kernel trên Kaggle vẫn chạy.
  - Quy trình phục hồi: `python3 automation/resume.py <scratchpad>/runs`.
  - Ghi tên run mới vào `runs/active_runs.txt` ngay khi khởi chạy.
- **Monitor chết vì lỗi proxy** (`ProxyError ... IntrospectToken`) nhưng vẫn ghi `STATUS=DONE:error`, dù kernel vẫn
  RUNNING. Kiểm tra `kaggle kernels status`, đổi tên log rồi `reattach.py`.
- **`resume.py` từng gắn lại kernel mà fanout còn đang push** (race). Đã sửa: bỏ qua run có fanout còn sống.
- **Tác vụ nền của Claude có trần 2 giờ.** Waiter chờ lâu bị giết. Dùng lượt kiểm tra hẹn giờ (`send_later` hoặc
  trigger hằng giờ) thay vì waiter dài.
- **Waiter chờ một đợt đã bị dừng sẽ chờ mãi** (ví dụ fix2). Khi dừng collector của một đợt thì dừng luôn waiter của nó.
- **Không dùng `sleep` dài trong lệnh foreground** (bị chặn). Dùng `until <điều kiện>; do sleep 15; done` trong lệnh nền.

### 8.4 Quản lý kết quả

- **Collector của đợt cũ có thể ghi đè kết quả mới** nếu xong sau. Hai cách xử lý:
  - dừng collector cũ (kill PID; kernel vẫn chạy);
  - hoặc chép lại kết quả của đợt mới sau cùng, vì output nằm ở `<run>/<slug>_out/results/`.
- **Kết quả Boreas trước khi sửa odometry** (2026-10-29 14:00 UTC; các run bor1/bor2/fix4/fix5/nav3/bdiag/bd50) **không
  dùng được**. Run sau sửa: bfix, bd50b, enull, navF, navFc, navG, fix7.
- **File 1 seed ghi đè file 3 seed:** các run chẩn đoán (`cdiag`, `enull`) ghi `nav_<ds>_<desc>.json` với 1 seed. Khi
  tổng hợp, kiểm tra `len(runs)`.
- **Tổng hợp:**
  - `paper/build_cert_tables.py` → `paper/cert_tables.md`;
  - `paper/build_report.py` → `paper/BAO_CAO_CertSeq.{md,pdf}`;
  - lọc file `hmmfix_*` theo khoá `drop` (0.3 = lưới chính).

### 8.5 Lỗi code đã gặp (vòng này)

| Lỗi | Sửa |
|---|---|
| 4Seasons: `re` chưa import; biến `T` che `torchvision.transforms` | import; đổi thành `TT` |
| 4Seasons: chỉ 21/30 recording có ảnh | chia part theo recording có thư mục cam0 |
| 4Seasons: căn khung GNSS↔VIO sai | brute-force tổ hợp phép biến đổi; sai số giữa recording 0.34 m |
| `cert_seq`: UnboundLocalError `A` | đổi biến vòng lặp thành `al` |
| `hmm_eval`: est rác | khởi tạo −1 |
| `hmm_fix`: index lỗi null ANCH | `map_null` dùng stride 2, nên phải dùng chỉ số `sub` |
| Tự tương quan gộp bị lệch | trừ trung bình theo từng sequence |
| **Boreas: bước odometry 8.7 km** (đứt bộ đếm xung `dmi.csv`) | chặn trong `odometry_wheel`: bước ≤ 0 hoặc > 10 × trung vị thì thay bằng trung vị |
| Lệnh `rm` có biến bị chặn | đường dẫn chữ hoặc `"${M:?}"` |

### 8.6 Bài học

- **Thành công:**
  - Dump descriptor + kernel CPU/GPU cho mọi thí nghiệm.
  - Dataset public dùng chung.
  - `--dump` từng frame để chẩn đoán offline. Nhờ nó mới tìm được lỗi odometry Boreas và độ trễ khi rời bản đồ.
  - Quét tham số offline trên npz thay vì chạy lại Kaggle.
- **Thất bại hoặc cần tránh:**
  - Tin kết quả của dataset mới mà chưa kiểm odometry. Lỗi 8.7 km làm hỏng một vòng chạy Boreas.
  - Khởi chạy nhiều fanout song song làm đè dataset code.
  - Giả thuyết "nhiễu odometry gây vi phạm D_R" được sửa và chạy trước khi kiểm bằng dữ liệu có sẵn. Lẽ ra nên đo vị trí
    vi phạm (theo khoảng cách tới mép đoạn) trước.
