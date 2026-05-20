## {{period_label}} Weather Summary — {{station_name}} ({{station_location}})

**Conditions in plain language:** {{narrative_paragraph}}

**Currently** (latest reading): {{current_temp}}°F, {{current_humidity}}% humidity, {{current_wind_description}}, pressure {{current_pressure}} inHg, AQI {{current_aqi}}.

{{record_count}} records spanning roughly the last {{period_words}} ({{oldest_utc}} → {{newest_utc}}).

| Metric | Range / Value |
|---|---|
| **Temperature** | {{tempf_min}}°F → {{tempf_max}}°F, avg **{{tempf_avg}}°F** |
| **Feels like** | {{feels_min}}°F → {{feels_max}}°F |
| **Rain** | {{rain_summary}} |
| **Wind** | {{wind_summary}} |
| **UV index** | max {{uv_max}}{{uv_note}} |
| **Air quality** | AQI PM2.5 ranged {{aqi_min}}–{{aqi_max}}, currently **{{current_aqi}} ({{aqi_category}})** |
| **Dew point** | {{dew_min}}°F → {{dew_max}}°F, avg {{dew_avg}}°F |
| **Humidity** | {{humidity_min}}% → {{humidity_max}}%, avg **{{humidity_avg}}%** |
| **Pressure** | {{baro_min}} → {{baro_max}} inHg ({{baro_swing_note}}) |
| **Solar** | peak {{solar_max}} W/m² ({{solar_note}}), avg {{solar_avg}} W/m² |

<!-- Append the per-day section only when days > 1 -->

### Per-Day Highlights (UTC days)

| Day | High / Low / Avg °F | Rain (in) | Gust (mph) | AQI |
|---|---|---|---|---|
| {{day_utc}} | {{tempf_max}} / {{tempf_min}} / {{tempf_avg}} | {{daily_rain_max_in}} | {{wind_gust_max_mph}} | {{aqi_pm25_max}} |
