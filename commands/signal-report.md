---
name: signal-report
description: Generate a signal performance report for a given period or signal type. Analyzes win rate, P&L, profit factor, and pending exposure. Uses the signal-performance skill.
argument-hint: "[period] [type: STRONG|MEDIUM|all]"
---

Run a full signal performance analysis using the **signal-performance** skill.

## Steps

1. Determine the target period from the argument (default: current month)
2. Determine the signal type filter from the argument (default: all)
3. If ~~gema-api is connected, call `GET /api/signals` and `GET /api/stats`
4. If not connected, ask the user to paste their signal data or stats
5. Apply the signal-performance skill methodology to calculate all metrics
6. Output the standard Signal Performance Report format from the skill
7. Highlight any metrics in Yellow or Red threshold zones
8. List specific action items if any flags are raised

## Example usage

```
/gema:signal-report
/gema:signal-report this-week
/gema:signal-report 2025-06 STRONG
/gema:signal-report last-month all
```
