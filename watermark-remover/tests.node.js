#!/usr/bin/env node
/* tests.node.js — run the browser test suite headlessly.
   Usage: node tests.node.js   (Node 18+, for DecompressionStream)
   The modules are plain scripts that attach to a global, so loading them here
   is a matter of evaluating them against globalThis. No build step, no shims
   beyond a stub for the one place images.js reaches for the DOM. */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const files = [
    'assets/js/bytes.js',
    'assets/js/unicode.js',
    'assets/js/images.js',
    'assets/js/pdf.js',
    'assets/js/containers.js',
    'assets/js/tests.js'
];

// images.js only touches `document` inside reencode(), which the suite does
// not exercise — it needs a real canvas. A stub keeps the load honest.
globalThis.document = globalThis.document || {
    createElement() { throw new Error('reencode() needs a browser.'); }
};

for (const rel of files) {
    const full = path.join(__dirname, rel);
    vm.runInThisContext(fs.readFileSync(full, 'utf8'), { filename: full });
}

const t0 = Date.now();
globalThis.WMR.tests.run(r => {
    const mark = r.pass ? '\x1b[32m ok \x1b[0m' : '\x1b[31mFAIL\x1b[0m';
    console.log(`${mark} ${r.name}`);
    if (!r.pass) console.log(`      ${r.error}`);
}).then(results => {
    const failed = results.filter(r => !r.pass);
    console.log(`\n${results.length - failed.length}/${results.length} passed in ${Date.now() - t0}ms`);
    process.exit(failed.length ? 1 : 0);
});
