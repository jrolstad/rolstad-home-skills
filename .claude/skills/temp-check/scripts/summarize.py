#!/usr/bin/env python3
"""Compute per-sensor and zone temperature stats from one ecobee
get_runtime_report response, filtered to the most recent 24 hours of populated
data.

Usage: summarize.py <path-to-spillover-file>

The spillover file is the JSON the MCP harness writes when
mcp__ecobee__get_runtime_report's payload exceeds the inline token limit.
Schema: {"result": {"reportList": [...], "sensorList": [...], "columns": "..."}}
or, if the harness wrapped the result inline: {"reportList": ..., ...}.

Emits a JSON object on stdout with min/max/median/n for the thermostat's
ambient zone, outdoor temp, and every sensor whose capability is `temperature`.
"""

import json
import statistics
import sys
from typing import Optional

INTERVALS_PER_24H = 288  # 5-min intervals


def stats(vals: list[float]) -> Optional[dict]:
    if not vals:
        return None
    return {
        "min": round(min(vals), 1),
        "max": round(max(vals), 1),
        "median": round(statistics.median(vals), 1),
        "n": len(vals),
    }


def parse_value(s: str) -> Optional[float]:
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def latest_24h_rows(rows: list[list[str]]) -> list[list[str]]:
    """Return the last 288 rows where at least one data column is populated."""
    populated = [r for r in rows if any(c.strip() for c in r[2:])]
    return populated[-INTERVALS_PER_24H:]


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: summarize.py <spillover-file>", file=sys.stderr)
        sys.exit(2)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Spillover wraps everything under "result"; inline responses don't.
    body = payload.get("result", payload)
    report_list = body.get("reportList", [])
    if not report_list:
        print(json.dumps({"error": "no reportList in input"}))
        return
    report = report_list[0]

    request_cols = ["date", "time"] + body.get("columns", "").split(",")
    rows = [r.split(",") for r in report.get("rowList", [])]
    rows_24h = latest_24h_rows(rows)

    out: dict = {
        "thermostatId": report.get("thermostatIdentifier"),
        "period": {
            "first": f"{rows_24h[0][0]} {rows_24h[0][1]}" if rows_24h else None,
            "last": f"{rows_24h[-1][0]} {rows_24h[-1][1]}" if rows_24h else None,
            "intervals": len(rows_24h),
        },
        "zone": None,
        "outdoor": None,
        "sensors": [],
    }

    if "zoneAveTemp" in request_cols:
        idx = request_cols.index("zoneAveTemp")
        vals = [v for v in (parse_value(r[idx]) for r in rows_24h) if v is not None]
        out["zone"] = stats(vals)

    if "outdoorTemp" in request_cols:
        idx = request_cols.index("outdoorTemp")
        vals = [v for v in (parse_value(r[idx]) for r in rows_24h) if v is not None]
        out["outdoor"] = stats(vals)

    sensor_list = body.get("sensorList", [])
    if sensor_list:
        sensor_entry = sensor_list[0]
        sensor_cols = sensor_entry.get("columns", [])
        sensor_meta = {s["sensorId"]: s for s in sensor_entry.get("sensors", [])}
        sensor_rows = [r.split(",") for r in sensor_entry.get("data", [])]
        sensor_rows_24h = latest_24h_rows(sensor_rows)

        for i, col_id in enumerate(sensor_cols):
            if i < 2:
                continue
            meta = sensor_meta.get(col_id, {})
            if meta.get("sensorType") != "temperature":
                continue
            vals = [v for v in (parse_value(r[i]) for r in sensor_rows_24h if i < len(r)) if v is not None]
            s = stats(vals)
            if s is None:
                continue
            out["sensors"].append({
                "id": col_id,
                "name": meta.get("sensorName", col_id),
                **s,
            })

    out["sensors"].sort(key=lambda s: s["name"])
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
