---
name: finance-check
description: Overview of account balances and recent transactions across BECU and Heritage Bank NW. Use when user asks "check accounts", "how much money do I have", "account balances", or wants a financial summary.
---

# Finance Check

Get a snapshot of current balances and recent activity across all home bank accounts.

## Prerequisites

- BECU MCP server must be running
- Heritage Bank NW MCP server must be running

## Steps

### 1. Fetch All Accounts and Balances

Call in parallel:
- `mcp__becu__get_accounts` — list BECU accounts
- `mcp__heritagebanknw__get_accounts` — list Heritage Bank NW accounts

Then fetch balances for each account using `mcp__becu__get_balance` and `mcp__heritagebanknw__get_balance`.

### 2. Get Recent Transactions

For each account, fetch recent transactions:
- `mcp__becu__get_transactions` — BECU transactions
- `mcp__heritagebanknw__get_transactions` — Heritage Bank NW transactions

Use the transactions only to determine the most recent transaction date per account. Do not display transaction details in the summary.

### 3. Generate Summary Report

Output a structured report:

```
## Finance Summary — [Date]

### Account Balances

#### BECU

Group BECU accounts by the first segment of the account name (the part before the first " - "). For example, "Alex and Jordan - Checking" and "Alex and Jordan - Savings" are grouped under **Alex and Jordan**.

**Alex and Jordan**
| Account | Balance | Last Transaction |
|---------|---------|-----------------|
| Checking | $3,720.00 | Mar 23 |
| Savings | $8,540.00 | Mar 15 |

**Jordan**
| Account | Balance | Last Transaction |
|---------|---------|-----------------|
| Tax Savings | $5,100.00 | Mar 15 |
| Working Profit | $2,875.00 | Mar 15 |

**Savings**
| Account | Balance | Last Transaction |
|---------|---------|-----------------|
| Annual Payments | $41,300.00 | Mar 10 |
| Mortgage Extra | $9,650.00 | Mar 10 |

*(continue for each group)*

#### Heritage Bank NW
| Account | Balance | Last Transaction |
|---------|---------|-----------------|
| Checking (...5537) | $6,240.00 | Mar 25 |

**Total across all accounts: $77,425.00**

### Notes
- Any accounts with low balances
- Anything that looks unusual
```

### 4. Offer Follow-up Actions

After presenting the summary, offer:

```
Would you like me to:
1. Show recent activity (last 7 days) across all accounts
2. Show full transaction history for a specific account
3. Refresh the cache and re-fetch
```

## Notes

- Use `mcp__becu__reset_cache` if data looks stale
- Balances are point-in-time snapshots; pending transactions may not be reflected
