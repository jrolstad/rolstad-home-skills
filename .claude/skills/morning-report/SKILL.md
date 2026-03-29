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

Also fetch recent transactions (last 24 hours) from both banks, and fetch images for all mail pieces in parallel using `mcp__usps__get_mail_piece_image`.

### 2. Generate Combined Report

Output a structured report. For finances, only show the primary checking accounts (BECU: the joint checking account; Heritage Bank NW: the main checking account). Use the most recent transaction date from fetched transactions to populate the Last Transaction column. For mail, use the same table format as the mail-check skill, reading recipient and description from each piece's image.

```
## Good Morning — [Day, Date]

---
## 💳 Finance Check
---

| Account | Balance | Last Transaction |
|---------|---------|-----------------|
| BECU - Checking | $3,720.00 | Mar 23 |
| Heritage Bank NW - Checking | $6,240.00 | Mar 25 |

**Recent activity (last 24h):** X transactions — [summary of notable items, or "None" if quiet]

---
## 📬 Mail Check
---

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

---
## 📦 Packages
---

| Shipper | Status | Expected |
|---------|--------|---------|
| Shopify | Expected Delivery | Mar 30 |

---
## 🌤️ Weather — Brier, WA
---

Use the same output format as the `/weather-check` skill: 3-day forecast table and forecast discussion summary.

```

### 3. Offer Follow-up Actions

```
Would you like me to:
1. Show balances for all accounts
2. Show full transaction details for an account
3. Show mail piece images for recent mail
4. Get tracking details for a specific package
```

## Notes

- Run this at the start of the day for best results
- Pairs with `/finance-check` for deeper financial drill-down
- Pairs with `/mail-check` for detailed mail and package tracking
- Pairs with `/weather-check` for a standalone weather forecast
