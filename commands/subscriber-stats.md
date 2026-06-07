---
name: subscriber-stats
description: Review subscriber base health — plan distribution, MRR, churn risk, and upgrade opportunities. Uses the subscriber-health skill.
argument-hint: "[segment: all|free|pro|enterprise] [period]"
---

Run a subscriber health analysis using the **subscriber-health** skill.

## Steps

1. Determine the segment filter from the argument (default: all)
2. Determine the period from the argument (default: current snapshot)
3. If ~~gema-api is connected, query user plan distribution from the API
4. If ~~stripe is connected, pull subscription states for churn risk detection
5. If neither is connected, ask the user for their current subscriber counts per plan
6. Apply the subscriber-health skill methodology
7. Output the standard Subscriber Health Report format
8. Surface any churn risk users and upgrade opportunity candidates

## Example usage

```
/gema:subscriber-stats
/gema:subscriber-stats pro
/gema:subscriber-stats all 2025-06
/gema:subscriber-stats enterprise
```
