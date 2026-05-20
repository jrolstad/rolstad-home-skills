#!/usr/bin/env python3
"""Compute aggregate stats from an Ambient Weather historical-data spillover file.

Usage: summarize.py <path-to-json-file>

The input file is the MCP spillover written by mcp__ambient__get_historical_data
when its result exceeds the inline token limit. Schema: {"result": [{record}, ...]}

Emits a JSON object on stdout with per-field stats, the current (newest) record
trimmed to display-relevant fields, and a per-day breakdown.
"""

import json
import sys
from collections import defaultdict


def stat(records, key):
    vals = [r[key] for r in records if r.get(key) is not None]
    if not vals:
        return None
    return {
        "min": min(vals),
        "max": max(vals),
        "avg": round(sum(vals) / len(vals), 2),
        "n": len(vals),
    }


def main():
    if len(sys.argv) != 2:
        print("usage: summarize.py <path-to-json-file>", file=sys.stderr)
        sys.exit(2)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        payload = json.load(f)
    recs = payload.get("result", [])
    if not recs:
        print(json.dumps({"error": "no records in input file"}))
        return

    recs.sort(key=lambda r: r.get("dateutc", 0), reverse=True)

    by_day = defaultdict(list)
    for r in recs:
        date = r.get("date") or ""
        by_day[date[:10]].append(r)

    per_day = []
    for day in sorted(by_day):
        d = by_day[day]
        t = [x["tempf"] for x in d if x.get("tempf") is not None]
        per_day.append({
            "day_utc": day,
            "records": len(d),
            "tempf_min": min(t) if t else None,
            "tempf_max": max(t) if t else None,
            "tempf_avg": round(sum(t) / len(t), 1) if t else None,
            "daily_rain_max_in": max((x.get("dailyrainin") or 0) for x in d),
            "wind_gust_max_mph": max((x.get("windgustmph") or 0) for x in d),
            "aqi_pm25_max": max((x.get("aqi_pm25") or 0) for x in d),
        })

    newest = recs[0]
    current = {
        "date": newest.get("date"),
        "tempf": newest.get("tempf"),
        "humidity": newest.get("humidity"),
        "windspeedmph": newest.get("windspeedmph"),
        "winddir": newest.get("winddir"),
        "baromrelin": newest.get("baromrelin"),
        "aqi_pm25": newest.get("aqi_pm25"),
        "lastRain": newest.get("lastRain"),
        "feelsLike": newest.get("feelsLike"),
    }

    summary = {
        "records": len(recs),
        "newest_utc": recs[0].get("date"),
        "oldest_utc": recs[-1].get("date"),
        "current": current,
        "tempf": stat(recs, "tempf"),
        "feelsLike": stat(recs, "feelsLike"),
        "dewPoint": stat(recs, "dewPoint"),
        "humidity": stat(recs, "humidity"),
        "windspeedmph": stat(recs, "windspeedmph"),
        "windgustmph": stat(recs, "windgustmph"),
        "baromrelin": stat(recs, "baromrelin"),
        "solarradiation": stat(recs, "solarradiation"),
        "uv": stat(recs, "uv"),
        "aqi_pm25": stat(recs, "aqi_pm25"),
        "hourlyrainin_max": max((r.get("hourlyrainin") or 0) for r in recs),
        "per_day": per_day,
    }
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
