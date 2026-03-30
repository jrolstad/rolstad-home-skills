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
- USPS packages (`mcp__usps__get_packages`) — only show packages with an estimated delivery date on or after today, or with a non-delivered status. Filter out packages that have already been delivered.
- Weather forecast: follow the same steps as the `/weather-check` skill
- Check register balances via Google Sheets (`mcp__google-workspace__read_sheet_values`, `user_google_email: [google_email]`):
  - Primary joint checking: spreadsheet ID `[spreadsheet_id_1]`, range `I2`
  - Secondary checking: spreadsheet ID `[spreadsheet_id_2]`, range `I2`
- Dinner meal plan for the next 7 days — use `mcp__google-workspace__get_drive_file_download_url` (`user_google_email: [google_email]`, `file_id: [meal_plan_doc_id]`, `export_format: docx`) to download the meal plan as a .docx file, then extract hyperlink display names and URLs from the docx XML using a Python script:
  ```python
  import zipfile, xml.etree.ElementTree as ET
  ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
  with zipfile.ZipFile('<local_path>') as z:
      rels = {}
      with z.open('word/_rels/document.xml.rels') as f:
          for rel in ET.parse(f).getroot():
              if rel.get('Type','').endswith('/hyperlink'):
                  rels[rel.get('Id')] = rel.get('Target','')
      with z.open('word/document.xml') as f:
          body = ET.parse(f).getroot().find('.//w:body', ns)
      for para in body.findall('.//w:p', ns):
          parts = []
          for elem in para:
              tag = elem.tag.split('}')[-1]
              if tag == 'r':
                  t = elem.find('w:t', ns)
                  if t is not None and t.text: parts.append(t.text)
              elif tag == 'hyperlink':
                  rid = elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id','')
                  text = ''.join(t.text or '' for t in elem.findall('.//w:t', ns))
                  if text: parts.append(text)
          line = ''.join(parts).strip()
          if line: print(line)
  ```
  This preserves linked recipe names as their display text. Find today's date, and show meals from today through the next 7 days (spanning into the next week's section if needed).
- Google Calendar events for the next 7 days (`mcp__google-workspace__get_events`, `user_google_email: [google_email]`, `calendar_id: primary`, `time_min`: today, `time_max`: 7 days from today, `max_results: 50`, `detailed: true`) — detailed mode is required to get the organizer field for Vrbas categorization
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
