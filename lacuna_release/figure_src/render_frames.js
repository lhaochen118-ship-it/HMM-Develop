const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 528 }, deviceScaleFactor: 1 });
  const files = fs.readdirSync('svg').filter(f => f.endsWith('.svg')).sort(); fs.mkdirSync('png', { recursive: true });
  for (const f of files) {
    await p.setContent('<html><body style="margin:0">' + fs.readFileSync('svg/' + f, 'utf8') + '</body></html>');
    await p.screenshot({ path: 'png/' + f.replace('.svg', '.png'), clip: { x: 0, y: 0, width: 1200, height: 528 } });
  }
  await b.close();
})();
