---
name: hawk-highlighter
description: Fetches all "Hawk Highlights" school newsletter emails from Gmail, selects the two most recent, and produces a diff report showing only what is new or changed. Use when the user asks about "hawk highlights", "what's new in hawk highlights", or "hawk highlighter". Do not use for comparing other emails, general Gmail search, or non-Hawk-Highlights newsletters. Requires the claude.ai Gmail MCP connector to be active.
---

# Hawk Highlighter

Fetch all Hawk Highlights emails, identify the two most recent issues, and report what is new or changed between them.

## Steps

### 0. Load Config

Read `config.yaml` (in this skill's directory) to load:
- `recipients` — use for the send action in Step 4

### 1. Search Gmail for All Hawk Highlights Emails

Search Gmail for all threads matching the subject:

```
mcp__claude_ai_Gmail__search_threads(
  query: '"Hawk Highlights" in:anywhere',
  pageSize: 20
)
```

**If 0 emails are found:** Stop and inform the user that no Hawk Highlights emails were found in their inbox.

**If exactly 1 email is found:** Skip to Step 3, display its full content, and note there is no previous issue to compare against.

**If 2 or more emails are found:** Sort all results by received date descending (newest first). Take the top 2. Proceed to Step 2.

### 2. Fetch Full Content of Both Threads

Fetch the full body of each thread in parallel:

```
mcp__claude_ai_Gmail__get_thread(threadId: id_of_newest, messageFormat: FULL_CONTENT)
mcp__claude_ai_Gmail__get_thread(threadId: id_of_second_newest, messageFormat: FULL_CONTENT)
```

The first result is the current issue. The second result is the previous issue.

### 3. Produce the Diff Report

Analyze both email bodies. Focus on meaningful content changes only — ignore formatting, whitespace, and boilerplate (counselor contacts, nurse health alert, standard footer).

Use the template at `assets/report-template.md` for output structure. Populate:

**New This Week** — content that appears in the current issue but not the previous one (new announcements, events, athlete of the week, etc.).

**Changed** — content present in both issues but with updated details (dates, prices, names, locations).

**Unchanged** — a single brief sentence summarizing recurring sections that did not change. Do not reprint their content.

### 4. Offer Follow-up Actions

```
Would you like me to:
1. 📧 Send these results to the recipients in config.yaml
2. 📄 Show the full text of the current issue
3. 📄 Show the full text of the previous issue
4. 🔍 Search for an older issue
```

**If the user chooses option 1:** Create a Gmail draft for the recipients from `config.yaml` using:

```
mcp__claude_ai_Gmail__create_draft(
  to: [recipients[0]],
  cc: [recipients[1]],
  subject: "Hawk Highlighter — [Current Issue Date] vs [Previous Issue Date]",
  body: "[intro sentence]\n\n[full diff report]"
)
```

Construct the body as follows:
- **First line:** A single sentence explaining what Hawk Highlighter is and which issues are compared. Example: `Hawk Highlighter summarizes what's new and changed in the MTHS Hawk Highlights newsletter — below is a comparison of the Apr 5, 2026 issue (Week 32) vs the Mar 29, 2026 issue (Week 31).`
- **Remainder:** The full diff report text (New This Week, Changed, Unchanged sections).

Confirm to the user once the draft has been created (they will need to review and send it from Gmail).
