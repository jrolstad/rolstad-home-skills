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

### 1. Fetch All Data in Parallel

Simultaneously retrieve:
- BECU accounts and balances (`mcp__becu__get_accounts`, `mcp__becu__get_balance`)
- Heritage Bank NW accounts and balances (`mcp__heritagebanknw__get_accounts`, `mcp__heritagebanknw__get_balance`)
- USPS mail pieces (`mcp__usps__get_mail_pieces`) — filter to last 3 days
- USPS packages (`mcp__usps__get_packages`)
- Weather forecast: follow the same steps as the `/weather-check` skill
- Check register balances via Google Sheets (`mcp__google-workspace__read_sheet_values`, `user_google_email: [google_email]`):
  - Primary joint checking: spreadsheet ID `[spreadsheet_id_1]`, range `I2`
  - Secondary checking: spreadsheet ID `[spreadsheet_id_2]`, range `I2`
- Google Calendar events for the next 7 days (`mcp__google-workspace__get_events`, `user_google_email: [google_email]`, `calendar_id: primary`, `time_min`: today, `time_max`: 7 days from today, `max_results: 50`)
- Gmail inbox (`user_google_email: [google_email]`):
  1. Search unread: `mcp__google-workspace__search_gmail_messages` with query `is:unread in:inbox`, `page_size: 20`
  2. Search recent read: `mcp__google-workspace__search_gmail_messages` with query `is:read in:inbox`, `page_size: 10`
  3. Batch-fetch metadata for all returned message IDs using `mcp__google-workspace__get_gmail_messages_content_batch` with `format: metadata`

Also fetch recent transactions (last 24 hours) from both banks, and fetch images for all mail pieces in parallel using `mcp__usps__get_mail_piece_image`.

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

Group events by theme. Common themes: Health & Medical, Kids & Family, Home, Work & Meetings, Reminders & Chores, Other. Only show themes that have events. Within each theme, sort by date/time ascending and include the day. Bold the entire line for events occurring today.

**Work & Meetings**
- **Mon Mar 30 — Team Standup — 9:00–9:30 AM**
- Tue Mar 31 — 1:1 with Manager — 2:00–2:30 PM

**Home**
- Wed Apr 1 — 🧼 Cleaning Day (all day)

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
