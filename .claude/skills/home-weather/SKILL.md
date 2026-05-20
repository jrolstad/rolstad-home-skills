---
name: home-weather
description: Reports observed conditions from the personal Ambient Weather station — default 24 hours, optional multi-day. Shows a plain-English synopsis, current snapshot, and an aggregate stats table (temp, rain, wind, UV, AQI, humidity, pressure, solar). Use when user asks "home weather", "how's the weather at home", "station report", "what did the weather do today", "past 24 hours at home", or asks for the past N days from the home station. Do not use for forecasts — use /weather-check for the National Weather Service forecast. Requires the ambient MCP server.
---

# Home Weather

Report on observed conditions from the personal weather station via the Ambient Weather API.

## Steps

### 1. Determine the Window

Default to **1 day** (24 hours). If the user asks for a different window (e.g. "past week" → 7, "last 3 days" → 3, "last month" → 30), use that integer. Cap at 30. Use the parsed value as `days` in step 3.

### 2. Fetch Station Metadata

Call:

```
mcp__ambient__get_devices()
```

The response includes the MAC address (`macAddress`), station name (`info.name`), and location (`info.coords.location` or `info.coords.address`). If 0 devices are returned, stop and tell the user no stations are registered on the account.

### 3. Fetch Historical Data

Call:

```
mcp__ambient__get_historical_data(mac: <macAddress>, days: <days>)
```

The full response exceeds the inline token limit (288 records ≈ 166K characters). The MCP harness will return an error message containing the spillover file path that looks like `...\tool-results\mcp-ambient-get_historical_data-<timestamp>.txt`. Capture that path for step 4.

### 4. Compute Aggregates

Run the bundled script against the spillover file. The script reads the JSON, computes per-field min/max/avg and a per-day breakdown, and prints a compact JSON object to stdout:

```bash
python <skill-dir>/scripts/summarize.py <spillover-file-path>
```

`<skill-dir>` is the absolute directory containing this SKILL.md. Use the Python from `C:\code\ambient-mcp\.venv\Scripts\python.exe` if a venv is not on PATH (the script has no third-party dependencies, so any Python 3.10+ works).

### 5. Render the Report

Load `assets/report-template.md` for the output structure. Populate it from the script's JSON output and the station metadata.

- **Period label** — "24-Hour" for days=1; "{N}-Day" for days>1.
- **Period words (in the "spanning roughly the last…" line)** — "24 hours" for days=1; "{N} days" otherwise.
- **Narrative paragraph** — 2–4 sentences in plain English describing what happened. Cover the temp range with a sense of warmth/cool, rain (timing if relevant), wind (calm vs gusty), humidity, and any AQI swings. Be conversational, not a recitation of the table.
- **Currently line** — one sentence using `current` from the script output: temp °F, humidity %, wind speed + direction (convert `winddir` degrees to compass — N/NE/E/SE/S/SW/W/NW), pressure inHg, AQI.
- **Air quality category** — derived from current AQI: 0–50 Good, 51–100 Moderate, 101–150 Unhealthy for Sensitive Groups, 151–200 Unhealthy, 201–300 Very Unhealthy, 301+ Hazardous.
- **Rain row** — if all `daily_rain_max_in` across `per_day` are 0 and `hourlyrainin_max` is 0, say "0 in the last {period} (last rain was {current.lastRain})". Otherwise show total daily rain summed across days plus the max hourly rate.
- **Wind row** — "calm to {windspeedmph.max} mph sustained, max gust **{windgustmph.max} mph**". If max sustained < 1 and max gust < 5, lead with "dead-calm" or similar.
- **Pressure swing note** — delta = `baromrelin.max - baromrelin.min`. "very flat" if delta < 0.10, "moderate swing" if 0.10–0.30, "active — frontal passage(s)" if > 0.30.
- **Solar note** — peak `solarradiation.max`. "consistent with overcast" if < 300, "partly cloudy" if 300–600, "clear-sky" if > 600.

**When days > 1**, also append the per-day highlights table (see template) using the script's `per_day` array.

### 6. Offer Follow-up

```
Would you like me to:
1. 📈 Show the past week from the station
2. 🌧️ Compare with the NWS forecast (runs /weather-check)
3. 🔎 Drill into a specific metric or time window
```

If the user picks option 2, invoke `/weather-check` after this report.

## Notes

- The ambient MCP server caches results for 10 minutes (matches the station's 5-minute reporting interval). Repeated calls within that window are free.
- All timestamps from the API are UTC. The narrative is fine in UTC for daily windows; do not bother converting for the report.
- The script tolerates missing fields (some Ambient Weather hardware reports different subsets); `stat()` skips nulls.
