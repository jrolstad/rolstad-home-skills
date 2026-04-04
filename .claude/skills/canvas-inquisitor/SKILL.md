---
name: canvas-inquisitor
description: Reports on current student grades, missing assignments, and upcoming work from Canvas LMS. Use when asked about "canvas grades", "how are students doing", "missing assignments", "student grades", or "canvas inquisitor". Do not use for managing assignments, posting grades, or non-grade queries. Requires the canvas-mtgibbs MCP server to be running.
---

# Canvas Inquisitor

Fetch the academic status for all observed students and produce a structured grade report.

## Steps

### 0. Load Config

Read `config.yaml` (in this skill's directory) to load:
- `excluded_course_keywords` — course names containing any of these keywords are hidden from the Current Grades section
- `sender_email` — use as `user_google_email` for Google Workspace tool calls
- `recipients` — use for the send action in Step 4

### 1. Fetch All Observed Students

Call:

```
mcp__canvas-mtgibbs__get_students()
```

**If 0 students are returned:** Stop and inform the user that no observed students were found in Canvas.

**If 1 or more students are returned:** Proceed to Step 2.

### 2. Fetch Status and Recent Grades for All Students

Call both in parallel for each student:

```
mcp__canvas-mtgibbs__get_all_students_status(
  days_grades: 14,
  low_grade_threshold: 70
)

mcp__canvas-mtgibbs__get_recent_grades(
  student_id: [each student_id],
  days: 14
)
```

`get_all_students_status` returns courses, current grades, and missing work. `get_recent_grades` returns individual assignment scores from the last 14 days, used to compute grade trend and identify low grades per course.

### 3. Produce the Grade Report

Load `assets/report-template.md` for output structure. For each student, populate:

**Summary** — a 2–3 sentence plain-English overview before the grades table. Only reference courses that appear in the table (i.e. after exclusions are applied). Call out the overall grade picture, highlight any 🟢 or 🔴 trends with brief context (e.g. which assignment caused the shift), and note anything actionable (missing work, low grades). Keep it conversational.

**Current Grades** — a single table with columns: Course, Grade, Trend, Missing, Low Grades. Exclude any course whose name contains a keyword from `excluded_course_keywords` (loaded in Step 0). Also exclude courses with no current score. Sort by course name ascending (A–Z).

- **Grade** — current score percentage.
- **Trend** — computed from `get_recent_grades` data (14 days) split into two 7-day buckets:
  - **This week** — assignments graded in the last 7 days
  - **Last week** — assignments graded 7–14 days ago
  - For each course, compute the average percentage in each bucket:
    - diff = this week avg − last week avg
    - diff > +0.5 → 🟢
    - diff < −0.5 → 🔴
    - Otherwise → ⚪
  - Show only the dot. If one or both buckets have no grades for the course, show ⚪.
- **Missing** — count of assignments Canvas has flagged as missing or past due with no submission for that course. Show the count (e.g. `2`) or `—` if none. On a separate line below the table, list each missing assignment: name, course, and due date.
- **Low Grades** — count of assignments graded below 70% in the last 14 days for that course. Show the count (e.g. `1`) or `—` if none. On a separate line below the table, list each low-grade assignment: name, score, points possible, percentage, and course.

### 4. Offer Follow-up Actions

```
Would you like me to:
1. 🔍 Drill into a specific course for a student
2. 📋 Show all assignments for a course
3. ⚠️  Show only missing assignments
4. 📊 Show full grade history (last 30 days)
5. 📧 Email this report to recipients
```

**If the user chooses option 1:** Ask which student and course, then call `mcp__canvas-mtgibbs__get_courses(student_id: ...)` to get the course_id, then `mcp__canvas-mtgibbs__list_assignments(course_id: ..., student_id: ...)` for full assignment detail.

**If the user chooses option 2:** Ask which course, then call `mcp__canvas-mtgibbs__list_assignments(course_id: ..., student_id: ...)`.

**If the user chooses option 3:** Call `mcp__canvas-mtgibbs__get_missing_assignments(student_id: ...)` for each student and display only missing work.

**If the user chooses option 4:** Call `mcp__canvas-mtgibbs__get_recent_grades(student_id: ..., days: 30)` for each student and display full grade history.

**If the user chooses option 5:** Send the grade report as an email to the recipients from `config.yaml` using:

```
mcp__google-workspace__send_gmail_message(
  to: recipients[0],
  cc: recipients[1],
  subject: "Canvas Inquisitor — [Date]",
  body: "[full grade report as HTML]",
  body_format: "html",
  user_google_email: sender_email
)
```

Construct the body as HTML so tables render correctly in Gmail:
- **Opening:** A single sentence in a `<p>` tag explaining what this is. Example: `<p>Canvas Inquisitor grade report for April 4, 2026.</p>`
- **Summary:** The summary text in a `<p>` tag.
- **Grades table:** An HTML `<table>` with a header row and one row per course. Use inline styles for borders and padding (e.g. `border: 1px solid #ddd; padding: 8px;`) since Gmail strips `<style>` blocks.
- **Legend:** A `<p>` below the table explaining trend dots.

Confirm to the user once the email has been sent.
