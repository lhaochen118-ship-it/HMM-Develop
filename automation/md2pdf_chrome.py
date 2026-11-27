#!/usr/bin/env python3
"""Markdown -> PDF through headless Chromium (Unicode/Vietnamese-safe). Relative image paths resolve against the md file.
Usage: md2pdf_chrome.py <in.md> <out.pdf>"""
import sys, os, markdown
import subprocess
src, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
body = markdown.markdown(open(src, encoding="utf-8").read(), extensions=["tables", "fenced_code", "sane_lists"])
css = """@page{size:A4;margin:14mm 13mm} body{font-family:'Noto Sans','DejaVu Sans',Arial,sans-serif;font-size:9.4pt;line-height:1.42;color:#1b1b1b}
h1{font-size:17pt;color:#0b3d6b;border-bottom:2px solid #0b3d6b;padding-bottom:3px} h2{font-size:12.5pt;color:#0b3d6b;border-bottom:1px solid #b8cfe0;margin-top:16px}
h3{font-size:11pt;color:#14517f} table{border-collapse:collapse;width:100%;margin:6px 0;font-size:8.2pt} th{background:#0b3d6b;color:#fff;padding:3px 5px;text-align:left}
td{border:1px solid #c3ccd4;padding:2px 5px;vertical-align:top} code{background:#eef2f6;padding:0 2px;font-size:8.2pt} pre{background:#f4f6f8;padding:6px;white-space:pre-wrap}
img{max-width:100%} em{color:#444}"""
html = f"<!doctype html><html><head><meta charset='utf-8'><base href='file://{os.path.dirname(src)}/'><style>{css}</style></head><body>{body}</body></html>"
tmp = out + ".html"; open(tmp, "w", encoding="utf-8").write(html)
CHROME = os.environ.get("CHROME", "/opt/pw-browsers/chromium/chrome-linux64/chrome")
if not os.path.exists(CHROME): CHROME = "/opt/pw-browsers/chromium-1243/chrome-linux64/chrome"
subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={out}", "file://" + tmp], check=True, capture_output=True)
os.remove(tmp); print("wrote", out)
