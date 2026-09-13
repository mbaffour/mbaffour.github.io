#!/usr/bin/env node
/* Checks every relative href/src in the site's own pages points at a file that exists.
   Run:  node scripts/check-links.mjs   (exit code 1 when something is broken) */
import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { dirname, join, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const skip = ['structure-viewer', 'watermark-remover', 'node_modules', '.git'];
const pages = [];
const walk = dir => readdirSync(dir, { withFileTypes: true }).forEach(entry => {
  if (skip.includes(entry.name)) return;
  const path = join(dir, entry.name);
  if (entry.isDirectory()) walk(path); else if (entry.name.endsWith('.html')) pages.push(path);
});
walk(root);
let broken = 0;
for (const page of pages) {
  const html = readFileSync(page, 'utf8');
  for (const match of html.matchAll(/(?:href|src)=["']([^"']+)["']/g)) {
    const url = match[1];
    if (/^(https?:|mailto:|tel:|data:|#|javascript:)/.test(url) || url.includes("${")) continue;
    const path = decodeURIComponent(url.split('#')[0].split('?')[0]);
    if (!path) continue;
    let target = path.startsWith('/') ? join(root, path) : resolve(dirname(page), path);
    if (existsSync(target) && statSync(target).isDirectory()) target = join(target, 'index.html');
    if (!existsSync(target)) { broken += 1; console.log(`${relative(root, page)}: ${url}`); }
  }
}
console.log(`${pages.length} pages checked, ${broken} broken reference${broken === 1 ? '' : 's'}`);
process.exit(broken ? 1 : 0);
