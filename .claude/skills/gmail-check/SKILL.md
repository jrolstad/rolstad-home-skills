---
name: gmail-check
description: Summarizes the Gmail inbox grouped by theme. Use when user asks "check my email", "what's in my inbox", "any new emails", or wants an overview of recent Gmail messages. Do NOT use for sending email, reading full message bodies, or non-Gmail queries.
---

# Gmail Check

Get a themed overview of recent Gmail inbox messages.

## Prerequisites

- Google Workspace MCP server must be running

## Steps

### 1. Fetch Messages in Two Waves

#### Wave 1 (all at once)

- `mcp__google-workspace__search_gmail_messages` (`query: is:unread in:inbox`, `page_size: 20`, `user_google_email: jrolstad@gmail.com`)
- `mcp__google-workspace__search_gmail_messages` (`query: is:read in:inbox`, `page_size: 10`, `user_google_email: jrolstad@gmail.com`)

#### Wave 2 (after Wave 1)

- `mcp__google-workspace__get_gmail_messages_content_batch` (`message_ids`: all IDs from both searches combined, `format: metadata`, `user_google_email: jrolstad@gmail.com`)

### 2. Generate Inbox Report

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
```

### 3. Offer Follow-up Actions

```
Would you like me to:
1. Open or summarize a specific email
2. Search for messages on a specific topic
```

## Notes

- Pairs with `/morning-report` for a full daily briefing
- To send email, use the Google Workspace tools directly
