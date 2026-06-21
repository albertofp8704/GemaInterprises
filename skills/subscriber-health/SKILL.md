---
name: subscriber-health
description: Review GemaInterprises subscriber base health. Use when analyzing plan distribution (Free/Pro/Enterprise), identifying churn risk, reviewing upgrade/downgrade patterns, or preparing a subscriber status report. Covers Stripe subscription states and user plan data.
argument-hint: "[segment] [period]"
---

# Subscriber Health Analysis

**Important**: This skill assists with subscriber analytics workflows. User data should be handled in accordance with your privacy policy and applicable regulations.

Methodology for monitoring subscriber acquisition, plan distribution, churn signals, and upgrade opportunities in GemaInterprises.

## Data Model

### User record (from GemaInterprises DB)
- **email** — User identifier
- **plan** — `free`, `pro`, `enterprise`
- **stripe_customer_id** — Linked Stripe customer (null for free users)
- **stripe_subscription_id** — Active subscription ID
- **created_at** — Registration timestamp

### Plan tiers
| Plan | Price | Target |
|------|-------|--------|
| Free | $0/mo | Acquisition / trial |
| Pro | $49/mo | Individual traders |
| Enterprise | $199/mo | Funds / professional desks |

## Analysis Workflow

### 1. Plan Distribution Snapshot

Calculate:
- Count and % of users per plan (Free / Pro / Enterprise)
- MRR = (Pro count × $49) + (Enterprise count × $199)
- ARR = MRR × 12
- Average Revenue Per User (ARPU) across all paying users

Healthy benchmark: Free-to-paid conversion rate ≥ 8%

### 2. Churn Risk Signals

Flag users who show any of these patterns:

| Signal | Risk level | Action |
|--------|-----------|--------|
| Stripe subscription `past_due` | High | Immediate outreach |
| Stripe subscription `unpaid` | Critical | Suspend access, contact |
| Pro/Enterprise user with 0 logins in 14d | Medium | Re-engagement email |
| Pro user who has never viewed signals | High | Onboarding check |
| Enterprise user approaching renewal | Medium | Account review call |

### 3. Upgrade Opportunity Identification

Free users most likely to convert:
- Registered > 7 days ago (have had time to explore)
- Have logged in ≥ 3 times
- Viewed the upgrade CTA (dashboard upgrade card)

Pro users most likely to upgrade to Enterprise:
- High signal consumption (near limit of 50 displayed)
- Account age > 90 days (established users)
- Multiple team members using the same account

### 4. Cohort Analysis

Group users by registration month and track:
- What % converted from Free to paid within 30/60/90 days
- What % of Pro subscribers churned within 3 months
- Retention curve by cohort

```
Cohort [Month]:
  Registered:    XXX
  Converted D30: XX%
  Converted D60: XX%
  Retained M3:   XX%
  Retained M6:   XX%
```

### 5. Standard Output Format

```
Subscriber Health Report — [Date]
Generated: [Timestamp]

PLAN DISTRIBUTION
  Free:         XXX users  (XX%)
  Pro:          XXX users  (XX%)   $X,XXX MRR
  Enterprise:   XXX users  (XX%)   $X,XXX MRR
  ─────────────────────────────────────────
  Total MRR:    $XX,XXX
  Total ARR:    $XXX,XXX
  ARPU (paid):  $XXX/mo

CHURN RISK
  Past due:     XX subscriptions  ⚠
  Inactive 14d: XX paying users   ⚠
  Never used:   XX paid users     🔴

UPGRADE OPPORTUNITIES
  Free → Pro candidates:        XX users
  Pro → Enterprise candidates:  XX users

FLAGS
  - [Any anomalies or items requiring attention]
```

## Stripe Subscription States

| State | Meaning | Action |
|-------|---------|--------|
| `active` | Healthy subscription | None |
| `trialing` | In trial period | Monitor conversion |
| `past_due` | Payment failed, retrying | Email + Stripe retry |
| `unpaid` | All retries exhausted | Suspend + manual contact |
| `canceled` | Subscription ended | Win-back campaign |
| `incomplete` | Initial payment pending | Follow up within 24h |

## Best Practices

1. **Review churn risk weekly** — catching `past_due` before it becomes `unpaid` saves 80% of at-risk revenue
2. **Segment by plan before drawing conclusions** — Free user inactivity is normal; Pro user inactivity is a churn signal
3. **Track MRR movement, not just totals** — new MRR, expansion MRR, churned MRR, and net MRR give a complete picture
4. **Never count Free users in revenue metrics** — keep acquisition and revenue KPIs separate
5. **Enterprise accounts need human touchpoints** — automated emails are insufficient for $199/mo relationships
