---
name: thermostat-summary
description: Reports min/max/median temperatures over the past 24 hours for every thermostat and remote sensor across all households, grouped by household. Pulls historical data from the ecobee MCP server and current state from the mysa MCP server (mysa lacks history; current reading only). Use when the user asks "thermostat summary", "temperature summary", "house temps", "how cold/hot has it been", or wants a 24-hour temperature breakdown across thermostats. Do not use for forecast (use /weather-check) or single-point queries (use the MCP tools directly).
---

# Thermostat Summary

Summarize 24-hour temperature ranges for every ecobee thermostat + remote sensor and every mysa thermostat across all configured households.

## Steps

### 1. Load Household Mapping

Read `config.yaml` from the skill directory. It defines households with:
- `name` (display name)
- `city`
- `ecobee_thermostat_ids` (list)
- `mysa_device_ids` (list)

Iterate households in declaration order for output.

### 2. Fetch Current Inventory and Mysa Data (parallel)

Call these MCP tools in a single message:

```
mcp__ecobee__list_thermostats()
mcp__mysa__get_devices()
mcp__mysa__get_current_state()
mcp__mysa__get_homes()
```

`list_thermostats` / `get_devices` confirm the configured IDs still exist. Warn the user (but continue) about any configured ID not present in the live response. `get_current_state` keys by device ID. `get_homes` is used for the city label of any device whose home isn't already represented in config.

### 3. Fetch Ecobee Runtime Reports (parallel)

For each unique ecobee thermostat ID across all configured households, call:

```
mcp__ecobee__get_runtime_report(
  thermostat_id=<id>,
  start_date=<today_local_minus_1>,
  end_date=<tomorrow_local>,
  columns=["zoneAveTemp", "outdoorTemp"],
  include_sensors=true,
)
```

Date math: `start_date` is yesterday's local date (YYYY-MM-DD), `end_date` is tomorrow's local date. This gives ~72 hours of data so the most recent populated 24 hours are guaranteed inside. The thermostats are in `America/Los_Angeles`; use that timezone for date math.

Each call will spillover (response is ~75K characters with one thermostat's sensors). Capture each spillover file path from the tool error message — they look like `...\tool-results\mcp-ecobee-get_runtime_report-<timestamp>.txt`.

If a thermostat is unreachable or returns no `reportList`, note the failure in the report and continue.

### 4. Summarize Each Spillover

For each spillover file, run:

```bash
python <skill-dir>/scripts/summarize.py <spillover-file-path>
```

`<skill-dir>` is the absolute directory containing this SKILL.md. Use `C:\code\rolstad-home-workspace\repos\ecobee-mcp\.venv\Scripts\python.exe` if no system Python is on PATH; the script has no third-party dependencies, so any Python 3.10+ works.

Each invocation prints a JSON object with `thermostatId`, `period`, `zone`, `outdoor`, and a `sensors` array. Capture them all.

### 5. Render the Report

Load `assets/report-template.md` for the high-level structure. Build one **Household section** per household defined in config:

#### Per-household section

Lead with the household name and city. Branch on whether the household has any ecobee thermostats:

##### Mixed (ecobee present) — historical table

**Outdoor line:** if at least one ecobee thermostat in the household reported `outdoor` stats, show the household-wide outdoor min/max/median (pool values across the household's ecobee thermostats).

**Member table** — one row per thermostat (and per remote sensor on those thermostats), plus one row per mysa device. Columns:

| Source | Sensor | Min °F | Max °F | Median °F | Range °F |

- **Ecobee thermostat (zone average)**: source = ecobee, sensor = "{thermostat name} (zone avg)", use `zone` stats.
- **Ecobee remote sensor**: source = ecobee, sensor = sensor name. Use the `sensors` array. Include the on-thermostat sensor too (`Thermostat Temperature`).
- **Mysa device** (if present): source = mysa. Mysa has no history, so emit one row with Min/Max/Median **all set to the current reading** (converted from °C → °F: `°F = °C × 9/5 + 32`), and a footnote under the table:
  > *Mysa shows current reading only; the Mysa cloud doesn't expose historical data via REST. Min/max/median are the same value.*
  Use the device's `CorrectedTemp.v` (preferred) or `SensorTemp.v` from `get_current_state`. If neither is present or equals -1, mark as `n/a`.

Sort: thermostat zone rows first, then their remote sensors alphabetically, then mysa devices.

**Range column** = max − min, one decimal. Bold the row with the widest range — that's the room most affected by HVAC cycling or external conditions.

**Period footnote** after the table (small text): "Window: {first_ts} → {last_ts} ({intervals} 5-minute intervals)." Use the period from the first ecobee thermostat in the household.

##### Mysa-only — current-state table

If a household has **no ecobee thermostats** (mysa-only), the data is current-state only. Skip the outdoor line and skip the period footnote. Title the table `### Current` (an H3 subheading inside the household section). Use these columns:

| Source | Sensor | Temp °F | Setpoint °F | Heating? |

For each mysa device, fill from `get_current_state`:
- `Temp °F` = `CorrectedTemp.v` (preferred) or `SensorTemp.v`, converted °C → °F.
- `Setpoint °F` = `SetPoint.v`, converted °C → °F.
- `Heating?` = "yes" if `Duty.v > 0`, "no" otherwise. Append `(duty 0)` style detail if useful.

Add this footnote below the table:
> *Mysa's cloud doesn't expose historical data via REST, so only the current reading is available.*

##### Per-household summary line

End every household section with a bold-led 1–2 sentence **Summary:** describing what's notable — what stood out, what looks normal, what's out of band. Reference specific numbers from this household's table only (don't bring in another household).

#### Overall summary at the top

Before the per-household sections, emit a one-line takeaway: which household with historical data ran cooler/warmer on average (compare median of zone averages), and any sensor that stood out (widest range across all sensors with historical data). Mysa-only households are excluded from the comparison.

### 6. Offer Follow-up

```
Would you like me to:
1. 📈 Show a longer window (past week)
2. 🔎 Drill into a specific room or thermostat
3. 🌤️ Compare with outdoor weather (runs /home-weather)
```

## Notes

- Both ecobee thermostats are in `America/Los_Angeles`. The runtime_report endpoint returns 24 hours per requested UTC day with timestamps in local thermostat time, so requesting yesterday + today + tomorrow guarantees full coverage regardless of when in the day this runs.
- Ecobee retains ~18 months of runtime data; the script is bounded to 288 intervals (24h) but the same skill can be modified for longer windows by raising `INTERVALS_PER_24H` in `summarize.py` or accepting an arg.
- The skill expects `ecobee_thermostat_ids` and `mysa_device_ids` in `config.yaml` to match the user's account. When devices are added or removed, update `config.yaml`. The skill warns about ID mismatches but doesn't auto-discover.
- Cache: the ecobee MCP server caches runtime reports for 5 minutes. Calling the skill twice within that window is free on the second call.
