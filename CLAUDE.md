# GemaInterprises — Project Memory

## What This Project Is

A **crypto trading signal SaaS platform** built with FastAPI + Vanilla JS. Users subscribe (Free / Pro $49/mo / Enterprise $199/mo) to receive whale-transaction signals with win/loss tracking and P&L metrics.

- **Backend**: FastAPI, SQLAlchemy, Stripe, JWT/bcrypt
- **DB**: PostgreSQL (prod via Railway) / SQLite (dev)
- **Frontend**: Vanilla HTML/CSS/JS — dark theme, no frameworks
- **Deployment**: Railway (nixpacks)

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | All FastAPI routes and business logic |
| `app/auth.py` | JWT auth helpers |
| `app/database.py` | SQLAlchemy models + DB init |
| `static/dashboard.html` | Main user dashboard |
| `index.html` | Public landing page |

## API Surface

- `POST /api/auth/register` / `POST /api/auth/login` / `GET /api/auth/me`
- `GET /api/signals` — recent 50 signals (auth required)
- `GET /api/stats` — win rate, P&L, totals (auth required)
- `POST /api/signals` — create signal (internal `X-API-Key`)
- `PATCH /api/signals/{id}/settle` — mark WIN/LOSS (internal `X-API-Key`)
- `POST /api/stripe/create-checkout/{plan}` / `verify-session` / `webhook`

## Design Tokens

- Background: `#03060f` | Secondary: `#070c1a`
- Accent green: `#00C805` | Gold: `#C9A84C` | Red: `#FF2D55`
- Fonts: Inter (body), JetBrains Mono (code/prices)

---

## Reference: anthropics/knowledge-work-plugins

Repo: <https://github.com/anthropics/knowledge-work-plugins>  
License: Apache-2.0 | ~19.5k ⭐

Open-source **Claude plugins** for knowledge workers. Each plugin bundles:
- **Skills** — domain expertise Claude uses automatically
- **Commands** — explicit slash commands (e.g. `/sales:call-prep`)
- **Connectors** — MCP server wiring to external tools (Slack, Notion, HubSpot, etc.)
- **Manifest** — `plugin.json` configuration

### Available Plugins (11 official)

| Plugin | Best for |
|--------|---------|
| Productivity | Tasks, calendars, Slack/Notion/Jira/Linear |
| Sales | Prospecting, call prep, pipeline, outreach |
| Customer Support | Ticket triage, response drafting, escalations |
| Product Management | Specs, roadmaps, user research |
| Marketing | Content, campaigns, brand voice, analytics |
| Legal | Contract review, NDA triage, compliance |
| Finance | Journal entries, reconciliation, statements |
| Data | SQL, visualization, dashboards |
| Enterprise Search | Search email, chat, docs, wikis |
| Bio Research | Genomics, literature, preclinical |
| Plugin Management | Build/customize plugins for your org |

### Plugin file layout

```
plugin-name/
├── .claude-plugin/plugin.json   # manifest
├── .mcp.json                    # MCP connector wiring
├── commands/                    # slash commands
└── skills/                      # domain expertise files
```

### Install in Claude Code

```bash
claude plugin marketplace add anthropics/knowledge-work-plugins
claude plugin install <name>@knowledge-work-plugins
```

### GemaInterprises Plugin (implemented)

A custom plugin has been built at the root of this repo following the knowledge-work-plugins structure:

```
.claude-plugin/plugin.json    # manifest
.mcp.json                     # gema-api + Stripe connectors
skills/
  signal-performance/SKILL.md # win rate, P&L, whale analysis
  subscriber-health/SKILL.md  # plan distribution, churn, MRR
  revenue-report/SKILL.md     # Stripe MRR/ARR, payment health
  daily-briefing/SKILL.md     # morning/EOD operational summary
commands/
  signal-report.md            # /gema:signal-report
  subscriber-stats.md         # /gema:subscriber-stats
  revenue-report.md           # /gema:revenue-report
  daily-briefing.md           # /gema:daily-briefing [quick|eod]
```

Skills are automatically used by Claude when relevant. Commands are invoked explicitly with `/gema:<command>`.
