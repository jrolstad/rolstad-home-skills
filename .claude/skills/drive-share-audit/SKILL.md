---
name: drive-share-audit
description: Audits Google Drive (My Drive) for items the user owns that are shared directly with other people, groups, domains, or via link, listing who has access and at what role. Only direct shares are reported; items that are shared only because a parent folder is shared are left out. Scans 200k+ items in a few minutes via a local Drive API script. Use when the user asks "what have I shared in Drive", "who has access to my Drive", "drive share audit", "shared files report", "who did I share with", "drive shares by person", or "anything public in my Drive". Do NOT use for files others shared with the user, for changing or removing sharing, or for reading file contents.
---

# Drive Share Audit

Report every item the user owns inside their own My Drive folder tree that carries a **direct** share, either as a full audit by item or as a summary by person. Items the user owns but stores in someone else's folder are left out.

## How it works

`scripts/drive_shares.py` lists the user's folders, then the contents of every folder in their My Drive tree through batched Drive API requests (about a minute for 80k items), then treats a permission as direct when the item has it and its parent folder does not. Only those items get a full permission fetch. Known limit: a grantee whose role is raised on a child (reader on the folder, writer on a file inside it) is treated as inherited and not reported.

Do not attempt this audit with the claude.ai Google Drive connector: it cannot filter for shared items and reads permissions one item per call.

## Steps

### 1. Run the script

From this skill's directory, run in the background (a full scan takes a few minutes):

```bash
uv run scripts/drive_shares.py
```

- Progress goes to stderr. The last stdout line is a JSON summary with `items_scanned`, `shared_items`, `direct_share_items`, `elapsed_seconds`, and `output` (the full result path, default `output/latest.json`).
- If it opens a browser, the saved token is missing or expired. Tell the user to finish the Google sign-in in the browser window, then wait for the run to finish.
- If it exits with an error, read `references/setup.md` for the fix, report the error, and stop.

### 2. Read the result

Read the `output` JSON file. Each entry in `items` has `name`, `kind` (folder or file), `path`, `link`, and `grants` (`type`, `role`, `email`, `name`, `domain`, `discoverable`).

Grant `type` meanings:
- `user` / `group`: a specific account; show `email`.
- `domain`: everyone at `domain`.
- `anyone`: anyone with the link (`discoverable: true` means also findable by search).

### 3. Write the report

If `direct_share_items` is 0, say so in one line and stop. Otherwise pick the format:

- **Summary by person** (the user asks for shares "by person", "per person", or "who each person can see"): go to 3a.
- **Otherwise** (default full audit): go to 3b.

#### 3a. Summary by person

Read `assets/by-person-template.md` for the exact output format. Rules:
- Write one section per `user`/`group` email, sorted by number of items descending, then by email.
- Within each section, list every item that person has (no truncation), sorted by path.
- After the people, add the **Public / anyone with link** and **Domain-wide** sections from `assets/report-template.md`.

#### 3b. Full audit

Read `assets/report-template.md` for the exact output format. Rules:
- List `anyone` grants first under **Public / anyone with link**, then `domain` grants.
- In **By item**, sort by path.

### 4. Follow-up questions

For drill-down questions about a single item ("who else can see X?", "what's inside that shared folder?"), use the claude.ai Google Drive connector (`get_file_permissions`, `search_files` with `parentId`) rather than re-running the full scan.
