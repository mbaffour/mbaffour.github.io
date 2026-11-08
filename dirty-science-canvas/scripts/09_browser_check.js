// Headless Chromium check of the combined atlas (file://, offline).
// 1) Geometric layout audit of every rendered figure: text/text overlap, text vs marks (pills, badges, beads, residue cells),
//    leader/connector lines crossing any label other than their own, leader/leader and bond/bond crossings, text clipped at the edges.
// 2) Scientific display checks: each residue's identity/number/state in the full sequence map; bead cartoons account for every residue once.
// 3) UI checks: search, filters, organism switch, component toggle, window, SVG/PNG export, no horizontal overflow at 390 px.
// Usage: node scripts/09_browser_check.js <out.json> [--sample N] [--shots dir]
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..'); const out = process.argv[2];
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const SAMPLE = +arg('--sample', 400), SHOTS = arg('--shots', null);
(async () => {
  const browser = await chromium.launch(); const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 }, offline: true, acceptDownloads: true });
  const page = await ctx.newPage(); const errors = [];
  page.on('pageerror', e => errors.push(String(e))); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  const file = path.join(ROOT, 'Dirty_Science_Canvas_Atlas.html');
  await page.goto('file://' + file, { timeout: 120000 });
  const res = await page.evaluate(async (SAMPLE) => {
    const host = document.createElement('div'); host.style.cssText = 'position:absolute;left:0;top:0;visibility:hidden;'; document.body.appendChild(host);
    const inter = (a, b, c, d) => { const o = (p, q, r) => (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0]); const d1=o(c,d,a), d2=o(c,d,b), d3=o(a,b,c), d4=o(a,b,d); return ((d1>0&&d2<0)||(d1<0&&d2>0)) && ((d3>0&&d4<0)||(d3<0&&d4>0)); };
    const segBox = (a, b, r) => { // segment intersects rect (shrunk by 1px)?
      const x0=r.x+1, y0=r.y+1, x1=r.x+r.w-1, y1=r.y+r.h-1; if (x1<=x0||y1<=y0) return false;
      const inside = p => p[0]>x0&&p[0]<x1&&p[1]>y0&&p[1]<y1; if (inside(a)||inside(b)) return true;
      const E=[[[x0,y0],[x1,y0]],[[x1,y0],[x1,y1]],[[x1,y1],[x0,y1]],[[x0,y1],[x0,y0]]]; return E.some(e=>inter(a,b,e[0],e[1])); };
    const ov = (a, b) => a.x < b.x + b.w - 0.5 && b.x < a.x + a.w - 0.5 && a.y < b.y + b.h - 0.5 && b.y < a.y + a.h - 0.5;
    function audit(svgStr) {
      host.innerHTML = svgStr; const svg = host.firstElementChild; const R = svg.getBoundingClientRect(); const W = +svg.getAttribute('width'), H = +svg.getAttribute('height');
      const box = el => { const r = el.getBoundingClientRect(); return { x: r.left - R.left, y: r.top - R.top, w: r.width, h: r.height }; };
      const pt = (el, x, y) => { const m = el.getCTM(); const sm = svg.getCTM(); const p = svg.createSVGPoint(); p.x = x; p.y = y; const q = p.matrixTransform(sm.inverse().multiply(m)); return [q.x, q.y]; };
      const issues = [];
      const T = [...svg.querySelectorAll('text.t')].map(e => ({ e, b: box(e), id: e.id, s: e.textContent.slice(0, 40) })).filter(t => t.b.w > 0);
      const marks = [...svg.querySelectorAll('g.pill rect, g.badge circle, g.bead circle, g.res rect, g.gap rect')].map(e => box(e));
      for (let i = 0; i < T.length; i++) {
        const a = T[i].b; if (a.x < -0.5 || a.y < -0.5 || a.x + a.w > W + 0.5 || a.y + a.h > H + 0.5) issues.push(`clipped text "${T[i].s}"`);
        for (let j = i + 1; j < T.length; j++) if (ov(a, T[j].b)) issues.push(`text overlap "${T[i].s}" / "${T[j].s}"`);
        for (const m of marks) if (ov(a, m)) { issues.push(`text over mark "${T[i].s}"`); break; }
      }
      const lines = [...svg.querySelectorAll('line.ldr, line.conn')].map(e => ({ cls: e.getAttribute('class'), f: e.dataset.for, a: pt(e, +e.getAttribute('x1'), +e.getAttribute('y1')), b: pt(e, +e.getAttribute('x2'), +e.getAttribute('y2')) }));
      for (const l of lines) for (const t of T) if (t.id !== l.f && segBox(l.a, l.b, t.b)) issues.push(`${l.cls} crosses text "${t.s}"`);
      for (let i = 0; i < lines.length; i++) for (let j = i + 1; j < lines.length; j++) if (inter(lines[i].a, lines[i].b, lines[j].a, lines[j].b)) issues.push('lines cross');
      for (const pth of svg.querySelectorAll('path.bonds')) { const segs = []; const re = /M([\d.-]+) ([\d.-]+)L([\d.-]+) ([\d.-]+)/g; let m; while ((m = re.exec(pth.getAttribute('d')))) segs.push([pt(pth, +m[1], +m[2]), pt(pth, +m[3], +m[4])]);
        if (segs.length < 1500) for (let i = 0; i < segs.length; i++) for (let j = i + 2; j < segs.length; j++) if (inter(segs[i][0], segs[i][1], segs[j][0], segs[j][1])) issues.push(`bonds cross at ${i}/${j}`); }
      host.innerHTML = ''; return issues;
    }
    const withPred = P.map((p, i) => i).filter(i => Object.keys(P[i].pred).length);
    const phage = withPred.filter(i => ORGS[P[i].org].kind === 'phage'); const hostI = withPred.filter(i => ORGS[P[i].org].kind === 'host');
    // deterministic host sample enriched for membrane proteins
    const hs = hostI.filter(i => P[i].any_membrane_span || P[i].any_signal_peptide); const pick = []; const step = Math.max(1, Math.floor(hs.length / SAMPLE)); for (let k = 0; k < hs.length && pick.length < SAMPLE; k += step) pick.push(hs[k]);
    const rest = hostI.filter(i => !pick.includes(i)); for (let k = 0; k < rest.length && pick.length < SAMPLE * 1.25; k += Math.max(1, Math.floor(rest.length / (SAMPLE / 4)))) pick.push(rest[k]);
    const todo = phage.concat(pick); const out = []; const all = MAIN.concat(COMP);
    for (const i of todo) { const p = ex(P[i]); const avail = all.filter(m => p.pred[m]); const r = { protein_id: p.protein_id, org: p.org, length: p.length, issues: {} };
      const add = (k, iss) => { if (iss.length) r.issues[k] = iss.slice(0, 8); };
      add('A_main', audit(figOrientation(p, MAIN))); add('A_all', audit(figOrientation(p, all))); add('D_all', audit(figTracks(p, all)));
      const used = MAIN.filter(m => p.pred[m]); const B = figSeqMap(p, used, null); add('B', audit(B));
      host.innerHTML = B; const titles = [...host.querySelectorAll('g.res > title')].map(t => t.textContent); host.innerHTML = '';
      r.seq_ok = titles.length === p.length && titles.every((t, j) => t.startsWith(p.sequence[j] + (j + 1) + ' ') && used.every(m => t.includes(`${m}: ${ST_SHORT[p.pred[m].labels[j]]}`)));
      r.beads = {};
      for (const m of avail) { const f = figBeads(p, m); add('C_' + m, audit(f.svg)); host.innerHTML = f.svg;
        const nums = [...host.querySelectorAll('g.bead > title')].map(t => +t.textContent.match(/^[A-Z](\d+)/)[1]); host.innerHTML = '';
        const om = (f.accounting && f.accounting.gaps || []).flatMap(([a, b]) => Array.from({ length: b - a + 1 }, (_, q) => a + q));
        const allp = nums.concat(om).sort((a, b) => a - b); r.beads[m] = { drawn: nums.length, omitted: om.length, exact: allp.length === p.length && allp.every((v, q) => v === q + 1) }; }
      out.push(r); }
    return { checked: out.length, phage: phage.length, host_sample: pick.length, results: out };
  }, SAMPLE);
  // UI
  const ui = {};
  await page.fill('#q', 'secY'); ui.search_secY = await page.$$eval('#plist li', l => l.length); await page.fill('#q', ''); await page.dispatchEvent('#q', 'input');
  await page.selectOption('#orgsel', 'M13'); ui.org_M13 = await page.$$eval('#plist li', l => l.length);
  await page.check('#filters input[data-f=span]'); ui.M13_span = await page.$$eval('#plist li', l => l.length); await page.uncheck('#filters input[data-f=span]');
  await page.evaluate(() => select(P.findIndex(p => p.protein_id === 'M13|M13p08')));
  await page.check('input[data-m=OCTOPUS]'); ui.component_track = await page.$eval('#figD svg', s => s.outerHTML.includes('OCTOPUS (component)')); await page.uncheck('input[data-m=OCTOPUS]');
  await page.fill('#w0', '5'); await page.fill('#w1', '20'); await page.click('#wapply'); ui.window_cells = await page.$$eval('#figB svg g.res', t => t.length); await page.click('#wfull');
  ui.rerun_forms = await page.$$eval('.rerun form', f => f.map(x => x.action)); ui.rerun_links = await page.$$eval('.rerun a', a => a.map(x => x.href));
  const exportsR = {};
  for (const act of ['svg', 'png2', 'png4']) { const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 30000 }), page.click(`#figA [data-act=${act}]`)]);
    const buf = fs.readFileSync(await dl.path()); exportsR[act] = { name: dl.suggestedFilename(), bytes: buf.length };
    if (act === 'svg') exportsR.svg.xml_ok = buf.toString().startsWith('<?xml') && buf.toString().trim().endsWith('</svg>'); else exportsR[act].png_size = [buf.readUInt32BE(16), buf.readUInt32BE(20)]; }
  if (SHOTS) { fs.mkdirSync(SHOTS, { recursive: true });
    for (const id of ['M13|M13p08', 'M13|M13p06', 'M13|M13p07', 'M13|M13p10', 'phiX174|phiX174p08', 'MS2|MS2g3']) { await page.evaluate(id => select(P.findIndex(p => p.protein_id === id)), id);
      for (const f of ['figA', 'figB', 'figC', 'figD']) { const el = await page.$(`#${f} .figwrap svg`); await el.screenshot({ path: path.join(SHOTS, `${id.replace('|', '_')}_${f}.png`) }); } } }
  const m = await browser.newContext({ viewport: { width: 390, height: 844 }, offline: true }); const mp = await m.newPage(); await mp.goto('file://' + file, { timeout: 120000 });
  const mobileOverflow = await mp.evaluate(() => document.documentElement.scrollWidth > window.innerWidth); await m.close();
  const bad = res.results.filter(r => Object.keys(r.issues).length || !r.seq_ok || Object.values(r.beads).some(b => !b.exact));
  const report = { checked_utc: new Date().toISOString(), browser: browser.version(), file: 'Dirty_Science_Canvas_Atlas.html', js_errors: errors, proteins_checked: res.checked, phage_proteins: res.phage, host_sample: res.host_sample,
    figures_with_layout_issues: bad.filter(r => Object.keys(r.issues).length).length, sequence_map_failures: bad.filter(r => !r.seq_ok).length, bead_accounting_failures: bad.filter(r => Object.values(r.beads).some(b => !b.exact)).length,
    problems: bad.slice(0, 200), ui, exports: exportsR, mobile_horizontal_overflow: mobileOverflow };
  fs.writeFileSync(out, JSON.stringify(report, null, 1)); await browser.close();
  console.log(JSON.stringify({ checked: res.checked, layout_issues: report.figures_with_layout_issues, seq: report.sequence_map_failures, beads: report.bead_accounting_failures, js_errors: errors.length, mobileOverflow }));
})();
