// Export the figure library using the atlas's own renderer (identical to in-browser exports).
// SVG for every protein: A (orientation, main methods), B (full sequence/charge, main methods), C (beads, each completed main method), D (tracks, main methods).
// PNG (2x) of figure A for proteins with any predicted membrane span or signal peptide.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..');
(async () => {
  const browser = await chromium.launch(); const manifest = {};
  for (const k of ['phiX174', 'M13', 'MS2']) {
    const dir = path.join(ROOT, `${k}_Topology_Lab_Reference`); const out = path.join(dir, 'figures'); fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(out, { recursive: true });
    const page = await (await browser.newContext({ offline: true })).newPage(); await page.goto('file://' + path.join(dir, `${k}_Topology_Atlas.html`));
    const files = await page.evaluate(async () => {
      const res = []; const main = MAIN.filter(m => P.some(p => p.method_status[m] === 'complete'));
      for (const p of P) {
        const sel = main.filter(m => p.method_status[m] === 'complete'); const tag = sel.join('+');
        res.push({ name: fname(p, tag, 'orientation') + '.svg', svg: figOrientation(p, sel) });
        res.push({ name: fname(p, tag, 'seqcharge') + '.svg', svg: figSeqMap(p, sel, null) });
        res.push({ name: fname(p, tag, 'tracks') + '.svg', svg: figTracks(p, sel) });
        for (const m of sel) res.push({ name: fname(p, m, 'beads') + '.svg', svg: figBeads(p, m).svg });
        if (p.any_membrane_span || p.any_signal_peptide) { const r = await svgToPng(figOrientation(p, sel), 2); const b64 = await new Promise(ok => { const fr = new FileReader(); fr.onload = () => ok(fr.result.split(',')[1]); fr.readAsDataURL(r.blob); }); res.push({ name: fname(p, tag, 'orientation') + '@2x.png', b64 }); }
      }
      return res;
    });
    for (const f of files) { const fp = path.join(out, f.name); if (f.svg) fs.writeFileSync(fp, '<?xml version="1.0" encoding="UTF-8"?>\n' + f.svg); else fs.writeFileSync(fp, Buffer.from(f.b64, 'base64')); }
    manifest[k] = files.length; await page.context().close();
  }
  await browser.close(); console.log(JSON.stringify(manifest));
})();
