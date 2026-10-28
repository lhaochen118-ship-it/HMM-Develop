# DIVE-HMM / CRSG — Dataset & Environment Summary (Updated 2026-10-28)

> **Status update (2026-10-28):** the research direction is now SelfCal (label-free off-map false-accept control). MixVPR, CosPlace, NetVLAD and MegaLoc weights are in the Kaggle dataset `nhatlong1103/vpr-descriptor-weights`; BoQ is still unavailable. See `handoff/03_HANDOFF_NEW_CHAT.md`.

*Bản cập nhật của "hmm_datasets_environment_summary". Giữ phần mô tả datasets + Offline Bundle; cập nhật hướng
nghiên cứu (CCBF/B2 → CRSG reliability), bổ sung **định dạng pose-GT đã phát hiện** (quan trọng cho notebook) và
**bài học vận hành T4/RTX** + **asset còn thiếu (BoQ/MixVPR)**.*

## 1. Hướng nghiên cứu hiện tại (THAY ĐỔI so với bản cũ)
Bản cũ ghi hướng **B2 Temporal Condition Belief** (CCBF). **Hướng này đã bị bỏ** (temperature theo điều kiện trơ).
Hướng hiện tại: **CRSG — Calibrated Retrieval-Score Geometry** (reliability per-frame: calibration + open-set
abstention + conformal). Dataset dùng chính: **RobotCar-Seasons v2, Extended-CMU-Seasons, Nordland** (+ Bundle).

## 2. Datasets đang attach (Kaggle, owner `nhatlong1103`)

| Tên | Slug | Vai trò hiện tại |
|---|---|---|
| RobotCar-Seasons v2 | `robotcar-seasons-v2` | Dataset thực tế chính; CRSG dominant. 9 điều kiện, 3 camera, pose train.txt. |
| Extended-CMU-Seasons | `extended-cmu-seasons` | Dataset thực tế đa-route (slice 2–24); CRSG dominant; filter sụp. |
| Extended-CMU-Seasons-2 | `extended-cmu-seasons-2` | slice25 bổ sung. |
| Nordland Full 47.6GB | `nordland-full-47-6gb` | 4 mùa, 143,072 ảnh (35,768/mùa), frame-aligned 1:1; dữ liệu DÀY ĐẶC lý tưởng (filter sân nhà). |
| Nordland Short | `norlandshort` | 2 mùa (summer/winter), 3,500 ảnh; smoke test. |
| 4Seasons | `4seasons` | Chưa dùng trong CRSG; dự phòng dataset thứ 4. |
| Bundle (offline assets) | `bundle` | Source + checkpoints: `dino_salad.ckpt`, `dinov2_vitb14_pretrain.pth`, SuperPoint, LightGlue; HLoc/LightGlue/salad/dinov2 sources; wheels (pycolmap). SALAD dim **8448**. |

## 3. ĐỊNH DẠNG POSE-GT (đã phát hiện/verify phiên này — CỰC QUAN TRỌNG cho loader)

- **RobotCar `robotcar_v2_train.txt`:** `"<cond>/<cam>/<ts>.jpg"` + 4×4 pose phẳng (12 floats row-major).
  **Translation = flat index [3,7,11]** (KHÔNG phải `nums[4:7]`). Ảnh: `images/<cond>/<cond>/<cam>/...`; resolve
  bằng index theo basename. File chỉ có **query conditions** (~200 ảnh/điều kiện); `overcast-reference` KHÔNG có
  trong train.txt (pose ở `3D-models/all.nvm`/`.db`). `robotcar_v2_test.txt` = test queries (cho benchmark chính
  thức — chưa dùng).
- **CMU `camera-poses/*.txt`:** `"img_XXXXX_cN_<ts>us.jpg" qw qx qy qz tx ty tz` → **xyz = `nums[-3:]`**. Cấu trúc
  **lồng** `sliceN/sliceN/` chứa `database/`, `query/`, `camera-poses/` (≈11 file pose theo **ngày = điều kiện**).
  Ảnh query ở `query/`. **Cảnh báo:** glob `**/slice*` bắt trùng `sliceN` và `sliceN/sliceN` → phải dedup theo base.
  Dùng 1 camera (c0) để tránh lệch viewpoint.
- **Nordland:** 4 mùa frame-aligned, filename `images-NNNNN.png`; GT place = frame-id identity. Full 35,768/mùa.
- **Regime:** ở tol lỏng (5m) RobotCar/CMU gần bão hòa → **sweep tolerance** {0.5,1,2,5}m; headline chọn acc≈0.8.

## 4. Môi trường chạy

| Thành phần | Cấu hình | Ghi chú |
|---|---|---|
| Kaggle Notebook | input `/kaggle/input`, output `/kaggle/working/dive_hmm` | Offline (Internet OFF); Bundle cấp source/ckpt/wheel. |
| Python runtime | Python 3.11/3.13 trong Kaggle (papermill/nbconvert) | torch 2.11.0+cu128 observed. |
| GPU | **RTX PRO 6000 (96GB)** HOẶC **T4 ×2 (15.6GB)** | Xem §5. |
| Offline mode env | HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1, PIP_NO_INDEX=1, WANDB_MODE=offline | Giữ nguyên. |

## 5. VẬN HÀNH GPU — bài học phiên này (bổ sung quan trọng)
- **T4 vs RTX:** RTX PRO 6000 có thể **BẬN** (kernel queued 21 phút, 0 output). **T4 instant + chạy song song 2
  kernel GPU** (trần Kaggle = 2 batch GPU session). Cỡ dữ liệu hiện tại (≤ vài chục nghìn ảnh) → **T4 nhanh +
  chắc** (SALAD ~16 ảnh/s; sequential filter là CPU-bound, RTX không tăng tốc). Chỉ dùng RTX khi cực lớn.
- **Ngắt session:** chỉ `kaggle kernels delete -y <slug>` mới ngắt thật; push version mới KHÔNG ngắt session cũ.
- **"0 output" ≠ treo:** Kaggle output/logs API trả log trễ (gần xong mới lộ).
- Runner: `automation/run_stall.py` (T4), `automation/run_rtx2.py` (RTX, delete-restart, 15'→restart ×4).

## 6. ASSET CÒN THIẾU (cho Phase 4 / việc tiếp theo)
- **Descriptor BoQ / MixVPR** (trọng số KHÔNG có trong `bundle`): để test descriptor-agnostic mạnh hơn. **Nhóm B:
  tải trọng số về máy user → upload lên Kaggle Dataset mới → import vào notebook.** (CRSG hiện mới test SALAD +
  DINOv2, cùng backbone DINOv2.)
- **(Cho benchmark chính thức)** reference poses `overcast-reference` từ `3D-models/all.nvm`/`.db` (để chạy
  RobotCar-Seasons test split chuẩn thay cho pose-GT tự dựng từ train.txt).

## 7. Cảnh báo giữ nguyên từ bản cũ
- Annotation CSV của Nordland là telemetry/GPS-style, cardinality khác số ảnh — không coi là thiếu dữ liệu.
- Một số near-black frame (đặc biệt đầu Summer) → flag, không xóa mù quáng.
- Condition label từ tên folder: chỉ dùng cho train/eval GT; **không đọc folder ở test-time** để suy condition.
