---
name: morning-report
description: Combined daily home status check. Runs finance-check, mail-check, weather-check, calendar-check, and gmail-check in sequence, then adds the weekly dinner plan. Use when user says "morning check", "morning report", "home status", "what's going on today", or wants a start-of-day overview.
---

# Morning Report

Assemble the full daily home status by running each home skill in sequence, then appending the dinner plan.

## Prerequisites

- BECU MCP server must be running
- Heritage Bank NW MCP server must be running
- USPS MCP server must be running
- Google Workspace MCP server must be running

## Steps

### 1. Run Home Skills in Sequence

Run each skill fully (all fetch steps + full output) before starting the next.

1. **`/finance-check`** — account balances and recent activity
2. **`/mail-check`** — USPS mail pieces and packages
3. **`/weather-check`** — 3-day NWS forecast for Brier, WA
4. **`/calendar-check`** — upcoming events for the next 7 days
5. **`/gmail-check`** — Gmail inbox grouped by theme

### 2. Fetch and Append Dinner Plan

#### Wave 1

- `mcp__google-workspace__get_drive_file_download_url` (`file_id: [meal_plan_doc_id]`, `export_format: docx`, `user_google_email: [google_email]`)

#### Wave 2 (after Wave 1)

- `Bash` to extract meal plan text: `python extract_docx_text.py <local_path>` using the path from Wave 1. Script is at `.claude/skills/morning-report/extract_docx_text.py`. Show meals from today through the next 7 days (spanning into the next week's section if needed).

#### Output

```
## 🍽️ Dinner This Week

Show meals from today through the next 7 days. Use the most recent week section covering today's date; if not enough days remain, continue into the next week's section. Skip days with no meal listed.

| Day | Meal |
|-----|------|
| Sun Mar 29 | Salad |
| Mon Mar 30 | Shrimp Tacos |
| Tue Mar 31 | Burgers, Fries |
```

### 3. Offer Follow-up Actions

```
Would you like me to:
1. Show full transaction details for an account
2. Show mail piece images for recent mail
3. Get tracking details for a specific package
4. Show more detailed weather information
5. Open or summarize a specific email
6. Show full details for a calendar event
```

## Notes

- Run this at the start of the day for best results
- Each section can also be run independently as its own skill
