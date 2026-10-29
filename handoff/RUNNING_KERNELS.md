# Kernel Kaggle đang chạy lúc bàn giao (2026-10-29 ~17:00 UTC)

Các kernel này được tạo bởi khung chat cũ. Output của chúng **không** tự về branch mới. Kéo về theo cách sau:

```bash
KAGGLE_API_TOKEN=$(cat ~/.kaggle/tok_<acc>) kaggle kernels status <acc>/<slug>
KAGGLE_API_TOKEN=$(cat ~/.kaggle/tok_<acc>) kaggle kernels output <acc>/<slug> -p out/<slug>
cp out/<slug>/results/*.json analysis/results/
```

- Kernel đã COMPLETE vẫn kéo được output.
- Một số kết quả đã có sẵn trong `analysis/results/` (cột "đã kéo").
- Những kernel có Boreas trong cột "đã kéo" là kết quả đã dùng odometry đã sửa.

| Run | Kernel | Job | Đã kéo |
|---|---|---|---|
| bd50b | `synchan5704/hmm-bd50b-1` | hmm_fix.py boreas cosplace; hmm_fix.py boreas dinov2 | có |
| bd50b | `huyenco/hmm-bd50b-2` | hmm_fix.py boreas megaloc | có |
| bd50b | `yuan1103/hmm-bd50b-3` | hmm_fix.py boreas salad | có |
| bd50b | `synchan5704/hmm-bd50b-4` | hmm_fix.py boreas mixvpr | có |
| bd50b | `huyenco/hmm-bd50b-5` | hmm_fix.py boreas netvlad | có |
| bfix | `nhatlong1103/hmm-bfix-1` | hmm_fix.py boreas megaloc; nav_demo.py boreas mixvpr; cert_seq.py boreas netvlad | có |
| bfix | `yeshenhi/hmm-bfix-2` | hmm_fix.py boreas salad; nav_demo.py boreas cosplace; cert_seq.py boreas dinov2 | có |
| bfix | `nguynduylm/hmm-bfix-3` | hmm_fix.py boreas mixvpr; nav_demo.py boreas netvlad | chưa |
| bfix | `loinguyentran/hmm-bfix-4` | hmm_fix.py boreas cosplace; nav_demo.py boreas dinov2 | chưa |
| bfix | `nhatlong1103/hmm-bfix-5` | hmm_fix.py boreas netvlad; cert_seq.py boreas megaloc | chưa |
| bfix | `yeshenhi/hmm-bfix-6` | hmm_fix.py boreas dinov2; cert_seq.py boreas salad | chưa |
| bfix | `nguynduylm/hmm-bfix-7` | nav_demo.py boreas megaloc; cert_seq.py boreas mixvpr | có |
| bfix | `loinguyentran/hmm-bfix-8` | nav_demo.py boreas salad; cert_seq.py boreas cosplace | có |
| enull | `nguynduylm/hmm-enull-1` | nav_demo.py boreas megaloc | có |
| enull | `loinguyentran/hmm-enull-2` | nav_demo.py boreas salad | có |
| enull | `yuan1103/hmm-enull-3` | nav_demo.py 4s:countryside cosplace | có |
| fix6 | `nhatlong1103/hmm-fix6-1` | hmm_fix.py cmu megaloc; hmm_fix.py 4s:old_town megaloc; hmm_fix.py 4s:countryside megaloc | có |
| fix6 | `huyenco/hmm-fix6-2` | hmm_fix.py cmu salad; hmm_fix.py 4s:old_town salad; hmm_fix.py 4s:countryside salad | có |
| fix6 | `loinguyentran/hmm-fix6-3` | hmm_fix.py cmu mixvpr; hmm_fix.py 4s:old_town mixvpr; hmm_fix.py 4s:countryside mixvpr | có |
| fix6 | `mucnokieu/hmm-fix6-4` | hmm_fix.py cmu cosplace; hmm_fix.py 4s:old_town cosplace; hmm_fix.py 4s:countryside cosplace | có |
| fix6 | `nguynduylm/hmm-fix6-5` | hmm_fix.py cmu netvlad; hmm_fix.py 4s:old_town netvlad; hmm_fix.py 4s:countryside netvlad | có |
| fix6 | `synchan5704/hmm-fix6-6` | hmm_fix.py cmu dinov2; hmm_fix.py 4s:old_town dinov2; hmm_fix.py 4s:countryside dinov2 | có |
| fix6 | `yeshenhi/hmm-fix6-7` | hmm_fix.py nord megaloc; hmm_fix.py 4s:office_loop megaloc; hmm_fix.py rc megaloc | có |
| fix6 | `yuan1103/hmm-fix6-8` | hmm_fix.py nord salad; hmm_fix.py 4s:office_loop salad; hmm_fix.py rc salad | có |
| fix6 | `nhatlong1103/hmm-fix6-9` | hmm_fix.py nord mixvpr; hmm_fix.py 4s:office_loop mixvpr; hmm_fix.py rc mixvpr | có |
| fix6 | `huyenco/hmm-fix6-10` | hmm_fix.py nord cosplace; hmm_fix.py 4s:office_loop cosplace; hmm_fix.py rc cosplace | có |
| fix6 | `loinguyentran/hmm-fix6-11` | hmm_fix.py nord netvlad; hmm_fix.py 4s:office_loop netvlad; hmm_fix.py rc netvlad | có |
| fix6 | `mucnokieu/hmm-fix6-12` | hmm_fix.py nord dinov2; hmm_fix.py 4s:office_loop dinov2; hmm_fix.py rc dinov2 | có |
| fix7 | `nhatlong1103/hmm-fix7-1` | hmm_fix.py boreas megaloc; hmm_fix.py nord mixvpr; hmm_fix.py 4s:office_loop netvlad | chưa |
| fix7 | `huyenco/hmm-fix7-2` | hmm_fix.py boreas salad; hmm_fix.py nord cosplace; hmm_fix.py 4s:office_loop dinov2 | chưa |
| fix7 | `loinguyentran/hmm-fix7-3` | hmm_fix.py boreas mixvpr; hmm_fix.py nord netvlad; hmm_fix.py 4s:old_town megaloc | chưa |
| fix7 | `mucnokieu/hmm-fix7-4` | hmm_fix.py boreas cosplace; hmm_fix.py nord dinov2; hmm_fix.py 4s:old_town salad | chưa |
| fix7 | `nguynduylm/hmm-fix7-5` | hmm_fix.py boreas netvlad; hmm_fix.py rc megaloc; hmm_fix.py 4s:old_town mixvpr | chưa |
| fix7 | `synchan5704/hmm-fix7-6` | hmm_fix.py boreas dinov2; hmm_fix.py rc salad; hmm_fix.py 4s:old_town cosplace | chưa |
| fix7 | `yeshenhi/hmm-fix7-7` | hmm_fix.py cmu megaloc; hmm_fix.py rc mixvpr; hmm_fix.py 4s:old_town netvlad | chưa |
| fix7 | `yuan1103/hmm-fix7-8` | hmm_fix.py cmu salad; hmm_fix.py rc cosplace; hmm_fix.py 4s:old_town dinov2 | chưa |
| fix7 | `nhatlong1103/hmm-fix7-9` | hmm_fix.py cmu mixvpr; hmm_fix.py rc netvlad; hmm_fix.py 4s:countryside megaloc | chưa |
| fix7 | `huyenco/hmm-fix7-10` | hmm_fix.py cmu cosplace; hmm_fix.py rc dinov2; hmm_fix.py 4s:countryside salad | chưa |
| fix7 | `loinguyentran/hmm-fix7-11` | hmm_fix.py cmu netvlad; hmm_fix.py 4s:office_loop megaloc; hmm_fix.py 4s:countryside mixvpr | chưa |
| fix7 | `mucnokieu/hmm-fix7-12` | hmm_fix.py cmu dinov2; hmm_fix.py 4s:office_loop salad; hmm_fix.py 4s:countryside cosplace | chưa |
| fix7 | `nguynduylm/hmm-fix7-13` | hmm_fix.py nord megaloc; hmm_fix.py 4s:office_loop mixvpr; hmm_fix.py 4s:countryside netvlad | chưa |
| fix7 | `synchan5704/hmm-fix7-14` | hmm_fix.py nord salad; hmm_fix.py 4s:office_loop cosplace; hmm_fix.py 4s:countryside dinov2 | chưa |
| navF | `yuan1103/hmm-navF-1` | nav_demo.py boreas megaloc; nav_demo.py boreas dinov2; nav_demo.py cmu netvlad | chưa |
| navF | `yeshenhi/hmm-navF-2` | nav_demo.py boreas salad; nav_demo.py cmu megaloc; nav_demo.py cmu dinov2 | chưa |
| navF | `nhatlong1103/hmm-navF-3` | nav_demo.py boreas mixvpr; nav_demo.py cmu salad | chưa |
| navF | `nhatlong1103/hmm-navF-4` | nav_demo.py boreas cosplace; nav_demo.py cmu mixvpr | push lỗi, đã chạy lại |
| navF | `yuan1103/hmm-navF-5` | nav_demo.py boreas netvlad; nav_demo.py cmu cosplace | chưa |
| navFc | `yuan1103/hmm-navFc-1` | nav_demo.py nord megaloc; nav_demo.py 4s:office_loop mixvpr; nav_demo.py 4s:old_town netvlad | có |
| navFc | `yeshenhi/hmm-navFc-2` | nav_demo.py nord salad; nav_demo.py 4s:office_loop cosplace; nav_demo.py 4s:old_town dinov2 | có |
| navFc | `huyenco/hmm-navFc-3` | nav_demo.py nord mixvpr; nav_demo.py 4s:office_loop netvlad; nav_demo.py 4s:countryside megaloc | chưa |
| navFc | `nhatlong1103/hmm-navFc-4` | nav_demo.py nord cosplace; nav_demo.py 4s:office_loop dinov2; nav_demo.py 4s:countryside salad | chưa |
| navFc | `yuan1103/hmm-navFc-5` | nav_demo.py nord netvlad; nav_demo.py 4s:old_town megaloc; nav_demo.py 4s:countryside mixvpr | chưa |
| navFc | `yeshenhi/hmm-navFc-6` | nav_demo.py nord dinov2; nav_demo.py 4s:old_town salad; nav_demo.py 4s:countryside cosplace | chưa |
| navFc | `huyenco/hmm-navFc-7` | nav_demo.py 4s:office_loop megaloc; nav_demo.py 4s:old_town mixvpr; nav_demo.py 4s:countryside netvlad | chưa |
| navFc | `nhatlong1103/hmm-navFc-8` | nav_demo.py 4s:office_loop salad; nav_demo.py 4s:old_town cosplace; nav_demo.py 4s:countryside dinov2 | chưa |
| navG | `synchan5704/hmm-navG-1` | nav_demo.py boreas cosplace | chưa |
| navG | `loinguyentran/hmm-navG-2` | nav_demo.py cmu mixvpr | chưa |

**Thứ tự quan trọng:** `pull_kernels.py` chép theo thứ tự bảng. Run sau ghi đè run trước:

- fix7 ghi đè fix6 (null cũ);
- navF, navFc và navG ghi đè enull và bfix (1 seed hoặc không có biến thể p_out).

Kernel có trạng thái "push lỗi" đã được chạy lại ở run khác: navF-4 thành navG.
