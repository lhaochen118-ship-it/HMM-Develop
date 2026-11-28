# Hướng dẫn tận dụng GPU L4 x4

*Dự án HMM-based sequence visual localization. Nhánh `claude/nice-fermi-l7bzd6`, ngày 28/11/2026.*

*Nguồn: Operations Plan v1.3, §3.1–3.5; kinh nghiệm vận hành trên nhánh `hmm-2nd-idea` (`handoff/02_ENGINEERING_OPS_NOTES.md`, `automation/make_dump_nclt.py`, `make_eval_kernel.py`, `make_meta.py`); các lần chạy Kaggle của nhánh này (`research/reports/RUN_REPORT.md`).*

*Mức bằng chứng: [V] đo trên nhánh này; [R] ghi chép từ nhánh `hmm-2nd-idea`; [L] thông số nhà sản xuất hoặc tài liệu; [H] ước lượng, phải đo lại bằng smoke test.*

---

## 0. Tóm tắt một trang

1. **File metadata anh gửi không chứa cấu hình L4.**
    - Nội dung: `"accelerator": "none"`, `"isGpuEnabled": false`, `"isInternetEnabled": false`, `dockerImageVersionId` 28755, Python 3.6.6.
    - Đây là metadata của một notebook CPU mẫu.
    - Muốn có L4 x4 phải khai báo trong `kernel-metadata.json` khi đẩy bằng CLI (mục 1).
    - Trên nhánh `hmm-2nd-idea`, L4 chỉ cấp được qua competition grant. Theo Ops Plan, chỉ được gắn grant này khi điều khoản cuộc thi cho phép.
2. **"96 GB" là 4 vùng nhớ riêng, mỗi vùng 24 GB, nối với nhau qua PCIe (không có NVLink).**
    - Một batch không thể trải lên cả 4 GPU, trừ khi dùng DDP hoặc FSDP.
    - Với việc chính của dự án (trích descriptor, matching), cách nhanh nhất là **4 tiến trình độc lập, mỗi GPU một tiến trình, mỗi tiến trình một phần dữ liệu**.
    - Cách này tương đương "batch × 4" mà không tốn chi phí đồng bộ.
3. **Nút thắt thật là đọc và giải mã ảnh, không phải VRAM.**
    - Trên T4 ta chỉ đo được 2.7–19 ảnh/s [V], quá thấp so với sức tính của GPU.
    - Phải xử lý ba thứ trước khi tăng batch:
        - chép hoặc giải nén dữ liệu sang đĩa cục bộ;
        - đọc trước trọng số mạng một lần cho cả 4 tiến trình;
        - giải mã ảnh một lần rồi cho mọi model dùng chung (RAM 188 GB chứa được).
4. **Batch size chọn bằng dò tự động:**
    - tăng gấp đôi cho tới khi chạm 90% VRAM;
    - sau đó lấy batch **nhỏ nhất** đạt ≥ 97% throughput cao nhất;
    - batch lớn hơn mức bão hoà không nhanh hơn mà chỉ tăng rủi ro OOM.
5. **Chia việc theo hàng đợi chunk động** (work-stealing) thay vì chia cứng 4 phần. GPU nào xong trước thì lấy chunk tiếp theo. Cách này tự cân tải, chạy lại được khi lỗi, và vẫn đúng khi phiên chỉ cấp 1–2 GPU.
6. **HMM vẫn chạy trên CPU.**
    - Toàn bộ E18 (108 lần chạy) chỉ tốn 655 phút CPU-lõi [V], khoảng 11 giờ.
    - Chia cho 5 phiên CPU × 4 vCPU của một tài khoản [R], phần này mất khoảng 35 phút wall.
    - Không nên đốt hạn mức L4 cho HMM.
    - Chỉ tận dụng CPU rảnh của phiên L4 khi GPU đang chạy việc khác.
7. **Ngân sách.**
    - Một giờ L4 x4 trừ 4 GPU-giờ trong hạn mức 30 GPU-giờ/tuần/tài khoản [R], tức khoảng 7.5 giờ wall mỗi tuần mỗi tài khoản.
    - Vì vậy chỉ dùng L4 x4 khi việc chia được ≥ 4 phần và smoke test cho thấy cả 4 GPU bận ≥ 70% thời gian.

---

## 1. Metadata: anh gửi gì, cần gì

### 1.1. File `gpu_l4 - metadata.ipynb`

| Trường | Giá trị trong file | Ý nghĩa |
|---|---|---|
| `kaggle.accelerator` | `"none"` | Không có GPU |
| `kaggle.isGpuEnabled` | `false` | Không có GPU |
| `kaggle.isInternetEnabled` | `false` | Không có Internet; mọi thứ phải lấy từ dataset hoặc bundle |
| `kaggle.dockerImageVersionId` | `28755` | Image cũ (`language_info` ghi Python 3.6.6) |
| Cell duy nhất | Mẫu mặc định của Kaggle (liệt kê `/kaggle/input`) | Không có cấu hình phần cứng |

Kết luận: file này không cho biết cách xin L4.

Nếu anh tạo notebook trên web, chọn Accelerator "GPU L4 x4" trong Settings (tài khoản phải có quyền), lưu một phiên bản rồi tải `.ipynb` về, thì trường `accelerator` sẽ khác `"none"`. Anh gửi file đó, tôi sẽ đối chiếu.

Khi đẩy bằng CLI, thứ quyết định phần cứng là `kernel-metadata.json`, không phải metadata của file `.ipynb`.

### 1.2. `kernel-metadata.json` cho L4 x4 (mẫu từ `make_meta.py` nhánh `hmm-2nd-idea`) [R]

```json
{
  "id": "<account>/<slug>",  "title": "<slug>",  "code_file": "launcher.ipynb",
  "language": "python", "kernel_type": "notebook", "is_private": true,
  "enable_gpu": true, "enable_tpu": false, "enable_internet": false,
  "machine_shape": "NvidiaL4x4",
  "dataset_sources": ["<owner>/<feature-or-image-dataset>", "<owner>/<offline-bundle>"],
  "competition_sources": ["<chỉ điền khi điều khoản cuộc thi cho phép>"],
  "kernel_sources": [], "model_sources": []
}
```

Lưu ý bắt buộc:

- **Không có grant thì không có L4.**
    - Nhánh `hmm-2nd-idea` xin L4 bằng `machine_shape: "NvidiaL4x4"` cộng `competition_sources: ["gemma-4-developer-agent"]`, và mỗi tài khoản phải tự bấm chấp nhận luật cuộc thi trên web.
    - Không có grant thì Kaggle **âm thầm** cấp GPU mặc định, không báo lỗi [R].
    - Nhánh này đã gặp đúng chuyện đó: kernel k07 xin `NvidiaL4` không kèm grant và bị hạ xuống T4 [V].
- **Tuân thủ.**
    - Ops Plan §2 và §3.4: "Không dùng tài khoản hoặc nguồn competition để né giới hạn; chỉ gắn competition khi job thật sự được phép theo điều khoản của nguồn đó."
    - Việc gắn grant cho job nghiên cứu HMM là quyết định của anh hoặc lab sau khi đọc luật cuộc thi.
    - Tôi **không** tự gắn grant khi chưa được anh xác nhận.
- **Kiểm tra cấp phát ở cell đầu.**
    - Cell đầu luôn in số GPU, tên GPU, VRAM, vCPU, RAM và dung lượng đĩa.
    - Nếu phần cứng thực tế khác phần cứng đã xin, code tự tính lại số shard, batch và ngân sách (mục 3.1).
- **Tài khoản.** Danh sách tài khoản lab đã có quyền L4 nằm trong `handoff/02` của nhánh `hmm-2nd-idea` (cập nhật 05/11/2026). Một tài khoản chỉ có T4 mà nhận kernel L4 thì chạy rất chậm [R], nên phải dựng lại kernel đó trên tài khoản có L4.

---

## 2. Phần cứng một phiên L4 x4 và hệ quả

| Thành phần | Giá trị | Hệ quả thiết kế |
|---|---|---|
| GPU | 4 × NVIDIA L4 (Ada, sm_89), 24 GB GDDR6 mỗi GPU (~23 GB dùng được) [R][L] | 4 tiến trình, mỗi GPU một tiến trình |
| Tính toán / GPU | FP16/BF16 tensor ≈ 121 TFLOPS dense, gấp khoảng 2× T4 (65 TFLOPS FP16); **có BF16**, T4 thì không [L] | Dùng BF16 autocast; kiểm tra độ lệch so với FP32 |
| Băng thông VRAM | ≈ 300 GB/s, gần bằng T4 (320 GB/s) [L] | Model nhỏ bị giới hạn bởi băng thông và input, không phải FLOPS |
| Kết nối giữa các GPU | PCIe, **không NVLink** [L] | DDP hoặc model-parallel tốn phí all-reduce; với suy luận thì tránh |
| CPU / RAM | 48 vCPU, ≈ 188 GB RAM [R] | Khoảng 10 DataLoader worker mỗi GPU; cache ảnh đã giải mã trong RAM |
| Đầu vào | `/kaggle/input` là ổ mạng, chậm khi nhiều tiến trình cùng đọc [R] | Stage-in sang đĩa cục bộ; đọc trước trọng số |
| Đầu ra | `/kaggle/working` tối đa 20 GB, được giữ lại | Gói một file `.tar`, tránh hàng nghìn file nhỏ |
| Hạn mức | 2 phiên GPU/tài khoản; 30 GPU-giờ/tuần; L4 x4 tính 4 GPU-giờ cho mỗi giờ [R] | Phải giữ cả 4 GPU luôn bận |

Ba bài học đo được trên nhánh `hmm-2nd-idea` [R]:

- `torch.hub` chép checkpoint từ `/kaggle/input` với tốc độ khoảng 1 MB/s, mỗi worker chép lại một lần (DINOv2 mất khoảng 15 phút). Cách sửa: tạo symlink checkpoint vào `~/.cache/torch/hub/checkpoints` trước khi chạy.
- 4 worker cùng đọc trọng số từ ổ mạng mất khoảng 490 s mỗi worker, trong khi phần trích xuất chỉ mất khoảng 30 s. Cách sửa: tiến trình cha đọc mọi file trọng số **một lần** bằng 16 luồng vào page cache.
- Kernel Kaggle chạy dưới dạng notebook đã chuyển đổi, nên phải **ghi `worker.py` ra file rồi `subprocess.Popen`**, không dùng `multiprocessing` fork trong notebook.

---

## 3. Chọn chiến lược theo loại việc

| Loại việc trong dự án | Chiến lược | Không nên |
|---|---|---|
| A. Trích descriptor (NetVLAD, CosPlace, SALAD, MegaLoc, JIST, SeqVLAD…) trên nhiều dataset | **Data-parallel bằng tiến trình độc lập**: hàng đợi chunk, 4 worker, giải mã một lần cho N model, ghép theo ID | `nn.DataParallel` (một tiến trình, nghẽn GIL, GPU0 quá tải); DDP (không có gradient nên không cần đồng bộ) |
| B. Matching / 6DoF (SuperPoint + LightGlue + PnP, k05/k11) và hình học (k09) | 3 tầng nối ống: keypoint (chia theo ảnh) → matching (chia theo query, cân bằng theo số cặp) → RANSAC/PnP trên pool CPU chạy song song | Chạy PnP tuần tự sau khi GPU xong (GPU ngồi chờ) |
| C. Nhiều job nhỏ độc lập (JIST/SeqVLAD từng dataset, ablation) | `CUDA_VISIBLE_DEVICES = i % NG`; nhiều job trên một GPU nếu mỗi job dùng < 25% GPU | Giả định luôn có 4 GPU |
| D. Training (chưa có trong kế hoạch hiện tại; emission là logistic chạy trên CPU) | DDP qua `torchrun --nproc_per_node=NG`, batch toàn cục = NG × batch mỗi GPU; FSDP chỉ khi model + optimizer > ~20 GB mỗi GPU | FSDP cho suy luận |
| E. HMM trên feature bank (E18, e15, MSLS) | CPU vector hoá, chạy song song `--par` trên phiên CPU (không tốn hạn mức GPU) | Mở L4 x4 chỉ để làm máy 48 lõi, trừ khi rất gấp |

"Dùng hết 96 GB để có batch lớn" chỉ có nghĩa thực ở loại D (DDP: 4 × batch mỗi GPU).

Ở loại A và B, descriptor của từng ảnh không phụ thuộc batch (BN ở chế độ eval). 4 tiến trình độc lập **đã là** batch × 4. Phần VRAM còn dư nên dùng để chạy nhiều model cùng lúc trên một batch đã giải mã.

---

## 4. Kiến trúc chuẩn "một phiên = 4 GPU bận"

```
Tiến trình cha (launcher, trong notebook)
 ├─ S0 probe: số GPU/VRAM/vCPU/RAM/đĩa, in "requested vs actual"
 ├─ S1 stage-in: giải nén ảnh vào đĩa cục bộ, đọc trước trọng số (16 luồng), symlink hub cache
 ├─ S2 manifest: danh sách task → chunk (mỗi chunk 2–5 phút GPU), ghi queue/ + manifest.json
 ├─ S3 spawn: NG tiến trình GPU (CUDA_VISIBLE_DEVICES=i) + pool CPU (PnP/RANSAC/HMM nếu có)
 ├─ S4 giám sát: heartbeat 60 s, nvidia-smi 30 s, thu hồi chunk của worker chết
 ├─ S5 merge + validate: theo ID, đủ/không trùng/hữu hạn/chuẩn L2, SHA-256
 └─ S6 đóng gói: dump.tar + manifest.json + log + gpu_util.csv → /kaggle/working
Tiến trình GPU i (worker.py)
 ├─ nạp model một lần, BF16 autocast, cudnn.benchmark, channels_last (CNN)
 ├─ dò batch (chỉ ở chunk đầu), kiểm tra precision BF16 so với FP32 (256 ảnh)
 └─ vòng lặp: nhận chunk → DataLoader → mọi model → ghi part (atomic) → đánh dấu done → heartbeat
```

### 4.1. S0: dò phần cứng và thích nghi

```python
def probe_hardware(requested_gpus=4):
    NG   = torch.cuda.device_count()
    gpus = [(torch.cuda.get_device_name(i),
             torch.cuda.get_device_properties(i).total_memory / 2**30) for i in range(NG)]
    ncpu = os.cpu_count(); ram = psutil.virtual_memory().total / 2**30
    disk = shutil.disk_usage("/kaggle/working").free / 2**30
    print(f"python {sys.version.split()[0]} torch {torch.__version__} cuda {torch.version.cuda}")
    print(f"requested {requested_gpus}xL4 | actual {NG} x {gpus} | vCPU {ncpu} | RAM {ram:.0f} GB | disk {disk:.0f} GB")
    bf16 = NG > 0 and torch.cuda.is_bf16_supported()      # L4: True, T4: False
    if NG < requested_gpus:
        log_event("tier_mismatch", requested=requested_gpus, actual=NG)  # ghi vào manifest, không dừng
    if NG == 0 and not ALLOW_CPU_FALLBACK:
        sys.exit("no GPU: stop (khong chay extraction tren CPU)")
    return dict(NG=max(NG, 1), ncpu=ncpu, ram_gb=ram,
                amp=torch.bfloat16 if bf16 else torch.float16,
                vram_gb=min(g[1] for g in gpus) if gpus else 0)
```

### 4.2. S1: stage-in (bước quyết định tốc độ)

```python
def stage_in(hw, local="/kaggle/tmp"):
    # (a) ảnh: giải nén tar trong dataset ra đĩa cục bộ, nhiều tar thì giải nén song song
    tars = glob("/kaggle/input/**/img_*.tar", recursive=True)
    with ThreadPoolExecutor(8) as ex: list(ex.map(lambda t: untar(t, local), tars))
    # (b) checkpoint: symlink vào hub cache để torch.hub không chép 1 MB/s cho mỗi worker
    hub = os.path.expanduser("~/.cache/torch/hub/checkpoints"); os.makedirs(hub, exist_ok=True)
    for f in glob("/kaggle/input/**/checkpoints/*", recursive=True):
        dst = os.path.join(hub, os.path.basename(f))
        if not os.path.exists(dst): os.symlink(f, dst)
    # (c) đọc trước MỌI file trọng số một lần vào page cache (16 luồng, khối 64 MB)
    wf = [f for f in glob("/kaggle/input/**/*", recursive=True)
          if f.endswith((".pth", ".pt", ".ckpt", ".bin", ".safetensors", ".pth.tar"))]
    def _rd(f):
        with open(f, "rb") as h:
            while h.read(64 << 20): pass
        return os.path.getsize(f)
    t = time.time(); nb = sum(ThreadPoolExecutor(16).map(_rd, wf))
    print(f"weights pre-read {len(wf)} files {nb/1e9:.2f} GB in {time.time()-t:.0f}s")
```

### 4.3. S2: manifest và hàng đợi chunk động

Chia cứng `rows i::NG` (cách của `make_dump_nclt.py`) dùng tốt khi mọi ảnh giống nhau và chỉ có một dataset. Khi có nhiều task khác cỡ (nhiều dataset, cặp matching có số keypoint khác nhau), dùng hàng đợi chunk:

```python
def build_queue(tasks, chunk_sec=180, est_ips=60):
    """tasks: [{task_id, kind, dataset, ids:[...], paths:[...], models:[...]}]"""
    os.makedirs("queue/todo"); os.makedirs("queue/claimed"); os.makedirs("queue/done")
    manifest = {"run_id": RUN_ID, "created": now(), "tasks": {}, "chunks": []}
    for t in tasks:
        n = len(t["ids"]); per = max(64, int(chunk_sec * est_ips / max(1, len(t["models"]))))
        manifest["tasks"][t["task_id"]] = {"n": n, "ids_sha": sha256(t["ids"])}
        for c, s in enumerate(range(0, n, per)):
            ch = {"chunk": f"{t['task_id']}__{c:05d}", "task_id": t["task_id"], "rows": [s, min(n, s + per)]}
            manifest["chunks"].append(ch); write_json(f"queue/todo/{ch['chunk']}.json", ch)
    # LPT: chunk lớn hoặc chậm (model nặng, ảnh to) lên đầu hàng để tránh đuôi dài
    manifest["chunks"].sort(key=lambda c: -est_cost(c))
    write_json("manifest.json", manifest); return manifest

def claim_next(worker):
    for f in sorted(os.listdir("queue/todo")):           # sắp theo chi phí (tiền tố ưu tiên)
        try:
            os.rename(f"queue/todo/{f}", f"queue/claimed/{worker}__{f}")   # atomic: chỉ 1 worker thắng
            return read_json(f"queue/claimed/{worker}__{f}")
        except FileNotFoundError:
            continue                                      # worker khác đã lấy, thử chunk sau
    return None
```

Lợi ích của hàng đợi động:

- GPU nhanh làm nhiều hơn.
- Worker chết thì chunk được trả lại hàng đợi.
- Chạy lại phiên thì chunk đã có `done/` được bỏ qua.
- Phiên chỉ có 2 GPU vẫn đúng.

### 4.4. S3: khởi chạy worker (không dùng fork trong notebook)

```python
def spawn_workers(hw, cpu_for_side_jobs=0):
    NG = hw["NG"]
    cpu_gpu = (hw["ncpu"] - cpu_for_side_jobs) // NG       # 48 vCPU, 4 GPU → 12; trừ 2 cho main → nw=10
    open("/kaggle/tmp/worker.py", "w").write(WORKER_SRC)
    procs = []
    for i in range(NG):
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(i), WORKER=str(i), NG=str(NG),
                   NUM_WORKERS=str(max(2, cpu_gpu - 2)),
                   OMP_NUM_THREADS="2", MKL_NUM_THREADS="2",   # chống tranh chấp luồng giữa 4 tiến trình
                   PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
        procs.append(subprocess.Popen([sys.executable, "/kaggle/tmp/worker.py"], env=env,
                     stdout=open(f"/kaggle/working/logs/worker{i}.log", "w"), stderr=subprocess.STDOUT))
    return procs
```

### 4.5. Worker: vòng lặp chính

```python
# worker.py: một GPU, nhìn thấy đúng 1 thiết bị cuda:0
torch.backends.cudnn.benchmark = True                    # kích thước ảnh cố định cho mỗi model
torch.backends.cuda.matmul.allow_tf32 = True; torch.backends.cudnn.allow_tf32 = True
dev = "cuda:0"; WK = int(os.environ["WORKER"])
MODELS = {name: build_model(name).eval().to(dev) for name in MODEL_LIST}   # nạp MỘT lần
for m in MODELS.values():
    if is_cnn(m): m.to(memory_format=torch.channels_last)
AMP = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16

BS = None
while (ch := claim_next(f"w{WK}")) is not None:
    if os.path.exists(f"queue/done/{ch['chunk']}"): continue       # resume
    task = TASKS[ch["task_id"]]; s, e = ch["rows"]
    ids, paths = task["ids"][s:e], task["paths"][s:e]
    if BS is None:                                                   # chỉ làm ở chunk đầu
        BS = probe_batch(MODELS, task, dev, AMP)                    # mục 5.1
        PREC = precision_check(MODELS, paths[:256], dev, AMP)       # mục 5.2 → AMP hoặc FP32
    dl = make_loader(paths, BS, task)                                # mục 5.3
    out = {n: np.empty((len(ids), MODELS[n].dim), np.float16) for n in MODELS}
    t0 = time.time(); k = 0
    with torch.inference_mode():
        for x_u8, idx in dl:                       # x_u8: uint8 NCHW đã giải mã ở độ phân giải gốc chung
            x_u8 = x_u8.to(dev, non_blocking=True)
            for n, m in MODELS.items():            # giải mã một lần, N model dùng chung
                x = preprocess_gpu(x_u8, m.size, m.mean, m.std)   # resize + chuẩn hoá trên GPU
                with torch.autocast("cuda", dtype=PREC[n], enabled=PREC[n] != torch.float32):
                    y = m(x)
                out[n][idx.numpy()] = F.normalize(y.float(), dim=1).cpu().numpy().astype(np.float16)
            k += len(idx); heartbeat(WK, ch, k, len(ids), k / (time.time() - t0))
    for n in out: assert np.isfinite(out[n].astype(np.float32)).all()
    save_atomic(f"parts/{ch['chunk']}.npz", ids=np.array(ids), rows=np.arange(s, e), **out)
    touch(f"queue/done/{ch['chunk']}")
```

Ghi chú:

- `save_atomic` ghi ra `*.tmp` rồi `os.replace`, nên chunk dang dở không bao giờ bị coi là xong.
- Đầu ra là FP16 đã chuẩn hoá L2, giống feature bank hiện tại (`hmmloc/data.py`).

---

## 5. Batch size, precision, input pipeline

### 5.1. Dò batch: tăng gấp đôi tới 90% VRAM, rồi chọn batch nhỏ nhất đã bão hoà

```python
def probe_batch(models, task, dev, amp, start=16, cap=1024, headroom=0.10, warm=2, rep=3):
    total = torch.cuda.get_device_properties(dev).total_memory
    H, W = task["decode_size"]; res = {}; bs = start
    while bs <= cap:
        try:
            torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(dev)
            x = torch.randint(0, 255, (bs, 3, H, W), dtype=torch.uint8, device=dev)
            run = lambda: [m(preprocess_gpu(x, m.size, m.mean, m.std)) for m in models.values()]
            with torch.inference_mode(), torch.autocast("cuda", dtype=amp):
                for _ in range(warm): run()
                torch.cuda.synchronize(); t = time.perf_counter()
                for _ in range(rep): run()
                torch.cuda.synchronize()
            ips = rep * bs / (time.perf_counter() - t)
            peak = torch.cuda.max_memory_reserved(dev)       # reserved, đã tính phân mảnh
            if peak > (1 - headroom) * total: break         # chừa 10% VRAM (Ops Plan §3.2)
            res[bs] = ips; bs *= 2
        except torch.cuda.OutOfMemoryError:
            break
    best = max(res.values())
    bs_opt = min(b for b, v in res.items() if v >= 0.97 * best)   # nhỏ nhất đạt 97% đỉnh
    log_event("batch_probe", table=res, chosen=bs_opt); return bs_opt
```

Ghi chú:

- Bảng `res` (batch → ảnh/s) được ghi vào manifest. Đó là bằng chứng batch được chọn theo đo đạc, không phải đoán.
- Với ViT (DINOv2, SALAD, MegaLoc), kiểm tra PyTorch dùng `scaled_dot_product_attention` (flash hoặc mem-efficient trên sm_89).
- `torch.compile` chỉ bật khi mỗi worker có > ~30 phút GPU. Thời gian biên dịch (1–3 phút mỗi model, nhân 4 tiến trình) phải được bù lại [H]. Nếu bật thì đệm batch cuối cho đủ kích thước để tránh biên dịch lại.

### 5.2. Kiểm tra precision (bắt buộc trước khi chạy dài)

```python
def precision_check(models, paths256, dev, amp, cos_min=0.999, top1_min=0.995):
    x = load_batch(paths256).to(dev); prec = {}
    for n, m in models.items():
        with torch.inference_mode():
            y32 = F.normalize(m(preprocess_gpu(x, m.size, m.mean, m.std)).float(), dim=1)
            with torch.autocast("cuda", dtype=amp):
                ylo = F.normalize(m(preprocess_gpu(x, m.size, m.mean, m.std)).float(), dim=1)
        cos = (y32 * ylo).sum(1)                                    # độ lệch từng ảnh
        top1 = (torch.argmax(y32 @ REF32[n].T, 1) == torch.argmax(ylo @ REF32[n].T, 1)).float().mean()
        prec[n] = amp if (cos.min() >= cos_min and top1 >= top1_min) else torch.float32
        log_event("precision", model=n, cos_min=float(cos.min()), top1_agree=float(top1), use=str(prec[n]))
    return prec
```

Ghi chú:

- `REF32[n]` là descriptor FP32 của một tập database nhỏ (calibration), tính ngay trong worker.
- Bước này cũng là **kiểm tra tiền xử lý**: so `preprocess_gpu` với pipeline tham chiếu PIL hoặc torchvision trên CPU (cos ≥ 0.999).
- Lỗi A28 (JIST bị trích ở 384×384 thay vì 480×640) chính là lỗi tiền xử lý. Mỗi model phải khai báo `size`, `mean`, `std` và cách resize đúng như repo gốc.

### 5.3. Input pipeline: ba mức, chọn mức thấp nhất đủ nuôi GPU

| Mức | Cách làm | Khi nào |
|---|---|---|
| P1 | `DataLoader(num_workers=10, pin_memory=True, persistent_workers=True, prefetch_factor=4)`, đọc từ **đĩa cục bộ**, `worker_init_fn` đặt `torch.set_num_threads(1)`, `cv2.setNumThreads(0)` | Mặc định |
| P2 | Worker CPU chỉ đọc **bytes** JPEG, giải mã theo batch trên GPU bằng `torchvision.io.decode_jpeg(list_bytes, device="cuda")` (nvJPEG), resize trên GPU | Dataset JPEG (RobotCar, CMU, MSLS) khi P1 vẫn dưới 70% util; PNG (Nordland, 4Seasons) thì vẫn giải mã trên CPU |
| P3 | **Giải mã một lần vào RAM**: mảng `uint8 [N,H,W,3]` trong shared memory hoặc memmap trên đĩa cục bộ, mọi model và mọi lần chạy đọc lại | Nhiều model trên cùng dataset. Ví dụ 10 000 ảnh 480×640 chỉ chiếm khoảng 9.2 GB, vừa RAM 188 GB |

```python
def make_loader(paths, bs, task):
    ds = DecodeDataset(paths, decode_size=task["decode_size"])     # trả về uint8 CHW, chưa chuẩn hoá
    return DataLoader(ds, batch_size=bs, shuffle=False, num_workers=NUM_WORKERS,
                      pin_memory=True, persistent_workers=True, prefetch_factor=4,
                      worker_init_fn=lambda _: (torch.set_num_threads(1), cv2.setNumThreads(0)))

def preprocess_gpu(x_u8, size, mean, std):          # x_u8 trên GPU
    x = x_u8.float().div_(255)
    if x.shape[-2:] != size: x = F.interpolate(x, size=size, mode="bilinear", antialias=True, align_corners=False)
    return ((x - mean) / std).contiguous(memory_format=torch.channels_last)
```

Gửi `uint8` lên GPU rồi mới chuyển sang float và chuẩn hoá. Lượng dữ liệu đi qua PCIe giảm 4 lần so với gửi float32.

---

## 6. Matching và 6DoF (k05/k11) và hình học (k09): ống 3 tầng

```python
# Tầng M1 (GPU, chia theo ẢNH): SuperPoint một lần cho mỗi ảnh xuất hiện trong các cặp
imgs = unique(pairs.query) ∪ unique(pairs.db)
queue_chunks(imgs, task="sp")              # worker: keypoint top-K=2048, desc FP16 → parts/sp_*.npz

# Tầng M2 (GPU, chia theo QUERY, LPT theo số cặp × K): LightGlue
#   nạp feature của shard vào RAM; cắt mọi ảnh về đúng K keypoint để batch được B cặp một lần;
#   nếu bản LightGlue không hỗ trợ batch có mask, chạy 2 tiến trình mỗi GPU (mỗi tiến trình bs=1).
for chunk in claim_loop("lg"):
    for batch in batched(chunk.pairs, B):
        m = lightglue(feats[batch.q], feats[batch.d])           # flash attention, early-stop mặc định
        cpu_q.put((batch.ids, m.cpu()))                         # đẩy sang tầng M3, GPU không chờ

# Tầng M3 (CPU pool ~36 tiến trình, chạy SONG SONG với M2): RANSAC/PnP/MAGSAC
with ProcessPoolExecutor(36) as ex:
    for ids, m in iter(cpu_q.get, None):
        ex.submit(pnp_or_fundamental, ids, m)       # k09: cv2 MAGSAC + try/except (A29) → 0 inlier
```

Ý chính:

- Tầng M1 và M2 không lặp keypoint: mỗi ảnh chỉ trích một lần, dù nằm trong nhiều cặp.
- Tầng M3 dùng 36 lõi CPU trong lúc GPU chạy tầng M2.
- Với k09, phần nặng là MAGSAC trên CPU, nên 48 vCPU của phiên L4 có ích thật.

---

## 7. Giám sát, merge, đóng gói

### 7.1. Giám sát trong phiên (tiến trình cha)

```python
while any(p.poll() is None for p in procs):
    time.sleep(60)
    util = nvidia_smi("utilization.gpu,memory.used")             # ghi gpu_util.csv mỗi 30–60 s
    hb = [read_json(f"hb/w{i}.json") for i in range(NG)]          # run_id, chunk, done/total, ips, eta
    print(fmt(time.time() - T0, util, hb), flush=True)            # 1 dòng/phút; không bao giờ in secret
    for i, p in enumerate(procs):
        if p.poll() not in (None, 0):                             # worker chết: trả chunk về hàng đợi
            for f in glob(f"queue/claimed/w{i}__*"):
                if not os.path.exists("queue/done/" + chunk_of(f)): os.rename(f, "queue/todo/" + chunk_of(f))
            procs[i] = respawn(i)                                  # tối đa 2 lần mỗi GPU, sau đó bỏ GPU đó
```

### 7.2. Merge có kiểm tra (S5)

```python
def merge(manifest):
    for tid, t in manifest["tasks"].items():
        n = t["n"]; cover = np.zeros(n, np.int32); out = {}
        for f in sorted(glob(f"parts/{tid}__*.npz")):
            z = np.load(f); r = z["rows"]; cover[r] += 1
            for m in MODEL_LIST:
                out.setdefault(m, np.empty((n, z[m].shape[1]), np.float16))[r] = z[m]
        assert (cover == 1).all(), f"{tid}: missing={int((cover==0).sum())} dup={int((cover>1).sum())}"
        assert sha256(concat_ids_in_order(tid)) == t["ids_sha"]          # đúng thứ tự ID gốc
        for m, X in out.items():
            Xf = X.astype(np.float32); nrm = np.linalg.norm(Xf, axis=1)
            assert np.isfinite(Xf).all() and np.abs(nrm - 1).max() < 1e-2
            np.save(f"dump/{m}/{tid}.npy", X)
            manifest["outputs"][f"{m}/{tid}"] = {"n": n, "dim": X.shape[1], "dtype": "float16",
                "sha256": sha256_file(f"dump/{m}/{tid}.npy"), "precision": PREC_USED[m],
                "batch": BS_USED[m], "gpu": GPU_NAME, "img_per_s": IPS[m]}
    subprocess.run(["tar", "-cf", "/kaggle/working/dump.tar", "dump", "manifest.json", "logs", "gpu_util.csv"])
```

Sau khi kéo `dump.tar` về:

- Kiểm tra lại SHA-256 từ manifest.
- Ghi một hàng `research/registry/runs.jsonl` cho mỗi output, theo đúng evidence policy.

### 7.3. Giám sát từ ngoài (máy điều phối, một monitor duy nhất vì API giới hạn theo IP)

| Trạng thái | Ngưỡng | Hành động |
|---|---|---|
| Queued, chưa có output | L4: 8 phút; T4: 10 phút; CPU: 5 phút | Xoá kernel, đẩy lại (≤ 5 lần, có backoff). Vẫn kẹt thì chuyển sang T4. Code tự thích nghi nhờ mục 4.1 |
| Running, không có log mới | > 2 chu kỳ heartbeat (> 2–4 phút) | Đọc log và checkpoint. Chưa chắc là treo thì không huỷ |
| Lỗi xác thực hoặc hạn mức | Ngay khi thấy | Không retry mù. Chuyển tài khoản (nếu được phép) hoặc đưa việc vào danh sách chờ |
| Hoàn tất | — | Kéo output có chọn lọc (`--pull-pattern`, tránh lỗi 429), kiểm tra manifest, ghi registry |

CLI Kaggle 2.2.5 không có lệnh huỷ kernel. Muốn dừng, phải xoá kernel hoặc đẩy phiên bản mới. Vì vậy smoke test phải ngắn.

---

## 8. Áp dụng cho việc đang chờ của dự án

| Việc (STATE.md) | Thiết kế trên L4 x4 | Tại sao |
|---|---|---|
| k11 6DoF còn lại (cmu1, cmu2, 4s, 4s3) | **Một phiên**: hàng đợi gồm 4 cảnh, ống M1→M2→M3 (mục 6); PnP trên 36 lõi CPU | Bốn cảnh độc lập, vừa đủ 4 GPU. Chạy tuần tự trên T4 thì mất 4 lần thời gian một cảnh (k05 v2 RobotCar mất 19.5 phút trên T4 [V]) |
| k12 SeqVLAD cmu | Thêm vào **cùng hàng đợi** của phiên trên (chunk nhỏ, GPU nào rảnh thì làm) | Lấp chỗ trống ở cuối phiên, không mở phiên riêng |
| k09 hình học (chạy lại vì A29) | GPU: keypoint và match; CPU: MAGSAC (36–40 lõi) | Nặng phần CPU, hợp với 48 vCPU |
| CaseVPR hoặc descriptor mới (khi có trọng số) | Mục 4–5: một lượt giải mã, N model, 6 dataset trong một hàng đợi | Chi phí giải mã chỉ trả một lần |
| e15 vmodels, MSLS e07, HMM | **Phiên CPU**, `--par` theo số lõi; không dùng L4 | 655 phút CPU cho toàn bộ E18 [V]; không đáng 4 GPU-giờ/giờ |

Ước lượng [H], phải xác nhận bằng smoke test:

- Phiên k11 + k12 trên L4 x4 mất khoảng 25–40 phút wall, tương đương 1.7–2.7 GPU-giờ.
- Chạy tuần tự trên T4 thì mất khoảng 100+ phút wall.
- Lợi ích chính là **wall-clock và số lần đẩy kernel**, không phải tiết kiệm GPU-giờ.

---

## 9. Checklist trước khi đẩy một phiên L4 x4

1. Người dùng đã xác nhận được phép gắn competition grant cho job này. Tài khoản đã chấp nhận luật cuộc thi.
2. `python3 tests/test_hmm_core.py` pass (Gate G0) với việc có phụ thuộc HMM.
3. Mã đã chạy được trên **T4 (rẻ)** với `SMOKE=1` (khoảng 2% mỗi task, ≤ 10 phút): merge OK, manifest OK.
4. Smoke ngắn trên L4 x4 (≤ 10 phút ≈ 0.7 GPU-giờ). Ghi lại:
    - NG thực tế, VRAM;
    - bảng dò batch, kết quả kiểm tra precision;
    - ảnh/s trên mỗi GPU;
    - **util trung bình của từng GPU**.
5. Dưới 70% util thì sửa input pipeline (P1 → P2/P3) **trước** khi chạy đầy đủ. Không tăng batch để chữa.
6. Ước lượng wall = tổng chi phí chunk / (NG × ảnh/s thực tế), cộng 30% biên an toàn. GPU-giờ = 4 × wall. So với hạn mức còn lại của tài khoản.
7. Output là một file `tar` < 20 GB, có manifest và SHA-256. Không ghi token hoặc secret vào log hay output.
8. Sau khi xong: ghi registry, cập nhật STATE, FINDINGS, ISSUES; ghi util thực tế để hiệu chỉnh lần sau.

---

## 10. Sai lầm thường gặp (đều đã xảy ra hoặc suýt xảy ra)

| Sai lầm | Hậu quả | Cách tránh |
|---|---|---|
| Xin `NvidiaL4` mà không có grant | Âm thầm nhận T4 (k07) [V] | Cell đầu in "requested vs actual"; code tự thích nghi |
| 4 worker cùng đọc trọng số hoặc chép hub từ `/kaggle/input` | Mất khoảng 490 s mỗi worker; DINOv2 mất 15 phút [R] | Đọc trước bằng 16 luồng; symlink hub |
| `nn.DataParallel` hoặc DDP cho suy luận | Nghẽn GPU0 hoặc phí đồng bộ vô ích | 4 tiến trình độc lập |
| Mỗi tiến trình 48 luồng OMP | Tranh chấp CPU, chậm hơn | `OMP_NUM_THREADS=2` mỗi tiến trình GPU; 1 luồng mỗi DataLoader worker |
| Tăng batch khi GPU đói dữ liệu | Không nhanh hơn, dễ OOM | Đo util; sửa pipeline (mục 5.3) |
| FP16 trên T4 với ViT | Có thể tràn số ở LayerNorm hoặc attention | L4 dùng BF16; luôn chạy `precision_check` |
| Resize trên GPU khác pipeline gốc | Descriptor lệch, kết quả sai (giống A28) | So cos với pipeline CPU tham chiếu |
| Hàng nghìn file nhỏ trong `/kaggle/working` | Kéo output chậm, dễ gặp 429 | Một file `tar` + `--pull-pattern` |
| Dùng phiên L4 x4 chỉ để chạy HMM CPU | Đốt 4 GPU-giờ/giờ | Dùng phiên CPU; chỉ ghép HMM vào CPU rảnh của phiên GPU |
