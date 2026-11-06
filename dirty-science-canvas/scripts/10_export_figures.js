// On-demand figure library export using the atlas's own renderer (identical to in-browser exports).
// Usage: node scripts/10_export_figures.js --org T4 [--out <dir>] [--png]
// Writes, per protein: A (orientation, main methods), B (full sequence/charge), C (beads, each completed main method), D (tracks) as SVG; --png adds 2x PNG of A.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..'); const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const key = arg('--org'); if (!key) { console.error('--org required'); process.exit(1); }
const out = arg('--out', path.join(ROOT, `${key}_Topology_Lab_Reference`, 'figures')); const png = process.argv.includes('--png');
(async () => {
  const browser = await chromium.launch(); const page = await (await browser.newContext({ offline: true })).newPage();
  await page.goto('file://' + path.join(ROOT, `${key}_Topology_Lab_Reference`, `${key}_Topology_Atlas.html`), { timeout: 120000 });
  fs.mkdirSync(out, { recursive: true }); let n = 0;
  const ids = await page.evaluate(() => P.map(p => p.protein_id));
  for (let s = 0; s < ids.length; s += 50) {
    const files = await page.evaluate(async ([a, b, png]) => { const res = [];
      for (const p of P.slice(a, b)) { ex(p); const sel = MAIN.filter(m => p.pred[m]); const tag = sel.join('+') || 'none';
        res.push({ name: fname(p, tag, 'orientation') + '.svg', svg: figOrientation(p, MAIN) }, { name: fname(p, tag, 'seqcharge') + '.svg', svg: figSeqMap(p, sel, null) }, { name: fname(p, tag, 'tracks') + '.svg', svg: figTracks(p, MAIN) });
        for (const m of sel) res.push({ name: fname(p, m, 'beads') + '.svg', svg: figBeads(p, m).svg });
        if (png) { const r = await svgToPng(figOrientation(p, MAIN), 2); res.push({ name: fname(p, tag, 'orientation') + '@2x.png', b64: await new Promise(ok => { const fr = new FileReader(); fr.onload = () => ok(fr.result.split(',')[1]); fr.readAsDataURL(r.blob); }) }); } }
      return res; }, [s, s + 50, png]);
    for (const f of files) { fs.writeFileSync(path.join(out, f.name), f.svg ? '<?xml version="1.0" encoding="UTF-8"?>\n' + f.svg : Buffer.from(f.b64, 'base64')); n++; }
  }
  await browser.close(); console.log(key, n, 'files ->', out);
})();
