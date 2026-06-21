---
name: daily-briefing
description: Generate a morning (or end-of-day) operational briefing covering signals, revenue, and subscriber alerts. Uses the daily-briefing skill.
argument-hint: "[quick|eod|date]"
---

Generate a GemaInterprises daily briefing using the **daily-briefing** skill.

## Steps

1. Parse the argument to determine mode: `quick`, `eod`, or full (default)
2. Determine the date (default: today)
3. If ~~gema-api is connected:
   - Call `GET /api/signals` for overnight results and pending positions
   - Call `GET /api/stats` for win rate snapshot
4. If ~~stripe is connected:
   - Pull active subscription count by plan
   - Check for any past_due or failed payment events
5. If neither is connected, ask the user for the data or offer to work from estimates
6. Apply daily-briefing skill methodology
7. Output the formatted briefing for the selected mode
8. Clearly state today's top 3 priorities as the final output

## Example usage

```
/gema:daily-briefing
/gema:daily-briefing quick
/gema:daily-briefing eod
/gema:daily-briefing 2025-06-07
```
