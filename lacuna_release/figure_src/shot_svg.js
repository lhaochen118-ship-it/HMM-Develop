const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [src, out, w, h] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
  await p.setContent('<html><body style="margin:0;background:#f1f5f9">' + fs.readFileSync(src, 'utf8') + '</body></html>');
  await p.screenshot({ path: out, clip: { x: 0, y: 0, width: +w, height: +h } }); await b.close();
})();
