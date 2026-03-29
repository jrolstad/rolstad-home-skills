---
name: weather-check
description: Weather forecast for Brier, WA using the National Weather Service. Use when user asks "what's the weather", "weather today", "will it rain", or wants a forecast.
---

# Weather Check

Get the current forecast and meteorologist discussion for Brier, WA from the National Weather Service.

## Prerequisites

- Internet access (NWS API is free, no key required)

## Steps

### 1. Fetch Weather Data in Parallel

Simultaneously retrieve:
- NWS point metadata: fetch `https://api.weather.gov/points/47.7937,-122.2715`, then fetch the `properties.forecast` URL from the response to get the 7-day forecast
- NWS Seattle Area Forecast Discussion: fetch `https://api.weather.gov/products/types/AFD/locations/SEW`, then fetch the `@graph[0].@id` URL from the response to get the full discussion text

### 2. Generate Weather Report

Output a structured report showing the next 3 days (day and night periods), plus a plain-English summary of the forecast discussion.

```
---
## 🌤️ Weather — Brier, WA
---

| Day | Conditions | High | Low | Precip |
|-----|-----------|------|-----|--------|
| Today (Sun Mar 29) | Rain and snow likely | 46°F | 32°F | 90% |
| Monday Mar 30 | Sunny | 48°F | 32°F | 1% |
| Tuesday Mar 31 | Mostly cloudy | 54°F | 40°F | 80% night |

**Forecast Discussion:** [2-3 sentence plain-English summary of the NWS Seattle Area Forecast Discussion — what's driving the weather, any notable systems, and the outlook for the coming days]
```

### 3. Offer Follow-up Actions

```
Would you like me to:
1. Show the full 7-day forecast
2. Show the full NWS forecast discussion text
```

## Notes

- NWS grid point for Brier, WA: office SEW, gridX 128, gridY 76
- Forecast discussion (AFD) is updated several times daily by NWS Seattle meteorologists
- The forecast URL from the point metadata may change; always resolve it dynamically
