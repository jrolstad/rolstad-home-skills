// Interactive VA.gov fetcher (CDP-attach model).
//
// This does NOT launch Chrome itself — Playwright launching Chrome trips ID.me bot detection
// (navigator.webdriver / --enable-automation). Instead the user launches a normal Chrome with a
// debugging port (see launch-chrome.ps1) and logs in like a human. This script then ATTACHES over
// CDP and reads the API endpoints from the live session. Attaching does not set automation flags,
// so the login is indistinguishable from normal browsing.
//
// Flow:
//   1) Run:  powershell -File scripts/launch-chrome.ps1      (opens Chrome on port 9222)
//   2) Log into https://www.va.gov/my-va/ in that window.
//   3) Run:  node scripts/fetch-va-data.mjs                  (this script)
//
// Output: one JSON file per endpoint in ../output/. Both the profile and output are gitignored.

import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const skillDir = join(here, '..');
const outDir = join(skillDir, 'output');
mkdirSync(outDir, { recursive: true });

const CDP_URL = 'http://127.0.0.1:9222';
const BASE = 'https://api.va.gov/v0';
const LOGIN_TIMEOUT_MS = 5 * 60 * 1000;
const POLL_MS = 3000;

function fail(msg) {
  console.error(msg);
  process.exit(1);
}

// Connect to the user-launched Chrome (retry briefly in case it is still starting).
let browser;
{
  const connectDeadline = Date.now() + 60 * 1000;
  while (Date.now() < connectDeadline) {
    try {
      browser = await chromium.connectOverCDP(CDP_URL);
      break;
    } catch {
      await new Promise((r) => setTimeout(r, 2000));
    }
  }
  if (!browser) {
    fail(
      `Could not connect to Chrome on ${CDP_URL}.\n` +
        `Launch it first:  powershell -File "${join(here, 'launch-chrome.ps1')}"\n` +
        `then log into VA.gov and re-run this script.`,
    );
  }
}

const context = browser.contexts()[0] ?? (await browser.newContext());
// Use a dedicated worker tab so we never navigate the user's login tab out from under them.
// Cookies are shared across tabs in the same profile, so this tab sees the session once the
// user has logged in on their own tab.
const page = await context.newPage();

async function fetchJson(url) {
  const resp = await page.goto(url, { waitUntil: 'domcontentloaded' });
  const status = resp ? resp.status() : 0;
  let body;
  try {
    body = await resp.json(); // raw network body — not the rendered JSON viewer
  } catch {
    body = resp ? await resp.text() : '';
  }
  return { status, body };
}

console.log('\n=== VA.gov fetch (attached to your Chrome) ===');
console.log('Make sure you are logged into https://www.va.gov/my-va/ in that window.');
console.log('Waiting for an authenticated session (up to 5 minutes)...\n');

let authed = false;
const deadline = Date.now() + LOGIN_TIMEOUT_MS;
while (Date.now() < deadline) {
  try {
    const { status } = await fetchJson(`${BASE}/user`);
    if (status === 200) {
      authed = true;
      break;
    }
  } catch {
    // page/browser may have closed; report cleanly below
  }
  await new Promise((r) => setTimeout(r, POLL_MS));
}

if (!authed) {
  fail('Timed out waiting for an authenticated VA.gov session. Nothing fetched.');
}

console.log('Authenticated. Fetching claims, ratings, and appeals...\n');

const manifest = [];
async function save(name, url) {
  const { status, body } = await fetchJson(url);
  const file = join(outDir, `${name}.json`);
  writeFileSync(file, JSON.stringify(body, null, 2));
  manifest.push({ name, status, file });
  return body;
}

const claims = await save('claims', `${BASE}/benefits_claims`);
await save('ratings', `${BASE}/rated_disabilities`);
await save('appeals', `${BASE}/appeals`);

const ids = Array.isArray(claims?.data) ? claims.data.map((c) => c.id).filter(Boolean) : [];
for (const id of ids) {
  await save(`claim-${id}`, `${BASE}/benefits_claims/${id}`);
}

console.log('Saved:');
for (const m of manifest) console.log(`  [${m.status}] ${m.name} -> ${m.file}`);
console.log(`\nOutput dir: ${outDir}`);
console.log('Done. You can close the browser window.');

// Detach without closing the user's browser.
await browser.close();
