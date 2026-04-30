---
name: gmail-check
description: Summarizes the Gmail inbox grouped by theme. Use when user asks "check my email", "what's in my inbox", "any new emails", or wants an overview of recent Gmail messages. Do NOT use for sending email, reading full message bodies, or non-Gmail queries.
---

# Gmail Check

Get a themed overview of recent Gmail inbox messages.

## Prerequisites

- claude.ai Gmail MCP connector must be active

## Steps

### 1. Fetch Threads (both calls in parallel)

- `mcp__claude_ai_Gmail__search_threads` (`query: "is:unread in:inbox"`, `pageSize: 20`)
- `mcp__claude_ai_Gmail__search_threads` (`query: "is:read in:inbox"`, `pageSize: 10`)

Each result includes subject, sender, recipients, and a message snippet — no second wave needed.

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
- To send email, use the claude.ai Gmail MCP tools directly
