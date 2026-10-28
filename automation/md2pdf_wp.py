#!/usr/bin/env python3
"""Markdown -> PDF via weasyprint (proper Vietnamese shaping, system DejaVu). Usage: md2pdf_wp.py <in.md> <out.pdf>"""
import sys, markdown
from weasyprint import HTML

src, out = sys.argv[1], sys.argv[2]
body = markdown.markdown(open(src, encoding="utf-8").read(),
                         extensions=["tables", "fenced_code", "sane_lists", "toc"])
CSS = """
@page { size: A4; margin: 1.4cm 1.5cm; }
body { font-family: 'DejaVu Sans', sans-serif; font-size: 8.8pt; line-height: 1.4; color: #1b1b1b; }
h1 { font-size: 16pt; color: #0b3d6b; border-bottom: 2px solid #0b3d6b; padding-bottom: 3px; margin: 2px 0 8px; }
h2 { font-size: 12.5pt; color: #0b3d6b; border-bottom: 1px solid #b8cfe0; padding-bottom: 2px; margin: 13px 0 5px; }
h3 { font-size: 10.5pt; color: #14517f; margin: 9px 0 3px; }
p { margin: 4px 0; } strong { color: #0b2c4a; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8pt; background: #eef2f6; color: #9b1d1d; padding: 0 2px; }
pre { font-family: 'DejaVu Sans Mono', monospace; font-size: 7.6pt; background: #f4f6f8; border: 1px solid #d5dde4; padding: 5px 7px; }
pre code { background: transparent; color: #12303f; }
table { border-collapse: collapse; margin: 6px 0; width: 100%; }
th { background: #0b3d6b; color: #fff; font-size: 8pt; padding: 4px 6px; border: 1px solid #0b3d6b; text-align: left; }
td { font-size: 8pt; padding: 3px 6px; border: 1px solid #c3ccd4; vertical-align: top; }
ul, ol { margin: 4px 0 4px 2px; } li { margin: 2px 0; }
hr { border: none; border-top: 1px solid #c3ccd4; margin: 9px 0; }
blockquote { border-left: 3px solid #b8cfe0; margin: 5px 0; padding: 2px 10px; color: #333; background: #f6f9fc; }
"""
html = '<html><head><meta charset="utf-8"><style>' + CSS + '</style></head><body>' + body + '</body></html>'
HTML(string=html).write_pdf(out)
print("PDF OK:", out)
