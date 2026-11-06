108 runs (common to every variant), reference R*

| dataset | n | R* | C9 |
|---|---|---|---|
| 4s:countryside | 18 | 0.791 / 0.0114 / 0 / 42.3 | 0.701 / 0.0073 / 0 / 39.9 |
| 4s:office_loop | 18 | 0.947 / 0.0015 / 0 / 13.6 | 0.945 / 0.0010 / 0 / 13.8 |
| 4s:old_town | 18 | 0.922 / 0.0001 / 0 / 32.1 | 0.895 / 0.0003 / 0 / 41.2 |
| boreas | 18 | 0.952 / 0.0018 / 0 / 4.7 | 0.940 / 0.0002 / 0 / 4.4 |
| cmu | 18 | 0.814 / 0.0322 / 4 / 10.8 | 0.817 / 0.0302 / 4 / 10.1 |
| nord | 18 | 0.937 / 0.0076 / 0 / 21.7 | 0.938 / 0.0034 / 0 / 13.2 |
| pooled | 108 | 0.894 / 0.0091 / 4 / 20.9 | 0.873 / 0.0071 / 4 / 20.4 |

cell = recall / mean segFAR / runs > alpha / navigation error (m)

| variant | Δ recall vs ref (CI 95 %) | wins / ties / losses | Δ nav (m) | worst-dataset mean segFAR | runs > α |
|---|---|---|---|---|---|
| C9 | -0.0211 [-0.0310, -0.0130] | 44 / 0 / 64 | -0.45 | 0.0302 | 4 |
