# VA Field Glossary

Reference for interpreting the JSON. The VA API is undocumented; treat these as best-known meanings
and report raw values when something is unrecognized.

## Claim status (`attributes.status`)

| Value | Plain English |
|---|---|
| `CLAIM_RECEIVED` | Claim received, not yet assigned |
| `INITIAL_REVIEW` | A reviewer has begun looking at the claim |
| `EVIDENCE_GATHERING_REVIEW_DECISION` | Active middle stage — gathering evidence, review, and decision prep |
| `PREPARATION_FOR_NOTIFICATION` | Decision made, preparing the notification letter |
| `COMPLETE` | Claim closed; decision letter available |

## Claim phases (`claimPhaseDates.phaseType` / `latestPhaseType`)

VA.gov shows an 8-step tracker:

1. `CLAIM_RECEIVED` — Claim received
2. `UNDER_REVIEW` — Initial review
3. `GATHERING_OF_EVIDENCE` — Evidence gathering
4. `REVIEW_OF_EVIDENCE` — Review of evidence
5. `PREPARATION_FOR_DECISION` — Preparation for decision
6. `PENDING_DECISION_APPROVAL` — Pending decision approval
7. `PREPARATION_FOR_NOTIFICATION` — Preparation for notification
8. `COMPLETE` — Complete

- `phaseChangeDate` — when the claim entered its current phase.
- `currentPhaseBack: true` — the claim **moved backward** a step (commonly because a new exam or
  additional evidence was ordered). Call this out; it is meaningful.
- `previousPhases.phaseXCompleteDate` — timestamps for completed phases.

## Key claim flags

| Field | Meaning |
|---|---|
| `developmentLetterSent` | A letter requesting evidence was sent (boolean only — **no date** is provided) |
| `decisionLetterSent` | A decision letter has been sent |
| `documentsNeeded` | The VA is waiting on documents |
| `evidenceWaiverSubmitted5103` | The veteran waived the 5103 evidence-gathering wait |
| `minEstClaimDate` / `maxEstClaimDate` | Estimated completion **window** — estimates only, not guaranteed |
| `claimTypeCode` | e.g. `010LCOMP` (disability compensation), `130DPNDCY` (dependency add/remove) |

## Contentions (`attributes.contentions[]`)

Each is a condition being claimed. The suffix tags the basis:
- `(New)` — newly claimed condition.
- `(Secondary)` — claimed as caused by another service-connected condition.

## Tracked items (`attributes.trackedItems[]`)

Things the VA requested. Status values:
- `NEEDED_FROM_YOU` / `uploadsAllowed: true` — **action needed**: the veteran owes this.
- `NEEDED_FROM_OTHERS` — the VA requested it from a third party (e.g., private records).
- `NO_LONGER_REQUIRED` — closed, nothing to do.
- `INITIAL_REVIEW_COMPLETE` / `SUBMITTED_AWAITING_REVIEW` — received.

`friendlyName` (e.g. "Non-VA medical records", "Authorization to disclose information") is the
human-readable label; prefer it over the raw `displayName` (e.g. "PMR Pending", "21-4142/21-4142a").

## Supporting documents (`attributes.supportingDocuments[]`)

Uploaded/generated files. `documentTypeLabel` of `C&P Exam` with a `DBQ-...` filename indicates a
completed Compensation & Pension exam (a strong sign of claim progress). The DBQ name hints at the
body system (e.g. `DBQ NEURO Parkinson's Disease`, `DBQ GU Kidney`, `DBQ PSYCH Mental Disorders`).

## Rated disabilities (`/v0/rated_disabilities`)

Top-level (`data.attributes`):
- `combined_disability_rating` — the overall combined % (VA "fuzzy math", not a simple sum).
- `combined_effective_date` — when payment at that level begins.
- `legal_effective_date` — when entitlement was legally established.

Each `individual_ratings[]` entry:
| Field | Meaning |
|---|---|
| `decision` | `Service Connected` (granted) or `Not Service Connected` (denied) |
| `rating_percentage` | The condition's rating; `null` for denied, `0` is granted but non-compensable |
| `diagnostic_type_name` | The rating schedule category (e.g. "Mood disorder", "Paralysis of the sciatic nerve") |
| `diagnostic_text` | The specific condition wording, often "... due to Parkinson's disease" for secondaries |
| `effective_date` | When the rating took effect |
| `static_ind` | `true` = static (not scheduled for re-exam); `false` = may be re-evaluated / not locked |
| `hyph_diagnostic_type_code` | A shared code linking secondaries to a primary (e.g. `8004` = Parkinson's) |

Note: a 0% rating is **still service-connected** and counts toward the overall picture; it can be
increased later if the condition worsens.

## Appeals (`/v0/appeals`)

Each appeal under `data[]` has `attributes` with:
- `status.type` — current step (e.g. `pending_form9`, `on_docket`, `scheduled_hearing`,
  `bva_decision`, `evidentiary_period`). Translate to plain English.
- `programArea` — e.g. `compensation`.
- `aoj` — agency of original jurisdiction.
- `events[]` — timeline; the last entry is the most recent action, with its `date`.
- `type` — the review lane: `legacyAppeal`, `higherLevelReview`, `supplementalClaim`,
  `appeal` (Board/AMA). Name the lane in the summary.

## Special Monthly Compensation (SMC) — for follow-up framing only

SMC is extra compensation beyond the percentage rating, for severe losses or needing aid. Worth
flagging (never determining) when the data shows a high combined rating with severe
conditions — especially Aid & Attendance (help with daily activities) or statutory housebound
(a single 100% plus 60%+ more). Direct the veteran to a VSO to confirm eligibility.
