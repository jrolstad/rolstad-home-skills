---
name: sleep-check
description: Reports CPAP therapy data from ResMed myAir, covering last night's usage, AHI, mask leak and myAir score, a table of recent nights (weekly rollups for longer windows), averages, the 4-hour compliance rate, and flagged nights. Defaults to the last 7 nights and accepts a number of nights or a phrase like "past month". Use when the user asks "sleep check", "how did I sleep", "CPAP report", "how's my CPAP", "myAir score", "AHI last week", or "sleep the last N nights". Do not use for sleep data from other devices, for medical advice or interpreting results beyond the configured thresholds, or for changing device settings. Do not add to /morning-report. Requires the myair MCP server.
---

# Sleep Check

Report on CPAP therapy from the ResMed myAir MCP server. All statistics come from `scripts/summarize.py`. Thresholds live in `config.yaml`.

## Steps

### 1. Determine the Window

Default to **7** nights. Parse the user's phrasing into an integer `days`:

- "last N nights" / "past N days" → N
- "past week" → 7, "past two weeks" → 14, "past month" → 30, "past 3 months" → 90, "past year" → 365, "all time" → 3650

Minimum 1.

### 2. Fetch Device Freshness

Call:

```
mcp__myair__get_devices()
```

Record `devices[0].name` and `devices[0].last_sleep_data_report_time`. Convert the timestamp to Pacific time for display.

If the call fails because the tool does not exist, stop and tell the user the `myair` MCP server is not loaded. They should check the `myair` entry in `~/.claude.json` and restart Claude Code. If it fails with a login or auth error, report the error once and stop. Do not retry, because repeated logins can lock the myAir account.

### 3. Fetch Records

Call:

```
mcp__myair__get_sleep_records(days: <max(days, 30)>)
```

Always fetch at least 30 nights, because the overview compares the last 7 nights with the last 30 regardless of the requested window. The result arrives as one JSON object per night (newest first). If the result spills over to a `tool-results` file, capture that file path for step 4.

### 4. Summarize

Run the script with the Bash tool. `<skill-dir>` is the absolute directory containing this SKILL.md. Any Python 3.10+ works, since the script is stdlib-only.

**Inline result (usual case):** pipe every returned record object, exactly as returned and in order, through a quoted heredoc:

```bash
python <skill-dir>/scripts/summarize.py --days <days> <<'JSON'
<every record object exactly as returned by get_sleep_records>
JSON
```

**Spillover file:** pass the path instead:

```bash
python <skill-dir>/scripts/summarize.py --days <days> <spillover-file-path>
```

The script prints a JSON summary:

- `overview`: `recent` (last 7 nights), `baseline` (last 30), and `comparison`, which gives each metric's `recent`, `baseline`, `change` and `direction` (`better` / `worse` / `steady` / null)
- `window`, `thresholds`, `latest`, `summary`, `flags`, `trend`, `skipped` for the requested `days`
- plus `nights` when `days` ≤ 14, or `weeks` when it is larger

If it exits non-zero, show its error message and stop. Never compute statistics by hand.

### 5. Render the Report

Load `assets/report-template.md` for the output structure and fill it from the script output and the step 2 device info. Use the script's numbers verbatim. The report always opens with the overview, then shows the detail for the requested window.

- **Overview summary:** write 2–3 plain-English sentences before any table, using only `overview` and the step 2 device info:
  - How the past week compares with the past 30 nights, leading with whatever moved (`better` or `worse`). If everything is `steady`, say the week is in line with the month.
  - Compliance for both windows, and whether each meets the target.
  - Flagged nights in each window, or that there were none.
  - Mention a missed night or a not-yet-uploaded last night if relevant.

  Keep it conversational, state changes as facts, and give no medical interpretation.
- **Overview table:** one row per `comparison` metric, with the dot from `direction`: `better` → 🟢, `worse` → 🔴, `steady` → ⚪, null → `—`. If `overview.baseline.window.clamped_to_first_record` is true, label the 30-night column "Since {baseline.window.start}".
- **Window Totals:** omit this section when `window.nights` is 7 or 30, because the overview table already shows those numbers.
- **Header window:** always use `window.nights` and the window dates from the script, not the requested `days`. If `window.clamped_to_first_record` is true, title it "All Nights Since {window.start}".
- **Last night vs. latest night:** if `latest.days_ago` is 1, title the section "Last Night". Otherwise title it "Latest Night (<date>)" and add the not-uploaded-yet note with the device's last upload time. Never present an older night as last night.
- **Unused nights:** show "not used" in place of usage, AHI and leak. Leave the score cell blank.
- **Nights vs. weeks:** render the nights table when `nights` is present, and the weekly table when `weeks` is present.
- **Compliance line:** "`nights_compliant` of `nights_in_window` nights at ≥`compliance_min_hours`h (`compliance_pct`%)". Add "meets the `compliance_target_pct`% target" or "below the `compliance_target_pct`% target".
- **Flags:** list each flagged night with its flags as plain facts. If `flags` is empty, write "No nights over the thresholds." Do not explain what a flag might mean medically.
- **Trend:** one sentence from `trend` ("Usage up 4 min and AHI up 0.03 in the second half of the window"). If `trend` is null, omit the line.
- **No data:** if `summary.nights_used` is 0, show the device line and "No therapy recorded in this window." and skip the tables.
- **skipped > 0:** add a note that N records had no date and were ignored.

### 6. Offer Follow-up

```
Would you like me to:
1. 📅 Show the past 30 nights
2. 🔁 Compare with the previous <days> nights
3. 🔎 Look at a specific night
```

For option 2, call `get_sleep_records(days: <max(days * 2, 30)>)` and run the script twice: once with `--days <days>` and once with `--days <days> --today <window.start from the first run>`. Then compare the two `summary` blocks.

## Notes

- The myair server caches the full history for 30 minutes, so repeat runs and the comparison follow-up cost no extra API calls.
- `config.yaml` holds every threshold, including the overview's trend bands (`trend_*`). To change one, edit the value there. The script rejects unknown keys, missing keys, and non-numeric values.
- The machine uploads over cellular after a session ends. Early in the morning, last night may not exist yet.
- Run the script's tests with `python -m pytest <skill-dir>/scripts` (needs pytest).
