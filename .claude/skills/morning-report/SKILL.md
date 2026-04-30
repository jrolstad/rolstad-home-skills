---
name: morning-report
description: Combined daily home status check. Runs finance-check, mail-check, weather-check, and calendar-check in sequence, then adds Gmail inbox and weekly dinner plan. Use when user says "morning check", "morning report", "home status", "what's going on today", or wants a start-of-day overview.
---

# Morning Report

Assemble the full daily home status by running each home skill in sequence, then appending the Gmail inbox and dinner plan.

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

### 2. Fetch Gmail and Meal Plan

After the skills above complete, fetch the remaining data in two waves.

#### Wave 1 (all at once)

- `mcp__google-workspace__search_gmail_messages` (`query: is:unread in:inbox`, `page_size: 20`, `user_google_email: [google_email]`)
- `mcp__google-workspace__search_gmail_messages` (`query: is:read in:inbox`, `page_size: 10`, `user_google_email: [google_email]`)
- `mcp__google-workspace__get_drive_file_download_url` (`file_id: [meal_plan_doc_id]`, `export_format: docx`, `user_google_email: [google_email]`)

#### Wave 2 (after Wave 1)

- `mcp__google-workspace__get_gmail_messages_content_batch` (`message_ids`: all IDs from both Gmail searches, `format: metadata`, `user_google_email: [google_email]`)
- `Bash` to extract meal plan text: `python extract_docx_text.py <local_path>` using the path from Wave 1. Script is at `.claude/skills/morning-report/extract_docx_text.py`. Show meals from today through the next 7 days (spanning into the next week's section if needed).

### 3. Append Gmail and Dinner Sections

```
## 📧 Gmail Inbox

Group all messages (unread and read) by theme. Mark unread messages with **UNREAD** in the From column. Common themes: Finance & Bills, Job Search, Newsletters, Shopping & Deliveries, Home & Family, Community & Local, Other. Only include themes that have messages. Sort messages within each group by date descending.

**Finance & Bills**
| Date | From | Subject |
|------|------|---------|
| Mar 27 | First National Bank | Your credit card statement is available |

**Newsletters**
| Date | From | Subject |
|------|------|---------|
| Mar 27 | **UNREAD** Tech Newsletter | Issue #42 |

---

## 🍽️ Dinner This Week

Show meals from today through the next 7 days. Use the most recent week section covering today's date; if not enough days remain, continue into the next week's section. Skip days with no meal listed.

| Day | Meal |
|-----|------|
| Sun Mar 29 | Salad |
| Mon Mar 30 | Shrimp Tacos |
| Tue Mar 31 | Burgers, Fries |
```

### 4. Offer Follow-up Actions

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
