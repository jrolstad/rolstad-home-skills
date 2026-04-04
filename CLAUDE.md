# rolstad-home-skills

This repository contains custom Claude Code skills for home use. Skills are stored in `.claude/skills/` and automatically loaded when working in this directory.

## Available Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| `/finance-check` | "check accounts", "how much money", "account balances" | Overview of balances and recent transactions across BECU and Heritage Bank NW |
| `/mail-check` | "check mail", "any packages", "what's in the mail" | Overview of incoming USPS mail pieces and packages |
| `/morning-report` | "morning check", "home status" | Combined daily home status: finances, mail, and weather |
| `/weather-check` | "what's the weather", "will it rain", "forecast" | 3-day NWS forecast and forecast discussion for Brier, WA |
| `/hawk-highlighter` | "hawk highlights", "what's new in hawk highlights" | Diff the two most recent Hawk Highlights emails and surface what changed |

## MCP Servers Required

- **becu** — BECU credit union accounts
- **heritagebanknw** — Heritage Bank NW accounts
- **usps** — USPS mail and package tracking

## Personal Configuration

Personal settings (email, spreadsheet IDs, etc.) are stored in `settings.md` (gitignored). See `settings.md` for placeholder values used by the skills.
