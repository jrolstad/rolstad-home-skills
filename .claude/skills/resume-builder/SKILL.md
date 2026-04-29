---
name: resume-builder
description: |
  Tailors a resume to a specific job posting, validates existing resumes in Google Drive against a job description, and generates a targeted cover letter. Use when user asks to "build a resume", "tailor my resume", "update my resume for a job", "validate my resume", "check my resume against a job", or "write a cover letter". Operates in three modes: Build (tailor a new resume for a role), Validate (score existing Drive resumes against a job description), and Cover Letter (draft a cover letter with user input). Do NOT use for general writing help, career coaching, or job search strategy unrelated to resume or cover letter content.
---

# Resume Builder

Tailor, validate, and generate resumes and cover letters targeted to specific job postings. Ensures ATS compatibility and strong alignment with role requirements.

## Prerequisites

- Google Workspace MCP server must be running
- User provides a job description or job posting URL (copy/paste or link)
- Resume source: Google Drive folder `0B4BtZJ4ZrcRca05TbWxOWWd1SU0`

## Modes

Determine which mode to run based on user intent:

- **Build** — tailor a resume for a new job description (default)
- **Validate** — score one or more existing Drive resumes against a job description
- **Cover Letter** — draft a targeted cover letter (runs after Build, or standalone)

---

## Mode: Build

### Step 1 — Collect the Job Description

Ask the user to provide the job posting. Accept any of:
- Pasted text
- A URL (use WebFetch to retrieve the full page text)

Extract and document:
- **Company name** and **role title**
- **Required skills and qualifications** (hard requirements)
- **Preferred skills** (nice-to-haves)
- **Key responsibilities**
- **ATS keywords** — exact phrases, tools, technologies, and titles used in the posting

### Step 2 — Fetch Existing Resumes from Google Drive

Call `mcp__google-workspace__search_drive_files` with:
- `query`: `'0B4BtZJ4ZrcRca05TbWxOWWd1SU0' in parents`
- `user_google_email`: jrolstad@gmail.com

List all files found. For each file, read content based on type:
- **Google Doc**: call `mcp__google-workspace__get_doc_content` using the file ID
- **Word (.docx) or PDF**: call `mcp__google-workspace__get_drive_file_download_url` with `export_format: docx` or `pdf`, then read the downloaded file

If multiple resume versions exist, present the list to the user and ask which to use as the base. Default to the most recently modified file.

### Step 3 — Analyze and Reason

Before generating recommendations, reason through all of the following:

1. **Keyword gap analysis**: Which ATS keywords from the job description are missing or underrepresented in the current resume?
2. **Skill alignment**: Which required skills are covered? Which are gaps?
3. **Responsibility match**: How well does current experience align with the listed responsibilities? Which bullet points should be rewritten to use the job's language?
4. **Strength identification**: What achievements, roles, or projects in the resume are most compelling for this specific role?
5. **ATS structural risks**: Are there formatting issues (tables, headers, columns, graphics) that could cause ATS parsing failures?
6. **Title and summary alignment**: Does the resume's title or summary reflect the target role?

Show this analysis to the user as a structured pre-flight report before presenting changes.

**Pre-flight report format:**
```
## Resume Analysis — [Role Title] at [Company]

### ATS Keyword Gaps
- Missing: [keyword], [keyword], [keyword]
- Present: [keyword], [keyword]

### Skill Coverage
| Skill | Required? | In Resume? | Notes |
|-------|-----------|------------|-------|
| Python | Yes | ✅ Yes | |
| Kubernetes | Yes | ❌ No | Adjacent: Docker mentioned |
| GraphQL | Preferred | ❌ No | |

### Strongest Resume Sections for This Role
- [section or bullet that maps well, and why]

### ATS Structural Issues
- [any formatting risks, or "None detected"]

### Recommended Strategy
[2-3 sentences summarizing the overall tailoring approach]
```

### Step 4 — Generate Tailored Resume

Produce the full tailored resume in Markdown, following these ATS rules:

**ATS Rules (never violate):**
- Plain text structure — no tables, columns, text boxes, or images
- Standard section headers: Summary, Experience, Skills, Education, Certifications
- Job title in resume summary must mirror (or closely match) the target role title
- Bullet points start with strong action verbs
- Quantify achievements wherever the base resume provides numbers
- Include exact keyword phrases from the job description naturally in context
- No headers/footers with contact info (repeat contact info in plain text at the top)
- File format note: recommend saving as .docx, not .pdf, for ATS submission unless PDF is specified

**Tailoring rules:**
- Reorder Skills section to lead with skills most relevant to the posting
- Rewrite experience bullets to use the job description's vocabulary where truthful
- Add keywords naturally — never fabricate experience
- If a preferred skill is not in the resume but adjacent work exists, note it in the summary or a relevant bullet
- Remove or demote bullets that are irrelevant to the role to keep the resume focused

### Step 5 — Interactive Revision Loop

After presenting the tailored resume, ask:

```
Resume draft complete. What would you like to do next?
1. Edit a specific section
2. Strengthen a particular bullet point
3. Add or remove content
4. Re-check ATS keyword coverage
5. Proceed to cover letter
6. Save this version to Google Drive
7. Done
```

Handle each choice and loop back to this menu after each action. Continue until the user says "done" or selects option 7.

**Saving to Google Drive:**
- Call `mcp__google-workspace__create_doc` with title `Resume — [Role Title] — [Company] — [YYYY-MM-DD]`
- Place it in the resume folder: parent `0B4BtZJ4ZrcRca05TbWxOWWd1SU0`
- Confirm the link after creation

---

## Mode: Validate

Use when user asks to validate or score a resume against a job description.

### Step 1 — Collect Job Description

Same as Build Step 1.

### Step 2 — List Resumes

Fetch all files from the Drive folder (same as Build Step 2). Present the list and ask which resume(s) to validate. Accept "all" to validate every file.

### Step 3 — Score Each Resume

For each selected resume, produce a scorecard:

```
## Resume Scorecard — [Filename]

| Category | Score | Notes |
|----------|-------|-------|
| ATS Keyword Coverage | 7/10 | Missing: Kubernetes, CI/CD |
| Required Skills Match | 8/10 | All hard requirements covered |
| Preferred Skills Match | 4/10 | 2 of 5 preferred skills present |
| Role Responsibility Alignment | 6/10 | Strong on delivery, weak on people mgmt language |
| ATS Structural Safety | 10/10 | Clean formatting |
| **Overall** | **35/50** | |

### Top 3 Improvements
1. [Most impactful change]
2. [Second change]
3. [Third change]
```

After scoring all selected resumes, recommend which version is the strongest base for this role.

---

## Mode: Cover Letter

Runs after Build (Step 5 option 5) or standalone when user asks for a cover letter.

### Step 1 — Gather Inputs

Ask the following questions one at a time. Wait for each answer before asking the next:

1. "Why does this role appeal to you? What about the work itself excites you?"
2. "What do you know or admire about [Company]? Any specific products, mission, culture, or news?"
3. "Is there a specific achievement or project from your experience you want to anchor the letter around?"
4. "Any constraints — length preference, tone (formal vs. conversational), or anything to avoid?"

### Step 2 — Generate Cover Letter

Write a targeted cover letter following this structure:

- **Opening paragraph**: Hook connecting the candidate's background to the specific role and company. Name the role and company explicitly. Reference something specific about the company (from user input or job posting).
- **Body paragraph 1**: Most relevant experience mapped directly to the role's top responsibilities. Use keywords from the job posting.
- **Body paragraph 2**: Key achievement or project that demonstrates impact. Quantify if possible.
- **Closing paragraph**: Why this company specifically (use user's answer). Express genuine enthusiasm. Clear call to action.

**Constraints:**
- Maximum 400 words
- No filler phrases ("I am writing to apply for...", "I am a passionate...")
- Mirror the tone of the company's job posting (formal → formal, conversational → conversational)
- Do not repeat the resume bullet-for-bullet — complement it, don't duplicate it

### Step 3 — Interactive Revision

Present the cover letter and ask:

```
Cover letter draft complete. What would you like to do next?
1. Adjust the tone
2. Strengthen a specific paragraph
3. Shorten or lengthen
4. Save to Google Drive
5. Done
```

**Saving to Google Drive:**
- Call `mcp__google-workspace__create_doc` with title `Cover Letter — [Role Title] — [Company] — [YYYY-MM-DD]`
- Place in the same resume folder
- Confirm the link after creation

---

## Error Handling

- If Drive folder returns no files: notify the user and ask them to paste resume content directly.
- If a file cannot be read (format unsupported): skip it, note the failure, and continue with remaining files.
- If the job description URL cannot be fetched: ask the user to paste the text directly.
- If a required input is not provided: ask for it explicitly before proceeding. Do NOT proceed with assumptions.
- If a step fails: STOP and report the exact failure before attempting the next step.
