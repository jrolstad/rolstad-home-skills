# rolstad-home-skills

This repository contains custom Claude Code skills for home use. Skills are stored in `.claude/skills/` and automatically loaded when working in this directory.

## Available Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| `/finance-check` | "check accounts", "how much money", "account balances" | Overview of balances and recent transactions across BECU and Heritage Bank NW |
| `/mail-check` | "check mail", "any packages", "what's in the mail" | Overview of incoming USPS mail pieces and packages |
| `/morning-report` | "morning check", "home status" | Combined daily home status: finances, mail, and weather |
| `/weather-check` | "what's the weather", "will it rain", "forecast" | 3-day NWS forecast and forecast discussion for Brier, WA |
| `/home-weather` | "home weather", "station report", "past 24 hours at home" | Observed conditions from the personal Ambient Weather station (default 24h, optional multi-day) |
| `/hawk-highlighter` | "hawk highlights", "what's new in hawk highlights" | Diff the two most recent Hawk Highlights emails and surface what changed |
| `/calendar-check` | "what's on my calendar", "what do I have this week", "any events coming up", "calendar check" | Upcoming calendar events for the next 7 days, grouped by theme |
| `/canvas-inquisitor` | "canvas grades", "how are students doing", "missing assignments", "student grades" | Grade report for all observed students from Canvas LMS |
| `/resume-builder` | "build a resume", "tailor my resume", "update resume for job", "validate resume", "write a cover letter" | Tailor a resume to a job posting, validate Drive resumes against a job description, or draft a targeted cover letter |

## MCP Servers Required

- **becu** — BECU credit union accounts
- **heritagebanknw** — Heritage Bank NW accounts
- **usps** — USPS mail and package tracking
- **canvas-mtgibbs** — Canvas LMS student grades and assignments
- **ambient** — Ambient Weather personal station observations
- **google-workspace** — Google Drive (resume storage) and Google Docs (output)

## Personal Configuration

Personal settings (email, spreadsheet IDs, etc.) are stored in `settings.md` (gitignored). See `settings.md` for placeholder values used by the skills.

## Skills Best Practices

When creating or modifying skills, follow these standards (sourced from [skills-best-practices](https://github.com/mgechev/skills-best-practices)):

### Structure

```
skill-name/
├── SKILL.md              # Required: Metadata + core instructions (<500 lines)
├── config.yaml           # Skill-specific configuration
├── scripts/              # Executable code (Python/Bash) designed as tiny CLIs
├── references/           # Supplementary context (schemas, cheatsheets)
└── assets/               # Templates or static files used in output
```

### Frontmatter

- **name:** 1–64 characters, lowercase letters/numbers/hyphens only, must match parent directory name exactly
- **description:** Max 1,024 characters, third-person perspective, include positive triggers ("use when...") and negative triggers ("do not use for...")

### Progressive Disclosure

- Keep SKILL.md under 500 lines — use it for navigation and high-level procedures
- Use flat subdirectories one level deep (`assets/template.md`, not `assets/v2/template.md`)
- Load files just-in-time with explicit instructions (e.g., "Read `assets/report-template.md` for output structure")
- Use relative paths with forward slashes
- Do not create documentation files (`README.md`, `CHANGELOG.md`) inside skills
- Do not include redundant logic or library code

### Instructions

- Use step-by-step numbering with decision trees mapped out clearly
- Provide concrete templates in `assets/` for output formatting
- Write in third-person imperative voice ("Fetch the data...", not "You should fetch...")
- Use consistent, domain-specific terminology throughout

### Scripts

- Offload fragile/repetitive tasks to tested scripts in `scripts/`
- Scripts should return descriptive error messages for agent self-correction
