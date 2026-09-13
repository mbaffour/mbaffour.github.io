#!/usr/bin/env node
/* Writes feed.xml and sitemap.xml from the shared data so they cannot drift from the
   pages. Run after adding or updating a post:  node scripts/build-site.mjs
   Post metadata comes from assets/js/posts-data.js; lastmod dates come from the last
   git commit that touched each file (or a post's `updated` field when that is later). */
import { readFileSync, writeFileSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const site = 'https://mbaffour.github.io';
const source = readFileSync(join(root, 'assets/js/posts-data.js'), 'utf8');
const posts = new Function(source + '\nreturn posts;')();
if (!Array.isArray(posts) || !posts.length) throw new Error('posts-data.js did not yield a posts array');
const sorted = posts.slice().sort((a, b) => b.iso.localeCompare(a.iso));

const gitDate = file => {
  try { return execSync(`git log -1 --format=%cs -- "${file}"`, { cwd: root, encoding: 'utf8' }).trim() || null; } catch (error) { return null; }
};
const today = new Date().toISOString().slice(0, 10);
const latest = (...dates) => dates.filter(Boolean).sort().pop() || today;
const escapeXml = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const rfc822 = iso => new Date(iso + 'T09:00:00Z').toUTCString().replace('GMT', '+0000');

/* ---- feed.xml ---- */
const build = latest(...sorted.map(p => p.updated || p.iso));
const items = sorted.map(p => `    <item>
      <title>${escapeXml(p.title)}</title>
      <link>${site}/${p.url}</link>
      <guid isPermaLink="true">${site}/${p.url}</guid>
      <pubDate>${rfc822(p.iso)}</pubDate>
${p.tags.map(t => `      <category>${escapeXml(t)}</category>`).join('\n')}
      <description>${escapeXml(p.blurb)}</description>
    </item>`).join('\n');
const feed = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Michael Baffour Awuah — Blog &amp; Notes</title>
    <link>${site}/blog/</link>
    <atom:link href="${site}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Notes on phage biology, lab life, and building research software.</description>
    <language>en-us</language>
    <lastBuildDate>${rfc822(build)}</lastBuildDate>
    <managingEditor>baffour@tamu.edu (Michael Baffour Awuah)</managingEditor>
${items}
  </channel>
</rss>
`;
writeFileSync(join(root, 'feed.xml'), feed);

/* ---- sitemap.xml ---- */
const pages = [
  { loc: '/', file: 'index.html', changefreq: 'weekly', priority: '1.0' },
  { loc: '/blog/', file: 'blog/index.html', changefreq: 'weekly', priority: '0.9', extra: latest(...sorted.map(p => p.updated || p.iso)) },
  { loc: '/journey.html', file: 'journey.html', changefreq: 'monthly', priority: '0.8' },
  { loc: '/builds.html', file: 'builds.html', changefreq: 'monthly', priority: '0.7' },
  { loc: '/structure-viewer/', file: 'structure-viewer/index.html', changefreq: 'weekly', priority: '0.8' },
  { loc: '/watermark-remover/', file: 'watermark-remover/index.html', changefreq: 'monthly', priority: '0.6' },
  { loc: '/cv-resume/Michael_Baffour_Awuah_CV.html', file: 'cv-resume/Michael_Baffour_Awuah_CV.html', changefreq: 'monthly', priority: '0.6' },
  ...sorted.map(p => ({ loc: '/' + p.url, file: p.url, changefreq: 'monthly', priority: '0.7', extra: p.updated || p.iso }))
];
const urls = pages.map(page => `  <url>
    <loc>${site}${page.loc}</loc>
    <lastmod>${latest(gitDate(page.file), page.extra)}</lastmod>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
  </url>`).join('\n');
writeFileSync(join(root, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`);
console.log(`feed.xml: ${sorted.length} posts, last build ${build}\nsitemap.xml: ${pages.length} URLs`);
