# VA Summary — Output Templates

Use only the sections matching the payload(s) the user pasted. Dates in plain form (e.g. "Feb 25,
2026"). Always label estimated dates as estimates. Close with the standard disclaimer.

---

## Claims

```
## VA Claims Summary — [Date]

### [Display title] — Claim #[id]
- **Type:** [claimType] ([claimTypeCode])
- **Filed:** [claimDate]
- **Current phase:** [phase N of 8 — plain name] (entered [phaseChangeDate])[ ⚠️ stepped back a phase — likely a new exam/evidence was ordered]
- **Status:** [plain-English status]
- **Letters:** Development letter [sent/not sent] · Decision letter [sent/not sent]
- **Documents needed from you:** [Yes/No]
- **Estimated completion:** between [minEstClaimDate] and [maxEstClaimDate] *(estimate only)*

[For a claim-detail payload, add:]
**Conditions claimed ([count]):** [bulleted contentions, grouped New vs Secondary]
**Exams:** [note completed C&P / DBQ exams by body system, if present]
**Open items you still owe:** [tracked items with NEEDED_FROM_YOU — or "None"]
```

If the payload is the **claims list**, give one compact block per claim and lead with a one-line
portfolio summary (how many claims, how many open).

---

## Rated Disabilities

```
## VA Rated Disabilities — [Date]

**Combined rating: [combined_disability_rating]%**
- Combined effective: [combined_effective_date]
- Legal effective: [legal_effective_date]

### Service-Connected (granted)
| Condition | Rating |
|---|---|
| [diagnostic_text] | [percentage]% |
*(sorted high → low; include 0% rows)*

### Not Service-Connected (denied)
- [diagnostic_text]
- ...

[1–2 sentence read: what's driving the combined rating; note 0% items are still service-connected.]
```

---

## Appeals

```
## VA Appeals — [Date]

### [Review lane] — associated claim #[id]
- **Status:** [plain-English status.type]
- **Most recent action:** [last event] on [date]
- **Next step:** [what that status means happens next]
```

If there are no appeals (`data: []`), say plainly that no appeals are on file.

---

## Standard closing (always include)

```
---
*This is a summary of your VA API data for information only — not an official VA determination.
Confirm details against your decision letter on VA.gov. For anything actionable (appeals, denied
conditions, SMC/Aid & Attendance), your VSO can advise.*
```
