"""Tests for summarize.py. Run: python -m pytest <skill-dir>/scripts"""

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import summarize

TODAY = dt.date(2026, 11, 24)
CFG = summarize.load_config(summarize.DEFAULT_CONFIG)


def rec(days_ago: int, usage: int = 420, ahi: float = 0.5, leak: float = 10.0, score: int = 100):
    return {
        "date": (TODAY - dt.timedelta(days=days_ago)).isoformat(),
        "usage_minutes": usage,
        "ahi": ahi,
        "leak_95th_l_per_min": leak,
        "mask_on_off_count": 1,
        "myair_score": score,
    }


def run(records, days=7):
    return summarize.summarize(records, days, TODAY, CFG)


def test_default_config_has_expected_thresholds():
    assert CFG == {
        "flag_min_usage_hours": 4,
        "flag_max_ahi": 5,
        "flag_max_leak_l_per_min": 24,
        "compliance_min_hours": 4,
        "compliance_target_pct": 70,
        "trend_usage_minutes": 15,
        "trend_ahi": 0.5,
        "trend_leak_l_per_min": 2,
        "trend_score": 2,
        "trend_compliance_pct": 5,
    }


def test_overview_compares_last_7_with_last_30():
    # Older 23 nights: 6h, AHI 2.0. Last 7: 8h, AHI 0.5. Leak and score flat.
    records = [rec(i, usage=480, ahi=0.5) for i in range(1, 8)]
    records += [rec(i, usage=360, ahi=2.0) for i in range(8, 31)]
    ov = summarize.overview(records, TODAY, CFG)
    assert ov["recent"]["window"]["nights"] == 7
    assert ov["baseline"]["window"]["nights"] == 30
    c = ov["comparison"]
    assert c["avg_usage_minutes"] == {
        "recent": 480,
        "baseline": 388,
        "change": 92,
        "direction": "better",
    }
    assert c["avg_ahi"]["direction"] == "better"
    assert c["avg_leak"]["direction"] == "steady"
    assert c["avg_score"]["direction"] == "steady"
    assert c["compliance_pct"]["direction"] == "steady"


def test_overview_worse_and_band_edges():
    assert summarize._direction(-16, 15, True) == "worse"
    assert summarize._direction(15, 15, True) == "steady"
    assert summarize._direction(0.6, 0.5, False) == "worse"
    assert summarize._direction(-0.6, 0.5, False) == "better"


def test_overview_with_no_used_nights_has_no_direction():
    ov = summarize.overview([rec(i, usage=0) for i in range(1, 31)], TODAY, CFG)
    assert ov["comparison"]["avg_ahi"] == {
        "recent": None,
        "baseline": None,
        "change": None,
        "direction": None,
    }
    assert ov["comparison"]["compliance_pct"]["direction"] == "steady"


def test_config_changes_flag_thresholds(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    text = summarize.DEFAULT_CONFIG.read_text().replace("flag_max_ahi: 5", "flag_max_ahi: 1")
    cfg_file.write_text(text)
    cfg = summarize.load_config(cfg_file)
    result = summarize.summarize([rec(1, ahi=2.0)], 7, TODAY, cfg)
    assert result["flags"] == [{"date": "2026-11-23", "flags": ["AHI over 1"]}]


@pytest.mark.parametrize(
    "text, message",
    [
        ("flag_max_ahi: five\n", "must be a number"),
        ("flag_max_ahii: 5\n", "unknown or malformed"),
        ("flag_max_ahi: 5\n", "missing keys"),
    ],
)
def test_bad_config_rejected(tmp_path, text, message):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(text)
    with pytest.raises(summarize.InputError, match=message):
        summarize.load_config(cfg_file)


def test_window_counts_missing_dates_as_unused():
    result = run([rec(1), rec(3), rec(40)])
    assert result["window"] == {
        "start": "2026-11-17",
        "end": "2026-11-23",
        "nights": 7,
        "clamped_to_first_record": False,
    }
    assert result["summary"]["nights_in_window"] == 7
    assert result["summary"]["nights_used"] == 2
    nights = result["nights"]
    assert [n["date"] for n in nights][:3] == ["2026-11-23", "2026-11-22", "2026-11-21"]
    assert nights[1] == {"date": "2026-11-22", "has_record": False, "flags": ["not used"]}


def test_window_clamped_to_first_record_for_all_time():
    result = run([rec(1), rec(2, usage=0), rec(3)], days=3650)
    assert result["window"]["start"] == "2026-11-21"
    assert result["window"]["nights"] == 3
    assert result["window"]["clamped_to_first_record"] is True
    assert result["summary"]["compliance_pct"] == 67
    assert "nights" in result


def test_records_outside_window_ignored_for_stats_but_latest_is_newest():
    result = run([rec(1, usage=400), rec(30, usage=100)])
    assert result["summary"]["nights_used"] == 1
    assert result["latest"]["date"] == "2026-11-23"
    assert result["latest"]["days_ago"] == 1


def test_zero_usage_excluded_from_averages_but_counted_in_compliance():
    result = run([rec(1, usage=480, ahi=1.0), rec(2, usage=0, ahi=0.0, score=0)], days=2)
    s = result["summary"]
    assert s["nights_used"] == 1
    assert s["avg_usage_hm"] == "8h 00m"
    assert s["avg_ahi"] == 1.0
    assert s["avg_score"] == 100
    assert s["compliance_pct"] == 50
    assert s["meets_compliance_target"] is False


def test_compliance_target():
    result = run([rec(i) for i in range(1, 6)] + [rec(6, usage=200), rec(7, usage=0)])
    assert result["summary"]["nights_compliant"] == 5
    assert result["summary"]["compliance_pct"] == 71
    assert result["summary"]["meets_compliance_target"] is True


def test_each_flag():
    result = run([rec(1, usage=200), rec(2, ahi=6.1), rec(3, leak=30.0), rec(4)])
    assert result["flags"] == [
        {"date": "2026-11-23", "flags": ["usage under 4h"]},
        {"date": "2026-11-22", "flags": ["AHI over 5"]},
        {"date": "2026-11-21", "flags": ["leak over 24 L/min"]},
    ]


def test_threshold_boundaries_not_flagged():
    result = run([rec(1, usage=240, ahi=5.0, leak=24.0)])
    assert result["flags"] == []


def test_nights_until_14_then_weeks():
    records = [rec(i) for i in range(1, 31)]
    assert "nights" in run(records, days=14) and "weeks" not in run(records, days=14)
    weeks = run(records, days=15)["weeks"]
    assert "nights" not in run(records, days=15)
    assert weeks[0]["week_of"] == "2026-11-23"
    assert sum(w["nights_in_window"] for w in weeks) == 15


def test_trend_needs_four_used_nights():
    assert run([rec(1), rec(2), rec(3)])["trend"] is None
    trend = run([rec(4, usage=300, ahi=2.0), rec(3, usage=300, ahi=2.0), rec(2), rec(1)])["trend"]
    assert trend["usage_change_minutes"] == 120
    assert trend["ahi_change"] == -1.5


def test_empty_input():
    result = run([])
    assert result["latest"] is None
    assert result["summary"]["nights_used"] == 0
    assert result["summary"]["avg_ahi"] is None
    assert result["summary"]["compliance_pct"] == 0


def test_records_without_date_are_skipped():
    assert run([rec(1), {"usage_minutes": 400}])["skipped"] == 1


def test_parses_concatenated_objects_as_mcp_renders_them():
    text = "\n".join(json.dumps(r, indent=2) for r in [rec(1), rec(2)])
    assert [r["date"] for r in summarize.parse_records(text)] == ["2026-11-23", "2026-11-22"]


def test_parses_array_and_tool_results_file():
    records = [rec(1), rec(2)]
    assert summarize.parse_records(json.dumps(records)) == records
    blocks = [{"type": "text", "text": json.dumps(r, indent=2)} for r in records]
    assert summarize.parse_records(json.dumps(blocks)) == records


def test_bad_json_exits_nonzero(tmp_path, capsys):
    bad = tmp_path / "bad.txt"
    bad.write_text('{"date": "2026-11-23", ')
    assert summarize.main([str(bad)]) == 1
    assert "invalid JSON" in capsys.readouterr().err


def test_cli_end_to_end(tmp_path, capsys):
    data = tmp_path / "records.txt"
    data.write_text("\n".join(json.dumps(r, indent=2) for r in [rec(1), rec(2)]))
    assert summarize.main(["--days", "2", "--today", "2026-11-24", str(data)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["summary"]["nights_used"] == 2
    assert out["overview"]["baseline"]["window"]["nights"] == 2
    assert out["overview"]["comparison"]["avg_ahi"]["direction"] == "steady"
