# Results of the 2026-11-05 afternoon session (Entries 16-17)

- `s1105_dev_gen_sota_json.tgz`:
  - `hc_dev_a.json`: Entry 16 decision variants (owf_hcal.py) on development set A, 399 runs.
  - `un_dev_a*.json`: tier simplifications (owf_union.py) on set A.
  - `gen_*.json`: incumbent INC / H on the generality sets (d10 / d50 holes, x = natural 4Seasons cross-scene, n = NCLT).
  - `sota_*.json`: the same runs merged with TAO'26 / Xu'21 / Claxton'24 / top-1 / oracle (sota_job.py), plus HSI-VN where published.
  - `sotagen/`: raw sota_job outputs.
  - `<tag>/j`: per-run OWF and OWF-H JSONs of the inc wave (aS5 = set A, nS5 = NCLT, d10S5 / d50S5 / xS5).
- `sota_<set>.md`: scoreboards (hcal_board.py; reference INC = OWF-HWA-S5).
  Cell = recall / mean segFAR / runs > alpha / navigation error (m); the navigation error of the natural set is meaningless (scene B
  coordinates are shifted by 1e6 m by construction).
Frames (fr_*.npz, hsifr_*.npz) are not committed (size); they are in the outputs of kernels inc-1..6 (accounts namhunhh, duckzuykobip,
dinhthinh) and can be regenerated with `owf_wave.py --set inc:setA+holes+natural` in ~35 min on 6 L4 sessions.
