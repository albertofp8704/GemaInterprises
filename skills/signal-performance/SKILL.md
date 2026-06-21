---
name: signal-performance
description: Analyze GemaInterprises trading signal performance. Use when reviewing win/loss rates, P&L totals, signal quality by type (STRONG/MEDIUM), pending signal exposure, or historical performance trends. Covers BTC/USD signals with whale-transaction context.
argument-hint: "[period] [type]"
---

# Signal Performance Analysis

**Important**: This skill assists with performance analysis workflows. Signal data reflects past results and does not constitute financial advice. Past performance does not guarantee future results.

Methodology for analyzing trading signal quality, win rates, P&L attribution, and pending exposure across GemaInterprises signal data.

## Data Model

Each signal has:
- **market** — Trading pair (currently BTC/USD)
- **side** — Direction: `YES` (long) or `NO` (short)
- **signal_type** — Strength: `STRONG` or `MEDIUM`
- **whale_amount** — On-chain transaction size that triggered the signal (USDT)
- **entry_price** — BTC price at signal creation
- **result** — `WIN`, `LOSS`, or `PENDING`
- **pnl** — Profit/loss in USD (null while PENDING)
- **created_at** — Signal timestamp

## API Endpoints

If ~~gema-api is connected:
- `GET /api/signals` — Last 50 signals for the authenticated user (requires JWT)
- `GET /api/stats` — Aggregated stats: total_signals, wins, losses, win_rate, total_pnl, pending_count (requires JWT)
- `POST /api/signals` — Create signal (requires X-API-Key)
- `PATCH /api/signals/{id}/settle` — Settle signal WIN/LOSS (requires X-API-Key)

If no API is connected:
> Connect ~~gema-api or paste raw signal data to analyze performance automatically.

## Performance Analysis Workflow

### 1. Gather Signal Data

Pull or request:
- All settled signals for the target period (exclude PENDING)
- Separate STRONG vs MEDIUM signal batches
- Total pending signal exposure (sum of open positions)

### 2. Core Metrics

Calculate the following for total, STRONG, and MEDIUM separately:

| Metric | Formula |
|--------|---------|
| Win Rate | wins / (wins + losses) × 100 |
| Total P&L | sum of all settled pnl values |
| Avg P&L per WIN | sum of positive pnl / wins |
| Avg Loss per LOSS | sum of negative pnl / losses |
| Profit Factor | gross profit / gross loss |
| Expectancy | (win_rate × avg_win) − (loss_rate × avg_loss) |

### 3. Signal Quality Assessment

**STRONG signals** should show:
- Higher win rate than MEDIUM (target ≥ 65%)
- Higher average P&L per trade
- Lower drawdown per loss

**MEDIUM signals** should show:
- Higher frequency
- Acceptable win rate (target ≥ 55%)
- Smaller average position sizes

Flag if STRONG win rate is below MEDIUM win rate — indicates a signal generation issue.

### 4. Whale Amount Analysis

Correlate whale_amount with outcome:
- Group signals into buckets: <$500k, $500k–$2M, $2M–$10M, >$10M
- Calculate win rate per bucket
- Identify the whale threshold that best predicts winning trades
- Flag unusually small whale amounts that triggered signals (potential noise)

### 5. Pending Exposure Report

For PENDING signals:
- Count open positions
- List by age (oldest first — signals pending >48h are high risk)
- Sum total capital at risk
- Flag any pending signals older than 72h for manual review

### 6. Standard Output Format

```
Signal Performance Report — [Period]
Generated: [Date]

OVERALL
  Settled signals:    XX
  Win rate:           XX.X%
  Total P&L:          $X,XXX
  Profit factor:      X.XX
  Expectancy/trade:   $XXX

BY TYPE
  STRONG  | Win rate: XX% | Count: XX | P&L: $X,XXX
  MEDIUM  | Win rate: XX% | Count: XX | P&L: $X,XXX

PENDING EXPOSURE
  Open positions:     XX
  Oldest signal:      XX hours ago
  ⚠ Signals >48h:    XX (review recommended)

FLAGS
  - [Any anomalies or items requiring attention]
```

## Benchmarks & Thresholds

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| Overall win rate | ≥ 60% | 50–59% | < 50% |
| STRONG win rate | ≥ 65% | 55–64% | < 55% |
| Profit factor | ≥ 1.5 | 1.0–1.49 | < 1.0 |
| Pending >48h | 0 | 1–2 | ≥ 3 |
| Total pending | ≤ 5 | 6–10 | > 10 |

## Best Practices

1. **Separate analysis by period** — weekly and monthly views reveal trends monthly aggregates hide
2. **Never mix PENDING into win rate** — only settled signals count
3. **Track whale_amount distribution** — signal quality degrades if thresholds drift
4. **Monitor expectancy, not just win rate** — a 40% win rate with 3:1 reward/risk beats 60% with 1:1
5. **Review LOSS clusters** — 3+ consecutive losses on STRONG signals may indicate market regime change
