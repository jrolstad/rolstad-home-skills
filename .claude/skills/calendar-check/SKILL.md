---
name: calendar-check
description: |
  Shows upcoming calendar events for the next 7 days, grouped by theme. Use when user asks "what's on my calendar", "what do I have this week", "any events coming up", "calendar check", or wants a schedule overview. Do NOT use for creating, editing, or deleting calendar events, or for non-calendar queries.
---

# Calendar Check

Get a grouped, themed overview of calendar events for the next 7 days.

## Prerequisites

- claude.ai Google Calendar MCP connector must be active

## Steps

### 1. Fetch Calendar Events

Call:

```
mcp__claude_ai_Google_Calendar__list_events(
  startTime: today at 00:00:00 local time (ISO 8601),
  endTime: 7 days from today at 23:59:59 local time (ISO 8601),
  pageSize: 50,
  orderBy: startTime,
  timeZone: America/Los_Angeles
)
```

### 2. Generate Calendar Report

Group events by theme. Common themes: Health & Medical, Kids & Family, Home, Work & Meetings, Reminders & Chores, Vrbas, Other. Only show themes that have events. Within each theme, sort by date/time ascending and include the day. Bold the entire line for events occurring today.

**Vrbas rule:** Any event where the organizer is `etvrbas@gmail.com` must be placed in the **Vrbas** theme regardless of its content.

**Recurring event grouping:** Events with the same name that recur within the 7-day window should be collapsed into a single line listing all dates. Example: `Mon Apr 28, Wed Apr 30, Fri May 2 — Kenzie Swim — 6:00–7:00 PM`.

```
## 📅 Calendar — [Start Date] through [End Date]

**[Theme]**
| Day(s) | Event | Time |
|--------|-------|------|
| **Thu Apr 30** | **Team Standup** | **9:00–9:30 AM** |
| Fri May 1 | 1:1 with Manager | 2:00–2:30 PM |

**[Theme]**
| Day(s) | Event | Time |
|--------|-------|------|
| Wed May 5 | 🧼 Cleaning Day | all day |
```

### 3. Offer Follow-up Actions

```
Would you like me to:
1. Show full details for a specific event
2. Check a different date range
```

## Notes

- Pairs with `/morning-report` for a full daily briefing
- To create or modify events, use the claude.ai Google Calendar MCP tools directly
