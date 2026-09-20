#!/usr/bin/env node
/*
 * Mobile responsive QA gate.
 *
 * This gate renders every page of the built site at phone widths. It fails
 * if a page scrolls sideways. Mobile is a first-class constraint in this
 * repo, and before this gate a person checked the widths by hand.
 *
 * Run it from the repo root:
 *   node scripts/mobile-qa.cjs
 *
 * The gate needs Playwright and a Chromium binary. Install both from the
 * repo root:
 *   npm --prefix scripts ci
 *   npm --prefix scripts exec -- playwright install chromium
 *
 * Use `--prefix scripts` and not a bare `npx`. The prefix resolves the
 * version that `scripts/package.json` pins, and each Playwright version maps
 * to one browser revision. A bare `npx playwright install` fetches the
 * newest Playwright and can install a revision that the pin does not want.
 *
 * ROOT_FONT_PX=20 repeats the same pass at a larger root font size. A reader
 * who raises the text size gets a 20px root, and every rem follows it. CI
 * runs that pass as its own step. The gate injects an `html { font-size }`
 * rule, because headless Chromium exposes no default-font-size setting to
 * Playwright. A rem inside a media query resolves against the browser
 * default and not against that rule, so this pass sees narrower breakpoints
 * than a real large-text browser. The pass therefore under-measures, and it
 * rewards a fix that wraps by content rather than a fix behind a query.
 *
 * Ported from the sibling `portfolio` repo on 2026-09-20.
 */
const fs = require('fs');
const path = require('path');

// Playwright lives in `scripts/node_modules`, and this file resolves it on
// its own. If it is absent the answer is always "install it", so print that
// instead of the error that `require` threw.
let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) {
  if (e.code !== 'MODULE_NOT_FOUND') throw e;
  console.error('mobile-qa error: Playwright is not installed. From the repo root, run:');
  console.error('  npm --prefix scripts ci');
  console.error('  npm --prefix scripts exec -- playwright install chromium');
  process.exit(1);
}

const { serve } = require('./static-server.cjs');

// The deployed site is the repo root. `deploy-pages.yml` uploads ".", and
// `build_site.py` and `build_graph.py` write their output there. This repo
// has no `dist/` directory.
const ROOT = process.env.SITE_ROOT ? path.resolve(process.env.SITE_ROOT) : process.cwd();
const WIDTHS = [320, 360, 390, 430]; // 320 covers Display-Zoom phones; 430 the largest iPhone.
// These directories hold no deployed page. `mkdocs/` builds a separate site
// that `deploy-pages.yml` does not upload.
const SKIP_DIRS = new Set(['node_modules', 'scripts', 'tests', 'mkdocs', 'site', '__pycache__']);

// `concept-map.html` loads D3 from this origin, and D3 draws the whole graph
// into an `<svg>` that is empty in the markup. Block the request and the
// element stays empty. An empty element never overflows, so the gate would
// report a pass for a page it did not render. Permit the origin, and fail
// loudly when the response does not arrive. The two checks below do that.
const ALLOWED_EXTERNAL = ['https://cdn.jsdelivr.net/'];

// Unset means the browser default root, which is 16px in every shipped Chromium.
const ROOT_FONT_PX = process.env.ROOT_FONT_PX ? Number(process.env.ROOT_FONT_PX) : null;
if (process.env.ROOT_FONT_PX && !(ROOT_FONT_PX > 0)) {
  console.error(`mobile-qa error: ROOT_FONT_PX is "${process.env.ROOT_FONT_PX}", which is not a positive number.`);
  process.exit(1);
}
const ROOT_NOTE = ROOT_FONT_PX ? ` at a ${ROOT_FONT_PX}px root` : '';

function findHtml(dir) {
  const out = [];
  for (const name of fs.readdirSync(path.join(ROOT, dir))) {
    if (name.startsWith('.') || SKIP_DIRS.has(name)) continue;
    const rel = dir === '.' ? name : `${dir}/${name}`;
    const stat = fs.statSync(path.join(ROOT, rel));
    if (stat.isDirectory()) out.push(...findHtml(rel));
    else if (name.endsWith('.html')) out.push(rel);
  }
  return out;
}

(async () => {
  const pages = findHtml('.').sort();
  // A gate that rendered no page must not report success.
  if (pages.length === 0) {
    console.error(`mobile-qa error: no HTML found under ${ROOT}. Nothing was rendered.`);
    console.error('  Run `python build_site.py` and `python build_graph.py` first, or unset SITE_ROOT.');
    process.exit(1);
  }
  // The browser is PW_CHROMIUM or Playwright's own, and nothing else. A
  // hardcoded default outranks the pinned revision on any host that holds
  // that path, and nobody notices that substitution.
  const exe = process.env.PW_CHROMIUM;
  if (exe && !fs.existsSync(exe)) {
    console.error(`mobile-qa error: PW_CHROMIUM is set to "${exe}" but nothing exists there.`);
    console.error('Unset it to use the Chromium from `npm --prefix scripts exec -- playwright install chromium`.');
    process.exit(1);
  }

  console.log(`mobile-qa: ${pages.length} page(s) under ${ROOT}${ROOT_NOTE}`);
  for (const rel of pages) console.log(`  page  ${rel}`);

  const site = await serve(ROOT);
  const browser = await chromium.launch(exe ? { executablePath: exe } : {});
  const context = await browser.newContext();
  if (ROOT_FONT_PX) {
    // The rule goes in at DOMContentLoaded, which fires before `page.goto`
    // resolves. The measurement below therefore reads a page that the
    // browser laid out at this root. `!important` outranks a later author
    // rule on `html`.
    await context.addInitScript((px) => {
      const inject = () => {
        const style = document.createElement('style');
        style.textContent = `html { font-size: ${px}px !important; }`;
        document.head.appendChild(style);
      };
      if (document.head) inject();
      else document.addEventListener('DOMContentLoaded', inject);
    }, ROOT_FONT_PX);
  }
  const page = await context.newPage();

  // Abort every request except the local server and the permitted CDN. The
  // abort keeps the pass fast and offline for everything else.
  await page.route('**/*', (r) => {
    const url = r.request().url();
    if (url.startsWith(site.origin)) return r.continue();
    if (ALLOWED_EXTERNAL.some((o) => url.startsWith(o))) return r.continue();
    return r.abort();
  });

  // A permitted request can still fail, for example when the CDN is down or
  // the runner has no network. That failure is not a layout defect, and the
  // gate must not report it as one. Record it and name it separately.
  const externalFailures = new Set();
  page.on('requestfailed', (req) => {
    const url = req.url();
    if (!ALLOWED_EXTERNAL.some((o) => url.startsWith(o))) return;
    externalFailures.add(`${url} (${(req.failure() || {}).errorText || 'unknown error'})`);
  });

  let fails = 0;
  let emptySvg = 0;
  for (const w of WIDTHS) {
    await page.setViewportSize({ width: w, height: 800 });
    for (const rel of pages) {
      await page.goto(`${site.origin}/${rel}`, { waitUntil: 'load', timeout: 20000 });
      await page.evaluate(() => document.fonts.ready);
      // Every inline `<svg>` on this site is script-drawn. An empty one
      // means the script did not run, and an empty element cannot widen the
      // page. Treat that as an unrun gate and not as a pass.
      const blank = await page.evaluate(
        () => [...document.querySelectorAll('svg')].filter((s) => s.children.length === 0).length
      );
      if (blank > 0) {
        emptySvg++;
        console.log(`  UNRUN  ${blank} empty <svg>  ${rel} @${w}px${ROOT_NOTE}`);
      }
      const over = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth
      );
      if (over > 0) { fails++; console.log(`  FAIL  +${over}px  ${rel} @${w}px${ROOT_NOTE}`); }
    }
  }
  await browser.close();
  await site.close();

  if (externalFailures.size) {
    console.error('\nmobile-qa error: a permitted external request failed, so a page did not fully render.');
    for (const f of externalFailures) console.error(`  ${f}`);
    console.error('This is a network fault and not a layout defect. The gate is unrun, not green.');
    process.exit(1);
  }
  if (emptySvg) {
    console.error(`\nmobile-qa error: ${emptySvg} page render(s) left an <svg> empty. The gate is unrun, not green.`);
    process.exit(1);
  }
  if (fails) {
    console.error(`\nFAIL: ${fails} horizontal-overflow issue(s) across ${WIDTHS.join('/')}px${ROOT_NOTE}. Fix before you commit.`);
    process.exit(1);
  }
  console.log(`OK: no horizontal overflow. ${pages.length} pages by ${WIDTHS.length} widths (${WIDTHS.join('/')}px)${ROOT_NOTE}.`);
})().catch((e) => { console.error('mobile-qa error:', e.message); process.exit(1); });
