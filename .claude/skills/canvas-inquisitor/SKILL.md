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
  days_upcoming: 7,
  low_grade_threshold: 70
)

mcp__canvas-mtgibbs__get_recent_grades(
  student_id: [each student_id],
  days: 14
)
```

`get_all_students_status` returns courses, current grades, missing work, and upcoming assignments. `get_recent_grades` returns individual assignment scores from the last 14 days, used to compute grade trend per course.

### 3. Produce the Grade Report

Load `assets/report-template.md` for output structure. For each student, populate:

**Current Grades** — list all courses with their current score percentage and a trend indicator. Exclude any course whose name contains a keyword from `excluded_course_keywords` (loaded in Step 0). Also exclude courses with no current score. Sort by course name ascending (A–Z).

To compute the trend for each course, use `get_recent_grades` data (14 days) split into two 7-day buckets:
- **This week** — assignments graded in the last 7 days
- **Last week** — assignments graded 7–14 days ago

For each course, compute the average percentage in each bucket:
- diff = this week avg − last week avg
- diff > +0.5 → 🟢
- diff < −0.5 → 🔴
- Otherwise → ⚪

Show the dot followed by the signed diff rounded to 2 decimal places (e.g. `🟢 +1.25`, `🔴 -0.82`, `⚪ +0.10`). If one or both buckets have no grades for the course, show `⚪ —`.

**Missing / Unsubmitted** — assignments Canvas has flagged as missing or that are past due with no submission. Show assignment name, course, and due date.

**Recent Low Grades** — assignments graded below 70% in the last 14 days. Show assignment name, score, points possible, percentage, and course.

**Due This Week** — upcoming assignments due in the next 7 days. Show assignment name, course, and due date. Omit already-graded assignments.

If a section has no items, show *(None)*.

### 4. Offer Follow-up Actions

```
Would you like me to:
1. 🔍 Drill into a specific course for a student
2. 📋 Show all assignments for a course
3. 📅 Show what's due this week in detail
4. ⚠️  Show only missing assignments
5. 📊 Show full grade history (last 30 days)
```

**If the user chooses option 1:** Ask which student and course, then call `mcp__canvas-mtgibbs__get_courses(student_id: ...)` to get the course_id, then `mcp__canvas-mtgibbs__list_assignments(course_id: ..., student_id: ...)` for full assignment detail.

**If the user chooses option 2:** Ask which course, then call `mcp__canvas-mtgibbs__list_assignments(course_id: ..., student_id: ...)`.

**If the user chooses option 3:** Call `mcp__canvas-mtgibbs__get_due_this_week(days: 7, hide_graded: false)` for each student and display all due dates with full detail.

**If the user chooses option 4:** Call `mcp__canvas-mtgibbs__get_missing_assignments(student_id: ...)` for each student and display only missing work.

**If the user chooses option 5:** Call `mcp__canvas-mtgibbs__get_recent_grades(student_id: ..., days: 30)` for each student and display full grade history.
