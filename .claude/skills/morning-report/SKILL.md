---
name: morning-report
description: Combined daily home status check covering finances and mail. Use when user says "morning check", "morning report", "home status", "what's going on today", or wants a start-of-day overview.
---

# Morning Report

Get a combined start-of-day overview: account balances, recent financial activity, and incoming mail and packages.

## Prerequisites

- BECU MCP server must be running
- Heritage Bank NW MCP server must be running
- USPS MCP server must be running

## Steps

### 1. Fetch All Data in Two Parallel Waves

Data is fetched in two waves to maximize parallelism. Within each wave, fire all tool calls simultaneously in a single message — do not wait for one call to finish before starting the next.

#### Wave 1 — No dependencies (all calls at once)

Send all of the following as one parallel batch:

- `mcp__becu__get_accounts` — needed to get checking account index for Wave 2
- `mcp__heritagebanknw__get_accounts` — needed to get checking account ID for Wave 2
- `mcp__usps__get_mail_pieces` — filter results to last 3 days; piece IDs needed for Wave 2
- `mcp__usps__get_packages` — filter to non-delivered or estimated delivery ≥ today
- `mcp__google-workspace__read_sheet_values` (`spreadsheet_id: [spreadsheet_id_1]`, `range_name: I2`, `user_google_email: [google_email]`) — Josh & Bethany check register
- `mcp__google-workspace__read_sheet_values` (`spreadsheet_id: [spreadsheet_id_2]`, `range_name: I2`, `user_google_email: [google_email]`) — Vrbas check register
- `mcp__google-workspace__get_drive_file_download_url` (`file_id: [meal_plan_doc_id]`, `export_format: docx`, `user_google_email: [google_email]`) — downloads meal plan; local path needed for Wave 2
- `mcp__google-workspace__get_events` (`calendar_id: primary`, `time_min`: today, `time_max`: 7 days from today, `max_results: 50`, `detailed: true`, `user_google_email: [google_email]`)
- `mcp__google-workspace__search_gmail_messages` (`query: is:unread in:inbox`, `page_size: 20`, `user_google_email: [google_email]`) — message IDs needed for Wave 2
- `mcp__google-workspace__search_gmail_messages` (`query: is:read in:inbox`, `page_size: 10`, `user_google_email: [google_email]`) — message IDs needed for Wave 2
- `WebFetch` of `https://api.weather.gov/gridpoints/SEW/128,76/forecast` — 3-day NWS forecast for Brier, WA

#### Wave 2 — Depends on Wave 1 results (all calls at once)

Once Wave 1 completes, send all of the following as one parallel batch:

- `mcp__becu__get_transactions` (`account_index`: checking account index from Wave 1, `days: 1`)
- `mcp__heritagebanknw__get_transactions` (`account_id`: checking account ID from Wave 1, `days: 1`)
- `mcp__usps__get_mail_piece_image` (`piece_id`: ...) — one call per mail piece from Wave 1 (last 3 days only)
- `mcp__google-workspace__get_gmail_messages_content_batch` (`message_ids`: all IDs from both Gmail searches in Wave 1, `format: metadata`, `user_google_email: [google_email]`)
- `Bash` to extract meal plan text: `python extract_docx_text.py <local_path>` using the path returned in Wave 1. Script is at `.claude/skills/morning-report/extract_docx_text.py`. Find today's date in the output, and show meals from today through the next 7 days (spanning into the next week's section if needed).

### 2. Generate Combined Report

Output a structured report. For finances, only show the primary checking accounts (BECU: the joint checking account; Heritage Bank NW: the main checking account). Use the most recent transaction date from fetched transactions to populate the Last Transaction column. For mail, use the same table format as the mail-check skill, reading recipient and description from each piece's image.

```
**----------------------------------------------------------------------------**
**THE MORNING REPORT**
** [Day, Date]**
**----------------------------------------------------------------------------**

**--------------------------------------**
**💳 Finance Check**
**--------------------------------------**

Compare the bank balance to the check register balance. Show ✅ after the check register value if they match, ❌ if they differ.

| Account | Balance | Check Register | Last Transaction |
|---------|---------|----------------|-----------------|
| BECU - Checking | $3,720.00 | $3,720.00 ✅ | Mar 23 |
| Heritage Bank NW - Checking | $6,240.00 | $6,180.00 ❌ | Mar 25 |

**Recent activity (last 24h):** X transactions — [summary of notable items, or "None" if quiet]

**--------------------------------------**
**📬 Mail Check**
**--------------------------------------**

Group mail by USPS account. For each account that was checked, show a table — even if no mail was found in the last 3 days (show "No mail in the last 3 days" below the account name in that case).

**Account A**
| Delivered | For | Sender | Summary |
|-----------|-----|--------|---------|
| Mar 28 | Alex | Ace Hardware | Premier Members promo mailer |
| Mar 28 | Jordan | Weed Man | 50% off first lawn service mailer |

**Account B**
No mail in the last 3 days.

**Account C**
No mail in the last 3 days.

**--------------------------------------**
**📦 Packages**
**--------------------------------------**

| Shipper | Status | Expected |
|---------|--------|---------|
| Shopify | Expected Delivery | Mar 30 |

**--------------------------------------**
**🌤️ Weather — [City, State]**
**--------------------------------------**

Use the same output format as the `/weather-check` skill: 3-day forecast table and forecast discussion summary.

**--------------------------------------**
**🍽️ Dinner This Week**
**--------------------------------------**

Show meals from today through the next 7 days. Use the most recent week section that covers today's date. If the week doesn't have enough days remaining, continue into the next week's section. Skip days with no meal listed.

| Day | Meal |
|-----|------|
| Sun Mar 29 | Salad |
| Mon Mar 30 | Shrimp Tacos |
| Tue Mar 31 | Burgers, Fries |

**--------------------------------------**
**📧 Gmail Inbox**
**--------------------------------------**

Group all messages (unread and read) by theme. Mark unread messages with **UNREAD** in the From column. Common themes: Finance & Bills, Job Search, Newsletters, Shopping & Deliveries, Home & Family, Community & Local, Other. Only include themes that have messages. Sort messages within each group by date descending.

**Finance & Bills**
| Date | From | Subject |
|------|------|---------|
| Mar 27 | First National Bank | Your credit card statement is available |

**Newsletters**
| Date | From | Subject |
|------|------|---------|
| Mar 27 | **UNREAD** Tech Newsletter | Issue #42 |

**--------------------------------------**
**📅 Calendar — Next 7 Days**
**--------------------------------------**

Group events by theme. Common themes: Health & Medical, Kids & Family, Home, Work & Meetings, Reminders & Chores, Vrbas, Other. Only show themes that have events. Within each theme, sort by date/time ascending and include the day. Bold the entire line for events occurring today.

**Vrbas rule:** Any event where the organizer is `etvrbas@gmail.com` must be placed in the **Vrbas** theme regardless of its content. To determine the organizer, fetch event details with `detailed: true`.

**Recurring event grouping:** Events with the same name that recur within the 7-day window should be collapsed into a single line listing all dates. Example: `Mon Mar 30, Wed Apr 1, Fri Apr 3 — Kenzie Swim — 6:00–7:00 PM`.

**Work & Meetings**
| Day(s) | Event | Time |
|--------|-------|------|
| **Mon Mar 30** | **Team Standup** | **9:00–9:30 AM** |
| Tue Mar 31 | 1:1 with Manager | 2:00–2:30 PM |

**Home**
| Day(s) | Event | Time |
|--------|-------|------|
| Wed Apr 1 | 🧼 Cleaning Day | all day |

```

### 3. Offer Follow-up Actions

```
Would you like me to:
1. Show balances for all accounts
2. Show full transaction details for an account
3. Show mail piece images for recent mail
4. Get tracking details for a specific package
5. Show more detailed weather information
6. Open or summarize a specific email
7. Show full details for a calendar event
```

## Notes

- Run this at the start of the day for best results
- Pairs with `/finance-check` for deeper financial drill-down
- Pairs with `/mail-check` for detailed mail and package tracking
- Pairs with `/weather-check` for a standalone weather forecast
