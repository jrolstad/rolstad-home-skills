---
name: meal-check
description: Shows the weekly dinner plan from the Rolstad family meal planning document in Google Drive. Use when user asks "what's for dinner", "what are we eating this week", "meal plan", or wants to see upcoming meals. Do NOT use for creating or editing the meal plan.
---

# Meal Check

Get the weekly dinner plan from Google Drive.

## Prerequisites

- claude.ai Google Drive MCP connector must be active

## Steps

### 1. Read the Meal Plan Document

Call:
- `mcp__claude_ai_Google_Drive__read_file_content` (`fileId: 1ef1sAMVyfuG9ijvNDLRk7xxuLGkihPubqzS2mFTT2HE`)

### 2. Generate Dinner Report

Find today's date in the extracted text. Show meals from today through the next 7 days, spanning into the next week's section if needed. Skip days with no meal listed.

```
## 🍽️ Dinner This Week

| Day | Meal |
|-----|------|
| Sun Mar 29 | Salad |
| Mon Mar 30 | Shrimp Tacos |
| Tue Mar 31 | Burgers, Fries |
```

### 3. Offer Follow-Up Actions

```
Would you like me to:
1. Show the full meal plan
2. Show meals for a different week
```

## Notes

- Meal plan document is a Google Doc in Drive; `read_file_content` handles it natively — no export or script needed
- Pairs with `/morning-report` for a full daily briefing
