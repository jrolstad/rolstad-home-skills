#!/usr/bin/env python3
"""Summarize myAir nightly records for /sleep-check.

Reads records returned by mcp__myair__get_sleep_records from stdin or a file,
and prints a JSON summary: an `overview` comparing the last 7 nights with the
last 30, followed by the detail for the requested `--days` window. Thresholds
and trend bands come from ../config.yaml. The input must cover at least 30
nights for the overview, i.e. get_sleep_records(days >= 30).

Accepted input: a JSON array of records, a run of concatenated JSON objects
(how FastMCP renders a list: one text block per record), or a Claude Code
tool-results file (a list of {"type": "text", "text": ...} blocks).

Usage: summarize.py [--days N] [--today YYYY-MM-DD] [--config PATH] [path]
Stdlib only; Python 3.10+.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"
CONFIG_KEYS = {
    "flag_min_usage_hours",
    "flag_max_ahi",
    "flag_max_leak_l_per_min",
    "compliance_min_hours",
    "compliance_target_pct",
    "trend_usage_minutes",
    "trend_ahi",
    "trend_leak_l_per_min",
    "trend_score",
    "trend_compliance_pct",
}
WEEKLY_ROLLUP_AFTER_NIGHTS = 14
MIN_USED_NIGHTS_FOR_TREND = 4
OVERVIEW_RECENT_NIGHTS = 7
OVERVIEW_BASELINE_NIGHTS = 30
# (summary key, config key for the "steady" band, whether higher is better)
OVERVIEW_METRICS = (
    ("avg_usage_minutes", "trend_usage_minutes", True),
    ("avg_ahi", "trend_ahi", False),
    ("avg_leak", "trend_leak_l_per_min", False),
    ("avg_score", "trend_score", True),
    ("compliance_pct", "trend_compliance_pct", True),
)


class InputError(Exception):
    pass


def load_config(path: Path) -> dict:
    """Parse flat `key: number` YAML. Strict, so a typo can't silently change a threshold."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as err:
        raise InputError(f"cannot read config {path}: {err}") from err
    config: dict = {}
    for lineno, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        key, sep, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not sep or key not in CONFIG_KEYS:
            raise InputError(f"config line {lineno}: unknown or malformed entry {raw.strip()!r}")
        try:
            number = float(value)
        except ValueError as err:
            raise InputError(
                f"config line {lineno}: {key} must be a number, got {value!r}"
            ) from err
        config[key] = int(number) if number.is_integer() else number
    missing = CONFIG_KEYS - config.keys()
    if missing:
        raise InputError(f"config missing keys: {', '.join(sorted(missing))}")
    return config


def _json_values(text: str) -> list:
    decoder = json.JSONDecoder()
    values, pos = [], 0
    while True:
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text):
            return values
        try:
            value, pos = decoder.raw_decode(text, pos)
        except json.JSONDecodeError as err:
            raise InputError(f"invalid JSON input at char {err.pos}: {err.msg}") from err
        values.append(value)


def _flatten(value) -> list:
    if isinstance(value, list):
        return [r for item in value for r in _flatten(item)]
    if isinstance(value, dict):
        if value.get("type") == "text" and isinstance(value.get("text"), str):
            return [r for v in _json_values(value["text"]) for r in _flatten(v)]
        if isinstance(value.get("result"), list):
            return _flatten(value["result"])
        return [value]
    raise InputError(f"unexpected JSON value of type {type(value).__name__}")


def parse_records(text: str) -> list:
    return _flatten(_json_values(text))


def hm(minutes: float | None) -> str | None:
    if minutes is None:
        return None
    total = round(minutes)
    return f"{total // 60}h {total % 60:02d}m"


def _avg(values: list, digits: int):
    return round(sum(values) / len(values), digits) if values else None


def _used(rec: dict | None) -> bool:
    return bool(rec) and (rec.get("usage_minutes") or 0) > 0


def night_flags(rec: dict | None, cfg: dict) -> list:
    if not _used(rec):
        return ["not used"]
    flags = []
    if rec["usage_minutes"] < cfg["flag_min_usage_hours"] * 60:
        flags.append(f"usage under {cfg['flag_min_usage_hours']}h")
    if (rec.get("ahi") or 0) > cfg["flag_max_ahi"]:
        flags.append(f"AHI over {cfg['flag_max_ahi']}")
    if (rec.get("leak_95th_l_per_min") or 0) > cfg["flag_max_leak_l_per_min"]:
        flags.append(f"leak over {cfg['flag_max_leak_l_per_min']} L/min")
    return flags


def _stats(recs: list) -> dict:
    used = [r for r in recs if _used(r)]
    return {
        "nights_used": len(used),
        "avg_usage_minutes": _avg([r["usage_minutes"] for r in used], 0),
        "avg_usage_hm": hm(_avg([r["usage_minutes"] for r in used], 1)),
        "avg_ahi": _avg([r.get("ahi") or 0 for r in used], 2),
        "avg_leak": _avg([r.get("leak_95th_l_per_min") or 0 for r in used], 1),
        "avg_score": _avg([r.get("myair_score") or 0 for r in used], 1),
    }


def _night_row(date: dt.date, rec: dict | None, cfg: dict) -> dict:
    row = {"date": date.isoformat(), "has_record": rec is not None}
    if rec:
        row.update({k: v for k, v in rec.items() if k != "date"})
        row["usage_hm"] = hm(rec.get("usage_minutes"))
    row["flags"] = night_flags(rec, cfg)
    return row


def summarize(records: list, days: int, today: dt.date, cfg: dict) -> dict:
    days = max(days, 1)
    start, end = today - dt.timedelta(days=days), today - dt.timedelta(days=1)
    by_date: dict = {}
    skipped = 0
    for rec in records:
        try:
            date = dt.date.fromisoformat(rec["date"])
        except (KeyError, TypeError, ValueError):
            skipped += 1
            continue
        by_date[date] = rec

    # Nights before the account's first record aren't missed therapy, so don't count them.
    clamped = bool(by_date) and start < min(by_date) <= end
    if clamped:
        start = min(by_date)
        days = (end - start).days + 1

    dates = [end - dt.timedelta(days=i) for i in range(days)]
    window = [(d, by_date.get(d)) for d in dates]
    in_window = [r for _, r in window if r]

    latest = None
    if by_date:
        newest = max(by_date)
        latest = {
            **by_date[newest],
            "usage_hm": hm(by_date[newest].get("usage_minutes")),
            "days_ago": (today - newest).days,
            "flags": night_flags(by_date[newest], cfg),
        }

    summary = _stats(in_window)
    compliant = sum(
        1 for r in in_window if (r.get("usage_minutes") or 0) >= cfg["compliance_min_hours"] * 60
    )
    summary["nights_in_window"] = days
    summary["nights_compliant"] = compliant
    summary["compliance_pct"] = round(compliant / days * 100)
    summary["meets_compliance_target"] = summary["compliance_pct"] >= cfg["compliance_target_pct"]

    result = {
        "window": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "nights": days,
            "clamped_to_first_record": clamped,
        },
        "thresholds": cfg,
        "latest": latest,
        "summary": summary,
        "flags": [
            {"date": d.isoformat(), "flags": night_flags(r, cfg)}
            for d, r in window
            if _used(r) and night_flags(r, cfg)
        ],
        "trend": _trend(window),
        "skipped": skipped,
    }
    if days <= WEEKLY_ROLLUP_AFTER_NIGHTS:
        result["nights"] = [_night_row(d, r, cfg) for d, r in window]
    else:
        result["weeks"] = _weeks(window)
    return result


def _weeks(window: list) -> list:
    weeks: dict = {}
    for d, rec in window:
        weeks.setdefault(d - dt.timedelta(days=d.weekday()), []).append((d, rec))
    rows = []
    for monday in sorted(weeks, reverse=True):
        nights = weeks[monday]
        stats = _stats([r for _, r in nights if r])
        rows.append(
            {
                "week_of": monday.isoformat(),
                "nights_in_window": len(nights),
                **{k: v for k, v in stats.items() if k != "avg_leak"},
            }
        )
    return rows


def _trend(window: list) -> dict | None:
    used = [r for _, r in sorted(window, key=lambda x: x[0]) if _used(r)]
    if len(used) < MIN_USED_NIGHTS_FOR_TREND:
        return None
    mid = len(used) // 2
    older, newer = _stats(used[:mid]), _stats(used[mid:])
    return {
        "older_half": {k: older[k] for k in ("avg_usage_hm", "avg_ahi")},
        "newer_half": {k: newer[k] for k in ("avg_usage_hm", "avg_ahi")},
        "usage_change_minutes": round(newer["avg_usage_minutes"] - older["avg_usage_minutes"]),
        "ahi_change": round(newer["avg_ahi"] - older["avg_ahi"], 2),
    }


def _direction(change: float, band: float, higher_is_better: bool) -> str:
    if abs(change) <= band:
        return "steady"
    return "better" if (change > 0) == higher_is_better else "worse"


def overview(records: list, today: dt.date, cfg: dict) -> dict:
    """Compare the last 7 nights against the last 30, using the config's trend bands."""
    windows = {}
    for name, nights in (
        ("recent", OVERVIEW_RECENT_NIGHTS),
        ("baseline", OVERVIEW_BASELINE_NIGHTS),
    ):
        result = summarize(records, nights, today, cfg)
        windows[name] = {
            "window": result["window"],
            "summary": result["summary"],
            "flagged_nights": len(result["flags"]),
            "trend": result["trend"],
        }
    comparison = {}
    for key, band_key, higher_is_better in OVERVIEW_METRICS:
        recent = windows["recent"]["summary"][key]
        baseline = windows["baseline"]["summary"][key]
        change = direction = None
        if recent is not None and baseline is not None:
            change = round(recent - baseline, 2)
            direction = _direction(change, cfg[band_key], higher_is_better)
        comparison[key] = {
            "recent": recent,
            "baseline": baseline,
            "change": change,
            "direction": direction,
        }
    return {**windows, "comparison": comparison}


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?", help="records file; reads stdin when omitted")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
        text = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
        records = parse_records(text)
        result = {
            "overview": overview(records, args.today, cfg),
            **summarize(records, args.days, args.today, cfg),
        }
    except (InputError, OSError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
