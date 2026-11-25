# Report Template

Fill the placeholders from the summarize.py output. Drop any section the SKILL.md rules say to omit.

```markdown
## 😴 Sleep Check: Last {window.nights} Nights ({window.start} to {window.end})

{device name} · last upload {last_sleep_data_report_time, Pacific, e.g. "Nov 24, 5:55 AM"}
{if latest.days_ago > 1: "> ⏳ Last night hasn't uploaded yet. Showing the most recent night on record."}

### Summary

{2–3 sentence overview: past week vs. past 30 nights, compliance, flags}

| Metric | Last 7 nights | Last 30 nights | Trend |
|--------|---------------|----------------|-------|
| Avg usage | {recent.summary.avg_usage_hm} | {baseline.summary.avg_usage_hm} | {dot} |
| Avg AHI | {comparison.avg_ahi.recent} | {comparison.avg_ahi.baseline} | {dot} |
| Avg leak | {comparison.avg_leak.recent} L/min | {comparison.avg_leak.baseline} L/min | {dot} |
| Avg myAir score | {comparison.avg_score.recent} | {comparison.avg_score.baseline} | {dot} |
| Compliance (≥{compliance_min_hours}h) | {comparison.compliance_pct.recent}% | {comparison.compliance_pct.baseline}% | {dot} |
| Flagged nights | {recent.flagged_nights} | {baseline.flagged_nights} | |

🟢 better · 🔴 worse · ⚪ steady (last 7 nights vs. last 30)

### {Last Night | Latest Night ({latest.date})}

| Usage | AHI | Leak (95th) | Mask on/off | myAir score |
|-------|-----|-------------|-------------|-------------|
| {latest.usage_hm} | {latest.ahi} | {latest.leak_95th_l_per_min} L/min | {latest.mask_on_off_count} | **{latest.myair_score}**/100 |

Score breakdown: usage {usage_score}/70 · AHI {ahi_score}/5 · mask {mask_score}/5 · leak {leak_score}/20

### Nights

| Date | Usage | AHI | Leak | Score | Flags |
|------|-------|-----|------|-------|-------|
| {Mon 11/23} | {usage_hm or "not used"} | {ahi} | {leak_95th_l_per_min} | {myair_score} | {flags joined with ", " or ""} |

### Weeks

| Week of | Nights used | Avg usage | Avg AHI | Avg score |
|---------|-------------|-----------|---------|-----------|
| {week_of} | {nights_used}/{nights_in_window} | {avg_usage_hm} | {avg_ahi} | {avg_score} |

### Window Totals

- **Nights used:** {summary.nights_used} of {summary.nights_in_window}
- **Averages (used nights):** {avg_usage_hm} usage · AHI {avg_ahi} · leak {avg_leak} L/min · score {avg_score}
- **Compliance:** {nights_compliant} of {nights_in_window} nights at ≥{compliance_min_hours}h ({compliance_pct}%), {meets | below} the {compliance_target_pct}% target
- **Trend:** {one sentence from trend}

### Flags

Thresholds: usage under {flag_min_usage_hours}h · AHI over {flag_max_ahi} · leak over {flag_max_leak_l_per_min} L/min

- {date}: {flags}

_Data from ResMed myAir. Informational only. Ask your care provider about anything that concerns you._
```
