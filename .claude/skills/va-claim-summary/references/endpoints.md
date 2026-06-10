# VA.gov API Endpoints

Source: r/VeteransBenefits community method ("Unlock Your VA Claim Secrets"). These are the
internal endpoints that power the My VA dashboard. They are **undocumented and can change**.

## How the user fetches the data

1. Log into **https://www.va.gov/my-va/** in a browser (Chrome recommended — it offers a
   "Pretty-print" checkbox for JSON).
2. In the **same browser session**, open a new tab and paste one of the URLs below.
3. The page returns JSON. Copy all of it and paste it back to the skill.

Authentication is the logged-in VA.gov **session cookie** — there is no separate API key. This is
why Claude cannot fetch these URLs directly; the data only resolves inside the user's authenticated
browser session.

If the user is not on Windows / wants a reader: https://jsonviewer.stack.hu

## Endpoints

| What it returns | URL |
|---|---|
| **All claims** (list, by claim ID) | `https://api.va.gov/v0/benefits_claims` |
| **Specific claim detail** | `https://api.va.gov/v0/benefits_claims/#########` (replace with the claim ID) |
| **Appeals** (by associated claim ID) | `https://api.va.gov/v0/appeals` |
| **Rated disabilities** (diagnostic codes, rating IDs, static indicators) | `https://api.va.gov/v0/rated_disabilities` |
| **User info** (authenticated profile) | `https://api.va.gov/v0/user` |
| **Maintenance windows** | `https://api.va.gov/v0/maintenance_windows/` |
| **Backend statuses** (caseflow/appeals, lighthouse, vbms, vre health) | `https://api.va.gov/v0/backend_statuses` |

To get a claim ID for the detail endpoint, first pull the **All claims** list; each entry's `id` is
the claim ID to substitute into the detail URL.

## Advanced (optional) direct fetch — discouraged

The endpoints require the live session cookie. If, and only if, the user explicitly pastes a current
cookie/token and asks for automation, the request shape is:

```
curl 'https://api.va.gov/v0/benefits_claims' \
  -H 'Cookie: <the user-provided va.gov session cookie>' \
  -H 'Accept: application/json'
```

Caveats to tell the user: the session token expires within minutes, it grants access to sensitive
medical/benefits data, and it must **never be saved to disk or memory**. Default to the paste
workflow instead.
