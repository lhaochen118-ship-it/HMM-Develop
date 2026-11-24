108 runs (common to every variant), reference R*

| dataset | n | R* | C9 |
|---|---|---|---|
| 4s:countryside | 18 | 0.886 / 0.0018 / 0 / 19.3 | 0.877 / 0.0049 / 0 / 19.7 |
| 4s:office_loop | 18 | 0.976 / 0.0000 / 0 / 6.9 | 0.976 / 0.0000 / 0 / 7.1 |
| 4s:old_town | 18 | 0.969 / 0.0005 / 0 / 16.2 | 0.958 / 0.0005 / 0 / 18.3 |
| boreas | 18 | 0.986 / 0.0003 / 0 / 3.4 | 0.983 / 0.0015 / 0 / 4.4 |
| cmu | 18 | 0.796 / 0.0077 / 1 / 2.8 | 0.814 / 0.0034 / 0 / 3.0 |
| nord | 18 | 0.984 / 0.0029 / 0 / 3.7 | 0.982 / 0.0010 / 0 / 3.4 |
| pooled | 108 | 0.933 / 0.0022 / 1 / 8.7 | 0.932 / 0.0019 / 0 / 9.3 |

cell = recall / mean segFAR / runs > alpha / navigation error (m)

| variant | Δ recall vs ref (CI 95 %) | wins / ties / losses | Δ nav (m) | worst-dataset mean segFAR | runs > α |
|---|---|---|---|---|---|
| C9 | -0.0011 [-0.0043, +0.0017] | 55 / 0 / 53 | +0.58 | 0.0049 | 0 |
