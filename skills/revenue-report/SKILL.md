---
name: revenue-report
description: Analyze GemaInterprises Stripe revenue. Use when reviewing MRR, ARR, new vs churned revenue, subscription events, failed payments, or preparing a monthly/weekly revenue summary. Covers Pro ($49/mo) and Enterprise ($199/mo) plans.
argument-hint: "[period]"
---

# Revenue Report

**Important**: This skill assists with revenue analysis workflows. All financial data should be reconciled against your official Stripe dashboard and accounting records before use in financial statements.

Methodology for tracking subscription revenue, payment health, and Stripe event analysis for GemaInterprises.

## Revenue Architecture

GemaInterprises uses Stripe for all paid subscriptions:

| Plan | Stripe Price | Billing |
|------|-------------|---------|
| Pro | $49/month | Monthly recurring |
| Enterprise | $199/month | Monthly recurring |

Stripe webhook events handled by `/api/stripe/webhook`:
- `checkout.session.completed` — activates plan on new signup
- `customer.subscription.deleted` — downgrades user to Free
- `invoice.payment_failed` — flags payment failure

## MRR Calculation

```
MRR = (active_pro_count × $49) + (active_enterprise_count × $199)
```

MRR components to track separately:
- **New MRR** — Revenue from new subscribers this period
- **Expansion MRR** — Revenue from Pro → Enterprise upgrades
- **Churned MRR** — Revenue lost from cancellations/downgrades
- **Reactivation MRR** — Revenue from previously churned users returning
- **Net New MRR** = New + Expansion + Reactivation − Churned

## Revenue Report Workflow

### 1. Pull Period Data

If ~~stripe is connected:
- List subscriptions created in period (new MRR)
- List subscriptions canceled in period (churned MRR)
- List subscription upgrades (expansion MRR)
- List failed invoices (payment risk)
- List successful charges (gross revenue)

If not connected:
> Connect ~~stripe or export a CSV from your Stripe dashboard to analyze revenue automatically.

### 2. Standard Revenue Summary

```
Revenue Report — [Month/Period]
Generated: [Date]

MRR SNAPSHOT
  Pro subscribers:        XXX  ×  $49  =  $X,XXX
  Enterprise subscribers: XXX  × $199  =  $X,XXX
  ──────────────────────────────────────────────
  Total MRR:              $XX,XXX
  ARR (×12):              $XXX,XXX

MRR MOVEMENT
  New MRR:          +$X,XXX   (XX new subscribers)
  Expansion MRR:    +$X,XXX   (XX Pro → Enterprise)
  Churned MRR:      -$X,XXX   (XX cancellations)
  Net New MRR:      +$X,XXX

PAYMENT HEALTH
  Successful charges:   $XX,XXX
  Failed charges:       $X,XXX   (XX events)  ⚠
  Recovery rate:        XX%

GROWTH
  MoM MRR growth:   +XX%
  MoM subscriber growth: +XX%
```

### 3. Failed Payment Analysis

For each failed payment event:
- Amount failed
- Retry attempt number (Stripe retries up to 4×)
- Days since first failure
- Customer plan (Pro vs Enterprise)
- Action taken (email sent? manual outreach?)

Escalation thresholds:
| Condition | Action |
|-----------|--------|
| 1st failure | Stripe auto-retries, send dunning email |
| 2nd failure (day 3) | Personal email to customer |
| 3rd failure (day 5) | Suspend dashboard access warning |
| 4th failure (day 7) | Cancel subscription, downgrade to Free |
| Enterprise any failure | Immediate personal outreach |

### 4. Revenue Reconciliation Checklist

Before finalizing any period report:
- [ ] Stripe dashboard MRR matches calculated MRR
- [ ] All `checkout.session.completed` events have corresponding plan activations in DB
- [ ] All `customer.subscription.deleted` events have corresponding Free downgrades in DB
- [ ] No discrepancy between paying users in DB and active subscriptions in Stripe
- [ ] All failed payment users are flagged with correct subscription state
- [ ] Gross revenue matches Stripe payout + fees

### 5. Key Growth Benchmarks

| Metric | Target | Alert |
|--------|--------|-------|
| MoM MRR growth | ≥ 10% | < 5% |
| Churn rate | ≤ 3%/mo | > 5%/mo |
| Failed payment recovery | ≥ 70% | < 50% |
| Free-to-paid conversion | ≥ 8% | < 4% |
| Enterprise % of MRR | ≥ 40% | < 20% |

## Best Practices

1. **Reconcile DB with Stripe weekly** — webhook failures can cause ghost subscriptions (active in Stripe, Free in DB)
2. **Track Net New MRR, not gross** — a flat MRR with high churn masked by new signups is a retention problem
3. **Enterprise revenue is lumpy** — a single Enterprise cancellation is −$199 MRR; give these accounts white-glove treatment
4. **Monitor failed payments daily** — the recovery window is short; acting within 24h recovers 2× more revenue than acting at 72h
5. **Review Stripe webhook delivery logs** — failed webhook deliveries silently break plan activation and cancellation flows
