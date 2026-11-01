datasets ['4s:countryside', '4s:office_loop', '4s:old_town', 'boreas', 'cmu', 'nclt', 'nord']
candidates ['CMS-CPC/H+SH', 'CMS-CPC/H+SH+G', 'CMS-CPC/H+SH+G+NGR', 'CMS-CPC/H+SH+G+NGRr', 'CMS-CPC/H+SH+G[both]', 'CMS-CPC/H+SH+G[both]+NGR', 'CMS-CPC/H+SH+G[both]+NGRr', 'CMS-CPC/H+SH+G[loco]', 'CMS-CPC/H+SH+G[loco]+NGR', 'CMS-CPC/H+SH+G[loco]+NGRr', 'CMS-CPC/H+SH+G[online]', 'CMS-CPC/H+SH+G[online]+NGR', 'CMS-CPC/H+SH+G[online]+NGRr', 'CMS-CPC/H+SH+NGR', 'CMS-CPC/H+SH+NGRr', 'CMS-CPCW/H+SH', 'CMS-CPCW/H+SH+NGR', 'CMS-CPCW/H+SH+NGRr', 'CMS-CPCW/H+SH[both]', 'CMS-CPCW/H+SH[both]+NGR', 'CMS-CPCW/H+SH[both]+NGRr', 'CMS-CPCW/H+SH[loco]', 'CMS-CPCW/H+SH[loco]+NGR', 'CMS-CPCW/H+SH[loco]+NGRr', 'CMS-CPCW/H+SH[online]', 'CMS-CPCW/H+SH[online]+NGR', 'CMS-CPCW/H+SH[online]+NGRr', 'CPC-SC+CS', 'CPC-SC+CS+NGRr', 'CPC-SC-T0.5+SH', 'CPC-SC-T0.5+SH+NGR', 'CPC-SC-T0.5+SH+NGRr']

| held-out | chosen on the others | held-out err | recall | segFAR | best label-free on held-out | regret (m) |
|---|---|---|---|---|---|---|
| 4s:countryside | CMS-CPC/H+SH+G+NGRr | 34.3 | 0.491 | 0.001 | CMS-CPC/H+SH+NGRr (31.8) | 2.5 |
| 4s:office_loop | CMS-CPC/H+SH+G+NGRr | 9.7 | 0.800 | 0.000 | CMS-CPC/H+SH+NGRr (9.6) | 0.1 |
| 4s:old_town | CMS-CPC/H+SH+G+NGRr | 26.1 | 0.703 | 0.006 | CMS-CPC/H+SH+G+NGR (25.8) | 0.3 |
| boreas | CMS-CPC/H+SH+G+NGRr | 4.5 | 0.775 | 0.003 | CMS-CPC/H+SH+G[both]+NGRr (4.3) | 0.2 |
| cmu | CMS-CPC/H+SH+G+NGRr | 4.0 | 0.822 | 0.009 | CPC-SC+CS+NGRr (3.4) | 0.6 |
| nclt | CMS-CPC/H+SH+G+NGRr | 4.3 | 0.612 | 0.002 | CMS-CPCW/H+SH[online]+NGRr (3.7) | 0.6 |
| nord | CMS-CPC/H+SH+G+NGRr | 5.6 | 0.765 | 0.000 | CMS-CPC/H+SH+NGRr (5.5) | 0.1 |
