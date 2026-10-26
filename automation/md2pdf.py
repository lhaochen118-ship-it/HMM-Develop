#!/usr/bin/env python3
"""Convert a Markdown file to PDF via markdown -> HTML -> xhtml2pdf (pisa). Pure-python, no system deps.
Usage: md2pdf.py <in.md> <out.pdf>"""
import sys, markdown
from xhtml2pdf import pisa

src, out = sys.argv[1], sys.argv[2]
md_text = open(src, encoding="utf-8").read()
html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "sane_lists", "toc"],
)

CSS = """
@page { size: A4; margin: 1.5cm 1.6cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 9.2pt; line-height: 1.38; color: #1b1b1b; }
h1 { font-size: 17pt; color: #0b3d6b; border-bottom: 2px solid #0b3d6b; padding-bottom: 3px; margin: 2px 0 8px; }
h2 { font-size: 13pt; color: #0b3d6b; border-bottom: 1px solid #b8cfe0; padding-bottom: 2px; margin: 14px 0 6px; }
h3 { font-size: 11pt; color: #14517f; margin: 10px 0 4px; }
p  { margin: 4px 0; }
em { color: #444; }
strong { color: #0b2c4a; }
code { font-family: Courier, monospace; font-size: 8.3pt; background: #eef2f6; color: #9b1d1d; padding: 0 2px; }
pre { font-family: Courier, monospace; font-size: 7.9pt; background: #f4f6f8; border: 1px solid #d5dde4;
      padding: 6px 8px; margin: 5px 0; -pdf-keep-with-next: false; }
pre code { background: transparent; color: #12303f; padding: 0; }
table { border-collapse: collapse; margin: 6px 0; width: 100%; }
th { background: #0b3d6b; color: #ffffff; font-size: 8.4pt; padding: 4px 6px; border: 1px solid #0b3d6b; text-align: left; }
td { font-size: 8.4pt; padding: 3px 6px; border: 1px solid #c3ccd4; vertical-align: top; }
ul, ol { margin: 4px 0 4px 2px; }
li { margin: 2px 0; }
hr { border: none; border-top: 1px solid #c3ccd4; margin: 10px 0; }
blockquote { border-left: 3px solid #b8cfe0; margin: 5px 0; padding: 2px 10px; color: #333; background: #f6f9fc; }
"""

html = f"""<!doctype html><html><head><meta charset="utf-8">
<style>{CSS}</style></head><body>{html_body}</body></html>"""

with open(out, "wb") as f:
    res = pisa.CreatePDF(html, dest=f, encoding="utf-8")
print("PDF error:" if res.err else "PDF OK:", out)
sys.exit(1 if res.err else 0)
