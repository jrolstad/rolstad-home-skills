# rolstad-home-skills

Custom Claude Code skills for home use.

## Skills

| Skill | Description |
|-------|-------------|
| `/finance-check` | Account balances and recent transactions across BECU and Heritage Bank NW |
| `/mail-check` | Incoming USPS mail pieces and packages |
| `/morning-report` | Combined daily home status: finances, mail, and weather |
| `/weather-check` | 3-day NWS forecast and forecast discussion for Brier, WA |
| `/hawk-highlighter` | Diff the two most recent MTHS Hawk Highlights newsletters and surface what's new or changed |

## Setup

### Install Skills

Copy the skills to your Claude Code skills directory:

```bash
cp -r .claude/skills/* ~/.claude/skills/
```

Or symlink for live updates:

```bash
for skill in .claude/skills/*/; do
  ln -s "$(pwd)/$skill" ~/.claude/skills/$(basename $skill)
done
```

### Required MCP Servers

| Server | Used By |
|--------|---------|
| `becu` | finance-check, morning-report |
| `heritagebanknw` | finance-check, morning-report |
| `usps` | mail-check, morning-report |
| `google-workspace` | hawk-highlighter |

## Repository Structure

```
.claude/
  skills/
    finance-check/        # /finance-check skill
    mail-check/           # /mail-check skill
    morning-report/       # /morning-report skill
    hawk-highlighter/     # /hawk-highlighter skill
CLAUDE.md                 # Project context for Claude
README.md                 # This file
```
