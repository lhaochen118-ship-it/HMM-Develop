datasets ['4s:countryside', '4s:office_loop', '4s:old_town', 'boreas', 'cmu', 'nclt', 'nord']
candidates ['CMS-CPC/H+SH(a=0.01)+NGR', 'CMS-CPC/H+SH(a=0.01)+NGRr', 'CMS-CPC/H+SH+G(a=0.01)', 'CMS-CPC/H+SH+G(a=0.01)+NGR', 'CMS-CPC/H+SH+G(a=0.01)+NGRr', 'CMS-CPC/H+SH+G[both](a=0.01)', 'CMS-CPC/H+SH+G[both](a=0.01)+NGR', 'CMS-CPC/H+SH+G[both](a=0.01)+NGRr', 'CMS-CPC/H+SH+G[loco](a=0.01)', 'CMS-CPC/H+SH+G[loco](a=0.01)+NGR', 'CMS-CPC/H+SH+G[loco](a=0.01)+NGRr', 'CMS-CPC/H+SH+G[online](a=0.01)', 'CMS-CPC/H+SH+G[online](a=0.01)+NGR', 'CMS-CPC/H+SH+G[online](a=0.01)+NGRr', 'CMS-CPCW/H+SH(a=0.01)', 'CMS-CPCW/H+SH(a=0.01)+NGR', 'CMS-CPCW/H+SH(a=0.01)+NGRr', 'CMS-CPCW/H+SH[both](a=0.01)', 'CMS-CPCW/H+SH[both](a=0.01)+NGR', 'CMS-CPCW/H+SH[both](a=0.01)+NGRr', 'CMS-CPCW/H+SH[loco](a=0.01)', 'CMS-CPCW/H+SH[loco](a=0.01)+NGR', 'CMS-CPCW/H+SH[loco](a=0.01)+NGRr', 'CMS-CPCW/H+SH[online](a=0.01)', 'CMS-CPCW/H+SH[online](a=0.01)+NGR', 'CMS-CPCW/H+SH[online](a=0.01)+NGRr']

| held-out | chosen on the others | held-out err | recall | segFAR | best label-free on held-out | regret (m) |
|---|---|---|---|---|---|---|
| 4s:countryside | CMS-CPC/H+SH+G(a=0.01)+NGRr | 46.2 | 0.384 | 0.000 | CMS-CPC/H+SH+G(a=0.01) (43.8) | 2.4 |
| 4s:office_loop | CMS-CPC/H+SH+G(a=0.01)+NGRr | 10.8 | 0.726 | 0.000 | CMS-CPC/H+SH+G[loco](a=0.01) (10.3) | 0.4 |
| 4s:old_town | CMS-CPC/H+SH+G(a=0.01)+NGRr | 27.1 | 0.685 | 0.004 | CMS-CPC/H+SH+G(a=0.01)+NGR (26.7) | 0.4 |
| boreas | CMS-CPC/H+SH+G(a=0.01)+NGR | 4.1 | 0.748 | 0.001 | CMS-CPC/H+SH+G(a=0.01)+NGRr (3.9) | 0.2 |
| cmu | CMS-CPC/H+SH+G(a=0.01)+NGRr | 3.6 | 0.786 | 0.007 | CMS-CPC/H+SH+G[online](a=0.01)+NGRr (3.5) | 0.0 |
| nclt | CMS-CPC/H+SH+G(a=0.01)+NGRr | 3.9 | 0.581 | 0.001 | CMS-CPC/H+SH+G(a=0.01)+NGRr (3.9) | 0.0 |
| nord | CMS-CPC/H+SH+G(a=0.01)+NGRr | 7.3 | 0.694 | 0.000 | CMS-CPC/H+SH+G(a=0.01)+NGR (7.2) | 0.1 |
