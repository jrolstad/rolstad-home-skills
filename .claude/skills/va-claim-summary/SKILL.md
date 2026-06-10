---
name: va-claim-summary
description: Summarizes VA disability claims, rated disabilities, and appeals from VA.gov API JSON. Gets the data one of two ways — an interactive Playwright fetch (the user logs into VA.gov in a Chrome window, then it pulls the endpoints), or the user pasting JSON copied from api.va.gov. Use when the user asks to "summarize my VA claim", "fetch my VA data", "check VA claim status", "summarize VA disability ratings", "VA appeals status", or pastes VA claim/rating JSON. Do NOT use for filing claims, giving legal/benefits determinations, or non-VA data. The data is behind the user's authenticated VA.gov session — Claude cannot reach it without either the Playwright fetch or pasted JSON.
---

# VA Claim Summary

Summarize a veteran's VA disability **claims**, **rated disabilities**, and **appeals** from the
JSON returned by the VA.gov internal API. The data is behind the user's authenticated VA.gov
session, so this skill is **paste-driven**: it guides the user to copy JSON from the browser, then
parses and summarizes it.

## Important framing

- This is **informational only**. Never present output as an official VA determination, and never
  give legal advice. Summarize what the data says; flag what is worth following up on.
- The VA API is undocumented and can change at any time. If a field named below is missing, report
  what is present rather than guessing.
- Estimated dates (`minEstClaimDate` / `maxEstClaimDate`) are **estimates, not guarantees** — always
  label them as such.

## Step 1 — Get the data

Decide which of the three reports the user wants (claims, ratings, appeals — or all three). If they
just say "summarize my VA stuff," do all three.

There are two ways to obtain the data. Pick based on what the user asks for:

**Fetch mode (preferred when they want it pulled for them).** Triggers: "fetch my VA data", "pull it
from VA.gov", "log me in". Read `references/playwright-fetch.md` and follow it. It is a two-step
attach model (Playwright must not launch Chrome — that trips ID.me bot detection): the user launches
Chrome via `scripts/launch-chrome.ps1` and logs into VA.gov, then run `scripts/fetch-va-data.mjs`
**in the background** to attach over CDP and fetch. When it finishes, read the JSON files it wrote to
`output/` and continue at Step 2.

**Paste mode (fallback).** If the user prefers to paste, or fetch mode is unavailable, read
`references/endpoints.md` and give them the relevant URL(s) with the "log into VA.gov first"
preamble, then ask them to paste the JSON back.

## Step 2 — Identify the payload

Each pasted blob is JSON. Identify which endpoint it came from by its shape:

| Shape clue | Endpoint | Report |
|---|---|---|
| `data` is an array of objects with `type: "claim"` | `benefits_claims` (list) | Claims |
| `data` is a single object with `type: "claim"` and `contentions`/`trackedItems` | `benefits_claims/{id}` (detail) | Claim detail |
| `data.attributes.individual_ratings[]` | `rated_disabilities` | Ratings |
| `data` array with appeal `attributes.status` / `events` | `appeals` | Appeals |

If the JSON does not match any shape, say so and show the top-level keys you did find.

## Step 3 — Parse and summarize

For field meanings (phase types, status codes, claim-type codes, diagnostic interpretation,
decision values, `static_ind`), read `references/va-glossary.md`. Do not invent code meanings.

Then produce the report using the structure in `assets/report-template.md`. Read that file for the
exact output format. Summarize per report type:

- **Claims** — for each claim: title, type, filed date, current phase (and whether
  `currentPhaseBack` indicates it stepped backward), status, the key letter/evidence flags,
  estimated completion window, and (for a claim detail payload) the list of contentions, completed
  C&P exams, and any **open** tracked items the veteran still owes.
- **Rated disabilities** — the combined rating and effective dates, a table of service-connected
  conditions with percentages sorted high to low, and a separate list of **Not Service Connected**
  (denied) conditions. Note that 0% ratings are still service-connected.
- **Appeals** — for each appeal: type/lane, current status in plain English, the most recent event
  and its date, and what the next step is.

## Step 4 — Surface follow-ups, with care

After the summary, point out only what the **data itself** supports, e.g.:
- Open tracked items the veteran still owes (action needed).
- A claim that stepped back a phase (`currentPhaseBack: true`) — usually a new exam was ordered.
- Denied (Not Service Connected) conditions as the candidates for appeal or more evidence.
- A high combined rating profile where **Special Monthly Compensation (SMC)** or Aid & Attendance
  may be worth asking a VSO about — frame as "worth checking," never as a determination.

Always close by recommending the veteran confirm details against the official **decision letter** on
VA.gov and, for anything actionable, their **VSO** (a VA Form 21-22 on file means one is appointed).

## Advanced (optional) — direct fetch

Do not do this by default. The endpoints require the live `va.gov` session cookie, which expires
quickly and is sensitive. Only if the user explicitly provides a current session token/cookie and
asks for automation, see `references/endpoints.md` for the curl shape — and never store the token.
