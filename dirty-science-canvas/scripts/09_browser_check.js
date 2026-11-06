// Headless-browser check of each atlas: loads via file:// (offline), visits every protein, every bead model,
// checks for JS errors, verifies residue cells in the full sequence map == protein length, and bead accounting == length.
// Usage: node scripts/09_browser_check.js <out_json> [screenshot_dir]
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..'); const out = process.argv[2]; const shots = process.argv[3];
const KEYS = ['phiX174', 'M13', 'MS2'];
(async () => {
  const browser = await chromium.launch(); const report = { checked_utc: new Date().toISOString(), browser: browser.version(), atlases: {} };
  for (const k of KEYS) {
    const file = path.join(ROOT, `${k}_Topology_Lab_Reference`, `${k}_Topology_Atlas.html`);
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 }, offline: true, acceptDownloads: true });
    const page = await ctx.newPage(); const errors = [];
    page.on('pageerror', e => errors.push(String(e))); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto('file://' + file);
    const res = await page.evaluate(async () => {
      const out = []; const P = D.proteins;
      for (let i = 0; i < P.length; i++) {
        select(i); const p = P[i];
        const models = [...MAIN, ...COMP].filter(m => p.method_status[m] === 'complete');
        const seqCells = document.querySelectorAll('#figB svg g > title').length;
        const titles = [...document.querySelectorAll('#figB svg g > title')].map(t => t.textContent);
        // identity/number check of each displayed residue
        let idOK = titles.length === p.length && titles.every((t, j) => t.startsWith(p.sequence[j] + (j + 1) + ' '));
        // state check: band title text contains state per method
        let stOK = titles.every((t, j) => methodsSelected(p).filter(m => p.predictions[m]).every(m => t.includes(`${m}: ${ST_SHORT[p.predictions[m].labels[j]]}`)));
        const beads = {};
        for (const m of models) { const r = figBeads(p, m); const acc = r.accounting;
          // count drawn residues by bead titles
          const tmp = document.createElement('div'); tmp.innerHTML = r.svg; const bt = [...tmp.querySelectorAll('g > title')].map(t => t.textContent).filter(t => /^[A-Z]\d+ · /.test(t));
          const nums = bt.map(t => +t.match(/^[A-Z](\d+)/)[1]); const omitted = acc ? acc.gaps.flatMap(([a, b]) => Array.from({ length: b - a + 1 }, (_, q) => a + q)) : [];
          const all = nums.concat(omitted).sort((a, b) => a - b); const exact = all.length === p.length && all.every((v, q) => v === q + 1);
          // overlap check: min distance between bead centres
          const cs = [...tmp.querySelectorAll('g > circle')].filter(c => +c.getAttribute('r') === 10).map(c => [+c.getAttribute('cx'), +c.getAttribute('cy')]);
          let minD = Infinity; for (let a = 0; a < cs.length; a++) for (let b = a + 1; b < cs.length; b++) minD = Math.min(minD, Math.hypot(cs[a][0] - cs[b][0], cs[a][1] - cs[b][1]));
          beads[m] = { residues_drawn: nums.length, omitted: omitted.length, each_residue_once: exact, min_bead_centre_distance: Math.round(minD * 10) / 10, gaps: acc ? acc.gaps : [] };
        }
        out.push({ protein_id: p.protein_id, length: p.length, seqmap_cells: seqCells, residue_identity_and_numbering_ok: idOK, band_states_ok: stOK, beads });
      }
      return out;
    });
    // UI interactions: search, filters, toggle, window, export
    await page.fill('#q', 'coat'); const nCoat = await page.$$eval('#plist li', l => l.length); await page.fill('#q', ''); await page.dispatchEvent('#q', 'input');
    await page.check('#filters input[data-f=span]'); const nSpan = await page.$$eval('#plist li', l => l.length); await page.uncheck('#filters input[data-f=span]');
    await page.check('#filters input[data-f=dis]'); const nDis = await page.$$eval('#plist li', l => l.length); await page.uncheck('#filters input[data-f=dis]');
    const exports = {};
    for (const act of ['svg', 'png2', 'png4']) {
      const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 20000 }), page.click(`#figB [data-act=${act}]`)]);
      const p = await dl.path(); const buf = fs.readFileSync(p); exports[act] = { name: dl.suggestedFilename(), bytes: buf.length };
      if (act !== 'svg') exports[act].png_size = [buf.readUInt32BE(16), buf.readUInt32BE(20)];
      else exports[act].xml_ok = buf.toString().startsWith('<?xml') && buf.toString().trim().endsWith('</svg>');
    }
    // window option
    await page.fill('#w0', '5'); await page.fill('#w1', '20'); await page.click('#wapply'); const winCells = await page.$$eval('#figB svg g > title', t => t.length); await page.click('#wfull');
    // component toggle
    await page.check('input[data-m=OCTOPUS]'); const tracksWithComp = await page.$eval('#figD svg', s => s.outerHTML.includes('OCTOPUS (component)')); await page.uncheck('input[data-m=OCTOPUS]');
    report.atlases[k] = { file: path.relative(ROOT, file), js_errors: errors, proteins: res, ui: { search_coat: nCoat, filter_span: nSpan, filter_disagree: nDis, window_5_20_cells: winCells, component_toggle_adds_track: tracksWithComp }, exports };
    if (shots) {
      const pick = { phiX174: ['phiX174|phiX174p08', 'phiX174|phiX174p01'], M13: ['M13|M13p08', 'M13|M13p06', 'M13|M13p07', 'M13|M13p05'], MS2: ['MS2|MS2g3'] }[k];
      for (const id of pick) { await page.evaluate(id => select(D.proteins.findIndex(p => p.protein_id === id)), id);
        for (const f of ['figA', 'figB', 'figC', 'figD']) { const el = await page.$(`#${f} .figwrap svg`); await el.screenshot({ path: path.join(shots, `${id.replace('|', '_')}_${f}.png`) }); } }
      await page.screenshot({ path: path.join(shots, `${k}_page.png`) });
    }
    { const m = await browser.newContext({ viewport: { width: 390, height: 844 }, offline: true }); const mp = await m.newPage(); await mp.goto('file://' + file);
      if (shots) await mp.screenshot({ path: path.join(shots, `${k}_mobile.png`) });
      report.atlases[k].mobile_horizontal_overflow = await mp.evaluate(() => document.documentElement.scrollWidth > window.innerWidth); await m.close(); }
    await ctx.close();
  }
  await browser.close(); fs.writeFileSync(out, JSON.stringify(report, null, 1)); console.log('ok');
})();
