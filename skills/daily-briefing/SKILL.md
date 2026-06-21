---
name: daily-briefing
description: Generate a morning briefing for GemaInterprises. Use at the start of each day to review overnight signal results, check pending trades, monitor revenue health, flag any subscriber issues, and set the day's top priorities. Scannable in under 2 minutes.
argument-hint: "[date]"
---

# Daily Briefing

**Important**: This briefing aggregates operational data for internal use. Signal performance data does not constitute financial advice.

A fast, scannable morning summary covering signal results, open positions, revenue status, and subscriber alerts for GemaInterprises.

## Briefing Sections

### 1. Signal Overnight Results

Pull all signals settled since last briefing:
- New WIN count and total P&L contributed
- New LOSS count and P&L impact
- Running win rate for current week/month
- Any signals settled unexpectedly (e.g. old PENDING resolved)

### 2. Open Positions (PENDING Signals)

List all currently PENDING signals ordered by age (oldest first):

| Age | Market | Side | Type | Entry | Whale Amount |
|-----|--------|------|------|-------|-------------|
| XXh | BTC/USD | YES | STRONG | $XX,XXX | $X.XM |

Flag any PENDING signal older than 48 hours — these require manual review or forced settlement.

### 3. Revenue Pulse

Quick snapshot (pull from Stripe or DB):
- Active paying subscribers (Pro + Enterprise)
- MRR as of today
- Any new subscribers since yesterday
- Any cancellations since yesterday
- Any failed payments currently open

### 4. Subscriber Alerts

Flag:
- Users with `past_due` subscription status
- Enterprise accounts with no activity in 7+ days
- New Free registrations (acquisition signal)
- Pro users who have been Free-to-Pro in the last 24h (conversion win)

### 5. Top 3 Priorities for Today

Based on the data above, surface the 3 most important actions:

Priority ranking logic:
1. **Critical** — Failed Enterprise payment, signal pending >72h, webhook delivery failure
2. **High** — Multiple failed Pro payments, win rate dropping below 55% this week
3. **Medium** — New Free users to nurture, Pro → Enterprise upgrade candidates

## Output Format

```
─────────────────────────────────────────
  GEMA INTERPRISES — Daily Briefing
  [Weekday, Month DD YYYY] — [Time]
─────────────────────────────────────────

SIGNALS
  Settled overnight:   X wins (+$X,XXX) / X losses (-$XXX)
  Week win rate:       XX.X%   [🟢 / 🟡 / 🔴]
  Open positions:      XX pending
  ⚠ Pending >48h:     X signal(s) — review needed

REVENUE
  MRR:                 $XX,XXX
  Active paid users:   XXX (XX Pro / XX Enterprise)
  New today:           +X subscriber(s)
  Canceled today:      -X subscriber(s)
  Failed payments:     X open  [⚠ if > 0]

SUBSCRIBERS
  Total registered:    XXX
  Past due accounts:   X  [🔴 if > 0]
  Inactive Enterprise: X  [⚠ if > 0]
  New Free today:      +X

TODAY'S PRIORITIES
  1. [Most urgent action]
  2. [Second priority]
  3. [Third priority]
─────────────────────────────────────────
```

## Modes

**Quick mode** (`/gema:daily-briefing quick`): Signals + revenue only, no subscriber detail. For when you have < 60 seconds.

**Full mode** (default): All five sections above.

**EOD mode** (`/gema:daily-briefing eod`): End-of-day wrap-up — what settled today, net P&L for the day, MRR movement, and tomorrow's setup.

## Data Sources

| Section | Source | Fallback |
|---------|--------|---------|
| Signals | `GET /api/signals` + `GET /api/stats` | Paste signal CSV |
| Revenue | ~~stripe subscriptions list | Stripe dashboard export |
| Subscribers | DB user table | Manual count from admin |

If ~~gema-api is connected, the briefing pulls live data automatically. Otherwise prompt the user to paste the relevant data or share a screenshot of their dashboard.

## Best Practices

1. **Run the briefing before opening Slack or email** — set priorities while your head is clear
2. **Never skip the pending signals section** — an unresolved PENDING signal is an undeclared position
3. **One critical priority maximum** — if everything is critical, nothing is
4. **Log the briefing output weekly** — tracking briefing-to-briefing deltas reveals operational trends
