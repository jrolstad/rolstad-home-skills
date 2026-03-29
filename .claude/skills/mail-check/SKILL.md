---
name: mail-check
description: Overview of incoming USPS mail pieces and packages. Use when user asks "check the mail", "any packages coming", "what's in the mail", or wants to see mail delivery status.
---

# Mail Check

Get a snapshot of incoming USPS mail and packages expected for delivery.

## Prerequisites

- USPS MCP server must be running

## Steps

### 1. Fetch Mail and Packages

Call in parallel:
- `mcp__usps__get_mail_pieces` — incoming mail pieces (Informed Delivery); filter to the last 3 days by default
- `mcp__usps__get_packages` — packages in transit

### 2. Get Mail Piece Images

For each mail piece, fetch its image using `mcp__usps__get_mail_piece_image`. Use the image to:
- Identify who the piece is addressed to (the recipient name on the envelope)
- Write a brief 1-sentence description of what the piece appears to be (e.g. "Statement from Chase Bank", "Marketing mailer from Amazon", "Official letter from IRS")

Fetch all images in parallel.

### 3. Generate Summary Report

Output a structured report:

```
## Mail Summary — [Date]

### Mail Pieces Today

Sort rows by delivery date descending (most recent first). The date column goes on the far left.

| Delivered | For | Sender | Summary |
|-----------|-----|--------|---------|
| Mar 28 | Alex | Chase Bank | Credit card statement |
| Mar 23 | Jordan | Amazon | Marketing mailer |

### Packages
| Tracking # | Description | Status | Expected |
|------------|-------------|--------|---------|
| 9400... | Amazon order | In transit | Tomorrow |
| 9261... | Return label | Delivered | Today |

### Summary
- X mail pieces expected today
- X packages in transit, X delivered today
```

### 4. Offer Follow-up Actions

After presenting the summary, offer:

```
Would you like me to:
1. Show the image of a specific mail piece
2. Get tracking details for a specific package
```

## Notes

- Mail pieces shown are from USPS Informed Delivery — requires enrollment
- Package tracking updates throughout the day; check again if status seems stale
