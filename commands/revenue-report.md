---
name: revenue-report
description: Generate a Stripe revenue report — MRR, ARR, new vs churned revenue, failed payments, and growth metrics. Uses the revenue-report skill.
argument-hint: "[period: YYYY-MM | this-month | last-month]"
---

Generate a GemaInterprises revenue report using the **revenue-report** skill.

## Steps

1. Determine the reporting period from the argument (default: current month)
2. If ~~stripe is connected:
   - List subscriptions created in period (new MRR)
   - List subscriptions canceled in period (churned MRR)
   - List failed invoices (payment risk)
   - List successful charges (gross revenue)
3. If ~~gema-api is connected, cross-check plan counts in DB against Stripe
4. If neither is connected, ask the user for Pro and Enterprise subscriber counts
5. Apply the revenue-report skill methodology to calculate MRR components
6. Run the reconciliation checklist from the skill
7. Output the standard Revenue Report format
8. Flag any discrepancies between DB and Stripe subscription states

## Example usage

```
/gema:revenue-report
/gema:revenue-report this-month
/gema:revenue-report last-month
/gema:revenue-report 2025-05
```
