---
name: meal-check
description: Shows the weekly dinner plan from the Rolstad family meal planning document in Google Drive. Use when user asks "what's for dinner", "what are we eating this week", "meal plan", or wants to see upcoming meals. Do NOT use for creating or editing the meal plan.
---

# Meal Check

Get the weekly dinner plan from Google Drive.

## Prerequisites

- Google Workspace MCP server must be running

## Steps

### 1. Download Meal Plan Document

Call:
- `mcp__google-workspace__get_drive_file_download_url` (`file_id: [meal_plan_doc_id]`, `export_format: docx`, `user_google_email: jrolstad@gmail.com`)

### 2. Extract Text

Run:
- `Bash`: `python .claude/skills/meal-check/extract_docx_text.py <local_path>` using the path returned in Step 1

### 3. Generate Dinner Report

Find today's date in the extracted text. Show meals from today through the next 7 days, spanning into the next week's section if needed. Skip days with no meal listed.

```
## 🍽️ Dinner This Week

| Day | Meal |
|-----|------|
| Sun Mar 29 | Salad |
| Mon Mar 30 | Shrimp Tacos |
| Tue Mar 31 | Burgers, Fries |
```

### 4. Offer Follow-up Actions

```
Would you like me to:
1. Show the full meal plan
2. Show meals for a different week
```

## Notes

- Meal plan document is stored in Google Drive
- Pairs with `/morning-report` for a full daily briefing
