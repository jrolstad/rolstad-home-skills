# Fetch mode — interactive Playwright

An alternative to pasting JSON: drive the user's installed Chrome, let them log into VA.gov by hand,
then pull the endpoints automatically using the browser's session cookie.

## When to use

Use fetch mode when the user wants the data pulled for them (e.g. "fetch my VA data", "pull it from
VA.gov", "log me in and summarize"). Otherwise use the paste workflow in `endpoints.md`.

## One-time setup

The script's dependencies install on first use. If `scripts/node_modules` is missing, run:

```
npm install --prefix <skill>/scripts
```

(Set `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` — the script uses installed Chrome via `channel: 'chrome'`,
so the bundled Chromium is not needed.)

## Run it — two steps (CDP attach model)

Playwright must **not** launch Chrome: a Playwright-launched browser sets `navigator.webdriver` and
`--enable-automation`, which trips ID.me bot validation and blocks login. Instead the user launches a
normal Chrome with a debugging port and logs in like a human; the script then attaches over CDP.

**Step A — launch Chrome and log in (user does this):**

```
powershell -File <skill>/scripts/launch-chrome.ps1
```

This opens a normal Chrome (dedicated profile `scripts/.chrome-cdp-profile`, debug port 9222) at
`https://www.va.gov/my-va/`. The user logs in (ID.me / Login.gov + MFA). Because Chrome was launched
without automation flags, ID.me sees an ordinary browser. After the first login the session caches in
the profile, so later runs often skip login until VA expires it.

**Step B — attach and fetch (run in the background):**

```
node <skill>/scripts/fetch-va-data.mjs
```

What happens:
1. The script connects to the running Chrome over CDP (`http://127.0.0.1:9222`); attaching does not
   set automation flags.
2. It polls `https://api.va.gov/v0/user` every 3s (up to 5 min) until the session is authenticated.
3. It reads each endpoint from the **raw network response** (not Chrome's rendered JSON viewer) and
   writes one file per endpoint to `output/`:
   - `claims.json` — `/v0/benefits_claims`
   - `claim-<id>.json` — `/v0/benefits_claims/<id>` for every claim ID in the list
   - `ratings.json` — `/v0/rated_disabilities`
   - `appeals.json` — `/v0/appeals`
5. It prints a manifest of `[status] name -> file`.

## After fetching

Read the files in `output/` and summarize them with the normal Step 3 logic (glossary +
`assets/report-template.md`). A non-200 status in the manifest means that endpoint failed (often an
expired session) — report it and offer to re-run rather than inventing data.

## Security

- `scripts/.chrome-cdp-profile/` holds the **live VA.gov session cookie**; `output/` holds **medical/PII**.
  Both are gitignored. Never commit them and never copy them outside the skill.
- The script never types credentials — the human performs the login. It only makes same-origin GETs
  afterward.
